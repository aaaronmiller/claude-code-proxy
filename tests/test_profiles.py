"""Tests for src/core/profiles.py — Option C-slim profile routing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.profiles import (
    ProfileContext,
    extract_profile_from_path,
    is_web_search_request,
    resolve_profile,
    validate_startup,
)


@pytest.fixture
def tmp_profiles(tmp_path: Path) -> Path:
    """Write a small profiles.json into a temp dir, return its path."""
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps({
        "default": {
            "toolcall_models": ["primary-model", "fallback-model"],
            "web_search": "web-model",
            "web_search_pattern": "^(web_search|search_web)$",
        },
        "pi": {
            "toolcall_models": ["pi-tool-model"],
            "web_search": "pi-web-model",
        },
        "no_intercept": {
            "web_search": "should-not-fire",
            "web_search_intercept": False,
        },
        "force_main_profile": {
            "force_main": "forced-main-model",
        },
    }))
    return p


# ── Path extraction ───────────────────────────────────────────────────────────


def test_extract_profile_strips_prefix():
    assert extract_profile_from_path("/p/pi/v1/chat/completions") == ("pi", "/v1/chat/completions")


def test_extract_profile_no_prefix_returns_none():
    assert extract_profile_from_path("/v1/messages") == (None, "/v1/messages")


def test_extract_profile_with_default_name():
    assert extract_profile_from_path("/p/default/v1/messages") == ("default", "/v1/messages")


def test_extract_profile_root_only():
    assert extract_profile_from_path("/p/pi") == ("pi", "/")


# ── Resolution + overlay ──────────────────────────────────────────────────────


def test_resolve_default_when_no_name(tmp_profiles):
    ctx = resolve_profile("", path=tmp_profiles)
    assert ctx.get("web_search") == "web-model"
    assert ctx.get("toolcall_models") == ["primary-model", "fallback-model"]


def test_resolve_named_overlays_default(tmp_profiles):
    ctx = resolve_profile("pi", path=tmp_profiles)
    # pi overrides toolcall_models and web_search
    assert ctx.get("toolcall_models") == ["pi-tool-model"]
    assert ctx.get("web_search") == "pi-web-model"
    # Inherits web_search_pattern from default
    assert ctx.get("web_search_pattern") == "^(web_search|search_web)$"


def test_resolve_unknown_falls_back_to_default(tmp_profiles):
    ctx = resolve_profile("nonexistent", path=tmp_profiles)
    assert ctx.get("web_search") == "web-model"


def test_profile_context_has_filters_empty(tmp_profiles):
    ctx = resolve_profile("pi", path=tmp_profiles)
    assert ctx.has("web_search") is True
    assert ctx.has("nonexistent_key") is False


# ── Startup validation ────────────────────────────────────────────────────────


def test_startup_validation_passes_with_default(tmp_profiles):
    assert validate_startup(tmp_profiles) is None


def test_startup_validation_fails_without_default(tmp_path):
    bad = tmp_path / "no-default.json"
    bad.write_text(json.dumps({"pi": {"web_search": "x"}}))
    err = validate_startup(bad)
    assert err is not None
    assert "default" in err


def test_startup_validation_graceful_when_file_missing(tmp_path):
    """Missing profiles.json should NOT fail startup — profile routing just degrades."""
    assert validate_startup(tmp_path / "absent.json") is None


# ── Web-search detection ──────────────────────────────────────────────────────


def test_web_search_detected_openai_shape(tmp_profiles):
    ctx = resolve_profile("default", path=tmp_profiles)
    req = {
        "model": "main-model",
        "tools": [{"type": "function", "function": {"name": "web_search"}}],
    }
    assert is_web_search_request(req, ctx) is True


def test_web_search_detected_anthropic_shape(tmp_profiles):
    ctx = resolve_profile("default", path=tmp_profiles)
    req = {
        "model": "main-model",
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }
    assert is_web_search_request(req, ctx) is True


def test_web_search_skipped_when_no_tools(tmp_profiles):
    ctx = resolve_profile("default", path=tmp_profiles)
    assert is_web_search_request({"model": "main"}, ctx) is False


def test_web_search_skipped_when_profile_lacks_web_search(tmp_path):
    p = tmp_path / "no-ws.json"
    p.write_text(json.dumps({"default": {"toolcall_models": []}}))
    ctx = resolve_profile("default", path=p)
    req = {"tools": [{"function": {"name": "web_search"}}]}
    assert is_web_search_request(req, ctx) is False


def test_web_search_skipped_when_intercept_disabled(tmp_profiles):
    ctx = resolve_profile("no_intercept", path=tmp_profiles)
    req = {"tools": [{"function": {"name": "web_search"}}]}
    assert is_web_search_request(req, ctx) is False


def test_web_search_skipped_when_mixed_tools_no_choice(tmp_profiles):
    """Multi-tool turn without explicit tool_choice = main model decides."""
    ctx = resolve_profile("default", path=tmp_profiles)
    req = {
        "tools": [
            {"function": {"name": "web_search"}},
            {"function": {"name": "calculator"}},
        ],
        "tool_choice": "auto",
    }
    assert is_web_search_request(req, ctx) is False


def test_web_search_fires_when_tool_choice_forces_it(tmp_profiles):
    """Mixed tools but tool_choice forces web-search → swap fires."""
    ctx = resolve_profile("default", path=tmp_profiles)
    req = {
        "tools": [
            {"function": {"name": "web_search"}},
            {"function": {"name": "calculator"}},
        ],
        "tool_choice": {"type": "function", "function": {"name": "web_search"}},
    }
    assert is_web_search_request(req, ctx) is True


# ── Force-main ────────────────────────────────────────────────────────────────


def test_force_main_value_accessible(tmp_profiles):
    ctx = resolve_profile("force_main_profile", path=tmp_profiles)
    assert ctx.has("force_main") is True
    assert ctx.get("force_main") == "forced-main-model"


def test_current_profile_name_helper(tmp_profiles):
    """current_profile_name() returns the active profile or None."""
    from src.core.profiles import ACTIVE_PROFILE, current_profile_name
    assert current_profile_name() is None  # default state
    ctx = resolve_profile("pi", path=tmp_profiles)
    token = ACTIVE_PROFILE.set(ctx)
    try:
        assert current_profile_name() == "pi"
    finally:
        ACTIVE_PROFILE.reset(token)
    assert current_profile_name() is None  # cleared after reset


def test_usage_tracker_accepts_profile_column(tmp_path):
    """log_request accepts profile= without error and stores it."""
    import sqlite3
    from src.services.usage.usage_tracker import UsageTracker
    db = tmp_path / "test_usage.db"
    tracker = UsageTracker(db_path=str(db), enabled=True)
    tracker.log_request(
        request_id="r1",
        original_model="claude-haiku-4-5",
        routed_model="minimax/minimax-m2.5:free",
        provider="openrouter",
        endpoint="chat/completions",
        profile="pi",
    )
    conn = sqlite3.connect(str(db))
    row = conn.execute(
        "SELECT profile FROM api_requests WHERE request_id='r1'"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "pi"


def test_routing_profiles_api_lists_and_resolves(tmp_path, monkeypatch):
    """The /api/routing-profiles endpoint returns merged overlays + request counts."""
    p = tmp_path / "rp.json"
    p.write_text(json.dumps({
        "default": {"toolcall_models": ["x"], "notes": "default"},
        "pi": {"web_search": "ws", "notes": "pi notes"},
    }))
    # Re-point the resolver's default path to our tmp file
    from src.core import profiles as profmod
    monkeypatch.setattr(profmod, "DEFAULT_PROFILES_PATH", p)
    profmod._cache = {}  # force reload
    profmod._cache_mtime = 0.0
    profmod._cache_path = None

    from src.api.routing_profiles_api import list_routing_profiles
    import asyncio
    result = asyncio.run(list_routing_profiles(hours=24))
    names = [pr["name"] for pr in result["profiles"]]
    assert "default" in names
    assert "pi" in names
    pi_entry = next(pr for pr in result["profiles"] if pr["name"] == "pi")
    # pi inherits toolcall_models from default
    assert pi_entry["resolved"]["toolcall_models"] == ["x"]
    # And has its own web_search
    assert pi_entry["resolved"]["web_search"] == "ws"
    assert result["default_exists"] is True


def test_spoof_response_model_defaults_true(tmp_path):
    """spoof_response_model is implicit-True (not present in profile = invisible swap)."""
    p = tmp_path / "spoof.json"
    p.write_text(json.dumps({
        "default": {"toolcall_models": ["x"]},
        "claude": {
            "tier_overrides": {"small": "openrouter/owl-alpha"},
        },
        "claude_debug": {
            "tier_overrides": {"small": "openrouter/owl-alpha"},
            "spoof_response_model": False,
        },
    }))
    invisible = resolve_profile("claude", path=p)
    # When the key is absent, .get() returns None — the OpenAI handler treats
    # `is not False` as the truth condition, so spoof fires.
    assert invisible.get("spoof_response_model") is None  # absent = default-True
    visible = resolve_profile("claude_debug", path=p)
    assert visible.get("spoof_response_model") is False  # explicit suppress


def test_tier_overrides_profile_key(tmp_path):
    """tier_overrides resolves per-tier model swaps from default + named profile."""
    p = tmp_path / "to.json"
    p.write_text(json.dumps({
        "default": {"toolcall_models": ["x"]},
        "claude": {
            "tier_overrides": {"small": "openrouter/owl-alpha"},
            "toolcall_models": ["qwen-tool"],
        },
    }))
    ctx = resolve_profile("claude", path=p)
    assert ctx.has("tier_overrides") is True
    overrides = ctx.get("tier_overrides")
    assert isinstance(overrides, dict)
    assert overrides.get("small") == "openrouter/owl-alpha"
    # Inherits default toolcall_models? No — named profile overrides.
    assert ctx.get("toolcall_models") == ["qwen-tool"]


def test_provider_override_in_profile_schema(tmp_path):
    """provider_override is accepted as a profile key (Phase 4)."""
    p = tmp_path / "po.json"
    p.write_text(json.dumps({
        "default": {"toolcall_models": ["a"]},
        "via_anthropic": {"provider_override": "anthropic"},
    }))
    ctx = resolve_profile("via_anthropic", path=p)
    assert ctx.has("provider_override") is True
    assert ctx.get("provider_override") == "anthropic"
    # Default toolcall_models still inherited
    assert ctx.get("toolcall_models") == ["a"]
