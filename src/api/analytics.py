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

from src.services.usage.usage_tracker import usage_tracker
from src.services.usage.cost_calculator import calculate_cost
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


@router.get("/api/analytics/dashboard")
async def get_dashboard_data(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get comprehensive dashboard data with all visualization metrics.

    Returns complete analytics for dashboard rendering:
    - Time series data for charts
    - Model comparison statistics
    - Savings analysis from smart routing
    - Token breakdown (prompt/completion/reasoning/etc)
    - Provider statistics
    - Overall summary metrics
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled. Set TRACK_USAGE=true to enable analytics."
        )

    try:
        data = usage_tracker.get_dashboard_summary(days=days)
        if not data:
            raise HTTPException(status_code=404, detail="No data available for the selected period")
        return data
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/savings")
async def get_savings_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get detailed savings analysis from smart model routing.

    Shows cost optimization achieved through routing decisions.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        savings_data = usage_tracker.get_savings_data(days=days)
        return {
            "period": {"days": days},
            "savings_by_routing": savings_data,
            "total_savings": sum(s['total_savings'] for s in savings_data),
            "total_requests": sum(s['request_count'] for s in savings_data)
        }
    except Exception as e:
        logger.error(f"Failed to get savings analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/token-breakdown")
async def get_token_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get detailed token breakdown analytics.

    Shows distribution across prompt, completion, reasoning, cached, tool_use, and audio tokens.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        token_stats = usage_tracker.get_token_breakdown_stats(days=days)
        if not token_stats:
            return {
                "period": {"days": days},
                "summary": {"total_tokens": 0, "request_count": 0},
                "breakdown": {}
            }
        return {
            "period": {"days": days},
            "summary": {
                "total_tokens": token_stats.get('total_tokens', 0),
                "request_count": token_stats.get('request_count', 0)
            },
            "breakdown": {
                "prompt": token_stats.get('prompt', {}),
                "completion": token_stats.get('completion', {}),
                "reasoning": token_stats.get('reasoning', {}),
                "cached": token_stats.get('cached', {}),
                "tool_use": token_stats.get('tool_use', {}),
                "audio": token_stats.get('audio', {})
            }
        }
    except Exception as e:
        logger.error(f"Failed to get token breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/providers")
async def get_provider_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get provider-level statistics and cost efficiency analysis.

    Shows which providers are being used and their performance characteristics.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        providers = usage_tracker.get_provider_stats(days=days)
        return {
            "period": {"days": days},
            "providers": providers
        }
    except Exception as e:
        logger.error(f"Failed to get provider analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/model-comparison")
async def get_model_comparison_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    min_requests: int = Query(1, ge=1, le=1000, description="Filter by minimum request count")
):
    """
    Get comparative analytics across different models.

    Shows performance metrics for each model including latency, cost efficiency, and token usage.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        models = usage_tracker.get_model_comparison(days=days)
        # Filter by minimum request count
        filtered_models = [m for m in models if m['total_requests'] >= min_requests]
        return {
            "period": {"days": days},
            "filters": {"min_requests": min_requests},
            "models": filtered_models
        }
    except Exception as e:
        logger.error(f"Failed to get model comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/insights")
async def get_analytics_insights(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Get AI-generated insights and recommendations from usage patterns.

    Returns actionable insights about cost optimization, performance improvements,
    and usage patterns based on the tracked data.
    """
    if not usage_tracker.enabled:
        raise HTTPException(
            status_code=503,
            detail="Usage tracking is not enabled."
        )

    try:
        # Get all relevant data
        summary = usage_tracker.get_cost_summary(days=days)
        savings = usage_tracker.get_savings_data(days=days)
        token_stats = usage_tracker.get_token_breakdown_stats(days=days)
        providers = usage_tracker.get_provider_stats(days=days)
        models = usage_tracker.get_model_comparison(days=days)

        # Generate insights
        insights = []

        # Savings insights
        total_savings = sum(s['total_savings'] for s in savings)
        if total_savings > 0:
            top_saving = max(savings, key=lambda x: x['total_savings']) if savings else None
            if top_saving:
                insights.append({
                    "type": "cost_saving",
                    "title": "Smart Routing Savings",
                    "description": f"Saved ${total_savings:.4f} ({top_saving['avg_savings_percent']:.1f}%) by routing {top_saving['request_count']} requests from {top_saving['original_model']} to {top_saving['routed_model']}",
                    "priority": "high" if top_saving['avg_savings_percent'] > 20 else "medium"
                })

        # Token efficiency insights
        if token_stats and token_stats.get('total_tokens', 0) > 0:
            reasoning_pct = token_stats['reasoning']['percentage']
            if reasoning_pct > 30:
                insights.append({
                    "type": "efficiency",
                    "title": "High Reasoning Token Usage",
                    "description": f"{reasoning_pct:.1f}% of tokens are reasoning tokens. Consider optimizing prompts or using smaller models for simpler tasks.",
                    "priority": "medium"
                })

            cached_pct = token_stats['cached']['percentage']
            if cached_pct < 5:
                insights.append({
                    "type": "optimization",
                    "title": "Low Cache Utilization",
                    "description": f"Only {cached_pct:.1f}% of tokens are cached. Consider using prompt caching for repetitive requests.",
                    "priority": "low"
                })

        # Provider insights
        if len(providers) > 1:
            top_provider = providers[0]
            second_provider = providers[1] if len(providers) > 1 else None
            if second_provider and top_provider['total_cost'] > second_provider['total_cost'] * 2:
                insights.append({
                    "type": "provider_concentration",
                    "title": "Provider Concentration",
                    "description": f"{top_provider['provider']} accounts for {top_provider['total_cost'] / (top_provider['total_cost'] + second_provider['total_cost']) * 100:.1f}% of costs. Consider diversifying providers.",
                    "priority": "low"
                })

        # Performance insights
        if summary and summary.get('avg_duration_ms', 0) > 5000:
            insights.append({
                "type": "performance",
                "title": "High Average Latency",
                "description": f"Average request latency is {summary['avg_duration_ms']:.0f}ms. Consider using faster models or enabling streaming.",
                "priority": "medium"
            })

        # Model usage insights
        if len(models) > 3:
            # Check for inefficient models (high cost per 1k tokens)
            inefficient = [m for m in models if m['avg_cost_per_1k_tokens'] > 10 and m['total_requests'] > 10]
            if inefficient:
                top_inefficient = inefficient[0]
                insights.append({
                    "type": "model_efficiency",
                    "title": "High Cost Model Usage",
                    "description": f"{top_inefficient['model']} costs ${top_inefficient['avg_cost_per_1k_tokens']:.2f}/1k tokens. Consider alternatives.",
                    "priority": "medium"
                })

        return {
            "period": {"days": days},
            "insights": insights,
            "summary": {
                "total_insights": len(insights),
                "high_priority": len([i for i in insights if i['priority'] == 'high']),
                "medium_priority": len([i for i in insights if i['priority'] == 'medium']),
                "low_priority": len([i for i in insights if i['priority'] == 'low'])
            }
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
