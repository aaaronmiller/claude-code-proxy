# File Audit: /home/cheta/code/claude-code-proxy/src/auth/user_manager.py
**Path**: `/home/cheta/code/claude-code-proxy/src/auth/user_manager.py`

**Module Overview**: 
```text
Multi-User Authentication System

Manages users, API keys, and per-user usage tracking.
```

## Global Presets & Variables
- `user_manager` = `UserManager()`

## Dependencies & Imports
sqlite3, os, secrets, hashlib, datetime.datetime, datetime.timedelta, typing.Dict, typing.Any, typing.Optional, typing.List, pathlib.Path, src.core.logging.logger

## Feature Class: `UserManager`
**Description:**
```text
Manages users and API keys for multi-user deployments
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Variables Used:** `project_root`
**Implementation:**
```python
def __init__(self, db_path: str='data/users.db'):
    if not os.path.isabs(db_path):
        project_root = Path(__file__).parent.parent.parent
        self.db_path = str(project_root / db_path)
    else:
        self.db_path = db_path
    self._init_db()
```

### Method: `_init_db`
**Logic & Purpose:**
```text
Initialize user database
```

**Parameters:** `self`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def _init_db(self):
    """Initialize user database"""
    Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("\n            CREATE TABLE IF NOT EXISTS users (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                username TEXT UNIQUE NOT NULL,\n                email TEXT UNIQUE NOT NULL,\n                created_at TEXT NOT NULL,\n                active BOOLEAN DEFAULT 1,\n                role TEXT DEFAULT 'user',\n                quota_requests_per_day INTEGER DEFAULT 1000,\n                quota_tokens_per_day INTEGER DEFAULT 1000000,\n                quota_cost_per_day REAL DEFAULT 10.0\n            )\n        ")
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS api_keys (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                user_id INTEGER NOT NULL,\n                key_hash TEXT UNIQUE NOT NULL,\n                key_prefix TEXT NOT NULL,\n                name TEXT NOT NULL,\n                created_at TEXT NOT NULL,\n                last_used_at TEXT,\n                active BOOLEAN DEFAULT 1,\n                FOREIGN KEY (user_id) REFERENCES users(id)\n            )\n        ')
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS user_usage (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                user_id INTEGER NOT NULL,\n                date TEXT NOT NULL,\n                request_count INTEGER DEFAULT 0,\n                token_count INTEGER DEFAULT 0,\n                cost REAL DEFAULT 0.0,\n                FOREIGN KEY (user_id) REFERENCES users(id),\n                UNIQUE(user_id, date)\n            )\n        ')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_usage_date ON user_usage(user_id, date)')
    conn.commit()
    conn.close()
```

### Method: `create_user`
**Logic & Purpose:**
```text
Create a new user.

Returns user details including generated API key.
```

**Parameters:** `self, username, email, role, quota_requests, quota_tokens, quota_cost`
**Variables Used:** `cursor, api_key, key_prefix, key_hash, user_id, conn`
**Implementation:**
```python
def create_user(self, username: str, email: str, role: str='user', quota_requests: int=1000, quota_tokens: int=1000000, quota_cost: float=10.0) -> Dict[str, Any]:
    """
        Create a new user.

        Returns user details including generated API key.
        """
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                INSERT INTO users (username, email, created_at, role, quota_requests_per_day, quota_tokens_per_day, quota_cost_per_day)\n                VALUES (?, ?, ?, ?, ?, ?, ?)\n            ', (username, email, datetime.utcnow().isoformat(), role, quota_requests, quota_tokens, quota_cost))
        user_id = cursor.lastrowid
        api_key = self._generate_api_key()
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:8]
        cursor.execute('\n                INSERT INTO api_keys (user_id, key_hash, key_prefix, name, created_at)\n                VALUES (?, ?, ?, ?, ?)\n            ', (user_id, key_hash, key_prefix, 'Default Key', datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        logger.info(f'Created user: {username} (ID: {user_id})')
        return {'user_id': user_id, 'username': username, 'email': email, 'role': role, 'api_key': api_key, 'created_at': datetime.utcnow().isoformat()}
    except sqlite3.IntegrityError as e:
        logger.error(f'Failed to create user: {e}')
        raise ValueError('Username or email already exists')
    except Exception as e:
        logger.error(f'Failed to create user: {e}')
        raise
```

### Method: `validate_api_key`
**Logic & Purpose:**
```text
Validate API key and return user info.

Returns None if invalid.
```

**Parameters:** `self, api_key`
**Variables Used:** `cursor, key_hash, user, conn, row`
**Implementation:**
```python
def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
    """
        Validate API key and return user info.

        Returns None if invalid.
        """
    try:
        key_hash = self._hash_key(api_key)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('\n                SELECT u.*, a.id as key_id\n                FROM users u\n                JOIN api_keys a ON u.id = a.user_id\n                WHERE a.key_hash = ? AND a.active = 1 AND u.active = 1\n            ', (key_hash,))
        row = cursor.fetchone()
        if row:
            cursor.execute('\n                    UPDATE api_keys\n                    SET last_used_at = ?\n                    WHERE id = ?\n                ', (datetime.utcnow().isoformat(), row['key_id']))
            conn.commit()
            user = dict(row)
            conn.close()
            return user
        conn.close()
        return None
    except Exception as e:
        logger.error(f'Failed to validate API key: {e}')
        return None
```

### Method: `check_user_quota`
**Logic & Purpose:**
```text
Check if user has remaining quota for today.

Returns quota status.
```

**Parameters:** `self, user_id`
**Variables Used:** `tokens_remaining, cursor, cost_remaining, today, usage, cost_used, requests_used, tokens_used, user, conn, requests_remaining`
**Implementation:**
```python
def check_user_quota(self, user_id: int) -> Dict[str, Any]:
    """
        Check if user has remaining quota for today.

        Returns quota status.
        """
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('\n                SELECT quota_requests_per_day, quota_tokens_per_day, quota_cost_per_day\n                FROM users\n                WHERE id = ?\n            ', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return {'error': 'User not found'}
        today = datetime.utcnow().date().isoformat()
        cursor.execute('\n                SELECT request_count, token_count, cost\n                FROM user_usage\n                WHERE user_id = ? AND date = ?\n            ', (user_id, today))
        usage = cursor.fetchone()
        conn.close()
        if usage:
            requests_used = usage['request_count']
            tokens_used = usage['token_count']
            cost_used = usage['cost']
        else:
            requests_used = 0
            tokens_used = 0
            cost_used = 0.0
        requests_remaining = user['quota_requests_per_day'] - requests_used
        tokens_remaining = user['quota_tokens_per_day'] - tokens_used
        cost_remaining = user['quota_cost_per_day'] - cost_used
        return {'user_id': user_id, 'date': today, 'requests': {'limit': user['quota_requests_per_day'], 'used': requests_used, 'remaining': max(0, requests_remaining), 'exceeded': requests_remaining < 0}, 'tokens': {'limit': user['quota_tokens_per_day'], 'used': tokens_used, 'remaining': max(0, tokens_remaining), 'exceeded': tokens_remaining < 0}, 'cost': {'limit': user['quota_cost_per_day'], 'used': cost_used, 'remaining': max(0, cost_remaining), 'exceeded': cost_remaining < 0}, 'quota_ok': requests_remaining > 0 and tokens_remaining > 0 and (cost_remaining > 0)}
    except Exception as e:
        logger.error(f'Failed to check quota: {e}')
        return {'error': str(e)}
```

### Method: `record_usage`
**Logic & Purpose:**
```text
Record usage for a user
```

**Parameters:** `self, user_id, requests, tokens, cost`
**Variables Used:** `today, conn, cursor`
**Implementation:**
```python
def record_usage(self, user_id: int, requests: int=1, tokens: int=0, cost: float=0.0):
    """Record usage for a user"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.utcnow().date().isoformat()
        cursor.execute('\n                INSERT INTO user_usage (user_id, date, request_count, token_count, cost)\n                VALUES (?, ?, ?, ?, ?)\n                ON CONFLICT(user_id, date) DO UPDATE SET\n                    request_count = request_count + ?,\n                    token_count = token_count + ?,\n                    cost = cost + ?\n            ', (user_id, today, requests, tokens, cost, requests, tokens, cost))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f'Failed to record usage: {e}')
```

### Method: `_generate_api_key`
**Logic & Purpose:**
```text
Generate a secure API key
```

**Parameters:** `self`
**Implementation:**
```python
def _generate_api_key(self) -> str:
    """Generate a secure API key"""
    return f'sk-{secrets.token_urlsafe(32)}'
```

### Method: `_hash_key`
**Logic & Purpose:**
```text
Hash API key for storage
```

**Parameters:** `self, api_key`
**Implementation:**
```python
def _hash_key(self, api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/alert_engine.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/alert_engine.py`

**Module Overview**: 
```text
Alert Engine Service - Phase 3

Core service for evaluating alert rules and triggering notifications.
Runs every minute to check all active rules against current metrics.

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `alert_engine` = `AlertEngine()`

## Dependencies & Imports
sqlite3, json, asyncio, datetime.datetime, datetime.timedelta, typing.Dict, typing.List, typing.Any, typing.Optional, dataclasses.dataclass, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker, src.services.notifications.notification_service, src.utils.json_utils.safe_json_loads

## Feature Class: `AlertRule`
**Description:**
```text
Data class for alert rule configuration
```

### Method: `conditions`
**Parameters:** `self`
**Variables Used:** `parsed`
**Implementation:**
```python
@property
def conditions(self):
    parsed = safe_json_loads(self.condition_json, default=[])
    if isinstance(parsed, str):
        parsed = safe_json_loads(parsed, default=[])
    if not isinstance(parsed, list):
        if isinstance(parsed, dict):
            return [parsed]
        return []
    return parsed
```

### Method: `logic`
**Parameters:** `self`
**Implementation:**
```python
@property
def logic(self):
    return safe_json_loads(self.condition_logic, default=None) if self.condition_logic else None
```

### Method: `actions`
**Parameters:** `self`
**Implementation:**
```python
@property
def actions(self):
    return safe_json_loads(self.actions_json, default={})
```

---

## Feature Class: `AlertTrigger`
**Description:**
```text
Data class for triggered alert
```

---

## Feature Class: `AlertEngine`
**Description:**
```text
Main alert evaluation engine
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.db_path = usage_tracker.db_path
    self.cooldown_cache = {}
```

### Method: `start`
**Logic & Purpose:**
```text
Start the alert engine (called from main.py lifespan)
```

**Parameters:** `self`
**Variables Used:** `rules, conn, cursor`
**Implementation:**
```python
async def start(self):
    """Start the alert engine (called from main.py lifespan)"""
    logger.info('🚀 Alert Engine Starting...')
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS alert_rules (\n                    id TEXT PRIMARY KEY,\n                    name TEXT,\n                    description TEXT,\n                    condition_json TEXT,\n                    condition_logic TEXT,\n                    actions_json TEXT,\n                    cooldown_minutes INTEGER,\n                    priority INTEGER,\n                    time_window INTEGER,\n                    is_active INTEGER,\n                    last_triggered TEXT,\n                    trigger_count INTEGER,\n                    created_at TEXT,\n                    created_by TEXT,\n                    muted_until TEXT\n                )')
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS alert_history (\n                    id TEXT PRIMARY KEY,\n                    rule_id TEXT,\n                    rule_name TEXT,\n                    triggered_at TEXT,\n                    severity TEXT,\n                    alert_data_json TEXT,\n                    description TEXT,\n                    resolved INTEGER DEFAULT 0,\n                    acknowledged INTEGER DEFAULT 0\n                )')
        conn.commit()
        conn.close()
        rules = self.get_active_rules()
        logger.info(f'📊 Loaded {len(rules)} active alert rules')
        asyncio.create_task(self.evaluation_loop())
        logger.info('✅ Alert Engine Started')
    except Exception as e:
        logger.error(f'❌ Alert Engine failed to start: {e}')
        raise
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop the alert engine
```

**Parameters:** `self`
**Implementation:**
```python
async def stop(self):
    """Stop the alert engine"""
    logger.info('🛑 Alert Engine Stopping...')
    logger.info('✅ Alert Engine Stopped')
```

### Method: `evaluation_loop`
**Logic & Purpose:**
```text
Main evaluation loop - runs every 60 seconds
```

**Parameters:** `self`
**Implementation:**
```python
async def evaluation_loop(self):
    """Main evaluation loop - runs every 60 seconds"""
    while True:
        try:
            await asyncio.sleep(60)
            await self.evaluate_all_rules()
        except Exception as e:
            logger.error(f'Error in alert evaluation loop: {e}')
