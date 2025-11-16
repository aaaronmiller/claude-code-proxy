"""Unit tests for model name parser."""

import pytest
from src.utils.model_parser import parse_model_name, ParsedModel


class TestModelParser:
    """Test model name parsing with reasoning suffixes."""
    
    def test_parse_openai_o_series_with_effort(self):
        """Test parsing OpenAI o-series models with effort levels."""
        result = parse_model_name("o4-mini:high")
        assert result.base_model == "o4-mini"
        assert result.reasoning_type == "effort"
        assert result.reasoning_value == "high"
        assert result.original_model == "o4-mini:high"
    
    def test_parse_anthropic_with_k_notation(self):
        """Test parsing Anthropic models with k-notation."""
        result = parse_model_name("claude-opus-4-20250514:4k")
        assert result.base_model == "claude-opus-4-20250514"
        assert result.reasoning_type == "thinking_tokens"
        assert result.reasoning_value == 4096
        assert result.original_model == "claude-opus-4-20250514:4k"
    
    def test_parse_anthropic_with_exact_number(self):
        """Test parsing Anthropic models with exact token count."""
        result = parse_model_name("claude-sonnet-4-20250514:8000")
        assert result.base_model == "claude-sonnet-4-20250514"
        assert result.reasoning_type == "thinking_tokens"
        assert result.reasoning_value == 8000
    
    def test_parse_gemini_with_k_notation(self):
        """Test parsing Gemini models with k-notation."""
        result = parse_model_name("gemini-2.5-flash-preview-04-17:16k")
        assert result.base_model == "gemini-2.5-flash-preview-04-17"
        assert result.reasoning_type == "thinking_budget"
        assert result.reasoning_value == 16384
    
    def test_parse_model_without_suffix(self):
        """Test parsing models without reasoning suffix (backward compatibility)."""
        result = parse_model_name("gpt-4")
        assert result.base_model == "gpt-4"
        assert result.reasoning_type is None
        assert result.reasoning_value is None
        assert result.original_model == "gpt-4"
    
    def test_k_notation_conversion(self):
        """Test k-notation conversion for various values."""
        test_cases = [
            ("claude-opus-4-20250514:1k", 1024),
            ("claude-opus-4-20250514:4k", 4096),
            ("claude-opus-4-20250514:8k", 8192),
            ("claude-opus-4-20250514:16k", 16384),
        ]
        for model_name, expected_value in test_cases:
            result = parse_model_name(model_name)
            assert result.reasoning_value == expected_value
    
    def test_invalid_suffix_format(self):
        """Test handling of invalid suffix formats."""
        result = parse_model_name("gpt-4:invalid")
        # Should return model without reasoning config
        assert result.base_model == "gpt-4"
        assert result.reasoning_type is None
        assert result.reasoning_value is None
