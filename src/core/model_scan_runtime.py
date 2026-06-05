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
from src.services.models import model_scan_snapshot

_LOCK = threading.RLock()
_ACTIVE_BINDING: BindResult | None = None


def clear_active_binding() -> None:
    """Reset runtime binding state. Intended for tests and disabled reloads."""
    global _ACTIVE_BINDING
    with _LOCK:
        _ACTIVE_BINDING = None


def get_active_binding() -> BindResult | None:
    with _LOCK:
        return _ACTIVE_BINDING


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


def reload_model_scan(*, profiles_path: Path | None = None) -> dict[str, Any]:
    """Reload model-scan bindings from disk/gateway and update assignment registry.

    Disabled config is a clean no-op. Invalid snapshots leave the previous good in-memory overlay
    in place and do not mutate assignments.
    """
    global _ACTIVE_BINDING
    chain = get_chain()
    config = chain.model_scan
    if not config.enabled:
        clear_active_binding()
        return _summary(enabled=False, changed=False, result=None)

    policy = SelectionPolicy.parse(config.policy)
    bindings = _profile_bindings(profiles_path or DEFAULT_PROFILES_PATH)
    if not bindings:
        return _summary(enabled=True, changed=False, result=None, error="no slot_bindings configured")

    snap = _load_snapshot(config)
    if snap is None:
        return _summary(enabled=True, changed=False, result=_ACTIVE_BINDING, error="no valid snapshot")

    result = bind(
        snap,
        policy,
        bindings,
        static_bindings=_static_assignments(),
        profile_lanes=_profile_lanes(profiles_path or DEFAULT_PROFILES_PATH),
    )
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

    with _LOCK:
        _ACTIVE_BINDING = result
    return _summary(enabled=True, changed=changed, result=result)
