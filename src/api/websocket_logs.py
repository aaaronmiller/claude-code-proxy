"""WebSocket endpoints for live log streaming and real-time updates."""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

# ═══════════════════════════════════════════════════════════════════════════════
# LOG BROADCAST SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class LogBroadcaster:
    """
    Manages WebSocket connections and broadcasts log messages to all connected clients.
    Acts as a central hub for log events from the proxy.
    """
    
    def __init__(self, max_history: int = 100):
        self.connections: Set[WebSocket] = set()
        self.history: deque = deque(maxlen=max_history)
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.connections.add(websocket)
        # Send recent history to new connection
        for log_entry in self.history:
            try:
                await websocket.send_json(log_entry)
            except Exception:
                pass
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.connections.discard(websocket)
    
    async def broadcast(self, log_entry: Dict[str, Any]):
        """Broadcast a log entry to all connected clients."""
        log_entry["timestamp"] = datetime.now().isoformat()
        self.history.append(log_entry)
        
        # Send to all connections
        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(log_entry)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected
        async with self._lock:
            self.connections -= disconnected
    
    def log(self, level: str, message: str, **kwargs):
        """Synchronous log method that schedules async broadcast."""
        log_entry = {
            "level": level,
            "message": message,
            **kwargs
        }
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(log_entry))
            else:
                loop.run_until_complete(self.broadcast(log_entry))
        except RuntimeError:
            # No event loop, just store in history
            log_entry["timestamp"] = datetime.now().isoformat()
            self.history.append(log_entry)
    
    @property
    def client_count(self) -> int:
        return len(self.connections)


# Global broadcaster instance
log_broadcaster = LogBroadcaster()

