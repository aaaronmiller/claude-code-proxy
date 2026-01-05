import json
import os
from typing import Dict, Any, List, Tuple
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

# Tool output truncation settings (inspired by Lynkr)
# Large tool outputs waste tokens and can confuse models
TOOL_OUTPUT_MAX_CHARS = int(os.getenv("TOOL_OUTPUT_MAX_CHARS", "50000"))
TOOL_OUTPUT_TRUNCATION_ENABLED = os.getenv("TOOL_OUTPUT_TRUNCATION", "true").lower() == "true"


def truncate_tool_output(content: str, max_chars: int = None) -> Tuple[str, bool]:
    """
    Truncate large tool outputs for token efficiency.

    Inspired by Lynkr's truncateToolOutput() function.
    Large outputs from tools like file reads or command execution
    can waste tokens and confuse the model.

    Args:
        content: The tool output content
        max_chars: Maximum characters allowed (defaults to TOOL_OUTPUT_MAX_CHARS)

    Returns:
        Tuple of (possibly truncated content, was_truncated boolean)
    """
    if max_chars is None:
        max_chars = TOOL_OUTPUT_MAX_CHARS

    if not TOOL_OUTPUT_TRUNCATION_ENABLED:
        return content, False

    if not content or len(content) <= max_chars:
        return content, False

    # Calculate how much was truncated
    original_len = len(content)
    truncated_chars = original_len - max_chars

    # Truncate and add indicator
    truncated = content[:max_chars]
    truncated += f"\n\n... [OUTPUT TRUNCATED: {truncated_chars:,} chars removed, {original_len:,} total]"

    logger.info(f"Tool output truncated: {original_len:,} -> {max_chars:,} chars (-{truncated_chars:,})")

    return truncated, True


