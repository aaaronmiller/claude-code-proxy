import asyncio
import json
import logging
import os
from fastapi import HTTPException
from typing import Optional, AsyncGenerator, Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai._exceptions import (
    APIError,
    RateLimitError,
    AuthenticationError,
    BadRequestError,
)

logger = logging.getLogger(__name__)

# Providers whose APIs expect bare model names (no provider prefix like "opencode_go/").
# The proxy stores models as "provider/model" for routing, but these endpoints
# only recognise the part after the slash.
_MODEL_PREFIX_STRIP_PROVIDERS = {
    "opencode_go",  # opencode.ai expects "qwen3.6-plus", not "opencode_go/qwen3.6-plus"
}


def _maybe_strip_model_prefix(model: str, base_url: str) -> str:
    """Strip provider prefix from model name if the target API requires it."""
    if "/" not in model:
        return model
    prefix = model.split("/", 1)[0].lower()
    # Match by checking if the URL belongs to a known strip-provider
    for known_prefix, url_fragment in [
        ("opencode_go", "opencode.ai"),
    ]:
        if prefix == known_prefix and url_fragment in base_url:
            stripped = model.split("/", 1)[1]
            logger.debug(
                f"Stripped provider prefix for {known_prefix}: '{model}' → '{stripped}'"
            )
            return stripped
    return model


# ─────────────────────────────────────────────────────────────────────────────
# Module-level circuit breaker registry (shared across all cascade calls)
# ─────────────────────────────────────────────────────────────────────────────
_circuit_breakers: Dict[str, Any] = {}

# ─────────────────────────────────────────────────────────────────────────────
# Mid-stream tier override registry
# When a stream hits MID_STREAM_OUTPUT_BUDGET, we record the session fingerprint
# here so the next request from that session routes to a cheaper tier.
# Format: { session_fingerprint: preferred_tier_name }
# ─────────────────────────────────────────────────────────────────────────────
_mid_stream_tier_overrides: Dict[str, str] = {}

def get_mid_stream_tier_override(session_fp: str) -> Optional[str]:
    """Return the cheaper tier override for a session, then clear it (one-shot)."""
    return _mid_stream_tier_overrides.pop(session_fp, None)

def set_mid_stream_tier_override(session_fp: str, tier: str) -> None:
    """Record that this session's next request should use a cheaper tier."""
    _mid_stream_tier_overrides[session_fp] = tier


def _get_circuit_breaker(model: str):
    """Return (or lazily create) the circuit breaker for a model.

    Thresholds read from env at first access:
        CB_FAILURE_THRESHOLD  — failures before opening (default: 3)
        CB_SUCCESS_THRESHOLD  — successes in half-open before closing (default: 1)
        CB_TIMEOUT_SECONDS    — cooldown before half-open probe (default: 300)
    """
    if model not in _circuit_breakers:
        import os
        from src.core.circuit_breaker import CircuitBreaker

        _circuit_breakers[model] = CircuitBreaker(
            name=model,
            failure_threshold=int(os.environ.get("CB_FAILURE_THRESHOLD", "3")),
            success_threshold=int(os.environ.get("CB_SUCCESS_THRESHOLD", "1")),
            timeout=float(os.environ.get("CB_TIMEOUT_SECONDS", "300")),
        )
    return _circuit_breakers[model]


def _is_cb_open(model: str) -> bool:
    """Return True if the circuit breaker for this model is OPEN (should be skipped)."""
    if model not in _circuit_breakers:
        return False
    return _circuit_breakers[model].is_open


def _build_or_models_list(primary: str, fallback_models: list) -> list:
    """
    Build the ordered model list for OR native injection, filtering out any
    models whose circuit breakers are currently OPEN.

    Dead models in the OR `models` array waste OR's routing budget evaluating
    endpoints we already know are broken.  The primary model is always kept
    as the first entry (OR needs at least one model to route).
    """
    candidates = [primary] + [m for m in fallback_models if m != primary]
    filtered = [m for m in candidates if not _is_cb_open(m)]
    if not filtered:
        # All breakers open — fall back to primary only so OR still gets a valid request
        filtered = [primary]
    # OpenRouter currently rejects `models` arrays longer than 3 total entries.
    # Keep the primary model first, then cap the native list to fit OR's limit.
    return filtered[:3]


def _get_dynamic_fallback_models(limit: int = 10) -> list:
    """
    Return the top tool-capable free models from the cached rankings file.
    Falls back to an empty list if the cache doesn't exist yet.
    Only models that *support_tools* are included — unusable for agentic tasks otherwise.
    """
    try:
        from src.services.models.free_model_rankings import (
            load_free_model_rankings,
            RANKINGS_PATH,
        )

        rankings = load_free_model_rankings(RANKINGS_PATH)
        capable = [r.model_id for r in rankings if r.supports_tools]
        return capable[:limit]
    except Exception:
        return []


class VibeProxyUnavailableError(Exception):
    """Raised when VibeProxy is not available."""

    pass


