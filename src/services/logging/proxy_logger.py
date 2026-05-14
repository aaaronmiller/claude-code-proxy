"""
Unified proxy request logger.

Design principles:
- Scaffold, never content. Color wraps routing, metrics, status — never the payload.
- One hue, one meaning, forever. Red=fail, Amber=warn, Green=ok, Cyan=route, Blue=metrics.
- Luminance encodes hierarchy (bright/normal/dim); hue encodes category.
- Color is progressive enhancement. NO_COLOR=1 produces identical information.
- Stable session fingerprint per client for concurrent request disambiguation.

Normal format (1 line):
  21:22:15 ▶ abc12  sonnet → qwen3.6+  4.2k tks  STREAM
  21:22:17 ✓ abc12  sonnet → qwen3.6+  4.2k→340t  2.3s  148t/s

Debug format (2 lines):
  21:22:15 ▶ abc12  claude-sonnet-4-20250514 → opencode_go/qwen3.6-plus @opencode_go
             endpoint: https://opencode.ai/zen/go/v1  ctx: 256k  STREAM 3msg
  21:22:17 ✓ abc12  sonnet → qwen3.6+  4200→340t  2.3s  148t/s
             cascade: sonnet(try) → qwen3.6+(ok)  route: middle tier
"""

import hashlib
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

try:
    from rich.console import Console
    from rich.text import Text

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").lower()  # info | debug
LOG_FILE = os.environ.get("LOG_FILE", "logs/proxy.log")
LOG_MAX_MB = int(os.environ.get("LOG_MAX_MB", "50"))
LOG_RETENTION = int(os.environ.get("LOG_RETENTION_DAYS", "7"))

DEBUG_MODE = LOG_LEVEL == "debug"

# ── Semantic Color Roles (Unified Palette) ────────────────────────────────────
# HUE  = category  (immutable: red=fail, amber=warn, green=ok, cyan=route, blue=metrics)
# DIM  = hierarchy (context/metadata, always paired with explicit color)
#
# ROLE     SEMANTIC                RICH STYLE
# ERROR    Fatal failures, 5xx     red
# WARN     Degradations, fallbacks yellow (amber)
# SUCCESS  2xx, completions        green
# INFO     Routing, flow arrows    cyan
# METRICS  Tokens, latency, speed  blue
# META     Timestamps, IDs, labels dim (gray)

COLOR_ERROR = "red"
COLOR_WARN = "yellow"
COLOR_SUCCESS = "green"
COLOR_INFO = "cyan"
COLOR_METRICS = "blue"
COLOR_META = "dim"  # Rich "dim" = gray

# ── Session fingerprinting ────────────────────────────────────────────────────
# Stable session ID for concurrent request disambiguation.
# Session colors use Rich's named colors so user theme is honored.
_session_ids: Dict[str, str] = {}
_session_index = 0

# 6 muted theme-friendly colors for session IDs
SESSION_HUES = [
    "cyan",
    "magenta",
    "blue",
    "green",
    "yellow",
    "white",
]


def _get_session_id(fingerprint: str) -> str:
    """Get consistent session identifier (hue) for a client."""
    global _session_index
    if fingerprint not in _session_ids:
        _session_ids[fingerprint] = SESSION_HUES[_session_index % len(SESSION_HUES)]
        _session_index += 1
    return _session_ids[fingerprint]


def _fingerprint_request(request_meta: Dict[str, Any]) -> str:
    """Create stable session fingerprint from request metadata."""
    ip = request_meta.get("client_ip", "unknown")
    ua = request_meta.get("user_agent", "")
    raw = f"{ip}|{ua}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


# ── Formatting helpers ────────────────────────────────────────────────────────
def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _fmt_duration(ms: float) -> str:
    if ms >= 60000:
        return f"{ms / 60000:.1f}m"
    if ms >= 1000:
        return f"{ms / 1000:.1f}s"
    return f"{ms:.0f}ms"


