"""
Structured logging system for Claude Code Proxy.

Provides tiered logging with automatic rotation, structured JSON output,
and sensitive data redaction.

Tiers:
- production: Errors only, 10MB files, 7-day retention (~5MB/day)
- debug: All requests, 50MB files, 3-day retention (~20MB/day)
- forensic: Full payloads, manual cleanup (~100MB/day)

Usage:
    from src.services.logging.structured_logger import get_logger
    logger = get_logger()
    logger.log_request(request_id, {...})
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        extra_fields = [
            'request_id', 'model', 'endpoint', 'duration_ms',
            'input_tokens', 'output_tokens', 'tool_calls', 'status',
            'error_type', 'session_id', 'provider'
        ]
        
        for field in extra_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                # Handle non-serializable objects
                if isinstance(value, (set, frozenset)):
                    value = list(value)
                elif hasattr(value, '__dict__'):
                    value = str(value)
                log_data[field] = value
        
        return json.dumps(log_data, default=str)


class DetailedFormatter(logging.Formatter):
    """Detailed human-readable formatter for forensic mode."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Build base message
        parts = [
            f"{timestamp} | {record.levelname:<8} | {record.name}",
        ]
        
        # Add request ID if present
        if hasattr(record, 'request_id'):
            parts.append(f"| req:{record.request_id[:8]}")
        
        # Add model if present
        if hasattr(record, 'model'):
            parts.append(f"| model:{record.model}")
        
        # Add message
        parts.append(f"| {record.getMessage()}")
        
        # Add extra data if present
        if hasattr(record, 'extra_data') and record.extra_data:
            extra = record.extra_data
            if len(extra) > 500:
                extra = extra[:500] + "..."
            parts.append(f"| {extra}")
        
        return " ".join(parts)


