"""Content-addressed shadow evidence cannot change execution or persistent state."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.core.model_scan_binder import BindResult
from src.services.models.shadow_comparison import (
    DIMENSIONS,
    MetricEvidence,
    RouteFacts,
    ShadowComparisonRejected,
    build_comparison,
    validate,
)

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"
OBSERVED_AT = "2026-07-24T12:00:00Z"


def _known(
    summary: str,
    *,
    number: float | None = None,
    unit: str | None = None,
    items: tuple[str, ...] = (),
    ref: str = "evidence:fixture",
) -> MetricEvidence:
    return MetricEvidence(
        status="known",
        summary=summary,
        numeric_value=number,
        unit=unit,
        items=items,
        evidence_refs=(ref,),
    )


def _unknown(summary: str) -> MetricEvidence:
    return MetricEvidence(
        status="unknown",
        summary=summary,
        evidence_refs=("absence:fixture",),
    )


def _route(*, shadow: bool) -> RouteFacts:
    if shadow:
        dimensions = {
            "compatibility": _known("compatible", items=("tools=supported",)),
            "privacy": _unknown("privacy evidence unavailable"),
            "quota": _known("remaining", number=0.75, unit="remaining_fraction"),
            "cost": _known("blended", number=0.0, unit="usd_per_million_blended"),
            "latency": _unknown("latency evidence unavailable"),
            "capability": _known("fitness", number=0.9, unit="fitness"),
            "fallbacks": _known("one fallback", items=("shadow/fallback",)),
        }
        return RouteFacts(
            model_id="shadow/model",
            provider_id="shadow",
            base_url="https://shadow.example/v1",
            fallbacks=("shadow/fallback",),
            dimensions=dimensions,
        )
    dimensions = {
        "compatibility": _known("compatible", items=("tools=supported",)),
        "privacy": _unknown("privacy evidence unavailable"),
        "quota": _known("remaining", number=0.5, unit="remaining_fraction"),
        "cost": _known("blended", number=0.0, unit="usd_per_million_blended"),
        "latency": _unknown("latency evidence unavailable"),
        "capability": _known("fitness", number=0.8, unit="fitness"),
        "fallbacks": _known("one fallback", items=("active/fallback",)),
    }
    return RouteFacts(
        model_id="active/model",
        provider_id="active",
        base_url="https://active.example/v1",
        fallbacks=("active/fallback",),
        dimensions=dimensions,
    )


def _comparison():
    return build_comparison(
        observed_at=OBSERVED_AT,
        assignment_id="big",
        source_scan_id=1487,
        source_schema_version="1.0.0",
        active_route=_route(shadow=False),
        shadow_route=_route(shadow=True),
        evidence_refs=("active:fixture", "shadow:fixture"),
    )


def _write_state(tmp_path: Path) -> tuple[Path, Path]:
    chain_path = tmp_path / "proxy_chain.json"
    chain_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "entries": [],
                "router": {},
                "assignments": [
                    {
                        "id": "big",
                        "kind": "tier",
                        "model": "static/big",
                        "provider": "static",
                        "base_url": "https://user:password@static.example/v1?api_key=secret",
                        "api_key": "must-not-appear",
                        "enabled": True,
                        "cascade": ["static/fallback"],
                    }
                ],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(SNAPSHOT),
                    "staleness_limit_s": 315360000,
                },
            }
        ),
        encoding="utf-8",
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps({"default": {"slot_bindings": {"big": "R1_primary"}}}),
        encoding="utf-8",
    )
    return chain_path, profiles_path


def test_record_is_deterministic_and_dimensions_are_independently_visible():
    first = _comparison()
    second = _comparison()

    assert first == second
    assert first["comparison_id"].startswith("sha256:")
    assert first["execution_route"] == "active"
    assert first["execution_changed"] is False
    assert [item["dimension"] for item in first["differences"]] == list(DIMENSIONS)
    status = {item["dimension"]: item["status"] for item in first["differences"]}
    assert status == {
        "compatibility": "same",
        "privacy": "unknown",
        "quota": "different",
        "cost": "same",
        "latency": "unknown",
        "capability": "different",
        "fallbacks": "different",
    }


def test_validation_rejects_mutation_extensions_and_false_execution_claim():
    record = _comparison()

    changed = copy.deepcopy(record)
    changed["shadow_route"]["model_id"] = "mutated"
    with pytest.raises(ShadowComparisonRejected, match="comparison_id"):
        validate(changed)

    extended = copy.deepcopy(record)
    extended["credential_ref"] = "SECRET_KEY"
    with pytest.raises(ShadowComparisonRejected, match="Additional properties"):
        validate(extended)

    executed = copy.deepcopy(record)
    executed["execution_changed"] = True
    with pytest.raises(ShadowComparisonRejected):
        validate(executed)


def test_unknown_evidence_cannot_carry_asserted_values():
    record = _comparison()
    privacy = next(
        item for item in record["differences"] if item["dimension"] == "privacy"
    )
    privacy["shadow"]["numeric_value"] = 1
    record["comparison_id"] = (
        "sha256:"
        + __import__("hashlib")
        .sha256(
            json.dumps(
                {key: value for key, value in record.items() if key != "comparison_id"},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        )
        .hexdigest()
    )
    with pytest.raises(ShadowComparisonRejected, match="unknown privacy"):
        validate(record)


def test_runtime_shadow_record_is_non_persisting_and_preserves_unknowns(
    monkeypatch,
    tmp_path,
):
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    live_chain = proxy_chain_module.reload_chain()
    baseline_binding = BindResult(scan_id=7, schema_version="baseline")
    baseline_allocation = {"enabled": False, "marker": "baseline"}
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_BINDING", baseline_binding)
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_ALLOCATION", baseline_allocation)

    chain_before = chain_path.read_bytes()
    profiles_before = profiles_path.read_bytes()
    assignments_before = [assignment.to_dict() for assignment in live_chain.assignments]

    result = model_scan_runtime.shadow_model_scan(profiles_path=profiles_path)

    assert result["mode"] == "shadow"
    assert result["execution_route"] == "active"
    assert result["execution_changed"] is False
    assert result["persistent_writes"] == []
    assert len(result["comparisons"]) == 1
    comparison = result["comparisons"][0]
    assert comparison["active_route"]["model_id"] == "static/big"
    assert comparison["active_route"]["base_url"] == "https://static.example/v1"
    assert comparison["shadow_route"]["model_id"] == (
        "openrouter/deepseek/deepseek-v4-flash:free"
    )
    dimensions = {item["dimension"]: item for item in comparison["differences"]}
    assert dimensions["privacy"]["status"] == "unknown"
    assert dimensions["latency"]["status"] == "unknown"
    assert dimensions["cost"]["active"]["status"] == "unknown"
    assert dimensions["cost"]["shadow"]["numeric_value"] == 0.0
    assert dimensions["fallbacks"]["status"] == "different"
    serialized = json.dumps(result)
    assert "must-not-appear" not in serialized
    assert "password" not in serialized
    assert "api_key=secret" not in serialized
    assert "credential_ref" not in serialized

    assert chain_path.read_bytes() == chain_before
    assert profiles_path.read_bytes() == profiles_before
    assert proxy_chain_module.get_chain() is live_chain
    assert [assignment.to_dict() for assignment in live_chain.assignments] == assignments_before
    assert model_scan_runtime.get_active_binding() is baseline_binding
    assert model_scan_runtime.get_active_allocation() == baseline_allocation


async def test_shadow_endpoint_uses_evidence_only_path(monkeypatch, tmp_path):
    from src.api.endpoints import shadow_model_scan_bindings
    from src.core import model_scan_runtime
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    proxy_chain_module.reload_chain()
    before = chain_path.read_bytes()

    result = await shadow_model_scan_bindings()

    assert result["mode"] == "shadow"
    assert result["execution_route"] == "active"
    assert result["execution_changed"] is False
    assert chain_path.read_bytes() == before
