"""S1-06: multi-dimensional QuotaMeter is additive and collapses back to the
provider-level QuotaSample that rotation consumes. See ai-gateway/plan/04-DATA-CONTRACTS.md."""
from src.core.quota_sources import (
    QuotaMeter,
    StaticQuotaMeterSource,
    meters_to_samples,
)
from src.core import rotation


def _m(provider, unit, limit, remaining, window=86400, model=None):
    return QuotaMeter(
        id=f"{provider}:{unit}:{window}:{model or 'provider'}",
        provider=provider, unit=unit, window_seconds=window,
        limit=limit, remaining=remaining,
        scope="provider_model" if model else "provider", model=model,
    )


def test_remaining_fraction_math():
    assert _m("groq", "calls", 0, 0).remaining_fraction == 1.0      # no limit -> unconstrained
    assert _m("groq", "calls", 10000, 5000).remaining_fraction == 0.5
    assert _m("groq", "calls", 100, 250).remaining_fraction == 1.0  # clamped high
    assert _m("groq", "calls", 100, -5).remaining_fraction == 0.0   # clamped low


def test_collapse_takes_tightest_meter_per_provider():
    metas = [
        _m("groq", "tokens", 1_000_000, 900_000, window=18000),  # 0.9
        _m("groq", "calls", 10000, 500, model="qwen3-32b"),       # 0.05 (tightest)
        _m("ollama", "tokens", 1000, 800),                        # 0.8
    ]
    samples = meters_to_samples(metas)
    assert set(samples) == {"groq", "ollama"}
    assert samples["groq"].remaining_fraction == 0.05   # tightest wins
    assert samples["ollama"].remaining_fraction == 0.8


def test_collapsed_samples_drive_existing_rotation():
    metas = [_m("groq", "calls", 10000, 200, model="qwen3-32b")]  # 0.02 remaining
    samples = meters_to_samples(metas)
    # existing rotation.provider_drained must see the provider as drained
    assert rotation.provider_drained("groq", samples, threshold=0.15) is True
    assert rotation.provider_drained("groq", samples, threshold=0.01) is False


def test_static_meter_source():
    src = StaticQuotaMeterSource("seed", [_m("groq", "calls", 10, 5)])
    assert src.name == "seed"
    assert len(src.meters()) == 1
