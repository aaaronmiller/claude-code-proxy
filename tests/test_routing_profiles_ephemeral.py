from __future__ import annotations

import json
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routing_profiles_api import router
from src.core import profiles


def test_ephemeral_profiles_route_independently(monkeypatch, tmp_path):
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}))
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", p)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()

    a = profiles.register_ephemeral_profile(
        preset="default",
        overlay={"slot_bindings": {"big": "R8_web_extract"}},
        profile_id="session-a",
    )
    b = profiles.register_ephemeral_profile(
        preset="default",
        overlay={"slot_bindings": {"big": "R12_delegation"}},
        profile_id="session-b",
    )

    assert a.get("slot_bindings")["big"] == "R8_web_extract"
    assert b.get("slot_bindings")["big"] == "R12_delegation"
    assert profiles.resolve_profile("session-a").get("slot_bindings")["big"] == "R8_web_extract"


def test_ephemeral_delete_is_idempotent_and_ttl_sweeps(monkeypatch, tmp_path):
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps({"default": {}}))
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", p)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()

    profiles.register_ephemeral_profile(preset="default", ttl_s=1, profile_id="short")
    assert profiles.has_profile("short")
    assert profiles.delete_ephemeral_profile("short") is True
    assert profiles.delete_ephemeral_profile("short") is False
    profiles.register_ephemeral_profile(preset="default", ttl_s=1, profile_id="short")
    assert profiles.sweep_ephemeral_profiles(now=time.time() + 2) == 1
    assert not profiles.has_profile("short")


def test_routing_profiles_api_creates_and_deletes(monkeypatch, tmp_path):
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps({"default": {"notes": "base"}}))
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", p)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post(
        "/api/routing-profiles",
        json={"preset": "default", "profile_id": "api-session", "overlay": {"lane": "standby"}},
    )
    assert resp.status_code == 200
    assert resp.json()["url_prefix"] == "/p/api-session"
    assert profiles.resolve_profile("api-session").get("lane") == "standby"

    assert client.delete("/api/routing-profiles/api-session").json()["deleted"] is True
    assert client.delete("/api/routing-profiles/api-session").json()["deleted"] is False
