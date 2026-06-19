"""
Model Router

Routes incoming requests to the appropriate model based on use-case signals,
mirroring the Claude Code Router routing strategy:

  default       → general tasks (falls back to BIG_MODEL from env)
  background    → lightweight/background tasks (smaller, cheaper model)
  think         → reasoning-heavy tasks, Plan Mode (thinking model)
  long_context  → requests exceeding long_context_threshold tokens
  web_search    → requests that need live web data (:online suffix for OR)
  image         → image-capable requests (vision model)
  custom        → custom_router.py script for advanced routing logic

Custom Router Contract (Python):
  # custom_router.py
  def route(request: dict, config: object) -> str | None:
      # Return "provider/model" string or None to fall through to default routing
      ...

Custom Router Contract (JavaScript, via Node.js subprocess):
  // custom_router.js
  module.exports = async function route(request, config) {
      return "provider/model" or null;
  }
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Token estimation: ~4 chars per token (rough)
_CHARS_PER_TOKEN = 4


def _estimate_tokens(request: dict) -> int:
    """Rough token estimate from message content length."""
    total_chars = 0
    for msg in request.get("messages", []):
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(
                        str(block.get("text", "") or block.get("content", ""))
                    )
    return total_chars // _CHARS_PER_TOKEN


def _has_image(request: dict) -> bool:
    """Return True if any message contains an image block."""
    for msg in request.get("messages", []):
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image":
                    return True
    return False


def _is_web_search_request(request: dict) -> bool:
    """Return True if the request appears to be a web search task."""
    tools = request.get("tools", [])
    for tool in tools:
        name = tool.get("name", "").lower()
        if any(
            k in name
            for k in ("web_search", "search_web", "brave", "exa", "perplexity")
        ):
            return True
    return False


def _is_background_request(request: dict) -> bool:
    """
    Return True if this is a background / lightweight task.

    Claude Code sends haiku-family models for background work (file scanning,
    auto-complete context, tool result summaries). We detect this from the
    original Claude model name stored in _original_model by endpoints.py,
    or by a low max_tokens cap that signals a cheap background call.
    """
    # Explicit signal set by endpoints.py before conversion
    if request.get("_is_background"):
        return True
    # Original Claude model preserved in the request dict
    orig = request.get("_original_model", "")
    if orig and "haiku" in orig.lower():
        return True
    # Heuristic: very low max_tokens = background/lightweight call
    max_tokens = request.get("max_tokens", 0)
    if max_tokens and max_tokens <= 256:
        return True
    return False


def _has_tools(request: dict) -> bool:
    """Return True if the request contains tool definitions."""
    tools = request.get("tools") or []
    return len(tools) > 0


# Cache of known tool-capable model IDs from OpenRouter enrichment
_tool_capable_cache: set[str] | None = None
_tool_capable_cache_ts: float = 0
_TOOL_CACHE_TTL = 600  # 10 minutes


def _get_tool_capable_models() -> set[str]:
    """Return a set of model IDs known to support tool calling.

    Sources:
    1. Cached OpenRouter free model rankings (supports_tools=True)
    2. TOOLCALL_MODELS from env (always treated as tool-capable)
    """
    global _tool_capable_cache, _tool_capable_cache_ts
    import time

    now = time.time()
    if (
        _tool_capable_cache is not None
        and (now - _tool_capable_cache_ts) < _TOOL_CACHE_TTL
    ):
        return _tool_capable_cache

    capable: set[str] = set()
    # Source 1: free model rankings
    try:
        from src.services.models.free_model_rankings import (
            load_free_model_rankings,
            RANKINGS_PATH,
        )

        rankings = load_free_model_rankings(RANKINGS_PATH)
        for r in rankings:
            if r.supports_tools:
                capable.add(r.model_id)
    except Exception:
        pass

    # Source 2: TOOLCALL_MODELS env var (always treated as capable)
    toolcall_env = os.environ.get("TOOLCALL_MODELS", "")
    if toolcall_env:
        for m in toolcall_env.split(","):
            m = m.strip()
            if m:
                capable.add(m)

    _tool_capable_cache = capable
    _tool_capable_cache_ts = now
    return capable


def _model_supports_tools(model_id: str) -> bool:
    """Return True if the given model is known to support tool calling."""
    if not model_id:
        return False
    # Capability comes from the models.dev-backed registry, NOT hardcoded family
    # names. Hardcoded model/family lists are a known source of routing bugs as the
    # free-model landscape changes; an unknown model must be resolved from data.
    try:
        from src.services.usage.model_limits import (
            supports_tool_call as _registry_supports_tools,
        )

        if _registry_supports_tools(model_id):
            return True
    except Exception:
        pass

    # Dynamic signals: free-model rankings (supports_tools) + TOOLCALL_MODELS env.
    # Match the full id and the bare family id after any provider prefix.
    capable = _get_tool_capable_models()
    return model_id in capable or model_id.split("/")[-1] in capable


def _detect_think_mode(request: dict) -> bool:
    """
    Return True if this is a reasoning/planning request.
    Heuristics: extended_thinking enabled, or system prompt contains planning keywords.
    """
    # Claude extended_thinking param
    if request.get("thinking", {}).get("type") == "enabled":
        return True
    # Plan Mode signature in system prompt
    system = ""
    for msg in request.get("messages", []):
        if msg.get("role") == "system":
            c = msg.get("content", "")
            system = c if isinstance(c, str) else str(c)
            break
    plan_keywords = (
        "plan mode",
        "planning mode",
        "think step by step",
        "think carefully",
    )
    return any(k in system.lower() for k in plan_keywords)


# ─────────────────────────────────────────────────────────────────────────────
# Custom router loader
# ─────────────────────────────────────────────────────────────────────────────


def _load_python_router(path: str):
    """Load a Python custom router module. Returns the route() callable or None."""
    try:
        spec = importlib.util.spec_from_file_location("custom_router", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "route"):
            return mod.route
    except Exception as e:
        logger.error(f"[ModelRouter] Failed to load Python custom router {path}: {e}")
    return None


def _call_js_router(path: str, request: dict, config_dict: dict) -> Optional[str]:
    """Call a JavaScript custom router via Node.js subprocess."""
    wrapper = f"""
