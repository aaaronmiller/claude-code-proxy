"""
Ultra-compact single-line request logger with sophisticated color scheme.

Design principles:
- Everything on ONE line
- Use emojis to save tokens
- Subtle colors for normal ops, bright for warnings/errors
- Color shades to differentiate request types
- Session-based color consistency
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try Rich for colors
try:
    from rich.console import Console
    from rich.text import Text
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


class CompactLogger:
    """Single-line, color-coded, emoji-rich request logger."""

    # Sophisticated color palette (subtle → bright)
    # Using cyan/magenta/blue shades for sessions (not rainbow)
    SESSION_COLORS = [
        ("cyan", "dim"),           # Subtle cyan
        ("bright_cyan", ""),        # Bright cyan
        ("magenta", "dim"),         # Subtle magenta
        ("bright_magenta", ""),     # Bright magenta
        ("blue", "dim"),            # Subtle blue
        ("bright_blue", ""),        # Bright blue
    ]

    # Request type colors
    TYPE_COLORS = {
        "text": "white",           # Plain text requests
        "tools": "yellow",         # Tool-using requests
        "images": "magenta",       # Image requests
        "reasoning": "cyan",       # Reasoning requests
        "streaming": "blue",       # Streaming requests
    }

    # Status colors
    STATUS_COLORS = {
        "start": "dim white",
        "ok": "green",
        "error": "bright_red",
        "warning": "bright_yellow",
    }

    @staticmethod
    def _get_session_color(session_id: str) -> tuple[str, str]:
        """Get consistent color and style for session."""
        if not session_id:
            return ("white", "dim")

        session_hash = int(hashlib.md5(session_id[:8].encode()).hexdigest()[:8], 16)
        color_idx = session_hash % len(CompactLogger.SESSION_COLORS)
        return CompactLogger.SESSION_COLORS[color_idx]

    @staticmethod
    def _get_request_type(
        has_tools: bool = False,
        has_images: bool = False,
        reasoning_config: Any = None,
        stream: bool = False
    ) -> str:
        """Determine request type for color coding."""
        if reasoning_config:
            return "reasoning"
        if has_images:
            return "images"
        if has_tools:
            return "tools"
        if stream:
            return "streaming"
        return "text"

    @staticmethod
    def _fmt_tokens(count: int) -> str:
        """Format token count compactly."""
        if count >= 1_000_000:
            return f"{count/1_000_000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}k"
        else:
            return str(count)

    @staticmethod
    def _fmt_duration(ms: float) -> str:
        """Format duration compactly."""
        if ms >= 60000:
            return f"{ms/60000:.1f}m"
        elif ms >= 1000:
            return f"{ms/1000:.1f}s"
        else:
            return f"{ms:.0f}ms"

    @staticmethod
    def _get_model_short(model: str) -> str:
        """Get short model name."""
        # Extract key parts: provider/family-size
        if "/" in model:
            parts = model.split("/")
            provider = parts[0][:3]  # openai → ope, anthropic → ant
            model_part = parts[1]

            # Shorten model name
            if "gpt-5" in model_part:
                family = "gpt5"
            elif "gpt-4o" in model_part:
                family = "4o"
            elif "o1" in model_part or "o3" in model_part:
                family = model_part.split("-")[0]  # o1, o3
            elif "claude-3.5" in model_part or "claude-sonnet-4" in model_part:
                family = "c3.5" if "3.5" in model_part else "c4"
            elif "claude" in model_part:
                family = "c3"
            else:
                family = model_part[:6]

            # Extract size
            size = ""
            if "mini" in model_part:
                size = "-m"
            elif "haiku" in model_part:
                size = "-h"
            elif "sonnet" in model_part:
                size = "-s"
            elif "opus" in model_part:
                size = "-o"

            return f"{provider}/{family}{size}"
        else:
            return model[:12]

    @staticmethod
    def log_request_start(
        request_id: str,
        original_model: str,
        routed_model: str,
        endpoint: str,
        reasoning_config: Optional[Any] = None,
        stream: bool = False,
        input_tokens: int = 0,
        context_limit: int = 0,
        output_limit: int = 0,
        message_count: int = 0,
        has_system: bool = False,
        has_tools: bool = False,
        has_images: bool = False,
        client_info: Optional[str] = None
    ) -> None:
        """
        Log request start - SINGLE LINE.

        Format:
        🔵abc12│ant/c3.5-s→ope/gpt5│6.2k/200k(3%)→16k│⚡8k│📨3│🔧│127.0.0.1
        """
        req_type = CompactLogger._get_request_type(has_tools, has_images, reasoning_config, stream)
        session_color, session_style = CompactLogger._get_session_color(request_id)

        # Icon based on type
        icon_map = {
            "reasoning": "🧠",
            "tools": "🔧",
            "images": "🖼️",
            "streaming": "🌊",
            "text": "📝"
        }
        type_icon = icon_map.get(req_type, "📝")

        # Build compact parts
        rid = request_id[:5]  # Shortened request ID
        orig = CompactLogger._get_model_short(original_model)
        routed = CompactLogger._get_model_short(routed_model)

        parts = []

        # Context usage
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = int(input_tokens / context_limit * 100)
            ctx_color = "green" if ctx_pct < 50 else "yellow" if ctx_pct < 80 else "red"
            ctx_str = f"{CompactLogger._fmt_tokens(input_tokens)}/{CompactLogger._fmt_tokens(context_limit)}({ctx_pct}%)"
            parts.append(("ctx", ctx_str, ctx_color))
        elif input_tokens > 0:
            parts.append(("ctx", CompactLogger._fmt_tokens(input_tokens), "cyan"))

        # Output limit
        if output_limit > 0:
            parts.append(("out", CompactLogger._fmt_tokens(output_limit), "blue"))

        # Reasoning budget
        if reasoning_config:
            from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
            if isinstance(reasoning_config, OpenAIReasoningConfig):
                think_str = CompactLogger._fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
            elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                think_str = CompactLogger._fmt_tokens(reasoning_config.budget)
            else:
                think_str = "?"
            parts.append(("think", think_str, "magenta"))

        # Build output
        if RICH_AVAILABLE and console:
            text = Text()

            # Status + ID (colored by session)
            style = f"{session_style} {session_color}" if session_style else session_color
            text.append("🔵", style=f"bold {session_color}")
            text.append(f"{rid}", style=style)
            text.append("│", style="dim")

            # Model routing
            text.append(f"{orig}", style="yellow")
            text.append("→", style="dim")
            text.append(f"{routed}", style="green")
            text.append("│", style="dim")

            # Add parts
            for i, (label, value, color) in enumerate(parts):
                if i > 0:
                    text.append("→", style="dim")
                text.append(value, style=color)

            # Type icon + metadata
            text.append("│", style="dim")
            text.append(type_icon)
            if message_count > 0:
                text.append(f"{message_count}", style="dim")
            if has_system:
                text.append("🖥️", style="dim")
            if stream:
                text.append("🌊", style="dim")
            if client_info:
                text.append(f"│{client_info[:9]}", style="dim")

            console.print(text)
        else:
            # Plain text fallback
            parts_str = "→".join([f"{v}" for _, v, _ in parts])
            meta = f"{type_icon}{message_count if message_count > 0 else ''}"
            if has_system:
                meta += "🖥️"
            if stream:
                meta += "🌊"

            line = f"🔵{rid}│{orig}→{routed}│{parts_str}│{meta}"
            if client_info:
                line += f"│{client_info[:9]}"
            logger.info(line)

    @staticmethod
    def log_request_complete(
        request_id: str,
        usage: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "OK",
        model_name: Optional[str] = None,
        stream: bool = False,
        has_reasoning: bool = False
    ) -> None:
        """
        Log request completion - SINGLE LINE.

        Format:
        🟢abc12│15.2s│43.7k→1.3k💭920│82t/s│$0.023
        """
        session_color, session_style = CompactLogger._get_session_color(request_id)

        # Extract tokens
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

        # Calculate cost (rough estimate)
        cost = 0.0
        if model_name:
            # Rough cost estimation (per 1M tokens)
            cost_map = {
                "gpt-5": (0.015, 0.060),
                "gpt-4o": (0.005, 0.015),
                "gpt-4": (0.030, 0.060),
                "claude-3.5": (0.003, 0.015),
                "claude-3": (0.003, 0.015),
            }
            for key, (in_cost, out_cost) in cost_map.items():
                if key in model_name.lower():
                    cost = (input_tokens / 1_000_000 * in_cost) + (output_tokens / 1_000_000 * out_cost)
                    break

        # Build output
        if RICH_AVAILABLE and console:
            text = Text()

            # Status
            icon = "🟢" if status == "OK" else "🔴"
            color = "green" if status == "OK" else "red"
            style = f"{session_style} {session_color}" if session_style else session_color

            text.append(icon, style=f"bold {color}")
            text.append(f"{request_id[:5]}", style=style)
            text.append("│", style="dim")

            # Duration
            if duration_ms:
                text.append(CompactLogger._fmt_duration(duration_ms), style="yellow")
                text.append("│", style="dim")

            # Tokens
            text.append(CompactLogger._fmt_tokens(input_tokens), style="cyan")
            text.append("→", style="dim")
            text.append(CompactLogger._fmt_tokens(output_tokens), style="blue")

            # Thinking tokens
            if thinking_tokens > 0:
                text.append("💭", style="dim")
                text.append(CompactLogger._fmt_tokens(thinking_tokens), style="magenta")

            text.append("│", style="dim")

            # Performance
            if duration_ms and output_tokens > 0:
                tps = output_tokens / (duration_ms / 1000)
                tps_color = "green" if tps > 50 else "yellow" if tps > 20 else "red"
                text.append(f"{tps:.0f}t/s", style=tps_color)
                text.append("│", style="dim")

            # Cost
            if cost > 0:
                cost_color = "green" if cost < 0.01 else "yellow" if cost < 0.10 else "red"
                text.append(f"${cost:.4f}", style=cost_color)

            console.print(text)
        else:
            # Plain text
            rid = request_id[:5]
            icon = "🟢" if status == "OK" else "🔴"

            parts = [f"{icon}{rid}"]

            if duration_ms:
                parts.append(CompactLogger._fmt_duration(duration_ms))

            tokens_str = f"{CompactLogger._fmt_tokens(input_tokens)}→{CompactLogger._fmt_tokens(output_tokens)}"
            if thinking_tokens > 0:
                tokens_str += f"💭{CompactLogger._fmt_tokens(thinking_tokens)}"
            parts.append(tokens_str)

            if duration_ms and output_tokens > 0:
                tps = output_tokens / (duration_ms / 1000)
                parts.append(f"{tps:.0f}t/s")

            if cost > 0:
                parts.append(f"${cost:.4f}")

            logger.info("│".join(parts))

    @staticmethod
    def log_request_error(
        request_id: str,
        error: str,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Log error - SINGLE LINE.

        Format:
        🔴abc12│0.5s│Rate limit exceeded
        """
        session_color, session_style = CompactLogger._get_session_color(request_id)

        # Truncate error
        error_msg = error[:60] + "..." if len(error) > 60 else error

        if RICH_AVAILABLE and console:
            text = Text()
            style = f"{session_style} {session_color}" if session_style else session_color

            text.append("🔴", style="bold red")
            text.append(f"{request_id[:5]}", style=style)
            text.append("│", style="dim")

            if duration_ms:
                text.append(CompactLogger._fmt_duration(duration_ms), style="yellow")
                text.append("│", style="dim")

            text.append(error_msg, style="red")

            console.print(text)
        else:
            parts = [f"🔴{request_id[:5]}"]
            if duration_ms:
                parts.append(CompactLogger._fmt_duration(duration_ms))
            parts.append(error_msg)
            logger.error("│".join(parts))


# Global instance
compact_logger = CompactLogger()
