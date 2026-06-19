"""Session-profile plumbing (F18 / F12): parse the `session_profiles` config shape
(see ai-gateway/plan/05-CONFIG-SCHEMA.md) into allocator RoleSpec objects.

Pure and offline-testable. A profile is a TEMPLATE; the caller instantiates it per running
session by passing a concrete session_id. Named floors (floor.min_value as a model name rather
than a number) are resolved at plan time against the snapshot, not here - see resolve note.
"""
from __future__ import annotations

from typing import Mapping

from src.services.allocator import RoleSpec


def role_specs_from_profile(session_id: str, profile_cfg: Mapping) -> list[RoleSpec]:
    """Expand one profile template into RoleSpecs for a concrete session.

    profile_cfg = {"start_mode": ..., "roles": {role_id: {
        floor: {min_value(number)|needs_tools|needs_vision|min_ctx|min_tier(ignored here)},
        value_sensitivity, diversity_cap, fallback_depth, expected_calls_per_day, importance,
        count(optional, default 1)}}}
    A role with count>1 expands to role_id-1..N (e.g. 10 aux roles).
    """
    out: list[RoleSpec] = []
    roles = profile_cfg.get("roles", {}) if isinstance(profile_cfg, Mapping) else {}
    for role_id, rc in roles.items():
        rc = rc or {}
        floor = rc.get("floor", {}) or {}
        min_value = floor.get("min_value")
        # numeric floor only; a model-name floor is resolved later against the snapshot
        floor_min = float(min_value) if isinstance(min_value, (int, float)) else 0.0
        count = int(rc.get("count", 1) or 1)
        for i in range(count):
            rid = role_id if count == 1 else f"{role_id}-{i + 1}"
            out.append(
                RoleSpec(
                    session_id=session_id,
                    role_id=rid,
                    floor_min_value=floor_min,
                    needs_tools=bool(floor.get("needs_tools", False)),
                    needs_vision=bool(floor.get("needs_vision", False)),
                    min_ctx=int(floor.get("min_ctx", 0) or 0),
                    value_sensitivity=float(rc.get("value_sensitivity", 1.0)),
                    diversity_cap=float(rc.get("diversity_cap", 0.6)),
                    fallback_depth=int(rc.get("fallback_depth", 4) or 4),
                    expected_calls_per_day=float(rc.get("expected_calls_per_day", 100.0)),
                    importance=float(rc.get("importance", 0.5)),
                )
            )
    return out


def named_floor_models(profile_cfg: Mapping) -> dict[str, str]:
    """Return {role_id: model_name} for roles whose floor.min_value is a model NAME (not a
    number). The plan step resolves these to that model's fitness from the snapshot, then sets
    the role's floor_min_value accordingly. Surfaced here so resolution is explicit, not silent."""
    out: dict[str, str] = {}
    roles = profile_cfg.get("roles", {}) if isinstance(profile_cfg, Mapping) else {}
    for role_id, rc in roles.items():
        mv = (rc or {}).get("floor", {}).get("min_value")
        if isinstance(mv, str) and mv:
            out[role_id] = mv
    return out