```

### Method: `get_active_rules`
**Logic & Purpose:**
```text
Retrieve all active alert rules from database
```

**Parameters:** `self`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_active_rules(self) -> List[AlertRule]:
    """Retrieve all active alert rules from database"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("\n            SELECT \n                id, name, description, condition_json, \n                COALESCE(condition_logic, '') as condition_logic,\n                actions_json, \n                COALESCE(cooldown_minutes, 5) as cooldown_minutes,\n                CASE \n                    WHEN priority = 'critical' THEN 0\n                    WHEN priority = 'high' THEN 1\n                    WHEN priority = 'medium' THEN 2\n                    WHEN priority = 'low' THEN 3\n                    ELSE CAST(COALESCE(priority, 2) AS INTEGER)\n                END as priority,\n                COALESCE(time_window, 5) as time_window,\n                COALESCE(is_active, 1) as is_active,\n                last_triggered,\n                COALESCE(trigger_count, 0) as trigger_count,\n                COALESCE(created_at, '') as created_at,\n                COALESCE(created_by, 'system') as created_by\n            FROM alert_rules\n            WHERE COALESCE(is_active, 1) = 1\n            ORDER BY priority ASC\n        ")
    rows = cursor.fetchall()
    conn.close()
    return [AlertRule(**dict(row)) for row in rows]
```

### Method: `evaluate_all_rules`
**Logic & Purpose:**
```text
Evaluate all active rules
```

**Parameters:** `self`
**Variables Used:** `rules`
**Implementation:**
```python
async def evaluate_all_rules(self):
    """Evaluate all active rules"""
    rules = self.get_active_rules()
    if not rules:
        return
    logger.info(f'Evaluating {len(rules)} active alert rules...')
    for rule in rules:
        try:
            await self.evaluate_rule(rule)
        except Exception as e:
            logger.error(f'Error evaluating rule {rule.id}: {e}')
```

### Method: `evaluate_rule`
**Logic & Purpose:**
```text
Evaluate a single alert rule
```

**Parameters:** `self, rule`
**Variables Used:** `current_metrics`
**Implementation:**
```python
async def evaluate_rule(self, rule: AlertRule):
    """Evaluate a single alert rule"""
    if not self.check_cooldown(rule):
        return
    current_metrics = await self.get_current_metrics(rule.time_window)
    triggered, alert_data = self.check_conditions(rule, current_metrics)
    if triggered:
        if self.recently_triggered(rule):
            return
        await self.trigger_alert(rule, alert_data)
        self.update_last_triggered(rule)
```

### Method: `check_cooldown`
**Logic & Purpose:**
```text
Check if rule is in cooldown period
```

**Parameters:** `self, rule`
**Variables Used:** `now, cooldown_delta, last_trigger`
**Implementation:**
```python
def check_cooldown(self, rule: AlertRule) -> bool:
    """Check if rule is in cooldown period"""
    if rule.last_triggered is None:
        return True
    last_trigger = datetime.fromisoformat(rule.last_triggered)
    cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
    now = datetime.utcnow()
    return now - last_trigger > cooldown_delta
```

### Method: `recently_triggered`
**Logic & Purpose:**
```text
Check if rule triggered within last N minutes
```

**Parameters:** `self, rule, window_minutes`
**Variables Used:** `window_delta, now, last_trigger`
**Implementation:**
```python
def recently_triggered(self, rule: AlertRule, window_minutes: int=5) -> bool:
    """Check if rule triggered within last N minutes"""
    if rule.last_triggered is None:
        return False
    last_trigger = datetime.fromisoformat(rule.last_triggered)
    window_delta = timedelta(minutes=window_minutes)
    now = datetime.utcnow()
    return now - last_trigger < window_delta
```

### Method: `get_current_metrics`
**Logic & Purpose:**
```text
Get current metrics for the specified time window
```

**Parameters:** `self, time_window`
**Variables Used:** `cursor, total_cost, yesterday_start, cost_change_percent, time_condition, yesterday_cost, cost_per_token, error_rate, errors, yesterday_end, yesterday_row, total_tokens, conn, total_requests, row`
**Implementation:**
```python
async def get_current_metrics(self, time_window: int) -> Dict[str, Any]:
    """Get current metrics for the specified time window"""
    if not usage_tracker.enabled:
        return {}
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    time_condition = datetime.utcnow() - timedelta(minutes=time_window)
    cursor = conn.execute("\n            SELECT\n                COUNT(*) as total_requests,\n                SUM(total_tokens) as total_tokens,\n                SUM(estimated_cost) as total_cost,\n                AVG(duration_ms) as avg_latency,\n                AVG(estimated_cost) as avg_cost_per_request,\n                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors\n            FROM api_requests\n            WHERE timestamp >= ?\n        ", (time_condition.isoformat(),))
    row = cursor.fetchone()
    total_requests = row['total_requests'] or 0
    errors = row['errors'] or 0
    total_cost = row['total_cost'] or 0
    total_tokens = row['total_tokens'] or 0
    yesterday_start = datetime.utcnow() - timedelta(days=1)
    yesterday_end = yesterday_start + timedelta(days=1)
    cursor.execute('\n            SELECT SUM(estimated_cost) as yesterday_cost\n            FROM api_requests\n            WHERE timestamp >= ? AND timestamp < ?\n        ', (yesterday_start.isoformat(), yesterday_end.isoformat()))
    yesterday_row = cursor.fetchone()
    yesterday_cost = yesterday_row['yesterday_cost'] or 0
    conn.close()
    cost_change_percent = 0
    if yesterday_cost > 0:
        cost_change_percent = (total_cost - yesterday_cost) / yesterday_cost * 100
    error_rate = errors / total_requests * 100 if total_requests > 0 else 0
    cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
    return {'total_requests': total_requests, 'total_tokens': total_tokens, 'total_cost': total_cost, 'avg_latency': row['avg_latency'] or 0, 'avg_cost_per_request': row['avg_cost_per_request'] or 0, 'errors': errors, 'error_rate': error_rate, 'cost_per_token': cost_per_token, 'cost_change_percent': cost_change_percent, 'time_window_minutes': time_window, 'evaluated_at': datetime.utcnow().isoformat()}
```

### Method: `check_conditions`
**Logic & Purpose:**
```text
Check if alert conditions are met.
Supports complex logic: AND, OR, nested conditions
```

**Parameters:** `self, rule, metrics`
**Variables Used:** `logic, conditions`
**Implementation:**
```python
def check_conditions(self, rule: AlertRule, metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """
        Check if alert conditions are met.
        Supports complex logic: AND, OR, nested conditions
        """
    if not metrics:
        return (False, {})
    logic = rule.logic
    if not logic:
        conditions = rule.conditions
        if isinstance(conditions, str):
            conditions = safe_json_loads(conditions, default=[])
            if not conditions:
                logger.warning(f'Rule {rule.id}: conditions is invalid JSON string')
                return (False, {})
        if not isinstance(conditions, list):
            logger.warning(f'Rule {rule.id}: conditions is not a list: {type(conditions)}')
            return (False, {})
        return self.evaluate_simple_condition(conditions, metrics)
    return self.evaluate_complex_logic(logic, metrics)
```

### Method: `evaluate_simple_condition`
**Logic & Purpose:**
```text
Evaluate simple list of conditions (all must be true)
```

**Parameters:** `self, conditions, metrics`
**Variables Used:** `test_value, results, match, all_met, alert_data, value, matched_conditions, metric, field, operator, threshold, compare_value`
**Implementation:**
```python
def evaluate_simple_condition(self, conditions: List[Dict], metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """Evaluate simple list of conditions (all must be true)"""
    results = []
    matched_conditions = []
    for condition in conditions:
        if not isinstance(condition, dict):
            continue
        field = condition.get('field')
        metric = condition.get('metric')
        operator = condition.get('operator')
        threshold = condition.get('threshold')
        value = condition.get('value')
        if metric:
            compare_value = metrics.get(metric)
            if compare_value is None:
                continue
            test_value = threshold
        elif field:
            compare_value = metrics.get(field)
            test_value = value
        else:
            continue
        match = self.compare_values(compare_value, operator, test_value)
        results.append(match)
        if match:
            matched_conditions.append({'metric': metric, 'field': field, 'operator': operator, 'value': test_value, 'actual': compare_value})
    all_met = len(results) > 0 and all(results)
    alert_data = {'triggered_conditions': matched_conditions, 'all_metrics': metrics, 'rule_type': 'simple'}
    return (all_met, alert_data)
```

### Method: `evaluate_complex_logic`
**Logic & Purpose:**
```text
Evaluate complex logic with AND/OR and nesting
```

**Parameters:** `self, logic, metrics`
**Variables Used:** `test_value, results, conditions, compare_value, match, value, alert_data, matched_conditions, metric, final_match, field, operator, threshold, logic_type`
**Implementation:**
```python
def evaluate_complex_logic(self, logic: Dict[str, Any], metrics: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """Evaluate complex logic with AND/OR and nesting"""
    logic_type = logic.get('type', 'AND')
    conditions = logic.get('conditions', [])
    results = []
    matched_conditions = []
    for condition in conditions:
        if 'type' in condition:
            nested_match, nested_data = self.evaluate_complex_logic(condition, metrics)
            results.append(nested_match)
            if nested_match:
                matched_conditions.extend(nested_data.get('triggered_conditions', []))
        else:
            if not isinstance(condition, dict):
                continue
            metric = condition.get('metric')
            field = condition.get('field')
            operator = condition.get('operator')
            threshold = condition.get('threshold')
            value = condition.get('value')
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
                matched_conditions.append({'metric': metric, 'field': field, 'operator': operator, 'value': test_value, 'actual': compare_value})
    if logic_type == 'AND':
        final_match = len(results) > 0 and all(results)
    elif logic_type == 'OR':
        final_match = len(results) > 0 and any(results)
    else:
        final_match = False
    alert_data = {'triggered_conditions': matched_conditions, 'all_metrics': metrics, 'rule_type': 'complex', 'logic_type': logic_type}
    return (final_match, alert_data)
```

### Method: `compare_values`
**Logic & Purpose:**
```text
Compare actual value with threshold using operator
```

**Parameters:** `self, actual, operator, threshold`
**Variables Used:** `actual, threshold`
**Implementation:**
```python
def compare_values(self, actual: float, operator: str, threshold: float) -> bool:
    """Compare actual value with threshold using operator"""
    if actual is None:
        return False
    try:
        actual = float(actual)
        threshold = float(threshold)
        if operator == '>':
            return actual > threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '>=':
            return actual >= threshold
        elif operator == '<=':
            return actual <= threshold
        elif operator == '=':
            return actual == threshold
        elif operator == '!=':
            return actual != threshold
        else:
            return False
    except (ValueError, TypeError):
        return False
```

### Method: `trigger_alert`
**Logic & Purpose:**
```text
Trigger an alert and send notifications
```

**Parameters:** `self, rule, alert_data`
**Variables Used:** `alert_trigger, severity, description, alert_id, severity_map`
**Implementation:**
```python
async def trigger_alert(self, rule: AlertRule, alert_data: Dict[str, Any]):
    """Trigger an alert and send notifications"""
    alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{rule.id}"
    severity_map = {0: 'critical', 1: 'high', 2: 'medium', 3: 'low'}
    severity = severity_map.get(rule.priority, 'medium')
    description = self.generate_alert_description(rule, alert_data)
    alert_trigger = self.log_alert(alert_id, rule, description, severity, alert_data)
    await self.send_notifications(rule, alert_trigger)
    logger.info(f'🔔 Alert triggered: {rule.name} ({severity})')
```

### Method: `generate_alert_description`
**Logic & Purpose:**
```text
Generate human-readable alert description
```

**Parameters:** `self, rule, alert_data`
**Variables Used:** `actual, conditions, value, metric, parts, operator`
**Implementation:**
```python
def generate_alert_description(self, rule: AlertRule, alert_data: Dict[str, Any]) -> str:
    """Generate human-readable alert description"""
    conditions = alert_data.get('triggered_conditions', [])
    if not conditions:
        return rule.description
    parts = []
    for cond in conditions:
        metric = cond.get('metric') or cond.get('field', 'unknown')
        operator = cond.get('operator')
        value = cond.get('value')
        actual = cond.get('actual')
        if actual is not None and value is not None:
            parts.append(f'{metric} {operator} {value} (actual: {actual:.2f})')
        else:
            parts.append(f'{metric} {operator} {value}')
    return f"{rule.name}: {' AND '.join(parts)}"
```

