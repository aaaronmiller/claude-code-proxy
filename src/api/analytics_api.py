"""Analytics API — per-assignment and per-model usage metrics.

Implements:
  GET /api/metrics/by-assignment — aggregate RequestMetric rows grouped by resolved_assignment_id
  GET /api/metrics/by-model      — aggregate RequestMetric rows grouped by resolved_model

Both accept optional `since` query parameter (ISO-8601 timestamp) to limit the window.

Success Criteria:
  SC-009  Per-assignment pivot available
  SC-010  Per-model pivot available
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.users_rbac import get_current_user

router = APIRouter(prefix="/api", tags=["analytics"])

# Path to usage_tracking.db (same location as usage_tracker module)
USAGE_DB_PATH = Path("usage_tracking.db")


def _connect() -> sqlite3.Connection:
    """Open a row_factory connection to the usage tracking database."""
    conn = sqlite3.connect(USAGE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 `since` parameter into a timezone-aware datetime, or None."""
    if not since:
        return None
    try:
        # Handle with or without trailing Z
        ts = since.rstrip("Z")
        # Assume naive is UTC, keep aware as-is
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        raise HTTPException(
            status_code=400, detail="`since` must be ISO-8601 UTC timestamp"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/metrics/by-assignment
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/metrics/by-assignment")
async def metrics_by_assignment(
    since: Optional[str] = Query(
        None, description="ISO-8601 UTC timestamp; only rows after this moment"
    ),
    _user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Aggregate usage metrics grouped by resolved_assignment_id.

    Columns returned per group:
      resolved_assignment_id   — assignment id (NULL → "unassigned")
      total_requests           — count of RequestMetric rows
      success_rate             — fraction with status='success' (0–1)
      cascade_rate             — fraction where attempt_index > 0
      avg_duration_ms          — mean duration over all attempts
    """
    conn = _connect()
    try:
        cursor = conn.cursor()
        where = ""
        params: List[Any] = []
        if since:
            dt = _parse_since(since)
            where = "WHERE created_at >= ?"
            params.append(dt.isoformat())

        sql = f"""
        SELECT
          COALESCE(resolved_assignment_id, 'unassigned') AS resolved_assignment_id,
          COUNT(*)                                     AS total_requests,
          AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) AS success_rate,
          AVG(CASE WHEN attempt_index > 0 THEN 1.0 ELSE 0.0 END) AS cascade_rate,
          AVG(duration_ms)                             AS avg_duration_ms
        FROM api_requests
        {where}
        GROUP BY resolved_assignment_id
        ORDER BY total_requests DESC
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/metrics/by-model
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/metrics/by-model")
async def metrics_by_model(
    since: Optional[str] = Query(
        None, description="ISO-8601 UTC timestamp; only rows after this moment"
    ),
    _user=Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Aggregate usage metrics grouped by resolved_model (the model that was actually called).

    Columns returned per group:
      resolved_model           — model name
      total_requests           — count of RequestMetric rows
      success_rate             — fraction with status='success'
      avg_duration_ms          — mean duration
      avg_tokens               — mean total_tokens (may be NULL for non-success)
    """
    conn = _connect()
    try:
        cursor = conn.cursor()
        where = ""
        params: List[Any] = []
        if since:
            dt = _parse_since(since)
            where = "WHERE created_at >= ?"
            params.append(dt.isoformat())

        sql = f"""
        SELECT
          resolved_model,
          COUNT(*)                                     AS total_requests,
          AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) AS success_rate,
          AVG(duration_ms)                             AS avg_duration_ms,
          AVG(total_tokens)                            AS avg_tokens
        FROM api_requests
        {where}
        GROUP BY resolved_model
        ORDER BY total_requests DESC
        """
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
