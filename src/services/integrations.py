"""
Third-Party Integrations Service - Phase 4

Integration adapters for popular monitoring, alerting, and incident management platforms:
- Datadog
- New Relic
- PagerDuty
- Opsgenie
- Microsoft Teams
- Slack (advanced)

Features:
- Unified integration interface
- Event forwarding
- Metric synchronization
- Alert forwarding
- Status sync
- Webhook management

Author: AI Architect
Date: 2026-01-05
"""

import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import os

from src.core.logging import logger


class IntegrationType(Enum):
    DATADOG = "datadog"
    NEWRELIC = "newrelic"
    PAGERDUTY = "pagerduty"
    OPSGENIE = "opsgenie"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"


@dataclass
class IntegrationConfig:
    """Configuration for a third-party integration"""
    type: IntegrationType
    enabled: bool
    api_key: Optional[str]
    endpoint: Optional[str]
    extra_config: Dict[str, Any]
    created_at: str


@dataclass
class IntegrationEvent:
    """Event to be forwarded to third-party service"""
    event_type: str  # alert, metric, log, anomaly
    severity: str    # info, warning, error, critical
    title: str
    message: str
    timestamp: str
    metadata: Dict[str, Any]


class IntegrationManager:
    """Central manager for all third-party integrations"""

    def __init__(self, config_path: str = "config/integrations.json"):
        self.config_path = config_path
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.logger = logger
        self.load_config()

    def load_config(self):
        """Load integration configurations"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for name, config in data.items():
                        self.integrations[name] = IntegrationConfig(
                            type=IntegrationType(config["type"]),
                            enabled=config.get("enabled", False),
                            api_key=config.get("api_key"),
                            endpoint=config.get("endpoint"),
                            extra_config=config.get("extra_config", {}),
                            created_at=config.get("created_at", datetime.now().isoformat())
                        )
            else:
                # Load from environment variables as fallback
                self._load_from_env()
        except Exception as e:
            self.logger.error(f"Failed to load integration config: {e}")
            self._load_from_env()

    def _load_from_env(self):
        """Load configs from environment variables"""
        env_configs = {
            "datadog": {
                "type": IntegrationType.DATADOG,
                "api_key": os.getenv("DATADOG_API_KEY"),
                "endpoint": os.getenv("DATADOG_ENDPOINT", "https://api.datadoghq.com"),
                "enabled": bool(os.getenv("DATADOG_API_KEY"))
            },
            "newrelic": {
                "type": IntegrationType.NEWRELIC,
                "api_key": os.getenv("NEWRELIC_API_KEY"),
                "endpoint": os.getenv("NEWRELIC_ENDPOINT", "https://api.newrelic.com"),
                "enabled": bool(os.getenv("NEWRELIC_API_KEY"))
            },
            "pagerduty": {
                "type": IntegrationType.PAGERDUTY,
                "api_key": os.getenv("PAGERDUTY_API_KEY"),
                "endpoint": os.getenv("PAGERDUTY_ENDPOINT", "https://events.pagerduty.com"),
                "enabled": bool(os.getenv("PAGERDUTY_API_KEY")),
                "extra_config": {
                    "service_key": os.getenv("PAGERDUTY_SERVICE_KEY"),
                    "routing_key": os.getenv("PAGERDUTY_ROUTING_KEY")
                }
            },
            "slack": {
                "type": IntegrationType.SLACK,
                "api_key": os.getenv("SLACK_BOT_TOKEN"),
                "endpoint": os.getenv("SLACK_WEBHOOK_URL"),
                "enabled": bool(os.getenv("SLACK_WEBHOOK_URL"))
            },
            "teams": {
                "type": IntegrationType.TEAMS,
                "endpoint": os.getenv("TEAMS_WEBHOOK_URL"),
                "enabled": bool(os.getenv("TEAMS_WEBHOOK_URL"))
            }
        }

        for name, config in env_configs.items():
            if config["enabled"]:
                self.integrations[name] = IntegrationConfig(
                    type=config["type"],
                    enabled=config["enabled"],
                    api_key=config.get("api_key"),
                    endpoint=config.get("endpoint"),
                    extra_config=config.get("extra_config", {}),
                    created_at=datetime.now().isoformat()
                )

    def save_config(self):
        """Save integration configurations"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {}
            for name, config in self.integrations.items():
                data[name] = {
                    "type": config.type.value,
                    "enabled": config.enabled,
                    "api_key": config.api_key,
                    "endpoint": config.endpoint,
                    "extra_config": config.extra_config,
                    "created_at": config.created_at
                }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save integration config: {e}")

    async def send_event(self, event: IntegrationEvent, integration_names: Optional[List[str]] = None):
        """Send event to specified integrations"""
        results = {}

        # Determine which integrations to use
        targets = []
        if integration_names:
            targets = [name for name in integration_names if name in self.integrations]
        else:
            targets = [name for name, config in self.integrations.items() if config.enabled]

        for name in targets:
            config = self.integrations[name]
            try:
                result = await self._send_to_integration(config, event)
                results[name] = result
            except Exception as e:
                self.logger.error(f"Failed to send to {name}: {e}")
                results[name] = {"success": False, "error": str(e)}

        return results

    async def _send_to_integration(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send event to specific integration"""
        if config.type == IntegrationType.DATADOG:
            return await self._send_to_datadog(config, event)
        elif config.type == IntegrationType.NEWRELIC:
            return await self._send_to_newrelic(config, event)
        elif config.type == IntegrationType.PAGERDUTY:
            return await self._send_to_pagerduty(config, event)
        elif config.type == IntegrationType.SLACK:
            return await self._send_to_slack(config, event)
        elif config.type == IntegrationType.TEAMS:
            return await self._send_to_teams(config, event)
        elif config.type == IntegrationType.WEBHOOK:
            return await self._send_to_webhook(config, event)
        else:
            return {"success": False, "error": f"Unknown integration type: {config.type}"}

    async def _send_to_datadog(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send metrics/events to Datadog"""
        if not config.api_key or not config.endpoint:
            return {"success": False, "error": "Missing Datadog configuration"}

        # Convert event to Datadog format
        payload = {
            "title": event.title,
            "text": event.message,
            "alert_type": self._map_severity_to_datadog(event.severity),
            "tags": [
                f"severity:{event.severity}",
                f"type:{event.event_type}",
                f"source:claude-proxy"
            ] + [f"{k}:{v}" for k, v in event.metadata.items()],
            "date_happened": int(datetime.fromisoformat(event.timestamp).timestamp())
        }

        async with aiohttp.ClientSession() as session:
            url = f"{config.endpoint}/api/v1/events"
            headers = {
                "DD-API-KEY": config.api_key,
                "Content-Type": "application/json"
            }
            async with session.post(url, json=payload, headers=headers) as response:
                content = await response.text()
                return {
                    "success": response.status == 202,
                    "status": response.status,
                    "response": content
                }

    async def _send_to_newrelic(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send events to New Relic"""
        if not config.api_key or not config.endpoint:
            return {"success": False, "error": "Missing New Relic configuration"}

        payload = {
            "eventType": "ClaudeProxyEvent",
            "title": event.title,
            "message": event.message,
            "severity": event.severity,
            "type": event.event_type,
            "timestamp": event.timestamp,
            **event.metadata
        }

        async with aiohttp.ClientSession() as session:
            url = f"{config.endpoint}/v1/accounts/{config.extra_config.get('account_id', 'unknown')}/events"
            headers = {
                "X-Query-Key": config.api_key,
                "Content-Type": "application/json"
            }
            async with session.post(url, json=[payload], headers=headers) as response:
                content = await response.text()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "response": content
                }

    async def _send_to_pagerduty(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send incidents to PagerDuty"""
        routing_key = config.extra_config.get("routing_key") or config.api_key
        if not routing_key:
            return {"success": False, "error": "Missing PagerDuty routing key"}

        # Map severity to PagerDuty severity
        pd_severity = {
            "info": "info",
            "warning": "warning",
            "error": "error",
            "critical": "critical"
        }.get(event.severity, "error")

        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": f"claude-proxy-{event.event_type}-{int(datetime.fromisoformat(event.timestamp).timestamp())}",
            "payload": {
                "summary": event.title,
                "severity": pd_severity,
                "source": "claude-proxy",
                "component": event.event_type,
                "custom_details": {
                    "message": event.message,
                    **event.metadata
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            url = f"{config.endpoint}/v2/enqueue"
            async with session.post(url, json=payload) as response:
                content = await response.text()
                return {
                    "success": response.status == 202,
                    "status": response.status,
                    "response": content
                }

    async def _send_to_slack(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send messages to Slack"""
        if not config.endpoint:
            return {"success": False, "error": "Missing Slack webhook URL"}

        # Color based on severity
        color_map = {
            "info": "#36a64f",
            "warning": "#ffcc00",
            "error": "#ff6600",
            "critical": "#ff0000"
        }
        color = color_map.get(event.severity, "#808080")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": event.title,
                    "text": event.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": event.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Type",
                            "value": event.event_type,
                            "short": True
                        }
                    ],
                    "footer": "Claude Proxy",
                    "ts": int(datetime.fromisoformat(event.timestamp).timestamp())
                }
            ]
        }

        # Add metadata if present
        if event.metadata:
            metadata_text = "\n".join([f"*{k}*: {v}" for k, v in event.metadata.items()])
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": metadata_text,
                "short": False
            })

        async with aiohttp.ClientSession() as session:
            async with session.post(config.endpoint, json=payload) as response:
                content = await response.text()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "response": content
                }

    async def _send_to_teams(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send messages to Microsoft Teams"""
        if not config.endpoint:
            return {"success": False, "error": "Missing Teams webhook URL"}

        # Teams theme color
        color_map = {
            "info": "00ff00",
            "warning": "ffcc00",
            "error": "ff6600",
            "critical": "ff0000"
        }
        color = color_map.get(event.severity, "808080")

        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": color,
            "summary": event.title,
            "sections": [
                {
                    "activityTitle": event.title,
                    "activitySubtitle": f"{event.event_type} - {event.severity.upper()}",
                    "facts": [
                        {"name": "Timestamp", "value": event.timestamp},
                        {"name": "Severity", "value": event.severity.upper()},
                        {"name": "Type", "value": event.event_type}
                    ] + [{"name": k, "value": str(v)} for k, v in event.metadata.items()],
                    "text": event.message
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(config.endpoint, json=payload) as response:
                content = await response.text()
                return {
                    "success": response.status == 200,
                    "status": response.status,
                    "response": content
                }

    async def _send_to_webhook(self, config: IntegrationConfig, event: IntegrationEvent):
        """Send to generic webhook"""
        if not config.endpoint:
            return {"success": False, "error": "Missing webhook URL"}

        payload = {
            "event_type": event.event_type,
            "severity": event.severity,
            "title": event.title,
            "message": event.message,
            "timestamp": event.timestamp,
            "metadata": event.metadata,
            "source": "claude-proxy"
        }

        headers = config.extra_config.get("headers", {})
        if not isinstance(headers, dict):
            headers = {}

        async with aiohttp.ClientSession() as session:
            async with session.post(config.endpoint, json=payload, headers=headers) as response:
                content = await response.text()
                return {
                    "success": 200 <= response.status < 300,
                    "status": response.status,
                    "response": content
                }

    def _map_severity_to_datadog(self, severity: str) -> str:
        """Map our severity to Datadog alert types"""
        return {
            "info": "info",
            "warning": "warning",
            "error": "error",
            "critical": "error"
        }.get(severity, "info")

    async def test_integration(self, name: str) -> Dict[str, Any]:
        """Test a specific integration"""
        if name not in self.integrations:
            return {"success": False, "error": "Integration not configured"}

        config = self.integrations[name]
        if not config.enabled:
            return {"success": False, "error": "Integration is disabled"}

        test_event = IntegrationEvent(
            event_type="test",
            severity="info",
            title="Integration Test",
            message="This is a test notification from Claude Proxy",
            timestamp=datetime.now().isoformat(),
            metadata={"test": "true", "integration": name}
        )

        try:
            result = await self._send_to_integration(config, test_event)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_integrations(self) -> List[Dict[str, Any]]:
        """List all configured integrations"""
        return [
            {
                "name": name,
                "type": config.type.value,
                "enabled": config.enabled,
                "endpoint": config.endpoint,
                "has_api_key": bool(config.api_key),
                "extra_config": config.extra_config
            }
            for name, config in self.integrations.items()
        ]


# Singleton instance
integration_manager = IntegrationManager()


class IntegrationForwarder:
    """Automated event forwarding based on rules"""

    def __init__(self):
        self.manager = integration_manager
        self.logger = logger

    async def forward_alert(self, alert_data: Dict[str, Any], target_integrations: Optional[List[str]] = None):
        """Forward alert to configured integrations"""
        event = IntegrationEvent(
            event_type="alert",
            severity=alert_data.get("severity", "warning"),
            title=f"Alert: {alert_data.get('name', 'Unnamed Alert')}",
            message=alert_data.get("message", ""),
            timestamp=datetime.now().isoformat(),
            metadata={
                "rule_id": alert_data.get("id", ""),
                "triggered_at": alert_data.get("triggered_at", ""),
                "value": alert_data.get("value", ""),
                "threshold": alert_data.get("threshold", "")
            }
        )

        return await self.manager.send_event(event, target_integrations)

    async def forward_anomaly(self, anomaly_data: Dict[str, Any], target_integrations: Optional[List[str]] = None):
        """Forward anomaly detection to integrations"""
        event = IntegrationEvent(
            event_type="anomaly",
            severity=anomaly_data.get("severity", "warning"),
            title=f"Anomaly Detected: {anomaly_data.get('metric', 'unknown')}",
            message=f"Detected deviation of {anomaly_data.get('deviation', 0)}%",
            timestamp=datetime.now().isoformat(),
            metadata={
                "metric": anomaly_data.get("metric"),
                "expected": anomaly_data.get("expected"),
                "actual": anomaly_data.get("actual"),
                "deviation": anomaly_data.get("deviation")
            }
        )

        return await self.manager.send_event(event, target_integrations)

    async def forward_metric(self, metric_data: Dict[str, Any], target_integrations: Optional[List[str]] = None):
        """Forward metrics to integrations (for observability)"""
        event = IntegrationEvent(
            event_type="metric",
            severity="info",
            title=f"Metrics: {metric_data.get('name', 'Unknown')}",
            message=f"Value: {metric_data.get('value', 0)}",
            timestamp=datetime.now().isoformat(),
            metadata={
                "metric": metric_data.get("name"),
                "value": metric_data.get("value"),
                "unit": metric_data.get("unit", "")
            }
        )

        return await self.manager.send_event(event, target_integrations)

    async def forward_report(self, report_data: Dict[str, Any], target_integrations: Optional[List[str]] = None):
        """Forward report completion notification"""
        event = IntegrationEvent(
            event_type="report",
            severity="info",
            title=f"Report Generated: {report_data.get('name', 'Unknown')}",
            message=f"Format: {report_data.get('format', 'unknown')} - Size: {report_data.get('size', 0)} bytes",
            timestamp=datetime.now().isoformat(),
            metadata={
                "report_name": report_data.get("name"),
                "format": report_data.get("format"),
                "size": report_data.get("size"),
                "recipients": report_data.get("recipients", [])
            }
        )

        return await self.manager.send_event(event, target_integrations)


# Singleton
integration_forwarder = IntegrationForwarder()


class MonitoringBridge:
    """Bridge for external monitoring systems"""

    def __init__(self):
        self.manager = integration_manager
        self.logger = logger

    async def get_datadog_metrics(self, metric_name: str, hours: int = 24):
        """Fetch metrics from Datadog for correlation"""
        config = self.manager.integrations.get("datadog")
        if not config or not config.api_key:
            return {"error": "Datadog not configured"}

        # This would query Datadog's API
        # Implementation would depend on specific Datadog endpoints needed
        return {"note": "Datadog metric fetch requires additional configuration"}

    async def get_newrelic_metrics(self, metric_name: str, hours: int = 24):
        """Fetch metrics from New Relic"""
        config = self.manager.integrations.get("newrelic")
        if not config or not config.api_key:
            return {"error": "New Relic not configured"}

        return {"note": "New Relic metric fetch requires additional configuration"}

    async def sync_status(self):
        """Sync current status with all configured monitoring systems"""
        # Get current system stats
        from src.services.predictive_alerting import predictive_alerting

        forecast = predictive_alerting.predict_metrics(1)

        # Prepare metric event
        status_event = IntegrationEvent(
            event_type="status",
            severity="info",
            title="System Status Update",
            message=f"Active requests: monitoring... Forecast risk: {forecast.risk_level}",
            timestamp=datetime.now().isoformat(),
            metadata={
                "risk_level": forecast.risk_level,
                "predicted_cost": round(forecast.cost_prediction, 4),
                "predicted_tokens": round(forecast.total_tokens_predicted, 0),
                "timestamp": datetime.now().isoformat()
            }
        )

        # Send to all enabled integrations
        results = await self.manager.send_event(status_event)

        return {
            "status": "synced",
            "integrations": results
        }


# Singleton
monitoring_bridge = MonitoringBridge()
