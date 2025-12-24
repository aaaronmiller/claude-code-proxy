"""
WebSocket Dashboard API

Provides real-time dashboard updates via WebSocket connections.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from typing import Set
import json
import asyncio
from pathlib import Path
from src.core.logging import logger

router = APIRouter()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


class DashboardBroadcaster:
    """Broadcasts dashboard updates to all connected clients"""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection"""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return

        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.connections.discard(conn)


# Global broadcaster instance
dashboard_broadcaster = DashboardBroadcaster()


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await dashboard_broadcaster.connect(websocket)

    try:
        # Send initial state
        from src.dashboard.dashboard_hooks import dashboard_hooks

        initial_state = {
            'type': 'initial_state',
            'data': dashboard_hooks.get_stats()
        }
        await websocket.send_json(initial_state)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client (e.g., ping/pong)
                data = await websocket.receive_text()

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    finally:
        dashboard_broadcaster.disconnect(websocket)


@router.get("/dashboard")
async def serve_websocket_dashboard():
    """Serve the WebSocket dashboard HTML page"""
    dashboard_file = Path(__file__).parent.parent.parent / "static" / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    return {"error": "Dashboard page not found"}


async def broadcast_dashboard_update(update_type: str, data: dict):
    """
    Broadcast a dashboard update to all connected clients.

    Args:
        update_type: Type of update (e.g., 'request_start', 'request_complete', 'stats_update')
        data: Update data
    """
    message = {
        'type': update_type,
        'data': data,
        'timestamp': asyncio.get_event_loop().time()
    }
    await dashboard_broadcaster.broadcast(message)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE LOGS WEBSOCKET - For Web UI
# ═══════════════════════════════════════════════════════════════════════════════

class LogsBroadcaster:
    """Broadcasts log messages to connected web UI clients"""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection"""
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"Logs WebSocket client connected. Total: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.connections.discard(websocket)
        logger.info(f"Logs WebSocket client disconnected. Total: {len(self.connections)}")

    async def broadcast(self, message: str, level: str = "info"):
        """Broadcast a log message to all connected clients"""
        if not self.connections:
            return

        payload = {
            "message": message,
            "level": level
        }

        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.connections.discard(conn)


# Global logs broadcaster instance
logs_broadcaster = LogsBroadcaster()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live request logs (Web UI)"""
    await logs_broadcaster.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "message": "Connected to live log stream",
            "level": "info"
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception:
                break

    finally:
        logs_broadcaster.disconnect(websocket)


async def broadcast_log(message: str, level: str = "info"):
    """
    Broadcast a log message to all connected Web UI clients.

    Args:
        message: Log message text
        level: Log level (info, warning, error, success)
    """
    await logs_broadcaster.broadcast(message, level)
