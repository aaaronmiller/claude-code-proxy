"""
Prometheus metrics exposition endpoint.

Exposes /metrics in Prometheus text format. Counters are incremented from
usage_tracker.log_request() and from cascade/circuit-breaker events. The user
brings their own Grafana (or any scraper) — no docker-compose bundled.

Why a small custom registry instead of the default `prometheus_client.REGISTRY`:
the default registry leaks process/python collectors that aren't useful for
proxy-level observability. We expose only the application-specific series.
"""

from __future__ import annotations

import logging
from typing import Dict

from fastapi import APIRouter, Response
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Application-specific registry — keeps the /metrics output focused.
REGISTRY = CollectorRegistry()


# ── Counters ──────────────────────────────────────────────────────────────────

requests_total = Counter(
    "proxy_requests_total",
    "Total requests processed by the proxy, labeled by profile/model/status.",
    ["profile", "model", "status"],
    registry=REGISTRY,
)

tokens_total = Counter(
    "proxy_tokens_total",
    "Total tokens (input/output/thinking) processed.",
    ["direction", "model", "profile"],
    registry=REGISTRY,
)

cost_usd_total = Counter(
    "proxy_cost_usd_total",
    "Cumulative estimated cost in USD per model/profile.",
    ["model", "profile"],
    registry=REGISTRY,
)

cascade_switches_total = Counter(
    "proxy_cascade_switches_total",
    "Number of cascade fallback switches per error class.",
    ["from_model", "to_model", "reason"],
    registry=REGISTRY,
)


# ── Histograms ────────────────────────────────────────────────────────────────

request_duration_seconds = Histogram(
    "proxy_request_duration_seconds",
    "End-to-end request duration including cascade retries.",
    ["model", "profile"],
    # Buckets chosen for LLM workloads: most reqs are 1s–60s; long-context >60s
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=REGISTRY,
)

cascade_depth_histogram = Histogram(
    "proxy_cascade_depth",
    "How deep into the cascade chain a request had to go (0 = primary worked).",
    buckets=(0, 1, 2, 3, 5, 10),
    registry=REGISTRY,
)


# ── Gauges ────────────────────────────────────────────────────────────────────

circuit_breaker_state = Gauge(
    "proxy_circuit_breaker_state",
    "Circuit breaker state per model: 0=closed, 1=half-open, 2=open.",
    ["model"],
    registry=REGISTRY,
)

active_profiles_gauge = Gauge(
    "proxy_active_profiles_total",
    "Number of profiles configured in profiles.json.",
    registry=REGISTRY,
)


# ── Recording helpers (called from usage_tracker / client) ────────────────────

def record_request(
    profile: str,
    model: str,
    status: str,
    duration_seconds: float,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int,
    cost_usd: float,
    cascade_depth: int,
) -> None:
    """Single call from usage_tracker.log_request() to update all relevant series."""
    try:
        prof = profile or "default"
        requests_total.labels(profile=prof, model=model or "unknown", status=status).inc()
        if duration_seconds > 0:
            request_duration_seconds.labels(
                model=model or "unknown", profile=prof
            ).observe(duration_seconds)
        if input_tokens > 0:
            tokens_total.labels(
                direction="input", model=model or "unknown", profile=prof
            ).inc(input_tokens)
        if output_tokens > 0:
            tokens_total.labels(
                direction="output", model=model or "unknown", profile=prof
            ).inc(output_tokens)
        if thinking_tokens > 0:
            tokens_total.labels(
                direction="thinking", model=model or "unknown", profile=prof
            ).inc(thinking_tokens)
        if cost_usd > 0:
            cost_usd_total.labels(model=model or "unknown", profile=prof).inc(cost_usd)
        if cascade_depth >= 0:
            cascade_depth_histogram.observe(cascade_depth)
    except Exception as e:
        # Metrics must never break the request path
        logger.debug(f"metrics record failed: {e}")


def record_cascade_switch(from_model: str, to_model: str, reason: str) -> None:
    """Called from src/api/websocket_logs.log_cascade() when action == 'switch'."""
    try:
        cascade_switches_total.labels(
            from_model=from_model or "unknown",
            to_model=to_model or "unknown",
            reason=reason or "unknown",
        ).inc()
    except Exception as e:
        logger.debug(f"cascade metric failed: {e}")


def set_circuit_breaker_state(model: str, state_name: str) -> None:
    """Called when a circuit breaker transitions state. state_name: closed/half_open/open."""
    try:
        value = {"closed": 0, "half_open": 1, "open": 2}.get(state_name, 0)
        circuit_breaker_state.labels(model=model).set(value)
    except Exception as e:
        logger.debug(f"breaker metric failed: {e}")


def refresh_profile_count() -> None:
    """Updated on startup + on profile reloads."""
    try:
        from src.core.profiles import get_all_profiles
        active_profiles_gauge.set(len(get_all_profiles()))
    except Exception:
        pass


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    """Prometheus text-format metrics. Scrape with `prometheus.yml`:

        scrape_configs:
          - job_name: claude-code-proxy
            scrape_interval: 15s
            static_configs:
              - targets: ['127.0.0.1:8082']
    """
    refresh_profile_count()
    payload = generate_latest(REGISTRY)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
