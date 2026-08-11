"""Unit tests for the OpenAI/Codex request path field compliance.

Covers the request model surface (reasoning_effort, reasoning, parallel_tool_calls,
top_k, metadata, response_format, max_completion_tokens, seed, stream_options)
and the reasoning/extra-field merge used by /v1/chat/completions.
"""

from types import SimpleNamespace
from unittest.mock import Mock

from src.api.openai_endpoints import (
    OpenAIChatRequest,
    apply_openai_client_reasoning_and_extras,
)
from src.models.reasoning import OpenAIReasoningConfig


class TestOpenAIChatRequestModel:
    """Codex/OpenAI-format request fields must parse, not be silently dropped."""

    def test_full_surface_parses(self):
        body = OpenAIChatRequest.model_validate(
            {
                "model": "gpt-5",
                "messages": [{"role": "user", "content": "hi"}],
                "reasoning_effort": "max",
                "parallel_tool_calls": False,
                "top_k": 40,
                "metadata": {"session_id": "s1"},
                "response_format": {"type": "text"},
                "max_completion_tokens": 1000,
                "seed": 7,
                "stream_options": {"include_usage": True},
            }
        )
        assert body.reasoning_effort == "max"
        assert body.parallel_tool_calls is False
        assert body.top_k == 40
        assert body.metadata == {"session_id": "s1"}
        assert body.response_format == {"type": "text"}
        assert body.max_completion_tokens == 1000
        assert body.seed == 7
        assert body.stream_options == {"include_usage": True}

    def test_reasoning_dict_parses(self):
        body = OpenAIChatRequest.model_validate(
            {
                "model": "gpt-5",
                "messages": [{"role": "user", "content": "hi"}],
                "reasoning": {"effort": "xl", "max_tokens": 8000},
            }
        )
        assert body.reasoning == {"effort": "xl", "max_tokens": 8000}


def _manager():
    mm = Mock()
    mm.config.openai_base_url = "https://openrouter.ai/api/v1"
    return mm


def _config():
    cfg = SimpleNamespace(reasoning_exclude=False)
    return cfg


class TestApplyClientReasoningAndExtras:
    """The merge used by the /v1/chat/completions handler."""

    def test_client_effort_wins_and_is_emitted(self):
        request = {"model": "gpt-5", "reasoning_effort": "max"}
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort="max",
            client_reasoning=None,
            parsed_reasoning_config=OpenAIReasoningConfig(
                enabled=True, effort="low", exclude=False
            ),
            model_manager=_manager(),
            config=_config(),
        )
        assert "reasoning_effort" not in request
        assert request["extra_body"]["reasoning"]["effort"] == "max"

    def test_reasoning_dict_effort_is_used(self):
        request = {"model": "gpt-5", "reasoning": {"effort": "xl"}}
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort=None,
            client_reasoning={"effort": "xl"},
            parsed_reasoning_config=None,
            model_manager=_manager(),
            config=_config(),
        )
        assert "reasoning" not in request
        assert request["extra_body"]["reasoning"]["effort"] == "xl"

    def test_reasoning_dict_max_tokens_only(self):
        request = {"model": "gpt-5", "reasoning": {"max_tokens": 16000}}
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort=None,
            client_reasoning={"max_tokens": 16000},
            parsed_reasoning_config=None,
            model_manager=_manager(),
            config=_config(),
        )
        assert request["extra_body"]["reasoning"]["max_tokens"] == 16000

    def test_invalid_client_effort_falls_back_to_parsed(self):
        request = {"model": "gpt-5", "reasoning_effort": "ultra"}
        parsed = OpenAIReasoningConfig(enabled=True, effort="high", exclude=False)
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort="ultra",
            client_reasoning=None,
            parsed_reasoning_config=parsed,
            model_manager=_manager(),
            config=_config(),
        )
        assert request["extra_body"]["reasoning"]["effort"] == "high"

    def test_parsed_config_applied_when_client_silent(self):
        request = {"model": "gpt-5"}
        parsed = OpenAIReasoningConfig(enabled=True, effort="high", exclude=False)
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort=None,
            client_reasoning=None,
            parsed_reasoning_config=parsed,
            model_manager=_manager(),
            config=_config(),
        )
        assert request["extra_body"]["reasoning"]["effort"] == "high"

    def test_top_k_and_metadata_ride_extra_body(self):
        request = {"model": "gpt-5", "top_k": 32, "metadata": {"sid": "x"}}
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort=None,
            client_reasoning=None,
            parsed_reasoning_config=None,
            model_manager=_manager(),
            config=_config(),
            top_k=32,
            metadata={"sid": "x"},
        )
        assert "top_k" not in request
        assert "metadata" not in request
        assert request["extra_body"]["top_k"] == 32
        assert request["extra_body"]["metadata"] == {"sid": "x"}

    def test_no_reasoning_when_nothing_set(self):
        request = {"model": "gpt-5"}
        apply_openai_client_reasoning_and_extras(
            request,
            client_effort=None,
            client_reasoning=None,
            parsed_reasoning_config=None,
            model_manager=_manager(),
            config=_config(),
        )
        assert "extra_body" not in request
