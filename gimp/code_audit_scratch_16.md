# File Audit: /home/cheta/code/claude-code-proxy/src/utils/json_utils.py
**Path**: `/home/cheta/code/claude-code-proxy/src/utils/json_utils.py`

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
json, logging, typing.Any, typing.Optional, typing.Dict, typing.List, typing.Union

## Feature Function: `safe_json_loads`
**Logic & Purpose:**
```text
Safely load JSON data without throwing exceptions if it's malformed or None.

Args:
    data: The JSON string or bytes to parse
    default: The fallback value to return if parsing fails (defaults to None)
    
Returns:
    The parsed Python object, or the default value on failure
```

**Parameters:** `data, default`
**Implementation:**
```python
def safe_json_loads(data: Union[str, bytes, None], default: Any=None) -> Any:
    """
    Safely load JSON data without throwing exceptions if it's malformed or None.
    
    Args:
        data: The JSON string or bytes to parse
        default: The fallback value to return if parsing fails (defaults to None)
        
    Returns:
        The parsed Python object, or the default value on failure
    """
    if data is None:
        return default
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f'Failed to parse JSON: {e}')
        return default
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/system_monitor.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/system_monitor.py`

**Module Overview**: 
```text
System Health and Monitoring API Endpoints

Provides system-level health checks and performance metrics for the dashboard.

Author: AI Architect
Date: 2026-01-04
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, datetime.datetime, datetime.timedelta, collections.defaultdict, typing.Optional, sqlite3, psutil, os, json, pathlib.Path, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Function: `get_system_health`
**Logic & Purpose:**
```text
Get comprehensive system health metrics.

Returns:
    - Uptime since last start
    - CPU and memory usage
    - Database size and health
    - WebSocket connection status (from context)
    - Proxy request metrics
