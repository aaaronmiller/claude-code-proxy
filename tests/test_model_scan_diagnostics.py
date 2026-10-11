"""CG-T050 — structured diagnostics distinguish all eight operator states.

The report covers process, dependency, catalog, snapshot, quota, binding,
reload, and degraded state without exposing any credential value.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.endpoints import router
from src.core.model_scan_diagnostics import assert_no_secrets, collect_diagnostics

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


def _write_state(tmp_path: Path, *, staleness_s: int = 315360000) -> tuple[Path, Path]:
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
                    "staleness_limit_s": staleness_s,
                    "quota_store_path": str(tmp_path / "quota-meters.json"),
                },
            }
        ),
        encoding="utf-8",
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "default": {"lane": "interactive", "slot_bindings": {"big": "R1_primary"}},
            }
        ),
        encoding="utf-8",
    )
    return chain_path, profiles_path


def _prepare(monkeypatch, tmp_path, *, staleness_s: int = 315360000):
    from src.core import model_scan_runtime
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path, staleness_s=staleness_s)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", profiles_path)
    profiles._cache = {}
    profiles._cache_path = None
    profiles._ephemeral_profiles.clear()
    model_scan_runtime.clear_active_binding()
    model_scan_runtime._LAST_RELOAD = None
    proxy_chain_module.reload_chain()
    return chain_path, profiles_path


def test_healthy_diagnostics_cover_all_sections(monkeypatch, tmp_path):
    from src.core import model_scan_runtime

    _prepare(monkeypatch, tmp_path)
    model_scan_runtime.reload_model_scan()

    report = collect_diagnostics()
    assert report["overall"] == "ok"
    assert report["degraded"] == []
    assert set(report["sections"]) == {
        "process",
        "dependency",
        "catalog",
        "snapshot",
        "quota",
        "binding",
        "reload",
    }
    assert report["sections"]["process"]["model_scan_enabled"] is True
    assert report["sections"]["snapshot"]["state"] == "ok"
    assert report["sections"]["snapshot"]["scan_id"] == 1487
    assert report["sections"]["catalog"]["state"] == "ok"
    assert report["sections"]["binding"]["state"] == "ok"
    assert report["sections"]["binding"]["global_tier_count"] == 1
    assert report["sections"]["reload"]["state"] == "ok"
    assert report["sections"]["reload"]["changed"] is True
    assert report["persistent_writes"] == []
    assert_no_secrets(report)
    assert "must-not-appear" not in json.dumps(report)


def test_missing_snapshot_is_flagged_degraded(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _prepare(monkeypatch, tmp_path)
    data = json.loads(chain_path.read_text())
    data["model_scan"]["snapshot_path"] = str(tmp_path / "absent.json")
    chain_path.write_text(json.dumps(data))
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()
    model_scan_runtime._LAST_RELOAD = None

    report = collect_diagnostics()
    assert report["overall"] == "degraded"
    assert report["sections"]["dependency"]["state"] == "missing"
    assert report["sections"]["snapshot"]["state"] == "missing"
    assert report["sections"]["catalog"]["state"] == "missing"
    assert report["sections"]["binding"]["state"] == "missing"
    assert "dependency:missing" in report["degraded"]
    assert "snapshot:missing" in report["degraded"]


def test_stale_snapshot_and_stale_quota_are_distinguished(monkeypatch, tmp_path):
    from src.core.quota_store import QuotaMeterStore

    chain_path, profiles_path = _prepare(monkeypatch, tmp_path, staleness_s=60)
    meters = tmp_path / "quota-meters.json"
    QuotaMeterStore(str(meters)).save([])

    report = collect_diagnostics()
    assert report["sections"]["snapshot"]["state"] == "stale"
    assert "snapshot:stale" in report["degraded"]
    assert report["sections"]["quota"]["state"] == "ok"
    assert report["sections"]["quota"]["meter_count"] == 0


def test_disabled_config_reports_disabled_without_degraded_binding(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _prepare(monkeypatch, tmp_path)
    data = json.loads(chain_path.read_text())
    data["model_scan"]["enabled"] = False
    chain_path.write_text(json.dumps(data))
    proxy_chain_module.reload_chain()
    model_scan_runtime.clear_active_binding()
    model_scan_runtime._LAST_RELOAD = None

    report = collect_diagnostics()
    assert report["model_scan_enabled"] is False
    assert report["overall"] == "disabled"
    assert report["sections"]["binding"]["state"] == "ok"
    assert report["degraded"] == []


def test_corrupt_quota_store_is_reported(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    meters = tmp_path / "quota-meters.json"
    meters.write_text("{not json", encoding="utf-8")

    report = collect_diagnostics()
    assert report["sections"]["quota"]["state"] == "corrupt"
    assert "quota:corrupt" in report["degraded"]


def test_diagnostics_endpoint_serves_report_without_secrets(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/api/model-scan/diagnostics")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "diagnostics"
    assert set(body["sections"]) == {
        "process",
        "dependency",
        "catalog",
        "snapshot",
        "quota",
        "binding",
        "reload",
    }
    assert "must-not-appear" not in response.text
    assert_no_secrets(body)
