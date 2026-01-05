"""
Predictive Alerting Service - Phase 4

AI-powered anomaly detection and predictive alerting using statistical analysis
and pattern recognition to forecast issues before they occur.

Features:
- Trend analysis and forecasting
- Anomaly detection using statistical methods
- Cost prediction
- Smart threshold recommendations
- Seasonal pattern detection

Author: AI Architect
Date: 2026-01-05
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import logging

from src.core.logging import logger


@dataclass
class PredictionResult:
    """Result from predictive analysis"""
    timestamp: str
    metric: str
    predicted_value: float
    confidence: float
    anomaly_score: float
    expected_range: Tuple[float, float]
    trend: str  # "increasing", "decreasing", "stable"
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class Forecast:
    """Multi-step forecast"""
    metric: str
    predictions: List[PredictionResult]
    total_tokens_predicted: float
    cost_prediction: float
    risk_level: str
    recommended_action: str


class PredictiveAlertingService:
    """AI-powered predictive alerting engine"""

    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.logger = logger

    def get_historical_data(self, days: int = 30) -> Dict[str, List[float]]:
        """Retrieve historical metrics data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get daily aggregates
            query = """
                SELECT
                    date(timestamp) as date,
                    SUM(total_tokens) as tokens,
                    SUM(estimated_cost) as cost,
                    COUNT(*) as requests,
                    AVG(duration_ms) as avg_latency
                FROM api_requests
                WHERE timestamp >= ? AND timestamp <= ?
                GROUP BY date(timestamp)
                ORDER BY date
            """

            cursor = conn.execute(query, [start_date.isoformat(), end_date.isoformat()])
            rows = cursor.fetchall()
            conn.close()

            data = {
                "tokens": [row["tokens"] or 0 for row in rows],
                "cost": [row["cost"] or 0 for row in rows],
                "requests": [row["requests"] or 0 for row in rows],
                "latency": [row["avg_latency"] or 0 for row in rows],
                "dates": [row["date"] for row in rows]
            }

            return data

        except Exception as e:
            self.logger.error(f"Failed to get historical data: {e}")
            return {}

    def calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction using linear regression"""
        if len(data) < 3:
            return "insufficient_data"

        x = np.arange(len(data))
        y = np.array(data)

        # Linear regression
        slope = np.polyfit(x, y, 1)[0]

        if abs(slope) < np.mean(y) * 0.05:  # Less than 5% change
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"

    def detect_anomalies(self, data: List[float], window: int = 7) -> List[float]:
        """Detect anomalies using rolling mean and std deviation"""
        if len(data) < window:
            return [0.0] * len(data)

        anomalies = []

        for i in range(len(data)):
            if i < window:
                anomalies.append(0.0)
                continue

            # Calculate rolling statistics
            window_data = data[i-window:i]
            mean = np.mean(window_data)
            std = np.std(window_data)

            # Z-score (how many standard deviations away from mean)
            if std == 0:
                z_score = 0
            else:
                z_score = abs(data[i] - mean) / std

            # Anomaly score (0-1)
            score = min(z_score / 3, 1.0)
            anomalies.append(score)

        return anomalies

    def forecast_simple(self, data: List[float], steps: int = 7) -> List[float]:
        """Simple exponential smoothing forecast"""
        if len(data) == 0:
            return [0.0] * steps

        alpha = 0.3  # Smoothing factor
        forecast = []

        # Initialize with last value
        level = data[-1]

        for _ in range(steps):
            # Apply exponential smoothing
            level = alpha * level + (1 - alpha) * level
            forecast.append(max(0, level))

        return forecast

    def predict_metrics(self, days_ahead: int = 7) -> Forecast:
        """Main prediction method - predicts future metrics"""
        try:
            # Get historical data
            history = self.get_historical_data(days=30)

            if not history or len(history.get("tokens", [])) < 5:
                return Forecast(
                    metric="all",
                    predictions=[],
                    total_tokens_predicted=0,
                    cost_prediction=0,
                    risk_level="unknown",
                    recommended_action="Insufficient data for prediction"
                )

            predictions = []

            # Predict each metric
            for metric in ["tokens", "cost", "requests"]:
                historical_values = history[metric]

                if len(historical_values) < 5:
                    continue

                # Calculate trend
                trend = self.calculate_trend(historical_values)

                # Detect anomalies
                anomalies = self.detect_anomalies(historical_values)

                # Generate forecast
                forecast_values = self.forecast_simple(historical_values, days_ahead)

                # Calculate confidence based on historical consistency
                std_dev = np.std(historical_values)
                mean_val = np.mean(historical_values)
                consistency = 1.0 - (std_dev / mean_val if mean_val > 0 else 1.0)
                confidence = max(0.5, min(0.95, consistency))

                # Calculate anomaly score for next period
                if anomalies:
                    recent_anomaly = np.mean(anomalies[-3:]) if len(anomalies) >= 3 else anomalies[-1]
                else:
                    recent_anomaly = 0.0

                # Expected range (confidence interval)
                lower_bound = [max(0, val * 0.8) for val in forecast_values]
                upper_bound = [val * 1.2 for val in forecast_values]

                # Determine severity based on trend and anomaly score
                severity = "low"
                if recent_anomaly > 0.5:
                    severity = "high"
                elif trend == "increasing" and recent_anomaly > 0.3:
                    severity = "medium"

                # Create prediction results
                for i, (pred_val, lower, upper) in enumerate(zip(forecast_values, lower_bound, upper_bound)):
                    future_date = datetime.now() + timedelta(days=i+1)

                    predictions.append(PredictionResult(
                        timestamp=future_date.isoformat(),
                        metric=metric,
                        predicted_value=pred_val,
                        confidence=confidence,
                        anomaly_score=recent_anomaly,
                        expected_range=(lower, upper),
                        trend=trend,
                        severity=severity
                    ))

            # Calculate total predictions
            tokens_predicted = sum(p.predicted_value for p in predictions if p.metric == "tokens")
            cost_predicted = sum(p.predicted_value for p in predictions if p.metric == "cost")

            # Determine overall risk
            high_severity = sum(1 for p in predictions if p.severity in ["high", "critical"])
            risk_level = "low"
            if high_severity > len(predictions) * 0.3:
                risk_level = "high"
            elif high_severity > 0:
                risk_level = "medium"

            # Generate recommendation
            recommendation = self._generate_recommendation(
                tokens_predicted, cost_predicted, risk_level, trend
            )

            return Forecast(
                metric="all",
                predictions=predictions,
                total_tokens_predicted=tokens_predicted,
                cost_prediction=cost_predicted,
                risk_level=risk_level,
                recommended_action=recommendation
            )

        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return Forecast(
                metric="all",
                predictions=[],
                total_tokens_predicted=0,
                cost_prediction=0,
                risk_level="error",
                recommended_action=f"Prediction error: {str(e)}"
            )

    def _generate_recommendation(self, tokens: float, cost: float, risk: str, trend: str) -> str:
        """Generate actionable recommendations"""
        if risk == "high":
            return "ALERT: High risk detected. Consider reducing model complexity or implementing rate limits."
        elif risk == "medium":
            if trend == "increasing":
                return "Monitor closely. Usage trending upward. Set up budget alerts."
            else:
                return "Medium risk. Review cost optimization opportunities."
        elif risk == "low":
            if trend == "increasing":
                return "Usage increasing normally. Monitor for continued growth."
            else:
                return "Usage stable. No immediate action required."
        else:
            return "Unable to determine risk level. Monitor manually."

    def get_smart_thresholds(self, metric: str) -> Dict[str, float]:
        """Calculate intelligent thresholds based on historical data"""
        history = self.get_historical_data(days=30)

        if metric not in history or len(history[metric]) < 5:
            return {"warning": 0, "critical": 0}

        values = history[metric]
        q75 = np.percentile(values, 75)
        q90 = np.percentile(values, 90)

        return {
            "warning": float(q75),
            "critical": float(q90),
            "info": f"Based on 30-day p75/p90 percentiles"
        }

    def detect_seasonal_patterns(self, days: int = 30) -> Dict[str, any]:
        """Detect daily/weekly patterns in usage"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Get hourly distribution
            query = """
                SELECT
                    strftime('%H', timestamp) as hour,
                    AVG(total_tokens) as avg_tokens,
                    COUNT(*) as request_count
                FROM api_requests
                WHERE timestamp >= ?
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            """

            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = conn.execute(query, [cutoff])
            rows = cursor.fetchall()
            conn.close()

            # Find peak hours
            hourly_data = {int(row["hour"]): (row["avg_tokens"] or 0, row["request_count"] or 0) for row in rows}

            peak_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h][0]) if hourly_data else None
            peak_avg = hourly_data[peak_hour][0] if peak_hour else 0

            # Detect weekday/weekend patterns
            query2 = """
                SELECT
                    CASE WHEN CAST(strftime('%w', timestamp) AS INTEGER) IN (0,6) THEN 'weekend' ELSE 'weekday' END as day_type,
                    AVG(total_tokens) as avg_tokens,
                    COUNT(*) as request_count
                FROM api_requests
                WHERE timestamp >= ?
                GROUP BY day_type
            """

            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(query2, [cutoff])
            pattern_rows = cursor.fetchall()
            conn.close()

            patterns = {}
            for row in pattern_rows:
                patterns[row["day_type"]] = {
                    "avg_tokens": row["avg_tokens"] or 0,
                    "requests": row["request_count"] or 0
                }

            return {
                "peak_hour": peak_hour,
                "peak_avg_tokens": peak_avg,
                "patterns": patterns,
                "recommendation": self._generate_pattern_recommendation(hourly_data, patterns)
            }

        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}")
            return {}

    def _generate_pattern_recommendation(self, hourly_data: Dict, patterns: Dict) -> str:
        """Generate scheduling recommendations based on patterns"""
        if not hourly_data or not patterns:
            return "Insufficient data for pattern analysis"

        peak_hour = max(hourly_data.keys(), key=lambda h: hourly_data[h][0])

        # Check if off-peak scheduling would help
        weekday_avg = patterns.get("weekday", {}).get("avg_tokens", 0)
        weekend_avg = patterns.get("weekend", {}).get("avg_tokens", 0)

        if weekday_avg > weekend_avg * 2:
            return f"Peak usage at hour {peak_hour}. Consider batch processing during off-peak hours (weekends)."
        elif peak_hour and (peak_hour >= 9 and peak_hour <= 17):
            return f"Business hours peak detected (hour {peak_hour}). Consider off-hours processing."
        else:
            return "Usage is well distributed. No scheduling optimization needed."


