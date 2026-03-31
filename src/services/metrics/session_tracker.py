"""
Session Metrics Tracker

Tracks per-session metrics in real-time:
- Token counts (input, output, thinking, cached)
- Tokens/second
- Cost (correlated with model)
- Tool call success/failure rates
- Cache usage
- Request latency

Data is stored in-memory for real-time access and periodically flushed to database.
"""

import asyncio
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sqlite3
import threading

from src.core.logging import logger


@dataclass
class SessionMetrics:
    """Metrics for a single session."""
    session_id: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    
    # Performance
    requests: int = 0
    total_latency_ms: float = 0
    tokens_per_second: float = 0
    
    # Cost
    estimated_cost: float = 0
    model_pricing: Dict[str, tuple] = field(default_factory=dict)
    
    # Tool calls
    tool_calls_total: int = 0
    tool_calls_success: int = 0
    tool_calls_failure: int = 0
    tool_call_names: List[str] = field(default_factory=list)
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Models used
    models_used: Dict[str, int] = field(default_factory=dict)  # model -> count
    
    # Last activity
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Calculate derived metrics
        if self.total_latency_ms > 0:
            data['avg_latency_ms'] = round(self.total_latency_ms / max(self.requests, 1), 1)
        if self.output_tokens > 0 and self.total_latency_ms > 0:
            data['tokens_per_second'] = round(
                self.output_tokens / (self.total_latency_ms / 1000), 1
            )
        if self.tool_calls_total > 0:
            data['tool_success_rate'] = round(
                self.tool_calls_success / self.tool_calls_total * 100, 1
            )
        if self.cached_tokens + self.total_tokens > 0:
            data['cache_hit_rate'] = round(
                self.cached_tokens / (self.cached_tokens + self.total_tokens) * 100, 1
            )
        return data


