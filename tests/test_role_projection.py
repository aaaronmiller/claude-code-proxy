"""CG-T083 — sparse role/effort projection, fail-closed, overrides recorded."""

from __future__ import annotations

import pytest

from src.services.workers.role_projection import (
    POLICY_ID,
    ProjectionError,
    project_role,
)


def test_canonical_policy_projects_exact_codex_profile():
    profile = project_role("implement", "codex")
    assert profile.effective_effort == "high"
    assert profile.requested_effort == ""
    assert profile.override_source == ""
    assert profile.harness_profile == {
        "cli": "codex exec",
        "config": {"model_reasoning_effort": "high"},
    }
    assert profile.policy_id.startswith("sha256:")
    assert profile.policy_id == POLICY_ID


def test_canonical_policy_projects_exact_opencode_profile():
    profile = project_role("implement", "opencode")
    assert profile.effective_effort == "high"
    assert profile.harness_profile == {
        "cli": "opencode run",
        "flags": {"--variant": "high"},
    }


def test_unknown_role_fails_closed():
    with pytest.raises(ProjectionError, match="refusing to guess"):
        project_role("vibes", "codex")


def test_unknown_harness_fails_closed():
    with pytest.raises(ProjectionError, match="no canonical projection"):
        project_role("implement", "claude-code")


def test_unsupported_effort_fails_closed():
    # "max" is not a Codex effort; the sparse cell set must refuse it.
    with pytest.raises(ProjectionError, match="not supported"):
        project_role("implement", "codex", effort_override="max", override_source="runtime")


def test_runtime_override_is_recorded():
    profile = project_role(
        "review", "opencode", effort_override="max", override_source="runtime"
    )
    assert profile.requested_effort == "max"
    assert profile.effective_effort == "max"
    assert profile.override_source == "runtime"
    assert profile.harness_profile["flags"]["--variant"] == "max"


def test_override_without_source_is_rejected():
    with pytest.raises(ProjectionError, match="runtime"):
        project_role("review", "opencode", effort_override="max")


def test_every_policy_cell_is_supported_by_its_harness():
    from src.services.workers.role_projection import ROLE_POLICY, SUPPORTED_EFFORT

    for role, cells in ROLE_POLICY.items():
        assert set(cells) <= {"codex", "opencode"}, role
        for harness, effort in cells.items():
            assert effort in SUPPORTED_EFFORT[harness], (role, harness, effort)
