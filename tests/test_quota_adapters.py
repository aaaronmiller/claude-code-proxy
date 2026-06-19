"""F06: header/payload quota parsers are pure and offline-testable with fixtures.
See ai-gateway/plan/features/F06 + 04-DATA-CONTRACTS.md."""
from src.core.quota_adapters import (
    parse_ratelimit_headers,
    parse_openrouter_auth_key,
    parse_reset_seconds,
    HeaderQuotaSource,
)

# Real headers captured from a live Groq gpt-oss-120b call (L1 verification).
REAL_GROQ_HEADERS = {
    "x-ratelimit-limit-requests": "1000",
    "x-ratelimit-limit-tokens": "8000",
    "x-ratelimit-remaining-requests": "999",
    "x-ratelimit-remaining-tokens": "7927",
    "x-ratelimit-reset-requests": "1m26.4s",
    "x-ratelimit-reset-tokens": "547ms",
}


def _by_unit(meters):
    return {m.unit: m for m in meters}


def test_openai_style_headers():
    h = {
        "x-ratelimit-limit-requests": "10000",
        "x-ratelimit-remaining-requests": "9500",
        "x-ratelimit-limit-tokens": "1000000",
        "x-ratelimit-remaining-tokens": "800000",
        "x-ratelimit-reset-requests": "60s",
    }
    meters = _by_unit(parse_ratelimit_headers("groq", h))
    assert meters["calls"].limit == 10000 and meters["calls"].remaining == 9500
    assert meters["calls"].remaining_fraction == 0.95
    assert meters["tokens"].remaining_fraction == 0.8
    assert meters["calls"].reset_at == "60s"
    assert meters["calls"].source == "header"


def test_anthropic_style_headers():
    h = {
        "anthropic-ratelimit-requests-limit": "1000",
        "anthropic-ratelimit-requests-remaining": "50",
        "anthropic-ratelimit-tokens-limit": "100000",
        "anthropic-ratelimit-tokens-remaining": "100",
    }
    meters = _by_unit(parse_ratelimit_headers("claude_code", h))
    assert meters["calls"].remaining_fraction == 0.05
    assert meters["tokens"].remaining_fraction == 0.001
    assert meters["calls"].id == "claude_code:calls:anthropic-ratelimit"


def test_missing_fields_graceful():
    # only a limit, no remaining -> no meter (never guesses)
    assert parse_ratelimit_headers("x", {"x-ratelimit-limit-requests": "100"}) == []
    assert parse_ratelimit_headers("x", {}) == []


def test_header_keys_case_insensitive():
    h = {"X-RateLimit-Limit-Requests": "10", "X-RateLimit-Remaining-Requests": "3"}
    meters = parse_ratelimit_headers("groq", h)
    assert len(meters) == 1 and meters[0].remaining == 3


def test_openrouter_auth_key():
    meters = parse_openrouter_auth_key({"data": {"limit": 50, "usage": 12.5}})
    assert len(meters) == 1
    assert meters[0].unit == "dollars"
    assert meters[0].remaining == 37.5
    assert meters[0].source == "poll"
    # unmetered key (limit None) -> no meter (verified live: real key returns limit=null)
    assert parse_openrouter_auth_key({"data": {"limit": None, "usage": 5}}) == []
    # real API shape: prefer explicit limit_remaining + carry limit_reset
    m = parse_openrouter_auth_key({"data": {"limit": 50, "usage": 12.5,
                                            "limit_remaining": 40, "limit_reset": "monthly"}})
    assert m[0].remaining == 40.0 and m[0].reset_at == "monthly"  # uses limit_remaining, not 37.5


# Real headers captured from a live Cerebras gpt-oss-120b call (windowed family).
REAL_CEREBRAS_HEADERS = {
    "x-ratelimit-limit-requests-minute": "5", "x-ratelimit-remaining-requests-minute": "4",
    "x-ratelimit-limit-requests-hour": "150", "x-ratelimit-remaining-requests-hour": "149",
    "x-ratelimit-limit-requests-day": "2400", "x-ratelimit-remaining-requests-day": "2399",
    "x-ratelimit-limit-tokens-minute": "30000", "x-ratelimit-remaining-tokens-minute": "29999",
    "x-ratelimit-limit-tokens-hour": "1000000", "x-ratelimit-remaining-tokens-hour": "999999",
    "x-ratelimit-limit-tokens-day": "1000000", "x-ratelimit-remaining-tokens-day": "999999",
}


def test_parses_real_cerebras_windowed_headers():
    meters = {m.id: m for m in parse_ratelimit_headers("cerebras", REAL_CEREBRAS_HEADERS)}
    assert len(meters) == 6  # calls + tokens x minute/hour/day
    day_calls = meters["cerebras:calls:x-ratelimit:day"]
    assert day_calls.limit == 2400 and day_calls.remaining == 2399 and day_calls.window_seconds == 86400
    assert meters["cerebras:tokens:x-ratelimit:minute"].window_seconds == 60
    # tightest meter (requests/minute 4/5=0.8) drives the collapsed provider sample
    from src.core.quota_sources import meters_to_samples
    samples = meters_to_samples(meters.values())
    assert abs(samples["cerebras"].remaining_fraction - 0.8) < 1e-9


def test_parses_real_groq_headers():
    meters = {m.unit: m for m in parse_ratelimit_headers("groq", REAL_GROQ_HEADERS)}
    assert meters["calls"].remaining == 999 and meters["calls"].limit == 1000
    assert abs(meters["tokens"].remaining_fraction - 7927 / 8000) < 1e-9


def test_header_quota_source_injected_fetcher():
    src = HeaderQuotaSource("groq", "groq", lambda: REAL_GROQ_HEADERS)
    meters = src.meters()
    assert {m.unit for m in meters} == {"calls", "tokens"}
    # never raises into caller
    boom = HeaderQuotaSource("x", "x", lambda: (_ for _ in ()).throw(RuntimeError("net")))
    assert boom.meters() == []


def test_parse_reset_seconds():
    assert abs(parse_reset_seconds("1m26.4s") - 86.4) < 1e-6   # real Groq value
    assert abs(parse_reset_seconds("547ms") - 0.547) < 1e-6
    assert parse_reset_seconds("5h") == 18000
    assert parse_reset_seconds("60") == 60
    assert parse_reset_seconds("") is None
    assert parse_reset_seconds("garbage") is None