class StructuredLogger:
    """
    Production-ready logger with tiered verbosity and automatic rotation.
    
    Features:
    - Automatic file rotation (size + time based)
    - Structured JSON logging for easy parsing
    - Tiered verbosity (production/debug/forensic)
    - Request tracing with correlation IDs
    - Sensitive data redaction
    - Tool call flow tracking
    """
    
    # Sensitive keys to redact
    SENSITIVE_KEYS = {
        'api_key', 'apikey', 'api-key', 'authorization', 'password', 
        'secret', 'token', 'access_token', 'refresh_token', 'private_key',
        'client_secret', 'auth_token'
    }
    
    def __init__(self, tier: Optional[str] = None, logs_dir: Optional[str] = None):
        """
        Initialize structured logger.
        
        Args:
            tier: Logging tier (production, debug, forensic). 
                  Defaults to LOG_TIER env var or 'production'.
            logs_dir: Directory for log files. 
                     Defaults to LOGS_DIR env var or 'logs/'.
        """
        self.tier = tier or os.getenv("LOG_TIER", "production").lower()
        self.logs_dir = Path(logs_dir or os.getenv("LOGS_DIR", "logs"))
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.max_size_mb = int(os.getenv("LOG_MAX_SIZE_MB", "50"))
        self.retention_days = int(os.getenv("LOG_RETENTION_DAYS", "7"))
        
        # Set up main logger
        self.logger = logging.getLogger("claude_proxy")
        self.logger.setLevel(logging.DEBUG)  # Log everything, handlers filter
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Set up handlers based on tier
        if self.tier == "production":
            self._setup_production_handlers()
        elif self.tier == "debug":
            self._setup_debug_handlers()
        elif self.tier == "forensic":
            self._setup_forensic_handlers()
        else:
            self._setup_production_handlers()
        
        # Log initialization
        self.logger.info(f"Structured logger initialized (tier={self.tier})")
    
    def _setup_production_handlers(self):
        """
        Production tier: errors only to file, info to console.
        - File: 10MB rotation, 7-day retention
        - Console: compact format
        """
        # Error file with rotation
        error_handler = RotatingFileHandler(
            self.logs_dir / "proxy_errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JsonFormatter())
        
        # Console handler (compact format from existing logger)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _setup_debug_handlers(self):
        """
        Debug tier: all requests to file.
        - File: 50MB rotation, 3-day retention
        - Console: debug format
        """
        # Debug file with rotation
        debug_handler = RotatingFileHandler(
            self.logs_dir / "proxy_debug.log",
            maxBytes=self.max_size_mb * 1024 * 1024,
            backupCount=3,
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(JsonFormatter())
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(console_handler)
    
    def _setup_forensic_handlers(self):
        """
        Forensic tier: full payloads, manual cleanup.
        - File: timestamped, no rotation
        - Console: detailed format
        """
        # Session-specific file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        forensic_handler = logging.FileHandler(
            self.logs_dir / f"forensic_{timestamp}.log",
            mode='w',
            encoding='utf-8'
        )
        forensic_handler.setLevel(logging.DEBUG)
        forensic_handler.setFormatter(DetailedFormatter())
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(DetailedFormatter())
        
        self.logger.addHandler(forensic_handler)
        self.logger.addHandler(console_handler)
        self.logger.warning("Forensic logging enabled - manual cleanup required")
    
    def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive data from dictionary.
        
        Args:
            data: Dictionary potentially containing sensitive data
            
        Returns:
            Dictionary with sensitive values redacted
        """
        if self.tier == "forensic":
            return data  # Keep everything in forensic mode
        
        def redact_value(key: str, value: Any) -> Any:
            key_lower = key.lower()
            if any(sens in key_lower for sens in self.SENSITIVE_KEYS):
                return "***REDACTED***"
            elif isinstance(value, dict):
                return {k: redact_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [redact_value(f"item_{i}", v) for i, v in enumerate(value)]
            return value
        
        return redact_value("root", data)
    
    def log_request(
        self,
        request_id: str,
        model: str,
        endpoint: str,
        message_count: int = 0,
        has_tools: bool = False,
        has_images: bool = False,
        has_reasoning: bool = False,
        input_tokens: int = 0,
        context_limit: int = 0,
        client_ip: str = "unknown",
        **kwargs
    ):
        """
        Log incoming request.
        
        Args:
            request_id: Unique request identifier
            model: Requested model
            endpoint: Target endpoint
            message_count: Number of messages in conversation
            has_tools: Whether request includes tool definitions
            has_images: Whether request includes images
            has_reasoning: Whether request uses reasoning/thinking
            input_tokens: Input token count
            context_limit: Model context limit
            client_ip: Client IP address
        """
        # Calculate context usage percentage
        ctx_pct = None
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = round(input_tokens / context_limit * 100, 1)
        
        self.logger.info(
            f"Request: {model} ({message_count} msgs, tools={has_tools})",
            extra={
                'request_id': request_id,
                'model': model,
                'endpoint': endpoint,
                'input_tokens': input_tokens,
                'tool_calls': 'yes' if has_tools else 'no',
                'status': 'start',
                'session_id': client_ip,
                'extra_data': json.dumps({
                    'message_count': message_count,
                    'has_tools': has_tools,
                    'has_images': has_images,
                    'has_reasoning': has_reasoning,
                    'context_pct': ctx_pct
                })
            }
        )
    
    def log_response(
        self,
        request_id: str,
        model: str,
        output_tokens: int = 0,
        input_tokens: int = 0,
        thinking_tokens: int = 0,
        duration_ms: float = 0,
        cost: float = 0,
        tool_calls: Optional[list] = None,
        status: str = "success",
        error: Optional[str] = None,
        **kwargs
    ):
        """
        Log response.
        
        Args:
            request_id: Unique request identifier
            model: Model that generated response
            output_tokens: Output token count
            input_tokens: Input token count
            thinking_tokens: Reasoning/thinking token count
            duration_ms: Request duration in milliseconds
            cost: Request cost in USD
            tool_calls: List of tool calls made
            status: Response status (success/error/cancelled)
            error: Error message if failed
        """
        # Calculate tokens per second
        tps = None
        if duration_ms > 0 and output_tokens > 0:
            tps = round(output_tokens / (duration_ms / 1000), 1)
        
        log_kwargs = {
            'request_id': request_id,
            'model': model,
            'duration_ms': round(duration_ms, 1),
            'output_tokens': output_tokens,
            'input_tokens': input_tokens,
            'status': status,
        }
        
        if thinking_tokens > 0:
            log_kwargs['thinking_tokens'] = thinking_tokens
        
        if tool_calls:
            log_kwargs['tool_calls'] = len(tool_calls)
        
        if error:
            log_kwargs['error_type'] = error.split(':')[0] if ':' in error else error
        
        # Build extra data
        extra_data = {
            'tps': tps,
            'cost': f"${cost:.4f}" if cost > 0 else None,
        }
        if tool_calls:
            extra_data['tool_names'] = [tc.get('name', 'unknown') for tc in tool_calls[:5]]
        
        log_kwargs['extra_data'] = json.dumps({k: v for k, v in extra_data.items() if v is not None})
        
        if status == "error" and error:
            self.logger.error(f"Error: {error[:100]}", extra=log_kwargs)
        else:
            self.logger.info(
                f"Response: {output_tokens} tokens in {duration_ms:.0f}ms",
                extra=log_kwargs
            )
    
    def log_tool_call_flow(
        self,
        request_id: str,
        tool_name: str,
        phase: str,
        tool_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    ):
        """
        Track tool call lifecycle for debugging and analytics.
        
        Phases:
        - call_start: Tool call detected in model response
        - call_transform: Arguments being transformed
        - call_sent: Tool call sent to client
        - result_received: Tool result received from client
        - result_transform: Result being transformed for model
        - result_sent: Transformed result sent to model
        - success: Tool call completed successfully
        - failure: Tool call failed
        
        Args:
            request_id: Request identifier
            tool_name: Name of tool (Bash, Read, Write, etc.)
            phase: Current phase
            tool_id: Tool call ID
            data: Phase-specific data
            session_id: Session identifier for per-session metrics
            success: Whether the tool call succeeded
            error: Error message if failed
        """
        extra_data = {
            'phase': phase,
            'tool_id': tool_id[:12] + '...' if tool_id and len(tool_id) > 12 else tool_id,
            'success': success,
            'session_id': session_id,
            **(data or {})
        }
        
        if error:
            extra_data['error'] = error[:200]
        
        extra = {
            'request_id': request_id,
            'tool_calls': tool_name,
            'session_id': session_id,
            'extra_data': json.dumps(extra_data)[:500]
        }
        
        # Log success/failure for analytics
        if phase in ('success', 'failure'):
            self.logger.info(
                f"Tool {phase}: {tool_name} (success={success})",
                extra=extra
            )
            # Also log to a separate tool analytics file
            self._log_tool_analytics({
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': request_id,
                'session_id': session_id,
                'tool_name': tool_name,
                'tool_id': tool_id,
                'phase': phase,
                'success': success,
                'error': error
            })
        else:
            self.logger.info(f"Tool {phase}: {tool_name}", extra=extra)
    
    def _log_tool_analytics(self, data: Dict[str, Any]):
        """Log tool call analytics to separate file for analysis."""
        try:
            analytics_file = self.logs_dir / "tool_analytics.jsonl"
            with open(analytics_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception:
            pass  # Don't fail if analytics logging fails
    
    def log_cache_usage(
        self,
        request_id: str,
        session_id: Optional[str] = None,
        cache_hit: bool = False,
        cache_miss: bool = False,
        cached_tokens: int = 0,
        total_tokens: int = 0,
        cache_type: str = "prompt",
        **kwargs
    ):
        """
        Log cache usage for analytics.
        
        Args:
            request_id: Request identifier
            session_id: Session identifier
            cache_hit: Whether cache was hit
            cache_miss: Whether cache was missed
            cached_tokens: Number of tokens from cache
            total_tokens: Total tokens in request
            cache_type: Type of cache (prompt, response, tool)
        """
        cache_ratio = round(cached_tokens / total_tokens * 100, 1) if total_tokens > 0 else 0
        
        extra = {
            'request_id': request_id,
            'session_id': session_id,
            'extra_data': json.dumps({
                'cache_hit': cache_hit,
                'cache_miss': cache_miss,
                'cached_tokens': cached_tokens,
                'total_tokens': total_tokens,
                'cache_ratio': cache_ratio,
                'cache_type': cache_type
            })
        }
        
        self.logger.info(
            f"Cache {'hit' if cache_hit else 'miss'}: {cached_tokens}/{total_tokens} ({cache_ratio}%)",
            extra=extra
        )
        
        # Log to cache analytics file
        try:
            analytics_file = self.logs_dir / "cache_analytics.jsonl"
            with open(analytics_file, 'a') as f:
                f.write(json.dumps({
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_id': request_id,
                    'session_id': session_id,
                    'cache_hit': cache_hit,
                    'cached_tokens': cached_tokens,
                    'total_tokens': total_tokens,
                    'cache_type': cache_type
                }) + '\n')
        except Exception:
            pass
    
    def log_error(
        self,
        error: Exception,
        context: str = "unknown",
        request_id: Optional[str] = None,
        **kwargs
    ):
        """
        Log error with context.
        
        Args:
            error: Exception object
            context: Where error occurred
            request_id: Request identifier if applicable
        """
        extra = {
            'error_type': type(error).__name__,
            'extra_data': json.dumps({
                'context': context,
                'error_message': str(error),
                **(kwargs or {})
            })
        }
        
        if request_id:
            extra['request_id'] = request_id
        
        self.logger.error(f"{context}: {type(error).__name__}: {error}", extra=extra)
    
    def log_provider_fallback(
        self,
        request_id: str,
        from_provider: str,
        to_provider: str,
        reason: str,
        **kwargs
    ):
        """
        Log provider fallback event.
        
        Args:
            request_id: Request identifier
            from_provider: Original provider
            to_provider: Fallback provider
            reason: Reason for fallback
        """
        self.logger.warning(
            f"Provider fallback: {from_provider} → {to_provider} ({reason})",
            extra={
                'request_id': request_id,
                'provider': to_provider,
                'extra_data': json.dumps({
                    'from': from_provider,
                    'to': to_provider,
                    'reason': reason
                })
            }
        )
    
    def log_startup_info(self, config_summary: Dict[str, Any]):
        """
        Log startup configuration summary.
        
        Args:
            config_summary: Configuration summary dictionary
        """
        redacted = self._redact_sensitive(config_summary)
        self.logger.info(
            "Proxy startup",
            extra={
                'extra_data': json.dumps(redacted, default=str, indent=2)
            }
        )


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger(tier: Optional[str] = None) -> StructuredLogger:
    """
    Get or create global logger instance.
    
    Args:
        tier: Optional tier override
        
    Returns:
        StructuredLogger instance
    """
    global _logger
    if _logger is None or tier:
        _logger = StructuredLogger(tier=tier)
    return _logger


def log_request(**kwargs):
    """Convenience function for logging requests."""
    get_logger().log_request(**kwargs)


def log_response(**kwargs):
    """Convenience function for logging responses."""
    get_logger().log_response(**kwargs)


def log_tool_call_flow(**kwargs):
    """Convenience function for logging tool call flow."""
    get_logger().log_tool_call_flow(**kwargs)


def log_error(error: Exception, **kwargs):
    """Convenience function for logging errors."""
    get_logger().log_error(error, **kwargs)
