"""Integration tests for end-to-end reasoning flow."""

import pytest
from unittest.mock import Mock
from src.core.model_manager import ModelManager
from src.services.conversion.request_converter import convert_claude_to_openai
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

        # o4-mini passes through as-is (not mapped to gpt-5)
        assert openai_model == "o4-mini"
        assert reasoning_config is not None
        assert reasoning_config.effort == "high"

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

        # Opus maps to big_model (gpt-4o)
        assert openai_model == "gpt-4o"
        assert reasoning_config is not None
        assert reasoning_config.budget == 4096

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

        # Gemini model passes through as-is (not Claude, so no mapping)
        assert openai_model == "gemini-2.5-flash-preview-04-17"
        assert reasoning_config is not None
        assert reasoning_config.budget == 8192

    def test_per_model_routing_with_reasoning(self):
        """Test per-model routing with different reasoning configs."""
        # Test big model (opus) with high reasoning
        claude_request_big = ClaudeMessagesRequest(
            model="claude-opus-4-20250514:8k",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )

        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request_big.model)
        assert openai_model == "gpt-4o"  # Maps to big_model
        assert reasoning_config is not None
        assert reasoning_config.budget == 8192

        # Test small model (haiku) - haiku maps to small_model
        claude_request_small = ClaudeMessagesRequest(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )

        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request_small.model)
        assert openai_model == "gpt-4o-mini"  # Maps to small_model
        # Haiku without reasoning suffix should have no reasoning config
        assert reasoning_config is None

    def test_model_without_reasoning_suffix(self):
        """Test model without reasoning suffix passes through cleanly."""
        claude_request = ClaudeMessagesRequest(
            model="gpt-4o",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )

        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request.model)
        assert openai_model == "gpt-4o"
        assert reasoning_config is None

    def test_sonnet_maps_to_middle_model(self):
        """Test Claude Sonnet maps to middle model."""
        claude_request = ClaudeMessagesRequest(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[ClaudeMessage(role="user", content="Test")]
        )

        openai_model, reasoning_config = self.model_manager.parse_and_map_model(claude_request.model)
        assert openai_model == "gpt-4o"  # Maps to middle_model
        assert reasoning_config is None  # No reasoning suffix
