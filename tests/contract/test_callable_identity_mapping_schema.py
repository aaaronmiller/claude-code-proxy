"""Strict contract tests for explicit capability-to-callable mappings."""

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
    / "callable_identity_mapping.schema.json"
)
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "catalogs" / "valid_callable_identity_mapping.json"


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def identity_map():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_identity_map_passes(validator, identity_map):
    assert list(validator.iter_errors(identity_map)) == []


@pytest.mark.parametrize("field", ["capability_id", "callable_id", "provenance"])
def test_missing_mapping_field_is_rejected(validator, identity_map, field):
    broken = copy.deepcopy(identity_map)
    del broken["mappings"][0][field]
    assert list(validator.iter_errors(broken))


def test_mapping_requires_provenance(validator, identity_map):
    broken = copy.deepcopy(identity_map)
    broken["mappings"][0]["provenance"] = []
    assert list(validator.iter_errors(broken))


def test_unknown_inference_field_is_rejected(validator, identity_map):
    broken = copy.deepcopy(identity_map)
    broken["mappings"][0]["display_name_guess"] = "Qwen Coder"
    assert list(validator.iter_errors(broken))


def test_schema_version_and_timestamp_are_enforced(validator, identity_map):
    broken_version = copy.deepcopy(identity_map)
    broken_version["schema_version"] = "1"
    assert list(validator.iter_errors(broken_version))

    broken_date = copy.deepcopy(identity_map)
    broken_date["generated_at"] = "today"
    assert list(validator.iter_errors(broken_date))
