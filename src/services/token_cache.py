"""
Accurate token counting with LRU cache.

Replaces the len(text)//4 heuristic in endpoints.py with real tiktoken
encoding. Results are cached by text hash so repeated system prompts and
tool schemas (sent every turn by Claude Code) skip re-encoding.

Usage:
    from src.services.token_cache import count_tokens, count_messages_tokens

Environment:
    TOKEN_COUNT_CACHE_SIZE  — LRU cache size (default: 512)
"""

import hashlib
import logging
import os
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

_CACHE_SIZE = int(os.getenv("TOKEN_COUNT_CACHE_SIZE", "512"))

# Lazy-loaded encoder — import cost paid once on first call
_encoder = None
_encoder_failed = False


def _get_encoder():
    global _encoder, _encoder_failed
    if _encoder is not None or _encoder_failed:
        return _encoder
    try:
        import tiktoken
        _encoder = tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        logger.debug(f"tiktoken unavailable, falling back to heuristic: {e}")
        _encoder_failed = True
    return _encoder


# Simple thread-safe-enough LRU (proxy is single-process asyncio, no true concurrency)
class _LRUCache:
    def __init__(self, maxsize: int):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str, default=None):
        if key not in self._cache:
            return default
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: int):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def __len__(self):
        return len(self._cache)


_cache = _LRUCache(_CACHE_SIZE)


def count_tokens(text: str) -> int:
    """
    Count tokens in a string, with LRU caching.

    Falls back to len(text)//4 if tiktoken is unavailable.
    Cache key is a sha256 prefix of the text (collision probability negligible
    for the prompt sizes we're working with).
    """
    if not text:
        return 0

    # Hash for cache key — sha256 first 16 hex chars is plenty for dedup
    key = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]
    cached = _cache.get(key)
    if cached is not None:
        return cached

    enc = _get_encoder()
    if enc is None:
        # Heuristic fallback
        result = max(1, len(text) // 4)
    else:
        try:
            result = len(enc.encode(text, disallowed_special=()))
        except Exception:
            result = max(1, len(text) // 4)

    _cache.set(key, result)
    return result


def count_messages_tokens(messages: list[dict[str, Any]]) -> int:
    """
    Estimate total token count for a list of OpenAI-format messages.

    Accounts for per-message overhead (~4 tokens each for role + framing).
    """
    total = 0
    for msg in messages:
        total += 4  # role + message framing overhead
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += count_tokens(block.get("text", "") or block.get("content", ""))
        # Tool calls in assistant messages
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            total += count_tokens(fn.get("name", ""))
            total += count_tokens(fn.get("arguments", ""))
    return total


def cache_stats() -> dict:
    """Return cache hit/miss stats for monitoring."""
    return {"size": len(_cache), "maxsize": _CACHE_SIZE}
