"""Routing-snapshot loader (Model-Scan Integration, T020).

Loads, validates, and caches the `routing_snapshot.json` contract emitted by model-scan.
This is the consumer half of the only coupling surface between the two projects; see
`specs/003-model-scan-integration/contracts/routing_snapshot.schema.json` for the contract and
`design.md` sections 3.2 and 4.2 for the in-memory model and loader interface.

Design invariants honoured here:
  * The active snapshot is an immutable frozen dataclass graph, so a rebind is a single atomic
    reference swap and concurrent readers never observe a half-updated structure.
  * Invalid, truncated, or schema-incompatible input returns ``None`` — never a partial object —
    so the caller retains its last good snapshot (the degradation rule in data-model.md).
  * A *newer* major schema version is refused with a logged alert; the router does not guess at a
    forward-incompatible contract.
  * No credentials are ever read from the snapshot; ``base_url`` is an advisory hint only and the
    router gap-fills it from its own provider registry at bind time (research.md, base_url rule).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

logger = logging.getLogger(__name__)

# The router accepts any matching major version of the contract and refuses a newer major.
SUPPORTED_SCHEMA_MAJOR = 1

# Single canonical schema: the spec contract, resolved relative to the repo root so there is no
# second copy to drift. parents[3] of src/services/models/<file> is the repository root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = (
    _REPO_ROOT
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "routing_snapshot.schema.json"
)


# ─────────────────────────────────────────────────────────────────────────────
# Immutable in-memory model (design.md 3.2)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Candidate:
    model_id: str
    provider: str
    api_model: str
    base_url: str
    fitness: float
    price_blended: float | None
    tier: str
    has_tools: bool
    has_vision: bool


@dataclass(frozen=True)
class RoleSelection:
    label: str
    eval_mode: str
    best: Candidate | None
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class RoutingSnapshot:
    schema_version: str
    generated_at: str
    scan_id: int
    slots: dict[str, RoleSelection]
    provider_health: dict[str, str]
    provider_quota: dict[str, dict[str, Any]]
    blocklist: frozenset[str]
    loaded_at: float  # time.monotonic() at load; basis for cache TTL


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator | None:
    """Build and cache the contract validator. Returns None if the schema is unavailable.

    The feature defaults to disabled, so a missing schema degrades to "no snapshot" rather than
    raising; the caller keeps serving static config.
    """
    try:
        schema = json.loads(SCHEMA_PATH.read_text())
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema)
    except Exception as exc:  # noqa: BLE001 - any schema-load failure degrades to "no snapshot"
        logger.error("routing-snapshot schema unavailable at %s: %s", SCHEMA_PATH, exc)
        return None


def _major(version: str) -> int | None:
    try:
        return int(version.split(".", 1)[0])
    except (ValueError, AttributeError, IndexError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Parsing (applies schema defaults jsonschema does not inject)
# ─────────────────────────────────────────────────────────────────────────────


def _parse_candidate(raw: dict[str, Any]) -> Candidate:
    return Candidate(
        model_id=raw["model_id"],
        provider=raw["provider"],
        api_model=raw["api_model"],
        base_url=raw.get("base_url", ""),  # advisory; router gap-fills from its registry
        fitness=float(raw["fitness"]),
        price_blended=raw["price_blended"],  # already number-or-null per schema
        tier=raw.get("tier", "unknown"),
        has_tools=bool(raw["has_tools"]),
        has_vision=bool(raw["has_vision"]),
    )


def _parse_role(raw: dict[str, Any]) -> RoleSelection:
    best_raw = raw.get("best")
    return RoleSelection(
        label=raw["label"],
        eval_mode=raw["eval_mode"],
        best=_parse_candidate(best_raw) if best_raw is not None else None,
        candidates=tuple(_parse_candidate(c) for c in raw.get("candidates", [])),
    )


def _build(data: dict[str, Any], *, source: str) -> RoutingSnapshot | None:
    """Validate parsed JSON against the contract and build the immutable snapshot, or None."""
    validator = _validator()
    if validator is None:
        return None

    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        logger.warning(
            "routing snapshot from %s failed contract validation (%d error(s); first: %s)",
            source,
            len(errors),
            errors[0].message,
        )
        return None

    version = data["schema_version"]
    major = _major(version)
    if major is None:
        logger.warning("routing snapshot from %s has unparseable schema_version %r", source, version)
        return None
    if major > SUPPORTED_SCHEMA_MAJOR:
        logger.error(
            "ALERT: routing snapshot from %s is schema major v%d; router supports v%d. "
            "Refusing the snapshot and retaining the last good binding.",
            source,
            major,
            SUPPORTED_SCHEMA_MAJOR,
        )
        return None
    if major != SUPPORTED_SCHEMA_MAJOR:
        logger.warning(
            "routing snapshot from %s is schema major v%d; router supports v%d. Refusing.",
            source,
            major,
            SUPPORTED_SCHEMA_MAJOR,
        )
        return None

    return RoutingSnapshot(
        schema_version=version,
        generated_at=data["generated_at"],
        scan_id=int(data["scan_id"]),
        slots={role_id: _parse_role(sel) for role_id, sel in data["slots"].items()},
        provider_health=dict(data.get("provider_health", {})),
        provider_quota=dict(data.get("provider_quota", {})),
        blocklist=frozenset(data.get("blocklist", [])),
        loaded_at=time.monotonic(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public loader interface (design.md 4.2)
# ─────────────────────────────────────────────────────────────────────────────


def load(path: str) -> RoutingSnapshot | None:
    """Load and validate a snapshot from disk. Returns None on any failure.

    None covers a missing file, a truncated/invalid JSON document, a contract violation, and an
    incompatible major version. The caller keeps its last good snapshot.
    """
    try:
        text = Path(path).read_text()
    except OSError as exc:
        logger.warning("routing snapshot not readable at %s: %s", path, exc)
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("routing snapshot at %s is not valid JSON (truncated?): %s", path, exc)
        return None

    if not isinstance(data, dict):
        logger.warning("routing snapshot at %s is not a JSON object", path)
        return None

    return _build(data, source=path)


def from_gateway(url: str, timeout_s: float = 2.0) -> RoutingSnapshot | None:
    """Pull a snapshot from the model-scan gateway (admin/refresh path only). None on failure.

    Never used on the request hot path; the request path reads the in-memory AssignmentRegistry.
    """
    try:
        resp = httpx.get(url, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("routing snapshot gateway pull from %s failed: %s", url, exc)
        return None

    if not isinstance(data, dict):
        logger.warning("routing snapshot from gateway %s is not a JSON object", url)
        return None

    return _build(data, source=url)


def is_stale(snap: RoutingSnapshot, ttl_s: int) -> bool:
    """True if the cached snapshot is older than the cache TTL and should be re-read.

    Uses the monotonic load time, so it is unaffected by wall-clock changes.
    """
    return (time.monotonic() - snap.loaded_at) > ttl_s


def data_age_seconds(snap: RoutingSnapshot, *, now: datetime | None = None) -> float | None:
    """Seconds between the snapshot's wall-clock ``generated_at`` and now (None if unparseable).

    This answers data staleness (a producer frozen for a day) independently of cache TTL.
    """
    try:
        generated = datetime.fromisoformat(snap.generated_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning("routing snapshot generated_at unparseable: %r", snap.generated_at)
        return None
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (current - generated).total_seconds()


def is_data_stale(snap: RoutingSnapshot, staleness_limit_s: int, *, now: datetime | None = None) -> bool:
    """True if the snapshot's data is older than the staleness limit (unparseable -> stale)."""
    age = data_age_seconds(snap, now=now)
    if age is None:
        return True
    return age > staleness_limit_s
