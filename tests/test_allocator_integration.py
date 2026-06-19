"""F18 end-to-end: ALLOCATOR_ENABLED + session_profiles in the chain make reload run the
allocator over the routing snapshot and write per-profile overlays that the request path already
reads via resolve_profile_binding(). Proves: (1) the seam fires at reload, (2) value_sensitivity
differentiates sessions, (3) the true api_model/base_url are recovered from the snapshot (not the
allocator's internal model_id), (4) disabled / no-profile is a safe no-op.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


def _write_chain(tmp_path, *, allocator_enabled, session_profiles, static_quota=None):
    chain_path = tmp_path / "proxy_chain.json"
    chain_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "entries": [],
                "router": {},
                "assignments": [
                    {
                        "id": "big",
                        "kind": "tier",
                        "model": "static/big",
                        "provider": "static",
                        "base_url": "",
                        "api_key": "",
                        "enabled": True,
                        "cascade": [],
                    }
                ],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(SNAPSHOT),
                    "staleness_limit_s": 315360000,
                    "allocator_enabled": allocator_enabled,
                    "session_profiles": session_profiles,
                    # role "big" pulls its candidate pool from the snapshot's R1_primary slot
                    "allocator_slot_map": {"big": "R1_primary"},
                    "static_quota": static_quota or {},
                    "quota_nominal_calls": 1000.0,
                },
            }
        )
    )
    return chain_path


# Two sessions over the SAME slot (R1_primary: opus fit96.4 $18, deepseek fit81.2 $0, both tools).
_PROFILES = {
    "rich": {"roles": {"big": {"value_sensitivity": 0.9, "importance": 0.9,
                               "floor": {"needs_tools": True}}}},
    "econ": {"roles": {"big": {"value_sensitivity": 0.1, "importance": 0.4,
                               "floor": {"needs_tools": True}}}},
}


def _reload(monkeypatch, chain_path, profiles_path):
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    # isolate from this machine's live quota sources (ccusage/tokscale): static_quota only
    monkeypatch.setattr("src.core.quota_runtime._default_live_sources", lambda: [])
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()
    return model_scan_runtime.reload_model_scan(profiles_path=profiles_path)


def test_allocator_routes_sessions_by_value_sensitivity(monkeypatch, tmp_path):
    from src.core import model_scan_runtime

    chain_path = _write_chain(
        tmp_path, allocator_enabled=True, session_profiles=_PROFILES,
        static_quota={"anthropic": 1.0, "openrouter": 1.0},
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({}))  # no slot_bindings: allocator drives overlays alone

    summary = _reload(monkeypatch, chain_path, profiles_path)
    assert summary["enabled"] is True

    rich = model_scan_runtime.resolve_profile_binding("rich", "big")
    econ = model_scan_runtime.resolve_profile_binding("econ", "big")
    assert rich is not None and econ is not None
    # maximizing session -> highest fitness (opus); api_model is the snapshot's, not "claude-opus-4-8"
    assert rich.api_model == "anthropic/claude-opus-4-8"
    assert rich.provider == "anthropic"
    assert rich.source == "allocator"
    # satisficing session -> abundant, cheaper floor-clearing model (deepseek)
    assert econ.api_model == "openrouter/deepseek/deepseek-v4-flash:free"
    assert econ.provider == "openrouter"


def test_allocator_reports_into_summary(monkeypatch, tmp_path):
    chain_path = _write_chain(
        tmp_path, allocator_enabled=True, session_profiles=_PROFILES,
        static_quota={"anthropic": 1.0, "openrouter": 1.0},
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({}))
    summary = _reload(monkeypatch, chain_path, profiles_path)

    alloc = summary["allocator"]
    assert alloc["enabled"] is True
    assert set(alloc["profiles"]) == {"rich", "econ"}
    assert alloc["profiles"]["rich"]["big"] == "anthropic/claude-opus-4-8"
    assert alloc["roles"] == 2


def test_allocator_disabled_is_noop(monkeypatch, tmp_path):
    from src.core import model_scan_runtime

    chain_path = _write_chain(
        tmp_path, allocator_enabled=False, session_profiles=_PROFILES,
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}))
    summary = _reload(monkeypatch, chain_path, profiles_path)

    # no allocator overlay produced; the normal slot-binding path still works
    assert summary["allocator"]["enabled"] is False
    assert model_scan_runtime.resolve_profile_binding("rich", "big") is None


def test_allocator_enabled_but_no_profiles_is_noop(monkeypatch, tmp_path):
    chain_path = _write_chain(
        tmp_path, allocator_enabled=True, session_profiles={},
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}))
    summary = _reload(monkeypatch, chain_path, profiles_path)
    assert summary["allocator"]["enabled"] is False
