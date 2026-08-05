"""Live quota layer (F06): stateful cache fed passively from real response headers, plus an
active poll for providers with a dedicated quota endpoint.

Design (verified empirically): header providers (Groq/Cerebras/Claude/...) expose rate-limit
ONLY on actual completion responses - GET /models returns none - so the gateway records those
headers here after each request, costing zero extra calls. Providers with a quota endpoint
(OpenRouter /api/v1/key) are polled actively. The allocator/rotation read `samples()` / `meters()`.
"""
from __future__ import annotations

import time
from typing import Callable, Mapping, Sequence

from src.core.quota_sources import QuotaMeter, QuotaSample, meters_to_samples
from src.core.quota_adapters import parse_ratelimit_headers, parse_openrouter_current_key


OPENROUTER_CURRENT_KEY_URL = "https://openrouter.ai/api/v1/key"


def _group_by_provider(meters: Sequence[QuotaMeter]) -> dict[str, list[QuotaMeter]]:
    out: dict[str, list[QuotaMeter]] = {}
    for m in meters:
        out.setdefault(m.provider, []).append(m)
    return out


class QuotaCache:
    """In-memory latest-known quota per provider. Thread-safety: callers should guard if writing
    from multiple threads (single dict assignment per provider is atomic in CPython)."""

    def __init__(self, store=None) -> None:
        self._by_provider: dict[str, list[QuotaMeter]] = {}
        self._store = store
        if store is not None:
            self._restore()

    def record_headers(self, provider: str, headers: Mapping[str, str], *, observed_at: float | None = None) -> list[QuotaMeter]:
        """Passive capture from a real response's headers. No-op (keeps prior) if none parse."""
        ms = parse_ratelimit_headers(provider, headers, observed_at=observed_at or time.time())
        if ms:
            self.record_meters(ms)
        return ms

    def record_meters(self, meters: Sequence[QuotaMeter]) -> None:
        """Write meters from an active poll (e.g. OpenRouter), grouped by provider."""
        for prov, group in _group_by_provider(meters).items():
            self._by_provider[prov] = group
        self._persist()

    def meters(self) -> list[QuotaMeter]:
        return [m for group in self._by_provider.values() for m in group]

    def samples(self) -> dict[str, QuotaSample]:
        """Collapsed provider-level samples (tightest meter wins) for rotation.provider_drained."""
        return meters_to_samples(self.meters())

    def freshness(
        self,
        *,
        now: float | None = None,
        max_age_s: float,
    ) -> list[dict]:
        """Expose age without discarding the last-known fact."""
        current = time.time() if now is None else float(now)
        out = []
        for meter in self.meters():
            age = (
                max(0.0, current - meter.observed_at)
                if meter.observed_at > 0
                else None
            )
            out.append(
                {
                    "id": meter.id,
                    "observed_at": meter.observed_at,
                    "age_seconds": age,
                    "stale": age is None or age > max_age_s,
                }
            )
        return out

    def set_store(self, store) -> None:
        """Attach a store once and merge its last-known facts."""
        current_path = getattr(self._store, "path", None)
        if current_path == getattr(store, "path", None):
            return
        self._store = store
        self._restore()

    def _restore(self) -> None:
        try:
            restored = self._store.load()
        except Exception:
            return
        for provider, group in _group_by_provider(restored).items():
            current = self._by_provider.get(provider, [])
            current_time = max((meter.observed_at for meter in current), default=0.0)
            restored_time = max((meter.observed_at for meter in group), default=0.0)
            if not current or restored_time > current_time:
                self._by_provider[provider] = group

    def _persist(self) -> None:
        if self._store is None:
            return
        try:
            self._store.save(self.meters())
        except Exception:
            # Persistence cannot fail the request or erase in-memory state.
            pass


# http_get(url, headers, timeout) -> (status:int, json_body:dict)
HttpGet = Callable[[str, dict, float], tuple[int, object]]


def fetch_openrouter_meters(api_key: str, *, http_get: HttpGet | None = None, observed_at: float = 0.0) -> list[QuotaMeter]:
    """Poll OpenRouter's current-key endpoint and return a finite credit meter.

    Non-200, unknown, inconsistent, or unmetered responses return no meter.
    ``http_get`` is injectable so the contract is tested without a live call.
    """
    url = OPENROUTER_CURRENT_KEY_URL
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
    return parse_openrouter_current_key(body, observed_at=observed_at)


# Process-wide cache the request path feeds (passively) and rotation/allocator read.
_GLOBAL_CACHE = QuotaCache()


def get_quota_cache() -> QuotaCache:
    """Shared QuotaCache singleton. client.py records response headers into it; rotation/allocator
    read its samples()."""
    return _GLOBAL_CACHE


def configure_quota_persistence(path: str) -> None:
    """Attach the configured local store and restore last-known facts."""
    if not str(path or "").strip():
        return
    from src.core.quota_store import QuotaMeterStore

    _GLOBAL_CACHE.set_store(QuotaMeterStore(path))


def record_provider_quota_headers(
    provider: str,
    headers: Mapping[str, str],
    *,
    observed_at: float | None = None,
) -> list[QuotaMeter]:
    """Record provider-authoritative response headers when they contain quota.

    Unknown providers or header shapes are harmless no-ops. Callers pass the
    provider resolved from the endpoint/configuration, never a guessed model
    display name.
    """
    provider_id = str(provider or "").strip().lower()
    if not provider_id or provider_id in {"default", "openai_compatible"}:
        return []
    return _GLOBAL_CACHE.record_headers(
        provider_id,
        headers,
        observed_at=observed_at,
    )


class QuotaCacheSource:
    """Adapts the live QuotaCache to the QuotaSource protocol (provider-level samples) so
    quota_runtime.collect_meters / rotation can consume header-derived live quota."""

    name = "quota_cache"

    def samples(self) -> list[QuotaSample]:
        return list(_GLOBAL_CACHE.samples().values())
