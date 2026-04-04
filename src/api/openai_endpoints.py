"""
OpenAI-Compatible Endpoint

Provides /v1/chat/completions endpoint for OpenAI-format IDEs:
- Codex CLI
- Gemini CLI
- Qwen Code
- OpenCode

This enables any OpenAI-format IDE to connect to VibeProxy and other
backends through this proxy.
"""

import json
import time
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.config import Config
from src.core.client import OpenAIClient
from src.core.model_manager import ModelManager
from src.services.ide import detect_ide, IDE
from src.services.tools import (
    normalize_tool_params,
    convert_tool_name,
    sanitize_function_name,
)
from src.services.providers import detect_provider, get_normalization_level
from src.services.conversion.response_converter import (
    streaming_transform_partial,
    normalize_tool_arguments,
)
from src.core.constants import Constants
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS (OpenAI Format)
# ═══════════════════════════════════════════════════════════════


class OpenAIMessage(BaseModel):
    """OpenAI message format."""

    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class OpenAIFunction(BaseModel):
    """OpenAI function definition."""

    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class OpenAITool(BaseModel):
    """OpenAI tool definition."""

    type: str = "function"
    function: OpenAIFunction


class OpenAIChatRequest(BaseModel):
    """OpenAI chat completion request."""

    model: str
    messages: List[OpenAIMessage]
    tools: Optional[List[OpenAITool]] = None
    tool_choice: Optional[Any] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Any] = None
    user: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def normalize_openai_tools_for_provider(
    tools: List[Dict[str, Any]], provider: str, source_ide: str
) -> List[Dict[str, Any]]:
    """
    Normalize tool definitions for the target provider.

    Converts tool names from source IDE format to Claude Code format,
    which is then properly handled by the existing normalization logic.
    """
    if not tools:
        return tools

    normalized = []
    for tool in tools:
        tool_copy = dict(tool)
        if "function" in tool_copy:
            func = dict(tool_copy["function"])
            original_name = func.get("name", "")

            # Convert tool name to Claude Code format (canonical)
            converted_name = convert_tool_name(original_name, "claude_code")

            # Sanitize function name for provider compatibility (PR #803)
            # Ensures: valid chars, no leading dots/digits, max 64 chars
            func["name"] = sanitize_function_name(converted_name)

            # Normalize parameters if present
            if "parameters" in func and func["parameters"]:
                params = func["parameters"]
                if "properties" in params:
                    # Normalize parameter names within the schema
                    props = params.get("properties", {})
                    normalized_props = {}
                    for key, val in props.items():
                        # This keeps schema intact, normalization happens at call time
                        normalized_props[key] = val
                    params["properties"] = normalized_props

            tool_copy["function"] = func
        normalized.append(tool_copy)

    return normalized


def normalize_tool_call_response(
    tool_calls: List[Dict[str, Any]], provider: str, target_ide: str
) -> List[Dict[str, Any]]:
    """
    Normalize tool calls in response back to target IDE format.

    This converts Claude Code format tool names back to the source IDE format.
    """
    if not tool_calls:
        return tool_calls

    normalized = []
    for tc in tool_calls:
        tc_copy = dict(tc)
        if "function" in tc_copy:
            func = dict(tc_copy["function"])
            original_name = func.get("name", "")

            # Convert back to target IDE format
            func["name"] = convert_tool_name(original_name, target_ide)

            # Normalize arguments
            if "arguments" in func:
                try:
                    args = (
                        json.loads(func["arguments"])
                        if isinstance(func["arguments"], str)
                        else func["arguments"]
                    )
                    # Apply provider-aware normalization
                    args = normalize_tool_arguments(original_name, args, provider)
                    func["arguments"] = (
                        json.dumps(args) if isinstance(func["arguments"], str) else args
                    )
                except (json.JSONDecodeError, TypeError):
                    pass

            tc_copy["function"] = func
        normalized.append(tc_copy)

    return normalized


# ═══════════════════════════════════════════════════════════════
# MAIN ENDPOINT
# ═══════════════════════════════════════════════════════════════


