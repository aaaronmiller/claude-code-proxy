"""Sparse canonical role/effort projection (CG-T083).

One canonical policy table projects a task role into exact per-harness
effort profiles for Codex and one alternate harness (OpenCode). The table is
sparse on purpose: an unlisted role, an unknown harness, or an effort value a
harness does not support fails closed. Explicit runtime overrides are
permitted (per the corrected dynamic-reasoning policy) and both the requested
override and the effective value are recorded on every projection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

POLICY_VERSION = "1.0.0"

#: Canonical task roles (aligned with the frozen task-family vocabulary).
CANONICAL_ROLES = ("implement", "review", "research", "triage", "docs")

#: Alternate harness beyond the exact Codex projection.
HARNESSES = ("codex", "opencode")

#: Effort values each harness actually accepts (probed 2026-08-29,
#: see worker-capability-inventory.md).
SUPPORTED_EFFORT = {
    "codex": ("minimal", "low", "medium", "high"),
    "opencode": ("minimal", "low", "medium", "high", "max"),
}

#: The sparse canonical policy: role -> harness -> effort. Missing cells are
#: deliberate; a projection hitting one must fail closed, never guess.
ROLE_POLICY = {
    "implement": {"codex": "high", "opencode": "high"},
    "review": {"codex": "medium", "opencode": "medium"},
    "research": {"codex": "high", "opencode": "high"},
    "triage": {"codex": "low", "opencode": "minimal"},
    "docs": {"codex": "low", "opencode": "minimal"},
}


class ProjectionError(ValueError):
    """Raised when the canonical policy cannot project a role fail-closed."""


def _policy_id() -> str:
    payload = json.dumps(
        {"version": POLICY_VERSION, "roles": ROLE_POLICY, "effort": SUPPORTED_EFFORT},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


POLICY_ID = _policy_id()


@dataclass(frozen=True)
class RoleEffortProfile:
    """The projection result: requested override and effective value recorded."""

    role: str
    harness: str
    requested_effort: str   # "" when the policy default applies
    effective_effort: str
    override_source: str    # "" (policy default) or "runtime"
    policy_id: str
    policy_version: str
    harness_profile: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def harness_profile(harness: str, effort: str) -> dict[str, Any]:
    """The exact harness invocation fragment for one effort value."""
    if harness == "codex":
        return {"cli": "codex exec", "config": {"model_reasoning_effort": effort}}
    if harness == "opencode":
        return {"cli": "opencode run", "flags": {"--variant": effort}}
    raise ProjectionError(f"harness {harness!r} has no profile projection")


def project_role(
    role: str,
    harness: str,
    *,
    effort_override: str = "",
    override_source: str = "",
) -> RoleEffortProfile:
    """Project one role onto one harness, failing closed on any gap."""
    if role not in ROLE_POLICY:
        raise ProjectionError(
            f"role {role!r} is not in the canonical policy; refusing to guess"
        )
    if harness not in HARNESSES:
        raise ProjectionError(
            f"harness {harness!r} has no canonical projection (known: {list(HARNESSES)})"
        )
    supported = SUPPORTED_EFFORT[harness]

    if effort_override:
        if override_source != "runtime":
            raise ProjectionError(
                "an explicit effort override must record override_source='runtime'"
            )
        if effort_override not in supported:
            raise ProjectionError(
                f"effort {effort_override!r} is not supported by {harness} "
                f"(supported: {list(supported)}); failing closed"
            )
        requested, effective, source = effort_override, effort_override, "runtime"
    else:
        cell = ROLE_POLICY[role].get(harness)
        if cell is None:
            raise ProjectionError(
                f"the canonical policy has no {harness} cell for role {role!r}"
            )
        if cell not in supported:
            raise ProjectionError(
                f"policy cell {cell!r} for {role}/{harness} is unsupported; "
                "failing closed"
            )
        requested, effective, source = "", cell, ""

    return RoleEffortProfile(
        role=role,
        harness=harness,
        requested_effort=requested,
        effective_effort=effective,
        override_source=source,
        policy_id=POLICY_ID,
        policy_version=POLICY_VERSION,
        harness_profile=harness_profile(harness, effective),
    )
