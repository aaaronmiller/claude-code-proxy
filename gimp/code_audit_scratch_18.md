# File Audit: /home/cheta/code/claude-code-proxy/src/api/users.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/users.py`

**Module Overview**: 
```text
User Management API Endpoints

Provides user and API key management for multi-user deployments.
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Header, fastapi.Depends, typing.Optional, pydantic.BaseModel, pydantic.EmailStr, src.auth.user_manager.user_manager, src.core.logging.logger

## Feature Class: `UserCreate`
---

## Feature Class: `QuotaUpdate`
---

## Feature Function: `create_user`
**Logic & Purpose:**
```text
Create a new user with API key.

Returns user details including API key (only shown once!).
```

**Parameters:** `user`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/users')
async def create_user(user: UserCreate):
    """
    Create a new user with API key.

    Returns user details including API key (only shown once!).
    """
    try:
        result = user_manager.create_user(username=user.username, email=user.email, role=user.role, quota_requests=user.quota_requests, quota_tokens=user.quota_tokens, quota_cost=user.quota_cost)
        return {'status': 'success', 'user': result, 'warning': "Save the API key securely - it won't be shown again!"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'Failed to create user: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_current_user`
**Logic & Purpose:**
```text
Get current user info based on API key.
```

**Parameters:** `x_api_key, authorization`
**Variables Used:** `user_info, user, api_key`
**Implementation:**
```python
@router.get('/api/users/me')
async def get_current_user(x_api_key: Optional[str]=Header(None), authorization: Optional[str]=Header(None)):
    """
    Get current user info based on API key.
    """
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith('Bearer '):
            api_key = authorization[7:]
    if not api_key:
        raise HTTPException(status_code=401, detail='API key required')
    user = user_manager.validate_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid API key')
    user_info = {'user_id': user['id'], 'username': user['username'], 'email': user['email'], 'role': user['role'], 'active': user['active'], 'created_at': user['created_at']}
    return user_info
```

---

## Feature Function: `get_user_quota`
**Logic & Purpose:**
```text
Get current user's quota status.

Returns remaining quota for requests, tokens, and cost.
```

**Parameters:** `x_api_key, authorization`
**Variables Used:** `user, quota_status, api_key`
**Implementation:**
```python
@router.get('/api/users/me/quota')
async def get_user_quota(x_api_key: Optional[str]=Header(None), authorization: Optional[str]=Header(None)):
    """
    Get current user's quota status.

    Returns remaining quota for requests, tokens, and cost.
    """
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith('Bearer '):
            api_key = authorization[7:]
    if not api_key:
        raise HTTPException(status_code=401, detail='API key required')
    user = user_manager.validate_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid API key')
    quota_status = user_manager.check_user_quota(user['id'])
    if 'error' in quota_status:
        raise HTTPException(status_code=500, detail=quota_status['error'])
    return quota_status
```

---

## Feature Function: `get_user_usage`
**Logic & Purpose:**
```text
Get user's usage history.

Returns daily usage stats for the specified period.
```

**Parameters:** `days, x_api_key, authorization`
**Variables Used:** `usage_data, cursor, api_key, rows, since, user, conn`
**Implementation:**
```python
@router.get('/api/users/me/usage')
async def get_user_usage(days: int=7, x_api_key: Optional[str]=Header(None), authorization: Optional[str]=Header(None)):
    """
    Get user's usage history.

    Returns daily usage stats for the specified period.
    """
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith('Bearer '):
            api_key = authorization[7:]
    if not api_key:
        raise HTTPException(status_code=401, detail='API key required')
    user = user_manager.validate_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid API key')
    try:
        import sqlite3
        from datetime import datetime, timedelta
        conn = sqlite3.connect(user_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        cursor.execute('\n            SELECT date, request_count, token_count, cost\n            FROM user_usage\n            WHERE user_id = ? AND date >= ?\n            ORDER BY date DESC\n        ', (user['id'], since))
        rows = cursor.fetchall()
        conn.close()
        usage_data = [dict(row) for row in rows]
        return {'user_id': user['id'], 'username': user['username'], 'period_days': days, 'usage': usage_data}
    except Exception as e:
        logger.error(f'Failed to get user usage: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/dashboards.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/dashboards.py`