# Cascade event history for observability and monitor stats
_cascade_events: deque = deque(maxlen=500)


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.websocket("/api/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for live log streaming.
    
    Clients receive JSON messages with format:
    {
        "timestamp": "2025-12-28T07:30:00.000000",
        "level": "info|warning|error|debug",
        "message": "Log message text",
        "model": "optional model name",
        "request_id": "optional request id",
        ...additional context
    }
    """
    await log_broadcaster.connect(websocket)
    try:
        while True:
            # Keep connection alive, optionally receive client messages
            data = await websocket.receive_text()
            # Handle client commands if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await log_broadcaster.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════════════════
# LOG HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def log_request(
    request_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    status: str = "success",
    error: Optional[str] = None
):
    """Log a request completion."""
    log_broadcaster.log(
        level="info" if status == "success" else "error",
        message=f"Request completed: {model}",
        request_id=request_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        status=status,
        error=error
    )


def _cascade_terminal(
    action: str,
    from_model: Optional[str],
    to_model: Optional[str],
    model: str,
    reason: Optional[str],
    error: Optional[str],
    request_id: Optional[str],
    tier: Optional[str],
) -> None:
    """Emit a rich terminal line for cascade events. Called synchronously inside log_cascade()."""
    try:
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H:%M:%S")
        rid = (request_id or "")[:6]

        # Error classification → short label + color.
        # Falls back to `reason` when no error string is provided (e.g. proactive
        # fallback attempts that switch model before a failure occurs).
        _err_low = (error or "").lower()
        _reason_low = (reason or "").lower()
        if "401" in _err_low or "unauthorized" in _err_low or "auth" in _err_low:
            err_tag, err_color = "401 UNAUTH", "bold red"
        elif "429" in _err_low or "rate" in _err_low or "limit" in _err_low:
            err_tag, err_color = "429 RATELIM", "bold yellow"
        elif "503" in _err_low or "502" in _err_low or "500" in _err_low or "504" in _err_low or "server error" in _err_low or "overload" in _err_low:
            err_tag, err_color = "5xx SERVER", "bold yellow"
        elif "timeout" in _err_low or "timed out" in _err_low:
            err_tag, err_color = "TIMEOUT", "bold yellow"
        elif "400" in _err_low or "bad request" in _err_low:
            err_tag, err_color = "400 BADREQ", "bold red"
        elif "context" in _err_low or "too long" in _err_low:
            err_tag, err_color = "CTX LIMIT", "bold magenta"
        elif "ssl" in _err_low or "cert" in _err_low:
            err_tag, err_color = "SSL ERROR", "bold red"
        elif "connect" in _err_low or "refused" in _err_low:
            err_tag, err_color = "CONN FAIL", "bold red"
        elif error:
            err_tag, err_color = "FAIL", "red"
        # No error → use the reason as the tag (e.g. "fallback_attempt", "alibaba_rampup")
        elif "rate_limit" in _reason_low or "ratelim" in _reason_low:
            err_tag, err_color = "RATELIM", "bold yellow"
        elif "fallback" in _reason_low or "cascade" in _reason_low:
            err_tag, err_color = "CASCADE", "dim cyan"
        elif "context" in _reason_low or "ctx" in _reason_low:
            err_tag, err_color = "CTX", "bold magenta"
        elif reason:
            err_tag, err_color = reason.upper()[:12], "dim yellow"
        else:
            err_tag, err_color = "RETRY", "dim"

        # Short model names
        def _short(m: Optional[str]) -> str:
            if not m:
                return ""
            parts = m.split("/")
            return parts[-1] if len(parts) > 1 else m

        try:
            from rich.console import Console as _Console
            from rich.text import Text as _Text
            _con = _Console()

            if action == "switch" and from_model and to_model:
                t = _Text()
                t.append(f"{ts} ", style="dim white")
                t.append("↷ ", style="bold yellow")
                if rid:
                    t.append(f"{rid}  ", style="dim cyan")
                t.append(_short(from_model), style="dim white")
                t.append(" [", style="dim")
                t.append(err_tag, style=err_color)
                t.append("]", style="dim")
                t.append(" → ", style="yellow")
                t.append(_short(to_model), style="bold cyan")
                if tier:
                    t.append(f"  [{tier}]", style="dim yellow")
                if reason:
                    t.append(f"  {reason}", style="dim yellow")
                _con.print(t)

            elif action == "exhausted":
                t = _Text()
                t.append(f"{ts} ", style="dim white")
                t.append("✗✗ ", style="bold red")
                if rid:
                    t.append(f"{rid}  ", style="dim cyan")
                t.append("ALL CASCADE MODELS FAILED", style="bold red")
                t.append(f"  primary={_short(model)}", style="dim red")
                if tier:
                    t.append(f"  [{tier}]", style="dim red")
                _con.print(t)
                if error:
                    _con.print(f"{'':>10}last error: {error[:120]}", style="dim red")

            elif action == "success" and from_model:
                t = _Text()
                t.append(f"{ts} ", style="dim white")
                t.append("↷✓ ", style="bold green")
                if rid:
                    t.append(f"{rid}  ", style="dim cyan")
                t.append("cascade success: ", style="dim green")
                t.append(_short(model), style="bold green")
                _con.print(t)

        except Exception:
            # Plain text fallback if rich unavailable
            import logging as _log
            _logger = _log.getLogger("src.core.cascade")
            if action == "switch" and from_model and to_model:
                _logger.warning(
                    f"CASCADE ↷ {rid}  {_short(from_model)} [{err_tag}] → {_short(to_model)}"
                    + (f"  [{tier}]" if tier else "")
                )
            elif action == "exhausted":
                _logger.error(f"CASCADE ✗✗ {rid}  ALL FAILED  primary={_short(model)}")
    except Exception:
        pass  # Never let terminal output break the request path


def log_cascade(
    model: str,
    action: str,
    tier: Optional[str] = None,
    reason: Optional[str] = None,
    from_model: Optional[str] = None,
    to_model: Optional[str] = None,
    request_id: Optional[str] = None,
    retry_count: int = 0,
    error: Optional[str] = None
):
    """Log a cascade event — both to the WebSocket stream and rich terminal."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "action": action,
        "tier": tier,
        "reason": reason,
        "from_model": from_model,
        "to_model": to_model,
        "request_id": request_id,
        "retry_count": retry_count,
        "error": error,
    }
    _cascade_events.append(event)

    # Mirror cascade switches to Prometheus (single choke point for all switch sites).
    # Best-effort: a metrics failure must never break cascade logging.
    if action == "switch":
        try:
            from src.api.metrics_api import record_cascade_switch

            record_cascade_switch(from_model or model, to_model or "", reason or "")
        except Exception:
            pass

    message = f"Cascade {action}: {model}"
    if from_model and to_model:
        message = f"Cascade {action}: {from_model} -> {to_model}"
    if reason:
        message = f"{message} ({reason})"

    # ── Rich terminal output ──────────────────────────────────────────────
    # Cascade switches are exactly the events users need to see: which model
    # failed, why, and what we're trying next. Previously these were buried
    # in DEBUG logs or never shown at all.
    _cascade_terminal(action, from_model, to_model, model, reason, error, request_id, tier)

    log_broadcaster.log(
        level="warning" if action == "switch" else "info",
        message=message,
        event_type="cascade",
        model=model,
        action=action,
        tier=tier,
        reason=reason,
        from_model=from_model,
        to_model=to_model,
        request_id=request_id,
        retry_count=retry_count,
        error=error
    )

    # Mirror into the Web UI logs stream (/ws/logs) if available.
    try:
        from src.api.websocket_dashboard import logs_broadcaster

        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                logs_broadcaster.broadcast(
                    f"[cascade] {message}",
                    "warning" if action == "switch" else "info",
                )
            )
    except Exception:
        # Keep cascade path resilient; observability must not break requests.
        pass


def get_cascade_stats(limit: int = 20) -> Dict[str, Any]:
    """Get aggregate cascade metrics and recent events for monitor UI."""
    events = list(_cascade_events)
    if not events:
        return {
            "total_events": 0,
            "switches": 0,
            "retries": 0,
            "successes": 0,
            "exhausted": 0,
            "success_rate": 0.0,
            "reasons": {},
            "recent": [],
        }

    switches = sum(1 for e in events if e.get("action") == "switch")
    retries = sum(1 for e in events if e.get("action") == "retry")
    successes = sum(1 for e in events if e.get("action") == "success")
    exhausted = sum(1 for e in events if e.get("action") == "exhausted")

    reasons: Dict[str, int] = {}
    for event in events:
        reason = event.get("reason")
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1

    completed_attempts = successes + exhausted
    success_rate = (successes / completed_attempts) if completed_attempts > 0 else 0.0

    return {
        "total_events": len(events),
        "switches": switches,
        "retries": retries,
        "successes": successes,
        "exhausted": exhausted,
        "success_rate": round(success_rate * 100, 1),
        "reasons": reasons,
        "recent": list(reversed(events[-max(1, limit):])),
    }


def log_crosstalk(
    session_id: str,
    turn: int,
    speaker: str,
    listener: str,
    message_preview: str
):
    """Log a crosstalk turn."""
    log_broadcaster.log(
        level="info",
        message=f"Crosstalk turn {turn}: {speaker} → {listener}",
        session_id=session_id,
        turn=turn,
        speaker=speaker,
        listener=listener,
        preview=message_preview[:100] if len(message_preview) > 100 else message_preview
    )