### Method: `log_alert`
**Logic & Purpose:**
```text
Log alert to database
```

**Parameters:** `self, alert_id, rule, description, severity, alert_data`
**Variables Used:** `conn, cursor, triggered_at`
**Implementation:**
```python
def log_alert(self, alert_id: str, rule: AlertRule, description: str, severity: str, alert_data: Dict[str, Any]) -> AlertTrigger:
    """Log alert to database"""
    if not usage_tracker.enabled:
        return None
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    triggered_at = datetime.utcnow().isoformat()
    cursor.execute('\n            INSERT INTO alert_history (\n                id, rule_id, rule_name, triggered_at, severity,\n                alert_data_json, description, resolved, acknowledged\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (alert_id, rule.id, rule.name, triggered_at, severity, json.dumps(alert_data), description, 0, 0))
    cursor.execute('\n            UPDATE alert_rules\n            SET last_triggered = ?, trigger_count = trigger_count + 1\n            WHERE id = ?\n        ', (triggered_at, rule.id))
    conn.commit()
    conn.close()
    return AlertTrigger(id=alert_id, rule_id=rule.id, rule_name=rule.name, triggered_at=triggered_at, severity=severity, alert_data=alert_data, description=description)
```

### Method: `send_notifications`
**Logic & Purpose:**
```text
Send notifications through configured channels
```

**Parameters:** `self, rule, alert`
**Variables Used:** `channels, actions`
**Implementation:**
```python
async def send_notifications(self, rule: AlertRule, alert: AlertTrigger):
    """Send notifications through configured channels"""
    actions = rule.actions
    channels = actions.get('channels', [])
    for channel_id in channels:
        try:
            await notification_service.send_alert(alert, channel_id)
        except Exception as e:
            logger.error(f'Failed to send notification to {channel_id}: {e}')
            self.log_notification_failure(alert.id, channel_id, str(e))
```

### Method: `log_notification_failure`
**Logic & Purpose:**
```text
Log failed notification delivery
```

**Parameters:** `self, alert_id, channel_id, error`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def log_notification_failure(self, alert_id: str, channel_id: str, error: str):
    """Log failed notification delivery"""
    if not usage_tracker.enabled:
        return
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('\n            INSERT INTO notification_history (id, alert_id, channel_id, status, error_message, sent_at)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ', (f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}", alert_id, channel_id, 'failed', error, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
```

### Method: `update_last_triggered`
**Logic & Purpose:**
```text
Update rule's last triggered timestamp
```

**Parameters:** `self, rule`
**Variables Used:** `conn, triggered_at`
**Implementation:**
```python
def update_last_triggered(self, rule: AlertRule):
    """Update rule's last triggered timestamp"""
    if not usage_tracker.enabled:
        return
    conn = sqlite3.connect(self.db_path)
    triggered_at = datetime.utcnow().isoformat()
    conn.execute('\n            UPDATE alert_rules\n            SET last_triggered = ?\n            WHERE id = ?\n        ', (triggered_at, rule.id))
    conn.commit()
    conn.close()
    rule.last_triggered = triggered_at
```

### Method: `get_alert_statistics`
**Logic & Purpose:**
```text
Get alert statistics for dashboard
```

**Parameters:** `self, days`
**Variables Used:** `cursor, time_condition, severity_breakdown, conn, row`
**Implementation:**
```python
def get_alert_statistics(self, days: int=30) -> Dict[str, Any]:
    """Get alert statistics for dashboard"""
    if not usage_tracker.enabled:
        return {}
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    time_condition = datetime.utcnow() - timedelta(days=days)
    cursor = conn.execute('\n            SELECT\n                COUNT(*) as total,\n                COUNT(DISTINCT rule_id) as unique_rules,\n                SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved,\n                SUM(CASE WHEN acknowledged = 1 THEN 1 ELSE 0 END) as acknowledged\n            FROM alert_history\n            WHERE triggered_at >= ?\n        ', (time_condition.isoformat(),))
    row = cursor.fetchone()
    cursor.execute('\n            SELECT severity, COUNT(*) as count\n            FROM alert_history\n            WHERE triggered_at >= ?\n            GROUP BY severity\n        ', (time_condition.isoformat(),))
    severity_breakdown = {row['severity']: row['count'] for row in cursor.fetchall()}
    conn.close()
    return {'total': row['total'] or 0, 'unique_rules': row['unique_rules'] or 0, 'resolved': row['resolved'] or 0, 'acknowledged': row['acknowledged'] or 0, 'open': (row['total'] or 0) - (row['resolved'] or 0), 'severity_breakdown': severity_breakdown, 'time_period_days': days}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/user_management.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/user_management.py`

**Module Overview**: 
```text
User Management & RBAC Service - Phase 4

Features:
- User authentication & authorization
- Role-based access control (RBAC)
- API key management
- Session management
- Permissions system

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `ROLE_PERMISSIONS` = `{UserRole.ADMIN: [p.value for p in Permission], UserRole.MODERATOR: [Permission.DASHBOARD_VIEW.value, Permission.DASHBOARD_EDIT.value, Permission.ANALYTICS_VIEW.value, Permission.ANALYTICS_EXPORT.value, Permission.ALERTS_VIEW.value, Permission.ALERTS_CREATE.value, Permission.ALERTS_EDIT.value, Permission.ALERTS_MANAGE.value, Permission.REPORTS_VIEW.value, Permission.REPORTS_CREATE.value, Permission.REPORTS_SCHEDULE.value, Permission.REPORTS_EXPORT.value, Permission.INTEGRATIONS_VIEW.value, Permission.PREDICTIVE_VIEW.value], UserRole.ANALYST: [Permission.DASHBOARD_VIEW.value, Permission.ANALYTICS_VIEW.value, Permission.ANALYTICS_EXPORT.value, Permission.ANALYTICS_CUSTOM.value, Permission.ALERTS_VIEW.value, Permission.REPORTS_VIEW.value, Permission.REPORTS_EXPORT.value, Permission.PREDICTIVE_VIEW.value], UserRole.VIEWER: [Permission.DASHBOARD_VIEW.value, Permission.ANALYTICS_VIEW.value, Permission.ALERTS_VIEW.value, Permission.REPORTS_VIEW.value], UserRole.API_USER: [Permission.ANALYTICS_VIEW.value, Permission.ANALYTICS_CUSTOM.value, Permission.ALERTS_VIEW.value]}`
- `user_service` = `UserManagementService()`

## Dependencies & Imports
sqlite3, hashlib, secrets, uuid, os, datetime.datetime, datetime.timedelta, typing.Dict, typing.List, typing.Optional, typing.Any, dataclasses.dataclass, enum.Enum, src.core.logging.logger, json

## Feature Class: `UserRole`
**Description:**
```text
User roles with permission levels
```

---

## Feature Class: `Permission`
**Description:**
```text
Granular permissions
```

---

## Feature Class: `User`
**Description:**
```text
User model
```

---

## Feature Class: `APIKey`
**Description:**
```text
API Key model
```

---

## Feature Class: `Session`
**Description:**
```text
Session model
```

---

## Feature Class: `UserManagementService`
**Description:**
```text
User management and authentication service
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.db_path = db_path
    self.logger = logger
```

### Method: `initialize`
**Logic & Purpose:**
```text
Initialize user management tables
```

**Parameters:** `self`
**Variables Used:** `conn`
**Implementation:**
```python
def initialize(self):
    """Initialize user management tables"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.execute('\n                CREATE TABLE IF NOT EXISTS users (\n                    id TEXT PRIMARY KEY,\n                    username TEXT UNIQUE NOT NULL,\n                    email TEXT,\n                    password_hash TEXT NOT NULL,\n                    role TEXT NOT NULL,\n                    is_active INTEGER DEFAULT 1,\n                    created_at TEXT NOT NULL,\n                    last_login TEXT\n                )\n            ')
        conn.execute('\n                CREATE TABLE IF NOT EXISTS api_keys (\n                    key TEXT PRIMARY KEY,\n                    user_id TEXT NOT NULL,\n                    name TEXT,\n                    permissions TEXT NOT NULL,\n                    created_at TEXT NOT NULL,\n                    expires_at TEXT,\n                    is_active INTEGER DEFAULT 1,\n                    usage_count INTEGER DEFAULT 0,\n                    FOREIGN KEY (user_id) REFERENCES users(id)\n                )\n            ')
        conn.execute('\n                CREATE TABLE IF NOT EXISTS sessions (\n                    token TEXT PRIMARY KEY,\n                    user_id TEXT NOT NULL,\n                    created_at TEXT NOT NULL,\n                    expires_at TEXT NOT NULL,\n                    is_valid INTEGER DEFAULT 1,\n                    FOREIGN KEY (user_id) REFERENCES users(id)\n                )\n            ')
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to initialize user management: {e}')
```

### Method: `hash_password`
**Logic & Purpose:**
```text
Hash password using SHA-256 with salt
```

**Parameters:** `self, password`
**Variables Used:** `salt`
**Implementation:**
```python
def hash_password(self, password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = 'claude_proxy_salt_v1'
    return hashlib.sha256((password + salt).encode()).hexdigest()
```

### Method: `create_user`
**Logic & Purpose:**
```text
Create a new user
```

**Parameters:** `self, username, password, email, role`
**Variables Used:** `user_id, conn, cursor, password_hash`
**Implementation:**
```python
def create_user(self, username: str, password: str, email: str, role: UserRole=UserRole.VIEWER) -> Optional[str]:
    """Create a new user"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return None
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)
        conn.execute('\n                INSERT INTO users (id, username, email, password_hash, role, created_at)\n                VALUES (?, ?, ?, ?, ?, ?)\n            ', (user_id, username, email, password_hash, role.value, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        self.logger.info(f'Created user: {username} with role: {role.value}')
        return user_id
    except Exception as e:
        self.logger.error(f'Failed to create user: {e}')
        return None
```

### Method: `authenticate`
**Logic & Purpose:**
```text
Authenticate user and return user ID
```

**Parameters:** `self, username, password`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def authenticate(self, username: str, password: str) -> Optional[str]:
    """Authenticate user and return user ID"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT id, password_hash, is_active FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row['is_active']:
            return None
        if row['password_hash'] == self.hash_password(password):
            self.update_last_login(row['id'])
            return row['id']
        return None
    except Exception as e:
        self.logger.error(f'Authentication failed: {e}')
        return None
```

### Method: `update_last_login`
**Logic & Purpose:**
```text
Update last login timestamp
```

**Parameters:** `self, user_id`
**Variables Used:** `conn`
**Implementation:**
```python
def update_last_login(self, user_id: str):
    """Update last login timestamp"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to update last login: {e}')
```

### Method: `create_session`
**Logic & Purpose:**
```text
Create a new session
```

**Parameters:** `self, user_id, duration_hours`
**Variables Used:** `token, conn, expires_at, created_at`
**Implementation:**
```python
def create_session(self, user_id: str, duration_hours: int=24) -> Optional[str]:
    """Create a new session"""
    try:
        conn = sqlite3.connect(self.db_path)
        token = secrets.token_urlsafe(32)
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=duration_hours)
        conn.execute('\n                INSERT INTO sessions (token, user_id, created_at, expires_at)\n                VALUES (?, ?, ?, ?)\n            ', (token, user_id, created_at.isoformat(), expires_at.isoformat()))
        conn.commit()
        conn.close()
        return token
    except Exception as e:
        self.logger.error(f'Failed to create session: {e}')
        return None
```

### Method: `validate_session`
**Logic & Purpose:**
```text
Validate session and return user ID
```

**Parameters:** `self, token`
**Variables Used:** `conn, now, cursor, row`
**Implementation:**
```python
def validate_session(self, token: str) -> Optional[str]:
    """Validate session and return user ID"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        now = datetime.now().isoformat()
        cursor = conn.execute('\n                SELECT user_id, expires_at, is_valid\n                FROM sessions\n                WHERE token = ? AND is_valid = 1 AND expires_at > ?\n            ', (token, now))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['user_id']
        return None
    except Exception as e:
        self.logger.error(f'Session validation failed: {e}')
        return None
```

### Method: `invalidate_session`
**Logic & Purpose:**
```text
Invalidate a session
```

**Parameters:** `self, token`
**Variables Used:** `conn`
**Implementation:**
```python
def invalidate_session(self, token: str):
    """Invalidate a session"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE sessions SET is_valid = 0 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to invalidate session: {e}')
