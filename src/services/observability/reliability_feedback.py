"""Aggregate router reliability metrics and post them back to model-scan."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import quantiles
from typing import Any
from urllib import request as urlrequest


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) < 2:
        return float(values[0])
    return float(quantiles(values, n=20, method="inclusive")[18])


def aggregate_reliability(db_path: str | Path, *, since_hours: int = 24) -> dict[str, Any]:
    """Build provider/model reliability from usage_tracking.db."""
    path = Path(db_path)
    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": since_hours,
        "providers": {},
        "models": {},
    }
    if not path.exists():
        return payload

    cutoff = time.time() - (since_hours * 3600)
    rows: list[sqlite3.Row] = []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, provider, resolved_model, routed_model, duration_ms, status, error_message
            FROM api_requests
            WHERE timestamp >= datetime(?, 'unixepoch')
            """,
            (cutoff,),
        )
        rows = list(cur.fetchall())
    finally:
        conn.close()

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        provider = str(row["provider"] or "unknown")
        model = str(row["resolved_model"] or row["routed_model"] or "unknown")
        status = str(row["status"] or "")
        error = str(row["error_message"] or "").lower()
        latency = float(row["duration_ms"] or 0)
        for key in (("providers", provider), ("models", model)):
            item = grouped.setdefault(key, {"latencies": [], "requests": 0, "errors": 0, "rate_limits": 0})
            item["requests"] += 1
            if latency > 0:
                item["latencies"].append(latency)
            if status != "success":
                item["errors"] += 1
            if "429" in error or "rate" in error or "limit" in error:
                item["rate_limits"] += 1

    for (bucket, name), item in grouped.items():
        requests = int(item["requests"])
        payload[bucket][name] = {
            "requests": requests,
            "latency_p95_ms": round(_p95(item["latencies"]), 2),
            "error_rate": round(item["errors"] / requests, 4) if requests else 0.0,
            "rate_limit_frequency": round(item["rate_limits"] / requests, 4) if requests else 0.0,
        }
    return payload


def reliability_url_from_gateway(gateway_url: str) -> str:
    base = gateway_url.rstrip("/")
    if base.endswith("/routing-snapshot"):
        return base[: -len("/routing-snapshot")] + "/reliability"
    return base + "/reliability"


def post_reliability(url: str, payload: dict[str, Any], *, timeout_s: float = 5.0) -> bool:
    data = __import__("json").dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    with urlrequest.urlopen(req, timeout=timeout_s) as resp:
        return 200 <= int(resp.status) < 300


async def reliability_feedback_loop(config, db_path: str | Path) -> None:
    interval = int(os.environ.get("MODEL_SCAN_RELIABILITY_INTERVAL_S", "300") or "300")
    gateway_url = str(getattr(config, "gateway_url", "") or "")
    if not gateway_url:
        return
    url = reliability_url_from_gateway(gateway_url)
    while True:
        try:
            payload = aggregate_reliability(db_path)
            await asyncio.to_thread(post_reliability, url, payload)
        except Exception:
            pass
        await asyncio.sleep(max(30, interval))