def validate_tool_message_sequence(messages: List[Dict[str, Any]], remove_orphans: bool = False) -> List[Dict[str, Any]]:
    """
    Validate that tool role messages have matching tool_calls in preceding assistant messages.
    
    Inspired by Lynkr's implementation, this prevents errors from orphaned tool messages
    that can occur when conversation history is truncated or corrupted.
    
    Args:
        messages: List of OpenAI-format messages
        remove_orphans: If True, remove orphaned tool messages. If False, just log warnings.
        
    Returns:
        Validated (and optionally cleaned) message list
    """
    if not messages:
        return messages
    
    validated = []
    orphan_count = 0
    
    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        
        if role == "tool":
            tool_call_id = msg.get("tool_call_id")
            
            # Search backwards for matching assistant message with tool_calls
            found_match = False
            for j in range(len(validated) - 1, -1, -1):
                prev_msg = validated[j]
                
                if prev_msg.get("role") == "assistant":
                    tool_calls = prev_msg.get("tool_calls", [])
                    if any(tc.get("id") == tool_call_id for tc in tool_calls):
                        found_match = True
                        break
                    
                # Stop searching if we hit a user message
                if prev_msg.get("role") == "user":
                    break
            
            if not found_match:
                orphan_count += 1
                logger.warning(
                    f"Orphaned tool message detected at index {i}: "
                    f"tool_call_id={tool_call_id}, no matching assistant tool_calls found"
                )
                
                if remove_orphans:
                    logger.info(f"Removing orphaned tool message (tool_call_id={tool_call_id})")
                    continue  # Skip this message
        
        validated.append(msg)
    
    if orphan_count > 0:
        logger.info(f"Tool message validation complete: {orphan_count} orphan(s) found, remove_orphans={remove_orphans}")
    
    return validated


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

    # Validate tool message sequence - detect orphaned tool messages
    # Set remove_orphans=True to auto-fix, False (default) to just warn
    openai_messages = validate_tool_message_sequence(openai_messages, remove_orphans=False)

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
    
    # Log outgoing message summary (debug level to avoid noise)
    logger.debug(f"OUTGOING REQUEST: {len(openai_messages)} messages")
    if logger.isEnabledFor(logging.DEBUG):
        for idx, msg in enumerate(openai_messages):
            role = msg.get("role", "?")
            content = str(msg.get("content", ""))[:80]
            tool_calls = "YES" if msg.get("tool_calls") else "NO"
            # Skip logging if content is empty or just placeholders to avoid token waste
            if content.strip() and "(no content)" not in content.lower():
                logger.debug(f"  MSG[{idx}] role={role}, tool_calls={tool_calls}, content={content}...")
            else:
                logger.debug(f"  MSG[{idx}] role={role}, tool_calls={tool_calls}, content=[empty/placeholder]")

    # Newer OpenAI models models (o1, o3, o4, gpt-5) require max_completion_tokens instead of max_tokens
    if is_newer_model:
        openai_request["max_completion_tokens"] = token_limit
        # Newer reasoning models require temperature=1
        openai_request["temperature"] = 1
        logger.debug(f"Converted request (newer model): model={openai_model}, messages={len(openai_messages)}, max_completion_tokens={token_limit}, temperature=1")
    else:
        openai_request["max_tokens"] = token_limit
        # Use client-requested temperature - no hardcoded overrides
        openai_request["temperature"] = claude_request.temperature
        logger.debug(f"Converted request: model={openai_model}, messages={len(openai_messages)}, max_tokens={token_limit}, temp={claude_request.temperature}")
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
                # Sanitize input schema to remove 'defer_loading' which causes Google API errors
                input_schema = tool.input_schema.copy() if tool.input_schema else {}
                if "defer_loading" in input_schema:
                    del input_schema["defer_loading"]
                
                openai_tools.append(
                    {
                        "type": Constants.TOOL_FUNCTION,
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": input_schema,
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
            # Reconstruct tool call
            tool_name = block.name
            arguments = block.input
            
            # REVERSE RENAMING: If tool is Bash/Repl, convert 'command' back to 'prompt'
            # This ensures Gemini sees the parameter name IT expects in the history, 
            # preventing it from getting confused and retrying.
            if tool_name.lower() in ["bash", "repl"] and isinstance(arguments, dict):
                # Copy dict to avoid modifying original object if shared
                arguments = arguments.copy()
                if "command" in arguments and "prompt" not in arguments:
                    arguments["prompt"] = arguments.pop("command")
            
            tool_calls.append(
                {
                    "id": block.id,
                    "type": Constants.TOOL_FUNCTION,
                    Constants.TOOL_FUNCTION: {
                        "name": tool_name,
                        "arguments": json.dumps(arguments, ensure_ascii=False),
                    },
                }
            )
        # Explicitly skip thinking blocks to avoid 422 errors
        elif block.type == "thinking" or block.type == "redacted_thinking":
            continue

    openai_message = {"role": Constants.ROLE_ASSISTANT}

    # Set content
    if text_parts:
        openai_message["content"] = "".join(text_parts)
    elif tool_calls:
        # If we have tool calls, content should be None for most OpenAI-compatible models.
        # This prevents Gemini from seeing an "interrupted" placeholder like "..." and 
        # autonomously repeating the previous forensic steps (Ghost Calls).
        openai_message["content"] = None
    else:
        # If no text AND no tool calls (e.g. only thinking blocks), we MUST provide 
        # some content to avoid a 400 error from the Google API.
        openai_message["content"] = "(thinking)"

    # Set tool calls
    if tool_calls:
        openai_message["tool_calls"] = tool_calls

    return openai_message


def convert_claude_tool_results(msg: ClaudeMessage) -> List[Dict[str, Any]]:
    """Convert Claude tool results to OpenAI format with deduplication."""
    tool_messages = []
    seen_tool_ids = set()  # Deduplicate by tool_use_id

    if isinstance(msg.content, list):
        for block in msg.content:
            if block.type == Constants.CONTENT_TOOL_RESULT:
                tool_id = block.tool_use_id
                # Skip duplicate tool results (same tool_use_id)
                if tool_id in seen_tool_ids:
                    logger.debug(f"DEDUP: Skipping duplicate tool_result for tool_use_id={tool_id}")
                    continue
                seen_tool_ids.add(tool_id)

                content = parse_tool_result_content(block.content)
                tool_messages.append(
                    {
                        "role": Constants.ROLE_TOOL,
                        "tool_call_id": tool_id,
                        "content": content,
                    }
                )

    return tool_messages


def parse_tool_result_content(content):
    """Parse and normalize tool result content into a string format.

    Applies truncation for large outputs to save tokens.
    """
    if content is None:
        return "No content provided"

    result = None

    if isinstance(content, str):
        result = content

    elif isinstance(content, list):
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
        result = "\n".join(result_parts).strip()

    elif isinstance(content, dict):
        if content.get("type") == Constants.CONTENT_TEXT:
            result = content.get("text", "")
        else:
            try:
                result = json.dumps(content, ensure_ascii=False)
            except (TypeError, ValueError):
                result = str(content)

    else:
        try:
            result = str(content)
        except Exception:
            result = "Unparseable content"

    # Apply truncation for large tool outputs (token efficiency)
    if result:
        result, was_truncated = truncate_tool_output(result)

    return result
