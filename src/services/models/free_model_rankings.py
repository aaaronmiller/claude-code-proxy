"""Dynamic ranking and classification for OpenRouter free models."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.services.models.openrouter_fetcher import get_models


DEFAULT_STEALTH_WINDOW_DAYS = 30
RANKINGS_PATH = Path("data/free_model_rankings.json")


@dataclass
class FreeModelRanking:
    model_id: str
    provider: str
    age_days: int
    class_type: str  # stealth_free | evergreen_free
    context_length: int
    max_completion_tokens: int
    supports_tools: bool
    supports_reasoning: bool
    supports_structured_output: bool
    score: float
    created: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_days(created_epoch: int) -> int:
    if not created_epoch:
        return 9999
    created = datetime.fromtimestamp(created_epoch, tz=timezone.utc)
    return max(0, (_utc_now() - created).days)


def _score_model(model: Dict[str, Any], stealth_window_days: int) -> FreeModelRanking:
    model_id = model.get("id", "")
    created = int(model.get("created", 0) or 0)
    context = int(model.get("context_length", 0) or 0)
    max_out = int(model.get("max_completion_tokens", 0) or 0)
    tools = bool(model.get("supports_tools", False))
    reasoning = bool(model.get("supports_reasoning", False))
    structured = bool(model.get("supports_structured_output", False))
    provider = str(model.get("provider", "unknown") or "unknown")

    age_days = _age_days(created)
    class_type = "stealth_free" if age_days <= stealth_window_days else "evergreen_free"

    # Score bands (0-100)
    capability = 0.0
    capability += 14.0 if tools else 0.0
    capability += 8.0 if reasoning else 0.0
    capability += 3.0 if structured else 0.0

    # Context score saturates near 256k.
    context_score = min(20.0, 20.0 * math.log10(max(context, 1024)) / math.log10(256_000))

    # Output score saturates near 64k.
    out_score = min(12.0, 12.0 * math.log10(max(max_out, 512)) / math.log10(65_536))

    # Recency: linear decay until stealth window, then low floor.
    if age_days <= stealth_window_days:
        recency = 20.0 * (1.0 - (age_days / max(1, stealth_window_days)))
    else:
        recency = 3.0

    score = round(min(100.0, capability + context_score + out_score + recency), 2)

    return FreeModelRanking(
        model_id=model_id,
        provider=provider,
        age_days=age_days,
        class_type=class_type,
        context_length=context,
        max_completion_tokens=max_out,
        supports_tools=tools,
        supports_reasoning=reasoning,
        supports_structured_output=structured,
        score=score,
        created=created,
    )


def build_free_model_rankings(
    models: Optional[List[Dict[str, Any]]] = None,
    stealth_window_days: int = DEFAULT_STEALTH_WINDOW_DAYS,
) -> List[FreeModelRanking]:
    """Build ranked list for free models only."""
    source = models if models is not None else get_models()
    free_models = [m for m in source if m.get("pricing", {}).get("is_free", False)]
    ranked = [_score_model(m, stealth_window_days) for m in free_models]
    ranked.sort(key=lambda r: (r.score, -r.context_length, -r.max_completion_tokens), reverse=True)
    return ranked


def save_free_model_rankings(
    rankings: List[FreeModelRanking],
    path: Path = RANKINGS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": _utc_now().isoformat(),
        "total": len(rankings),
        "rankings": [asdict(r) for r in rankings],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_free_model_rankings(path: Path = RANKINGS_PATH) -> List[FreeModelRanking]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rankings = []
        for row in payload.get("rankings", []):
            rankings.append(FreeModelRanking(**row))
        return rankings
    except Exception:
        return []


def get_or_build_free_model_rankings(
    force_refresh: bool = False,
    stealth_window_days: int = DEFAULT_STEALTH_WINDOW_DAYS,
) -> List[FreeModelRanking]:
    if not force_refresh:
        cached = load_free_model_rankings()
        if cached:
            return cached
    fresh = build_free_model_rankings(stealth_window_days=stealth_window_days)
    save_free_model_rankings(fresh)
    return fresh


def get_top_free_models(limit: int = 40, force_refresh: bool = False) -> List[str]:
    rankings = get_or_build_free_model_rankings(force_refresh=force_refresh)
    return [r.model_id for r in rankings[: max(1, limit)]]

