"""Runtime quota-meter assembly for the F18 allocator (best-effort, never raises).

Collapses live/static provider quota *fractions* (the same sources rotation.py uses) into the
absolute QuotaMeter list `allocator.allocate()` consumes. Provider-level only; finer per-model
header meters come from `quota_adapters.parse_ratelimit_headers` when a live header fetch is wired.

A remaining_fraction is turned into a meter against a nominal per-window call budget
(`quota_nominal_calls`) so scarcity is proportional and the satisfice/maximize split has teeth.
With no quota data the result is empty and the allocator degrades to pure floor+fitness routing.
"""
from __future__ import annotations

from typing import Sequence

from src.core.quota_sources import (
    QuotaMeter,
    QuotaSample,
    StaticQuotaSource,
    merge_quota_samples,
)


def _config_sources(config) -> list:
    """Operator-pinned provider fractions from `model_scan.static_quota` (lowest precedence)."""
    static = getattr(config, "static_quota", {}) or {}
    if not static:
        return []
    return [StaticQuotaSource("static", {str(k): float(v) for k, v in static.items()})]


def _default_live_sources() -> list:
    """The live fraction sources rotation already trusts, plus the live header-fed QuotaCache.
    Imported lazily so tests stay offline."""
    from src.core.quota_sources import CcusageSource, TokscaleSQLiteSource
    from src.core.quota_live import QuotaCacheSource

    return [TokscaleSQLiteSource(), CcusageSource(), QuotaCacheSource()]


def collect_meters(config, *, sources: Sequence | None = None) -> list[QuotaMeter]:
    """Assemble provider-level QuotaMeters from config + quota sources.

    `sources=None` uses the default live sources; pass an explicit list (incl. `[]`) to isolate.
    Any source that raises is skipped — quota assembly must never break a reload.
    """
    nominal = float(getattr(config, "quota_nominal_calls", 1000.0) or 1000.0)
    all_sources = _config_sources(config)
    all_sources.extend(sources if sources is not None else _default_live_sources())

    samples: list[QuotaSample] = []
    for src in all_sources:
        try:
            samples.extend(src.samples() or [])
        except Exception:
            continue  # a flaky provider source must not abort allocation

    meters: list[QuotaMeter] = []
    for provider, sample in merge_quota_samples(samples).items():
        frac = max(0.0, min(1.0, sample.remaining_fraction))
        meters.append(
            QuotaMeter(
                id=f"{provider}:calls:runtime",
                provider=provider,
                unit="calls",
                window_seconds=0,
                limit=nominal,
                remaining=frac * nominal,
                reset_at=sample.reset_at,
                source=sample.source or "runtime",
                observed_at=sample.observed_at,
            )
        )
    return meters
