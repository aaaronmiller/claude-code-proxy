"""Runtime reload and overlay state for model-scan routing bindings."""

from __future__ import annotations

import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.core.assignments import Assignment, get_registry
from src.core.model_scan_binder import BindResult, ResolvedBinding, SelectionPolicy, bind
from src.core.profiles import DEFAULT_PROFILES_PATH, get_all_profiles
from src.core.proxy_chain import get_chain
from src.core.quota_runtime import collect_meters
from src.services.allocator import plan_from_snapshot
from src.services.models import model_scan_snapshot
from src.services.session_profiles import named_floor_models, role_specs_from_profile

_LOCK = threading.RLock()
_ACTIVE_BINDING: BindResult | None = None
_ALLOC_NOOP: dict[str, Any] = {
    "enabled": False, "profiles": {}, "roles": 0, "meters": [], "tightest_meters": []
}
_ACTIVE_ALLOCATION: dict[str, Any] = dict(_ALLOC_NOOP)


def clear_active_binding() -> None:
    """Reset runtime binding state. Intended for tests and disabled reloads."""
    global _ACTIVE_BINDING, _ACTIVE_ALLOCATION
    with _LOCK:
        _ACTIVE_BINDING = None
        _ACTIVE_ALLOCATION = dict(_ALLOC_NOOP)


def get_active_binding() -> BindResult | None:
    with _LOCK:
        return _ACTIVE_BINDING


def get_active_allocation() -> dict[str, Any]:
    """Last F18 allocator report (per-profile picks + quota meters) for observability."""
    with _LOCK:
        return dict(_ACTIVE_ALLOCATION)


def resolve_profile_binding(profile_name: str, assignment_id: str) -> ResolvedBinding | None:
    """Return the active request-time overlay for a profile/assignment pair."""
    with _LOCK:
        active = _ACTIVE_BINDING
        if active is None:
            return None
        return active.overlay.get(profile_name, {}).get(assignment_id)


def _profile_bindings(path: Path | None) -> dict[str, dict[str, str]]:
    profiles = get_all_profiles(path)
    result: dict[str, dict[str, str]] = {}
    for name, slots in profiles.items():
        bindings = slots.get("slot_bindings") if isinstance(slots, dict) else None
        if isinstance(bindings, dict):
            result[name] = {str(k): str(v) for k, v in bindings.items() if k and v}
    return result


def _profile_lanes(path: Path | None) -> dict[str, str]:
    profiles = get_all_profiles(path)
    return {
        name: str(slots.get("lane", "interactive"))
        for name, slots in profiles.items()
        if isinstance(slots, dict)
    }


def _static_assignments() -> dict[str, Assignment]:
    return {assignment.id: assignment for assignment in get_registry().list()}


def _load_snapshot(config) -> model_scan_snapshot.RoutingSnapshot | None:
    snapshot_path = str(getattr(config, "snapshot_path", "") or "").strip()
    gateway_url = str(getattr(config, "gateway_url", "") or "").strip()
    snap = None
    if snapshot_path:
        snap = model_scan_snapshot.load(str(Path(snapshot_path).expanduser()))
    if snap is None and gateway_url:
        snap = model_scan_snapshot.from_gateway(gateway_url)
    if snap is None:
        return None
    limit = int(getattr(config, "staleness_limit_s", 86400) or 86400)
    if model_scan_snapshot.is_data_stale(snap, limit):
        return None
    return snap


def _binding_to_assignment_updates(binding: ResolvedBinding) -> dict[str, Any]:
    return {
        "model": binding.api_model,
        "provider": binding.provider,
        "base_url": binding.base_url,
        "cascade": list(binding.cascade),
    }


def _summary(
    *,
    enabled: bool,
    changed: bool,
    result: BindResult | None,
    error: str = "",
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "changed": changed,
        "scan_id": result.scan_id if result else None,
        "schema_version": result.schema_version if result else "",
        "global_tiers": {
            tier: asdict(binding) for tier, binding in (result.global_tiers if result else {}).items()
        },
        "overlay_profiles": sorted((result.overlay if result else {}).keys()),
        "provenance": dict(result.provenance) if result else {},
        "error": error,
    }


