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
    import tiktoken
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
    
    # Subtle color palette for session differentiation (using shades, not rainbow)
    SESSION_COLORS = [
        "bright_blue",      # Bright blue
        "bright_cyan",      # Bright cyan
        "bright_magenta",   # Bright magenta
        "blue",             # Blue
        "cyan",             # Cyan
        "magenta",          # Magenta
        "bright_white",     # Bright white
        "white",            # White
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
        input_tokens: int = 0
    ) -> None:
        """
        Log request start with ALL info on ONE line.
        
        Format (1 line with colors):
        🔵 abc123 | claude-opus→gpt-4o | openrouter.ai | CTX:1.2k/200k (1%) | OUT:0/16k | THINK:8k
        """
        # Extract endpoint name
        endpoint_name = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Format token counts
        def fmt_tokens(count):
            return f"{count/1000:.1f}k" if count >= 1000 else str(count)
        
        # Build ultra-compact single-line output
        if USE_RICH and console:
            # Get session-specific color
            session_color = RequestLogger._get_session_color(request_id)
            
            text = Text()
            text.append("🔵 ", style=f"bold {session_color}")
            text.append(f"{request_id[:6]} ", style=session_color)
            text.append(f"{original_model}→{routed_model} ", style="yellow")
            text.append(f"@{endpoint_name} ", style="dim")
            
            # Context window usage
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = (input_tokens / context_limit) * 100
                ctx_color = "green" if ctx_pct < 50 else "yellow" if ctx_pct < 80 else "red"
                text.append("| CTX:", style="dim")
                text.append(f"{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ", style=ctx_color)
                text.append(f"({ctx_pct:.0f}%) ", style=ctx_color)
            
            # Output limit
            if output_limit > 0:
                text.append("| OUT:", style="dim")
                text.append(f"{fmt_tokens(output_limit)} ", style="cyan")
            
            # Thinking/reasoning quota
            if reasoning_config:
                from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
                text.append("| THINK:", style="dim")
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    if reasoning_config.max_tokens:
                        text.append(f"{fmt_tokens(reasoning_config.max_tokens)}", style="bold magenta")
                    elif reasoning_config.effort:
                        text.append(f"{reasoning_config.effort}", style="bold magenta")
                elif isinstance(reasoning_config, AnthropicThinkingConfig):
                    text.append(f"{fmt_tokens(reasoning_config.budget)}", style="bold magenta")
                elif isinstance(reasoning_config, GeminiThinkingConfig):
                    text.append(f"{fmt_tokens(reasoning_config.budget)}", style="bold magenta")
            
            console.print(text)
        else:
            # Plain text version
            parts = [f"🔵 {request_id[:6]}", f"{original_model}→{routed_model}", f"@{endpoint_name}"]
            
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = (input_tokens / context_limit) * 100
                parts.append(f"CTX:{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ({ctx_pct:.0f}%)")
            
            if output_limit > 0:
                parts.append(f"OUT:{fmt_tokens(output_limit)}")
            
            if reasoning_config:
                from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    think = fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
                    parts.append(f"THINK:{think}")
                elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                    parts.append(f"THINK:{fmt_tokens(reasoning_config.budget)}")
            
            logger.info(" | ".join(parts))
    
    @staticmethod
    def log_request_complete(
        request_id: str,
        usage: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "OK",
        model_name: Optional[str] = None
    ) -> None:
        """
        Log request completion with ACTUAL usage stats from API response.
        
        Format (1 line with colors):
        🟢 abc123 1.7s | CTX:132k/400k (33%) | OUT:56/128k | THINK:8k | 24t/s
        """
        def format_tokens(count):
            """Format token count compactly."""
            if count >= 1000:
                return f"{count/1000:.1f}k"
            return str(count)
        
        def format_tokens(count):
            return f"{count/1000:.1f}k" if count >= 1000 else str(count)
        
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
        
        # Single compact line with ACTUAL token counts
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
                # Show context window with ACTUAL input tokens
                if context_limit > 0 and input_tokens > 0:
                    ctx_pct = (input_tokens / context_limit) * 100
                    ctx_color = "green" if ctx_pct < 50 else "yellow" if ctx_pct < 80 else "red"
                    text.append("| CTX:", style="dim")
                    text.append(f"{format_tokens(input_tokens)}/{format_tokens(context_limit)} ", style=ctx_color)
                    text.append(f"({ctx_pct:.0f}%) ", style=ctx_color)
                else:
                    text.append(f"| IN:{format_tokens(input_tokens)} ", style="blue")
                
                # Show output tokens with limit
                if output_limit > 0:
                    out_pct = (output_tokens / output_limit) * 100 if output_tokens > 0 else 0
                    out_color = "green" if out_pct < 50 else "yellow" if out_pct < 80 else "red"
                    text.append("| OUT:", style="dim")
                    text.append(f"{format_tokens(output_tokens)}/{format_tokens(output_limit)} ", style=out_color)
                else:
                    text.append(f"| OUT:{format_tokens(output_tokens)} ", style="green")
                
                # Show thinking tokens
                if thinking_tokens > 0:
                    text.append("| THINK:", style="dim")
                    text.append(f"{format_tokens(thinking_tokens)} ", style="magenta")
            
            if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
                tok_s = output_tokens / (duration_ms / 1000)
                text.append(f"| {tok_s:.0f}t/s", style="cyan")
            
            console.print(text)
        else:
            icon = "🟢" if status == "OK" else "🔴"
            info = f"{icon} {request_id[:8]}"
            if duration_ms:
                info += f" {duration_ms/1000:.1f}s"
            if usage:
                info += f" IN:{format_tokens(input_tokens)} OUT:{format_tokens(output_tokens)}"
                if thinking_tokens > 0:
                    info += f" THINK:{format_tokens(thinking_tokens)}"
            logger.info(info)
    
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
    
    @staticmethod
    def log_context_window_usage(
        request_id: str,
        input_tokens: int,
        context_limit: int,
        model_name: str
    ) -> None:
        """
        Log context window usage with visual progress bar.
        
        Format:
        📥 CONTEXT IN: [████████░░░░░░░░░░░░] 8.0k/128k (6%) ← Input tokens vs context limit
        """
        if context_limit == 0:
            return  # Skip if we don't know the limit
        
        percentage = input_tokens / context_limit
        
        def format_tokens(count):
            if count >= 1000:
                return f"{count/1000:.1f}k"
            return str(count)
        
        if USE_RICH and console:
            bar_color = RequestLogger._get_bar_color(percentage)
            bar = RequestLogger._create_progress_bar(input_tokens, context_limit, width=20)
            
            context_text = Text()
            context_text.append("📥 CONTEXT IN: ", style="bold blue")
            context_text.append("[", style="dim")
            context_text.append(bar, style=f"bold {bar_color}")
            context_text.append("]", style="dim")
            context_text.append(f" {format_tokens(input_tokens)}", style=f"bold {bar_color}")
            context_text.append(f"/{format_tokens(context_limit)}", style="cyan")
            context_text.append(f" ({percentage*100:.0f}%)", style=bar_color)
            
            console.print(context_text)
        else:
            bar = RequestLogger._create_progress_bar(input_tokens, context_limit, width=20)
            logger.info(
                f"📥 CONTEXT IN: [{bar}] {format_tokens(input_tokens)}/{format_tokens(context_limit)} "
                f"({percentage*100:.0f}%)"
            )
    
    @staticmethod
    def log_output_token_usage(
        request_id: str,
        output_tokens: int,
        output_limit: int,
        thinking_tokens: int = 0
    ) -> None:
        """
        Log output token usage with visual progress bar.
        
        Format:
        📤 OUTPUT: [███░░░░░░░░░░░░░░░░░] 3.0k/16k (19%) ← Output tokens vs output limit
        🟣 THINKING: [████████░░░░░░░░░░░░] 8.0k/16k (50%) ← Thinking tokens (if present)
        """
        if output_limit == 0:
            return  # Skip if we don't know the limit
        
        percentage = output_tokens / output_limit
        
        def format_tokens(count):
            if count >= 1000:
                return f"{count/1000:.1f}k"
            return str(count)
        
        if USE_RICH and console:
            bar_color = RequestLogger._get_bar_color(percentage)
            bar = RequestLogger._create_progress_bar(output_tokens, output_limit, width=20)
            
            output_text = Text()
            output_text.append("📤 OUTPUT: ", style="bold green")
            output_text.append("[", style="dim")
            output_text.append(bar, style=f"bold {bar_color}")
            output_text.append("]", style="dim")
            output_text.append(f" {format_tokens(output_tokens)}", style=f"bold {bar_color}")
            output_text.append(f"/{format_tokens(output_limit)}", style="cyan")
            output_text.append(f" ({percentage*100:.0f}%)", style=bar_color)
            
            console.print(output_text)
            
            # Show thinking tokens separately if present
            if thinking_tokens > 0:
                think_percentage = thinking_tokens / output_limit
                think_bar_color = RequestLogger._get_bar_color(think_percentage)
                think_bar = RequestLogger._create_progress_bar(thinking_tokens, output_limit, width=20)
                
                think_text = Text()
                think_text.append("🟣 THINKING: ", style="bold magenta")
                think_text.append("[", style="dim")
                think_text.append(think_bar, style=f"bold {think_bar_color}")
                think_text.append("]", style="dim")
                think_text.append(f" {format_tokens(thinking_tokens)}", style=f"bold {think_bar_color}")
                think_text.append(f"/{format_tokens(output_limit)}", style="cyan")
                think_text.append(f" ({think_percentage*100:.0f}%)", style=think_bar_color)
                
                console.print(think_text)
        else:
            bar = RequestLogger._create_progress_bar(output_tokens, output_limit, width=20)
            logger.info(
                f"📤 OUTPUT: [{bar}] {format_tokens(output_tokens)}/{format_tokens(output_limit)} "
                f"({percentage*100:.0f}%)"
            )
            
            if thinking_tokens > 0:
                think_bar = RequestLogger._create_progress_bar(thinking_tokens, output_limit, width=20)
                think_percentage = thinking_tokens / output_limit
                logger.info(
                    f"🟣 THINKING: [{think_bar}] {format_tokens(thinking_tokens)}/{format_tokens(output_limit)} "
                    f"({think_percentage*100:.0f}%)"
                )


# Global instance
request_logger = RequestLogger()