```

### Method: `get_user`
**Logic & Purpose:**
```text
Get user details
```

**Parameters:** `self, user_id`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def get_user(self, user_id: str) -> Optional[User]:
    """Get user details"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return User(id=row['id'], username=row['username'], email=row['email'], role=UserRole(row['role']), is_active=bool(row['is_active']), created_at=row['created_at'], last_login=row['last_login'])
    except Exception as e:
        self.logger.error(f'Failed to get user: {e}')
        return None
```

### Method: `get_user_permissions`
**Logic & Purpose:**
```text
Get all permissions for a user
```

**Parameters:** `self, user_id`
**Variables Used:** `user`
**Implementation:**
```python
def get_user_permissions(self, user_id: str) -> List[str]:
    """Get all permissions for a user"""
    user = self.get_user(user_id)
    if not user:
        return []
    return ROLE_PERMISSIONS.get(user.role, [])
```

### Method: `has_permission`
**Logic & Purpose:**
```text
Check if user has specific permission
```

**Parameters:** `self, user_id, permission`
**Variables Used:** `perms`
**Implementation:**
```python
def has_permission(self, user_id: str, permission: Permission) -> bool:
    """Check if user has specific permission"""
    perms = self.get_user_permissions(user_id)
    return permission.value in perms
```

### Method: `create_api_key`
**Logic & Purpose:**
```text
Create an API key
```

**Parameters:** `self, user_id, name, permissions, expires_days`
**Variables Used:** `expires_at, key, cursor, created_at, conn`
**Implementation:**
```python
def create_api_key(self, user_id: str, name: str, permissions: List[str], expires_days: Optional[int]=None) -> Optional[str]:
    """Create an API key"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return None
        key = f'cp_{secrets.token_urlsafe(32)}'
        created_at = datetime.now()
        expires_at = None
        if expires_days:
            expires_at = (created_at + timedelta(days=expires_days)).isoformat()
        conn.execute('\n                INSERT INTO api_keys (key, user_id, name, permissions, created_at, expires_at)\n                VALUES (?, ?, ?, ?, ?, ?)\n            ', (key, user_id, name, json.dumps(permissions), created_at.isoformat(), expires_at))
        conn.commit()
        conn.close()
        return key
    except Exception as e:
        self.logger.error(f'Failed to create API key: {e}')
        return None
```

### Method: `validate_api_key`
**Logic & Purpose:**
```text
Validate API key and return user info
```

**Parameters:** `self, key`
**Variables Used:** `conn, now, cursor, row`
**Implementation:**
```python
def validate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
    """Validate API key and return user info"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        now = datetime.now().isoformat()
        cursor = conn.execute('\n                SELECT ak.*, u.role, u.username\n                FROM api_keys ak\n                JOIN users u ON ak.user_id = u.id\n                WHERE ak.key = ? AND ak.is_active = 1\n                AND (ak.expires_at IS NULL OR ak.expires_at > ?)\n            ', (key, now))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        self.increment_key_usage(key)
        return {'user_id': row['user_id'], 'username': row['username'], 'role': row['role'], 'permissions': json.loads(row['permissions']), 'name': row['name']}
    except Exception as e:
        self.logger.error(f'API key validation failed: {e}')
        return None
```

### Method: `increment_key_usage`
**Logic & Purpose:**
```text
Increment API key usage count
```

**Parameters:** `self, key`
**Variables Used:** `conn`
**Implementation:**
```python
def increment_key_usage(self, key: str):
    """Increment API key usage count"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE api_keys SET usage_count = usage_count + 1 WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    except Exception as e:
        self.logger.error(f'Failed to increment key usage: {e}')
```

### Method: `revoke_api_key`
**Logic & Purpose:**
```text
Revoke an API key
```

**Parameters:** `self, key`
**Variables Used:** `conn, cursor, revoked`
**Implementation:**
```python
def revoke_api_key(self, key: str) -> bool:
    """Revoke an API key"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('UPDATE api_keys SET is_active = 0 WHERE key = ?', (key,))
        revoked = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return revoked
    except Exception as e:
        self.logger.error(f'Failed to revoke API key: {e}')
        return False
```

### Method: `get_user_api_keys`
**Logic & Purpose:**
```text
Get all API keys for a user
```

**Parameters:** `self, user_id`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_user_api_keys(self, user_id: str) -> List[APIKey]:
    """Get all API keys for a user"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('\n                SELECT * FROM api_keys\n                WHERE user_id = ?\n                ORDER BY created_at DESC\n            ', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [APIKey(key=row['key'], user_id=row['user_id'], name=row['name'], permissions=json.loads(row['permissions']), created_at=row['created_at'], expires_at=row['expires_at'], is_active=bool(row['is_active']), usage_count=row['usage_count']) for row in rows]
    except Exception as e:
        self.logger.error(f'Failed to get API keys: {e}')
        return []
```

### Method: `list_users`
**Logic & Purpose:**
```text
List all users
```

**Parameters:** `self`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def list_users(self) -> List[User]:
    """List all users"""
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [User(id=row['id'], username=row['username'], email=row['email'], role=UserRole(row['role']), is_active=bool(row['is_active']), created_at=row['created_at'], last_login=row['last_login']) for row in rows]
    except Exception as e:
        self.logger.error(f'Failed to list users: {e}')
        return []
```

### Method: `update_user_role`
**Logic & Purpose:**
```text
Update user role
```

**Parameters:** `self, user_id, role`
**Variables Used:** `updated, conn, cursor`
**Implementation:**
```python
def update_user_role(self, user_id: str, role: UserRole) -> bool:
    """Update user role"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('UPDATE users SET role = ? WHERE id = ?', (role.value, user_id))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        self.logger.error(f'Failed to update user role: {e}')
        return False
