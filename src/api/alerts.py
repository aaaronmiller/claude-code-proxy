"""
Alert Management API - Phase 3

Provides endpoints for:
- Creating, updating, deleting alert rules
- Managing alert history
- Bulk operations on alerts
- Alert statistics

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import json

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker
from src.services.alert_engine import alert_engine

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# ALERT RULE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/alerts/rules")
async def create_alert_rule(rule_data: Dict[str, Any]):
    """Create a new alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)

        # Generate ID
        rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = conn.execute("""
            INSERT INTO alert_rules (
                id, name, description, condition_json, condition_logic,
                actions_json, cooldown_minutes, priority, time_window,
                is_active, created_at, created_by, trigger_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule_id,
            rule_data.get("name", "Unnamed Rule"),
            rule_data.get("description", ""),
            json.dumps(rule_data.get("conditions", [])),
            json.dumps(rule_data.get("logic", None)),
            json.dumps(rule_data.get("actions", {"channels": ["in_app"]})),
            rule_data.get("cooldown_minutes", 5),
            rule_data.get("priority", 2),
            rule_data.get("time_window", 5),
            1,  # Active by default
            datetime.utcnow().isoformat(),
            rule_data.get("created_by", "web_ui"),
            0
        ))

        conn.commit()
        conn.close()

        return {"success": True, "rule_id": rule_id, "message": "Rule created successfully"}

    except Exception as e:
        logger.error(f"Create alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts/rules")
async def get_alert_rules(include_inactive: bool = False):
    """Get all alert rules"""
    try:
        if not usage_tracker.enabled:
            return {"rules": []}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM alert_rules"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY priority ASC, created_at DESC"

        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()

        rules = []
        for row in rows:
            rule = dict(row)
            # Parse JSON fields
            try:
                rule["conditions"] = json.loads(rule.get("condition_json", "[]"))
                rule["logic"] = json.loads(rule.get("condition_logic", "null"))
                rule["actions"] = json.loads(rule.get("actions_json", "{}"))
            except:
                pass
            rules.append(rule)

        return {"rules": rules, "count": len(rules)}

    except Exception as e:
        logger.error(f"Get alert rules failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts/rules/{rule_id}")
async def get_alert_rule(rule_id: str):
    """Get specific alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")

        rule = dict(row)
        try:
            rule["conditions"] = json.loads(rule.get("condition_json", "[]"))
            rule["logic"] = json.loads(rule.get("condition_logic", "null"))
            rule["actions"] = json.loads(rule.get("actions_json", "{}"))
        except:
            pass

        return rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: str, rule_data: Dict[str, Any]):
    """Update alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        # Check if rule exists
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("SELECT id FROM alert_rules WHERE id = ?", (rule_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Rule not found")

        # Update rule
        updates = []
        params = []

        if "name" in rule_data:
            updates.append("name = ?")
            params.append(rule_data["name"])
        if "description" in rule_data:
            updates.append("description = ?")
            params.append(rule_data["description"])
        if "conditions" in rule_data:
            updates.append("condition_json = ?")
            params.append(json.dumps(rule_data["conditions"]))
        if "logic" in rule_data:
            updates.append("condition_logic = ?")
            params.append(json.dumps(rule_data["logic"]))
        if "actions" in rule_data:
            updates.append("actions_json = ?")
            params.append(json.dumps(rule_data["actions"]))
        if "cooldown_minutes" in rule_data:
            updates.append("cooldown_minutes = ?")
            params.append(rule_data["cooldown_minutes"])
        if "priority" in rule_data:
            updates.append("priority = ?")
            params.append(rule_data["priority"])
        if "time_window" in rule_data:
            updates.append("time_window = ?")
            params.append(rule_data["time_window"])

        if not updates:
            conn.close()
            return {"success": False, "message": "No updates provided"}

        params.append(rule_id)
        query = f"UPDATE alert_rules SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()

        return {"success": True, "rule_id": rule_id, "message": "Rule updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {"success": True, "rule_id": rule_id, "message": "Rule deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/rules/{rule_id}/toggle")
async def toggle_alert_rule(rule_id: str):
    """Enable or disable alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)

        # Get current state
        cursor = conn.execute("SELECT is_active FROM alert_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Rule not found")

        new_state = 1 - row[0]  # Toggle

        cursor.execute("UPDATE alert_rules SET is_active = ? WHERE id = ?", (new_state, rule_id))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "rule_id": rule_id,
            "is_active": bool(new_state),
            "message": f"Rule {'enabled' if new_state else 'disabled'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/rules/{rule_id}/test")
