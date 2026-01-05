import json
import uuid
import logging
import os
from fastapi import HTTPException, Request
from src.core.constants import Constants
from src.models.claude import ClaudeMessagesRequest
from src.services.providers.provider_detector import (
    NormalizationLevel,
    get_normalization_level,
)

# Debug flag for SSE tracing - enable to diagnose tool call streaming issues
DEBUG_SSE = os.getenv("DEBUG_SSE", "false").lower() == "true"
sse_logger = logging.getLogger("sse_debug")


def _normalize_tool_name(tool_name: str, provider: str = "gemini") -> str:
    """
    Normalize tool names that models may call with different names than expected.

    For example, some models call "write_file" instead of "Write".
    """
    tool_name_lower = tool_name.lower().replace("_", "")

    # Common tool name mappings
    name_mappings = {
        "readfile": "Read",
        "writefile": "Write",
        "runcommand": "Bash",
        "runbash": "Bash",
        "listfiles": "LS",
        "searchfiles": "Grep",
        "search": "Grep",
        "findfiles": "Glob",
        "createtask": "Task",
        "runtask": "Task",
        "todowrite": "TodoWrite",
        "todolist": "TodoRead",
        "todoread": "TodoRead",
        "webfetch": "WebFetch",
        "websearch": "WebSearch",
        "browse": "Browser",
        "notebookedit": "NotebookEdit",
        "notebookread": "NotebookRead",
        "multiedit": "MultiEdit",
        "agentdispatch": "AgentDispatch",
    }

    return name_mappings.get(tool_name_lower, tool_name)


def normalize_tool_arguments(
    tool_name: str, arguments: dict, provider: str = "gemini"
) -> dict:
    """
    Normalize tool arguments to match Claude Code CLI's expected schemas.

    This function transforms parameter names that may differ between providers
    (e.g., Gemini's "prompt" → Claude's "command" for Bash tools).

    Normalization intensity varies by provider:
    - NONE (openai, azure): Pass through unchanged
    - LIGHT (openrouter, openai_compatible): Common mismatches only
    - FULL (gemini): All 18+ tool transformations

    Handles ALL Claude Code CLI tools:
    - Tier 1: Bash, Repl, Read, Write, Edit, MultiEdit
    - Tier 2: Glob, Grep, LS
    - Tier 3: Task, AgentDispatch
    - Tier 4: TodoWrite, TodoRead
    - Tier 5: WebFetch, WebSearch, Browser
    - Tier 6: NotebookEdit, NotebookRead

    Args:
        tool_name: The name of the tool being called
        arguments: The raw arguments dict from the provider
        provider: The provider type (gemini, openrouter, openai, etc.)

    Returns:
        Normalized arguments dict matching Claude CLI schema
    """
    # First, normalize tool names that models may call differently
    tool_name = _normalize_tool_name(tool_name, provider)

    # Get normalization level based on provider
    normalization_level = get_normalization_level(provider)

    # Skip normalization entirely for providers that don't need it
    if normalization_level == NormalizationLevel.NONE.value:
        return arguments

    # Light normalization for OpenRouter and unknown providers
    if normalization_level == NormalizationLevel.LIGHT.value:
        return _light_normalize(tool_name, arguments)

    # Full normalization for Gemini
    return _full_normalize(tool_name, arguments)


def _light_normalize(tool_name: str, arguments: dict) -> dict:
    """
    Light normalization for OpenRouter and OpenAI-compatible providers.

    Handles common parameter mismatches that occur with non-Gemini providers.
    """
    tool_name_lower = tool_name.lower() if tool_name else ""

    # Bash/Repl: Most common mismatch
    if tool_name_lower in ["bash", "repl"]:
        if "prompt" in arguments and "command" not in arguments:
            arguments["command"] = arguments.pop("prompt")

    # Read: Common path variants
    if tool_name_lower == "read":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "filePath" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filePath")

    # Write: Claude CLI expects 'file_path' + 'content'
    # Models often send: path, filePath, filename → file_path
    #                    text, contents, data → content
    if tool_name_lower == "write":
        # Path variants
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "filePath" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filePath")
        elif "filename" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filename")
        elif "file" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("file")

        # Content variants
        if "text" in arguments and "content" not in arguments:
            arguments["content"] = arguments.pop("text")
        elif "contents" in arguments and "content" not in arguments:
            arguments["content"] = arguments.pop("contents")
        elif "data" in arguments and "content" not in arguments:
            arguments["content"] = arguments.pop("data")

    # Edit: Claude CLI expects 'file_path', 'old_text', 'new_text'
    if tool_name_lower == "edit":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "filePath" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filePath")

    return arguments


