"""Explicit capability-to-callable identity resolution with no name inference."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from src.services.models.callable_catalog import CallableCatalog, CallableRecord

logger = logging.getLogger(__name__)
SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "callable_identity_mapping.schema.json"
)


@dataclass(frozen=True)
class IdentityMapping:
    capability_id: str
    callable_id: str
    provenance: tuple[str, ...]


@dataclass(frozen=True)
class IdentityMap:
    schema_version: str
    generated_at: str
    mappings: tuple[IdentityMapping, ...]


@dataclass(frozen=True)
class IdentityExclusion:
    capability_id: str
    reason: str
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class IdentityResolution:
    resolved: tuple[tuple[str, CallableRecord], ...]
    excluded: tuple[IdentityExclusion, ...]


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


def from_data(data: Any, *, source: str = "memory") -> IdentityMap | None:
    if not isinstance(data, dict):
        return None
    errors = sorted(_validator().iter_errors(data), key=lambda error: list(error.path))
    if errors or _major(data.get("schema_version")) != SUPPORTED_SCHEMA_MAJOR:
        if errors:
            logger.warning(
                "callable identity map rejected from %s: %s",
                source,
                errors[0].message,
            )
        return None
    return IdentityMap(
        schema_version=data["schema_version"],
        generated_at=data["generated_at"],
        mappings=tuple(
            IdentityMapping(
                capability_id=mapping["capability_id"],
                callable_id=mapping["callable_id"],
                provenance=tuple(mapping["provenance"]),
            )
            for mapping in data["mappings"]
        ),
    )


def load(path: str | Path) -> IdentityMap | None:
    source = str(path)
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return from_data(data, source=source)


def resolve(
    capability_ids: Iterable[str],
    catalog: CallableCatalog,
    identity_map: IdentityMap,
) -> IdentityResolution:
    """Resolve only exact, explicit mappings and report every exclusion."""
    catalog_by_id = catalog.by_id()
    mappings_by_capability: dict[str, list[IdentityMapping]] = {}
    for mapping in identity_map.mappings:
        mappings_by_capability.setdefault(mapping.capability_id, []).append(mapping)

    resolved: list[tuple[str, CallableRecord]] = []
    excluded: list[IdentityExclusion] = []
    for capability_id in capability_ids:
        mappings = mappings_by_capability.get(capability_id, [])
        callable_ids = tuple(sorted({mapping.callable_id for mapping in mappings}))
        if not mappings:
            excluded.append(IdentityExclusion(capability_id, "unresolved-identity"))
            continue
        if len(callable_ids) != 1:
            excluded.append(
                IdentityExclusion(
                    capability_id,
                    "ambiguous-identity",
                    callable_ids,
                )
            )
            continue
        record = catalog_by_id.get(callable_ids[0])
        if record is None:
            excluded.append(
                IdentityExclusion(
                    capability_id,
                    "missing-callable",
                    callable_ids,
                )
            )
            continue
        if not record.reachable:
            excluded.append(
                IdentityExclusion(
                    capability_id,
                    "unreachable-callable",
                    callable_ids,
                )
            )
            continue
        resolved.append((capability_id, record))

    return IdentityResolution(tuple(resolved), tuple(excluded))
