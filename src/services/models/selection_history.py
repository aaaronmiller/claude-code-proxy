"""Tracks model selections from TUI/Web configuration flows."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


HISTORY_PATH = Path("data/model_selection_history.json")


@dataclass
class SelectionEvent:
    timestamp: str
    source: str  # tui | web
    slot: str  # big | middle | small
    model_id: str
    provider: Optional[str] = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_raw() -> dict:
    if not HISTORY_PATH.exists():
        return {"events": []}
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"events": []}


def _save_raw(data: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_selection(
    slot: str,
    model_id: str,
    provider: Optional[str] = None,
    source: str = "tui",
) -> None:
    data = _load_raw()
    event = SelectionEvent(
        timestamp=_utc_now_iso(),
        source=source,
        slot=slot,
        model_id=model_id,
        provider=provider,
    )
    data.setdefault("events", []).append(asdict(event))
    # Keep file bounded
    data["events"] = data["events"][-500:]
    _save_raw(data)


def get_recent_selections(limit: int = 30) -> List[SelectionEvent]:
    data = _load_raw()
    rows = data.get("events", [])
    out: List[SelectionEvent] = []
    for row in rows[-limit:]:
        try:
            out.append(SelectionEvent(**row))
        except Exception:
            continue
    return list(reversed(out))


def get_recent_models(limit: int = 30) -> List[str]:
    seen = set()
    result: List[str] = []
    for event in get_recent_selections(limit=200):
        if event.model_id in seen:
            continue
        seen.add(event.model_id)
        result.append(event.model_id)
        if len(result) >= limit:
            break
    return result

