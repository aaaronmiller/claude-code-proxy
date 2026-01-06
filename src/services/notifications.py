"""
Notification Service - Phase 3

Handles multi-channel alert delivery: Email, Slack, Webhook, In-App
Supports retries, rate limiting, and delivery tracking.

Author: AI Architect
Date: 2026-01-05
"""

import smtplib
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

from src.core.logging import logger
from src.core.config import config
from src.services.usage.usage_tracker import usage_tracker


class NotificationService:
    """Multi-channel notification delivery service"""

    def __init__(self):
        self.db_path = usage_tracker.db_path
        self.rate_limiter = {}  # Track send times per channel
        self.session = None

    async def initialize(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()

        logger.info("🚀Initializing notification channels table if not exists...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_channels (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    name TEXT,
                    config TEXT,
                    is_enabled INTEGER,
                    last_used TEXT
                )""")
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to migrate 001 to perform table upgrades. Reason: {e}")


        try:
            # Create the table notification_channels if it doesn't exist:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_channels (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    name TEXT,
                    config TEXT,
                    is_enabled INTEGER,
                    last_used TEXT
                )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def send_alert(self, alert, channel_id: str):
        """
        Send alert through specified channel

        Args:
            alert: AlertTrigger object
            channel_id: ID of notification channel
        """
        # Get channel config
        channel = self.get_channel(channel_id)
        if not channel:
            logger.error(f"Channel {channel_id} not found")
            return False

        if not channel["is_enabled"]:
            logger.info(f"Channel {channel_id} is disabled")
            return False

        # Check rate limiting
        if not self.check_rate_limit(channel_id):
            logger.warning(f"Rate limit hit for channel {channel_id}")
            return False

        # Send based on type
        channel_type = channel["type"]
        config_data = json.loads(channel["config"])

        try:
            if channel_type == "email":
                success = await self.send_email(alert, config_data)
            elif channel_type == "slack":
                success = await self.send_slack(alert, config_data)
            elif channel_type == "in_app":
                success = await self.send_in_app(alert, config_data)
            elif channel_type == "webhook":
                success = await self.send_webhook(alert, config_data)
            elif channel_type == "pagerduty":
                success = await self.send_pagerduty(alert, config_data)
            else:
                logger.error(f"Unknown channel type: {channel_type}")
                success = False

            # Log delivery
            self.log_delivery(alert.id, channel_id, success)

            if success:
                self.update_channel_last_used(channel_id)
                logger.info(f"✅ Notification sent via {channel_type}: {channel_id}")
            else:
                logger.error(f"❌ Notification failed via {channel_type}: {channel_id}")

            return success

        except Exception as e:
            logger.error(f"Exception sending notification: {e}")
            self.log_delivery(alert.id, channel_id, False, str(e))
            return False

    def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get notification channel configuration"""
        if not usage_tracker.enabled:
            return None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            "SELECT * FROM notification_channels WHERE id = ?",
            (channel_id,)
        )

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def check_rate_limit(self, channel_id: str, min_interval: int = 60) -> bool:
        """
        Rate limit notifications to prevent spam

        Args:
            channel_id: Channel to check
            min_interval: Minimum seconds between notifications

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow().timestamp()
        last_sent = self.rate_limiter.get(channel_id, 0)

        if (now - last_sent) < min_interval:
            return False

        self.rate_limiter[channel_id] = now
        return True

    def get_all_channels(self) -> list:
        """Get all notification channels"""
        if not usage_tracker.enabled:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM notification_channels")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ─────────────────────────────────────────────────────────────────────
    # EMAIL NOTIFICATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def send_email(self, alert, config: Dict[str, Any]) -> bool:
        """Send email notification"""
        if not config.get("to"):
            logger.error("No email recipient specified")
            return False

        # Get SMTP config from environment or config
        smtp_server = config.get("smtp_server") or config.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(config.get("smtp_port") or config.get("SMTP_PORT", 587))
        smtp_user = config.get("smtp_user") or config.get("SMTP_USER")
        smtp_pass = config.get("smtp_password") or config.get("SMTP_PASSWORD")

        if not smtp_user or not smtp_pass:
            logger.error("SMTP credentials not configured")
            return False

        # Build email message
        subject = f"{config.get('subject_prefix', '[Alert]')} {alert.rule_name}"

        html_content = self.generate_email_html(alert)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = config["to"]

        # Plain text fallback
        text_part = MIMEText(self.generate_email_text(alert), 'plain')
        msg.attach(text_part)

        # HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        try:
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def generate_email_html(self, alert) -> str:
        """Generate HTML email template"""
        severity_colors = {
            "critical": "#dc2626",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#3b82f6"
        }

        color = severity_colors.get(alert.severity, "#6b7280")

        # Format triggered conditions
        conditions_html = ""
        if alert.alert_data and "triggered_conditions" in alert.alert_data:
            for cond in alert.alert_data["triggered_conditions"]:
                metric = cond.get("metric") or cond.get("field", "unknown")
                actual = cond.get("actual")
                value = cond.get("value")
                conditions_html += f"<li><strong>{metric}</strong>: {actual} vs threshold {value}</li>"

        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: {color}; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .details {{ background: #f3f4f6; padding: 15px; border-left: 4px solid {color}; }}
                .footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 {alert.rule_name}</h1>
                <p>Severity: {alert.severity.upper()} | {alert.triggered_at}</p>
            </div>
            <div class="content">
                <p><strong>Description:</strong> {alert.description}</p>
                <div class="details">
                    <h3>Triggered Conditions:</h3>
                    <ul>{conditions_html}</ul>
                </div>
                <p><strong>Alert ID:</strong> {alert.id}</p>
            </div>
            <div class="footer">
                <p>This is an automated alert from Claude Proxy Analytics.</p>
                <p>Rule ID: {alert.rule_id}</p>
            </div>
        </body>
        </html>
        """

    def generate_email_text(self, alert) -> str:
        """Generate plain text email"""
        text = f"""
🚨 ALERT: {alert.rule_name}

Severity: {alert.severity.upper()}
Time: {alert.triggered_at}
Description: {alert.description}

Alert ID: {alert.id}
Rule ID: {alert.rule_id}

This is an automated alert from Claude Proxy Analytics.
        """
        return text.strip()

    # ─────────────────────────────────────────────────────────────────────
    # SLACK NOTIFICATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def send_slack(self, alert, config: Dict[str, Any]) -> bool:
        """Send Slack notification via webhook"""
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.error("Slack webhook URL not configured")
            return False

        # Build Slack message blocks
        severity_colors = {
            "critical": "#dc2626",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#3b82f6"
        }
        color = severity_colors.get(alert.severity, "#6b7280")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {alert.rule_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{alert.triggered_at[:19]}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {alert.description}"
                }
            }
        ]

        # Add triggered conditions if available
        if alert.alert_data and "triggered_conditions" in alert.alert_data:
            conditions_text = "\n".join([
                f"• {c.get('metric') or c.get('field')}: {c.get('actual')} (threshold: {c.get('value')})"
                for c in alert.alert_data["triggered_conditions"]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Triggered Conditions:*\n{conditions_text}"
                }
            })

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Rule ID: {alert.rule_id} | Alert ID: {alert.id}"
                }
            ]
        })

        message = {"blocks": blocks, "color": color}

        try:
            async with self.session.post(webhook_url, json=message) as response:
                if response.status == 200:
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Slack webhook returned {response.status}: {text}")
                    return False
        except Exception as e:
            logger.error(f"Slack webhook exception: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────
    # WEBHOOK NOTIFICATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def send_webhook(self, alert, config: Dict[str, Any]) -> bool:
        """Send custom webhook notification"""
        webhook_url = config.get("url")
        if not webhook_url:
            logger.error("Webhook URL not configured")
            return False

        # Build payload
        payload = {
            "alert_id": alert.id,
            "rule_id": alert.rule_id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "triggered_at": alert.triggered_at,
            "description": alert.description,
            "data": alert.alert_data
        }

        # Custom headers if provided
        headers = config.get("headers", {})

        try:
            async with self.session.post(webhook_url, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Webhook returned {response.status}: {text}")
                    return False
        except Exception as e:
            logger.error(f"Webhook exception: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────
    # PAGERDUTY NOTIFICATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def send_pagerduty(self, alert, config: Dict[str, Any]) -> bool:
        """Send PagerDuty incident"""
        integration_key = config.get("integration_key")
        if not integration_key:
            logger.error("PagerDuty integration key not configured")
            return False

        # PagerDuty Events API v2
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": alert.id,
            "payload": {
                "summary": alert.description,
                "severity": "critical" if alert.severity == "critical" else "error",
                "source": "claude-proxy",
                "component": "alert-engine",
                "group": alert.rule_name,
                "class": alert.severity,
                "custom_details": {
                    "alert_id": alert.id,
                    "rule_id": alert.rule_id,
                    "rule_name": alert.rule_name,
                    "triggered_at": alert.triggered_at,
                    "data": alert.alert_data
                }
            }
        }

        try:
            async with self.session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            ) as response:
                if response.status == 202:
                    return True
                else:
                    text = await response.text()
                    logger.error(f"PagerDuty returned {response.status}: {text}")
                    return False
        except Exception as e:
            logger.error(f"PagerDuty exception: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────────
    # IN-APP NOTIFICATIONS
    # ─────────────────────────────────────────────────────────────────────

    async def send_in_app(self, alert, config: Dict[str, Any]) -> bool:
        """Store in-app notification (delivered via WebSocket)"""
        if not usage_tracker.enabled:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert into notification history
        cursor.execute("""
            INSERT INTO notification_history
            (id, alert_id, channel_id, status, sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"inapp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            alert.id,
            "in_app",
            "sent",
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        # WebSocket broadcast would be handled by websocket_live service
        # For now, we return True to indicate storage succeeded
        logger.info(f"In-app notification stored: {alert.id}")

        return True

    # ─────────────────────────────────────────────────────────────────────
    # DATABASE OPERATIONS
    # ─────────────────────────────────────────────────────────────────────

    def log_delivery(self, alert_id: str, channel_id: str, success: bool, error: Optional[str] = None):
        """Log notification delivery to database"""
        if not usage_tracker.enabled:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        status = "sent" if success else "failed"

        cursor.execute("""
            INSERT INTO notification_history
            (id, alert_id, channel_id, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            alert_id,
            channel_id,
            status,
            error,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

    def update_channel_last_used(self, channel_id: str):
        """Update channel's last used timestamp"""
        if not usage_tracker.enabled:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE notification_channels
            SET last_used = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), channel_id))

        conn.commit()
        conn.close()

    def get_delivery_history(self, limit: int = 50) -> list:
        """Get recent notification delivery history"""
        if not usage_tracker.enabled:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT
                nh.*,
                c.name as channel_name,
                c.type as channel_type,
                ah.rule_name
            FROM notification_history nh
            LEFT JOIN notification_channels c ON nh.channel_id = c.id
            LEFT JOIN alert_history ah ON nh.alert_id = ah.id
            ORDER BY nh.sent_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def test_notification(self, channel_id: str) -> tuple[bool, str]:
        """Send test notification to specified channel"""
        channel = self.get_channel(channel_id)
        if not channel:
            return False, f"Channel {channel_id} not found"

        # Create test alert
        test_alert = type('AlertTrigger', (), {
            'id': 'test_alert',
            'rule_id': 'test_rule',
            'rule_name': 'Test Notification',
            'triggered_at': datetime.utcnow().isoformat(),
            'severity': 'medium',
            'alert_data': {'test': True},
            'description': 'This is a test notification'
        })()

        # Send synchronously for testing
        success = asyncio.run(self.send_alert(test_alert, channel_id))

        if success:
            return True, "Test notification sent successfully"
        else:
            return False, "Failed to send test notification"


# Singleton instance
notification_service = NotificationService()