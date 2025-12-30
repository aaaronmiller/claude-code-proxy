"""WebSocket endpoints for live log streaming and real-time updates."""

import asyncio
from collections import deque
from datetime import datetime
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
    retry_count: int = 0,
    error: Optional[str] = None
):
    """Log a cascade event."""
    log_broadcaster.log(
        level="warning" if action == "switch" else "info",
        message=f"Cascade {action}: {model}",
        model=model,
        action=action,
        retry_count=retry_count,
        error=error
    )


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
