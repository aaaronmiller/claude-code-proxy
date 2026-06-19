from __future__ import annotations

import asyncio
from types import SimpleNamespace

from src.core.client import OpenAIClient


def _build_test_client() -> OpenAIClient:
    return OpenAIClient(api_key="test", base_url="http://localhost:12345/v1")


def test_nonstream_cascade_skips_primary_when_daily_threshold_reached(monkeypatch):
    client = _build_test_client()
    calls = []

    async def fake_create_chat_completion(request, request_id=None, config=None, api_key=None):
        calls.append(request["model"])
        return {
            "id": "mock",
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    monkeypatch.setattr(client, "create_chat_completion", fake_create_chat_completion)

    from src.services.usage.usage_tracker import usage_tracker

    monkeypatch.setattr(usage_tracker, "enabled", True)
    monkeypatch.setattr(
        usage_tracker,
        "get_daily_model_request_count",
        lambda model: 1000 if model == "primary-model" else 0,
    )

    config = SimpleNamespace(
        model_cascade=True,
        model_cascade_daily_limit=1000,
        get_cascade_for_tier=lambda tier: ["fallback-model"],
    )

    result = asyncio.run(
        client.create_chat_completion_with_cascade(
            {"model": "primary-model", "messages": [{"role": "user", "content": "hi"}]},
            tier="big",
            config=config,
            request_id="req-1",
        )
    )

    assert result["choices"][0]["message"]["content"] == "ok"
    assert calls == ["fallback-model"]


def test_stream_cascade_skips_primary_when_daily_threshold_reached(monkeypatch):
    client = _build_test_client()
    calls = []

    async def fake_create_chat_completion_stream(request, request_id=None, config=None, api_key=None):
        calls.append(request["model"])
        yield 'data: {"id":"x","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":null}]}\n\n'
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(client, "create_chat_completion_stream", fake_create_chat_completion_stream)

    from src.services.usage.usage_tracker import usage_tracker
    import src.core.client as client_module
    import src.services.usage.model_limits as model_limits_module

    monkeypatch.setattr(usage_tracker, "enabled", True)
    monkeypatch.setattr(
        usage_tracker,
        "get_daily_model_request_count",
        lambda model: 1000 if model == "primary-model" else 0,
    )
    # Prevent real env models from polluting the cascade candidates
    monkeypatch.setattr(client_module, "_get_dynamic_fallback_models", lambda limit=8: [])
    # Make every model name pass the context-limit filter
    monkeypatch.setattr(model_limits_module, "get_model_limits", lambda m: (200_000, 8192))

    config = SimpleNamespace(
        model_cascade=True,
        model_cascade_daily_limit=1000,
        get_cascade_for_tier=lambda tier: ["fallback-model"],
        toolcall_models=[],
        toolcall_max_retries=2,
        local_enabled=False,
        local_model=None,
        local_endpoint=None,
    )

    async def run():
        out = []
        async for line in client.create_chat_completion_stream_with_cascade(
            {"model": "primary-model", "messages": [{"role": "user", "content": "hi"}]},
            tier="big",
            config=config,
            request_id="req-2",
        ):
            out.append(line)
        return out

    out = asyncio.run(run())
    assert any("[DONE]" in line for line in out)
    assert calls == ["fallback-model"]
