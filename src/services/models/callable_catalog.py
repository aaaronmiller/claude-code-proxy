"""Strict consumer for the versioned Model Scraper callable catalog."""

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
    / "callable_catalog.schema.json"
)


@dataclass(frozen=True)
class CallableRecord:
    callable_id: str
    provider_id: str
    api_model_id: str
    base_url: str
    credential_ref: str
    observed_at: str
    reachable: bool
    features: tuple[str, ...]
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class CallableCatalog:
    schema_version: str
    generated_at: str
    source: str
    records: tuple[CallableRecord, ...]

    def by_id(self) -> dict[str, CallableRecord]:
        return {record.callable_id: record for record in self.records}


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


def from_data(data: Any, *, source: str = "memory") -> CallableCatalog | None:
    """Validate and freeze a catalog without inferring any missing identity."""
    if not isinstance(data, dict):
        return None
    errors = sorted(_validator().iter_errors(data), key=lambda error: list(error.path))
    if errors:
        logger.warning("callable catalog rejected from %s: %s", source, errors[0].message)
        return None
    if _major(data["schema_version"]) != SUPPORTED_SCHEMA_MAJOR:
        logger.warning(
            "callable catalog from %s has unsupported schema version %s",
            source,
            data["schema_version"],
        )
        return None

    records = tuple(
        CallableRecord(
            callable_id=record["callable_id"],
            provider_id=record["provider_id"],
            api_model_id=record["api_model_id"],
            base_url=record["base_url"],
            credential_ref=record["credential_ref"],
            observed_at=record["observed_at"],
            reachable=record["reachable"],
            features=tuple(record["features"]),
            provenance=tuple(record["provenance"]),
        )
        for record in data["records"]
    )
    ids = [record.callable_id for record in records]
    if len(ids) != len(set(ids)):
        logger.warning("callable catalog rejected from %s: duplicate callable_id", source)
        return None

    return CallableCatalog(
        schema_version=data["schema_version"],
        generated_at=data["generated_at"],
        source=data["source"],
        records=records,
    )


def load(path: str | Path) -> CallableCatalog | None:
    """Load a complete catalog or return ``None`` without mutating prior state."""
    source = str(path)
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return from_data(data, source=source)
