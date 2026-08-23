"""Runtime reload and overlay state for model-scan routing bindings."""

from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.core.model_scan_binder import BindResult, ResolvedBinding, SelectionPolicy, bind
from src.core.persistence_boundary import non_persisting_preview
from src.core.profiles import DEFAULT_PROFILES_PATH, get_all_profiles
from src.core.proxy_chain import ProxyChain, get_chain
from src.core.quota_runtime import collect_meters
from src.services.allocator import plan_from_snapshot
from src.services.models import model_scan_snapshot
from src.services.models.shadow_comparison import (
    MetricEvidence,
    RouteFacts,
    build_comparison,
)
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
    """Return the active dynamic binding for a profile/assignment pair.

    A named profile override wins when present. Otherwise every request sees the
    active global binding. Static configuration remains outside this function and
    is therefore the exact fallback when Model Scan is disabled or unavailable.
    """
    from src.core.profiles import ACTIVE_PROFILE, get_canary_binding

    profile = ACTIVE_PROFILE.get()
    if profile is not None and profile.kind == "canary" and profile.name == profile_name:
        canary = get_canary_binding(profile_name, assignment_id)
        if canary is not None:
            return ResolvedBinding(
                api_model=str(canary["api_model"]),
                base_url=str(canary["base_url"]),
                cascade=tuple(canary["cascade"]),
                source="canary",
                provider=str(canary["provider"]),
                role=str(canary["role"]),
            )
    with _LOCK:
        active = _ACTIVE_BINDING
        if active is None:
            return None
        return active.overlay.get(profile_name, {}).get(
            assignment_id,
            active.global_tiers.get(assignment_id),
        )


@dataclass(frozen=True)
class CallableBinding:
    """A dynamic binding joined to the router-owned provider registry."""

    binding: ResolvedBinding
    endpoint: str
    provider: str
    api_key: str = field(repr=False)


def configured_assignment_id(model: str, config: Any) -> str | None:
    """Match a routed model to one configured tier without family guessing."""

    def normalize(value: Any) -> str:
        text = str(value or "").lower()
        return text.split("/", 1)[1] if "/" in text else text

    routed = normalize(model)
    if not routed:
        return None
    for assignment_id in ("xbig", "big", "middle", "small"):
        if routed == normalize(getattr(config, f"{assignment_id}_model", "")):
            return assignment_id
    return None


def resolve_callable_binding(
    profile_name: str,
    assignment_id: str,
    config: Any,
) -> CallableBinding | None:
    """Return a credential-paired dynamic route, or abstain to static routing.

    Model Scan owns the model identity and ranking. Clutch owns provider URLs and
    credentials. A snapshot binding is never applied unless that join is complete.
    """
    binding = resolve_profile_binding(profile_name, assignment_id)
    if binding is None or not binding.provider:
        return None
    endpoint = binding.base_url or config.get_provider_endpoint(binding.provider)
    api_key = config.get_provider_api_key(binding.provider)
    if not endpoint or not api_key:
        return None
    return CallableBinding(
        binding=binding,
        endpoint=str(endpoint),
        provider=binding.provider,
        api_key=str(api_key),
    )


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


def _static_assignments() -> dict[str, Any]:
    return _chain_assignments(get_chain())


def _chain_assignments(chain: ProxyChain) -> dict[str, Any]:
    return {assignment.id: assignment for assignment in chain.assignments}


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

    # Index exact snapshot identities. Missing entries are excluded rather than
    # reconstructed from display or benchmark names.
    index: dict[str, Any] = {}
    for sel in snap.slots.values():
        for cand in (*sel.candidates, *( (sel.best,) if sel.best else () )):
            index.setdefault(cand.model_id, cand)

    profiles_report: dict[str, dict[str, str]] = {}
    identity_exclusions: list[dict[str, str]] = []
    for slot_key, slot in augmented["slots"].items():
        profile_name, _, role_id = slot_key.partition(":")
        best_mid = slot["best"]["model_id"]
        orig = index.get(best_mid)
        if orig is None or not orig.api_model or not orig.provider:
            identity_exclusions.append(
                {
                    "slot": slot_key,
                    "model_id": best_mid,
                    "reason": "unresolved-callable-identity",
                }
            )
            continue
        api_model = orig.api_model
        cascade = tuple(
            index[c["model_id"]].api_model
            for c in slot["candidates"]
            if c["model_id"] != best_mid
            and c["model_id"] in index
            and index[c["model_id"]].api_model
        )
        result.overlay.setdefault(profile_name, {})[role_id] = ResolvedBinding(
            api_model=api_model,
            base_url=orig.base_url or "",
            cascade=cascade,
            source="allocator",
            provider=orig.provider,
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
        "identity_exclusions": identity_exclusions,
    }


