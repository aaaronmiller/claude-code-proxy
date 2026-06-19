"""Contract test for the routing_snapshot schema (T001, T015 mirror).

Validates that the shared `routing_snapshot.schema.json` contract — the only coupling
surface between model-scan (producer) and claude-code-proxy (consumer) — accepts a
representative valid snapshot and rejects the failure modes the loader (T020) relies on
the schema to catch. The schema itself does no major-version refusal or TTL work; those
are loader concerns. This test asserts only the structural contract.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = (
    _REPO_ROOT
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "routing_snapshot.schema.json"
)
_FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text())
    # Fail loudly if the schema itself is malformed rather than silently passing.
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def snapshot() -> dict:
    return json.loads(_FIXTURE_PATH.read_text())


def test_valid_snapshot_passes(validator: Draft202012Validator, snapshot: dict) -> None:
    errors = sorted(validator.iter_errors(snapshot), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


def test_null_best_with_empty_candidates_allowed(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    # The R_curator slot exercises the "no candidate qualified" branch (best: null).
    assert snapshot["slots"]["R_curator"]["best"] is None
    assert list(validator.iter_errors(snapshot)) == []


def test_missing_required_top_level_field_rejected(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    broken = copy.deepcopy(snapshot)
    del broken["blocklist"]
    assert validator.iter_errors(broken)


def test_unknown_top_level_property_rejected(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    broken = copy.deepcopy(snapshot)
    broken["unexpected_field"] = True
    assert validator.iter_errors(broken)


def test_bad_eval_mode_enum_rejected(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    broken = copy.deepcopy(snapshot)
    broken["slots"]["R1_primary"]["eval_mode"] = "guesswork"
    assert validator.iter_errors(broken)


def test_null_price_blended_allowed(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    # price_blended null means "unknown" — eligible for non-budget policies only.
    variant = copy.deepcopy(snapshot)
    variant["slots"]["R1_primary"]["best"]["price_blended"] = None
    assert list(validator.iter_errors(variant)) == []


def test_candidate_missing_required_field_rejected(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    broken = copy.deepcopy(snapshot)
    del broken["slots"]["R1_primary"]["best"]["api_model"]
    assert validator.iter_errors(broken)


def test_schema_version_pattern_enforced(
    validator: Draft202012Validator, snapshot: dict
) -> None:
    broken = copy.deepcopy(snapshot)
    broken["schema_version"] = "1.0"  # not MAJOR.MINOR.PATCH
    assert validator.iter_errors(broken)
