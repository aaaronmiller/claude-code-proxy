"""CG-T085 — one trace joins events across two harness adapters."""

from __future__ import annotations

import pytest

from src.services.orchestration.event_correlation import (
    EventRejected,
    build_trace,
    living_document_projection,
    normalize_codex_event,
    normalize_omp_event,
    operations_projection,
)

BASE = dict(
    trace_id="trace-7",
    task_id="task-b09",
    project_id="claude-code-proxy",
    session_id="sess-codex-1",
)


def _codex_stream() -> list[dict]:
    return [
        {**BASE, "type": "session.created", "sequence": 0},
        {
            **BASE,
            "type": "item.completed",
            "sequence": 1,
            "item": {"type": "reasoning", "id": "r1"},
        },
        {
            **BASE,
            "type": "item.completed",
            "sequence": 2,
            "item": {"type": "tool_call", "id": "t1"},
        },
        {**BASE, "type": "token_count", "sequence": 3, "usage": {"total": 100}},
        {**BASE, "type": "turn.completed", "sequence": 4},
    ]


def _omp_stream() -> list[dict]:
    base = {**BASE, "session_id": "sess-omp-1"}
    return [
        {**base, "type": "handoff", "sequence": 5},
        {**base, "type": "test_report", "sequence": 6},
        {**base, "type": "gate", "sequence": 7},
        {**base, "type": "quota", "sequence": 8},
        {**base, "type": "outcome", "sequence": 9},
    ]


def test_one_trace_joins_both_adapters_across_the_full_vocabulary():
    events = [normalize_codex_event(raw) for raw in _codex_stream()]
    events += [normalize_omp_event(raw) for raw in _omp_stream()]
    join = build_trace(events)

    assert join.harnesses == ["codex", "omp"]
    assert join.session_ids == {"codex": "sess-codex-1", "omp": "sess-omp-1"}
    kinds = join.event_counts
    for expected in (
        "launch",
        "model_generation",
        "tool",
        "test",
        "handoff",
        "gate",
        "quota",
        "outcome",
    ):
        assert expected in kinds, expected
    assert [e.sequence for e in join.events] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert join.outcome == "outcome"
    assert len(join.quota_events) == 2  # codex token_count + omp quota
    assert len(join.handoff_events) == 1


def test_identity_is_preserved_across_the_join():
    events = [normalize_codex_event(raw) for raw in _codex_stream()]
    events += [normalize_omp_event(raw) for raw in _omp_stream()]
    join = build_trace(events)
    assert {e.task_id for e in join.events} == {"task-b09"}
    assert {e.project_id for e in join.events} == {"claude-code-proxy"}
    assert {e.trace_id for e in join.events} == {"trace-7"}


def test_protected_prompt_capture_is_rejected():
    raw = {**_codex_stream()[0], "prompt": "secret user prompt text"}
    with pytest.raises(EventRejected, match="protected"):
        normalize_codex_event(raw)
    raw = {**_omp_stream()[0], "payload_ref": "x", "note": "sk-abcdefghijklmnop1234"}
    with pytest.raises(EventRejected, match="protected"):
        normalize_omp_event(raw)


def test_unknown_adapter_kinds_fail_closed():
    with pytest.raises(EventRejected, match="unknown codex"):
        normalize_codex_event({**BASE, "type": "vibes", "sequence": 0})
    with pytest.raises(EventRejected, match="unknown omp"):
        normalize_omp_event({**BASE, "type": "vibes", "sequence": 0})


def test_raw_events_stay_in_operations_store_only():
    events = [normalize_codex_event(raw) for raw in _codex_stream()]
    events += [normalize_omp_event(raw) for raw in _omp_stream()]
    join = build_trace(events)

    ops = operations_projection(join)
    assert len(ops["events"]) == 10  # raw events live here
    assert ops["store_kind"] == "operations_trace"

    derived = living_document_projection(join)
    # the Living Document receives only derived counts and references
    assert "events" not in derived
    assert derived["projection_kind"] == "trace_summary"
    assert derived["event_counts"]["tool"] == 1
    assert derived["handoff_count"] == 1
    assert all(ref.startswith("ops-store:") for ref in derived["payload_refs"])


def test_multi_trace_or_multi_identity_joins_are_rejected():
    events = [normalize_codex_event(raw) for raw in _codex_stream()]
    with pytest.raises(EventRejected, match="one task and one project"):
        build_trace(
            events
            + [normalize_codex_event({**_codex_stream()[0], "task_id": "task-other"})]
        )
    with pytest.raises(EventRejected, match="empty event set"):
        build_trace([])
