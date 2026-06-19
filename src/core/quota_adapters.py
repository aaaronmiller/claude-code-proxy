"""Quota header parsers (F06) - pure, offline-testable.

Turns provider HTTP response headers into QuotaMeter objects. Behavior-driven: detects the
header family from the response itself (OpenAI/Groq/Cerebras `x-ratelimit-*` and Anthropic
`anthropic-ratelimit-*`) rather than hardcoding per-provider names, per the project's
normalization mandate. Live fetching (issuing the request, reading headers) is a thin wrapper
left for a session with provider access; the PARSING here is fully unit-tested with fixtures.

See ai-gateway/plan/features/F06 + 04-DATA-CONTRACTS.md.
"""
from __future__ import annotations

import re
from typing import Callable, Mapping

from src.core.quota_sources import QuotaMeter

# (header-unit-token, QuotaMeter unit)
_UNIT_MAP = (("requests", "calls"), ("tokens", "tokens"))
# windowed header suffix -> window_seconds (Cerebras exposes per minute/hour/day)
_WINDOWS = (("minute", 60), ("hour", 3600), ("day", 86400))


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return None


def parse_ratelimit_headers(
    provider: str,
    headers: Mapping[str, str],
    *,
    observed_at: float = 0.0,
) -> list[QuotaMeter]:
    """Parse standard rate-limit headers into QuotaMeters (calls + tokens).

    Handles both families; missing fields are skipped gracefully (a provider that only
    exposes request limits yields one meter). window_seconds is left 0 (unknown) when it
    cannot be derived; the allocator uses remaining/limit, which is window-agnostic.
    """
    h = {str(k).lower(): v for k, v in headers.items()}
    out: list[QuotaMeter] = []

    for hkey, unit in _UNIT_MAP:
        # OpenAI / Groq style (non-windowed): x-ratelimit-{limit,remaining}-{requests,tokens}
        lim = _num(h.get(f"x-ratelimit-limit-{hkey}"))
        rem = _num(h.get(f"x-ratelimit-remaining-{hkey}"))
        if lim is not None and rem is not None:
            out.append(
                QuotaMeter(
                    id=f"{provider}:{unit}:x-ratelimit",
                    provider=provider, unit=unit, window_seconds=0,
                    limit=lim, remaining=rem,
                    reset_at=str(h.get(f"x-ratelimit-reset-{hkey}", "")),
                    source="header", observed_at=observed_at,
                )
            )

        # Cerebras style (windowed): x-ratelimit-{limit,remaining}-{requests,tokens}-{minute,hour,day}
        for wname, wsec in _WINDOWS:
            lim_w = _num(h.get(f"x-ratelimit-limit-{hkey}-{wname}"))
            rem_w = _num(h.get(f"x-ratelimit-remaining-{hkey}-{wname}"))
            if lim_w is not None and rem_w is not None:
                out.append(
                    QuotaMeter(
                        id=f"{provider}:{unit}:x-ratelimit:{wname}",
                        provider=provider, unit=unit, window_seconds=wsec,
                        limit=lim_w, remaining=rem_w,
                        reset_at=str(h.get(f"x-ratelimit-reset-{hkey}-{wname}", "")),
                        source="header", observed_at=observed_at,
                    )
                )

        # Anthropic style: anthropic-ratelimit-{requests,tokens}-{limit,remaining}
        lim_a = _num(h.get(f"anthropic-ratelimit-{hkey}-limit"))
        rem_a = _num(h.get(f"anthropic-ratelimit-{hkey}-remaining"))
        if lim_a is not None and rem_a is not None:
            out.append(
                QuotaMeter(
                    id=f"{provider}:{unit}:anthropic-ratelimit",
                    provider=provider, unit=unit, window_seconds=0,
                    limit=lim_a, remaining=rem_a,
                    reset_at=str(h.get(f"anthropic-ratelimit-{hkey}-reset", "")),
                    source="header", observed_at=observed_at,
                )
            )

    return out


_DUR_RE = re.compile(r"(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m)?(?:(\d+(?:\.\d+)?)s)?(?:(\d+)ms)?$")


def parse_reset_seconds(value: str | None) -> float | None:
    """Parse a rate-limit reset value into seconds-to-reset. Handles Groq-style durations
    ("1m26.4s", "547ms", "5h"), plain seconds ("60", "1.5"). Returns None if unparseable.
    Verified against live Groq headers (reset is duration-to-refill, not a window length)."""
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    try:
        return float(v)  # plain seconds
    except ValueError:
        pass
    m = _DUR_RE.match(v)
    if not m or not any(m.groups()):
        return None
    h, mn, s, ms = (float(g) if g else 0.0 for g in m.groups())
    total = h * 3600 + mn * 60 + s + ms / 1000.0
    return total or None


class HeaderQuotaSource:
    """QuotaMeterSource backed by a provider's HTTP response headers. The fetcher is INJECTED
    (a callable returning a headers dict) so this is unit-testable offline and live-usable with a
    real HTTP fetcher. Never raises into the caller (returns [] on failure)."""

    def __init__(self, name: str, provider: str, fetch_headers: Callable[[], Mapping[str, str]]):
        self.name = name
        self.provider = provider
        self._fetch = fetch_headers

    def meters(self) -> list[QuotaMeter]:
        try:
            return parse_ratelimit_headers(self.provider, self._fetch() or {})
        except Exception:
            return []


def parse_openrouter_auth_key(payload: Mapping, *, observed_at: float = 0.0) -> list[QuotaMeter]:
    """Parse OpenRouter GET /api/v1/auth/key JSON ({data:{limit,usage,...}}) into a meter.

    limit None => unmetered (skip). Otherwise remaining = limit - usage.
    """
    data = payload.get("data", payload) if isinstance(payload, Mapping) else {}
    limit = _num(data.get("limit"))
    if limit is None:
        return []  # unmetered key (verified live: limit=null => no dollar cap)
    # Prefer the explicit limit_remaining the API returns; fall back to limit - usage.
    rem = _num(data.get("limit_remaining"))
    if rem is None:
        rem = limit - (_num(data.get("usage")) or 0.0)
    return [
        QuotaMeter(
            id="openrouter:dollars:auth-key", provider="openrouter", unit="dollars",
            window_seconds=0, limit=limit, remaining=max(0.0, rem),
            reset_at=str(data.get("limit_reset", "") or ""),
            source="poll", observed_at=observed_at,
        )
    ]
