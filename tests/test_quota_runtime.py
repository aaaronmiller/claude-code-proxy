"""F18 runtime quota-meter assembly: turn live/static provider quota fractions into the
QuotaMeter list the allocator consumes. Pure + offline (sources are injectable)."""
from src.core.quota_runtime import collect_meters
from src.core.quota_sources import StaticQuotaSource


class _Cfg:
    def __init__(self, static_quota=None, nominal=1000.0):
        self.static_quota = static_quota or {}
        self.quota_nominal_calls = nominal


def test_static_quota_becomes_meter():
    cfg = _Cfg(static_quota={"cerebras": 0.3, "openrouter": 1.0}, nominal=1000.0)
    meters = collect_meters(cfg, sources=[])
    by_provider = {m.provider: m for m in meters}
    assert set(by_provider) == {"cerebras", "openrouter"}
    assert by_provider["cerebras"].unit == "calls"
    assert by_provider["cerebras"].limit == 1000.0
    assert by_provider["cerebras"].remaining == 300.0   # 0.3 * nominal
    assert by_provider["openrouter"].remaining == 1000.0


def test_injected_source_merges_by_precedence():
    cfg = _Cfg(static_quota={"groq": 0.9})
    # an injected higher-precedence source should win over static for the same provider
    src = StaticQuotaSource("tokscale", {"groq": 0.1})
    meters = collect_meters(cfg, sources=[src])
    groq = [m for m in meters if m.provider == "groq"][0]
    assert groq.remaining_fraction == 0.1   # tokscale (precedence 100) beats static


def test_no_data_returns_empty_and_never_raises():
    cfg = _Cfg(static_quota={})
    assert collect_meters(cfg, sources=[]) == []


def test_broken_source_is_ignored():
    class Boom:
        name = "boom"

        def samples(self):
            raise RuntimeError("provider down")

    cfg = _Cfg(static_quota={"openrouter": 0.5})
    meters = collect_meters(cfg, sources=[Boom()])
    assert [m.provider for m in meters] == ["openrouter"]   # boom swallowed, static kept
