"""Regression test: cascade-exhausted path must surface a clean error, not a masked 500.

Root cause (fixed): when every cascade model is skipped before an attempt (e.g. all circuit
breakers open after repeated upstream failures), the loop exits with ``last_error is None`` and
the old code did ``raise APIError("All cascade models failed")``. The OpenAI SDK's
``APIError.__init__(message, request, *, body)`` requires ``request``, so that construction threw
``TypeError: ... missing 1 required positional argument: 'request'`` — which the endpoint layer
turned into a generic 500, masking the real cause. The fix raises ``HTTPException(503)`` instead.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import src.core.client as client_mod
from src.core.client import OpenAIClient


def _client() -> OpenAIClient:
    return OpenAIClient(api_key="test", base_url="http://localhost:12345/v1")


class _OpenCircuit:
    """Stub circuit breaker that is always OPEN, so every model is skipped."""

    is_open = True

    def _record_failure(self, *_a, **_k):  # pragma: no cover - not reached in this path
        return None


@pytest.fixture
def all_circuits_open(monkeypatch):
    monkeypatch.setattr(client_mod, "_get_circuit_breaker", lambda _model: _OpenCircuit())


_REQUEST = {"model": "primary-model", "messages": [{"role": "user", "content": "hi"}]}
_CONFIG = SimpleNamespace(
    model_cascade=True,
    model_cascade_daily_limit=0,
    get_cascade_for_tier=lambda tier: ["primary-model", "fallback-a", "fallback-b"],
)


def test_nonstream_cascade_all_skipped_raises_503_not_typeerror(all_circuits_open):
    client = _client()
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            client.create_chat_completion_with_cascade(
                _REQUEST, tier="big", config=_CONFIG, request_id="req-503"
            )
        )
    assert exc_info.value.status_code == 503
    assert "unavailable" in str(exc_info.value.detail).lower()


def test_stream_cascade_all_skipped_raises_503_not_typeerror(all_circuits_open):
    client = _client()

    async def _drain():
        agen = client.create_chat_completion_stream_with_cascade(
            _REQUEST, tier="big", config=_CONFIG, request_id="req-503s"
        )
        async for _chunk in agen:  # the raise fires while the loop exhausts
            pass

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(_drain())
    assert exc_info.value.status_code == 503


def test_apierror_is_never_constructed_with_only_a_message():
    """Guard: the SDK APIError needs a request; a bare message is a TypeError. This documents
    why the cascade fallback must not use APIError(message)."""
    from openai import APIError

    with pytest.raises(TypeError):
        APIError("all failed")  # noqa: B018 - intentional: proves the old construction was broken