```

### Method: `deactivate_user`
**Logic & Purpose:**
```text
Deactivate a user
```

**Parameters:** `self, user_id`
**Variables Used:** `deactivated, conn, cursor`
**Implementation:**
```python
def deactivate_user(self, user_id: str) -> bool:
    """Deactivate a user"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        deactivated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deactivated
    except Exception as e:
        self.logger.error(f'Failed to deactivate user: {e}')
        return False
```

---

## Feature Class: `PermissionChecker`
**Description:**
```text
Middleware for checking permissions
```

### Method: `require_permission`
**Logic & Purpose:**
```text
Decorator to require specific permission
```

**Parameters:** `permission`
**Variables Used:** `user_id`
**Implementation:**
```python
@staticmethod
def require_permission(permission: Permission):
    """Decorator to require specific permission"""

    def decorator(func):

        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            if not user_id:
                return {'error': 'Authentication required'}
            if not user_service.has_permission(user_id, permission):
                return {'error': f"Permission '{permission.value}' required"}
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Method: `require_role`
**Logic & Purpose:**
```text
Decorator to require specific role
```

**Parameters:** `role`
**Variables Used:** `user, user_id`
**Implementation:**
```python
@staticmethod
def require_role(role: UserRole):
    """Decorator to require specific role"""

    def decorator(func):

        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id')
            if not user_id:
                return {'error': 'Authentication required'}
            user = user_service.get_user(user_id)
            if not user or user.role.value != role.value:
                return {'error': f"Role '{role.value}' required"}
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Feature Function: `create_default_admin`
**Logic & Purpose:**
```text
Create default admin user if none exists
```

**Parameters:** ``
**Variables Used:** `default_password, cursor, count, user_id, conn`
**Implementation:**
```python
def create_default_admin():
    """Create default admin user if none exists"""
    try:
        user_service.initialize()
        conn = sqlite3.connect(user_service.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        count = cursor.fetchone()[0]
        conn.close()
        if count == 0:
            default_password = os.environ.get('PROXY_DEFAULT_ADMIN_PASSWORD')
            if not default_password:
                default_password = secrets.token_urlsafe(16)
            user_id = user_service.create_user(username='admin', password=default_password, email='admin@localhost', role=UserRole.ADMIN)
            if user_id:
                print(f"✅ Default admin created: username='admin'")
                print(f'   🔑 Password: {default_password}')
                print('⚠️  WARNING: Save this password or change it immediately!')
    except Exception as e:
        print(f'⚠️  Failed to create default admin: {e}')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/antigravity_proto.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/antigravity_proto.py`

**Module Overview**: 
```text
Raw protobuf encoder for Antigravity Connect-RPC without .proto files.

This module provides raw protobuf binary encoding for Connect-RPC calls
to Antigravity's jetski agent service.
```

## Global Presets & Variables
- `ANTIGRAVITY_MODEL_IDS` = `{'gemini-3-pro': 'gemini-3-pro-high', 'gemini-3-flash': 'gemini-3-flash', 'claude-sonnet-4.5': 'claude-sonnet-4-5', 'claude-sonnet-4.5-thinking': 'claude-sonnet-4-5-thinking', 'claude-opus-4.5': 'claude-opus-4-5-thinking', 'gpt-oss-120b': 'gpt-oss-120b-medium'}`

## Dependencies & Imports
struct, typing.Dict, typing.Any, typing.List, typing.Optional, io.BytesIO

## Feature Function: `encode_varint`
**Logic & Purpose:**
```text
Encode a varint (variable-length integer).
```

**Parameters:** `value`
**Variables Used:** `result`
**Implementation:**
```python
def encode_varint(value: int) -> bytes:
    """Encode a varint (variable-length integer)."""
    result = []
    while value > 127:
        result.append(value & 127 | 128)
        value >>= 7
    result.append(value)
    return bytes(result)
```

---

## Feature Function: `encode_field`
**Logic & Purpose:**
```text
Encode a protobuf field with its tag.
```

**Parameters:** `field_number, wire_type, data`
**Variables Used:** `tag`
**Implementation:**
```python
def encode_field(field_number: int, wire_type: int, data: bytes) -> bytes:
    """Encode a protobuf field with its tag."""
    tag = field_number << 3 | wire_type
    return encode_varint(tag) + data
```

---

## Feature Function: `encode_string`
**Logic & Purpose:**
```text
Encode a string field (wire type 2).
```

**Parameters:** `field_number, value`
**Variables Used:** `encoded`
**Implementation:**
```python
def encode_string(field_number: int, value: str) -> bytes:
    """Encode a string field (wire type 2)."""
    encoded = value.encode('utf-8')
    return encode_field(field_number, 2, encode_varint(len(encoded)) + encoded)
```

---

## Feature Function: `encode_bytes_field`
**Logic & Purpose:**
```text
Encode a bytes field (wire type 2).
```

**Parameters:** `field_number, value`
**Implementation:**
```python
def encode_bytes_field(field_number: int, value: bytes) -> bytes:
    """Encode a bytes field (wire type 2)."""
    return encode_field(field_number, 2, encode_varint(len(value)) + value)
```

---

## Feature Function: `encode_int32`
**Logic & Purpose:**
```text
Encode an int32 field (wire type 0).
```

**Parameters:** `field_number, value`
**Implementation:**
```python
def encode_int32(field_number: int, value: int) -> bytes:
    """Encode an int32 field (wire type 0)."""
    return encode_field(field_number, 0, encode_varint(value))
```

---

## Feature Function: `encode_bool`
**Logic & Purpose:**
```text
Encode a bool field (wire type 0).
```

**Parameters:** `field_number, value`
**Implementation:**
```python
def encode_bool(field_number: int, value: bool) -> bytes:
    """Encode a bool field (wire type 0)."""
    return encode_field(field_number, 0, encode_varint(1 if value else 0))
```

---

## Feature Function: `encode_embedded_message`
**Logic & Purpose:**
```text
Encode an embedded message field (wire type 2).
```

**Parameters:** `field_number, message_bytes`
**Implementation:**
```python
def encode_embedded_message(field_number: int, message_bytes: bytes) -> bytes:
    """Encode an embedded message field (wire type 2)."""
    return encode_field(field_number, 2, encode_varint(len(message_bytes)) + message_bytes)
```

---

## Feature Class: `ClientMetadata`
**Description:**
```text
Encodes ClientMetadata protobuf message.

Based on: google.internal.cloud.code.v1internal.ClientMetadata
Fields from JS analysis:
- ide_version (string) = field 1
- ide_name (string) = field 9
- ide_type (enum) = field 10 (guess based on pattern)
```

### Method: `encode`
**Parameters:** `ide_name, ide_version, ide_type`
**Variables Used:** `result`
**Implementation:**
```python
@staticmethod
def encode(ide_name: str='antigravity', ide_version: str='1.0.0', ide_type: int=2) -> bytes:
    result = BytesIO()
    result.write(encode_string(1, ide_version))
    result.write(encode_string(9, ide_name))
    result.write(encode_int32(10, ide_type))
    return result.getvalue()
```

---

## Feature Class: `ChatMessage`
**Description:**
```text
Encodes a chat message for the jetski agent.

This is a best-guess structure based on JS analysis.
Fields likely include: content, role, etc.
```

### Method: `encode`
**Parameters:** `content, role`
**Variables Used:** `result`
**Implementation:**
```python
@staticmethod
def encode(content: str, role: str='user') -> bytes:
    result = BytesIO()
    result.write(encode_string(1, content))
    result.write(encode_string(2, role))
    return result.getvalue()
```

---

## Feature Class: `CascadeRequest`
**Description:**
```text
Encodes a CascadeRequest protobuf message.

Based on analysis of exa.jetski_cortex_pb namespace.
This is the request sent to start/continue a cascade (agent) conversation.
```

### Method: `encode`
**Parameters:** `message, model_id, metadata, project`
**Variables Used:** `result`
**Implementation:**
```python
@staticmethod
def encode(message: str, model_id: str='gemini-3-pro-high', metadata: Optional[bytes]=None, project: str='') -> bytes:
    result = BytesIO()
    result.write(encode_string(1, message))
    result.write(encode_string(2, model_id))
    if metadata:
        result.write(encode_embedded_message(3, metadata))
    else:
        result.write(encode_embedded_message(3, ClientMetadata.encode()))
    if project:
        result.write(encode_string(4, project))
    return result.getvalue()
```

---

## Feature Function: `encode_connect_rpc_message`
**Logic & Purpose:**
```text
Encode a message for Connect-RPC binary format.

Connect-RPC uses a 5-byte envelope:
- 1 byte: flags (0 = uncompressed)
- 4 bytes: message length (big-endian)
```

**Parameters:** `message_bytes`
**Variables Used:** `envelope, length, flags`
**Implementation:**
```python
def encode_connect_rpc_message(message_bytes: bytes) -> bytes:
    """Encode a message for Connect-RPC binary format.
    
    Connect-RPC uses a 5-byte envelope:
    - 1 byte: flags (0 = uncompressed)
    - 4 bytes: message length (big-endian)
    """
    flags = 0
    length = len(message_bytes)
    envelope = struct.pack('>BI', flags, length)
    return envelope + message_bytes
```

---

## Feature Function: `decode_connect_rpc_envelope`
**Logic & Purpose:**
```text
Decode a Connect-RPC envelope.

Returns: (flags, message_bytes)
```

**Parameters:** `data`
**Variables Used:** `message, length, flags`
**Implementation:**
```python
def decode_connect_rpc_envelope(data: bytes) -> tuple:
    """Decode a Connect-RPC envelope.
    
    Returns: (flags, message_bytes)
    """
    if len(data) < 5:
        return (None, None)
    flags = data[0]
    length = struct.unpack('>I', data[1:5])[0]
    message = data[5:5 + length]
    return (flags, message)
```

---

## Feature Function: `get_model_id`
**Logic & Purpose:**
```text
Convert friendly model name to Antigravity API model ID.
```

**Parameters:** `friendly_name`
**Variables Used:** `name_lower`
**Implementation:**
```python
def get_model_id(friendly_name: str) -> str:
    """Convert friendly model name to Antigravity API model ID."""
    name_lower = friendly_name.lower().replace('antigravity/', '')
    return ANTIGRAVITY_MODEL_IDS.get(name_lower, name_lower)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/antigravity.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/antigravity.py`

**Module Overview**: 
```text
Antigravity token extraction and API client.

This module provides functionality to extract OAuth tokens from the
local Antigravity IDE installation and make API calls using those credentials.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `VIBEPROXY_BASE_URL` = `os.getenv('VIBEPROXY_URL', 'http://127.0.0.1:1337')`
- `VIBEPROXY_HEALTH_TIMEOUT` = `float(os.getenv('VIBEPROXY_HEALTH_TIMEOUT', '2.0'))`

## Dependencies & Imports
json, logging, os, sqlite3, time, pathlib.Path, typing.Optional, typing.Dict, typing.Any, typing.Tuple, httpx

## Feature Function: `check_vibeproxy_health`
**Logic & Purpose:**
```text
Check if VibeProxy is available and responding.

Args:
    force_refresh: Bypass cache and check immediately

Returns:
    Tuple of (is_available, error_message)
```

**Parameters:** `force_refresh`
**Variables Used:** `now, error_msg, response, cache_age, is_available`
**Implementation:**
```python
def check_vibeproxy_health(force_refresh: bool=False) -> Tuple[bool, Optional[str]]:
    """
    Check if VibeProxy is available and responding.

    Args:
        force_refresh: Bypass cache and check immediately

    Returns:
        Tuple of (is_available, error_message)
    """
    global _vibeproxy_health_cache
    now = time.time()
    cache_age = now - _vibeproxy_health_cache['last_check']
    if not force_refresh and cache_age < _vibeproxy_health_cache['cache_ttl']:
        if _vibeproxy_health_cache['available'] is not None:
            return (_vibeproxy_health_cache['available'], None)
    try:
        response = httpx.get(f'{VIBEPROXY_BASE_URL}/health', timeout=VIBEPROXY_HEALTH_TIMEOUT)
        if response.status_code == 404:
            response = httpx.get(f'{VIBEPROXY_BASE_URL}/v1/models', timeout=VIBEPROXY_HEALTH_TIMEOUT, headers={'Authorization': f"Bearer {os.getenv('BIG_API_KEY', 'pass')}"})
        is_available = response.status_code == 200
        _vibeproxy_health_cache['available'] = is_available
        _vibeproxy_health_cache['last_check'] = now
        if is_available:
            logger.debug(f'VibeProxy health check passed')
        else:
            logger.warning(f'VibeProxy health check failed: status {response.status_code}')
        return (is_available, None if is_available else f'Status {response.status_code}')
    except httpx.ConnectError as e:
        _vibeproxy_health_cache['available'] = False
        _vibeproxy_health_cache['last_check'] = now
        error_msg = 'VibeProxy not reachable (connection refused)'
        logger.warning(f'{error_msg}: {e}')
        return (False, error_msg)
    except httpx.TimeoutException:
        _vibeproxy_health_cache['available'] = False
        _vibeproxy_health_cache['last_check'] = now
        error_msg = f'VibeProxy health check timed out ({VIBEPROXY_HEALTH_TIMEOUT}s)'
        logger.warning(error_msg)
        return (False, error_msg)
    except Exception as e:
        _vibeproxy_health_cache['available'] = False
        _vibeproxy_health_cache['last_check'] = now
        error_msg = f'VibeProxy health check error: {type(e).__name__}'
        logger.error(f'{error_msg}: {e}')
        return (False, error_msg)
```

---

## Feature Function: `is_vibeproxy_available`
**Logic & Purpose:**
```text
Quick check if VibeProxy is available (uses cache).
```

**Parameters:** ``
**Implementation:**
```python
def is_vibeproxy_available() -> bool:
    """Quick check if VibeProxy is available (uses cache)."""
    available, _ = check_vibeproxy_health()
    return available
```

---

## Feature Function: `clear_vibeproxy_health_cache`
**Logic & Purpose:**
```text
Clear the health check cache to force fresh check.
```

**Parameters:** ``
**Implementation:**
```python
def clear_vibeproxy_health_cache():
    """Clear the health check cache to force fresh check."""
    global _vibeproxy_health_cache
    _vibeproxy_health_cache['available'] = None
    _vibeproxy_health_cache['last_check'] = 0
```

---

## Feature Class: `AntigravityAuth`
**Description:**
```text
Extract and manage Antigravity OAuth tokens.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self._cached_token: Optional[str] = None
    self._auth_data: Optional[Dict[str, Any]] = None
```

### Method: `get_auth_data`
**Logic & Purpose:**
```text
Get full auth data from Antigravity's local database.

Args:
    force_refresh: If True, bypass cache and fetch fresh data from database

Returns:
    Dictionary with name, email, apiKey, or None if not available
```

**Parameters:** `self, force_refresh`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def get_auth_data(self, force_refresh: bool=False) -> Optional[Dict[str, Any]]:
    """
        Get full auth data from Antigravity's local database.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data from database
        
        Returns:
            Dictionary with name, email, apiKey, or None if not available
        """
    if self._auth_data and (not force_refresh):
        logger.debug(f'[AntigravityAuth] Using CACHED auth data')
        return self._auth_data
    if not self.DB_PATH.exists():
        print(f'ERROR [AntigravityAuth]: Database not found at {self.DB_PATH}')
        return None
    logger.debug(f'[AntigravityAuth] Accessing SQLite database at {self.DB_PATH}')
    try:
        conn = sqlite3.connect(str(self.DB_PATH))
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM ItemTable WHERE key=?;', (self.AUTH_KEY,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self._auth_data = json.loads(row[0])
            logger.debug(f'[AntigravityAuth] Successfully loaded auth data from database')
            return self._auth_data
        else:
            print(f"ERROR [AntigravityAuth]: No row found for key '{self.AUTH_KEY}'")
    except Exception as e:
        print(f'ERROR [AntigravityAuth]: Database access failed - {type(e).__name__}: {str(e)}')
        pass
    return None
```

### Method: `get_token`
**Logic & Purpose:**
```text
Get OAuth Bearer token for Antigravity API.

Args:
    force_refresh: If True, bypass cache and fetch fresh token from database

Returns:
    Bearer token string or None if not available
```

**Parameters:** `self, force_refresh`
**Variables Used:** `new_token, auth_data`
**Implementation:**
```python
def get_token(self, force_refresh: bool=False) -> Optional[str]:
    """
        Get OAuth Bearer token for Antigravity API.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh token from database
        
        Returns:
            Bearer token string or None if not available
        """
    if self._cached_token and (not force_refresh):
        logger.debug(f'[AntigravityAuth] Using CACHED token (first 20 chars): {self._cached_token[:20]}...')
        return self._cached_token
    logger.debug(f'[AntigravityAuth] Fetching FRESH token from database (force_refresh={force_refresh})')
    auth_data = self.get_auth_data(force_refresh=force_refresh)
    if auth_data:
        new_token = auth_data.get('apiKey')
        if new_token:
            if self._cached_token and self._cached_token != new_token:
                print(f'WARNING [AntigravityAuth]: Token CHANGED! Old: {self._cached_token[:20]}... New: {new_token[:20]}...')
            else:
                logger.debug(f'[AntigravityAuth] Token retrieved successfully (first 20 chars): {new_token[:20]}...')
            self._cached_token = new_token
            return self._cached_token
        else:
            print(f'ERROR [AntigravityAuth]: Auth data found but apiKey is missing!')
    else:
        print(f'ERROR [AntigravityAuth]: No auth data found in database at {self.DB_PATH}')
    return None
```

### Method: `get_email`
**Logic & Purpose:**
```text
Get user email.
```

**Parameters:** `self`
**Variables Used:** `auth_data`
**Implementation:**
```python
def get_email(self) -> Optional[str]:
    """Get user email."""
    auth_data = self.get_auth_data()
    return auth_data.get('email') if auth_data else None
```

### Method: `get_name`
**Logic & Purpose:**
```text
Get user name.
```

**Parameters:** `self`
**Variables Used:** `auth_data`
**Implementation:**
```python
def get_name(self) -> Optional[str]:
    """Get user name."""
    auth_data = self.get_auth_data()
    return auth_data.get('name') if auth_data else None
```

### Method: `is_available`
**Logic & Purpose:**
```text
Check if Antigravity auth is available.
```

**Parameters:** `self`
**Implementation:**
```python
def is_available(self) -> bool:
    """Check if Antigravity auth is available."""
    return self.get_token() is not None
```

### Method: `clear_cache`
**Logic & Purpose:**
```text
Clear cached token (refresh on next call).
```

**Parameters:** `self`
**Implementation:**
```python
def clear_cache(self) -> None:
    """Clear cached token (refresh on next call)."""
    self._cached_token = None
    self._auth_data = None
```

---

## Feature Function: `get_antigravity_auth`
**Logic & Purpose:**
```text
Get or create the Antigravity auth singleton.
```

**Parameters:** ``
**Variables Used:** `_auth_instance`
**Implementation:**
```python
def get_antigravity_auth() -> AntigravityAuth:
    """Get or create the Antigravity auth singleton."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AntigravityAuth()
    return _auth_instance
```

---

## Feature Function: `get_antigravity_token`
**Logic & Purpose:**
```text
Convenience function to get Antigravity OAuth token.
```

**Parameters:** ``
**Implementation:**
```python
def get_antigravity_token() -> Optional[str]:
    """Convenience function to get Antigravity OAuth token."""
    return get_antigravity_auth().get_token()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/notifications.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/notifications.py`

**Module Overview**: 
```text
Notification Service - Phase 3