def preview_model_scan(*, profiles_path: Path | None = None) -> dict[str, Any]:
    """Compute model-scan bindings without mutating persistent or active state."""
    with non_persisting_preview():
        live_chain = get_chain()
        chain = ProxyChain.from_dict(live_chain.to_dict())
        config = chain.model_scan
        if not config.enabled:
            out = _summary(enabled=False, changed=False, result=None)
            out.update(
                {
                    "mode": "preview",
                    "would_change": False,
                    "proposed_global_changes": {},
                    "persistent_writes": [],
                    "allocator": dict(_ALLOC_NOOP),
                }
            )
            return out

        path = profiles_path or DEFAULT_PROFILES_PATH
        bindings = _profile_bindings(path)
        allocator_on = bool(
            getattr(config, "allocator_enabled", False)
            and getattr(config, "session_profiles", None)
        )
        if not bindings and not allocator_on:
            out = _summary(
                enabled=True,
                changed=False,
                result=None,
                error="no slot_bindings configured",
            )
            out.update(
                {
                    "mode": "preview",
                    "would_change": False,
                    "proposed_global_changes": {},
                    "persistent_writes": [],
                    "allocator": dict(_ALLOC_NOOP),
                }
            )
            return out

        snap = _load_snapshot(config)
        if snap is None:
            out = _summary(
                enabled=True,
                changed=False,
                result=None,
                error="no valid snapshot",
            )
            out.update(
                {
                    "mode": "preview",
                    "would_change": False,
                    "proposed_global_changes": {},
                    "persistent_writes": [],
                    "allocator": dict(_ALLOC_NOOP),
                }
            )
            return out

        policy = SelectionPolicy.parse(config.policy)
        if bindings:
            result = bind(
                snap,
                policy,
                bindings,
                static_bindings=_chain_assignments(chain),
                profile_lanes=_profile_lanes(path),
            )
        else:
            result = BindResult(
                scan_id=snap.scan_id,
                schema_version=snap.schema_version,
            )
        alloc_report = (
            _apply_allocator(snap, config, result)
            if allocator_on
            else dict(_ALLOC_NOOP)
        )

        proposed: dict[str, dict[str, Any]] = {}
        current = _chain_assignments(chain)
        for assignment_id, binding in result.global_tiers.items():
            existing = current.get(assignment_id)
            if existing is None:
                continue
            before = {
                "model": existing.model,
                "provider": existing.provider,
                "base_url": existing.base_url,
                "cascade": list(existing.cascade),
            }
            after = _binding_to_assignment_updates(binding)
            if before != after:
                proposed[assignment_id] = {"before": before, "after": after}

        out = _summary(enabled=True, changed=False, result=result)
        out.update(
            {
                "mode": "preview",
                "would_change": bool(proposed or result.overlay),
                "proposed_global_changes": proposed,
                "persistent_writes": [],
                "allocator": alloc_report,
            }
        )
        return out


def _known_metric(
    *,
    summary: str,
    evidence_ref: str,
    numeric_value: float | None = None,
    unit: str | None = None,
    items: tuple[str, ...] = (),
) -> MetricEvidence:
    return MetricEvidence(
        status="known",
        summary=summary,
        numeric_value=numeric_value,
        unit=unit,
        items=items,
        evidence_refs=(evidence_ref,),
    )


def _unknown_metric(summary: str, evidence_ref: str) -> MetricEvidence:
    return MetricEvidence(
        status="unknown",
        summary=summary,
        evidence_refs=(evidence_ref,),
    )


def _candidate_for_route(
    snap: model_scan_snapshot.RoutingSnapshot,
    *,
    api_model: str,
    provider: str,
    role: str,
) -> tuple[model_scan_snapshot.Candidate | None, str]:
    """Find exact candidate evidence; never infer identity from a display name."""
    selections = (
        ((role, snap.slots[role]),)
        if role and role in snap.slots
        else tuple(sorted(snap.slots.items()))
    )
    matches: list[tuple[str, model_scan_snapshot.Candidate]] = []
    for role_id, selection in selections:
        candidates = list(selection.candidates)
        if selection.best is not None:
            candidates.append(selection.best)
        for candidate in candidates:
            if candidate.api_model != api_model:
                continue
            if provider and candidate.provider != provider:
                continue
            matches.append((role_id, candidate))

    unique: dict[tuple[str, str, str], tuple[str, model_scan_snapshot.Candidate]] = {}
    for role_id, candidate in matches:
        unique[(candidate.api_model, candidate.provider, candidate.model_id)] = (
            role_id,
            candidate,
        )
    if len(unique) != 1:
        absence = (
            f"absence:routing-snapshot:scan-{snap.scan_id}:"
            f"exact-candidate:{provider or 'unknown-provider'}:{api_model}"
        )
        return None, absence
    role_id, candidate = next(iter(unique.values()))
    return (
        candidate,
        f"routing-snapshot:scan-{snap.scan_id}:slot-{role_id}:candidate-{candidate.model_id}",
    )


