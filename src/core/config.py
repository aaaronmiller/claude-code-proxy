"""Configuration shim delegating all reads to ConfigResolver.

All field reads go through the global resolver; this class provides
attribute-style access with appropriate type coercion. This replaces the
legacy os.environ-based implementation and satisfies Constitution Principle VI
(single source of truth).
"""

import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.config_resolver import resolver as _resolver, ConfigLayer

# ── API key format patterns (unchanged from legacy) ────────────────────────────
API_KEY_PATTERNS: Dict[str, re.Pattern] = {
    "openai": re.compile(r"^sk-[a-zA-Z0-9]{20,}$"),
    "openrouter": re.compile(r"^sk-or-v1-[a-f0-9]{64}$"),
    "anthropic": re.compile(r"^sk-ant-[a-zA-Z0-9\-_]{20,}$"),
    "google": re.compile(r"^AIza[a-zA-Z0-9_-]{35}$"),
    "gemini": re.compile(r"^AIza[a-zA-Z0-9_-]{35}$"),
    "azure": re.compile(r"^[a-f0-9]{32}$"),
    "vibeproxy": re.compile(r"^ya29\.[a-zA-Z0-9_-]+$"),
    "kiro": re.compile(r"^[a-zA-Z0-9\-_]{20,}$"),
}


# ── Descriptor ─────────────────────────────────────────────────────────────────


class ConfigField:
    """Descriptor that resolves a config field on every access with optional cast."""

    def __init__(self, field_path: str, cast: Callable[[Any], Any] = lambda x: x):
        self.field_path = field_path
        self.cast = cast

    def __get__(self, instance, owner):
        try:
            # Prefer request-scoped snapshot if present (US3 in-flight isolation)
            from src.core.config_resolver import get_snapshot

            snap = get_snapshot()
            if snap is not None and self.field_path in snap:
                rv = snap[self.field_path]
                return self.cast(rv.value)
            rv = _resolver.resolve(self.field_path)
            return self.cast(rv.value)
        except KeyError:
            return None

    def __set__(self, instance, value):
        raise AttributeError("Config is read-only; use resolver API to mutate")


# ── Config shim ────────────────────────────────────────────────────────────────