**Module Overview**: 
```text
Custom Dashboard Builder API - Phase 4

Endpoints for creating, saving, and managing custom dashboards

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, typing.Dict, typing.Any, typing.List, typing.Optional, sqlite3, json, datetime.datetime, uuid, src.utils.json_utils.safe_json_loads, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Function: `save_dashboard`
**Logic & Purpose:**
```text
Save a custom dashboard
```

**Parameters:** `dashboard`
**Variables Used:** `cursor, created_at, widgets, exists, config, dashboard_id, conn, name, updated_at`
**Implementation:**
```python
@router.post('/api/dashboards')
async def save_dashboard(dashboard: Dict[str, Any]):
    """Save a custom dashboard"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.execute("\n            CREATE TABLE IF NOT EXISTS custom_dashboards (\n                id TEXT PRIMARY KEY,\n                name TEXT NOT NULL,\n                widgets TEXT NOT NULL,\n                config TEXT,\n                created_at TEXT NOT NULL,\n                updated_at TEXT NOT NULL,\n                owner TEXT DEFAULT 'default'\n            )\n        ")
        dashboard_id = dashboard.get('id') or str(uuid.uuid4())
        name = dashboard.get('name', 'Untitled Dashboard')
        widgets = json.dumps(dashboard.get('widgets', []))
        config = json.dumps(dashboard.get('config', {}))
        created_at = dashboard.get('created_at', datetime.now().isoformat())
        updated_at = datetime.now().isoformat()
        cursor = conn.execute('SELECT id FROM custom_dashboards WHERE id = ?', (dashboard_id,))
        exists = cursor.fetchone() is not None
        if exists:
            conn.execute('\n                UPDATE custom_dashboards\n                SET name = ?, widgets = ?, config = ?, updated_at = ?\n                WHERE id = ?\n            ', (name, widgets, config, updated_at, dashboard_id))
        else:
            conn.execute('\n                INSERT INTO custom_dashboards (id, name, widgets, config, created_at, updated_at, owner)\n                VALUES (?, ?, ?, ?, ?, ?, ?)\n            ', (dashboard_id, name, widgets, config, created_at, updated_at, 'default'))
        conn.commit()
        conn.close()
        return {'success': True, 'id': dashboard_id, 'name': name, 'status': 'updated' if exists else 'created'}
    except Exception as e:
        logger.error(f'Save dashboard failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_dashboards`
**Logic & Purpose:**
```text
Get all custom dashboards
```

**Parameters:** ``
**Variables Used:** `rows, conn, dashboards, cursor`
**Implementation:**
```python
@router.get('/api/dashboards')
async def get_dashboards():
    """Get all custom dashboards"""
    try:
        if not usage_tracker.enabled:
            return {'dashboards': []}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute('\n                SELECT id, name, widgets, config, created_at, updated_at, owner\n                FROM custom_dashboards\n                ORDER BY updated_at DESC\n            ')
        except sqlite3.OperationalError:
            conn.close()
            return {'dashboards': []}
        rows = cursor.fetchall()
        conn.close()
        dashboards = []
        for row in rows:
            dashboards.append({'id': row['id'], 'name': row['name'], 'widgets': safe_json_loads(row['widgets'], default=[]), 'config': safe_json_loads(row['config'], default={}), 'created_at': row['created_at'], 'updated_at': row['updated_at'], 'owner': row['owner']})
        return {'dashboards': dashboards, 'count': len(dashboards)}
    except Exception as e:
        logger.error(f'Get dashboards failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_dashboard`
**Logic & Purpose:**
```text
Get a specific dashboard
```

**Parameters:** `dashboard_id`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
@router.get('/api/dashboards/{dashboard_id}')
async def get_dashboard(dashboard_id: str):
    """Get a specific dashboard"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('\n            SELECT id, name, widgets, config, created_at, updated_at, owner\n            FROM custom_dashboards\n            WHERE id = ?\n        ', (dashboard_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail='Dashboard not found')
        return {'id': row['id'], 'name': row['name'], 'widgets': safe_json_loads(row['widgets'], default=[]), 'config': safe_json_loads(row['config'], default={}), 'created_at': row['created_at'], 'updated_at': row['updated_at'], 'owner': row['owner']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Get dashboard failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `delete_dashboard`
**Logic & Purpose:**
```text
Delete a dashboard
```

**Parameters:** `dashboard_id`
**Variables Used:** `conn, cursor, deleted`
**Implementation:**
```python
@router.delete('/api/dashboards/{dashboard_id}')
async def delete_dashboard(dashboard_id: str):
    """Delete a dashboard"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('DELETE FROM custom_dashboards WHERE id = ?', (dashboard_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='Dashboard not found')
        return {'success': True, 'id': dashboard_id, 'status': 'deleted'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Delete dashboard failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `duplicate_dashboard`
**Logic & Purpose:**
```text
Duplicate a dashboard
```

**Parameters:** `dashboard_id`
**Variables Used:** `cursor, created_at, new_name, new_id, conn, row`
**Implementation:**
```python
@router.post('/api/dashboards/{dashboard_id}/duplicate')
async def duplicate_dashboard(dashboard_id: str):
    """Duplicate a dashboard"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM custom_dashboards WHERE id = ?', (dashboard_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail='Dashboard not found')
        new_id = str(uuid.uuid4())
        new_name = f"{row['name']} (Copy)"
        created_at = datetime.now().isoformat()
        conn.execute('\n            INSERT INTO custom_dashboards (id, name, widgets, config, created_at, updated_at, owner)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n        ', (new_id, new_name, row['widgets'], row['config'], created_at, created_at, row['owner']))
        conn.commit()
        conn.close()
        return {'success': True, 'id': new_id, 'name': new_name, 'original_id': dashboard_id}
    except Exception as e:
        logger.error(f'Duplicate dashboard failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_dashboard_data`
**Logic & Purpose:**
```text
Get data for a dashboard's widgets
```

**Parameters:** `dashboard_id`
**Variables Used:** `now, cursor, data, results, dashboard, widget_id, metric, aggregate, period, select, start_date, query, conn, metric_map`
**Implementation:**
```python
@router.get('/api/dashboards/{dashboard_id}/data')
async def get_dashboard_data(dashboard_id: str):
    """Get data for a dashboard's widgets"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        dashboard = await get_dashboard(dashboard_id)
        if 'error' in dashboard:
            return dashboard
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        results = {}
        for widget in dashboard.get('widgets', []):
            widget_id = widget['id']
            metric = widget['config']['metric']
            period = widget['config']['period']
            aggregate = widget['config']['aggregate']
            from datetime import timedelta
            now = datetime.now()
            if period == '24h':
                start_date = now - timedelta(hours=24)
            elif period == '7d':
                start_date = now - timedelta(days=7)
            elif period == '30d':
                start_date = now - timedelta(days=30)
            elif period == '90d':
                start_date = now - timedelta(days=90)
            else:
                start_date = now - timedelta(days=7)
            metric_map = {'tokens': 'SUM(total_tokens)', 'cost': 'SUM(estimated_cost)', 'requests': 'COUNT(*)', 'latency': 'AVG(duration_ms)', 'error_rate': "AVG(CASE WHEN status = 'error' THEN 100 ELSE 0 END)", 'efficiency': 'CASE WHEN SUM(estimated_cost) > 0 THEN SUM(total_tokens) / SUM(estimated_cost) ELSE 0 END'}
            select = metric_map.get(metric, 'COUNT(*)')
            if widget['type'] == 'chart':
                query = f'\n                    SELECT\n                        date(timestamp) as date,\n                        {select} as value\n                    FROM api_requests\n                    WHERE timestamp >= ?\n                    GROUP BY date(timestamp)\n                    ORDER BY date(timestamp)\n                '
            else:
                query = f'\n                    SELECT {select} as value\n                    FROM api_requests\n                    WHERE timestamp >= ?\n                '
            cursor = conn.execute(query, [start_date.isoformat()])
            data = cursor.fetchall()
            if widget['type'] == 'chart':
                results[widget_id] = [{'date': row['date'], 'value': row['value'] or 0} for row in data]
            else:
                results[widget_id] = {'value': data[0]['value'] if data else 0}
        conn.close()
        return {'dashboard_id': dashboard_id, 'data': results, 'generated_at': datetime.now().isoformat()}
    except Exception as e:
        logger.error(f'Get dashboard data failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `export_dashboard`
**Logic & Purpose:**
```text
Export dashboard as JSON file
```

**Parameters:** `dashboard_id`
**Variables Used:** `dashboard`
**Implementation:**
```python
@router.get('/api/dashboards/{dashboard_id}/export')
async def export_dashboard(dashboard_id: str):
    """Export dashboard as JSON file"""
    try:
        dashboard = await get_dashboard(dashboard_id)
        return dashboard
    except Exception as e:
        logger.error(f'Export dashboard failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `dashboards_health`
**Logic & Purpose:**
```text
Health check for dashboards service
```

**Parameters:** ``
**Variables Used:** `count, conn, cursor`
**Implementation:**
```python
@router.get('/api/dashboards/health')
async def dashboards_health():
    """Health check for dashboards service"""
    try:
        if not usage_tracker.enabled:
            return {'status': 'disabled', 'enabled': False}
        conn = sqlite3.connect(usage_tracker.db_path)
        try:
            cursor = conn.execute('SELECT COUNT(*) as count FROM custom_dashboards')
            count = cursor.fetchone()[0]
            conn.close()
            return {'status': 'healthy', 'enabled': True, 'dashboards_count': count}
        except sqlite3.OperationalError:
            conn.close()
            return {'status': 'healthy', 'enabled': True, 'dashboards_count': 0}
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return {'status': 'error', 'error': str(e)}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/alerts.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/alerts.py`

**Module Overview**: 
```text
Alert Management API - Phase 3

Provides endpoints for:
- Creating, updating, deleting alert rules
- Managing alert history
- Bulk operations on alerts
- Alert statistics

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, typing.List, typing.Dict, typing.Any, typing.Optional, datetime.datetime, sqlite3, json, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker, src.services.alert_engine.alert_engine, src.utils.json_utils.safe_json_loads

## Feature Function: `create_alert_rule`
**Logic & Purpose:**
```text
Create a new alert rule
```

**Parameters:** `rule_data`
**Variables Used:** `conn, cursor, rule_id`
**Implementation:**
```python
@router.post('/api/alerts/rules')
async def create_alert_rule(rule_data: Dict[str, Any]):
    """Create a new alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        rule_id = f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor = conn.execute('\n            INSERT INTO alert_rules (\n                id, name, description, condition_json, condition_logic,\n                actions_json, cooldown_minutes, priority, time_window,\n                is_active, created_at, created_by, trigger_count\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (rule_id, rule_data.get('name', 'Unnamed Rule'), rule_data.get('description', ''), json.dumps(rule_data.get('conditions', [])), json.dumps(rule_data.get('logic', None)), json.dumps(rule_data.get('actions', {'channels': ['in_app']})), rule_data.get('cooldown_minutes', 5), rule_data.get('priority', 2), rule_data.get('time_window', 5), 1, datetime.utcnow().isoformat(), rule_data.get('created_by', 'web_ui'), 0))
        conn.commit()
        conn.close()
        return {'success': True, 'rule_id': rule_id, 'message': 'Rule created successfully'}
    except Exception as e:
        logger.error(f'Create alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_alert_rules`
**Logic & Purpose:**
```text
Get all alert rules
```

**Parameters:** `include_inactive`
**Variables Used:** `cursor, rows, rules, rule, query, conn`
**Implementation:**
```python
@router.get('/api/alerts/rules')
async def get_alert_rules(include_inactive: bool=False):
    """Get all alert rules"""
    try:
        if not usage_tracker.enabled:
            return {'rules': []}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        query = 'SELECT * FROM alert_rules'
        if not include_inactive:
            query += ' WHERE is_active = 1'
        query += ' ORDER BY priority ASC, created_at DESC'
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()
        rules = []
        for row in rows:
            rule = dict(row)
            rule['conditions'] = safe_json_loads(rule.get('condition_json', '[]'), default=[])
            rule['logic'] = safe_json_loads(rule.get('condition_logic', 'null'), default=None)
            rule['actions'] = safe_json_loads(rule.get('actions_json', '{}'), default={})
            rules.append(rule)
        return {'rules': rules, 'count': len(rules)}
    except Exception as e:
        logger.error(f'Get alert rules failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_alert_rule`
**Logic & Purpose:**
```text
Get specific alert rule
```

**Parameters:** `rule_id`
**Variables Used:** `conn, cursor, rule, row`
**Implementation:**
```python
@router.get('/api/alerts/rules/{rule_id}')
async def get_alert_rule(rule_id: str):
    """Get specific alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM alert_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail='Rule not found')
        rule = dict(row)
        rule['conditions'] = safe_json_loads(rule.get('condition_json', '[]'), default=[])
        rule['logic'] = safe_json_loads(rule.get('condition_logic', 'null'), default=None)
        rule['actions'] = safe_json_loads(rule.get('actions_json', '{}'), default={})
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Get alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `update_alert_rule`
**Logic & Purpose:**
```text
Update alert rule
```

**Parameters:** `rule_id, rule_data`
**Variables Used:** `cursor, params, updates, query, conn`
**Implementation:**
```python
@router.put('/api/alerts/rules/{rule_id}')
async def update_alert_rule(rule_id: str, rule_data: Dict[str, Any]):
    """Update alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('SELECT id FROM alert_rules WHERE id = ?', (rule_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail='Rule not found')
        updates = []
        params = []
        if 'name' in rule_data:
            updates.append('name = ?')
            params.append(rule_data['name'])
        if 'description' in rule_data:
            updates.append('description = ?')
            params.append(rule_data['description'])
        if 'conditions' in rule_data:
            updates.append('condition_json = ?')
            params.append(json.dumps(rule_data['conditions']))
        if 'logic' in rule_data:
            updates.append('condition_logic = ?')
            params.append(json.dumps(rule_data['logic']))
        if 'actions' in rule_data:
            updates.append('actions_json = ?')
            params.append(json.dumps(rule_data['actions']))
        if 'cooldown_minutes' in rule_data:
            updates.append('cooldown_minutes = ?')
            params.append(rule_data['cooldown_minutes'])
        if 'priority' in rule_data:
            updates.append('priority = ?')
            params.append(rule_data['priority'])
        if 'time_window' in rule_data:
            updates.append('time_window = ?')
            params.append(rule_data['time_window'])
        if not updates:
            conn.close()
            return {'success': False, 'message': 'No updates provided'}
        params.append(rule_id)
        query = f"UPDATE alert_rules SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return {'success': True, 'rule_id': rule_id, 'message': 'Rule updated'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Update alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `delete_alert_rule`
**Logic & Purpose:**
```text
Delete alert rule
```

**Parameters:** `rule_id`
**Variables Used:** `conn, cursor, deleted`
**Implementation:**
```python
@router.delete('/api/alerts/rules/{rule_id}')
async def delete_alert_rule(rule_id: str):
    """Delete alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('DELETE FROM alert_rules WHERE id = ?', (rule_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted == 0:
            raise HTTPException(status_code=404, detail='Rule not found')
        return {'success': True, 'rule_id': rule_id, 'message': 'Rule deleted'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Delete alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `toggle_alert_rule`
**Logic & Purpose:**
```text
Enable or disable alert rule
```

**Parameters:** `rule_id`
**Variables Used:** `new_state, conn, cursor, row`
**Implementation:**
```python
@router.post('/api/alerts/rules/{rule_id}/toggle')
async def toggle_alert_rule(rule_id: str):
    """Enable or disable alert rule"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('SELECT is_active FROM alert_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail='Rule not found')
        new_state = 1 - row[0]
        cursor.execute('UPDATE alert_rules SET is_active = ? WHERE id = ?', (new_state, rule_id))
        conn.commit()
        conn.close()
        return {'success': True, 'rule_id': rule_id, 'is_active': bool(new_state), 'message': f"Rule {('enabled' if new_state else 'disabled')}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Toggle alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `test_alert_rule`
**Logic & Purpose:**
```text
Test alert rule by simulating with current metrics
```

**Parameters:** `rule_id`
**Variables Used:** `cursor, rule, conn, metrics, row`
**Implementation:**
```python
@router.post('/api/alerts/rules/{rule_id}/test')
async def test_alert_rule(rule_id: str):
    """Test alert rule by simulating with current metrics"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM alert_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail='Rule not found')
        metrics = await alert_engine.get_current_metrics(row['time_window'])
        from src.services.alert_engine import AlertRule
        rule = AlertRule(**dict(row))
        triggered, alert_data = alert_engine.check_conditions(rule, metrics)
        return {'triggered': triggered, 'metrics': metrics, 'alert_data': alert_data, 'rule_name': rule.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Test alert rule failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_alert_history`
**Logic & Purpose:**
```text
Get alert history with filtering
```

**Parameters:** `limit, offset, severity, status, rule_id, start_date, end_date`
**Variables Used:** `cursor, params, count_cursor, alerts, rows, alert, total, query, conn, count_query`
**Implementation:**
```python
@router.get('/api/alerts/history')
async def get_alert_history(limit: int=Query(50, ge=1, le=500), offset: int=Query(0, ge=0), severity: Optional[str]=None, status: Optional[str]=None, rule_id: Optional[str]=None, start_date: Optional[str]=None, end_date: Optional[str]=None):
    """Get alert history with filtering"""
    try:
        if not usage_tracker.enabled:
            return {'alerts': [], 'count': 0}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        query = '\n            SELECT\n                h.*,\n                r.description as rule_description,\n                r.priority as rule_priority\n            FROM alert_history h\n            LEFT JOIN alert_rules r ON h.rule_id = r.id\n            WHERE 1=1\n        '
        params = []
        if severity:
            query += ' AND h.severity = ?'
            params.append(severity)
        if status == 'resolved':
            query += ' AND h.resolved = 1'
        elif status == 'unresolved':
            query += ' AND h.resolved = 0'
        if rule_id:
            query += ' AND h.rule_id = ?'
            params.append(rule_id)
        if start_date:
            query += ' AND h.triggered_at >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND h.triggered_at <= ?'
            params.append(end_date)
        query += ' ORDER BY h.triggered_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        count_query = query.replace('SELECT h.*, r.description as rule_description, r.priority as rule_priority', 'SELECT COUNT(*) as total')
        count_query = count_query.split('ORDER BY')[0]
        count_cursor = conn.execute(count_query, params[:-2])
        total = count_cursor.fetchone()['total']
        conn.close()
        alerts = []
        for row in rows:
            alert = dict(row)
            alert['alert_data'] = safe_json_loads(row.get('alert_data_json', '{}'), default={})
            alerts.append(alert)
        return {'alerts': alerts, 'count': len(alerts), 'total': total, 'pagination': {'limit': limit, 'offset': offset, 'has_more': offset + limit < total}}
    except Exception as e:
        logger.error(f'Get alert history failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_alert_detail`
**Logic & Purpose:**
```text
Get specific alert detail
```

**Parameters:** `alert_id`
**Variables Used:** `alert, conn, cursor, row`
**Implementation:**
```python
@router.get('/api/alerts/history/{alert_id}')
async def get_alert_detail(alert_id: str):
    """Get specific alert detail"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('\n            SELECT h.*, r.description as rule_description\n            FROM alert_history h\n            LEFT JOIN alert_rules r ON h.rule_id = r.id\n            WHERE h.id = ?\n        ', (alert_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail='Alert not found')
        alert = dict(row)
        alert['alert_data'] = safe_json_loads(row.get('alert_data_json', '{}'), default={})
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Get alert detail failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `acknowledge_alert`
**Logic & Purpose:**
```text
Acknowledge alert
```

**Parameters:** `alert_id`
**Variables Used:** `updated, conn, cursor`
**Implementation:**
```python
@router.post('/api/alerts/history/{alert_id}/ack')
async def acknowledge_alert(alert_id: str):
    """Acknowledge alert"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('\n            UPDATE alert_history\n            SET acknowledged = 1\n            WHERE id = ? AND acknowledged = 0\n        ', (alert_id,))
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        if updated == 0:
            raise HTTPException(status_code=404, detail='Alert not found or already acknowledged')
        return {'success': True, 'alert_id': alert_id, 'message': 'Alert acknowledged'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Acknowledge alert failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `resolve_alert`
**Logic & Purpose:**
```text
Resolve alert with optional notes
```

**Parameters:** `alert_id, notes`
**Variables Used:** `updated, conn, now, cursor`
**Implementation:**
```python
@router.post('/api/alerts/history/{alert_id}/resolve')
async def resolve_alert(alert_id: str, notes: Optional[str]=None):
    """Resolve alert with optional notes"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        now = datetime.utcnow().isoformat()
        cursor = conn.execute('\n            UPDATE alert_history\n            SET resolved = 1, acknowledged = 1, notes = ?, resolution_time = ?\n            WHERE id = ? AND resolved = 0\n        ', (notes, now, alert_id))
        updated = cursor.rowcount
        conn.commit()
        conn.close()
        if updated == 0:
            raise HTTPException(status_code=404, detail='Alert not found or already resolved')
        return {'success': True, 'alert_id': alert_id, 'resolution_time': now, 'message': 'Alert resolved'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Resolve alert failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `bulk_alert_actions`
**Logic & Purpose:**
```text
Perform bulk actions on alerts

Actions: acknowledge, resolve, delete
```

**Parameters:** `action, alert_ids, notes`
**Variables Used:** `results, conn, cursor`
**Implementation:**
```python
@router.post('/api/alerts/history/bulk')
async def bulk_alert_actions(action: str, alert_ids: List[str], notes: Optional[str]=None):
    """
    Perform bulk actions on alerts

    Actions: acknowledge, resolve, delete
    """
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        if action not in ['acknowledge', 'resolve', 'delete']:
            raise HTTPException(status_code=400, detail='Invalid action')
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()
        results = {'success': 0, 'failed': 0}
        for alert_id in alert_ids:
            try:
                if action == 'acknowledge':
                    cursor.execute('UPDATE alert_history SET acknowledged = 1 WHERE id = ? AND acknowledged = 0', (alert_id,))
                elif action == 'resolve':
                    cursor.execute('UPDATE alert_history SET resolved = 1, acknowledged = 1, notes = ?, resolution_time = ? WHERE id = ? AND resolved = 0', (notes, datetime.utcnow().isoformat(), alert_id))
                elif action == 'delete':
                    cursor.execute('DELETE FROM alert_history WHERE id = ?', (alert_id,))
                if cursor.rowcount > 0:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as _e:
                results['failed'] += 1
        conn.commit()
        conn.close()
        return {'success': True, 'action': action, 'results': results, 'message': f"Bulk {action} completed: {results['success']} succeeded, {results['failed']} failed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Bulk alert actions failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_alert_statistics`
**Logic & Purpose:**
```text
Get alert statistics
```

**Parameters:** `days`
**Variables Used:** `stats`
**Implementation:**
```python
@router.get('/api/alerts/stats')
async def get_alert_statistics(days: int=Query(30, ge=1, le=365)):
    """Get alert statistics"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        stats = alert_engine.get_alert_statistics(days)
        return stats
    except Exception as e:
        logger.error(f'Get alert stats failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_notification_channels`
**Logic & Purpose:**
```text
Get all notification channels
```

**Parameters:** ``
**Variables Used:** `channels, cursor, rows, conn, channel`
**Implementation:**
```python
@router.get('/api/notifications/channels')
async def get_notification_channels():
    """Get all notification channels"""
    try:
        if not usage_tracker.enabled:
            return {'channels': []}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM notification_channels')
        rows = cursor.fetchall()
        conn.close()
        channels = []
        for row in rows:
            channel = dict(row)
            channel['config'] = safe_json_loads(row.get('config', '{}'), default={})
            channels.append(channel)
        return {'channels': channels, 'count': len(channels)}
    except Exception as e:
        logger.error(f'Get notification channels failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `create_notification_channel`
**Logic & Purpose:**
```text
Create notification channel
```

**Parameters:** `channel_data`
**Variables Used:** `conn, cursor, channel_id`
**Implementation:**
```python
@router.post('/api/notifications/channels')
async def create_notification_channel(channel_data: Dict[str, Any]):
    """Create notification channel"""
    try:
        if not usage_tracker.enabled:
            raise HTTPException(status_code=400, detail='Usage tracking disabled')
        conn = sqlite3.connect(usage_tracker.db_path)
        channel_id = f"chan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cursor = conn.execute('\n            INSERT INTO notification_channels (id, name, type, config, created_at)\n            VALUES (?, ?, ?, ?, ?)\n        ', (channel_id, channel_data.get('name', 'Unnamed Channel'), channel_data.get('type', 'in_app'), json.dumps(channel_data.get('config', {})), datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        return {'success': True, 'channel_id': channel_id, 'message': 'Channel created'}
    except Exception as e:
        logger.error(f'Create notification channel failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `test_notification_channel`
**Logic & Purpose:**
```text
Send test notification to channel
```

**Parameters:** `channel_id`
**Implementation:**
```python
@router.post('/api/notifications/channels/{channel_id}/test')
async def test_notification_channel(channel_id: str):
    """Send test notification to channel"""
    try:
        from src.services.notifications import notification_service
        success, message = notification_service.test_notification(channel_id)
        return {'success': success, 'channel_id': channel_id, 'message': message}
    except Exception as e:
        logger.error(f'Test notification failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_notification_history`
**Logic & Purpose:**
```text
Get notification delivery history
```

**Parameters:** `limit`
**Variables Used:** `history`
**Implementation:**
```python
@router.get('/api/notifications/history')
async def get_notification_history(limit: int=Query(50, ge=1, le=200)):
    """Get notification delivery history"""
    try:
        if not usage_tracker.enabled:
            return {'history': []}
        from src.services.notifications import notification_service
        history = notification_service.get_delivery_history(limit)
        return {'history': history, 'count': len(history)}
    except Exception as e:
        logger.error(f'Get notification history failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/analytics.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/analytics.py`

**Module Overview**: 
```text
Analytics API Endpoints - Phase 2
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, datetime.datetime, datetime.timedelta, typing.List, typing.Dict, typing.Optional, typing.Any, sqlite3, json, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Function: `get_timeseries_data`
**Parameters:** `metric, start_date, end_date, group_by, provider, model`
**Variables Used:** `cursor, params, where, filters, time_cond, end_date, rows, values, select, start_date, conn, labels`
**Implementation:**
```python
@router.get('/api/analytics/timeseries')
async def get_timeseries_data(metric: str=Query(...), start_date: Optional[str]=Query(None), end_date: Optional[str]=Query(None), group_by: str=Query('hour'), provider: Optional[str]=None, model: Optional[str]=None):
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        time_cond = {'hour': "strftime('%Y-%m-%d %H:00', timestamp)", 'day': "strftime('%Y-%m-%d', timestamp)", 'week': "strftime('%Y-W%W', timestamp)"}.get(group_by, "strftime('%Y-%m-%d %H:00', timestamp)")
        filters = [f'{time_cond} >= ?', f'{time_cond} <= ?']
        params = [start_date, end_date]
        if provider:
            filters.append('provider = ?')
            params.append(provider)
        if model:
            filters.append('routed_model = ?')
            params.append(model)
        where = ' AND '.join(filters)
        select = {'tokens': 'SUM(total_tokens)', 'cost': 'SUM(estimated_cost)', 'requests': 'COUNT(*)', 'latency': 'AVG(duration_ms)'}.get(metric, 'COUNT(*)')
        cursor = conn.execute(f'SELECT {time_cond} as time_bucket, {select} as value FROM api_requests WHERE {where} GROUP BY time_bucket ORDER BY time_bucket', params)
        rows = cursor.fetchall()
        labels = [r['time_bucket'] for r in rows]
        values = [r['value'] or 0 for r in rows]
        conn.close()
        return {'labels': labels, 'datasets': [{'label': metric.capitalize(), 'data': values}], 'meta': {'metric': metric, 'total': len(labels)}}
    except Exception as e:
        logger.error(f'Timeseries failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_aggregated_stats`
**Parameters:** `start_date, end_date`
**Variables Used:** `cursor, errs, cost, start_date, efficiency, end_date, error_rate, tokens, conn, row, reqs`
**Implementation:**
```python
@router.get('/api/analytics/aggregate')
async def get_aggregated_stats(start_date: Optional[str]=None, end_date: Optional[str]=None):
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("\n            SELECT COUNT(*) as requests, SUM(total_tokens) as tokens, SUM(estimated_cost) as cost,\n                   AVG(duration_ms) as latency, COUNT(DISTINCT provider) as providers, COUNT(DISTINCT routed_model) as models,\n                   SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors\n            FROM api_requests\n            WHERE timestamp >= ? AND timestamp <= ?\n        ", [start_date, end_date])
        row = cursor.fetchone()
        conn.close()
        reqs = row['requests'] or 0
        errs = row['errors'] or 0
        error_rate = errs / reqs * 100 if reqs > 0 else 0
        cost = row['cost'] or 0
        tokens = row['tokens'] or 0
        efficiency = tokens / cost if cost > 0 else 0
        return {'requests': {'total': reqs, 'errors': errs, 'error_rate': round(error_rate, 2)}, 'usage': {'tokens': tokens, 'cost': round(cost, 4), 'efficiency': round(efficiency, 2)}, 'performance': {'avg': round(row['latency'] or 0, 0)}, 'distribution': {'providers': row['providers'] or 0, 'models': row['models'] or 0}}
    except Exception as e:
        logger.error(f'Aggregate failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `execute_custom_query`
**Parameters:** `query_config`
**Variables Used:** `cursor, params, limit, results, conditions, offset, total, rows, total_cursor, sort_field, sort_order, query_parts, conn, count_query`
**Implementation:**
```python
@router.post('/api/analytics/query')
async def execute_custom_query(query_config: Dict[str, Any]):
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        query_parts = ['SELECT * FROM api_requests']
        conditions = []
        params = []
        if 'filters' in query_config:
            for f in query_config['filters']:
                field, operator, value = (f['field'], f['operator'], f['value'])
                if field not in {'provider', 'routed_model', 'status', 'estimated_cost', 'total_tokens', 'duration_ms', 'timestamp', 'model'}:
                    continue
                if operator == '=':
                    conditions.append(f'{field} = ?')
                    params.append(value)
                elif operator == '>':
                    conditions.append(f'{field} > ?')
                    params.append(value)
                elif operator == 'contains':
                    conditions.append(f'{field} LIKE ?')
                    params.append(f'%{value}%')
        if conditions:
            query_parts.append('WHERE ' + ' AND '.join(conditions))
        if 'sort' in query_config:
            sort_field = query_config['sort']['field']
            sort_order = query_config['sort']['order']
            if sort_field in {'timestamp', 'estimated_cost', 'total_tokens', 'duration_ms'}:
                query_parts.append(f'ORDER BY {sort_field} {sort_order}')
        limit = query_config.get('limit', 100)
        offset = query_config.get('offset', 0)
        query_parts.append(f'LIMIT {limit} OFFSET {offset}')
        cursor = conn.execute(' '.join(query_config), params)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        count_query = 'SELECT COUNT(*) as total FROM api_requests'
        if conditions:
            count_query += ' WHERE ' + ' AND '.join(conditions)
        total_cursor = conn.execute(count_query, params)
        total = total_cursor.fetchone()[0]
        conn.close()
        return {'results': results, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'has_more': offset + limit < total}, 'query': query_config}
    except Exception as e:
        logger.error(f'Custom query failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_custom_analytics`
**Logic & Purpose:**
```text
Custom analytics endpoint for query builder
```

**Parameters:** `metrics, start_date, end_date, group_by, aggregator`
**Variables Used:** `metric_list, metric_sql, cursor, data, time_cond, filter_conditions, query, rows, filter_params, where_clause, conn, metric_selects`
**Implementation:**
```python
@router.get('/api/analytics/custom')
async def get_custom_analytics(metrics: str=Query(...), start_date: str=Query(...), end_date: str=Query(...), group_by: str=Query('day'), aggregator: str=Query('sum')):
    """Custom analytics endpoint for query builder"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled', 'data': []}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        metric_list = [m.strip() for m in metrics.split(',')]
        time_cond = {'hour': "strftime('%Y-%m-%d %H:00', timestamp)", 'day': "strftime('%Y-%m-%d', timestamp)", 'week': "strftime('%Y-W%W', timestamp)", 'month': "strftime('%Y-%m', timestamp)"}.get(group_by, "strftime('%Y-%m-%d', timestamp)")
        metric_selects = []
        for m in metric_list:
            if m == 'tokens':
                metric_selects.append(f'{aggregator}(total_tokens) as tokens')
            elif m == 'cost':
                metric_selects.append(f'{aggregator}(estimated_cost) as cost')
            elif m == 'requests':
                metric_selects.append('COUNT(*) as requests')
            elif m == 'latency':
                metric_selects.append('AVG(duration_ms) as latency')
        if not metric_selects:
            return {'error': 'No valid metrics specified', 'data': []}
        filter_conditions = []
        filter_params = []
        filter_conditions.append(f'{time_cond} >= ?')
        filter_params.append(start_date)
        filter_conditions.append(f'{time_cond} <= ?')
        filter_params.append(end_date)
        where_clause = ' AND '.join(filter_conditions)
        metric_sql = ', '.join(metric_selects)
        query = f'\n            SELECT {time_cond} as date, {metric_sql}\n            FROM api_requests\n            WHERE {where_clause}\n            GROUP BY date\n            ORDER BY date\n        '
        cursor = conn.execute(query, filter_params)
        rows = cursor.fetchall()
        conn.close()
        data = [dict(row) for row in rows]
        return {'data': data, 'meta': {'metrics': metric_list, 'group_by': group_by, 'aggregator': aggregator}}
    except Exception as e:
        logger.error(f'Custom analytics failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `save_query`
**Logic & Purpose:**
```text
Save a custom query
```

**Parameters:** `query_data`
**Variables Used:** `created_at, query_id, query, conn, name`
**Implementation:**
```python
@router.post('/api/analytics/queries')
async def save_query(query_data: Dict[str, Any]):
    """Save a custom query"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.execute('\n            CREATE TABLE IF NOT EXISTS saved_queries (\n                id TEXT PRIMARY KEY,\n                name TEXT NOT NULL,\n                query TEXT NOT NULL,\n                created_at TEXT NOT NULL\n            )\n        ')
        import uuid
        query_id = str(uuid.uuid4())
        name = query_data.get('name', 'Untitled Query')
        query = json.dumps(query_data.get('query', {}))
        created_at = datetime.utcnow().isoformat()
        conn.execute('INSERT INTO saved_queries (id, name, query, created_at) VALUES (?, ?, ?, ?)', (query_id, name, query, created_at))
        conn.commit()
        conn.close()
        return {'id': query_id, 'name': name, 'status': 'saved'}
    except Exception as e:
        logger.error(f'Save query failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_saved_queries`
**Logic & Purpose:**
```text
Get all saved queries
```

**Parameters:** ``
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
@router.get('/api/analytics/queries')
async def get_saved_queries():
    """Get all saved queries"""
    try:
        if not usage_tracker.enabled:
            return []
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute('SELECT * FROM saved_queries ORDER BY created_at DESC')
        except sqlite3.OperationalError:
            conn.close()
            return []
        rows = cursor.fetchall()
        conn.close()
        return [{'id': row['id'], 'name': row['name'], 'query': json.loads(row['query']), 'created_at': row['created_at']} for row in rows]
    except Exception as e:
        logger.error(f'Get queries failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `delete_query`
**Logic & Purpose:**
```text
Delete a saved query
```

**Parameters:** `query_id`
**Variables Used:** `conn, cursor, deleted`
**Implementation:**
```python
@router.delete('/api/analytics/queries/{query_id}')
async def delete_query(query_id: str):
    """Delete a saved query"""
    try:
        if not usage_tracker.enabled:
            return {'error': 'Usage tracking disabled'}
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.execute('DELETE FROM saved_queries WHERE id = ?', (query_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return {'deleted': deleted > 0, 'id': query_id}
    except Exception as e:
        logger.error(f'Delete query failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `analytics_health`
**Parameters:** ``
**Implementation:**
```python
@router.get('/api/analytics/health')
async def analytics_health():
    return {'status': 'healthy', 'enabled': usage_tracker.enabled, 'database': usage_tracker.db_path if usage_tracker.enabled else None}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/integrations.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/integrations.py`

**Module Overview**: 
```text
Third-Party Integrations API - Phase 4

Endpoints for managing third-party integrations and forwarding events

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, typing.Dict, typing.Any, typing.List, typing.Optional, datetime.datetime, src.core.logging.logger, src.services.integrations.integration_manager, src.services.integrations.integration_forwarder, src.services.integrations.monitoring_bridge, src.services.integrations.IntegrationType, src.services.integrations.IntegrationConfig, src.services.integrations.IntegrationEvent

## Feature Function: `list_integrations`
**Logic & Purpose:**
```text
List all configured integrations
```

**Parameters:** ``
**Variables Used:** `integrations`
**Implementation:**
```python
@router.get('/api/integrations')
async def list_integrations():
    """List all configured integrations"""
    try:
        integrations = integration_manager.list_integrations()
        return {'integrations': integrations, 'count': len(integrations)}
    except Exception as e:
        logger.error(f'Failed to list integrations: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `configure_integration`
**Logic & Purpose:**
```text
Configure a new integration
```

**Parameters:** `integration_type, config`
**Variables Used:** `int_type, int_config`
**Implementation:**
```python
@router.post('/api/integrations/{integration_type}/config')
async def configure_integration(integration_type: str, config: Dict[str, Any]):
    """Configure a new integration"""
    try:
        try:
            int_type = IntegrationType(integration_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f'Invalid integration type: {integration_type}')
        int_config = IntegrationConfig(type=int_type, enabled=config.get('enabled', True), api_key=config.get('api_key'), endpoint=config.get('endpoint'), extra_config=config.get('extra_config', {}), created_at=datetime.now().isoformat())
        integration_manager.integrations[integration_type] = int_config
        integration_manager.save_config()
        return {'success': True, 'integration': integration_type, 'status': 'configured'}
    except Exception as e:
        logger.error(f'Configuration failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `enable_integration`
**Logic & Purpose:**
```text
Enable or disable an integration
```

**Parameters:** `name, enabled`
**Implementation:**
```python
@router.put('/api/integrations/{name}/enable')
async def enable_integration(name: str, enabled: bool):
    """Enable or disable an integration"""
    try:
        if name not in integration_manager.integrations:
            raise HTTPException(status_code=404, detail=f'Integration {name} not found')
        integration_manager.integrations[name].enabled = enabled
        integration_manager.save_config()
        return {'success': True, 'integration': name, 'enabled': enabled}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to enable integration: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `remove_integration`
**Logic & Purpose:**
```text
Remove an integration configuration
```

**Parameters:** `name`
**Implementation:**
```python
@router.delete('/api/integrations/{name}')
async def remove_integration(name: str):
    """Remove an integration configuration"""
    try:
        if name not in integration_manager.integrations:
            raise HTTPException(status_code=404, detail=f'Integration {name} not found')
        del integration_manager.integrations[name]
        integration_manager.save_config()
        return {'success': True, 'integration': name, 'status': 'removed'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to remove integration: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `test_integration`
**Logic & Purpose:**
```text
Test a specific integration
```

**Parameters:** `name`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/integrations/{name}/test')
async def test_integration(name: str):
    """Test a specific integration"""
    try:
        result = await integration_manager.test_integration(name)
        return result
    except Exception as e:
        logger.error(f'Test failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `forward_alert`
**Logic & Purpose:**
```text
Forward alert to integrations
```

**Parameters:** `alert_data, integrations`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/integrations/events/alert')
async def forward_alert(alert_data: Dict[str, Any], integrations: Optional[List[str]]=None):
    """Forward alert to integrations"""
    try:
        result = await integration_forwarder.forward_alert(alert_data, integrations)
        return {'success': True, 'integrations': result}
    except Exception as e:
        logger.error(f'Alert forwarding failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `forward_anomaly`
**Logic & Purpose:**
```text
Forward anomaly detection to integrations
```

**Parameters:** `anomaly_data, integrations`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/integrations/events/anomaly')
async def forward_anomaly(anomaly_data: Dict[str, Any], integrations: Optional[List[str]]=None):
    """Forward anomaly detection to integrations"""
    try:
        result = await integration_forwarder.forward_anomaly(anomaly_data, integrations)
        return {'success': True, 'integrations': result}
    except Exception as e:
        logger.error(f'Anomaly forwarding failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `forward_metric`
**Logic & Purpose:**
```text
Forward metric to integrations
```

**Parameters:** `metric_data, integrations`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/integrations/events/metric')
async def forward_metric(metric_data: Dict[str, Any], integrations: Optional[List[str]]=None):
    """Forward metric to integrations"""
    try:
        result = await integration_forwarder.forward_metric(metric_data, integrations)
        return {'success': True, 'integrations': result}
    except Exception as e:
        logger.error(f'Metric forwarding failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `forward_report`
**Logic & Purpose:**
```text
Forward report notification to integrations
```

**Parameters:** `report_data, integrations`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/integrations/events/report')
async def forward_report(report_data: Dict[str, Any], integrations: Optional[List[str]]=None):
    """Forward report notification to integrations"""
    try:
        result = await integration_forwarder.forward_report(report_data, integrations)
        return {'success': True, 'integrations': result}
    except Exception as e:
        logger.error(f'Report forwarding failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_system_status`
**Logic & Purpose:**
```text
Get current system status and sync with monitoring
```

**Parameters:** ``
**Variables Used:** `status`
**Implementation:**
```python
@router.get('/api/integrations/status')
async def get_system_status():
    """Get current system status and sync with monitoring"""
    try:
        status = await monitoring_bridge.sync_status()
        return status
    except Exception as e:
        logger.error(f'Status sync failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `send_custom_event`
**Logic & Purpose:**
```text
Send a custom event to integrations
```

**Parameters:** `event, integrations`
**Variables Used:** `result, int_event`
**Implementation:**
```python
@router.post('/api/integrations/custom-event')
async def send_custom_event(event: Dict[str, Any], integrations: Optional[List[str]]=None):
    """Send a custom event to integrations"""
    try:
        int_event = IntegrationEvent(event_type=event.get('type', 'custom'), severity=event.get('severity', 'info'), title=event.get('title', 'Custom Event'), message=event.get('message', ''), timestamp=datetime.now().isoformat(), metadata=event.get('metadata', {}))
        result = await integration_manager.send_event(int_event, integrations)
        return {'success': True, 'event': event, 'integrations': result}
    except Exception as e:
        logger.error(f'Custom event failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `integrations_health`
**Logic & Purpose:**
```text
Health check for integrations
```

**Parameters:** ``
**Variables Used:** `enabled_count, total_count`
**Implementation:**
```python
@router.get('/api/integrations/health')
async def integrations_health():
    """Health check for integrations"""
    try:
        enabled_count = sum((1 for config in integration_manager.integrations.values() if config.enabled))
        total_count = len(integration_manager.integrations)
        return {'status': 'healthy', 'total_integrations': total_count, 'enabled_integrations': enabled_count, 'integrations': [{'name': name, 'type': config.type.value, 'enabled': config.enabled} for name, config in integration_manager.integrations.items()]}
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_available_integrations`
**Logic & Purpose:**
```text
Get list of all available integration types
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/integrations/available')
async def get_available_integrations():
    """Get list of all available integration types"""
    return {'available': [{'type': t.value, 'description': t.name.title(), 'config_required': ['api_key', 'endpoint'], 'env_vars': [f'{t.value.upper()}_API_KEY', f'{t.value.upper()}_ENDPOINT']} for t in IntegrationType]}
```

---

## Feature Function: `forward_batch`
**Logic & Purpose:**
```text
Forward multiple events in batch
```

**Parameters:** `events, integrations`
**Variables Used:** `results, event, result`
**Implementation:**
```python
@router.post('/api/integrations/forward/batch')
async def forward_batch(events: List[Dict[str, Any]], integrations: Optional[List[str]]=None):
    """Forward multiple events in batch"""
    try:
        results = []
        for event_data in events:
            event = IntegrationEvent(event_type=event_data.get('type', 'batch'), severity=event_data.get('severity', 'info'), title=event_data.get('title', 'Batch Event'), message=event_data.get('message', ''), timestamp=datetime.now().isoformat(), metadata=event_data.get('metadata', {}))
            result = await integration_manager.send_event(event, integrations)
            results.append({'event': event_data, 'results': result})
        return {'success': True, 'batch_size': len(events), 'results': results}
    except Exception as e:
        logger.error(f'Batch forwarding failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_external_metrics`
**Logic & Purpose:**
```text
Fetch metrics from external monitoring systems
```

**Parameters:** `system, metric, hours`
**Variables Used:** `result`
**Implementation:**
```python
@router.get('/api/integrations/monitoring/external')
async def get_external_metrics(system: str=Query(..., enum=['datadog', 'newrelic']), metric: str=Query(...), hours: int=Query(24, ge=1, le=168)):
    """Fetch metrics from external monitoring systems"""
    try:
        if system == 'datadog':
            result = await monitoring_bridge.get_datadog_metrics(metric, hours)
        elif system == 'newrelic':
            result = await monitoring_bridge.get_newrelic_metrics(metric, hours)
        else:
            raise HTTPException(status_code=400, detail='Invalid system')
        return result
    except Exception as e:
        logger.error(f'External metric fetch failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `verify_webhook`
**Logic & Purpose:**
```text
Verify webhook endpoint connectivity
```

**Parameters:** `url, payload`
**Variables Used:** `test_payload, content`
**Implementation:**
```python
@router.post('/api/integrations/webhook/verify')
async def verify_webhook(url: str, payload: Optional[Dict[str, Any]]=None):
    """Verify webhook endpoint connectivity"""
    import aiohttp
    try:
        test_payload = payload or {'test': True, 'timestamp': datetime.now().isoformat(), 'source': 'claude-proxy', 'message': 'Webhook verification'}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_payload, timeout=10) as response:
                content = await response.text()
                return {'success': 200 <= response.status < 300, 'status_code': response.status, 'response': content[:500], 'headers': dict(response.headers)}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/websocket_dashboard.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/websocket_dashboard.py`

**Module Overview**: 
```text
WebSocket Dashboard API

Provides real-time dashboard updates via WebSocket connections.
```

## Global Presets & Variables
- `router` = `APIRouter()`
- `dashboard_broadcaster` = `DashboardBroadcaster()`
- `logs_broadcaster` = `LogsBroadcaster()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.WebSocket, fastapi.WebSocketDisconnect, fastapi.responses.FileResponse, typing.Set, json, asyncio, pathlib.Path, src.core.logging.logger

## Feature Class: `DashboardBroadcaster`
**Description:**
```text
Broadcasts dashboard updates to all connected clients
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.connections: Set[WebSocket] = set()
```

### Method: `connect`
**Logic & Purpose:**
```text
Add a new WebSocket connection
```

**Parameters:** `self, websocket`
**Implementation:**
```python
async def connect(self, websocket: WebSocket):
    """Add a new WebSocket connection"""
    await websocket.accept()
    self.connections.add(websocket)
    logger.info(f'WebSocket client connected. Total connections: {len(self.connections)}')
```

### Method: `disconnect`
**Logic & Purpose:**
```text
Remove a WebSocket connection
```

**Parameters:** `self, websocket`
**Implementation:**
```python
def disconnect(self, websocket: WebSocket):
    """Remove a WebSocket connection"""
    self.connections.discard(websocket)
    logger.info(f'WebSocket client disconnected. Total connections: {len(self.connections)}')
```

### Method: `broadcast`
**Logic & Purpose:**
```text
Broadcast message to all connected clients
```

**Parameters:** `self, message`
**Variables Used:** `disconnected`
**Implementation:**
```python
async def broadcast(self, message: dict):
    """Broadcast message to all connected clients"""
    if not self.connections:
        return
    disconnected = set()
    for connection in self.connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.warning(f'Error broadcasting to WebSocket client: {e}')
            disconnected.add(connection)
    for conn in disconnected:
        self.connections.discard(conn)
```

---

## Feature Function: `websocket_dashboard`
**Logic & Purpose:**
```text
WebSocket endpoint for real-time dashboard updates
```

**Parameters:** `websocket`
**Variables Used:** `initial_state, data`
**Implementation:**
```python
@router.websocket('/ws/dashboard')
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    await dashboard_broadcaster.connect(websocket)
    try:
        from src.dashboard.dashboard_hooks import dashboard_hooks
        initial_state = {'type': 'initial_state', 'data': dashboard_hooks.get_stats()}
        await websocket.send_json(initial_state)
        while True:
            try:
                data = await websocket.receive_text()
                if data == 'ping':
                    await websocket.send_text('pong')
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f'WebSocket error: {e}')
                break
    finally:
        dashboard_broadcaster.disconnect(websocket)
```

---

## Feature Function: `serve_websocket_dashboard`
**Logic & Purpose:**
```text
Serve the WebSocket dashboard HTML page
```

**Parameters:** ``
**Variables Used:** `dashboard_file`
**Implementation:**
```python
@router.get('/dashboard')
async def serve_websocket_dashboard():
    """Serve the WebSocket dashboard HTML page"""
    dashboard_file = Path(__file__).parent.parent.parent / 'static' / 'dashboard.html'
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    return {'error': 'Dashboard page not found'}
```

---

## Feature Function: `broadcast_dashboard_update`
**Logic & Purpose:**
```text
Broadcast a dashboard update to all connected clients.

Args:
    update_type: Type of update (e.g., 'request_start', 'request_complete', 'stats_update')
    data: Update data
```

**Parameters:** `update_type, data`
**Variables Used:** `message`
**Implementation:**
```python
async def broadcast_dashboard_update(update_type: str, data: dict):
    """
    Broadcast a dashboard update to all connected clients.

    Args:
        update_type: Type of update (e.g., 'request_start', 'request_complete', 'stats_update')
        data: Update data
    """
    message = {'type': update_type, 'data': data, 'timestamp': asyncio.get_event_loop().time()}
    await dashboard_broadcaster.broadcast(message)
```

---

## Feature Class: `LogsBroadcaster`
**Description:**
```text
Broadcasts log messages to connected web UI clients
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.connections: Set[WebSocket] = set()
```

### Method: `connect`
**Logic & Purpose:**
```text
Add a new WebSocket connection
```

**Parameters:** `self, websocket`
**Implementation:**
```python
async def connect(self, websocket: WebSocket):
    """Add a new WebSocket connection"""
    await websocket.accept()
    self.connections.add(websocket)
    logger.info(f'Logs WebSocket client connected. Total: {len(self.connections)}')
```

### Method: `disconnect`
**Logic & Purpose:**
```text
Remove a WebSocket connection
```

**Parameters:** `self, websocket`
**Implementation:**
```python
def disconnect(self, websocket: WebSocket):
    """Remove a WebSocket connection"""
    self.connections.discard(websocket)
    logger.info(f'Logs WebSocket client disconnected. Total: {len(self.connections)}')
```

### Method: `broadcast`
**Logic & Purpose:**
```text
Broadcast a log message to all connected clients
```

**Parameters:** `self, message, level`
**Variables Used:** `disconnected, payload`
**Implementation:**
```python
async def broadcast(self, message: str, level: str='info'):
    """Broadcast a log message to all connected clients"""
    if not self.connections:
        return
    payload = {'message': message, 'level': level}
    disconnected = set()
    for connection in self.connections:
        try:
            await connection.send_json(payload)
        except Exception:
            disconnected.add(connection)
    for conn in disconnected:
        self.connections.discard(conn)
```

---

## Feature Function: `websocket_logs`
**Logic & Purpose:**
```text
WebSocket endpoint for live request logs (Web UI)
```

**Parameters:** `websocket`
**Variables Used:** `data`
**Implementation:**
```python
@router.websocket('/ws/logs')
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for live request logs (Web UI)"""
    await logs_broadcaster.connect(websocket)
    try:
        await websocket.send_json({'message': 'Connected to live log stream', 'level': 'info'})
        while True:
            try:
                data = await websocket.receive_text()
                if data == 'ping':
                    await websocket.send_text('pong')
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        logs_broadcaster.disconnect(websocket)
```

---

## Feature Function: `broadcast_log`
**Logic & Purpose:**
```text
Broadcast a log message to all connected Web UI clients.

Args:
    message: Log message text
    level: Log level (info, warning, error, success)
```

**Parameters:** `message, level`
**Implementation:**
```python
async def broadcast_log(message: str, level: str='info'):
    """
    Broadcast a log message to all connected Web UI clients.

    Args:
        message: Log message text
        level: Log level (info, warning, error, success)
    """
    await logs_broadcaster.broadcast(message, level)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/billing.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/billing.py`

**Module Overview**: 
```text
Billing API Endpoints

Provides access to real-time billing data from provider APIs.
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.Query, fastapi.HTTPException, src.services.billing.billing_integrations.BillingManager, src.services.billing.billing_integrations.BillingProvider, src.core.logging.logger

## Feature Function: `get_billing_usage`
**Logic & Purpose:**
```text
Fetch actual billing usage from all configured providers.

Returns real billing data where available, falls back to estimates.
```

**Parameters:** `days`
**Variables Used:** `usage_data`
**Implementation:**
```python
@router.get('/api/billing/usage')
async def get_billing_usage(days: int=Query(7, ge=1, le=90, description='Number of days')):
    """
    Fetch actual billing usage from all configured providers.

    Returns real billing data where available, falls back to estimates.
    """
    try:
        usage_data = await billing_manager.fetch_all_usage(days=days)
        return usage_data
    except Exception as e:
        logger.error(f'Failed to fetch billing usage: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_billing_balance`
**Logic & Purpose:**
```text
Fetch current account balance/credits from all configured providers.

Returns current billing status and remaining credits.
```

**Parameters:** ``
**Variables Used:** `balance_data`
**Implementation:**
```python
@router.get('/api/billing/balance')
async def get_billing_balance():
    """
    Fetch current account balance/credits from all configured providers.

    Returns current billing status and remaining credits.
    """
    try:
        balance_data = await billing_manager.fetch_all_balances()
        return balance_data
    except Exception as e:
        logger.error(f'Failed to fetch billing balance: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_provider_billing`
**Logic & Purpose:**
```text
Fetch billing data for a specific provider.

Supported providers: openai, openrouter, anthropic
```

**Parameters:** `provider_name, days`
**Variables Used:** `usage_data, end_date, balance_data, provider, start_date`
**Implementation:**
```python
@router.get('/api/billing/provider/{provider_name}')
async def get_provider_billing(provider_name: str, days: int=Query(7, ge=1, le=90, description='Number of days')):
    """
    Fetch billing data for a specific provider.

    Supported providers: openai, openrouter, anthropic
    """
    provider = billing_manager.get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found. Available: openai, openrouter, anthropic")
    if not provider.enabled:
        raise HTTPException(status_code=503, detail=f"Provider '{provider_name}' is not configured. Add API key to environment.")
    try:
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        usage_data = await provider.fetch_usage(start_date, end_date)
        balance_data = await provider.fetch_current_balance()
        return {'provider': provider_name, 'usage': usage_data, 'balance': balance_data}
    except Exception as e:
        logger.error(f'Failed to fetch {provider_name} billing: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/benchmarks.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/benchmarks.py`

**Module Overview**: 
```text
Benchmarking API Endpoints

Provides endpoints to run model benchmarks and view results.
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.Query, fastapi.HTTPException, fastapi.BackgroundTasks, typing.List, pathlib.Path, json, src.services.benchmarking.model_benchmarks.model_benchmarker, src.services.benchmarking.model_benchmarks.BENCHMARK_TESTS, src.core.logging.logger

## Feature Function: `run_benchmark`
**Logic & Purpose:**
```text
Run a benchmark on a specific model.

This runs in the background and saves results to disk.
```

**Parameters:** `model_name, iterations, background_tasks`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/benchmarks/run')
async def run_benchmark(model_name: str=Query(..., description='Model to benchmark'), iterations: int=Query(1, ge=1, le=10, description='Number of iterations'), background_tasks: BackgroundTasks=None):
    """
    Run a benchmark on a specific model.

    This runs in the background and saves results to disk.
    """
    try:

        async def run_benchmark_task():
            try:
                await model_benchmarker.benchmark_model(model_name, iterations=iterations)
            except Exception as e:
                logger.error(f'Benchmark failed: {e}')
        if background_tasks:
            background_tasks.add_task(run_benchmark_task)
            return {'status': 'started', 'model': model_name, 'iterations': iterations, 'message': 'Benchmark started in background. Check /api/benchmarks/results for results.'}
        else:
            result = await model_benchmarker.benchmark_model(model_name, iterations=iterations)
            return {'status': 'completed', 'result': result}
    except Exception as e:
        logger.error(f'Failed to start benchmark: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `compare_models`
**Logic & Purpose:**
```text
Compare multiple models on the same test suite.
```

**Parameters:** `models, background_tasks`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/benchmarks/compare')
async def compare_models(models: List[str]=Query(..., description='List of models to compare'), background_tasks: BackgroundTasks=None):
    """
    Compare multiple models on the same test suite.
    """
    if len(models) < 2:
        raise HTTPException(status_code=400, detail='At least 2 models required for comparison')
    try:

        async def run_comparison_task():
            try:
                await model_benchmarker.compare_models(models)
            except Exception as e:
                logger.error(f'Comparison failed: {e}')
        if background_tasks:
            background_tasks.add_task(run_comparison_task)
            return {'status': 'started', 'models': models, 'message': 'Comparison started in background. Check /api/benchmarks/results for results.'}
        else:
            result = await model_benchmarker.compare_models(models)
            return {'status': 'completed', 'result': result}
    except Exception as e:
        logger.error(f'Failed to start comparison: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_benchmark_results`
**Logic & Purpose:**
```text
Get recent benchmark results.

Returns list of benchmark result files sorted by date.
```

**Parameters:** `limit`
**Variables Used:** `results, result_files, data, results_dir`
**Implementation:**
```python
@router.get('/api/benchmarks/results')
async def get_benchmark_results(limit: int=Query(20, ge=1, le=100, description='Maximum number of results')):
    """
    Get recent benchmark results.

    Returns list of benchmark result files sorted by date.
    """
    try:
        results_dir = Path('benchmark_results')
        if not results_dir.exists():
            return {'results': []}
        result_files = sorted(results_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
        results = []
        for filepath in result_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    results.append({'filename': filepath.name, 'timestamp': data.get('timestamp'), 'model': data.get('model', data.get('models', [])), 'summary': data.get('summary', data.get('winner'))})
            except Exception as e:
                logger.warning(f'Failed to read {filepath}: {e}')
        return {'count': len(results), 'results': results}
    except Exception as e:
        logger.error(f'Failed to get benchmark results: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_benchmark_result`
**Logic & Purpose:**
```text
Get detailed results from a specific benchmark run.
```

**Parameters:** `filename`
**Variables Used:** `filepath, data`
**Implementation:**
```python
@router.get('/api/benchmarks/results/{filename}')
async def get_benchmark_result(filename: str):
    """
    Get detailed results from a specific benchmark run.
    """
    try:
        filepath = Path('benchmark_results') / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail='Benchmark result not found')
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to get benchmark result: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_benchmark_tests`
**Logic & Purpose:**
```text
Get list of available benchmark tests.
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/benchmarks/tests')
async def get_benchmark_tests():
    """
    Get list of available benchmark tests.
    """
    return {'count': len(BENCHMARK_TESTS), 'tests': [{'name': test.name, 'category': test.category, 'prompt': test.prompt[:100] + '...' if len(test.prompt) > 100 else test.prompt} for test in BENCHMARK_TESTS]}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/websocket_logs.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/websocket_logs.py`

**Module Overview**: 
```text
WebSocket endpoints for live log streaming and real-time updates.
```

## Global Presets & Variables
- `router` = `APIRouter()`
- `log_broadcaster` = `LogBroadcaster()`

## Dependencies & Imports
asyncio, collections.deque, datetime.datetime, datetime.timezone, typing.Set, typing.Dict, typing.Any, typing.Optional, fastapi.APIRouter, fastapi.WebSocket, fastapi.WebSocketDisconnect, json

## Feature Class: `LogBroadcaster`
**Description:**
```text
Manages WebSocket connections and broadcasts log messages to all connected clients.
Acts as a central hub for log events from the proxy.
```

### Method: `__init__`
**Parameters:** `self, max_history`
**Implementation:**
```python
def __init__(self, max_history: int=100):
    self.connections: Set[WebSocket] = set()
    self.history: deque = deque(maxlen=max_history)
    self._lock = asyncio.Lock()
```

### Method: `connect`
**Logic & Purpose:**
```text
Accept a new WebSocket connection.
```

**Parameters:** `self, websocket`
**Implementation:**
```python
async def connect(self, websocket: WebSocket):
    """Accept a new WebSocket connection."""
    await websocket.accept()
    async with self._lock:
        self.connections.add(websocket)
    for log_entry in self.history:
        try:
            await websocket.send_json(log_entry)
        except Exception:
            pass
```

### Method: `disconnect`
**Logic & Purpose:**
```text
Remove a WebSocket connection.
```

**Parameters:** `self, websocket`
**Implementation:**
```python
async def disconnect(self, websocket: WebSocket):
    """Remove a WebSocket connection."""
    async with self._lock:
        self.connections.discard(websocket)
```

### Method: `broadcast`
**Logic & Purpose:**
```text
Broadcast a log entry to all connected clients.
```

**Parameters:** `self, log_entry`
**Variables Used:** `disconnected`
**Implementation:**
```python
async def broadcast(self, log_entry: Dict[str, Any]):
    """Broadcast a log entry to all connected clients."""
    log_entry['timestamp'] = datetime.now().isoformat()
    self.history.append(log_entry)
    disconnected = set()
    for connection in self.connections:
        try:
            await connection.send_json(log_entry)
        except Exception:
            disconnected.add(connection)
    async with self._lock:
        self.connections -= disconnected
```

### Method: `log`
**Logic & Purpose:**
```text
Synchronous log method that schedules async broadcast.
```

**Parameters:** `self, level, message`
**Variables Used:** `log_entry, loop`
**Implementation:**
```python
def log(self, level: str, message: str, **kwargs):
    """Synchronous log method that schedules async broadcast."""
    log_entry = {'level': level, 'message': message, **kwargs}
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.broadcast(log_entry))
        else:
            loop.run_until_complete(self.broadcast(log_entry))
    except RuntimeError:
        log_entry['timestamp'] = datetime.now().isoformat()
        self.history.append(log_entry)
```

### Method: `client_count`
**Parameters:** `self`
**Implementation:**
```python
@property
def client_count(self) -> int:
    return len(self.connections)
```

---

## Feature Function: `websocket_logs`
**Logic & Purpose:**
```text
WebSocket endpoint for live log streaming.

Clients receive JSON messages with format:
{
    "timestamp": "2025-12-28T07:30:00.000000",
    "level": "info|warning|error|debug",
    "message": "Log message text",
    "model": "optional model name",
    "request_id": "optional request id",
    ...additional context
}
```

**Parameters:** `websocket`
**Variables Used:** `data`
**Implementation:**
```python
@router.websocket('/api/ws/logs')
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for live log streaming.
    
    Clients receive JSON messages with format:
    {
        "timestamp": "2025-12-28T07:30:00.000000",
        "level": "info|warning|error|debug",
        "message": "Log message text",
        "model": "optional model name",
        "request_id": "optional request id",
        ...additional context
    }
    """
    await log_broadcaster.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == 'ping':
                await websocket.send_json({'type': 'pong'})
    except WebSocketDisconnect:
        await log_broadcaster.disconnect(websocket)
```

---

## Feature Function: `log_request`
**Logic & Purpose:**
```text
Log a request completion.
```

**Parameters:** `request_id, model, input_tokens, output_tokens, duration_ms, status, error`
**Implementation:**
```python
def log_request(request_id: str, model: str, input_tokens: int, output_tokens: int, duration_ms: int, status: str='success', error: Optional[str]=None):
    """Log a request completion."""
    log_broadcaster.log(level='info' if status == 'success' else 'error', message=f'Request completed: {model}', request_id=request_id, model=model, input_tokens=input_tokens, output_tokens=output_tokens, duration_ms=duration_ms, status=status, error=error)
```

---

## Feature Function: `log_cascade`
**Logic & Purpose:**
```text
Log a cascade event.
```

**Parameters:** `model, action, tier, reason, from_model, to_model, request_id, retry_count, error`
**Variables Used:** `message, event, loop`
**Implementation:**
```python
def log_cascade(model: str, action: str, tier: Optional[str]=None, reason: Optional[str]=None, from_model: Optional[str]=None, to_model: Optional[str]=None, request_id: Optional[str]=None, retry_count: int=0, error: Optional[str]=None):
    """Log a cascade event."""
    event = {'timestamp': datetime.now(timezone.utc).isoformat(), 'model': model, 'action': action, 'tier': tier, 'reason': reason, 'from_model': from_model, 'to_model': to_model, 'request_id': request_id, 'retry_count': retry_count, 'error': error}
    _cascade_events.append(event)
    message = f'Cascade {action}: {model}'
    if from_model and to_model:
        message = f'Cascade {action}: {from_model} -> {to_model}'
    if reason:
        message = f'{message} ({reason})'
    log_broadcaster.log(level='warning' if action == 'switch' else 'info', message=message, event_type='cascade', model=model, action=action, tier=tier, reason=reason, from_model=from_model, to_model=to_model, request_id=request_id, retry_count=retry_count, error=error)
    try:
        from src.api.websocket_dashboard import logs_broadcaster
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(logs_broadcaster.broadcast(f'[cascade] {message}', 'warning' if action == 'switch' else 'info'))
    except Exception:
        pass
```

---

## Feature Function: `get_cascade_stats`
**Logic & Purpose:**
```text
Get aggregate cascade metrics and recent events for monitor UI.
```

**Parameters:** `limit`
**Variables Used:** `completed_attempts, successes, reason, exhausted, retries, success_rate, events, switches`
**Implementation:**
```python
def get_cascade_stats(limit: int=20) -> Dict[str, Any]:
    """Get aggregate cascade metrics and recent events for monitor UI."""
    events = list(_cascade_events)
    if not events:
        return {'total_events': 0, 'switches': 0, 'retries': 0, 'successes': 0, 'exhausted': 0, 'success_rate': 0.0, 'reasons': {}, 'recent': []}
    switches = sum((1 for e in events if e.get('action') == 'switch'))
    retries = sum((1 for e in events if e.get('action') == 'retry'))
    successes = sum((1 for e in events if e.get('action') == 'success'))
    exhausted = sum((1 for e in events if e.get('action') == 'exhausted'))
    reasons: Dict[str, int] = {}
    for event in events:
        reason = event.get('reason')
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
    completed_attempts = successes + exhausted
    success_rate = successes / completed_attempts if completed_attempts > 0 else 0.0
    return {'total_events': len(events), 'switches': switches, 'retries': retries, 'successes': successes, 'exhausted': exhausted, 'success_rate': round(success_rate * 100, 1), 'reasons': reasons, 'recent': list(reversed(events[-max(1, limit):]))}
```

---

## Feature Function: `log_crosstalk`
**Logic & Purpose:**
```text
Log a crosstalk turn.
```

**Parameters:** `session_id, turn, speaker, listener, message_preview`
**Implementation:**
```python
def log_crosstalk(session_id: str, turn: int, speaker: str, listener: str, message_preview: str):
    """Log a crosstalk turn."""
    log_broadcaster.log(level='info', message=f'Crosstalk turn {turn}: {speaker} → {listener}', session_id=session_id, turn=turn, speaker=speaker, listener=listener, preview=message_preview[:100] if len(message_preview) > 100 else message_preview)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/docs_routes.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/docs_routes.py`

**Module Overview**: 
```text
Documentation API Routes

Serves markdown documentation files for the web UI.
```

## Global Presets & Variables
- `router` = `APIRouter(prefix='/api/docs', tags=['documentation'])`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent`
- `DOCS_DIR` = `PROJECT_ROOT / 'docs'`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, pathlib.Path, typing.List, typing.Dict, typing.Any

## Feature Function: `list_docs`
**Logic & Purpose:**
```text
List all available documentation files.
```

**Parameters:** ``
**Variables Used:** `docs, relative`
**Implementation:**
```python
@router.get('/')
async def list_docs() -> Dict[str, Any]:
    """List all available documentation files."""
    docs = []
    if not DOCS_DIR.exists():
        return {'docs': [], 'error': 'Documentation directory not found'}
    for path in DOCS_DIR.rglob('*.md'):
        relative = path.relative_to(DOCS_DIR)
        docs.append({'path': str(relative), 'name': path.stem.replace('-', ' ').replace('_', ' ').title(), 'category': relative.parent.name if relative.parent.name != '.' else 'root', 'size': path.stat().st_size})
    docs.sort(key=lambda x: (0 if x['category'] == 'root' else 1, x['category'], x['name']))
    return {'docs': docs, 'categories': list(set((d['category'] for d in docs)))}
```

---

## Feature Function: `get_doc`
**Logic & Purpose:**
```text
Get a specific documentation file's content.
```

**Parameters:** `path`
**Variables Used:** `doc_path, title, content`
**Implementation:**
```python
@router.get('/{path:path}')
async def get_doc(path: str) -> Dict[str, Any]:
    """Get a specific documentation file's content."""
    if '..' in path:
        raise HTTPException(status_code=400, detail='Invalid path')
    doc_path = DOCS_DIR / path
    if not doc_path.suffix:
        doc_path = doc_path.with_suffix('.md')
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail=f'Document not found: {path}')
    if not doc_path.is_file():
        raise HTTPException(status_code=400, detail='Path is not a file')
    try:
        content = doc_path.read_text()
        title = path
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break
        return {'path': str(doc_path.relative_to(DOCS_DIR)), 'title': title, 'content': content, 'size': len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error reading document: {str(e)}')
```

---

## Feature Function: `search_docs`
**Logic & Purpose:**
```text
Search documentation content.
```

**Parameters:** `query`
**Variables Used:** `results, content, query_lower, matches`
**Implementation:**
```python
@router.get('/search/{query}')
async def search_docs(query: str) -> Dict[str, Any]:
    """Search documentation content."""
    results = []
    query_lower = query.lower()
    if not DOCS_DIR.exists():
        return {'results': [], 'query': query}
    for path in DOCS_DIR.rglob('*.md'):
        try:
            content = path.read_text()
            if query_lower in content.lower():
                matches = []
                for i, line in enumerate(content.split('\n')):
                    if query_lower in line.lower():
                        matches.append({'line': i + 1, 'text': line[:200]})
                results.append({'path': str(path.relative_to(DOCS_DIR)), 'name': path.stem.replace('-', ' ').replace('_', ' ').title(), 'matches': matches[:5]})
        except Exception:
            continue
    return {'query': query, 'results': results, 'count': len(results)}
```

---