async def test_alert_rule(rule_id: str):
    """Test alert rule by simulating with current metrics"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        # Get rule
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Get current metrics
        metrics = await alert_engine.get_current_metrics(row["time_window"])

        # Check conditions
        from src.services.alert_engine import AlertRule
        rule = AlertRule(**dict(row))

        triggered, alert_data = alert_engine.check_conditions(rule, metrics)

        return {
            "triggered": triggered,
            "metrics": metrics,
            "alert_data": alert_data,
            "rule_name": rule.name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test alert rule failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ALERT HISTORY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/alerts/history")
async def get_alert_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    status: Optional[str] = None,  # resolved, unresolved
    rule_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get alert history with filtering"""
    try:
        if not usage_tracker.enabled:
            return {"alerts": [], "count": 0}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        query = """
            SELECT
                h.*,
                r.description as rule_description,
                r.priority as rule_priority
            FROM alert_history h
            LEFT JOIN alert_rules r ON h.rule_id = r.id
            WHERE 1=1
        """
        params = []

        if severity:
            query += " AND h.severity = ?"
            params.append(severity)
        if status == "resolved":
            query += " AND h.resolved = 1"
        elif status == "unresolved":
            query += " AND h.resolved = 0"
        if rule_id:
            query += " AND h.rule_id = ?"
            params.append(rule_id)
        if start_date:
            query += " AND h.triggered_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND h.triggered_at <= ?"
            params.append(end_date)

        query += " ORDER BY h.triggered_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        # Count total for pagination
        count_query = query.replace(
            "SELECT h.*, r.description as rule_description, r.priority as rule_priority",
            "SELECT COUNT(*) as total"
        )
        count_query = count_query.split("ORDER BY")[0]  # Remove ordering
        count_cursor = conn.execute(count_query, params[:-2])  # Remove limit/offset
        total = count_cursor.fetchone()["total"]

        conn.close()

        alerts = []
        for row in rows:
            alert = dict(row)
            try:
                alert["alert_data"] = json.loads(row.get("alert_data_json", "{}"))
            except:
                alert["alert_data"] = {}
            alerts.append(alert)

        return {
            "alerts": alerts,
            "count": len(alerts),
            "total": total,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total
            }
        }

    except Exception as e:
        logger.error(f"Get alert history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/alerts/history/{alert_id}")
