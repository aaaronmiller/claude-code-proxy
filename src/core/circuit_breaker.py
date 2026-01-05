"""
Circuit Breaker Pattern for Provider Resilience

Inspired by Lynkr's implementation, this module provides:
- Per-provider circuit breakers to prevent cascading failures
- Automatic recovery after timeout period
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


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
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    success_threshold=success_threshold,
                    timeout=timeout
                )
                logger.debug(f"Created circuit breaker for '{name}'")
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
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout
            )
            logger.debug(f"Created circuit breaker for '{name}'")
        return self._breakers[name]
    
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
