"""Strict contract tests for exact callable identity records."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).parents[2]
SCHEMA_PATH = (
    ROOT / "specs" / "003-model-scan-integration" / "contracts" / "callable_catalog.schema.json"
)
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "catalogs" / "valid_callable_catalog.json"


@pytest.fixture
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.fixture
def catalog():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_catalog_passes(validator, catalog):
    assert list(validator.iter_errors(catalog)) == []


@pytest.mark.parametrize(
    "field",
    [
        "provider_id",
        "api_model_id",
        "base_url",
        "credential_ref",
        "observed_at",
        "provenance",
    ],
)
def test_missing_exact_identity_field_is_rejected(validator, catalog, field):
    broken = copy.deepcopy(catalog)
    del broken["records"][0][field]
    assert list(validator.iter_errors(broken))


def test_secret_value_cannot_be_used_as_credential_reference(validator, catalog):
    broken = copy.deepcopy(catalog)
    broken["records"][0]["credential_ref"] = "sk-or-v1-secret-value"
    assert list(validator.iter_errors(broken))


def test_unknown_record_field_is_rejected(validator, catalog):
    broken = copy.deepcopy(catalog)
    broken["records"][0]["display_name_guess"] = "qwen coder"
    assert list(validator.iter_errors(broken))


def test_schema_version_and_dates_are_enforced(validator, catalog):
    broken_version = copy.deepcopy(catalog)
    broken_version["schema_version"] = "1.0"
    assert list(validator.iter_errors(broken_version))

    broken_date = copy.deepcopy(catalog)
    broken_date["records"][0]["observed_at"] = "yesterday"
    assert list(validator.iter_errors(broken_date))
