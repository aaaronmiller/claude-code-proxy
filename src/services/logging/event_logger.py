"""
Structured event logger — emits one JSON line per request to logs/events.jsonl.

Each event contains every signal needed to compute the reliability score and
power the error feedback loop:
  timestamp, request_id, model_attempted, model_succeeded, cascade_depth,
  error_type, http_status, latency_ms, input_tokens, output_tokens,
  cost_usd, cache_hit, tier

Reliability Score formula (R ∈ [0, 1]):
  R = P_success × 0.50
    + (1 - cascade_depth_norm) × 0.20
    + (1 - latency_penalty) × 0.15
    + P_cache_hit × 0.15

  Where:
    P_success         = success_count / total_count (last 24h)
    cascade_depth_norm = avg(cascade_depth) / max_tiers (max_tiers = 4)
    latency_penalty   = clamp((p95_latency_ms - 3000) / 10000, 0, 1)
    P_cache_hit       = cache_hit_count / total_count

Current baseline (empty cascades, no cache): ~0.40
Target after all fixes: 0.85+

Usage:
    from src.services.logging.event_logger import event_logger
    event_logger.record(request_id=..., model_attempted=..., ...)
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_LOG_DIR = Path(os.environ.get("LOGS_DIR", "logs"))
_EVENTS_FILE = _LOG_DIR / "events.jsonl"
_MAX_BYTES = int(os.environ.get("EVENTS_LOG_MAX_MB", "20")) * 1024 * 1024

_file_handle = None


def _get_handle():
    global _file_handle
    if _file_handle is not None:
        return _file_handle
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _file_handle = open(_EVENTS_FILE, "a", encoding="utf-8", buffering=1)
    except Exception as e:
        logger.warning(f"event_logger: could not open {_EVENTS_FILE}: {e}")
    return _file_handle


class EventLogger:
    """Writes one structured JSON event per request completion."""

    def record(
        self,
        *,
        request_id: str,
        model_attempted: str,
        model_succeeded: Optional[str] = None,
        cascade_depth: int = 0,
        error_type: Optional[str] = None,
        http_status: Optional[int] = None,
        latency_ms: Optional[float] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        cache_hit: bool = False,
        tier: str = "",
        stream: bool = False,
    ) -> None:
        fh = _get_handle()
        if fh is None:
            return
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "rid": request_id[:8],
            "model": model_attempted,
            "ok": model_succeeded or model_attempted,
            "depth": cascade_depth,
            "err": error_type,
            "status": http_status,
            "lat": round(latency_ms, 1) if latency_ms else None,
            "in": input_tokens,
            "out": output_tokens,
            "cost": round(cost_usd, 6) if cost_usd else 0.0,
            "cache": cache_hit,
            "tier": tier,
            "stream": stream,
        }
        try:
            fh.write(json.dumps(event, separators=(",", ":")) + "\n")
            # Rotate if oversized
            if _EVENTS_FILE.stat().st_size > _MAX_BYTES:
                _rotate()
        except Exception:
            pass

    def compute_reliability_score(self, hours: int = 24) -> dict:
        """
        Compute reliability score R from the last N hours of event log.

        Returns:
          {
            "score": float,           # R ∈ [0, 1]
            "grade": str,             # S/A/B/C/F
            "components": {...},      # per-component breakdown
            "total_requests": int,
            "window_hours": int,
          }
        """
        if not _EVENTS_FILE.exists():
            return {"score": None, "grade": "?", "total_requests": 0, "window_hours": hours}

        cutoff = time.time() - hours * 3600
        events = []
        try:
            with open(_EVENTS_FILE, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        # Parse ISO timestamp
                        ts_str = e.get("ts", "")
                        if ts_str:
                            from datetime import datetime as _dt
                            ts = _dt.fromisoformat(ts_str).timestamp()
                            if ts >= cutoff:
                                events.append(e)
                    except Exception:
                        pass
        except Exception:
            pass

        if not events:
            return {"score": None, "grade": "?", "total_requests": 0, "window_hours": hours}

        total = len(events)
        successes = sum(1 for e in events if not e.get("err"))
        cascade_depths = [e.get("depth", 0) for e in events]
        latencies = [e["lat"] for e in events if e.get("lat")]
        cache_hits = sum(1 for e in events if e.get("cache"))

        p_success = successes / total
        avg_depth = sum(cascade_depths) / len(cascade_depths) if cascade_depths else 0
        cascade_norm = min(avg_depth / 4.0, 1.0)  # 4 = max tiers

        p95_lat = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 2 else 0
        lat_penalty = min(max((p95_lat - 3000) / 10000, 0.0), 1.0)

        p_cache = cache_hits / total

        score = (
            p_success * 0.50
            + (1 - cascade_norm) * 0.20
            + (1 - lat_penalty) * 0.15
            + p_cache * 0.15
        )

        grade = "S" if score >= 0.90 else "A" if score >= 0.80 else "B" if score >= 0.65 else "C" if score >= 0.50 else "F"

        # Error type breakdown for feedback loop
        error_counts: dict = {}
        for e in events:
            err = e.get("err")
            if err:
                error_counts[err] = error_counts.get(err, 0) + 1

        return {
            "score": round(score, 3),
            "grade": grade,
            "components": {
                "success_rate": round(p_success, 3),
                "cascade_efficiency": round(1 - cascade_norm, 3),
                "latency_score": round(1 - lat_penalty, 3),
                "cache_hit_rate": round(p_cache, 3),
            },
            "error_breakdown": error_counts,
            "p95_latency_ms": round(p95_lat, 1) if p95_lat else None,
            "avg_cascade_depth": round(avg_depth, 2),
            "total_requests": total,
            "window_hours": hours,
        }


def _rotate():
    """Rename events.jsonl → events.jsonl.1 and start fresh."""
    global _file_handle
    try:
        if _file_handle:
            _file_handle.close()
            _file_handle = None
        rotated = _EVENTS_FILE.with_suffix(".jsonl.1")
        _EVENTS_FILE.rename(rotated)
    except Exception:
        pass


# Singleton
event_logger = EventLogger()
