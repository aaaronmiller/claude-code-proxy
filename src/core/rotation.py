"""Quota-aware model rotation helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, Mapping

from src.core.model_scan_binder import ResolvedBinding
from src.core.quota_sources import QuotaSample


@dataclass
class RotationState:
    cooldown_until: dict[str, float]


def _provider(model: str, fallback: str = "") -> str:
    if "/" in model:
        return model.split("/", 1)[0].lower()
    return fallback.lower()


def _is_free(binding: ResolvedBinding) -> bool:
    return ":free" in binding.api_model or binding.api_model.endswith(":cloud")


def provider_drained(provider: str, quotas: Mapping[str, QuotaSample], threshold: float = 0.05) -> bool:
    sample = quotas.get(provider.lower())
    return bool(sample and sample.remaining_fraction <= threshold)


def choose_binding(
    primary: ResolvedBinding,
    fallbacks: Iterable[ResolvedBinding],
    *,
    lane: str,
    quotas: Mapping[str, QuotaSample],
    free_floor: ResolvedBinding | None = None,
    state: RotationState | None = None,
    cooldown_s: int = 120,
    now: float | None = None,
) -> ResolvedBinding:
    """Choose a binding under lane/quota constraints."""
    current = now if now is not None else time.time()
    state = state or RotationState(cooldown_until={})
    candidates = [primary] + list(fallbacks)
    if lane == "standby":
        free = [c for c in candidates if _is_free(c)]
        return free[0] if free else (free_floor or primary)

    for binding in candidates:
        provider = binding.provider or _provider(binding.api_model)
        if state.cooldown_until.get(binding.api_model, 0) > current:
            continue
        if not provider_drained(provider, quotas):
            return binding
        state.cooldown_until[binding.api_model] = current + cooldown_s
    return free_floor or primary


def record_rate_limit(binding: ResolvedBinding, state: RotationState, cooldown_s: int = 120) -> None:
    state.cooldown_until[binding.api_model] = time.time() + cooldown_s
