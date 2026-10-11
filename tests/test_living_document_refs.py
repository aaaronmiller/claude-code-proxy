"""CG-T060 — runtime records reference the Living Document project, not its content."""

from __future__ import annotations

import pytest

from src.core.living_document_refs import (
    RECORD_KINDS,
    LivingDocRef,
    LivingDocRefRejected,
    derived_projection,
    link_record,
    resolve_project_id,
    validate_ref,
)

DOSSIER = "/home/cheta/LIVING_DOCUMENTS/projects/claude-code-proxy"


def _make_dossier(tmp_path, project_id="claude-code-proxy"):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "project.md").write_text(
        f"---\nid: {project_id}\ntitle: t\ntype: project\n---\n# t\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks.md").write_text(
        "# Tasks\n\n- [ ] **CG-T043 - x.**\n", encoding="utf-8"
    )
    (tmp_path / "evidence.md").write_text("evidence\n", encoding="utf-8")
    return tmp_path


def test_all_record_kinds_link_to_the_correct_project():
    for kind in RECORD_KINDS:
        ref = link_record(kind, DOSSIER, task_ref="CG-T043")
        assert ref.project_id == "claude-code-proxy"
        assert ref.record_kind == kind
        assert ref.task_ref == "CG-T043"
        assert ref.schema_version == "1.0.0"


def test_task_ref_must_match_a_task_id_shape():
    with pytest.raises(LivingDocRefRejected, match="task id"):
        link_record("route", DOSSIER, task_ref="not a task")


def test_evidence_ref_must_exist_and_stay_inside_the_dossier(tmp_path):
    root = _make_dossier(tmp_path)
    ref = link_record("failure", root, evidence_ref="evidence.md")
    assert ref.evidence_ref == "evidence.md"

    with pytest.raises(LivingDocRefRejected, match="does not exist"):
        link_record("failure", root, evidence_ref="absent.md")
    with pytest.raises(LivingDocRefRejected, match="escapes"):
        link_record("failure", root, evidence_ref="../../etc/passwd")


def test_record_cannot_duplicate_the_task_board_or_content(tmp_path):
    root = _make_dossier(tmp_path)
    record = {
        "schema_version": "1.0.0",
        "record_kind": "promotion",
        "project_id": "claude-code-proxy",
        "tasks": ["CG-T043"],
    }
    with pytest.raises(LivingDocRefRejected, match="duplicates"):
        validate_ref(record, project_root=root)

    ref = link_record("promotion", root, task_ref="CG-T043")
    validate_ref(
        {
            "schema_version": "1.0.0",
            "record_kind": "promotion",
            "project_id": "claude-code-proxy",
        },
        project_root=root,
    )
    assert ref.record_id.startswith("promotion-")


def test_project_id_mismatch_is_rejected(tmp_path):
    wrong = _make_dossier(tmp_path / "wrong", project_id="some-other-project")
    with pytest.raises(LivingDocRefRejected, match="disagrees"):
        validate_ref(
            {
                "schema_version": "1.0.0",
                "record_kind": "quota",
                "project_id": "claude-code-proxy",
            },
            project_root=wrong,
        )


def test_missing_dossier_is_rejected(tmp_path):
    with pytest.raises(LivingDocRefRejected, match="no Living Document dossier"):
        link_record("session", tmp_path)


def test_projection_carries_references_and_counts_only(tmp_path):
    root = _make_dossier(tmp_path)
    refs = [
        link_record("route", root, task_ref="CG-T043"),
        link_record("route", root),
        link_record("quota", root, task_ref="CG-T021"),
    ]
    projection = derived_projection(refs)
    assert projection["project_ids"] == ["claude-code-proxy"]
    assert projection["records_by_kind"] == {"route": 2, "quota": 1}
    assert projection["task_refs"] == ["CG-T021", "CG-T043"]
    assert projection["record_count"] == 3
    blob = repr(projection)
    assert "task_ref" not in blob or projection["task_refs"] == ["CG-T021", "CG-T043"]
    # no record payload, no board text, no evidence content
    for forbidden in ("record_id", "project_root", "created_at", "evidence_ref"):
        assert forbidden not in projection


def test_real_dossier_resolves_its_canonical_id():
    assert resolve_project_id(DOSSIER) == "claude-code-proxy"
    ref = link_record("canary", DOSSIER, task_ref="CG-T043")
    assert isinstance(ref, LivingDocRef)
    assert ref.project_id == "claude-code-proxy"
