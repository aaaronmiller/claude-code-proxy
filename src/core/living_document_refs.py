"""Structured runtime records reference the Living Documents project.

CG-T060. Session, route, quota, fallback, failure, canary, and promotion
records carry a strict reference to the owning Living Document project. The
project id is resolved from the dossier's own ``project.md`` frontmatter so a
record can never point at the wrong project, and records are forbidden from
duplicating the task board or any content-store payload: they carry ids,
relative evidence paths, and derived counts only.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0.0"

RECORD_KINDS = (
    "session",
    "route",
    "quota",
    "fallback",
    "failure",
    "canary",
    "promotion",
)

_TASK_REF = re.compile(r"^[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+$")

#: Fields that would duplicate Living Document content inside a runtime record.
_FORBIDDEN_FIELDS = (
    "board",
    "tasks",
    "content",
    "body",
    "markdown",
    "html",
    "transcript",
    "prompt",
    "messages",
)


class LivingDocRefRejected(ValueError):
    """Raised when a record reference is wrong, unsafe, or content-bearing."""


@dataclass(frozen=True)
class LivingDocRef:
    """The strict, reference-only link between a runtime record and a project."""

    record_kind: str
    project_id: str
    project_root: str
    record_id: str
    created_at: str
    task_ref: str = ""
    evidence_ref: str = ""
    schema_version: str = SCHEMA_VERSION


def resolve_project_id(project_root: str | Path) -> str:
    """Read the canonical project id from the dossier's project.md frontmatter."""
    frontmatter = (Path(project_root) / "project.md").read_text(encoding="utf-8")
    match = re.search(r"^id:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    if not match:
        raise LivingDocRefRejected(
            f"{Path(project_root) / 'project.md'} frontmatter has no id field"
        )
    return match.group(1)


def _safe_relative(project_root: Path, evidence_ref: str) -> Path:
    candidate = (project_root / evidence_ref).resolve()
    root = project_root.resolve()
    if root not in candidate.parents and candidate != root:
        raise LivingDocRefRejected(
            f"evidence_ref escapes the project root: {evidence_ref!r}"
        )
    return candidate


def link_record(
    record_kind: str,
    project_root: str | Path,
    *,
    task_ref: str = "",
    evidence_ref: str = "",
) -> LivingDocRef:
    """Build a validated reference record for one runtime fact."""
    if record_kind not in RECORD_KINDS:
        raise LivingDocRefRejected(
            f"record_kind {record_kind!r} must be one of {list(RECORD_KINDS)}"
        )
    root = Path(project_root)
    if not (root / "project.md").is_file():
        raise LivingDocRefRejected(f"no Living Document dossier at {root}")
    project_id = resolve_project_id(root)
    if task_ref and not _TASK_REF.match(task_ref):
        raise LivingDocRefRejected(f"task_ref {task_ref!r} is not a task id")
    if evidence_ref:
        target = _safe_relative(root, evidence_ref)
        if not target.is_file():
            raise LivingDocRefRejected(
                f"evidence_ref {evidence_ref!r} does not exist in the dossier"
            )
    return LivingDocRef(
        record_kind=record_kind,
        project_id=project_id,
        project_root=str(root),
        record_id=f"{record_kind}-{uuid.uuid4().hex[:12]}",
        created_at=datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        task_ref=task_ref,
        evidence_ref=evidence_ref,
    )


def validate_ref(record: Mapping[str, Any], *, project_root: str | Path) -> None:
    """Re-validate any record against its claimed project root."""
    if record.get("schema_version") != SCHEMA_VERSION:
        raise LivingDocRefRejected(
            f"unsupported record schema {record.get('schema_version')!r}"
        )
    if record.get("record_kind") not in RECORD_KINDS:
        raise LivingDocRefRejected(
            f"record_kind {record.get('record_kind')!r} is not a linkable kind"
        )
    if record.get("project_id") != resolve_project_id(project_root):
        raise LivingDocRefRejected(
            f"record claims project {record.get('project_id')!r} but the dossier "
            f"at {project_root} disagrees"
        )
    blob = {k: v for k, v in record.items()}
    for field_name in _FORBIDDEN_FIELDS:
        if field_name in blob:
            raise LivingDocRefRejected(
                f"record duplicates Living Document content via field {field_name!r}"
            )


def derived_projection(refs: Iterable[LivingDocRef]) -> dict[str, Any]:
    """Project record references into the only form Living Documents store."""
    refs = list(refs)
    counts: dict[str, int] = {}
    for ref in refs:
        counts[ref.record_kind] = counts.get(ref.record_kind, 0) + 1
    task_refs = sorted({ref.task_ref for ref in refs if ref.task_ref})
    project_ids = sorted({ref.project_id for ref in refs})
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_kind": "record_references",
        "project_ids": project_ids,
        "record_count": len(refs),
        "records_by_kind": counts,
        "task_refs": task_refs,
    }
