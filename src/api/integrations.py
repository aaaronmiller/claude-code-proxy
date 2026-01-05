"""
Third-Party Integrations API - Phase 4

Endpoints for managing third-party integrations and forwarding events

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.logging import logger
from src.services.integrations import (
    integration_manager,
    integration_forwarder,
    monitoring_bridge,
    IntegrationType,
    IntegrationConfig,
    IntegrationEvent
)

router = APIRouter()


@router.get("/api/integrations")
async def list_integrations():
    """List all configured integrations"""
    try:
        integrations = integration_manager.list_integrations()
        return {
            "integrations": integrations,
            "count": len(integrations)
        }
    except Exception as e:
        logger.error(f"Failed to list integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/{integration_type}/config")
async def configure_integration(integration_type: str, config: Dict[str, Any]):
    """Configure a new integration"""
    try:
        # Validate type
        try:
            int_type = IntegrationType(integration_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid integration type: {integration_type}")

        # Create config
        int_config = IntegrationConfig(
            type=int_type,
            enabled=config.get("enabled", True),
            api_key=config.get("api_key"),
            endpoint=config.get("endpoint"),
            extra_config=config.get("extra_config", {}),
            created_at=datetime.now().isoformat()
        )

        # Store in manager
        integration_manager.integrations[integration_type] = int_config
        integration_manager.save_config()

        return {
            "success": True,
            "integration": integration_type,
            "status": "configured"
        }

    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/integrations/{name}/enable")
async def enable_integration(name: str, enabled: bool):
    """Enable or disable an integration"""
    try:
        if name not in integration_manager.integrations:
            raise HTTPException(status_code=404, detail=f"Integration {name} not found")

        integration_manager.integrations[name].enabled = enabled
        integration_manager.save_config()

        return {
            "success": True,
            "integration": name,
            "enabled": enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/integrations/{name}")
async def remove_integration(name: str):
    """Remove an integration configuration"""
    try:
        if name not in integration_manager.integrations:
            raise HTTPException(status_code=404, detail=f"Integration {name} not found")

        del integration_manager.integrations[name]
        integration_manager.save_config()

        return {
            "success": True,
            "integration": name,
            "status": "removed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/{name}/test")
async def test_integration(name: str):
    """Test a specific integration"""
    try:
        result = await integration_manager.test_integration(name)
        return result
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/events/alert")
async def forward_alert(alert_data: Dict[str, Any], integrations: Optional[List[str]] = None):
    """Forward alert to integrations"""
    try:
        result = await integration_forwarder.forward_alert(alert_data, integrations)
        return {
            "success": True,
            "integrations": result
        }
    except Exception as e:
        logger.error(f"Alert forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/events/anomaly")
async def forward_anomaly(anomaly_data: Dict[str, Any], integrations: Optional[List[str]] = None):
    """Forward anomaly detection to integrations"""
    try:
        result = await integration_forwarder.forward_anomaly(anomaly_data, integrations)
        return {
            "success": True,
            "integrations": result
        }
    except Exception as e:
        logger.error(f"Anomaly forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/events/metric")
async def forward_metric(metric_data: Dict[str, Any], integrations: Optional[List[str]] = None):
    """Forward metric to integrations"""
    try:
        result = await integration_forwarder.forward_metric(metric_data, integrations)
        return {
            "success": True,
            "integrations": result
        }
    except Exception as e:
        logger.error(f"Metric forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/events/report")
async def forward_report(report_data: Dict[str, Any], integrations: Optional[List[str]] = None):
    """Forward report notification to integrations"""
    try:
        result = await integration_forwarder.forward_report(report_data, integrations)
        return {
            "success": True,
            "integrations": result
        }
    except Exception as e:
        logger.error(f"Report forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/integrations/status")
async def get_system_status():
    """Get current system status and sync with monitoring"""
    try:
        status = await monitoring_bridge.sync_status()
        return status
    except Exception as e:
        logger.error(f"Status sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/custom-event")
async def send_custom_event(event: Dict[str, Any], integrations: Optional[List[str]] = None):
    """Send a custom event to integrations"""
    try:
        int_event = IntegrationEvent(
            event_type=event.get("type", "custom"),
            severity=event.get("severity", "info"),
            title=event.get("title", "Custom Event"),
            message=event.get("message", ""),
            timestamp=datetime.now().isoformat(),
            metadata=event.get("metadata", {})
        )

        result = await integration_manager.send_event(int_event, integrations)

        return {
            "success": True,
            "event": event,
            "integrations": result
        }

    except Exception as e:
        logger.error(f"Custom event failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/integrations/health")
async def integrations_health():
    """Health check for integrations"""
    try:
        enabled_count = sum(1 for config in integration_manager.integrations.values() if config.enabled)
        total_count = len(integration_manager.integrations)

        return {
            "status": "healthy",
            "total_integrations": total_count,
            "enabled_integrations": enabled_count,
            "integrations": [
                {
                    "name": name,
                    "type": config.type.value,
                    "enabled": config.enabled
                }
                for name, config in integration_manager.integrations.items()
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/api/integrations/available")
async def get_available_integrations():
    """Get list of all available integration types"""
    return {
        "available": [
            {
                "type": t.value,
                "description": t.name.title(),
                "config_required": ["api_key", "endpoint"],
                "env_vars": [
                    f"{t.value.upper()}_API_KEY",
                    f"{t.value.upper()}_ENDPOINT"
                ]
            }
            for t in IntegrationType
        ]
    }


@router.post("/api/integrations/forward/batch")
async def forward_batch(events: List[Dict[str, Any]], integrations: Optional[List[str]] = None):
    """Forward multiple events in batch"""
    try:
        results = []

        for event_data in events:
            event = IntegrationEvent(
                event_type=event_data.get("type", "batch"),
                severity=event_data.get("severity", "info"),
                title=event_data.get("title", "Batch Event"),
                message=event_data.get("message", ""),
                timestamp=datetime.now().isoformat(),
                metadata=event_data.get("metadata", {})
            )

            result = await integration_manager.send_event(event, integrations)
            results.append({
                "event": event_data,
                "results": result
            })

        return {
            "success": True,
            "batch_size": len(events),
            "results": results
        }

    except Exception as e:
        logger.error(f"Batch forwarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/integrations/monitoring/external")
async def get_external_metrics(
    system: str = Query(..., enum=["datadog", "newrelic"]),
    metric: str = Query(...),
    hours: int = Query(24, ge=1, le=168)
):
    """Fetch metrics from external monitoring systems"""
    try:
        if system == "datadog":
            result = await monitoring_bridge.get_datadog_metrics(metric, hours)
        elif system == "newrelic":
            result = await monitoring_bridge.get_newrelic_metrics(metric, hours)
        else:
            raise HTTPException(status_code=400, detail="Invalid system")

        return result

    except Exception as e:
        logger.error(f"External metric fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/integrations/webhook/verify")
async def verify_webhook(url: str, payload: Optional[Dict[str, Any]] = None):
    """Verify webhook endpoint connectivity"""
    import aiohttp

    try:
        test_payload = payload or {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "source": "claude-proxy",
            "message": "Webhook verification"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_payload, timeout=10) as response:
                content = await response.text()
                return {
                    "success": 200 <= response.status < 300,
                    "status_code": response.status,
                    "response": content[:500],  # Limit response size
                    "headers": dict(response.headers)
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
