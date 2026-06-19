"""Wire the F03/F11 probe (`src.services.probe`) to the live allocation.

Builds probe targets from the active model-scan overlay (the per-profile/role picks the request
path routes to) and runs the minimal latency/availability probe over them. Pure plumbing: both the
HTTP call (`http_post`) and credential resolution (`resolve_creds`) are injected, so the whole
module is offline-testable. The endpoint layer supplies real httpx + the provider registry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.services.probe import probe_model


@dataclass(frozen=True)
class ProbeTarget:
    profile: str
    role: str
    provider: str
    base_url: str  # advisory; "" means resolve from the provider registry
    api_model: str


def targets_from_binding(binding) -> list[ProbeTarget]:
    """Flatten an active BindResult.overlay into one probe target per (profile, role)."""
    out: list[ProbeTarget] = []
    if binding is None:
        return out
    for profile, roles in binding.overlay.items():
        for role, rb in roles.items():
            out.append(ProbeTarget(profile, role, rb.provider, rb.base_url or "", rb.api_model))
    return out


# resolve_creds(provider, advisory_base_url) -> (base_url, api_key)
ResolveCreds = Callable[[str, str], tuple[str, str]]


def probe_targets(
    targets: list[ProbeTarget],
    resolve_creds: ResolveCreds,
    *,
    http_post=None,
    timeout: float = 20.0,
) -> list[dict[str, Any]]:
    """Probe each target. A target with no resolvable endpoint is reported, not probed, so a
    misconfigured provider never raises. Returns JSON-friendly dicts."""
    results: list[dict[str, Any]] = []
    for t in targets:
        base_url, api_key = resolve_creds(t.provider, t.base_url)
        if not base_url:
            results.append({
                "profile": t.profile, "role": t.role, "provider": t.provider,
                "model": t.api_model, "ok": False, "status": 0,
                "latency_s": 0.0, "tokens_out": 0, "tokens_per_s": None,
                "error_class": "no_endpoint",
            })
            continue
        r = probe_model(
            t.provider, base_url, t.api_model, api_key or "",
            timeout=timeout, http_post=http_post,
        )
        results.append({
            "profile": t.profile, "role": t.role, "provider": r.provider,
            "model": r.model, "ok": r.ok, "status": r.status,
            "latency_s": r.latency_s, "tokens_out": r.tokens_out,
            "tokens_per_s": r.tokens_per_s, "error_class": r.error_class,
        })
    return results
