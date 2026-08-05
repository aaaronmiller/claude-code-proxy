"""Build, validate, publish, and recover default-off routing snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

from src.services.models.callable_catalog import CallableRecord

SUPPORTED_SCHEMA_MAJOR = 1
SCHEMA_VERSION = "1.0.0"
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "003-model-scan-integration"
    / "contracts"
    / "deterministic_routing_snapshot.schema.json"
)


class SnapshotRejected(ValueError):
    """Raised before publication when a snapshot fails a required gate."""


@dataclass(frozen=True)
class RankedCallable:
    rank: int
    record: CallableRecord
    capability_ref: str
    quota_ref: str
    eligibility_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ExcludedCandidate:
    candidate_ref: str
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SnapshotLoadResult:
    snapshot: dict[str, Any] | None
    source: str | None
    failures: tuple[str, ...]


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


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _canonical_payload(snapshot: dict[str, Any]) -> bytes:
    payload = dict(snapshot)
    payload.pop("snapshot_id", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _snapshot_id(snapshot: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_payload(snapshot)).hexdigest()


def build_snapshot(
    *,
    generated_at: str,
    expires_at: str,
    catalog_version: str,
    policy_version: str,
    request_class: str,
    candidates: Iterable[RankedCallable],
    excluded_candidates: Iterable[ExcludedCandidate] = (),
    evidence_refs: Iterable[str],
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    """Build a self-contained snapshot without activating or persisting routing."""
    snapshot: dict[str, Any] = {
        "schema_version": schema_version,
        "snapshot_id": "",
        "generated_at": generated_at,
        "expires_at": expires_at,
        "catalog_version": catalog_version,
        "policy_version": policy_version,
        "request_class": request_class,
        "candidates": [
            {
                "rank": candidate.rank,
                "callable_id": candidate.record.callable_id,
                "provider_id": candidate.record.provider_id,
                "api_model_id": candidate.record.api_model_id,
                "base_url": candidate.record.base_url,
                "credential_ref": candidate.record.credential_ref,
                "capability_ref": candidate.capability_ref,
                "quota_ref": candidate.quota_ref,
                "eligibility_reasons": list(candidate.eligibility_reasons),
                "evidence_refs": list(candidate.evidence_refs),
            }
            for candidate in candidates
        ],
        "excluded_candidates": [
            {
                "candidate_ref": excluded.candidate_ref,
                "reasons": list(excluded.reasons),
                "evidence_refs": list(excluded.evidence_refs),
            }
            for excluded in excluded_candidates
        ],
        "evidence_refs": list(evidence_refs),
    }
    snapshot["snapshot_id"] = _snapshot_id(snapshot)
    validate(snapshot)
    return snapshot


def validate(snapshot: Any, *, require_fresh_at: datetime | None = None) -> None:
    """Apply schema, compatibility, determinism, and optional freshness gates."""
    if not isinstance(snapshot, dict):
        raise SnapshotRejected("snapshot must be an object")
    errors = sorted(_validator().iter_errors(snapshot), key=lambda error: list(error.path))
    if errors:
        raise SnapshotRejected(errors[0].message)
    if _major(snapshot["schema_version"]) != SUPPORTED_SCHEMA_MAJOR:
        raise SnapshotRejected(f"unsupported schema version {snapshot['schema_version']}")
    if snapshot["snapshot_id"] != _snapshot_id(snapshot):
        raise SnapshotRejected("snapshot_id does not match canonical content")

    generated_at = _parse_utc(snapshot["generated_at"])
    expires_at = _parse_utc(snapshot["expires_at"])
    if expires_at <= generated_at:
        raise SnapshotRejected("expires_at must be later than generated_at")
    if require_fresh_at is not None and expires_at <= require_fresh_at.astimezone(timezone.utc):
        raise SnapshotRejected("snapshot is stale")

    ranks = [candidate["rank"] for candidate in snapshot["candidates"]]
    if ranks != list(range(1, len(ranks) + 1)):
        raise SnapshotRejected("candidate ranks must be ordered and contiguous")
    callable_ids = [candidate["callable_id"] for candidate in snapshot["candidates"]]
    if len(callable_ids) != len(set(callable_ids)):
        raise SnapshotRejected("candidate callable_id values must be unique")


def _encoded(snapshot: dict[str, Any]) -> bytes:
    return (json.dumps(snapshot, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode(
        "utf-8"
    )


def _atomic_replace(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_name = handle.name
            os.chmod(temp_name, 0o600)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def last_known_good_path(path: str | Path) -> Path:
    target = Path(path).expanduser()
    return target.with_name(f"{target.stem}.last-known-good{target.suffix}")


def publish(
    snapshot: dict[str, Any],
    path: str | Path,
    *,
    now: datetime | None = None,
) -> Path:
    """Validate first, then atomically publish current and recovery copies."""
    publication_time = now or datetime.now(timezone.utc)
    validate(snapshot, require_fresh_at=publication_time)
    target = Path(path).expanduser()
    content = _encoded(snapshot)

    # Recovery is installed first. If current replacement fails, the prior
    # current remains and the new validated recovery copy is still usable.
    _atomic_replace(last_known_good_path(target), content)
    _atomic_replace(target, content)
    return target


def _load_candidate(
    path: Path,
    *,
    now: datetime,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except (OSError, json.JSONDecodeError) as error:
        return None, f"unreadable:{type(error).__name__}"
    try:
        validate(snapshot, require_fresh_at=now)
    except SnapshotRejected as error:
        return None, str(error)
    return snapshot, None


def load_best(
    path: str | Path,
    *,
    now: datetime | None = None,
) -> SnapshotLoadResult:
    """Load current, then its independent last-known-good recovery copy."""
    target = Path(path).expanduser()
    reference_time = now or datetime.now(timezone.utc)
    failures: list[str] = []
    for label, candidate_path in (
        ("current", target),
        ("last-known-good", last_known_good_path(target)),
    ):
        snapshot, failure = _load_candidate(candidate_path, now=reference_time)
        if snapshot is not None:
            return SnapshotLoadResult(snapshot, label, tuple(failures))
        failures.append(f"{label}:{failure}")
    return SnapshotLoadResult(None, None, tuple(failures))
