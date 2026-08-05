"""Strict schema tests keep classifier evidence separate from model choice."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_PATH = (
    ROOT / "specs" / "003-model-scan-integration" / "contracts" / "task_classification.schema.json"
)


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def classification():
    return {
        "schema_version": "1.0.0",
        "classification_id": "sha256:" + "0" * 64,
        "classified_at": "2026-07-23T13:00:00Z",
        "classifier_version": "adrf:2.0.0",
        "taxonomy_version": "taxonomy:2026-07",
        "input_ref": "request:sha256:abc",
        "task_class": "code_patch",
        "task_family": "code_patch",
        "required_capabilities": ["tools", "code_edit"],
        "privacy_class": "proprietary",
        "importance": "high",
        "confidence": 0.9,
        "decision_provenance": ["classifier:fixture"],
    }


def test_valid_classification_passes_schema(validator, classification):
    assert list(validator.iter_errors(classification)) == []


@pytest.mark.parametrize(
    "field",
    [
        "task_class",
        "task_family",
        "required_capabilities",
        "privacy_class",
        "importance",
        "confidence",
        "decision_provenance",
    ],
)
def test_required_decision_fields_are_enforced(validator, classification, field):
    broken = copy.deepcopy(classification)
    del broken[field]
    assert list(validator.iter_errors(broken))


@pytest.mark.parametrize(
    "forbidden_field",
    ["model", "model_id", "selected_model_id", "provider", "callable_id"],
)
def test_callable_selection_fields_are_forbidden(validator, classification, forbidden_field):
    broken = copy.deepcopy(classification)
    broken[forbidden_field] = "openrouter/model"
    assert list(validator.iter_errors(broken))


def test_privacy_and_confidence_are_bounded(validator, classification):
    privacy = copy.deepcopy(classification)
    privacy["privacy_class"] = "guess"
    assert list(validator.iter_errors(privacy))

    confidence = copy.deepcopy(classification)
    confidence["confidence"] = 1.01
    assert list(validator.iter_errors(confidence))
