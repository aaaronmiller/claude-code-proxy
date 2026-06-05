from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Query

from scripts.status.rtk_status import DEFAULT_CACHE_PATH, get_stats


router = APIRouter(prefix="/api/rtk", tags=["rtk"])


@router.get("/stats")
async def rtk_stats(
    scope: Literal["project", "global"] = Query("project"),
    refresh: bool = Query(False),
    cwd: str = Query("/home/cheta/code/claude-code-proxy"),
    ttl: int = Query(10, ge=0, le=3600),
):
    """Return cached RTK token savings stats."""
    return get_stats(
        cache_path=Path(DEFAULT_CACHE_PATH),
        scope=scope,
        cwd=cwd,
        ttl_seconds=ttl,
        force=refresh,
    )
