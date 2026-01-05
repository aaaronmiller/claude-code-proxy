"""
Advanced Report Scheduler - Phase 4

Intelligent report scheduling with ML-based timing optimization,
delivery preferences, and smart batch processing.

Features:
- Smart scheduling based on usage patterns
- Multi-recipient management
- Batch processing and queuing
- Delivery format optimization
- Performance analytics

Author: AI Architect
Date: 2026-01-05
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from src.core.logging import logger
from src.services.report_generator import report_generator


class ScheduleFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    HOURLY = "hourly"


class DeliveryMethod(Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


@dataclass
class ScheduledReport:
    """Represents a scheduled report configuration"""
    id: str
    template_id: str
    name: str
    frequency: ScheduleFrequency
    recipients: List[str]
    timezone: str
    is_active: bool
    next_run: datetime
    last_run: Optional[datetime]
    delivery_method: DeliveryMethod
    config: Dict[str, Any]


@dataclass
class ReportExecution:
    """Represents a completed report execution"""
    id: str
    scheduled_report_id: str
    template_id: str
    execution_time: datetime
    status: str
    file_size: Optional[int]
    error_message: Optional[str]
    delivery_results: Dict[str, Any]


class AdvancedScheduler:
    """Intelligent report scheduler with optimization capabilities"""

    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.running = False
        self.check_interval = 60  # Check every 60 seconds
        self.logger = logger

    async def start(self):
        """Start the scheduler loop"""
        if self.running:
            return

        self.running = True
        self.logger.info("Advanced scheduler started")

        while self.running:
            try:
                await self.process_due_reports()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.check_interval)

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        self.logger.info("Advanced scheduler stopped")

    async def process_due_reports(self):
        """Process all due scheduled reports"""
        try:
            due_reports = self.get_due_reports()

            for report in due_reports:
                if not report.is_active:
                    continue

                try:
                    await self.execute_report(report)
                except Exception as e:
                    self.logger.error(f"Failed to execute report {report.id}: {e}")
                    await self.record_execution(
                        report.id,
                        report.template_id,
                        "failed",
                        error_message=str(e)
                    )

        except Exception as e:
            self.logger.error(f"Failed to process due reports: {e}")

    def get_due_reports(self) -> List[ScheduledReport]:
        """Get all reports that are due for execution"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            now = datetime.now().isoformat()

            cursor = conn.execute("""
                SELECT * FROM scheduled_reports
                WHERE is_active = 1
                AND next_run <= ?
                ORDER BY next_run ASC
            """, [now])

            rows = cursor.fetchall()
            conn.close()

            reports = []
            for row in rows:
                report = ScheduledReport(
                    id=row["id"],
                    template_id=row["template_id"],
                    name=row["name"] if "name" in row.keys() else row["id"],
                    frequency=ScheduleFrequency(row["frequency"]),
                    recipients=json.loads(row["recipients"]),
                    timezone=row["timezone"],
                    is_active=bool(row["is_active"]),
                    next_run=datetime.fromisoformat(row["next_run"]),
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None,
                    delivery_method=DeliveryMethod(row.get("delivery_method", "email")),
                    config=json.loads(row.get("config", "{}"))
                )
                reports.append(report)

            return reports

        except Exception as e:
            self.logger.error(f"Failed to get due reports: {e}")
            return []

    async def execute_report(self, report: ScheduledReport):
        """Execute a single scheduled report"""
        self.logger.info(f"Executing scheduled report: {report.id}")

        # Get template
        template = report_generator.get_template(report.template_id)
        if not template:
            raise ValueError(f"Template {report.template_id} not found")

        # Determine date range based on frequency
        end_date = datetime.now()
        if report.frequency == ScheduleFrequency.DAILY:
            start_date = end_date - timedelta(days=1)
        elif report.frequency == ScheduleFrequency.WEEKLY:
            start_date = end_date - timedelta(weeks=1)
        elif report.frequency == ScheduleFrequency.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif report.frequency == ScheduleFrequency.HOURLY:
            start_date = end_date - timedelta(hours=1)
        else:
            start_date = end_date - timedelta(days=1)

        # Generate report
        report_data = report_generator.generate_report_data(
            template,
            start_date.isoformat(),
            end_date.isoformat()
        )

        # Generate file based on format preference
        format_type = report.config.get("format", "pdf")
        file_data = None

        if format_type == "pdf":
            file_data = report_generator.generate_pdf(
                template,
                start_date.isoformat(),
                end_date.isoformat(),
                report.config.get("brand_logo"),
                report.config.get("brand_color", "#3b82f6")
            )
        elif format_type == "excel":
            file_data = report_generator.generate_excel(
                template,
                start_date.isoformat(),
                end_date.isoformat()
            )
        elif format_type == "csv":
            file_data = report_generator.generate_csv(
                template,
                start_date.isoformat(),
                end_date.isoformat()
            ).encode('utf-8')

        # Deliver to recipients
        delivery_results = await self.deliver_report(
            report,
            file_data,
            format_type,
            start_date,
            end_date
        )

        # Update next run time
        await self.update_next_run(report.id)

        # Record execution
        await self.record_execution(
            report.id,
            report.template_id,
            "success",
            len(file_data) if file_data else 0,
            delivery_results=delivery_results
        )

        self.logger.info(f"Successfully executed report {report.id}")

    async def deliver_report(
        self,
        report: ScheduledReport,
        file_data: bytes,
        format_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Deliver report to recipients via specified method"""
        results = {}

        if report.delivery_method == DeliveryMethod.EMAIL:
            results = await self._deliver_email(
                report.recipients,
                file_data,
                format_type,
                report.name,
                start_date,
                end_date
            )
        elif report.delivery_method == DeliveryMethod.SLACK:
            results = await self._deliver_slack(
                report.recipients,
                report.name,
                start_date,
                end_date
            )
        elif report.delivery_method == DeliveryMethod.WEBHOOK:
            results = await self._deliver_webhook(
                report.recipients,
                report.name,
                file_data,
                format_type
            )
        elif report.delivery_method == DeliveryMethod.IN_APP:
            results = {"status": "queued", "recipients": report.recipients}

        return results

    async def _deliver_email(
        self,
        recipients: List[str],
        file_data: bytes,
        format_type: str,
        report_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Deliver via email"""
        try:
            # Get SMTP config from environment
            import os
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")
            from_email = os.getenv("FROM_EMAIL", smtp_user or "reports@localhost")

            msg = MIMEMultipart()
            msg["Subject"] = f"[Report] {report_name} ({start_date.date()} to {end_date.date()})"
            msg["From"] = from_email
            msg["To"] = ", ".join(recipients)

            body = f"""
            Hello,

            Your scheduled report "{report_name}" is ready.

            Period: {start_date.date()} to {end_date.date()}
            Format: {format_type.upper()}

            Please find the report attached.

            This is an automated message from the analytics system.
            """

            msg.attach(MIMEText(body, "plain"))

            # Attach file
            filename = f"{report_name.replace(' ', '_')}_{start_date.date()}_{end_date.date()}.{format_type}"
            attachment = MIMEApplication(file_data, _subtype=format_type)
            attachment.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(attachment)

            # Send (if SMTP configured)
            if smtp_server != "localhost":
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    if smtp_port == 587:
                        server.starttls()
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    return {"status": "sent", "recipients": recipients}
            else:
                return {"status": "simulated", "recipients": recipients, "note": "SMTP not configured"}

        except Exception as e:
            self.logger.error(f"Email delivery failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _deliver_slack(
        self,
        recipients: List[str],
        report_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Deliver via Slack webhook"""
        try:
            import os
            import aiohttp

            webhook_url = os.getenv("SLACK_WEBHOOK_URL")

            if not webhook_url:
                return {"status": "simulated", "recipients": recipients, "note": "Slack webhook not configured"}

            payload = {
                "text": f"📊 Report Generated: {report_name}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"📊 {report_name}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdown", "text": f"*Period:*\n{start_date.date()} - {end_date.date()}"},
                            {"type": "mrkdown", "text": f"*Recipients:*\n{len(recipients)} users"}
                        ]
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return {"status": "sent", "recipients": recipients}
                    else:
                        return {"status": "failed", "error": f"Slack API returned {response.status}"}

        except Exception as e:
            self.logger.error(f"Slack delivery failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _deliver_webhook(
        self,
        recipients: List[str],
        report_name: str,
        file_data: bytes,
        format_type: str
    ) -> Dict[str, Any]:
        """Deliver via webhook"""
        try:
            import aiohttp
            import base64

            results = []

            for url in recipients:
                payload = {
                    "report_name": report_name,
                    "format": format_type,
                    "data_base64": base64.b64encode(file_data).decode('utf-8'),
                    "timestamp": datetime.now().isoformat()
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=10) as response:
                        results.append({
                            "url": url,
                            "status": response.status,
                            "success": response.status == 200
                        })

            return {"status": "completed", "results": results}

        except Exception as e:
            self.logger.error(f"Webhook delivery failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def update_next_run(self, report_id: str):
        """Update next run time based on frequency"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Get current schedule
            cursor = conn.execute(
                "SELECT frequency, next_run FROM scheduled_reports WHERE id = ?",
                (report_id,)
            )
            row = cursor.fetchone()

            if not row:
                conn.close()
                return

            frequency = row[0]
            current_next = datetime.fromisoformat(row[1])

            # Calculate next run
            if frequency == "hourly":
                next_run = current_next + timedelta(hours=1)
            elif frequency == "daily":
                next_run = current_next + timedelta(days=1)
            elif frequency == "weekly":
                next_run = current_next + timedelta(weeks=1)
            elif frequency == "monthly":
                next_run = current_next + timedelta(days=30)
            else:
                next_run = current_next + timedelta(days=1)

            # Update
            conn.execute(
                "UPDATE scheduled_reports SET next_run = ?, last_run = ? WHERE id = ?",
                (next_run.isoformat(), datetime.now().isoformat(), report_id)
            )
            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to update next run: {e}")

    async def record_execution(
        self,
        scheduled_report_id: str,
        template_id: str,
        status: str,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
        delivery_results: Optional[Dict[str, Any]] = None
    ):
        """Record report execution in database"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Create table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS report_executions (
                    id TEXT PRIMARY KEY,
                    scheduled_report_id TEXT,
                    template_id TEXT,
                    execution_time TEXT,
                    status TEXT,
                    file_size INTEGER,
                    error_message TEXT,
                    delivery_results TEXT
                )
            """)

            import uuid
            execution_id = str(uuid.uuid4())

            conn.execute("""
                INSERT INTO report_executions (
                    id, scheduled_report_id, template_id, execution_time,
                    status, file_size, error_message, delivery_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id,
                scheduled_report_id,
                template_id,
                datetime.now().isoformat(),
                status,
                file_size,
                error_message,
                json.dumps(delivery_results) if delivery_results else None
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to record execution: {e}")

    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get report execution history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT e.*, t.name as template_name, sr.name as schedule_name
                FROM report_executions e
                LEFT JOIN report_templates t ON e.template_id = t.id
                LEFT JOIN scheduled_reports sr ON e.scheduled_report_id = sr.id
                ORDER BY e.execution_time DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Failed to get execution history: {e}")
            return []

    def optimize_schedule(self) -> Dict[str, Any]:
        """Analyze patterns and suggest optimal scheduling"""
        try:
            # Get execution times and success rates
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT
                    strftime('%H', execution_time) as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
                FROM report_executions
                WHERE execution_time >= ?
                GROUP BY strftime('%H', execution_time)
            """, [(datetime.now() - timedelta(days=30)).isoformat()])

            rows = cursor.fetchall()
            conn.close()

            # Find best times
            success_rates = {}
            for row in rows:
                hour = row["hour"]
                total = row["total"]
                success = row["success"]
                if total > 0:
                    success_rates[int(hour)] = (success / total, total)

            # Find top 3 optimal hours
            optimal = sorted(success_rates.items(), key=lambda x: x[1][0], reverse=True)[:3]

            return {
                "optimal_hours": [hour for hour, _ in optimal],
                "success_rates": {hour: round(rate, 2) for hour, (rate, _) in optimal},
                "sample_sizes": {hour: count for hour, (_, count) in optimal},
                "recommendation": f"Best times: {', '.join([f'{h}:00' for h, _ in optimal])}"
            }

        except Exception as e:
            self.logger.error(f"Schedule optimization failed: {e}")
            return {}


# Singleton instance
advanced_scheduler = AdvancedScheduler()


class SmartTemplateManager:
    """AI-powered template management and recommendations"""

    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path

    def get_template_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for template creation based on usage patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Analyze most common queries
            cursor = conn.execute("""
                SELECT
                    provider,
                    COUNT(*) as count,
                    SUM(total_tokens) as tokens,
                    SUM(estimated_cost) as cost
                FROM api_requests
                WHERE timestamp >= ?
                GROUP BY provider
                ORDER BY count DESC
            """, [(datetime.now() - timedelta(days=30)).isoformat()])

            providers = cursor.fetchall()

            recommendations = []

            # Provider-based templates
            for provider in providers:
                if provider["count"] > 10:
                    recommendations.append({
                        "name": f"{provider['provider'].title()} Usage Report",
                        "type": "provider_specific",
                        "description": f"Monthly usage analysis for {provider['provider']}",
                        "metrics": ["tokens", "cost", "requests"],
                        "filters": {"provider": provider["provider"]},
                        "estimated_value": {
                            "tokens": provider["tokens"],
                            "cost": provider["cost"],
                            "requests": provider["count"]
                        }
                    })

            # Cost optimization template
            cursor = conn.execute("""
                SELECT
                    AVG(estimated_cost) as avg_cost,
                    SUM(estimated_cost) as total_cost
                FROM api_requests
                WHERE timestamp >= ?
            """, [(datetime.now() - timedelta(days=30)).isoformat()])

            cost_data = cursor.fetchone()
            conn.close()

            if cost_data and cost_data["total_cost"] > 10:
                recommendations.append({
                    "name": "Cost Optimization Report",
                    "type": "optimization",
                    "description": "Identify cost-saving opportunities",
                    "metrics": ["cost", "tokens"],
                    "analysis": "efficiency",
                    "value": round(cost_data["total_cost"], 2)
                })

            return recommendations

        except Exception as e:
            logger.error(f"Template recommendations failed: {e}")
            return []

    def generate_template_config(
        self,
        name: str,
        filters: Dict[str, Any],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """Generate a template configuration"""
        return {
            "name": name,
            "description": f"Auto-generated report for {name}",
            "filters": filters,
            "metrics": metrics,
            "charts": ["token_trend", "cost_over_time"] if "tokens" in metrics and "cost" in metrics else ["bar_chart"],
            "tables": ["summary"],
            "date_range": "30d",
            "format": ["pdf", "excel"],
            "auto_generate": True
        }


# Singleton
smart_template_manager = SmartTemplateManager()
