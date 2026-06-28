"""F06 live quota layer: passive QuotaCache + active OpenRouter poll (offline, injected)."""
from src.core.quota_live import QuotaCache, fetch_openrouter_meters

GROQ_HDR = {  # real shape (Groq, per-minute)
    "x-ratelimit-limit-requests": "1000", "x-ratelimit-remaining-requests": "999",
    "x-ratelimit-limit-tokens": "8000", "x-ratelimit-remaining-tokens": "7927",
}
CEREBRAS_HDR = {  # real shape (windowed); requests/day 100/2400 is tightest at ~0.0417
    "x-ratelimit-limit-requests-day": "2400", "x-ratelimit-remaining-requests-day": "100",
    "x-ratelimit-limit-tokens-day": "1000000", "x-ratelimit-remaining-tokens-day": "999999",
}


def test_cache_passive_capture_multi_provider():
    c = QuotaCache()
    c.record_headers("groq", GROQ_HDR)
    c.record_headers("cerebras", CEREBRAS_HDR)
    samples = c.samples()
    assert set(samples) == {"groq", "cerebras"}
    # tightest meter wins: groq tokens 7927/8000 < requests 999/1000
    assert abs(samples["groq"].remaining_fraction - 7927 / 8000) < 1e-9
    assert abs(samples["cerebras"].remaining_fraction - 100 / 2400) < 1e-9


def test_cache_ignores_headers_without_ratelimit():
    c = QuotaCache()
    assert c.record_headers("x", {"content-type": "application/json"}) == []
    assert c.samples() == {}


def test_cache_record_meters_from_poll():
    c = QuotaCache()
    c.record_meters(fetch_openrouter_meters(
        "k", http_get=lambda u, h, t: (200, {"data": {"limit": 50, "limit_remaining": 40}})))
    assert "openrouter" in c.samples()
    assert c.samples()["openrouter"].remaining_fraction == 0.8


def test_global_cache_singleton():
    from src.core.quota_live import get_quota_cache
    assert get_quota_cache() is get_quota_cache()
    get_quota_cache().record_headers("groq", GROQ_HDR)
    assert "groq" in get_quota_cache().samples()


def test_quota_cache_source_feeds_collect_meters():
    # closes the F06->F18 loop: live headers -> QuotaCache -> QuotaCacheSource -> collect_meters
    from src.core.quota_live import get_quota_cache, QuotaCacheSource
    from src.core.quota_runtime import collect_meters
    get_quota_cache().record_headers("groq", GROQ_HDR)

    class _Cfg:
        pass

    meters = collect_meters(_Cfg(), sources=[QuotaCacheSource()])
    assert any(m.provider == "groq" for m in meters)


def test_fetch_openrouter_meters_cases():
    ok = fetch_openrouter_meters("k", http_get=lambda u, h, t: (200, {"data": {"limit": 50, "limit_remaining": 40}}))
    assert len(ok) == 1 and ok[0].remaining == 40.0
    # unmetered key
    assert fetch_openrouter_meters("k", http_get=lambda u, h, t: (200, {"data": {"limit": None}})) == []
    # non-200
    assert fetch_openrouter_meters("k", http_get=lambda u, h, t: (429, {})) == []
    # transport error -> []
    assert fetch_openrouter_meters("k", http_get=lambda u, h, t: (_ for _ in ()).throw(RuntimeError("net"))) == []