Handles multi-channel alert delivery: Email, Slack, Webhook, In-App
Supports retries, rate limiting, and delivery tracking.

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `notification_service` = `NotificationService()`

## Dependencies & Imports
smtplib, json, asyncio, aiohttp, datetime.datetime, typing.Dict, typing.Any, typing.Optional, email.mime.text.MIMEText, email.mime.multipart.MIMEMultipart, sqlite3, src.core.logging.logger, src.core.config.config, src.services.usage.usage_tracker.usage_tracker

## Feature Class: `NotificationService`
**Description:**
```text
Multi-channel notification delivery service
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.db_path = usage_tracker.db_path
    self.rate_limiter = {}
    self.session = None
```

### Method: `initialize`
**Logic & Purpose:**
```text
Initialize aiohttp session
```

**Parameters:** `self`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
async def initialize(self):
    """Initialize aiohttp session"""
    self.session = aiohttp.ClientSession()
    logger.info('🚀Initializing notification channels table if not exists...')
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS notification_channels (\n                    id TEXT PRIMARY KEY,\n                    type TEXT,\n                    name TEXT,\n                    config TEXT,\n                    is_enabled INTEGER,\n                    last_used TEXT\n                )')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f'Failed to migrate 001 to perform table upgrades. Reason: {e}')
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS notification_channels (\n                    id TEXT PRIMARY KEY,\n                    type TEXT,\n                    name TEXT,\n                    config TEXT,\n                    is_enabled INTEGER,\n                    last_used TEXT\n                )')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f'Failed to initialize notification service: {e}')
```

### Method: `close`
**Logic & Purpose:**
```text
Close aiohttp session
```

**Parameters:** `self`
**Implementation:**
```python
async def close(self):
    """Close aiohttp session"""
    if self.session:
        await self.session.close()
```

### Method: `send_alert`
**Logic & Purpose:**
```text
Send alert through specified channel

Args:
    alert: AlertTrigger object
    channel_id: ID of notification channel
```

**Parameters:** `self, alert, channel_id`
**Variables Used:** `config_data, channel_type, channel, success`
**Implementation:**
```python
async def send_alert(self, alert, channel_id: str):
    """
        Send alert through specified channel

        Args:
            alert: AlertTrigger object
            channel_id: ID of notification channel
        """
    channel = self.get_channel(channel_id)
    if not channel:
        logger.error(f'Channel {channel_id} not found')
        return False
    if not channel['is_enabled']:
        logger.info(f'Channel {channel_id} is disabled')
        return False
    if not self.check_rate_limit(channel_id):
        logger.warning(f'Rate limit hit for channel {channel_id}')
        return False
    channel_type = channel['type']
    config_data = json.loads(channel['config'])
    try:
        if channel_type == 'email':
            success = await self.send_email(alert, config_data)
        elif channel_type == 'slack':
            success = await self.send_slack(alert, config_data)
        elif channel_type == 'in_app':
            success = await self.send_in_app(alert, config_data)
        elif channel_type == 'webhook':
            success = await self.send_webhook(alert, config_data)
        elif channel_type == 'pagerduty':
            success = await self.send_pagerduty(alert, config_data)
        else:
            logger.error(f'Unknown channel type: {channel_type}')
            success = False
        self.log_delivery(alert.id, channel_id, success)
        if success:
            self.update_channel_last_used(channel_id)
            logger.info(f'✅ Notification sent via {channel_type}: {channel_id}')
        else:
            logger.error(f'❌ Notification failed via {channel_type}: {channel_id}')
        return success
    except Exception as e:
        logger.error(f'Exception sending notification: {e}')
        self.log_delivery(alert.id, channel_id, False, str(e))
        return False
```

### Method: `get_channel`
**Logic & Purpose:**
```text
Get notification channel configuration
```

**Parameters:** `self, channel_id`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
    """Get notification channel configuration"""
    if not usage_tracker.enabled:
        return None
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('SELECT * FROM notification_channels WHERE id = ?', (channel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
```

### Method: `check_rate_limit`
**Logic & Purpose:**
```text
Rate limit notifications to prevent spam

Args:
    channel_id: Channel to check
    min_interval: Minimum seconds between notifications

Returns:
    True if allowed, False if rate limited
```

**Parameters:** `self, channel_id, min_interval`
**Variables Used:** `now, last_sent`
**Implementation:**
```python
def check_rate_limit(self, channel_id: str, min_interval: int=60) -> bool:
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
    if now - last_sent < min_interval:
        return False
    self.rate_limiter[channel_id] = now
    return True
```

### Method: `get_all_channels`
**Logic & Purpose:**
```text
Get all notification channels
```

**Parameters:** `self`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_all_channels(self) -> list:
    """Get all notification channels"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('SELECT * FROM notification_channels')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

### Method: `send_email`
**Logic & Purpose:**
```text
Send email notification
```

**Parameters:** `self, alert, config`
**Variables Used:** `smtp_pass, smtp_server, smtp_port, smtp_user, html_content, text_part, html_part, msg, server, subject`
**Implementation:**
```python
async def send_email(self, alert, config: Dict[str, Any]) -> bool:
    """Send email notification"""
    if not config.get('to'):
        logger.error('No email recipient specified')
        return False
    smtp_server = config.get('smtp_server') or config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(config.get('smtp_port') or config.get('SMTP_PORT', 587))
    smtp_user = config.get('smtp_user') or config.get('SMTP_USER')
    smtp_pass = config.get('smtp_password') or config.get('SMTP_PASSWORD')
    if not smtp_user or not smtp_pass:
        logger.error('SMTP credentials not configured')
        return False
    subject = f"{config.get('subject_prefix', '[Alert]')} {alert.rule_name}"
    html_content = self.generate_email_html(alert)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = config['to']
    text_part = MIMEText(self.generate_email_text(alert), 'plain')
    msg.attach(text_part)
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f'Email send failed: {e}')
        return False
```

### Method: `generate_email_html`
**Logic & Purpose:**
```text
Generate HTML email template
```

**Parameters:** `self, alert`
**Variables Used:** `severity_colors, actual, value, metric, color, conditions_html`
**Implementation:**
```python
def generate_email_html(self, alert) -> str:
    """Generate HTML email template"""
    severity_colors = {'critical': '#dc2626', 'high': '#f97316', 'medium': '#eab308', 'low': '#3b82f6'}
    color = severity_colors.get(alert.severity, '#6b7280')
    conditions_html = ''
    if alert.alert_data and 'triggered_conditions' in alert.alert_data:
        for cond in alert.alert_data['triggered_conditions']:
            metric = cond.get('metric') or cond.get('field', 'unknown')
            actual = cond.get('actual')
            value = cond.get('value')
            conditions_html += f'<li><strong>{metric}</strong>: {actual} vs threshold {value}</li>'
    return f'\n        <html>\n        <head>\n            <style>\n                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}\n                .header {{ background: {color}; color: white; padding: 20px; }}\n                .content {{ padding: 20px; }}\n                .details {{ background: #f3f4f6; padding: 15px; border-left: 4px solid {color}; }}\n                .footer {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}\n            </style>\n        </head>\n        <body>\n            <div class="header">\n                <h1>🚨 {alert.rule_name}</h1>\n                <p>Severity: {alert.severity.upper()} | {alert.triggered_at}</p>\n            </div>\n            <div class="content">\n                <p><strong>Description:</strong> {alert.description}</p>\n                <div class="details">\n                    <h3>Triggered Conditions:</h3>\n                    <ul>{conditions_html}</ul>\n                </div>\n                <p><strong>Alert ID:</strong> {alert.id}</p>\n            </div>\n            <div class="footer">\n                <p>This is an automated alert from Claude Proxy Analytics.</p>\n                <p>Rule ID: {alert.rule_id}</p>\n            </div>\n        </body>\n        </html>\n        '
```

### Method: `generate_email_text`
**Logic & Purpose:**
```text
Generate plain text email
```

**Parameters:** `self, alert`
**Variables Used:** `text`
**Implementation:**
```python
def generate_email_text(self, alert) -> str:
    """Generate plain text email"""
    text = f'\n🚨 ALERT: {alert.rule_name}\n\nSeverity: {alert.severity.upper()}\nTime: {alert.triggered_at}\nDescription: {alert.description}\n\nAlert ID: {alert.id}\nRule ID: {alert.rule_id}\n\nThis is an automated alert from Claude Proxy Analytics.\n        '
    return text.strip()
```

### Method: `send_slack`
**Logic & Purpose:**
```text
Send Slack notification via webhook
```

**Parameters:** `self, alert, config`
**Variables Used:** `severity_colors, message, text, conditions_text, blocks, color, webhook_url`
**Implementation:**
```python
async def send_slack(self, alert, config: Dict[str, Any]) -> bool:
    """Send Slack notification via webhook"""
    webhook_url = config.get('webhook_url')
    if not webhook_url:
        logger.error('Slack webhook URL not configured')
        return False
    severity_colors = {'critical': '#dc2626', 'high': '#f97316', 'medium': '#eab308', 'low': '#3b82f6'}
    color = severity_colors.get(alert.severity, '#6b7280')
    blocks = [{'type': 'header', 'text': {'type': 'plain_text', 'text': f'🚨 {alert.rule_name}'}}, {'type': 'section', 'fields': [{'type': 'mrkdwn', 'text': f'*Severity:*\n{alert.severity.upper()}'}, {'type': 'mrkdwn', 'text': f'*Time:*\n{alert.triggered_at[:19]}'}]}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f'*Description:* {alert.description}'}}]
    if alert.alert_data and 'triggered_conditions' in alert.alert_data:
        conditions_text = '\n'.join([f"• {c.get('metric') or c.get('field')}: {c.get('actual')} (threshold: {c.get('value')})" for c in alert.alert_data['triggered_conditions']])
        blocks.append({'type': 'section', 'text': {'type': 'mrkdwn', 'text': f'*Triggered Conditions:*\n{conditions_text}'}})
    blocks.append({'type': 'context', 'elements': [{'type': 'mrkdwn', 'text': f'Rule ID: {alert.rule_id} | Alert ID: {alert.id}'}]})
    message = {'blocks': blocks, 'color': color}
    try:
        async with self.session.post(webhook_url, json=message) as response:
            if response.status == 200:
                return True
            else:
                text = await response.text()
                logger.error(f'Slack webhook returned {response.status}: {text}')
                return False
    except Exception as e:
        logger.error(f'Slack webhook exception: {e}')
        return False
```

### Method: `send_webhook`
**Logic & Purpose:**
```text
Send custom webhook notification
```

**Parameters:** `self, alert, config`
**Variables Used:** `headers, text, payload, webhook_url`
**Implementation:**
```python
async def send_webhook(self, alert, config: Dict[str, Any]) -> bool:
    """Send custom webhook notification"""
    webhook_url = config.get('url')
    if not webhook_url:
        logger.error('Webhook URL not configured')
        return False
    payload = {'alert_id': alert.id, 'rule_id': alert.rule_id, 'rule_name': alert.rule_name, 'severity': alert.severity, 'triggered_at': alert.triggered_at, 'description': alert.description, 'data': alert.alert_data}
    headers = config.get('headers', {})
    try:
        async with self.session.post(webhook_url, json=payload, headers=headers) as response:
            if response.status in [200, 201]:
                return True
            else:
                text = await response.text()
                logger.error(f'Webhook returned {response.status}: {text}')
                return False
    except Exception as e:
        logger.error(f'Webhook exception: {e}')
        return False
```

### Method: `send_pagerduty`
**Logic & Purpose:**
```text
Send PagerDuty incident
```

**Parameters:** `self, alert, config`
**Variables Used:** `integration_key, text, payload`
**Implementation:**
```python
async def send_pagerduty(self, alert, config: Dict[str, Any]) -> bool:
    """Send PagerDuty incident"""
    integration_key = config.get('integration_key')
    if not integration_key:
        logger.error('PagerDuty integration key not configured')
        return False
    payload = {'routing_key': integration_key, 'event_action': 'trigger', 'dedup_key': alert.id, 'payload': {'summary': alert.description, 'severity': 'critical' if alert.severity == 'critical' else 'error', 'source': 'claude-proxy', 'component': 'alert-engine', 'group': alert.rule_name, 'class': alert.severity, 'custom_details': {'alert_id': alert.id, 'rule_id': alert.rule_id, 'rule_name': alert.rule_name, 'triggered_at': alert.triggered_at, 'data': alert.alert_data}}}
    try:
        async with self.session.post('https://events.pagerduty.com/v2/enqueue', json=payload) as response:
            if response.status == 202:
                return True
            else:
                text = await response.text()
                logger.error(f'PagerDuty returned {response.status}: {text}')
                return False
    except Exception as e:
        logger.error(f'PagerDuty exception: {e}')
        return False
```

### Method: `send_in_app`
**Logic & Purpose:**
```text
Store in-app notification (delivered via WebSocket)
```

**Parameters:** `self, alert, config`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
async def send_in_app(self, alert, config: Dict[str, Any]) -> bool:
    """Store in-app notification (delivered via WebSocket)"""
    if not usage_tracker.enabled:
        return False
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('\n            INSERT INTO notification_history\n            (id, alert_id, channel_id, status, sent_at)\n            VALUES (?, ?, ?, ?, ?)\n        ', (f"inapp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}", alert.id, 'in_app', 'sent', datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    logger.info(f'In-app notification stored: {alert.id}')
    return True
```

### Method: `log_delivery`
**Logic & Purpose:**
```text
Log notification delivery to database
```

**Parameters:** `self, alert_id, channel_id, success, error`
**Variables Used:** `status, conn, cursor`
**Implementation:**
```python
def log_delivery(self, alert_id: str, channel_id: str, success: bool, error: Optional[str]=None):
    """Log notification delivery to database"""
    if not usage_tracker.enabled:
        return
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    status = 'sent' if success else 'failed'
    cursor.execute('\n            INSERT INTO notification_history\n            (id, alert_id, channel_id, status, error_message, sent_at)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ', (f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}", alert_id, channel_id, status, error, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
```

### Method: `update_channel_last_used`
**Logic & Purpose:**
```text
Update channel's last used timestamp
```

**Parameters:** `self, channel_id`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def update_channel_last_used(self, channel_id: str):
    """Update channel's last used timestamp"""
    if not usage_tracker.enabled:
        return
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('\n            UPDATE notification_channels\n            SET last_used = ?\n            WHERE id = ?\n        ', (datetime.utcnow().isoformat(), channel_id))
    conn.commit()
    conn.close()
