"""Gateway consumes independent capability evidence without callable inference."""

import copy
import json
from pathlib import Path

from src.services.models.capability_evidence import from_data, load

FIXTURE = Path(__file__).parent / "fixtures" / "capabilities" / "valid_capability_evidence.json"


def _data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_model_scan_fixture_loads_to_immutable_records():
    evidence = load(FIXTURE)
    assert evidence is not None
    record = evidence.records[0]
    assert record.capability_id == ("model-scan:openrouter:qwen/qwen3-coder:free")
    assert record.model_identity == "qwen/qwen3-coder:free"
    assert record.features == ("tools", "context:131072")
    assert record.cost.blended_per_million == 0.0


def test_callable_identity_fields_are_rejected():
    data = _data()
    data["records"][0]["api_model_id"] = "inferred/model"
    assert from_data(data) is None


def test_duplicate_capability_identity_is_rejected():
    data = _data()
    data["records"].append(copy.deepcopy(data["records"][0]))
    assert from_data(data) is None


def test_unknown_major_and_invalid_confidence_are_rejected():
    unknown = _data()
    unknown["schema_version"] = "2.0.0"
    assert from_data(unknown) is None

    confidence = _data()
    confidence["records"][0]["confidence"] = 1.1
    assert from_data(confidence) is None
