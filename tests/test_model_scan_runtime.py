"""Runtime binding tests for the model-scan integration.

These cover the mutable wiring around the pure binder: preserving config, reloading a snapshot,
updating static tier assignments, and exposing per-profile overlays without request-time file IO.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.assignments import Assignment
from src.core.profiles import resolve_profile
from src.core.proxy_chain import ProxyChain


def test_proxy_chain_preserves_model_scan_config():
    data = {
        "schema_version": "2.0.0",
        "entries": [],
        "router": {},
        "assignments": [],
        "identifier_mappings": [],
        "model_scan": {
            "enabled": True,
            "policy": "free",
            "snapshot_path": "~/.config/model-scan/routing_snapshot.json",
            "gateway_url": "http://127.0.0.1:7099/routing-snapshot",
            "cache_ttl_s": 300,
            "staleness_limit_s": 86400,
        },
    }

    chain = ProxyChain.from_dict(data)

    serialized = chain.to_dict()["model_scan"]
    for key, value in data["model_scan"].items():
        assert serialized[key] == value
    assert serialized["lanes"]["standby"]["allow_paid"] is False


def test_resolve_profile_deep_merges_slot_bindings(tmp_path):
    profiles = {
        "default": {
            "slot_bindings": {
                "big": "R1_primary",
                "middle": "R2_fast",
            }
        },
        "codex": {
            "slot_bindings": {
                "middle": "R8_web_extract",
            }
        },
    }
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps(profiles))

    resolved = resolve_profile("codex", p)

    assert resolved.get("slot_bindings") == {
        "big": "R1_primary",
        "middle": "R8_web_extract",
    }


def test_reload_model_scan_updates_assignments_and_overlay(monkeypatch, tmp_path):
    from src.core import proxy_chain as proxy_chain_module
    from src.core import model_scan_runtime

    repo_root = Path(__file__).resolve().parents[1]
    snapshot_path = repo_root / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"
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
                        "cascade": ["static/fallback"],
                    },
                    {
                        "id": "middle",
                        "kind": "tier",
                        "model": "static/middle",
                        "provider": "static",
                        "base_url": "",
                        "api_key": "",
                        "enabled": True,
                        "cascade": [],
                    },
                ],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(snapshot_path),
                    "cache_ttl_s": 300,
                    "staleness_limit_s": 315360000,
                },
            }
        )
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "default": {
                    "slot_bindings": {
                        "big": "R1_primary",
                        "middle": "R_curator",
                    }
                },
                "codex": {
                    "slot_bindings": {
                        "big": "R8_web_extract",
                    }
                },
            }
        )
    )

    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()

    summary = model_scan_runtime.reload_model_scan(profiles_path=profiles_path)

    assert summary["enabled"] is True
    assert summary["scan_id"] == 1487
    chain = proxy_chain_module.reload_chain()
    big = next(a for a in chain.assignments if a.id == "big")
    middle = next(a for a in chain.assignments if a.id == "middle")
    assert big.model == "openrouter/deepseek/deepseek-v4-flash:free"
    assert big.provider == "openrouter"
    assert middle.model == "static/middle"
    overlay = model_scan_runtime.resolve_profile_binding("codex", "big")
    assert overlay is not None
    assert overlay.api_model == "ollama_cloud/qwen3-coder-next:cloud"


def test_reload_model_scan_missing_snapshot_keeps_previous_assignments(monkeypatch, tmp_path):
    from src.core import proxy_chain as proxy_chain_module
    from src.core import model_scan_runtime

    chain_path = tmp_path / "proxy_chain.json"
    missing = tmp_path / "missing.json"
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
                        "cascade": ["static/fallback"],
                    }
                ],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(missing),
                    "cache_ttl_s": 300,
                    "staleness_limit_s": 315360000,
                },
            }
        )
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}))

    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()

    summary = model_scan_runtime.reload_model_scan(profiles_path=profiles_path)

    assert summary["changed"] is False
    assert summary["error"] == "no valid snapshot"
    chain = proxy_chain_module.reload_chain()
    big = next(a for a in chain.assignments if a.id == "big")
    assert big.model == "static/big"


def test_reload_model_scan_disabled_is_static_baseline(monkeypatch, tmp_path):
    from src.core import proxy_chain as proxy_chain_module
    from src.core import model_scan_runtime

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
                        "cascade": ["static/fallback"],
                    }
                ],
                "identifier_mappings": [],
                "model_scan": {"enabled": False, "policy": "static"},
            }
        )
    )
    before = json.loads(chain_path.read_text())

    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    proxy_chain_module.reload_chain()
    summary = model_scan_runtime.reload_model_scan()

    assert summary == {
        "enabled": False,
        "changed": False,
        "scan_id": None,
        "schema_version": "",
        "global_tiers": {},
        "overlay_profiles": [],
        "provenance": {},
        "error": "",
    }
    assert json.loads(chain_path.read_text()) == before


def test_concurrent_ephemeral_profiles_survive_rebind(monkeypatch, tmp_path):
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module
    from src.core import model_scan_runtime

    repo_root = Path(__file__).resolve().parents[1]
    snapshot_path = repo_root / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"
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
                    "snapshot_path": str(snapshot_path),
                    "staleness_limit_s": 315360000,
                },
            }
        )
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}))

    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", profiles_path)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()

    for i in range(12):
        profiles.register_ephemeral_profile(
            preset="default",
            overlay={"slot_bindings": {"big": "R8_web_extract"}},
            profile_id=f"session-{i}",
        )

    def resolve_and_bind(name: str) -> str:
        model_scan_runtime.reload_model_scan(profiles_path=profiles_path)
        binding = model_scan_runtime.resolve_profile_binding(name, "big")
        return binding.api_model if binding else ""

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(resolve_and_bind, [f"session-{i}" for i in range(12)]))

    assert len(results) == 12
    assert all(result for result in results)
