import json
import uuid
from fastapi import HTTPException, Request
from src.core.constants import Constants
from src.models.claude import ClaudeMessagesRequest


def convert_openai_to_claude_response(
    openai_response: dict, original_request: ClaudeMessagesRequest
) -> dict:
    """Convert OpenAI response to Claude format with enhanced error handling."""

    # Validate response structure
    if not isinstance(openai_response, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid OpenAI response format: expected dictionary"
        )

    # Extract response data with validation
    choices = openai_response.get("choices", [])
    if not choices:
        raise HTTPException(
            status_code=500,
            detail="No choices in OpenAI response"
        )

    if not isinstance(choices, list):
        raise HTTPException(
            status_code=500,
            detail="Invalid choices format in OpenAI response"
        )

    choice = choices[0]
    if not isinstance(choice, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid choice format in OpenAI response"
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

            # PATCH: Alias arguments for CLI compatibility (Bash, Task, Skill)
            tool_name = function_data.get("name", "")
            tool_name_lower = tool_name.lower() if tool_name else ""
            
            # Bash/Repl: command <-> prompt
            if tool_name_lower in ["bash", "repl"]:
                if "command" in arguments and "prompt" not in arguments:
                    arguments["prompt"] = arguments["command"]
                elif "prompt" in arguments and "command" not in arguments:
                    arguments["command"] = arguments["prompt"]
            
            # Task: description <-> prompt, default subagent_type
            if tool_name_lower == "task":
                if "description" in arguments and "prompt" not in arguments:
                    arguments["prompt"] = arguments["description"]
                elif "prompt" in arguments and "description" not in arguments:
                    arguments["description"] = arguments["prompt"]
                if "subagent_type" not in arguments:
                    arguments["subagent_type"] = "research"
            
            # Skill: pass through unchanged - CLI expects 'skill'\n            # (Gemini sends 'skill', CLI expects 'skill' - no transformation needed)
            
            # TodoWrite: tasks -> todos + normalize status values
            if tool_name_lower == "todowrite":
                if "tasks" in arguments and "todos" not in arguments:
                    arguments["todos"] = arguments["tasks"]
                if "tasks" in arguments:
                    del arguments["tasks"]
                # Normalize status values
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
    openai_stream, original_request: ClaudeMessagesRequest, logger
):
    """Convert OpenAI streaming response to Claude streaming format."""

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
                    reasoning_content = delta.get("reasoning_content") or delta.get("thinking")
                    
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
                                    "started": False
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
                            if (tool_call["id"] and tool_call["name"] and not tool_call["started"]):
                                current_block_index += 1
                                tool_call["claude_index"] = current_block_index
                                tool_call["started"] = True
                                
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': tool_call['claude_index'], 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call['id'], 'name': tool_call['name']}}, ensure_ascii=False)}\n\n"
                            
                            # Handle Arguments
                            if "arguments" in function_data and tool_call["started"] and function_data["arguments"] is not None:
                                partial_args = function_data["arguments"]
                                tool_call["args_buffer"] += partial_args
                                
                                # Send delta immediately (Streaming)
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': tool_call['claude_index'], 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': partial_args}}, ensure_ascii=False)}\n\n"
                                    
                    # Handle finish reason
                    if finish_reason:
                        if finish_reason == "length":
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ["tool_calls", "function_call"]:
                            final_stop_reason = Constants.STOP_TOOL_USE
                        elif finish_reason == "stop":
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN
                        
                        # Close any open block
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            # We DON'T set current_block_index = -1 here
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
):
    """Convert OpenAI streaming response to Claude streaming format with cancellation support."""

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
                            prompt_tokens_details = usage.get('prompt_tokens_details', {})
                            if prompt_tokens_details:
                                cache_read_input_tokens = prompt_tokens_details.get('cached_tokens', 0)
                            usage_data = {
                                'input_tokens': usage.get('prompt_tokens', 0),
                                'output_tokens': usage.get('completion_tokens', 0),
                                'cache_read_input_tokens': cache_read_input_tokens
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
                    reasoning_content = delta.get("reasoning_content") or delta.get("thinking")
                    
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

                    # Handle tool call deltas - ID-BASED DEDUPLICATION LOGIC
                    if "tool_calls" in delta and delta["tool_calls"]:
                        # Close previous block if we were doing text/thinking
                        if current_block_type in ["thinking", "text"]:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_type = "tool"

                        for tc_delta in delta["tool_calls"]:
                            tc_index = tc_delta.get("index", 0)
                            tc_id = tc_delta.get("id")
                            
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
                                    target_claude_index = active_tool_ids[tc_id]["claude_index"]
                                    
                                    # Log potential ghost call
                                    if active_tool_ids[tc_id]["primary_index"] != tc_index:
                                        # Secondary stream for same ID -> Ghost Call
                                        # Policy: IGNORE secondary stream content to prevent arg duplication
                                        logger.debug(f"Ignoring ghost stream for ID {tc_id} (index {tc_index} vs primary {active_tool_ids[tc_id]['primary_index']})")
                                        continue
                                else:
                                    # New unique ID -> New Block
                                    current_block_index += 1
                                    target_claude_index = current_block_index
                                    is_new_block = True
                                    
                                    active_tool_ids[tc_id] = {
                                        "primary_index": tc_index,
                                        "claude_index": current_block_index
                                    }
                                    logger.debug(f"New tool call detected: index={tc_index}, id={tc_id} -> claude_index={current_block_index}")
                            
                            # Case 2: No ID (streaming arguments)
                            else:
                                # Look up ID from stream index
                                known_id = stream_index_to_id.get(tc_index)
                                if known_id and known_id in active_tool_ids:
                                    target_claude_index = active_tool_ids[known_id]["claude_index"]
                                else:
                                    # No ID map found. This happens if:
                                    # a) Stream started without ID (rare for OpenAI, possible for broken proxies)
                                    # b) We filtered out the start (ghost call without ID)
                                    
                                    # Heuristic: If index > 0 and we haven't mapped it, it's likely a ghost call
                                    if tc_index > 0:
                                        logger.debug(f"Ignoring unmapped tool delta at index {tc_index}")
                                        continue
                                    
                                    # Fallback for index 0 if something weird happened
                                    if current_tool_calls.get(0, {}).get("claude_index") is not None:
                                        target_claude_index = current_tool_calls[0]["claude_index"]
                                        logger.debug(f"Fallback: mapping index 0 to existing claude_index {target_claude_index}")
                            
                            # If we decided to process this delta
                            if target_claude_index is not None:
                                if tc_index not in current_tool_calls:
                                    current_tool_calls[tc_index] = {
                                        "id": None,
                                        "name": None,
                                        "args_buffer": "",
                                        "json_sent": False,
                                        "claude_index": target_claude_index,
                                        "started": False
                                    }
                                
                                tool_call = current_tool_calls[tc_index]
                                
                                # Update Internal State
                                if tc_id: tool_call["id"] = tc_id
                                
                                function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                                if function_data.get("name"):
                                    tool_call["name"] = function_data["name"]
                                
                                # Emit START block if needed (only for the first time we see this ID/Block)
                                if is_new_block:
                                    tool_call["started"] = True # Mark local tracker as started too
                                    # Ensure we have a name (or empty string placeholder if needed, though OpenAI usually sends name with ID)
                                    name_val = tool_call["name"] or ""
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': target_claude_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call['id'], 'name': name_val}}, ensure_ascii=False)}\n\n"
                                
                                # Emit DELTA for arguments
                                if "arguments" in function_data and function_data["arguments"]:
                                    partial_args = function_data["arguments"]
                                    tool_call["args_buffer"] += partial_args
                                    
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': target_claude_index, 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': partial_args}}, ensure_ascii=False)}\n\n"
                                    

                    # Handle finish reason
                    if finish_reason:

                        if finish_reason == "length":
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ["tool_calls", "function_call"]:
                            final_stop_reason = Constants.STOP_TOOL_USE
                        elif finish_reason == "stop":
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN
                        
                        # Close any open block
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_index = -1

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
            logger.error(f"HTTPException during streaming: {e.status_code} - {e.detail}")
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

    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n"