@router.post("/v1/chat/completions")
async def openai_chat_completions(request: Request, body: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Accepts requests from Codex CLI, Gemini CLI, Qwen Code, OpenCode
    and routes them to VibeProxy or other configured backends.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]

    # Get config and clients
    config = Config()

    # Validate required config values
    api_key = config.openai_api_key
    base_url = config.openai_base_url

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "No API key configured. Set PROVIDER_API_KEY or OPENAI_API_KEY environment variable.",
                    "type": "configuration_error",
                    "code": "missing_api_key",
                }
            },
        )

    if not base_url:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "No base URL configured. Set PROVIDER_BASE_URL or OPENAI_BASE_URL environment variable.",
                    "type": "configuration_error",
                    "code": "missing_base_url",
                }
            },
        )

    custom_headers = config.get_custom_headers()
    openai_client = OpenAIClient(
        api_key,
        base_url,
        config.request_timeout,
        api_version=config.azure_api_version,
        custom_headers=custom_headers,
    )
    openai_client.configure_per_model_clients(config)
    model_manager = ModelManager(config)

    # Detect source IDE
    headers = dict(request.headers)
    source_ide = detect_ide(
        headers=headers, path=str(request.url.path), body=body.model_dump()
    )

    logger.info(f"[{request_id}] OpenAI endpoint request from IDE: {source_ide}")
    logger.debug(f"[{request_id}] Model requested: {body.model}")

    try:
        # Parse model to get routing info
        routed_model, reasoning_config = model_manager.parse_and_map_model(body.model)

        # Determine endpoint and provider via provider registry
        client = openai_client.get_client_for_model(routed_model, config)
        endpoint = str(client.base_url) if hasattr(client, 'base_url') else config.openai_base_url
        provider = config.provider_for_endpoint(endpoint) if hasattr(config, 'provider_for_endpoint') else config.default_provider

        logger.debug(f"[{request_id}] Routing to {endpoint} (provider: {provider})")

        # Prepare request dict
        openai_request = body.model_dump(exclude_none=True)
        openai_request["model"] = routed_model

        def infer_model_tier(model_name: str) -> Optional[str]:
            def norm(name):
                return name.split("/", 1)[1].lower() if name and "/" in name else (name or "").lower()
            req = norm(model_name)
            if req == norm(config.big_model):
                return "big"
            if req == norm(config.middle_model):
                return "middle"
            if req == norm(config.small_model):
                return "small"
            return None

        # Normalize tools for provider
        if openai_request.get("tools"):
            openai_request["tools"] = normalize_openai_tools_for_provider(
                openai_request["tools"], provider, source_ide
            )
        tier = infer_model_tier(openai_request.get("model", ""))

        if body.stream:
            # Streaming response
            async def generate_stream():
                try:
                    saw_data_chunk = False
                    saw_done = False

                    def transform_chunk_dict(chunk_dict: Dict[str, Any]) -> List[str]:
                        # Normalize tool calls in streaming response
                        for choice in chunk_dict.get("choices", []):
                            delta = choice.get("delta", {})
                            if "tool_calls" in delta and delta["tool_calls"]:
                                delta["tool_calls"] = normalize_tool_call_response(
                                    delta["tool_calls"], provider, source_ide
                                )

                        # Fix for Issue #796: Split merged usage/finish_reason chunks
                        usage = chunk_dict.get("usage")
                        choices = chunk_dict.get("choices", [])
                        has_stop = any(choice.get("finish_reason") for choice in choices)

                        if usage and has_stop:
                            logger.debug(
                                f"[{request_id}] Detected merged usage/stop chunk, splitting..."
                            )
                            chunk_no_usage = chunk_dict.copy()
                            if "usage" in chunk_no_usage:
                                del chunk_no_usage["usage"]
                            chunk_usage_only = {
                                "id": chunk_dict.get("id"),
                                "object": chunk_dict.get(
                                    "object", "chat.completion.chunk"
                                ),
                                "created": chunk_dict.get("created"),
                                "model": chunk_dict.get("model"),
                                "choices": [],
                                "usage": usage,
                            }
                            return [
                                f"data: {json.dumps(chunk_no_usage)}\n\n",
                                f"data: {json.dumps(chunk_usage_only)}\n\n",
                            ]

                        return [f"data: {json.dumps(chunk_dict)}\n\n"]

                    if config.model_cascade and tier:
                        stream_lines = openai_client.create_chat_completion_stream_with_cascade(
                            openai_request,
                            tier=tier,
                            config=config,
                            request_id=request_id
                        )
                        async for line in stream_lines:
                            if not line.startswith("data: "):
                                continue
                            payload = line[6:].strip()
                            if payload == "[DONE]":
                                saw_done = True
                                yield "data: [DONE]\n\n"
                                break
                            chunk_dict = json.loads(payload)
                            saw_data_chunk = True
                            for output in transform_chunk_dict(chunk_dict):
                                yield output
                    else:
                        stream = await client.chat.completions.create(
                            **openai_request, stream=True
                        )
                        async for chunk in stream:
                            chunk_dict = chunk.model_dump()
                            saw_data_chunk = True
                            for output in transform_chunk_dict(chunk_dict):
                                yield output

                        if not saw_data_chunk:
                            logger.error(
                                f"[{request_id}] Upstream stream opened but produced no chunks "
                                f"(endpoint={endpoint}, provider={provider}, model={routed_model})"
                            )
                            error_chunk = {
                                "error": {
                                    "message": "Upstream stream closed without any chunks",
                                    "type": "empty_stream",
                                }
                            }
                            yield f"data: {json.dumps(error_chunk)}\n\n"
                            return

                        yield "data: [DONE]\n\n"
                        saw_done = True

                    if saw_data_chunk and not saw_done:
                        logger.warning(
                            f"[{request_id}] Stream ended after data without explicit [DONE] "
                            f"(endpoint={endpoint}, provider={provider}, model={routed_model})"
                        )

                except Exception as e:
                    logger.error(f"[{request_id}] Streaming error: {e}")
                    error_chunk = {"error": {"message": str(e), "type": "server_error"}}
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            # Non-streaming response
            if config.model_cascade and tier:
                response_dict = await openai_client.create_chat_completion_with_cascade(
                    openai_request,
                    tier=tier,
                    config=config,
                    request_id=request_id
                )
                # create_chat_completion_with_cascade returns dict in this codebase.
                # Keep response API stable by reusing dict directly.
                response_dict = response_dict if isinstance(response_dict, dict) else response_dict.model_dump()
            else:
                response = await client.chat.completions.create(**openai_request)
                response_dict = response.model_dump()

            # Normalize tool calls in response
            for choice in response_dict.get("choices", []):
                message = choice.get("message", {})
                if "tool_calls" in message and message["tool_calls"]:
                    message["tool_calls"] = normalize_tool_call_response(
                        message["tool_calls"], provider, source_ide
                    )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[{request_id}] Completed in {duration_ms:.0f}ms")

            return response_dict

    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "internal_error",
                }
            },
        )


@router.get("/v1/models")
async def list_models():
    """
    List available models endpoint.

    Required for Codex CLI and other OpenAI-format tools.
    """
    config = Config()

    created = int(time.time())
    model_ids: list[str] = []

    def add_model(model_id: str | None) -> None:
        if model_id and model_id not in model_ids:
            model_ids.append(model_id)

    # Advertise the actual routed backend models.
    add_model(config.big_model)
    add_model(config.middle_model)
    add_model(config.small_model)

    # Advertise Claude-facing aliases too. The request path maps these aliases
    # to BIG/MIDDLE/SMALL at runtime, so exposing them keeps Claude CLI model
    # selection valid even when the underlying backend models are non-Claude.
    for alias in [
        "opus",
        "sonnet",
        "sonnet[1m]",
        "haiku",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
        "claude-sonnet-4-6[1m]",
        "claude-haiku-4-5-20251001",
    ]:
        add_model(alias)

    models = [
        {
            "id": model_id,
            "object": "model",
            "created": created,
            "owned_by": "vibeproxy",
        }
        for model_id in model_ids
    ]

    return {"object": "list", "data": models}
