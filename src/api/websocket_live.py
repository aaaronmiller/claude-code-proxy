"""
WebSocket Live Metrics & Real-time Monitoring

Provides real-time updates for:
- Live metrics (requests/second, cost, tokens)
- Request feed (streaming requests)
- Alert notifications
- Crosstalk session progress

Author: AI Architect
Date: 2026-01-04
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from pathlib import Path

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker

router = APIRouter()

# Active connections
active_connections: Set[WebSocket] = set()

# Live metrics cache
metrics_cache = {
    "requests_per_second": 0,
    "tokens_per_second": 0,
    "cost_per_second": 0.0,
    "active_requests": 0,
    "error_rate": 0.0,
    "model_distribution": {},
    "timestamp": datetime.utcnow().isoformat()
}

# Request feed buffer (last 100 requests)
request_feed_buffer: List[Dict] = []

# Alert queue
alert_queue: List[Dict] = []

# Crosstalk session trackers
crosstalk_sessions: Dict[str, Dict] = {}


class LiveMetricsManager:
    """Manages real-time metrics calculation and broadcasting"""

    def __init__(self):
        self._running = False
        self._task = None

    async def start(self):
        """Start the metrics calculation loop"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._metrics_loop())
        logger.info("Live metrics manager started")

    async def stop(self):
        """Stop the metrics calculation loop"""
        self._running = False
        if self._task:
            await self._task
        logger.info("Live metrics manager stopped")

    async def _metrics_loop(self):
        """Calculate and update live metrics every second"""
        while self._running:
            try:
                if usage_tracker.enabled:
                    # Calculate metrics from last 60 seconds
                    metrics = await self._calculate_metrics()
                    metrics_cache.update(metrics)

                    # Broadcast to all connected clients
                    await self._broadcast_metrics()

                    # Check for alerts
                    await self._check_alerts()

                await asyncio.sleep(1)  # Update every second

            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _calculate_metrics(self) -> Dict:
        """Calculate real-time metrics from database"""
        try:
            import sqlite3
            import time

            conn = sqlite3.connect(usage_tracker.db_path)
            cursor = conn.cursor()

            # Calculate from last 60 seconds
            since = (datetime.utcnow().timestamp() - 60)

            # Requests per second
            cursor.execute("""
                SELECT COUNT(*) FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
            """, (since,))
            requests_60s = cursor.fetchone()[0]
            rps = requests_60s / 60.0

            # Tokens per second
            cursor.execute("""
                SELECT SUM(total_tokens) FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
            """, (since,))
            tokens_60s = cursor.fetchone()[0] or 0
            tps = tokens_60s / 60.0

            # Cost per second
            cursor.execute("""
                SELECT SUM(estimated_cost) FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
            """, (since,))
            cost_60s = cursor.fetchone()[0] or 0
            cps = cost_60s / 60.0

            # Active requests (last 5 seconds)
            cursor.execute("""
                SELECT COUNT(*) FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
                AND status = 'active'
            """, (time.time() - 5,))
            active = cursor.fetchone()[0]

            # Error rate (last 60 seconds)
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                    COUNT(*) as total
                FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
            """, (since,))
            result = cursor.fetchone()
            errors = result[0] or 0
            total = result[1] or 1
            error_rate = (errors / total) * 100

            # Model distribution (last 60 seconds)
            cursor.execute("""
                SELECT routed_model, COUNT(*) as count
                FROM api_requests
                WHERE timestamp >= datetime(?, 'unixepoch')
                GROUP BY routed_model
                ORDER BY count DESC
                LIMIT 10
            """, (since,))
            model_dist = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                "requests_per_second": round(rps, 2),
                "tokens_per_second": round(tps, 2),
                "cost_per_second": round(cps, 4),
                "active_requests": active,
                "error_rate": round(error_rate, 2),
                "model_distribution": model_dist,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return metrics_cache  # Return previous cache on error

    async def _broadcast_metrics(self):
        """Broadcast metrics to all connected clients"""
        if not active_connections:
            return

        message = {
            "type": "metrics",
            "data": metrics_cache,
            "timestamp": datetime.utcnow().isoformat()
        }

        disconnected = set()
        for connection in active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)

        # Remove disconnected clients
        for conn in disconnected:
            active_connections.discard(conn)

    async def _check_alerts(self):
        """Check alert rules and trigger notifications"""
        if not usage_tracker.enabled:
            return

        try:
            import sqlite3
            conn = sqlite3.connect(usage_tracker.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get active alert rules
            cursor.execute("""
                SELECT * FROM alert_rules
                WHERE enabled = 1
                AND (muted_until IS NULL OR muted_until < datetime('now'))
            """)

            for rule in cursor.fetchall():
                # Parse condition
                condition = json.loads(rule["condition_json"])
                metric = condition["metric"]
                operator = condition["operator"]
                threshold = condition["threshold"]
                window = condition.get("window_minutes", 5)

                # Get current metric value
                current_value = self._get_metric_value(metric, window)

                # Check condition
                if self._evaluate_condition(current_value, operator, threshold):
                    # Check cooldown
                    if self._in_cooldown(rule, cursor):
                        continue

                    # Trigger alert
                    await self._trigger_alert(rule, current_value, cursor)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Alert check error: {e}")

    def _get_metric_value(self, metric: str, window_minutes: int) -> float:
        """Get current value for a metric"""
        since = datetime.utcnow().timestamp() - (window_minutes * 60)

        try:
            import sqlite3
            conn = sqlite3.connect(usage_tracker.db_path)
            cursor = conn.cursor()

            if metric == "cost":
                cursor.execute("""
                    SELECT SUM(estimated_cost) FROM api_requests
                    WHERE timestamp >= datetime(?, 'unixepoch')
                """, (since,))
                return (cursor.fetchone()[0] or 0) * (1440 / window_minutes)  # Project to daily

            elif metric == "latency":
                cursor.execute("""
                    SELECT AVG(duration_ms) FROM api_requests
                    WHERE timestamp >= datetime(?, 'unixepoch')
                """, (since,))
                return cursor.fetchone()[0] or 0

            elif metric == "error_rate":
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                    FROM api_requests
                    WHERE timestamp >= datetime(?, 'unixepoch')
                """, (since,))
                return cursor.fetchone()[0] or 0

            elif metric == "token_count":
                cursor.execute("""
                    SELECT SUM(total_tokens) FROM api_requests
                    WHERE timestamp >= datetime(?, 'unixepoch')
                """, (since,))
                return cursor.fetchone()[0] or 0

            elif metric == "request_count":
                cursor.execute("""
                    SELECT COUNT(*) FROM api_requests
                    WHERE timestamp >= datetime(?, 'unixepoch')
                """, (since,))
                return cursor.fetchone()[0] or 0

            conn.close()

        except:
            pass

        return 0

    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "=":
            return abs(value - threshold) < 0.01
        return False

    def _in_cooldown(self, rule: sqlite3.Row, cursor) -> bool:
        """Check if rule is in cooldown period"""
        if not rule["last_triggered"]:
            return False

        cooldown_minutes = rule["cooldown_minutes"] or 5
        last_trigger = datetime.fromisoformat(rule["last_triggered"])
        cooldown_until = last_trigger.timestamp() + (cooldown_minutes * 60)

        return datetime.utcnow().timestamp() < cooldown_until

    async def _trigger_alert(self, rule: sqlite3.Row, value: float, cursor):
        """Trigger alert and send notifications"""
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{rule['id']}"

        # Update rule
        cursor.execute("""
            UPDATE alert_rules
            SET last_triggered = ?, trigger_count = trigger_count + 1
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), rule["id"]))

        # Log to history
        alert_data = {
            "metric_value": value,
            "threshold": json.loads(rule["condition_json"])["threshold"],
            "window_minutes": json.loads(rule["condition_json"]).get("window_minutes", 5)
        }

        cursor.execute("""
            INSERT INTO alert_history
            (id, rule_id, rule_name, triggered_at, alert_data_json, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (alert_id, rule["id"], rule["name"], datetime.utcnow().isoformat(),
              json.dumps(alert_data), rule["priority"]))

        # Send notifications
        actions = json.loads(rule["actions_json"])

        # In-app notification (broadcast via WebSocket)
        if actions.get("in_app"):
            await self._broadcast_alert({
                "type": "alert",
                "alert_id": alert_id,
                "rule_name": rule["name"],
                "severity": rule["priority"],
                "message": f"{rule['name']}: {value} (threshold: {alert_data['threshold']})",
                "timestamp": datetime.utcnow().isoformat()
            })

        # Webhook (async)
        if actions.get("webhook"):
            asyncio.create_task(self._send_webhook(actions["webhook"], {
                "alert_id": alert_id,
                "rule": rule["name"],
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }))

        logger.info(f"Alert triggered: {rule['name']} - {value}")

    async def _broadcast_alert(self, alert: Dict):
        """Broadcast alert to all connected clients"""
        disconnected = set()
        for connection in active_connections:
            try:
                await connection.send_json(alert)
            except:
                disconnected.add(connection)

        for conn in disconnected:
            active_connections.discard(conn)

    async def _send_webhook(self, url: str, payload: Dict):
        """Send webhook notification"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.warning(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")


# Global manager instance
metrics_manager = LiveMetricsManager()


@router.websocket("/ws/live")
async def websocket_live_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for live metrics

    Client receives:
    - metrics: Real-time system metrics (1Hz)
    - alerts: Alert notifications when triggered
    - request_feed: Streaming request events

    Client can send:
    - subscribe: Subscribe to specific feeds
    - ping: Connection health check
    """
    await websocket.accept()
    active_connections.add(websocket)

    try:
        # Send initial metrics
        await websocket.send_json({
            "type": "metrics",
            "data": metrics_cache,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send recent request feed
        if request_feed_buffer:
            await websocket.send_json({
                "type": "request_feed",
                "data": request_feed_buffer[-10:],  # Last 10 requests
                "timestamp": datetime.utcnow().isoformat()
            })

        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

                elif data.get("type") == "subscribe":
                    # Handle subscription to specific feeds
                    feeds = data.get("feeds", ["metrics"])
                    await websocket.send_json({
                        "type": "subscribed",
                        "feeds": feeds,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except TimeoutError:
                continue

    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        active_connections.discard(websocket)
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/crosstalk/{session_id}")
async def websocket_crosstalk_session(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time Crosstalk session monitoring

    Client receives:
    - session_status: Current session state
    - round_update: Progress on each round
    - cost_update: Running cost totals

    Path params:
        session_id: Crosstalk session ID
    """
    await websocket.accept()

    # Track this connection for the specific session
    if session_id not in crosstalk_sessions:
        crosstalk_sessions[session_id] = {
            "connections": set(),
            "last_update": None,
            "cost": 0,
            "tokens": 0,
            "round": 0
        }

    crosstalk_sessions[session_id]["connections"].add(websocket)

    try:
        # Send current session state if available
        session_data = crosstalk_sessions.get(session_id)
        if session_data:
            await websocket.send_json({
                "type": "session_status",
                "data": session_data,
                "timestamp": datetime.utcnow().isoformat()
            })

        # Listen for updates
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        if session_id in crosstalk_sessions:
            crosstalk_sessions[session_id]["connections"].discard(websocket)

    except Exception as e:
        logger.error(f"Crosstalk WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# Event handlers for integration with existing systems
async def broadcast_request_event(request_data: Dict):
    """Broadcast new request event to all live feed subscribers"""
    # Add to buffer
    request_feed_buffer.append({
        **request_data,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Keep buffer size manageable
    if len(request_feed_buffer) > 100:
        request_feed_buffer.pop(0)

    # Broadcast to all connections
    message = {
        "type": "request_event",
        "data": request_data,
        "timestamp": datetime.utcnow().isoformat()
    }

    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.add(connection)

    for conn in disconnected:
        active_connections.discard(conn)


async def update_crosstalk_session(session_id: str, round_data: Dict):
    """Update crosstalk session with new round data"""
    if session_id not in crosstalk_sessions:
        crosstalk_sessions[session_id] = {
            "connections": set(),
            "last_update": None,
            "cost": 0,
            "tokens": 0,
            "round": 0
        }

    session = crosstalk_sessions[session_id]
    session["last_update"] = datetime.utcnow().isoformat()
    session["round"] = round_data.get("round", session["round"] + 1)
    session["cost"] += round_data.get("cost", 0)
    session["tokens"] += round_data.get("tokens", 0)

    # Broadcast to all session connections
    message = {
        "type": "round_update",
        "data": round_data,
        "session_summary": {
            "round": session["round"],
            "total_cost": session["cost"],
            "total_tokens": session["tokens"]
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    disconnected = set()
    for connection in session["connections"]:
        try:
            await connection.send_json(message)
        except:
            disconnected.add(connection)

    for conn in disconnected:
        session["connections"].discard(conn)


# Start metrics manager on module load
async def start_live_metrics():
    """Initialize live metrics system"""
    await metrics_manager.start()


async def stop_live_metrics():
    """Stop live metrics system"""
    await metrics_manager.stop()


# Export for main app startup
__all__ = [
    "router",
    "metrics_manager",
    "start_live_metrics",
    "stop_live_metrics",
    "broadcast_request_event",
    "update_crosstalk_session"
]