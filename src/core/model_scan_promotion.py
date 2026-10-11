"""Gated promotion of validated canary evidence and in-memory rollback.

CG-T043. Promotion applies validated canary bindings to the active in-memory
overlay only after a complete promotion vector (protocol, streaming, tools,
response identity, latency, quota/cost, fallback, rollback) plus a passing
required offline regression gate is presented. Promotion never writes
persistent configuration and sends no provider traffic; rollback restores the
captured previous binding in memory. Every rejection is explicit and leaves
the active binding untouched.
"""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from src.core import profiles
from src.core.model_scan_binder import BindResult, ResolvedBinding
from src.core.model_scan_runtime import _LOCK, get_active_binding

SCHEMA_VERSION = "1.0.0"

#: The complete promotion vector. Every dimension must carry explicit evidence.
DIMENSIONS = (
    "protocol",
    "streaming",
    "tools",
    "response_identity",
    "latency",
    "quota_cost",
    "fallback",
    "rollback",
)

_EVIDENCE_STATUSES = ("pass", "fail")


class PromotionBlocked(ValueError):
    """Raised when promotion evidence is incomplete, failing, or stale."""


@dataclass(frozen=True)
class DimensionEvidence:
    """One promotion dimension with its measured status and evidence pointer."""

    dimension: str
    status: str
    evidence_ref: str
    detail: str = ""


@dataclass(frozen=True)
class RegressionEvidence:
    """The required offline regression gate result that authorizes promotion."""

    gate: str
    passed: bool
    ran_at: str
    result_ref: str


@dataclass(frozen=True)
class PromotionVector:
    """Content-addressed, complete evidence vector for one promotion decision."""

    canary_profile_id: str
    comparison_ids: tuple[str, ...]
    dimensions: Mapping[str, DimensionEvidence]
    regression: RegressionEvidence
    vector_id: str = ""
    schema_version: str = SCHEMA_VERSION


