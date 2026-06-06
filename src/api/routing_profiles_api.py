"""
API for Option C-slim routing profiles.

Lives at /api/routing-profiles to avoid colliding with the legacy
/api/profiles endpoints in web_ui.py (which manage the env-var profile
system — saving model configs from the wizard).

Persistent routing profiles are edited by hand in profiles/profiles.json. This API also supports
temporary profiles used by the ccp launcher for per-session routing.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.profiles import (
    DEFAULT_PROFILES_PATH,
    get_all_profiles,
    resolve_profile,
    register_ephemeral_profile,
    delete_ephemeral_profile,
    list_ephemeral_profiles,
    sweep_ephemeral_profiles,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class EphemeralProfileRequest(BaseModel):
    preset: str = "default"
    overlay: Dict[str, Any] = Field(default_factory=dict)
    ttl_s: int = 3600
    profile_id: Optional[str] = None


def _request_counts_by_profile(hours: int = 24) -> Dict[str, int]:
    """Count requests per profile from usage_tracker over the window."""
    counts: Dict[str, int] = {}
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return counts
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute(
            """
            SELECT COALESCE(profile, '(unprefixed)'), COUNT(*)
            FROM api_requests
            WHERE timestamp >= ?
            GROUP BY profile
            """,
            (cutoff,),
        )
        for prof, count in cursor.fetchall():
            counts[prof] = count
        conn.close()
    except Exception as e:
        logger.debug(f"profile request counts unavailable: {e}")
    return counts


@router.get("/api/routing-profiles")
async def list_routing_profiles(hours: int = 24) -> Dict[str, Any]:
    """List all routing profiles with their resolved overlays + request counts.

    Args:
        hours: Window for request-count aggregation (default: 24).

    Returns:
        {
          "profiles": [
            {
              "name": "pi",
              "notes": "...",
              "resolved": {merged overlay on default},
              "raw": {profile as defined in profiles.json},
              "request_count_24h": 42
            },
            ...
          ],
          "profiles_file": "/abs/path/profiles.json",
          "window_hours": 24,
          "default_exists": true,
        }
    """
    raw = get_all_profiles()
    counts = _request_counts_by_profile(hours)
    profiles: List[Dict[str, Any]] = []
    for name in sorted(raw.keys()):
        merged = resolve_profile(name).slots
        profiles.append({
            "name": name,
            "notes": raw[name].get("notes", ""),
            "resolved": merged,
            "raw": raw[name],
            "request_count": counts.get(name, 0),
        })
    return {
        "profiles": profiles,
        "profiles_file": str(DEFAULT_PROFILES_PATH),
        "window_hours": hours,
        "default_exists": "default" in raw,
        "ephemeral": {
            name: {
                "preset": item.get("preset"),
                "expires_at": item.get("expires_at"),
            }
            for name, item in list_ephemeral_profiles().items()
        },
        "unprefixed_count": counts.get("(unprefixed)", 0),
    }


@router.post("/api/routing-profiles")
async def create_ephemeral_routing_profile(payload: EphemeralProfileRequest) -> Dict[str, Any]:
    """Create a temporary routing profile and return its proxy URL prefix."""
    raw = get_all_profiles()
    if payload.preset not in raw:
        raise HTTPException(status_code=404, detail=f"Preset '{payload.preset}' not found")
    ctx = register_ephemeral_profile(
        preset=payload.preset,
        overlay=payload.overlay,
        ttl_s=payload.ttl_s,
        profile_id=payload.profile_id,
    )
    return {
        "id": ctx.name,
        "preset": payload.preset,
        "url_prefix": f"/p/{ctx.name}",
        "base_url": f"http://127.0.0.1:8082/p/{ctx.name}",
        "ttl_s": payload.ttl_s,
        "resolved": ctx.slots,
    }


@router.delete("/api/routing-profiles/{name}")
async def delete_ephemeral_routing_profile(name: str) -> Dict[str, Any]:
    """Delete a temporary routing profile. Idempotent by design."""
    existed = delete_ephemeral_profile(name)
    return {"id": name, "deleted": existed}


@router.post("/api/routing-profiles/sweep")
async def sweep_expired_routing_profiles() -> Dict[str, Any]:
    return {"removed": sweep_ephemeral_profiles()}


@router.get("/api/routing-profiles/{name}")
async def get_routing_profile(name: str) -> Dict[str, Any]:
    """Get a single profile's resolved overlay + raw definition.

    Returns 404 if the profile name is not in profiles.json.
    """
    raw = get_all_profiles()
    if name not in raw:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{name}' not found. Available: {sorted(raw.keys())}",
        )
    return {
        "name": name,
        "notes": raw[name].get("notes", ""),
        "resolved": resolve_profile(name).slots,
        "raw": raw[name],
    }


@router.get("/api/routing-profiles/{name}/usage")
async def get_routing_profile_usage(name: str, hours: int = 24) -> Dict[str, Any]:
    """Per-model request breakdown for a profile over the window."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return {"profile": name, "enabled": False, "models": []}
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        conn = sqlite3.connect(usage_tracker.db_path)
        rows = conn.execute(
            """
            SELECT routed_model,
                   COUNT(*) AS n,
                   AVG(duration_ms) AS avg_ms,
                   SUM(input_tokens) AS in_tok,
                   SUM(output_tokens) AS out_tok
            FROM api_requests
            WHERE profile = ? AND timestamp >= ?
            GROUP BY routed_model
            ORDER BY n DESC
            """,
            (name, cutoff),
        ).fetchall()
        conn.close()
        return {
            "profile": name,
            "window_hours": hours,
            "models": [
                {
                    "model": r[0],
                    "requests": r[1],
                    "avg_duration_ms": round(r[2] or 0, 1),
                    "input_tokens": r[3] or 0,
                    "output_tokens": r[4] or 0,
                }
                for r in rows
            ],
        }
    except Exception as e:
        logger.error(f"profile usage query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