# Singleton instance
predictive_alerting = PredictiveAlertingService()


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    timestamp: str
    metric: str
    value: float
    expected: float
    deviation: float
    severity: str
    description: str


class AnomalyDetector:
    """Real-time anomaly detection for incoming requests"""

    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.baseline_cache = {}  # Cache for baseline stats

    def update_baseline(self, metric: str, window_hours: int = 24) -> Dict[str, float]:
        """Update baseline statistics for a metric"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()

        if metric == "cost":
            query = "SELECT AVG(estimated_cost) as mean, STDDEV(estimated_cost) as std FROM api_requests WHERE timestamp >= ?"
        elif metric == "tokens":
            query = "SELECT AVG(total_tokens) as mean, STDDEV(total_tokens) as std FROM api_requests WHERE timestamp >= ?"
        elif metric == "latency":
            query = "SELECT AVG(duration_ms) as mean, STDDEV(duration_ms) as std FROM api_requests WHERE timestamp >= ?"
        else:
            conn.close()
            return {}

        cursor = conn.execute(query, [cutoff])
        row = cursor.fetchone()
        conn.close()

        if not row or row["mean"] is None:
            return {}

        stats = {
            "mean": row["mean"],
            "std": row["std"] or 0,
            "upper_bound": row["mean"] + (3 * (row["std"] or 0)),  # 3-sigma rule
            "lower_bound": max(0, row["mean"] - (3 * (row["std"] or 0)))
        }

        self.baseline_cache[metric] = stats
        return stats

    def check_request(self, request_data: Dict) -> Optional[Anomaly]:
        """Check a single request for anomalies"""
        baseline = self.update_baseline("cost")  # Check cost first

        if not baseline:
            return None

        cost = request_data.get("estimated_cost", 0)

        if cost > baseline["upper_bound"]:
            deviation = ((cost - baseline["mean"]) / baseline["mean"]) * 100
            return Anomaly(
                timestamp=datetime.now().isoformat(),
                metric="cost",
                value=cost,
                expected=baseline["mean"],
                deviation=deviation,
                severity="high" if deviation > 200 else "medium",
                description=f"Cost anomaly: ${cost:.4f} vs expected ${baseline['mean']:.4f} (+{deviation:.1f}%)"
            )

        return None


# Singleton
anomaly_detector = AnomalyDetector()


class PredictionAPI:
    """API interface for predictive features"""

    @staticmethod
    async def get_predictions(days: int = 7) -> Dict:
        """Get predictive forecast"""
        try:
            forecast = predictive_alerting.predict_metrics(days)

            return {
                "success": True,
                "data": {
                    "predictions": [
                        {
                            "timestamp": p.timestamp,
                            "metric": p.metric,
                            "value": round(p.predicted_value, 4),
                            "confidence": round(p.confidence, 3),
                            "anomaly_score": round(p.anomaly_score, 3),
                            "expected_range": [round(r, 4) for r in p.expected_range],
                            "trend": p.trend,
                            "severity": p.severity
                        }
                        for p in forecast.predictions
                    ],
                    "summary": {
                        "total_tokens": round(forecast.total_tokens_predicted, 0),
                        "total_cost": round(forecast.cost_prediction, 4),
                        "risk_level": forecast.risk_level,
                        "recommendation": forecast.recommended_action
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_smart_thresholds(metric: str) -> Dict:
        """Get intelligent thresholds"""
        thresholds = predictive_alerting.get_smart_thresholds(metric)
        return {
            "metric": metric,
            "thresholds": thresholds,
            "source": "30-day historical analysis"
        }

    @staticmethod
    async def get_patterns() -> Dict:
        """Get usage patterns"""
        patterns = predictive_alerting.detect_seasonal_patterns()
        return {"patterns": patterns}

    @staticmethod
    async def detect_current_anomaly(request_data: Dict) -> Dict:
        """Detect if current request is anomalous"""
        anomaly = anomaly_detector.check_request(request_data)

        if anomaly:
            return {
                "is_anomaly": True,
                "details": {
                    "metric": anomaly.metric,
                    "value": anomaly.value,
                    "expected": anomaly.expected,
                    "deviation_percent": anomaly.deviation,
                    "severity": anomaly.severity,
                    "description": anomaly.description
                }
            }

        return {"is_anomaly": False}
