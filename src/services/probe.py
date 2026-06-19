"""Latency / availability probe (F03/F11 measured inputs for the allocator + reliability loop).

Makes a minimal chat-completion call to a provider/model, measures latency and tokens, and
classifies the outcome. The HTTP call is INJECTABLE so the metric/classification logic is
unit-testable offline; the default does a real httpx POST. Keep probes minimal (max_tokens=1).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ProbeResult:
    provider: str
    model: str
    ok: bool
    status: int
    latency_s: float
    tokens_out: int
    tokens_per_s: float | None
    error_class: str


def classify(status: int) -> str:
    if status == 200:
        return "ok"
    if status == 429:
        return "rate_limit"
    if status in (401, 403):
        return "auth"
    if status in (400, 422):
        return "bad_request"
    if status >= 500:
        return "server"
    if status == 0:
        return "network"
    return "other"


# http_post(url, headers, json, timeout) -> (status:int, body:dict|None, elapsed_s:float)
HttpPost = Callable[[str, dict, dict, float], tuple[int, Any, float]]


def _default_post(url, headers, json, timeout):
    import httpx

    t0 = time.monotonic()
    try:
        r = httpx.post(url, headers=headers, json=json, timeout=timeout)
        elapsed = time.monotonic() - t0
        body = None
        if r.headers.get("content-type", "").startswith("application/json"):
            try:
                body = r.json()
            except Exception:
                body = None
        return r.status_code, body, elapsed
    except Exception:
        return 0, None, time.monotonic() - t0


def probe_model(
    provider: str,
    base_url: str,
    model: str,
    api_key: str,
    *,
    timeout: float = 20.0,
    http_post: HttpPost | None = None,
) -> ProbeResult:
    """Minimal non-streaming probe. Returns a ProbeResult with latency, completion tokens, and
    tokens/s (None when unavailable). error_class is the normalized failure category."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}

    post = http_post or _default_post
    status, body, elapsed = post(url, headers, payload, timeout)

    tokens_out = 0
    if isinstance(body, dict):
        tokens_out = int((body.get("usage") or {}).get("completion_tokens", 0) or 0)
    tps = round(tokens_out / elapsed, 2) if (elapsed > 0 and tokens_out) else None

    return ProbeResult(
        provider=provider, model=model, ok=(status == 200), status=status,
        latency_s=round(elapsed, 4), tokens_out=tokens_out, tokens_per_s=tps,
        error_class=classify(status),
    )
