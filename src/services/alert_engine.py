"""
Alert Engine Service - Phase 3

Core service for evaluating alert rules and triggering notifications.
Runs every minute to check all active rules against current metrics.

Author: AI Architect
Date: 2026-01-05
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker
from src.services.notifications import notification_service


@dataclass
class AlertRule:
    """Data class for alert rule configuration"""
    id: str
    name: str
    description: str
    condition_json: str
    condition_logic: str
    actions_json: str
    cooldown_minutes: int
    priority: int
    time_window: int
    is_active: bool
    last_triggered: Optional[str]
    trigger_count: int
    created_at: str
    created_by: str

    @property
    def conditions(self):
        return json.loads(self.condition_json)

    @property
    def logic(self):
        return json.loads(self.condition_logic) if self.condition_logic else None

    @property
    def actions(self):
        return json.loads(self.actions_json)


@dataclass
class AlertTrigger:
    """Data class for triggered alert"""
    id: str
    rule_id: str
    rule_name: str
    triggered_at: str
    severity: str
    alert_data: Dict[str, Any]
    description: str
    resolved: bool = False
    acknowledged: bool = False


class AlertEngine:
    """Main alert evaluation engine"""

    def __init__(self):
        self.db_path = usage_tracker.db_path
        self.cooldown_cache = {}  # Track recent triggers to prevent spam

    async def start(self):
        """Start the alert engine (called from main.py lifespan)"""
        logger.info("🚀 Alert Engine Starting...")
        try:
            # Load all active rules
            rules = self.get_active_rules()
            logger.info(f"📊 Loaded {len(rules)} active alert rules")

            # Start background task
            asyncio.create_task(self.evaluation_loop())
            logger.info("✅ Alert Engine Started")

        except Exception as e:
            logger.error(f"❌ Alert Engine failed to start: {e}")
            raise

    async def stop(self):
        """Stop the alert engine"""
        logger.info("🛑 Alert Engine Stopping...")
        # Save any pending state if needed
        logger.info("✅ Alert Engine Stopped")

    async def evaluation_loop(self):
        """Main evaluation loop - runs every 60 seconds"""
        while True:
            try:
                await asyncio.sleep(60)  # Wait 60 seconds
                await self.evaluate_all_rules()
            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                # Continue loop despite errors

    def get_active_rules(self) -> List[AlertRule]:
        """Retrieve all active alert rules from database"""
        if not usage_tracker.enabled:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM alert_rules
            WHERE is_active = 1
            ORDER BY priority ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [AlertRule(**dict(row)) for row in rows]

    async def evaluate_all_rules(self):
        """Evaluate all active rules"""
        rules = self.get_active_rules()
        if not rules:
            return

        logger.info(f"Evaluating {len(rules)} active alert rules...")

        for rule in rules:
            try:
                await self.evaluate_rule(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")

    async def evaluate_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        # Check cooldown
        if not self.check_cooldown(rule):
            return

        # Get current metrics
        current_metrics = await self.get_current_metrics(rule.time_window)

        # Check conditions
        triggered, alert_data = self.check_conditions(rule, current_metrics)

        if triggered:
            # Check if already triggered recently (prevent duplicate alerts)
            if self.recently_triggered(rule):
                return

            # Trigger the alert
            await self.trigger_alert(rule, alert_data)
            self.update_last_triggered(rule)

    def check_cooldown(self, rule: AlertRule) -> bool:
        """Check if rule is in cooldown period"""
        if rule.last_triggered is None:
            return True

        last_trigger = datetime.fromisoformat(rule.last_triggered)
        cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
        now = datetime.utcnow()

        return (now - last_trigger) > cooldown_delta

    def recently_triggered(self, rule: AlertRule, window_minutes: int = 5) -> bool:
        """Check if rule triggered within last N minutes"""
        if rule.last_triggered is None:
            return False

        last_trigger = datetime.fromisoformat(rule.last_triggered)
        window_delta = timedelta(minutes=window_minutes)
        now = datetime.utcnow()

        return (now - last_trigger) < window_delta

    async def get_current_metrics(self, time_window: int) -> Dict[str, Any]:
        """Get current metrics for the specified time window"""
        if not usage_tracker.enabled:
            return {}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        time_condition = datetime.utcnow() - timedelta(minutes=time_window)

        # Get basic metrics
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(duration_ms) as avg_latency,
                AVG(estimated_cost) as avg_cost_per_request,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors
            FROM api_requests
            WHERE timestamp >= ?
        """, (time_condition.isoformat(),))

        row = cursor.fetchone()

        # Calculate derived metrics
        total_requests = row["total_requests"] or 0
        errors = row["errors"] or 0
        total_cost = row["total_cost"] or 0
        total_tokens = row["total_tokens"] or 0

        # Get yesterday's cost for comparison
        yesterday_start = datetime.utcnow() - timedelta(days=1)
        yesterday_end = yesterday_start + timedelta(days=1)

        cursor.execute("""
            SELECT SUM(estimated_cost) as yesterday_cost
            FROM api_requests
            WHERE timestamp >= ? AND timestamp < ?
        """, (yesterday_start.isoformat(), yesterday_end.isoformat()))

        yesterday_row = cursor.fetchone()
        yesterday_cost = yesterday_row["yesterday_cost"] or 0

        conn.close()

        # Calculate percentage changes
        cost_change_percent = 0
        if yesterday_cost > 0:
            cost_change_percent = ((total_cost - yesterday_cost) / yesterday_cost) * 100

        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
        cost_per_token = (total_cost / total_tokens) if total_tokens > 0 else 0

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_latency": row["avg_latency"] or 0,
            "avg_cost_per_request": row["avg_cost_per_request"] or 0,
            "errors": errors,
            "error_rate": error_rate,
            "cost_per_token": cost_per_token,
            "cost_change_percent": cost_change_percent,
            "time_window_minutes": time_window,
            "evaluated_at": datetime.utcnow().isoformat()
        }

    def check_conditions(self, rule: AlertRule, metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """
        Check if alert conditions are met.
        Supports complex logic: AND, OR, nested conditions
        """
        if not metrics:
            return False, {}

        logic = rule.logic
        if not logic:
            # Fallback to simple conditions
            return self.evaluate_simple_condition(rule.conditions, metrics)

        # Evaluate complex logic
        return self.evaluate_complex_logic(logic, metrics)

    def evaluate_simple_condition(self, conditions: List[Dict], metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Evaluate simple list of conditions (all must be true)"""
        results = []
        matched_conditions = []

        for condition in conditions:
            field = condition.get("field")
            metric = condition.get("metric")
            operator = condition.get("operator")
            threshold = condition.get("threshold")
            value = condition.get("value")

            # Determine what to compare
            if metric:
                compare_value = metrics.get(metric)
                if compare_value is None:
                    continue
                test_value = threshold
            elif field:
                # Direct field comparison
                compare_value = metrics.get(field)
                test_value = value
            else:
                continue

            # Perform comparison
            match = self.compare_values(compare_value, operator, test_value)
            results.append(match)

            if match:
                matched_conditions.append({
                    "metric": metric,
                    "field": field,
                    "operator": operator,
                    "value": test_value,
                    "actual": compare_value
                })

        # All conditions must be met
        all_met = len(results) > 0 and all(results)

        alert_data = {
            "triggered_conditions": matched_conditions,
            "all_metrics": metrics,
            "rule_type": "simple"
        }

        return all_met, alert_data

    def evaluate_complex_logic(self, logic: Dict[str, Any], metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Evaluate complex logic with AND/OR and nesting"""
        logic_type = logic.get("type", "AND")
        conditions = logic.get("conditions", [])

        results = []
        matched_conditions = []

        for condition in conditions:
            # Check if nested logic
            if "type" in condition:
                # Recursive call for nested logic
                nested_match, nested_data = self.evaluate_complex_logic(condition, metrics)
                results.append(nested_match)
                if nested_match:
                    matched_conditions.extend(nested_data.get("triggered_conditions", []))
            else:
                # Regular condition
                metric = condition.get("metric")
                field = condition.get("field")
                operator = condition.get("operator")
                threshold = condition.get("threshold")
                value = condition.get("value")

                if metric:
                    compare_value = metrics.get(metric)
                    test_value = threshold
                elif field:
                    compare_value = metrics.get(field)
                    test_value = value
                else:
                    continue

                match = self.compare_values(compare_value, operator, test_value)
                results.append(match)

                if match:
                    matched_conditions.append({
                        "metric": metric,
                        "field": field,
                        "operator": operator,
                        "value": test_value,
                        "actual": compare_value
                    })

        # Apply logic type
        if logic_type == "AND":
            final_match = len(results) > 0 and all(results)
        elif logic_type == "OR":
            final_match = len(results) > 0 and any(results)
        else:
            final_match = False

        alert_data = {
            "triggered_conditions": matched_conditions,
            "all_metrics": metrics,
            "rule_type": "complex",
            "logic_type": logic_type
        }

        return final_match, alert_data

    def compare_values(self, actual: float, operator: str, threshold: float) -> bool:
        """Compare actual value with threshold using operator"""
        if actual is None:
            return False

        try:
            actual = float(actual)
            threshold = float(threshold)

            if operator == ">":
                return actual > threshold
            elif operator == "<":
                return actual < threshold
            elif operator == ">=":
                return actual >= threshold
            elif operator == "<=":
                return actual <= threshold
            elif operator == "=":
                return actual == threshold
            elif operator == "!=":
                return actual != threshold
            else:
                return False
        except (ValueError, TypeError):
            return False

    async def trigger_alert(self, rule: AlertRule, alert_data: Dict[str, Any]):
        """Trigger an alert and send notifications"""
        # Generate alert ID
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{rule.id}"

        # Determine severity based on priority
        severity_map = {0: "critical", 1: "high", 2: "medium", 3: "low"}
        severity = severity_map.get(rule.priority, "medium")

        # Create description
        description = self.generate_alert_description(rule, alert_data)

        # Log to database
        alert_trigger = self.log_alert(alert_id, rule, description, severity, alert_data)

        # Send notifications
        await self.send_notifications(rule, alert_trigger)

        logger.info(f"🔔 Alert triggered: {rule.name} ({severity})")

    def generate_alert_description(self, rule: AlertRule, alert_data: Dict[str, Any]) -> str:
        """Generate human-readable alert description"""
        conditions = alert_data.get("triggered_conditions", [])

        if not conditions:
            return rule.description

        # Build description from triggered conditions
        parts = []
        for cond in conditions:
            metric = cond.get("metric") or cond.get("field", "unknown")
            operator = cond.get("operator")
            value = cond.get("value")
            actual = cond.get("actual")

            if actual is not None and value is not None:
                parts.append(f"{metric} {operator} {value} (actual: {actual:.2f})")
            else:
                parts.append(f"{metric} {operator} {value}")

        return f"{rule.name}: {' AND '.join(parts)}"

    def log_alert(self, alert_id: str, rule: AlertRule, description: str, severity: str, alert_data: Dict[str, Any]) -> AlertTrigger:
        """Log alert to database"""
        if not usage_tracker.enabled:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        triggered_at = datetime.utcnow().isoformat()

        # Insert into alert_history
        cursor.execute("""
            INSERT INTO alert_history (
                id, rule_id, rule_name, triggered_at, severity,
                alert_data_json, description, resolved, acknowledged
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_id,
            rule.id,
            rule.name,
            triggered_at,
            severity,
            json.dumps(alert_data),
            description,
            0,  # Not resolved
            0   # Not acknowledged
        ))

        # Update rule stats
        cursor.execute("""
            UPDATE alert_rules
            SET last_triggered = ?, trigger_count = trigger_count + 1
            WHERE id = ?
        """, (triggered_at, rule.id))

        conn.commit()
        conn.close()

        return AlertTrigger(
            id=alert_id,
            rule_id=rule.id,
            rule_name=rule.name,
            triggered_at=triggered_at,
            severity=severity,
            alert_data=alert_data,
            description=description
        )

    async def send_notifications(self, rule: AlertRule, alert: AlertTrigger):
        """Send notifications through configured channels"""
        actions = rule.actions
        channels = actions.get("channels", [])

        for channel_id in channels:
            try:
                await notification_service.send_alert(alert, channel_id)
            except Exception as e:
                logger.error(f"Failed to send notification to {channel_id}: {e}")
                # Log failed notification
                self.log_notification_failure(alert.id, channel_id, str(e))

    def log_notification_failure(self, alert_id: str, channel_id: str, error: str):
        """Log failed notification delivery"""
        if not usage_tracker.enabled:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO notification_history (id, alert_id, channel_id, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            alert_id,
            channel_id,
            "failed",
            error,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

    def update_last_triggered(self, rule: AlertRule):
        """Update rule's last triggered timestamp"""
        if not usage_tracker.enabled:
            return

        conn = sqlite3.connect(self.db_path)
        triggered_at = datetime.utcnow().isoformat()

        conn.execute("""
            UPDATE alert_rules
            SET last_triggered = ?
            WHERE id = ?
        """, (triggered_at, rule.id))

        conn.commit()
        conn.close()

        # Update in-memory rule
        rule.last_triggered = triggered_at

    def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        if not usage_tracker.enabled:
            return {}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        time_condition = datetime.utcnow() - timedelta(days=days)

        # Total triggered
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT rule_id) as unique_rules,
                SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN acknowledged = 1 THEN 1 ELSE 0 END) as acknowledged
            FROM alert_history
            WHERE triggered_at >= ?
        """, (time_condition.isoformat(),))

        row = cursor.fetchone()

        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alert_history
            WHERE triggered_at >= ?
            GROUP BY severity
        """, (time_condition.isoformat(),))

        severity_breakdown = {row["severity"]: row["count"] for row in cursor.fetchall()}

        conn.close()

        return {
            "total": row["total"] or 0,
            "unique_rules": row["unique_rules"] or 0,
            "resolved": row["resolved"] or 0,
            "acknowledged": row["acknowledged"] or 0,
            "open": (row["total"] or 0) - (row["resolved"] or 0),
            "severity_breakdown": severity_breakdown,
            "time_period_days": days
        }


# Singleton instance
alert_engine = AlertEngine()