def _full_normalize(tool_name: str, arguments: dict) -> dict:
    """
    Full normalization for Gemini provider.

    Handles all 18+ Claude Code CLI tools with comprehensive parameter mapping.
    """
    tool_name_lower = tool_name.lower() if tool_name else ""

    # ============================================================
    # TIER 1: Core File Operations
    # ============================================================

    # Bash/Repl: Claude CLI expects 'command', Gemini may output 'prompt' or 'code'
    if tool_name_lower in ["bash", "repl"]:
        if "prompt" in arguments and "command" not in arguments:
            arguments["command"] = arguments.pop("prompt")
        elif "code" in arguments and "command" not in arguments:
            arguments["command"] = arguments.pop("code")

    # Read: Claude CLI expects 'file_path', Gemini may output 'path' or 'filename'
    if tool_name_lower == "read":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "filename" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filename")
        elif "file" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("file")

    # Write: Claude CLI expects 'file_path' + 'content'
    if tool_name_lower == "write":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "filename" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("filename")
        elif "file" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("file")
        # Content variants
        if "text" in arguments and "content" not in arguments:
            arguments["content"] = arguments.pop("text")
        elif "data" in arguments and "content" not in arguments:
            arguments["content"] = arguments.pop("data")

    # Edit: Claude CLI expects 'file_path', 'old_text', 'new_text'
    if tool_name_lower == "edit":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "file" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("file")
        # Text variants
        if "original" in arguments and "old_text" not in arguments:
            arguments["old_text"] = arguments.pop("original")
        elif "before" in arguments and "old_text" not in arguments:
            arguments["old_text"] = arguments.pop("before")
        if "replacement" in arguments and "new_text" not in arguments:
            arguments["new_text"] = arguments.pop("replacement")
        elif "after" in arguments and "new_text" not in arguments:
            arguments["new_text"] = arguments.pop("after")

    # MultiEdit: Claude CLI expects 'file_path' + 'edits' array
    if tool_name_lower == "multiedit":
        if "path" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("path")
        elif "file" in arguments and "file_path" not in arguments:
            arguments["file_path"] = arguments.pop("file")
        # Edits array variants
        if "changes" in arguments and "edits" not in arguments:
            arguments["edits"] = arguments.pop("changes")
        elif "modifications" in arguments and "edits" not in arguments:
            arguments["edits"] = arguments.pop("modifications")

    # ============================================================
    # TIER 2: Search & Navigation
    # ============================================================

    # Glob: Claude CLI expects 'pattern'
    if tool_name_lower == "glob":
        if "glob" in arguments and "pattern" not in arguments:
            arguments["pattern"] = arguments.pop("glob")
        elif "glob_pattern" in arguments and "pattern" not in arguments:
            arguments["pattern"] = arguments.pop("glob_pattern")

    # Grep: Claude CLI expects 'pattern' + optional 'path'
    if tool_name_lower == "grep":
        if "query" in arguments and "pattern" not in arguments:
            arguments["pattern"] = arguments.pop("query")
        elif "search" in arguments and "pattern" not in arguments:
            arguments["pattern"] = arguments.pop("search")
        elif "regex" in arguments and "pattern" not in arguments:
            arguments["pattern"] = arguments.pop("regex")
        # Path variants
        if "directory" in arguments and "path" not in arguments:
            arguments["path"] = arguments.pop("directory")
        elif "dir" in arguments and "path" not in arguments:
            arguments["path"] = arguments.pop("dir")

    # LS: Claude CLI expects 'path'
    if tool_name_lower == "ls":
        if "directory" in arguments and "path" not in arguments:
            arguments["path"] = arguments.pop("directory")
        elif "dir" in arguments and "path" not in arguments:
            arguments["path"] = arguments.pop("dir")
        elif "folder" in arguments and "path" not in arguments:
            arguments["path"] = arguments.pop("folder")

    # ============================================================
    # TIER 3: Task & Agent
    # ============================================================

    # Task: Claude CLI expects 'prompt' + 'description' + 'subagent_type'
    if tool_name_lower == "task":
        if "description" in arguments and "prompt" not in arguments:
            arguments["prompt"] = arguments["description"]
        elif "prompt" in arguments and "description" not in arguments:
            arguments["description"] = arguments["prompt"]
        # Check agent type variants FIRST before setting default
        if "agent_type" in arguments and "subagent_type" not in arguments:
            arguments["subagent_type"] = arguments.pop("agent_type")
        elif "type" in arguments and "subagent_type" not in arguments:
            arguments["subagent_type"] = arguments.pop("type")
        # Apply default LAST if still missing
        if "subagent_type" not in arguments:
            arguments["subagent_type"] = "Explore"

    # AgentDispatch: Claude CLI expects 'agent_id' + 'task'
    if tool_name_lower == "agentdispatch":
        if "id" in arguments and "agent_id" not in arguments:
            arguments["agent_id"] = arguments.pop("id")
        if "prompt" in arguments and "task" not in arguments:
            arguments["task"] = arguments.pop("prompt")
        elif "instruction" in arguments and "task" not in arguments:
            arguments["task"] = arguments.pop("instruction")

    # ============================================================
    # TIER 4: Todo Management
    # ============================================================

    # TodoWrite: tasks → todos + normalize status values
    if tool_name_lower == "todowrite":
        if "tasks" in arguments and "todos" not in arguments:
            arguments["todos"] = arguments["tasks"]
        if "tasks" in arguments:
            del arguments["tasks"]
        # Items variant
        if "items" in arguments and "todos" not in arguments:
            arguments["todos"] = arguments.pop("items")
        if "todos" in arguments and isinstance(arguments["todos"], list):
            valid_statuses = {"pending", "in_progress", "completed"}
            for todo in arguments["todos"]:
                if isinstance(todo, dict) and "status" in todo:
                    status = todo["status"]
                    if status not in valid_statuses:
                        if "complete" in status.lower():
                            todo["status"] = "completed"
                        elif "progress" in status.lower():
                            todo["status"] = "in_progress"
                        else:
                            todo["status"] = "pending"

    # TodoRead: No parameters typically, but handle variants
    if tool_name_lower == "todoread":
        # No normalization needed - usually parameterless
        pass

    # ============================================================
    # TIER 5: Web & Browser
    # ============================================================

    # WebFetch: Claude CLI expects 'url'
    if tool_name_lower == "webfetch":
        if "link" in arguments and "url" not in arguments:
            arguments["url"] = arguments.pop("link")
        elif "href" in arguments and "url" not in arguments:
            arguments["url"] = arguments.pop("href")
        elif "address" in arguments and "url" not in arguments:
            arguments["url"] = arguments.pop("address")

    # WebSearch: Claude CLI expects 'query'
    if tool_name_lower == "websearch":
        if "search" in arguments and "query" not in arguments:
            arguments["query"] = arguments.pop("search")
        elif "q" in arguments and "query" not in arguments:
            arguments["query"] = arguments.pop("q")
        elif "term" in arguments and "query" not in arguments:
            arguments["query"] = arguments.pop("term")

    # Browser: Claude CLI expects 'url' + 'action'
    if tool_name_lower == "browser":
        if "link" in arguments and "url" not in arguments:
            arguments["url"] = arguments.pop("link")
        elif "address" in arguments and "url" not in arguments:
            arguments["url"] = arguments.pop("address")
        # Action variants
        if "command" in arguments and "action" not in arguments:
            arguments["action"] = arguments.pop("command")
        elif "operation" in arguments and "action" not in arguments:
            arguments["action"] = arguments.pop("operation")

    # ============================================================
    # TIER 6: Notebook Operations
    # ============================================================

    # NotebookEdit: Claude CLI expects 'notebook_path' + 'cell_id' + 'content'
    if tool_name_lower == "notebookedit":
        if "path" in arguments and "notebook_path" not in arguments:
            arguments["notebook_path"] = arguments.pop("path")
        elif "file" in arguments and "notebook_path" not in arguments:
            arguments["notebook_path"] = arguments.pop("file")
        # Cell ID variants
        if "cell" in arguments and "cell_id" not in arguments:
            arguments["cell_id"] = arguments.pop("cell")
        elif "index" in arguments and "cell_id" not in arguments:
            arguments["cell_id"] = arguments.pop("index")

    # NotebookRead: Claude CLI expects 'notebook_path'
    if tool_name_lower == "notebookread":
        if "path" in arguments and "notebook_path" not in arguments:
            arguments["notebook_path"] = arguments.pop("path")
        elif "file" in arguments and "notebook_path" not in arguments:
            arguments["notebook_path"] = arguments.pop("file")

    return arguments


