"""
Per-CLI Profile Routing.

Each HTTP request can activate a named profile that overlays per-slot model
configuration on top of the proxy's global router/cascade settings. Profiles
are selected by URL path prefix: /p/{name}/v1/... activates profile {name}.

Architectural rules (per Option C-slim plan):
  1. Profiles are overlays on existing slot routing, not a replacement.
  2. Profile resolution happens once at request entry, rides on a contextvar.
  3. No global state mutation, no env-var rewriting, no per-CLI proxy instances.

Profile schema (flat dict; unknown keys ignored for forward compat):
  - notes:                  str  — human bookkeeping, ignored by router
  - toolcall_models:        list — override TOOLCALL_MODELS for this request
  - force_main:             str  — replace request.model BEFORE cascade
  - tier_overrides:         dict — per-tier model swap applied AFTER tier
                                    resolution. Format: {"small": "owl-alpha",
                                    "middle": "...", "big": "..."}. Lets a
                                    profile route haiku→cheap-model invisibly
                                    while preserving opus/sonnet routing.
  - tier_providers:         dict — per-tier provider swap applied with
                                    tier_overrides. Format:
                                    {"big": "cliproxyapi", "middle": "openrouter"}.
                                    Provider names resolve through PROVIDERS_*.
  - slot_bindings:          dict — model-scan role bindings by assignment id.
                                    Format: {"big": "R1_primary"}.
  - spoof_response_model:   bool — when tier_overrides (or future force_main)
                                    swaps the model, rewrite the upstream
                                    response's `model` field back to what the
                                    client requested. Default True = invisible.
                                    Set False to surface the real upstream
                                    model in responses (e.g. for debugging).
                                    Anthropic /v1/messages path is already
                                    invisible by construction (response
                                    converter uses request.model). This flag
                                    only affects OpenAI /v1/chat/completions.
  - web_search:             str  — model to dispatch web-search tool calls to
  - web_search_pattern:     str  — regex matching tool names (default below)
  - web_search_intercept:   bool — disable interception if False
  - subagent_model:         str  — reserved for future subagent routing
  - provider_override:      str  — force a specific provider entry from the
                                    PROVIDERS_* env registry (e.g. "openrouter",
                                    "anthropic"). Resolved via
                                    config.get_provider_endpoint/api_key.

The reserved profile name 'default' must exist; startup fails otherwise.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULT_PROFILES_PATH = (
    Path(os.environ.get("PROFILES_FILE"))
    if os.environ.get("PROFILES_FILE")
    else Path(__file__).parent.parent.parent / "profiles" / "profiles.json"
)

DEFAULT_WEB_SEARCH_PATTERN = re.compile(
    r"^(web_search|search_web|brave_search|exa_search|google_search|fetch_url)$",
    re.IGNORECASE,
)


# ── ProfileContext ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProfileContext:
    """Resolved profile for a single request. Immutable; rides on a contextvar."""

    name: str
    slots: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.slots.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.slots and self.slots[key] is not None and self.slots[key] != ""


# ── Request-scoped active profile ────────────────────────────────────────────
# contextvars are per-task in asyncio: each FastAPI request gets its own value.
# Reading from anywhere in the call stack returns the value set by THIS request.
# Tests and direct calls without setting it just see None (= default behavior).

ACTIVE_PROFILE: contextvars.ContextVar[Optional[ProfileContext]] = contextvars.ContextVar(
    "active_profile", default=None
)


def current_profile_name() -> Optional[str]:
    """Return the active profile name for this request, or None if unprefixed.

    Convenience helper for callers (usage_tracker, dashboards) that just need
    the name string and don't want to import ProfileContext.
    """
    p = ACTIVE_PROFILE.get()
    return p.name if p else None


# ── File cache (mtime-invalidated) ────────────────────────────────────────────

_cache: Dict[str, Any] = {}
_cache_mtime: float = 0.0
_cache_path: Optional[Path] = None
_ephemeral_profiles: Dict[str, Dict[str, Any]] = {}


def _load_from_disk(path: Path) -> Dict[str, Any]:
    """Read and parse profiles.json. Returns the raw dict."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning(f"profiles.json not found at {path}; profile routing disabled")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"profiles.json is malformed: {e}; ignoring profile routing")
        return {}


