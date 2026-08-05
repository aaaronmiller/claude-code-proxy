"""Isolated model-scan canaries stay explicit, ephemeral, and profile-scoped."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routing_profiles_api import router
from src.core.model_scan_binder import BindResult, ResolvedBinding

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


def _write_state(tmp_path: Path) -> tuple[Path, Path]:
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
                        "api_key": "must-not-appear",
                        "enabled": True,
                        "cascade": ["static/fallback"],
                    }
                ],
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
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "default": {
                    "lane": "interactive",
                    "slot_bindings": {"big": "R1_primary"},
                },
                "normal": {
                    "lane": "interactive",
                    "slot_bindings": {"big": "R8_web_extract"},
                },
            }
        ),
        encoding="utf-8",
    )
    return chain_path, profiles_path


def _prepare(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", profiles_path)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()
    live_chain = proxy_chain_module.reload_chain()
    normal_binding = ResolvedBinding(
        api_model="normal/model",
        base_url="",
        cascade=("normal/fallback",),
        source="snapshot",
        provider="normal",
        role="R8_web_extract",
    )
    active = BindResult(
        overlay={"normal": {"big": normal_binding}},
        scan_id=7,
        schema_version="baseline",
    )
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_BINDING", active)
    return chain_path, profiles_path, live_chain, normal_binding


def test_canary_creation_is_ephemeral_exact_and_non_persisting(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path, live_chain, normal_binding = _prepare(monkeypatch, tmp_path)
    chain_before = chain_path.read_bytes()
    profiles_before = profiles_path.read_bytes()
    assignments_before = [assignment.to_dict() for assignment in live_chain.assignments]
    active_before = model_scan_runtime.get_active_binding()

    result = model_scan_runtime.create_model_scan_canary(ttl_s=600)

    assert result["mode"] == "canary"
    assert result["profile_id"].startswith("canary-")
    assert result["profile_kind"] == "canary"
    assert result["url_prefix"] == f"/p/{result['profile_id']}"
    assert result["traffic_sent"] is False
    assert result["active_binding_changed"] is False
    assert result["persistent_writes"] == []
    assert result["source_comparison_ids"][0].startswith("sha256:")
    assert result["bindings"]["big"]["api_model"] == (
        "openrouter/deepseek/deepseek-v4-flash:free"
    )
    assert "must-not-appear" not in json.dumps(result)

    canary = profiles.resolve_profile(result["profile_id"])
    assert canary.kind == "canary"
    token = profiles.ACTIVE_PROFILE.set(canary)
    try:
        binding = model_scan_runtime.resolve_profile_binding(canary.name, "big")
    finally:
        profiles.ACTIVE_PROFILE.reset(token)
    assert binding is not None
    assert binding.source == "canary"
    assert binding.api_model == "openrouter/deepseek/deepseek-v4-flash:free"

    assert model_scan_runtime.resolve_profile_binding(canary.name, "big") is None
    assert model_scan_runtime.resolve_profile_binding("normal", "big") is normal_binding
    assert chain_path.read_bytes() == chain_before
    assert profiles_path.read_bytes() == profiles_before
    assert proxy_chain_module.get_chain() is live_chain
    assert [assignment.to_dict() for assignment in live_chain.assignments] == assignments_before
    assert model_scan_runtime.get_active_binding() is active_before


def test_canary_delete_and_expiry_remove_exact_binding(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles

    _prepare(monkeypatch, tmp_path)
    first = model_scan_runtime.create_model_scan_canary(ttl_s=60)
    first_name = first["profile_id"]
    assert profiles.is_canary_profile(first_name)
    assert profiles.delete_ephemeral_profile(first_name) is True
    assert not profiles.is_canary_profile(first_name)

    second = model_scan_runtime.create_model_scan_canary(ttl_s=60)
    second_name = second["profile_id"]
    expires_at = profiles.list_ephemeral_profiles()[second_name]["expires_at"]
    assert profiles.sweep_ephemeral_profiles(now=float(expires_at) + 1) == 1
    assert not profiles.has_profile(second_name)


def test_canary_health_and_continuation_state_do_not_leak(monkeypatch, tmp_path):
    from src.core import client as client_module
    from src.core import model_scan_runtime
    from src.core import profiles

    _prepare(monkeypatch, tmp_path)
    result = model_scan_runtime.create_model_scan_canary(ttl_s=600)
    canary = profiles.resolve_profile(result["profile_id"])
    normal = profiles.resolve_profile("normal")
    monkeypatch.setattr(client_module, "_circuit_breakers", {})
    monkeypatch.setattr(client_module, "_mid_stream_tier_overrides", {})

    normal_token = profiles.ACTIVE_PROFILE.set(normal)
    try:
        normal_breaker = client_module._get_circuit_breaker("shared/model")
        client_module.set_mid_stream_tier_override("same-session", "middle")
    finally:
        profiles.ACTIVE_PROFILE.reset(normal_token)

    canary_token = profiles.ACTIVE_PROFILE.set(canary)
    try:
        canary_breaker = client_module._get_circuit_breaker("shared/model")
        assert client_module.get_mid_stream_tier_override("same-session") is None
        client_module.set_mid_stream_tier_override("same-session", "small")
        assert client_module.get_mid_stream_tier_override("same-session") == "small"
    finally:
        profiles.ACTIVE_PROFILE.reset(canary_token)

    assert canary_breaker is not normal_breaker
    normal_token = profiles.ACTIVE_PROFILE.set(normal)
    try:
        assert client_module.get_mid_stream_tier_override("same-session") == "middle"
    finally:
        profiles.ACTIVE_PROFILE.reset(normal_token)


def test_canary_request_context_is_concurrent_task_local(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles

    _prepare(monkeypatch, tmp_path)
    result = model_scan_runtime.create_model_scan_canary(ttl_s=600)
    canary = profiles.resolve_profile(result["profile_id"])
    normal = profiles.resolve_profile("normal")

    async def observe(profile):
        token = profiles.ACTIVE_PROFILE.set(profile)
        try:
            await asyncio.sleep(0)
            active = profiles.ACTIVE_PROFILE.get()
            binding = model_scan_runtime.resolve_profile_binding(active.name, "big")
            return active.name, active.kind, binding.api_model if binding else None
        finally:
            profiles.ACTIVE_PROFILE.reset(token)

    async def observe_both():
        return await asyncio.gather(observe(canary), observe(normal))

    observed = asyncio.run(observe_both())

    assert observed[0][0] == canary.name
    assert observed[0][1:] == (
        "canary",
        "openrouter/deepseek/deepseek-v4-flash:free",
    )
    assert observed[1] == ("normal", "normal", "normal/model")
    assert profiles.ACTIVE_PROFILE.get() is None


def test_canary_api_returns_explicit_prefix_without_sending_traffic(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles

    chain_path, profiles_path, _, _ = _prepare(monkeypatch, tmp_path)
    before_chain = chain_path.read_bytes()
    before_profiles = profiles_path.read_bytes()
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", profiles_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post("/api/routing-profiles/canary", json={"ttl_s": 300})

    assert response.status_code == 200
    body = response.json()
    assert body["url_prefix"].startswith("/p/canary-")
    assert body["traffic_sent"] is False
    assert chain_path.read_bytes() == before_chain
    assert profiles_path.read_bytes() == before_profiles
