"""
Analytics API Endpoints - Phase 2
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import sqlite3, json
from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker

router = APIRouter()

@router.get("/api/analytics/timeseries")
async def get_timeseries_data(
    metric: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    group_by: str = Query("hour"),
    provider: Optional[str] = None,
    model: Optional[str] = None
):
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        
        time_cond = {
            "hour": "strftime('%Y-%m-%d %H:00', timestamp)",
            "day": "strftime('%Y-%m-%d', timestamp)",
            "week": "strftime('%Y-W%W', timestamp)"
        }.get(group_by, "strftime('%Y-%m-%d %H:00', timestamp)")
        
        filters = [f"{time_cond} >= ?", f"{time_cond} <= ?"]
        params = [start_date, end_date]
        
        if provider:
            filters.append("provider = ?")
            params.append(provider)
        if model:
            filters.append("routed_model = ?")
            params.append(model)
        
        where = " AND ".join(filters)
        select = {"tokens": "SUM(total_tokens)", "cost": "SUM(estimated_cost)", "requests": "COUNT(*)", "latency": "AVG(duration_ms)"}.get(metric, "COUNT(*)")
        
        cursor = conn.execute(f"SELECT {time_cond} as time_bucket, {select} as value FROM api_requests WHERE {where} GROUP BY time_bucket ORDER BY time_bucket", params)
        rows = cursor.fetchall()
        
        labels = [r["time_bucket"] for r in rows]
        values = [r["value"] or 0 for r in rows]
        conn.close()
        
        return {"labels": labels, "datasets": [{"label": metric.capitalize(), "data": values}], "meta": {"metric": metric, "total": len(labels)}}
    except Exception as e:
        logger.error(f"Timeseries failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/aggregate")
async def get_aggregated_stats(start_date: Optional[str] = None, end_date: Optional[str] = None):
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT COUNT(*) as requests, SUM(total_tokens) as tokens, SUM(estimated_cost) as cost,
                   AVG(duration_ms) as latency, COUNT(DISTINCT provider) as providers, COUNT(DISTINCT routed_model) as models,
                   SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors
            FROM api_requests
            WHERE timestamp >= ? AND timestamp <= ?
        """, [start_date, end_date])
        
        row = cursor.fetchone()
        conn.close()
        
        reqs = row["requests"] or 0
        errs = row["errors"] or 0
        error_rate = (errs / reqs * 100) if reqs > 0 else 0
        
        cost = row["cost"] or 0
        tokens = row["tokens"] or 0
        efficiency = (tokens / cost) if cost > 0 else 0
        
        return {
            "requests": {"total": reqs, "errors": errs, "error_rate": round(error_rate, 2)},
            "usage": {"tokens": tokens, "cost": round(cost, 4), "efficiency": round(efficiency, 2)},
            "performance": {"avg": round(row["latency"] or 0, 0)},
            "distribution": {"providers": row["providers"] or 0, "models": row["models"] or 0}
        }
    except Exception as e:
        logger.error(f"Aggregate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analytics/query")
async def execute_custom_query(query_config: Dict[str, Any]):
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}
        
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        
        query_parts = ["SELECT * FROM api_requests"]
        conditions = []
        params = []
        
        if "filters" in query_config:
            for f in query_config["filters"]:
                field, operator, value = f["field"], f["operator"], f["value"]
                if field not in {"provider", "routed_model", "status", "estimated_cost", "total_tokens", "duration_ms", "timestamp", "model"}:
                    continue
                if operator == "=":
                    conditions.append(f"{field} = ?")
                    params.append(value)
                elif operator == ">":
                    conditions.append(f"{field} > ?")
                    params.append(value)
                elif operator == "contains":
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        if "sort" in query_config:
            sort_field = query_config["sort"]["field"]
            sort_order = query_config["sort"]["order"]
            if sort_field in {"timestamp", "estimated_cost", "total_tokens", "duration_ms"}:
                query_parts.append(f"ORDER BY {sort_field} {sort_order}")
        
        limit = query_config.get("limit", 100)
        offset = query_config.get("offset", 0)
        query_parts.append(f"LIMIT {limit} OFFSET {offset}")
        
        cursor = conn.execute(" ".join(query_config), params)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        
        count_query = "SELECT COUNT(*) as total FROM api_requests"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        total_cursor = conn.execute(count_query, params)
        total = total_cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "results": results,
            "pagination": {"total": total, "limit": limit, "offset": offset, "has_more": (offset + limit) < total},
            "query": query_config
        }
    except Exception as e:
        logger.error(f"Custom query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/custom")