class Config:
    """Thin read-only shim over ConfigResolver. Attributes are live."""

    # ── Simple scalar fields ───────────────────────────────────────────────────
    host = ConfigField("host")
    port = ConfigField("port", int)
    log_level = ConfigField("log_level")
    request_timeout = ConfigField("request_timeout", int)
    max_retries = ConfigField("max_retries", int)
    azure_api_version = ConfigField("azure_api_version")

    log_tier = ConfigField("log_tier")
    logs_dir = ConfigField("logs_dir")
    log_max_size_mb = ConfigField("log_max_size_mb", int)
    log_retention_days = ConfigField("log_retention_days", int)
    track_usage = ConfigField(
        "track_usage",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else True,
    )
    usage_tracking_db_path = ConfigField("usage_tracking_db_path")

    tool_output_max_chars = ConfigField("tool_output_max_chars", int)
    tool_output_truncation = ConfigField(
        "tool_output_truncation",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else True,
    )
    max_tokens_limit = ConfigField(
        "max_tokens_limit", lambda v: int(v) if v is not None else None
    )
    min_tokens_limit = ConfigField(
        "min_tokens_limit", lambda v: int(v) if v is not None else None
    )
    enable_openrouter_selection = ConfigField(
        "enable_openrouter_selection", lambda v: str(v).lower() in ("true", "1", "yes")
    )

    model_cascade = ConfigField(
        "model_cascade", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    model_cascade_daily_limit = ConfigField("model_cascade_daily_limit", int)
    # Token budget enforcement — 0 means disabled
    daily_token_budget = ConfigField("daily_token_budget", int)
    per_request_token_budget = ConfigField("per_request_token_budget", int)
    # Cost budget enforcement — 0.0 means disabled (USD)
    daily_cost_budget = ConfigField(
        "daily_cost_budget", lambda v: float(v) if v is not None else 0.0
    )
    # Headroom bypass: skip compression for requests below this token count (0=disabled)
    headroom_bypass_threshold = ConfigField("headroom_bypass_threshold", int)
    # Mid-stream output budget: stop expensive model after N output tokens, route next turn cheaper (0=disabled)
    mid_stream_output_budget = ConfigField("mid_stream_output_budget", int)
    # Local GPU inference (4th cascade tier via ollama/llamafile)
    local_model = ConfigField("local_model")           # e.g. ollama/llama3.2 or llamafile/mistral
    local_endpoint = ConfigField("local_endpoint")     # e.g. http://localhost:11434/v1
    local_enabled = ConfigField(
        "local_enabled",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else False,
    )
    openrouter_fallback_models = ConfigField(
        "openrouter_fallback_models",
        lambda v: [m.strip() for m in v.split(",")] if v else [],
    )
    fallback_methods = ConfigField(
        "fallback_methods", lambda v: set(v.split(",")) if v else set()
    )

    # ── Tool-calling fallback ───────────────────────────────────────────────────
    toolcall_models = ConfigField(
        "toolcall_models",
        lambda v: [m.strip() for m in v.split(",") if m.strip()] if v else [],
    )
    toolcall_auto_route = ConfigField(
        "toolcall_auto_route",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else True,
    )
    toolcall_max_retries = ConfigField(
        "toolcall_max_retries",
        lambda v: int(v) if v else 2,
    )

    enable_custom_big_prompt = ConfigField(
        "enable_custom_big_prompt", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    enable_custom_middle_prompt = ConfigField(
        "enable_custom_middle_prompt", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    enable_custom_small_prompt = ConfigField(
        "enable_custom_small_prompt", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    big_system_prompt_file = ConfigField("big_system_prompt_file")
    middle_system_prompt_file = ConfigField("middle_system_prompt_file")
    small_system_prompt_file = ConfigField("small_system_prompt_file")
    big_system_prompt = ConfigField("big_system_prompt")
    middle_system_prompt = ConfigField("middle_system_prompt")
    small_system_prompt = ConfigField("small_system_prompt")

    reasoning_effort = ConfigField("reasoning_effort")
    verbosity = ConfigField("verbosity")
    reasoning_exclude = ConfigField(
        "reasoning_exclude", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    reasoning_max_tokens = ConfigField(
        "reasoning_max_tokens", lambda v: int(v) if v else None
    )
    big_model_reasoning = ConfigField("big_model_reasoning")
    middle_model_reasoning = ConfigField("middle_model_reasoning")
    small_model_reasoning = ConfigField("small_model_reasoning")

    enable_dashboard = ConfigField(
        "enable_dashboard", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    dashboard_layout = ConfigField("dashboard_layout")
    dashboard_refresh = ConfigField("dashboard_refresh", float)
    dashboard_waterfall_size = ConfigField("dashboard_waterfall_size", int)
    compact_logger = ConfigField(
        "compact_logger", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_display_mode = ConfigField("terminal_display_mode")
    terminal_show_workspace = ConfigField(
        "terminal_show_workspace", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_show_context_pct = ConfigField(
        "terminal_show_context_pct", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_show_task_type = ConfigField(
        "terminal_show_task_type", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_show_speed = ConfigField(
        "terminal_show_speed", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_show_cost = ConfigField(
        "terminal_show_cost", lambda v: str(v).lower() in ("true", "1", "yes")
    )
    terminal_show_duration_colors = ConfigField(
        "terminal_show_duration_colors",
        lambda v: str(v).lower() in ("true", "1", "yes"),
    )
    terminal_color_scheme = ConfigField("terminal_color_scheme")
    terminal_session_colors = ConfigField(
        "terminal_session_colors", lambda v: str(v).lower() in ("true", "1", "yes")
    )

    # ── Assignment fields (tier) ────────────────────────────────────────────────
    big_model = ConfigField("assignments.big.model")
    big_provider = ConfigField("assignments.big.provider")
    big_endpoint = ConfigField("assignments.big.base_url")
    big_api_key = ConfigField("assignments.big.api_key")
    big_cascade = ConfigField("assignments.big.cascade")
    big_enabled = ConfigField(
        "assignments.big.enabled",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else False,
    )
    middle_model = ConfigField("assignments.middle.model")
    middle_provider = ConfigField("assignments.middle.provider")
    middle_endpoint = ConfigField("assignments.middle.base_url")
    middle_api_key = ConfigField("assignments.middle.api_key")
    middle_cascade = ConfigField("assignments.middle.cascade")
    middle_enabled = ConfigField(
        "assignments.middle.enabled",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else False,
    )
    small_model = ConfigField("assignments.small.model")
    small_provider = ConfigField("assignments.small.provider")
    small_endpoint = ConfigField("assignments.small.base_url")
    small_api_key = ConfigField("assignments.small.api_key")
    small_cascade = ConfigField("assignments.small.cascade")
    small_enabled = ConfigField(
        "assignments.small.enabled",
        lambda v: str(v).lower() in ("true", "1", "yes") if v is not None else False,
    )

    # ── Compatibility aliases ───────────────────────────────────────────────────
    # Preserve old attribute names
    openai_api_key = ConfigField("assignments.big.api_key")
    proxy_auth_key = ConfigField("proxy_auth_key")
    anthropic_api_key_legacy = ConfigField("anthropic_api_key_legacy")
    default_provider = ConfigField(
        "default_provider", lambda v: v.lower() if v else "openrouter"
    )

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """
        The key clients must present to use this proxy.

        Priority (first non-empty wins):
        1. PROXY_AUTH_KEY — explicit access restriction (e.g. 'pass', a shared secret)
        2. ANTHROPIC_API_KEY — legacy: when set, only clients knowing this key can connect
        3. None — no auth configured, all clients accepted

        PROXY_AUTH_KEY taking priority ensures that setting a custom restriction
        cannot be bypassed by a client who happens to know the real API key.
        """
        # PROXY_AUTH_KEY gates clients. ANTHROPIC_API_KEY is the upstream provider
        # credential and must NOT double as a client access restriction by default
        # (that would expose the provider key as the auth gate).
        # Set ENABLE_LEGACY_PROXY_AUTH=true to restore the old behavior where
        # ANTHROPIC_API_KEY also served as the client gate.
        proxy_auth = os.environ.get("PROXY_AUTH_KEY", "").strip()
        if proxy_auth:
            return proxy_auth
        if os.environ.get("ENABLE_LEGACY_PROXY_AUTH", "").lower() in ("true", "1", "yes"):
            legacy = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            return legacy if legacy else None
        return None

    @property
    def openai_base_url(self) -> Optional[str]:
        """Return the effective upstream URL, considering the proxy chain.

        If the proxy chain has an enabled HTTP entry (e.g. headroom),
        route through it. Otherwise fall back to the direct provider URL.
        """
        try:
            from src.core.proxy_chain import get_chain
            chain = get_chain()
            upstream = chain.upstream_url()
            if upstream:
                return upstream
        except Exception:
            pass
        # Fallback: direct provider URL from config
        try:
            return _resolver.resolve("assignments.big.base_url").value
        except KeyError:
            return None

    # ── Computed properties ─────────────────────────────────────────────────────
    @property
    def provider_registry(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Build provider registry from PROVIDERS_* environment-style config."""
        combined: dict = {}
        combined.update(_resolver._layers[ConfigLayer.SHELL_ENV])
        combined.update(_resolver._layers[ConfigLayer.DOTENV])
        prefix = "PROVIDERS_"
        suffix_url = "_URL"
        # Collect provider names with their original key casing for accurate lookup
        providers: Dict[str, str] = {}  # lowercase_name → original_key (without suffix)
        for key in combined:
            if key.startswith(prefix) and key.endswith(suffix_url):
                raw_name = key[len(prefix) : -len(suffix_url)]
                providers[raw_name.lower()] = key[: -len(suffix_url)]
        reg: Dict[str, Dict[str, Optional[str]]] = {}
        for name, key_prefix in providers.items():
            url = combined.get(f"{key_prefix}_URL", "")
            api_key = combined.get(f"{key_prefix}_API_KEY") or combined.get(
                f"{key_prefix}_KEY"
            )
            if url:
                reg[name] = {"url": url, "api_key": api_key}
        return reg

    @property
    def tier_provider_overrides(self) -> Dict[str, str]:
        overrides = {}
        for tier in ("big", "middle", "small"):
            prov = _resolver.resolve(f"assignments.{tier}.provider").value
            if prov:
                overrides[tier] = prov
        return overrides

    def _get_tier_provider_from_model(self, tier: str) -> str:
        model = getattr(self, f"{tier}_model") or ""
        if "/" in model:
            return model.split("/", 1)[0].lower()
        return "default"

    def _get_tier_provider(self, tier: str) -> str:
        overrides = self.tier_provider_overrides
        if tier in overrides:
            return overrides[tier]
        return self._get_tier_provider_from_model(tier)

    @property
    def big_provider(self) -> str:
        return self._get_tier_provider("big")

    @property
    def middle_provider(self) -> str:
        return self._get_tier_provider("middle")

    @property
    def small_provider(self) -> str:
        return self._get_tier_provider("small")

    @property
    def passthrough_mode(self) -> bool:
        key = self.openai_api_key
        if not key:
            return True
        if (
            key in ("pass", "dummy", "your-api-key-here", "sk-your-openai-api-key-here")
            or "your-" in key.lower()
        ):
            return True
        return False

    # ── Methods ─────────────────────────────────────────────────────────────────
    @staticmethod
    def validate_api_key_format(key: str, provider: str = None) -> Tuple[bool, str]:
        """Validate an API key's format (stateless utility)."""
        if not key:
            return False, "No API key provided"

        if not provider:
            if key.startswith("sk-or-"):
                provider = "openrouter"
            elif key.startswith("sk-ant-"):
                provider = "anthropic"
            elif key.startswith("AIza"):
                provider = "google"
            elif key.startswith("ya29."):
                provider = "vibeproxy"
            elif key.startswith("sk-"):
                provider = "openai"
            elif len(key) == 32 and all(c in "0123456789abcdef" for c in key.lower()):
                provider = "azure"
            else:
                if len(key) >= 20:
                    return True, "Unknown key format (accepted)"
                return False, "Key too short (minimum 20 characters)"

        pattern = API_KEY_PATTERNS.get(provider.lower())
        if pattern:
            if pattern.match(key):
                return True, f"Valid {provider} key format"
            else:
                if provider == "openrouter" and key.startswith("sk-or-"):
                    return True, "Valid OpenRouter key (relaxed validation)"
                elif provider in ("google", "gemini") and key.startswith("AIza"):
                    return True, "Valid Google key (relaxed validation)"
                return False, f"Invalid {provider} key format"

        if len(key) >= 10:
            return True, f"Accepted key for {provider}"
        return False, "Key too short"

    def validate_api_key(self, api_key: str = None, provider: str = None) -> bool:
        """Validate an API key (optionally the configured default)."""
        key = api_key if api_key is not None else self.openai_api_key
        if not key:
            return False
        valid, _ = self.validate_api_key_format(key, provider)
        return valid

    def validate_client_api_key(self, client_api_key: str) -> bool:
        """Validate a client-supplied API key against proxy auth (if configured)."""
        if not self.anthropic_api_key:
            return True
        return client_api_key == self.anthropic_api_key

    def get_provider_endpoint(self, provider_name: str) -> Optional[str]:
        """Get base URL for a named provider from provider_registry."""
        reg = self.provider_registry
        entry = reg.get(provider_name.lower())
        return entry.get("url") if entry else None

    def get_provider_api_key(self, provider_name: str) -> Optional[str]:
        """Get API key for a named provider from provider_registry."""
        reg = self.provider_registry
        entry = reg.get(provider_name.lower())
        return entry.get("api_key") if entry else None

    def get_custom_headers(self) -> Dict[str, str]:
        """Extract CUSTOM_HEADER_* environment variables."""
        custom = {}
        for key, val in os.environ.items():
            if key.startswith("CUSTOM_HEADER_"):
                header_name = key[14:].replace("_", "-")
                custom[header_name] = val
        return custom

    def get_cascade_for_tier(self, tier: str) -> List[str]:
        """Return the cascade fallback list for a tier.

        Reads from two sources (new format takes precedence):
        1. assignments.{tier}.cascade  — new unified config format
        2. {TIER}_CASCADE env var      — legacy format still in common use
        """
        # 1. New format
        field = f"assignments.{tier}.cascade"
        try:
            val = _resolver.resolve(field).value
            if isinstance(val, list) and val:
                return val
        except KeyError:
            pass

        # 2. Legacy env var fallback: BIG_CASCADE, MIDDLE_CASCADE, SMALL_CASCADE
        legacy_key = f"{tier.upper()}_CASCADE"
        raw = os.environ.get(legacy_key, "").strip()
        if raw:
            models = [m.strip() for m in raw.split(",") if m.strip()]
            if models:
                return models

        return []

    def get_toolcall_provider_models(self) -> Dict[str, str]:
        """Return provider-specific tool-calling model overrides from TOOLCALL_<provider> env vars."""
        result = {}
        combined: dict = {}
        combined.update(_resolver._layers[ConfigLayer.SHELL_ENV])
        combined.update(_resolver._layers[ConfigLayer.DOTENV])
        prefix = "TOOLCALL_"
        # Skip known non-provider keys
        skip_keys = {"TOOLCALL_MODELS", "TOOLCALL_AUTO_ROUTE", "TOOLCALL_MAX_RETRIES"}
        for key, val in combined.items():
            if key.startswith(prefix) and key not in skip_keys and val:
                provider_name = key[len(prefix) :].lower()
                result[provider_name] = val
        return result


# ── Singleton instance ─────────────────────────────────────────────────────────

config = Config()

# ── Exports for validator.py ─────────────────────────────────────────────────
validate_api_key_format = Config.validate_api_key_format


def set_provider_status(provider: str, status: str, error: str = None) -> None:
    """Set provider status for health checks."""
    # This was a no-op in the original config - keep it that way
    pass
