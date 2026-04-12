from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import uuid
import time
import os
import hashlib
import json as json_module
from typing import Optional, Dict, Any
from collections import OrderedDict
from threading import Lock

from src.core.config import config
from src.core.logging import logger
from src.core.client import OpenAIClient, VibeProxyUnavailableError
from src.models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest
from src.services.conversion.request_converter import convert_claude_to_openai
from src.services.conversion.response_converter import (
    convert_openai_to_claude_response,
    convert_openai_streaming_to_claude_with_cancellation,
    convert_openai_streaming_to_claude,
)
from src.core.model_manager import model_manager
from src.services.logging.request_logger import request_logger, RequestLogger
from src.services.logging.compact_logger import compact_logger
from src.services.usage.usage_tracker import usage_tracker
from src.services.usage.model_limits import check_model_limits
from src.services.models.model_filter import filter_models
from src.services.prompts.prompt_injection_middleware import inject_system_prompts
from src.services.usage.model_limits import get_model_limits
from src.conversation.crosstalk import crosstalk_orchestrator
from src.core.json_detector import json_detector
from src.dashboard.dashboard_hooks import dashboard_hooks
from src.models.crosstalk import (
    CrosstalkSetupRequest,
    CrosstalkSetupResponse,
    CrosstalkRunResponse,
    CrosstalkStatusResponse,
    CrosstalkListResponse,
    CrosstalkDeleteResponse,
    CrosstalkError,
)

# Debug logging for traffic capture
import logging

DEBUG_TRAFFIC_LOG = os.environ.get("DEBUG_TRAFFIC_LOG", "false").lower() == "true"
traffic_logger = logging.getLogger("traffic_debugger")
traffic_logger.setLevel(logging.DEBUG)

if DEBUG_TRAFFIC_LOG:
    # Setup file handler for traffic logs
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = logging.FileHandler(f"{log_dir}/debug_traffic.log")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    traffic_logger.addHandler(file_handler)


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
# Prevents duplicate terminal output caused by client retries


class RequestDeduplicator:
    """
    Deduplicates requests based on content hash within a time window.

    When Claude Code retries a request (e.g., after malformed tool call response),
    this prevents processing the same request multiple times and causing duplicate
    terminal output.
    """

    def __init__(self, window_seconds: float = 5.0, max_cache_size: int = 100):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        self._window_seconds = window_seconds
        self._max_cache_size = max_cache_size

    def _extract_session_fingerprint(self, request: "ClaudeMessagesRequest") -> str:
        """Extract a stable per-session fingerprint from Claude Code metadata."""
        if request.metadata and isinstance(request.metadata, dict):
            user_id = request.metadata.get("user_id")
            if user_id:
                return str(user_id)

        # Fallback: Claude Code often includes billing/session markers in system blocks.
        system = getattr(request, "system", None)
        if isinstance(system, list):
            for block in system:
                if isinstance(block, dict):
                    text = block.get("text", "")
                else:
                    text = getattr(block, "text", "")
                if text and "cc_version=" in text:
                    return text[:256]

        return "unknown-session"

    def _compute_hash(
        self, request: "ClaudeMessagesRequest", client_ip: str = "unknown"
    ) -> str:
        """Compute a retry hash with strong session isolation."""
        session_fingerprint = self._extract_session_fingerprint(request)
        content_parts = [session_fingerprint, client_ip, request.model]

        if request.stream is not None:
            content_parts.append(str(request.stream))
        if getattr(request, "max_tokens", None) is not None:
            content_parts.append(str(request.max_tokens))
        if getattr(request, "temperature", None) is not None:
            content_parts.append(str(request.temperature))

        if getattr(request, "tool_choice", None):
            content_parts.append(
                json_module.dumps(request.tool_choice, sort_keys=True, default=str)
            )
        if getattr(request, "tools", None):
            tool_names = [getattr(tool, "name", "") for tool in request.tools]
            content_parts.append(",".join(tool_names))

        for msg in request.messages:
            content_parts.append(getattr(msg, "role", ""))
            if hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, str):
                    content_parts.append(content[:400])
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            block_type = block.get("type", "")
                            content_parts.append(block_type)
                            if block_type == "text":
                                text = block.get("text", "")
                                if text:
                                    content_parts.append(text[:200])
                            if block_type == "tool_use":
                                content_parts.append(block.get("id", ""))
                                content_parts.append(block.get("name", ""))
                            if block_type == "tool_result":
                                content_parts.append(block.get("tool_use_id", ""))
                        else:
                            block_type = getattr(block, "type", "")
                            content_parts.append(block_type)
                            if block_type == "text":
                                text = getattr(block, "text", "")
                                if text:
                                    content_parts.append(text[:200])
                            if block_type == "tool_use":
                                content_parts.append(getattr(block, "id", ""))
                                content_parts.append(getattr(block, "name", ""))
                            if block_type == "tool_result":
                                content_parts.append(getattr(block, "tool_use_id", ""))

        content_str = "|".join(str(x) for x in content_parts)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def check_duplicate(
        self, request: "ClaudeMessagesRequest", client_ip: str = "unknown"
    ) -> tuple[bool, str, Optional[Dict]]:
        """
        Check if request is a duplicate within the time window.
        Uses client IP to distinguish between different sessions.

        Args:
            request: The Claude messages request
            client_ip: Client IP address to include in hash for session isolation

        Returns:
            (is_duplicate, request_hash, cached_response or None)
        """
        request_hash = self._compute_hash(request, client_ip)
        current_time = time.time()

        with self._lock:
            # Clean expired entries
            expired = []
            for h, data in self._cache.items():
                if current_time - data["timestamp"] > self._window_seconds:
                    expired.append(h)
            for h in expired:
                del self._cache[h]

            # Check if this request is in cache
            if request_hash in self._cache:
                cached = self._cache[request_hash]
                age = current_time - cached["timestamp"]

                if age < self._window_seconds:
                    # Only treat as duplicate if we have a cached response
                    # Streaming requests should NOT be deduplicated
                    if cached.get("response") and not getattr(request, "stream", False):
                        cached["count"] += 1
                        logger.warning(
                            f"Duplicate request detected (hash={request_hash[:8]}, "
                            f"count={cached['count']}, age={age:.2f}s)"
                        )
                        return True, request_hash, cached.get("response")
                    # No cached response yet - request is still processing
                    # Log but don't block - let it through
                    logger.debug(
                        f"Request {request_hash[:8]} similar to in-flight request "
                        f"(age={age:.2f}s, count={cached['count']}) - allowing"
                    )

            # Not a duplicate, add to cache
            self._cache[request_hash] = {
                "timestamp": current_time,
                "count": 1,
                "response": None,
            }

            # Move to end (most recent)
            self._cache.move_to_end(request_hash)

            # Trim cache if too large
            while len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)

            return False, request_hash, None

    def cache_response(self, request_hash: str, response: Dict):
        """Cache a response for potential duplicate requests."""
        with self._lock:
            if request_hash in self._cache:
                self._cache[request_hash]["response"] = response


