"""
Circuit Breaker Pattern for Provider Resilience

Inspired by Lynkr's implementation, this module provides:
- Per-provider circuit breakers to prevent cascading failures
- Automatic recovery after timeout period
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
"""

import asyncio
import json
import os
import time
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Persistence helpers
# ─────────────────────────────────────────────────────────────────────────────
# Circuit breaker state is persisted to a lightweight JSON sidecar next to the
# usage database so state survives proxy restarts.  The file is small (~1 KB
# for 20 models), written only when state changes, and read once at startup.

_CB_STATE_FILE = Path(os.environ.get("CB_STATE_FILE", "data/circuit_breaker_state.json"))


def _load_persisted_state() -> Dict[str, dict]:
    """Load previously saved circuit breaker states from disk."""
    try:
        if _CB_STATE_FILE.exists():
            return json.loads(_CB_STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"[CB] Could not load persisted state: {e}")
    return {}


def _save_persisted_state(states: Dict[str, dict]) -> None:
    """Persist current circuit breaker states to disk."""
    try:
        _CB_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CB_STATE_FILE.write_text(json.dumps(states, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[CB] Could not save state: {e}")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests flow through
    OPEN = "open"          # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""
    failure_threshold: int = 5     # Failures before opening circuit
    success_threshold: int = 2     # Successes in half-open before closing
    timeout: float = 60.0          # Seconds before trying half-open
    

@dataclass
class CircuitBreakerStats:
    """Runtime statistics for a circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    total_failures: int = 0
    total_successes: int = 0
    total_rejections: int = 0
    # Soft failures: HTTP 200 but structurally broken response (empty content,
    # missing tool_calls, finish_reason: length).  Two soft failures = one hard
    # failure toward the threshold.
    soft_failure_count: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for a single provider.
    
    Usage:
        breaker = CircuitBreaker("openrouter")
        try:
            result = await breaker.execute(async_fn, arg1, arg2)
        except CircuitOpenError:
            # Handle circuit open (fail fast)
            pass
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0
    ):
        self.name = name
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout
        )
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        return self.stats.state
    
    @property
    def is_closed(self) -> bool:
        return self.stats.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        return self.stats.state == CircuitState.OPEN
    
    def _should_attempt(self) -> bool:
        """Check if request should be attempted based on circuit state."""
        if self.stats.state == CircuitState.CLOSED:
            return True
            
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.stats.last_failure_time:
                elapsed = time.time() - self.stats.last_failure_time
                if elapsed >= self.config.timeout:
                    # Transition to half-open
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN after {elapsed:.1f}s")
                    return True
            return False
            
        # HALF_OPEN - allow request through for testing
        return True
    
    def _record_success(self):
        """Record a successful request."""
        self.stats.total_successes += 1
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
            if self.stats.success_count >= self.config.success_threshold:
                # Transition back to closed
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' CLOSED after {self.stats.success_count} successes")
        else:
            # Reset failure count on success in closed state
            self.stats.failure_count = 0
    
    def _record_failure(self, error: Exception):
        """Record a failed request."""
        self.stats.total_failures += 1
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            # Any failure in half-open sends back to open
            self.stats.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' OPEN (failed in half-open): {error}")
            
        elif self.stats.state == CircuitState.CLOSED:
            if self.stats.failure_count >= self.config.failure_threshold:
                self.stats.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' OPEN after {self.stats.failure_count} failures: {error}"
                )
    
    async def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            fn: Async function to execute
            *args, **kwargs: Arguments to pass to fn
            
        Returns:
            Result of fn
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from fn (after recording failure)
        """
        async with self._lock:
            if not self._should_attempt():
                self.stats.total_rejections += 1
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - failing fast"
                )
        
        try:
            result = await fn(*args, **kwargs)
            async with self._lock:
                self._record_success()
            return result
        except Exception as e:
            async with self._lock:
                self._record_failure(e)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "total_rejections": self.stats.total_rejections,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def record_soft_failure(self) -> None:
        """
        Record a structural response failure (HTTP 200 but unusable output).

        Two soft failures accumulate to one hard-failure equivalent toward the
        circuit-open threshold, so a consistently-broken-but-not-404 model
        still gets penalized without tripping the breaker as aggressively.
        """
        self.stats.soft_failure_count += 1
        # Every 2 soft failures counts as 1 hard failure
        if self.stats.soft_failure_count % 2 == 0:
            class _SoftError(Exception):
                pass
            self._record_failure(_SoftError("soft failure accumulation"))
            logger.debug(
                f"[CB] {self.name}: soft failure #{self.stats.soft_failure_count} "
                f"→ equivalent hard failure triggered"
            )

    def record_parse_ok(self, response: dict) -> bool:
        """
        Check structural validity of a non-streaming response and record the
        result in the circuit breaker.

        A response is 'ok' when:
          - choices list is non-empty
          - finish_reason is not 'length' (truncated output is unreliable)
          - at least one of: tool_calls populated OR non-empty message content

        Returns True if the response is structurally valid.
        """
        choices = response.get("choices", [])
        if not choices:
            self.record_soft_failure()
            logger.debug(f"[CB] {self.name}: parse_ok=False (empty choices)")
            return False

        c = choices[0]
        finish_reason = c.get("finish_reason", "")
        msg = c.get("message", {}) or {}
        has_tool_calls = bool(msg.get("tool_calls"))
        has_content = bool((msg.get("content") or "").strip())

        # finish_reason: length means truncation — unreliable for tool use
        if finish_reason == "length" and not has_tool_calls:
            self.record_soft_failure()
            logger.debug(f"[CB] {self.name}: parse_ok=False (finish_reason=length, no tool_calls)")
            return False

        if not has_tool_calls and not has_content:
            self.record_soft_failure()
            logger.debug(f"[CB] {self.name}: parse_ok=False (empty content and no tool_calls)")
            return False

        return True

    def record_stream_finish(self, finish_reason: Optional[str], had_tool_calls: bool, had_content: bool) -> bool:
        """
        Record parse result for a completed streaming response.

        Call this at stream end (after the last SSE chunk).
        Returns True if the stream output is structurally valid.
        """
        if finish_reason == "length" and not had_tool_calls:
            self.record_soft_failure()
            logger.debug(f"[CB] {self.name}: stream parse_ok=False (finish_reason=length)")
            return False
        if not had_tool_calls and not had_content:
            self.record_soft_failure()
            logger.debug(f"[CB] {self.name}: stream parse_ok=False (empty stream)")
            return False
        return True

    def to_persist_dict(self) -> dict:
        """Serialise current state for disk persistence."""
        return {
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "last_failure_time": self.stats.last_failure_time,
            "soft_failure_count": self.stats.soft_failure_count,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
        }

    @classmethod
    def from_persist_dict(cls, name: str, d: dict, **kwargs) -> "CircuitBreaker":
        """Restore a circuit breaker from a persisted dict."""
        cb = cls(name=name, **kwargs)
        state_str = d.get("state", CircuitState.CLOSED.value)
        try:
            cb.stats.state = CircuitState(state_str)
        except ValueError:
            cb.stats.state = CircuitState.CLOSED
        cb.stats.failure_count = d.get("failure_count", 0)
        cb.stats.last_failure_time = d.get("last_failure_time")
        cb.stats.soft_failure_count = d.get("soft_failure_count", 0)
        cb.stats.total_failures = d.get("total_failures", 0)
        cb.stats.total_successes = d.get("total_successes", 0)
        # An OPEN state from a previous session must re-evaluate its timeout
        # immediately; if the cooldown has already elapsed, drop to HALF_OPEN.
        if cb.stats.state == CircuitState.OPEN and cb.stats.last_failure_time:
            elapsed = time.time() - cb.stats.last_failure_time
            if elapsed >= cb.config.timeout:
                cb.stats.state = CircuitState.HALF_OPEN
                logger.info(
                    f"[CB] Restored '{name}' to HALF_OPEN (timeout elapsed during restart)"
                )
            else:
                logger.info(
                    f"[CB] Restored '{name}' as OPEN ({elapsed:.0f}s into "
                    f"{cb.config.timeout:.0f}s cooldown)"
                )
        return cb

    def reset(self):
        """Manually reset the circuit breaker to closed state."""
        self.stats = CircuitBreakerStats()
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests."""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Usage:
        registry = CircuitBreakerRegistry()
        breaker = registry.get("openrouter")
        await breaker.execute(fn)
    """
    
    _instance: Optional["CircuitBreakerRegistry"] = None
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
        self._persisted = _load_persisted_state()  # loaded once at startup
    
    @classmethod
    def get_instance(cls) -> "CircuitBreakerRegistry":
        """Get or create the singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0
    ) -> CircuitBreaker:
        """Get or create a circuit breaker by name."""
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = self._make_breaker(
                    name, failure_threshold, success_threshold, timeout
                )
            return self._breakers[name]

    def get_sync(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0
    ) -> CircuitBreaker:
        """Synchronous version for non-async contexts."""
        if name not in self._breakers:
            self._breakers[name] = self._make_breaker(
                name, failure_threshold, success_threshold, timeout
            )
        return self._breakers[name]

    def _make_breaker(self, name: str, failure_threshold: int, success_threshold: int, timeout: float) -> CircuitBreaker:
        """Create a new breaker, restoring persisted state if available."""
        kwargs = dict(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
        )
        if name in self._persisted:
            cb = CircuitBreaker.from_persist_dict(name, self._persisted[name], **kwargs)
            logger.debug(f"[CB] Restored '{name}' from disk (state={cb.stats.state.value})")
        else:
            cb = CircuitBreaker(name=name, **kwargs)
            logger.debug(f"[CB] Created new breaker for '{name}'")
        return cb

    def save_all(self) -> None:
        """Persist all circuit breaker states to disk."""
        states = {name: cb.to_persist_dict() for name, cb in self._breakers.items()}
        _save_persisted_state(states)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


# Convenience function for global registry access
def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return CircuitBreakerRegistry.get_instance()
