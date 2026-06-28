"""Live quota layer (F06): stateful cache fed passively from real response headers, plus an
active poll for providers with a dedicated quota endpoint.

Design (verified empirically): header providers (Groq/Cerebras/Claude/...) expose rate-limit
ONLY on actual completion responses - GET /models returns none - so the gateway records those
headers here after each request, costing zero extra calls. Providers with a quota endpoint
(OpenRouter /auth/key) are polled actively. The allocator/rotation read `samples()` / `meters()`.
"""
from __future__ import annotations

import time
from typing import Callable, Mapping, Sequence

from src.core.quota_sources import QuotaMeter, QuotaSample, meters_to_samples
from src.core.quota_adapters import parse_ratelimit_headers, parse_openrouter_auth_key


def _group_by_provider(meters: Sequence[QuotaMeter]) -> dict[str, list[QuotaMeter]]:
    out: dict[str, list[QuotaMeter]] = {}
    for m in meters:
        out.setdefault(m.provider, []).append(m)
    return out


class QuotaCache:
    """In-memory latest-known quota per provider. Thread-safety: callers should guard if writing
    from multiple threads (single dict assignment per provider is atomic in CPython)."""

    def __init__(self) -> None:
        self._by_provider: dict[str, list[QuotaMeter]] = {}

    def record_headers(self, provider: str, headers: Mapping[str, str], *, observed_at: float | None = None) -> list[QuotaMeter]:
        """Passive capture from a real response's headers. No-op (keeps prior) if none parse."""
        ms = parse_ratelimit_headers(provider, headers, observed_at=observed_at or time.time())
        if ms:
            self._by_provider[provider] = ms
        return ms

    def record_meters(self, meters: Sequence[QuotaMeter]) -> None:
        """Write meters from an active poll (e.g. OpenRouter), grouped by provider."""
        for prov, group in _group_by_provider(meters).items():
            self._by_provider[prov] = group

    def meters(self) -> list[QuotaMeter]:
        return [m for group in self._by_provider.values() for m in group]

    def samples(self) -> dict[str, QuotaSample]:
        """Collapsed provider-level samples (tightest meter wins) for rotation.provider_drained."""
        return meters_to_samples(self.meters())


# http_get(url, headers, timeout) -> (status:int, json_body:dict)
HttpGet = Callable[[str, dict, float], tuple[int, object]]


def fetch_openrouter_meters(api_key: str, *, http_get: HttpGet | None = None, observed_at: float = 0.0) -> list[QuotaMeter]:
    """Active poll of OpenRouter GET /api/v1/auth/key -> meters. Returns [] on non-200, bad body,
    or an unmetered key (limit=null). http_get is injectable for offline tests."""
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {api_key}"}

    if http_get is None:
        def http_get(url, headers, timeout):  # noqa: A001 (shadow ok, local)
            import httpx

            r = httpx.get(url, headers=headers, timeout=timeout)
            body = {}
            if r.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = r.json()
                except Exception:
                    body = {}
            return r.status_code, body

    try:
        status, body = http_get(url, headers, 15.0)
    except Exception:
        return []
    if status != 200 or not isinstance(body, dict):
        return []
    return parse_openrouter_auth_key(body, observed_at=observed_at)
