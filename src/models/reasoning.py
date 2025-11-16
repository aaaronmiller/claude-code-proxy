"""
Reasoning configuration data models for OpenAI, Anthropic, and Gemini providers.

These models define the structure for reasoning parameters that can be applied
to API requests for models that support advanced reasoning capabilities.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ReasoningConfig(BaseModel):
    """Base reasoning configuration for all providers."""
    
    enabled: bool = Field(
        default=True,
        description="Whether reasoning is enabled"
    )


class OpenAIReasoningConfig(ReasoningConfig):
    """
    OpenAI o-series reasoning configuration.
    
    Applies to models like o1, o3, o4-mini that support reasoning effort levels.
    Supports both effort levels (low/medium/high) and arbitrary token budgets.
    """
    
    effort: Optional[Literal["low", "medium", "high"]] = Field(
        default=None,
        description="Reasoning effort level (low, medium, or high)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Arbitrary reasoning token budget (overrides effort level)",
        ge=0
    )
    exclude: bool = Field(
        default=False,
        description="Whether to exclude reasoning tokens from the response"
    )


class AnthropicThinkingConfig(ReasoningConfig):
    """
    Anthropic thinking tokens configuration.
    
    Applies to Claude 3.7, Claude 4.x models that support extended thinking.
    Budget range: 1024-16000 tokens.
    """
    
    type: Literal["enabled"] = Field(
        default="enabled",
        description="Thinking type (always 'enabled' for Anthropic)"
    )
    budget: int = Field(
        description="Thinking token budget (1024-16000)",
        ge=1024,
        le=16000
    )


class GeminiThinkingConfig(ReasoningConfig):
    """
    Google Gemini thinking budget configuration.
    
    Applies to gemini-2.5-flash-preview-04-17 model.
    Budget range: 0-24576 tokens.
    """
    
    budget: int = Field(
        description="Thinking budget in tokens (0-24576)",
        ge=0,
        le=24576
    )
