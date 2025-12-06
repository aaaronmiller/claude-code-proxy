import json
from typing import Dict, Any, List
import logging
from src.services.models.model_parser import parse_model_id
from src.services.prompts.templates import apply_template
from src.models.claude import ClaudeMessagesRequest, ClaudeMessage
from src.core.config import config
from src.models.reasoning import (
    OpenAIReasoningConfig,
    AnthropicThinkingConfig,
    GeminiThinkingConfig
)
from src.services.models.model_filter import model_filter
from src.core.constants import Constants

logger = logging.getLogger(__name__)


def _apply_reasoning_config(
    openai_request: Dict[str, Any],
    reasoning_config: Any,
    model_name: str,
    model_manager
) -> None:
    """
    Apply reasoning configuration to OpenAI request based on provider type.
    
    Args:
        openai_request: OpenAI request dictionary to modify
        reasoning_config: ReasoningConfig object (OpenAI/Anthropic/Gemini)
        model_name: Model name for logging
        model_manager: ModelManager instance for config access
    """
    is_using_openrouter = "openrouter" in model_manager.config.openai_base_url.lower()
    
    # OpenAI o-series reasoning effort or arbitrary token budget
    if isinstance(reasoning_config, OpenAIReasoningConfig):
        if is_using_openrouter:
            # OpenRouter requires reasoning params in extra_body
            if "extra_body" not in openai_request:
                openai_request["extra_body"] = {}
            
            reasoning_params = {}
            if reasoning_config.effort:
                reasoning_params["effort"] = reasoning_config.effort
            if reasoning_config.max_tokens:
                reasoning_params["max_tokens"] = reasoning_config.max_tokens
            reasoning_params["exclude"] = reasoning_config.exclude
            
            openai_request["extra_body"]["reasoning"] = reasoning_params
            
            log_msg = f"Applied OpenAI reasoning config for {model_name}: "
            if reasoning_config.effort:
                log_msg += f"effort={reasoning_config.effort}"
            if reasoning_config.max_tokens:
                log_msg += f" max_tokens={reasoning_config.max_tokens}"
            log_msg += f" exclude={reasoning_config.exclude}"
            logger.info(log_msg)
        else:
            # For direct OpenAI API, check if Responses API is supported
            # For now, we'll add it to extra_body as well
            if "extra_body" not in openai_request:
                openai_request["extra_body"] = {}
            
            reasoning_params = {}
            if reasoning_config.effort:
                reasoning_params["effort"] = reasoning_config.effort
            if reasoning_config.max_tokens:
                reasoning_params["max_tokens"] = reasoning_config.max_tokens
            
            openai_request["extra_body"]["reasoning"] = reasoning_params
            
            log_msg = f"Applied OpenAI reasoning config for {model_name}: "
            if reasoning_config.effort:
                log_msg += f"effort={reasoning_config.effort}"
            if reasoning_config.max_tokens:
                log_msg += f"max_tokens={reasoning_config.max_tokens}"
            logger.info(log_msg)
    
    # Anthropic thinking tokens
    elif isinstance(reasoning_config, AnthropicThinkingConfig):
        # Anthropic uses 'thinking' parameter in request body
        # For OpenRouter, this goes in extra_body
        if is_using_openrouter:
            if "extra_body" not in openai_request:
                openai_request["extra_body"] = {}
            
            openai_request["extra_body"]["thinking"] = {
                "type": reasoning_config.type,
                "budget": reasoning_config.budget
            }
        else:
            # For direct Anthropic API (if proxying), add to top level
            openai_request["thinking"] = {
                "type": reasoning_config.type,
                "budget": reasoning_config.budget
            }
        
        logger.info(
            f"Applied Anthropic thinking config for {model_name}: "
            f"budget={reasoning_config.budget}"
        )
    
    # Gemini thinking budget
    elif isinstance(reasoning_config, GeminiThinkingConfig):
        # Gemini uses 'thinking_config' in generation_config
        if "generation_config" not in openai_request:
            if "extra_body" not in openai_request:
                openai_request["extra_body"] = {}
            openai_request["extra_body"]["generation_config"] = {}
        
        if "extra_body" in openai_request and "generation_config" in openai_request["extra_body"]:
            openai_request["extra_body"]["generation_config"]["thinking_config"] = {
                "budget": reasoning_config.budget
            }
        else:
            if "generation_config" not in openai_request:
                openai_request["generation_config"] = {}
            openai_request["generation_config"]["thinking_config"] = {
                "budget": reasoning_config.budget
            }
        
        logger.info(
            f"Applied Gemini thinking config for {model_name}: "
            f"budget={reasoning_config.budget}"
        )


