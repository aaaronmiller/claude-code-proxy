"""
Model configuration presets for E2E integration tests.

Each configuration defines BIG, MIDDLE, and SMALL models with their routing.
Tests will iterate through these configurations to verify multi-provider support.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration for a test run."""
    name: str
    big_model: str
    middle_model: str
    small_model: str
    description: str
    requires_vibeproxy: bool = False
    requires_openrouter: bool = False
    requires_direct_api: bool = False
    

# ═══════════════════════════════════════════════════════════════════════════════
# TEST CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

# All models via VibeProxy (FREE - uses local OAuth)
ALL_VIBEPROXY = ModelConfig(
    name="all_vibeproxy",
    big_model="vibeproxy/gemini-2.5-pro",
    middle_model="vibeproxy/claude-sonnet-4",
    small_model="vibeproxy/gpt-4o",
    description="All models routed through VibeProxy (port 8317)",
    requires_vibeproxy=True,
)

# All models via OpenRouter
ALL_OPENROUTER = ModelConfig(
    name="all_openrouter",
    big_model="openrouter/anthropic/claude-3.5-sonnet",
    middle_model="openrouter/openai/gpt-4o",
    small_model="openrouter/google/gemini-pro-1.5",
    description="All models routed through OpenRouter API",
    requires_openrouter=True,
)

# VibeProxy for BIG/MIDDLE, OpenRouter for SMALL
VIBEPROXY_BIG_OPENROUTER_SMALL = ModelConfig(
    name="vibeproxy_big_openrouter_small",
    big_model="vibeproxy/gemini-3-pro",
    middle_model="vibeproxy/gemini-3-pro",
    small_model="openrouter/meta-llama/llama-3.1-70b-instruct",
    description="VibeProxy for primary tiers, OpenRouter for small tasks",
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# Mixed providers - one from each
MIXED_PROVIDERS = ModelConfig(
    name="mixed_providers",
    big_model="vibeproxy/gemini-2.5-pro",
    middle_model="openrouter/anthropic/claude-3.5-sonnet",
    small_model="openrouter/openai/gpt-4o-mini",
    description="Different provider for each tier",
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# Gemini-only via VibeProxy
GEMINI_ONLY = ModelConfig(
    name="gemini_only",
    big_model="vibeproxy/gemini-2.5-pro",
    middle_model="vibeproxy/gemini-2.5-flash",
    small_model="vibeproxy/gemini-2.0-flash-thinking",
    description="All Gemini models via VibeProxy",
    requires_vibeproxy=True,
)

# Claude-only via VibeProxy
CLAUDE_ONLY = ModelConfig(
    name="claude_only",
    big_model="vibeproxy/claude-opus-4",
    middle_model="vibeproxy/claude-sonnet-4",
    small_model="vibeproxy/claude-sonnet-4",
    description="All Claude models via VibeProxy",
    requires_vibeproxy=True,
)

# FREE OpenRouter models (no credit cost)
FREE_OPENROUTER = ModelConfig(
    name="free_openrouter",
    big_model="openrouter/meta-llama/llama-3.1-8b-instruct:free",
    middle_model="openrouter/qwen/qwen-2.5-7b-instruct:free",
    small_model="openrouter/mistralai/mistral-7b-instruct:free",
    description="Free-tier OpenRouter models (no credit cost)",
    requires_openrouter=True,
)


# List of all configurations for parametrized tests
ALL_CONFIGS = [
    ALL_VIBEPROXY,
    FREE_OPENROUTER,
    ALL_OPENROUTER,
    VIBEPROXY_BIG_OPENROUTER_SMALL,
    MIXED_PROVIDERS,
    GEMINI_ONLY,
    CLAUDE_ONLY,
]

# Quick/smoke test configs - FREE MODELS ONLY (conserve OpenRouter credits)
# These use VibeProxy or free OpenRouter tiers exclusively (no API costs)
QUICK_CONFIGS = [
    ALL_VIBEPROXY,     # FREE - uses local OAuth
    GEMINI_ONLY,       # FREE - Gemini via VibeProxy
    FREE_OPENROUTER,   # FREE - Llama/Qwen/Mistral free tier
]

# Paid model configs - use ONLY after free models verified working
PAID_CONFIGS = [
    ALL_OPENROUTER,
    VIBEPROXY_BIG_OPENROUTER_SMALL,
    MIXED_PROVIDERS,
]


def get_config_by_name(name: str) -> Optional[ModelConfig]:
    """Get a configuration by name."""
    for config in ALL_CONFIGS:
        if config.name == name:
            return config
    return None