```

### Method: `get_delivery_history`
**Logic & Purpose:**
```text
Get recent notification delivery history
```

**Parameters:** `self, limit`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_delivery_history(self, limit: int=50) -> list:
    """Get recent notification delivery history"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('\n            SELECT\n                nh.*,\n                c.name as channel_name,\n                c.type as channel_type,\n                ah.rule_name\n            FROM notification_history nh\n            LEFT JOIN notification_channels c ON nh.channel_id = c.id\n            LEFT JOIN alert_history ah ON nh.alert_id = ah.id\n            ORDER BY nh.sent_at DESC\n            LIMIT ?\n        ', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

### Method: `test_notification`
**Logic & Purpose:**
```text
Send test notification to specified channel
```

**Parameters:** `self, channel_id`
**Variables Used:** `success, channel, test_alert`
**Implementation:**
```python
def test_notification(self, channel_id: str) -> tuple[bool, str]:
    """Send test notification to specified channel"""
    channel = self.get_channel(channel_id)
    if not channel:
        return (False, f'Channel {channel_id} not found')
    test_alert = type('AlertTrigger', (), {'id': 'test_alert', 'rule_id': 'test_rule', 'rule_name': 'Test Notification', 'triggered_at': datetime.utcnow().isoformat(), 'severity': 'medium', 'alert_data': {'test': True}, 'description': 'This is a test notification'})()
    success = asyncio.run(self.send_alert(test_alert, channel_id))
    if success:
        return (True, 'Test notification sent successfully')
    else:
        return (False, 'Failed to send test notification')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/report_generator.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/report_generator.py`

**Module Overview**: 
```text
Report Generator Service - Phase 3

Generates professional reports in multiple formats:
- PDF (with charts, tables, branding)
- Excel (XLSX with formatting)
- CSV (export data)
- Scheduled reports

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `report_generator` = `ReportGenerator()`

## Dependencies & Imports
io, json, sqlite3, datetime.datetime, datetime.timedelta, typing.Dict, typing.Any, typing.List, typing.Optional, dataclasses.dataclass, reportlab.lib.colors, reportlab.lib.pagesizes.letter, reportlab.lib.pagesizes.A4, reportlab.lib.styles.getSampleStyleSheet, reportlab.lib.styles.ParagraphStyle, reportlab.lib.units.inch, reportlab.platypus.SimpleDocTemplate, reportlab.platypus.Paragraph, reportlab.platypus.Spacer, reportlab.platypus.Table, reportlab.platypus.TableStyle, reportlab.platypus.Image, reportlab.graphics.shapes.Drawing, reportlab.graphics.charts.linecharts.LineChart, reportlab.graphics.charts.barcharts.VerticalBarChart, reportlab.graphics.widgets.markers.makeMarker, openpyxl.Workbook, openpyxl.styles.Font, openpyxl.styles.PatternFill, openpyxl.styles.Alignment, openpyxl.styles.Border, openpyxl.styles.Side, openpyxl.chart.LineChart, openpyxl.chart.Reference, openpyxl.chart.BarChart, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Class: `ReportTemplate`
**Description:**
```text
Report template configuration
```

---

## Feature Class: `ReportGenerator`
**Description:**
```text
Main report generation service
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.db_path = usage_tracker.db_path
```

### Method: `get_templates`
**Logic & Purpose:**
```text
Get all report templates
```

