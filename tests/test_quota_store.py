"""Atomic quota-meter persistence, restart recovery, and freshness."""

import json

from src.core.quota_live import QuotaCache
from src.core.quota_sources import QuotaMeter
from src.core.quota_store import QuotaMeterStore


def _meter(*, observed_at=10.0):
    return QuotaMeter(
        id="groq:calls:minute",
        provider="groq",
        unit="calls",
        window_seconds=60,
        limit=100,
        remaining=75,
        reset_at="30s",
        source="header",
        observed_at=observed_at,
        resource="api-rate-limit",
        confidence=1.0,
    )


def test_store_round_trip_and_restart_recovery(tmp_path):
    path = tmp_path / "quota-meters.json"
    first = QuotaCache(QuotaMeterStore(path))
    first.record_meters([_meter()])

    restarted = QuotaCache(QuotaMeterStore(path))
    assert restarted.meters() == [_meter()]
    assert path.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.glob("*.tmp")) == []


def test_corrupt_store_is_preserved_and_ignored(tmp_path):
    path = tmp_path / "quota-meters.json"
    path.write_text("{not-json", encoding="utf-8")

    cache = QuotaCache(QuotaMeterStore(path))
    assert cache.meters() == []
    assert path.read_text(encoding="utf-8") == "{not-json"


def test_unknown_schema_or_meter_field_is_rejected(tmp_path):
    path = tmp_path / "quota-meters.json"
    payload = {
        "schema_version": "1.0.0",
        "meters": [{**_meter().__dict__, "secret": "must-not-load"}],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert QuotaMeterStore(path).load() == []


def test_invalid_meter_types_are_rejected(tmp_path):
    path = tmp_path / "quota-meters.json"
    payload = {
        "schema_version": "1.0.0",
        "meters": [{**_meter().__dict__, "limit": "not-a-number"}],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert QuotaMeterStore(path).load() == []


def test_stale_fact_remains_available_and_exposes_freshness(tmp_path):
    path = tmp_path / "quota-meters.json"
    first = QuotaCache(QuotaMeterStore(path))
    first.record_meters([_meter(observed_at=10.0)])

    restarted = QuotaCache(QuotaMeterStore(path))
    state = restarted.freshness(now=100.0, max_age_s=60.0)
    assert restarted.meters() == [_meter(observed_at=10.0)]
    assert state == [
        {
            "id": "groq:calls:minute",
            "observed_at": 10.0,
            "age_seconds": 90.0,
            "stale": True,
        }
    ]


def test_store_write_failure_does_not_drop_in_memory_fact(tmp_path):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("x", encoding="utf-8")
    cache = QuotaCache(QuotaMeterStore(blocked / "quota.json"))
    cache.record_meters([_meter()])
    assert cache.meters() == [_meter()]