const router = require({json.dumps(path)});
const req = {json.dumps(request)};
const cfg = {json.dumps(config_dict)};
(async () => {{
    const result = await router(req, cfg);
    process.stdout.write(JSON.stringify(result ?? null));
}})();
"""
    try:
        result = subprocess.run(
            ["node", "-e", wrapper],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            val = json.loads(result.stdout.strip())
            return val if isinstance(val, str) else None
    except Exception as e:
        logger.error(f"[ModelRouter] JS custom router error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main router
# ─────────────────────────────────────────────────────────────────────────────


class ModelRouter:
    """
    Decides which model to use for a given request.
    Falls back to the configured BIG_MODEL when no route matches.
    """

    def __init__(self, router_config, base_config=None):
        """
        router_config: RouterConfig from proxy_chain.py
        base_config: The main Config object (used for BIG/MIDDLE/SMALL models)
        """
        self._rc = router_config
        self._base = base_config
        self._python_router = None
        self._router_loaded = False

    def _get_python_router(self):
        if self._router_loaded:
            return self._python_router
        self._router_loaded = True
        path = self._rc.custom_router_path
        if path and Path(path).exists():
            if path.endswith(".py"):
                self._python_router = _load_python_router(path)
            # JS handled inline in route()
        return self._python_router

    def route(self, request: dict):
        """
        Return the RouteTarget to use, or None to leave the existing model unchanged.

        Priority:
          0. Disabled/passthrough flags (short-circuit)
          1. Custom router script
          2. Image detection
          3. Web search detection
          4. Long context detection
          5. Think/Plan mode detection
          6. Background task detection (caller must pass metadata)
          7. Default model (or None → caller keeps original)
        """
        rc = self._rc

        # 0. Passthrough or disabled — skip all routing
        if rc.passthrough or rc.disabled:
            return None

        # 0b. IdentifierMapping lookup (FR-003b, FR-003c) — upstream identifier
        # (Anthropic model name, Hermes role, future task type) maps to an
        # explicit Assignment before any tier-based logic fires.
        try:
            from src.core.identifier_mapping import get_registry as get_im_registry
            from src.core.assignments import get_registry as get_assignment_registry
            from src.core.proxy_chain import RouteTarget

            incoming = request.get("_original_model") or request.get("model") or ""
            if incoming:
                mapping = get_im_registry().lookup_by_incoming_identifier(incoming)
                if mapping is not None:
                    target_assignment = get_assignment_registry().get(
                        mapping.assignment_id
                    )
                    if target_assignment is not None and target_assignment.enabled:
                        logger.debug(
                            f"[ModelRouter] IdentifierMapping '{incoming}' → assignment "
                            f"'{target_assignment.id}' (model={target_assignment.model})"
                        )
                        return RouteTarget(
                            model=target_assignment.model,
                            base_url=target_assignment.base_url,
                            api_key=target_assignment.api_key,
                            assignment_id=target_assignment.id,
                        )
        except Exception as e:
            # Registry not yet initialized or unreachable — fall through to tier logic
            logger.debug(f"[ModelRouter] IdentifierMapping lookup skipped: {e}")

        # 1. Custom router — Python
        python_router = self._get_python_router()
        if python_router:
            try:
                config_dict = {
                    "default": rc.default,
                    "background": rc.background,
                    "think": rc.think,
                    "long_context": rc.long_context,
                    "web_search": rc.web_search,
                    "image": rc.image,
                }
                result = python_router(request, config_dict)
                if result:
                    logger.debug(f"[ModelRouter] Custom Python router → {result}")
                    from src.core.proxy_chain import RouteTarget

                    return RouteTarget.from_any(result)
            except Exception as e:
                logger.error(f"[ModelRouter] Custom router exception: {e}")

        # 1b. Custom router — JavaScript
        path = rc.custom_router_path
        if path and path.endswith(".js") and Path(path).exists():
            config_dict = {
                "default": rc.default.to_dict(),
                "background": rc.background.to_dict(),
            }
            result = _call_js_router(path, request, config_dict)
            if result:
                logger.debug(f"[ModelRouter] Custom JS router → {result}")
                from src.core.proxy_chain import RouteTarget

                return RouteTarget.from_any(result)

        # 2. Image
        if rc.image and rc.image.model and _has_image(request):
            logger.debug(f"[ModelRouter] Image request → {rc.image.model}")
            return RouteTarget(
                model=rc.image.model,
                base_url=rc.image.base_url,
                api_key=rc.image.api_key,
                assignment_id="image",
            )

        # 2b. Tool-call routing — when the request has tools[] and the current
        # model doesn't support tool calling, auto-route to the first model
        # from TOOLCALL_MODELS that does.
        if _has_tools(request):
            current_model = request.get("model", "")
            base_config = self._base
            toolcall_auto_route = True
            toolcall_models_list = []
            if base_config is not None:
                toolcall_auto_route = getattr(base_config, "toolcall_auto_route", True)
                toolcall_models_list = getattr(base_config, "toolcall_models", []) or []
            else:
                # Fallback: read directly from env
                toolcall_auto_route = os.environ.get(
                    "TOOLCALL_AUTO_ROUTE", "true"
                ).lower() in ("true", "1", "yes")
                toolcall_env = os.environ.get("TOOLCALL_MODELS", "")
                toolcall_models_list = (
                    [m.strip() for m in toolcall_env.split(",") if m.strip()]
                    if toolcall_env
                    else []
                )

            if toolcall_auto_route and toolcall_models_list:
                if not _model_supports_tools(current_model):
                    # Pick first tool-capable model from the list
                    target_model = toolcall_models_list[0]
                    logger.info(
                        f"[ModelRouter] Tool-call request but '{current_model}' lacks tool support "
                        f"→ re-routing to '{target_model}'"
                    )
                    return RouteTarget(
                        model=target_model,
                        assignment_id="toolcall",
                    )

        # 3. Web search
        if rc.web_search and rc.web_search.model and _is_web_search_request(request):
            logger.debug(f"[ModelRouter] Web search request → {rc.web_search.model}")
            return RouteTarget(
                model=rc.web_search.model,
                base_url=rc.web_search.base_url,
                api_key=rc.web_search.api_key,
                assignment_id="web_search",
            )

        # 4. Long context
        if rc.long_context and rc.long_context.model:
            tokens = _estimate_tokens(request)
            if tokens > rc.long_context_threshold:
                logger.debug(
                    f"[ModelRouter] Long context (~{tokens} tokens) → {rc.long_context.model}"
                )
                return RouteTarget(
                    model=rc.long_context.model,
                    base_url=rc.long_context.base_url,
                    api_key=rc.long_context.api_key,
                    assignment_id="long_context",
                )

        # 5. Think / Plan Mode
        if rc.think and rc.think.model and _detect_think_mode(request):
            logger.debug(f"[ModelRouter] Think mode → {rc.think.model}")
            return RouteTarget(
                model=rc.think.model,
                base_url=rc.think.base_url,
                api_key=rc.think.api_key,
                assignment_id="think",
            )

        # 6. Background task (haiku-family original model or low max_tokens)
        if rc.background and rc.background.model and _is_background_request(request):
            logger.debug(f"[ModelRouter] Background request → {rc.background.model}")
            return RouteTarget(
                model=rc.background.model,
                base_url=rc.background.base_url,
                api_key=rc.background.api_key,
                assignment_id="background",
            )

        # 7. Default (non-empty means explicit override of BIG_MODEL)
        if rc.default and rc.default.model:
            return RouteTarget(
                model=rc.default.model,
                base_url=rc.default.base_url,
                api_key=rc.default.api_key,
                assignment_id="default",
            )

        # 7. No override — caller keeps existing model
        return None


# ── Module-level singleton ────────────────────────────────────────────────────

_router: Optional[ModelRouter] = None


def get_router(config=None) -> ModelRouter:
    """
    Return the module-level router, initializing if needed.

    When a Config object is supplied, env-var overrides (ROUTER_*) are merged
    on top of the proxy_chain.json router section so that .env always wins.
    """
    global _router
    if _router is None:
        from src.core.proxy_chain import get_chain, RouterConfig

        chain = get_chain()
        rc = chain.router

        # Merge env-var overrides from Config if available
        if config is not None:
            rc = RouterConfig(
                default=getattr(config, "router_default", rc.default) or rc.default,
                background=getattr(config, "router_background", rc.background)
                or rc.background,
                think=getattr(config, "router_think", rc.think) or rc.think,
                long_context=getattr(config, "router_long_context", rc.long_context)
                or rc.long_context,
                long_context_threshold=getattr(
                    config, "router_long_context_threshold", rc.long_context_threshold
                ),
                web_search=getattr(config, "router_web_search", rc.web_search)
                or rc.web_search,
                image=getattr(config, "router_image", rc.image) or rc.image,
                custom_router_path=getattr(
                    config, "router_custom_path", rc.custom_router_path
                )
                or rc.custom_router_path,
            )

        _router = ModelRouter(rc, base_config=config)
    return _router


def reload_router(config=None) -> ModelRouter:
    """Force reload router from chain config."""
    global _router
    from src.core.proxy_chain import get_chain, reload_chain

    chain = reload_chain()
    _router = ModelRouter(chain.router, base_config=config)
    return _router
