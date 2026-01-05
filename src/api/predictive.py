"""
Predictive Alerting API - Phase 4

Endpoints for AI-powered predictive analytics and anomaly detection

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import json
import sqlite3
from datetime import datetime, timedelta

from src.core.logging import logger
from src.services.predictive_alerting import (
    predictive_alerting,
    anomaly_detector,
    PredictionAPI
)
from src.services.usage.usage_tracker import usage_tracker

router = APIRouter()


@router.get("/api/predictive/forecast")
async def get_forecast(
    days: int = Query(7, ge=1, le=30, description="Number of days to forecast")
):
    """Get predictive forecast for usage metrics"""
    try:
        result = await PredictionAPI.get_predictions(days)
        return result
    except Exception as e:
        logger.error(f"Forecast endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictive/thresholds")
async def get_smart_thresholds(
    metric: str = Query(..., description="Metric: tokens, cost, requests, latency")
):
    """Get intelligent thresholds based on historical analysis"""
    try:
        result = await PredictionAPI.get_smart_thresholds(metric)
        return result
    except Exception as e:
        logger.error(f"Thresholds endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictive/patterns")
async def get_patterns():
    """Get seasonal and usage patterns"""
    try:
        result = await PredictionAPI.get_patterns()
        return result
    except Exception as e:
        logger.error(f"Patterns endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/predictive/detect-anomaly")
async def detect_anomaly(request_data: Dict[str, Any]):
    """Detect if current request is anomalous"""
    try:
        result = await PredictionAPI.detect_current_anomaly(request_data)
        return result
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/predictive/analyze-cost")
async def analyze_cost_prediction(
    request_config: Dict[str, Any],
    model: Optional[str] = None,
    provider: Optional[str] = None
):
    """Analyze potential cost before making request"""
    try:
        # Get current metrics
        forecast = predictive_alerting.predict_metrics(1)

        # Estimate cost based on request
        input_tokens = request_config.get("input_tokens", 0)
        output_tokens = request_config.get("output_tokens", 0)

        if not model:
            model = request_config.get("model", "unknown")

        # Simple cost estimation (would need actual pricing data)
        estimated_cost = (input_tokens + output_tokens) * 0.00003  # Rough estimate

        # Check if this would exceed thresholds
        thresholds = predictive_alerting.get_smart_thresholds("cost")

        daily_total = sum(p.predicted_value for p in forecast.predictions if p.metric == "cost")
        projected_total = daily_total + estimated_cost

        response = {
            "estimated_cost": round(estimated_cost, 6),
            "daily_projected_total": round(projected_total, 6),
            "within_budget": projected_total < thresholds.get("warning", float('inf')),
            "thresholds": thresholds,
            "recommendation": ""
        }

        if projected_total > thresholds.get("critical", 0):
            response["recommendation"] = "CRITICAL: Request would exceed budget threshold. Consider using a smaller model."
            response["severity"] = "critical"
        elif projected_total > thresholds.get("warning", 0):
            response["recommendation"] = "WARNING: Request would exceed warning threshold. Proceed with caution."
            response["severity"] = "warning"
        else:
            response["recommendation"] = "OK: Cost projection within normal range."
            response["severity"] = "low"

        return response

    except Exception as e:
        logger.error(f"Cost analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictive/trend-analysis")
async def get_trend_analysis(days: int = Query(7, ge=1, le=90)):
    """Get detailed trend analysis"""
    try:
        history = predictive_alerting.get_historical_data(days=days)

        if not history:
            return {"error": "Insufficient data"}

        # Calculate trends for each metric
        trends = {}
        for metric in ["tokens", "cost", "requests"]:
            if metric in history and len(history[metric]) >= 2:
                data = history[metric]
                trend = predictive_alerting.calculate_trend(data)

                # Calculate growth rate
                if len(data) >= 2:
                    growth_rate = ((data[-1] - data[0]) / data[0]) * 100 if data[0] > 0 else 0
                else:
                    growth_rate = 0

                # Confidence based on data points
                confidence = min(0.95, len(data) / 30)  # Scale with data availability

                trends[metric] = {
                    "trend": trend,
                    "growth_rate": round(growth_rate, 2),
                    "confidence": round(confidence, 2),
                    "recent_values": data[-7:] if len(data) >= 7 else data
                }

        return {
            "analysis_period_days": days,
            "trends": trends,
            "summary": f"Analyzed {days} days of data"
        }

    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/predictive/smart-alert")
async def create_smart_alert(
    alert_config: Dict[str, Any]
):
    """Create an alert with AI-suggested thresholds"""
    try:
        metric = alert_config.get("metric", "cost")
        operator = alert_config.get("operator", ">")

        # Get smart thresholds
        thresholds = predictive_alerting.get_smart_thresholds(metric)

        # Use recommended threshold if not provided
        threshold_value = alert_config.get("threshold")
        if threshold_value is None:
            threshold_value = thresholds.get("warning", 0)

        # Validate the threshold is reasonable
        if threshold_value > thresholds.get("critical", 0) * 1.5:
            warning = "Threshold is significantly higher than historical 90th percentile"
        elif threshold_value < thresholds.get("critical", 0) * 0.5:
            warning = "Threshold may trigger too frequently"
        else:
            warning = None

        response = {
            "alert_config": {
                "metric": metric,
                "operator": operator,
                "threshold": threshold_value,
                "time_window": alert_config.get("time_window", "5m")
            },
            "smart_thresholds": thresholds,
            "validation": {
                "is_recommended": warning is None,
                "warning": warning,
                "source": "30-day historical analysis"
            },
            "predicted_alerts": []  # Will be populated by alert engine
        }

        return response

    except Exception as e:
        logger.error(f"Smart alert creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictive/health")
async def predictive_health():
    """Health check for predictive services"""
    try:
        # Test data availability
        history = predictive_alerting.get_historical_data(days=3)
        has_data = bool(history and len(history.get("tokens", [])) > 0)

        return {
            "status": "healthy" if has_data else "degraded",
            "data_available": has_data,
            "services": {
                "forecasting": has_data,
                "anomaly_detection": True,
                "pattern_analysis": has_data
            },
            "recommendation": "Run some requests to generate training data" if not has_data else "Ready"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/api/predictive/recommendations")
async def get_recommendations(
    days: int = Query(7, ge=1, le=90)
):
    """Get actionable recommendations based on AI analysis"""
    try:
        forecast = predictive_alerting.predict_metrics(days)
        patterns = predictive_alerting.detect_seasonal_patterns()

        recommendations = []

        # Based on forecast risk
        if forecast.risk_level == "high":
            recommendations.append({
                "priority": "high",
                "category": "budget_protection",
                "message": forecast.recommended_action,
                "action": "Consider setting up strict rate limits or model restrictions"
            })
        elif forecast.risk_level == "medium":
            recommendations.append({
                "priority": "medium",
                "category": "monitoring",
                "message": forecast.recommended_action,
                "action": "Enable detailed logging and set up alerts"
            })

        # Based on cost projection
        if forecast.cost_prediction > 100:  # Arbitrary threshold
            recommendations.append({
                "priority": "medium",
                "category": "optimization",
                "message": f"Projected cost: ${forecast.cost_prediction:.2f} for next {days} days",
                "action": "Review model selection for cost optimization"
            })

        # Based on patterns
        if patterns.get("peak_hour") is not None:
            peak = patterns["peak_hour"]
            if peak >= 9 and peak <= 17:
                recommendations.append({
                    "priority": "low",
                    "category": "scheduling",
                    "message": f"Peak usage during business hours ({peak}:00)",
                    "action": "Consider batch processing during off-peak hours"
                })

        # Empty recommendations
        if not recommendations:
            recommendations.append({
                "priority": "low",
                "category": "general",
                "message": "No critical issues detected. System operating normally.",
                "action": "Continue monitoring"
            })

        return {
            "risk_level": forecast.risk_level,
            "forecast_summary": {
                "tokens": round(forecast.total_tokens_predicted, 0),
                "cost": round(forecast.cost_prediction, 4),
                "days_ahead": days
            },
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/predictive/anomaly-history")
async def get_anomaly_history(
    limit: int = Query(50, ge=1, le=500)
):
    """Get history of detected anomalies"""
    try:
        # This would query the anomaly history table if we had one
        # For now, we'll scan recent data and generate what we can detect
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row

        # Get recent requests that are outliers
        query = """
            SELECT
                timestamp,
                estimated_cost,
                total_tokens,
                duration_ms,
                provider,
                routed_model,
                CASE
                    WHEN estimated_cost > (SELECT AVG(estimated_cost) * 3 FROM api_requests) THEN 'cost'
                    WHEN total_tokens > (SELECT AVG(total_tokens) * 3 FROM api_requests) THEN 'tokens'
                    WHEN duration_ms > (SELECT AVG(duration_ms) * 3 FROM api_requests) THEN 'latency'
                END as anomaly_type
            FROM api_requests
            WHERE timestamp >= ?
            HAVING anomaly_type IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """

        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        cursor = conn.execute(query, [cutoff, limit])
        rows = cursor.fetchall()
        conn.close()

        anomalies = []
        for row in rows:
            anomalies.append({
                "timestamp": row["timestamp"],
                "type": row["anomaly_type"],
                "value": row.get(row["anomaly_type"], 0),
                "provider": row["provider"],
                "model": row["routed_model"]
            })

        return {
            "count": len(anomalies),
            "anomalies": anomalies,
            "period": "last 7 days"
        }

    except Exception as e:
        logger.error(f"Anomaly history failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
