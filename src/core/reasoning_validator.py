"""
Reasoning parameter validator for OpenAI, Anthropic, and Gemini models.

Validates and adjusts reasoning parameters to provider-specific constraints:
- OpenAI o-series: effort levels (low, medium, high)
- Anthropic Claude: thinking token budget (1024-128000)
- Google Gemini: thinking budget (0-24576)

Capability detection uses keyword-based matching rather than version-specific
regex patterns, so new model versions are automatically supported.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


# Valid OpenAI reasoning effort levels
VALID_EFFORT_LEVELS = {"low", "medium", "high"}

# Anthropic thinking token constraints
ANTHROPIC_MIN_TOKENS = 1024
ANTHROPIC_MAX_TOKENS = 128000

# Gemini thinking budget constraints
GEMINI_MIN_BUDGET = 0
GEMINI_MAX_BUDGET = 24576

# Keyword-based model family detection (version-agnostic)
# These keywords identify model families without pinning to specific versions.
# Adding a new model version (e.g., opus-4.7, gemini-4-flash) requires NO code changes.

OPENAI_O_SERIES_KEYWORDS = [
    "o1-",
    "o1mini",
    "o3-",
    "o3mini",
    "o4-",
    "o4mini",
    "gpt-5",
    "gpt5",
]
ANTHROPIC_THINKING_KEYWORDS = ["opus", "sonnet", "claude-3-7", "claude-3.7"]
GEMINI_THINKING_KEYWORDS = [
    "thinking",
    "gemini-2",
    "gemini-2.5",
    "gemini-pro",
    "gemini-flash",
]  # Gemini 2.x and flash models support thinking


def _is_openai_reasoning_model(model_lower: str) -> bool:
    """Detect OpenAI o-series / GPT-5+ reasoning models by keyword."""
    return any(kw in model_lower for kw in OPENAI_O_SERIES_KEYWORDS)


def _is_anthropic_thinking_model(model_lower: str) -> bool:
    """Detect Anthropic Claude thinking-capable models by keyword."""
    return "claude" in model_lower and any(
        kw in model_lower for kw in ANTHROPIC_THINKING_KEYWORDS
    )


def _is_gemini_thinking_model(model_lower: str) -> bool:
    """Detect Gemini thinking-capable models by keyword."""
    return "gemini" in model_lower and any(
        kw in model_lower for kw in GEMINI_THINKING_KEYWORDS
    )


def validate_openai_reasoning(effort: str) -> str:
    """
    Validate OpenAI reasoning effort level.

    Args:
        effort: Reasoning effort level (low, medium, high)

    Returns:
        Validated effort level (lowercase)

    Raises:
        ValueError: If effort level is not valid
    """
    effort_lower = effort.lower()

    if effort_lower not in VALID_EFFORT_LEVELS:
        raise ValueError(
            f"Invalid reasoning effort '{effort}'. "
            f"Valid options: {', '.join(sorted(VALID_EFFORT_LEVELS))}"
        )

    logger.debug(f"Validated OpenAI reasoning effort: {effort_lower}")
    return effort_lower


def validate_anthropic_thinking(budget: int) -> int:
    """
    Validate and adjust Anthropic thinking token budget to valid range (1024-16000).

    Args:
        budget: Thinking token budget

    Returns:
        Adjusted budget within valid range
    """
    original_budget = budget

    if budget < ANTHROPIC_MIN_TOKENS:
        budget = ANTHROPIC_MIN_TOKENS
        logger.warning(
            f"Anthropic thinking token budget {original_budget} is below minimum. "
            f"Adjusted to {budget}. Valid range: {ANTHROPIC_MIN_TOKENS}-{ANTHROPIC_MAX_TOKENS}"
        )
    elif budget > ANTHROPIC_MAX_TOKENS:
        budget = ANTHROPIC_MAX_TOKENS
        logger.warning(
            f"Anthropic thinking token budget {original_budget} exceeds maximum. "
            f"Adjusted to {budget}. Valid range: {ANTHROPIC_MIN_TOKENS}-{ANTHROPIC_MAX_TOKENS}"
        )
    else:
        logger.debug(f"Validated Anthropic thinking budget: {budget}")

    return budget


def validate_gemini_thinking(budget: int) -> int:
    """
    Validate and adjust Gemini thinking budget to valid range (0-24576).

    Args:
        budget: Thinking budget

    Returns:
        Adjusted budget within valid range
    """
    original_budget = budget

    if budget < GEMINI_MIN_BUDGET:
        budget = GEMINI_MIN_BUDGET
        logger.warning(
            f"Gemini thinking budget {original_budget} is below minimum. "
            f"Adjusted to {budget}. Valid range: {GEMINI_MIN_BUDGET}-{GEMINI_MAX_BUDGET}"
        )
    elif budget > GEMINI_MAX_BUDGET:
        budget = GEMINI_MAX_BUDGET
        logger.warning(
            f"Gemini thinking budget {original_budget} exceeds maximum. "
            f"Adjusted to {budget}. Valid range: {GEMINI_MIN_BUDGET}-{GEMINI_MAX_BUDGET}"
        )
    else:
        logger.debug(f"Validated Gemini thinking budget: {budget}")

    return budget


def is_reasoning_capable_model(model_name: str) -> Tuple[bool, str]:
    """
    Check if model supports reasoning capabilities.

    Uses keyword-based detection so new model versions are automatically supported.
    For example, 'gemini-claude-opus-4-6-thinking' matches because it contains
    both 'claude' and 'opus' keywords.

    Args:
        model_name: Model name to check

    Returns:
        Tuple of (is_capable, reasoning_type)
        - is_capable: True if model supports reasoning
        - reasoning_type: 'effort', 'thinking_tokens', 'thinking_budget', or empty string
    """
    # Strip provider prefix if present (e.g., "anthropic/claude-opus-4" → "claude-opus-4")
    model_lower = model_name.lower()
    if "/" in model_lower:
        model_lower = model_lower.split("/", 1)[1]

    # Check Gemini thinking budget first (before Anthropic, because hybrid names
    # like "gemini-claude-opus-4-6-thinking" should be routed as Gemini)
    if _is_gemini_thinking_model(model_lower):
        logger.debug(f"Model {model_name} supports Gemini thinking budget")
        return True, "thinking_budget"

    # Check OpenAI o-series
    if _is_openai_reasoning_model(model_lower):
        logger.debug(f"Model {model_name} supports OpenAI reasoning effort")
        return True, "effort"

    # Check Anthropic thinking tokens
    if _is_anthropic_thinking_model(model_lower):
        logger.debug(f"Model {model_name} supports Anthropic thinking tokens")
        return True, "thinking_tokens"

    logger.debug(f"Model {model_name} does not support reasoning capabilities")
    return False, ""
