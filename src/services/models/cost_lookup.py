"""
Per-request cost estimation from models/scout/models.json pricing data.

Usage:
    from src.services.models.cost_lookup import estimate_cost
    cost = estimate_cost("openrouter/minimax-m2.5:free", input_tokens=4200, output_tokens=340)
    # Returns 0.0 for free models, None if model unknown
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MODELS_FILE = Path(__file__).parent.parent.parent / "models" / "scout" / "models.json"

# Lazy-loaded index: model_id → {"prompt": float, "completion": float}
_pricing_index: Optional[dict] = None


def _load_pricing_index() -> dict:
    global _pricing_index
    if _pricing_index is not None:
        return _pricing_index

    _pricing_index = {}
    try:
        data = json.loads(_MODELS_FILE.read_text(encoding="utf-8"))
        for model in data:
            model_id = model.get("id", "")
            pricing = model.get("pricing") or {}
            prompt_cost = pricing.get("prompt")
            completion_cost = pricing.get("completion")
            if model_id and (prompt_cost is not None or completion_cost is not None):
                _pricing_index[model_id] = {
                    "prompt": float(prompt_cost or 0),
                    "completion": float(completion_cost or 0),
                }
    except Exception as e:
        logger.debug(f"Could not load pricing index: {e}")

    return _pricing_index


def _normalize_model_id(model: str) -> str:
    """Strip provider prefix variants so lookups hit the index."""
    # openrouter/minimax/m2.5:free → minimax/m2.5:free
    if "/" in model:
        parts = model.split("/", 1)
        # If first segment is a known proxy prefix, strip it
        if parts[0].lower() in ("openrouter", "opencode_go", "opencode", "or"):
            return parts[1]
    return model


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Optional[float]:
    """
    Estimate cost in USD for a completed request.

    Returns:
        float — estimated cost (0.0 for free models)
        None  — model not found in pricing data
    """
    if not model or (not input_tokens and not output_tokens):
        return None

    index = _load_pricing_index()

    # Try the model ID as-is, then normalized
    pricing = index.get(model) or index.get(_normalize_model_id(model))

    # Also try stripping trailing :free / :nitro tags
    if pricing is None:
        base = model.split(":")[0]
        pricing = index.get(base) or index.get(_normalize_model_id(base))

    if pricing is None:
        return None

    cost = (pricing["prompt"] * input_tokens) + (pricing["completion"] * output_tokens)
    return cost


def fmt_cost(cost: Optional[float]) -> str:
    """Format cost for terminal display."""
    if cost is None:
        return ""
    if cost == 0.0:
        return "$0.00"
    if cost < 0.0001:
        return f"${cost * 1000:.3f}m"  # show in milli-dollars
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.3f}"
