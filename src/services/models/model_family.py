"""
Dynamic Model Family Detection

Provides version-agnostic model family detection. Instead of hardcoding specific
model names (e.g., "claude-opus-4-20250514"), this module uses flexible pattern
matching to detect model families (e.g., "claude-opus", "gemini-flash", "o-series").

This ensures the proxy remains functional when providers update model versions
without breaking the entire codebase.
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ModelFamily(Enum):
    """Model family categories for routing and transformation logic."""

    OPENAI_O_SERIES = "openai_o_series"  # o1, o3, o4, etc.
    OPENAI_GPT = "openai_gpt"  # gpt-4, gpt-5, etc.
    ANTHROPIC_CLAUDE = "anthropic_claude"  # claude-opus, claude-sonnet, claude-haiku
    GEMINI_FLASH = "gemini_flash"  # gemini-flash, gemini-2.0-flash, etc.
    GEMINI_PRO = "gemini_pro"  # gemini-pro, gemini-2.0-pro, etc.
    GEMINI_OTHER = "gemini_other"  # Other Gemini models
    OTHER = "other"


@dataclass
class ModelFamilyInfo:
    """Information about a detected model family."""

    family: ModelFamily
    provider: str  # openai, anthropic, google, openrouter
    base_name: str  # e.g., "claude-opus", "gemini-flash"
    version: Optional[str]  # e.g., "4", "2.0", "3.5"
    tier: Optional[str]  # "flash", "pro", "opus", "sonnet", "haiku"


# Dynamic detection patterns - version-agnostic
MODEL_FAMILY_PATTERNS = [
    # OpenAI O-Series (o1, o1-mini, o3, o3-mini, o4, o4-mini, etc.)
    (r"^(?:openai/)?(o\d+-?mini?)", ModelFamily.OPENAI_O_SERIES),
    (r"^(?:openai/)?(o\d+)", ModelFamily.OPENAI_O_SERIES),
    # OpenAI GPT series
    (r"^(?:openai/)?gpt-5", ModelFamily.OPENAI_GPT),
    (r"^(?:openai/)?gpt-4o(?:-?\d+)?", ModelFamily.OPENAI_GPT),
    (r"^(?:openai/)?gpt-4turbo", ModelFamily.OPENAI_GPT),
    (r"^(?:openai/)?gpt-4", ModelFamily.OPENAI_GPT),
    (r"^(?:openai/)?gpt-3\.5", ModelFamily.OPENAI_GPT),
    # Anthropic Claude
    (r"^(?:anthropic/)?claude-opus[-\s]?(\d+)", ModelFamily.ANTHROPIC_CLAUDE),
    (r"^(?:anthropic/)?claude-sonnet[-\s]?(\d+)", ModelFamily.ANTHROPIC_CLAUDE),
    (r"^(?:anthropic/)?claude-haiku[-\s]?(\d+)", ModelFamily.ANTHROPIC_CLAUDE),
    (
        r"^(?:anthropic/)?claude-3[-\s]?(?:opus|sonnet|haiku)",
        ModelFamily.ANTHROPIC_CLAUDE,
    ),
    (r"^(?:anthropic/)?claude-3\.5", ModelFamily.ANTHROPIC_CLAUDE),
    (r"^(?:anthropic/)?claude-3\.7", ModelFamily.ANTHROPIC_CLAUDE),
    # Anthropic with provider prefix variants
    (
        r"^(?:openrouter/)?(?:anthropic/)?claude-(opus|sonnet|haiku)",
        ModelFamily.ANTHROPIC_CLAUDE,
    ),
    (
        r"^(?:vibeproxy|antigravity)/claude-(opus|sonnet|haiku)",
        ModelFamily.ANTHROPIC_CLAUDE,
    ),
    # Gemini Flash
    (r"^(?:google/)?gemini[-\s]?(\d+\.\d+)?[-\s]?flash", ModelFamily.GEMINI_FLASH),
    (r"^(?:google/)?gemini-flash", ModelFamily.GEMINI_FLASH),
    # Gemini Pro
    (r"^(?:google/)?gemini[-\s]?(\d+\.\d+)?[-\s]?pro", ModelFamily.GEMINI_PRO),
    (r"^(?:google/)?gemini-pro", ModelFamily.GEMINI_PRO),
    # Gemini with "thinking" suffix
    (r"^(?:google/)?gemini[-\s]?.*thinking", ModelFamily.GEMINI_PRO),
    # Other Gemini
    (r"^(?:google/)?gemini", ModelFamily.GEMINI_OTHER),
]


def detect_model_family(model_name: str) -> ModelFamilyInfo:
    """
    Detect model family from model name using flexible pattern matching.

    This function is version-agnostic - it detects model families rather than
    specific versions, so it works with new model releases without code changes.

    Args:
        model_name: Model identifier (with or without provider prefix)
                    e.g., "claude-opus-4-20250514", "openai/o1-mini", "gemini-2.0-flash"

    Returns:
        ModelFamilyInfo with detected family, provider, and metadata
    """
    model_lower = model_name.lower()

    # Extract provider prefix if present
    provider = "unknown"
    base_name = model_lower

    if "/" in model_name:
        provider_part, base_name = model_lower.split("/", 1)
        # Normalize provider names
        provider_map = {
            "openai": "openai",
            "anthropic": "anthropic",
            "google": "google",
            "vibeproxy": "vibeproxy",
            "antigravity": "antigravity",
            "openrouter": "openrouter",
            "minimax": "minimax",
            "stepfun": "stepfun",
            "nvidia": "nvidia",
        }
        provider = provider_map.get(provider_part, provider_part)

    # Try each pattern
    for pattern, family in MODEL_FAMILY_PATTERNS:
        match = re.match(pattern, base_name)
        if match:
            # Extract version if present
            version = None
            tier = None

            if match.groups():
                potential = match.group(1)
                if potential:
                    # Check if it's a version number or tier
                    if potential.replace(".", "").isdigit():
                        version = potential
                    else:
                        tier = potential

            # Determine tier from pattern match
            if family == ModelFamily.ANTHROPIC_CLAUDE:
                if "opus" in base_name:
                    tier = "opus"
                elif "sonnet" in base_name:
                    tier = "sonnet"
                elif "haiku" in base_name:
                    tier = "haiku"
            elif family == ModelFamily.GEMINI_FLASH:
                tier = "flash"
            elif family == ModelFamily.GEMINI_PRO:
                tier = "pro"
            elif family == ModelFamily.OPENAI_O_SERIES:
                if "mini" in base_name:
                    tier = "mini"

            return ModelFamilyInfo(
                family=family,
                provider=provider,
                base_name=base_name,
                version=version,
                tier=tier,
            )

    # No match - return OTHER
    return ModelFamilyInfo(
        family=ModelFamily.OTHER,
        provider=provider,
        base_name=base_name,
        version=None,
        tier=None,
    )


def is_reasoning_model(model_name: str) -> bool:
    """
    Check if a model supports reasoning/thinking parameters.

    Version-agnostic: detects any o-series, claude with thinking, or gemini with thinking.
    """
    family_info = detect_model_family(model_name)
    return family_info.family in (
        ModelFamily.OPENAI_O_SERIES,
        ModelFamily.ANTHROPIC_CLAUDE,
        ModelFamily.GEMINI_PRO,
        ModelFamily.GEMINI_FLASH,  # Some flash models support thinking
    )


def requires_thinking_budget(model_name: str) -> bool:
    """Check if model requires thinking_budget parameter (Gemini-style)."""
    family_info = detect_model_family(model_name)
    return family_info.family in (ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_FLASH)


def requires_thinking_tokens(model_name: str) -> bool:
    """Check if model requires thinking_tokens parameter (Anthropic-style)."""
    family_info = detect_model_family(model_name)
    return family_info.family == ModelFamily.ANTHROPIC_CLAUDE


def requires_effort_level(model_name: str) -> bool:
    """Check if model requires effort level (OpenAI o-series style)."""
    family_info = detect_model_family(model_name)
    return family_info.family == ModelFamily.OPENAI_O_SERIES


def get_provider_for_model(model_name: str) -> str:
    """Extract or infer provider from model name."""
    family_info = detect_model_family(model_name)
    return family_info.provider


# Convenience function for backward compatibility
get_model_family = detect_model_family