def _model_short(name: str) -> str:
    """Short model name for normal mode."""
    if "/" in name:
        prefix, rest = name.split("/", 1)
        p = prefix[:3]
        if "qwen3.6" in rest:
            f = "q3.6" + (
                "-plus"
                if "plus" in rest
                else "-max"
                if "max" in rest
                else "-flash"
                if "flash" in rest
                else ""
            )
        elif "qwen3" in rest:
            f = "q3"
        elif "claude-sonnet-4" in rest:
            f = "sonnet4"
        elif "claude-opus-4" in rest:
            f = "opus4"
        elif "claude-haiku" in rest:
            f = "haiku"
        elif "claude-3.5" in rest:
            f = "c3.5"
        elif "claude" in rest:
            f = "claude"
        elif "owl" in rest:
            f = "owl"
        elif "nemotron" in rest:
            f = "nemotron"
        elif "hy3" in rest:
            f = "hy3"
        elif "minimax" in rest:
            f = "minimax"
        elif "gpt-oss" in rest:
            f = "gpt-oss"
        elif "gpt-4" in rest:
            f = "gpt4"
        elif "gpt-5" in rest:
            f = "gpt5"
        elif "gemini" in rest:
            f = "gemini"
        else:
            f = rest[:8]
        return f"{p}/{f}"
    # No provider prefix — match model families directly
    if name.startswith("claude-sonnet-4"):
        return "sonnet4"
    if name.startswith("claude-opus-4"):
        return "opus4"
    if name.startswith("claude-haiku"):
        return "haiku"
    if name.startswith("claude-3.5"):
        return "c3.5"
    if name.startswith("claude"):
        return "claude"
    if name.startswith("gpt-4"):
        return "gpt4"
    if name.startswith("gpt-5"):
        return "gpt5"
    if name.startswith("qwen3.6"):
        return "q3.6"
    if name.startswith("qwen3"):
        return "q3"
    return name[:10]


# ── File logger setup ─────────────────────────────────────────────────────────
_file_logger: Optional[logging.Logger] = None


def _setup_file_logger():
    """Set up rotating file logger for logs/proxy.log."""
    global _file_logger
    if _file_logger is not None:
        return

    _file_logger = logging.getLogger("proxy.file")
    _file_logger.setLevel(logging.DEBUG)
    _file_logger.propagate = False

    if LOG_FILE:
        os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_MB * 1024 * 1024,
            backupCount=LOG_RETENTION,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        _file_logger.addHandler(handler)


def _log_file(line: str):
    """Write plain-text line to file logger."""
    if _file_logger is None:
        _setup_file_logger()
    if _file_logger:
        _file_logger.info(line)


# ── Task tag helpers ──────────────────────────────────────────────────────────
_TASK_TAGS = {
    "big": "",
    "middle": "",
    "small": "",
    "background": "[bg]",
    "long_context": "[ctx]",
    "web_search": "[search]",
    "think": "[think]",
    "image": "[img]",
    "router": "[route]",
    "toolcall": "[tools]",
}


def _task_tag(assignment_id: str) -> str:
    """Return task tag for non-standard routing."""
    if assignment_id and assignment_id not in ("big", "middle", "small", ""):
        return _TASK_TAGS.get(assignment_id, f"[{assignment_id}]")
    return ""


# ── Public API ────────────────────────────────────────────────────────────────


