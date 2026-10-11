"""The harness-neutral worker contract (CG-T080).

Strict, versioned records for launch, cancellation, effective binding, event,
result, and handoff. Every record preserves task/project/session/trace/worktree
identity, distinguishes an approval decision from an explicit launch, records
the task packet, model role, escalation policy, device role, host capability
reference, and resource envelope, and excludes secrets: payloads travel as
references, never as content.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "1.0.0"

#: Every contract record kind with its frozen schema version.
RECORD_VERSIONS = {
    "launch_request": SCHEMA_VERSION,
    "cancellation": SCHEMA_VERSION,
    "effective_binding": SCHEMA_VERSION,
    "worker_event": SCHEMA_VERSION,
    "worker_result": SCHEMA_VERSION,
    "handoff": SCHEMA_VERSION,
}

EVENT_KINDS = (
    "launch",
    "model_generation",
    "tool",
    "test",
    "handoff",
    "gate",
    "quota",
    "cancellation",
    "error",
    "outcome",
)

ESCALATION_POLICIES = ("none", "bounded_repair", "harness_switch")
STATUSES = ("accepted", "rejected", "failed", "stopped")
NETWORK_ACCESS = ("none", "worktree", "full")

_SECRET_MARKERS = ("api_key", "apikey", "password", "bearer ", "credential")
_SECRET_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")
_REF_SHAPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/#-]{0,255}$")
_TASK_REF_SHAPE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+$")
_FORBIDDEN_CONTENT_FIELDS = (
    "prompt",
    "messages",
    "transcript",
    "content",
    "body",
    "markdown",
)

class ContractRejected(ValueError):
    """Raised when a record violates the worker contract."""


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _check_ref(value: str, what: str) -> str:
    if not value or not _REF_SHAPE.match(value):
        raise ContractRejected(f"{what} {value!r} is not a valid reference")
    return value


def assert_no_secrets_or_content(payload: Mapping[str, Any]) -> None:
    """Reject credential values and prompt/content capture by field or shape."""
    blob = json.dumps(payload, default=str)
    lowered = blob.lower()
    for marker in _SECRET_MARKERS:
        if marker in lowered:
            raise ContractRejected(
                f"record may carry a credential (matched {marker!r})"
            )
    if _SECRET_KEY_PATTERN.search(blob):
        raise ContractRejected("record may carry an sk- credential key")
    for field_name in _FORBIDDEN_CONTENT_FIELDS:
        if field_name in payload:
            raise ContractRejected(
                f"record carries content via field {field_name!r}; pass a reference"
            )


@dataclass(frozen=True)
class TaskIdentity:
    """Immutable identity carried by every worker record."""

    task_id: str
    project_id: str
    session_id: str
    trace_id: str
    worktree_path: str

    def validate(self) -> None:
        for name in ("task_id", "project_id", "session_id", "trace_id"):
            value = str(getattr(self, name))
            if not value or not _REF_SHAPE.match(value):
                raise ContractRejected(f"identity.{name} {value!r} is not a stable id")
        if not self.worktree_path or not self.worktree_path.startswith("/"):
            raise ContractRejected("identity.worktree_path must be absolute")


@dataclass(frozen=True)
class Approval:
    """A user/policy decision. An approval alone never launches a worker."""

    decision_id: str
    approved_by: str
    scope: str
    approved_at: str

    def validate(self) -> None:
        if not self.decision_id or not self.approved_by:
            raise ContractRejected("approval requires decision_id and approved_by")
        _check_ref(self.scope, "approval.scope")


@dataclass(frozen=True)
class TaskPacket:
    """Reference-only description of the work plus its acceptance gate."""

    packet_id: str
    task_ref: str
    classification_ref: str
    skill_pipeline: str
    acceptance_gate: str

    def validate(self) -> None:
        if not self.packet_id:
            raise ContractRejected("task packet requires packet_id")
        if not _TASK_REF_SHAPE.match(self.task_ref):
            raise ContractRejected(f"task_ref {self.task_ref!r} is not a task id")
        _check_ref(self.classification_ref, "task_packet.classification_ref")
        _check_ref(self.skill_pipeline, "task_packet.skill_pipeline")
        if not self.acceptance_gate:
            raise ContractRejected("task packet requires an acceptance gate")


@dataclass(frozen=True)
class ResourceEnvelope:
    max_wall_clock_s: int
    max_retries: int
    allowed_tools: tuple[str, ...]
    network_access: str

    def validate(self) -> None:
        if self.max_wall_clock_s <= 0 or self.max_retries < 0:
            raise ContractRejected("resource envelope bounds are not positive")
        if self.network_access not in NETWORK_ACCESS:
            raise ContractRejected(
                f"network_access {self.network_access!r} not in {NETWORK_ACCESS}"
            )


@dataclass(frozen=True)
class EffectiveBinding:
    """The exact resolved model identity for one launch."""

    provider: str
    api_model: str
    base_url: str
    quota_source: str
    confidence: float
    snapshot_ref: str

    def validate(self) -> None:
        if not self.provider or not self.api_model:
            raise ContractRejected(
                "effective binding requires exact provider and API model identity"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ContractRejected("binding confidence must be within [0, 1]")
        _check_ref(self.snapshot_ref, "binding.snapshot_ref")
        if self.base_url and "@" in self.base_url:
            raise ContractRejected("binding.base_url must not carry credentials")


@dataclass(frozen=True)
class ModelRole:
    role: str
    harness: str
    effort: str
    effective_binding: EffectiveBinding
    effort_override_source: str = ""   # "" (profile default) or "runtime"

    def validate(self) -> None:
        if not self.role or not self.harness:
            raise ContractRejected("model role requires role and harness")
        if self.effort_override_source not in ("", "runtime"):
            raise ContractRejected(
                "effort_override_source must be '' (profile) or 'runtime'"
            )
        self.effective_binding.validate()


@dataclass(frozen=True)
class LaunchRequest:
    """The explicit launch of one approved task on one harness."""

    record_kind: str
    launch_id: str
    identity: TaskIdentity
    approval: Approval
    launch_requested: bool
    task_packet: TaskPacket
    model_role: ModelRole
    escalation: str
    device_role: str
    host_capability_ref: str
    resource_envelope: ResourceEnvelope
    created_at: str = ""

    def validate(self) -> None:
        if self.record_kind != "launch_request":
            raise ContractRejected("record_kind must be launch_request")
        if RECORD_VERSIONS["launch_request"] != SCHEMA_VERSION:
            raise ContractRejected("schema version drift")
        self.identity.validate()
        self.approval.validate()
        self.task_packet.validate()
        self.model_role.validate()
        self.resource_envelope.validate()
        if self.escalation not in ESCALATION_POLICIES:
            raise ContractRejected(
                f"escalation {self.escalation!r} not in {ESCALATION_POLICIES}"
            )
        if not self.device_role:
            raise ContractRejected("launch requires a device role")
        _check_ref(self.host_capability_ref, "host_capability_ref")
        if not self.launch_requested:
            raise ContractRejected(
                "approval alone does not launch; launch_requested must be explicit"
            )
        if not self.created_at:
            raise ContractRejected("launch requires created_at")
        assert_no_secrets_or_content(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Cancellation:
    record_kind: str
    launch_id: str
    identity: TaskIdentity
    reason: str
    requested_by: str
    force: bool
    requested_at: str

    def validate(self) -> None:
        if self.record_kind != "cancellation":
            raise ContractRejected("record_kind must be cancellation")
        self.identity.validate()
        if not self.launch_id or not self.reason or not self.requested_by:
            raise ContractRejected("cancellation requires launch_id, reason, requester")
        assert_no_secrets_or_content(asdict(self))


@dataclass(frozen=True)
class WorkerEvent:
    record_kind: str
    event_kind: str
    sequence: int
    identity: TaskIdentity
    harness: str
    payload_ref: str
    occurred_at: str

    def validate(self) -> None:
        if self.record_kind != "worker_event":
            raise ContractRejected("record_kind must be worker_event")
        if self.event_kind not in EVENT_KINDS:
            raise ContractRejected(
                f"event_kind {self.event_kind!r} not in {EVENT_KINDS}"
            )
        if self.sequence < 0:
            raise ContractRejected("event sequence must be non-negative")
        self.identity.validate()
        if not self.harness:
            raise ContractRejected("event requires the emitting harness")
        _check_ref(self.payload_ref, "event.payload_ref")
        assert_no_secrets_or_content(
            {k: v for k, v in asdict(self).items() if k != "identity"}
        )


@dataclass(frozen=True)
class WorkerResult:
    record_kind: str
    result_id: str
    launch_id: str
    identity: TaskIdentity
    status: str
    output_ref: str
    gate_ref: str
    provenance: tuple[str, ...]
    finished_at: str

    def validate(self) -> None:
        if self.record_kind != "worker_result":
            raise ContractRejected("record_kind must be worker_result")
        if self.status not in STATUSES:
            raise ContractRejected(f"status {self.status!r} not in {STATUSES}")
        if not self.result_id or not self.launch_id:
            raise ContractRejected("result requires result_id and launch_id")
        self.identity.validate()
        _check_ref(self.output_ref, "result.output_ref")
        _check_ref(self.gate_ref, "result.gate_ref")
        if not self.provenance:
            raise ContractRejected("result requires provenance references")
        assert_no_secrets_or_content(asdict(self))


@dataclass(frozen=True)
class Handoff:
    """Cross-harness artifact handoff; escalation approval is distinct from launch."""

    record_kind: str
    handoff_id: str
    from_harness: str
    to_harness: str
    identity: TaskIdentity
    artifact_refs: tuple[str, ...]
    reason: str
    approval: Approval
    created_at: str

    def validate(self) -> None:
        if self.record_kind != "handoff":
            raise ContractRejected("record_kind must be handoff")
        if not self.handoff_id or not self.from_harness or not self.to_harness:
            raise ContractRejected("handoff requires ids and both harnesses")
        if self.from_harness == self.to_harness:
            raise ContractRejected("handoff must cross harnesses")
        if self.reason not in ("escalation", "continuity", "failure"):
            raise ContractRejected(f"handoff reason {self.reason!r} is not allowed")
        self.identity.validate()
        if not self.artifact_refs:
            raise ContractRejected("handoff requires artifact references")
        for artifact in self.artifact_refs:
            _check_ref(artifact, "handoff.artifact_ref")
        self.approval.validate()
        assert_no_secrets_or_content(asdict(self))


def new_launch_id() -> str:
    return f"launch-{uuid_hex()}"


def uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex[:12]
