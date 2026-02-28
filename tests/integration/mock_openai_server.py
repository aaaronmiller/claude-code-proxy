"""
Mock OpenAI-compatible upstream for cascade integration tests.

Behavior is controlled via environment variables:
- PRIMARY_MODEL (default: primary-model)
- FALLBACK_MODEL (default: fallback-model)
- PRIMARY_ERROR_MODE: always_429 | always_200 (default: always_429)
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()

PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL", "primary-model")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "fallback-model")
PRIMARY_ERROR_MODE = os.environ.get("PRIMARY_ERROR_MODE", "always_429")

CALLS: List[Dict[str, Any]] = []


def _usage() -> Dict[str, int]:
    return {"prompt_tokens": 20, "completion_tokens": 12, "total_tokens": 32}


def _tool_call_message(model: str) -> Dict[str, Any]:
    return {
        "id": "chatcmpl-mock-tool",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_mock_1",
                            "type": "function",
                            "function": {
                                "name": "Read",
                                "arguments": json.dumps({"file_path": "README.md"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": _usage(),
    }


def _text_message(model: str, text: str) -> Dict[str, Any]:
    return {
        "id": "chatcmpl-mock-text",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": _usage(),
    }


@app.get("/v1/models")
async def list_models() -> Dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {"id": PRIMARY_MODEL, "object": "model", "created": int(time.time()), "owned_by": "mock"},
            {"id": FALLBACK_MODEL, "object": "model", "created": int(time.time()), "owned_by": "mock"},
        ],
    }


@app.get("/debug/calls")
async def debug_calls() -> Dict[str, Any]:
    return {"calls": CALLS, "count": len(CALLS)}


@app.post("/debug/reset")
async def debug_reset() -> Dict[str, Any]:
    CALLS.clear()
    return {"ok": True}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "")
    stream = bool(body.get("stream", False))
    tools = body.get("tools") or []
    messages = body.get("messages", [])

    CALLS.append(
        {
            "model": model,
            "stream": stream,
            "tools": bool(tools),
            "messages": len(messages),
            "ts": int(time.time()),
        }
    )

    if model == PRIMARY_MODEL and PRIMARY_ERROR_MODE == "always_429":
        return JSONResponse(
            status_code=429,
            content={"error": {"message": "mock primary rate limit", "type": "rate_limit"}},
        )

    if stream:
        async def gen():
            first = {
                "id": "chatcmpl-mock-stream",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "delta": {"content": f"stream from {model}"}, "finish_reason": None}],
            }
            stop = {
                "id": "chatcmpl-mock-stream",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                "usage": _usage(),
            }
            yield f"data: {json.dumps(first)}\n\n"
            yield f"data: {json.dumps(stop)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    has_tool_result = any(m.get("role") == "tool" for m in messages if isinstance(m, dict))
    if tools and not has_tool_result:
        return _tool_call_message(model)

    return _text_message(model, f"final response from {model}")
