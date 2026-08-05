"""Mechanical non-persistence for model-scan preview."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.assignments import AssignmentRegistry
from src.core.model_scan_binder import BindResult
from src.core.persistence_boundary import (
    PersistenceBlocked,
    non_persisting_preview,
    preview_is_non_persisting,
)
from src.core.proxy_chain import ProxyChain


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
                        "api_key": "",
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
                    "slot_bindings": {"big": "R1_primary"},
                },
                "codex": {
                    "slot_bindings": {"big": "R8_web_extract"},
                },
            }
        ),
        encoding="utf-8",
    )
    return chain_path, profiles_path


def test_preview_reports_changes_without_mutating_any_state(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    live_chain = proxy_chain_module.reload_chain()
    baseline_binding = BindResult(scan_id=7, schema_version="baseline")
    baseline_allocation = {"enabled": False, "marker": "baseline"}
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_BINDING", baseline_binding)
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_ALLOCATION", baseline_allocation)

    chain_before = chain_path.read_bytes()
    profiles_before = profiles_path.read_bytes()
    assignments_before = [assignment.to_dict() for assignment in live_chain.assignments]

    summary = model_scan_runtime.preview_model_scan(profiles_path=profiles_path)

    assert summary["mode"] == "preview"
    assert summary["changed"] is False
    assert summary["would_change"] is True
    assert summary["persistent_writes"] == []
    assert summary["proposed_global_changes"]["big"]["before"]["model"] == "static/big"
    assert (
        summary["proposed_global_changes"]["big"]["after"]["model"]
        == "openrouter/deepseek/deepseek-v4-flash:free"
    )
    assert chain_path.read_bytes() == chain_before
    assert profiles_path.read_bytes() == profiles_before
    assert proxy_chain_module.get_chain() is live_chain
    assert [assignment.to_dict() for assignment in live_chain.assignments] == assignments_before
    assert model_scan_runtime.get_active_binding() is baseline_binding
    assert model_scan_runtime.get_active_allocation() == baseline_allocation
    assert preview_is_non_persisting() is False


async def test_preview_endpoint_uses_the_non_persisting_path(monkeypatch, tmp_path):
    from src.api.endpoints import preview_model_scan_bindings
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    proxy_chain_module.reload_chain()
    before = chain_path.read_bytes()

    summary = await preview_model_scan_bindings()

    assert summary["mode"] == "preview"
    assert summary["would_change"] is True
    assert summary["persistent_writes"] == []
    assert chain_path.read_bytes() == before


async def test_preview_scope_blocks_client_profile_and_routing_writes(
    monkeypatch,
    tmp_path,
):
    from src.api import web_ui
    from src.cli.env_utils import update_env_values
    from src.core import proxy_chain as proxy_chain_module

    chain_path, _ = _write_state(tmp_path)
    env_path = tmp_path / ".env"
    env_path.write_text("BIG_MODEL=before\n", encoding="utf-8")
    profile_dir = tmp_path / "profiles"
    monkeypatch.setattr(web_ui, "PROFILES_DIR", profile_dir)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    live_chain = proxy_chain_module.reload_chain()
    routing_before = chain_path.read_bytes()
    assignments_before = [assignment.to_dict() for assignment in live_chain.assignments]

    with non_persisting_preview():
        with pytest.raises(PersistenceBlocked, match="client configuration"):
            update_env_values(
                {"BIG_MODEL": "after"},
                env_path=env_path,
                verbose=False,
            )
        with pytest.raises(PersistenceBlocked, match="profile"):
            await web_ui.save_profile(
                web_ui.ProfileCreate(
                    name="preview-profile",
                    config={"big_model": "after"},
                )
            )
        with pytest.raises(PersistenceBlocked, match="routing"):
            live_chain.save()
        registry = AssignmentRegistry()
        with pytest.raises(PersistenceBlocked, match="routing"):
            registry.update("big", {"model": "after"})

    assert env_path.read_text(encoding="utf-8") == "BIG_MODEL=before\n"
    assert not profile_dir.exists()
    assert chain_path.read_bytes() == routing_before
    assert [assignment.to_dict() for assignment in live_chain.assignments] == assignments_before


def test_preview_scope_is_nestable_and_context_local():
    assert preview_is_non_persisting() is False
    with non_persisting_preview():
        assert preview_is_non_persisting() is True
        with non_persisting_preview():
            assert preview_is_non_persisting() is True
        assert preview_is_non_persisting() is True
    assert preview_is_non_persisting() is False


def test_proxy_chain_copy_is_detached():
    original = ProxyChain.from_dict(
        {
            "schema_version": "2.0.0",
            "entries": [],
            "router": {},
            "assignments": [
                {
                    "id": "big",
                    "kind": "tier",
                    "model": "before",
                }
            ],
            "identifier_mappings": [],
            "model_scan": {},
        }
    )
    copied = ProxyChain.from_dict(original.to_dict())

    copied.assignments[0].model = "after"

    assert original.assignments[0].model == "before"


def test_preview_blocks_automatic_routing_migration(tmp_path):
    chain_path = tmp_path / "proxy_chain.json"
    chain_path.write_text(
        json.dumps(
            {
                "entries": [],
                "router": {},
            }
        ),
        encoding="utf-8",
    )
    before = chain_path.read_bytes()

    with non_persisting_preview():
        with pytest.raises(PersistenceBlocked, match="routing migration"):
            ProxyChain.load(chain_path)

    assert chain_path.read_bytes() == before
    assert not list(tmp_path.glob("proxy_chain.bak.*"))
    assert not chain_path.with_suffix(".tmp").exists()