# Global deduplicator instance
ENABLE_DEDUP = os.getenv("ENABLE_REQUEST_DEDUP", "true").lower() == "true"
DEDUP_WINDOW = float(os.getenv("DEDUP_WINDOW_SECONDS", "3.0"))
request_deduplicator = RequestDeduplicator(window_seconds=DEDUP_WINDOW)


async def log_request_body(request: Request):
    """Middleware-like function to log request body if enabled."""
    if not DEBUG_TRAFFIC_LOG:
        return

    try:
        # Clone body stream so it can be read again
        body = await request.body()

        # Log basic info
        traffic_logger.info(f"--- INCOMING REQUEST: {request.method} {request.url} ---")
        traffic_logger.info(f"Headers: {dict(request.headers)}")

        # Log body (truncated if too large)
        try:
            body_str = body.decode("utf-8")
            # Filter out (no content) placeholders to reduce token waste in debug logs
            body_str_filtered = body_str.replace("(no content)", "[empty]").replace(
                "no content", "[empty]"
            )
            if len(body_str_filtered) > 50000:
                traffic_logger.info(
                    f"Body (Truncated): {body_str_filtered[:1000]}... [Total {len(body_str_filtered)} bytes]"
                )
            elif len(body_str_filtered) > 1000:
                traffic_logger.info(
                    f"Body (Truncated): {body_str_filtered[:200]}... [Total {len(body_str_filtered)} bytes]"
                )
            else:
                traffic_logger.info(f"Body: {body_str_filtered}")
        except Exception as _e:
            traffic_logger.info(f"Body (Binary): {len(body)} bytes")

        traffic_logger.info("------------------------------------------------")
    except Exception as e:
        traffic_logger.error(f"Failed to log request: {e}")


router = APIRouter()

# Choose logger based on environment variable
USE_COMPACT_LOGGER = os.getenv("USE_COMPACT_LOGGER", "false").lower() == "true"
active_logger = compact_logger if USE_COMPACT_LOGGER else request_logger

# Get custom headers from config
custom_headers = config.get_custom_headers()

openai_client = OpenAIClient(
    config.openai_api_key or "",
    config.openai_base_url,
    config.request_timeout,
    api_version=config.azure_api_version,
    custom_headers=custom_headers,
)

# Configure per-model clients for hybrid deployments
openai_client.configure_per_model_clients(config)


