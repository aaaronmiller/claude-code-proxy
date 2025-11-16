"""
Compact request logging utility for terminal output.

Provides information-dense, color-coded logging for reasoning requests,
model routing, and token usage in 3-5 lines maximum.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Try to import Rich for colored output
try:
    from rich.console import Console
    from rich.text import Text
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
        input_text: Optional[str] = None
    ) -> None:
        """
        Log request start with routing and reasoning info.
        
        Format (2-4 lines with colors):
        🔵 REQ abc123 | claude-opus-4:8k → gpt-4o @ openrouter.ai | STREAM
        🟣 REASONING: Anthropic thinking=8192 tokens
        📊 INPUT: ~1.2k tokens (4.8k chars)
        """
        # Extract endpoint name
        endpoint_name = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        mode = "STREAM" if stream else "SYNC"
        
        if USE_RICH and console:
            # Rich colored output
            # Line 1: Request routing (Blue)
            route_text = Text()
            route_text.append("🔵 REQ ", style="bold blue")
            route_text.append(f"{request_id[:8]} ", style="cyan")
            route_text.append("| ", style="dim")
            route_text.append(f"{original_model} ", style="yellow")
            route_text.append("→ ", style="dim")
            route_text.append(f"{routed_model} ", style="green")
            route_text.append("@ ", style="dim")
            route_text.append(f"{endpoint_name} ", style="magenta")
            route_text.append("| ", style="dim")
            route_text.append(mode, style="bold cyan" if stream else "cyan")
            console.print(route_text)
            
            # Line 2: Reasoning config (Purple/Magenta)
            if reasoning_config:
                from src.models.reasoning import (
                    OpenAIReasoningConfig,
                    AnthropicThinkingConfig,
                    GeminiThinkingConfig
                )
                
                reasoning_text = Text()
                reasoning_text.append("🟣 REASONING: ", style="bold magenta")
                
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    if reasoning_config.effort:
                        reasoning_text.append(f"OpenAI effort=", style="magenta")
                        reasoning_text.append(f"{reasoning_config.effort}", style="bold magenta")
                    if reasoning_config.max_tokens:
                        if reasoning_config.effort:
                            reasoning_text.append(" + ", style="dim")
                        reasoning_text.append(f"budget=", style="magenta")
                        reasoning_text.append(f"{reasoning_config.max_tokens:,}", style="bold magenta")
                        reasoning_text.append(" tokens", style="magenta")
                    if reasoning_config.exclude:
                        reasoning_text.append(" (excluded)", style="dim magenta")
                elif isinstance(reasoning_config, AnthropicThinkingConfig):
                    reasoning_text.append(f"Anthropic thinking=", style="magenta")
                    reasoning_text.append(f"{reasoning_config.budget:,}", style="bold magenta")
                    reasoning_text.append(" tokens", style="magenta")
                elif isinstance(reasoning_config, GeminiThinkingConfig):
                    reasoning_text.append(f"Gemini thinking=", style="magenta")
                    reasoning_text.append(f"{reasoning_config.budget:,}", style="bold magenta")
                    reasoning_text.append(" tokens", style="magenta")
                
                console.print(reasoning_text)
            
            # Line 3: Input token count (if available)
            if SHOW_TOKEN_COUNTS and input_text:
                input_tokens = RequestLogger._count_tokens_precise(input_text, routed_model)
                input_chars = len(input_text)
                
                input_text_obj = Text()
                input_text_obj.append("📊 INPUT: ", style="bold blue")
                input_text_obj.append(f"~{input_tokens/1000:.1f}k" if input_tokens >= 1000 else f"{input_tokens}", style="bold cyan")
                input_text_obj.append(" tokens ", style="cyan")
                input_text_obj.append(f"({input_chars/1000:.1f}k chars)" if input_chars >= 1000 else f"({input_chars} chars)", style="dim cyan")
                console.print(input_text_obj)
        else:
            # Plain text output (fallback)
            route_info = f"🔵 REQ {request_id[:8]} | {original_model} → {routed_model} @ {endpoint_name} | {mode}"
            logger.info(route_info)
            
            if reasoning_config:
                from src.models.reasoning import (
                    OpenAIReasoningConfig,
                    AnthropicThinkingConfig,
                    GeminiThinkingConfig
                )
                
                reasoning_info = "🟣 REASONING: "
                if isinstance(reasoning_config, OpenAIReasoningConfig):
                    if reasoning_config.effort:
                        reasoning_info += f"OpenAI effort={reasoning_config.effort}"
                    if reasoning_config.max_tokens:
                        reasoning_info += f" budget={reasoning_config.max_tokens:,} tokens"
                elif isinstance(reasoning_config, AnthropicThinkingConfig):
                    reasoning_info += f"Anthropic thinking={reasoning_config.budget:,} tokens"
                elif isinstance(reasoning_config, GeminiThinkingConfig):
                    reasoning_info += f"Gemini thinking={reasoning_config.budget:,} tokens"
                
                logger.info(reasoning_info)
            
            if SHOW_TOKEN_COUNTS and input_text:
                input_tokens = RequestLogger._count_tokens_precise(input_text, routed_model)
                input_chars = len(input_text)
                logger.info(f"📊 INPUT: ~{input_tokens:,} tokens ({input_chars:,} chars)")
    
    @staticmethod
    def log_request_complete(
        request_id: str,
        usage: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "OK"
    ) -> None:
        """
        Log request completion with usage stats.
        
        Format (1-2 lines with colors):
        🟢 REQ abc123 | OK | 2.3s | 45 tok/s | $0.0234
        📊 IN:1.2k OUT:3.4k THINK:8.0k TOTAL:12.6k
        """
        def format_tokens(count):
            """Format token count compactly."""
            if count >= 1000:
                return f"{count/1000:.1f}k"
            return str(count)
        
        if USE_RICH and console:
            # Rich colored output
            completion_text = Text()
            
            # Status icon and color
            if status == "OK":
                completion_text.append("🟢 ", style="bold green")
                status_style = "bold green"
            else:
                completion_text.append("🟡 ", style="bold yellow")
                status_style = "bold yellow"
            
            completion_text.append("REQ ", style=status_style)
            completion_text.append(f"{request_id[:8]} ", style="cyan")
            completion_text.append("| ", style="dim")
            completion_text.append(status, style=status_style)
            
            # Duration
            if duration_ms:
                completion_text.append(" | ", style="dim")
                duration_s = duration_ms / 1000
                completion_text.append(f"{duration_s:.2f}s", style="yellow")
            
            # Performance metrics
            if SHOW_PERFORMANCE and usage and duration_ms:
                output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
                if output_tokens > 0 and duration_ms > 0:
                    tokens_per_sec = output_tokens / (duration_ms / 1000)
                    completion_text.append(" | ", style="dim")
                    completion_text.append(f"{tokens_per_sec:.0f} tok/s", style="bold cyan")
            
            console.print(completion_text)
            
            # Token usage breakdown
            if usage:
                input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0))
                output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
                
                # Check for thinking/reasoning tokens
                thinking_tokens = 0
                if "thinking_tokens" in usage:
                    thinking_tokens = usage["thinking_tokens"]
                elif "reasoning_tokens" in usage:
                    thinking_tokens = usage["reasoning_tokens"]
                elif "completion_tokens_details" in usage:
                    details = usage["completion_tokens_details"]
                    if isinstance(details, dict):
                        thinking_tokens = details.get("reasoning_tokens", 0)
                
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens + thinking_tokens)
                
                usage_text = Text()
                usage_text.append("📊 ", style="bold")
                usage_text.append("IN:", style="blue")
                usage_text.append(format_tokens(input_tokens), style="bold blue")
                usage_text.append(" OUT:", style="green")
                usage_text.append(format_tokens(output_tokens), style="bold green")
                
                if thinking_tokens > 0:
                    usage_text.append(" THINK:", style="magenta")
                    usage_text.append(format_tokens(thinking_tokens), style="bold magenta")
                
                usage_text.append(" TOTAL:", style="cyan")
                usage_text.append(format_tokens(total_tokens), style="bold cyan")
                
                console.print(usage_text)
        else:
            # Plain text output (fallback)
            status_icon = "🟢" if status == "OK" else "🟡"
            completion_info = f"{status_icon} REQ {request_id[:8]} | {status}"
            
            if duration_ms:
                completion_info += f" | {duration_ms/1000:.2f}s"
            
            if SHOW_PERFORMANCE and usage and duration_ms:
                output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
                if output_tokens > 0:
                    tokens_per_sec = output_tokens / (duration_ms / 1000)
                    completion_info += f" | {tokens_per_sec:.0f} tok/s"
            
            logger.info(completion_info)
            
            if usage:
                input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0))
                output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0))
                
                thinking_tokens = 0
                if "thinking_tokens" in usage:
                    thinking_tokens = usage["thinking_tokens"]
                elif "reasoning_tokens" in usage:
                    thinking_tokens = usage["reasoning_tokens"]
                elif "completion_tokens_details" in usage:
                    details = usage["completion_tokens_details"]
                    if isinstance(details, dict):
                        thinking_tokens = details.get("reasoning_tokens", 0)
                
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens + thinking_tokens)
                
                usage_info = f"📊 IN:{format_tokens(input_tokens)} OUT:{format_tokens(output_tokens)}"
                if thinking_tokens > 0:
                    usage_info += f" THINK:{format_tokens(thinking_tokens)}"
                usage_info += f" TOTAL:{format_tokens(total_tokens)}"
                
                logger.info(usage_info)
    
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
            error_text = Text()
            error_text.append("🔴 ", style="bold red")
            error_text.append("REQ ", style="bold red")
            error_text.append(f"{request_id[:8]} ", style="cyan")
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
