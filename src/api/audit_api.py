"""Audit log read API — returns config-write audit events.

Implements:
  GET /api/audit — list audit log entries with optional filters

Filters:
  since   — ISO-8601 UTC timestamp; entries with timestamp >= since
  principal — exact principal username
  field_path — exact field path pattern (exact match)
  limit   — maximum number of entries to return (default 100, max 1000)

Requires admin role (FR-030).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.users_rbac import require_admin

router = APIRouter(prefix="/api", tags=["audit"])

# Audit log file path (same as audit_log.append_audit)
AUDIT_LOG_PATH = Path("logs/config-audit.log")


def _parse_iso(ts: str) -> datetime:
    """Parse ISO-8601 timestamp (with or without Z) into timezone-aware datetime."""
    try:
        s = ts.rstrip("Z")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        # Return minimal value so entry is excluded by filter
        return datetime.min.replace(tzinfo=timezone.utc)


@router.get("/audit")
async def list_audit_entries(
    since: Optional[str] = Query(
        None,
        description="ISO-8601 UTC timestamp; only entries after this moment",
        examples=["2026-04-25T12:00:00Z"],
    ),
    principal: Optional[str] = Query(
        None, description="Filter by exact principal username"
    ),
    field_path: Optional[str] = Query(None, description="Filter by exact field_path"),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of entries to return (newest first)",
    ),
    _admin=Depends(require_admin),
) -> List[Dict[str, Any]]:
    """Return audit log entries matching the provided filters.

    Response format mirrors the on-disk JSONL structure:
      {
        "seq": <int>,
        "timestamp": "<ISO-8601 UTC>",
        "principal": "<username>",
        "surface": "<cli|dotenv|tui|web>",
        "endpoint": "<HTTP endpoint or CLI command>",
        "field_path": "<config field modified>",
        "before_value": "<masked previous value>",
        "after_value":  "<masked new value>",
        "client_ip":   "<optional IP>"
      }
    """
    if not AUDIT_LOG_PATH.exists():
        return []

    entries: List[Dict[str, Any]] = []
    # Read & filter
    try:
        with AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed

                # Apply filters
                if since:
                    entry_dt = _parse_iso(entry.get("timestamp", ""))
                    filter_dt = _parse_iso(since)
                    if entry_dt < filter_dt:
                        continue
                if principal is not None and entry.get("principal") != principal:
                    continue
                if field_path is not None and entry.get("field_path") != field_path:
                    continue

                entries.append(entry)
    except Exception:
        # File read error — return whatever we collected or empty
        pass

    # Return newest first, limit
    entries.sort(key=lambda e: e.get("seq", 0), reverse=True)
    return entries[:limit]
