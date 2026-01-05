"""
Custom Dashboard Builder API - Phase 4

Endpoints for creating, saving, and managing custom dashboards

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import sqlite3
import json
from datetime import datetime
import uuid

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker

router = APIRouter()


@router.post("/api/dashboards")
async def save_dashboard(dashboard: Dict[str, Any]):
    """Save a custom dashboard"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        conn = sqlite3.connect(usage_tracker.db_path)

        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_dashboards (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                widgets TEXT NOT NULL,
                config TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                owner TEXT DEFAULT 'default'
            )
        """)

        dashboard_id = dashboard.get("id") or str(uuid.uuid4())
        name = dashboard.get("name", "Untitled Dashboard")
        widgets = json.dumps(dashboard.get("widgets", []))
        config = json.dumps(dashboard.get("config", {}))
        created_at = dashboard.get("created_at", datetime.now().isoformat())
        updated_at = datetime.now().isoformat()

        # Check if exists
        cursor = conn.execute("SELECT id FROM custom_dashboards WHERE id = ?", (dashboard_id,))
        exists = cursor.fetchone() is not None

        if exists:
            # Update
            conn.execute("""
                UPDATE custom_dashboards
                SET name = ?, widgets = ?, config = ?, updated_at = ?
                WHERE id = ?
            """, (name, widgets, config, updated_at, dashboard_id))
        else:
            # Insert
            conn.execute("""
                INSERT INTO custom_dashboards (id, name, widgets, config, created_at, updated_at, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dashboard_id, name, widgets, config, created_at, updated_at, "default"))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "id": dashboard_id,
            "name": name,
            "status": "updated" if exists else "created"
        }

    except Exception as e:
        logger.error(f"Save dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboards")
async def get_dashboards():
    """Get all custom dashboards"""
    try:
        if not usage_tracker.enabled:
            return {"dashboards": []}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.execute("""
                SELECT id, name, widgets, config, created_at, updated_at, owner
                FROM custom_dashboards
                ORDER BY updated_at DESC
            """)
        except sqlite3.OperationalError:
            conn.close()
            return {"dashboards": []}

        rows = cursor.fetchall()
        conn.close()

        dashboards = []
        for row in rows:
            dashboards.append({
                "id": row["id"],
                "name": row["name"],
                "widgets": json.loads(row["widgets"]),
                "config": json.loads(row["config"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "owner": row["owner"]
            })

        return {"dashboards": dashboards, "count": len(dashboards)}

    except Exception as e:
        logger.error(f"Get dashboards failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get a specific dashboard"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT id, name, widgets, config, created_at, updated_at, owner
            FROM custom_dashboards
            WHERE id = ?
        """, (dashboard_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        return {
            "id": row["id"],
            "name": row["name"],
            "widgets": json.loads(row["widgets"]),
            "config": json.loads(row["config"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "owner": row["owner"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/dashboards/{dashboard_id}")
async def delete_dashboard(dashboard_id: str):
    """Delete a dashboard"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("DELETE FROM custom_dashboards WHERE id = ?", (dashboard_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted == 0:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        return {"success": True, "id": dashboard_id, "status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/dashboards/{dashboard_id}/duplicate")
async def duplicate_dashboard(dashboard_id: str):
    """Duplicate a dashboard"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        # Get original
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM custom_dashboards WHERE id = ?", (dashboard_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Dashboard not found")

        # Create copy
        new_id = str(uuid.uuid4())
        new_name = f"{row['name']} (Copy)"
        created_at = datetime.now().isoformat()

        conn.execute("""
            INSERT INTO custom_dashboards (id, name, widgets, config, created_at, updated_at, owner)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (new_id, new_name, row["widgets"], row["config"], created_at, created_at, row["owner"]))

        conn.commit()
        conn.close()

        return {"success": True, "id": new_id, "name": new_name, "original_id": dashboard_id}

    except Exception as e:
        logger.error(f"Duplicate dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboards/{dashboard_id}/data")
async def get_dashboard_data(dashboard_id: str):
    """Get data for a dashboard's widgets"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        # Get dashboard config
        dashboard = await get_dashboard(dashboard_id)

        if "error" in dashboard:
            return dashboard

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        results = {}

        for widget in dashboard.get("widgets", []):
            widget_id = widget["id"]
            metric = widget["config"]["metric"]
            period = widget["config"]["period"]
            aggregate = widget["config"]["aggregate"]

            # Calculate date range
            from datetime import timedelta

            now = datetime.now()
            if period == "24h":
                start_date = now - timedelta(hours=24)
            elif period == "7d":
                start_date = now - timedelta(days=7)
            elif period == "30d":
                start_date = now - timedelta(days=30)
            elif period == "90d":
                start_date = now - timedelta(days=90)
            else:
                start_date = now - timedelta(days=7)

            # Query data based on metric
            metric_map = {
                "tokens": "SUM(total_tokens)",
                "cost": "SUM(estimated_cost)",
                "requests": "COUNT(*)",
                "latency": "AVG(duration_ms)",
                "error_rate": "AVG(CASE WHEN status = 'error' THEN 100 ELSE 0 END)",
                "efficiency": "CASE WHEN SUM(estimated_cost) > 0 THEN SUM(total_tokens) / SUM(estimated_cost) ELSE 0 END"
            }

            select = metric_map.get(metric, "COUNT(*)")

            # Group by day for charts, single value for stats
            if widget["type"] == "chart":
                query = f"""
                    SELECT
                        date(timestamp) as date,
                        {select} as value
                    FROM api_requests
                    WHERE timestamp >= ?
                    GROUP BY date(timestamp)
                    ORDER BY date(timestamp)
                """
            else:
                query = f"""
                    SELECT {select} as value
                    FROM api_requests
                    WHERE timestamp >= ?
                """

            cursor = conn.execute(query, [start_date.isoformat()])
            data = cursor.fetchall()

            if widget["type"] == "chart":
                results[widget_id] = [
                    {"date": row["date"], "value": row["value"] or 0}
                    for row in data
                ]
            else:
                results[widget_id] = {
                    "value": data[0]["value"] if data else 0
                }

        conn.close()

        return {
            "dashboard_id": dashboard_id,
            "data": results,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Get dashboard data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboards/{dashboard_id}/export")
async def export_dashboard(dashboard_id: str):
    """Export dashboard as JSON file"""
    try:
        dashboard = await get_dashboard(dashboard_id)
        return dashboard

    except Exception as e:
        logger.error(f"Export dashboard failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboards/health")
async def dashboards_health():
    """Health check for dashboards service"""
    try:
        if not usage_tracker.enabled:
            return {"status": "disabled", "enabled": False}

        conn = sqlite3.connect(usage_tracker.db_path)
        try:
            cursor = conn.execute("SELECT COUNT(*) as count FROM custom_dashboards")
            count = cursor.fetchone()[0]
            conn.close()

            return {
                "status": "healthy",
                "enabled": True,
                "dashboards_count": count
            }
        except sqlite3.OperationalError:
            conn.close()
            return {"status": "healthy", "enabled": True, "dashboards_count": 0}

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}