def _route_facts(
    snap: model_scan_snapshot.RoutingSnapshot,
    *,
    model: str,
    provider: str,
    base_url: str,
    cascade: tuple[str, ...],
    role: str,
    route_ref: str,
) -> RouteFacts:
    candidate, candidate_ref = _candidate_for_route(
        snap,
        api_model=model,
        provider=provider,
        role=role,
    )
    if candidate is None:
        compatibility = _unknown_metric(
            "no exact candidate evidence for route compatibility",
            candidate_ref,
        )
        cost = _unknown_metric(
            "no exact candidate evidence for blended cost",
            candidate_ref,
        )
        capability = _unknown_metric(
            "no exact candidate evidence for capability",
            candidate_ref,
        )
    else:
        compatibility_items = [
            f"tool_calling={'supported' if candidate.has_tools else 'unsupported'}",
            f"vision={'supported' if candidate.has_vision else 'unsupported'}",
        ]
        provider_health = snap.provider_health.get(candidate.provider)
        if provider_health:
            compatibility_items.append(f"provider_health={provider_health}")
        compatibility = _known_metric(
            summary="exact callable compatibility evidence",
            evidence_ref=candidate_ref,
            items=tuple(compatibility_items),
        )
        if candidate.price_blended is None:
            cost = _unknown_metric(
                "snapshot publishes no blended cost for the exact candidate",
                candidate_ref,
            )
        else:
            cost = _known_metric(
                summary="snapshot blended price",
                evidence_ref=candidate_ref,
                numeric_value=candidate.price_blended,
                unit="usd_per_million_blended",
            )
        capability_items = [
            f"tier={candidate.tier}",
            f"tool_calling={'supported' if candidate.has_tools else 'unsupported'}",
            f"vision={'supported' if candidate.has_vision else 'unsupported'}",
        ]
        capability = _known_metric(
            summary="snapshot fitness and feature evidence",
            evidence_ref=candidate_ref,
            numeric_value=candidate.fitness,
            unit="fitness",
            items=tuple(capability_items),
        )

    quota_data = snap.provider_quota.get(provider)
    remaining = quota_data.get("remaining_fraction") if isinstance(quota_data, dict) else None
    if isinstance(remaining, (int, float)) and not isinstance(remaining, bool):
        quota_items = []
        for name in ("reset_at", "unit", "source"):
            value = quota_data.get(name)
            if value is not None:
                quota_items.append(f"{name}={value}")
        quota = _known_metric(
            summary="provider quota remaining fraction",
            evidence_ref=f"routing-snapshot:scan-{snap.scan_id}:provider-quota:{provider}",
            numeric_value=float(remaining),
            unit="remaining_fraction",
            items=tuple(quota_items),
        )
    else:
        quota = _unknown_metric(
            "snapshot publishes no numeric remaining fraction for this provider",
            f"absence:routing-snapshot:scan-{snap.scan_id}:provider-quota:{provider or 'unknown'}",
        )

    dimensions = {
        "compatibility": compatibility,
        "privacy": _unknown_metric(
            "routing snapshot does not publish privacy compatibility evidence",
            "absence:routing-snapshot:privacy",
        ),
        "quota": quota,
        "cost": cost,
        "latency": _unknown_metric(
            "routing snapshot does not publish latency evidence",
            "absence:routing-snapshot:latency",
        ),
        "capability": capability,
        "fallbacks": _known_metric(
            summary=f"{len(cascade)} configured fallback(s)",
            evidence_ref=route_ref,
            items=cascade,
        ),
    }
    return RouteFacts(
        model_id=model,
        provider_id=provider,
        base_url=_sanitized_base_url(base_url),
        fallbacks=cascade,
        dimensions=dimensions,
    )


def _sanitized_base_url(value: str) -> str:
    """Retain endpoint identity while removing userinfo, query secrets, and fragments."""
    if not value:
        return ""
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.hostname:
        return "[redacted-invalid-url]"
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    try:
        port = f":{parsed.port}" if parsed.port is not None else ""
    except ValueError:
        return "[redacted-invalid-url]"
    return urlunsplit((parsed.scheme, f"{host}{port}", parsed.path, "", ""))