class SessionMetricsTracker:
    """
    Real-time session metrics tracker.
    
    Usage:
        tracker = SessionMetricsTracker()
        tracker.record_request(session_id, {...})
        tracker.record_tool_call(session_id, "Bash", success=True)
        tracker.get_session_metrics(session_id)
    """
    
    # Model pricing (per 1M tokens) - updated dynamically
    MODEL_PRICING = {
        # OpenAI
        'gpt-4o': (5.0, 15.0),  # (input, output)
        'gpt-4o-mini': (0.15, 0.6),
        'o1': (15.0, 60.0),
        'o3': (10.0, 40.0),
        # Anthropic
        'claude-3-opus': (15.0, 75.0),
        'claude-3-sonnet': (3.0, 15.0),
        'claude-3-haiku': (0.25, 1.25),
        # Google
        'gemini-2.0-flash': (0.075, 0.3),
        'gemini-2.0-pro': (1.25, 5.0),
        # OpenRouter (varies)
        'default': (1.0, 3.0),
    }
    
    def __init__(self, db_path: str = "usage_tracking.db"):
        self.sessions: Dict[str, SessionMetrics] = {}
        self.db_path = db_path
        self._lock = threading.Lock()
        self._cleanup_interval = 3600  # 1 hour
        self._flush_interval = 60  # 30 seconds
        
        # Start background tasks
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._flush_task = asyncio.create_task(self._flush_loop())
        
        logger.info("Session metrics tracker initialized")
    
    async def _cleanup_loop(self):
        """Clean up stale sessions periodically."""
        while self._running:
            await asyncio.sleep(self._cleanup_interval)
            self._cleanup_stale_sessions()
    
    async def _flush_loop(self):
        """Flush metrics to database periodically."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            self._flush_to_database()
    
    def _cleanup_stale_sessions(self):
        """Remove sessions inactive for more than 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        stale = []
        
        with self._lock:
            for session_id, metrics in self.sessions.items():
                last_activity = datetime.fromisoformat(metrics.last_activity)
                if last_activity < cutoff:
                    stale.append(session_id)
            
            for session_id in stale:
                del self.sessions[session_id]
        
        if stale:
            logger.info(f"Cleaned up {len(stale)} stale sessions")
    
    def _flush_to_database(self):
        """Flush current metrics to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    started_at TEXT,
                    last_activity TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    thinking_tokens INTEGER,
                    cached_tokens INTEGER,
                    total_tokens INTEGER,
                    requests INTEGER,
                    total_latency_ms REAL,
                    estimated_cost REAL,
                    tool_calls_total INTEGER,
                    tool_calls_success INTEGER,
                    tool_calls_failure INTEGER,
                    cache_hits INTEGER,
                    cache_misses INTEGER,
                    models_used TEXT,
                    tool_call_names TEXT
                )
            """)
            
            with self._lock:
                for session_id, metrics in self.sessions.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO session_metrics 
                        (session_id, started_at, last_activity, input_tokens, output_tokens,
                         thinking_tokens, cached_tokens, total_tokens, requests,
                         total_latency_ms, estimated_cost, tool_calls_total,
                         tool_calls_success, tool_calls_failure, cache_hits,
                         cache_misses, models_used, tool_call_names)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        metrics.started_at,
                        metrics.last_activity,
                        metrics.input_tokens,
                        metrics.output_tokens,
                        metrics.thinking_tokens,
                        metrics.cached_tokens,
                        metrics.total_tokens,
                        metrics.requests,
                        metrics.total_latency_ms,
                        metrics.estimated_cost,
                        metrics.tool_calls_total,
                        metrics.tool_calls_success,
                        metrics.tool_calls_failure,
                        metrics.cache_hits,
                        metrics.cache_misses,
                        json.dumps(metrics.models_used),
                        json.dumps(metrics.tool_call_names)
                    ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to flush session metrics: {e}")
    
    def _get_model_pricing(self, model: str) -> tuple:
        """Get pricing for a model (input, output per 1M tokens)."""
        model_lower = model.lower()
        
        # Check exact matches first
        for key, pricing in self.MODEL_PRICING.items():
            if key in model_lower:
                return pricing
        
        # Default pricing
        return self.MODEL_PRICING['default']
    
    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> float:
        """Calculate estimated cost for a request."""
        input_price, output_price = self._get_model_pricing(model)
        
        # Cached tokens are discounted (typically 50-90% cheaper)
        cached_discount = 0.9  # 90% off for cached tokens
        effective_input = input_tokens - cached_tokens
        cached_cost = (cached_tokens / 1_000_000) * input_price * (1 - cached_discount)
        input_cost = (effective_input / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        
        return round(input_cost + output_cost + cached_cost, 6)
    
    def record_request(
        self,
        session_id: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        cached_tokens: int = 0,
        latency_ms: float = 0,
        **kwargs
    ):
        """Record a request for a session."""
        total_tokens = input_tokens + output_tokens + thinking_tokens
        cost = self._calculate_cost(model, input_tokens, output_tokens, cached_tokens)
        
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionMetrics(session_id=session_id)
            
            metrics = self.sessions[session_id]
            metrics.input_tokens += input_tokens
            metrics.output_tokens += output_tokens
            metrics.thinking_tokens += thinking_tokens
            metrics.cached_tokens += cached_tokens
            metrics.total_tokens += total_tokens
            metrics.requests += 1
            metrics.total_latency_ms += latency_ms
            metrics.estimated_cost += cost
            metrics.last_activity = datetime.utcnow().isoformat()
            
            # Track models used
            if model not in metrics.models_used:
                metrics.models_used[model] = 0
            metrics.models_used[model] += 1
        
        logger.debug(
            f"Session {session_id[:8]}: {model} - {total_tokens} tokens, {latency_ms:.0f}ms, ${cost:.6f}"
        )
    
    def record_tool_call(
        self,
        session_id: str,
        tool_name: str,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    ):
        """Record a tool call for a session."""
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionMetrics(session_id=session_id)
            
            metrics = self.sessions[session_id]
            metrics.tool_calls_total += 1
            
            if success:
                metrics.tool_calls_success += 1
            else:
                metrics.tool_calls_failure += 1
            
            if tool_name not in metrics.tool_call_names:
                metrics.tool_call_names.append(tool_name)
            
            metrics.last_activity = datetime.utcnow().isoformat()
        
        logger.debug(
            f"Session {session_id[:8]}: Tool {tool_name} - {'success' if success else 'failure'}"
        )
    
    def record_cache_usage(
        self,
        session_id: str,
        cache_hit: bool,
        cached_tokens: int = 0,
        total_tokens: int = 0,
        **kwargs
    ):
        """Record cache usage for a session."""
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionMetrics(session_id=session_id)
            
            metrics = self.sessions[session_id]
            
            if cache_hit:
                metrics.cache_hits += 1
                metrics.cached_tokens += cached_tokens
            else:
                metrics.cache_misses += 1
            
            metrics.last_activity = datetime.utcnow().isoformat()
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific session."""
        with self._lock:
            if session_id not in self.sessions:
                return None
            return self.sessions[session_id].to_dict()
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get metrics for all active sessions."""
        with self._lock:
            return [
                metrics.to_dict()
                for metrics in self.sessions.values()
            ]
    
    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Get aggregate metrics across all sessions."""
        with self._lock:
            total_sessions = len(self.sessions)
            total_requests = sum(m.requests for m in self.sessions.values())
            total_tokens = sum(m.total_tokens for m in self.sessions.values())
            total_cost = sum(m.estimated_cost for m in self.sessions.values())
            total_tool_calls = sum(m.tool_calls_total for m in self.sessions.values())
            total_tool_success = sum(m.tool_calls_success for m in self.sessions.values())
            total_cache_hits = sum(m.cache_hits for m in self.sessions.values())
            total_cached_tokens = sum(m.cached_tokens for m in self.sessions.values())
            
            # Calculate averages
            avg_tokens = total_tokens / max(total_requests, 1)
            avg_latency = sum(m.total_latency_ms for m in self.sessions.values()) / max(total_requests, 1)
            avg_tokens_per_sec = sum(m.output_tokens for m in self.sessions.values()) / max(sum(m.total_latency_ms for m in self.sessions.values()) / 1000, 1)
            
            return {
                'total_sessions': total_sessions,
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'total_cost': round(total_cost, 4),
                'total_tool_calls': total_tool_calls,
                'tool_success_rate': round(total_tool_success / max(total_tool_calls, 1) * 100, 1),
                'cache_hit_rate': round(total_cache_hits / max(total_cache_hits + sum(m.cache_misses for m in self.sessions.values()), 1) * 100, 1),
                'cached_tokens': total_cached_tokens,
                'avg_tokens_per_request': round(avg_tokens, 1),
                'avg_latency_ms': round(avg_latency, 1),
                'avg_tokens_per_second': round(avg_tokens_per_sec, 1),
                'active_sessions': [
                    {
                        'session_id': m.session_id[:8] + '...',
                        'requests': m.requests,
                        'tokens': m.total_tokens,
                        'cost': round(m.estimated_cost, 4),
                        'tool_success_rate': m.to_dict().get('tool_success_rate', 0)
                    }
                    for m in sorted(self.sessions.values(), key=lambda x: x.last_activity, reverse=True)[:10]
                ]
            }
    
    def stop(self):
        """Stop background tasks and flush final metrics."""
        self._running = False
        self._flush_to_database()
        logger.info("Session metrics tracker stopped")


# Global instance
_tracker: Optional[SessionMetricsTracker] = None


def get_tracker() -> SessionMetricsTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SessionMetricsTracker()
    return _tracker


def record_request(**kwargs):
    """Convenience function for recording requests."""
    get_tracker().record_request(**kwargs)


def record_tool_call(**kwargs):
    """Convenience function for recording tool calls."""
    get_tracker().record_tool_call(**kwargs)


def record_cache_usage(**kwargs):
    """Convenience function for recording cache usage."""
    get_tracker().record_cache_usage(**kwargs)


def get_session_metrics(session_id: str) -> Optional[Dict[str, Any]]:
    """Get metrics for a session."""
    return get_tracker().get_session_metrics(session_id)


def get_all_sessions() -> List[Dict[str, Any]]:
    """Get all session metrics."""
    return get_tracker().get_all_sessions()


def get_aggregate_metrics() -> Dict[str, Any]:
    """Get aggregate metrics."""
    return get_tracker().get_aggregate_metrics()
