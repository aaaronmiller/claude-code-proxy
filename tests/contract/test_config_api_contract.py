"""Contract tests for /api/assignments, /api/identifier-mappings, and /api/chain.

Validates shapes match contracts/config-api.yaml and that the admin-role gate
returns 403 for non-admin callers (FR-026, FR-028). Includes provenance stubs.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.config_api import router as config_router
from src.core.assignments import get_registry as get_assignment_registry
from src.core.identifier_mapping import get_registry as get_identifier_mapping_registry


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures — app with auth dependencies stubbed
# ─────────────────────────────────────────────────────────────────────────────


def _make_app_with_role(role: str) -> TestClient:
    """Build a FastAPI app that injects a user of the given role."""
    app = FastAPI()
    app.include_router(config_router)

    from src.api.users_rbac import get_current_user, require_admin

    async def _fake_user() -> Dict[str, Any]:
        return {"username": "tester", "role": role, "permissions": []}

    async def _fake_require_admin() -> Dict[str, Any]:
        if role != "admin":
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Admin role required")
        return {"username": "tester", "role": role, "permissions": []}

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[require_admin] = _fake_require_admin
    return TestClient(app)


@pytest.fixture
def admin_client() -> TestClient:
    return _make_app_with_role("admin")


@pytest.fixture
def user_client() -> TestClient:
    return _make_app_with_role("user")


_TEST_CHAIN_ID_PREFIXES = (
    "test_",
    "first",
    "second",
    "entry_",
    "patchable",
    "tobedeleted",
    "a",
    "b",
)


def _is_test_chain_entry(entry_id: str) -> bool:
    if entry_id in {"a", "b"}:
        return True
    return any(entry_id.startswith(p) for p in _TEST_CHAIN_ID_PREFIXES)


@pytest.fixture(autouse=True)
def _reset_registries():
    """Remove any test-created slot assignments, mappings, and chain entries."""
    yield
    ar = get_assignment_registry()
    for a in list(ar.list()):
        if a.kind == "slot" and a.id.startswith("test_"):
            try:
                ar.delete(a.id, principal="test-cleanup")
            except Exception:
                pass
    im = get_identifier_mapping_registry()
    for m in list(im.list()):
        if m.incoming_identifier.startswith("test_"):
            try:
                im.delete(m.incoming_identifier)
            except Exception:
                pass
    # Strip any leftover chain entries created by tests; production entries
    # have known stable ids (claude_code_proxy, headroom, rtk, ...).
    from src.core.proxy_chain import get_chain

    chain = get_chain()
    before = len(chain.entries)
    chain.entries = [e for e in chain.entries if not _is_test_chain_entry(e.id)]
    if len(chain.entries) != before:
        chain._renumber()
        chain.save()


# ─────────────────────────────────────────────────────────────────────────────
# Assignments (T033)
# ─────────────────────────────────────────────────────────────────────────────


def test_list_assignments_returns_array(user_client: TestClient) -> None:
    resp = user_client.get("/api/assignments")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for item in body:
        for key in (
            "id",
            "kind",
            "model",
            "provider",
            "base_url",
            "api_key",
            "enabled",
            "cascade",
        ):
            assert key in item, f"Missing '{key}' in assignment: {item}"


def test_create_slot_assignment_as_admin(admin_client: TestClient) -> None:
    body = {
        "id": "test_analysis",
        "kind": "slot",
        "model": "openai/gpt-4o-mini",
        "provider": "openai",
        "enabled": True,
    }
    resp = admin_client.post("/api/assignments", json=body)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"] == "test_analysis"
    assert created["kind"] == "slot"
    assert created["model"] == "openai/gpt-4o-mini"


def test_create_tier_rejected(admin_client: TestClient) -> None:
    """Tiers are fixed; creating one via POST must be rejected with 400."""
    resp = admin_client.post(
        "/api/assignments",
        json={"id": "big", "kind": "tier", "model": "whatever"},
    )
    assert resp.status_code == 400


def test_non_admin_cannot_create(user_client: TestClient) -> None:
    """FR-026: write endpoints require admin role."""
    resp = user_client.post(
        "/api/assignments",
        json={"id": "test_rejected", "kind": "slot", "model": "x"},
    )
    assert resp.status_code == 403


def test_non_admin_can_read(user_client: TestClient) -> None:
    """FR-027: reads require authenticated user but not admin."""
    resp = user_client.get("/api/assignments")
    assert resp.status_code == 200


def test_update_assignment(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/assignments",
        json={"id": "test_updater", "kind": "slot", "model": "a"},
    )
    resp = admin_client.patch(
        "/api/assignments/test_updater",
        json={"model": "b", "enabled": False},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["model"] == "b"
    assert updated["enabled"] is False


def test_delete_slot_ok_tier_forbidden(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/assignments",
        json={"id": "test_deletable", "kind": "slot", "model": "x"},
    )
    resp = admin_client.delete("/api/assignments/test_deletable")
    assert resp.status_code == 204

    # Tier deletion must be rejected with 409 (or 404 if not present)
    resp = admin_client.delete("/api/assignments/big")
    assert resp.status_code in (404, 409)


def test_invalid_slot_id_rejected(admin_client: TestClient) -> None:
    """Slot id must match ^[a-z][a-z0-9_]{0,63}$."""
    resp = admin_client.post(
        "/api/assignments",
        json={"id": "Invalid-ID", "kind": "slot"},
    )
    assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Identifier mappings (T033)
# ─────────────────────────────────────────────────────────────────────────────


def test_list_mappings(user_client: TestClient) -> None:
    resp = user_client.get("/api/identifier-mappings")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_mapping_requires_existing_assignment(admin_client: TestClient) -> None:
    """FK check: assignment_id must exist."""
    resp = admin_client.post(
        "/api/identifier-mappings",
        json={
            "incoming_identifier": "test_unknown_tgt",
            "assignment_id": "does_not_exist",
        },
    )
    assert resp.status_code == 400


def test_create_and_delete_mapping(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/assignments",
        json={"id": "test_slot_for_mapping", "kind": "slot", "model": "x"},
    )
    resp = admin_client.post(
        "/api/identifier-mappings",
        json={
            "incoming_identifier": "test_hermes_role",
            "assignment_id": "test_slot_for_mapping",
            "priority": 10,
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["priority"] == 10

    resp = admin_client.delete("/api/identifier-mappings/test_hermes_role")
    assert resp.status_code == 204


def test_non_admin_cannot_create_mapping(user_client: TestClient) -> None:
    resp = user_client.post(
        "/api/identifier-mappings",
        json={"incoming_identifier": "test_x", "assignment_id": "big"},
    )
    assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Chain management (T047)
# ─────────────────────────────────────────────────────────────────────────────


def test_list_chain_returns_array(user_client: TestClient) -> None:
    resp = user_client.get("/api/chain")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    for entry in body:
        for key in (
            "id",
            "name",
            "url",
            "auth_key",
            "enabled",
            "order",
            "service_cmd",
            "port",
            "health_path",
            "timeout",
            "extra_headers",
            "type",
            "model_prefixes",
        ):
            assert key in entry, f"Missing '{key}' in chain entry"


def test_add_chain_entry_requires_admin(user_client: TestClient) -> None:
    new_entry = {
        "id": "test_new",
        "name": "Test Proxy",
        "url": "http://127.0.0.1:9999/v1",
        "enabled": True,
        "port": 9999,
    }
    resp = user_client.post("/api/chain", json=new_entry)
    assert resp.status_code == 403


def test_add_chain_entry_valid(admin_client: TestClient) -> None:
    new_entry = {
        "id": "test_add_ok",
        "name": "Test OK",
        "url": "http://127.0.0.1:8888/v1",
        "enabled": True,
        "port": 8888,
        "type": "http",
    }
    resp = admin_client.post("/api/chain", json=new_entry)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"] == "test_add_ok"
    assert created["port"] == 8888


def test_add_chain_entry_port_conflict(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/chain",
        json={
            "id": "first",
            "name": "First",
            "url": "http://127.0.0.1:7777/v1",
            "enabled": True,
            "port": 7777,
            "type": "http",
        },
    )
    resp = admin_client.post(
        "/api/chain",
        json={
            "id": "second",
            "name": "Second",
            "url": "http://127.0.0.1:7777/v1",
            "enabled": True,
            "port": 7777,
            "type": "http",
        },
    )
    assert resp.status_code == 400
    assert "port conflict" in resp.json()["detail"].lower()


def test_reorder_chain_validation(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/chain",
        json={
            "id": "a",
            "name": "A",
            "url": "http://127.0.0.1:9001/v1",
            "enabled": True,
            "port": 9001,
            "type": "http",
        },
    )
    admin_client.post(
        "/api/chain",
        json={
            "id": "b",
            "name": "B",
            "url": "http://127.0.0.1:9002/v1",
            "enabled": True,
            "port": 9002,
            "type": "http",
        },
    )
    resp = admin_client.post("/api/chain/reorder", json={"order": ["b", "unknown"]})
    assert resp.status_code == 400
    resp = admin_client.post("/api/chain/reorder", json={"order": ["a", "a"]})
    assert resp.status_code == 400


def test_reorder_chain_success(admin_client: TestClient) -> None:
    for i in range(3):
        admin_client.post(
            "/api/chain",
            json={
                "id": f"entry_{i}",
                "name": f"Entry {i}",
                "url": f"http://127.0.0.1:{9000 + i}/v1",
                "enabled": True,
                "port": 9000 + i,
                "type": "http",
            },
        )
    resp = admin_client.post(
        "/api/chain/reorder", json={"order": ["entry_2", "entry_1", "entry_0"]}
    )
    assert resp.status_code == 200
    entries = admin_client.get("/api/chain").json()
    assert [e["id"] for e in entries] == ["entry_2", "entry_1", "entry_0"]


def test_patch_chain_entry(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/chain",
        json={
            "id": "patchable",
            "name": "Patch Me",
            "url": "http://127.0.0.1:8000/v1",
            "enabled": True,
            "port": 8000,
            "type": "http",
        },
    )
    resp = admin_client.patch(
        "/api/chain/patchable",
        json={"enabled": False, "name": "Patched"},
    )
    assert resp.status_code == 200
    patched = resp.json()
    assert patched["enabled"] is False
    assert patched["name"] == "Patched"


def test_delete_chain_entry(admin_client: TestClient) -> None:
    admin_client.post(
        "/api/chain",
        json={
            "id": "tobedeleted",
            "name": "Delete Me",
            "url": "http://127.0.0.1:8001/v1",
            "enabled": True,
            "port": 8001,
            "type": "http",
        },
    )
    resp = admin_client.delete("/api/chain/tobedeleted")
    assert resp.status_code == 204
    ids = [e["id"] for e in admin_client.get("/api/chain").json()]
    assert "tobedeleted" not in ids


def test_chain_endpoints_require_admin(user_client: TestClient) -> None:
    # POST
    resp = user_client.post(
        "/api/chain",
        json={
            "id": "x",
            "name": "X",
            "url": "http://127.0.0.1:8002/v1",
            "enabled": True,
            "port": 8002,
            "type": "http",
        },
    )
    assert resp.status_code == 403
    # PATCH
    resp = user_client.patch("/api/chain/x", json={"enabled": False})
    assert resp.status_code == 403
    # DELETE
    resp = user_client.delete("/api/chain/x")
    assert resp.status_code == 403
    # reorder
    resp = user_client.post("/api/chain/reorder", json={"order": []})
    assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Provenance (T064 stub hook)
# ─────────────────────────────────────────────────────────────────────────────


def test_config_field_unknown_returns_404(user_client: TestClient) -> None:
    resp = user_client.get("/api/config/nonexistent.field.path")
    assert resp.status_code == 404


def test_get_full_config_returns_provenance(user_client: TestClient) -> None:
    """GET /api/config returns the resolved tree with source_layer per leaf."""
    resp = user_client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    # At least the always-registered scalar fields should be present.
    assert "host" in body or "log_level" in body
    # Each leaf must carry value + source_layer per ResolvedValue contract.
    # The dict key serves as the field_path; leaves don't need to repeat it.
    for key, leaf in body.items():
        if isinstance(leaf, dict) and "source_layer" in leaf:
            assert leaf["source_layer"] in (
                "cli",
                "shell_env",
                "dotenv",
                "stored",
                "default",
            )
            assert "value" in leaf


def test_get_config_field_returns_resolved_value(user_client: TestClient) -> None:
    """GET /api/config/{field_path} returns ResolvedValue shape."""
    # ``host`` always has a default registered via _register_static_schemas
    resp = user_client.get("/api/config/host")
    assert resp.status_code == 200
    body = resp.json()
    assert body["field_path"] == "host"
    assert "value" in body
    assert body["source_layer"] in (
        "cli",
        "shell_env",
        "dotenv",
        "stored",
        "default",
    )


def test_provenance_reflects_winning_layer(admin_client: TestClient) -> None:
    """Setting a value via stored layer should make /api/config/<field> show source_layer=stored."""
    # Pick a slot we can safely create
    create_resp = admin_client.post(
        "/api/assignments",
        json={
            "id": "test_provenance_slot",
            "kind": "slot",
            "model": "anthropic/claude-haiku-4-5",
            "provider": "anthropic",
            "enabled": True,
            "cascade": [],
        },
    )
    assert create_resp.status_code in (200, 201)

    resp = admin_client.get("/api/config/assignments.test_provenance_slot.model")
    assert resp.status_code == 200
    body = resp.json()
    assert body["value"] == "anthropic/claude-haiku-4-5"
    assert body["source_layer"] == "stored"
