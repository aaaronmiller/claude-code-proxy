from src.models.claude import ClaudeContentBlockToolUse, ClaudeMessage
from src.services.conversion.request_converter import convert_claude_assistant_message
from src.services.conversion.response_converter import _extract_tool_calls_from_text
from src.services.conversion.tool_behavior_cache import record_tool_argument_style


def test_extract_tool_calls_from_text_parses_function_equals_markup():
    remaining, calls = _extract_tool_calls_from_text(
        'before<tool_call><function="bash"><parameters>{"prompt":"pwd","timeout":"30"}</parameters></tool_call>after'
    )

    assert remaining == "beforeafter"
    assert calls == [{"name": "bash", "arguments": {"prompt": "pwd", "timeout": "30"}}]


def test_convert_claude_assistant_message_uses_observed_prompt_style():
    record_tool_argument_style("openrouter", "Bash", {"prompt": "ls"})

    message = ClaudeMessage(
        role="assistant",
        content=[
            ClaudeContentBlockToolUse(
                type="tool_use",
                id="tool_1",
                name="Bash",
                input={"command": "ls", "timeout": 30},
            )
        ],
    )

    converted = convert_claude_assistant_message(
        message,
        target_provider="openrouter",
    )

    assert converted["tool_calls"][0]["function"]["arguments"] == (
        '{"timeout": 30, "prompt": "ls"}'
    )
