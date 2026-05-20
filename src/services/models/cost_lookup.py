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


def paid_equivalent_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    baseline: str = "auto",
) -> tuple[Optional[float], str]:
    """
    Compute what the request WOULD have cost at paid rates.

    Args:
        model: the model actually used (often a :free variant)
        baseline: which paid model to compare to:
            'auto'   — same model with :free stripped (default)
            'tier'   — class-matched paid model (haiku/sonnet/opus by size)
            '<id>'   — explicit paid model ID

    Returns:
        (cost_usd, baseline_name) — cost is None if no paid equivalent found.
    """
    if not model or (not input_tokens and not output_tokens):
        return None, ""

    index = _load_pricing_index()
    baseline_id: Optional[str] = None

    if baseline == "auto" or baseline == "same":
        # Strip :free / :nitro tags from the model and look up its paid version
        base = model.split(":")[0]
        baseline_id = base if index.get(base) else _normalize_model_id(base)
        if baseline_id not in index:
            baseline_id = None
    elif baseline == "tier":
        # Heuristic tier matching by model name keywords
        m = model.lower()
        if "haiku" in m or "nano" in m or "mini" in m or "small" in m or "8b" in m:
            for cand in ("anthropic/claude-haiku-4-5", "anthropic/claude-3-5-haiku-20241022", "openai/gpt-4o-mini"):
                if cand in index:
                    baseline_id = cand
                    break
        elif "opus" in m or "300b" in m or "405b" in m or "ultra" in m or "premium" in m:
            for cand in ("anthropic/claude-opus-4", "anthropic/claude-opus-4-20250514"):
                if cand in index:
                    baseline_id = cand
                    break
        else:
            # middle/sonnet-class default
            for cand in ("anthropic/claude-sonnet-4-5", "anthropic/claude-sonnet-4-20250514"):
                if cand in index:
                    baseline_id = cand
                    break
    else:
        # Explicit model id requested
        baseline_id = baseline if baseline in index else None

    if not baseline_id:
        return None, ""

    p = index[baseline_id]
    cost = (p["prompt"] * input_tokens) + (p["completion"] * output_tokens)
    return cost, baseline_id


def list_paid_models_by_tier() -> dict:
    """
    Group paid models from the pricing index by tier for UI baseline dropdown.

    Returns:
        {
          "premium":  [{"id": "anthropic/claude-opus-4", "prompt": 1.5e-5, ...}, ...],
          "mid":      [...],
          "budget":   [...],
        }
    Tiers determined by completion price: premium >$1e-5, mid $1e-6..$1e-5, budget <$1e-6.
    """
    index = _load_pricing_index()
    premium, mid, budget = [], [], []
    for mid_id, p in index.items():
        comp = p.get("completion", 0) or 0
        entry = {
            "id": mid_id,
            "prompt": p.get("prompt", 0) or 0,
            "completion": comp,
        }
        if comp >= 1e-5:
            premium.append(entry)
        elif comp >= 1e-6:
            mid.append(entry)
        else:
            budget.append(entry)
    # Sort each tier by completion price descending (most-expensive first = "best")
    premium.sort(key=lambda x: -x["completion"])
    mid.sort(key=lambda x: -x["completion"])
    budget.sort(key=lambda x: -x["completion"])
    return {"premium": premium, "mid": mid, "budget": budget}


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
