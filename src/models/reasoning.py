"""
Reasoning configuration classes for different AI providers.

This module defines configuration classes for reasoning capabilities
across OpenAI, Anthropic, and Google Gemini models.
"""

from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class ReasoningConfig:
    """Base class for reasoning configurations."""
    pass


@dataclass
class OpenAIReasoningConfig(ReasoningConfig):
    """Configuration for OpenAI reasoning models (o-series, GPT-5)."""
    enabled: bool = True
    effort: Optional[str] = None  # 'low', 'medium', 'high'
    max_tokens: Optional[int] = None  # Arbitrary token budget
    exclude: bool = False  # Whether to exclude reasoning from response


@dataclass
class AnthropicThinkingConfig(ReasoningConfig):
    """Configuration for Anthropic thinking models."""
    budget: int  # Token budget for thinking
    type: str = "enabled"  # Thinking type


@dataclass
class GeminiThinkingConfig(ReasoningConfig):
    """Configuration for Google Gemini thinking models."""
    budget: int  # Token budget for thinking
