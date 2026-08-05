"""Callable catalog loader preserves exact identity and rejects ambiguity."""

import copy
import json
from pathlib import Path

from src.services.models.callable_catalog import from_data, load

FIXTURE = Path(__file__).parent / "fixtures" / "catalogs" / "valid_callable_catalog.json"


def _data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_loader_freezes_exact_record():
    catalog = load(FIXTURE)
    assert catalog is not None
    record = catalog.records[0]
    assert record.provider_id == "openrouter"
    assert record.api_model_id == "qwen/qwen3-coder:free"
    assert record.base_url == "https://openrouter.ai/api/v1"
    assert record.credential_ref == "OPENROUTER_API_KEY"
    assert catalog.by_id()[record.callable_id] == record


def test_loader_rejects_duplicate_callable_id():
    data = _data()
    data["records"].append(copy.deepcopy(data["records"][0]))
    assert from_data(data) is None


def test_loader_rejects_unsupported_major_and_partial_record():
    newer = _data()
    newer["schema_version"] = "2.0.0"
    assert from_data(newer) is None

    partial = _data()
    del partial["records"][0]["base_url"]
    assert from_data(partial) is None


def test_missing_or_corrupt_file_returns_none(tmp_path):
    assert load(tmp_path / "missing.json") is None
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{", encoding="utf-8")
    assert load(corrupt) is None
