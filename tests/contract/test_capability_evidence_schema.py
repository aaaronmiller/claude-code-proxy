"""Strict capability evidence contract excludes callable identity fields."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_PATH = (
    ROOT / "specs" / "003-model-scan-integration" / "contracts" / "capability_evidence.schema.json"
)


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def evidence():
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-07-23T14:00:00Z",
        "source": "model-scan:test",
        "records": [
            {
                "capability_id": "model-scan:openrouter:qwen3-coder",
                "model_identity": "openrouter:qwen3-coder",
                "dimensions": {"coding": 91.2, "agentic": 88.0},
                "features": ["tools"],
                "health": "healthy",
                "cost": {
                    "input_per_million": 0.0,
                    "output_per_million": 0.0,
                    "blended_per_million": 0.0,
                },
                "latency_ms": 450.0,
                "confidence": 0.92,
                "evidence_refs": ["scan:fixture"],
                "measured_at": "2026-07-23T14:00:00Z",
            }
        ],
    }


def test_valid_evidence_passes_schema(validator, evidence):
    assert list(validator.iter_errors(evidence)) == []


@pytest.mark.parametrize(
    "field",
    [
        "capability_id",
        "model_identity",
        "dimensions",
        "features",
        "health",
        "cost",
        "latency_ms",
        "confidence",
        "evidence_refs",
        "measured_at",
    ],
)
def test_required_capability_fields_are_enforced(validator, evidence, field):
    broken = copy.deepcopy(evidence)
    del broken["records"][0][field]
    assert list(validator.iter_errors(broken))


@pytest.mark.parametrize(
    "forbidden_field",
    ["provider_id", "api_model_id", "base_url", "credential_ref", "callable_id"],
)
def test_callable_fields_are_forbidden(validator, evidence, forbidden_field):
    broken = copy.deepcopy(evidence)
    broken["records"][0][forbidden_field] = "not-capability-evidence"
    assert list(validator.iter_errors(broken))


def test_unknown_health_or_out_of_range_confidence_is_rejected(validator, evidence):
    health = copy.deepcopy(evidence)
    health["records"][0]["health"] = "probably"
    assert list(validator.iter_errors(health))

    confidence = copy.deepcopy(evidence)
    confidence["records"][0]["confidence"] = 1.1
    assert list(validator.iter_errors(confidence))
