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
    """Log a cascade event."""
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

    message = f"Cascade {action}: {model}"
    if from_model and to_model:
        message = f"Cascade {action}: {from_model} -> {to_model}"
    if reason:
        message = f"{message} ({reason})"

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
