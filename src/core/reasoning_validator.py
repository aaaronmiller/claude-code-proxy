"""
Reasoning parameter validator for OpenAI, Anthropic, and Gemini models.

Validates and adjusts reasoning parameters to provider-specific constraints:
- OpenAI o-series: effort levels (low, medium, high)
- Anthropic Claude: thinking token budget (1024-16000)
- Google Gemini: thinking budget (0-24576)
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


# Valid OpenAI reasoning effort levels
VALID_EFFORT_LEVELS = {'low', 'medium', 'high'}

# Anthropic thinking token constraints
ANTHROPIC_MIN_TOKENS = 1024
ANTHROPIC_MAX_TOKENS = 128000

# Gemini thinking budget constraints
GEMINI_MIN_BUDGET = 0
GEMINI_MAX_BUDGET = 24576

# Model capability patterns
OPENAI_O_SERIES_PATTERNS = [
    re.compile(r'^o1-'),
    re.compile(r'^o3-'),
    re.compile(r'^o4-mini'),
    re.compile(r'^gpt-5')
]

ANTHROPIC_THINKING_PATTERNS = [
    re.compile(r'^claude-opus-4-'),
    re.compile(r'^claude-sonnet-4-'),
    re.compile(r'^claude-3-7-sonnet-')
]

GEMINI_THINKING_PATTERNS = [
    re.compile(r'^gemini-2\.5-flash-preview-04-17')
]


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
    
    Args:
        model_name: Model name to check
        
    Returns:
        Tuple of (is_capable, reasoning_type)
        - is_capable: True if model supports reasoning
        - reasoning_type: 'effort', 'thinking_tokens', 'thinking_budget', or empty string
    """
    # Check OpenAI o-series
    for pattern in OPENAI_O_SERIES_PATTERNS:
        if pattern.match(model_name):
            logger.debug(f"Model {model_name} supports OpenAI reasoning effort")
            return True, 'effort'
    
    # Check Anthropic thinking tokens
    for pattern in ANTHROPIC_THINKING_PATTERNS:
        if pattern.match(model_name):
            logger.debug(f"Model {model_name} supports Anthropic thinking tokens")
            return True, 'thinking_tokens'
    
    # Check Gemini thinking budget
    for pattern in GEMINI_THINKING_PATTERNS:
        if pattern.match(model_name):
            logger.debug(f"Model {model_name} supports Gemini thinking budget")
            return True, 'thinking_budget'
    
    logger.debug(f"Model {model_name} does not support reasoning capabilities")
    return False, ''
