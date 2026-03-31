"""
System Health and Monitoring API Endpoints

Provides system-level health checks and performance metrics for the dashboard.

Author: AI Architect
Date: 2026-01-04
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
import sqlite3
import psutil
import os
import json
from pathlib import Path

from src.core.logging import logger
from src.services.usage.usage_tracker import usage_tracker

router = APIRouter()


@router.get("/api/system/health")
async def get_system_health():
    """
    Get comprehensive system health metrics.

    Returns:
        - Uptime since last start
        - CPU and memory usage
        - Database size and health
        - WebSocket connection status (from context)
        - Proxy request metrics
    """
    try:
        # Get process info
        process = psutil.Process()

        # Calculate uptime (mock - would need actual start time tracking)
        # For now, estimate from db creation time or use start tracking
        uptime_seconds = 0
        try:
            # Try to get from migration log
            if usage_tracker.enabled:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT executed_at FROM migration_log ORDER BY executed_at ASC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    start_time = datetime.fromisoformat(result[0])
                    uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
                conn.close()
        except Exception as _e:
            pass

        # Format uptime
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        uptime_formatted = f"{hours}h {minutes}m"

        # Get resource usage
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)

        # Database size
        db_size_mb = 0
        if usage_tracker.enabled and os.path.exists(usage_tracker.db_path):
            db_size_mb = os.path.getsize(usage_tracker.db_path) / (1024 * 1024)

        # Request stats from last hour
        hourly_requests = 0
        if usage_tracker.enabled:
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM api_requests
                    WHERE timestamp >= datetime('now', '-1 hour')
                """)
                hourly_requests = cursor.fetchone()[0] or 0
                conn.close()
            except Exception as _e:
                pass

        return {
            "status": "healthy",
            "uptime": uptime_formatted,
            "uptime_seconds": uptime_seconds,
            "resources": {
                "cpu_percent": round(cpu_percent, 1),
                "memory_mb": round(memory_mb, 1),
                "memory_percent": round((memory_mb / psutil.virtual_memory().total * 100), 2)
            },
            "database": {
                "enabled": usage_tracker.enabled,
                "size_mb": round(db_size_mb, 1),
                "path": str(usage_tracker.db_path) if usage_tracker.enabled else None
            },
            "performance": {
                "hourly_requests": hourly_requests,
                "avg_requests_per_hour": round(hourly_requests, 1)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/stats")
async def get_system_stats():
    """
    Get real-time system statistics for dashboard.

    Enhanced metrics beyond basic health:
    - Total requests since start
    - Total cost since start
    - Provider distribution
    - Error rates
    - Average latency
    """
    try:
        if not usage_tracker.enabled:
            return {
                "enabled": False,
                "message": "Usage tracking disabled",
                "stats": {}
            }

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Overall summary
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                SUM(estimated_cost) as total_cost,
                AVG(duration_ms) as avg_latency,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                COUNT(DISTINCT routed_model) as unique_models,
                COUNT(DISTINCT provider) as unique_providers
            FROM api_requests
        """)
        summary = cursor.fetchone()

        # Requests today
        cursor.execute("""
            SELECT COUNT(*) FROM api_requests
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        requests_today = cursor.fetchone()[0]

        # Cost today
        cursor.execute("""
            SELECT SUM(estimated_cost) FROM api_requests
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        cost_today = cursor.fetchone()[0] or 0

        # Token total
        cursor.execute("SELECT SUM(total_tokens) FROM api_requests")
        total_tokens = cursor.fetchone()[0] or 0

        # Error rate
        total = summary['total_requests'] or 1
        errors = summary['errors'] or 0
        error_rate = (errors / total) * 100

        conn.close()

        return {
            "enabled": True,
            "requests_today": requests_today,
            "total_tokens": total_tokens,
            "est_cost": round(cost_today, 4),
            "avg_latency": round(summary['avg_latency'] or 0, 0),
            "total_requests": summary['total_requests'],
            "total_cost": round(summary['total_cost'] or 0, 4),
            "error_rate": round(error_rate, 2),
            "unique_models": summary['unique_models'],
            "unique_providers": summary['unique_providers']
        }

    except Exception as e:
        logger.error(f"System stats failed: {e}")
        return {
            "enabled": False,
            "error": str(e),
            "stats": {}
        }


@router.get("/api/system/request-feed")
async def get_request_feed(limit: int = 20):
    """
    Get recent requests for live feed display.

    Returns detailed request information for real-time monitoring.
    """
    try:
        if not usage_tracker.enabled:
            return {"requests": [], "enabled": False}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                timestamp,
                provider,
                routed_model,
                status,
                duration_ms,
                estimated_cost,
                total_tokens
            FROM api_requests
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        requests = []
        for row in rows:
            requests.append({
                "timestamp": row["timestamp"],
                "provider": row["provider"],
                "model": row["routed_model"],
                "status": row["status"],
                "duration_ms": row["duration_ms"],
                "cost": round(row["estimated_cost"] or 0, 4),
                "tokens": row["total_tokens"]
            })

        return {
            "requests": requests,
            "count": len(requests),
            "enabled": True
        }

    except Exception as e:
        logger.error(f"Request feed failed: {e}")
        return {"requests": [], "error": str(e)}


@router.get("/api/system/crosstalk-stats")
async def get_crosstalk_dashboard_stats():
    """
    Get Crosstalk session statistics for dashboard overview.

    Returns aggregated stats about historical Crosstalk sessions.
    """
    try:
        sessions_dir = Path("configs/crosstalk/sessions")
        if not sessions_dir.exists():
            return {
                "total_sessions": 0,
                "sessions": []
            }

        sessions = []
        total_cost = 0
        total_rounds = 0
        paradigm_counts = {}

        for session_file in sessions_dir.glob("*.json"):
            try:
                import json
                with open(session_file, 'r') as f:
                    data = json.load(f)

                # Extract session info
                config = data.get("config", {})
                messages = data.get("messages", [])

                # Calculate cost if not stored
                session_cost = 0
                for msg in messages:
                    session_cost += msg.get("cost", 0)

                session_info = {
                    "filename": session_file.stem,
                    "started_at": data.get("started_at", ""),
                    "ended_at": data.get("ended_at", ""),
                    "paradigm": config.get("paradigm", "relay"),
                    "topology": config.get("topology", {}).get("type", "ring"),
                    "rounds": config.get("rounds", len(messages)),
                    "models": len(config.get("models", [])),
                    "total_cost": round(session_cost, 4),
                    "total_tokens": sum(m.get("tokens", 0) for m in messages),
                    "status": data.get("status", "completed")
                }

                sessions.append(session_info)

                total_cost += session_cost
                total_rounds += session_info["rounds"]

                paradigm = session_info["paradigm"]
                paradigm_counts[paradigm] = paradigm_counts.get(paradigm, 0) + 1

            except Exception as e:
                logger.warning(f"Failed to parse session {session_file}: {e}")
                continue

        # Sort by date (most recent first)
        sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)

        # Calculate averages
        avg_cost = total_cost / len(sessions) if sessions else 0
        avg_rounds = total_rounds / len(sessions) if sessions else 0

        # Get top paradigm
        top_paradigm = max(paradigm_counts, key=paradigm_counts.get) if paradigm_counts else "none"

        return {
            "total_sessions": len(sessions),
            "avg_cost_per_session": round(avg_cost, 4),
            "avg_rounds": int(avg_rounds) if avg_rounds else 0,
            "top_paradigm": top_paradigm,
            "paradigm_distribution": paradigm_counts,
            "sessions": sessions[:10],  # Last 10
            "total_cost": round(total_cost, 4)
        }

    except Exception as e:
        logger.error(f"Crosstalk stats failed: {e}")
        return {"total_sessions": 0, "error": str(e)}


@router.get("/api/alerts/active")
async def get_active_alerts():
    """
    Get currently active alerts (triggered but not resolved).
    """
    try:
        if not usage_tracker.enabled:
            return {"alerts": [], "enabled": False}

        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get alerts from last 24 hours that haven't been resolved
        cursor.execute("""
            SELECT
                h.id,
                h.rule_id,
                h.rule_name,
                h.triggered_at,
                h.severity,
                h.alert_data_json,
                r.description,
                r.condition_json
            FROM alert_history h
            LEFT JOIN alert_rules r ON h.rule_id = r.id
            WHERE h.triggered_at >= datetime('now', '-24 hours')
            AND h.resolved = 0
            ORDER BY h.triggered_at DESC
            LIMIT 20
        """)

        rows = cursor.fetchall()
        conn.close()

        alerts = []
        for row in rows:
            alerts.append({
                "id": row["id"],
                "rule_name": row["rule_name"],
                "severity": row["severity"],
                "triggered_at": row["triggered_at"],
                "description": row["description"],
                "condition": row["condition_json"],
                "data": row["alert_data_json"]
            })

        return {
            "alerts": alerts,
            "count": len(alerts),
            "enabled": True
        }

    except Exception as e:
        logger.error(f"Active alerts failed: {e}")
        return {"alerts": [], "error": str(e)}


@router.get("/api/budget/status")
async def get_budget_status():
    """
    Get current budget tracking status.
    """
    try:
        if not usage_tracker.enabled:
            return {"enabled": False, "message": "Usage tracking disabled"}

        # Get today's cost
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(estimated_cost) FROM api_requests
            WHERE DATE(timestamp) = DATE('now', 'localtime')
        """)
        current_daily = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(estimated_cost) FROM api_requests
            WHERE timestamp >= datetime('now', '-30 days')
        """)
        current_monthly = cursor.fetchone()[0] or 0

        conn.close()

        # Mock budget limits (would come from config)
        daily_limit = 100.0
        monthly_limit = 3000.0

        return {
            "enabled": True,
            "daily": {
                "limit": daily_limit,
                "current": round(current_daily, 2),
                "percentage": round((current_daily / daily_limit * 100), 1) if daily_limit > 0 else 0,
                "remaining": round(daily_limit - current_daily, 2)
            },
            "monthly": {
                "limit": monthly_limit,
                "current": round(current_monthly, 2),
                "percentage": round((current_monthly / monthly_limit * 100), 1) if monthly_limit > 0 else 0,
                "remaining": round(monthly_limit - current_monthly, 2)
            }
        }

    except Exception as e:
        logger.error(f"Budget status failed: {e}")
        return {"enabled": False, "error": str(e)}


@router.post("/api/budget/configure")
async def configure_budget(daily_limit: float, monthly_limit: float):
    """
    Configure budget limits (placeholder for future implementation).
    """
    # In full implementation, this would save to config file
    return {
        "status": "success",
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "message": "Budget configuration saved (would persist to config file)"
    }

@router.get("/api/system/health/diagnostic")
async def get_diagnostic_health():
    """
    Comprehensive diagnostic health check for debugging.
    
    Returns detailed information about:
    - System status and uptime
    - Log configuration and recent errors
    - Provider endpoint health
    - Database status
    - Recent request statistics
    - Configuration summary (redacted)
    
    This endpoint is useful for troubleshooting issues
    like Issue 18 (tool call continuation).
    """
    import time
    from src.core.config import config
    from src.services.logging.structured_logger import get_logger
    
    start_time = time.time()
    
    try:
        process = psutil.Process()
        
        # Get uptime
        uptime_seconds = 0
        try:
            if usage_tracker.enabled:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT executed_at FROM migration_log ORDER BY executed_at ASC LIMIT 1")
                result = cursor.fetchone()
                if result:
                    start_time_db = datetime.fromisoformat(result[0])
                    uptime_seconds = (datetime.utcnow() - start_time_db).total_seconds()
                conn.close()
        except Exception:
            pass
        
        # Get log statistics
        logs_info = {
            "tier": config.log_tier,
            "dir": config.logs_dir,
            "max_size_mb": config.log_max_size_mb,
            "retention_days": config.log_retention_days,
            "files": [],
            "total_size_mb": 0,
            "recent_errors": []
        }
        
        logs_path = Path(config.logs_dir)
        if logs_path.exists():
            for log_file in sorted(logs_path.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)[:10]:
                logs_info["files"].append({
                    "name": log_file.name,
                    "size_mb": round(log_file.stat().st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
                logs_info["total_size_mb"] += log_file.stat().st_size / (1024 * 1024)
            
            # Read recent errors from error log
            error_log = logs_path / "proxy_errors.log"
            if error_log.exists():
                try:
                    with open(error_log, 'r') as f:
                        lines = f.readlines()[-10:]  # Last 10 errors
                        logs_info["recent_errors"] = [line.strip()[:200] for line in lines if line.strip()]
                except Exception:
                    pass
        
        logs_info["total_size_mb"] = round(logs_info["total_size_mb"], 2)
        
        # Check provider endpoints
        providers = {
            "default": check_endpoint(config.openai_base_url),
            "big": check_endpoint(config.big_endpoint) if config.big_endpoint != config.openai_base_url else None,
            "middle": check_endpoint(config.middle_endpoint) if config.middle_endpoint != config.openai_base_url else None,
            "small": check_endpoint(config.small_endpoint) if config.small_endpoint != config.openai_base_url else None,
        }
        
        # Database info
        db_info = {
            "enabled": usage_tracker.enabled,
            "path": str(usage_tracker.db_path) if usage_tracker.enabled else None,
            "size_mb": 0,
            "tables": []
        }
        
        if usage_tracker.enabled and os.path.exists(usage_tracker.db_path):
            db_info["size_mb"] = round(os.path.getsize(usage_tracker.db_path) / (1024 * 1024), 2)
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                db_info["tables"] = [row[0] for row in cursor.fetchall()]
                conn.close()
            except Exception as e:
                db_info["error"] = str(e)
        
        # Recent request statistics
        request_stats = {
            "last_hour": 0,
            "last_24h": 0,
            "errors_last_hour": 0,
            "avg_duration_ms": 0
        }
        
        if usage_tracker.enabled:
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE timestamp >= datetime('now', '-1 hour')")
                request_stats["last_hour"] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE timestamp >= datetime('now', '-24 hours')")
                request_stats["last_24h"] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE status = 'error' AND timestamp >= datetime('now', '-1 hour')")
                request_stats["errors_last_hour"] = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT AVG(duration_ms) FROM api_requests WHERE timestamp >= datetime('now', '-1 hour') AND duration_ms IS NOT NULL")
                avg_dur = cursor.fetchone()[0]
                request_stats["avg_duration_ms"] = round(avg_dur, 1) if avg_dur else 0
                
                conn.close()
            except Exception:
                pass
        
        # Configuration summary (redacted)
        config_summary = {
            "models": {
                "big": config.big_model,
                "middle": config.middle_model,
                "small": config.small_model
            },
            "features": {
                "dashboard": config.enable_dashboard,
                "tracking": config.track_usage,
                "cascade": config.model_cascade
            },
            "endpoints": {
                "default": sanitize_url(config.openai_base_url),
                "has_big_override": config.big_endpoint != config.openai_base_url,
                "has_middle_override": config.middle_endpoint != config.openai_base_url,
                "has_small_override": config.small_endpoint != config.openai_base_url
            }
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "check_duration_ms": round((time.time() - start_time) * 1000, 1),
            "uptime": {
                "seconds": round(uptime_seconds, 1),
                "formatted": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
            },
            "resources": {
                "cpu_percent": round(process.cpu_percent(), 1),
                "memory_mb": round(process.memory_info().rss / (1024 * 1024), 1),
                "memory_percent": round(process.memory_percent(), 1)
            },
            "logs": logs_info,
            "providers": providers,
            "database": db_info,
            "requests": request_stats,
            "configuration": config_summary
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }


def check_endpoint(url: str) -> dict:
    """Check if an endpoint is reachable."""
    import httpx
    
    if not url:
        return {"status": "not_configured", "url": None}
    
    try:
        # Just check if we can connect (don't send real request)
        with httpx.Client(timeout=5.0) as client:
            # Try a lightweight request
            response = client.get(url.replace('/v1', '/health'), follow_redirects=True)
            return {
                "status": "healthy" if response.status_code < 400 else "error",
                "url": sanitize_url(url),
                "status_code": response.status_code,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 1)
            }
    except httpx.ConnectError:
        return {
            "status": "unreachable",
            "url": sanitize_url(url),
            "error": "Connection failed"
        }
    except Exception as e:
        return {
            "status": "error",
            "url": sanitize_url(url),
            "error": str(e)[:100]
        }


def sanitize_url(url: str) -> str:
    """Sanitize URL for display (hide API keys)."""
    if not url:
        return None
    
    # Remove query params and fragment
    base_url = url.split('?')[0].split('#')[0]
    
    # Hide sensitive parts
    if 'openrouter' in base_url.lower():
        return "https://openrouter.ai/api/v1"
    elif 'openai' in base_url.lower():
        return "https://api.openai.com/v1"
    elif 'localhost' in base_url or '127.0.0.1' in base_url:
        return base_url  # Keep local URLs as-is
    else:
        # Generic sanitization
        return base_url[:50] + "..." if len(base_url) > 50 else base_url


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION METRICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/metrics/sessions")
async def get_all_session_metrics():
    """Get real-time metrics for all active sessions."""
    try:
        from src.services.metrics.session_tracker import get_all_sessions
        sessions = get_all_sessions()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "sessions": []
        }


@router.get("/api/metrics/sessions/{session_id}")
async def get_session_metrics(session_id: str):
    """Get metrics for a specific session."""
    try:
        from src.services.metrics.session_tracker import get_session_metrics
        metrics = get_session_metrics(session_id)
        
        if metrics:
            return {
                "status": "success",
                "session_id": session_id,
                "metrics": metrics
            }
        else:
            return {
                "status": "not_found",
                "message": f"Session {session_id} not found or inactive"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/api/metrics/aggregate")
async def get_aggregate_metrics():
    """Get aggregate metrics across all sessions."""
    try:
        from src.services.metrics.session_tracker import get_aggregate_metrics
        metrics = get_aggregate_metrics()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/api/metrics/tool-analytics")
async def get_tool_analytics(
    hours: int = 24,
    session_id: Optional[str] = None
):
    """Get tool call analytics."""
    try:
        logs_path = Path(os.getenv("LOGS_DIR", "logs"))
        analytics_file = logs_path / "tool_analytics.jsonl"
        
        if not analytics_file.exists():
            return {
                "status": "no_data",
                "message": "No tool analytics data available yet"
            }
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        tool_stats = defaultdict(lambda: {"success": 0, "failure": 0, "sessions": set()})
        total_success = 0
        total_failure = 0
        
        with open(analytics_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    
                    if timestamp < cutoff:
                        continue
                    
                    if session_id and data.get('session_id') != session_id:
                        continue
                    
                    tool_name = data.get('tool_name', 'unknown')
                    success = data.get('success', True)
                    
                    if success:
                        tool_stats[tool_name]['success'] += 1
                        total_success += 1
                    else:
                        tool_stats[tool_name]['failure'] += 1
                        total_failure += 1
                    
                    if data.get('session_id'):
                        tool_stats[tool_name]['sessions'].add(data['session_id'])
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Convert to serializable format
        result = {
            "status": "success",
            "period_hours": hours,
            "total_tool_calls": total_success + total_failure,
            "success_rate": round(total_success / max(total_success + total_failure, 1) * 100, 1),
            "tools": {}
        }
        
        for tool_name, stats in tool_stats.items():
            total = stats['success'] + stats['failure']
            result['tools'][tool_name] = {
                "total": total,
                "success": stats['success'],
                "failure": stats['failure'],
                "success_rate": round(stats['success'] / max(total, 1) * 100, 1),
                "unique_sessions": len(stats['sessions'])
            }
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/api/metrics/cache-analytics")
async def get_cache_analytics(hours: int = 24):
    """Get cache usage analytics."""
    try:
        logs_path = Path(os.getenv("LOGS_DIR", "logs"))
        analytics_file = logs_path / "cache_analytics.jsonl"
        
        if not analytics_file.exists():
            return {
                "status": "no_data",
                "message": "No cache analytics data available yet"
            }
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cache_hits = 0
        cache_misses = 0
        total_cached_tokens = 0
        total_tokens = 0
        
        with open(analytics_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    
                    if timestamp < cutoff:
                        continue
                    
                    if data.get('cache_hit'):
                        cache_hits += 1
                        total_cached_tokens += data.get('cached_tokens', 0)
                    else:
                        cache_misses += 1
                    
                    total_tokens += data.get('total_tokens', 0)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        total_requests = cache_hits + cache_misses
        cache_hit_rate = round(cache_hits / max(total_requests, 1) * 100, 1)
        token_savings = round(total_cached_tokens / max(total_tokens, 1) * 100, 1)
        
        # Estimate cost savings (assuming $1/1M tokens average)
        cost_savings = round(total_cached_tokens / 1_000_000 * 1.0, 4)
        
        return {
            "status": "success",
            "period_hours": hours,
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cached_tokens": total_cached_tokens,
            "total_tokens": total_tokens,
            "token_savings_percent": token_savings,
            "estimated_cost_savings": cost_savings
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/api/metrics/history")
async def get_metrics_history(
    limit: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get historical metrics from aggregated history.
    
    Args:
        limit: Maximum number of entries to return (default: 30)
        start_date: Filter by start date (ISO format: YYYY-MM-DD)
        end_date: Filter by end date (ISO format: YYYY-MM-DD)
    
    Returns:
        List of aggregated metric snapshots
    """
    try:
        logs_path = Path(os.getenv("LOGS_DIR", "logs"))
        history_file = logs_path / "metrics_history.jsonl"
        
        if not history_file.exists():
            return {
                "status": "no_data",
                "message": "No metrics history available yet. Run log cleanup to start collecting history.",
                "entries": []
            }
        
        entries = []
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    
                    # Filter by date range
                    if start_date:
                        entry_date = data.get('timestamp', '')[:10]
                        if entry_date < start_date:
                            continue
                    
                    if end_date:
                        entry_date = data.get('timestamp', '')[:10]
                        if entry_date > end_date:
                            continue
                    
                    entries.append(data)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Sort by timestamp (newest first) and limit
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        entries = entries[:limit]
        
        return {
            "status": "success",
            "count": len(entries),
            "entries": entries
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "entries": []
        }


@router.get("/api/metrics/history/trends")
async def get_metrics_trends(
    days: int = 30
):
    """
    Get trend data from metrics history for charting.
    
    Returns aggregated trends for:
    - Tool call volume and success rate
    - Cache hit rate and token savings
    - Session count
    
    Args:
        days: Number of days to include (default: 30)
    
    Returns:
        Trend data suitable for charts
    """
    try:
        logs_path = Path(os.getenv("LOGS_DIR", "logs"))
        history_file = logs_path / "metrics_history.jsonl"
        
        if not history_file.exists():
            return {
                "status": "no_data",
                "message": "No metrics history available yet",
                "trends": {
                    'dates': [],
                    'tool_calls': [],
                    'tool_success_rate': [],
                    'cache_hit_rate': [],
                    'cached_tokens': [],
                    'sessions': []
                }
            }
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        entries = []
        
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
                    
                    if timestamp.replace(tzinfo=None) < cutoff:
                        continue
                    
                    entries.append({
                        'date': data.get('timestamp', '')[:10],
                        'tool_calls': data.get('tool_calls', {}).get('total', 0),
                        'tool_success_rate': data.get('tool_calls', {}).get('success_rate', 0),
                        'cache_hit_rate': data.get('cache_usage', {}).get('hit_rate', 0),
                        'cached_tokens': data.get('cache_usage', {}).get('cached_tokens', 0),
                        'sessions': data.get('sessions', 0)
                    })
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Sort by date
        entries.sort(key=lambda x: x['date'])
        
        # Extract arrays for charting
        trends = {
            'dates': [e['date'] for e in entries],
            'tool_calls': [e['tool_calls'] for e in entries],
            'tool_success_rate': [e['tool_success_rate'] for e in entries],
            'cache_hit_rate': [e['cache_hit_rate'] for e in entries],
            'cached_tokens': [e['cached_tokens'] for e in entries],
            'sessions': [e['sessions'] for e in entries]
        }
        
        return {
            "status": "success",
            "period_days": days,
            "entry_count": len(entries),
            "trends": trends
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "trends": {
                'dates': [],
                'tool_calls': [],
                'tool_success_rate': [],
                'cache_hit_rate': [],
                'cached_tokens': [],
                'sessions': []
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TOOL SESSION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/cli-tools")
async def get_cli_tools():
    """Get data from all AI coding CLI tools."""
    try:
        from src.services.cli.session_collector import collect_cli_sessions
        data = collect_cli_sessions()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }


@router.get("/api/cli-tools/stats")
async def get_cli_tool_stats():
    """Get aggregate statistics from CLI tools."""
    try:
        from src.services.cli.session_collector import get_cli_stats
        stats = get_cli_stats()
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "stats": {}
        }


@router.get("/api/cli-tools/timeline")
async def get_cli_tool_timeline(
    days: int = 7,
    tool: Optional[str] = None
):
    """
    Get session timeline from CLI tools.
    
    Args:
        days: Number of days to include (default: 7)
        tool: Filter by specific tool (optional)
    """
    try:
        from src.services.cli.session_collector import get_cli_timeline
        timeline = get_cli_timeline(days)
        
        # Filter by tool if specified
        if tool:
            timeline = [s for s in timeline if s['tool'] == tool]
        
        return {
            "status": "success",
            "period_days": days,
            "session_count": len(timeline),
            "timeline": timeline
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timeline": []
        }


@router.get("/api/cli-tools/{tool_id}")
async def get_cli_tool_details(tool_id: str):
    """Get detailed data for a specific CLI tool."""
    try:
        from src.services.cli.session_collector import collect_cli_sessions
        all_data = collect_cli_sessions()
        
        if tool_id not in all_data.get('tools', {}):
            return {
                "status": "not_found",
                "message": f"Tool '{tool_id}' not found",
                "available_tools": list(all_data.get('tools', {}).keys())
            }
        
        return {
            "status": "success",
            "tool_id": tool_id,
            "data": all_data['tools'][tool_id]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