class ProxyLogger:
    """Unified request logger with normal + debug modes."""

    def log_start(
        self,
        request_id: str,
        original_model: str,
        routed_model: str,
        endpoint: str = "",
        stream: bool = False,
        input_tokens: int = 0,
        context_limit: int = 0,
        output_limit: int = 0,
        message_count: int = 0,
        has_tools: bool = False,
        has_reasoning: bool = False,
        has_images: bool = False,
        assignment_id: str = "",
        client_ip: str = "",
        user_agent: str = "",
        cascade_info: str = "",
        **kwargs,
    ) -> None:
        """Log request start."""
        fp = _fingerprint_request({"client_ip": client_ip, "user_agent": user_agent})
        session = _get_session_id(fp)

        ts = datetime.now().strftime("%H:%M:%S")
        rid = request_id[:6]
        task = _task_tag(assignment_id)

        # Task type icon
        icon = "📝"
        if has_reasoning:
            icon = "🧠"
        elif has_images:
            icon = "🖼️"
        elif has_tools:
            icon = "🔧"

        if DEBUG_MODE:
            self._terminal_debug_start(
                ts,
                rid,
                session,
                original_model,
                routed_model,
                endpoint,
                stream,
                input_tokens,
                context_limit,
                output_limit,
                message_count,
                icon,
                task,
                cascade_info,
            )
        else:
            self._terminal_normal_start(
                ts,
                rid,
                session,
                original_model,
                routed_model,
                stream,
                input_tokens,
                icon,
                task,
            )

        # File log (always plain text, debug detail)
        self._file_start(
            ts,
            rid,
            original_model,
            routed_model,
            endpoint,
            stream,
            input_tokens,
            context_limit,
            output_limit,
            message_count,
            has_tools,
            has_reasoning,
            has_images,
            assignment_id,
            cascade_info,
        )

    def log_complete(
        self,
        request_id: str,
        usage: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        status: str = "OK",
        model_name: str = "",
        stream: bool = False,
        original_model: str = "",
        assignment_id: str = "",
        cascade_chain: str = "",
        client_ip: str = "",
        user_agent: str = "",
        error: str = "",
        **kwargs,
    ) -> None:
        """Log request completion."""
        fp = _fingerprint_request({"client_ip": client_ip, "user_agent": user_agent})
        session = _get_session_id(fp)

        ts = datetime.now().strftime("%H:%M:%S")
        rid = request_id[:6]

        input_tokens = usage.get("input_tokens", 0) if usage else 0
        output_tokens = usage.get("output_tokens", 0) if usage else 0
        thinking_tokens = usage.get("thinking_tokens", 0) if usage else 0

        # Cost estimation from pricing index
        cost: Optional[float] = None
        try:
            from src.services.models.cost_lookup import estimate_cost
            cost = estimate_cost(model_name, input_tokens, output_tokens)
        except Exception:
            pass

        speed = ""
        if duration_ms and output_tokens > 0:
            tps = output_tokens / (duration_ms / 1000)
            speed = f"{tps:.0f}t/s"

        task = _task_tag(assignment_id)

        if DEBUG_MODE:
            self._terminal_debug_complete(
                ts, rid, session, status, model_name,
                input_tokens, output_tokens, thinking_tokens,
                duration_ms, speed, stream, task, cascade_chain, error, cost,
            )
        else:
            self._terminal_normal_complete(
                ts, rid, session, status, original_model, model_name,
                input_tokens, output_tokens, thinking_tokens,
                duration_ms, speed, stream, task, cascade_chain, error, cost,
            )

        # File log
        self._file_complete(
            ts,
            rid,
            status,
            original_model,
            model_name,
            input_tokens,
            output_tokens,
            thinking_tokens,
            duration_ms,
            speed,
            stream,
            assignment_id,
            cascade_chain,
            error,
        )

    def log_error(
        self,
        request_id: str,
        error: str,
        duration_ms: Optional[float] = None,
        model_name: str = "",
        original_model: str = "",
        provider: str = "",
        endpoint: str = "",
        cascade_chain: str = "",
        traceback_str: str = "",
        client_ip: str = "",
        user_agent: str = "",
        **kwargs,
    ) -> None:
        """Log request error."""
        fp = _fingerprint_request({"client_ip": client_ip, "user_agent": user_agent})
        session = _get_session_id(fp)

        ts = datetime.now().strftime("%H:%M:%S")
        rid = request_id[:6]

        if DEBUG_MODE:
            self._terminal_debug_error(
                ts,
                rid,
                session,
                error,
                duration_ms,
                model_name,
                original_model,
                provider,
                endpoint,
                cascade_chain,
                traceback_str,
            )
        else:
            self._terminal_normal_error(
                ts,
                rid,
                session,
                error,
                duration_ms,
                model_name,
                original_model,
                provider,
                endpoint,
                cascade_chain,
                traceback_str,
            )

        # File log
        self._file_error(
            ts,
            rid,
            error,
            duration_ms,
            model_name,
            original_model,
            provider,
            endpoint,
            cascade_chain,
            traceback_str,
        )

    # ── Terminal: Normal mode ─────────────────────────────────────────────

    def _terminal_normal_start(
        self, ts, rid, session, orig, routed, stream, input_tokens, icon, task
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            text.append(f"{ts} ", style=COLOR_META)
            text.append("▶ ", style=f"bold {COLOR_INFO}")
            text.append(f"{rid}  ", style=f"dim {session}")
            text.append(f"{_model_short(orig)}", style=f"dim {COLOR_INFO}")
            text.append(" → ", style=f"dim {COLOR_INFO}")
            text.append(f"{_model_short(routed)}", style=f"bold {COLOR_INFO}")
            if task:
                text.append(f"  {task}", style=f"dim {COLOR_WARN}")
            if input_tokens > 0:
                text.append(f"  {_fmt_tokens(input_tokens)} tks", style=COLOR_METRICS)
            if stream:
                text.append("  STREAM", style=f"dim {COLOR_INFO}")
            text.append(f"  {icon}", style=COLOR_META)
            console.print(text)
        else:
            parts = [f"{ts} ▶ {rid}  {_model_short(orig)} → {_model_short(routed)}"]
            if task:
                parts.append(task)
            if input_tokens > 0:
                parts.append(f"{_fmt_tokens(input_tokens)} tks")
            if stream:
                parts.append("STREAM")
            logger.info("  ".join(parts))

    def _terminal_normal_complete(
        self,
        ts, rid, session, status, orig, routed,
        in_tk, out_tk, think_tk, duration_ms, speed, stream, task, cascade,
        error="", cost=None,
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            icon = "✓" if status == "OK" else "✗"
            status_color = COLOR_SUCCESS if status == "OK" else COLOR_ERROR
            text.append(f"{ts} ", style=COLOR_META)
            text.append(f"{icon} ", style=f"bold {status_color}")
            text.append(f"{rid}  ", style=f"dim {session}")
            if orig and routed and orig != routed:
                text.append(f"{_model_short(orig)}", style=f"dim {COLOR_INFO}")
                text.append(" → ", style=f"dim {COLOR_INFO}")
            text.append(f"{_model_short(routed)}", style=f"bold {COLOR_INFO}")
            if task:
                text.append(f"  {task}", style=f"dim {COLOR_WARN}")
            parts = []
            if in_tk > 0 or out_tk > 0:
                parts.append(f"{_fmt_tokens(in_tk)}→{_fmt_tokens(out_tk)}t")
            if think_tk > 0:
                parts.append(f"💭{_fmt_tokens(think_tk)}")
            if duration_ms:
                parts.append(_fmt_duration(duration_ms))
            if speed:
                parts.append(speed)
            if parts:
                text.append(f"  {'  '.join(parts)}", style=COLOR_METRICS)
            if cost is not None:
                from src.services.models.cost_lookup import fmt_cost
                cost_str = fmt_cost(cost)
                cost_color = "green" if cost == 0.0 else "yellow" if cost < 0.005 else "red"
                text.append(f"  {cost_str}", style=cost_color)
            if cascade:
                text.append(f"  {cascade}", style=f"dim {COLOR_WARN}")
            if stream:
                text.append("  STREAM", style=f"dim {COLOR_INFO}")
            if error and status != "OK":
                text.append(f"\n{' ' * 10}ERROR: {error}", style=COLOR_ERROR)
            console.print(text)
        else:
            icon = "✓" if status == "OK" else "✗"
            parts = [f"{ts} {icon} {rid}"]
            if orig and routed and orig != routed:
                parts.append(f"{_model_short(orig)} → {_model_short(routed)}")
            else:
                parts.append(_model_short(routed))
            if task:
                parts.append(task)
            tok_parts = []
            if in_tk > 0 or out_tk > 0:
                tok_parts.append(f"{_fmt_tokens(in_tk)}→{_fmt_tokens(out_tk)}t")
            if think_tk > 0:
                tok_parts.append(f"think:{_fmt_tokens(think_tk)}")
            if duration_ms:
                tok_parts.append(_fmt_duration(duration_ms))
            if speed:
                tok_parts.append(speed)
            if tok_parts:
                parts.append("  ".join(tok_parts))
            if cost is not None:
                from src.services.models.cost_lookup import fmt_cost
                parts.append(fmt_cost(cost))
            if cascade:
                parts.append(cascade)
            if error and status != "OK":
                parts.append(f"ERROR: {error}")
            logger.info("  ".join(parts))

    def _terminal_normal_error(
        self,
        ts,
        rid,
        session,
        error,
        duration_ms,
        model_name,
        orig_model,
        provider,
        endpoint="",
        cascade_chain="",
        traceback_str="",
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            # META: timestamp
            text.append(f"{ts} ", style=COLOR_META)
            # ERROR: status icon
            text.append("✗ ", style=f"bold {COLOR_ERROR}")
            # SESSION: request ID
            text.append(f"{rid}  ", style=f"dim {session}")
            # INFO: routing
            if orig_model and model_name and orig_model != model_name:
                text.append(f"{_model_short(orig_model)}", style=f"dim {COLOR_INFO}")
                text.append(" → ", style=f"dim {COLOR_INFO}")
            if model_name:
                text.append(f"{_model_short(model_name)}", style=f"bold {COLOR_INFO}")
            # WARN: provider
            if provider:
                text.append(f" @{provider}", style=f"dim {COLOR_WARN}")
            # METRICS: duration
            if duration_ms:
                text.append(f"  {_fmt_duration(duration_ms)}", style=COLOR_METRICS)
            # WARN: endpoint
            if endpoint:
                text.append(f"  endpoint: {endpoint}", style=f"dim {COLOR_WARN}")
            # ERROR: full error on next line — always visible
            text.append(f"\n{' ' * 10}ERROR: {error}", style=COLOR_ERROR)
            if cascade_chain:
                text.append(
                    f"\n{' ' * 10}cascade: {cascade_chain}", style=f"dim {COLOR_WARN}"
                )
            if traceback_str:
                text.append(f"\n{' ' * 10}", style=f"dim {COLOR_ERROR}")
                for line in traceback_str.strip().split("\n")[-6:]:
                    text.append(f"{' ' * 10}{line}\n", style=f"dim {COLOR_ERROR}")
            console.print(text)
        else:
            parts = [f"{ts} ✗ {rid}"]
            if orig_model and model_name and orig_model != model_name:
                parts.append(f"{_model_short(orig_model)} → {_model_short(model_name)}")
            elif model_name:
                parts.append(_model_short(model_name))
            if provider:
                parts.append(f"@{provider}")
            if duration_ms:
                parts.append(_fmt_duration(duration_ms))
            logger.error("  ".join(parts) + f"\n          ERROR: {error}")

    # ── Terminal: Debug mode ─────────────────────────────────────────────

    def _terminal_debug_start(
        self,
        ts,
        rid,
        session,
        orig,
        routed,
        endpoint,
        stream,
        in_tk,
        ctx_lim,
        out_lim,
        msg_count,
        icon,
        task,
        cascade_info,
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            # META: timestamp
            text.append(f"{ts} ", style=COLOR_META)
            # INFO: routing arrow
            text.append("▶ ", style=f"bold {COLOR_INFO}")
            # SESSION: request ID
            text.append(f"{rid}  ", style=f"dim {session}")
            # INFO: full model names
            text.append(f"{orig}", style=f"dim {COLOR_INFO}")
            text.append(" → ", style=f"dim {COLOR_INFO}")
            text.append(f"{routed}", style=f"bold {COLOR_INFO}")
            if task:
                text.append(f"  {task}", style=f"dim {COLOR_WARN}")
            if endpoint:
                if provider_from_endpoint(endpoint):
                    text.append(
                        f" @{provider_from_endpoint(endpoint)}",
                        style=f"dim {COLOR_WARN}",
                    )
            meta_parts = []
            if in_tk > 0:
                meta_parts.append(f"{_fmt_tokens(in_tk)} input")
            if ctx_lim > 0:
                pct = int(in_tk / ctx_lim * 100) if in_tk > 0 else 0
                c = "green" if pct < 50 else "yellow" if pct < 80 else "red"
                meta_parts.append(f"ctx:{_fmt_tokens(ctx_lim)}({pct}%)")
            if out_lim > 0:
                meta_parts.append(f"out:{_fmt_tokens(out_lim)}")
            if msg_count > 0:
                meta_parts.append(f"{msg_count}msg")
            if meta_parts:
                text.append(f"  {'  '.join(meta_parts)}", style=COLOR_META)
            if stream:
                text.append("  STREAM", style=f"bold {COLOR_INFO}")
            text.append(f"  {icon}", style=COLOR_META)
            if cascade_info:
                text.append(
                    f"\n{' ' * 10}cascade: {cascade_info}", style=f"dim {COLOR_INFO}"
                )
            console.print(text)

    def _terminal_debug_complete(
        self,
        ts, rid, session, status, model_name,
        in_tk, out_tk, think_tk, duration_ms, speed, stream, task, cascade_chain,
        error, cost=None,
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            icon = "✓" if status == "OK" else "✗"
            status_color = COLOR_SUCCESS if status == "OK" else COLOR_ERROR
            text.append(f"{ts} ", style=COLOR_META)
            text.append(f"{icon} ", style=f"bold {status_color}")
            text.append(f"{rid}  ", style=f"dim {session}")
            text.append(f"{model_name}", style=f"bold {COLOR_INFO}")
            if task:
                text.append(f"  {task}", style=f"dim {COLOR_WARN}")
            parts = []
            if in_tk > 0 or out_tk > 0:
                parts.append(f"{in_tk}→{out_tk}t")
            if think_tk > 0:
                parts.append(f"💭{think_tk}")
            if duration_ms:
                parts.append(_fmt_duration(duration_ms))
            if speed:
                parts.append(speed)
            if parts:
                text.append(f"  {'  '.join(parts)}", style=COLOR_METRICS)
            if cost is not None:
                from src.services.models.cost_lookup import fmt_cost
                cost_color = "green" if cost == 0.0 else "yellow" if cost < 0.005 else "red"
                text.append(f"  {fmt_cost(cost)}", style=cost_color)
            if cascade_chain:
                text.append(f"\n{' ' * 10}{cascade_chain}", style=f"dim {COLOR_WARN}")
            if error:
                text.append(f"\n{' ' * 10}ERROR: {error}", style=COLOR_ERROR)
            console.print(text)

    def _terminal_debug_error(
        self,
        ts,
        rid,
        session,
        error,
        duration_ms,
        model_name,
        orig_model,
        provider,
        endpoint,
        cascade_chain,
        traceback_str,
    ):
        if RICH_AVAILABLE and console:
            text = Text()
            # META: timestamp
            text.append(f"{ts} ", style=COLOR_META)
            # ERROR: status icon
            text.append("✗ ", style=f"bold {COLOR_ERROR}")
            # SESSION: request ID
            text.append(f"{rid}  ", style=f"dim {session}")
            # INFO: routing
            if orig_model and model_name:
                text.append(f"{orig_model}", style=f"dim {COLOR_INFO}")
                text.append(" → ", style=f"dim {COLOR_INFO}")
            if model_name:
                text.append(f"{model_name}", style=f"bold {COLOR_INFO}")
            # WARN: provider
            if provider:
                text.append(f" @{provider}", style=f"dim {COLOR_WARN}")
            # METRICS: duration
            if duration_ms:
                text.append(f"  {_fmt_duration(duration_ms)}", style=COLOR_METRICS)
            if endpoint:
                text.append(
                    f"\n{' ' * 10}endpoint: {endpoint}", style=f"dim {COLOR_WARN}"
                )
            text.append(f"\n{' ' * 10}error: {error[:200]}", style=COLOR_ERROR)
            if cascade_chain:
                text.append(
                    f"\n{' ' * 10}cascade: {cascade_chain}", style=f"dim {COLOR_WARN}"
                )
            if DEBUG_MODE and traceback_str:
                text.append(f"\n{' ' * 10}", style=f"dim {COLOR_ERROR}")
                for line in traceback_str.strip().split("\n")[-8:]:
                    text.append(f"{' ' * 10}{line}\n", style=f"dim {COLOR_ERROR}")
            console.print(text)

    # ── File logging (plain text, always debug-level detail) ─────────────

    def _file_start(
        self,
        ts,
        rid,
        orig,
        routed,
        endpoint,
        stream,
        in_tk,
        ctx_lim,
        out_lim,
        msg_count,
        has_tools,
        has_reasoning,
        has_images,
        assignment_id,
        cascade_info,
    ):
        tags = []
        if assignment_id and assignment_id not in ("big", "middle", "small"):
            tags.append(assignment_id)
        if stream:
            tags.append("STREAM")
        if has_tools:
            tags.append("TOOLS")
        if has_reasoning:
            tags.append("REASONING")
        if has_images:
            tags.append("IMAGE")
        parts = [
            f"[{ts}]",
            f"▶{rid}",
            f"{orig} → {routed}",
            f"in={in_tk}",
            f"ctx={ctx_lim}",
            f"out={out_lim}",
            f"msgs={msg_count}",
        ]
        if tags:
            parts.append(f"[{' '.join(tags)}]")
        if cascade_info:
            parts.append(f"cascade={cascade_info}")
        _log_file(" ".join(parts))

    def _file_complete(
        self,
        ts,
        rid,
        status,
        orig,
        routed,
        in_tk,
        out_tk,
        think_tk,
        duration_ms,
        speed,
        stream,
        assignment_id,
        cascade_chain,
        error,
    ):
        parts = [
            f"[{ts}]",
            f"{'OK' if status == 'OK' else 'ERR'} {rid}",
            f"{orig} → {routed}",
            f"in={in_tk}",
            f"out={out_tk}",
        ]
        if think_tk > 0:
            parts.append(f"think={think_tk}")
        if duration_ms:
            parts.append(_fmt_duration(duration_ms))
        if speed:
            parts.append(speed)
        if cascade_chain:
            parts.append(f"cascade={cascade_chain}")
        if error:
            parts.append(f"ERROR: {error}")
        _log_file(" ".join(parts))

    def _file_error(
        self,
        ts,
        rid,
        error,
        duration_ms,
        model_name,
        orig_model,
        provider,
        endpoint,
        cascade_chain,
        traceback_str,
    ):
        parts = [
            f"[{ts}]",
            f"ERR {rid}",
            f"{orig_model} → {model_name}",
        ]
        if provider:
            parts.append(f"@{provider}")
        if endpoint:
            parts.append(f"endpoint={endpoint}")
        if duration_ms:
            parts.append(_fmt_duration(duration_ms))
        parts.append(f"error={error[:200]}")
        if cascade_chain:
            parts.append(f"cascade={cascade_chain}")
        if traceback_str:
            parts.append(f"traceback={traceback_str[:200]}")
        _log_file(" ".join(parts))


def provider_from_endpoint(endpoint: str) -> str:
    """Extract provider name from endpoint URL."""
    if not endpoint:
        return ""
    ep = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
    if "openrouter" in ep:
        return "openrouter"
    if "opencode" in ep:
        return "opencode_go"
    if "anthropic" in ep:
        return "anthropic"
    if "openai" in ep:
        return "openai"
    if "nvidia" in ep:
        return "nvidia"
    if "google" in ep:
        return "google"
    return ep


# ── Singleton ─────────────────────────────────────────────────────────────────
proxy_logger = ProxyLogger()
