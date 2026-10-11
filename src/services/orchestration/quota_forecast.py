"""Useful-work quota forecasting in shadow mode (CG-T087).

Exact (provider-authoritative) and estimated (local) meters remain distinct
forever; reserves and hard filters hold before any acceleration is advised;
forecast error is measured against observed outcomes; and no synthetic work is
generated to feed the forecast. This module advises only — it never spends,
schedules, or mutates routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from src.core.quota_sources import PRECEDENCE, QuotaMeter

FORECAST_SCHEMA_VERSION = "1.0.0"

#: Provider-authoritative sources rank at/above this precedence rank.
EXACT_PRECEDENCE_FLOOR = 900

#: Hard filter: below this remaining fraction nothing may be accelerated.
HARD_FLOOR_FRACTION = 0.05


def meter_class(source: str) -> str:
    """'exact' for provider-authoritative meters, 'estimated' otherwise."""
    rank = PRECEDENCE.get(source, 0)
    return "exact" if rank >= EXACT_PRECEDENCE_FLOOR else "estimated"


@dataclass(frozen=True)
class ClassForecast:
    meter_class: str
    providers: tuple[str, ...]
    tightest_remaining_fraction: float
    projected_remaining_fraction: float
    confidence: float
    meter_count: int


@dataclass(frozen=True)
class ForecastResult:
    schema_version: str
    generated_at: str
    exact: ClassForecast | None
    estimated: ClassForecast | None
    reserve_fraction: float
    reserve_holds: bool
    hard_filter_blocks: bool
    advisory: str                 # "accelerate" | "hold" | "blocked"
    synthetic_work_generated: bool
    mutations: list[str]


def _project_class(
    meters: list[QuotaMeter], window_s: float, now_ts: float
) -> ClassForecast | None:
    if not meters:
        return None
    tightest = min(m.remaining_fraction for m in meters)
    confidence = sum(m.confidence for m in meters) / len(meters)
    # linear projection of the tightest meter across the forecast window.
    # A meter's remaining fraction is measured within its own window; the
    # conservative uniform-drain assumption spreads the observed drain across
    # that window (bounded, no history store is read in shadow mode).
    rates: list[float] = []
    for meter in meters:
        window = max(float(meter.window_seconds) or 86400.0, 1.0)
        drained = 1.0 - meter.remaining_fraction
        rates.append(drained / window)
    drain_per_s = sum(rates) / len(rates) if rates else 0.0
    projected = max(0.0, tightest - drain_per_s * window_s)
    return ClassForecast(
        meter_class=meter_class(meters[0].source or ""),
        providers=tuple(sorted({m.provider for m in meters})),
        tightest_remaining_fraction=round(tightest, 6),
        projected_remaining_fraction=round(projected, 6),
        confidence=round(confidence, 3),
        meter_count=len(meters),
    )


def forecast(
    meters: Iterable[QuotaMeter],
    *,
    window_s: float = 3600.0,
    reserve_fraction: float = 0.2,
    now: datetime | None = None,
) -> ForecastResult:
    """Forecast per meter class without merging them."""
    now = now or datetime.now(timezone.utc)
    grouped: dict[str, list[QuotaMeter]] = {"exact": [], "estimated": []}
    for meter in meters:
        grouped[meter_class(meter.source or "")].append(meter)

    exact = _project_class(grouped["exact"], window_s, now.timestamp())
    estimated = _project_class(grouped["estimated"], window_s, now.timestamp())

    # the authoritative class decides; estimated meters may only inform
    authoritative = exact or estimated
    if authoritative is None:
        return ForecastResult(
            FORECAST_SCHEMA_VERSION,
            now.isoformat(timespec="seconds").replace("+00:00", "Z"),
            None,
            None,
            reserve_fraction,
            True,
            False,
            "hold",
            False,
            [],
        )

    projected = authoritative.projected_remaining_fraction
    tightest = authoritative.tightest_remaining_fraction
    hard_filter_blocks = tightest < HARD_FLOOR_FRACTION
    reserve_holds = tightest >= reserve_fraction
    if hard_filter_blocks:
        advisory = "blocked"
    elif reserve_holds and projected >= reserve_fraction:
        advisory = "accelerate"
    else:
        advisory = "hold"
    return ForecastResult(
        FORECAST_SCHEMA_VERSION,
        now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        exact,
        estimated,
        reserve_fraction,
        reserve_holds,
        hard_filter_blocks,
        advisory,
        False,
        [],
    )


def measure_forecast_error(
    predicted_remaining: float, actual_remaining: float
) -> dict[str, Any]:
    """Forecast error for one calibration point (0..1 fractions)."""
    error = abs(predicted_remaining - actual_remaining)
    return {
        "schema_version": FORECAST_SCHEMA_VERSION,
        "measure_kind": "forecast_error",
        "predicted_remaining": round(predicted_remaining, 6),
        "actual_remaining": round(actual_remaining, 6),
        "absolute_error": round(error, 6),
        "synthetic_work_generated": False,
    }