def convert_claude_to_openai(
    claude_request: ClaudeMessagesRequest, model_manager
) -> Dict[str, Any]:
    """Convert Claude API request format to OpenAI format with enhanced validation."""

    # Validate input request
    if not claude_request:
        raise ValueError("Claude request cannot be None")

    if not claude_request.messages:
        raise ValueError("Claude request must contain at least one message")

    if not isinstance(claude_request.messages, list):
        raise ValueError("Claude request messages must be a list")

    if claude_request.max_tokens < 1:
        raise ValueError(f"max_tokens must be at least 1, got {claude_request.max_tokens}")

    # Parse model name and extract reasoning configuration
    openai_model, reasoning_config = model_manager.parse_and_map_model(claude_request.model)
    
    # Track model usage
    model_filter.track_model_usage(openai_model)

    # Convert messages
    openai_messages = []

    # Add system message if present
    if claude_request.system:
        system_text = ""
        if isinstance(claude_request.system, str):
            system_text = claude_request.system
        elif isinstance(claude_request.system, list):
            text_parts = []
            for block in claude_request.system:
                if hasattr(block, "type") and block.type == Constants.CONTENT_TEXT:
                    text_parts.append(block.text)
                elif (
                    isinstance(block, dict)
                    and block.get("type") == Constants.CONTENT_TEXT
                ):
                    text_parts.append(block.get("text", ""))
            system_text = "\n\n".join(text_parts)

        if system_text.strip():
            openai_messages.append(
                {"role": Constants.ROLE_SYSTEM, "content": system_text.strip()}
            )

    # Process Claude messages
    i = 0
    while i < len(claude_request.messages):
        msg = claude_request.messages[i]

        if msg.role == Constants.ROLE_USER:
            openai_message = convert_claude_user_message(msg)
            openai_messages.append(openai_message)
        elif msg.role == Constants.ROLE_ASSISTANT:
            openai_message = convert_claude_assistant_message(msg)
            openai_messages.append(openai_message)

            # Check if next message contains tool results
            if i + 1 < len(claude_request.messages):
                next_msg = claude_request.messages[i + 1]
                if (
                    next_msg.role == Constants.ROLE_USER
                    and isinstance(next_msg.content, list)
                    and any(
                        block.type == Constants.CONTENT_TOOL_RESULT
                        for block in next_msg.content
                        if hasattr(block, "type")
                    )
                ):
                    # Process tool results
                    i += 1  # Skip to tool result message
                    tool_results = convert_claude_tool_results(next_msg)
                    openai_messages.extend(tool_results)

        i += 1

    # Build OpenAI request
    # Check if this is a newer OpenAI model (o1, o3, o4, gpt-5)
    is_newer_model = model_manager.is_newer_openai_model(openai_model)

    # Calculate token limit
    token_limit = min(
        max(claude_request.max_tokens, config.min_tokens_limit),
        config.max_tokens_limit,
    )

    openai_request = {
        "model": openai_model,
        "messages": openai_messages,
        "stream": claude_request.stream,
    }

    # Newer OpenAI models (o1, o3, o4, gpt-5) require max_completion_tokens instead of max_tokens
    if is_newer_model:
        openai_request["max_completion_tokens"] = token_limit
        # Newer reasoning models require temperature=1
        openai_request["temperature"] = 1
        logger.debug(f"Converted request (newer model): model={openai_model}, messages={len(openai_messages)}, max_completion_tokens={token_limit}, temperature=1")
    else:
        openai_request["max_tokens"] = token_limit
        openai_request["temperature"] = claude_request.temperature
        logger.debug(f"Converted request: model={openai_model}, messages={len(openai_messages)}, max_tokens={token_limit}")
    # Add optional parameters
    if claude_request.stop_sequences:
        openai_request["stop"] = claude_request.stop_sequences
    if claude_request.top_p is not None:
        openai_request["top_p"] = claude_request.top_p

    # Convert tools
    if claude_request.tools:
        openai_tools = []
        for tool in claude_request.tools:
            if tool.name and tool.name.strip():
                openai_tools.append(
                    {
                        "type": Constants.TOOL_FUNCTION,
                        Constants.TOOL_FUNCTION: {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )
        if openai_tools:
            openai_request["tools"] = openai_tools

    # Convert tool choice
    if claude_request.tool_choice:
        choice_type = claude_request.tool_choice.get("type")
        if choice_type == "auto":
            openai_request["tool_choice"] = "auto"
        elif choice_type == "any":
            openai_request["tool_choice"] = "auto"
        elif choice_type == "tool" and "name" in claude_request.tool_choice:
            openai_request["tool_choice"] = {
                "type": Constants.TOOL_FUNCTION,
                Constants.TOOL_FUNCTION: {"name": claude_request.tool_choice["name"]},
            }
        else:
            openai_request["tool_choice"] = "auto"

    # Apply reasoning configuration if present
    if reasoning_config:
        _apply_reasoning_config(openai_request, reasoning_config, openai_model, model_manager)
    
    # Add verbosity if configured (for providers that support it)
    # Note: Not all models support verbosity, and some only support specific values
    # Skip verbosity to avoid compatibility issues - let the model use its default
    if model_manager.config.verbosity and _model_supports_reasoning(openai_model, model_manager):
        # Only add verbosity for models that explicitly support it
        # Many models don't support this parameter or have restrictions
        logger.debug(f"Verbosity configured but skipped for {openai_model} to avoid compatibility issues")

    # Inject custom system prompt if configured
    from src.services.prompts.system_prompt_loader import inject_system_prompt
    model_size = _get_model_size_from_model_id(openai_model)
    openai_messages = inject_system_prompt(openai_messages, model_size, model_manager.config)
    openai_request["messages"] = openai_messages

    return openai_request


def _model_supports_reasoning(model_id: str, model_manager=None) -> bool:
    """
    Check if a model supports reasoning parameters.

    Models known to support reasoning_effort and related parameters:
    - OpenAI: GPT-5 family, o1 series, o3 series
    - Anthropic: Claude 3.7, Claude 4.x, Claude 4.1 with reasoning
    - xAI: Grok models with reasoning
    - Qwen: Qwen3, Qwen-2.5 thinking variants
    - DeepSeek: DeepSeek V3/V3.1, DeepSeek R1 variants
    - MiniMax: M2 thinking models
    - Kimi: K2 thinking models
    """
    model_lower = model_id.lower()

    # Primary keyword patterns that indicate reasoning support
    # OpenAI models - support both "openai/gpt-5" and "gpt-5" formats
    if any(keyword in model_lower for keyword in [
        "openai/gpt-5", "gpt-5",
        "openai/o1", "o1",
        "openai/o3", "o3"
    ]):
        return True

    # Anthropic models (explicit support for all reasoning-capable variants)
    if any(pattern in model_lower for pattern in [
        "anthropic/claude-3.7",
        "anthropic/claude-4",
        "anthropic/claude-4.1",
        "anthropic/claude-sonnet",
        "anthropic/claude-opus",
        "anthropic/claude-haiku"
    ]):
        return True

    # xAI models
    if "xai/" in model_lower and any(keyword in model_lower for keyword in ["reason", "thinking"]):
        return True

    # Qwen thinking models
    if any(keyword in model_lower for keyword in [
        "qwen3",
        "qwen2.5-thinking",
        "qwen-2.5-thinking",
        "qwen-thinking",
        "qwen-reasoning"
    ]):
        return True

    # DeepSeek reasoning models
    if any(keyword in model_lower for keyword in [
        "deepseek-v3",
        "deepseek-v3.1",
        "deepseek-r1",
        "deepseek-reasoning"
    ]):
        return True

    # MiniMax and Kimi
    if any(keyword in model_lower for keyword in [
        "minimax/m2",
        "minimax-thinking",
        "kimi-k2",
        "kimi-thinking"
    ]):
        return True

    # Generic patterns
    if any(keyword in model_lower for keyword in [
        "thinking",
        "-reasoning",
        "-r1",
        "-deepseek-r1",
        "cognition",
        "chain-of-thought"
    ]):
        return True

    # Check metadata if available (for OpenRouter models)
    if model_manager and hasattr(model_manager, 'models_data'):
        for category in ['reasoning_models', 'verbosity_models']:
            if category in model_manager.models_data:
                for model in model_manager.models_data[category]:
                    if model.get('id', '').lower() == model_lower:
                        return True

    return False


def _get_model_size_from_model_id(model_id: str) -> str:
    """
    Determine model size from model ID.

    Args:
        model_id: The OpenAI model ID

    Returns:
        "big", "middle", or "small"
    """
    model_lower = model_id.lower()

    # Match against configured models
    if model_lower == config.big_model.lower():
        return "big"
    elif model_lower == config.middle_model.lower():
        return "middle"
    elif model_lower == config.small_model.lower():
        return "small"

    # Fallback: infer from model name patterns
    if any(keyword in model_lower for keyword in ["opus", "gpt-5", "gpt-4.1"]):
        return "big"
    elif any(keyword in model_lower for keyword in ["sonnet", "gpt-4"]):
        return "middle"
    elif any(keyword in model_lower for keyword in ["haiku", "mini", "gpt-4o-mini"]):
        return "small"

    # Default to middle
    return "middle"


def convert_claude_user_message(msg: ClaudeMessage) -> Dict[str, Any]:
    """Convert Claude user message to OpenAI format."""
    if msg.content is None:
        return {"role": Constants.ROLE_USER, "content": ""}
    
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_USER, "content": msg.content}

    # Handle multimodal content
    openai_content = []
    for block in msg.content:
        if block.type == Constants.CONTENT_TEXT:
            openai_content.append({"type": "text", "text": block.text})
        elif block.type == Constants.CONTENT_IMAGE:
            # Convert Claude image format to OpenAI format
            if (
                isinstance(block.source, dict)
                and block.source.get("type") == "base64"
                and "media_type" in block.source
                and "data" in block.source
            ):
                openai_content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{block.source['media_type']};base64,{block.source['data']}"
                        },
                    }
                )

    if len(openai_content) == 1 and openai_content[0]["type"] == "text":
        return {"role": Constants.ROLE_USER, "content": openai_content[0]["text"]}
    else:
        return {"role": Constants.ROLE_USER, "content": openai_content}


