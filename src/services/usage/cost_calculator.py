"""
Cost calculation utility for API requests.

Provides accurate cost estimates based on model pricing and token usage.
Pricing data updated as of November 2025.
"""

from typing import Dict, Any, Optional, Tuple


# Pricing per 1M tokens (input_price, output_price)
# Source: Provider pricing pages (OpenAI, Anthropic, Google, etc.)
MODEL_PRICING = {
    # OpenAI models
    "gpt-5": (0.015, 0.060),
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.010, 0.030),
    "gpt-4": (0.030, 0.060),
    "gpt-3.5-turbo": (0.0015, 0.002),

    # OpenAI reasoning models
    "o1-preview": (0.015, 0.060),
    "o1-mini": (0.003, 0.012),
    "o3-mini": (0.003, 0.012),

    # Anthropic Claude models
    "claude-3.5-sonnet": (0.003, 0.015),
    "claude-3-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "claude-3-opus": (0.015, 0.075),
    "claude-4-sonnet": (0.003, 0.015),
    "claude-4": (0.015, 0.075),

    # Google Gemini models
    "gemini-pro": (0.001, 0.002),
    "gemini-1.5-pro": (0.001, 0.002),
    "gemini-1.5-flash": (0.0001, 0.0003),
    "gemini-2.0-flash": (0.0001, 0.0003),
    "gemini-flash": (0.0001, 0.0003),

    # Meta Llama models (via cloud providers)
    "llama-3.1-405b": (0.0027, 0.0027),
    "llama-3.1-70b": (0.00088, 0.00088),
    "llama-3.1-8b": (0.00018, 0.00018),
    "llama-3.3-70b": (0.00088, 0.00088),
    "llama-2-70b": (0.00070, 0.00090),

    # Mistral models
    "mistral-large": (0.002, 0.006),
    "mistral-medium": (0.00027, 0.00081),
    "mistral-small": (0.000068, 0.000204),
    "mixtral-8x7b": (0.00024, 0.00024),
    "mixtral-8x22b": (0.00065, 0.00065),

    # Cohere models
    "command-r-plus": (0.003, 0.015),
    "command-r": (0.00015, 0.0006),
    "command": (0.001, 0.002),

    # Qwen models
    "qwen-2.5-72b": (0.00035, 0.00140),
    "qwen-2.5-32b": (0.00018, 0.00072),
    "qwen-2.5-14b": (0.00010, 0.00040),
    "qwen-2.5-7b": (0.00005, 0.00020),
    "qwen3-235b": (0.0010, 0.0040),

    # DeepSeek models
    "deepseek-v3": (0.00027, 0.0011),
    "deepseek-r1": (0.00055, 0.0022),
    "deepseek-coder": (0.00014, 0.00028),

    # xAI Grok
    "grok-2": (0.002, 0.010),
    "grok-beta": (0.005, 0.015),

    # Local models (free)
    "ollama": (0.0, 0.0),
    "lmstudio": (0.0, 0.0),
}

# Provider-specific pricing multipliers for OpenRouter
# OpenRouter adds markup to base pricing
OPENROUTER_MARKUP = 1.05  # 5% markup


def get_model_pricing(model_id: str) -> Optional[Tuple[float, float]]:
    """
    Get pricing for a model.

    Args:
        model_id: Model identifier (e.g., "gpt-4o", "claude-3-sonnet")

    Returns:
        Tuple of (input_price_per_1m, output_price_per_1m) or None
    """
    model_lower = model_id.lower()

    # Check if it's a local model (free)
    if any(provider in model_lower for provider in ["ollama/", "lmstudio/", "local/"]):
        return (0.0, 0.0)

    # Try exact match first
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]

    # Try partial match (e.g., "openai/gpt-4o" matches "gpt-4o")
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower:
            # Apply OpenRouter markup if applicable
            if "openrouter" in model_lower:
                return (
                    pricing[0] * OPENROUTER_MARKUP,
                    pricing[1] * OPENROUTER_MARKUP
                )
            return pricing

    # Model not found in pricing database
    return None


def calculate_cost(
    usage: Dict[str, Any],
    model_id: str,
    include_thinking_tokens: bool = True
) -> float:
    """
    Calculate estimated cost for an API request.

    Args:
        usage: Usage dict with token counts
               Expected keys: input_tokens, output_tokens, thinking_tokens
               Also supports: prompt_tokens, completion_tokens, reasoning_tokens
        model_id: Model identifier
        include_thinking_tokens: Whether to include thinking/reasoning tokens in cost

    Returns:
        Estimated cost in USD
    """
    # Extract token counts (support multiple formats)
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))

    # Thinking/reasoning tokens (some models charge separately)
    thinking_tokens = 0
    if include_thinking_tokens:
        thinking_tokens = (
            usage.get("thinking_tokens", 0) or
            usage.get("reasoning_tokens", 0)
        )

        # Check if completion_tokens_details exists (OpenAI format)
        details = usage.get("completion_tokens_details", {})
        if isinstance(details, dict):
            thinking_tokens = max(thinking_tokens, details.get("reasoning_tokens", 0))

    # Get pricing for model
    pricing = get_model_pricing(model_id)

    if not pricing:
        # Unknown model, return 0 cost
        return 0.0

    input_price, output_price = pricing

    # Calculate cost (prices are per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * input_price

    # Output tokens include thinking tokens for most models
    total_output = output_tokens + thinking_tokens
    output_cost = (total_output / 1_000_000) * output_price

    total_cost = input_cost + output_cost

    return round(total_cost, 6)


def estimate_cost_from_text(
    text: str,
    model_id: str,
    is_input: bool = True
) -> float:
    """
    Estimate cost from raw text (without token counts).

    Uses rough approximation: ~4 characters per token

    Args:
        text: Input or output text
        model_id: Model identifier
        is_input: True if this is input text, False if output

    Returns:
        Estimated cost in USD
    """
    # Rough token estimate
    estimated_tokens = max(1, len(text) // 4)

    # Get pricing
    pricing = get_model_pricing(model_id)

    if not pricing:
        return 0.0

    input_price, output_price = pricing
    price = input_price if is_input else output_price

    cost = (estimated_tokens / 1_000_000) * price

    return round(cost, 6)


def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0123", "$1.23", "<$0.0001")
    """
    if cost == 0.0:
        return "$0.00"
    elif cost < 0.0001:
        return "<$0.0001"
    elif cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1.0:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def get_cost_summary(
    requests: list[Dict[str, Any]],
    group_by: str = "model"
) -> Dict[str, Any]:
    """
    Calculate cost summary for multiple requests.

    Args:
        requests: List of request dicts with 'usage' and 'model' keys
        group_by: Grouping criterion - "model", "date", or "total"

    Returns:
        Summary dict with cost breakdowns
    """
    if group_by == "total":
        total_cost = sum(
            calculate_cost(req.get("usage", {}), req.get("model", ""))
            for req in requests
        )
        return {
            "total_cost": total_cost,
            "total_requests": len(requests)
        }

    elif group_by == "model":
        from collections import defaultdict

        by_model = defaultdict(lambda: {"cost": 0.0, "requests": 0})

        for req in requests:
            model = req.get("model", "unknown")
            cost = calculate_cost(req.get("usage", {}), model)

            by_model[model]["cost"] += cost
            by_model[model]["requests"] += 1

        return dict(by_model)

    else:
        raise ValueError(f"Unknown group_by: {group_by}")


# Export main functions
__all__ = [
    "calculate_cost",
    "estimate_cost_from_text",
    "get_model_pricing",
    "format_cost",
    "get_cost_summary",
]