```

**Parameters:** ``
**Variables Used:** `hours, cpu_percent, cursor, result, uptime_seconds, start_time, process, memory_mb, hourly_requests, uptime_formatted, db_size_mb, minutes, memory_info, conn`
**Implementation:**
```python
@router.get('/api/system/health')
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
        process = psutil.Process()
        uptime_seconds = 0
        try:
            if usage_tracker.enabled:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT executed_at FROM migration_log ORDER BY executed_at ASC LIMIT 1')
                result = cursor.fetchone()
                if result:
                    start_time = datetime.fromisoformat(result[0])
                    uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
                conn.close()
        except Exception as _e:
            pass
        hours = int(uptime_seconds // 3600)
        minutes = int(uptime_seconds % 3600 // 60)
        uptime_formatted = f'{hours}h {minutes}m'
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        db_size_mb = 0
        if usage_tracker.enabled and os.path.exists(usage_tracker.db_path):
            db_size_mb = os.path.getsize(usage_tracker.db_path) / (1024 * 1024)
        hourly_requests = 0
        if usage_tracker.enabled:
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("\n                    SELECT COUNT(*) FROM api_requests\n                    WHERE timestamp >= datetime('now', '-1 hour')\n                ")
                hourly_requests = cursor.fetchone()[0] or 0
                conn.close()
            except Exception as _e:
                pass
        return {'status': 'healthy', 'uptime': uptime_formatted, 'uptime_seconds': uptime_seconds, 'resources': {'cpu_percent': round(cpu_percent, 1), 'memory_mb': round(memory_mb, 1), 'memory_percent': round(memory_mb / psutil.virtual_memory().total * 100, 2)}, 'database': {'enabled': usage_tracker.enabled, 'size_mb': round(db_size_mb, 1), 'path': str(usage_tracker.db_path) if usage_tracker.enabled else None}, 'performance': {'hourly_requests': hourly_requests, 'avg_requests_per_hour': round(hourly_requests, 1)}, 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f'System health check failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_system_stats`
**Logic & Purpose:**
```text
Get real-time system statistics for dashboard.

Enhanced metrics beyond basic health:
- Total requests since start
- Total cost since start
- Provider distribution
- Error rates
- Average latency
```

**Parameters:** ``
**Variables Used:** `cursor, cost_today, requests_today, total, error_rate, errors, summary, conn, total_tokens`
**Implementation:**
```python
@router.get('/api/system/stats')
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
            return {'enabled': False, 'message': 'Usage tracking disabled', 'stats': {}}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("\n            SELECT\n                COUNT(*) as total_requests,\n                SUM(estimated_cost) as total_cost,\n                AVG(duration_ms) as avg_latency,\n                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,\n                COUNT(DISTINCT routed_model) as unique_models,\n                COUNT(DISTINCT provider) as unique_providers\n            FROM api_requests\n        ")
        summary = cursor.fetchone()
        cursor.execute("\n            SELECT COUNT(*) FROM api_requests\n            WHERE DATE(timestamp) = DATE('now', 'localtime')\n        ")
        requests_today = cursor.fetchone()[0]
        cursor.execute("\n            SELECT SUM(estimated_cost) FROM api_requests\n            WHERE DATE(timestamp) = DATE('now', 'localtime')\n        ")
        cost_today = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(total_tokens) FROM api_requests')
        total_tokens = cursor.fetchone()[0] or 0
        total = summary['total_requests'] or 1
        errors = summary['errors'] or 0
        error_rate = errors / total * 100
        conn.close()
        return {'enabled': True, 'requests_today': requests_today, 'total_tokens': total_tokens, 'est_cost': round(cost_today, 4), 'avg_latency': round(summary['avg_latency'] or 0, 0), 'total_requests': summary['total_requests'], 'total_cost': round(summary['total_cost'] or 0, 4), 'error_rate': round(error_rate, 2), 'unique_models': summary['unique_models'], 'unique_providers': summary['unique_providers']}
    except Exception as e:
        logger.error(f'System stats failed: {e}')
        return {'enabled': False, 'error': str(e), 'stats': {}}
```

---

## Feature Function: `get_request_feed`
**Logic & Purpose:**
```text
Get recent requests for live feed display.

Returns detailed request information for real-time monitoring.
```

**Parameters:** `limit`
**Variables Used:** `rows, conn, cursor, requests`
**Implementation:**
```python
@router.get('/api/system/request-feed')
async def get_request_feed(limit: int=20):
    """
    Get recent requests for live feed display.

    Returns detailed request information for real-time monitoring.
    """
    try:
        if not usage_tracker.enabled:
            return {'requests': [], 'enabled': False}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('\n            SELECT\n                timestamp,\n                provider,\n                routed_model,\n                status,\n                duration_ms,\n                estimated_cost,\n                total_tokens\n            FROM api_requests\n            ORDER BY timestamp DESC\n            LIMIT ?\n        ', (limit,))
        rows = cursor.fetchall()
        conn.close()
        requests = []
        for row in rows:
            requests.append({'timestamp': row['timestamp'], 'provider': row['provider'], 'model': row['routed_model'], 'status': row['status'], 'duration_ms': row['duration_ms'], 'cost': round(row['estimated_cost'] or 0, 4), 'tokens': row['total_tokens']})
        return {'requests': requests, 'count': len(requests), 'enabled': True}
    except Exception as e:
        logger.error(f'Request feed failed: {e}')
        return {'requests': [], 'error': str(e)}
```

---

## Feature Function: `get_crosstalk_dashboard_stats`
**Logic & Purpose:**
```text
Get Crosstalk session statistics for dashboard overview.

Returns aggregated stats about historical Crosstalk sessions.
```

**Parameters:** ``
**Variables Used:** `total_cost, top_paradigm, data, total_rounds, avg_cost, config, session_cost, sessions_dir, paradigm, messages, avg_rounds, paradigm_counts, sessions, session_info`
**Implementation:**
```python
@router.get('/api/system/crosstalk-stats')
async def get_crosstalk_dashboard_stats():
    """
    Get Crosstalk session statistics for dashboard overview.

    Returns aggregated stats about historical Crosstalk sessions.
    """
    try:
        sessions_dir = Path('configs/crosstalk/sessions')
        if not sessions_dir.exists():
            return {'total_sessions': 0, 'sessions': []}
        sessions = []
        total_cost = 0
        total_rounds = 0
        paradigm_counts = {}
        for session_file in sessions_dir.glob('*.json'):
            try:
                import json
                with open(session_file, 'r') as f:
                    data = json.load(f)
                config = data.get('config', {})
                messages = data.get('messages', [])
                session_cost = 0
                for msg in messages:
                    session_cost += msg.get('cost', 0)
                session_info = {'filename': session_file.stem, 'started_at': data.get('started_at', ''), 'ended_at': data.get('ended_at', ''), 'paradigm': config.get('paradigm', 'relay'), 'topology': config.get('topology', {}).get('type', 'ring'), 'rounds': config.get('rounds', len(messages)), 'models': len(config.get('models', [])), 'total_cost': round(session_cost, 4), 'total_tokens': sum((m.get('tokens', 0) for m in messages)), 'status': data.get('status', 'completed')}
                sessions.append(session_info)
                total_cost += session_cost
                total_rounds += session_info['rounds']
                paradigm = session_info['paradigm']
                paradigm_counts[paradigm] = paradigm_counts.get(paradigm, 0) + 1
            except Exception as e:
                logger.warning(f'Failed to parse session {session_file}: {e}')
                continue
        sessions.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        avg_cost = total_cost / len(sessions) if sessions else 0
        avg_rounds = total_rounds / len(sessions) if sessions else 0
        top_paradigm = max(paradigm_counts, key=paradigm_counts.get) if paradigm_counts else 'none'
        return {'total_sessions': len(sessions), 'avg_cost_per_session': round(avg_cost, 4), 'avg_rounds': int(avg_rounds) if avg_rounds else 0, 'top_paradigm': top_paradigm, 'paradigm_distribution': paradigm_counts, 'sessions': sessions[:10], 'total_cost': round(total_cost, 4)}
    except Exception as e:
        logger.error(f'Crosstalk stats failed: {e}')
        return {'total_sessions': 0, 'error': str(e)}
```

---

## Feature Function: `get_active_alerts`
**Logic & Purpose:**
```text
Get currently active alerts (triggered but not resolved).
```

**Parameters:** ``
**Variables Used:** `rows, conn, cursor, alerts`
**Implementation:**
```python
@router.get('/api/alerts/active')
async def get_active_alerts():
    """
    Get currently active alerts (triggered but not resolved).
    """
    try:
        if not usage_tracker.enabled:
            return {'alerts': [], 'enabled': False}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("\n            SELECT\n                h.id,\n                h.rule_id,\n                h.rule_name,\n                h.triggered_at,\n                h.severity,\n                h.alert_data_json,\n                r.description,\n                r.condition_json\n            FROM alert_history h\n            LEFT JOIN alert_rules r ON h.rule_id = r.id\n            WHERE h.triggered_at >= datetime('now', '-24 hours')\n            AND h.resolved = 0\n            ORDER BY h.triggered_at DESC\n            LIMIT 20\n        ")
        rows = cursor.fetchall()
        conn.close()
        alerts = []
        for row in rows:
            alerts.append({'id': row['id'], 'rule_name': row['rule_name'], 'severity': row['severity'], 'triggered_at': row['triggered_at'], 'description': row['description'], 'condition': row['condition_json'], 'data': row['alert_data_json']})
        return {'alerts': alerts, 'count': len(alerts), 'enabled': True}
    except Exception as e:
        logger.error(f'Active alerts failed: {e}')
        return {'alerts': [], 'error': str(e)}
```

---

## Feature Function: `get_budget_status`
**Logic & Purpose:**
```text
Get current budget tracking status.
```

**Parameters:** ``
**Variables Used:** `cursor, daily_limit, current_monthly, current_daily, conn, monthly_limit`
**Implementation:**
```python
@router.get('/api/budget/status')
async def get_budget_status():
    """
    Get current budget tracking status.
    """
    try:
        if not usage_tracker.enabled:
            return {'enabled': False, 'message': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("\n            SELECT SUM(estimated_cost) FROM api_requests\n            WHERE DATE(timestamp) = DATE('now', 'localtime')\n        ")
        current_daily = cursor.fetchone()[0] or 0
        cursor.execute("\n            SELECT SUM(estimated_cost) FROM api_requests\n            WHERE timestamp >= datetime('now', '-30 days')\n        ")
        current_monthly = cursor.fetchone()[0] or 0
        conn.close()
        daily_limit = 100.0
        monthly_limit = 3000.0
        return {'enabled': True, 'daily': {'limit': daily_limit, 'current': round(current_daily, 2), 'percentage': round(current_daily / daily_limit * 100, 1) if daily_limit > 0 else 0, 'remaining': round(daily_limit - current_daily, 2)}, 'monthly': {'limit': monthly_limit, 'current': round(current_monthly, 2), 'percentage': round(current_monthly / monthly_limit * 100, 1) if monthly_limit > 0 else 0, 'remaining': round(monthly_limit - current_monthly, 2)}}
    except Exception as e:
        logger.error(f'Budget status failed: {e}')
        return {'enabled': False, 'error': str(e)}
```

---

## Feature Function: `configure_budget`
**Logic & Purpose:**
```text
Configure budget limits (placeholder for future implementation).
```

**Parameters:** `daily_limit, monthly_limit`
**Implementation:**
```python
@router.post('/api/budget/configure')
async def configure_budget(daily_limit: float, monthly_limit: float):
    """
    Configure budget limits (placeholder for future implementation).
    """
    return {'status': 'success', 'daily_limit': daily_limit, 'monthly_limit': monthly_limit, 'message': 'Budget configuration saved (would persist to config file)'}
```

---

## Feature Function: `get_diagnostic_health`
**Logic & Purpose:**
```text
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
```

**Parameters:** ``
**Variables Used:** `cursor, result, start_time_db, uptime_seconds, start_time, logs_info, db_info, process, config_summary, error_log, request_stats, lines, providers, logs_path, conn, avg_dur`
**Implementation:**
```python
@router.get('/api/system/health/diagnostic')
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
        uptime_seconds = 0
        try:
            if usage_tracker.enabled:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT executed_at FROM migration_log ORDER BY executed_at ASC LIMIT 1')
                result = cursor.fetchone()
                if result:
                    start_time_db = datetime.fromisoformat(result[0])
                    uptime_seconds = (datetime.utcnow() - start_time_db).total_seconds()
                conn.close()
        except Exception:
            pass
        logs_info = {'tier': config.log_tier, 'dir': config.logs_dir, 'max_size_mb': config.log_max_size_mb, 'retention_days': config.log_retention_days, 'files': [], 'total_size_mb': 0, 'recent_errors': []}
        logs_path = Path(config.logs_dir)
        if logs_path.exists():
            for log_file in sorted(logs_path.glob('*.log'), key=lambda f: f.stat().st_mtime, reverse=True)[:10]:
                logs_info['files'].append({'name': log_file.name, 'size_mb': round(log_file.stat().st_size / (1024 * 1024), 2), 'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()})
                logs_info['total_size_mb'] += log_file.stat().st_size / (1024 * 1024)
            error_log = logs_path / 'proxy_errors.log'
            if error_log.exists():
                try:
                    with open(error_log, 'r') as f:
                        lines = f.readlines()[-10:]
                        logs_info['recent_errors'] = [line.strip()[:200] for line in lines if line.strip()]
                except Exception:
                    pass
        logs_info['total_size_mb'] = round(logs_info['total_size_mb'], 2)
        providers = {'default': check_endpoint(config.openai_base_url), 'big': check_endpoint(config.big_endpoint) if config.big_endpoint != config.openai_base_url else None, 'middle': check_endpoint(config.middle_endpoint) if config.middle_endpoint != config.openai_base_url else None, 'small': check_endpoint(config.small_endpoint) if config.small_endpoint != config.openai_base_url else None}
        db_info = {'enabled': usage_tracker.enabled, 'path': str(usage_tracker.db_path) if usage_tracker.enabled else None, 'size_mb': 0, 'tables': []}
        if usage_tracker.enabled and os.path.exists(usage_tracker.db_path):
            db_info['size_mb'] = round(os.path.getsize(usage_tracker.db_path) / (1024 * 1024), 2)
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                db_info['tables'] = [row[0] for row in cursor.fetchall()]
                conn.close()
            except Exception as e:
                db_info['error'] = str(e)
        request_stats = {'last_hour': 0, 'last_24h': 0, 'errors_last_hour': 0, 'avg_duration_ms': 0}
        if usage_tracker.enabled:
            try:
                conn = sqlite3.connect(usage_tracker.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE timestamp >= datetime('now', '-1 hour')")
                request_stats['last_hour'] = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE timestamp >= datetime('now', '-24 hours')")
                request_stats['last_24h'] = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM api_requests WHERE status = 'error' AND timestamp >= datetime('now', '-1 hour')")
                request_stats['errors_last_hour'] = cursor.fetchone()[0] or 0
                cursor.execute("SELECT AVG(duration_ms) FROM api_requests WHERE timestamp >= datetime('now', '-1 hour') AND duration_ms IS NOT NULL")
                avg_dur = cursor.fetchone()[0]
                request_stats['avg_duration_ms'] = round(avg_dur, 1) if avg_dur else 0
                conn.close()
            except Exception:
                pass
        config_summary = {'models': {'big': config.big_model, 'middle': config.middle_model, 'small': config.small_model}, 'features': {'dashboard': config.enable_dashboard, 'tracking': config.track_usage, 'cascade': config.model_cascade}, 'endpoints': {'default': sanitize_url(config.openai_base_url), 'has_big_override': config.big_endpoint != config.openai_base_url, 'has_middle_override': config.middle_endpoint != config.openai_base_url, 'has_small_override': config.small_endpoint != config.openai_base_url}}
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat(), 'check_duration_ms': round((time.time() - start_time) * 1000, 1), 'uptime': {'seconds': round(uptime_seconds, 1), 'formatted': f'{int(uptime_seconds // 3600)}h {int(uptime_seconds % 3600 // 60)}m'}, 'resources': {'cpu_percent': round(process.cpu_percent(), 1), 'memory_mb': round(process.memory_info().rss / (1024 * 1024), 1), 'memory_percent': round(process.memory_percent(), 1)}, 'logs': logs_info, 'providers': providers, 'database': db_info, 'requests': request_stats, 'configuration': config_summary}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'error_type': type(e).__name__, 'timestamp': datetime.utcnow().isoformat()}
```

---

## Feature Function: `check_endpoint`
**Logic & Purpose:**
```text
Check if an endpoint is reachable.
```

**Parameters:** `url`
**Variables Used:** `response`
**Implementation:**
```python
def check_endpoint(url: str) -> dict:
    """Check if an endpoint is reachable."""
    import httpx
    if not url:
        return {'status': 'not_configured', 'url': None}
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url.replace('/v1', '/health'), follow_redirects=True)
            return {'status': 'healthy' if response.status_code < 400 else 'error', 'url': sanitize_url(url), 'status_code': response.status_code, 'response_time_ms': round(response.elapsed.total_seconds() * 1000, 1)}
    except httpx.ConnectError:
        return {'status': 'unreachable', 'url': sanitize_url(url), 'error': 'Connection failed'}
    except Exception as e:
        return {'status': 'error', 'url': sanitize_url(url), 'error': str(e)[:100]}
```

---

## Feature Function: `sanitize_url`
**Logic & Purpose:**
```text
Sanitize URL for display (hide API keys).
```

**Parameters:** `url`
**Variables Used:** `base_url`
**Implementation:**
```python
def sanitize_url(url: str) -> str:
    """Sanitize URL for display (hide API keys)."""
    if not url:
        return None
    base_url = url.split('?')[0].split('#')[0]
    if 'openrouter' in base_url.lower():
        return 'https://openrouter.ai/api/v1'
    elif 'openai' in base_url.lower():
        return 'https://api.openai.com/v1'
    elif 'localhost' in base_url or '127.0.0.1' in base_url:
        return base_url
    else:
        return base_url[:50] + '...' if len(base_url) > 50 else base_url
```

---

## Feature Function: `get_all_session_metrics`
**Logic & Purpose:**
```text
Get real-time metrics for all active sessions.
```

**Parameters:** ``
**Variables Used:** `sessions`
**Implementation:**
```python
@router.get('/api/metrics/sessions')
async def get_all_session_metrics():
    """Get real-time metrics for all active sessions."""
    try:
        from src.services.metrics.session_tracker import get_all_sessions
        sessions = get_all_sessions()
        return {'status': 'success', 'timestamp': datetime.utcnow().isoformat(), 'sessions': sessions, 'count': len(sessions)}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'sessions': []}
```

---

## Feature Function: `get_session_metrics`
**Logic & Purpose:**
```text
Get metrics for a specific session.
```

**Parameters:** `session_id`
**Variables Used:** `metrics`
**Implementation:**
```python
@router.get('/api/metrics/sessions/{session_id}')
async def get_session_metrics(session_id: str):
    """Get metrics for a specific session."""
    try:
        from src.services.metrics.session_tracker import get_session_metrics
        metrics = get_session_metrics(session_id)
        if metrics:
            return {'status': 'success', 'session_id': session_id, 'metrics': metrics}
        else:
            return {'status': 'not_found', 'message': f'Session {session_id} not found or inactive'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_aggregate_metrics`
**Logic & Purpose:**
```text
Get aggregate metrics across all sessions.
```

**Parameters:** ``
**Variables Used:** `metrics`
**Implementation:**
```python
@router.get('/api/metrics/aggregate')
async def get_aggregate_metrics():
    """Get aggregate metrics across all sessions."""
    try:
        from src.services.metrics.session_tracker import get_aggregate_metrics
        metrics = get_aggregate_metrics()
        return {'status': 'success', 'timestamp': datetime.utcnow().isoformat(), 'metrics': metrics}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_tool_analytics`
**Logic & Purpose:**
```text
Get tool call analytics.
```

**Parameters:** `hours, session_id`
**Variables Used:** `cutoff, total_failure, result, total_success, data, timestamp, analytics_file, tool_name, success, tool_stats, total, logs_path`
**Implementation:**
```python
@router.get('/api/metrics/tool-analytics')
async def get_tool_analytics(hours: int=24, session_id: Optional[str]=None):
    """Get tool call analytics."""
    try:
        logs_path = Path(os.getenv('LOGS_DIR', 'logs'))
        analytics_file = logs_path / 'tool_analytics.jsonl'
        if not analytics_file.exists():
            return {'status': 'no_data', 'message': 'No tool analytics data available yet'}
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        tool_stats = defaultdict(lambda: {'success': 0, 'failure': 0, 'sessions': set()})
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
        result = {'status': 'success', 'period_hours': hours, 'total_tool_calls': total_success + total_failure, 'success_rate': round(total_success / max(total_success + total_failure, 1) * 100, 1), 'tools': {}}
        for tool_name, stats in tool_stats.items():
            total = stats['success'] + stats['failure']
            result['tools'][tool_name] = {'total': total, 'success': stats['success'], 'failure': stats['failure'], 'success_rate': round(stats['success'] / max(total, 1) * 100, 1), 'unique_sessions': len(stats['sessions'])}
        return result
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_cache_analytics`
**Logic & Purpose:**
```text
Get cache usage analytics.
```

**Parameters:** `hours`
**Variables Used:** `token_savings, cutoff, data, timestamp, analytics_file, cache_hit_rate, cache_hits, total_cached_tokens, cost_savings, total_tokens, logs_path, cache_misses, total_requests`
**Implementation:**
```python
@router.get('/api/metrics/cache-analytics')
async def get_cache_analytics(hours: int=24):
    """Get cache usage analytics."""
    try:
        logs_path = Path(os.getenv('LOGS_DIR', 'logs'))
        analytics_file = logs_path / 'cache_analytics.jsonl'
        if not analytics_file.exists():
            return {'status': 'no_data', 'message': 'No cache analytics data available yet'}
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
        cost_savings = round(total_cached_tokens / 1000000 * 1.0, 4)
        return {'status': 'success', 'period_hours': hours, 'total_requests': total_requests, 'cache_hits': cache_hits, 'cache_misses': cache_misses, 'cache_hit_rate': cache_hit_rate, 'cached_tokens': total_cached_tokens, 'total_tokens': total_tokens, 'token_savings_percent': token_savings, 'estimated_cost_savings': cost_savings}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_metrics_history`
**Logic & Purpose:**
```text
Get historical metrics from aggregated history.

Args:
    limit: Maximum number of entries to return (default: 30)
    start_date: Filter by start date (ISO format: YYYY-MM-DD)
    end_date: Filter by end date (ISO format: YYYY-MM-DD)

Returns:
    List of aggregated metric snapshots
```

**Parameters:** `limit, start_date, end_date`
**Variables Used:** `data, entry_date, entries, logs_path, history_file`
**Implementation:**
```python
@router.get('/api/metrics/history')
async def get_metrics_history(limit: int=30, start_date: Optional[str]=None, end_date: Optional[str]=None):
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
        logs_path = Path(os.getenv('LOGS_DIR', 'logs'))
        history_file = logs_path / 'metrics_history.jsonl'
        if not history_file.exists():
            return {'status': 'no_data', 'message': 'No metrics history available yet. Run log cleanup to start collecting history.', 'entries': []}
        entries = []
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
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
        entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        entries = entries[:limit]
        return {'status': 'success', 'count': len(entries), 'entries': entries}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'entries': []}
```

---

## Feature Function: `get_metrics_trends`
**Logic & Purpose:**
```text
Get trend data from metrics history for charting.

Returns aggregated trends for:
- Tool call volume and success rate
- Cache hit rate and token savings
- Session count

Args:
    days: Number of days to include (default: 30)

Returns:
    Trend data suitable for charts
```

**Parameters:** `days`
**Variables Used:** `cutoff, data, timestamp, trends, entries, logs_path, history_file`
**Implementation:**
```python
@router.get('/api/metrics/history/trends')
async def get_metrics_trends(days: int=30):
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
        logs_path = Path(os.getenv('LOGS_DIR', 'logs'))
        history_file = logs_path / 'metrics_history.jsonl'
        if not history_file.exists():
            return {'status': 'no_data', 'message': 'No metrics history available yet', 'trends': {'dates': [], 'tool_calls': [], 'tool_success_rate': [], 'cache_hit_rate': [], 'cached_tokens': [], 'sessions': []}}
        cutoff = datetime.utcnow() - timedelta(days=days)
        entries = []
        with open(history_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
                    if timestamp.replace(tzinfo=None) < cutoff:
                        continue
                    entries.append({'date': data.get('timestamp', '')[:10], 'tool_calls': data.get('tool_calls', {}).get('total', 0), 'tool_success_rate': data.get('tool_calls', {}).get('success_rate', 0), 'cache_hit_rate': data.get('cache_usage', {}).get('hit_rate', 0), 'cached_tokens': data.get('cache_usage', {}).get('cached_tokens', 0), 'sessions': data.get('sessions', 0)})
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        entries.sort(key=lambda x: x['date'])
        trends = {'dates': [e['date'] for e in entries], 'tool_calls': [e['tool_calls'] for e in entries], 'tool_success_rate': [e['tool_success_rate'] for e in entries], 'cache_hit_rate': [e['cache_hit_rate'] for e in entries], 'cached_tokens': [e['cached_tokens'] for e in entries], 'sessions': [e['sessions'] for e in entries]}
        return {'status': 'success', 'period_days': days, 'entry_count': len(entries), 'trends': trends}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'trends': {'dates': [], 'tool_calls': [], 'tool_success_rate': [], 'cache_hit_rate': [], 'cached_tokens': [], 'sessions': []}}
```

---

## Feature Function: `get_cli_tools`
**Logic & Purpose:**
```text
Get data from all AI coding CLI tools.
```

**Parameters:** ``
**Variables Used:** `data`
**Implementation:**
```python
@router.get('/api/cli-tools')
async def get_cli_tools():
    """Get data from all AI coding CLI tools."""
    try:
        from src.services.cli.session_collector import collect_cli_sessions
        data = collect_cli_sessions()
        return {'status': 'success', 'timestamp': datetime.utcnow().isoformat(), 'data': data}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'data': None}
```

---

## Feature Function: `get_cli_tool_stats`
**Logic & Purpose:**
```text
Get aggregate statistics from CLI tools.
```

**Parameters:** ``
**Variables Used:** `stats`
**Implementation:**
```python
@router.get('/api/cli-tools/stats')
async def get_cli_tool_stats():
    """Get aggregate statistics from CLI tools."""
    try:
        from src.services.cli.session_collector import get_cli_stats
        stats = get_cli_stats()
        return {'status': 'success', 'timestamp': datetime.utcnow().isoformat(), 'stats': stats}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'stats': {}}
```

---

## Feature Function: `get_cli_tool_timeline`
**Logic & Purpose:**
```text
Get session timeline from CLI tools.

Args:
    days: Number of days to include (default: 7)
    tool: Filter by specific tool (optional)
```

**Parameters:** `days, tool`
**Variables Used:** `timeline`
**Implementation:**
```python
@router.get('/api/cli-tools/timeline')
async def get_cli_tool_timeline(days: int=7, tool: Optional[str]=None):
    """
    Get session timeline from CLI tools.
    
    Args:
        days: Number of days to include (default: 7)
        tool: Filter by specific tool (optional)
    """
    try:
        from src.services.cli.session_collector import get_cli_timeline
        timeline = get_cli_timeline(days)
        if tool:
            timeline = [s for s in timeline if s['tool'] == tool]
        return {'status': 'success', 'period_days': days, 'session_count': len(timeline), 'timeline': timeline}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'timeline': []}
```

---

## Feature Function: `get_cli_tool_details`
**Logic & Purpose:**
```text
Get detailed data for a specific CLI tool.
```

**Parameters:** `tool_id`
**Variables Used:** `all_data`
**Implementation:**
```python
@router.get('/api/cli-tools/{tool_id}')
async def get_cli_tool_details(tool_id: str):
    """Get detailed data for a specific CLI tool."""
    try:
        from src.services.cli.session_collector import collect_cli_sessions
        all_data = collect_cli_sessions()
        if tool_id not in all_data.get('tools', {}):
            return {'status': 'not_found', 'message': f"Tool '{tool_id}' not found", 'available_tools': list(all_data.get('tools', {}).keys())}
        return {'status': 'success', 'tool_id': tool_id, 'data': all_data['tools'][tool_id]}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/graphql_schema.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/graphql_schema.py`

**Module Overview**: 
```text
GraphQL Schema and API - Phase 4

Provides GraphQL interface for the analytics platform.
Uses Strawberry GraphQL library for type-safe schema definitions.

Features:
- Unified query interface
- Type-safe resolvers
- Nested data fetching
- Flexible filtering and aggregation
- Real-time subscriptions

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `__all__` = `['get_graphql_router', 'schema', 'SimpleGraphQL']`

## Dependencies & Imports
typing.List, typing.Optional, typing.Dict, typing.Any, datetime.datetime, json, sqlite3, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Class: `SimpleGraphQL`
**Description:**
```text
Simple GraphQL-like interface without external dependencies
```

### Method: `execute`
**Logic & Purpose:**
```text
Execute a simple query
```

**Parameters:** `query, variables`
**Variables Used:** `cursor, end_match, end_date, rows, start_match, start_date, query_sql, conn, metrics`
**Implementation:**
```python
@staticmethod
def execute(query: str, variables: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    """Execute a simple query"""
    try:
        if 'health' in query:
            return {'data': {'health': 'Analytics API is running'}}
        if 'metrics' in query:
            if not usage_tracker.enabled:
                return {'data': {'metrics': []}}
            import re
            start_match = re.search('startDate:\\s*"([^"]+)"', query)
            end_match = re.search('endDate:\\s*"([^"]+)"', query)
            if not start_match or not end_match:
                return {'error': 'Missing startDate or endDate'}
            start_date = start_match.group(1)
            end_date = end_match.group(1)
            conn = sqlite3.connect(usage_tracker.db_path)
            conn.row_factory = sqlite3.Row
            query_sql = '\n                    SELECT\n                        date(timestamp) as date,\n                        SUM(total_tokens) as tokens,\n                        SUM(estimated_cost) as cost,\n                        COUNT(*) as requests\n                    FROM api_requests\n                    WHERE timestamp >= ? AND timestamp <= ?\n                    GROUP BY date(timestamp)\n                    ORDER BY date\n                '
            cursor = conn.execute(query_sql, [start_date, end_date])
            rows = cursor.fetchall()
            conn.close()
            metrics = [{'timestamp': row['date'], 'tokens': row['tokens'] or 0, 'cost': row['cost'] or 0, 'requests': row['requests'] or 0} for row in rows]
            return {'data': {'metrics': metrics}}
        return {'error': 'Query not recognized'}
    except Exception as e:
        return {'error': str(e)}
```

---

## Feature Function: `get_graphql_router`
**Logic & Purpose:**
```text
Get the GraphQL router for FastAPI
```

**Parameters:** ``
**Variables Used:** `router`
**Implementation:**
```python
def get_graphql_router():
    """Get the GraphQL router for FastAPI"""
    if HAS_STRAWBERRY:
        from strawberry.fastapi import GraphQLRouter
        return GraphQLRouter(schema, graphiql=True)
    else:
        from fastapi import APIRouter
        router = APIRouter()

        @router.post('/graphql')
        async def simple_graphql(query: Dict[str, Any]):
            return SimpleGraphQL.execute(query.get('query', ''), query.get('variables', {}))

        @router.get('/graphql')
        async def graphql_playground():
            return {'message': 'GraphQL Playground requires strawberry-graphql', 'install': 'pip install strawberry-graphql', 'alternative': 'Use POST /graphql with JSON: {"query": "..."}'}
        return router
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/reports.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/reports.py`

**Module Overview**: 
```text
Reports API - Phase 3

Endpoints for report generation, templates, scheduling, and delivery

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, fastapi.BackgroundTasks, typing.List, typing.Dict, typing.Any, typing.Optional, datetime.datetime, datetime.timedelta, pydantic.BaseModel, sqlite3, json, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker, src.services.report_generator.report_generator, src.services.report_generator.ReportTemplate

## Feature Class: `ReportConfigRequest`
**Description:**
```text
Request model for report generation
```

---

## Feature Function: `get_report_templates`
**Logic & Purpose:**
```text
Get all report templates
```

**Parameters:** ``
**Variables Used:** `templates`
**Implementation:**
```python
@router.get('/api/reports/templates')
async def get_report_templates():
    """Get all report templates"""
    try:
        if not usage_tracker.enabled:
            return {'templates': []}
        templates = report_generator.get_templates()
        return {'templates': [{'id': t.id, 'name': t.name, 'description': t.description, 'config': t.config, 'created_at': t.created_at, 'created_by': t.created_by, 'is_default': t.is_default} for t in templates], 'count': len(templates)}
    except Exception as e:
        logger.error(f'Get templates failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `create_report_template`
**Logic & Purpose:**
```text
Create a new report template
```

**Parameters:** `template_data`
**Variables Used:** `template_id`
**Implementation:**
```python
@router.post('/api/reports/templates')
async def create_report_template(template_data: Dict[str, Any]):
    """Create a new report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template_id = report_generator.create_template(name=template_data.get('name', 'Custom Template'), description=template_data.get('description', ''), config=template_data.get('config', {}), created_by=template_data.get('created_by', 'web_ui'), is_default=template_data.get('is_default', False))
        return {'success': True, 'template_id': template_id, 'message': 'Template created successfully'}
    except Exception as e:
        logger.error(f'Create template failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_report_template`
**Logic & Purpose:**
```text
Get specific report template
```

**Parameters:** `template_id`
**Variables Used:** `template`
**Implementation:**
```python
@router.get('/api/reports/templates/{template_id}')
async def get_report_template(template_id: str):
    """Get specific report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Template not found')
        return {'id': template.id, 'name': template.name, 'description': template.description, 'config': template.config, 'created_at': template.created_at, 'created_by': template.created_by, 'is_default': template.is_default}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Get template failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `delete_report_template`
**Logic & Purpose:**
```text
Delete report template
```

**Parameters:** `template_id`
**Variables Used:** `conn, cursor, deleted`
**Implementation:**
```python
@router.delete('/api/reports/templates/{template_id}')
async def delete_report_template(template_id: str):
    """Delete report template"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('DELETE FROM report_templates WHERE id = ?', (template_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='Template not found')
        return {'success': True, 'template_id': template_id, 'message': 'Template deleted'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Delete template failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `generate_report`
**Logic & Purpose:**
```text
Generate report in specified format (PDF, Excel, CSV)
```

**Parameters:** `report_config`
**Variables Used:** `template, data, brand_logo, media_type, end_date, template_id, format_type, brand_color, filename, start_date`
**Implementation:**
```python
@router.post('/api/reports/generate')
async def generate_report(report_config: ReportConfigRequest):
    """Generate report in specified format (PDF, Excel, CSV)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template_id = report_config.template_id
        start_date = report_config.start_date
        end_date = report_config.end_date
        format_type = report_config.format
        brand_logo = report_config.brand_logo
        brand_color = report_config.brand_color
        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Template not found')
        if format_type == 'pdf':
            data = report_generator.generate_pdf(template, start_date, end_date, brand_logo, brand_color)
            media_type = 'application/pdf'
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.pdf"
        elif format_type == 'excel':
            data = report_generator.generate_excel(template, start_date, end_date)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.xlsx"
        elif format_type == 'csv':
            data = report_generator.generate_csv(template, start_date, end_date).encode('utf-8')
            media_type = 'text/csv'
            filename = f"{template.name.replace(' ', '_')}_{start_date}_{end_date}.csv"
        else:
            raise HTTPException(status_code=400, detail='Invalid format type')
        return {'success': True, 'template': template.name, 'format': format_type, 'size': len(data), 'filename': filename, 'download_url': f'/api/reports/download/{template_id}/{format_type}?start={start_date}&end={end_date}', 'data': data.hex()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Generate report failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `download_report`
**Logic & Purpose:**
```text
Download generated report file
```

**Parameters:** `template_id, format_type, start, end`
**Variables Used:** `filename, template, media_type, data`
**Implementation:**
```python
@router.get('/api/reports/download/{template_id}/{format_type}')
async def download_report(template_id: str, format_type: str, start: str=Query(...), end: str=Query(...)):
    """Download generated report file"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Template not found')
        if format_type == 'pdf':
            data = report_generator.generate_pdf(template, start, end)
            media_type = 'application/pdf'
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.pdf"
        elif format_type == 'excel':
            data = report_generator.generate_excel(template, start, end)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.xlsx"
        elif format_type == 'csv':
            data = report_generator.generate_csv(template, start, end).encode('utf-8')
            media_type = 'text/csv'
            filename = f"{template.name.replace(' ', '_')}_{start}_{end}.csv"
        else:
            raise HTTPException(status_code=400, detail='Invalid format')
        from fastapi.responses import Response
        return Response(content=data, media_type=media_type, headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Download report failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `preview_report`
**Logic & Purpose:**
```text
Generate report preview (metadata only, no file)
```

**Parameters:** `report_config`
**Variables Used:** `template, data, end_date, template_id, start_date`
**Implementation:**
```python
@router.post('/api/reports/generate/preview')
async def preview_report(report_config: Dict[str, Any]):
    """Generate report preview (metadata only, no file)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template_id = report_config.get('template_id')
        start_date = report_config.get('start_date')
        end_date = report_config.get('end_date')
        template = report_generator.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Template not found')
        data = report_generator.generate_report_data(template, start_date, end_date)
        return {'preview': data, 'template': template.name, 'date_range': {'start': start_date, 'end': end_date}}
    except Exception as e:
        logger.error(f'Preview report failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_scheduled_reports`
**Logic & Purpose:**
```text
Get all scheduled reports
```

**Parameters:** ``
**Variables Used:** `scheduled`
**Implementation:**
```python
@router.get('/api/reports/schedule')
async def get_scheduled_reports():
    """Get all scheduled reports"""
    try:
        if not usage_tracker.enabled:
            return {'scheduled': []}
        scheduled = report_generator.get_scheduled_reports()
        return {'scheduled': scheduled, 'count': len(scheduled)}
    except Exception as e:
        logger.error(f'Get scheduled reports failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `schedule_report`
**Logic & Purpose:**
```text
Create scheduled report
```

**Parameters:** `schedule_config`
**Variables Used:** `frequency, recipients, schedule_id, template_id, timezone`
**Implementation:**
```python
@router.post('/api/reports/schedule')
async def schedule_report(schedule_config: Dict[str, Any]):
    """Create scheduled report"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        template_id = schedule_config.get('template_id')
        frequency = schedule_config.get('frequency', 'weekly')
        recipients = schedule_config.get('recipients', [])
        timezone = schedule_config.get('timezone', 'UTC')
        schedule_id = report_generator.schedule_report(template_id=template_id, frequency=frequency, recipients=recipients, timezone=timezone)
        if not schedule_id:
            raise HTTPException(status_code=400, detail='Failed to create schedule')
        return {'success': True, 'schedule_id': schedule_id, 'message': f'Report scheduled {frequency}'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Schedule report failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `toggle_schedule`
**Logic & Purpose:**
```text
Enable/disable scheduled report
```

**Parameters:** `schedule_id`
**Variables Used:** `new_state, conn, cursor, row`
**Implementation:**
```python
@router.post('/api/reports/schedule/{schedule_id}/toggle')
async def toggle_schedule(schedule_id: str):
    """Enable/disable scheduled report"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('SELECT is_active FROM scheduled_reports WHERE id = ?', (schedule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail='Schedule not found')
        new_state = 1 - row[0]
        cursor.execute('UPDATE scheduled_reports SET is_active = ? WHERE id = ?', (new_state, schedule_id))
        conn.commit()
        conn.close()
        return {'success': True, 'schedule_id': schedule_id, 'is_active': bool(new_state), 'message': f"Schedule {('enabled' if new_state else 'disabled')}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Toggle schedule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_execution_history`
**Logic & Purpose:**
```text
Get report execution history
```

**Parameters:** `limit`
**Variables Used:** `history`
**Implementation:**
```python
@router.get('/api/reports/history')
async def get_execution_history(limit: int=Query(50, ge=1, le=200)):
    """Get report execution history"""
    try:
        if not usage_tracker.enabled:
            return {'history': []}
        history = report_generator.get_execution_history(limit)
        return {'history': history, 'count': len(history)}
    except Exception as e:
        logger.error(f'Get execution history failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `check_scheduled_reports`
**Logic & Purpose:**
```text
Check and execute due scheduled reports (manual trigger)
```

**Parameters:** ``
**Variables Used:** `results`
**Implementation:**
```python
@router.post('/api/reports/schedule/check')
async def check_scheduled_reports():
    """Check and execute due scheduled reports (manual trigger)"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        results = report_generator.check_scheduled_reports()
        return {'checked': True, 'reports_processed': len(results), 'results': results}
    except Exception as e:
        logger.error(f'Check scheduled reports failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `reports_health`
**Logic & Purpose:**
```text
Check if report generation is available
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/reports/health')
async def reports_health():
    """Check if report generation is available"""
    return {'status': 'healthy', 'enabled': usage_tracker.enabled, 'formats_supported': ['pdf', 'excel', 'csv'], 'features': ['templates', 'scheduling', 'exports', 'previews']}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/providers.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/providers.py`

**Module Overview**: 
```text
Provider Authentication API

Endpoints for managing provider authentication tokens and credentials.

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, typing.Dict, typing.Any, typing.Optional, datetime.datetime, src.core.logging.logger, src.services.providers.kiro_token_manager.KiroTokenManager, src.services.providers.kiro_token_manager.get_token_manager, src.services.providers.kiro_token_manager.store_kiro_tokens, src.services.providers.kiro_token_manager.has_kiro_token, src.services.providers.provider_detector.detect_provider, src.services.providers.provider_detector.get_provider_info, src.services.providers.provider_detector.get_provider_config, src.services.providers.provider_detector.requires_kiro_token

## Feature Function: `get_provider_info_endpoint`
**Logic & Purpose:**
```text
Get provider information for a given base URL.

Args:
    base_url: The API base URL to analyze

Returns:
    Provider detection results
```

**Parameters:** `base_url`
**Variables Used:** `config`
**Implementation:**
```python
@router.get('/api/providers/{base_url}/info')
async def get_provider_info_endpoint(base_url: str):
    """
    Get provider information for a given base URL.

    Args:
        base_url: The API base URL to analyze

    Returns:
        Provider detection results
    """
    try:
        provider, normalization, auth_type = get_provider_info(base_url)
        config = get_provider_config(provider)
        return {'base_url': base_url, 'detected_provider': provider, 'normalization_level': normalization, 'auth_type': auth_type, 'config': config, 'requires_kiro_token': requires_kiro_token(base_url)}
    except Exception as e:
        logger.error(f'Failed to get provider info: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `set_kiro_tokens`
**Logic & Purpose:**
```text
Set Kiro authentication tokens.

Args:
    token_data: Dictionary containing:
        - access_token (required): Kiro access token
        - refresh_token (optional): Kiro refresh token
        - expires_in (optional): Token lifetime in seconds

Returns:
    Success confirmation
```

**Parameters:** `token_data`
**Variables Used:** `expires_in, access_token, refresh_token, success`
**Implementation:**
```python
@router.post('/api/providers/kiro/tokens')
async def set_kiro_tokens(token_data: Dict[str, Any]):
    """
    Set Kiro authentication tokens.

    Args:
        token_data: Dictionary containing:
            - access_token (required): Kiro access token
            - refresh_token (optional): Kiro refresh token
            - expires_in (optional): Token lifetime in seconds

    Returns:
        Success confirmation
    """
    try:
        access_token = token_data.get('access_token')
        if not access_token:
            raise HTTPException(status_code=400, detail='access_token is required')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        success = store_kiro_tokens(access_token, refresh_token, expires_in)
        if success:
            return {'success': True, 'provider': 'kiro', 'status': 'tokens_stored', 'stored_at': datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=500, detail='Failed to store tokens')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to store Kiro tokens: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_kiro_tokens_info`
**Logic & Purpose:**
```text
Get information about stored Kiro tokens.

Returns:
    Token status and metadata
```

**Parameters:** ``
**Variables Used:** `info, manager`
**Implementation:**
```python
@router.get('/api/providers/kiro/tokens')
async def get_kiro_tokens_info():
    """
    Get information about stored Kiro tokens.

    Returns:
        Token status and metadata
    """
    try:
        manager = get_token_manager()
        info = manager.get_token_info()
        return {'provider': 'kiro', 'tokens': info, 'has_valid_token': has_kiro_token()}
    except Exception as e:
        logger.error(f'Failed to get Kiro token info: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `clear_kiro_tokens`
**Logic & Purpose:**
```text
Clear stored Kiro tokens.

Returns:
    Success confirmation
```

**Parameters:** ``
**Variables Used:** `manager`
**Implementation:**
```python
@router.delete('/api/providers/kiro/tokens')
async def clear_kiro_tokens():
    """
    Clear stored Kiro tokens.

    Returns:
        Success confirmation
    """
    try:
        manager = get_token_manager()
        manager.clear_tokens()
        return {'success': True, 'provider': 'kiro', 'status': 'tokens_cleared'}
    except Exception as e:
        logger.error(f'Failed to clear Kiro tokens: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `refresh_kiro_tokens`
**Logic & Purpose:**
```text
Refresh Kiro tokens using refresh token (if available).

Returns:
    New token information or error
```

**Parameters:** ``
**Variables Used:** `success, manager`
**Implementation:**
```python
@router.post('/api/providers/kiro/refresh')
async def refresh_kiro_tokens():
    """
    Refresh Kiro tokens using refresh token (if available).

    Returns:
        New token information or error
    """
    try:
        manager = get_token_manager()
        success = manager.refresh_tokens()
        if success:
            return {'success': True, 'provider': 'kiro', 'status': 'refreshed', 'new_tokens': manager.get_token_info()}
        else:
            raise HTTPException(status_code=400, detail='No refresh token available or refresh failed')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to refresh Kiro tokens: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `kiro_health_check`
**Logic & Purpose:**
```text
Check if Kiro provider is configured and ready.

Returns:
    Health status
```

**Parameters:** ``
**Variables Used:** `manager, token_info, has_token`
**Implementation:**
```python
@router.get('/api/providers/kiro/health')
async def kiro_health_check():
    """
    Check if Kiro provider is configured and ready.

    Returns:
        Health status
    """
    try:
        manager = get_token_manager()
        has_token = manager.has_valid_token()
        token_info = manager.get_token_info()
        return {'provider': 'kiro', 'status': 'healthy' if has_token else 'unconfigured', 'has_valid_token': has_token, 'token_info': token_info, 'config_instructions': {'environment_variable': 'KIRO_ACCESS_TOKEN', 'api_endpoint': '/api/providers/kiro/tokens (POST)', 'required_data': {'access_token': 'your-kiro-access-token'}}}
    except Exception as e:
        logger.error(f'Kiro health check failed: {e}')
        return {'provider': 'kiro', 'status': 'error', 'error': str(e)}
```

---

## Feature Function: `test_provider_auth`
**Logic & Purpose:**
```text
Test authentication for a specific provider.

Args:
    provider: Provider name (e.g., 'kiro')
    config: Configuration data for testing

Returns:
    Authentication test results
```

**Parameters:** `provider, config`
**Variables Used:** `has_token`
**Implementation:**
```python
@router.post('/api/providers/{provider}/test')
async def test_provider_auth(provider: str, config: Dict[str, Any]):
    """
    Test authentication for a specific provider.

    Args:
        provider: Provider name (e.g., 'kiro')
        config: Configuration data for testing

    Returns:
        Authentication test results
    """
    try:
        if provider.lower() == 'kiro':
            has_token = has_kiro_token()
            return {'provider': provider, 'auth_test': 'pending', 'status': 'configured' if has_token else 'unconfigured', 'message': 'Token exists - ready for API calls' if has_token else 'No token configured'}
        else:
            raise HTTPException(status_code=400, detail=f'Provider {provider} not supported for auth testing')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Auth test failed for {provider}: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/web_ui.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/web_ui.py`

**Module Overview**: 
```text
Web UI and Configuration API endpoints
```

## Global Presets & Variables
- `router` = `APIRouter()`
- `PROFILES_DIR` = `Path('configs/profiles')`
- `CROSSTALK_PRESETS_DIR` = `Path('configs/crosstalk/presets')`
- `CROSSTALK_SESSIONS_DIR` = `Path('configs/crosstalk/sessions')`

## Dependencies & Imports
os, json, datetime.datetime, datetime.timedelta, pathlib.Path, typing.Dict, typing.List, typing.Any, typing.Optional, fastapi.APIRouter, fastapi.HTTPException, pydantic.BaseModel, httpx, src.core.config.config, src.core.logging.logger, src.cli.env_utils.update_env_values, src.services.models.free_model_rankings.get_or_build_free_model_rankings, src.services.models.selection_history.get_recent_selections, src.services.models.selection_history.record_selection, src.api.websocket_logs.get_cascade_stats

## Feature Function: `validate_safe_filename`
**Parameters:** `name`
**Implementation:**
```python
def validate_safe_filename(name: str) -> str:
    if not name or any((c in name for c in ('/', '\\', '.', '\x00'))):
        raise HTTPException(status_code=400, detail='Invalid filename format. Cannot contain path separators or dots.')
    return name
```

---

## Feature Class: `ConfigUpdate`
**Description:**
```text
Configuration update model - supports all web UI settings
```

---

## Feature Class: `ProfileCreate`
**Description:**
```text
Profile creation model
```

---

## Feature Function: `get_config`
**Logic & Purpose:**
```text
Get current configuration - returns all settings for web UI
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/config')
async def get_config():
    """Get current configuration - returns all settings for web UI"""
    return {'provider_api_key': '***' if os.getenv('PROVIDER_API_KEY') or config.openai_api_key else '', 'provider_base_url': os.getenv('PROVIDER_BASE_URL') or config.openai_base_url, 'proxy_auth_key': '***' if os.getenv('PROXY_AUTH_KEY') or config.anthropic_api_key else '', 'default_provider': os.getenv('DEFAULT_PROVIDER', 'openrouter'), 'azure_api_version': os.getenv('AZURE_API_VERSION', ''), 'enable_openrouter_selection': os.getenv('ENABLE_OPENROUTER_SELECTION', 'true'), 'openai_api_key': '***' if config.openai_api_key else '', 'anthropic_api_key': '***' if config.anthropic_api_key else '', 'openai_base_url': config.openai_base_url, 'host': os.getenv('HOST', config.host if hasattr(config, 'host') else '0.0.0.0'), 'port': os.getenv('PORT', str(config.port) if hasattr(config, 'port') else '8082'), 'log_level': os.getenv('LOG_LEVEL', config.log_level if hasattr(config, 'log_level') else 'INFO'), 'big_model': config.big_model, 'middle_model': config.middle_model, 'small_model': config.small_model, 'reasoning_effort': config.reasoning_effort if hasattr(config, 'reasoning_effort') else '', 'reasoning_max_tokens': str(config.reasoning_max_tokens) if hasattr(config, 'reasoning_max_tokens') and config.reasoning_max_tokens else '', 'reasoning_exclude': os.getenv('REASONING_EXCLUDE', 'false'), 'verbosity': os.getenv('VERBOSITY', ''), 'big_model_reasoning': os.getenv('BIG_MODEL_REASONING', ''), 'middle_model_reasoning': os.getenv('MIDDLE_MODEL_REASONING', ''), 'small_model_reasoning': os.getenv('SMALL_MODEL_REASONING', ''), 'enable_custom_big_prompt': os.getenv('ENABLE_CUSTOM_BIG_PROMPT', 'false'), 'big_system_prompt': os.getenv('BIG_SYSTEM_PROMPT', ''), 'big_system_prompt_file': os.getenv('BIG_SYSTEM_PROMPT_FILE', ''), 'enable_custom_middle_prompt': os.getenv('ENABLE_CUSTOM_MIDDLE_PROMPT', 'false'), 'middle_system_prompt': os.getenv('MIDDLE_SYSTEM_PROMPT', ''), 'middle_system_prompt_file': os.getenv('MIDDLE_SYSTEM_PROMPT_FILE', ''), 'enable_custom_small_prompt': os.getenv('ENABLE_CUSTOM_SMALL_PROMPT', 'false'), 'small_system_prompt': os.getenv('SMALL_SYSTEM_PROMPT', ''), 'small_system_prompt_file': os.getenv('SMALL_SYSTEM_PROMPT_FILE', ''), 'max_tokens_limit': str(config.max_tokens_limit) if hasattr(config, 'max_tokens_limit') else '65536', 'min_tokens_limit': str(config.min_tokens_limit) if hasattr(config, 'min_tokens_limit') else '4096', 'request_timeout': str(config.request_timeout) if hasattr(config, 'request_timeout') else '120', 'max_retries': str(config.max_retries) if hasattr(config, 'max_retries') else '2', 'terminal_display_mode': os.getenv('TERMINAL_DISPLAY_MODE', 'detailed'), 'terminal_color_scheme': os.getenv('TERMINAL_COLOR_SCHEME', 'auto'), 'terminal_show_workspace': os.getenv('TERMINAL_SHOW_WORKSPACE', 'true'), 'terminal_show_context_pct': os.getenv('TERMINAL_SHOW_CONTEXT_PCT', 'true'), 'terminal_show_task_type': os.getenv('TERMINAL_SHOW_TASK_TYPE', 'true'), 'terminal_show_speed': os.getenv('TERMINAL_SHOW_SPEED', 'true'), 'terminal_show_cost': os.getenv('TERMINAL_SHOW_COST', 'true'), 'terminal_show_duration_colors': os.getenv('TERMINAL_SHOW_DURATION_COLORS', 'true'), 'terminal_session_colors': os.getenv('TERMINAL_SESSION_COLORS', 'true'), 'log_style': os.getenv('LOG_STYLE', 'rich'), 'compact_logger': os.getenv('COMPACT_LOGGER', 'false'), 'show_token_counts': os.getenv('SHOW_TOKEN_COUNTS', 'true'), 'show_performance': os.getenv('SHOW_PERFORMANCE', 'true'), 'color_scheme': os.getenv('COLOR_SCHEME', 'auto'), 'track_usage': os.getenv('TRACK_USAGE', 'false'), 'usage_db_path': os.getenv('USAGE_DB_PATH', 'usage_tracking.db'), 'enable_dashboard': os.getenv('ENABLE_DASHBOARD', 'false'), 'dashboard_layout': os.getenv('DASHBOARD_LAYOUT', 'default'), 'dashboard_refresh': os.getenv('DASHBOARD_REFRESH', '0.5'), 'dashboard_waterfall_size': os.getenv('DASHBOARD_WATERFALL_SIZE', '20'), 'providers': {name: {'url': entry['url'], 'has_key': bool(entry.get('api_key'))} for name, entry in config.provider_registry.items()}, 'big_model': os.getenv('BIG_MODEL', config.big_model), 'middle_model': os.getenv('MIDDLE_MODEL', config.middle_model), 'small_model': os.getenv('SMALL_MODEL', config.small_model), 'model_cascade': os.getenv('MODEL_CASCADE', 'false'), 'big_cascade': os.getenv('BIG_CASCADE', ''), 'middle_cascade': os.getenv('MIDDLE_CASCADE', ''), 'small_cascade': os.getenv('SMALL_CASCADE', ''), 'model_cascade_daily_limit': os.getenv('MODEL_CASCADE_DAILY_LIMIT', str(getattr(config, 'model_cascade_daily_limit', 1000))), 'passthrough_mode': config.passthrough_mode if hasattr(config, 'passthrough_mode') else False}
```

---

## Feature Function: `update_config`
**Logic & Purpose:**
```text
Update configuration (hot reload without restart)
```

**Parameters:** `config_update`
**Variables Used:** `key_map, env_key, env_updates, payload`
**Implementation:**
```python
@router.post('/api/config')
async def update_config(config_update: ConfigUpdate):
    """Update configuration (hot reload without restart)"""
    try:
        if config_update.openai_api_key is not None:
            if config_update.openai_api_key:
                config.openai_api_key = config_update.openai_api_key
                config.passthrough_mode = False
            else:
                config.openai_api_key = None
                config.passthrough_mode = True
        if config_update.anthropic_api_key is not None:
            config.anthropic_api_key = config_update.anthropic_api_key or None
        if config_update.openai_base_url:
            config.openai_base_url = config_update.openai_base_url
        if config_update.provider_api_key is not None:
            config.openai_api_key = config_update.provider_api_key or None
        if config_update.provider_base_url is not None:
            config.openai_base_url = config_update.provider_base_url or config.openai_base_url
        if config_update.big_model:
            config.big_model = config_update.big_model
        if config_update.middle_model:
            config.middle_model = config_update.middle_model
        if config_update.small_model:
            config.small_model = config_update.small_model
        if hasattr(config, 'reasoning_effort') and config_update.reasoning_effort is not None:
            config.reasoning_effort = config_update.reasoning_effort
        if hasattr(config, 'reasoning_max_tokens') and config_update.reasoning_max_tokens:
            config.reasoning_max_tokens = int(config_update.reasoning_max_tokens)
        if config_update.model_cascade is not None:
            config.model_cascade = config_update.model_cascade.lower() == 'true'
        if config_update.big_cascade is not None:
            config.big_cascade = [m.strip() for m in config_update.big_cascade.split(',') if m.strip()]
        if config_update.middle_cascade is not None:
            config.middle_cascade = [m.strip() for m in config_update.middle_cascade.split(',') if m.strip()]
        if config_update.small_cascade is not None:
            config.small_cascade = [m.strip() for m in config_update.small_cascade.split(',') if m.strip()]
        if config_update.model_cascade_daily_limit is not None and hasattr(config, 'model_cascade_daily_limit'):
            config.model_cascade_daily_limit = int(config_update.model_cascade_daily_limit)
        payload = config_update.model_dump(exclude_none=True)
        env_updates = {}
        key_map = {'provider_api_key': 'PROVIDER_API_KEY', 'provider_base_url': 'PROVIDER_BASE_URL', 'proxy_auth_key': 'PROXY_AUTH_KEY', 'host': 'HOST', 'port': 'PORT', 'log_level': 'LOG_LEVEL', 'big_model': 'BIG_MODEL', 'middle_model': 'MIDDLE_MODEL', 'small_model': 'SMALL_MODEL', 'reasoning_effort': 'REASONING_EFFORT', 'reasoning_max_tokens': 'REASONING_MAX_TOKENS', 'reasoning_exclude': 'REASONING_EXCLUDE', 'max_tokens_limit': 'MAX_TOKENS_LIMIT', 'min_tokens_limit': 'MIN_TOKENS_LIMIT', 'request_timeout': 'REQUEST_TIMEOUT', 'track_usage': 'TRACK_USAGE', 'enable_dashboard': 'ENABLE_DASHBOARD', 'dashboard_layout': 'DASHBOARD_LAYOUT', 'dashboard_refresh': 'DASHBOARD_REFRESH', 'compact_logger': 'COMPACT_LOGGER', 'big_model': 'BIG_MODEL', 'middle_model': 'MIDDLE_MODEL', 'small_model': 'SMALL_MODEL', 'model_cascade': 'MODEL_CASCADE', 'big_cascade': 'BIG_CASCADE', 'middle_cascade': 'MIDDLE_CASCADE', 'small_cascade': 'SMALL_CASCADE', 'model_cascade_daily_limit': 'MODEL_CASCADE_DAILY_LIMIT', 'terminal_display_mode': 'TERMINAL_DISPLAY_MODE', 'terminal_color_scheme': 'TERMINAL_COLOR_SCHEME', 'terminal_show_workspace': 'TERMINAL_SHOW_WORKSPACE', 'terminal_show_context_pct': 'TERMINAL_SHOW_CONTEXT_PCT', 'terminal_show_task_type': 'TERMINAL_SHOW_TASK_TYPE', 'terminal_show_speed': 'TERMINAL_SHOW_SPEED', 'terminal_show_cost': 'TERMINAL_SHOW_COST', 'terminal_show_duration_colors': 'TERMINAL_SHOW_DURATION_COLORS', 'terminal_session_colors': 'TERMINAL_SESSION_COLORS', 'log_style': 'LOG_STYLE'}
        for k, v in payload.items():
            env_key = key_map.get(k)
            if env_key:
                env_updates[env_key] = str(v)
        if env_updates:
            update_env_values(env_updates, verbose=False)
            for k, v in env_updates.items():
                os.environ[k] = v
        if config_update.big_model:
            record_selection('big', config_update.big_model, source='web')
        if config_update.middle_model:
            record_selection('middle', config_update.middle_model, source='web')
        if config_update.small_model:
            record_selection('small', config_update.small_model, source='web')
        logger.info('Configuration updated via Web UI')
        return {'status': 'success', 'message': 'Configuration updated'}
    except Exception as e:
        logger.error(f'Failed to update config: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `reload_config`
**Logic & Purpose:**
```text
Reload configuration from environment variables
```

**Parameters:** ``
**Implementation:**
```python
@router.post('/api/config/reload')
async def reload_config():
    """Reload configuration from environment variables"""
    try:
        config.openai_api_key = os.environ.get('OPENAI_API_KEY')
        config.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        config.openai_base_url = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        config.big_model = os.environ.get('BIG_MODEL', 'gpt-4o')
        config.middle_model = os.environ.get('MIDDLE_MODEL', config.big_model)
        config.small_model = os.environ.get('SMALL_MODEL', 'gpt-4o-mini')
        logger.info('Configuration reloaded from environment')
        return {'status': 'success', 'message': 'Configuration reloaded'}
    except Exception as e:
        logger.error(f'Failed to reload config: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_proxy_chain`
**Logic & Purpose:**
```text
Return the current proxy chain configuration.
```

**Parameters:** ``
**Variables Used:** `chain`
**Implementation:**
```python
@router.get('/api/proxy-chain')
async def get_proxy_chain():
    """Return the current proxy chain configuration."""
    try:
        from src.core.proxy_chain import get_chain
        chain = get_chain()
        return chain.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `update_proxy_chain`
**Logic & Purpose:**
```text
Replace the proxy chain configuration and persist to disk.

Accepts the same JSON shape as GET /api/proxy-chain returns.
The running singleton is reloaded immediately.
```

**Parameters:** `body`
**Variables Used:** `new_chain`
**Implementation:**
```python
@router.put('/api/proxy-chain')
async def update_proxy_chain(body: dict):
    """
    Replace the proxy chain configuration and persist to disk.

    Accepts the same JSON shape as GET /api/proxy-chain returns.
    The running singleton is reloaded immediately.
    """
    try:
        from src.core.proxy_chain import ProxyChain, reload_chain
        from src.core.model_router import reload_router
        new_chain = ProxyChain.from_dict(body)
        new_chain.save()
        reload_chain()
        reload_router()
        logger.info('Proxy chain updated via API')
        return {'status': 'success', 'message': 'Proxy chain saved and reloaded'}
    except Exception as e:
        logger.error(f'Failed to update proxy chain: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_router_config`
**Logic & Purpose:**
```text
Return the current model router configuration.
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/router-config')
async def get_router_config():
    """Return the current model router configuration."""
    try:
        from src.core.proxy_chain import get_chain
        from dataclasses import asdict
        return asdict(get_chain().router)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `update_router_config`
**Logic & Purpose:**
```text
Update the model router configuration and persist to disk.

Accepts the same JSON shape as GET /api/router-config returns.
```

**Parameters:** `body`
**Variables Used:** `chain, current`
**Implementation:**
```python
@router.put('/api/router-config')
async def update_router_config(body: dict):
    """
    Update the model router configuration and persist to disk.

    Accepts the same JSON shape as GET /api/router-config returns.
    """
    try:
        from src.core.proxy_chain import RouterConfig, get_chain, reload_chain
        from src.core.model_router import reload_router
        chain = get_chain()
        current = {k: v for k, v in vars(chain.router).items()}
        current.update({k: v for k, v in body.items() if hasattr(chain.router, k)})
        chain.router = RouterConfig(**current)
        chain.save()
        reload_chain()
        reload_router()
        logger.info('Router config updated via API')
        return {'status': 'success', 'message': 'Router config saved and reloaded'}
    except Exception as e:
        logger.error(f'Failed to update router config: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `list_profiles`
**Logic & Purpose:**
```text
List all saved profiles
```

**Parameters:** ``
**Variables Used:** `profile_data, profiles`
**Implementation:**
```python
@router.get('/api/profiles')
async def list_profiles():
    """List all saved profiles"""
    try:
        profiles = []
        for profile_file in PROFILES_DIR.glob('*.json'):
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
                profiles.append({'name': profile_data['name'], 'modified': profile_data.get('modified', datetime.now().isoformat()), 'big_model': profile_data['config'].get('big_model', ''), 'middle_model': profile_data['config'].get('middle_model', ''), 'small_model': profile_data['config'].get('small_model', '')})
        return profiles
    except Exception as e:
        logger.error(f'Failed to list profiles: {e}')
        return []
```

---

## Feature Function: `save_profile`
**Logic & Purpose:**
```text
Save a configuration profile
```

**Parameters:** `profile`
**Variables Used:** `profile_file, profile_data, safe_name`
**Implementation:**
```python
@router.post('/api/profiles')
async def save_profile(profile: ProfileCreate):
    """Save a configuration profile"""
    try:
        safe_name = validate_safe_filename(profile.name)
        profile_file = PROFILES_DIR / f'{safe_name}.json'
        profile_data = {'name': profile.name, 'modified': datetime.now().isoformat(), 'config': profile.config}
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        logger.info(f"Profile '{profile.name}' saved")
        return {'status': 'success', 'message': f"Profile '{profile.name}' saved"}
    except Exception as e:
        logger.error(f'Failed to save profile: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_profile`
**Logic & Purpose:**
```text
Get a specific profile
```

**Parameters:** `profile_name`
**Variables Used:** `profile_file, safe_name`
**Implementation:**
```python
@router.get('/api/profiles/{profile_name}')
async def get_profile(profile_name: str):
    """Get a specific profile"""
    try:
        safe_name = validate_safe_filename(profile_name)
        profile_file = PROFILES_DIR / f'{safe_name}.json'
        if not profile_file.exists():
            raise HTTPException(status_code=404, detail='Profile not found')
        with open(profile_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Profile not found')
    except Exception as e:
        logger.error(f'Failed to load profile: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `deactivate_profile`
**Logic & Purpose:**
```text
Delete a profile
```

**Parameters:** `profile_name`
**Variables Used:** `profile_file, safe_name`
**Implementation:**
```python
@router.delete('/api/profiles/{profile_name}')
async def deactivate_profile(profile_name: str):
    """Delete a profile"""
    try:
        safe_name = validate_safe_filename(profile_name)
        profile_file = PROFILES_DIR / f'{safe_name}.json'
        if not profile_file.exists():
            raise HTTPException(status_code=404, detail='Profile not found')
        profile_file.unlink()
        logger.info(f"Profile '{profile_name}' deleted")
        return {'status': 'success', 'message': f"Profile '{profile_name}' deleted"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Profile not found')
    except Exception as e:
        logger.error(f'Failed to delete profile: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `list_models`
**Logic & Purpose:**
```text
List available models with optional filtering and organization.

Args:
    provider: Filter by provider (openai, anthropic, google, etc.)
    search: Search in model ID and name
    supports_reasoning: Filter by reasoning capability
    supports_vision: Filter by vision capability
    supports_tools: Filter by tool use capability
    is_free: Filter by free pricing
    min_context: Minimum context length
    limit: Maximum number of results
    group_by_provider: Return models organized by provider instead of flat list

Returns:
    Either flat list or grouped structure based on group_by_provider
```

**Parameters:** `provider, search, supports_reasoning, supports_vision, supports_tools, is_free, min_context, limit, group_by_provider`
**Variables Used:** `status, grouped_response, model_provider, provider_status, models_file, models, models_data, grouped`
**Implementation:**
```python
@router.get('/api/models')
async def list_models(provider: Optional[str]=None, search: Optional[str]=None, supports_reasoning: Optional[bool]=None, supports_vision: Optional[bool]=None, supports_tools: Optional[bool]=None, is_free: Optional[bool]=None, min_context: Optional[int]=None, limit: Optional[int]=None, group_by_provider: bool=False):
    """
    List available models with optional filtering and organization.

    Args:
        provider: Filter by provider (openai, anthropic, google, etc.)
        search: Search in model ID and name
        supports_reasoning: Filter by reasoning capability
        supports_vision: Filter by vision capability
        supports_tools: Filter by tool use capability
        is_free: Filter by free pricing
        min_context: Minimum context length
        limit: Maximum number of results
        group_by_provider: Return models organized by provider instead of flat list

    Returns:
        Either flat list or grouped structure based on group_by_provider
    """
    try:
        from src.services.models.openrouter_fetcher import filter_models, get_model_stats
        models = filter_models(provider=provider, supports_reasoning=supports_reasoning, supports_vision=supports_vision, supports_tools=supports_tools, is_free=is_free, min_context=min_context, search=search)
        if limit and len(models) > limit:
            models = models[:limit]
        if group_by_provider:
            grouped = {}
            for model in models:
                model_provider = model.get('provider', 'unknown')
                if model_provider not in grouped:
                    grouped[model_provider] = []
                grouped[model_provider].append(model)
            try:
                from src.core.config import get_provider_status_cache
                provider_status = get_provider_status_cache()
            except Exception as _e:
                provider_status = {}
            grouped_response = []
            for provider_name, provider_models in grouped.items():
                status = provider_status.get(provider_name, {})
                grouped_response.append({'provider': provider_name, 'is_available': status.get('is_valid', False), 'model_count': len(provider_models), 'models': provider_models, 'display_name': provider_name.replace('_', ' ').title()})
            grouped_response.sort(key=lambda x: (not x['is_available'], -x['model_count']))
            return {'grouped': grouped_response, 'flat': models, 'count': len(models), 'stats': get_model_stats()}
        return {'models': models, 'count': len(models), 'stats': get_model_stats()}
    except ImportError:
        try:
            models_file = Path('models.json')
            if models_file.exists():
                with open(models_file, 'r') as f:
                    models_data = json.load(f)
                    return {'models': models_data.get('models', []), 'count': 0}
            return {'models': [], 'count': 0}
        except Exception:
            return {'models': [], 'count': 0}
    except Exception as e:
        logger.error(f'Failed to load models: {e}')
        return {'models': [], 'count': 0, 'error': str(e)}
```

---

## Feature Function: `get_free_recommended_models`
**Logic & Purpose:**
```text
Get programmatically ranked free models for coding workflows.
```

**Parameters:** `limit, refresh`
**Variables Used:** `rows, data`
**Implementation:**
```python
@router.get('/api/models/free-recommended')
async def get_free_recommended_models(limit: int=40, refresh: bool=False):
    """Get programmatically ranked free models for coding workflows."""
    try:
        rows = get_or_build_free_model_rankings(force_refresh=refresh)
        data = [{'id': r.model_id, 'provider': r.provider, 'score': r.score, 'class_type': r.class_type, 'age_days': r.age_days, 'context_length': r.context_length, 'max_completion_tokens': r.max_completion_tokens, 'supports_tools': r.supports_tools, 'supports_reasoning': r.supports_reasoning} for r in rows[:max(1, limit)]]
        return {'models': data, 'count': len(data)}
    except Exception as e:
        logger.error(f'Failed to get free recommended models: {e}')
        return {'models': [], 'count': 0, 'error': str(e)}
```

---

## Feature Function: `get_model_selection_history`
**Logic & Purpose:**
```text
Get recent model selection history (TUI + Web).
```

**Parameters:** `limit`
**Variables Used:** `events`
**Implementation:**
```python
@router.get('/api/models/selection-history')
async def get_model_selection_history(limit: int=30):
    """Get recent model selection history (TUI + Web)."""
    try:
        events = get_recent_selections(limit=limit)
        return {'events': [e.__dict__ for e in events], 'count': len(events)}
    except Exception as e:
        logger.error(f'Failed to get selection history: {e}')
        return {'events': [], 'count': 0, 'error': str(e)}
```

---

## Feature Function: `get_model_catalog`
**Logic & Purpose:**
```text
Get curated model catalog with categories and specs.

Returns:
    Curated model lists organized by category (free, smartest, coding, value)
    plus recent models from selection history
```

**Parameters:** ``
**Variables Used:** `recent, result, all_lists`
**Implementation:**
```python
@router.get('/api/models/catalog')
async def get_model_catalog():
    """
    Get curated model catalog with categories and specs.

    Returns:
        Curated model lists organized by category (free, smartest, coding, value)
        plus recent models from selection history
    """
    try:
        from src.services.models.model_catalog import model_catalog
        all_lists = model_catalog.get_all_curated(limit_per_category=5)
        result = {}
        for category, models in all_lists.items():
            result[category] = [{'id': m.id, 'name': m.name, 'provider': m.provider, 'context_length': m.context_length, 'max_output': m.max_output, 'price_per_1m_input': m.price_per_1m_input, 'price_per_1m_output': m.price_per_1m_output, 'throughput_tps': m.throughput_tps, 'intelligence_score': m.intelligence_score, 'is_free': m.is_free} for m in models]
        recent = model_catalog.get_recent_models(limit=5)
        result['recent'] = [{'id': m.id, 'name': m.name, 'provider': m.provider, 'context_length': m.context_length, 'max_output': m.max_output, 'is_free': m.is_free} for m in recent]
        return result
    except Exception as e:
        logger.error(f'Failed to get model catalog: {e}')
        return {'error': str(e), 'free': [], 'smartest': [], 'coding': [], 'value': [], 'recent': []}
```

---

## Feature Function: `get_model_specs`
**Logic & Purpose:**
```text
Get specifications for a specific model.
```

**Parameters:** `model_id`
**Variables Used:** `spec`
**Implementation:**
```python
@router.get('/api/models/specs/{model_id}')
async def get_model_specs(model_id: str):
    """Get specifications for a specific model."""
    try:
        from src.services.models.model_catalog import model_catalog
        spec = model_catalog.get_model_spec(model_id)
        if spec:
            return {'id': spec.id, 'name': spec.name, 'provider': spec.provider, 'context_length': spec.context_length, 'max_output': spec.max_output, 'price_per_1m_input': spec.price_per_1m_input, 'price_per_1m_output': spec.price_per_1m_output, 'throughput_tps': spec.throughput_tps, 'intelligence_score': spec.intelligence_score, 'is_free': spec.is_free}
        return {'error': 'Model not found'}
    except Exception as e:
        logger.error(f'Failed to get model specs: {e}')
        return {'error': str(e)}
```

---

## Feature Function: `refresh_model_catalog`
**Logic & Purpose:**
```text
Refresh model catalog from scraper.
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/models/refresh-catalog')
async def refresh_model_catalog():
    """
    Refresh model catalog from scraper.
    """
    try:
        import subprocess
        from pathlib import Path
        result = subprocess.run(['python', '-m', 'src.services.models.catalog_sync', '--sync'], cwd=Path(__file__).parent.parent.parent, capture_output=True, text=True, timeout=120)
        from src.services.models.model_catalog import model_catalog
        model_catalog.reload()
        return {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr if result.returncode != 0 else None}
    except Exception as e:
        logger.error(f'Failed to refresh catalog: {e}')
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `scout_sync_models`
**Logic & Purpose:**
```text
Run model-scraper to sync OpenRouter models.

Args:
    force: Force sync even if recently synced

Returns:
    Sync status and results
```

**Parameters:** `force`
**Variables Used:** `scout, result`
**Implementation:**
```python
@router.post('/api/models/scout-sync')
async def scout_sync_models(force: bool=False):
    """
    Run model-scraper to sync OpenRouter models.

    Args:
        force: Force sync even if recently synced

    Returns:
        Sync status and results
    """
    try:
        from src.services.openrouter_model_scout.integration import get_model_scout
        scout = get_model_scout()
        result = await scout.run_sync(force=force)
        from src.services.models.model_catalog import model_catalog
        model_catalog.reload()
        return result
    except Exception as e:
        logger.error(f'Model scout sync failed: {e}')
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_scout_status`
**Logic & Purpose:**
```text
Get model-scraper status and cached data.
```

**Parameters:** ``
**Variables Used:** `scout`
**Implementation:**
```python
@router.get('/api/models/scout-status')
async def get_scout_status():
    """
    Get model-scraper status and cached data.
    """
    try:
        from src.services.openrouter_model_scout.integration import get_model_scout
        scout = get_model_scout()
        return {'last_sync': scout.get_last_sync_time().isoformat() if scout.get_last_sync_time() else None, 'is_sync_needed': scout.is_sync_needed(), 'free_models_count': len(scout.get_free_models()), 'smartest_models_count': len(scout.get_smartest_models()), 'total_models_count': len(scout.get_all_models())}
    except Exception as e:
        logger.error(f'Failed to get scout status: {e}')
        return {'error': str(e)}
```

---

## Feature Function: `refresh_models`
**Logic & Purpose:**
```text
Force refresh models from OpenRouter API.

Returns:
    Status of the refresh operation
```

**Parameters:** ``
**Implementation:**
```python
@router.post('/api/models/refresh')
async def refresh_models():
    """
    Force refresh models from OpenRouter API.

    Returns:
        Status of the refresh operation
    """
    try:
        from src.services.models.openrouter_fetcher import refresh_openrouter_models
        data, was_refreshed, error = await refresh_openrouter_models(force=True)
        if error:
            return {'success': False, 'error': error, 'models_count': len(data.get('models', []))}
        return {'success': True, 'was_refreshed': was_refreshed, 'models_count': len(data.get('models', [])), 'stats': data.get('stats', {})}
    except Exception as e:
        logger.error(f'Failed to refresh models: {e}')
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `list_providers`
**Logic & Purpose:**
```text
List available providers with their connection status and model counts.

Returns:
    Dict with providers list and summary statistics
```

**Parameters:** ``
**Variables Used:** `status, model_stats, unique_providers, provider_counts, cached_status, providers`
**Implementation:**
```python
@router.get('/api/providers')
async def list_providers():
    """
    List available providers with their connection status and model counts.

    Returns:
        Dict with providers list and summary statistics
    """
    try:
        from src.core.config import get_provider_status_cache
        from src.services.models.openrouter_fetcher import get_model_stats
        cached_status = get_provider_status_cache()
        model_stats = get_model_stats()
        provider_counts = model_stats.get('by_provider', {})
        providers = [{'id': 'openrouter', 'name': 'OpenRouter', 'description': '350+ models, aggregated access', 'endpoint': 'https://openrouter.ai/api/v1', 'env_var': 'OPENROUTER_API_KEY'}, {'id': 'openai', 'name': 'OpenAI', 'description': 'GPT-4, GPT-4o, o1 models', 'endpoint': 'https://api.openai.com/v1', 'env_var': 'OPENAI_API_KEY'}, {'id': 'anthropic', 'name': 'Anthropic', 'description': 'Claude 3.5, Claude 4 models', 'endpoint': 'https://api.anthropic.com/v1', 'env_var': 'ANTHROPIC_API_KEY'}, {'id': 'google', 'name': 'Google Gemini', 'description': 'Gemini Pro, Gemini Flash', 'endpoint': 'https://generativelanguage.googleapis.com/v1beta', 'env_var': 'GOOGLE_API_KEY'}, {'id': 'vibeproxy', 'name': 'VibeProxy (Local)', 'description': 'Local OAuth proxy for Google models', 'endpoint': 'http://127.0.0.1:8317/v1', 'env_var': None}]
        for provider in providers:
            status = cached_status.get(provider['id'], {})
            provider['is_available'] = status.get('is_valid', False)
            provider['status'] = status.get('status', 'unknown')
            provider['key_set'] = bool(os.getenv(provider['env_var'])) if provider['env_var'] else False
            provider['model_count'] = provider_counts.get(provider['id'], 0)
        unique_providers = set()
        for provider in providers:
            unique_providers.add(provider['id'])
        for provider_id, count in provider_counts.items():
            if provider_id not in unique_providers:
                providers.append({'id': provider_id, 'name': provider_id.capitalize(), 'description': f'Provider with {count} models', 'endpoint': None, 'env_var': None, 'is_available': True, 'status': 'via_openrouter', 'key_set': False, 'model_count': count})
        providers.sort(key=lambda p: p['model_count'], reverse=True)
        return {'providers': providers, 'total_models': model_stats.get('total', 0)}
    except Exception as e:
        logger.error(f'Failed to list providers: {e}')
        return {'providers': [], 'total_models': 0, 'error': str(e)}
```

---

## Feature Function: `test_provider`
**Logic & Purpose:**
```text
Test connection to a specific provider.

Returns:
    Connection test result with model count if successful
```

**Parameters:** `provider_id`
**Variables Used:** `env_vars, model_count, api_key, data, endpoints, response, env_var, endpoint`
**Implementation:**
```python
@router.get('/api/providers/{provider_id}/test')
async def test_provider(provider_id: str):
    """
    Test connection to a specific provider.

    Returns:
        Connection test result with model count if successful
    """
    endpoints = {'openrouter': 'https://openrouter.ai/api/v1', 'openai': 'https://api.openai.com/v1', 'anthropic': 'https://api.anthropic.com/v1', 'google': 'https://generativelanguage.googleapis.com/v1beta/openai', 'vibeproxy': 'http://127.0.0.1:8317/v1'}
    env_vars = {'openrouter': 'OPENROUTER_API_KEY', 'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY', 'google': 'GOOGLE_API_KEY'}
    endpoint = endpoints.get(provider_id)
    if not endpoint:
        return {'success': False, 'error': f'Unknown provider: {provider_id}'}
    env_var = env_vars.get(provider_id)
    api_key = os.getenv(env_var) if env_var else 'dummy'
    if not api_key and provider_id != 'vibeproxy':
        return {'success': False, 'error': f'No API key set ({env_var})'}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f'{endpoint}/models', headers={'Authorization': f'Bearer {api_key}'} if api_key else {})
            if response.status_code == 200:
                try:
                    data = response.json()
                    model_count = len(data.get('data', []))
                except Exception as _e:
                    model_count = 0
                return {'success': True, 'status': 'connected', 'models_available': model_count}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key (401)'}
            elif response.status_code == 403:
                return {'success': False, 'error': 'Insufficient permissions (403)'}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
    except httpx.TimeoutException:
        return {'success': False, 'error': 'Connection timeout'}
    except httpx.ConnectError:
        return {'success': False, 'error': 'Cannot connect to provider'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `get_auto_routing_config`
**Logic & Purpose:**
```text
Get automatic routing configuration for a provider.

When a user selects a provider, this returns the recommended:
- Base URL
- Model tier recommendations
- Any special settings

This eliminates manual "select API backend" dialogs.
```

**Parameters:** `provider`
**Variables Used:** `current_config, routing_configs, config`
**Implementation:**
```python
@router.get('/api/routing/auto')
async def get_auto_routing_config(provider: str):
    """
    Get automatic routing configuration for a provider.

    When a user selects a provider, this returns the recommended:
    - Base URL
    - Model tier recommendations
    - Any special settings

    This eliminates manual "select API backend" dialogs.
    """
    routing_configs = {'openrouter': {'base_url': 'https://openrouter.ai/api/v1', 'recommended_big': 'anthropic/claude-3.5-sonnet', 'recommended_middle': 'openai/gpt-4o', 'recommended_small': 'google/gemini-2.0-flash-exp', 'special_notes': 'Uses OPENROUTER_API_KEY - routes to 350+ models', 'auto_config': True}, 'openai': {'base_url': 'https://api.openai.com/v1', 'recommended_big': 'gpt-4o', 'recommended_middle': 'gpt-4o-mini', 'recommended_small': 'gpt-4o-mini', 'special_notes': 'Uses OPENAI_API_KEY - direct OpenAI access', 'auto_config': True}, 'anthropic': {'base_url': 'https://api.anthropic.com/v1', 'recommended_big': 'claude-3-5-sonnet-20241022', 'recommended_middle': 'claude-3-5-sonnet-20241022', 'recommended_small': 'claude-3-haiku-20240307', 'special_notes': 'Uses ANTHROPIC_API_KEY - direct Anthropic access', 'auto_config': True}, 'google': {'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai', 'recommended_big': 'gemini-1.5-pro', 'recommended_middle': 'gemini-1.5-flash', 'recommended_small': 'gemini-1.5-flash', 'special_notes': 'Uses GOOGLE_API_KEY - Google AI Studio', 'auto_config': True}, 'vibeproxy': {'base_url': 'http://127.0.0.1:8317/v1', 'recommended_big': '(auto-detect from /v1/models)', 'recommended_middle': '(auto-detect from /v1/models)', 'recommended_small': '(auto-detect from /v1/models)', 'special_notes': 'Local OAuth proxy - no API key needed for some models', 'auto_config': True}}
    config = routing_configs.get(provider.lower())
    if not config:
        return {'error': 'Unknown provider', 'auto_config': False}
    current_config = {'openai_api_key': '***' if config.openai_api_key else '', 'openai_base_url': config.openai_base_url, 'big_model': config.big_model, 'middle_model': config.middle_model, 'small_model': config.small_model} if hasattr(config, 'openai_api_key') else {}
    return {'provider': provider, 'routing': config, 'current': current_config, 'status': 'ready'}
```

---

## Feature Function: `apply_auto_routing`
**Logic & Purpose:**
```text
Apply automatic routing configuration for a provider.

This eliminates the need for manual backend selection dialogs
and automatically configures the system for the selected provider.
```

**Parameters:** `provider`
**Variables Used:** `routing, routing_response`
**Implementation:**
```python
@router.post('/api/routing/apply')
async def apply_auto_routing(provider: str):
    """
    Apply automatic routing configuration for a provider.

    This eliminates the need for manual backend selection dialogs
    and automatically configures the system for the selected provider.
    """
    try:
        from src.core.config import config
        routing_response = await get_auto_routing_config(provider)
        if 'error' in routing_response:
            raise HTTPException(status_code=400, detail=routing_response['error'])
        routing = routing_response['routing']
        config.openai_base_url = routing['base_url']
        config.big_model = routing['recommended_big']
        config.middle_model = routing['recommended_middle']
        config.small_model = routing['recommended_small']
        config.big_endpoint = ''
        config.middle_endpoint = ''
        config.small_endpoint = ''
        config.default_provider = provider.lower()
        logger.info(f"Auto-routed to {provider}: {routing['base_url']}")
        return {'success': True, 'message': f'Automatically configured for {provider}', 'applied': {'base_url': routing['base_url'], 'big_model': routing['recommended_big'], 'middle_model': routing['recommended_middle'], 'small_model': routing['recommended_small']}}
    except Exception as e:
        logger.error(f'Failed to apply auto routing: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `save_api_key`
**Logic & Purpose:**
```text
Save API key for a specific provider.

Args:
    provider: Provider name (openrouter, openai, anthropic, google)
    api_key: API key to save
```

**Parameters:** `provider, api_key`
**Variables Used:** `env_file, env_vars, lines, content, updated, env_var`
**Implementation:**
```python
@router.post('/api/config/api-key')
async def save_api_key(provider: str, api_key: str):
    """
    Save API key for a specific provider.

    Args:
        provider: Provider name (openrouter, openai, anthropic, google)
        api_key: API key to save
    """
    try:
        import os
        import dotenv
        env_vars = {'openrouter': 'OPENROUTER_API_KEY', 'openai': 'OPENAI_API_KEY', 'anthropic': 'ANTHROPIC_API_KEY', 'google': 'GOOGLE_API_KEY'}
        env_var = env_vars.get(provider.lower())
        if not env_var:
            raise HTTPException(status_code=400, detail=f'Unknown provider: {provider}')
        os.environ[env_var] = api_key
        from src.core.config import config
        if provider.lower() == 'openrouter' or provider.lower() == 'openai':
            config.openai_api_key = api_key
        elif provider.lower() == 'anthropic':
            config.anthropic_api_key = api_key
        env_file = Path('.env')
        if env_file.exists():
            content = env_file.read_text()
            lines = content.split('\n')
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{env_var}='):
                    lines[i] = f'{env_var}={api_key}'
                    updated = True
                    break
            if not updated:
                lines.append(f'{env_var}={api_key}')
            env_file.write_text('\n'.join(lines))
        logger.info(f'Updated API key for {provider}')
        return {'success': True, 'message': f'API key saved for {getProviderDisplayName(provider)}', 'env_var': env_var}
    except Exception as e:
        logger.error(f'Failed to save API key: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `getProviderDisplayName`
**Parameters:** `provider`
**Variables Used:** `names`
**Implementation:**
```python
def getProviderDisplayName(provider: str):
    names = {'openrouter': 'OpenRouter', 'openai': 'OpenAI', 'anthropic': 'Anthropic', 'google': 'Google', 'vibeproxy': 'VibeProxy'}
    return names.get(provider.lower(), provider)
```

---

## Feature Function: `get_stats`
**Logic & Purpose:**
```text
Get proxy statistics
```

**Parameters:** ``
**Variables Used:** `cursor, recent, summary`
**Implementation:**
```python
@router.get('/api/stats')
async def get_stats():
    """Get proxy statistics"""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if usage_tracker.enabled:
            summary = usage_tracker.get_cost_summary(days=1)
            recent = []
            with usage_tracker.get_connection() as conn:
                cursor = conn.execute('\n                    SELECT original_model, input_tokens + output_tokens as total_tokens,\n                           duration_ms, estimated_cost, timestamp, status\n                    FROM api_requests\n                    ORDER BY timestamp DESC\n                    LIMIT 10\n                ')
                for row in cursor:
                    recent.append({'model': row[0], 'tokens': row[1], 'duration': int(row[2]), 'cost': f'{row[3]:.4f}', 'timestamp': row[4], 'status': row[5]})
            return {'requests_today': summary.get('total_requests', 0), 'total_tokens': summary.get('total_tokens', 0), 'est_cost': summary.get('total_cost', 0), 'avg_latency': int(summary.get('avg_duration_ms', 0)), 'recent_requests': recent, 'cascade': get_cascade_stats(limit=10)}
        else:
            return {'requests_today': 0, 'total_tokens': 0, 'est_cost': 0, 'avg_latency': 0, 'recent_requests': [], 'cascade': get_cascade_stats(limit=10)}
    except Exception as e:
        logger.error(f'Failed to get stats: {e}')
        return {'requests_today': 0, 'total_tokens': 0, 'est_cost': 0, 'avg_latency': 0, 'recent_requests': [], 'cascade': get_cascade_stats(limit=10)}
```

---

## Feature Function: `get_recent_requests`
**Logic & Purpose:**
```text
Get recent requests list for dashboard
```

**Parameters:** ``
**Variables Used:** `cursor, recent`
**Implementation:**
```python
@router.get('/api/stats/requests')
async def get_recent_requests():
    """Get recent requests list for dashboard"""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return []
        recent = []
        with usage_tracker.get_connection() as conn:
            cursor = conn.execute('\n                SELECT original_model, input_tokens + output_tokens as total_tokens,\n                       duration_ms, estimated_cost, timestamp, status, endpoint, request_id\n                FROM api_requests\n                ORDER BY timestamp DESC\n                LIMIT 50\n            ')
            for row in cursor:
                recent.append({'model': row[0], 'tokens': row[1], 'duration': int(row[2]), 'cost': f'{row[3]:.4f}', 'timestamp': row[4], 'status': row[5], 'endpoint': row[6], 'id': row[7]})
        return recent
    except Exception as e:
        logger.error(f'Failed to get recent requests: {e}')
        return []
```

---

## Feature Function: `get_dashboard_analytics`
**Logic & Purpose:**
```text
Get comprehensive analytics data for dashboard visualization.

Returns:
    - Summary metrics
    - Time series data (tokens, cost, requests over time)
    - Model comparison stats
    - Savings achieved through routing
    - Token breakdown (prompt/ completion/ reasoning)
    - Provider statistics
```

**Parameters:** `days`
**Variables Used:** `enriched_data, enriched_path, model_metadata, data`
**Implementation:**
```python
@router.get('/api/analytics/dashboard')
async def get_dashboard_analytics(days: int=7):
    """
    Get comprehensive analytics data for dashboard visualization.

    Returns:
        - Summary metrics
        - Time series data (tokens, cost, requests over time)
        - Model comparison stats
        - Savings achieved through routing
        - Token breakdown (prompt/ completion/ reasoning)
        - Provider statistics
    """
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return {'enabled': False, 'message': 'Usage tracking is disabled. Set TRACK_USAGE=true to enable.', 'data': {}}
        data = usage_tracker.get_dashboard_summary(days)
        try:
            from src.services.models.openrouter_enricher import enrich_model
            import json
            from pathlib import Path
            enriched_path = Path(__file__).parent.parent.parent / 'data' / 'openrouter_models_enriched.json'
            if enriched_path.exists():
                with open(enriched_path, 'r') as f:
                    enriched_data = json.load(f)
                    model_metadata = {}
                    for model in enriched_data.get('models', []):
                        model_metadata[model['id']] = {'name': model.get('name'), 'provider': model.get('provider'), 'pricing': model.get('pricing'), 'capabilities': {'tools': model.get('supports_tools', False), 'vision': model.get('supports_vision', False), 'reasoning': model.get('supports_reasoning', False), 'audio': model.get('supports_audio', False)}, 'context_length': model.get('context_length', 0)}
                    data['model_metadata'] = model_metadata
        except Exception:
            pass
        return {'enabled': True, 'days': days, 'data': data}
    except Exception as e:
        logger.error(f'Failed to get dashboard analytics: {e}')
        return {'enabled': False, 'error': str(e), 'data': {}}
```

---

## Feature Function: `get_time_series_analytics`
**Logic & Purpose:**
```text
Get time-series data for line charts.
```

**Parameters:** `days`
**Implementation:**
```python
@router.get('/api/analytics/time-series')
async def get_time_series_analytics(days: int=14):
    """Get time-series data for line charts."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return {'dates': [], 'tokens': [], 'cost': [], 'requests': []}
        return usage_tracker.get_time_series_data(days)
    except Exception as e:
        logger.error(f'Failed to get time series: {e}')
        return {'dates': [], 'tokens': [], 'cost': [], 'requests': []}
```

---

## Feature Function: `get_model_comparison_analytics`
**Logic & Purpose:**
```text
Get comparative data for different models.
```

**Parameters:** `days`
**Implementation:**
```python
@router.get('/api/analytics/model-comparison')
async def get_model_comparison_analytics(days: int=14):
    """Get comparative data for different models."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return []
        return usage_tracker.get_model_comparison(days)
    except Exception as e:
        logger.error(f'Failed to get model comparison: {e}')
        return []
```

---

## Feature Function: `get_savings_analytics`
**Logic & Purpose:**
```text
Get savings achieved through smart routing.
```

**Parameters:** `days`
**Implementation:**
```python
@router.get('/api/analytics/savings')
async def get_savings_analytics(days: int=14):
    """Get savings achieved through smart routing."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return []
        return usage_tracker.get_savings_data(days)
    except Exception as e:
        logger.error(f'Failed to get savings data: {e}')
        return []
```

---

## Feature Function: `get_token_breakdown_analytics`
**Logic & Purpose:**
```text
Get detailed token breakdown statistics.
```

**Parameters:** `days`
**Implementation:**
```python
@router.get('/api/analytics/token-breakdown')
async def get_token_breakdown_analytics(days: int=14):
    """Get detailed token breakdown statistics."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return {}
        return usage_tracker.get_token_breakdown_stats(days)
    except Exception as e:
        logger.error(f'Failed to get token breakdown: {e}')
        return {}
```

---

## Feature Function: `get_provider_analytics`
**Logic & Purpose:**
```text
Get provider-level statistics.
```

**Parameters:** `days`
**Implementation:**
```python
@router.get('/api/analytics/providers')
async def get_provider_analytics(days: int=14):
    """Get provider-level statistics."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        if not usage_tracker.enabled:
            return []
        return usage_tracker.get_provider_stats(days)
    except Exception as e:
        logger.error(f'Failed to get provider stats: {e}')
        return []
```

---

## Feature Function: `export_analytics`
**Logic & Purpose:**
```text
Export usage data to JSON or CSV format.
```

**Parameters:** `format, days`
**Variables Used:** `success, suffix, content`
**Implementation:**
```python
@router.get('/api/analytics/export')
async def export_analytics(format: str='json', days: int=30):
    """Export usage data to JSON or CSV format."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        import tempfile
        import os
        if not usage_tracker.enabled:
            return {'success': False, 'error': 'Usage tracking disabled'}
        suffix = '.json' if format == 'json' else '.csv'
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            if format == 'json':
                success = usage_tracker.export_to_json(path, days)
            else:
                success = usage_tracker.export_to_csv(path, days)
            if success:
                with open(path, 'r') as f:
                    content = f.read()
                os.unlink(path)
                return {'success': True, 'format': format, 'content': content, 'message': f'Exported {days} days of data in {format.upper()} format'}
            else:
                os.unlink(path)
                return {'success': False, 'error': 'Export failed'}
        except Exception as e:
            if os.path.exists(path):
                os.unlink(path)
            raise e
    except Exception as e:
        logger.error(f'Failed to export analytics: {e}')
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `refresh_model_metadata`
**Logic & Purpose:**
```text
Manually refresh the OpenRouter model metadata cache.
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/analytics/refresh-models')
async def refresh_model_metadata():
    """Manually refresh the OpenRouter model metadata cache."""
    try:
        from src.services.models.openrouter_fetcher import fetch_and_cache_models
        import asyncio
        result = await fetch_and_cache_models()
        return {'success': True, 'models_fetched': len(result.get('models', [])), 'message': 'Model metadata refreshed successfully'}
    except Exception as e:
        logger.error(f'Failed to refresh models: {e}')
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `get_analytics_health`
**Logic & Purpose:**
```text
Check if analytics data is being collected properly.
```

**Parameters:** ``
**Variables Used:** `cursor, breakdown_count, daily_count, savings_count, api_count, conn`
**Implementation:**
```python
@router.get('/api/analytics/health')
async def get_analytics_health():
    """Check if analytics data is being collected properly."""
    try:
        from src.services.usage.usage_tracker import usage_tracker
        import sqlite3
        if not usage_tracker.enabled:
            return {'enabled': False, 'message': 'Usage tracking disabled', 'data_available': False}
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM api_requests')
        api_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM daily_model_stats')
        daily_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM savings_tracking')
        savings_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM token_breakdown')
        breakdown_count = cursor.fetchone()[0]
        conn.close()
        return {'enabled': True, 'data_available': api_count > 0, 'tables': {'api_requests': api_count, 'daily_model_stats': daily_count, 'savings_tracking': savings_count, 'token_breakdown': breakdown_count}, 'health': 'healthy' if api_count > 0 else 'no_data'}
    except Exception as e:
        logger.error(f'Analytics health check failed: {e}')
        return {'enabled': False, 'error': str(e), 'health': 'error'}
```

---

## Feature Function: `test_provider_connection`
**Logic & Purpose:**
```text
Test connection to the configured provider
```

**Parameters:** ``
**Variables Used:** `provider_url, provider_key, response`
**Implementation:**
```python
@router.post('/api/test-connection')
async def test_provider_connection():
    """Test connection to the configured provider"""
    try:
        provider_url = os.getenv('PROVIDER_BASE_URL') or config.openai_base_url
        provider_key = os.getenv('PROVIDER_API_KEY') or config.openai_api_key
        if not provider_url or not provider_key:
            return {'success': False, 'error': 'Provider URL or API key not configured'}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{provider_url.rstrip('/')}/models", headers={'Authorization': f'Bearer {provider_key}'})
            if response.status_code == 200:
                return {'success': True, 'message': 'Connection successful', 'provider': provider_url}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key (401 Unauthorized)'}
            elif response.status_code == 403:
                return {'success': False, 'error': 'API key valid but insufficient permissions (403 Forbidden)'}
            else:
                return {'success': False, 'error': f'Unexpected response: {response.status_code}'}
    except httpx.TimeoutException:
        return {'success': False, 'error': 'Connection timeout - provider may be slow or unreachable'}
    except httpx.ConnectError:
        return {'success': False, 'error': 'Cannot connect to provider - check URL'}
    except Exception as e:
        logger.error(f'Connection test failed: {e}')
        return {'success': False, 'error': str(e)}
```

---

## Feature Function: `list_crosstalk_presets`
**Logic & Purpose:**
```text
List available Crosstalk presets
```

**Parameters:** ``
**Variables Used:** `preset_data, presets`
**Implementation:**
```python
@router.get('/api/crosstalk/presets')
async def list_crosstalk_presets():
    """List available Crosstalk presets"""
    try:
        presets = []
        if CROSSTALK_PRESETS_DIR.exists():
            for preset_file in CROSSTALK_PRESETS_DIR.glob('*.json'):
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                    presets.append({'filename': preset_file.stem, 'name': preset_data.get('name', preset_file.stem), 'description': preset_data.get('description', ''), 'models': len(preset_data.get('models', [])), 'topology': preset_data.get('topology', {}).get('type', 'ring')})
        return presets
    except Exception as e:
        logger.error(f'Failed to list presets: {e}')
        return []
```

---

## Feature Function: `get_crosstalk_preset`
**Logic & Purpose:**
```text
Get a specific Crosstalk preset
```

**Parameters:** `preset_name`
**Variables Used:** `preset_file, safe_name`
**Implementation:**
```python
@router.get('/api/crosstalk/presets/{preset_name}')
async def get_crosstalk_preset(preset_name: str):
    """Get a specific Crosstalk preset"""
    try:
        safe_name = validate_safe_filename(preset_name)
        preset_file = CROSSTALK_PRESETS_DIR / f'{safe_name}.json'
        if not preset_file.exists():
            raise HTTPException(status_code=404, detail='Preset not found')
        with open(preset_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Preset not found')
    except Exception as e:
        logger.error(f'Failed to load preset: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Class: `CrosstalkSessionCreate`
**Description:**
```text
Crosstalk session configuration
```

---

## Feature Function: `save_crosstalk_preset`
**Logic & Purpose:**
```text
Save a Crosstalk preset
```

**Parameters:** `preset`
**Variables Used:** `preset_data, preset_file, name, safe_name`
**Implementation:**
```python
@router.post('/api/crosstalk/presets')
async def save_crosstalk_preset(preset: CrosstalkSessionCreate):
    """Save a Crosstalk preset"""
    try:
        CROSSTALK_PRESETS_DIR.mkdir(parents=True, exist_ok=True)
        name = preset.name or f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        safe_name = validate_safe_filename(name)
        preset_file = CROSSTALK_PRESETS_DIR / f'{safe_name}.json'
        preset_data = {'name': name, 'models': preset.models, 'topology': preset.topology, 'paradigm': preset.paradigm, 'rounds': preset.rounds, 'infinite': preset.infinite, 'stop_conditions': preset.stop_conditions, 'summarize_every': preset.summarize_every, 'initial_prompt': preset.initial_prompt}
        with open(preset_file, 'w') as f:
            json.dump(preset_data, f, indent=2)
        return {'status': 'success', 'filename': name}
    except Exception as e:
        logger.error(f'Failed to save preset: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `list_crosstalk_sessions`
**Logic & Purpose:**
```text
List recent Crosstalk sessions
```

**Parameters:** ``
**Variables Used:** `session_data, sessions`
**Implementation:**
```python
@router.get('/api/crosstalk/sessions')
async def list_crosstalk_sessions():
    """List recent Crosstalk sessions"""
    try:
        sessions = []
        if CROSSTALK_SESSIONS_DIR.exists():
            for session_file in sorted(CROSSTALK_SESSIONS_DIR.glob('*.json'), reverse=True)[:20]:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    sessions.append({'filename': session_file.stem, 'started_at': session_data.get('started_at', ''), 'ended_at': session_data.get('ended_at', ''), 'messages': len(session_data.get('messages', [])), 'paradigm': session_data.get('config', {}).get('paradigm', 'relay')})
        return sessions
    except Exception as e:
        logger.error(f'Failed to list sessions: {e}')
        return []
```

---

## Feature Function: `get_crosstalk_session`
**Logic & Purpose:**
```text
Get a specific Crosstalk session transcript
```

**Parameters:** `session_name`
**Variables Used:** `session_file, safe_name`
**Implementation:**
```python
@router.get('/api/crosstalk/sessions/{session_name}')
async def get_crosstalk_session(session_name: str):
    """Get a specific Crosstalk session transcript"""
    try:
        safe_name = validate_safe_filename(session_name)
        session_file = CROSSTALK_SESSIONS_DIR / f'{safe_name}.json'
        if not session_file.exists():
            raise HTTPException(status_code=404, detail='Session not found')
        with open(session_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Session not found')
    except Exception as e:
        logger.error(f'Failed to load session: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Class: `CrosstalkRunRequest`
**Description:**
```text
Request to run a crosstalk session
```

---

## Feature Function: `run_crosstalk_session`
**Logic & Purpose:**
```text
Run a Crosstalk session from the web UI
```

**Parameters:** `request`
**Variables Used:** `session_config, session_file, session_id`
**Implementation:**
```python
@router.post('/api/crosstalk/run')
async def run_crosstalk_session(request: CrosstalkRunRequest):
    """Run a Crosstalk session from the web UI"""
    import asyncio
    from datetime import datetime
    try:
        if not request.initial_prompt:
            raise HTTPException(status_code=400, detail='Initial prompt is required')
        if len(request.models) < 2:
            raise HTTPException(status_code=400, detail='At least 2 models required')
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_config = {'session_id': session_id, 'models': request.models, 'topology': request.topology, 'paradigm': request.paradigm, 'rounds': request.rounds, 'infinite': request.infinite, 'stop_conditions': request.stop_conditions, 'initial_prompt': request.initial_prompt, 'messages': []}
        CROSSTALK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        session_file = CROSSTALK_SESSIONS_DIR / f'{session_id}.json'
        with open(session_file, 'w') as f:
            json.dump(session_config, f, indent=2)
        return {'status': 'created', 'session_id': session_id, 'message': 'Session created. Use CLI for full execution: python start_proxy.py --crosstalk-studio', 'config': session_config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to run crosstalk session: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `health_check`
**Logic & Purpose:**
```text
Health check endpoint for auto-wizard
```

**Parameters:** ``
**Variables Used:** `provider_url, provider_key`
**Implementation:**
```python
@router.get('/api/health')
async def health_check():
    """Health check endpoint for auto-wizard"""
    provider_url = os.getenv('PROVIDER_BASE_URL') or config.openai_base_url
    provider_key = os.getenv('PROVIDER_API_KEY') or config.openai_api_key
    return {'status': 'ok', 'provider_configured': bool(provider_key), 'provider_url': provider_url, 'cascade_enabled': getattr(config, 'model_cascade', False), 'big_model': config.big_model, 'middle_model': config.middle_model, 'small_model': config.small_model}
```

---

## Feature Class: `PlaygroundRequest`
**Description:**
```text
Model playground request
```

---

## Feature Function: `run_playground`
**Logic & Purpose:**
```text
Run a test prompt through the proxy.

Returns the model response with token counts and latency.
```

**Parameters:** `request`
**Variables Used:** `api_key, data, base_url, start_time, latency_ms, usage, messages, response, model_map, content, model`
**Implementation:**
```python
@router.post('/api/playground/run')
async def run_playground(request: PlaygroundRequest):
    """
    Run a test prompt through the proxy.

    Returns the model response with token counts and latency.
    """
    import time
    model_map = {'big': config.big_model, 'middle': config.middle_model, 'small': config.small_model}
    model = model_map.get(request.model_tier, config.big_model)
    if not model:
        raise HTTPException(status_code=400, detail=f'No model configured for tier: {request.model_tier}')
    api_key = os.getenv('PROVIDER_API_KEY') or os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(status_code=400, detail='No API key configured')
    messages = []
    if request.system_prompt:
        messages.append({'role': 'system', 'content': request.system_prompt})
    messages.append({'role': 'user', 'content': request.user_message})
    base_url = config.openai_base_url or 'https://openrouter.ai/api/v1'
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f'{base_url}/chat/completions', headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}, json={'model': model, 'messages': messages, 'temperature': request.temperature, 'max_tokens': request.max_tokens})
            latency_ms = int((time.time() - start_time) * 1000)
            if response.status_code != 200:
                return {'success': False, 'error': f'API error: {response.status_code}', 'latency_ms': latency_ms}
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = data.get('usage', {})
            return {'success': True, 'content': content, 'model': model, 'input_tokens': usage.get('prompt_tokens', 0), 'output_tokens': usage.get('completion_tokens', 0), 'latency_ms': latency_ms}
    except Exception as e:
        logger.error(f'Playground error: {e}')
        return {'success': False, 'error': str(e), 'latency_ms': int((time.time() - start_time) * 1000)}
```

---


