"""Deterministic snapshot publication and recovery stay offline and default-off."""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.services.models import deterministic_routing_snapshot as snapshot_module
from src.services.models.callable_catalog import load as load_catalog
from src.services.models.deterministic_routing_snapshot import (
    ExcludedCandidate,
    RankedCallable,
    SnapshotRejected,
    build_snapshot,
    last_known_good_path,
    load_best,
    publish,
    validate,
)

FIXTURES = Path(__file__).parent / "fixtures" / "catalogs"
NOW = datetime(2026, 7, 23, 12, 30, tzinfo=timezone.utc)


def _record():
    catalog = load_catalog(FIXTURES / "valid_callable_catalog.json")
    assert catalog is not None
    return catalog.records[0]


def _snapshot(**overrides):
    values = {
        "generated_at": "2026-07-23T12:00:00Z",
        "expires_at": "2026-07-23T13:00:00Z",
        "catalog_version": "catalog:sha256:abc",
        "policy_version": "policy:1.0.0",
        "request_class": "coding:tool-use",
        "candidates": [
            RankedCallable(
                rank=1,
                record=_record(),
                capability_ref="capability:qwen3-coder",
                quota_ref="quota:openrouter:current-key",
                eligibility_reasons=("tools-supported", "quota-available"),
                evidence_refs=("catalog:fixture", "quota:fixture"),
            )
        ],
        "excluded_candidates": [
            ExcludedCandidate(
                candidate_ref="capability:unknown-display-name",
                reasons=("unresolved-identity",),
                evidence_refs=("identity-map:fixture",),
            )
        ],
        "evidence_refs": ["policy:fixture", "catalog:fixture"],
    }
    values.update(overrides)
    return build_snapshot(**values)


def test_build_is_deterministic_and_self_contained():
    first = _snapshot()
    second = _snapshot()
    assert first == second
    assert first["snapshot_id"].startswith("sha256:")
    assert first["candidates"][0]["api_model_id"] == "qwen/qwen3-coder:free"
    assert first["candidates"][0]["credential_ref"] == "OPENROUTER_API_KEY"


def test_content_mutation_invalidates_snapshot_id():
    snapshot = _snapshot()
    snapshot["candidates"][0]["api_model_id"] = "different"
    with pytest.raises(SnapshotRejected, match="snapshot_id"):
        validate(snapshot)


def test_ranks_must_be_ordered_and_contiguous():
    candidate = RankedCallable(
        rank=2,
        record=_record(),
        capability_ref="capability:qwen3-coder",
        quota_ref="quota:openrouter",
        eligibility_reasons=("eligible",),
        evidence_refs=("catalog:fixture",),
    )
    with pytest.raises(SnapshotRejected, match="ranks"):
        _snapshot(candidates=[candidate])


def test_publish_writes_current_and_recovery_atomically(tmp_path):
    target = tmp_path / "routing-snapshot.json"
    snapshot = _snapshot()
    publish(snapshot, target, now=NOW)

    assert json.loads(target.read_text(encoding="utf-8")) == snapshot
    assert json.loads(last_known_good_path(target).read_text(encoding="utf-8")) == snapshot
    assert target.stat().st_mode & 0o077 == 0


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (lambda snapshot: snapshot.update(schema_version="2.0.0"), "unsupported"),
        (
            lambda snapshot: snapshot.update(expires_at="2026-07-23T12:15:00Z"),
            "stale",
        ),
    ],
)
def test_invalid_replacement_does_not_touch_known_good(tmp_path, mutation, expected):
    target = tmp_path / "routing-snapshot.json"
    known_good = _snapshot()
    publish(known_good, target, now=NOW)
    before = target.read_bytes()

    replacement = copy.deepcopy(known_good)
    mutation(replacement)
    replacement["snapshot_id"] = "sha256:" + "0" * 64
    if expected == "stale":
        replacement = _snapshot(expires_at="2026-07-23T12:15:00Z")

    with pytest.raises(SnapshotRejected, match=expected):
        publish(replacement, target, now=NOW)
    assert target.read_bytes() == before
    assert last_known_good_path(target).read_bytes() == before


def test_missing_or_partial_current_recovers_last_known_good(tmp_path):
    target = tmp_path / "routing-snapshot.json"
    snapshot = _snapshot()
    publish(snapshot, target, now=NOW)

    target.unlink()
    missing = load_best(target, now=NOW)
    assert missing.source == "last-known-good"
    assert missing.snapshot == snapshot
    assert missing.failures == ("current:missing",)

    target.write_text('{"partial":', encoding="utf-8")
    partial = load_best(target, now=NOW)
    assert partial.source == "last-known-good"
    assert partial.snapshot == snapshot
    assert partial.failures[0].startswith("current:unreadable:")


def test_failed_current_replace_preserves_prior_current_and_valid_recovery(tmp_path, monkeypatch):
    target = tmp_path / "routing-snapshot.json"
    prior = _snapshot()
    publish(prior, target, now=NOW)
    prior_bytes = target.read_bytes()
    replacement = _snapshot(policy_version="policy:1.0.1")

    real_atomic_replace = snapshot_module._atomic_replace
    calls = 0

    def fail_second_replace(path, content):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated current replacement failure")
        real_atomic_replace(path, content)

    monkeypatch.setattr(snapshot_module, "_atomic_replace", fail_second_replace)
    with pytest.raises(OSError, match="simulated"):
        publish(replacement, target, now=NOW)

    assert target.read_bytes() == prior_bytes
    recovered = load_best(target, now=NOW)
    assert recovered.source == "current"
    assert recovered.snapshot == prior
    assert json.loads(last_known_good_path(target).read_text(encoding="utf-8")) == replacement


def test_stale_or_incompatible_current_recovers_last_known_good(tmp_path):
    target = tmp_path / "routing-snapshot.json"
    known_good = _snapshot()
    publish(known_good, target, now=NOW)

    stale = _snapshot(expires_at="2026-07-23T12:15:00Z")
    target.write_text(json.dumps(stale), encoding="utf-8")
    recovered = load_best(target, now=NOW)
    assert recovered.source == "last-known-good"
    assert recovered.snapshot == known_good
    assert recovered.failures == ("current:snapshot is stale",)

    incompatible = copy.deepcopy(known_good)
    incompatible["schema_version"] = "2.0.0"
    incompatible["snapshot_id"] = "sha256:" + "0" * 64
    target.write_text(json.dumps(incompatible), encoding="utf-8")
    recovered = load_best(target, now=NOW)
    assert recovered.source == "last-known-good"
    assert recovered.snapshot == known_good
    assert recovered.failures[0].startswith("current:unsupported schema version")


def test_empty_or_duplicate_evidence_is_rejected():
    with pytest.raises(SnapshotRejected):
        _snapshot(evidence_refs=[])
    with pytest.raises(SnapshotRejected):
        _snapshot(evidence_refs=["catalog:fixture", "catalog:fixture"])
