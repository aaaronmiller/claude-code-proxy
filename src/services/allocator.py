"""F18 capacity planner / global allocator - dry-run greedy implementation.

Satisfice-then-maximize allocation of finite, multi-dimensional quota (QuotaMeter,
see src/core/quota_sources.py) across many session-roles. Each role has a hard floor
(gates) and a value_sensitivity weight: low => satisficing (route to the most ABUNDANT
floor-clearing model, preserving scarce smart capacity), high => maximizing (route to
the highest-fitness affordable model).

This is a deterministic greedy approximation of the LP in ai-gateway/plan/04-DATA-CONTRACTS.md.
No solver dependency. The LP core (scipy/pulp/ortools) can replace `allocate()` behind this
same interface if/when a solver dep is approved. Dry-run: computes an allocation + a
bottleneck/notes report; does not enforce anything at runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, Sequence

from src.core.quota_sources import QuotaMeter

_SATISFICE_CUTOFF = 0.25  # value_sensitivity below this => satisficing behavior
_DEFAULT_TOKENS_PER_CALL = 1000.0


@dataclass(frozen=True)
class Candidate:
    model_id: str
    provider: str
    fitness: float
    price_blended: float = 0.0
    has_tools: bool = False
    has_vision: bool = False
    ctx: int = 0
    tier: str = ""


@dataclass(frozen=True)
class RoleSpec:
    session_id: str
    role_id: str
    floor_min_value: float = 0.0
    needs_tools: bool = False
    needs_vision: bool = False
    min_ctx: int = 0
    value_sensitivity: float = 1.0
    diversity_cap: float = 0.6
    fallback_depth: int = 4
    expected_calls_per_day: float = 100.0
    importance: float = 0.5


@dataclass(frozen=True)
class RoleAllocation:
    session_id: str
    role_id: str
    primary: str | None
    cascade: list[str]
    reason: str


@dataclass
class AllocationResult:
    allocations: list[RoleAllocation] = field(default_factory=list)
    bottleneck_meters: list[tuple[str, float]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _clears_floor(c: Candidate, role: RoleSpec) -> bool:
    if role.needs_tools and not c.has_tools:
        return False
    if role.needs_vision and not c.has_vision:
        return False
    if role.min_ctx and c.ctx and c.ctx < role.min_ctx:
        return False
    if c.fitness < role.floor_min_value:
        return False
    return True


def _meters_for(c: Candidate, meters: Sequence[QuotaMeter]) -> list[QuotaMeter]:
    out = []
    for m in meters:
        if m.provider != c.provider:
            continue
        if m.model is not None and m.model != c.model_id:
            continue
        out.append(m)
    return out


def _cost_per_call(meter: QuotaMeter, c: Candidate) -> float:
    if meter.unit == "calls" or meter.unit == "search_calls":
        return 1.0
    if meter.unit == "tokens":
        return _DEFAULT_TOKENS_PER_CALL
    if meter.unit in ("credits", "dollars"):
        return max(c.price_blended, 0.0)
    return 1.0


def _affordable(c: Candidate, role: RoleSpec, meters: Sequence[QuotaMeter], rem: dict[str, float]) -> bool:
    for m in _meters_for(c, meters):
        need = role.expected_calls_per_day * _cost_per_call(m, c)
        if m.limit > 0 and rem.get(m.id, m.remaining) < need:
            return False
    return True


def _min_headroom(c: Candidate, meters: Sequence[QuotaMeter], rem: dict[str, float]) -> float:
    fracs = []
    for m in _meters_for(c, meters):
        if m.limit > 0:
            fracs.append(rem.get(m.id, m.remaining) / m.limit)
    return min(fracs) if fracs else 1.0


def _debit(c: Candidate, role: RoleSpec, meters: Sequence[QuotaMeter], rem: dict[str, float]) -> None:
    for m in _meters_for(c, meters):
        rem[m.id] = rem.get(m.id, m.remaining) - role.expected_calls_per_day * _cost_per_call(m, c)


def allocate(
    roles: Sequence[RoleSpec],
    candidates_by_role: Mapping[str, Sequence[Candidate]],
    meters: Sequence[QuotaMeter],
) -> AllocationResult:
    """Greedy satisfice-then-maximize allocation. Maximizing roles (high
    value_sensitivity * importance) claim scarce capacity first; satisficing roles take
    the most abundant floor-clearing model so scarce smart capacity is preserved."""
    rem: dict[str, float] = {m.id: m.remaining for m in meters}
    result = AllocationResult()

    # Priority: maximizing + important roles first.
    ordered = sorted(
        roles, key=lambda r: r.value_sensitivity * (0.5 + r.importance), reverse=True
    )

    for role in ordered:
        cands = [c for c in candidates_by_role.get(role.role_id, []) if _clears_floor(c, role)]
        eligible = [c for c in cands if _affordable(c, role, meters, rem)]
        if not eligible:
            result.allocations.append(
                RoleAllocation(role.session_id, role.role_id, None, [],
                               "no floor-clearing affordable candidate (error: would route below floor)")
            )
            continue

        if role.value_sensitivity < _SATISFICE_CUTOFF:
            # satisfice: most abundant, then cheaper, then fitness
            primary = max(eligible, key=lambda c: (_min_headroom(c, meters, rem), -c.price_blended, c.fitness))
            reason = "satisfice: abundant floor-clearing model (scarce capacity preserved)"
        else:
            # maximize: highest fitness, then abundance
            primary = max(eligible, key=lambda c: (c.fitness, _min_headroom(c, meters, rem)))
            reason = "maximize: highest-fitness affordable model"

        _debit(primary, role, meters, rem)

        # cascade: next best eligible by fitness, diversity-capped by provider
        cascade: list[str] = []
        used_providers = {primary.provider}
        provider_share: dict[str, int] = {primary.provider: 1}
        for c in sorted(eligible, key=lambda c: c.fitness, reverse=True):
            if c.model_id == primary.model_id:
                continue
            if len(cascade) >= role.fallback_depth:
                break
            # enforce diversity cap (approx: limit repeats of a provider)
            if provider_share.get(c.provider, 0) >= max(1, int(role.fallback_depth * role.diversity_cap)):
                continue
            cascade.append(c.model_id)
            provider_share[c.provider] = provider_share.get(c.provider, 0) + 1
            used_providers.add(c.provider)

        result.allocations.append(
            RoleAllocation(role.session_id, role.role_id, primary.model_id, cascade, reason)
        )

    # bottleneck report: tightest meters after allocation
    fracs = []
    for m in meters:
        if m.limit > 0:
            fracs.append((m.id, max(0.0, rem.get(m.id, m.remaining) / m.limit)))
    result.bottleneck_meters = sorted(fracs, key=lambda t: t[1])[:5]

    unfilled = [a for a in result.allocations if a.primary is None]
    if unfilled:
        result.notes.append(f"{len(unfilled)} role(s) had no affordable floor-clearing model")
    return result


def allocation_to_snapshot_dict(
    result: AllocationResult,
    candidates_by_role: Mapping[str, Sequence[Candidate]],
    *,
    schema_version: str = "1.0.0",
    generated_at: str = "",
    scan_id: int = 0,
    eval_mode: str = "cost_basis",  # snapshot contract: cost_basis | free (NOT a policy name)
) -> dict:
    """Map an AllocationResult to the routing_snapshot JSON shape that
    src/services/models/model_scan_snapshot.py parses (S1-08). Each session-role becomes a
    slot keyed "<session>:<role>" with best=primary and candidates=[primary, *cascade].
    base_url is left empty (the consumer gap-fills from its provider registry). This is the
    mapping only; wiring it into model_scan_runtime.reload is a separate follow-up that changes
    runtime routing and should be a deliberate commit."""
    idx: dict[tuple[str, str], Candidate] = {}
    for role_id, cands in candidates_by_role.items():
        for c in cands:
            idx[(role_id, c.model_id)] = c

    def _cand(role_id: str, model_id: str) -> dict:
        c = idx.get((role_id, model_id))
        return {
            "model_id": model_id,
            "provider": c.provider if c else (model_id.split("/")[0] if "/" in model_id else ""),
            "api_model": model_id,
            "base_url": "",
            "fitness": c.fitness if c else 0.0,
            "price_blended": c.price_blended if c else None,
            "tier": c.tier if c else "",
            "has_tools": c.has_tools if c else False,
            "has_vision": c.has_vision if c else False,
        }

    slots: dict[str, dict] = {}
    for a in result.allocations:
        if a.primary is None:
            continue
        slot_key = f"{a.session_id}:{a.role_id}"
        models = [a.primary] + list(a.cascade)
        slots[slot_key] = {
            "label": slot_key,
            "eval_mode": eval_mode,
            "best": _cand(a.role_id, a.primary),
            "candidates": [_cand(a.role_id, m) for m in models],
        }

    return {
        "schema_version": schema_version,
        "generated_at": generated_at,
        "scan_id": scan_id,
        "slots": slots,
        "provider_health": {},
        "provider_quota": {},
        "blocklist": [],
    }


def candidates_from_snapshot(snapshot, slot_id: str) -> list[Candidate]:
    """Build allocator Candidates from a RoutingSnapshot slot (duck-typed: needs
    .slots[slot_id].candidates with model_scan_snapshot.Candidate fields)."""
    sel = getattr(snapshot, "slots", {}).get(slot_id)
    if sel is None:
        return []
    out: list[Candidate] = []
    for c in sel.candidates:
        out.append(
            Candidate(
                model_id=c.model_id,
                provider=c.provider,
                fitness=c.fitness,
                price_blended=(c.price_blended or 0.0),
                has_tools=c.has_tools,
                has_vision=c.has_vision,
                ctx=getattr(c, "ctx", 0) or 0,
                tier=c.tier,
            )
        )
    return out


def _snapshot_fitness_index(snapshot) -> dict[str, float]:
    """Best fitness per model_id across all snapshot slots."""
    idx: dict[str, float] = {}
    for sel in getattr(snapshot, "slots", {}).values():
        for c in sel.candidates:
            if c.fitness > idx.get(c.model_id, float("-inf")):
                idx[c.model_id] = c.fitness
    return idx


def _base_role(role_id: str) -> str:
    """aux-3 -> aux (strip a numeric expansion suffix); leave others as-is."""
    head, _, tail = role_id.rpartition("-")
    return head if (head and tail.isdigit()) else role_id


def resolve_named_floors(
    roles: Sequence[RoleSpec], named_floors: Mapping[str, str] | None, snapshot
) -> list[RoleSpec]:
    """Set floor_min_value for roles whose floor was a MODEL NAME (e.g. "gpt-oss-120b") by
    looking up that model's fitness in the snapshot. Matches by exact role_id or its base
    (so a counted role aux-3 picks up the "aux" named floor). Unknown names leave the floor
    unchanged (0.0). RoleSpec is frozen, so returns new instances."""
    if not named_floors:
        return list(roles)
    idx = _snapshot_fitness_index(snapshot)
    out: list[RoleSpec] = []
    for r in roles:
        name = named_floors.get(r.role_id) or named_floors.get(_base_role(r.role_id))
        if name and name in idx:
            out.append(replace(r, floor_min_value=idx[name]))
        else:
            out.append(r)
    return out


def plan_from_snapshot(
    snapshot,
    roles: Sequence[RoleSpec],
    meters: Sequence[QuotaMeter],
    *,
    slot_map: Mapping[str, str] | None = None,
    named_floors: Mapping[str, str] | None = None,
    schema_version: str = "1.0.0",
    generated_at: str = "",
    scan_id: int = 0,
) -> dict:
    """End-to-end F18 integration core (pure): read a model-scan RoutingSnapshot, run the
    fleet allocator over the given session-roles + quota meters, and emit an augmented
    routing_snapshot dict (per-session-role slots). Each role pulls its candidate pool from the
    snapshot slot named by slot_map.get(role_id, role_id). No runtime side effects; wiring this
    into model_scan_runtime.reload (behind a default-off flag) is the only remaining step."""
    slot_map = slot_map or {}
    roles = resolve_named_floors(roles, named_floors, snapshot)
    cbr: dict[str, list[Candidate]] = {}
    for r in roles:
        slot_id = slot_map.get(r.role_id) or slot_map.get(_base_role(r.role_id)) or _base_role(r.role_id)
        cbr[r.role_id] = candidates_from_snapshot(snapshot, slot_id)
    result = allocate(roles, cbr, meters)
    return allocation_to_snapshot_dict(
        result, cbr, schema_version=schema_version, generated_at=generated_at, scan_id=scan_id
    )


def apply_allocator_if_enabled(
    snapshot,
    roles: Sequence[RoleSpec],
    meters: Sequence[QuotaMeter],
    *,
    enabled: bool,
    slot_map: Mapping[str, str] | None = None,
    schema_version: str = "1.0.0",
    generated_at: str = "",
    scan_id: int = 0,
) -> dict | None:
    """Integration seam (DEFAULT OFF, gated by config ALLOCATOR_ENABLED).

    Returns None when disabled OR when inputs are insufficient (no roles) - the caller then
    keeps the original snapshot UNCHANGED, so enabling the flag without configured session
    profiles is a safe no-op (never misroutes). When enabled with roles, returns the augmented
    snapshot dict. Splicing this single call into model_scan_runtime.reload is the only remaining
    (user-gated) step; this function itself has no runtime side effects."""
    if not enabled or not roles:
        return None
    return plan_from_snapshot(
        snapshot, roles, meters or [], slot_map=slot_map,
        schema_version=schema_version, generated_at=generated_at, scan_id=scan_id,
    )
