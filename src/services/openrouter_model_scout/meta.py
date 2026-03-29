"""
Meta.json management for run history and timestamps.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from openrouter_model_scout.models import Meta as MetaModel

logger = logging.getLogger(__name__)


def load_meta(meta_path: str | Path) -> MetaModel:
    """
    Load meta.json, initializing if missing.

    Args:
        meta_path: Path to meta.json

    Returns:
        Meta model instance
    """
    path = Path(meta_path)
    if not path.exists():
        logger.info("meta.json not found, initializing new meta")
        now = datetime.now(timezone.utc).isoformat()
        return MetaModel(
            last_run=now,
            last_deep_audit=now,
            run_history=[]
        )

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return MetaModel(**data)


def append_run(
    meta: MetaModel,
    timestamp: str,
    mode: str,
    api_duration: float,
    scrape_duration: float,
    models_count: int,
    token_usage: Dict[str, Any]
) -> None:
    """
    Append a new run entry to meta and update timestamps.

    Args:
        meta: Meta model (modified in place)
        timestamp: ISO 8601 timestamp of run start
        mode: Run mode (full, fast, force, etc.)
        api_duration: Seconds spent in API sync
        scrape_duration: Seconds spent in deep scrape
        models_count: Number of models processed
        token_usage: Dict with token counts and cost
    """
    from openrouter_model_scout.models import RunHistoryEntry

    entry = RunHistoryEntry(
        timestamp=timestamp,
        mode=mode,
        api_sync_duration_seconds=api_duration,
        scrape_duration_seconds=scrape_duration,
        models_count=models_count,
        token_usage=token_usage,
    )

    meta.run_history.append(entry)
    meta.last_run = timestamp

    # If this was a deep audit, update that timestamp too
    if mode in ('full', 'force'):
        meta.last_deep_audit = timestamp

    # Prune history to keep size manageable (last 100 entries)
    if len(meta.run_history) > 100:
        meta.run_history = meta.run_history[-100:]


def write_meta(meta: MetaModel, meta_path: str | Path) -> None:
    """
    Write meta to disk atomically.

    Args:
        meta: Meta model
        meta_path: Destination file path
    """
    from openrouter_model_scout.io import atomic_json_write

    data = meta.model_dump(mode='json')
    atomic_json_write(data, meta_path)
