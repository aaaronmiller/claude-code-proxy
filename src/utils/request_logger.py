"""
Compact request logging utility for terminal output.

Provides information-dense, color-coded logging for reasoning requests,
model routing, and token usage in 3-5 lines maximum.
"""

import logging
import os
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

# Try to import Rich for colored output
try:
    from rich.console import Console
    from rich.text import Text
    from rich.style import Style
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Try to import tiktoken for accurate token counting
try:
    import tiktoken  # type: ignore
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration from environment
LOG_STYLE = os.environ.get("LOG_STYLE", "rich").lower()  # rich, plain, compact
SHOW_TOKEN_COUNTS = os.environ.get("SHOW_TOKEN_COUNTS", "true").lower() == "true"
SHOW_PERFORMANCE = os.environ.get("SHOW_PERFORMANCE", "true").lower() == "true"
COLOR_SCHEME = os.environ.get("COLOR_SCHEME", "auto").lower()  # auto, dark, light, none

# Disable Rich if requested or unavailable
USE_RICH = RICH_AVAILABLE and LOG_STYLE == "rich" and COLOR_SCHEME != "none"


class RequestLogger:
    """Compact request logger for terminal output with color support."""
    
    # Subtle color palette for session differentiation (cyan/magenta shades only)
    SESSION_COLORS = [
        "bright_cyan",      # Session 1: Bright cyan
        "cyan",             # Session 2: Cyan
        "bright_magenta",   # Session 3: Bright magenta
        "magenta",          # Session 4: Magenta
        "bright_blue",      # Session 5: Bright blue
        "blue",             # Session 6: Blue
    ]
    
    @staticmethod
    def _get_session_color(request_id: str) -> str:
        """Get a consistent color for a session based on request ID prefix."""
        # Use first 8 chars of request ID to determine session
        session_hash = int(hashlib.md5(request_id[:8].encode()).hexdigest()[:8], 16)
        color_idx = session_hash % len(RequestLogger.SESSION_COLORS)
        return RequestLogger.SESSION_COLORS[color_idx]
    
    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count from text (rough approximation)."""
        # Rough estimate: ~4 characters per token
        return max(1, len(text) // 4)
    
    @staticmethod
    def _count_tokens_precise(text: str, model: str = "gpt-4") -> int:
        """Count tokens precisely using tiktoken if available."""
        if not TIKTOKEN_AVAILABLE:
            return RequestLogger._estimate_tokens(text)
        
        try:
            # Try to get encoding for specific model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")
        
        return len(encoding.encode(text))
    
    @staticmethod
    def log_request_start(
        request_id: str,
        original_model: str,
        routed_model: str,
        endpoint: str,
        reasoning_config: Optional[Any] = None,
        stream: bool = False,
        input_text: Optional[str] = None,
        context_limit: int = 0,
        output_limit: int = 0,
        input_tokens: int = 0,
        message_count: int = 0,
        has_system: bool = False,
        client_info: Optional[str] = None
    ) -> None:
        """
        Log request start with ALL comprehensive info on ONE line.
        
        Format (1 line with colors):
        🔵 abc123 | anthropic/claude-3.5-sonnet→openai/gpt-4o-mini | openrouter.ai | CTX:1.2k/200k (1%) | OUT:16k | THINK:8k | STREAM | 3msg | SYS | 127.0.0.1
        """
        # Extract provider and model info
        def get_provider_info(model_name: str) -> tuple[str, str, str]:
            """Extract provider, model family, and size from model name."""
            if "claude" in model_name.lower():
                provider = "anthropic"
                if "3.5" in model_name:
                    family = "claude-3.5"
                    size = "sonnet" if "sonnet" in model_name else "haiku" if "haiku" in model_name else "opus" if "opus" in model_name else "unknown"
                elif "3" in model_name:
                    family = "claude-3"
                    size = "sonnet" if "sonnet" in model_name else "haiku" if "haiku" in model_name else "opus" if "opus" in model_name else "unknown"
                else:
                    family = "claude"
                    size = "unknown"
            elif "gpt" in model_name.lower() or "o1" in model_name.lower():
                provider = "openai"
                if "gpt-4o" in model_name:
                    family = "gpt-4o"
                    size = "mini" if "mini" in model_name else "standard"
                elif "gpt-4" in model_name:
                    family = "gpt-4"
                    size = "turbo" if "turbo" in model_name else "standard"
                elif "o1" in model_name:
                    family = "o1"
                    size = "mini" if "mini" in model_name else "preview" if "preview" in model_name else "standard"
                else:
                    family = "gpt"
                    size = "unknown"
            elif "gemini" in model_name.lower():
                provider = "google"
                family = "gemini"
                size = "pro" if "pro" in model_name else "flash" if "flash" in model_name else "unknown"
            else:
                provider = "unknown"
                family = model_name.split("/")[-1] if "/" in model_name else model_name
                size = "unknown"
            
            return provider, family, size
        
        # Extract endpoint name and provider
        endpoint_name = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        endpoint_provider = "openrouter" if "openrouter" in endpoint_name else "openai" if "openai" in endpoint_name else "anthropic" if "anthropic" in endpoint_name else endpoint_name
        
        # Get model info
        orig_provider, orig_family, orig_size = get_provider_info(original_model)
        routed_provider, routed_family, routed_size = get_provider_info(routed_model)
        
        # Format token counts
        def fmt_tokens(count):
            return f"{count/1000:.1f}k" if count >= 1000 else str(count)
        
        # Build comprehensive single-line output
        if USE_RICH and console:
            # Get session-specific color
            session_color = RequestLogger._get_session_color(request_id)
            
            text = Text()
            text.append("🔵 ", style=f"bold {session_color}")
            text.append(f"{request_id[:6]} ", style=session_color)
            
            # Model routing with provider/family/size info
            text.append(f"{orig_provider}/", style="dim")
            text.append(f"{orig_family}", style="yellow")
            if orig_size != "unknown":
                text.append(f"-{orig_size}", style="bright_yellow")
            text.append("→", style="dim")
            text.append(f"{routed_provider}/", style="dim")
            text.append(f"{routed_family}", style="green")
            if routed_size != "unknown":
                text.append(f"-{routed_size}", style="bright_green")
            
            # Endpoint provider
            text.append(f" @{endpoint_provider} ", style="dim")
            
            # Context window usage
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = (input_tokens / context_limit) * 100
                ctx_color = "green" if ctx_pct < 50 else "yellow" if ctx_pct < 80 else "red"
                text.append("| CTX:", style="dim")
                text.append(f"{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ", style=ctx_color)
                text.append(f"({ctx_pct:.0f}%) ", style=ctx_color)
            elif input_tokens > 0:
                text.append("| CTX:", style="dim")
                text.append(f"{fmt_tokens(input_tokens)} ", style="cyan")
            
            # Output limit
            if output_limit > 0:
                text.append("| OUT:", style="dim")
                text.append(f"{fmt_tokens(output_limit)} ", style="blue")
            
            # Thinking/reasoning budget
            if reasoning_config:
                from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
                text.append("| THINK:", style="dim")
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    if reasoning_config.max_tokens:
                        text.append(f"{fmt_tokens(reasoning_config.max_tokens)} ", style="bold magenta")
                    elif reasoning_config.effort:
                        text.append(f"{reasoning_config.effort} ", style="bold magenta")
                elif isinstance(reasoning_config, AnthropicThinkingConfig):
                    text.append(f"{fmt_tokens(reasoning_config.budget)} ", style="bold magenta")
                elif isinstance(reasoning_config, GeminiThinkingConfig):
                    text.append(f"{fmt_tokens(reasoning_config.budget)} ", style="bold magenta")
            
            # Request metadata
            if stream:
                text.append("| STREAM ", style="bright_blue")
            
            if message_count > 0:
                text.append(f"| {message_count}msg ", style="dim")
            
            if has_system:
                text.append("| SYS ", style="green")
            
            if client_info:
                text.append(f"| {client_info}", style="dim")
            
            console.print(text)
        else:
            # Plain text version
            parts = [f"🔵 {request_id[:6]}"]
            
            # Model routing
            orig_model_str = f"{orig_provider}/{orig_family}"
            if orig_size != "unknown":
                orig_model_str += f"-{orig_size}"
            routed_model_str = f"{routed_provider}/{routed_family}"
            if routed_size != "unknown":
                routed_model_str += f"-{routed_size}"
            parts.append(f"{orig_model_str}→{routed_model_str}")
            
            parts.append(f"@{endpoint_provider}")
            
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = (input_tokens / context_limit) * 100
                parts.append(f"CTX:{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ({ctx_pct:.0f}%)")
            elif input_tokens > 0:
                parts.append(f"CTX:{fmt_tokens(input_tokens)}")
            
            if output_limit > 0:
                parts.append(f"OUT:{fmt_tokens(output_limit)}")
            
            if reasoning_config:
                from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    think = fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
                    parts.append(f"THINK:{think}")
                elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                    parts.append(f"THINK:{fmt_tokens(reasoning_config.budget)}")
            
            if stream:
                parts.append("STREAM")
            
            if message_count > 0:
                parts.append(f"{message_count}msg")
            
            if has_system:
                parts.append("SYS")
            
            if client_info:
                parts.append(client_info)
            
            logger.info(" | ".join(parts))
    
    @staticmethod
    def log_request_complete(
        request_id: str,
        usage: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "OK",
        model_name: Optional[str] = None,
        stream: bool = False,
        message_count: int = 0,
        has_system: bool = False,
        client_info: Optional[str] = None
    ) -> None:
        """
        Log request completion with ALL available info on ONE comprehensive line.
        
        Format (1 line with colors):
        🟢 abc123 15.8s | CTX:43.7k/1840.0k (2%) | OUT:1.3k/64.0k | THINK:920 | 81t/s | 📤 OUTPUT: [░░░░░░░░░░░░░░░░░░░░] 1.3k/64.0k (2%) 🟣 THINKING: [░░░░░░░░░░░░░░░░░░░░] 920/64.0k (1%) | STREAM | 3msg | SYS | 127.0.0.1
        """
        def format_tokens(count):
            """Format token count compactly."""
            if count >= 1000:
                return f"{count/1000:.1f}k"
            else:
                return str(count)
        
        # Extract token counts
        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0)) if usage else 0
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0)) if usage else 0
        thinking_tokens = 0
        
        if usage:
            if "thinking_tokens" in usage:
                thinking_tokens = usage["thinking_tokens"]
            elif "reasoning_tokens" in usage:
                thinking_tokens = usage["reasoning_tokens"]
            elif "completion_tokens_details" in usage:
                details = usage["completion_tokens_details"]
                if isinstance(details, dict):
                    thinking_tokens = details.get("reasoning_tokens", 0)
        
        # Get model limits for context window display
        from src.utils.model_limits import get_model_limits
        context_limit = 0
        output_limit = 0
        if model_name:
            context_limit, output_limit = get_model_limits(model_name)
        
        # Single comprehensive line with ALL info
        if USE_RICH and console:
            # Get session-specific color
            session_color = RequestLogger._get_session_color(request_id)
            
            text = Text()
            icon = "🟢" if status == "OK" else "🔴"
            text.append(f"{icon} ", style="bold green" if status == "OK" else "bold red")
            text.append(f"{request_id[:6]} ", style=session_color)
            
            if duration_ms:
                text.append(f"{duration_ms/1000:.1f}s ", style="yellow")
            
            if usage:
                # Show context window with ACTUAL input tokens (cyan shades)
                if context_limit > 0 and input_tokens > 0:
                    ctx_pct = (input_tokens / context_limit) * 100
                    ctx_color = "cyan" if ctx_pct < 50 else "bright_cyan" if ctx_pct < 80 else "yellow"
                    text.append("| CTX:", style="dim")
                    text.append(f"{format_tokens(input_tokens)}/{format_tokens(context_limit)} ", style=ctx_color)
                    text.append(f"({ctx_pct:.0f}%) ", style=ctx_color)
                else:
                    text.append(f"| CTX:{format_tokens(input_tokens)} ", style="cyan")
                
                # Show output tokens with limit (blue shades)
                if output_limit > 0:
                    out_pct = (output_tokens / output_limit) * 100 if output_tokens > 0 else 0
                    out_color = "blue" if out_pct < 50 else "bright_blue" if out_pct < 80 else "yellow"
                    text.append("| OUT:", style="dim")
                    text.append(f"{format_tokens(output_tokens)}/{format_tokens(output_limit)} ", style=out_color)
                else:
                    text.append(f"| OUT:{format_tokens(output_tokens)} ", style="blue")
                
                # Show thinking tokens (magenta)
                if thinking_tokens > 0:
                    text.append("| THINK:", style="dim")
                    text.append(f"{format_tokens(thinking_tokens)} ", style="bright_magenta")
            
            # Performance metrics
            if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
                tok_s = output_tokens / (duration_ms / 1000)
                text.append(f"| {tok_s:.0f}t/s ", style="cyan")
            
            # Compact progress bars (shorter)
            if output_limit > 0 and output_tokens > 0:
                out_pct = output_tokens / output_limit
                out_bar = RequestLogger._create_progress_bar(output_tokens, output_limit, width=10)
                out_color = RequestLogger._get_bar_color(out_pct)
                
                text.append("| 📤[", style="dim")
                text.append(out_bar, style=f"bold {out_color}")
                text.append("] ", style="dim")
                
                # Thinking tokens progress bar (compact)
                if thinking_tokens > 0:
                    think_pct = thinking_tokens / output_limit
                    think_bar = RequestLogger._create_progress_bar(thinking_tokens, output_limit, width=10)
                    think_color = RequestLogger._get_bar_color(think_pct)
                    
                    text.append("🟣[", style="dim")
                    text.append(think_bar, style=f"bold {think_color}")
                    text.append("] ", style="dim")
            
            # Request metadata
            if stream:
                text.append("| STREAM ", style="bright_blue")
            
            if message_count > 0:
                text.append(f"| {message_count}msg ", style="dim")
            
            if has_system:
                text.append("| SYS ", style="green")
            
            if client_info:
                text.append(f"| {client_info}", style="dim")
            
            console.print(text)
        else:
            icon = "🟢" if status == "OK" else "🔴"
            parts = [f"{icon} {request_id[:6]}"]
            
            if duration_ms:
                parts.append(f"{duration_ms/1000:.1f}s")
            
            if usage:
                if context_limit > 0 and input_tokens > 0:
                    ctx_pct = (input_tokens / context_limit) * 100
                    parts.append(f"CTX:{format_tokens(input_tokens)}/{format_tokens(context_limit)} ({ctx_pct:.0f}%)")
                else:
                    parts.append(f"CTX:{format_tokens(input_tokens)}")
                
                if output_limit > 0:
                    out_pct = (output_tokens / output_limit) * 100 if output_tokens > 0 else 0
                    parts.append(f"OUT:{format_tokens(output_tokens)}/{format_tokens(output_limit)}")
                else:
                    parts.append(f"OUT:{format_tokens(output_tokens)}")
                
                if thinking_tokens > 0:
                    parts.append(f"THINK:{format_tokens(thinking_tokens)}")
            
            if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
                tok_s = output_tokens / (duration_ms / 1000)
                parts.append(f"{tok_s:.0f}t/s")
            
            if stream:
                parts.append("STREAM")
            
            if message_count > 0:
                parts.append(f"{message_count}msg")
            
            if has_system:
                parts.append("SYS")
            
            if client_info:
                parts.append(client_info)
            
            logger.info(" | ".join(parts))
    
    @staticmethod
    def log_request_error(
        request_id: str,
        error: str,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log request error.
        
        Format (1 line with color):
        🔴 REQ abc123 | ERROR | 0.5s | Rate limit exceeded
        """
        # Truncate error message if too long
        error_msg = str(error)
        if len(error_msg) > 80:
            error_msg = error_msg[:77] + "..."
        
        if USE_RICH and console:
            # Get session-specific color
            session_color = RequestLogger._get_session_color(request_id)
            
            error_text = Text()
            error_text.append("🔴 ", style="bold red")
            error_text.append("REQ ", style="bold red")
            error_text.append(f"{request_id[:8]} ", style=session_color)
            error_text.append("| ", style="dim")
            error_text.append("ERROR", style="bold red")
            
            if duration_ms:
                error_text.append(" | ", style="dim")
                error_text.append(f"{duration_ms/1000:.1f}s", style="yellow")
            
            error_text.append(" | ", style="dim")
            error_text.append(error_msg, style="red")
            console.print(error_text)
        else:
            error_info = f"🔴 REQ {request_id[:8]} | ERROR"
            if duration_ms:
                error_info += f" | {duration_ms/1000:.1f}s"
            error_info += f" | {error_msg}"
            logger.error(error_info)


    @staticmethod
    def _create_progress_bar(
        used: int,
        total: int,
        width: int = 20,
        filled_char: str = "█",
        empty_char: str = "░"
    ) -> str:
        """
        Create an ASCII progress bar.
        
        Args:
            used: Used amount
            total: Total capacity
            width: Width of the bar in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            ASCII progress bar string
        """
        if total == 0:
            return empty_char * width
        
        percentage = min(used / total, 1.0)
        filled_width = int(width * percentage)
        empty_width = width - filled_width
        
        return filled_char * filled_width + empty_char * empty_width
    
    @staticmethod
    def _get_bar_color(percentage: float) -> str:
        """Get color style based on usage percentage."""
        if percentage < 0.5:
            return "green"
        elif percentage < 0.8:
            return "yellow"
        else:
            return "red"
    



# Global instance
request_logger = RequestLogger()
