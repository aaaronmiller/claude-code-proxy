"""Runtime binding tests for the model-scan integration.

These cover the in-memory dynamic layer, exact static fallback, provider joins,
and per-profile overlays without request-time file IO.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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


def test_reload_model_scan_activates_overlay_without_persisting(monkeypatch, tmp_path):
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
                        "xbig": "R1_primary",
                        "big": "R1_primary",
                        "middle": "R_curator",
                        "small": "R1_primary",
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
    assert summary["activation"] == "in_memory_overlay"
    assert summary["persistent_writes"] == []
    chain = proxy_chain_module.reload_chain()
    big = next(a for a in chain.assignments if a.id == "big")
    middle = next(a for a in chain.assignments if a.id == "middle")
    assert big.model == "static/big"
    assert big.provider == "static"
    assert middle.model == "static/middle"
    default = model_scan_runtime.resolve_profile_binding("default", "big")
    assert default is not None
    assert default.api_model == "openrouter/deepseek/deepseek-v4-flash:free"
    assert model_scan_runtime.resolve_profile_binding("default", "xbig") is not None
    assert model_scan_runtime.resolve_profile_binding("default", "middle") is not None
    assert model_scan_runtime.resolve_profile_binding("default", "small") is not None
    overlay = model_scan_runtime.resolve_profile_binding("codex", "big")
    assert overlay is not None
    assert overlay.api_model == "ollama_cloud/qwen3-coder-next:cloud"


def test_callable_binding_requires_provider_url_and_key(monkeypatch):
    from src.core import model_scan_runtime
    from src.core.model_scan_binder import BindResult, ResolvedBinding

    binding = ResolvedBinding(
        api_model="poolside/laguna-xs-2.1:free",
        base_url="",
        cascade=(),
        source="snapshot",
        provider="openrouter",
        role="S01_haiku",
    )
    monkeypatch.setattr(
        model_scan_runtime,
        "_ACTIVE_BINDING",
        BindResult(global_tiers={"small": binding}),
    )

    class Config:
        def __init__(self, *, endpoint="", key=""):
            self.endpoint = endpoint
            self.key = key

        def get_provider_endpoint(self, provider):
            return self.endpoint if provider == "openrouter" else None

        def get_provider_api_key(self, provider):
            return self.key if provider == "openrouter" else None

    assert model_scan_runtime.resolve_callable_binding("default", "small", Config()) is None
    assert (
        model_scan_runtime.resolve_callable_binding(
            "default", "small", Config(endpoint="https://openrouter.ai/api/v1")
        )
        is None
    )
    target = model_scan_runtime.resolve_callable_binding(
        "default",
        "small",
        Config(endpoint="https://openrouter.ai/api/v1", key="private-test-key"),
    )
    assert target is not None
    assert target.binding.api_model == "poolside/laguna-xs-2.1:free"
    assert target.endpoint == "https://openrouter.ai/api/v1"
    assert target.provider == "openrouter"
    assert "private-test-key" not in repr(target)


def test_configured_assignment_matching_has_no_family_heuristic():
    from src.core.model_scan_runtime import configured_assignment_id

    class Config:
        xbig_model = "provider/x-model"
        big_model = "provider/b-model"
        middle_model = "provider/m-model"
        small_model = "provider/s-model"

    config = Config()
    assert configured_assignment_id("other/x-model", config) == "xbig"
    assert configured_assignment_id("provider/b-model", config) == "big"
    assert configured_assignment_id("m-model", config) == "middle"
    assert configured_assignment_id("provider/s-model", config) == "small"
    assert configured_assignment_id("claude-haiku-4-5", config) is None


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
