"""
Model context window and output limits database.

Provides context limits and max output tokens for various models.
Data sourced from OpenRouter, OpenAI, Anthropic, and Google documentation.
"""

from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Static model limits database
# Format: "model_id": {"context": tokens, "output": tokens}
MODEL_LIMITS = {
    # OpenAI Models
    "gpt-4o": {"context": 128000, "output": 16384},
    "gpt-4o-mini": {"context": 128000, "output": 16384},
    "gpt-4-turbo": {"context": 128000, "output": 4096},
    "gpt-4": {"context": 8192, "output": 4096},
    "gpt-3.5-turbo": {"context": 16385, "output": 4096},
    
    # OpenAI o-series (reasoning models)
    "o1-preview": {"context": 128000, "output": 32768},
    "o1-mini": {"context": 128000, "output": 65536},
    "o3-mini": {"context": 200000, "output": 100000},
    "o4-mini": {"context": 200000, "output": 100000},
    "gpt-5": {"context": 200000, "output": 100000},
    
    # Anthropic Claude Models
    "claude-3-opus-20240229": {"context": 200000, "output": 4096},
    "claude-3-sonnet-20240229": {"context": 200000, "output": 4096},
    "claude-3-haiku-20240307": {"context": 200000, "output": 4096},
    "claude-3-5-sonnet-20241022": {"context": 200000, "output": 8192},
    "claude-3-5-haiku-20241022": {"context": 200000, "output": 8192},
    
    # Anthropic Claude 4.x (with thinking tokens)
    "claude-opus-4-20250514": {"context": 200000, "output": 16384},
    "claude-sonnet-4-20250514": {"context": 200000, "output": 16384},
    "claude-3-7-sonnet-20250219": {"context": 200000, "output": 16384},
    
    # Google Gemini Models
    "gemini-1.5-pro": {"context": 2000000, "output": 8192},
    "gemini-1.5-flash": {"context": 1000000, "output": 8192},
    "gemini-2.0-flash": {"context": 1000000, "output": 8192},
    "gemini-2.5-flash-preview-04-17": {"context": 1000000, "output": 8192},
    
    # DeepSeek Models
    "deepseek-chat": {"context": 64000, "output": 4096},
    "deepseek-coder": {"context": 16000, "output": 4096},
    "deepseek-v3": {"context": 64000, "output": 8192},
    
    # Qwen Models
    "qwen-2.5-72b": {"context": 32768, "output": 8192},
    "qwen-2.5-coder-32b": {"context": 131072, "output": 8192},
    "qwen3-4b-thinking": {"context": 32768, "output": 8192},
    
    # Mistral Models
    "mistral-large": {"context": 128000, "output": 4096},
    "mistral-medium": {"context": 32000, "output": 4096},
    "mistral-small": {"context": 32000, "output": 4096},
    
    # Meta Llama Models
    "llama-3.1-405b": {"context": 128000, "output": 4096},
    "llama-3.1-70b": {"context": 128000, "output": 4096},
    "llama-3.1-8b": {"context": 128000, "output": 4096},
    "llama-3.3-70b": {"context": 128000, "output": 4096},
    
    # xAI Grok Models
    "grok-2": {"context": 131072, "output": 32768},
    "grok-2-vision": {"context": 32768, "output": 16384},
    
    # Cohere Models
    "command-r-plus": {"context": 128000, "output": 4096},
    "command-r": {"context": 128000, "output": 4096},
    
    # OpenRouter prefixed models
    "openai/gpt-4o": {"context": 128000, "output": 16384},
    "openai/gpt-4o-mini": {"context": 128000, "output": 16384},
    "openai/o1-preview": {"context": 128000, "output": 32768},
    "openai/o1-mini": {"context": 128000, "output": 65536},
    "openai/gpt-5": {"context": 200000, "output": 100000},
    "anthropic/claude-opus-4-20250514": {"context": 200000, "output": 16384},
    "anthropic/claude-sonnet-4-20250514": {"context": 200000, "output": 16384},
    "anthropic/claude-3-5-sonnet-20241022": {"context": 200000, "output": 8192},
    "google/gemini-2.5-flash-preview-04-17": {"context": 1000000, "output": 8192},
    "google/gemini-2.0-flash": {"context": 1000000, "output": 8192},
    "meta-llama/llama-3.3-70b": {"context": 128000, "output": 4096},
    "deepseek/deepseek-v3": {"context": 64000, "output": 8192},
    "qwen/qwen-2.5-72b": {"context": 32768, "output": 8192},
    "x-ai/grok-2": {"context": 131072, "output": 32768},
}


def get_model_limits(model_name: str) -> Tuple[int, int]:
    """
    Get context window and output limits for a model.
    
    Args:
        model_name: Model identifier (e.g., "gpt-4o", "claude-opus-4-20250514")
        
    Returns:
        Tuple of (context_limit, output_limit) in tokens
        Returns (0, 0) if model not found
    """
    # Try exact match first
    if model_name in MODEL_LIMITS:
        limits = MODEL_LIMITS[model_name]
        return limits["context"], limits["output"]
    
    # Try case-insensitive match
    model_lower = model_name.lower()
    for key, limits in MODEL_LIMITS.items():
        if key.lower() == model_lower:
            return limits["context"], limits["output"]
    
    # Try partial match (for versioned models)
    for key, limits in MODEL_LIMITS.items():
        if key in model_name or model_name in key:
            logger.debug(f"Partial match for {model_name}: using limits from {key}")
            return limits["context"], limits["output"]
    
    # Try without provider prefix
    if "/" in model_name:
        base_name = model_name.split("/", 1)[1]
        if base_name in MODEL_LIMITS:
            limits = MODEL_LIMITS[base_name]
            return limits["context"], limits["output"]
    
    # Default fallback for unknown models
    logger.warning(f"Model limits not found for {model_name}, using defaults")
    return 128000, 4096  # Conservative defaults


def get_context_limit(model_name: str) -> int:
    """Get context window limit for a model."""
    context, _ = get_model_limits(model_name)
    return context


def get_output_limit(model_name: str) -> int:
    """Get max output tokens for a model."""
    _, output = get_model_limits(model_name)
    return output


def format_model_info(model_name: str) -> str:
    """
    Format model limits as a readable string.
    
    Returns:
        String like "128k context / 16k output"
    """
    context, output = get_model_limits(model_name)
    
    def format_tokens(count):
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.0f}k"
        return str(count)
    
    return f"{format_tokens(context)} context / {format_tokens(output)} output"
