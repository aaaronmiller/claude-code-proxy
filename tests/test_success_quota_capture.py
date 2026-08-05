"""Successful SDK responses feed provider quota headers into the live cache."""

from src.core.client import OpenAIClient
from src.core.quota_live import QuotaCache, get_quota_cache

HEADERS = {
    "x-ratelimit-limit-requests": "100",
    "x-ratelimit-remaining-requests": "75",
}


class _Completion:
    def model_dump(self):
        return {"id": "ok", "choices": []}


class _Chunk:
    def model_dump(self):
        return {"id": "chunk", "choices": []}


class _Stream:
    def __init__(self):
        self._done = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._done:
            raise StopAsyncIteration
        self._done = True
        return _Chunk()


class _RawResponse:
    def __init__(self, parsed):
        self.headers = HEADERS
        self._parsed = parsed

    def parse(self):
        return self._parsed


class _RawCreate:
    def __init__(self, parsed):
        self._parsed = parsed

    async def create(self, **_kwargs):
        return _RawResponse(self._parsed)


class _Completions:
    def __init__(self, parsed):
        self.with_raw_response = _RawCreate(parsed)


class _Chat:
    def __init__(self, parsed):
        self.completions = _Completions(parsed)


class _Client:
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, parsed):
        self.chat = _Chat(parsed)


def _wrapper(parsed):
    wrapper = OpenAIClient.__new__(OpenAIClient)
    wrapper.client = _Client(parsed)
    wrapper.active_requests = {}
    return wrapper


def _reset_cache():
    cache = get_quota_cache()
    cache._by_provider.clear()
    return cache


async def test_nonstream_success_captures_quota_headers():
    cache = _reset_cache()
    result = await _wrapper(_Completion()).create_chat_completion(
        {"model": "fixture", "messages": []}
    )
    assert result["id"] == "ok"
    assert cache.samples()["openrouter"].remaining_fraction == 0.75


async def test_stream_success_captures_quota_headers():
    cache = _reset_cache()
    lines = [
        line
        async for line in _wrapper(_Stream()).create_chat_completion_stream(
            {"model": "fixture", "messages": []}
        )
    ]
    assert lines[-1] == "data: [DONE]"
    assert cache.samples()["openrouter"].remaining_fraction == 0.75