def _canonical_payload(record: Mapping[str, Any]) -> bytes:
    payload = {k: v for k, v in record.items() if k != "vector_id"}
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _validated_vector(vector: PromotionVector) -> PromotionVector:
    if vector.schema_version != SCHEMA_VERSION:
        raise PromotionBlocked(
            f"unsupported promotion vector schema {vector.schema_version!r}"
        )
    if not vector.canary_profile_id or not vector.canary_profile_id.startswith("canary-"):
        raise PromotionBlocked("promotion requires an exact canary profile id")
    if not vector.comparison_ids or len(vector.comparison_ids) != len(
        set(vector.comparison_ids)
    ):
        raise PromotionBlocked("promotion requires non-empty unique comparison ids")

    presented = tuple(vector.dimensions.keys())
    if presented != DIMENSIONS:
        raise PromotionBlocked(
            f"promotion vector dimensions must be exactly {list(DIMENSIONS)}"
        )
    for dimension in DIMENSIONS:
        evidence = vector.dimensions[dimension]
        if not isinstance(evidence, DimensionEvidence) or evidence.dimension != dimension:
            raise PromotionBlocked(f"dimension {dimension!r} evidence is mismatched")
        if evidence.status not in _EVIDENCE_STATUSES:
            raise PromotionBlocked(
                f"dimension {dimension!r} has no decided evidence "
                f"(status={evidence.status!r}); unknown evidence blocks promotion"
            )
        if not evidence.evidence_ref:
            raise PromotionBlocked(f"dimension {dimension!r} lacks an evidence_ref")
        if evidence.status == "fail":
            raise PromotionBlocked(
                f"dimension {dimension!r} evidence failed: {evidence.detail or 'no detail'}"
            )

    regression = vector.regression
    if not isinstance(regression, RegressionEvidence) or not regression.gate:
        raise PromotionBlocked("promotion requires regression evidence")
    if not regression.passed:
        raise PromotionBlocked(
            "the required regression gate failed; promotion is blocked"
        )
    if not regression.result_ref:
        raise PromotionBlocked("regression evidence lacks a result_ref")
    try:
        datetime.fromisoformat(regression.ran_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise PromotionBlocked("regression ran_at is not a valid timestamp") from exc

    payload = {
        "schema_version": vector.schema_version,
        "canary_profile_id": vector.canary_profile_id,
        "comparison_ids": list(vector.comparison_ids),
        "dimensions": {
            d: asdict(vector.dimensions[d]) for d in DIMENSIONS
        },
        "regression": asdict(vector.regression),
    }
    vector_id = "sha256:" + hashlib.sha256(_canonical_payload(payload)).hexdigest()
    return replace_vector(vector, vector_id=vector_id)


def replace_vector(vector: PromotionVector, **changes: Any) -> PromotionVector:
    fields = {f: getattr(vector, f) for f in vector.__dataclass_fields__ if f != "vector_id"}
    fields.pop("vector_id", None)
    fields.update(changes)
    return PromotionVector(**fields)


def build_promotion_vector(
    *,
    canary: Mapping[str, Any],
    dimension_evidence: Mapping[str, DimensionEvidence],
    regression: RegressionEvidence,
) -> PromotionVector:
    """Build a validated vector from a canary result and measured evidence."""
    if not isinstance(canary, Mapping) or canary.get("mode") != "canary":
        raise PromotionBlocked("promotion evidence requires a canary record")
    if canary.get("traffic_sent") is not False:
        raise PromotionBlocked("canary evidence must be traffic-free")
    profile_id = str(canary.get("profile_id") or "")
    comparison_ids = tuple(str(c) for c in canary.get("source_comparison_ids") or ())
    vector = PromotionVector(
        canary_profile_id=profile_id,
        comparison_ids=comparison_ids,
        dimensions={str(k): v for k, v in dimension_evidence.items()},
        regression=regression,
    )
    return _validated_vector(vector)


def _resolve_live_canary(profile_id: str) -> dict[str, Any]:
    profiles.sweep_ephemeral_profiles()
    entry = profiles.list_ephemeral_profiles().get(profile_id)
    if not entry or entry.get("kind") != "canary":
        raise PromotionBlocked(f"canary {profile_id!r} is not a live canary profile")
    if float(entry.get("expires_at") or 0) <= datetime.now(timezone.utc).timestamp():
        raise PromotionBlocked(f"canary {profile_id!r} has expired")
    return entry


def _binding_from_canary(raw: Mapping[str, Any]) -> ResolvedBinding:
    return ResolvedBinding(
        api_model=str(raw["api_model"]),
        base_url=str(raw.get("base_url") or ""),
        cascade=tuple(raw.get("cascade") or ()),
        source="canary",
        provider=str(raw.get("provider") or ""),
        role=str(raw.get("role") or ""),
    )


def _serialize_binding(binding: BindResult | None) -> dict[str, Any] | None:
    if binding is None:
        return None
    return {
        "global_tiers": {
            aid: asdict(rb) for aid, rb in binding.global_tiers.items()
        },
        "overlay": {
            profile: {aid: asdict(rb) for aid, rb in inner.items()}
            for profile, inner in binding.overlay.items()
        },
        "scan_id": binding.scan_id,
        "schema_version": binding.schema_version,
        "provenance": dict(binding.provenance),
    }


def _restore_binding(serialized: dict[str, Any] | None) -> BindResult | None:
    if serialized is None:
        return None
    return BindResult(
        global_tiers={
            aid: ResolvedBinding(**rb) for aid, rb in serialized["global_tiers"].items()
        },
        overlay={
            profile: {aid: ResolvedBinding(**rb) for aid, rb in inner.items()}
            for profile, inner in serialized["overlay"].items()
        },
        scan_id=serialized["scan_id"],
        schema_version=serialized["schema_version"],
        provenance=dict(serialized["provenance"]),
    )


@dataclass
class _PromotionState:
    records: dict[str, dict[str, Any]] = field(default_factory=dict)


_STATE = _PromotionState()


def promote(vector: PromotionVector) -> dict[str, Any]:
    """Apply validated canary bindings to the active in-memory overlay."""
    vector = _validated_vector(vector)
    entry = _resolve_live_canary(vector.canary_profile_id)
    stored_ids = tuple(entry.get("source_comparison_ids") or ())
    if stored_ids != vector.comparison_ids:
        raise PromotionBlocked(
            "canary source comparisons changed since the vector was built"
        )
    bindings = entry.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise PromotionBlocked("live canary carries no exact bindings")

    global_tiers = {
        assignment_id: _binding_from_canary(raw)
        for assignment_id, raw in sorted(bindings.items())
    }

    import src.core.model_scan_runtime as runtime

    with _LOCK:
        previous = copy.deepcopy(runtime._ACTIVE_BINDING)
        promoted = BindResult(
            global_tiers=global_tiers,
            overlay=copy.deepcopy(previous.overlay) if previous else {},
            scan_id=previous.scan_id if previous else 0,
            schema_version=f"canary:{vector.vector_id[:23]}",
            provenance={
                **(dict(previous.provenance) if previous else {}),
                **{f"canary.{aid}": "canary" for aid in global_tiers},
            },
        )
        import src.core.model_scan_runtime as runtime

        runtime._ACTIVE_BINDING = promoted
        record = {
            "record_kind": "promotion",
            "schema_version": SCHEMA_VERSION,
            "vector_id": vector.vector_id,
            "canary_profile_id": vector.canary_profile_id,
            "comparison_ids": list(vector.comparison_ids),
            "applied_assignments": sorted(global_tiers),
            "previous_binding": _serialize_binding(previous),
            "persistent_writes": [],
            "traffic_sent": False,
            "rolled_back": False,
            "promoted_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
        }
        _STATE.records[vector.vector_id] = record
    return dict(record)

def rollback(record: Mapping[str, Any]) -> dict[str, Any]:
    """Restore the previous active binding captured by :func:`promote`."""
    if not isinstance(record, Mapping) or record.get("record_kind") != "promotion":
        raise PromotionBlocked("rollback requires a promotion record")
    stored = _STATE.records.get(str(record.get("vector_id")))
    if stored is not None:
        record = stored
    if record.get("rolled_back"):
        raise PromotionBlocked("this promotion was already rolled back")
    previous = record.get("previous_binding")
    restored = _restore_binding(copy.deepcopy(previous))
    with _LOCK:
        import src.core.model_scan_runtime as runtime

        runtime._ACTIVE_BINDING = restored
        stored = _STATE.records.get(str(record.get("vector_id")))
        if stored is not None:
            stored["rolled_back"] = True
    return {
        "record_kind": "rollback",
        "schema_version": SCHEMA_VERSION,
        "vector_id": record.get("vector_id"),
        "canary_profile_id": record.get("canary_profile_id"),
        "restored": True,
        "persistent_writes": [],
        "traffic_sent": False,
        "active_binding_restored": _serialize_binding(get_active_binding()),
    }
