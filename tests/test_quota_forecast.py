"""CG-T087 — quota forecasting shadow mode: distinct meters, reserves, error."""

from __future__ import annotations

from datetime import datetime, timezone

from src.core.quota_sources import QuotaMeter
from src.services.orchestration.quota_forecast import (
    HARD_FLOOR_FRACTION,
    forecast,
    measure_forecast_error,
    meter_class,
)


def _meter(provider: str, source: str, remaining: float, age_s: float = 60.0, confidence: float = 1.0):
    return QuotaMeter(
        id=f"{provider}:{source}",
        provider=provider,
        unit="calls",
        window_seconds=86400,
        limit=100.0,
        remaining=remaining * 100.0,
        source=source,
        observed_at=datetime.now(timezone.utc).timestamp() - age_s,
        confidence=confidence,
    )


def test_exact_and_estimated_meter_classes_stay_distinct():
    assert meter_class("header") == "exact"
    assert meter_class("openrouter-current-key") == "exact"
    assert meter_class("provider_account") == "exact"
    assert meter_class("tokscale") == "estimated"
    assert meter_class("ccusage") == "estimated"

    result = forecast(
        [
            _meter("openrouter", "openrouter-current-key", 0.5),
            _meter("openrouter", "tokscale", 0.05, confidence=0.4),
        ]
    )
    # the estimated meter's 5% never contaminates the exact class
    assert result.exact is not None
    assert result.exact.providers == ("openrouter",)
    assert result.exact.meter_count == 1
    assert result.exact.tightest_remaining_fraction == 0.5
    assert result.estimated is not None
    assert result.estimated.tightest_remaining_fraction == 0.05
    # the authoritative (exact) class decides the advisory
    assert result.advisory == "accelerate"


def test_estimated_only_class_still_advises_but_marks_low_confidence():
    result = forecast([_meter("groq", "tokscale", 0.8, confidence=0.3)])
    assert result.exact is None
    assert result.estimated is not None
    assert result.estimated.confidence < 1.0
    assert result.advisory in {"accelerate", "hold"}


def test_reserve_holds_below_reserve_fraction():
    result = forecast([_meter("openrouter", "header", 0.15)], reserve_fraction=0.2)
    assert result.reserve_holds is False
    assert result.advisory == "hold"
    assert result.reserve_holds is False


def test_hard_filter_blocks_below_the_floor():
    result = forecast([_meter("openrouter", "header", HARD_FLOOR_FRACTION / 2)])
    assert result.hard_filter_blocks is True
    assert result.advisory == "blocked"


def test_forecast_error_is_measured():
    point = measure_forecast_error(0.42, 0.40)
    assert point["absolute_error"] == 0.02
    assert point["synthetic_work_generated"] is False


def test_no_meters_means_hold_and_no_synthetic_work():
    result = forecast([])
    assert result.advisory == "hold"
    assert result.synthetic_work_generated is False
    assert result.mutations == []
    assert result.exact is None and result.estimated is None


def test_forecast_is_shadow_only():
    # the module never touches routing, dispatch, or spending surfaces
    import inspect

    from src.services.orchestration import quota_forecast as m

    source = inspect.getsource(m)
    for forbidden in ("reload_model_scan", "promote", "dispatch", "submit", "requests.post"):
        assert forbidden not in source, forbidden
