"""Strict Gateway consumer for independent Model Scan capability evidence."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

logger = logging.getLogger(__name__)
SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "capability_evidence.schema.json"
)


@dataclass(frozen=True)
class CapabilityCost:
    input_per_million: float | None
    output_per_million: float | None
    blended_per_million: float | None


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    model_identity: str
    dimensions: dict[str, float]
    features: tuple[str, ...]
    health: str
    cost: CapabilityCost
    latency_ms: float | None
    confidence: float
    evidence_refs: tuple[str, ...]
    measured_at: str


@dataclass(frozen=True)
class CapabilityEvidence:
    schema_version: str
    generated_at: str
    source: str
    records: tuple[CapabilityRecord, ...]

    def by_id(self) -> dict[str, CapabilityRecord]:
        return {record.capability_id: record for record in self.records}


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _major(version: str) -> int | None:
    try:
        return int(version.split(".", 1)[0])
    except (AttributeError, ValueError):
        return None


def from_data(data: Any, *, source: str = "memory") -> CapabilityEvidence | None:
    if not isinstance(data, dict):
        return None
    errors = sorted(_validator().iter_errors(data), key=lambda error: list(error.path))
    if errors:
        logger.warning(
            "capability evidence rejected from %s: %s",
            source,
            errors[0].message,
        )
        return None
    if _major(data["schema_version"]) != SUPPORTED_SCHEMA_MAJOR:
        logger.warning(
            "capability evidence from %s has unsupported schema version %s",
            source,
            data["schema_version"],
        )
        return None

    records = tuple(
        CapabilityRecord(
            capability_id=record["capability_id"],
            model_identity=record["model_identity"],
            dimensions=dict(record["dimensions"]),
            features=tuple(record["features"]),
            health=record["health"],
            cost=CapabilityCost(**record["cost"]),
            latency_ms=record["latency_ms"],
            confidence=record["confidence"],
            evidence_refs=tuple(record["evidence_refs"]),
            measured_at=record["measured_at"],
        )
        for record in data["records"]
    )
    ids = [record.capability_id for record in records]
    if len(ids) != len(set(ids)):
        logger.warning(
            "capability evidence rejected from %s: duplicate capability_id",
            source,
        )
        return None
    return CapabilityEvidence(
        schema_version=data["schema_version"],
        generated_at=data["generated_at"],
        source=data["source"],
        records=records,
    )


def load(path: str | Path) -> CapabilityEvidence | None:
    source = str(path)
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return from_data(data, source=source)
