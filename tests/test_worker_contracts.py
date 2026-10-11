"""CG-T080 — strict worker contract records, positive and negative fixtures."""

from __future__ import annotations

import pytest

from src.services.workers.contracts import (
    SCHEMA_VERSION,
    Approval,
    ContractRejected,
    EffectiveBinding,
    Handoff,
    LaunchRequest,
    ModelRole,
    ResourceEnvelope,
    TaskIdentity,
    TaskPacket,
    WorkerEvent,
    WorkerResult,
)

IDENTITY = TaskIdentity(
    task_id="task-b09",
    project_id="claude-code-proxy",
    session_id="sess-1",
    trace_id="trace-1",
    worktree_path="/home/cheta/code/claude-code-proxy/.worktrees/b09",
)

APPROVAL = Approval("dec-1", "user", "CG-T043", "2026-08-29T00:00:00Z")
PACKET = TaskPacket("packet-1", "CG-T043", "taxonomy:tool_implementation", "pipeline:review-fix-verify", "pytest tests/test_model_scan_promotion.py -q passes")
BINDING = EffectiveBinding("openrouter", "z-ai/glm-5.3-flash", "https://openrouter.ai/api/v1", "header", 1.0, "snapshot:1487")
ROLE = ModelRole("implement", "codex", "high", BINDING)
ENVELOPE = ResourceEnvelope(1800, 2, ("read", "edit", "pytest"), "worktree")


def _launch(**overrides) -> LaunchRequest:
    values = dict(
        record_kind="launch_request",
        launch_id="launch-1",
        identity=IDENTITY,
        approval=APPROVAL,
        launch_requested=True,
        task_packet=PACKET,
        model_role=ROLE,
        escalation="bounded_repair",
        device_role="workstation",
        host_capability_ref="capability-inventory:codex",
        resource_envelope=ENVELOPE,
        created_at="2026-08-29T00:00:00Z",
    )
    values.update(overrides)
    return LaunchRequest(**values)


def test_complete_launch_request_is_valid_and_secret_free():
    launch = _launch()
    launch.validate()
    payload = launch.to_dict()
    import json as _json
    import re as _re

    blob = _json.dumps(payload)
    assert not _re.search(r"\bsk-[A-Za-z0-9]{16,}\b", blob)
    assert "api_key" not in blob.lower()
    # the contract records every required dimension
    assert launch.task_packet.acceptance_gate
    assert launch.model_role.effective_binding.api_model
    assert launch.escalation in ("none", "bounded_repair", "harness_switch")
    assert launch.device_role == "workstation"
    assert launch.host_capability_ref.startswith("capability-inventory:")
    assert launch.resource_envelope.network_access == "worktree"


def test_approval_without_explicit_launch_is_rejected():
    with pytest.raises(ContractRejected, match="launch_requested"):
        _launch(launch_requested=False).validate()


def test_identity_must_be_complete_and_stable():
    for field_name in ("task_id", "project_id", "session_id", "trace_id"):
        broken = TaskIdentity(
            **{
                **{
                    "task_id": "t",
                    "project_id": "p",
                    "session_id": "s",
                    "trace_id": "tr",
                    "worktree_path": "/tmp/w",
                },
                field_name: "",
            }
        )
        with pytest.raises(ContractRejected, match=field_name):
            broken.validate()
    with pytest.raises(ContractRejected, match="worktree"):
        TaskIdentity("t", "p", "s", "tr", "relative/path").validate()


def test_launch_requires_exact_provider_and_api_model():
    with pytest.raises(ContractRejected, match="provider"):
        ModelRole(
            "implement", "codex", "high",
            EffectiveBinding("", "", "", "header", 1.0, "snapshot:1"),
        ).validate()


def test_runtime_effort_override_must_be_recorded():
    overridden = ModelRole("implement", "codex", "max", BINDING, "runtime")
    overridden.validate()
    with pytest.raises(ContractRejected, match="effort_override_source"):
        ModelRole("implement", "codex", "max", BINDING, "undefined").validate()


def test_events_must_reference_payloads_not_content():
    event = WorkerEvent(
        "worker_event", "tool", 1, IDENTITY, "codex",
        "ops-store:event-0001", "2026-08-29T00:00:01Z",
    )
    event.validate()
    with pytest.raises(ContractRejected, match="not a valid reference"):
        WorkerEvent(
            "worker_event", "tool", 2, IDENTITY, "codex", "",
            "2026-08-29T00:00:01Z",
        ).validate()
    with pytest.raises(ContractRejected, match="content"):
        WorkerEvent(
            "worker_event", "tool", 3, IDENTITY, "codex",
            "ops-store:event-0001", "2026-08-29T00:00:01Z",
        )
        # content capture is rejected at the field level:
        bad = {"prompt": "do things", "payload_ref": "x"}
        from src.services.workers.contracts import assert_no_secrets_or_content
        assert_no_secrets_or_content(bad)


def test_event_kind_is_closed():
    with pytest.raises(ContractRejected, match="event_kind"):
        WorkerEvent(
            "worker_event", "vibes", 0, IDENTITY, "codex", "ref:x", "2026-08-29T00:00:00Z"
        ).validate()


def test_result_requires_gate_and_provenance():
    result = WorkerResult(
        "worker_result", "res-1", "launch-1", IDENTITY, "accepted",
        "ops-store:out-1", "gate:pytest-tests", ("pipeline:review-fix-verify",),
        "2026-08-29T00:05:00Z",
    )
    result.validate()
    with pytest.raises(ContractRejected, match="provenance"):
        WorkerResult(
            "worker_result", "res-2", "launch-1", IDENTITY, "accepted",
            "ops-store:out-1", "gate:pytest", (), "2026-08-29T00:05:00Z",
        ).validate()
    with pytest.raises(ContractRejected, match="status"):
        WorkerResult(
            "worker_result", "res-3", "launch-1", IDENTITY, "vibes",
            "ops-store:out-1", "gate:pytest", ("p",), "2026-08-29T00:05:00Z",
        ).validate()


def test_handoff_preserves_identity_and_crosses_harnesses():
    handoff = Handoff(
        "handoff", "handoff-1", "codex", "omp", IDENTITY,
        ("artifact:diff-1",), "escalation", APPROVAL, "2026-08-29T00:06:00Z",
    )
    handoff.validate()
    with pytest.raises(ContractRejected, match="cross harnesses"):
        Handoff(
            "handoff", "handoff-2", "codex", "codex", IDENTITY,
            ("artifact:diff-1",), "escalation", APPROVAL, "2026-08-29T00:06:00Z",
        ).validate()
    with pytest.raises(ContractRejected, match="artifact"):
        Handoff(
            "handoff", "handoff-3", "codex", "omp", IDENTITY,
            (), "escalation", APPROVAL, "2026-08-29T00:06:00Z",
        ).validate()


def test_cancellation_carries_identity_and_reason():
    from src.services.workers.contracts import Cancellation

    cancel = Cancellation(
        "cancellation", "launch-1", IDENTITY, "user stop", "user", False,
        "2026-08-29T00:07:00Z",
    )
    cancel.validate()
    with pytest.raises(ContractRejected, match="reason"):
        Cancellation(
            "cancellation", "launch-1", IDENTITY, "", "user", False,
            "2026-08-29T00:07:00Z",
        ).validate()


def test_credentials_are_rejected_everywhere():
    with pytest.raises(ContractRejected, match="credential"):
        ModelRole(
            "implement", "codex", "high",
            EffectiveBinding("openrouter", "m", "https://user:sk-secret@api/v1",
                             "header", 1.0, "snapshot:1"),
        ).validate()
