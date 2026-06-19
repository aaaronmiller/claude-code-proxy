"""Tests for the routing-snapshot loader (T021).

Covers the failure modes the binder and startup wiring depend on: a valid load builds an
immutable graph with schema defaults applied; truncated/invalid/incompatible input returns None
(so the caller keeps its last good snapshot); cache TTL and data staleness are distinct clocks.
"""

from __future__ import annotations

import copy
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.services.models import model_scan_snapshot as mss

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


@pytest.fixture
def raw() -> dict:
    return json.loads(_FIXTURE.read_text())


@pytest.fixture
def snapshot_file(tmp_path, raw) -> str:
    p = tmp_path / "routing_snapshot.json"
    p.write_text(json.dumps(raw))
    return str(p)


# ── Valid load ────────────────────────────────────────────────────────────────


def test_valid_load_returns_snapshot(snapshot_file):
    snap = mss.load(snapshot_file)
    assert snap is not None
    assert snap.schema_version == "1.0.0"
    assert snap.scan_id == 1487
    assert "R1_primary" in snap.slots
    assert isinstance(snap.blocklist, frozenset)
    assert "groq/gpt-oss-120b" in snap.blocklist


def test_null_best_slot_parses(snapshot_file):
    snap = mss.load(snapshot_file)
    curator = snap.slots["R_curator"]
    assert curator.best is None
    assert curator.candidates == ()


def test_schema_defaults_applied(snapshot_file):
    # The free candidate omits base_url and tier; the loader must fill the schema defaults
    # because jsonschema validates but never injects defaults.
    snap = mss.load(snapshot_file)
    free_best = snap.slots["R8_web_extract"].best
    assert free_best.base_url == ""
    assert free_best.tier == "unknown"


def test_null_price_blended_preserved(snapshot_file, raw, tmp_path):
    variant = copy.deepcopy(raw)
    variant["slots"]["R1_primary"]["best"]["price_blended"] = None
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(variant))
    snap = mss.load(str(p))
    assert snap.slots["R1_primary"].best.price_blended is None


def test_snapshot_is_immutable(snapshot_file):
    snap = mss.load(snapshot_file)
    with pytest.raises(Exception):
        snap.scan_id = 9  # frozen dataclass


# ── Failure modes return None ───────────────────────────────────────────────────


def test_missing_file_returns_none(tmp_path):
    assert mss.load(str(tmp_path / "does_not_exist.json")) is None


def test_truncated_file_returns_none(tmp_path, raw):
    text = json.dumps(raw)
    p = tmp_path / "truncated.json"
    p.write_text(text[: len(text) // 2])  # cut mid-document
    assert mss.load(str(p)) is None


def test_non_object_json_returns_none(tmp_path):
    p = tmp_path / "arr.json"
    p.write_text("[1, 2, 3]")
    assert mss.load(str(p)) is None


def test_contract_violation_returns_none(tmp_path, raw):
    broken = copy.deepcopy(raw)
    del broken["blocklist"]  # required by the contract
    p = tmp_path / "broken.json"
    p.write_text(json.dumps(broken))
    assert mss.load(str(p)) is None


# ── Major-version gating ────────────────────────────────────────────────────────


def test_newer_major_rejected(tmp_path, raw, caplog):
    newer = copy.deepcopy(raw)
    newer["schema_version"] = "2.0.0"
    p = tmp_path / "newer.json"
    p.write_text(json.dumps(newer))
    with caplog.at_level("ERROR"):
        assert mss.load(str(p)) is None
    assert any("schema major v2" in r.message for r in caplog.records)


def test_older_major_rejected(tmp_path, raw):
    older = copy.deepcopy(raw)
    older["schema_version"] = "0.9.0"
    p = tmp_path / "older.json"
    p.write_text(json.dumps(older))
    assert mss.load(str(p)) is None


def test_matching_major_minor_bump_accepted(tmp_path, raw):
    # A newer minor within the supported major is forward-compatible and must load.
    bumped = copy.deepcopy(raw)
    bumped["schema_version"] = "1.4.0"
    p = tmp_path / "bumped.json"
    p.write_text(json.dumps(bumped))
    assert mss.load(str(p)) is not None


# ── Cache TTL (monotonic) ───────────────────────────────────────────────────────


def test_is_stale_false_when_fresh(snapshot_file):
    snap = mss.load(snapshot_file)
    assert mss.is_stale(snap, ttl_s=60) is False


def test_is_stale_true_when_past_ttl(snapshot_file):
    snap = mss.load(snapshot_file)
    aged = mss.RoutingSnapshot(**{**snap.__dict__, "loaded_at": time.monotonic() - 120})
    assert mss.is_stale(aged, ttl_s=60) is True


# ── Data staleness (wall clock on generated_at) ─────────────────────────────────


def test_data_not_stale_when_recent(raw, tmp_path):
    fresh = copy.deepcopy(raw)
    now = datetime.now(timezone.utc)
    fresh["generated_at"] = now.isoformat().replace("+00:00", "Z")
    p = tmp_path / "fresh.json"
    p.write_text(json.dumps(fresh))
    snap = mss.load(str(p))
    assert mss.is_data_stale(snap, staleness_limit_s=86400) is False


def test_data_stale_when_old(snapshot_file):
    snap = mss.load(snapshot_file)  # generated_at 2026-05-31
    far_future = datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert mss.is_data_stale(snap, staleness_limit_s=86400, now=far_future) is True


def test_unparseable_generated_at_is_stale(snapshot_file):
    snap = mss.load(snapshot_file)
    mangled = mss.RoutingSnapshot(**{**snap.__dict__, "generated_at": "not-a-date"})
    assert mss.data_age_seconds(mangled) is None
    assert mss.is_data_stale(mangled, staleness_limit_s=86400) is True


# ── Gateway pull ────────────────────────────────────────────────────────────────


def test_from_gateway_success(monkeypatch, raw):
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return raw

    monkeypatch.setattr(mss.httpx, "get", lambda url, timeout: _Resp())
    snap = mss.from_gateway("http://localhost:8124/routing-snapshot")
    assert snap is not None
    assert snap.scan_id == 1487


def test_from_gateway_http_error_returns_none(monkeypatch):
    def _boom(url, timeout):
        raise mss.httpx.ConnectError("refused")

    monkeypatch.setattr(mss.httpx, "get", _boom)
    assert mss.from_gateway("http://localhost:8124/routing-snapshot") is None