async def validate_and_extract_api_key(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    openai_api_key: Optional[str] = Header(None, alias="openai-api-key"),
) -> Optional[str]:
    """
    Validate and extract API keys based on operating mode.

    Returns:
        OpenAI API key to use for the request (None in proxy mode)

    Raises:
        HTTPException: If validation fails
    """
    client_api_key = None
    openai_key = None

    # Extract Anthropic API key from headers (for Claude client validation)
    if x_api_key:
        client_api_key = x_api_key
        logger.debug(f"API key from x-api-key header: {client_api_key[:10]}...")
    elif authorization and authorization.startswith("Bearer "):
        client_api_key = authorization.replace("Bearer ", "")
        logger.debug(f"API key from Authorization header: {client_api_key[:10]}...")

    # Extract OpenAI API key from headers (for passthrough mode)
    if openai_api_key:
        openai_key = openai_api_key
        logger.debug(f"OpenAI API key from header: {openai_key[:10]}...")

    # Passthrough mode: Require OpenAI API key from user
    if config.passthrough_mode:
        if not openai_key:
            raise HTTPException(
                status_code=401,
                detail="Passthrough mode: Please provide your OpenAI API key via 'openai-api-key' header",
            )

        # Validate OpenAI API key format
        if not config.validate_api_key(openai_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key format. Key must start with 'sk-' and be at least 20 characters",
            )

        logger.debug("Passthrough mode: OpenAI API key validated")
        return openai_key

    # Proxy mode: Validate Anthropic client key if configured
    if config.anthropic_api_key:
        if not client_api_key or not config.validate_client_api_key(client_api_key):
            logger.warning(
                f"Invalid API key provided by client. Expected: {config.anthropic_api_key}, Got: {client_api_key[:10] if client_api_key else 'None'}..."
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please provide a valid Anthropic API key.",
            )
        logger.debug("Proxy mode: Anthropic API key validation passed")

    return None  # Proxy mode: use server-configured API key


