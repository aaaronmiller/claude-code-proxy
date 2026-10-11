"""CG-T051 — configuration parity for the model-scan settings.

Every ModelScanConfig setting resolves through exactly one path (the
ProxyChain file model). The file and web surfaces are tested; the CLI, TUI,
and environment surfaces are deliberate, mechanically asserted exclusions so
no second precedence path can appear.
"""

from __future__ import annotations

import dataclasses
import json
from src.core import config_manifest
from pathlib import Path

from src.core import config_manifest
from src.core.proxy_chain import ModelScanConfig, ProxyChain

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


def _all_model_scan_fields() -> list[str]:
    return [f.name for f in dataclasses.fields(ModelScanConfig)]


def test_every_setting_round_trips_through_the_single_file_path(tmp_path):
    overrides = {
        "enabled": True,
        "policy": "free",
        "snapshot_path": str(SNAPSHOT),
        "gateway_url": "http://127.0.0.1:7099/routing-snapshot",
        "cache_ttl_s": 111,
        "staleness_limit_s": 222,
        "lanes": {"interactive": {"allow_paid": False}},
        "allocator_enabled": True,
        "session_profiles": {"p1": {"roles": {"big": {"floor": {"per_call": 1}}}}},
        "allocator_slot_map": {"p1": "slot-1"},
        "static_quota": {"openrouter": 0.5},
        "quota_nominal_calls": 42.0,
        "quota_store_path": str(tmp_path / "meters.json"),
        "quota_staleness_limit_s": 333,
    }
    assert set(overrides) == set(_all_model_scan_fields()), (
        "a new ModelScanConfig setting was added without a parity row"
    )

    chain = ProxyChain()
    chain.model_scan = ModelScanConfig.from_any(dict(overrides))
    restored = ProxyChain.from_dict(chain.to_dict())

    for name, value in overrides.items():
        assert getattr(restored.model_scan, name) == value, name


def test_unknown_settings_cannot_enter_through_the_single_path():
    before = ModelScanConfig()
    parsed = ModelScanConfig.from_any(
        {"enabled": True, "bogus_new_setting": "injected"}
    )
    assert parsed.enabled is True
    assert not hasattr(parsed, "bogus_new_setting")
    assert not hasattr(before, "bogus_new_setting")


def test_no_environment_or_cli_surface_exists_for_model_scan_settings():
    # The env/.env surface is the config manifest; model-scan settings must not
    # appear there (no second precedence path).
    env_vars = set(config_manifest.current_env_dict().keys())
    leaked = [name for name in env_vars if name.startswith("MODEL_SCAN")]
    assert leaked == []

    # The resolver schema set must not carry model_scan field paths either.
    from src.core.config_resolver import resolver

    model_scan_paths = [
        path for path in resolver._schemas if "model_scan" in path.lower()
    ]
    assert model_scan_paths == []


def test_web_surface_serves_the_model_scan_configuration(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from src.api.endpoints import router

    chain_path = tmp_path / "proxy_chain.json"
    chain_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "entries": [],
                "router": {},
                "assignments": [],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(SNAPSHOT),
                    "staleness_limit_s": 315360000,
                },
            }
        ),
        encoding="utf-8",
    )
    import os

    old = os.environ.get("PROXY_CHAIN_FILE")
    os.environ["PROXY_CHAIN_FILE"] = str(chain_path)
    try:
        from src.core import proxy_chain as proxy_chain_module

        proxy_chain_module.reload_chain()
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        body = client.get("/api/model-scan/diagnostics").json()
        assert body["sections"]["process"]["model_scan_enabled"] is True
        assert body["sections"]["process"]["policy"] == "free"
    finally:
        if old is None:
            os.environ.pop("PROXY_CHAIN_FILE", None)
        else:
            os.environ["PROXY_CHAIN_FILE"] = old
