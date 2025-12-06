"""
Model context window and output limits database.

Loads model limits from scraped OpenRouter data (CSV/JSON files).
Falls back to static database if files don't exist.

Run `python scripts/scrape_openrouter_models.py` to update the database.
"""

from typing import Dict, Optional, Tuple
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to model limits files
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
JSON_PATH = MODELS_DIR / "model_limits.json"

# Cache for loaded model limits
_MODEL_LIMITS_CACHE: Optional[Dict[str, Dict[str, int]]] = None


def _load_model_limits() -> Dict[str, Dict[str, int]]:
    """Load model limits from JSON file or return fallback."""
    global _MODEL_LIMITS_CACHE
    
    if _MODEL_LIMITS_CACHE is not None:
        return _MODEL_LIMITS_CACHE
    
    # Try to load from scraped JSON file
    if JSON_PATH.exists():
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)
                _MODEL_LIMITS_CACHE = data
                logger.info(f"Loaded {len(data)} model limits from {JSON_PATH}")
                return _MODEL_LIMITS_CACHE
        except Exception as e:
            logger.warning(f"Failed to load model limits from {JSON_PATH}: {e}")
    
    # Fallback to static database
    logger.info("Using static fallback model limits (run scraper to update)")
    _MODEL_LIMITS_CACHE = _get_fallback_limits()
    return _MODEL_LIMITS_CACHE


def _get_fallback_limits() -> Dict[str, Dict[str, int]]:
    """Get static fallback model limits."""
    return {
        # OpenAI Models
        "openai/gpt-4o": {"context": 128000, "output": 16384},
        "openai/gpt-4o-mini": {"context": 128000, "output": 16384},
        "openai/o1-preview": {"context": 128000, "output": 32768},
        "openai/o1-mini": {"context": 128000, "output": 65536},
        "openai/gpt-5": {"context": 200000, "output": 100000},
        
        # Anthropic Claude
        "anthropic/claude-opus-4-20250514": {"context": 200000, "output": 16384},
        "anthropic/claude-sonnet-4-20250514": {"context": 200000, "output": 16384},
        "anthropic/claude-3-5-sonnet-20241022": {"context": 200000, "output": 8192},
        
        # Google Gemini
        "google/gemini-2.5-flash-preview-04-17": {"context": 1000000, "output": 8192},
        "google/gemini-2.0-flash": {"context": 1000000, "output": 8192},
        
        # Meta Llama
        "meta-llama/llama-3.3-70b": {"context": 128000, "output": 4096},
        
        # DeepSeek
        "deepseek/deepseek-v3": {"context": 64000, "output": 8192},
        
        # Qwen
        "qwen/qwen-2.5-72b": {"context": 32768, "output": 8192},
        
        # xAI
        "x-ai/grok-2": {"context": 131072, "output": 32768},
        "x-ai/grok-4.1-fast:free": {"context": 128000, "output": 4096},
    }


def get_model_limits(model_name: str) -> Tuple[int, int]:
    """
    Get context window and output limits for a model.
    
    Args:
        model_name: Model identifier (e.g., "gpt-4o", "openai/gpt-5")
        
    Returns:
        Tuple of (context_limit, output_limit) in tokens
        Returns (128000, 4096) as conservative defaults if not found
    """
    MODEL_LIMITS = _load_model_limits()
    
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
    
    # Try with provider prefix if not present
    if "/" not in model_name:
        for prefix in ["openai/", "anthropic/", "google/", "meta-llama/", "deepseek/", "qwen/", "x-ai/"]:
            prefixed = f"{prefix}{model_name}"
            if prefixed in MODEL_LIMITS:
                limits = MODEL_LIMITS[prefixed]
                logger.debug(f"Found {model_name} with prefix: {prefixed}")
                return limits["context"], limits["output"]
    
    # Default fallback for unknown models
    logger.warning(f"Model limits not found for {model_name}, using defaults (128k/4k)")
    return 128000, 4096


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


def reload_model_limits() -> int:
    """
    Reload model limits from file (useful after running scraper).
    
    Returns:
        Number of models loaded
    """
    global _MODEL_LIMITS_CACHE
    _MODEL_LIMITS_CACHE = None
    limits = _load_model_limits()
    return len(limits)


def check_model_limits(model_name: str, input_tokens: int, max_output_tokens: int = 0) -> Tuple[bool, str]:
    """
    Check if request exceeds model limits.
    
    Args:
        model_name: Model identifier
        input_tokens: Estimated input tokens
        max_output_tokens: Requested max output tokens
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    context_limit, output_limit = get_model_limits(model_name)
    
    # Check context limit (input + output)
    total_tokens = input_tokens + max_output_tokens
    if total_tokens > context_limit:
        return False, f"Total tokens ({total_tokens}) exceeds model context limit ({context_limit})"
        
    # Check output limit
    if max_output_tokens > output_limit:
        return False, f"Requested output tokens ({max_output_tokens}) exceeds model output limit ({output_limit})"
        
    return True, ""