def _apply_allocator(snap, config, result: BindResult) -> dict[str, Any]:
    """F18 seam: run the quota-aware allocator over `snap` for the chain's session_profiles and
    splice the per-(profile, role) picks into `result.overlay` — the exact dict the request path
    reads via resolve_profile_binding(). Mutates `result.overlay` in place; returns a report.

    The allocator works in snapshot model_id space, so the true api_model/base_url are recovered
    from the original snapshot candidate (base_url stays advisory; the router still gap-fills)."""
    profiles_cfg = getattr(config, "session_profiles", None) or {}
    slot_map = dict(getattr(config, "allocator_slot_map", None) or {})

    roles = []
    named_floors: dict[str, str] = {}
    for profile_name, pcfg in profiles_cfg.items():
        roles.extend(role_specs_from_profile(profile_name, pcfg))
        named_floors.update(named_floor_models(pcfg))
    if not roles:
        return dict(_ALLOC_NOOP)

    meters = collect_meters(config)
    augmented = plan_from_snapshot(
        snap, roles, meters,
        slot_map=slot_map, named_floors=named_floors,
        schema_version=getattr(snap, "schema_version", "1.0.0"),
        generated_at=getattr(snap, "generated_at", "") or "",
        scan_id=getattr(snap, "scan_id", 0),
    )

    # index snapshot candidates by model_id to recover the real api_model / base_url / provider
    index: dict[str, Any] = {}
    for sel in snap.slots.values():
        for cand in (*sel.candidates, *( (sel.best,) if sel.best else () )):
            index.setdefault(cand.model_id, cand)

    profiles_report: dict[str, dict[str, str]] = {}
    for slot_key, slot in augmented["slots"].items():
        profile_name, _, role_id = slot_key.partition(":")
        best_mid = slot["best"]["model_id"]
        orig = index.get(best_mid)
        api_model = orig.api_model if orig else best_mid
        cascade = tuple(
            (index[c["model_id"]].api_model if c["model_id"] in index else c["model_id"])
            for c in slot["candidates"] if c["model_id"] != best_mid
        )
        result.overlay.setdefault(profile_name, {})[role_id] = ResolvedBinding(
            api_model=api_model,
            base_url=(orig.base_url if orig else "") or "",
            cascade=cascade,
            source="allocator",
            provider=orig.provider if orig else slot["best"].get("provider", ""),
            role=role_id,
        )
        profiles_report.setdefault(profile_name, {})[role_id] = api_model

    meters_report = [
        {"provider": m.provider, "remaining_fraction": round(m.remaining_fraction, 4)} for m in meters
    ]
    return {
        "enabled": True,
        "profiles": profiles_report,
        "roles": len(roles),
        "meters": meters_report,
        "tightest_meters": sorted(meters_report, key=lambda d: d["remaining_fraction"])[:5],
    }


def reload_model_scan(*, profiles_path: Path | None = None) -> dict[str, Any]:
    """Reload model-scan bindings from disk/gateway and update assignment registry.

    Disabled config is a clean no-op. Invalid snapshots leave the previous good in-memory overlay
    in place and do not mutate assignments. When ALLOCATOR_ENABLED + session_profiles are set, the
    F18 allocator also writes per-profile overlays (consumed at request time, no registry writes).
    """
    global _ACTIVE_BINDING, _ACTIVE_ALLOCATION
    chain = get_chain()
    config = chain.model_scan
    if not config.enabled:
        clear_active_binding()
        return _summary(enabled=False, changed=False, result=None)

    policy = SelectionPolicy.parse(config.policy)
    bindings = _profile_bindings(profiles_path or DEFAULT_PROFILES_PATH)
    allocator_on = bool(
        getattr(config, "allocator_enabled", False) and getattr(config, "session_profiles", None)
    )

    if not bindings and not allocator_on:
        out = _summary(enabled=True, changed=False, result=None, error="no slot_bindings configured")
        out["allocator"] = dict(_ALLOC_NOOP)
        return out

    snap = _load_snapshot(config)
    if snap is None:
        out = _summary(enabled=True, changed=False, result=_ACTIVE_BINDING, error="no valid snapshot")
        out["allocator"] = dict(_ALLOC_NOOP)
        return out

    if bindings:
        result = bind(
            snap,
            policy,
            bindings,
            static_bindings=_static_assignments(),
            profile_lanes=_profile_lanes(profiles_path or DEFAULT_PROFILES_PATH),
        )
    else:
        result = BindResult(scan_id=snap.scan_id, schema_version=snap.schema_version)

    registry = get_registry()
    changed = False
    for assignment_id, binding in result.global_tiers.items():
        current = registry.get(assignment_id)
        if current is None:
            continue
        updates = _binding_to_assignment_updates(binding)
        if any(getattr(current, key) != value for key, value in updates.items()):
            registry.update(assignment_id, updates, principal="model_scan")
            changed = True

    alloc_report = _apply_allocator(snap, config, result) if allocator_on else dict(_ALLOC_NOOP)

    with _LOCK:
        _ACTIVE_BINDING = result
        _ACTIVE_ALLOCATION = alloc_report

    out = _summary(enabled=True, changed=changed, result=result)
    out["allocator"] = alloc_report
    return out
