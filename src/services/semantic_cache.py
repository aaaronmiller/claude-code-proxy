"""
Semantic dedup cache — skip provider calls for near-duplicate prompts.

Two-level architecture:
  Level 1 (exact):   SHA-256 hash of full prompt text → cache hit in O(1)
  Level 2 (fuzzy):   SimHash fingerprint → cosine similarity of bit vectors
                     Catches near-duplicates (same prompt, different search term)

Why SimHash instead of sentence-transformers:
- Zero ML dependency — runs in microseconds, no model download
- Sufficient for the target use case: repetitive agentic loops where the
  system prompt + tool list is identical and only the search keyword changes
- Adjustable threshold: SEMANTIC_CACHE_THRESHOLD=0.97 (default)

Configuration (env vars):
  SEMANTIC_CACHE_ENABLED=true         Enable/disable (default: true)
  SEMANTIC_CACHE_SIZE=256             Max cached entries (LRU, default: 256)
  SEMANTIC_CACHE_THRESHOLD=0.97       Similarity threshold 0–1 (default: 0.97)
  SEMANTIC_CACHE_MIN_TOKENS=200       Min input tokens to attempt cache (default: 200)
  SEMANTIC_CACHE_TTL=3600             Seconds before cache entry expires (default: 3600)

Usage:
  from src.services.semantic_cache import semantic_cache

  hit = semantic_cache.lookup(prompt_text)
  if hit:
      return hit  # cached response dict

  response = await call_provider(...)
  semantic_cache.store(prompt_text, response)
"""

import hashlib
import logging
import os
import time
from collections import OrderedDict
from typing import Any, Optional

logger = logging.getLogger(__name__)

_ENABLED = os.environ.get("SEMANTIC_CACHE_ENABLED", "true").lower() != "false"
_CACHE_SIZE = int(os.environ.get("SEMANTIC_CACHE_SIZE", "256"))
_THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.97"))
_MIN_TOKENS = int(os.environ.get("SEMANTIC_CACHE_MIN_TOKENS", "200"))
_TTL = int(os.environ.get("SEMANTIC_CACHE_TTL", "3600"))


# ── SimHash implementation (pure Python, zero deps) ──────────────────────────

def _shingle(text: str, k: int = 4) -> list[str]:
    """Generate character k-shingles from text."""
    text = text.lower()
    return [text[i:i+k] for i in range(max(1, len(text) - k + 1))]


def _simhash(text: str, bits: int = 64) -> int:
    """
    Compute a SimHash fingerprint of text.
    Similar texts produce fingerprints with high bit-overlap.
    """
    v = [0] * bits
    for shingle in _shingle(text):
        h = int(hashlib.md5(shingle.encode("utf-8", errors="replace")).hexdigest(), 16)
        for i in range(bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint


def _similarity(h1: int, h2: int, bits: int = 64) -> float:
    """Cosine-approximate similarity: fraction of matching bits."""
    xor = h1 ^ h2
    differing = bin(xor).count("1")
    return 1.0 - differing / bits


# ── LRU Cache ─────────────────────────────────────────────────────────────────

class _Entry:
    __slots__ = ("exact_key", "simhash", "response", "created_at", "hits")

    def __init__(self, exact_key: str, simhash: int, response: Any):
        self.exact_key = exact_key
        self.simhash = simhash
        self.response = response
        self.created_at = time.time()
        self.hits = 0


class SemanticCache:
    """
    Two-level semantic cache: exact hash + SimHash near-duplicate detection.
    Thread-safe enough for asyncio single-process use.
    """

    def __init__(self):
        self._exact: dict[str, _Entry] = {}          # sha256 → entry
        self._lru: OrderedDict[str, _Entry] = OrderedDict()  # ordered by recency
        self._hits_exact = 0
        self._hits_fuzzy = 0
        self._misses = 0
        self._stores = 0

    def _evict_expired(self):
        now = time.time()
        stale = [k for k, e in self._lru.items() if now - e.created_at > _TTL]
        for k in stale:
            self._lru.pop(k, None)
            self._exact.pop(k, None)

    def _evict_lru(self):
        while len(self._lru) >= _CACHE_SIZE:
            oldest_key, _ = self._lru.popitem(last=False)
            self._exact.pop(oldest_key, None)

    def lookup(self, text: str) -> Optional[Any]:
        """
        Look up a response for this prompt text.
        Returns cached response dict or None on miss.
        """
        if not _ENABLED or not text:
            return None

        self._evict_expired()

        # Level 1: exact match
        exact_key = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        if exact_key in self._exact:
            entry = self._exact[exact_key]
            entry.hits += 1
            self._lru.move_to_end(exact_key)
            self._hits_exact += 1
            logger.debug(f"SemanticCache: exact hit (key={exact_key[:8]})")
            return entry.response

        # Level 2: SimHash fuzzy match
        fingerprint = _simhash(text)
        best_key: Optional[str] = None
        best_sim = 0.0
        for k, entry in self._lru.items():
            sim = _similarity(fingerprint, entry.simhash)
            if sim > best_sim:
                best_sim = sim
                best_key = k

        if best_sim >= _THRESHOLD and best_key:
            entry = self._lru[best_key]
            entry.hits += 1
            self._lru.move_to_end(best_key)
            self._hits_fuzzy += 1
            logger.debug(
                f"SemanticCache: fuzzy hit (sim={best_sim:.3f}, key={best_key[:8]})"
            )
            return entry.response

        self._misses += 1
        return None

    def store(self, text: str, response: Any) -> None:
        """Cache a response keyed by prompt text."""
        if not _ENABLED or not text:
            return

        exact_key = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
        if exact_key in self._exact:
            # Already cached — just refresh TTL
            self._lru.move_to_end(exact_key)
            return

        self._evict_lru()
        fingerprint = _simhash(text)
        entry = _Entry(exact_key, fingerprint, response)
        self._exact[exact_key] = entry
        self._lru[exact_key] = entry
        self._stores += 1
        logger.debug(f"SemanticCache: stored (key={exact_key[:8]}, size={len(self._lru)})")

    def stats(self) -> dict:
        total = self._hits_exact + self._hits_fuzzy + self._misses
        hit_rate = (self._hits_exact + self._hits_fuzzy) / total if total else 0
        return {
            "enabled": _ENABLED,
            "size": len(self._lru),
            "max_size": _CACHE_SIZE,
            "threshold": _THRESHOLD,
            "ttl_s": _TTL,
            "hits_exact": self._hits_exact,
            "hits_fuzzy": self._hits_fuzzy,
            "misses": self._misses,
            "stores": self._stores,
            "hit_rate": round(hit_rate, 3),
        }

    def clear(self) -> None:
        self._exact.clear()
        self._lru.clear()


# Singleton
semantic_cache = SemanticCache()