async def get_custom_analytics(
    metrics: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    group_by: str = Query("day"),
    aggregator: str = Query("sum")
):
    """Custom analytics endpoint for query builder"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled", "data": []}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        # Parse metrics
        metric_list = [m.strip() for m in metrics.split(",")]

        # Time grouping
        time_cond = {
            "hour": "strftime('%Y-%m-%d %H:00', timestamp)",
            "day": "strftime('%Y-%m-%d', timestamp)",
            "week": "strftime('%Y-W%W', timestamp)",
            "month": "strftime('%Y-%m', timestamp)"
        }.get(group_by, "strftime('%Y-%m-%d', timestamp)")

        # Metric mapping
        metric_selects = []
        for m in metric_list:
            if m == "tokens":
                metric_selects.append(f"{aggregator}(total_tokens) as tokens")
            elif m == "cost":
                metric_selects.append(f"{aggregator}(estimated_cost) as cost")
            elif m == "requests":
                metric_selects.append("COUNT(*) as requests")
            elif m == "latency":
                metric_selects.append("AVG(duration_ms) as latency")

        if not metric_selects:
            return {"error": "No valid metrics specified", "data": []}

        # Parse URL parameters for filters
        filter_conditions = []
        filter_params = []

        # For now, use the original API structure with query params
        # In future, could parse from URL or request body
        filter_conditions.append(f"{time_cond} >= ?")
        filter_params.append(start_date)
        filter_conditions.append(f"{time_cond} <= ?")
        filter_params.append(end_date)

        where_clause = " AND ".join(filter_conditions)
        metric_sql = ", ".join(metric_selects)

        query = f"""
            SELECT {time_cond} as date, {metric_sql}
            FROM api_requests
            WHERE {where_clause}
            GROUP BY date
            ORDER BY date
        """

        cursor = conn.execute(query, filter_params)
        rows = cursor.fetchall()
        conn.close()

        # Convert to list of dicts
        data = [dict(row) for row in rows]

        return {"data": data, "meta": {"metrics": metric_list, "group_by": group_by, "aggregator": aggregator}}

    except Exception as e:
        logger.error(f"Custom analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/analytics/queries")
async def save_query(query_data: Dict[str, Any]):
    """Save a custom query"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        conn = sqlite3.connect(usage_tracker.db_path)

        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_queries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        import uuid
        query_id = str(uuid.uuid4())
        name = query_data.get("name", "Untitled Query")
        query = json.dumps(query_data.get("query", {}))
        created_at = datetime.utcnow().isoformat()

        conn.execute(
            "INSERT INTO saved_queries (id, name, query, created_at) VALUES (?, ?, ?, ?)",
            (query_id, name, query, created_at)
        )
        conn.commit()
        conn.close()

        return {"id": query_id, "name": name, "status": "saved"}

    except Exception as e:
        logger.error(f"Save query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/queries")
async def get_saved_queries():
    """Get all saved queries"""
    try:
        if not usage_tracker.enabled:
            return []

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.execute("SELECT * FROM saved_queries ORDER BY created_at DESC")
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            conn.close()
            return []

        rows = cursor.fetchall()
        conn.close()

        return [{
            "id": row["id"],
            "name": row["name"],
            "query": json.loads(row["query"]),
            "created_at": row["created_at"]
        } for row in rows]

    except Exception as e:
        logger.error(f"Get queries failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/analytics/queries/{query_id}")
async def delete_query(query_id: str):
    """Delete a saved query"""
    try:
        if not usage_tracker.enabled:
            return {"error": "Usage tracking disabled"}

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute("DELETE FROM saved_queries WHERE id = ?", (query_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return {"deleted": deleted > 0, "id": query_id}

    except Exception as e:
        logger.error(f"Delete query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/health")
async def analytics_health():
    return {"status": "healthy", "enabled": usage_tracker.enabled, "database": usage_tracker.db_path if usage_tracker.enabled else None}
