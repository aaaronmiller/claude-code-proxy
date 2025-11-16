"""Integration tests for end-to-end reasoning flow."""

import pytest
from unittest.mock import Mock
from src.core.model_manager import ModelManager
from src.conversion.request_converter import convert_claude_to_openai
from src.models.claude import ClaudeMessagesRequest, ClaudeMessage


class TestReasoningIntegration:
    """Test end-to-end reasoning flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock()
        self.config.openai_base_url = "https://openrouter.ai/api/v1"
        self.config.min_tokens_limit = 100
        self.config.max_tokens_limit = 8000
        self.config.reasoning_effort = None
        self.config.reasoning_max_tokens = None
        self.config.reasoning_exclude = False
        self.config.verbosity = None
        self.config.big_model = "gpt-4o"
        self.config.middle_model = "gpt-4o"
        self.config.small_model = "gpt-4o-mini"
        
        self.model_manager = ModelManager(self.config)
    
    def test_openai_o_series_reasoning_flow(self):
        """Test complete request flow with OpenAI o-series reasoning."""
        claude_request = ClaudeMessagesRequest(
            model="o4-mini:high",
            max_tokens=4096,
            messages=[
                ClaudeMessage(role="user", content="Explain quantum computing")
            ]
        )
        
        # Parse and map model
        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request.model)
        
        assert openai_model == "openai/gpt-5"
        assert reasoning_config is not None
        assert reasoning_config.effort == "high"
        
        # Convert request
        result = convert_claude_to_openai(claude_request, self.model_manager)
        
        assert result["model"] == "openai/gpt-5"
        assert "extra_body" in result
        assert result["extra_body"]["reasoning"]["effort"] == "high"
    
    def test_anthropic_thinking_tokens_flow(self):
        """Test complete request flow with Anthropic thinking tokens."""
        claude_request = ClaudeMessagesRequest(
            model="claude-opus-4-20250514:4k",
            max_tokens=4096,
            messages=[
                ClaudeMessage(role="user", content="Solve this complex problem")
            ]
        )
        
        # Parse and map model
        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request.model)
        
        assert openai_model == "gpt-4o"
        assert reasoning_config is not None
        assert reasoning_config.budget == 4096
        
        # Convert request
        result = convert_claude_to_openai(claude_request, self.model_manager)
        
        assert result["model"] == "gpt-4o"
        assert "extra_body" in result
        assert result["extra_body"]["thinking"]["budget"] == 4096
    
    def test_gemini_thinking_budget_flow(self):
        """Test complete request flow with Gemini thinking budget."""
        claude_request = ClaudeMessagesRequest(
            model="gemini-2.5-flash-preview-04-17:8k",
            max_tokens=4096,
            messages=[
                ClaudeMessage(role="user", content="Analyze this data")
            ]
        )
        
        # Parse and map model
        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request.model)
        
        assert openai_model == "gpt-4o"
        assert reasoning_config is not None
        assert reasoning_config.budget == 8192
        
        # Convert request
        result = convert_claude_to_openai(claude_request, self.model_manager)
        
        assert result["model"] == "gpt-4o"
        assert "extra_body" in result
        assert "generation_config" in result["extra_body"]
        assert result["extra_body"]["generation_config"]["thinking_config"]["budget"] == 8192
    
    def test_per_model_routing_with_reasoning(self):
        """Test per-model routing with different reasoning configs."""
        # Test big model (opus) with high reasoning
        claude_request_big = ClaudeMessagesRequest(
            model="claude-opus-4-20250514:8k",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )
        
        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request_big.model)
        assert openai_model == "gpt-4o"
        assert reasoning_config.budget == 8192
        
        # Test small model (haiku) with lower reasoning
        claude_request_small = ClaudeMessagesRequest(
            model="claude-haiku-3-20240307:1k",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )
        
        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request_small.model)
        assert openai_model == "gpt-4o-mini"
        # Haiku doesn't support reasoning, so config should be None
        assert reasoning_config is None