**Parameters:** `self`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_templates(self) -> List[ReportTemplate]:
    """Get all report templates"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('SELECT * FROM report_templates ORDER BY name')
    rows = cursor.fetchall()
    conn.close()
    return [ReportTemplate(id=row['id'], name=row['name'], description=row['description'], config=json.loads(row['template_config']), created_at=row['created_at'], created_by=row['created_by'], is_default=bool(row['is_default'])) for row in rows]
```

### Method: `get_template`
**Logic & Purpose:**
```text
Get specific template
```

**Parameters:** `self, template_id`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def get_template(self, template_id: str) -> Optional[ReportTemplate]:
    """Get specific template"""
    if not usage_tracker.enabled:
        return None
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('SELECT * FROM report_templates WHERE id = ?', (template_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return ReportTemplate(id=row['id'], name=row['name'], description=row['description'], config=json.loads(row['template_config']), created_at=row['created_at'], created_by=row['created_by'], is_default=bool(row['is_default']))
```

### Method: `generate_report_data`
**Logic & Purpose:**
```text
Generate data for report based on template config
```

**Parameters:** `self, template, start_date, end_date`
**Variables Used:** `summary_row, conn, cursor, data`
**Implementation:**
```python
def generate_report_data(self, template: ReportTemplate, start_date: str, end_date: str) -> Dict[str, Any]:
    """Generate data for report based on template config"""
    if not usage_tracker.enabled:
        return {}
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    data = {'metadata': {'template': template.name, 'generated_at': datetime.utcnow().isoformat(), 'date_range': {'start': start_date, 'end': end_date}}, 'summary': {}, 'charts': {}, 'tables': {}}
    if 'charts' in template.config:
        for chart_type in template.config['charts']:
            if chart_type == 'token_trend':
                cursor = conn.execute('\n                        SELECT DATE(timestamp) as date, SUM(total_tokens) as tokens\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY DATE(timestamp)\n                        ORDER BY date\n                    ', (start_date, end_date))
                data['charts']['token_trend'] = [{'date': row['date'], 'value': row['tokens'] or 0} for row in cursor.fetchall()]
            elif chart_type == 'cost_breakdown':
                cursor = conn.execute('\n                        SELECT provider, SUM(estimated_cost) as cost\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY provider\n                        ORDER BY cost DESC\n                    ', (start_date, end_date))
                data['charts']['cost_breakdown'] = [{'label': row['provider'], 'value': row['cost'] or 0} for row in cursor.fetchall()]
            elif chart_type == 'cost_over_time':
                cursor = conn.execute('\n                        SELECT DATE(timestamp) as date, SUM(estimated_cost) as cost\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY DATE(timestamp)\n                        ORDER BY date\n                    ', (start_date, end_date))
                data['charts']['cost_over_time'] = [{'date': row['date'], 'value': row['cost'] or 0} for row in cursor.fetchall()]
    if 'tables' in template.config:
        for table_type in template.config['tables']:
            if table_type == 'model_usage':
                cursor = conn.execute('\n                        SELECT routed_model as model, COUNT(*) as requests,\n                               SUM(total_tokens) as tokens, SUM(estimated_cost) as cost\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY routed_model\n                        ORDER BY cost DESC\n                    ', (start_date, end_date))
                data['tables']['model_usage'] = [dict(row) for row in cursor.fetchall()]
            elif table_type == 'cost_breakdown':
                cursor = conn.execute('\n                        SELECT provider, COUNT(*) as requests,\n                               SUM(total_tokens) as tokens, SUM(estimated_cost) as cost,\n                               AVG(duration_ms) as avg_latency\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY provider\n                        ORDER BY cost DESC\n                    ', (start_date, end_date))
                data['tables']['cost_breakdown'] = [dict(row) for row in cursor.fetchall()]
            elif table_type == 'model_comparison':
                cursor = conn.execute('\n                        SELECT routed_model as model, provider, COUNT(*) as requests,\n                               SUM(total_tokens) as tokens, SUM(estimated_cost) as cost,\n                               AVG(duration_ms) as avg_latency\n                        FROM api_requests\n                        WHERE timestamp >= ? AND timestamp <= ?\n                        GROUP BY routed_model, provider\n                        ORDER BY cost DESC\n                    ', (start_date, end_date))
                data['tables']['model_comparison'] = [dict(row) for row in cursor.fetchall()]
    cursor = conn.execute('\n            SELECT\n                COUNT(*) as total_requests,\n                SUM(total_tokens) as total_tokens,\n                SUM(estimated_cost) as total_cost,\n                AVG(duration_ms) as avg_latency\n            FROM api_requests\n            WHERE timestamp >= ? AND timestamp <= ?\n        ', (start_date, end_date))
    summary_row = cursor.fetchone()
    data['summary'] = {'total_requests': summary_row['total_requests'] or 0, 'total_tokens': summary_row['total_tokens'] or 0, 'total_cost': round(summary_row['total_cost'] or 0, 2), 'avg_latency': round(summary_row['avg_latency'] or 0, 0)}
    conn.close()
    return data
```

### Method: `generate_pdf`
**Logic & Purpose:**
```text
Generate PDF report
```

**Parameters:** `self, template, start_date, end_date, brand_logo, brand_color`
**Variables Used:** `report_data, logo, detailed_table, pdf_bytes, summary_table, doc, styles, headers, table_rows, summary_data, title_style, buffer, story`
**Implementation:**
```python
def generate_pdf(self, template: ReportTemplate, start_date: str, end_date: str, brand_logo: Optional[str]=None, brand_color: str='#3b82f6') -> bytes:
    """Generate PDF report"""
    if not usage_tracker.enabled:
        return b''
    report_data = self.generate_report_data(template, start_date, end_date)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)
    story = []
    styles = getSampleStyleSheet()
    if brand_logo:
        try:
            logo = Image(brand_logo, width=1 * inch, height=1 * inch)
            story.append(logo)
            story.append(Spacer(1, 12))
        except Exception as _e:
            pass
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=brand_color, spaceAfter=20)
    story.append(Paragraph(template.name, title_style))
    story.append(Paragraph(f'Date Range: {start_date} to {end_date}', styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph('Summary', styles['Heading2']))
    summary_data = report_data['summary']
    summary_table = Table([['Metric', 'Value'], ['Total Requests', f"{summary_data['total_requests']:,}"], ['Total Tokens', f"{summary_data['total_tokens']:,}"], ['Total Cost', f"${summary_data['total_cost']:,.2f}"], ['Avg Latency', f"{summary_data['avg_latency']} ms"]], colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(brand_color)), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 12), ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    if 'tables' in report_data and report_data['tables']:
        story.append(Paragraph('Detailed Tables', styles['Heading2']))
        for table_name, table_data in report_data['tables'].items():
            if table_data:
                story.append(Paragraph(table_name.replace('_', ' ').title(), styles['Heading3']))
                if table_data:
                    headers = list(table_data[0].keys())
                    table_rows = [headers]
                    for row in table_data:
                        table_rows.append([str(row.get(h, '')) for h in headers])
                    if len(table_rows) > 1:
                        detailed_table = Table(table_rows)
                        detailed_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.black), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 9), ('FONTSIZE', (0, 1), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
                        story.append(detailed_table)
                        story.append(Spacer(1, 12))
    if 'charts' in report_data and report_data['charts']:
        story.append(Paragraph('Charts Data', styles['Heading2']))
        for chart_name, chart_data in report_data['charts'].items():
            if chart_data:
                story.append(Paragraph(chart_name.replace('_', ' ').title(), styles['Heading3']))
                story.append(Paragraph(f'Data points: {len(chart_data)}', styles['Normal']))
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
```

### Method: `generate_excel`
**Logic & Purpose:**
```text
Generate Excel report with charts
```

**Parameters:** `self, template, start_date, end_date`
**Variables Used:** `report_data, ws_charts, cell_value, ws_summary, chart_row, ws, headers, chart, data, excel_bytes, wb, summary, buffer, categories, cell, max_length, row`
**Implementation:**
```python
def generate_excel(self, template: ReportTemplate, start_date: str, end_date: str) -> bytes:
    """Generate Excel report with charts"""
    if not usage_tracker.enabled:
        return b''
    report_data = self.generate_report_data(template, start_date, end_date)
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = 'Summary'
    ws_summary['A1'] = template.name
    ws_summary['A1'].font = Font(size=14, bold=True)
    ws_summary['A2'] = f'Date Range: {start_date} to {end_date}'
    ws_summary['A3'] = f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    row = 5
    ws_summary.cell(row=row, column=1, value='Metric').font = Font(bold=True)
    ws_summary.cell(row=row, column=2, value='Value').font = Font(bold=True)
    row += 1
    summary = report_data['summary']
    for key, value in summary.items():
        ws_summary.cell(row=row, column=1, value=key.replace('_', ' ').title())
        ws_summary.cell(row=row, column=2, value=value)
        row += 1
    for cell in ws_summary['A5:B5']:
        cell[0].fill = PatternFill(start_color='3B82F6', end_color='3B82F6', fill_type='solid')
        cell[0].font = Font(color='FFFFFF', bold=True)
    if 'tables' in report_data:
        for table_name, table_data in report_data['tables'].items():
            if not table_data:
                continue
            ws = wb.create_sheet(title=table_name[:30])
            headers = list(table_data[0].keys())
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col, value=header.replace('_', ' ').title())
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color='E5E7EB', end_color='E5E7EB', fill_type='solid')
            for row_idx, row_data in enumerate(table_data, start=2):
                for col, header in enumerate(headers, start=1):
                    ws.cell(row=row_idx, column=col, value=row_data.get(header, 0))
            for col in range(1, len(headers) + 1):
                max_length = 0
                for row in range(1, ws.max_row + 1):
                    cell_value = str(ws.cell(row=row, column=col).value or '')
                    max_length = max(max_length, len(cell_value))
                ws.column_dimensions[chr(64 + col)].width = min(max_length + 2, 50)
    if 'charts' in report_data and report_data['charts']:
        ws_charts = wb.create_sheet(title='Charts')
        chart_row = 1
        for chart_name, chart_data in report_data['charts'].items():
            if not chart_data:
                continue
            ws_charts.cell(row=chart_row, column=1, value=chart_name.replace('_', ' ').title())
            chart_row += 1
            if 'date' in chart_data[0]:
                for i, point in enumerate(chart_data, start=chart_row):
                    ws_charts.cell(row=i, column=1, value=point['date'])
                    ws_charts.cell(row=i, column=2, value=point['value'])
                chart = XLSXLineChart()
                data = XLSXReference(ws_charts, min_col=2, min_row=chart_row, max_row=chart_row + len(chart_data) - 1)
                categories = XLSXReference(ws_charts, min_col=1, min_row=chart_row, max_row=chart_row + len(chart_data) - 1)
                chart.add_data(data, titles_from_data=False)
                chart.set_categories(categories)
                chart.title = chart_name.replace('_', ' ').title()
                chart.x_axis.title = 'Date'
                chart.y_axis.title = 'Value'
                chart.height = 10
                chart.width = 16
                ws_charts.add_chart(chart, f'D{chart_row}')
                chart_row += len(chart_data) + 2
            elif 'label' in chart_data[0]:
                for i, point in enumerate(chart_data, start=chart_row):
                    ws_charts.cell(row=i, column=1, value=point['label'])
                    ws_charts.cell(row=i, column=2, value=point['value'])
                chart = XLSXBarChart()
                data = XLSXReference(ws_charts, min_col=2, min_row=chart_row, max_row=chart_row + len(chart_data) - 1)
                categories = XLSXReference(ws_charts, min_col=1, min_row=chart_row, max_row=chart_row + len(chart_data) - 1)
                chart.add_data(data, titles_from_data=False)
                chart.set_categories(categories)
                chart.title = chart_name.replace('_', ' ').title()
                chart.x_axis.title = 'Category'
                chart.y_axis.title = 'Value'
                chart.height = 10
                chart.width = 16
                ws_charts.add_chart(chart, f'D{chart_row}')
                chart_row += len(chart_data) + 2
    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()
    buffer.close()
    return excel_bytes
```

### Method: `generate_csv`
**Logic & Purpose:**
```text
Generate CSV report
```

**Parameters:** `self, template, start_date, end_date`
**Variables Used:** `report_data, headers, csv_lines`
**Implementation:**
```python
def generate_csv(self, template: ReportTemplate, start_date: str, end_date: str) -> str:
    """Generate CSV report"""
    if not usage_tracker.enabled:
        return ''
    report_data = self.generate_report_data(template, start_date, end_date)
    csv_lines = []
    csv_lines.append(f'Template,{template.name}')
    csv_lines.append(f'Date Range,{start_date} to {end_date}')
    csv_lines.append(f'Generated,{datetime.utcnow().isoformat()}')
    csv_lines.append('')
    csv_lines.append('Summary')
    for key, value in report_data['summary'].items():
        csv_lines.append(f'{key},{value}')
    csv_lines.append('')
    for table_name, table_data in report_data['tables'].items():
        if not table_data:
            continue
        csv_lines.append(f"Table: {table_name.replace('_', ' ').title()}")
        headers = list(table_data[0].keys())
        csv_lines.append(','.join(headers))
        for row in table_data:
            csv_lines.append(','.join((str(row.get(h, '')) for h in headers)))
        csv_lines.append('')
    for chart_name, chart_data in report_data['charts'].items():
        if not chart_data:
            continue
        csv_lines.append(f"Chart: {chart_name.replace('_', ' ').title()}")
        if 'date' in chart_data[0]:
            csv_lines.append('Date,Value')
            for point in chart_data:
                csv_lines.append(f"{point['date']},{point['value']}")
        elif 'label' in chart_data[0]:
            csv_lines.append('Label,Value')
            for point in chart_data:
                csv_lines.append(f"{point['label']},{point['value']}")
        csv_lines.append('')
    return '\n'.join(csv_lines)
```

### Method: `create_template`
**Logic & Purpose:**
```text
Create a new report template
```

**Parameters:** `self, name, description, config, created_by, is_default`
**Variables Used:** `conn, cursor, template_id`
**Implementation:**
```python
def create_template(self, name: str, description: str, config: Dict[str, Any], created_by: str='system', is_default: bool=False) -> str:
    """Create a new report template"""
    if not usage_tracker.enabled:
        return ''
    conn = sqlite3.connect(self.db_path)
    template_id = f"tpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor = conn.execute('\n            INSERT INTO report_templates (id, name, description, template_config, created_at, created_by, is_default)\n            VALUES (?, ?, ?, ?, ?, ?, ?)\n        ', (template_id, name, description, json.dumps(config), datetime.utcnow().isoformat(), created_by, 1 if is_default else 0))
    conn.commit()
    conn.close()
    return template_id
```

### Method: `get_scheduled_reports`
**Logic & Purpose:**
```text
Get all scheduled reports
```

**Parameters:** `self`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_scheduled_reports(self) -> List[Dict[str, Any]]:
    """Get all scheduled reports"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('\n            SELECT sr.*, t.name as template_name\n            FROM scheduled_reports sr\n            JOIN report_templates t ON sr.template_id = t.id\n            WHERE sr.is_active = 1\n            ORDER BY sr.next_run\n        ')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

### Method: `schedule_report`
**Logic & Purpose:**
```text
Schedule a report for automatic delivery
```

**Parameters:** `self, template_id, frequency, recipients, timezone`
**Variables Used:** `next_run, now, cursor, schedule_id, conn`
**Implementation:**
```python
def schedule_report(self, template_id: str, frequency: str, recipients: List[str], timezone: str='UTC') -> str:
    """Schedule a report for automatic delivery"""
    if not usage_tracker.enabled:
        return ''
    now = datetime.utcnow()
    if frequency == 'daily':
        next_run = now + timedelta(days=1)
    elif frequency == 'weekly':
        next_run = now + timedelta(days=7)
    elif frequency == 'monthly':
        next_run = now + timedelta(days=30)
    else:
        return ''
    conn = sqlite3.connect(self.db_path)
    schedule_id = f"sch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor = conn.execute('\n            INSERT INTO scheduled_reports (id, template_id, frequency, recipients, last_run, next_run, timezone, is_active, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (schedule_id, template_id, frequency, json.dumps(recipients), None, next_run.isoformat(), timezone, 1, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return schedule_id
```

### Method: `check_scheduled_reports`
**Logic & Purpose:**
```text
Check for reports due for delivery and execute them
```

**Parameters:** `self`
**Variables Used:** `due_reports, now, cursor, template, next_run, results, end_date, recipients, excel_data, start_date, conn`
**Implementation:**
```python
def check_scheduled_reports(self) -> List[Dict[str, Any]]:
    """Check for reports due for delivery and execute them"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    now = datetime.utcnow().isoformat()
    cursor = conn.execute('\n            SELECT sr.*, t.template_config, t.name as template_name\n            FROM scheduled_reports sr\n            JOIN report_templates t ON sr.template_id = t.id\n            WHERE sr.is_active = 1 AND sr.next_run <= ?\n        ', (now,))
    due_reports = cursor.fetchall()
    results = []
    for report in due_reports:
        try:
            if report['frequency'] == 'daily':
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=1)
            elif report['frequency'] == 'weekly':
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=7)
            else:
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=30)
            template = self.get_template(report['template_id'])
            if template:
                recipients = json.loads(report['recipients'])
                excel_data = self.generate_excel(template, str(start_date), str(end_date))
                cursor.execute('\n                        INSERT INTO report_executions (id, scheduled_report_id, template_id, execution_time, status, file_size)\n                        VALUES (?, ?, ?, ?, ?, ?)\n                    ', (f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}", report['id'], report['template_id'], datetime.utcnow().isoformat(), 'success', len(excel_data)))
                if report['frequency'] == 'daily':
                    next_run = datetime.utcnow() + timedelta(days=1)
                elif report['frequency'] == 'weekly':
                    next_run = datetime.utcnow() + timedelta(days=7)
                else:
                    next_run = datetime.utcnow() + timedelta(days=30)
                cursor.execute('\n                        UPDATE scheduled_reports\n                        SET last_run = ?, next_run = ?\n                        WHERE id = ?\n                    ', (datetime.utcnow().isoformat(), next_run.isoformat(), report['id']))
                results.append({'template_id': report['template_id'], 'template_name': report['template_name'], 'recipients': recipients, 'status': 'delivered'})
        except Exception as e:
            logger.error(f"Failed to execute scheduled report {report['id']}: {e}")
            cursor.execute('\n                    INSERT INTO report_executions (id, scheduled_report_id, template_id, execution_time, status, error_message)\n                    VALUES (?, ?, ?, ?, ?, ?)\n                ', (f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}", report['id'], report['template_id'], datetime.utcnow().isoformat(), 'failed', str(e)))
    conn.commit()
    conn.close()
    return results
```

### Method: `get_execution_history`
**Logic & Purpose:**
```text
Get report execution history
```

**Parameters:** `self, limit`
**Variables Used:** `rows, conn, cursor`
**Implementation:**
```python
def get_execution_history(self, limit: int=50) -> List[Dict[str, Any]]:
    """Get report execution history"""
    if not usage_tracker.enabled:
        return []
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('\n            SELECT e.*, t.name as template_name, sr.frequency\n            FROM report_executions e\n            JOIN report_templates t ON e.template_id = t.id\n            LEFT JOIN scheduled_reports sr ON e.scheduled_report_id = sr.id\n            ORDER BY e.execution_time DESC\n            LIMIT ?\n        ', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
```

---


