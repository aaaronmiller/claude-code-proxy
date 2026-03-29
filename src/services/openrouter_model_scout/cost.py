"""
Cost estimation utilities.
Calculates estimated cost from token usage and model pricing.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def calculate_estimated_cost(
    pricing,
    token_usage: Dict[str, int]
) -> float:
    """
    Calculate estimated cost for a run based on token usage and pricing.

    Args:
        pricing: Pricing model object OR dict with keys: prompt (per 1M), completion (per 1M), cache_read, cache_write (optional)
        token_usage: Dict with prompt_tokens, completion_tokens, (optional) cache_read_tokens, cache_write_tokens

    Returns:
        Estimated cost in USD
    """
    # Support both Pydantic model and dict
    if hasattr(pricing, 'prompt'):
        prompt_rate = pricing.prompt
        completion_rate = pricing.completion
        cache_read_rate = getattr(pricing, 'cache_read', 0.0)
        cache_write_rate = getattr(pricing, 'cache_write', 0.0)
    else:
        prompt_rate = pricing.get('prompt', 0.0)
        completion_rate = pricing.get('completion', 0.0)
        cache_read_rate = pricing.get('cache_read', 0.0)
        cache_write_rate = pricing.get('cache_write', 0.0)

    prompt_tokens = token_usage.get('prompt_tokens', 0)
    completion_tokens = token_usage.get('completion_tokens', 0)
    cache_read_tokens = token_usage.get('cache_read_tokens', 0)
    cache_write_tokens = token_usage.get('cache_write_tokens', 0)

    # Prices are per 1M tokens; convert
    cost = (
        (prompt_tokens / 1_000_000) * prompt_rate +
        (completion_tokens / 1_000_000) * completion_rate +
        (cache_read_tokens / 1_000_000) * cache_read_rate +
        (cache_write_tokens / 1_000_000) * (cache_write_rate or 0.0)
    )

    return round(cost, 6)  # Microunits precision is enough
