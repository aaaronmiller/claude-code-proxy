"""
Analytics API Endpoints

Provides REST API access to historical usage data and analytics.
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime, timedelta
import os
from pathlib import Path

from src.utils.usage_tracker import usage_tracker
from src.core.logging import logger

router = APIRouter()


@router.get("/api/analytics/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get analytics summary for the specified time period.

    Returns aggregated metrics including:
    - Total requests
    - Token usage
    - Cost estimates
    - Performance metrics
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled. Set TRACK_USAGE=true to enable analytics."
        )

    try:
        summary = usage_tracker.get_cost_summary(days=days)
        top_models = usage_tracker.get_top_models(limit=10)
        json_analysis = usage_tracker.get_json_toon_analysis()

        return {
            "period": {
                "days": days,
                "start": (datetime.utcnow() - timedelta(days=days)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "summary": summary,
            "top_models": top_models,
            "json_analysis": json_analysis
        }
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/models")
async def get_model_usage(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of models to return")
):
    """
    Get model usage statistics.

    Returns a list of models sorted by request count with detailed metrics.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled. Set TRACK_USAGE=true to enable analytics."
        )

    try:
        models = usage_tracker.get_top_models(limit=limit)
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        logger.error(f"Failed to get model usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/timeseries")
async def get_timeseries_data(
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    interval: str = Query("hour", description="Interval: hour or day")
):
    """
    Get time-series data for charting.

    Returns aggregated metrics over time intervals for visualization.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        import sqlite3

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        if interval == "hour":
            time_format = '%Y-%m-%d %H:00:00'
        else:
            time_format = '%Y-%m-%d'

        cursor.execute(f"""
            SELECT
                strftime('{time_format}', timestamp) as time_bucket,
                COUNT(*) as request_count,
                SUM(estimated_cost) as cost,
                AVG(duration_ms) as avg_duration,
                SUM(total_tokens) as total_tokens
            FROM api_requests
            WHERE timestamp >= ? AND status = 'success'
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """, (since,))

        rows = cursor.fetchall()
        conn.close()

        data_points = []
        for row in rows:
            data_points.append({
                "timestamp": row[0],
                "requests": row[1],
                "cost": round(row[2] or 0.0, 4),
                "avg_duration_ms": round(row[3] or 0.0, 2),
                "tokens": row[4] or 0
            })

        return {
            "period": {
                "days": days,
                "interval": interval
            },
            "data": data_points
        }
    except Exception as e:
        logger.error(f"Failed to get timeseries data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/errors")
async def get_error_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get error analytics.

    Returns error rates, types, and trends.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        import sqlite3

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Get error summary
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                AVG(duration_ms) as avg_duration
            FROM api_requests
            WHERE timestamp >= ?
            GROUP BY status
        """, (since,))

        status_counts = {}
        total_requests = 0
        for row in cursor.fetchall():
            status_counts[row[0]] = {
                "count": row[1],
                "avg_duration_ms": round(row[2] or 0.0, 2)
            }
            total_requests += row[1]

        # Get error types
        cursor.execute("""
            SELECT
                error_message,
                COUNT(*) as count
            FROM api_requests
            WHERE timestamp >= ? AND status = 'error'
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 10
        """, (since,))

        error_types = []
        for row in cursor.fetchall():
            error_types.append({
                "message": row[0],
                "count": row[1]
            })

        conn.close()

        success_count = status_counts.get('success', {}).get('count', 0)
        error_count = total_requests - success_count
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 100

        return {
            "period": {
                "days": days
            },
            "summary": {
                "total_requests": total_requests,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": round(success_rate, 2)
            },
            "status_breakdown": status_counts,
            "top_errors": error_types
        }
    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/export")
async def export_analytics_data(
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("csv", description="Export format: csv or json")
):
    """
    Export analytics data to file.

    Returns a downloadable file with historical data.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_export_{timestamp}.{format}"
        filepath = export_dir / filename

        if format == "csv":
            success = usage_tracker.export_to_csv(str(filepath), days=days)
        elif format == "json":
            success = usage_tracker.export_to_json(str(filepath), days=days)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'.")

        if success and filepath.exists():
            return FileResponse(
                path=str(filepath),
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(status_code=500, detail="Export failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/cost-breakdown")
async def get_cost_breakdown(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get detailed cost breakdown by model, provider, and time.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        import sqlite3

        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Cost by model
        cursor.execute("""
            SELECT
                routed_model,
                COUNT(*) as requests,
                SUM(estimated_cost) as total_cost,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens
            FROM api_requests
            WHERE timestamp >= ? AND status = 'success'
            GROUP BY routed_model
            ORDER BY total_cost DESC
        """, (since,))

        model_costs = []
        total_cost = 0.0
        for row in cursor.fetchall():
            cost = row[2] or 0.0
            total_cost += cost
            model_costs.append({
                "model": row[0],
                "requests": row[1],
                "cost": round(cost, 4),
                "input_tokens": row[3] or 0,
                "output_tokens": row[4] or 0
            })

        # Cost by provider
        cursor.execute("""
            SELECT
                provider,
                COUNT(*) as requests,
                SUM(estimated_cost) as total_cost
            FROM api_requests
            WHERE timestamp >= ? AND status = 'success'
            GROUP BY provider
            ORDER BY total_cost DESC
        """, (since,))

        provider_costs = []
        for row in cursor.fetchall():
            provider_costs.append({
                "provider": row[0] or "unknown",
                "requests": row[1],
                "cost": round(row[2] or 0.0, 4)
            })

        conn.close()

        return {
            "period": {
                "days": days
            },
            "total_cost": round(total_cost, 4),
            "by_model": model_costs,
            "by_provider": provider_costs
        }
    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))
