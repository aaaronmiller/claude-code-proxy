"""Strict, content-addressed evidence for non-executing route comparisons."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_VERSION = "1.0.0"
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "shadow_comparison.schema.json"
)
DIMENSIONS = (
    "compatibility",
    "privacy",
    "quota",
    "cost",
    "latency",
    "capability",
    "fallbacks",
)


class ShadowComparisonRejected(ValueError):
    """Raised when shadow evidence is incomplete, inconsistent, or mutated."""


@dataclass(frozen=True)
class MetricEvidence:
    status: str
    summary: str
    numeric_value: float | None = None
    unit: str | None = None
    items: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouteFacts:
    model_id: str
    provider_id: str
    base_url: str
    fallbacks: tuple[str, ...]
    dimensions: Mapping[str, MetricEvidence]


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _metric_dict(metric: MetricEvidence) -> dict[str, Any]:
    return {
        "status": metric.status,
        "summary": metric.summary,
        "numeric_value": metric.numeric_value,
        "unit": metric.unit,
        "items": list(metric.items),
        "evidence_refs": list(metric.evidence_refs),
    }


def _route_dict(route: RouteFacts) -> dict[str, Any]:
    return {
        "model_id": route.model_id,
        "provider_id": route.provider_id,
        "base_url": route.base_url,
        "fallbacks": list(route.fallbacks),
    }


def _comparable(metric: MetricEvidence) -> tuple[Any, ...]:
    return (
        metric.summary,
        metric.numeric_value,
        metric.unit,
        metric.items,
    )


def _difference(
    dimension: str,
    active: MetricEvidence,
    shadow: MetricEvidence,
) -> dict[str, Any]:
    if active.status == "unknown" or shadow.status == "unknown":
        status = "unknown"
    elif _comparable(active) == _comparable(shadow):
        status = "same"
    else:
        status = "different"
    return {
        "dimension": dimension,
        "status": status,
        "active": _metric_dict(active),
        "shadow": _metric_dict(shadow),
    }


def _canonical_payload(record: dict[str, Any]) -> bytes:
    payload = dict(record)
    payload.pop("comparison_id", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _comparison_id(record: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_payload(record)).hexdigest()


def build_comparison(
    *,
    observed_at: str,
    assignment_id: str,
    source_scan_id: int,
    source_schema_version: str,
    active_route: RouteFacts,
    shadow_route: RouteFacts,
    evidence_refs: tuple[str, ...],
) -> dict[str, Any]:
    """Build evidence only; the active route remains execution authority."""
    active_dimensions = set(active_route.dimensions)
    shadow_dimensions = set(shadow_route.dimensions)
    required_dimensions = set(DIMENSIONS)
    if active_dimensions != required_dimensions:
        raise ShadowComparisonRejected(
            f"active route dimensions must be exactly {list(DIMENSIONS)}"
        )
    if shadow_dimensions != required_dimensions:
        raise ShadowComparisonRejected(
            f"shadow route dimensions must be exactly {list(DIMENSIONS)}"
        )

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "comparison_id": "",
        "observed_at": observed_at,
        "assignment_id": assignment_id,
        "source_scan_id": source_scan_id,
        "source_schema_version": source_schema_version,
        "execution_route": "active",
        "execution_changed": False,
        "active_route": _route_dict(active_route),
        "shadow_route": _route_dict(shadow_route),
        "differences": [
            _difference(
                dimension,
                active_route.dimensions[dimension],
                shadow_route.dimensions[dimension],
            )
            for dimension in DIMENSIONS
        ],
        "evidence_refs": list(evidence_refs),
    }
    record["comparison_id"] = _comparison_id(record)
    validate(record)
    return record


def validate(record: Any) -> None:
    """Validate schema, content identity, dimension order, and evidence invariants."""
    if not isinstance(record, dict):
        raise ShadowComparisonRejected("shadow comparison must be an object")
    errors = sorted(_validator().iter_errors(record), key=lambda error: list(error.path))
    if errors:
        raise ShadowComparisonRejected(errors[0].message)
    if record["comparison_id"] != _comparison_id(record):
        raise ShadowComparisonRejected("comparison_id does not match canonical content")

    dimensions = [difference["dimension"] for difference in record["differences"]]
    if dimensions != list(DIMENSIONS):
        raise ShadowComparisonRejected(
            f"comparison dimensions must be ordered exactly {list(DIMENSIONS)}"
        )
    for difference in record["differences"]:
        for side in ("active", "shadow"):
            metric = difference[side]
            if metric["status"] == "unknown":
                if metric["numeric_value"] is not None or metric["unit"] is not None:
                    raise ShadowComparisonRejected(
                        f"unknown {difference['dimension']} evidence cannot carry a numeric value"
                    )
                if metric["items"]:
                    raise ShadowComparisonRejected(
                        f"unknown {difference['dimension']} evidence cannot carry items"
                    )