def _refresh_cache(path: Optional[Path] = None) -> Dict[str, Any]:
    """Reload profiles from disk if the file's mtime changed since last read."""
    global _cache, _cache_mtime, _cache_path
    p = path or DEFAULT_PROFILES_PATH
    try:
        mtime = p.stat().st_mtime
    except OSError:
        _cache = {}
        _cache_mtime = 0.0
        return _cache
    if p != _cache_path or mtime != _cache_mtime:
        _cache = _load_from_disk(p)
        _cache_mtime = mtime
        _cache_path = p
        logger.debug(f"Reloaded profiles from {p} (mtime={mtime})")
    return _cache


# ── Public API ────────────────────────────────────────────────────────────────


def get_all_profiles(path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Return the full profiles dict, refreshing from disk if mtime changed."""
    sweep_ephemeral_profiles()
    merged = dict(_refresh_cache(path))
    merged.update({name: item["slots"] for name, item in _ephemeral_profiles.items()})
    return merged


def has_profile(name: str, path: Optional[Path] = None) -> bool:
    sweep_ephemeral_profiles()
    return name in _ephemeral_profiles or name in _refresh_cache(path)


def resolve_profile(name: str, path: Optional[Path] = None) -> ProfileContext:
    """
    Return a ProfileContext for the named profile, overlaid on 'default'.

    If `name` is missing or unknown, returns the 'default' profile (if it
    exists) or an empty ProfileContext.
    """
    profiles = get_all_profiles(path)
    default = dict(profiles.get("default", {}))
    if name and name != "default" and name in profiles:
        # Overlay named profile onto default; named keys win
        named = profiles[name]
        merged = {**default, **named}
        for key in ("slot_bindings", "tier_overrides"):
            if isinstance(default.get(key), dict) or isinstance(named.get(key), dict):
                merged[key] = {
                    **(default.get(key) if isinstance(default.get(key), dict) else {}),
                    **(named.get(key) if isinstance(named.get(key), dict) else {}),
                }
    else:
        merged = default
    return ProfileContext(name=name or "default", slots=merged)


def register_ephemeral_profile(
    *,
    preset: str = "default",
    overlay: Optional[Dict[str, Any]] = None,
    ttl_s: int = 3600,
    profile_id: Optional[str] = None,
) -> ProfileContext:
    """Register a temporary profile overlay and return its resolved context."""
    base = resolve_profile(preset).slots
    slots = {**base, **(overlay or {})}
    for key in ("slot_bindings", "tier_overrides"):
        if isinstance(base.get(key), dict) or isinstance((overlay or {}).get(key), dict):
            slots[key] = {
                **(base.get(key) if isinstance(base.get(key), dict) else {}),
                **((overlay or {}).get(key) if isinstance((overlay or {}).get(key), dict) else {}),
            }
    name = profile_id or f"{preset}-{uuid.uuid4().hex[:8]}"
    _ephemeral_profiles[name] = {
        "slots": slots,
        "preset": preset,
        "created_at": time.time(),
        "expires_at": time.time() + max(1, int(ttl_s)),
    }
    return ProfileContext(name=name, slots=slots)


def delete_ephemeral_profile(name: str) -> bool:
    """Delete a temporary profile. Returns True when it existed."""
    return _ephemeral_profiles.pop(name, None) is not None


def sweep_ephemeral_profiles(now: Optional[float] = None) -> int:
    """Remove expired temporary profiles and return the number removed."""
    current = now if now is not None else time.time()
    expired = [
        name for name, item in _ephemeral_profiles.items()
        if float(item.get("expires_at", 0)) <= current
    ]
    for name in expired:
        _ephemeral_profiles.pop(name, None)
    return len(expired)


def list_ephemeral_profiles() -> Dict[str, Dict[str, Any]]:
    sweep_ephemeral_profiles()
    return dict(_ephemeral_profiles)


def extract_profile_from_path(path: str) -> tuple[Optional[str], str]:
    """
    Strip a /p/{name} prefix from a URL path.

    Returns (profile_name, rewritten_path). If no /p/ prefix, returns (None, path).

    Examples:
      "/p/pi/v1/chat/completions"  → ("pi", "/v1/chat/completions")
      "/v1/messages"               → (None, "/v1/messages")
      "/p/default/v1/messages"     → ("default", "/v1/messages")
    """
    if not path.startswith("/p/"):
        return None, path
    rest = path[3:]  # drop "/p/"
    slash = rest.find("/")
    if slash == -1:
        return rest or None, "/"
    return rest[:slash] or None, rest[slash:]


def validate_startup(path: Optional[Path] = None) -> Optional[str]:
    """
    Run at proxy startup. Returns an error string if the profile system is
    misconfigured, or None if ready.

    The 'default' profile must exist. Missing profiles.json is acceptable
    (profile routing becomes a no-op), but a malformed or default-less file
    is a hard failure since it would silently misroute requests.
    """
    p = path or DEFAULT_PROFILES_PATH
    if not p.exists():
        return None  # profiles.json missing → graceful degradation
    profiles = _refresh_cache(p)
    if not profiles:
        return f"profiles file {p} exists but is empty/malformed"
    if "default" not in profiles:
        return (
            f"profiles file {p} lacks required 'default' profile. "
            f"Found profiles: {sorted(profiles.keys())}"
        )
    return None


# ── Web-search tool detection ─────────────────────────────────────────────────


def is_web_search_request(
    request_body: Dict[str, Any],
    profile_ctx: ProfileContext,
) -> bool:
    """
    Check if this request is dispatching a web-search tool call exclusively.

    The swap fires only when:
      - The profile defines a web_search model AND web_search_intercept != False
      - The request body's tools array contains at least one tool whose name
        (or anthropic-style 'type') matches the web_search_pattern regex
      - AND either tool_choice forces that tool, OR the web-search tool is
        the only tool listed (so we won't break multi-tool reasoning turns)

    Operates on both OpenAI ({"tools": [{"function": {"name": "..."}}]}) and
    Anthropic ({"tools": [{"name": "..."} or {"type": "web_search_20250305"}]})
    request shapes.
    """
    if not profile_ctx.has("web_search"):
        return False
    if profile_ctx.get("web_search_intercept") is False:
        return False

    tools = request_body.get("tools") or []
    if not tools:
        return False

    pattern_str = profile_ctx.get("web_search_pattern")
    pattern = (
        re.compile(pattern_str, re.IGNORECASE)
        if pattern_str
        else DEFAULT_WEB_SEARCH_PATTERN
    )

    def _is_web_search_tool(tool: Dict[str, Any]) -> bool:
        # Anthropic-style: top-level "name" or "type"
        name = tool.get("name", "") or ""
        ttype = tool.get("type", "") or ""
        if "web_search" in ttype.lower():
            return True
        if name and pattern.match(name):
            return True
        # OpenAI-style: nested function.name
        fn = tool.get("function") or {}
        fn_name = fn.get("name", "") or ""
        if fn_name and pattern.match(fn_name):
            return True
        return False

    web_search_tools = [t for t in tools if _is_web_search_tool(t)]
    if not web_search_tools:
        return False

    # Don't swap if request mixes web-search with other tools and doesn't force one
    if len(tools) > 1:
        tool_choice = request_body.get("tool_choice")
        if isinstance(tool_choice, dict):
            tc_name = (tool_choice.get("function") or {}).get("name") or tool_choice.get("name", "")
            if not pattern.match(tc_name or ""):
                return False
        elif tool_choice in (None, "auto", "any"):
            # Auto/any/None with mixed tools = let main model decide
            return False
    return True
