"""Cross-harness event correlation (CG-T085).

One trace joins launch, model generation, tools, tests, handoff, gate, quota,
and outcome events across two harness adapters. Adapter events are normalized
into the common worker-contract vocabulary; protected prompt content and
secrets are rejected before correlation. Raw events stay in the caller's
global operations store: this module returns a full-fidelity projection for
that store and a strictly derived, reference-only projection for the Living
Document.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from src.services.workers.contracts import (
    EVENT_KINDS,
    ContractRejected,
    assert_no_secrets_or_content,
)

CORRELATION_SCHEMA_VERSION = "1.0.0"

#: Adapter-specific -> common vocabulary mappings (evidence: harness help text
#: probed 2026-08-29; see worker-capability-inventory.md).
_CODEX_KIND_MAP = {
    "session.created": "launch",
    "item.started": "model_generation",
    "item.completed": "tool",       # refined by item type below
    "turn.completed": "outcome",
    "error": "error",
    "token_count": "quota",
}

_OMP_KIND_MAP = {
    "session_start": "launch",
    "assistant_message": "model_generation",
    "tool_call": "tool",
    "tool_result": "tool",
    "test_report": "test",
    "handoff": "handoff",
    "gate": "gate",
    "quota": "quota",
    "outcome": "outcome",
    "cancelled": "cancellation",
    "error": "error",
}

#: Codex item types refine the coarse item.completed mapping.
_CODEX_ITEM_MAP = {
    "tool_call": "tool",
    "command_execution": "tool",
    "reasoning": "model_generation",
    "agent_message": "model_generation",
}


class EventRejected(ContractRejected):
    """Raised when an adapter event carries protected content or is invalid."""


@dataclass(frozen=True)
class HarnessEvent:
    """One normalized event from one harness adapter."""

    harness: str
    event_kind: str
    sequence: int
    trace_id: str
    task_id: str
    project_id: str
    session_id: str
    payload_ref: str
    raw_kind: str
    occurred_at: str = ""
    schema_version: str = CORRELATION_SCHEMA_VERSION


def _protected_fields(payload: Mapping[str, Any]) -> None:
    try:
        assert_no_secrets_or_content(dict(payload))
    except ContractRejected as exc:
        raise EventRejected(f"adapter event carries protected data: {exc}") from exc


def normalize_codex_event(raw: Mapping[str, Any]) -> HarnessEvent:
    """Normalize one codex exec --json JSONL event."""
    _protected_fields(raw)  # fail closed on any capture attempt in the raw event
    raw_kind = str(raw.get("type") or "")
    if raw_kind not in _CODEX_KIND_MAP:
        raise EventRejected(f"unknown codex event type {raw_kind!r}")
    event_kind = _CODEX_KIND_MAP[raw_kind]
    item = raw.get("item") or {}
    if raw_kind == "item.completed" and isinstance(item, Mapping):
        item_type = str(item.get("type") or "")
        event_kind = _CODEX_ITEM_MAP.get(item_type, "tool")
    payload = {
        k: v
        for k, v in raw.items()
        if k in ("id", "item", "usage", "trace_id", "session_id")
    }
    _protected_fields(payload)
    return HarnessEvent(
        harness="codex",
        event_kind=event_kind,
        sequence=int(raw["sequence"]),
        trace_id=str(raw["trace_id"]),
        task_id=str(raw["task_id"]),
        project_id=str(raw["project_id"]),
        session_id=str(raw["session_id"]),
        payload_ref=str(raw.get("payload_ref") or f"ops-store:{raw_kind}:{raw['sequence']}"),
        raw_kind=raw_kind,
        occurred_at=str(raw.get("timestamp") or ""),
    )


def normalize_omp_event(raw: Mapping[str, Any]) -> HarnessEvent:
    """Normalize one omp --mode json event."""
    _protected_fields(raw)  # fail closed on any capture attempt in the raw event
    raw_kind = str(raw.get("type") or "")
    if raw_kind not in _OMP_KIND_MAP:
        raise EventRejected(f"unknown omp event type {raw_kind!r}")
    payload = {k: v for k, v in raw.items() if k not in ("prompt",)}
    _protected_fields(payload)
    return HarnessEvent(
        harness="omp",
        event_kind=_OMP_KIND_MAP[raw_kind],
        sequence=int(raw["sequence"]),
        trace_id=str(raw["trace_id"]),
        task_id=str(raw["task_id"]),
        project_id=str(raw["project_id"]),
        session_id=str(raw["session_id"]),
        payload_ref=str(raw.get("payload_ref") or f"ops-store:{raw_kind}:{raw['sequence']}"),
        raw_kind=raw_kind,
        occurred_at=str(raw.get("timestamp") or ""),
    )


@dataclass
class TraceJoin:
    """The correlated single-trace view across adapters."""

    trace_id: str
    task_id: str
    project_id: str
    harnesses: list[str] = field(default_factory=list)
    events: list[HarnessEvent] = field(default_factory=list)
    event_counts: dict[str, int] = field(default_factory=dict)
    quota_events: list[HarnessEvent] = field(default_factory=list)
    handoff_events: list[HarnessEvent] = field(default_factory=list)
    outcome: str = ""          # raw_kind of the outcome event
    session_ids: dict[str, str] = field(default_factory=dict)


def build_trace(events: list[HarnessEvent]) -> TraceJoin:
    """Join normalized events from both adapters into one ordered trace."""
    if not events:
        raise EventRejected("cannot correlate an empty event set")
    trace_ids = {e.trace_id for e in events}
    if len(trace_ids) != 1:
        raise EventRejected(f"events span {len(trace_ids)} traces; one trace per join")
    task_ids = {e.task_id for e in events}
    project_ids = {e.project_id for e in events}
    if len(task_ids) != 1 or len(project_ids) != 1:
        raise EventRejected(
            "trace events must preserve one task and one project identity"
        )

    ordered = sorted(events, key=lambda e: (e.sequence, e.harness))
    join = TraceJoin(
        trace_id=ordered[0].trace_id,
        task_id=ordered[0].task_id,
        project_id=ordered[0].project_id,
    )
    for event in ordered:
        if event.harness not in join.harnesses:
            join.harnesses.append(event.harness)
        if event.harness not in join.session_ids:
            join.session_ids[event.harness] = event.session_id
        join.events.append(event)
        join.event_counts[event.event_kind] = (
            join.event_counts.get(event.event_kind, 0) + 1
        )
        if event.event_kind == "quota":
            join.quota_events.append(event)
        if event.event_kind == "handoff":
            join.handoff_events.append(event)
        if event.event_kind == "outcome":
            join.outcome = event.raw_kind
    return join


def operations_projection(join: TraceJoin) -> dict[str, Any]:
    """Full-fidelity record for the global operations store (raw refs kept)."""
    return {
        "schema_version": CORRELATION_SCHEMA_VERSION,
        "store_kind": "operations_trace",
        "trace_id": join.trace_id,
        "task_id": join.task_id,
        "project_id": join.project_id,
        "harnesses": join.harnesses,
        "session_ids": join.session_ids,
        "outcome": join.outcome,
        "events": [asdict(e) for e in join.events],
    }


def living_document_projection(join: TraceJoin) -> dict[str, Any]:
    """Derived, reference-only projection; raw events never leave the store."""
    return {
        "schema_version": CORRELATION_SCHEMA_VERSION,
        "projection_kind": "trace_summary",
        "project_id": join.project_id,
        "task_id": join.task_id,
        "trace_id": join.trace_id,
        "harnesses": join.harnesses,
        "event_counts": dict(sorted(join.event_counts.items())),
        "outcome": join.outcome,
        "handoff_count": len(join.handoff_events),
        "quota_event_count": len(join.quota_events),
        "payload_refs": [e.payload_ref for e in join.events],
    }