async def get_alert_detail(alert_id: str):
    """Get specific alert detail"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT h.*, r.description as rule_description
            FROM alert_history h
            LEFT JOIN alert_rules r ON h.rule_id = r.id
            WHERE h.id = ?
        """, (alert_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert = dict(row)
        try:
            alert["alert_data"] = json.loads(row.get("alert_data_json", "{}"))
        except:
            alert["alert_data"] = {}

        return alert

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get alert detail failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/history/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """Acknowledge alert"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("""
            UPDATE alert_history
            SET acknowledged = 1
            WHERE id = ? AND acknowledged = 0
        """, (alert_id,))

        updated = cursor.rowcount
        conn.commit()
        conn.close()

        if updated == 0:
            raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")

        return {"success": True, "alert_id": alert_id, "message": "Alert acknowledged"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Acknowledge alert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/history/{alert_id}/resolve")
async def resolve_alert(alert_id: str, notes: Optional[str] = None):
    """Resolve alert with optional notes"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)
        now = datetime.utcnow().isoformat()

        cursor = conn.execute("""
            UPDATE alert_history
            SET resolved = 1, acknowledged = 1, notes = ?, resolution_time = ?
            WHERE id = ? AND resolved = 0
        """, (notes, now, alert_id))

        updated = cursor.rowcount
        conn.commit()
        conn.close()

        if updated == 0:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")

        return {"success": True, "alert_id": alert_id, "resolution_time": now, "message": "Alert resolved"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resolve alert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/alerts/history/bulk")
async def bulk_alert_actions(action: str, alert_ids: List[str], notes: Optional[str] = None):
    """
    Perform bulk actions on alerts

    Actions: acknowledge, resolve, delete
    """
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")
        if action not in ["acknowledge", "resolve", "delete"]:
            raise HTTPException(status_code=400, detail="Invalid action")

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        results = {"success": 0, "failed": 0}

        for alert_id in alert_ids:
            try:
                if action == "acknowledge":
                    cursor.execute("UPDATE alert_history SET acknowledged = 1 WHERE id = ? AND acknowledged = 0", (alert_id,))
                elif action == "resolve":
                    cursor.execute("UPDATE alert_history SET resolved = 1, acknowledged = 1, notes = ?, resolution_time = ? WHERE id = ? AND resolved = 0",
                                   (notes, datetime.utcnow().isoformat(), alert_id))
                elif action == "delete":
                    cursor.execute("DELETE FROM alert_history WHERE id = ?", (alert_id,))

                if cursor.rowcount > 0:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except:
                results["failed"] += 1

        conn.commit()
        conn.close()

        return {
            "success": True,
            "action": action,
            "results": results,
            "message": f"Bulk {action} completed: {results['success']} succeeded, {results['failed']} failed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk alert actions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ALERT STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/alerts/stats")
async def get_alert_statistics(days: int = Query(30, ge=1, le=365)):
    """Get alert statistics"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        stats = alert_engine.get_alert_statistics(days)

        return stats

    except Exception as e:
        logger.error(f"Get alert stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATION CHANNEL MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/notifications/channels")
async def get_notification_channels():
    """Get all notification channels"""
    try:
        if not usage_tracker.enabled:
            return {"channels": []}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM notification_channels")
        rows = cursor.fetchall()
        conn.close()

        channels = []
        for row in rows:
            channel = dict(row)
            try:
                channel["config"] = json.loads(row.get("config", "{}"))
            except:
                channel["config"] = {}
            channels.append(channel)

        return {"channels": channels, "count": len(channels)}

    except Exception as e:
        logger.error(f"Get notification channels failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/notifications/channels")
async def create_notification_channel(channel_data: Dict[str, Any]):
    """Create notification channel"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail="Usage tracking disabled")

        conn = sqlite3.connect(usage_tracker.db_path)

        channel_id = f"chan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = conn.execute("""
            INSERT INTO notification_channels (id, name, type, config, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            channel_id,
            channel_data.get("name", "Unnamed Channel"),
            channel_data.get("type", "in_app"),
            json.dumps(channel_data.get("config", {})),
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return {"success": True, "channel_id": channel_id, "message": "Channel created"}

    except Exception as e:
        logger.error(f"Create notification channel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/notifications/channels/{channel_id}/test")
async def test_notification_channel(channel_id: str):
    """Send test notification to channel"""
    try:
        from src.services.notifications import notification_service

        success, message = notification_service.test_notification(channel_id)

        return {
            "success": success,
            "channel_id": channel_id,
            "message": message
        }

    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/notifications/history")
async def get_notification_history(limit: int = Query(50, ge=1, le=200)):
    """Get notification delivery history"""
    try:
        if not usage_tracker.enabled:
            return {"history": []}

        from src.services.notifications import notification_service
        history = notification_service.get_delivery_history(limit)

        return {"history": history, "count": len(history)}

    except Exception as e:
        logger.error(f"Get notification history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))