"""Unit tests for request converter reasoning logic."""

import pytest
from unittest.mock import Mock, MagicMock
from src.conversion.request_converter import convert_claude_to_openai, _apply_reasoning_config
from src.models.claude import ClaudeMessagesRequest, ClaudeMessage
from src.models.reasoning import (
    OpenAIReasoningConfig,
    AnthropicThinkingConfig,
    GeminiThinkingConfig
)


class TestReasoningConfigApplication:
    """Test reasoning configuration application to requests."""
    
    def test_apply_openai_reasoning_config(self):
        """Test applying OpenAI reasoning configuration."""
        openai_request = {"model": "o4-mini", "messages": []}
        reasoning_config = OpenAIReasoningConfig(
            enabled=True,
            effort="high",
            exclude=False
        )
        
        model_manager = Mock()
        model_manager.config.openai_base_url = "https://openrouter.ai/api/v1"
        
        _apply_reasoning_config(openai_request, reasoning_config, "o4-mini", model_manager)
        
        assert "extra_body" in openai_request
        assert "reasoning" in openai_request["extra_body"]
        assert openai_request["extra_body"]["reasoning"]["effort"] == "high"
        assert openai_request["extra_body"]["reasoning"]["exclude"] is False
    
    def test_apply_anthropic_thinking_config(self):
        """Test applying Anthropic thinking configuration."""
        openai_request = {"model": "claude-opus-4-20250514", "messages": []}
        reasoning_config = AnthropicThinkingConfig(
            enabled=True,
            type="enabled",
            budget=4096
        )
        
        model_manager = Mock()
        model_manager.config.openai_base_url = "https://openrouter.ai/api/v1"
        
        _apply_reasoning_config(openai_request, reasoning_config, "claude-opus-4-20250514", model_manager)
        
        assert "extra_body" in openai_request
        assert "thinking" in openai_request["extra_body"]
        assert openai_request["extra_body"]["thinking"]["budget"] == 4096
    
    def test_apply_gemini_thinking_config(self):
        """Test applying Gemini thinking configuration."""
        openai_request = {"model": "gemini-2.5-flash-preview-04-17", "messages": []}
        reasoning_config = GeminiThinkingConfig(
            enabled=True,
            budget=8192
        )
        
        model_manager = Mock()
        model_manager.config.openai_base_url = "https://openrouter.ai/api/v1"
        
        _apply_reasoning_config(openai_request, reasoning_config, "gemini-2.5-flash-preview-04-17", model_manager)
        
        assert "extra_body" in openai_request
        assert "generation_config" in openai_request["extra_body"]
        assert openai_request["extra_body"]["generation_config"]["thinking_config"]["budget"] == 8192


class TestRequestConverterWithReasoning:
    """Test request converter with reasoning parameters."""
    
    def test_convert_with_reasoning_suffix(self):
        """Test conversion with reasoning suffix in model name."""
        claude_request = ClaudeMessagesRequest(
            model="o4-mini:high",
            max_tokens=4096,
            messages=[
                ClaudeMessage(role="user", content="Test message")
            ]
        )
        
        model_manager = Mock()
        model_manager.config.openai_base_url = "https://openrouter.ai/api/v1"
        model_manager.config.min_tokens_limit = 100
        model_manager.config.max_tokens_limit = 8000
        model_manager.config.reasoning_exclude = False
        model_manager.config.verbosity = None
        
        # Mock parse_and_map_model to return reasoning config
        reasoning_config = OpenAIReasoningConfig(enabled=True, effort="high", exclude=False)
        model_manager.parse_and_map_model.return_value = ("o4-mini", reasoning_config)
        
        result = convert_claude_to_openai(claude_request, model_manager)
        
        assert result["model"] == "o4-mini"
        assert "extra_body" in result
        assert "reasoning" in result["extra_body"]
        assert result["extra_body"]["reasoning"]["effort"] == "high"
    
    def test_convert_without_reasoning(self):
        """Test conversion without reasoning parameters."""
        claude_request = ClaudeMessagesRequest(
            model="gpt-4",
            max_tokens=4096,
            messages=[
                ClaudeMessage(role="user", content="Test message")
            ]
        )
        
        model_manager = Mock()
        model_manager.config.openai_base_url = "https://api.openai.com/v1"
        model_manager.config.min_tokens_limit = 100
        model_manager.config.max_tokens_limit = 8000
        model_manager.config.verbosity = None
        
        # Mock parse_and_map_model to return no reasoning config
        model_manager.parse_and_map_model.return_value = ("gpt-4", None)
        
        result = convert_claude_to_openai(claude_request, model_manager)
        
        assert result["model"] == "gpt-4"
        # Should not have reasoning config
        if "extra_body" in result:
            assert "reasoning" not in result.get("extra_body", {})
