"""Unit tests for reasoning parameter validator."""

import pytest
from src.core.reasoning_validator import (
    validate_openai_reasoning,
    validate_anthropic_thinking,
    validate_gemini_thinking,
    is_reasoning_capable_model
)


class TestOpenAIReasoningValidation:
    """Test OpenAI reasoning effort validation."""
    
    def test_valid_effort_levels(self):
        """Test validation of valid effort levels."""
        assert validate_openai_reasoning("low") == "low"
        assert validate_openai_reasoning("medium") == "medium"
        assert validate_openai_reasoning("high") == "high"
        assert validate_openai_reasoning("HIGH") == "high"  # Case insensitive
    
    def test_invalid_effort_level(self):
        """Test validation rejects invalid effort levels."""
        with pytest.raises(ValueError, match="Invalid reasoning effort"):
            validate_openai_reasoning("invalid")


class TestAnthropicThinkingValidation:
    """Test Anthropic thinking token validation."""
    
    def test_valid_budget_within_range(self):
        """Test validation of budgets within valid range."""
        assert validate_anthropic_thinking(1024) == 1024
        assert validate_anthropic_thinking(4096) == 4096
        assert validate_anthropic_thinking(8000) == 8000
        assert validate_anthropic_thinking(16000) == 16000
        assert validate_anthropic_thinking(64000) == 64000
        assert validate_anthropic_thinking(128000) == 128000
    
    def test_budget_below_minimum(self):
        """Test adjustment of budget below minimum."""
        assert validate_anthropic_thinking(500) == 1024
        assert validate_anthropic_thinking(0) == 1024
    
    def test_budget_above_maximum(self):
        """Test adjustment of budget above maximum."""
        assert validate_anthropic_thinking(130000) == 128000
        assert validate_anthropic_thinking(200000) == 128000


class TestGeminiThinkingValidation:
    """Test Gemini thinking budget validation."""
    
    def test_valid_budget_within_range(self):
        """Test validation of budgets within valid range."""
        assert validate_gemini_thinking(0) == 0
        assert validate_gemini_thinking(4096) == 4096
        assert validate_gemini_thinking(16000) == 16000
        assert validate_gemini_thinking(24576) == 24576
    
    def test_budget_below_minimum(self):
        """Test adjustment of budget below minimum."""
        assert validate_gemini_thinking(-100) == 0
    
    def test_budget_above_maximum(self):
        """Test adjustment of budget above maximum."""
        assert validate_gemini_thinking(30000) == 24576
        assert validate_gemini_thinking(50000) == 24576


class TestModelCapabilityDetection:
    """Test model capability detection."""
    
    def test_openai_o_series_detection(self):
        """Test detection of OpenAI o-series models."""
        is_capable, reasoning_type = is_reasoning_capable_model("o4-mini")
        assert is_capable is True
        assert reasoning_type == "effort"
        
        is_capable, reasoning_type = is_reasoning_capable_model("o1-preview")
        assert is_capable is True
        assert reasoning_type == "effort"
    
    def test_anthropic_thinking_detection(self):
        """Test detection of Anthropic thinking-capable models."""
        is_capable, reasoning_type = is_reasoning_capable_model("claude-opus-4-20250514")
        assert is_capable is True
        assert reasoning_type == "thinking_tokens"
        
        is_capable, reasoning_type = is_reasoning_capable_model("claude-sonnet-4-20250514")
        assert is_capable is True
        assert reasoning_type == "thinking_tokens"
    
    def test_gemini_thinking_detection(self):
        """Test detection of Gemini thinking-capable models."""
        is_capable, reasoning_type = is_reasoning_capable_model("gemini-2.5-flash-preview-04-17")
        assert is_capable is True
        assert reasoning_type == "thinking_budget"
    
    def test_non_reasoning_model_detection(self):
        """Test detection of non-reasoning-capable models."""
        is_capable, reasoning_type = is_reasoning_capable_model("gpt-4")
        assert is_capable is False
        assert reasoning_type == ""
        
        is_capable, reasoning_type = is_reasoning_capable_model("claude-3-opus")
        assert is_capable is False
        assert reasoning_type == ""