def streaming_transform_partial(
    partial_args: str, tool_name: str, provider: str = "gemini"
) -> str:
    """
    Return partial args as-is to prevent content corruption.

    CRITICAL BUG FIX: The original implementation used naive string replacement
    (e.g., transformed.replace('"text":', '"content":')) which could corrupt
    user-generated content that happens to contain these patterns.

    Example corruption scenario:
    - User asks: "Write a script that creates a file with {'text': 'hello'}"
    - Old code would replace "text" in the file content itself
    - Result: Corrupted file with {'content': 'hello'} instead

    The proper normalization happens in normalize_tool_arguments() which parses
    the complete JSON and only transforms keys, not content.

    Returns:
        Unmodified partial_args string
    """
    return partial_args


def convert_openai_to_claude_response(
    openai_response: dict,
    original_request: ClaudeMessagesRequest,
    provider: str = "gemini",
) -> dict:
    """Convert OpenAI response to Claude format with enhanced error handling."""

    # Validate response structure
    if not isinstance(openai_response, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid OpenAI response format: expected dictionary",
        )

    # Extract response data with validation
    choices = openai_response.get("choices", [])
    if not choices:
        raise HTTPException(status_code=500, detail="No choices in OpenAI response")

    if not isinstance(choices, list):
        raise HTTPException(
            status_code=500, detail="Invalid choices format in OpenAI response"
        )

    choice = choices[0]
    if not isinstance(choice, dict):
        raise HTTPException(
            status_code=500, detail="Invalid choice format in OpenAI response"
        )

    message = choice.get("message", {})

    # Build Claude content blocks
    content_blocks = []

    # Add text content
    text_content = message.get("content")
    if text_content is not None:
        content_blocks.append({"type": Constants.CONTENT_TEXT, "text": text_content})

    # Add tool calls
    tool_calls = message.get("tool_calls", []) or []
    for tool_call in tool_calls:
        if tool_call.get("type") == Constants.TOOL_FUNCTION:
            function_data = tool_call.get(Constants.TOOL_FUNCTION, {})
            try:
                arguments = json.loads(function_data.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {"raw_arguments": function_data.get("arguments", "")}

            # Normalize tool name first, then arguments
            original_tool_name = function_data.get("name", "")
            tool_name = _normalize_tool_name(original_tool_name, provider)
            arguments = normalize_tool_arguments(tool_name, arguments, provider)

            content_blocks.append(
                {
                    "type": Constants.CONTENT_TOOL_USE,
                    "id": tool_call.get("id", f"tool_{uuid.uuid4()}"),
                    "name": tool_name,
                    "input": arguments,
                }
            )

    # Ensure at least one content block
    if not content_blocks:
        content_blocks.append({"type": Constants.CONTENT_TEXT, "text": ""})

    # Map finish reason
    finish_reason = choice.get("finish_reason", "stop")
    stop_reason = {
        "stop": Constants.STOP_END_TURN,
        "length": Constants.STOP_MAX_TOKENS,
        "tool_calls": Constants.STOP_TOOL_USE,
        "function_call": Constants.STOP_TOOL_USE,
    }.get(finish_reason, Constants.STOP_END_TURN)

    # Build Claude response with prompt cache support
    usage = openai_response.get("usage", {})
    usage_data = {
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }

    # Add prompt cache tokens if available (OpenAI prompt caching)
    prompt_tokens_details = usage.get("prompt_tokens_details", {})
    if prompt_tokens_details:
        cache_read_input_tokens = prompt_tokens_details.get("cached_tokens", 0)
        if cache_read_input_tokens > 0:
            usage_data["cache_read_input_tokens"] = cache_read_input_tokens

    claude_response = {
        "id": openai_response.get("id", f"msg_{uuid.uuid4()}"),
        "type": "message",
        "role": Constants.ROLE_ASSISTANT,
        "model": original_request.model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": usage_data,
    }

    return claude_response


async def convert_openai_streaming_to_claude(
    openai_stream,
    original_request: ClaudeMessagesRequest,
    logger,
    provider: str = "gemini",
):
    """Convert OpenAI streaming response to Claude streaming format with provider-aware normalization."""

    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # Send initial SSE events - Message Start
    yield f"event: {Constants.EVENT_MESSAGE_START}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"

    # CRITICAL FIX: Always start with an empty text block.
    # Claude CLI seems to require this to initialize its display loop, otherwise it says "(no content)"
    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"

    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n"

    # State tracking
    # Start with text block active at index 0
    current_block_type = "text"
    current_block_index = 0

    current_tool_calls = {}
    final_stop_reason = Constants.STOP_END_TURN

    # Track usage if available
    usage_data = {"input_tokens": 0, "output_tokens": 0}

    try:
        async for line in openai_stream:
            if line.strip():
                if line.startswith("data: "):
                    chunk_data = line[6:]
                    if chunk_data.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(chunk_data)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to parse chunk: {chunk_data}, error: {e}"
                        )
                        continue

                    choice = choices[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")

                    # Handle reasoning/thinking content
                    reasoning_content = delta.get("reasoning_content") or delta.get(
                        "thinking"
                    )

                    if reasoning_content:
                        # Handle switching to thinking block
                        if current_block_type != "thinking":
                            if current_block_index >= 0:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

                            current_block_index += 1
                            current_block_type = "thinking"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_THINKING, 'thinking': ''}}, ensure_ascii=False)}\n\n"

                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_THINKING, 'thinking': reasoning_content}}, ensure_ascii=False)}\n\n"

                    # Handle standard text content
                    text_content = delta.get("content")
                    if text_content is not None:
                        # Switch to text block if not already
                        if current_block_type != "text":
                            if current_block_index >= 0:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

                            current_block_index += 1
                            current_block_type = "text"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"

                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': text_content}}, ensure_ascii=False)}\n\n"

                    # Handle tool call deltas - SIMPLIFIED LOGIC (Restored from working version)
                    if "tool_calls" in delta and delta["tool_calls"]:
                        # Close previous block if we were doing text/thinking
                        if current_block_type in ["thinking", "text"]:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_type = "tool"

                        for tc_delta in delta["tool_calls"]:
                            tc_index = tc_delta.get("index", 0)

                            if tc_index not in current_tool_calls:
                                current_tool_calls[tc_index] = {
                                    "id": None,
                                    "name": None,
                                    "args_buffer": "",
                                    "json_sent": False,
                                    "claude_index": None,
                                    "started": False,
                                }

                            tool_call = current_tool_calls[tc_index]

                            # Update ID
                            if tc_delta.get("id"):
                                tool_call["id"] = tc_delta["id"]

                            # Update Name
                            function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                            if function_data.get("name"):
                                tool_call["name"] = function_data["name"]

                            # Start block if we have ID and Name
                            if (
                                tool_call["id"]
                                and tool_call["name"]
                                and not tool_call["started"]
                            ):
                                current_block_index += 1
                                tool_call["claude_index"] = current_block_index
                                tool_call["started"] = True

                                if DEBUG_SSE:
                                    sse_logger.info(
                                        f"SSE: content_block_start tool_use index={current_block_index} name={tool_call['name']} id={tool_call['id'][:12]}..."
                                    )

                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': tool_call['claude_index'], 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call['id'], 'name': tool_call['name']}}, ensure_ascii=False)}\n\n"

                            # Handle Arguments - Transform parameter names on-the-fly (provider-aware)
                            if (
                                "arguments" in function_data
                                and tool_call["started"]
                                and function_data["arguments"] is not None
                            ):
                                partial_args = function_data["arguments"]
                                tool_call["args_buffer"] += partial_args

                                # Use provider-aware streaming transformation
                                transformed_partial = streaming_transform_partial(
                                    partial_args, tool_call["name"], provider
                                )

                                # Send transformed delta - skip the inline transformations below
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': tool_call['claude_index'], 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': transformed_partial}}, ensure_ascii=False)}\n\n"

                    # Handle finish reason
                    if finish_reason:
                        if DEBUG_SSE:
                            sse_logger.info(
                                f"SSE: finish_reason={finish_reason} current_block_index={current_block_index} current_block_type={current_block_type}"
                            )

                        if finish_reason == "length":
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ["tool_calls", "function_call"]:
                            final_stop_reason = Constants.STOP_TOOL_USE

                            # Process completed tool calls - normalize accumulated arguments
                            # This ensures arguments are properly transformed even though streaming uses raw partials
                            if DEBUG_SSE:
                                sse_logger.info(f"Processing {len(current_tool_calls)} completed tool calls")

                            for tc_index, tool_call in current_tool_calls.items():
                                if tool_call["started"] and tool_call["name"]:
                                    try:
                                        # Parse the accumulated args_buffer
                                        if tool_call["args_buffer"]:
                                            complete_args = json.loads(tool_call["args_buffer"])
                                            normalized_args = normalize_tool_arguments(
                                                tool_call["name"], complete_args, provider
                                            )
                                            if DEBUG_SSE:
                                                sse_logger.info(
                                                    f"Normalized args for '{tool_call['name']}': {normalized_args}"
                                                )
                                            # Store normalized args back in the tool call for potential use
                                            tool_call["normalized_args"] = normalized_args
                                    except json.JSONDecodeError as e:
                                        if DEBUG_SSE:
                                            sse_logger.warning(
                                                f"Failed to parse args_buffer for '{tool_call['name']}': {e}"
                                            )

                        elif finish_reason == "stop":
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN

                        if DEBUG_SSE:
                            sse_logger.info(
                                f"SSE: final_stop_reason={final_stop_reason}"
                            )

                        # Close any open block
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_index = -1  # Mark as closed to prevent duplicate close in final cleanup
                            current_block_type = None

                        break

    except Exception as e:
        # Handle any streaming errors gracefully
        logger.error(f"Streaming error: {e}")

        error_event = {
            "type": "error",
            "error": {"type": "api_error", "message": f"Streaming error: {str(e)}"},
        }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        return

    # Send final SSE events
    if current_block_index >= 0 and current_block_type is not None:
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

    if DEBUG_SSE:
        sse_logger.info(
            f"SSE: message_delta stop_reason={final_stop_reason} usage={usage_data}"
        )

    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n"


