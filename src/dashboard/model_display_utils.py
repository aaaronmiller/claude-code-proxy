"""
Shared utilities for formatting model names in dashboard displays.

These functions use dynamic model family detection to create consistent
shortened display names without hardcoding specific model versions.
"""

from src.services.models.model_family import detect_model_family, ModelFamily


def format_model_name(model_name: str) -> str:
    """
    Format model name for display using dynamic family detection.

    Returns shortened names like "claude-opus", "claude-sonnet", "gpt4o", "o1", "gemini"
    instead of full version strings.

    Args:
        model_name: Full model identifier

    Returns:
        Shortened display name
    """
    if not model_name:
        return "unknown"

    model_lower = model_name.lower()

    # Try dynamic family detection first
    try:
        family_info = detect_model_family(model_name)

        if family_info.family == ModelFamily.ANTHROPIC_CLAUDE:
            if family_info.tier:
                return f"claude-{family_info.tier}"
            return "claude"

        elif family_info.family == ModelFamily.OPENAI_GPT:
            if "mini" in model_lower or family_info.tier == "mini":
                return "gpt4o-mini"
            return "gpt4o"

        elif family_info.family == ModelFamily.OPENAI_O_SERIES:
            if family_info.tier == "mini":
                return "o1-mini"
            return "o1"

        elif family_info.family in (
            ModelFamily.GEMINI_FLASH,
            ModelFamily.GEMINI_PRO,
            ModelFamily.GEMINI_OTHER,
        ):
            if family_info.tier:
                return f"gemini-{family_info.tier}"
            return "gemini"

    except Exception:
        pass

    # Fallback to simple string matching for edge cases
    if "claude" in model_lower:
        if "opus" in model_lower:
            return "claude-opus"
        elif "sonnet" in model_lower:
            return "claude-sonnet"
        elif "haiku" in model_lower:
            return "claude-haiku"
        return "claude"
    elif "gpt-4o" in model_lower:
        return "gpt4o" + ("-mini" if "mini" in model_lower else "")
    elif "gpt-4" in model_lower:
        return "gpt4"
    elif "o1" in model_lower:
        return "o1" + ("-mini" if "mini" in model_lower else "")
    elif "o3" in model_lower:
        return "o3" + ("-mini" if "mini" in model_lower else "")
    elif "gemini" in model_lower:
        return "gemini"

    # Final fallback: strip provider prefix and truncate
    return model_name.split("/")[-1][:10] if "/" in model_name else model_name[:10]


def is_reasoning_model(model_name: str) -> bool:
    """Check if model supports reasoning/thinking (for cost estimation)."""
    if not model_name:
        return False
    model_lower = model_name.lower()

    # Check for reasoning models
    if any(p in model_lower for p in ["o1", "o3", "o4", "claude", "gemini"]):
        return True

    try:
        family_info = detect_model_family(model_name)
        return family_info.family in (
            ModelFamily.OPENAI_O_SERIES,
            ModelFamily.ANTHROPIC_CLAUDE,
            ModelFamily.GEMINI_PRO,
            ModelFamily.GEMINI_FLASH,
        )
    except Exception:
        return False
