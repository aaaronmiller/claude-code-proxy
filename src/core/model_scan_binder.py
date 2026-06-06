"""Selection policy and binder for the Model-Scan Integration (T022, T023).

The selection policy turns one role's ranked candidates into a primary + ordered cascade under a
chosen rule (static/free/budget/quality/roles). The binder applies that policy across every bound
tier and role to produce the global tier assignments and the per-profile overlay map.

See `design.md` sections 4.3 and 4.4, and the validation rules in `data-model.md`:
  * a blocklisted model never appears as primary or in a cascade;
  * `price_blended` null is ineligible for budget and free, eligible for quality;
  * nothing qualifying returns ``(None, [])`` so the binder keeps the static value for that role.

This module (T022 scope) intentionally contains only the snapshot-pure selection logic and the
result dataclasses; the registry/overlay wiring (T023) builds on it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from src.services.models.model_scan_snapshot import Candidate, RoleSelection, RoutingSnapshot

logger = logging.getLogger(__name__)

PolicyKind = Literal["static", "free", "budget", "quality", "roles"]


@dataclass(frozen=True)
class SelectionPolicy:
    """A rule for choosing a primary and cascade from a role's candidates.

    Candidates in a RoleSelection are already ranked best-first by the producer, so after
    filtering, the head of the surviving list is the primary and the tail is the cascade.
    """

    kind: PolicyKind = "static"
    price_ceiling: float | None = None

    @classmethod
    def parse(cls, spec: str) -> "SelectionPolicy":
        """Parse a policy spec string. ``budget:<ceiling>`` carries a numeric per-Mtok ceiling."""
        text = (spec or "static").strip()
        if text.startswith("budget:"):
            raw = text.split(":", 1)[1]
            try:
                ceiling = float(raw)
            except ValueError as exc:
                raise ValueError(f"budget policy needs a numeric ceiling, got {raw!r}") from exc
            if ceiling < 0:
                raise ValueError(f"budget ceiling must be non-negative, got {ceiling}")
            return cls(kind="budget", price_ceiling=ceiling)
        if text in ("static", "free", "quality", "roles"):
            return cls(kind=text)
        raise ValueError(f"unknown selection policy: {spec!r}")

    def _eligible(self, role: RoleSelection, c: Candidate) -> bool:
        """Per-candidate eligibility under this policy (blocklist applied separately)."""
        if self.kind in ("static",):
            return False
        if self.kind == "free":
            return c.price_blended == 0.0
        if self.kind == "budget":
            # Unknown price (null) and over-ceiling are both excluded.
            return (
                c.price_blended is not None
                and self.price_ceiling is not None
                and c.price_blended <= self.price_ceiling
            )
        if self.kind == "quality":
            # Quality ranks by fitness; an unknown price is eligible.
            return True
        if self.kind == "roles":
            # Respect each role's own eval_mode: a free role stays free, a cost role uses cost.
            if role.eval_mode == "free":
                return c.price_blended == 0.0
            return True
        return False

    def choose(
        self, role: RoleSelection, blocklist: frozenset[str]
    ) -> tuple[Candidate | None, list[Candidate]]:
        """Return ``(primary, cascade)``. The cascade excludes the primary and the blocklist.

        Returns ``(None, [])`` when nothing qualifies, signalling the binder to keep static.
        """
        pool = [
            c
            for c in role.candidates
            if c.api_model not in blocklist
            and c.model_id not in blocklist
            and self._eligible(role, c)
        ]
        if not pool:
            return None, []
        return pool[0], pool[1:]


# ─────────────────────────────────────────────────────────────────────────────
# Binder result types (consumed by T023 wiring and the endpoints overlay)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResolvedBinding:
    api_model: str
    base_url: str
    cascade: tuple[str, ...]
    source: str  # "snapshot" | "static"
    provider: str = ""
    role: str = ""


@dataclass(frozen=True)
class BindResult:
    global_tiers: dict[str, ResolvedBinding] = field(default_factory=dict)
    overlay: dict[str, dict[str, ResolvedBinding]] = field(default_factory=dict)
    scan_id: int = -1
    schema_version: str = ""
    provenance: dict[str, str] = field(default_factory=dict)


def _assignment_value(obj: Any, field_name: str, default: Any = "") -> Any:
    if isinstance(obj, Mapping):
        return obj.get(field_name, default)
    return getattr(obj, field_name, default)


def _static_binding(static: Any, role: str) -> ResolvedBinding | None:
    if static is None:
        return None
    model = _assignment_value(static, "model", "")
    if not model:
        return None
    return ResolvedBinding(
        api_model=model,
        base_url=_assignment_value(static, "base_url", "") or "",
        cascade=tuple(_assignment_value(static, "cascade", []) or []),
        source="static",
        provider=_assignment_value(static, "provider", "") or "",
        role=role,
    )


def _snapshot_binding(
    snapshot: RoutingSnapshot,
    role_id: str,
    policy: SelectionPolicy,
) -> ResolvedBinding | None:
    role = snapshot.slots.get(role_id)
    if role is None:
        return None
    primary, cascade = policy.choose(role, snapshot.blocklist)
    if primary is None:
        return None
    return ResolvedBinding(
        api_model=primary.api_model,
        base_url=primary.base_url,
        cascade=tuple(c.api_model for c in cascade),
        source="snapshot",
        provider=primary.provider,
        role=role_id,
    )


def bind(
    snapshot: RoutingSnapshot,
    policy: SelectionPolicy,
    profile_bindings: Mapping[str, Mapping[str, str]],
    *,
    static_bindings: Mapping[str, Any] | None = None,
    profile_lanes: Mapping[str, str] | None = None,
) -> BindResult:
    """Resolve profile slot bindings into static tier writes and per-profile overlays.

    The default profile is the only source of global tier mutations. Named profiles produce
    request-time overlays only when their resolved binding differs from default.
    """
    static_bindings = static_bindings or {}
    profile_lanes = profile_lanes or {}
    default_bindings = profile_bindings.get("default", {}) or {}
    global_tiers: dict[str, ResolvedBinding] = {}
    overlay: dict[str, dict[str, ResolvedBinding]] = {}
    provenance: dict[str, str] = {}

    for assignment_id, role_id in default_bindings.items():
        lane_policy = SelectionPolicy.parse("free") if profile_lanes.get("default") == "standby" else policy
        resolved = _snapshot_binding(snapshot, role_id, lane_policy)
        source = "snapshot"
        if resolved is None:
            resolved = _static_binding(static_bindings.get(assignment_id), role_id)
            source = "static"
        if resolved is None:
            logger.warning("No snapshot or static binding for default.%s role=%s", assignment_id, role_id)
            continue
        global_tiers[assignment_id] = resolved
        provenance[f"default.{assignment_id}"] = source

    for profile_name, bindings in profile_bindings.items():
        if profile_name == "default":
            continue
        profile_overlay: dict[str, ResolvedBinding] = {}
        for assignment_id, role_id in (bindings or {}).items():
            lane_policy = SelectionPolicy.parse("free") if profile_lanes.get(profile_name) == "standby" else policy
            resolved = _snapshot_binding(snapshot, role_id, lane_policy)
            source = "snapshot"
            if resolved is None:
                resolved = _static_binding(static_bindings.get(assignment_id), role_id)
                source = "static"
            if resolved is None:
                logger.warning(
                    "No snapshot or static binding for %s.%s role=%s",
                    profile_name,
                    assignment_id,
                    role_id,
                )
                continue
            default_resolved = global_tiers.get(assignment_id)
            if resolved != default_resolved:
                profile_overlay[assignment_id] = resolved
            provenance[f"{profile_name}.{assignment_id}"] = source
        if profile_overlay:
            overlay[profile_name] = profile_overlay

    return BindResult(
        global_tiers=global_tiers,
        overlay=overlay,
        scan_id=snapshot.scan_id,
        schema_version=snapshot.schema_version,
        provenance=provenance,
    )