async def convert_openai_streaming_to_claude_with_cancellation(
    openai_stream,
    original_request: ClaudeMessagesRequest,
    logger,
    http_request: Request,
    openai_client,
    request_id: str,
    config=None,
    provider: str = "gemini",
):
    """Convert OpenAI streaming response to Claude streaming format with cancellation support and provider-aware normalization."""

    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # Send initial SSE events - Message Start
    yield f"event: {Constants.EVENT_MESSAGE_START}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"

    # CRITICAL FIX: Always start with an empty text block.
    # Claude CLI seems to require this to initialize its display loop, otherwise it says "(no content)"
    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"

    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n"

    # State tracking
    # Start with text block active at index 0
    current_block_type = "text"
    current_block_index = 0

    current_tool_calls = {}

    # ID-based deduplication state
    # Map: tool_call_id -> {primary_index: int, claude_index: int}
    active_tool_ids = {}

    # Fallback map for streams that don't send IDs in every chunk
    # Map: stream_index -> tool_call_id
    stream_index_to_id = {}

    # Content-based deduplication: (name, args_prefix) -> first_tool_id
    # This catches duplicate tool calls with DIFFERENT IDs but SAME content
    # (Gemini sometimes emits the same tool call multiple times with unique IDs)
    content_fingerprints = {}

    # Set of tool_call IDs that were detected as duplicates and should be skipped
    skipped_tool_ids = set()

    final_stop_reason = Constants.STOP_END_TURN
    usage_data = {"input_tokens": 0, "output_tokens": 0}

    try:
        async for line in openai_stream:
            # Check if client disconnected
            if await http_request.is_disconnected():
                logger.info(f"Client disconnected, cancelling request {request_id}")
                openai_client.cancel_request(request_id)
                break

            if line.strip():
                if line.startswith("data: "):
                    chunk_data = line[6:]
                    if chunk_data.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(chunk_data)
                        # logger.info(f"OpenAI chunk: {json.dumps(chunk, ensure_ascii=False)[:500]}")
                        usage = chunk.get("usage", None)
                        if usage:
                            cache_read_input_tokens = 0
                            prompt_tokens_details = usage.get(
                                "prompt_tokens_details", {}
                            )
                            if prompt_tokens_details:
                                cache_read_input_tokens = prompt_tokens_details.get(
                                    "cached_tokens", 0
                                )
                            usage_data = {
                                "input_tokens": usage.get("prompt_tokens", 0),
                                "output_tokens": usage.get("completion_tokens", 0),
                                "cache_read_input_tokens": cache_read_input_tokens,
                            }
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to parse chunk: {chunk_data}, error: {e}"
                        )
                        continue

                    choice = choices[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")

                    # Handle reasoning/thinking content
                    reasoning_content = delta.get("reasoning_content") or delta.get(
                        "thinking"
                    )

                    if reasoning_content:
                        # Handle switching to thinking block
                        if current_block_type != "thinking":
                            if current_block_index >= 0:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

                            current_block_index += 1
                            current_block_type = "thinking"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_THINKING, 'thinking': ''}}, ensure_ascii=False)}\n\n"

                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_THINKING, 'thinking': reasoning_content}}, ensure_ascii=False)}\n\n"

                    # Handle standard text content
                    text_content = delta.get("content")
                    # Only process if content is non-empty (skip null/empty during tool calls)
                    if text_content:
                        # Switch to text block if not already
                        if current_block_type != "text":
                            if current_block_index >= 0:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

                            current_block_index += 1
                            current_block_type = "text"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"

                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': text_content}}, ensure_ascii=False)}\n\n"
                        # Only log non-empty text content to avoid spam
                        if text_content.strip():
                            logger.debug(
                                f"STREAM: text delta idx={current_block_index}, text='{text_content[:30]}'"
                            )

                    # Handle tool call deltas - ID-BASED DEDUPLICATION LOGIC
                    if "tool_calls" in delta and delta["tool_calls"]:
                        # Close previous block if we were doing text/thinking
                        if current_block_type in ["thinking", "text"]:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_type = "tool"

                        for tc_delta in delta["tool_calls"]:
                            tc_index = tc_delta.get("index", 0)
                            tc_id = tc_delta.get("id")

                            # EARLY SKIP: If this tool call ID was already marked as duplicate, skip all chunks
                            if tc_id and tc_id in skipped_tool_ids:
                                continue

                            # Determine Target Claude Block Index
                            target_claude_index = None
                            is_new_block = False

                            # Case 1: We have an ID (start of a call or redundant ID)
                            if tc_id:
                                stream_index_to_id[tc_index] = tc_id

                                if tc_id in active_tool_ids:
                                    # Known ID -> Duplicate/Ghost stream?
                                    # If the index is different from the primary one, it's a ghost stream.
                                    # We should MERGE into the existing block but be careful not to duplicate args.
                                    # Usually, ghost streams send duplicate args. Ideally we ignore args from secondary streams.
                                    target_claude_index = active_tool_ids[tc_id][
                                        "claude_index"
                                    ]

                                    # Log potential ghost call
                                    if (
                                        active_tool_ids[tc_id]["primary_index"]
                                        != tc_index
                                    ):
                                        # Secondary stream for same ID -> Ghost Call
                                        # Policy: IGNORE secondary stream content to prevent arg duplication
                                        logger.debug(
                                            f"Ignoring ghost stream for ID {tc_id} (index {tc_index} vs primary {active_tool_ids[tc_id]['primary_index']})"
                                        )
                                        continue
                                else:
                                    # New unique ID -> Check fingerprint FIRST before creating block
                                    # This catches duplicates with different IDs but same operation

                                    # Try to get tool name early (may be in this chunk)
                                    function_data = tc_delta.get(
                                        Constants.TOOL_FUNCTION, {}
                                    )
                                    original_tool_name = function_data.get("name", "")
                                    tool_name = _normalize_tool_name(
                                        original_tool_name, provider
                                    )
                                    first_args = function_data.get("arguments", "")

                                    if tool_name:
                                        # Create fingerprint from name + first 50 chars of args
                                        fingerprint = f"{tool_name}:{first_args[:50]}"

                                        if fingerprint in content_fingerprints:
                                            # DUPLICATE DETECTED - skip this tool call entirely
                                            original_id = content_fingerprints[
                                                fingerprint
                                            ]
                                            logger.info(
                                                f"DEDUP: Blocking duplicate tool call '{tool_name}' (id={tc_id}) - matches existing (id={original_id})"
                                            )
                                            # Mark in a skip set so we ignore all future chunks for this ID
                                            if "skipped_ids" not in locals():
                                                skipped_ids = set()
                                            skipped_tool_ids.add(tc_id)
                                            continue
                                        else:
                                            # First occurrence - register fingerprint
                                            content_fingerprints[fingerprint] = tc_id
                                            logger.debug(
                                                f"DEDUP: Registered fingerprint '{fingerprint}' for tool '{tool_name}' (id={tc_id})"
                                            )

                                    # Not a duplicate - create new block
                                    current_block_index += 1
                                    target_claude_index = current_block_index
                                    is_new_block = True

                                    active_tool_ids[tc_id] = {
                                        "primary_index": tc_index,
                                        "claude_index": current_block_index,
                                    }
                                    logger.debug(
                                        f"New tool call detected: index={tc_index}, id={tc_id} -> claude_index={current_block_index}"
                                    )

                            # Case 2: No ID (streaming arguments)
                            else:
                                # Look up ID from stream index
                                known_id = stream_index_to_id.get(tc_index)
                                if known_id and known_id in active_tool_ids:
                                    target_claude_index = active_tool_ids[known_id][
                                        "claude_index"
                                    ]
                                else:
                                    # No ID map found. This happens if:
                                    # a) Stream started without ID (rare for OpenAI, possible for broken proxies)
                                    # b) We filtered out the start (ghost call without ID)

                                    # Heuristic: If index > 0 and we haven't mapped it, it's likely a ghost call
                                    if tc_index > 0:
                                        logger.debug(
                                            f"Ignoring unmapped tool delta at index {tc_index}"
                                        )
                                        continue

                                    # Fallback for index 0 if something weird happened
                                    if (
                                        current_tool_calls.get(0, {}).get(
                                            "claude_index"
                                        )
                                        is not None
                                    ):
                                        target_claude_index = current_tool_calls[0][
                                            "claude_index"
                                        ]
                                        logger.debug(
                                            f"Fallback: mapping index 0 to existing claude_index {target_claude_index}"
                                        )

                            # Skip if no valid target
                            if target_claude_index is None:
                                continue

                            # Init tool_call state if new block
                            if is_new_block or tc_index not in current_tool_calls:
                                if tc_index not in current_tool_calls:
                                    current_tool_calls[tc_index] = {
                                        "id": tc_id,
                                        "name": None,
                                        "args_buffer": "",
                                        "claude_index": target_claude_index,
                                    }
                                tool_call_state = current_tool_calls[tc_index]
                            else:
                                tool_call_state = current_tool_calls.get(tc_index)
                                if not tool_call_state:
                                    continue

                            # Update Name
                            function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                            if function_data.get("name"):
                                tool_call_state["name"] = _normalize_tool_name(
                                    function_data["name"], provider
                                )

                            # Send block start if new block (duplicates were already filtered before reaching here)
                            if is_new_block and tc_id and tool_call_state.get("name"):
                                if DEBUG_SSE:
                                    sse_logger.info(
                                        f"SSE[cancel]: content_block_start tool_use index={target_claude_index} name={tool_call_state['name']} id={tc_id[:12]}..."
                                    )
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': target_claude_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tc_id, 'name': tool_call_state['name']}}, ensure_ascii=False)}\n\n"

                            if (
                                "arguments" in function_data
                                and function_data["arguments"] is not None
                            ):
                                partial_args = function_data["arguments"]
                                tool_call_state["args_buffer"] += partial_args

                                # Use provider-aware streaming transformation
                                transformed_partial = streaming_transform_partial(
                                    partial_args,
                                    tool_call_state.get("name", ""),
                                    provider,
                                )

                                # Send transformed delta
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': target_claude_index, 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': transformed_partial}}, ensure_ascii=False)}\n\n"

                    # Handle finish reason
                    if finish_reason:
                        if DEBUG_SSE:
                            sse_logger.info(
                                f"SSE[cancel]: finish_reason={finish_reason} current_block_index={current_block_index}"
                            )

                        if finish_reason == "length":
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ["tool_calls", "function_call"]:
                            final_stop_reason = Constants.STOP_TOOL_USE

                            # Process completed tool calls - normalize accumulated arguments
                            # This ensures arguments are properly transformed even though streaming uses raw partials
                            if DEBUG_SSE:
                                sse_logger.info(f"Processing {len(current_tool_calls)} completed tool calls (cancel version)")

                            for tc_index, tool_call in current_tool_calls.items():
                                if tool_call.get("name"):
                                    try:
                                        # Parse the accumulated args_buffer
                                        if tool_call["args_buffer"]:
                                            complete_args = json.loads(tool_call["args_buffer"])
                                            normalized_args = normalize_tool_arguments(
                                                tool_call["name"], complete_args, provider
                                            )
                                            if DEBUG_SSE:
                                                sse_logger.info(
                                                    f"Normalized args for '{tool_call['name']}': {normalized_args}"
                                                )
                                            # Store normalized args back in the tool call
                                            tool_call["normalized_args"] = normalized_args
                                    except json.JSONDecodeError as e:
                                        if DEBUG_SSE:
                                            sse_logger.warning(
                                                f"Failed to parse args_buffer for '{tool_call['name']}': {e}"
                                            )

                        elif finish_reason == "stop":
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN

                        if DEBUG_SSE:
                            sse_logger.info(
                                f"SSE[cancel]: final_stop_reason={final_stop_reason}"
                            )

                        # Close any open block
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_index = -1  # Mark as closed to prevent duplicate close in final cleanup
                            current_block_type = None

                        break

    except HTTPException as e:
        # Handle ALL HTTPExceptions (not just 499)
        if e.status_code == 499:
            logger.info(f"Request {request_id} was cancelled")
            error_event = {
                "type": "error",
                "error": {
                    "type": "cancelled",
                    "message": "Request was cancelled by client",
                },
            }
        else:
            logger.error(
                f"HTTPException during streaming: {e.status_code} - {e.detail}"
            )
            error_event = {
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": f"API error ({e.status_code}): {e.detail}",
                },
            }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        return
    except Exception as e:
        # Handle any streaming errors gracefully
        logger.error(f"Streaming error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        error_event = {
            "type": "error",
            "error": {"type": "api_error", "message": f"Streaming error: {str(e)}"},
        }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        return

    # Send final SSE events
    if current_block_index >= 0:
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"

    if DEBUG_SSE:
        sse_logger.info(
            f"SSE[cancel]: message_delta stop_reason={final_stop_reason} usage={usage_data}"
        )

    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n"
