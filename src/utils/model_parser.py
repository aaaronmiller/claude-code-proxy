"""
Model name parser utility for extracting reasoning parameters from model name suffixes.

Supports parsing model names with reasoning suffixes like:
- OpenAI o-series: o4-mini:high, o3:low
- Anthropic Claude: claude-opus-4-20250514:4k, claude-sonnet-4-20250514:8000
- Google Gemini: gemini-2.5-flash-preview-04-17:4k
"""

import re
from dataclasses import dataclass
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedModel:
    """Parsed model name with reasoning parameters."""
    
    base_model: str
    reasoning_type: Optional[str]  # 'effort', 'thinking_tokens', 'thinking_budget'
    reasoning_value: Optional[Union[str, int]]
    original_model: str


# Model family patterns for reasoning type detection
OPENAI_O_SERIES_PATTERN = re.compile(r'^(o1-|o3-|o4-mini|gpt-5)')
ANTHROPIC_THINKING_PATTERN = re.compile(r'^(claude-opus-4-|claude-sonnet-4-|claude-3-7-sonnet-)')
GEMINI_THINKING_PATTERN = re.compile(r'^gemini-2\.5-flash-preview-04-17')

# K-notation conversion mapping
K_NOTATION_MAP = {
    '1k': 1024,
    '4k': 4096,
    '8k': 8192,
    '16k': 16384,
    '24k': 24576
}


def _convert_k_notation(value: str) -> int:
    """
    Convert k-notation to exact token count.
    
    Args:
        value: String value like '1k', '4k', '8k', '16k'
        
    Returns:
        Exact token count as integer
        
    Raises:
        ValueError: If k-notation is not recognized
    """
    value_lower = value.lower()
    if value_lower in K_NOTATION_MAP:
        return K_NOTATION_MAP[value_lower]
    
    # Try to parse as number with 'k' suffix
    if value_lower.endswith('k'):
        try:
            num = int(value_lower[:-1])
            return num * 1024
        except ValueError:
            pass
    
    raise ValueError(f"Invalid k-notation: {value}")


def _detect_reasoning_type(base_model: str, suffix: Optional[str] = None) -> Optional[str]:
    """
    Detect reasoning type based on model family and suffix.
    
    Args:
        base_model: Base model name without suffix
        suffix: Optional suffix to help determine type
        
    Returns:
        Reasoning type: 'effort', 'thinking_tokens', 'thinking_budget', or None
    """
    if OPENAI_O_SERIES_PATTERN.match(base_model):
        # Check if suffix is numeric (token budget) or effort level
        if suffix and suffix.isdigit():
            return 'thinking_tokens'  # Arbitrary token budget for OpenAI
        return 'effort'
    elif ANTHROPIC_THINKING_PATTERN.match(base_model):
        return 'thinking_tokens'
    elif GEMINI_THINKING_PATTERN.match(base_model):
        return 'thinking_budget'
    
    return None


def parse_model_name(model_name: str) -> ParsedModel:
    """
    Parse model name with optional reasoning suffix.
    
    Suffix format: model_name:suffix
    
    Examples:
        'claude-opus-4-20250514:4k' → ParsedModel(
            base_model='claude-opus-4-20250514',
            reasoning_type='thinking_tokens',
            reasoning_value=4096,
            original_model='claude-opus-4-20250514:4k'
        )
        'o4-mini:high' → ParsedModel(
            base_model='o4-mini',
            reasoning_type='effort',
            reasoning_value='high',
            original_model='o4-mini:high'
        )
        'gpt-4' → ParsedModel(
            base_model='gpt-4',
            reasoning_type=None,
            reasoning_value=None,
            original_model='gpt-4'
        )
    
    Args:
        model_name: Model name with optional reasoning suffix
        
    Returns:
        ParsedModel with extracted components
    """
    # Use regex to split model name and suffix
    # Pattern: ^(.+?)(?::([^:]+))?$
    # Captures: (base_model)(optional :suffix)
    match = re.match(r'^(.+?)(?::([^:]+))?$', model_name)
    
    if not match:
        logger.warning(f"Failed to parse model name: {model_name}")
        return ParsedModel(
            base_model=model_name,
            reasoning_type=None,
            reasoning_value=None,
            original_model=model_name
        )
    
    base_model = match.group(1)
    suffix = match.group(2)
    
    # If no suffix, return base model only
    if not suffix:
        return ParsedModel(
            base_model=base_model,
            reasoning_type=None,
            reasoning_value=None,
            original_model=model_name
        )
    
    # Detect reasoning type based on model family and suffix
    reasoning_type = _detect_reasoning_type(base_model, suffix)
    
    if not reasoning_type:
        logger.warning(
            f"Model {base_model} does not support reasoning parameters. "
            f"Suffix '{suffix}' will be ignored."
        )
        return ParsedModel(
            base_model=base_model,
            reasoning_type=None,
            reasoning_value=None,
            original_model=model_name
        )
    
    # Parse suffix based on reasoning type
    reasoning_value: Optional[Union[str, int]] = None
    
    try:
        if reasoning_type == 'effort':
            # OpenAI o-series: expect 'low', 'medium', 'high', k-notation, or numeric token budget
            if suffix.isdigit():
                # Numeric suffix = arbitrary token budget
                reasoning_value = int(suffix)
                reasoning_type = 'thinking_tokens'  # Switch to token budget mode
            elif suffix.lower().endswith('k'):
                # K-notation = arbitrary token budget
                reasoning_value = _convert_k_notation(suffix)
                reasoning_type = 'thinking_tokens'  # Switch to token budget mode
            else:
                # Effort level
                reasoning_value = suffix.lower()
            
        elif reasoning_type in ('thinking_tokens', 'thinking_budget'):
            # Anthropic/Gemini/OpenAI token budgets: expect k-notation or exact number
            if suffix.lower().endswith('k'):
                reasoning_value = _convert_k_notation(suffix)
            else:
                # Try to parse as exact number
                reasoning_value = int(suffix)
                
    except (ValueError, KeyError) as e:
        logger.error(
            f"Failed to parse reasoning suffix '{suffix}' for model {base_model}: {e}"
        )
        return ParsedModel(
            base_model=base_model,
            reasoning_type=None,
            reasoning_value=None,
            original_model=model_name
        )
    
    logger.debug(
        f"Parsed model: {model_name} → base={base_model}, "
        f"type={reasoning_type}, value={reasoning_value}"
    )
    
    return ParsedModel(
        base_model=base_model,
        reasoning_type=reasoning_type,
        reasoning_value=reasoning_value,
        original_model=model_name
    )