class OpenAIClient:
    """Async OpenAI client with cancellation support and multi-endpoint routing."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 90,
        api_version: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ):
        # Basic validation for custom headers
        if custom_headers is not None:
            if not isinstance(custom_headers, dict):
                raise ValueError("custom_headers must be a dictionary")
            if not all(
                isinstance(k, str) and isinstance(v, str)
                for k, v in custom_headers.items()
            ):
                raise ValueError(
                    "custom_headers must contain only string keys and values"
                )

        self.default_api_key = api_key
        self.default_base_url = base_url
        self.default_api_version = api_version
        self.timeout = timeout
        self.custom_headers = custom_headers

        # Default client
        self.client = self._create_client(
            api_key, base_url, api_version, custom_headers
        )

        # Provider-based client pool: key = provider name, value = client instance
        self._provider_clients: Dict[str, Any] = {}
        self._config = None  # Set in configure_per_model_clients / set_config

        # VibeProxy availability tracking
        self._vibeproxy_available = None
        self._vibeproxy_error = None

        self.active_requests: Dict[str, asyncio.Event] = {}
        self._provider_key_index: Dict[str, int] = {}

    def _next_provider_key(self, model: str, config=None) -> Optional[str]:
        """Return the next key from a provider pool, or None when no pool exists."""
        if not config or "/" not in model or not hasattr(config, "get_provider_api_keys"):
            return None
        provider = model.split("/", 1)[0].lower()
        keys = config.get_provider_api_keys(provider)
        if len(keys) < 2:
            return None
        idx = (self._provider_key_index.get(provider, 0) + 1) % len(keys)
        self._provider_key_index[provider] = idx
        return keys[idx]

    def _create_client(
        self,
        api_key: str,
        base_url: str,
        api_version: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        check_health: bool = True,
    ):
        """Create an OpenAI or Azure client."""
        import time

        timestamp = time.strftime("%H:%M:%S")

        # Detect provider type from URL
        from src.services.providers.provider_detector import (
            detect_provider,
            requires_kiro_token,
        )

        provider = detect_provider(base_url)
        is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url
        is_kiro = requires_kiro_token(base_url)

        # Special handling for Kiro provider
        if is_kiro:
            from src.services.providers.kiro_token_manager import get_token_manager

            logger.debug(f"[Kiro {timestamp}] CLIENT CREATION for Kiro provider")
            kiro_manager = get_token_manager()
            token = kiro_manager.get_access_token()

            if token:
                logger.debug(
                    f"[Kiro {timestamp}] Using Kiro access token (first 20 chars): {token[:20]}..."
                )
                api_key = token
            else:
                logger.error(
                    f"[Kiro {timestamp}] No Kiro token found! Authentication will FAIL."
                )
                logger.error(
                    f"[Kiro {timestamp}] Please set Kiro tokens via /api/providers/kiro/tokens endpoint"
                )
                # Proceed anyway - let it fail with clear auth error

        # Special handling for VibeProxy/CLIProxyAPI (Antigravity's local proxy on port 8317)
        elif is_vibeproxy:
            # Check VibeProxy/CLIProxyAPI availability BEFORE attempting to use it
            if check_health:
                from src.services.antigravity import check_vibeproxy_health

                available, error_msg = check_vibeproxy_health()
                if not available:
                    logger.warning(
                        f"[VibeProxy {timestamp}] VibeProxy/CLIProxyAPI is NOT available: {error_msg}"
                    )
                    self._vibeproxy_available = False
                    self._vibeproxy_error = error_msg
                else:
                    self._vibeproxy_available = True
                    self._vibeproxy_error = None

            # If caller provided an explicit API key (e.g. BIG_API_KEY=pass for CLIProxyAPI),
            # use it directly — CLIProxyAPI handles OAuth internally.
            # Only fetch Antigravity token if no key was provided.
            if api_key and api_key not in ("dummy", "your-api-key-here", ""):
                logger.debug(
                    f"[VibeProxy {timestamp}] Using provided API key for CLIProxyAPI (first 10 chars): {api_key[:10]}..."
                )
            else:
                from src.services.antigravity import get_antigravity_token

                logger.debug(
                    f"[VibeProxy {timestamp}] No explicit API key - fetching Antigravity token..."
                )
                antigravity_token = get_antigravity_token()
                if antigravity_token:
                    logger.debug(
                        f"[VibeProxy {timestamp}] Token retrieved successfully (first 20 chars): {antigravity_token[:20]}..."
                    )
                    api_key = antigravity_token
                else:
                    logger.error(
                        f"[VibeProxy {timestamp}] No Antigravity token found! Authentication will FAIL."
                    )
                    logger.error(
                        f"[VibeProxy {timestamp}] Please ensure you're logged into Antigravity IDE."
                    )

        # Diagnostic logging for special providers
        if is_vibeproxy:
            logger.debug(f"[VibeProxy {timestamp}] Creating NEW OpenAI client instance")
            logger.debug(f"[VibeProxy {timestamp}] Endpoint: {base_url}")
            logger.debug(
                f"[VibeProxy {timestamp}] Token in use (first 20 chars): {api_key[:20] if api_key else 'None'}..."
            )
            logger.debug(f"[VibeProxy {timestamp}] Custom headers: {custom_headers}")
        elif is_kiro:
            logger.debug(
                f"[Kiro {timestamp}] Creating NEW OpenAI client instance for Kiro"
            )
            logger.debug(f"[Kiro {timestamp}] Endpoint: {base_url}")
            logger.debug(f"[Kiro {timestamp}] Custom headers: {custom_headers}")

        # For Kiro (Claude API compatible), use empty API key and add Kiro token in headers
        # Kiro expects Bearer token in Authorization header, not api_key parameter
        if is_kiro and not api_key:
            # Fallback: Try to get token from environment
            api_key = os.environ.get("KIRO_ACCESS_TOKEN", "")

        # In passthrough mode api_key is None — the OpenAI SDK requires a non-empty string
        # at construction time even though it makes no network call here.  The actual per-
        # request key is injected later by endpoints.py when the request arrives.
        if not api_key:
            api_key = "passthrough-no-server-key"

        if api_version:
            return AsyncAzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                api_version=api_version,
                timeout=self.timeout,
                default_headers=custom_headers,
            )
        else:
            return AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.timeout,
                default_headers=custom_headers,
            )

    def configure_per_model_clients(self, config):
        """Store config reference for per-request routing."""
        self._config = config

    def _get_provider_client(self, provider_name: str) -> Any:
        """Get or lazily create a client for a registered provider."""
        if provider_name in self._provider_clients:
            return self._provider_clients[provider_name]
        config = self._config
        if not config:
            return None
        url = config.get_provider_endpoint(provider_name)
        key = config.get_provider_api_key(provider_name)
        if url is None:
            return None
        if key is None:
            key = self.default_api_key
        client = self._create_client(
            key, url, self.default_api_version, self.custom_headers
        )
        self._provider_clients[provider_name] = client
        return client

    def _resolve_provider_for_tier(
        self, config, tier_model: str, tier_lower: str
    ) -> str:
        """Determine the provider name for a tier's configured model."""
        if not tier_model:
            return ""
        # Check explicit tier override
        override = config.tier_provider_overrides.get(tier_lower)
        if override:
            return override
        # Infer provider prefix from model name (e.g., "qwen/foo" → "qwen")
        if "/" in tier_model:
            prefix = tier_model.split("/", 1)[0].lower()
            if prefix in config.provider_registry:
                return prefix
        return "default"

    def get_client_for_model(self, model: str, config=None) -> Any:
        """Resolve provider client for a model using the provider registry.

        Logic:
        1. Compare the model name (with/without provider prefix) against each tier's configured model
        2. If matched AND tier is enabled, route to that tier's resolved provider
        3. If tier is disabled, skip it (falls through to default)
        4. Fall back to the default client (OpenRouter)
        """
        import time

        timestamp = time.strftime("%H:%M:%S")
        if not config:
            return self.client

        def norm(name: str) -> str:
            if name and "/" in name:
                return name.split("/", 1)[1]
            return name or ""

        tier_enabled_map = {
            "big": getattr(config, "big_enabled", True),
            "middle": getattr(config, "middle_enabled", True),
            "small": getattr(config, "small_enabled", True),
        }

        raw_requested = model
        stripped_requested = norm(model)

        tiers = [
            ("BIG", config.big_model),
            ("MIDDLE", config.middle_model),
            ("SMALL", config.small_model),
        ]

        for tier_name, configured_model in tiers:
            if not configured_model:
                continue
            tier_lower = tier_name.lower()

            # Skip disabled tiers entirely
            if not tier_enabled_map.get(tier_lower, True):
                logger.debug(
                    f"[Client Selection {timestamp}] {tier_name} tier DISABLED — skipping"
                )
                continue

            stripped_config = norm(configured_model)

            # Match: raw vs raw, raw vs stripped, stripped vs stripped
            if (
                raw_requested == configured_model
                or raw_requested == stripped_config
                or stripped_requested == configured_model
                or stripped_requested == stripped_config
            ):
                provider = self._resolve_provider_for_tier(
                    config, configured_model, tier_lower
                )
                client = self._get_provider_client(provider)
                if client:
                    logger.debug(
                        f"[Client Selection {timestamp}] {tier_name}→provider '{provider}' for '{model}'"
                    )
                    return client
                logger.debug(
                    f"[Client Selection {timestamp}] {tier_name} matched but provider '{provider}' not in registry, using DEFAULT"
                )
                return self.client

        logger.debug(
            f"[Client Selection {timestamp}] No tier matched for '{model}', using DEFAULT client"
        )
        return self.client

    def _resolve_cascade_client(self, model: str, config=None) -> Any:
        """Resolve the correct client for a cascade model, supporting cross-provider fallback.

        When cascading through models from different providers (e.g., OpenRouter → NVIDIA → OpenAI),
        this method creates or retrieves the appropriate client for each provider.

        Resolution order:
        1. Check provider registry via model prefix (e.g., "nvidia/..." → PROVIDERS_nvidia_URL)
        2. Fall back to default client (OpenRouter)
        """
        if not model or not config:
            return self.client

        # Extract provider prefix from model name
        if "/" in model:
            prefix = model.split("/", 1)[0].lower()
            # Check if this provider exists in the registry
            provider_client = self._get_provider_client(prefix)
            if provider_client:
                import time

                logger.debug(
                    f"[Cascade Client {time.strftime('%H:%M:%S')}] Cross-provider: "
                    f"'{model}' → provider '{prefix}'"
                )
                return provider_client

        # LOCAL tier: check if this model is the configured local_model
        # and route to the local inference endpoint (ollama/llamafile).
        local_model = getattr(config, "local_model", None) or ""
        local_endpoint = getattr(config, "local_endpoint", None) or "http://localhost:11434/v1"
        if local_model and model == local_model:
            _local_key = "_local_client"
            if _local_key not in self._per_model_clients:
                self._per_model_clients[_local_key] = OpenAIClient(
                    api_key="ollama",  # ollama accepts any non-empty key
                    base_url=local_endpoint,
                    timeout=self.timeout,
                )
                logger.info(f"[LOCAL] Registered local inference client at {local_endpoint}")
            return self._per_model_clients[_local_key].client

        # No provider match — use default client
        return self.client

    async def create_chat_completion(
        self,
        request: Dict[str, Any],
        request_id: Optional[str] = None,
        config=None,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
        import time

        timestamp = time.strftime("%H:%M:%S")

        # Get the appropriate client based on the model
        # If api_key is provided (passthrough mode), create a temporary client
        if api_key:
            client = self._create_client(
                api_key,
                config.openai_base_url if config else self.default_base_url,
                config.azure_api_version if config else self.default_api_version,
                self.custom_headers,
            )
        else:
            client = self.get_client_for_model(request.get("model", ""), config)
            override_key = request.get("_provider_api_key")
            if override_key and hasattr(client, "base_url"):
                client = self._create_client(
                    override_key,
                    str(client.base_url),
                    config.azure_api_version if config else self.default_api_version,
                    self.custom_headers,
                    check_health=False,
                )

            model = request.get("model", "")

            # FIX: For VibeProxy requests, ensure we have a fresh token for each request
            # Check the actual client's base_url, not the default config
            base_url = str(client.base_url)
            is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url

            # Allow refresh for any tier (including small) if it points to VibeProxy/CLIProxyAPI
            if is_vibeproxy:
                # Check CLIProxyAPI/VibeProxy health BEFORE attempting to use it
                from src.services.antigravity import check_vibeproxy_health

                available, error_msg = check_vibeproxy_health()
                if not available:
                    logger.error(
                        f"[VibeProxy {timestamp}] CLIProxyAPI/VibeProxy is NOT available: {error_msg}"
                    )
                    raise VibeProxyUnavailableError(
                        f"VibeProxy is not available: {error_msg}. "
                        "Please ensure CLIProxyAPI or Antigravity IDE is running. "
                        "Alternatively, use a different model/provider."
                    )

                # When CLIProxyAPI handles auth (BIG_API_KEY is set), skip token refresh.
                # CLIProxyAPI manages OAuth tokens internally from ~/.cli-proxy-api/ credentials.
                big_api_key = config.big_api_key if config else None
                if big_api_key and big_api_key not in (
                    "dummy",
                    "your-api-key-here",
                    "",
                ):
                    logger.debug(
                        f"[VibeProxy {timestamp}] CLIProxyAPI mode - using provided API key, skipping token refresh"
                    )
                else:
                    # Legacy: direct Antigravity token refresh from macOS SQLite DB
                    from src.services.antigravity import get_antigravity_auth

                    logger.debug(
                        f"[VibeProxy {timestamp}] Refreshing client with fresh Antigravity token for request"
                    )
                    auth = get_antigravity_auth()
                    fresh_token = auth.get_token(force_refresh=True)

                    if fresh_token:
                        logger.debug(
                            f"[VibeProxy {timestamp}] Creating new client with fresh token (first 20 chars): {fresh_token[:20]}..."
                        )
                        client = self._create_client(
                            fresh_token,
                            base_url,
                            config.azure_api_version
                            if config
                            else self.default_api_version,
                            self.custom_headers,
                            check_health=False,
                        )
                    else:
                        logger.error(
                            f"[VibeProxy {timestamp}] Failed to retrieve fresh token! Using cached client (may fail)"
                        )

        # Strip provider prefix from model name for APIs that don't support it
        # (e.g., opencode.ai expects "qwen3.6-plus", not "opencode_go/qwen3.6-plus")
        if client and hasattr(client, "base_url"):
            raw_model = request.get("model", "")
            cleaned_model = _maybe_strip_model_prefix(raw_model, str(client.base_url))
            if cleaned_model != raw_model:
                request = {**request, "model": cleaned_model}

        # Inject OpenRouter native fallback (models array + require_parameters) when enabled.
        # Uses _build_or_models_list() to exclude any models with OPEN circuit breakers
        # so we don't waste OR's routing budget evaluating known-dead endpoints.
        if config and "openrouter_native" in (config.fallback_methods or set()):
            base_url = str(client.base_url)
            if "openrouter.ai" in base_url or "8787" in base_url:
                fallback_models = getattr(config, "openrouter_fallback_models", [])
                primary = request.get("model", "")
                if fallback_models and primary not in ("", None):
                    or_models = _build_or_models_list(primary, fallback_models)
                    request = {
                        **request,
                        "model": or_models[0],
                        "extra_body": {
                            **request.get("extra_body", {}),
                            "models": or_models,
                            "provider": {
                                **request.get("extra_body", {}).get("provider", {}),
                                "require_parameters": True,
                                "sort": {"by": "throughput", "partition": "none"},
                            },
                        },
                    }

        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            # Strip internal proxy metadata keys (prefixed with _) before forwarding.
            # Keys like _session_fingerprint, _original_model, _force_tier are proxy
            # annotations that the upstream OpenAI SDK rejects as unknown kwargs.
            api_request = {k: v for k, v in request.items() if not k.startswith("_")}

            # Create task that can be cancelled
            completion_task = asyncio.create_task(
                client.chat.completions.create(**api_request)
            )

            if request_id:
                # Wait for either completion or cancellation
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [completion_task, cancel_task], return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # Check if request was cancelled
                if cancel_task in done:
                    completion_task.cancel()
                    raise HTTPException(
                        status_code=499, detail="Request cancelled by client"
                    )

                completion = await completion_task
            else:
                completion = await completion_task

            # Convert to dict format that matches the original interface
            return completion.model_dump()

        except AuthenticationError as e:
            raise HTTPException(
                status_code=401, detail=self.classify_openai_error(str(e))
            )
        except RateLimitError as e:
            raise HTTPException(
                status_code=429, detail=self.classify_openai_error(str(e))
            )
        except BadRequestError as e:
            raise HTTPException(
                status_code=400, detail=self.classify_openai_error(str(e))
            )
        except APIError as e:
            status_code = getattr(e, "status_code", 500)
            raise HTTPException(
                status_code=status_code, detail=self.classify_openai_error(str(e))
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]

    async def create_chat_completion_stream(
        self,
        request: Dict[str, Any],
        request_id: Optional[str] = None,
        config=None,
        api_key: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Send streaming chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
        import time

        timestamp = time.strftime("%H:%M:%S")

        # Get the appropriate client based on the model
        # If api_key is provided (passthrough mode), create a temporary client
        if api_key:
            client = self._create_client(
                api_key,
                config.openai_base_url if config else self.default_base_url,
                config.azure_api_version if config else self.default_api_version,
                self.custom_headers,
            )
        else:
            client = self.get_client_for_model(request.get("model", ""), config)

            model = request.get("model", "")

            # Determine if this is SMALL tier request (use getattr for safety)
            small_client = getattr(self, "small_client", None)
            is_small_tier = config and small_client and model == config.small_model

            # FIX: For VibeProxy requests, ensure we have a fresh token for each request
            # Check the actual client's base_url, not the default config
            base_url = str(client.base_url)
            is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url

            # Allow refresh for any tier (including small) if it points to VibeProxy/CLIProxyAPI
            if is_vibeproxy:
                # When CLIProxyAPI handles auth, skip token refresh
                big_api_key = config.big_api_key if config else None
                if big_api_key and big_api_key not in (
                    "dummy",
                    "your-api-key-here",
                    "",
                ):
                    logger.debug(
                        f"[VibeProxy {timestamp}] CLIProxyAPI mode - using provided API key for streaming, skipping token refresh"
                    )
                else:
                    logger.debug(
                        f"[VibeProxy {timestamp}] Refreshing client with fresh Antigravity token for streaming request"
                    )
                    from src.services.antigravity import get_antigravity_auth

                    auth = get_antigravity_auth()
                    fresh_token = auth.get_token(force_refresh=True)
                    if fresh_token:
                        logger.debug(
                            f"[VibeProxy {timestamp}] Creating new client with fresh token (first 20 chars): {fresh_token[:20]}..."
                        )
                        client = self._create_client(
                            fresh_token,
                            base_url,
                            config.azure_api_version
                            if config
                            else self.default_api_version,
                            self.custom_headers,
                        )
                    else:
                        logger.error(
                            f"[VibeProxy {timestamp}] Failed to retrieve fresh token! Using cached client (may fail)"
                        )
            elif is_small_tier:
                logger.debug(
                    f"[Client Selection {timestamp}] SMALL tier streaming - routing to {config.small_endpoint} (not VibeProxy)"
                )

        # Strip provider prefix from model name for APIs that don't support it
        if client and hasattr(client, "base_url"):
            raw_model = request.get("model", "")
            cleaned_model = _maybe_strip_model_prefix(raw_model, str(client.base_url))
            if cleaned_model != raw_model:
                request = {**request, "model": cleaned_model}

        # Inject OpenRouter native fallback for streaming requests
        # (same CB-filtered model list as non-streaming path)
        if config and "openrouter_native" in (config.fallback_methods or set()):
            base_url = str(client.base_url)
            if "openrouter.ai" in base_url or "8787" in base_url:
                fallback_models = getattr(config, "openrouter_fallback_models", [])
                primary = request.get("model", "")
                if fallback_models and primary not in ("", None):
                    or_models = _build_or_models_list(primary, fallback_models)
                    request = {
                        **request,
                        "model": or_models[0],
                        "extra_body": {
                            **request.get("extra_body", {}),
                            "models": or_models,
                            "provider": {
                                **request.get("extra_body", {}).get("provider", {}),
                                "require_parameters": True,
                                "sort": {"by": "throughput", "partition": "none"},
                            },
                        },
                    }

        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            # Ensure stream options are set for usage tracking
            if "stream_options" not in request:
                request["stream_options"] = {}
            request["stream_options"]["include_usage"] = True
            # stream=True is already in the request dict from the converter;
            # the SDK's create() accepts it via **request unpacking.
            request["stream"] = True

            # Strip internal proxy metadata keys before forwarding to SDK.
            api_request = {k: v for k, v in request.items() if not k.startswith("_")}

            # Create the streaming completion
            streaming_completion = await client.chat.completions.create(**api_request)

            async for chunk in streaming_completion:
                # Check for cancellation before yielding each chunk
                if request_id and request_id in self.active_requests:
                    if self.active_requests[request_id].is_set():
                        raise HTTPException(
                            status_code=499, detail="Request cancelled by client"
                        )

                # Convert chunk to SSE format matching original HTTP client format
                chunk_dict = chunk.model_dump()
                chunk_json = json.dumps(chunk_dict, ensure_ascii=False)
                yield f"data: {chunk_json}"

            # Signal end of stream
            yield "data: [DONE]"

        except AuthenticationError as e:
            raise HTTPException(
                status_code=401, detail=self.classify_openai_error(str(e))
            )
        except RateLimitError as e:
            raise HTTPException(
                status_code=429, detail=self.classify_openai_error(str(e))
            )
        except BadRequestError as e:
            raise HTTPException(
                status_code=400, detail=self.classify_openai_error(str(e))
            )
        except APIError as e:
            status_code = getattr(e, "status_code", 500)
            raise HTTPException(
                status_code=status_code, detail=self.classify_openai_error(str(e))
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]

    def classify_openai_error(self, error_detail: Any) -> str:
        """Provide specific error guidance for common API issues."""
        error_str = str(error_detail).lower()

        # Debug logging for error classification
        logger.debug(f"Classifying error: {error_str}")

        # VibeProxy/Gemini-specific errors
        if (
            "gemini code assist license" in error_str
            or "subscription_required" in error_str
        ):
            return "Gemini Code Assist license required. Your Google Cloud Project needs a Gemini Code Assist license. Contact your administrator or use a different model/provider."

        if "auth_unavailable" in error_str or "no auth available" in error_str:
            return "VibeProxy authentication unavailable. Please ensure Antigravity IDE is running and you're logged in. Try restarting Antigravity IDE."

        if "permission_denied" in error_str and (
            "googleapis" in error_str or "cloudaicompanion" in error_str
        ):
            return "Google Cloud permission denied. Check your Gemini/Antigravity credentials and project permissions."

        # Region/country restrictions
        if (
            "unsupported_country_region_territory" in error_str
            or "country, region, or territory not supported" in error_str
        ):
            return "API is not available in your region. Consider using a VPN or different provider."

        # API key issues
        if (
            "invalid_api_key" in error_str
            or "unauthorized" in error_str
            or "user not found" in error_str
        ):
            return "Invalid API key or user not found. Please check your OPENAI_API_KEY configuration and ensure your provider account is active. Note: OPENAI_API_KEY is used for any provider (OpenRouter, OpenAI, Azure, etc.)"

        # Rate limiting
        if "rate_limit" in error_str or "quota" in error_str:
            return "Rate limit exceeded. Please wait and try again, or upgrade your API plan with your provider."

        # Model not found
        if "model" in error_str and (
            "not found" in error_str or "does not exist" in error_str
        ):
            return "Model not found. Please check your BIG_MODEL and SMALL_MODEL configuration."

        # Billing issues
        if "billing" in error_str or "payment" in error_str:
            return "Billing issue. Please check your provider account billing status."

        # Default: return original message
        return str(error_detail)

    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request by request_id."""
        if request_id in self.active_requests:
            self.active_requests[request_id].set()
            return True
        return False

    async def create_chat_completion_with_cascade(
        self,
        request: Dict[str, Any],
        tier: str,
        config=None,
        request_id: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        """
        Chat completion with cascade fallback on provider errors.

        Args:
            request: OpenAI request dictionary
            tier: Model tier (big, middle, small)
            config: Config object with cascade settings
            request_id: Optional request ID for cancellation
            api_key: Optional per-request API key

        Returns:
            ChatCompletion from first successful model
        """
        import ssl
        import httpx
        import time
        from src.api.websocket_logs import log_cascade
        from src.services.usage.usage_tracker import usage_tracker

        timestamp = time.strftime("%H:%M:%S")

        if not config or not config.model_cascade:
            # Cascade disabled - use normal call
            return await self.create_chat_completion(
                request, request_id, config, api_key
            )

        # Build models to try: primary → static cascade → dynamic rankings (tool-capable free models)
        primary_model = request.get("model", "")
        cascade_models = request.get("_model_scan_cascade") or config.get_cascade_for_tier(tier)
        dynamic_models = _get_dynamic_fallback_models(limit=8)

        # Tool-call-aware cascade: prepend TOOLCALL_MODELS when request has tools
        is_tool_request = bool(request.get("tools")) or bool(request.get("tool_choice"))
        toolcall_models = []
        toolcall_max_retries = 2
        if is_tool_request:
            # Profile overlay wins over global config (Option C-slim per-request override).
            _profile_tc = request.get("_profile_toolcall_models")
            if _profile_tc:
                toolcall_models = list(_profile_tc)
            elif config:
                toolcall_models = getattr(config, "toolcall_models", []) or []
            if config:
                toolcall_max_retries = getattr(config, "toolcall_max_retries", 2) or 2
            if toolcall_models:
                logger.debug(
                    f"[CASCADE] Tool-call request — prepending {len(toolcall_models)} tool-capable models"
                )

        # Estimate input tokens for context filtering
        import json

        estimated_input_chars = len(json.dumps(request.get("messages", []))) + len(
            json.dumps(request.get("tools", []))
        )
        estimated_input_tokens = estimated_input_chars // 4
        required_output = 4096  # default safe assumption

        # Deduplicate while preserving priority order
        # Priority: primary → tool-call models → tier cascade → dynamic rankings
        seen: set = set()
        raw_models_to_try: list = []
        for m in [primary_model] + toolcall_models + cascade_models + dynamic_models:
            if m and m not in seen:
                seen.add(m)
                raw_models_to_try.append(m)

        # Context Filter & Rate Limit Sorting
        from src.services.usage.model_limits import get_model_limits
        from src.services.usage.rate_limiter import rate_limiter

        valid_models = []
        for m in raw_models_to_try:
            ctx_limit, _ = get_model_limits(m)
            effective_context = int(ctx_limit * 0.9)
            if effective_context >= estimated_input_tokens + required_output:
                valid_models.append(m)
            else:
                logger.debug(
                    f"[CASCADE] Skipping {m} (context limit {ctx_limit} too small)"
                )

        if not valid_models:
            # If all models are filtered out, throw a clear 400 error immediately
            max_limit = (
                max([get_model_limits(m)[0] for m in raw_models_to_try])
                if raw_models_to_try
                else 0
            )
            raise HTTPException(
                status_code=400,
                detail=f"⚠️ Proxy System Warning: Your context size (~{estimated_input_tokens} tokens) exceeds the maximum allowed by available fallback models ({max_limit} tokens). Please clear your conversation history.",
            )

        # Separate primary model to keep it first, sort the rest by available quota
        primary_valid = (
            valid_models[0]
            if valid_models and valid_models[0] == primary_model
            else None
        )
        fallbacks = valid_models[1:] if primary_valid else valid_models

        # Fire off background limit fetchers for unknown models
        import asyncio

        for m in fallbacks:
            if rate_limiter.is_unknown(m):
                try:
                    tmp_client = self._resolve_cascade_client(m, config)
                    base_url = (
                        str(tmp_client.client.base_url)
                        if hasattr(tmp_client, "client")
                        and hasattr(tmp_client.client, "base_url")
                        else ""
                    )
                    m_api_key = (
                        tmp_client.client.api_key
                        if hasattr(tmp_client, "client")
                        and hasattr(tmp_client.client, "api_key")
                        else api_key
                    )
                    if base_url and m_api_key:
                        asyncio.create_task(
                            rate_limiter.fetch_limits_bg(m, m_api_key, base_url)
                        )
                except Exception:
                    pass

        # Sort fallbacks by available quota (descending)
        fallbacks.sort(
            key=lambda m: rate_limiter.get_available_quota_score(m), reverse=True
        )

        models_to_try = ([primary_valid] if primary_valid else []) + fallbacks

        timestamp = time.strftime("%H:%M:%S")
        last_error = None

        # Track retry counts per model for soft failures
        retry_counts = {}
        MAX_RETRIES_BEFORE_CASCADE = 5  # Soft errors need 5 failures
        # Use lower retry count for tool-call cascades to fail-fast to next capable model
        if is_tool_request and toolcall_max_retries:
            MAX_RETRIES_BEFORE_CASCADE = toolcall_max_retries

        model_idx = 0
        while model_idx < len(models_to_try):
            model = models_to_try[model_idx]
            if not model:
                model_idx += 1
                continue

            # Skip models whose circuit is OPEN (tripped by recent failures)
            cb = _get_circuit_breaker(model)
            if cb.is_open:
                import time as _time

                logger.debug(
                    f"[CASCADE {_time.strftime('%H:%M:%S')}] ⚡ Circuit OPEN for {model} — skipping"
                )
                model_idx += 1
                continue

            # Optional preemptive switch when local UTC-day request count is at/over threshold.
            daily_limit = (
                getattr(config, "model_cascade_daily_limit", 0) if config else 0
            )
            if daily_limit and usage_tracker.enabled:
                daily_count = usage_tracker.get_daily_model_request_count(model)
                if daily_count >= daily_limit:
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    logger.debug(
                        f"[CASCADE] Skipping {model} (daily limit {daily_count}/{daily_limit})"
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="daily_limit_threshold",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts.get(model, 0),
                    )
                    model_idx += 1
                    continue

            # Initialize retry count for this model
            if model not in retry_counts:
                retry_counts[model] = 0

            try:
                # Update request with current model
                current_request = {**request, "model": model}

                if model_idx > 0 and retry_counts[model] == 0:
                    logger.info(
                        f"[CASCADE] ↷ trying fallback: {model}"
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="fallback_attempt",
                        from_model=raw_models_to_try[model_idx - 1]
                        if model_idx > 0
                        else primary_model,
                        to_model=model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )

                # Record request to immediately decrement local sliding window quotas
                rate_limiter.record_request(model, estimated_input_tokens)
                result = await self.create_chat_completion(
                    current_request, request_id, config, api_key=None
                )

                # Record success — also check structural validity (parse_ok).
                # A HTTP 200 with empty or truncated output still penalises the model
                # via record_soft_failure so chronically-broken models accumulate toward
                # their circuit-open threshold without being treated as total failures.
                cb = _get_circuit_breaker(model)
                cb._record_success()
                cb.record_parse_ok(result)

                # Tool-call validation: if request had tools and tool_choice was
                # 'required' or 'auto', verify the response actually contains tool_calls.
                # Missing tool_calls = model can't do tool calling = cascade to next.
                if is_tool_request:
                    choices = result.get("choices", [])
                    has_tool_response = False
                    if choices:
                        msg = choices[0].get("message", {}) or {}
                        has_tool_response = bool(msg.get("tool_calls"))
                    tool_choice = request.get("tool_choice", "auto")
                    if tool_choice == "required" and not has_tool_response:
                        logger.debug(
                            f"[CASCADE] {model} returned no tool_calls despite tool_choice=required"
                        )
                        cb.record_soft_failure()
                        model_idx += 1
                        continue

                if model_idx > 0:
                    logger.info(f"[CASCADE] Fallback used: {model}")
                    log_cascade(
                        model=model,
                        action="success",
                        tier=tier,
                        reason="fallback_success",
                        request_id=request_id,
                    )

                return result

            except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
                # SSL/Cert errors: switch IMMEDIATELY (hard failure) + trip the circuit
                _get_circuit_breaker(model)._record_failure(e)
                logger.debug(
                    f"[CASCADE] SSL/Cert error on {model} - switching immediately: {e}"
                )
                next_model = (
                    models_to_try[model_idx + 1]
                    if model_idx + 1 < len(models_to_try)
                    else None
                )
                log_cascade(
                    model=model,
                    action="switch",
                    tier=tier,
                    reason="ssl_error",
                    from_model=model,
                    to_model=next_model,
                    request_id=request_id,
                    error=str(e),
                )
                last_error = e
                model_idx += 1  # Move to next model immediately
                continue

            except httpx.ConnectError as e:
                retry_counts[model] += 1
                logger.debug(
                    f"[CASCADE] Connection error on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE})"
                )
                log_cascade(
                    model=model,
                    action="retry",
                    tier=tier,
                    reason="connect_error",
                    request_id=request_id,
                    retry_count=retry_counts[model],
                    error=str(e),
                )
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    logger.debug(
                        f"[CASCADE] Max retries reached for {model}, switching to next"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="max_connect_retries",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                continue

            except httpx.TimeoutException as e:
                retry_counts[model] += 1
                logger.debug(
                    f"[CASCADE] Timeout on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE})"
                )
                log_cascade(
                    model=model,
                    action="retry",
                    tier=tier,
                    reason="timeout_error",
                    request_id=request_id,
                    retry_count=retry_counts[model],
                    error=str(e),
                )
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    logger.debug(
                        f"[CASCADE] Max retries reached for {model}, switching to next"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="max_timeout_retries",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                continue

            except RateLimitError as e:
                error_str = str(e).lower()
                # Alibaba's burst ramp-up detector: "rate increased too quickly" fires on
                # velocity spikes from cold starts.  Retrying the same provider doesn't help
                # since the window hasn't reset — skip straight to a different provider.
                is_alibaba_rampup = (
                    "rate increased too quickly" in error_str
                    or "scale requests more smoothly" in error_str
                )
                if is_alibaba_rampup:
                    logger.debug(
                        f"[CASCADE] Alibaba ramp-up limit on {model} — cascading immediately to next provider"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="alibaba_rampup_cascade",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        error=str(e),
                    )
                    last_error = e
                    model_idx += 1
                    continue

                retry_counts[model] += 1
                import random as _random
                import time as _time

                # Read X-RateLimit-Reset from response headers when available.
                # OpenRouter free models return this with the exact UTC reset timestamp.
                # Using it avoids burning quota on blind retries during the window.
                header_backoff: Optional[float] = None
                try:
                    resp_headers = getattr(getattr(e, "__cause__", None), "response", None)
                    if resp_headers is None:
                        resp_headers = getattr(e, "response", None)
                    if resp_headers is not None:
                        # Passively feed the live quota cache from error-response headers
                        # (provider rate-limit info on 429/5xx -> rotation drain decisions). F06.
                        try:
                            from src.core.quota_live import get_quota_cache
                            _prov = model.split("/")[0] if "/" in model else model
                            get_quota_cache().record_headers(_prov, dict(resp_headers.headers))
                        except Exception:
                            pass
                        # X-RateLimit-Reset can be epoch seconds or seconds-until-reset
                        reset_raw = resp_headers.headers.get("X-RateLimit-Reset") or \
                                    resp_headers.headers.get("x-ratelimit-reset") or \
                                    resp_headers.headers.get("Retry-After")
                        if reset_raw:
                            reset_val = float(reset_raw)
                            now = _time.time()
                            # If value looks like a unix timestamp (>1e9), convert to delta
                            if reset_val > 1_000_000_000:
                                header_backoff = max(1.0, reset_val - now + 1.0)
                            else:
                                header_backoff = max(1.0, reset_val + 1.0)
                            logger.debug(
                                f"[CASCADE] X-RateLimit-Reset on {model}: {reset_raw} → backoff {header_backoff:.1f}s"
                            )
                except Exception:
                    pass

                if header_backoff is not None:
                    backoff = min(header_backoff, 120.0)  # cap at 2 min
                else:
                    backoff = min(
                        30.0, (2 ** min(retry_counts[model], 4)) * _random.uniform(0.8, 1.2)
                    )
                logger.debug(
                    f"[CASCADE] Rate limit on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}), backoff {backoff:.1f}s"
                )
                log_cascade(
                    model=model,
                    action="retry",
                    tier=tier,
                    reason="rate_limit",
                    request_id=request_id,
                    retry_count=retry_counts[model],
                    error=str(e),
                )
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    logger.debug(
                        f"[CASCADE] Max retries reached for {model}, switching to next"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="max_rate_limit_retries",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                await asyncio.sleep(backoff)
                continue

            except (BadRequestError, AuthenticationError) as e:
                # 400/401 errors: switch IMMEDIATELY (model not available or auth failed) + trip circuit
                _get_circuit_breaker(model)._record_failure(e)
                error_str = str(e).lower()
                # If this looks like a context-length violation, refresh the limit so
                # the cascade's context filter uses the correct value on the next attempt.
                if any(
                    p in error_str
                    for p in (
                        "context_length",
                        "maximum context",
                        "too long",
                        "context window",
                        "prompt is too long",
                    )
                ):
                    try:
                        from src.services.usage.model_limits import (
                            refresh_model_limit_from_api,
                        )

                        asyncio.create_task(
                            refresh_model_limit_from_api(model, api_key)
                        )
                    except Exception:
                        pass
                    logger.debug(
                        f"[CASCADE {timestamp}] 🚫 Request error on {model} - switching immediately: {e}"
                    )
                next_model = (
                    models_to_try[model_idx + 1]
                    if model_idx + 1 < len(models_to_try)
                    else None
                )
                log_cascade(
                    model=model,
                    action="switch",
                    tier=tier,
                    reason="request_error",
                    from_model=model,
                    to_model=next_model,
                    request_id=request_id,
                    error=str(e),
                )
                last_error = e
                model_idx += 1  # Move to next model immediately
                continue

            except APIError as e:
                # 502, 503, 504: retry with count
                if hasattr(e, "status_code") and e.status_code in [502, 503, 504]:
                    retry_counts[model] += 1
                    logger.debug(
                        f"[CASCADE] Server error {e.status_code} on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE})"
                    )
                    log_cascade(
                        model=model,
                        action="retry",
                        tier=tier,
                        reason=f"server_error_{e.status_code}",
                        request_id=request_id,
                        retry_count=retry_counts[model],
                        error=str(e),
                    )
                    last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    logger.debug(
                        f"[CASCADE] Max retries reached for {model}, switching to next"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason=f"max_server_error_{e.status_code}_retries",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                    continue
                # Other API errors should not cascade
                raise

            except HTTPException as e:
                # create_chat_completion wraps SDK exceptions as HTTPException.
                # Map back to cascade behavior by status code so the cascade can
                # still try fallback models rather than propagating the error immediately.
                code = e.status_code
                if code == 429:
                    rotated_key = self._next_provider_key(model, config)
                    if rotated_key and not current_request.get("_provider_api_key"):
                        logger.info(f"[CASCADE] {model} → 429, rotating provider key once")
                        current_request["_provider_api_key"] = rotated_key
                        retry_counts[model] += 1
                        continue
                    retry_counts[model] += 1
                    logger.info(f"[CASCADE] {model} → 429 rate-limit, cascading to next")
                    last_error = e
                    model_idx += 1
                    continue
                elif code in (400, 401, 403):
                    _get_circuit_breaker(model)._record_failure(e)
                    logger.info(f"[CASCADE] {model} → {code} auth/bad-request, cascading to next")
                    last_error = e
                    model_idx += 1
                    continue
                elif code in (500, 502, 503, 504):
                    # Cap server-error retries at 2 (not MAX_RETRIES_BEFORE_CASCADE=5):
                    # 5xx means the upstream is overloaded — retrying the same model 5
                    # times wastes 8+ seconds before cascading. Cascade fast, fall back fast.
                    _SERVER_ERR_RETRIES = 2
                    retry_counts[model] += 1
                    logger.info(f"[CASCADE] {model} → {code} server error ({retry_counts[model]}/{_SERVER_ERR_RETRIES})")
                    last_error = e
                    if retry_counts[model] >= _SERVER_ERR_RETRIES:
                        model_idx += 1
                    continue
                else:
                    raise

        # All models failed — persist circuit breaker state so the next session
        # skips known-dead models immediately rather than re-burning quota.
        try:
            from src.core.circuit_breaker import get_circuit_breaker_registry

            get_circuit_breaker_registry().save_all()
        except Exception:
            pass

        logger.warning(f"[CASCADE] All models exhausted for {primary_model}")
        log_cascade(
            model=primary_model,
            action="exhausted",
            tier=tier,
            reason="all_models_failed",
            request_id=request_id,
            error=str(last_error) if last_error else None,
        )
        if last_error:
            raise last_error
        # No last_error means every model was skipped before an attempt (e.g. all circuit
        # breakers open). The OpenAI SDK's APIError requires an httpx.Request, so constructing
        # it with only a message raised TypeError and masked the real cause as a generic 500.
        # Surface a clear 503 instead (the file's established HTTPException pattern).
        raise HTTPException(
            status_code=503,
            detail="All cascade models are currently unavailable (every model was skipped, "
            "likely due to open circuit breakers from recent failures). Try again shortly.",
        )

    async def create_chat_completion_stream_with_cascade(
        self,
        request: Dict[str, Any],
        tier: str,
        config=None,
        request_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming chat completion with cascade fallback on provider errors.

        Args:
            request: OpenAI request dictionary
            tier: Model tier (big, middle, small)
            config: Config object with cascade settings
            request_id: Optional request ID for cancellation
            api_key: Optional per-request API key

        Yields:
            OpenAI-format SSE lines ("data: ...")
        """
        import ssl
        import httpx
        import time
        from src.api.websocket_logs import log_cascade
        from src.services.usage.usage_tracker import usage_tracker

        timestamp = time.strftime("%H:%M:%S")

        if not config or not config.model_cascade:
            async for line in self.create_chat_completion_stream(
                request, request_id, config, api_key
            ):
                yield line
            return

        primary_model = request.get("model", "")
        cascade_models = request.get("_model_scan_cascade") or config.get_cascade_for_tier(tier)
        dynamic_models = _get_dynamic_fallback_models(limit=8)

        # LOCAL tier: append ollama/llamafile as the final fallback when LOCAL_ENABLED=true.
        # This is the 4th cascade layer — only used when all remote tiers have open CBs.
        local_model = getattr(config, "local_model", None) or ""
        local_endpoint = getattr(config, "local_endpoint", None) or "http://localhost:11434/v1"
        local_enabled = getattr(config, "local_enabled", False)
        if local_enabled and local_model and local_model not in cascade_models:
            cascade_models = list(cascade_models) + [local_model]
            logger.debug(f"[CASCADE] LOCAL tier appended: {local_model} @ {local_endpoint}")

        # Tool-call-aware cascade: prepend TOOLCALL_MODELS when request has tools
        is_tool_request = bool(request.get("tools")) or bool(request.get("tool_choice"))
        toolcall_models = []
        toolcall_max_retries = 2
        if is_tool_request:
            # Profile overlay wins over global config (Option C-slim per-request override).
            _profile_tc = request.get("_profile_toolcall_models")
            if _profile_tc:
                toolcall_models = list(_profile_tc)
            elif config:
                toolcall_models = getattr(config, "toolcall_models", []) or []
            if config:
                toolcall_max_retries = getattr(config, "toolcall_max_retries", 2) or 2
            if toolcall_models:
                logger.debug(
                    f"[CASCADE] Tool-call streaming request — prepending {len(toolcall_models)} tool-capable models"
                )

        # Estimate input tokens for context filtering
        import json

        estimated_input_chars = len(json.dumps(request.get("messages", []))) + len(
            json.dumps(request.get("tools", []))
        )
        estimated_input_tokens = estimated_input_chars // 4
        required_output = 4096  # default safe assumption

        # Deduplicate while preserving priority order
        # Priority: primary → tool-call models → tier cascade → dynamic rankings
        timestamp = time.strftime("%H:%M:%S")
        raw_models_to_try = []
        seen_stream: set = set()
        for model_name in (
            [primary_model] + toolcall_models + cascade_models + dynamic_models
        ):
            if model_name and model_name not in seen_stream:
                seen_stream.add(model_name)
                raw_models_to_try.append(model_name)

        # Context Filter & Rate Limit Sorting
        from src.services.usage.model_limits import get_model_limits
        from src.services.usage.rate_limiter import rate_limiter

        valid_models = []
        for m in raw_models_to_try:
            ctx_limit, _ = get_model_limits(m)
            effective_context = int(ctx_limit * 0.9)
            if effective_context >= estimated_input_tokens + required_output:
                valid_models.append(m)
            else:
                logger.debug(
                    f"[CASCADE] Skipping {m} (context limit {ctx_limit} too small)"
                )

        if not valid_models:
            max_limit = (
                max([get_model_limits(m)[0] for m in raw_models_to_try])
                if raw_models_to_try
                else 0
            )
            raise HTTPException(
                status_code=400,
                detail=f"⚠️ Proxy System Warning: Your context size (~{estimated_input_tokens} tokens) exceeds the maximum allowed by available fallback models ({max_limit} tokens). Please clear your conversation history.",
            )

        # Separate primary model to keep it first, sort the rest by available quota
        primary_valid = (
            valid_models[0]
            if valid_models and valid_models[0] == primary_model
            else None
        )
        fallbacks = valid_models[1:] if primary_valid else valid_models

        # Fire off background limit fetchers for unknown models
        import asyncio

        for m in fallbacks:
            if rate_limiter.is_unknown(m):
                try:
                    tmp_client = self._resolve_cascade_client(m, config)
                    base_url = (
                        str(tmp_client.client.base_url)
                        if hasattr(tmp_client, "client")
                        and hasattr(tmp_client.client, "base_url")
                        else ""
                    )
                    m_api_key = (
                        tmp_client.client.api_key
                        if hasattr(tmp_client, "client")
                        and hasattr(tmp_client.client, "api_key")
                        else api_key
                    )
                    if base_url and m_api_key:
                        asyncio.create_task(
                            rate_limiter.fetch_limits_bg(m, m_api_key, base_url)
                        )
                except Exception:
                    pass

        fallbacks.sort(
            key=lambda m: rate_limiter.get_available_quota_score(m), reverse=True
        )
        models_to_try = ([primary_valid] if primary_valid else []) + fallbacks

        last_error = None
        retry_counts = {}
        max_retries_before_cascade = 5
        # Use lower retry count for tool-call cascades to fail-fast
        if is_tool_request and toolcall_max_retries:
            max_retries_before_cascade = toolcall_max_retries

        model_idx = 0
        while model_idx < len(models_to_try):
            model = models_to_try[model_idx]
            if model not in retry_counts:
                retry_counts[model] = 0

            # Skip models with OPEN circuit breakers (same as non-streaming cascade)
            _cb_stream = _get_circuit_breaker(model)
            if _cb_stream.is_open:
                import time as _t

                logger.debug(
                    f"[CASCADE {_t.strftime('%H:%M:%S')}] ⚡ Circuit OPEN for {model} (stream) — skipping"
                )
                model_idx += 1
                continue

            daily_limit = (
                getattr(config, "model_cascade_daily_limit", 0) if config else 0
            )
            if daily_limit and usage_tracker.enabled:
                daily_count = usage_tracker.get_daily_model_request_count(model)
                if daily_count >= daily_limit:
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    logger.debug(
                        f"[CASCADE] Skipping {model} (stream) - daily limit {daily_count}/{daily_limit}"
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="daily_limit_threshold_stream",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                    continue

            current_request = {**request, "model": model}
            emitted_any_chunk = False
            # Track stream-level parse signals for soft failure detection
            _stream_finish_reason: Optional[str] = None
            _stream_had_tool_calls = False
            _stream_had_content = False

            try:
                if model_idx > 0 and retry_counts[model] == 0:
                    logger.info(f"[CASCADE] ↷ stream fallback: {model}")
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="fallback_attempt_stream",
                        from_model=raw_models_to_try[model_idx - 1]
                        if model_idx > 0
                        else primary_model,
                        to_model=model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )

                # Record request to immediately decrement local sliding window quotas
                rate_limiter.record_request(model, estimated_input_tokens)

                # Mid-stream output budget (MID_STREAM_OUTPUT_BUDGET env var).
                # When the expensive model produces more than N output tokens,
                # inject a synthetic length-stop and record a tier override so the
                # next continuation request from this session routes to a cheaper tier.
                _mid_budget = int(os.environ.get("MID_STREAM_OUTPUT_BUDGET", "0"))
                _mid_out_chars = 0
                _mid_stream_stopped = False
                _session_fp = request.get("_session_fingerprint", "")

                stream = self.create_chat_completion_stream(
                    current_request, request_id, config, api_key=None
                )
                async for line in stream:
                    emitted_any_chunk = True
                    # Sniff last chunk for parse_ok signals and output token tracking
                    if line.startswith("data: {"):
                        try:
                            chunk = json.loads(line[6:])
                            choices = chunk.get("choices", [])
                            if choices:
                                c = choices[0]
                                if c.get("finish_reason"):
                                    _stream_finish_reason = c["finish_reason"]
                                delta = c.get("delta", {}) or {}
                                if delta.get("tool_calls"):
                                    _stream_had_tool_calls = True
                                content = delta.get("content") or ""
                                if content:
                                    _stream_had_content = True
                                    _mid_out_chars += len(content)

                                    # Mid-stream budget check: stop expensive model,
                                    # signal next turn to use cheaper tier.
                                    if _mid_budget > 0 and _mid_out_chars > _mid_budget * 4:
                                        _mid_stream_stopped = True
                                        # Inject a synthetic length-stop so the format
                                        # converter emits stop_reason: max_tokens to Claude Code
                                        stop_chunk = json.dumps({
                                            "choices": [{
                                                "index": 0,
                                                "delta": {},
                                                "finish_reason": "length",
                                            }]
                                        })
                                        yield f"data: {stop_chunk}\n\n"
                                        yield "data: [DONE]\n\n"
                                        # Record session override for next request
                                        if _session_fp:
                                            next_tier = {
                                                "big": "middle", "middle": "small"
                                            }.get(tier, "small")
                                            set_mid_stream_tier_override(_session_fp, next_tier)
                                        logger.info(
                                            f"[CASCADE] Mid-stream budget ({_mid_budget} tokens) "
                                            f"reached on {model} — stopping; next turn → {tier} cheaper tier"
                                        )
                                        log_cascade(
                                            model=model,
                                            action="mid_stream_stop",
                                            tier=tier,
                                            reason=f"mid_stream_output_budget_{_mid_budget}",
                                            request_id=request_id,
                                        )
                                        break
                        except Exception:
                            pass
                    if _mid_stream_stopped:
                        break
                    yield line

                # Record parse result for this model's circuit breaker
                _get_circuit_breaker(model)._record_success()
                _get_circuit_breaker(model).record_stream_finish(
                    _stream_finish_reason, _stream_had_tool_calls, _stream_had_content
                )

                if model_idx > 0:
                    logger.info(f"[CASCADE] Streaming fallback success: {model}")
                    log_cascade(
                        model=model,
                        action="success",
                        tier=tier,
                        reason="fallback_success_stream",
                        request_id=request_id,
                    )
                return

            except HTTPException as e:
                if emitted_any_chunk:
                    # Do not restart a stream after partial output.
                    raise

                last_error = e
                status_code = e.status_code

                if status_code in (400, 401):
                    error_str = str(e.detail).lower()
                    if any(
                        p in error_str
                        for p in (
                            "context_length",
                            "maximum context",
                            "too long",
                            "context window",
                            "prompt is too long",
                        )
                    ):
                        try:
                            from src.services.usage.model_limits import (
                                refresh_model_limit_from_api,
                            )

                            asyncio.create_task(
                                refresh_model_limit_from_api(model, api_key)
                            )
                        except Exception:
                            pass
                        logger.info(
                            f"[CASCADE] {model} → {status_code} (context limit), cascading"
                        )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="request_error_stream",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        error=str(e.detail),
                    )
                    model_idx += 1
                    continue

                if status_code == 429:
                    rotated_key = self._next_provider_key(model, config)
                    if rotated_key and not current_request.get("_provider_api_key"):
                        logger.info(f"[CASCADE] {model} → 429 stream, rotating provider key once")
                        current_request["_provider_api_key"] = rotated_key
                        retry_counts[model] += 1
                        continue
                    error_str = str(e.detail).lower()
                    # Alibaba's burst ramp-up detector fires on velocity spikes from cold starts.
                    # Retrying the same provider doesn't help — skip straight to next provider.
                    is_alibaba_rampup = (
                        "rate increased too quickly" in error_str
                        or "scale requests more smoothly" in error_str
                    )
                    if is_alibaba_rampup:
                        logger.info(
                            f"[CASCADE] {model} → 429 ramp-up burst, cascading to next provider"
                        )
                        next_model = (
                            models_to_try[model_idx + 1]
                            if model_idx + 1 < len(models_to_try)
                            else None
                        )
                        log_cascade(
                            model=model,
                            action="switch",
                            tier=tier,
                            reason="alibaba_rampup_cascade_stream",
                            from_model=model,
                            to_model=next_model,
                            request_id=request_id,
                            error=str(e.detail),
                        )
                        last_error = e
                        model_idx += 1
                        continue

                    # Rate-limit (streaming): cascade after 1 retry to avoid long backoff
                    retry_counts[model] += 1
                    logger.debug(
                        f"[CASCADE] Streaming rate limit on {model} ({retry_counts[model]}/1), cascading next"
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="rate_limit_stream_cascade",
                        request_id=request_id,
                        retry_count=retry_counts[model],
                        error=str(e.detail),
                    )
                    last_error = e
                    model_idx += 1
                    continue

                if status_code in (500, 502, 503, 504):
                    retry_counts[model] += 1
                    logger.debug(
                        f"[CASCADE] Streaming server error {status_code} on {model} ({retry_counts[model]}/{max_retries_before_cascade})"
                    )
                    log_cascade(
                        model=model,
                        action="retry",
                        tier=tier,
                        reason=f"server_error_stream_{status_code}",
                        request_id=request_id,
                        retry_count=retry_counts[model],
                        error=str(e.detail),
                    )
                    if retry_counts[model] >= max_retries_before_cascade:
                        logger.debug(
                            f"[CASCADE] Max retries reached for {model}, switching to next"
                        )
                        next_model = (
                            models_to_try[model_idx + 1]
                            if model_idx + 1 < len(models_to_try)
                            else None
                        )
                        log_cascade(
                            model=model,
                            action="switch",
                            tier=tier,
                            reason=f"max_server_error_stream_{status_code}_retries",
                            from_model=model,
                            to_model=next_model,
                            request_id=request_id,
                            retry_count=retry_counts[model],
                        )
                        model_idx += 1
                    continue

                # 499 (cancelled) and other errors should propagate.
                raise

            except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
                if emitted_any_chunk:
                    raise
                logger.debug(
                    f"[CASCADE] Streaming SSL/Cert error on {model} - switching immediately: {e}"
                )
                next_model = (
                    models_to_try[model_idx + 1]
                    if model_idx + 1 < len(models_to_try)
                    else None
                )
                log_cascade(
                    model=model,
                    action="switch",
                    tier=tier,
                    reason="ssl_error_stream",
                    from_model=model,
                    to_model=next_model,
                    request_id=request_id,
                    error=str(e),
                )
                last_error = e
                model_idx += 1
                continue

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if emitted_any_chunk:
                    raise
                retry_counts[model] += 1
                logger.debug(
                    f"[CASCADE] Streaming network error on {model} ({retry_counts[model]}/{max_retries_before_cascade})"
                )
                log_cascade(
                    model=model,
                    action="retry",
                    tier=tier,
                    reason="network_error_stream",
                    request_id=request_id,
                    retry_count=retry_counts[model],
                    error=str(e),
                )
                last_error = e
                if retry_counts[model] >= max_retries_before_cascade:
                    logger.debug(
                        f"[CASCADE] Max retries reached for {model}, switching to next"
                    )
                    next_model = (
                        models_to_try[model_idx + 1]
                        if model_idx + 1 < len(models_to_try)
                        else None
                    )
                    log_cascade(
                        model=model,
                        action="switch",
                        tier=tier,
                        reason="max_network_retries_stream",
                        from_model=model,
                        to_model=next_model,
                        request_id=request_id,
                        retry_count=retry_counts[model],
                    )
                    model_idx += 1
                continue

        try:
            from src.core.circuit_breaker import get_circuit_breaker_registry

            get_circuit_breaker_registry().save_all()
        except Exception:
            pass

        logger.warning(
            f"[CASCADE] All stream cascade models exhausted for {primary_model}"
        )
        log_cascade(
            model=primary_model,
            action="exhausted",
            tier=tier,
            reason="all_models_failed_stream",
            request_id=request_id,
            error=str(last_error) if last_error else None,
        )
        if last_error:
            raise last_error
        # See the non-stream cascade: APIError(message) raises TypeError (missing request) and
        # masks the real cause as a 500. Surface a clear 503 for "all models skipped" instead.
        raise HTTPException(
            status_code=503,
            detail="All stream cascade models are currently unavailable (every model was skipped, "
            "likely due to open circuit breakers from recent failures). Try again shortly.",
        )