def shadow_model_scan(*, profiles_path: Path | None = None) -> dict[str, Any]:
    """Compare preview-selected and active global routes without executing the preview."""
    with non_persisting_preview():
        preview = preview_model_scan(profiles_path=profiles_path)
        response: dict[str, Any] = {
            "mode": "shadow",
            "enabled": preview["enabled"],
            "scan_id": preview["scan_id"],
            "schema_version": preview["schema_version"],
            "execution_route": "active",
            "execution_changed": False,
            "would_change": preview["would_change"],
            "persistent_writes": [],
            "comparisons": [],
            "error": preview["error"],
        }
        if not preview["enabled"] or preview["error"] or preview["scan_id"] is None:
            return response

        live_chain = get_chain()
        snap = _load_snapshot(live_chain.model_scan)
        if snap is None:
            response["error"] = "snapshot became unavailable during shadow comparison"
            return response

        current = _chain_assignments(live_chain)
        observed_at = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        comparisons = []
        for assignment_id, selected in sorted(preview["global_tiers"].items()):
            active = current.get(assignment_id)
            if active is None:
                continue
            active_ref = f"active-routing:assignment:{assignment_id}"
            shadow_ref = (
                f"preview-routing:scan-{snap.scan_id}:assignment:{assignment_id}"
            )
            active_facts = _route_facts(
                snap,
                model=active.model,
                provider=active.provider,
                base_url=active.base_url,
                cascade=tuple(active.cascade),
                role="",
                route_ref=active_ref,
            )
            shadow_facts = _route_facts(
                snap,
                model=str(selected["api_model"]),
                provider=str(selected["provider"]),
                base_url=str(selected["base_url"]),
                cascade=tuple(selected["cascade"]),
                role=str(selected["role"]),
                route_ref=shadow_ref,
            )
            comparisons.append(
                build_comparison(
                    observed_at=observed_at,
                    assignment_id=assignment_id,
                    source_scan_id=snap.scan_id,
                    source_schema_version=snap.schema_version,
                    active_route=active_facts,
                    shadow_route=shadow_facts,
                    evidence_refs=(active_ref, shadow_ref),
                )
            )
        response["comparisons"] = comparisons
        return response


def create_model_scan_canary(
    *,
    ttl_s: int = 900,
    profiles_path: Path | None = None,
) -> dict[str, Any]:
    """Create an in-memory canary from shadow evidence without sending traffic."""
    shadow = shadow_model_scan(profiles_path=profiles_path)
    if shadow["error"]:
        raise ValueError(f"cannot create canary: {shadow['error']}")
    if not shadow["comparisons"]:
        raise ValueError("cannot create canary: no selected global bindings")

    bindings: dict[str, dict[str, Any]] = {}
    comparison_ids: list[str] = []
    for comparison in shadow["comparisons"]:
        route = comparison["shadow_route"]
        assignment_id = comparison["assignment_id"]
        bindings[assignment_id] = {
            "api_model": route["model_id"],
            "provider": route["provider_id"],
            "base_url": route["base_url"],
            "cascade": list(route["fallbacks"]),
            "role": assignment_id,
        }
        comparison_ids.append(comparison["comparison_id"])

    from src.core.profiles import list_ephemeral_profiles, register_canary_profile

    profile = register_canary_profile(
        bindings=bindings,
        source_comparison_ids=tuple(comparison_ids),
        ttl_s=ttl_s,
    )
    metadata = list_ephemeral_profiles()[profile.name]
    return {
        "mode": "canary",
        "profile_id": profile.name,
        "profile_kind": profile.kind,
        "url_prefix": f"/p/{profile.name}",
        "ttl_s": ttl_s,
        "expires_at": metadata["expires_at"],
        "source_comparison_ids": comparison_ids,
        "bindings": bindings,
        "traffic_sent": False,
        "active_binding_changed": False,
        "persistent_writes": [],
    }


def reload_model_scan(*, profiles_path: Path | None = None) -> dict[str, Any]:
    """Reload model-scan bindings into the request-time in-memory overlay.

    Disabled config is a clean no-op. Invalid snapshots leave the previous good
    in-memory overlay in place. Static assignments, environment values, and
    profile files are never rewritten. When ALLOCATOR_ENABLED + session_profiles
    are set, the F18 allocator also writes per-profile in-memory overlays.
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

    alloc_report = _apply_allocator(snap, config, result) if allocator_on else dict(_ALLOC_NOOP)

    with _LOCK:
        changed = _ACTIVE_BINDING != result
        _ACTIVE_BINDING = result
        _ACTIVE_ALLOCATION = alloc_report

    out = _summary(enabled=True, changed=changed, result=result)
    out["activation"] = "in_memory_overlay"
    out["persistent_writes"] = []
    out["allocator"] = alloc_report
    return out
