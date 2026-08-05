"""Strict schema tests for the successor deterministic routing snapshot."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_PATH = (
    ROOT
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "deterministic_routing_snapshot.schema.json"
)


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def snapshot():
    return {
        "schema_version": "1.0.0",
        "snapshot_id": "sha256:" + "0" * 64,
        "generated_at": "2026-07-23T12:00:00Z",
        "expires_at": "2026-07-23T13:00:00Z",
        "catalog_version": "catalog:1",
        "policy_version": "policy:1",
        "request_class": "coding:tool-use",
        "candidates": [
            {
                "rank": 1,
                "callable_id": "openrouter:qwen/qwen3-coder:free",
                "provider_id": "openrouter",
                "api_model_id": "qwen/qwen3-coder:free",
                "base_url": "https://openrouter.ai/api/v1",
                "credential_ref": "OPENROUTER_API_KEY",
                "capability_ref": "capability:qwen3-coder",
                "quota_ref": "quota:openrouter:current-key",
                "eligibility_reasons": ["tools-supported", "quota-available"],
                "evidence_refs": ["catalog:fixture"],
            }
        ],
        "excluded_candidates": [
            {
                "candidate_ref": "capability:unknown",
                "reasons": ["unresolved-identity"],
                "evidence_refs": ["identity-map:fixture"],
            }
        ],
        "evidence_refs": ["policy:fixture"],
    }


def test_valid_snapshot_passes_schema(validator, snapshot):
    assert list(validator.iter_errors(snapshot)) == []


@pytest.mark.parametrize(
    "field",
    [
        "expires_at",
        "catalog_version",
        "policy_version",
        "request_class",
        "candidates",
        "excluded_candidates",
        "evidence_refs",
    ],
)
def test_required_top_level_fields_are_enforced(validator, snapshot, field):
    broken = copy.deepcopy(snapshot)
    del broken[field]
    assert list(validator.iter_errors(broken))


@pytest.mark.parametrize(
    "field",
    [
        "provider_id",
        "api_model_id",
        "base_url",
        "credential_ref",
        "capability_ref",
        "quota_ref",
        "eligibility_reasons",
        "evidence_refs",
    ],
)
def test_exact_candidate_fields_are_enforced(validator, snapshot, field):
    broken = copy.deepcopy(snapshot)
    del broken["candidates"][0][field]
    assert list(validator.iter_errors(broken))


def test_secret_value_and_unknown_field_are_rejected(validator, snapshot):
    secret = copy.deepcopy(snapshot)
    secret["candidates"][0]["credential_ref"] = "sk-secret"
    assert list(validator.iter_errors(secret))

    inferred = copy.deepcopy(snapshot)
    inferred["candidates"][0]["display_name_guess"] = "Qwen Coder"
    assert list(validator.iter_errors(inferred))