def convert_claude_assistant_message(msg: ClaudeMessage) -> Dict[str, Any]:
    """Convert Claude assistant message to OpenAI format."""
    text_parts = []
    tool_calls = []

    if msg.content is None:
        return {"role": Constants.ROLE_ASSISTANT, "content": None}
    
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_ASSISTANT, "content": msg.content}

    for block in msg.content:
        if block.type == Constants.CONTENT_TEXT:
            text_parts.append(block.text)
        elif block.type == Constants.CONTENT_TOOL_USE:
            tool_calls.append(
                {
                    "id": block.id,
                    "type": Constants.TOOL_FUNCTION,
                    Constants.TOOL_FUNCTION: {
                        "name": block.name,
                        "arguments": json.dumps(block.input, ensure_ascii=False),
                    },
                }
            )

    openai_message = {"role": Constants.ROLE_ASSISTANT}

    # Set content
    if text_parts:
        openai_message["content"] = "".join(text_parts)
    else:
        openai_message["content"] = None

    # Set tool calls
    if tool_calls:
        openai_message["tool_calls"] = tool_calls

    return openai_message


def convert_claude_tool_results(msg: ClaudeMessage) -> List[Dict[str, Any]]:
    """Convert Claude tool results to OpenAI format."""
    tool_messages = []

    if isinstance(msg.content, list):
        for block in msg.content:
            if block.type == Constants.CONTENT_TOOL_RESULT:
                content = parse_tool_result_content(block.content)
                tool_messages.append(
                    {
                        "role": Constants.ROLE_TOOL,
                        "tool_call_id": block.tool_use_id,
                        "content": content,
                    }
                )

    return tool_messages


def parse_tool_result_content(content):
    """Parse and normalize tool result content into a string format."""
    if content is None:
        return "No content provided"

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        result_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == Constants.CONTENT_TEXT:
                result_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                result_parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    result_parts.append(item.get("text", ""))
                else:
                    try:
                        result_parts.append(json.dumps(item, ensure_ascii=False))
                    except (TypeError, ValueError):
                        result_parts.append(str(item))
        return "\n".join(result_parts).strip()

    if isinstance(content, dict):
        if content.get("type") == Constants.CONTENT_TEXT:
            return content.get("text", "")
        try:
            return json.dumps(content, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(content)

    try:
        return str(content)
    except Exception:
        return "Unparseable content"
