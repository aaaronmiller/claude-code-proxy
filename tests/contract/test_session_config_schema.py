"""Contract test for the session_config schema (T003).

The session config is the per-session overlay the launcher passes with `--config`. It
composes over a preset and under inline args. This test pins the policy grammar (static,
free, quality, roles, budget:<ceiling>) and the additive-only shape so the launcher (T042)
and the ephemeral-profile API (T040) can rely on a validated structure.
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
    / "session_config.schema.json"
)
_FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "sessions" / "valid_session.json"


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = json.loads(_SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def session() -> dict:
    return json.loads(_FIXTURE_PATH.read_text())


def test_valid_session_passes(validator: Draft202012Validator, session: dict) -> None:
    errors = sorted(validator.iter_errors(session), key=lambda e: e.path)
    assert errors == [], [e.message for e in errors]


@pytest.mark.parametrize(
    "policy",
    ["static", "free", "quality", "roles", "budget:0.50", "budget:1", "budget:0.05"],
)
def test_accepted_policies(
    validator: Draft202012Validator, session: dict, policy: str
) -> None:
    variant = copy.deepcopy(session)
    variant["policy"] = policy
    assert list(validator.iter_errors(variant)) == [], policy


@pytest.mark.parametrize(
    "policy",
    ["budget", "budget:", "cheap", "budget:abc", "Free", "budget:0.5.0"],
)
def test_rejected_policies(
    validator: Draft202012Validator, session: dict, policy: str
) -> None:
    variant = copy.deepcopy(session)
    variant["policy"] = policy
    assert validator.iter_errors(variant), policy


def test_unknown_top_level_property_rejected(
    validator: Draft202012Validator, session: dict
) -> None:
    broken = copy.deepcopy(session)
    broken["compresss"] = True  # typo'd key must be rejected (additionalProperties: false)
    assert validator.iter_errors(broken)


def test_unknown_role_override_mode_rejected(
    validator: Draft202012Validator, session: dict
) -> None:
    broken = copy.deepcopy(session)
    broken["roles"]["big"]["mdoel"] = "x"  # typo'd override key
    assert validator.iter_errors(broken)


def test_minimal_empty_session_is_valid(validator: Draft202012Validator) -> None:
    # Every field is optional; an empty object is a no-op overlay and must validate.
    assert list(validator.iter_errors({})) == []