@router.post("/v1/messages")
async def create_message(
    request: ClaudeMessagesRequest,
    http_request: Request,
    openai_api_key: Optional[str] = Depends(validate_and_extract_api_key),
):
    # Log full request for debugging
    await log_request_body(http_request)

    request_start_time = time.time()
    request_id = str(uuid.uuid4())

    # Extract client IP for deduplication (before processing)
    client_ip = http_request.client.host if http_request.client else "unknown"

    # ═══════════════════════════════════════════════════════════════════════════════
    # REQUEST DEDUPLICATION CHECK
    # ═══════════════════════════════════════════════════════════════════════════════
    # Detects and handles duplicate requests caused by client retries
    # Uses client IP to distinguish between different Claude Code sessions
    # Only blocks if we have a cached response (non-streaming only)
    request_hash = None
    if ENABLE_DEDUP:
        is_duplicate, request_hash, cached_response = (
            request_deduplicator.check_duplicate(request, client_ip)
        )
        if is_duplicate and cached_response:
            # Return cached response for duplicate non-streaming request
            logger.info(
                f"Request {request_id}: Returning cached response for duplicate request"
            )
            return JSONResponse(content=cached_response)

    try:
        logger.debug(
            f"Processing Claude request: model={request.model}, stream={request.stream}"
        )
        logger.debug(f"Request ID: {request_id}")
        logger.debug("Request deduplication check passed")

        # Parse model to get routing info and reasoning config
        routed_model, reasoning_config = model_manager.parse_and_map_model(
            request.model
        )

        # Determine endpoint and provider FIRST (before conversion)
        client = openai_client.get_client_for_model(routed_model, config)
        endpoint = str(client.base_url) if hasattr(client, 'base_url') else config.openai_base_url
        provider = config.provider_for_endpoint(endpoint) if hasattr(config, 'provider_for_endpoint') else config.default_provider
        original_tier = None  # Track for fallback logging

        # FALLBACK ROUTING: If selected endpoint uses VibeProxy and it's down, fallback to SMALL
        # Also check default endpoint for VibeProxy
        is_vibeproxy_endpoint = endpoint and (
            "127.0.0.1:8317" in endpoint or "localhost:8317" in endpoint
        )
        is_default_vibeproxy = config.openai_base_url and (
            "127.0.0.1:8317" in config.openai_base_url
            or "localhost:8317" in config.openai_base_url
        )
        # VibeProxy fallback: if the chosen endpoint is VibeProxy and it's down,
        # fall back to the default provider
        if is_vibeproxy_endpoint or (original_tier is None and is_default_vibeproxy):
            from src.services.antigravity import is_vibeproxy_available

            if not is_vibeproxy_available():
                tier_name = original_tier or "DEFAULT"
                logger.warning(
                    f"Request {request_id}: VibeProxy unavailable, falling back from {tier_name} to DEFAULT provider"
                )
                client = openai_client.client
                endpoint = config.openai_base_url
                provider = config.default_provider
                routed_model = config.big_model  # Use big model on the default provider

        # Convert Claude request to OpenAI format with provider-specific transformations
        openai_request = convert_claude_to_openai(
            request, model_manager, target_provider=provider
        )

        # Update the openai_request with the routed model
        openai_request["model"] = routed_model

        custom_client = None
        active_api_key = openai_api_key

        # Apply per-use-case model routing (image, long_context, think, background, etc.)
        # This runs AFTER tier routing so use-case overrides win over tier defaults.
        # _original_model carries the raw Claude model name (e.g. "claude-haiku-...") so the
        # router can detect background/lightweight requests even after tier mapping.
        openai_request["_original_model"] = request.model
        _use_case_tier: Optional[str] = None  # cascade tier for use-case-routed requests
        try:
            from src.core.model_router import get_router
            _use_case_route = get_router(config).route(openai_request)
            if _use_case_route:
                openai_request["model"] = _use_case_route.model
                
                # Check for custom endpoint wrapper
                if _use_case_route.base_url:
                    endpoint = _use_case_route.base_url
                    if hasattr(config, 'provider_for_endpoint'):
                        provider = config.provider_for_endpoint(endpoint)
                    
                    active_api_key = _use_case_route.api_key or openai_api_key
                    custom_client = OpenAIClient(
                        active_api_key, 
                        endpoint, 
                        config.request_timeout, 
                        api_version=config.azure_api_version,
                        custom_headers=custom_headers
                    )
                    custom_client.configure_per_model_clients(config)

                # Determine which cascade list to use if this model fails.
                # background → middle tier fallbacks (lighter models)
                # image/web_search/think → big tier fallbacks (capability matters)
                # long_context → big tier fallbacks (context window matters)
                _orig = (openai_request.get("_original_model") or "").lower()
                
                # Check background model string handling safely against string or RouteTarget
                bg_config = getattr(config, "router_background", "")
                bg_model_str = bg_config.model if hasattr(bg_config, "model") else str(bg_config)
                
                if "haiku" in _orig or _use_case_route.model == bg_model_str:
                    _use_case_tier = "middle"
                else:
                    _use_case_tier = "big"
        except Exception as _router_err:
            logger.warning(f"ModelRouter error (non-fatal): {_router_err}")
        # Strip proxy-internal keys before forwarding upstream
        openai_request.pop("_original_model", None)
        openai_request.pop("_is_background", None)

        def infer_model_tier(model_name: str) -> Optional[str]:
            def norm(name):
                return name.split("/", 1)[1].lower() if name and "/" in name else (name or "").lower()
            req = norm(model_name)
            if req == norm(config.big_model):
                return "big"
            if req == norm(config.middle_model):
                return "middle"
            if req == norm(config.small_model):
                return "small"
            return None

        # Log API configuration for debugging (helps diagnose 401 errors)
        logger.debug(f"Request {request_id}: Routing to endpoint: {endpoint}")
        logger.debug(f"Request {request_id}: Using model: {routed_model}")
        if openai_api_key:
            logger.debug(
                f"Request {request_id}: Using passthrough mode with user-provided API key"
            )
        else:
            api_key_preview = (
                config.openai_api_key[:15] if config.openai_api_key else "None"
            )
            logger.debug(
                f"Request {request_id}: Using proxy mode with server API key: {api_key_preview}..."
            )

        # Extract request metadata for comprehensive logging
        message_count = len(request.messages)
        has_system = bool(request.system)
        client_ip = http_request.client.host if http_request.client else "unknown"

        # Extract input text for token counting and workspace detection
        input_text = ""
        workspace_name = None

        def extract_workspace_name(text: str) -> Optional[str]:
            """Extract workspace/project name from system prompt text."""
            try:
                import re
                import os

                # Try multiple patterns in order of preference
                patterns = [
                    # Claude Code pattern: "Working directory: /path/to/project"
                    r"Working directory:\s+([^\n]+)",
                    # Git path pattern: /something/git/project-name
                    r"/git/([^/\s]+)",
                    # Generic path pattern: extract last folder name from absolute paths
                    r"/([a-zA-Z0-9_-]+)(?:/[a-zA-Z0-9_.-]+)*\s",
                    # Workspace keyword pattern
                    r"workspace.*?:?\s+([a-zA-Z0-9_-]+)",
                ]

                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        # If it's a full path, extract just the last folder name
                        if "/" in candidate:
                            candidate = os.path.basename(candidate.rstrip("/"))
                        # Skip common parent folders
                        skip_names = [
                            "users",
                            "home",
                            "user",
                            "documents",
                            "projects",
                            "git",
                            "code",
                            "my_projects",
                            "0my_projects",
                        ]
                        if candidate.lower() not in skip_names and len(candidate) > 0:
                            # Shorten if too long
                            if len(candidate) > 20:
                                return candidate[:17] + "..."
                            return candidate
                return None
            except Exception as e:
                # If workspace extraction fails, just return None - don't break the request
                logger.debug(f"Workspace name extraction failed: {e}")
                return None

        if request.system:
            if isinstance(request.system, str):
                input_text += request.system
                workspace_name = extract_workspace_name(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        input_text += block.text
                        if not workspace_name and block.text:
                            workspace_name = extract_workspace_name(block.text)

        for msg in request.messages:
            if isinstance(msg.content, str):
                input_text += msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        input_text += block.text

        # Get model limits and token counts for logging
        # Get model limits and token counts for logging
        from src.services.usage.model_limits import get_model_limits

        context_limit, output_limit = get_model_limits(routed_model)

        # Estimate input tokens
        input_tokens = 0
        if input_text:
            # Rough estimate: ~4 characters per token
            input_tokens = max(1, len(input_text) // 4)

        # Detect images and tools
        has_images = False
        has_tools = bool(request.tools)
        for msg in request.messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "type") and block.type == "image":
                        has_images = True
                        break

        # Log comprehensive request start
        active_logger.log_request_start(
            request_id=request_id,
            original_model=request.model,
            routed_model=routed_model,
            endpoint=endpoint,
            reasoning_config=reasoning_config,
            stream=request.stream if request.stream is not None else False,
            input_text=input_text,
            context_limit=context_limit,
            output_limit=output_limit,
            input_tokens=input_tokens,
            message_count=message_count,
            has_system=has_system,
            has_tools=has_tools,
            has_images=has_images,
            client_info=client_ip,
            workspace_name=workspace_name,
        )

        # Dashboard hook: request start
        dashboard_hooks.on_request_start(
            request_id,
            {
                "model": routed_model,
                "stream": request.stream,
                "has_tools": has_tools,
                "has_images": has_images,
                "input_tokens": input_tokens,
            },
        )

        # Check if client disconnected before processing
        if await http_request.is_disconnected():
            logger.warning(
                f"Client disconnected before processing request_id: {request_id}"
            )
            raise HTTPException(status_code=499, detail="Client disconnected")

        if request.stream:
            # Streaming response - wrap in error handling
            logger.debug(f"Starting streaming response for request_id: {request_id}")
            try:
                active_openai_client = custom_client if custom_client else openai_client
                tier = infer_model_tier(openai_request.get("model", "")) or _use_case_tier
                if config.model_cascade and tier:
                    openai_stream = (
                        active_openai_client.create_chat_completion_stream_with_cascade(
                            openai_request,
                            tier=tier,
                            config=config,
                            request_id=request_id,
                            api_key=active_api_key,
                        )
                    )
                else:
                    openai_stream = active_openai_client.create_chat_completion_stream(
                        openai_request, request_id, config, api_key=active_api_key
                    )
                logger.debug(f"OpenAI stream created for request_id: {request_id}")
                return StreamingResponse(
                    convert_openai_streaming_to_claude_with_cancellation(
                        openai_stream,
                        request,
                        logger,
                        http_request,
                        active_openai_client,
                        request_id,
                        config,
                        provider,
                    ),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "*",
                    },
                )
            except HTTPException as e:
                # Convert to proper error response for streaming
                logger.error(
                    f"Streaming HTTPException for request_id {request_id}: status={e.status_code}, detail={e.detail}"
                )
                import traceback

                logger.error(f"Streaming traceback: {traceback.format_exc()}")
                error_message = openai_client.classify_openai_error(e.detail)
                error_response = {
                    "type": "error",
                    "error": {"type": "api_error", "message": error_message},
                }
                return JSONResponse(status_code=e.status_code, content=error_response)
            except VibeProxyUnavailableError as e:
                logger.error(f"VibeProxy unavailable for request_id {request_id}: {e}")
                error_response = {
                    "type": "error",
                    "error": {
                        "type": "vibeproxy_unavailable",
                        "message": str(e),
                    },
                }
                return JSONResponse(status_code=503, content=error_response)
            except Exception as e:
                logger.error(
                    f"Unexpected streaming error for request_id {request_id}: {e}"
                )
                import traceback

                logger.error(f"Streaming traceback: {traceback.format_exc()}")
                error_message = openai_client.classify_openai_error(str(e))
                error_response = {
                    "type": "error",
                    "error": {"type": "api_error", "message": error_message},
                }
                return JSONResponse(status_code=500, content=error_response)
        else:
            # Non-streaming response
            logger.debug(
                f"Starting non-streaming response for request_id: {request_id}"
            )
            logger.debug("Request deduplication check passed")

            # Seamless Key Rotation / Retry Loop
            # If we get a 401, we wait for the user to fix the key via the wizard
            from src.utils.key_reloader import key_reloader
            import asyncio

            max_retries = 150  # Wait up to 300 seconds (5 minutes)
            retry_count = 0

            while True:
                try:
                    active_openai_client = custom_client if custom_client else openai_client
                    tier = infer_model_tier(openai_request.get("model", "")) or _use_case_tier
                    if config.model_cascade and tier:
                        openai_response = (
                            await active_openai_client.create_chat_completion_with_cascade(
                                openai_request,
                                tier=tier,
                                config=config,
                                request_id=request_id,
                                api_key=active_api_key,
                            )
                        )
                    else:
                        openai_response = await active_openai_client.create_chat_completion(
                            openai_request, request_id, config, api_key=active_api_key
                        )
                    break  # Success!

                except VibeProxyUnavailableError as e:
                    # VibeProxy is down - fail fast with clear error
                    logger.error(
                        f"VibeProxy unavailable for request_id {request_id}: {e}"
                    )
                    error_response = {
                        "type": "error",
                        "error": {
                            "type": "vibeproxy_unavailable",
                            "message": str(e),
                        },
                    }
                    return JSONResponse(status_code=503, content=error_response)

                except HTTPException as e:
                    if (
                        e.status_code == 401 and not openai_api_key
                    ):  # Only retry for server-side keys (proxy mode)
                        if retry_count >= max_retries:
                            logger.error(
                                f"Authentication failed. Timed out waiting for key update."
                            )
                            raise e

                        if retry_count == 0:
                            logger.warning(
                                f"Authentication failed (401). Waiting for key update in profile..."
                            )
                            logger.warning(
                                f"Run 'cproxy-init' or the wizard to fix your key."
                            )

                        # Wait and check for updates
                        await asyncio.sleep(2)
                        retry_count += 1

                        if key_reloader.check_for_updates():
                            logger.info("Key update detected! Retrying request...")
                            # Re-configure active client with new key
                            if custom_client:
                                custom_client.api_key = config.openai_api_key or ""
                                active_api_key = custom_client.api_key
                            else:
                                openai_client.api_key = config.openai_api_key or ""  # type: ignore
                            continue

                        # Log progress every 10 seconds
                        if retry_count % 5 == 0:
                            logger.info(
                                f"Still waiting for key update... ({retry_count * 2}s elapsed)"
                            )
                    else:
                        raise e  # Re-raise other errors immediately

            logger.debug(f"OpenAI response received for request_id: {request_id}")
            logger.debug("Request deduplication check passed")
            # Log comprehensive completion with all metadata
            duration_ms = (time.time() - request_start_time) * 1000
            usage = openai_response.get("usage", {})

            # Detect JSON for TOON analysis
            has_json_content = False
            json_size_bytes = 0
            if input_text:
                has_json, json_bytes, _ = json_detector.detect_json_in_text(input_text)
                has_json_content = has_json
                json_size_bytes = json_bytes

            # Extract provider from endpoint
            provider = "unknown"
            if "openrouter" in endpoint.lower():
                provider = "openrouter"
            elif (
                "daily-cloudcode-pa" in endpoint.lower()
                or "antigravity" in routed_model.lower()
            ):
                provider = "antigravity"
            elif "openai" in endpoint.lower():
                provider = "openai"
            elif "anthropic" in endpoint.lower():
                provider = "anthropic"
            elif "azure" in endpoint.lower():
                provider = "azure"

            # Calculate cost
            # Fallback for when calculate_cost is missing or fails
            try:
                from src.services.usage.cost_calculator import calculate_cost

                estimated_cost = calculate_cost(usage, routed_model)
            except ImportError:
                # If module missing, define inline or skip
                estimated_cost = 0.0
            except Exception as e:
                logger.warning(f"Failed to calculate cost: {e}")
                estimated_cost = 0.0

            # Log to active logger
            active_logger.log_request_complete(
                request_id=request_id,
                usage=usage,
                duration_ms=duration_ms,
                status="OK",
                model_name=routed_model,
                stream=request.stream if request.stream is not None else False,
                has_reasoning=bool(reasoning_config),
            )

            # Track usage if enabled
            if usage_tracker.enabled:
                # Capture content for full logging if enabled
                import json as json_module

                req_content = (
                    json_module.dumps(request.model_dump())
                    if hasattr(request, "model_dump")
                    else str(request)
                )
                resp_content = (
                    json_module.dumps(openai_response) if openai_response else None
                )

                # Extract detailed token breakdown if available (with None safety)
                usage = usage or {}
                completion_details = usage.get("completion_tokens_details", {}) or {}
                prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
                completion_tokens = usage.get(
                    "completion_tokens", usage.get("output_tokens", 0)
                )
                reasoning_tokens = usage.get("reasoning_tokens", 0) or (
                    completion_details.get("reasoning_tokens", 0)
                    if completion_details
                    else 0
                )
                cached_tokens = (
                    usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
                    if isinstance(usage.get("prompt_tokens_details"), dict)
                    else 0
                )
                audio_tokens = (
                    usage.get("completion_tokens_details", {}).get("audio_tokens", 0)
                    if isinstance(usage.get("completion_tokens_details"), dict)
                    else 0
                )

                # Detect if this was a tool call request
                tool_use_tokens = 0
                # Try to detect from response or request
                if openai_response and isinstance(openai_response, dict):
                    choices = openai_response.get("choices", [])
                    if choices and isinstance(choices[0], dict):
                        message = choices[0].get("message", {})
                        if message.get("tool_calls"):
                            tool_use_tokens = completion_tokens * 0.3  # Estimate

                # Calculate original cost (what it would have been without smart routing)
                # This requires knowing what model we "should have" used
                original_cost = None
                original_model = request.model

                # For savings calculation, we need to compare against what would have been used
                # If this was a routing decision, the original_model tells us what was requested
                try:
                    from src.services.usage.cost_calculator import (
                        calculate_cost,
                        get_model_pricing,
                    )

                    if routed_model != original_model:
                        original_pricing = get_model_pricing(original_model)
                        if original_pricing:
                            original_cost = calculate_cost(usage, original_model)
                except Exception:
                    get_model_pricing = lambda x: None  # Fallback if import fails

                # Determine model tier for comparison stats
                # Simple tier detection based on model names and pricing
                model_tier = None
                if (
                    "free" in routed_model
                    or "mini" in routed_model.lower()
                    or "flash" in routed_model.lower()
                ):
                    model_tier = "small"
                elif (
                    "sonnet" in routed_model.lower()
                    or "medium" in routed_model.lower()
                    or "turbo" in routed_model.lower()
                ):
                    model_tier = "middle"
                elif (
                    "opus" in routed_model.lower()
                    or "large" in routed_model.lower()
                    or "4.5" in routed_model.lower()
                ):
                    model_tier = "big"
                elif (
                    "gpt-4o" in routed_model.lower()
                    and "mini" not in routed_model.lower()
                ):
                    model_tier = "middle"

                # Check if it's a free model
                try:
                    if get_model_pricing(routed_model) == (0.0, 0.0):
                        model_tier = "free"
                except Exception:
                    pass  # Skip free model detection if pricing lookup fails

                usage_tracker.log_request(
                    request_id=request_id,
                    original_model=request.model,
                    routed_model=routed_model,
                    provider=provider,
                    endpoint=endpoint,
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                    thinking_tokens=reasoning_tokens,
                    duration_ms=duration_ms,
                    estimated_cost=estimated_cost,
                    stream=request.stream if request.stream is not None else False,
                    message_count=message_count,
                    has_system=has_system,
                    has_tools=has_tools,
                    has_images=has_images,
                    status="success",
                    session_id=request_id[:8],
                    client_ip=client_ip,
                    has_json_content=has_json_content,
                    json_size_bytes=json_size_bytes,
                    request_content=req_content,
                    response_content=resp_content,
                    # Extended parameters for detailed analytics
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    reasoning_tokens=reasoning_tokens,
                    cached_tokens=cached_tokens,
                    tool_use_tokens=tool_use_tokens,
                    audio_tokens=audio_tokens,
                    original_cost=original_cost,
                    model_tier=model_tier,
                )
                daily_count = usage_tracker.get_daily_model_request_count(routed_model)
                logger.info(
                    f"Request {request_id}: {routed_model} UTC-day requests={daily_count}"
                )

            claude_response = convert_openai_to_claude_response(
                openai_response, request, provider
            )
            logger.debug(f"Claude response created for request_id: {request_id}")

            # Cache response for deduplication (non-streaming only)
            if ENABLE_DEDUP and request_hash:
                try:
                    # Convert response to dict if it's a model
                    if hasattr(claude_response, "model_dump"):
                        response_dict = claude_response.model_dump()
                    elif hasattr(claude_response, "dict"):
                        response_dict = claude_response.dict()
                    else:
                        response_dict = claude_response
                    request_deduplicator.cache_response(request_hash, response_dict)
                except Exception as cache_err:
                    logger.debug(f"Failed to cache response for dedup: {cache_err}")

            # Dashboard hook: request complete
            dashboard_hooks.on_request_complete(
                request_id,
                "completed",
                {
                    "model": routed_model,
                    "duration_ms": int(duration_ms),
                    "input_tokens": usage.get(
                        "input_tokens", usage.get("prompt_tokens", 0)
                    ),
                    "output_tokens": usage.get(
                        "output_tokens", usage.get("completion_tokens", 0)
                    ),
                    "thinking_tokens": usage.get("thinking_tokens", 0),
                    "tokens": usage.get("total_tokens", 0),
                    "cost": estimated_cost,
                    "tokens_per_sec": int(
                        usage.get("total_tokens", 0) / (duration_ms / 1000)
                    )
                    if duration_ms > 0
                    else 0,
                    "has_tools": has_tools,
                    "has_images": has_images,
                    "context_tokens": input_tokens,
                    "context_limit": context_limit,
                },
            )

            return claude_response
    except HTTPException as e:
        duration_ms = (time.time() - request_start_time) * 1000
        logger.error(
            f"HTTPException in create_message for request_id {request_id}: status={e.status_code}, detail={e.detail}"
        )

        # Log error
        active_logger.log_request_error(
            request_id=request_id, error=e.detail, duration_ms=duration_ms
        )

        # Track error if enabled
        if usage_tracker.enabled:
            usage_tracker.log_request(
                request_id=request_id,
                original_model=request.model,
                routed_model=routed_model,
                provider="unknown",
                endpoint=endpoint,
                status="error",
                error_message=str(e.detail),
                duration_ms=duration_ms,
                session_id=request_id[:8],
                client_ip=client_ip,
            )
        logger.error(
            f"HTTPException in create_message for request_id {request_id}: status={e.status_code}, detail={e.detail}"
        )
        raise
    except Exception as e:
        import traceback

        duration_ms = (time.time() - request_start_time) * 1000
        logger.error(f"Unexpected error processing request {request_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        error_message = openai_client.classify_openai_error(str(e))

        # Log error
        active_logger.log_request_error(
            request_id=request_id, error=error_message, duration_ms=duration_ms
        )

        # Track error if enabled
        if usage_tracker.enabled:
            usage_tracker.log_request(
                request_id=request_id,
                original_model=request.model,
                routed_model="unknown",
                provider="unknown",
                endpoint="unknown",
                status="error",
                error_message=error_message,
                duration_ms=duration_ms,
                session_id=request_id[:8],
                client_ip="unknown",
            )

        # Dashboard hook: request error
        dashboard_hooks.on_request_complete(
            request_id,
            "error",
            {
                "model": routed_model,
                "duration_ms": int(duration_ms),
                "error": error_message,
                "error_type": "Unknown",
            },
        )

        logger.error(f"Unexpected error processing request {request_id}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_message)


@router.post("/v1/messages/count_tokens")
async def count_tokens(
    request: ClaudeTokenCountRequest,
    openai_api_key: Optional[str] = Depends(validate_and_extract_api_key),
):
    try:
        # For token counting, we'll use a simple estimation
        # In a real implementation, you might want to use tiktoken or similar

        total_chars = 0

        # Count system message characters
        if request.system:
            if isinstance(request.system, str):
                total_chars += len(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, "text"):
                        total_chars += len(block.text)

        # Count message characters
        for msg in request.messages:
            if msg.content is None:
                continue
            elif isinstance(msg.content, str):
                total_chars += len(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, "text") and block.text is not None:
                        total_chars += len(block.text)

        # Rough estimation: 4 characters per token
        estimated_tokens = max(1, total_chars // 4)

        return {"input_tokens": estimated_tokens}

    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_api_configured": bool(config.openai_api_key),
        "api_key_valid": config.validate_api_key(),
        "client_api_key_validation": bool(config.anthropic_api_key),
    }


@router.get("/test-connection")
async def test_connection():
    """Test API connectivity to OpenAI"""
    try:
        # Simple test request to verify API connectivity
        # Check if the test model is a newer OpenAI model
        is_newer_model = model_manager.is_newer_openai_model(config.small_model)

        test_request = {
            "model": config.small_model,
            "messages": [{"role": "user", "content": "Hello"}],
        }

        # Newer OpenAI models (o1, o3, o4, gpt-5) require max_completion_tokens and temperature=1
        if is_newer_model:
            test_request["max_completion_tokens"] = 200
            test_request["temperature"] = 1
        else:
            test_request["max_tokens"] = 5

        test_response = await openai_client.create_chat_completion(
            test_request, config=config
        )

        return {
            "status": "success",
            "message": "Successfully connected to OpenAI API",
            "model_used": config.small_model,
            "timestamp": datetime.now().isoformat(),
            "response_id": test_response.get("id", "unknown"),
        }

    except Exception as e:
        logger.error(f"API connectivity test failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "failed",
                "error_type": "API Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "suggestions": [
                    "Check your OPENAI_API_KEY is valid",
                    "Verify your API key has the necessary permissions",
                    "Check if you have reached rate limits",
                ],
            },
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CROSSTALK ENDPOINTS - Model-to-Model Conversations
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/v1/crosstalk/setup")
async def setup_crosstalk(
    request: CrosstalkSetupRequest,
) -> CrosstalkSetupResponse:
    """
    Setup a new crosstalk session.

    This endpoint configures a model-to-model conversation using Exchange-of-Thought
    (EoT) paradigms: Memory, Report, Relay, or Debate.
    """
    try:
        session_id = await crosstalk_orchestrator.setup_crosstalk(
            models=request.models,
            system_prompts=request.system_prompts,
            paradigm=request.paradigm,
            iterations=request.iterations,
            topic=request.topic,
        )

        return CrosstalkSetupResponse(
            session_id=session_id,
            status="configured",
            models=request.models,
            paradigm=request.paradigm,
            iterations=request.iterations,
        )

    except Exception as e:
        logger.error(f"Crosstalk setup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/crosstalk/{session_id}/run")
async def run_crosstalk(
    session_id: str,
) -> CrosstalkRunResponse:
    """
    Execute a configured crosstalk session.

    Runs the model-to-model conversation and returns the complete transcript.
    """
    try:
        start_time = time.time()
        conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)
        duration = time.time() - start_time

        return CrosstalkRunResponse(
            session_id=session_id,
            status="completed",
            conversation=conversation,
            duration_seconds=duration,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Crosstalk execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/crosstalk/{session_id}/status")
async def crosstalk_status(
    session_id: str,
) -> CrosstalkStatusResponse:
    """
    Get the status of a crosstalk session.
    """
    status = crosstalk_orchestrator.get_session_status(session_id)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return CrosstalkStatusResponse(**status)


@router.get("/v1/crosstalk/list")
async def list_crosstalk_sessions() -> CrosstalkListResponse:
    """
    List all active crosstalk sessions.
    """
    sessions = []
    for session_id in crosstalk_orchestrator.active_sessions:
        status = crosstalk_orchestrator.get_session_status(session_id)
        sessions.append(status)

    return CrosstalkListResponse(sessions=sessions, total=len(sessions))


@router.delete("/v1/crosstalk/{session_id}/delete")
async def delete_crosstalk_session(
    session_id: str,
) -> CrosstalkDeleteResponse:
    """
    Delete a completed or errored crosstalk session.
    """
    success = crosstalk_orchestrator.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return CrosstalkDeleteResponse(success=True, message="Session deleted successfully")
