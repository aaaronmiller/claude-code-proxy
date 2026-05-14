# File Audit: /home/cheta/code/claude-code-proxy/src/services/usage/usage_tracker.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/usage/usage_tracker.py`

**Module Overview**: 
```text
Actual API usage tracking system (opt-in).

Tracks real API requests for analytics, cost analysis, and optimization.
Stores data in SQLite for persistence and efficient querying.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `usage_tracker` = `UsageTracker()`

## Dependencies & Imports
sqlite3, os, json, datetime.datetime, datetime.timedelta, typing.Dict, typing.Any, typing.List, typing.Optional, typing.Tuple, pathlib.Path, logging

## Feature Function: `sanitize_content_for_logging`
**Logic & Purpose:**
```text
Sanitize content to remove token-wasting placeholder strings.

Filters out:
- "(no content)" placeholders from Claude CLI
- Empty or whitespace-only content
- Excessively long content that would waste log tokens

Args:
    content: The content string to sanitize

Returns:
    Sanitized content string, or None if content should be excluded entirely
```

**Parameters:** `content`
**Variables Used:** `stripped, no_content_patterns, remaining, content_lower`
**Implementation:**
```python
def sanitize_content_for_logging(content: Optional[str]) -> Optional[str]:
    """
    Sanitize content to remove token-wasting placeholder strings.

    Filters out:
    - "(no content)" placeholders from Claude CLI
    - Empty or whitespace-only content
    - Excessively long content that would waste log tokens

    Args:
        content: The content string to sanitize

    Returns:
        Sanitized content string, or None if content should be excluded entirely
    """
    if content is None:
        return None
    stripped = content.strip()
    if not stripped:
        return None
    no_content_patterns = ['(no content)', 'no content', 'claude: (no content)', 'claude: no content']
    content_lower = stripped.lower()
    for pattern in no_content_patterns:
        if content_lower == pattern:
            return None
        if pattern in content_lower:
            remaining = content_lower.replace(pattern, '').strip()
            if not remaining or remaining in ['.', '...']:
                return None
    if len(stripped) > 500:
        return stripped[:500] + '...'
    return stripped
```

---

## Feature Class: `UsageTracker`
**Description:**
```text
Track actual API usage for analytics and cost optimization.

Features:
- Persistent SQLite storage
- Session-based tracking
- Cost estimation
- Performance metrics
- Privacy-focused (opt-in, no content storage)
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize usage tracker.

Args:
    db_path: Path to SQLite database
    enabled: Override environment variable (for testing)
```

**Parameters:** `self, db_path, enabled`
**Variables Used:** `enabled`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db', enabled: bool=None):
    """
        Initialize usage tracker.

        Args:
            db_path: Path to SQLite database
            enabled: Override environment variable (for testing)
        """
    self.db_path = db_path
    if enabled is None:
        enabled = os.getenv('TRACK_USAGE', 'false').lower() == 'true'
    self.enabled = enabled
    self.log_full_content = os.getenv('LOG_FULL_CONTENT', 'false').lower() == 'true'
    if self.enabled:
        self._init_db()
        logger.info(f'Usage tracking enabled. Database: {self.db_path}')
        if self.log_full_content:
            logger.info('Full request/response content logging enabled')
    else:
        logger.debug('Usage tracking disabled. Set TRACK_USAGE=true to enable')
```

### Method: `get_connection`
**Logic & Purpose:**
```text
Get a database connection.
```

**Parameters:** `self`
**Implementation:**
```python
def get_connection(self):
    """Get a database connection."""
    return sqlite3.connect(self.db_path)
```

### Method: `_init_db`
**Logic & Purpose:**
```text
Initialize SQLite database with schema.
```

**Parameters:** `self`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def _init_db(self):
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("\n            CREATE TABLE IF NOT EXISTS api_requests (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                request_id TEXT UNIQUE NOT NULL,\n                timestamp TEXT NOT NULL,\n\n                -- Model info\n                original_model TEXT NOT NULL,\n                routed_model TEXT NOT NULL,\n                provider TEXT,\n                endpoint TEXT,\n\n                -- Token usage\n                input_tokens INTEGER,\n                output_tokens INTEGER,\n                thinking_tokens INTEGER DEFAULT 0,\n                total_tokens INTEGER,\n\n                -- Performance\n                duration_ms REAL,\n                tokens_per_second REAL,\n\n                -- Cost estimation\n                estimated_cost REAL DEFAULT 0.0,\n\n                -- Request metadata\n                stream BOOLEAN,\n                message_count INTEGER,\n                has_system BOOLEAN,\n                has_tools BOOLEAN,\n                has_images BOOLEAN,\n\n                -- Status\n                status TEXT DEFAULT 'success',\n                error_message TEXT,\n\n                -- Session tracking\n                session_id TEXT,\n                client_ip TEXT,\n\n                -- JSON detection (for TOON analysis)\n                has_json_content BOOLEAN DEFAULT 0,\n                json_size_bytes INTEGER DEFAULT 0,\n\n                -- Full content logging (optional, for debugging/testing)\n                request_content TEXT,\n                response_content TEXT\n            )\n        ")
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS model_usage_summary (\n                model TEXT PRIMARY KEY,\n                request_count INTEGER DEFAULT 0,\n                total_input_tokens INTEGER DEFAULT 0,\n                total_output_tokens INTEGER DEFAULT 0,\n                total_thinking_tokens INTEGER DEFAULT 0,\n                total_cost REAL DEFAULT 0.0,\n                avg_duration_ms REAL DEFAULT 0.0,\n                last_used TEXT\n            )\n        ')
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS session_summary (\n                session_id TEXT PRIMARY KEY,\n                start_time TEXT,\n                end_time TEXT,\n                request_count INTEGER DEFAULT 0,\n                total_tokens INTEGER DEFAULT 0,\n                total_cost REAL DEFAULT 0.0,\n\n                -- JSON/TOON analysis\n                json_requests INTEGER DEFAULT 0,\n                total_json_bytes INTEGER DEFAULT 0,\n                potential_toon_savings INTEGER DEFAULT 0\n            )\n        ')
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS terminal_output (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                session_id TEXT NOT NULL,\n                test_config TEXT,\n                timestamp TEXT NOT NULL,\n\n                -- Terminal capture\n                stdout TEXT,\n                stderr TEXT,\n                exit_code INTEGER,\n\n                -- Execution metadata\n                workspace_path TEXT,\n                prompt TEXT,\n                duration_seconds REAL,\n\n                -- Test results\n                poem_created BOOLEAN DEFAULT 0,\n                poem_content TEXT,\n                folder_listed BOOLEAN DEFAULT 0,\n\n                -- Status\n                success BOOLEAN DEFAULT 0,\n                error_message TEXT\n            )\n        ')
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS daily_model_stats (\n                date TEXT NOT NULL,\n                model TEXT NOT NULL,\n                provider TEXT,\n                request_count INTEGER DEFAULT 0,\n                input_tokens INTEGER DEFAULT 0,\n                output_tokens INTEGER DEFAULT 0,\n                thinking_tokens INTEGER DEFAULT 0,\n                total_tokens INTEGER DEFAULT 0,\n                total_cost REAL DEFAULT 0.0,\n                avg_duration_ms REAL DEFAULT 0.0,\n                has_tools_count INTEGER DEFAULT 0,\n                has_images_count INTEGER DEFAULT 0,\n                success_count INTEGER DEFAULT 0,\n                error_count INTEGER DEFAULT 0,\n                PRIMARY KEY (date, model)\n            )\n        ')
    cursor.execute("\n            CREATE TABLE IF NOT EXISTS model_comparison_stats (\n                date TEXT NOT NULL,\n                model_tier TEXT NOT NULL,  -- 'big', 'middle', 'small', 'free'\n                model TEXT NOT NULL,\n                cost_per_1k_tokens REAL DEFAULT 0.0,\n                tokens_per_request REAL DEFAULT 0.0,\n                avg_latency_ms REAL DEFAULT 0.0,\n                request_count INTEGER DEFAULT 0,\n                PRIMARY KEY (date, model_tier, model)\n            )\n        ")
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS savings_tracking (\n                date TEXT NOT NULL,\n                original_model TEXT NOT NULL,\n                routed_model TEXT NOT NULL,\n                original_cost REAL DEFAULT 0.0,\n                actual_cost REAL DEFAULT 0.0,\n                savings REAL DEFAULT 0.0,\n                savings_percent REAL DEFAULT 0.0,\n                request_count INTEGER DEFAULT 1,\n                PRIMARY KEY (date, original_model, routed_model)\n            )\n        ')
    cursor.execute('\n            CREATE TABLE IF NOT EXISTS token_breakdown (\n                request_id TEXT PRIMARY KEY,\n                timestamp TEXT NOT NULL,\n                model TEXT NOT NULL,\n                prompt_tokens INTEGER DEFAULT 0,\n                completion_tokens INTEGER DEFAULT 0,\n                reasoning_tokens INTEGER DEFAULT 0,\n                cached_tokens INTEGER DEFAULT 0,\n                tool_use_tokens INTEGER DEFAULT 0,\n                audio_tokens INTEGER DEFAULT 0,\n                total_tokens INTEGER DEFAULT 0\n            )\n        ')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON api_requests(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_model ON api_requests(routed_model)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON api_requests(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON api_requests(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_terminal_session ON terminal_output(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_terminal_timestamp ON terminal_output(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_model_stats(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_model ON daily_model_stats(model)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_savings_date ON savings_tracking(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_breakdown_model ON token_breakdown(model)')
    conn.commit()
    conn.close()
```

### Method: `log_request`
**Logic & Purpose:**
```text
Log an API request.

Returns:
    True if logged successfully, False otherwise
```

**Parameters:** `self, request_id, original_model, routed_model, provider, endpoint, input_tokens, output_tokens, thinking_tokens, duration_ms, estimated_cost, stream, message_count, has_system, has_tools, has_images, status, error_message, session_id, client_ip, has_json_content, json_size_bytes, request_content, response_content, prompt_tokens, completion_tokens, reasoning_tokens, cached_tokens, tool_use_tokens, audio_tokens, original_cost, model_tier`
**Variables Used:** `bd_total, cursor, c_tokens, tokens_per_req, tokens_per_second, today, cost_per_1k, p_tokens, req_content, savings, r_tokens, total_tokens, resp_content, conn, savings_percent`
**Implementation:**
```python
def log_request(self, request_id: str, original_model: str, routed_model: str, provider: str, endpoint: str, input_tokens: int=0, output_tokens: int=0, thinking_tokens: int=0, duration_ms: float=0.0, estimated_cost: float=0.0, stream: bool=False, message_count: int=0, has_system: bool=False, has_tools: bool=False, has_images: bool=False, status: str='success', error_message: Optional[str]=None, session_id: Optional[str]=None, client_ip: Optional[str]=None, has_json_content: bool=False, json_size_bytes: int=0, request_content: Optional[str]=None, response_content: Optional[str]=None, prompt_tokens: Optional[int]=None, completion_tokens: Optional[int]=None, reasoning_tokens: Optional[int]=None, cached_tokens: Optional[int]=None, tool_use_tokens: Optional[int]=None, audio_tokens: Optional[int]=None, original_cost: Optional[float]=None, model_tier: Optional[str]=None) -> bool:
    """
        Log an API request.

        Returns:
            True if logged successfully, False otherwise
        """
    if not self.enabled:
        return False
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        total_tokens = input_tokens + output_tokens + thinking_tokens
        tokens_per_second = output_tokens / (duration_ms / 1000) if duration_ms > 0 and output_tokens > 0 else 0.0
        req_content = sanitize_content_for_logging(request_content) if self.log_full_content and request_content else None
        resp_content = sanitize_content_for_logging(response_content) if self.log_full_content and response_content else None
        try:
            cursor.execute('\n                    INSERT INTO api_requests (\n                        request_id, timestamp,\n                        original_model, routed_model, provider, endpoint,\n                        input_tokens, output_tokens, thinking_tokens, total_tokens,\n                        duration_ms, tokens_per_second, estimated_cost,\n                        stream, message_count, has_system, has_tools, has_images,\n                        status, error_message,\n                        session_id, client_ip,\n                        has_json_content, json_size_bytes,\n                        request_content, response_content\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ', (request_id, datetime.utcnow().isoformat(), original_model, routed_model, provider, endpoint, input_tokens, output_tokens, thinking_tokens, total_tokens, duration_ms, tokens_per_second, estimated_cost, stream, message_count, has_system, has_tools, has_images, status, error_message, session_id, client_ip, has_json_content, json_size_bytes, req_content, resp_content))
        except sqlite3.IntegrityError:
            cursor.execute('\n                    UPDATE api_requests SET\n                        status = ?, error_message = ?\n                    WHERE request_id = ?\n                ', (status, error_message, request_id))
        cursor.execute('\n                INSERT INTO model_usage_summary (\n                    model, request_count,\n                    total_input_tokens, total_output_tokens, total_thinking_tokens,\n                    total_cost, avg_duration_ms, last_used\n                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(model) DO UPDATE SET\n                    request_count = request_count + 1,\n                    total_input_tokens = total_input_tokens + excluded.total_input_tokens,\n                    total_output_tokens = total_output_tokens + excluded.total_output_tokens,\n                    total_thinking_tokens = total_thinking_tokens + excluded.total_thinking_tokens,\n                    total_cost = total_cost + excluded.total_cost,\n                    avg_duration_ms = (avg_duration_ms * request_count + excluded.avg_duration_ms) / (request_count + 1),\n                    last_used = excluded.last_used\n            ', (routed_model, input_tokens, output_tokens, thinking_tokens, estimated_cost, duration_ms, datetime.utcnow().isoformat()))
        if session_id:
            cursor.execute('\n                    INSERT INTO session_summary (\n                        session_id, start_time, end_time,\n                        request_count, total_tokens, total_cost,\n                        json_requests, total_json_bytes\n                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)\n                    ON CONFLICT(session_id) DO UPDATE SET\n                        end_time = excluded.end_time,\n                        request_count = request_count + 1,\n                        total_tokens = total_tokens + excluded.total_tokens,\n                        total_cost = total_cost + excluded.total_cost,\n                        json_requests = json_requests + excluded.json_requests,\n                        total_json_bytes = total_json_bytes + excluded.total_json_bytes\n                ', (session_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), total_tokens, estimated_cost, 1 if has_json_content else 0, json_size_bytes))
        today = datetime.utcnow().strftime('%Y-%m-%d')
        cursor.execute('\n                INSERT INTO daily_model_stats (\n                    date, model, provider,\n                    request_count, input_tokens, output_tokens, thinking_tokens,\n                    total_tokens, total_cost, avg_duration_ms,\n                    has_tools_count, has_images_count, success_count, error_count\n                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ON CONFLICT(date, model) DO UPDATE SET\n                    request_count = request_count + 1,\n                    input_tokens = input_tokens + excluded.input_tokens,\n                    output_tokens = output_tokens + excluded.output_tokens,\n                    thinking_tokens = thinking_tokens + excluded.thinking_tokens,\n                    total_tokens = total_tokens + excluded.total_tokens,\n                    total_cost = total_cost + excluded.total_cost,\n                    avg_duration_ms = (avg_duration_ms * request_count + excluded.avg_duration_ms) / (request_count + 1),\n                    has_tools_count = has_tools_count + excluded.has_tools_count,\n                    has_images_count = has_images_count + excluded.has_images_count,\n                    success_count = success_count + excluded.success_count,\n                    error_count = error_count + excluded.error_count\n            ', (today, routed_model, provider, input_tokens, output_tokens, thinking_tokens, total_tokens, estimated_cost, duration_ms, 1 if has_tools else 0, 1 if has_images else 0, 1 if status == 'success' else 0, 1 if status != 'success' else 0))
        if model_tier:
            cost_per_1k = estimated_cost / total_tokens * 1000 if total_tokens > 0 else 0.0
            tokens_per_req = total_tokens
            cursor.execute('\n                    INSERT INTO model_comparison_stats (\n                        date, model_tier, model, cost_per_1k_tokens, tokens_per_request, avg_latency_ms\n                    ) VALUES (?, ?, ?, ?, ?, ?)\n                    ON CONFLICT(date, model_tier, model) DO UPDATE SET\n                        cost_per_1k_tokens = (cost_per_1k_tokens * request_count + excluded.cost_per_1k_tokens) / (request_count + 1),\n                        tokens_per_request = (tokens_per_request * request_count + excluded.tokens_per_request) / (request_count + 1),\n                        avg_latency_ms = (avg_latency_ms * request_count + excluded.avg_latency_ms) / (request_count + 1)\n                ', (today, model_tier, routed_model, cost_per_1k, tokens_per_req, duration_ms))
        if original_cost is not None and original_cost > 0:
            savings = original_cost - estimated_cost
            savings_percent = savings / original_cost * 100 if original_cost > 0 else 0.0
            cursor.execute('\n                    INSERT INTO savings_tracking (\n                        date, original_model, routed_model,\n                        original_cost, actual_cost, savings, savings_percent, request_count\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)\n                    ON CONFLICT(date, original_model, routed_model) DO UPDATE SET\n                        original_cost = original_cost + excluded.original_cost,\n                        actual_cost = actual_cost + excluded.actual_cost,\n                        savings = savings + excluded.savings,\n                        savings_percent = (savings_percent * request_count + excluded.savings_percent) / (request_count + 1),\n                        request_count = request_count + 1\n                ', (today, original_model, routed_model, original_cost, estimated_cost, savings, savings_percent))
        if prompt_tokens is not None or completion_tokens is not None:
            p_tokens = prompt_tokens if prompt_tokens is not None else input_tokens
            c_tokens = completion_tokens if completion_tokens is not None else output_tokens
            r_tokens = reasoning_tokens if reasoning_tokens is not None else thinking_tokens
            bd_total = (p_tokens or 0) + (c_tokens or 0) + (r_tokens or 0)
            if bd_total == 0:
                bd_total = total_tokens
            cursor.execute('\n                    INSERT INTO token_breakdown (\n                        request_id, timestamp, model,\n                        prompt_tokens, completion_tokens, reasoning_tokens,\n                        cached_tokens, tool_use_tokens, audio_tokens, total_tokens\n                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ON CONFLICT(request_id) DO UPDATE SET\n                        prompt_tokens = excluded.prompt_tokens,\n                        completion_tokens = excluded.completion_tokens,\n                        reasoning_tokens = excluded.reasoning_tokens,\n                        cached_tokens = excluded.cached_tokens,\n                        tool_use_tokens = excluded.tool_use_tokens,\n                        audio_tokens = excluded.audio_tokens,\n                        total_tokens = excluded.total_tokens\n                ', (request_id, datetime.utcnow().isoformat(), routed_model, p_tokens or 0, c_tokens or 0, r_tokens or 0, cached_tokens or 0, tool_use_tokens or 0, audio_tokens or 0, bd_total))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f'Failed to log usage: {e}')
        return False
```

### Method: `log_terminal_output`
**Logic & Purpose:**
```text
Log Claude Code terminal output for correlation with API requests.

Returns:
    True if logged successfully, False otherwise
```

**Parameters:** `self, session_id, stdout, stderr, exit_code, test_config, workspace_path, prompt, duration_seconds, poem_created, poem_content, folder_listed, success, error_message`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def log_terminal_output(self, session_id: str, stdout: str, stderr: str, exit_code: int, test_config: Optional[str]=None, workspace_path: Optional[str]=None, prompt: Optional[str]=None, duration_seconds: float=0.0, poem_created: bool=False, poem_content: Optional[str]=None, folder_listed: bool=False, success: bool=False, error_message: Optional[str]=None) -> bool:
    """
        Log Claude Code terminal output for correlation with API requests.

        Returns:
            True if logged successfully, False otherwise
        """
    if not self.enabled:
        return False
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                INSERT INTO terminal_output (\n                    session_id, test_config, timestamp,\n                    stdout, stderr, exit_code,\n                    workspace_path, prompt, duration_seconds,\n                    poem_created, poem_content, folder_listed,\n                    success, error_message\n                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (session_id, test_config, datetime.utcnow().isoformat(), stdout, stderr, exit_code, workspace_path, prompt, duration_seconds, poem_created, poem_content, folder_listed, success, error_message))
        conn.commit()
        conn.close()
        logger.debug(f'Terminal output logged for session {session_id}')
        return True
    except Exception as e:
        logger.error(f'Failed to log terminal output: {e}')
        return False
```

### Method: `get_terminal_output`
**Logic & Purpose:**
```text
Get terminal output for a session.
```

**Parameters:** `self, session_id`
**Variables Used:** `conn, cursor, row`
**Implementation:**
```python
def get_terminal_output(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Get terminal output for a session."""
    if not self.enabled:
        return None
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('\n                SELECT * FROM terminal_output\n                WHERE session_id = ?\n                ORDER BY timestamp DESC\n                LIMIT 1\n            ', (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f'Failed to get terminal output: {e}')
        return None
```

### Method: `get_top_models`
**Logic & Purpose:**
```text
Get most used models by request count.
```

**Parameters:** `self, limit`
**Variables Used:** `results, conn, cursor`
**Implementation:**
```python
def get_top_models(self, limit: int=10) -> List[Dict[str, Any]]:
    """Get most used models by request count."""
    if not self.enabled:
        return []
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('\n                SELECT * FROM model_usage_summary\n                ORDER BY request_count DESC\n                LIMIT ?\n            ', (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception as e:
        logger.error(f'Failed to get top models: {e}')
        return []
```

### Method: `get_daily_model_request_count`
**Logic & Purpose:**
```text
Get request count for a model on a UTC calendar day.
```

**Parameters:** `self, model, date_utc`
**Variables Used:** `target_date, conn, cursor, row`
**Implementation:**
```python
def get_daily_model_request_count(self, model: str, date_utc: Optional[str]=None) -> int:
    """Get request count for a model on a UTC calendar day."""
    if not self.enabled:
        return 0
    target_date = date_utc or datetime.utcnow().strftime('%Y-%m-%d')
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                SELECT request_count\n                FROM daily_model_stats\n                WHERE date = ? AND model = ?\n                ', (target_date, model))
        row = cursor.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        logger.error(f'Failed to get daily model request count: {e}')
        return 0
```

### Method: `get_cost_summary`
**Logic & Purpose:**
```text
Get cost summary for last N days.
```

**Parameters:** `self, days`
**Variables Used:** `conn, cursor, since, row`
**Implementation:**
```python
def get_cost_summary(self, days: int=7) -> Dict[str, Any]:
    """Get cost summary for last N days."""
    if not self.enabled:
        return {}
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute("\n                SELECT\n                    COUNT(*) as total_requests,\n                    SUM(input_tokens) as total_input_tokens,\n                    SUM(output_tokens) as total_output_tokens,\n                    SUM(thinking_tokens) as total_thinking_tokens,\n                    SUM(total_tokens) as total_tokens,\n                    SUM(estimated_cost) as total_cost,\n                    AVG(duration_ms) as avg_duration_ms,\n                    AVG(tokens_per_second) as avg_tokens_per_second\n                FROM api_requests\n                WHERE timestamp >= ? AND status = 'success'\n            ", (since,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return {'total_requests': row[0] or 0, 'total_input_tokens': row[1] or 0, 'total_output_tokens': row[2] or 0, 'total_thinking_tokens': row[3] or 0, 'total_tokens': row[4] or 0, 'total_cost': round(row[5] or 0.0, 4), 'avg_duration_ms': round(row[6] or 0.0, 2), 'avg_tokens_per_second': round(row[7] or 0.0, 2), 'days': days}
        return {}
    except Exception as e:
        logger.error(f'Failed to get cost summary: {e}')
        return {}
```

### Method: `get_json_toon_analysis`
**Logic & Purpose:**
```text
Analyze JSON usage to determine if TOON conversion would help.
```

**Parameters:** `self`
**Variables Used:** `avg_json_size, json_requests, cursor, total_json_bytes, estimated_toon_savings, json_percentage, conn, total_requests, row`
**Implementation:**
```python
def get_json_toon_analysis(self) -> Dict[str, Any]:
    """Analyze JSON usage to determine if TOON conversion would help."""
    if not self.enabled:
        return {}
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("\n                SELECT\n                    COUNT(*) as total_requests,\n                    SUM(CASE WHEN has_json_content = 1 THEN 1 ELSE 0 END) as json_requests,\n                    SUM(json_size_bytes) as total_json_bytes,\n                    AVG(CASE WHEN has_json_content = 1 THEN json_size_bytes ELSE 0 END) as avg_json_size\n                FROM api_requests\n                WHERE timestamp >= datetime('now', '-7 days')\n            ")
        row = cursor.fetchone()
        conn.close()
        if row:
            total_requests = row[0] or 0
            json_requests = row[1] or 0
            total_json_bytes = row[2] or 0
            avg_json_size = row[3] or 0
            estimated_toon_savings = int(total_json_bytes * 0.3)
            json_percentage = json_requests / total_requests * 100 if total_requests > 0 else 0
            return {'total_requests': total_requests, 'json_requests': json_requests, 'json_percentage': round(json_percentage, 1), 'total_json_bytes': total_json_bytes, 'avg_json_size': round(avg_json_size, 0), 'estimated_toon_savings_bytes': estimated_toon_savings, 'recommended': json_percentage > 30 and avg_json_size > 500}
        return {}
    except Exception as e:
        logger.error(f'Failed to analyze JSON usage: {e}')
        return {}
```

### Method: `export_to_csv`
**Logic & Purpose:**
```text
Export usage data to CSV.
```

**Parameters:** `self, output_file, days`
**Variables Used:** `writer, cursor, rows, since, conn`
**Implementation:**
```python
def export_to_csv(self, output_file: str, days: int=30) -> bool:
    """Export usage data to CSV."""
    if not self.enabled:
        return False
    try:
        import csv
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT * FROM api_requests\n                WHERE timestamp >= ?\n                ORDER BY timestamp DESC\n            ', (since,))
        rows = cursor.fetchall()
        if rows:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])
            logger.info(f'Exported {len(rows)} records to {output_file}')
        conn.close()
        return True
    except Exception as e:
        logger.error(f'Failed to export to CSV: {e}')
        return False
```

### Method: `export_to_json`
**Logic & Purpose:**
```text
Export usage data to JSON.
```

**Parameters:** `self, output_file, days`
**Variables Used:** `cursor, data, rows, since, conn`
**Implementation:**
```python
def export_to_json(self, output_file: str, days: int=30) -> bool:
    """Export usage data to JSON."""
    if not self.enabled:
        return False
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT * FROM api_requests\n                WHERE timestamp >= ?\n                ORDER BY timestamp DESC\n            ', (since,))
        rows = cursor.fetchall()
        if rows:
            data = [dict(row) for row in rows]
            with open(output_file, 'w') as f:
                json.dump({'exported_at': datetime.utcnow().isoformat(), 'days': days, 'record_count': len(data), 'records': data}, f, indent=2)
            logger.info(f'Exported {len(rows)} records to {output_file}')
        conn.close()
        return True
    except Exception as e:
        logger.error(f'Failed to export to JSON: {e}')
        return False
```

### Method: `get_time_series_data`
**Logic & Purpose:**
```text
Get time-series data for line charts and graphs.

Returns data points by date for:
- Total tokens per day
- Cost per day
- Request count per day
- Token breakdown per day
```

**Parameters:** `self, days`
**Variables Used:** `cursor, success_rate, result, rows, since, total, conn`
**Implementation:**
```python
def get_time_series_data(self, days: int=14) -> Dict[str, Any]:
    """
        Get time-series data for line charts and graphs.

        Returns data points by date for:
        - Total tokens per day
        - Cost per day
        - Request count per day
        - Token breakdown per day
        """
    if not self.enabled:
        return {'dates': [], 'tokens': [], 'cost': [], 'requests': []}
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT\n                    date,\n                    SUM(total_tokens) as total_tokens,\n                    SUM(total_cost) as total_cost,\n                    SUM(request_count) as total_requests,\n                    SUM(input_tokens) as input_tokens,\n                    SUM(output_tokens) as output_tokens,\n                    SUM(thinking_tokens) as thinking_tokens,\n                    SUM(success_count) as success_count,\n                    SUM(error_count) as error_count\n                FROM daily_model_stats\n                WHERE date >= ?\n                GROUP BY date\n                ORDER BY date\n            ', (since,))
        rows = cursor.fetchall()
        conn.close()
        result = {'dates': [], 'tokens': [], 'cost': [], 'requests': [], 'token_breakdown': {'input': [], 'output': [], 'thinking': []}, 'success_rate': []}
        for row in rows:
            result['dates'].append(row['date'])
            result['tokens'].append(row['total_tokens'] or 0)
            result['cost'].append(round(row['total_cost'] or 0, 4))
            result['requests'].append(row['total_requests'] or 0)
            result['token_breakdown']['input'].append(row['input_tokens'] or 0)
            result['token_breakdown']['output'].append(row['output_tokens'] or 0)
            result['token_breakdown']['thinking'].append(row['thinking_tokens'] or 0)
            total = (row['success_count'] or 0) + (row['error_count'] or 0)
            success_rate = row['success_count'] / total * 100 if total > 0 else 100
            result['success_rate'].append(round(success_rate, 1))
        return result
    except Exception as e:
        logger.error(f'Failed to get time series data: {e}')
        return {'dates': [], 'tokens': [], 'cost': [], 'requests': []}
```

### Method: `get_model_comparison`
**Logic & Purpose:**
```text
Get comparative data for different models over time.

Returns stats by model including:
- Request count
- Average tokens per request
- Cost per 1K tokens
- Average latency
- Provider
```

**Parameters:** `self, days`
**Variables Used:** `cursor, result, rows, since, conn`
**Implementation:**
```python
def get_model_comparison(self, days: int=14) -> List[Dict[str, Any]]:
    """
        Get comparative data for different models over time.

        Returns stats by model including:
        - Request count
        - Average tokens per request
        - Cost per 1K tokens
        - Average latency
        - Provider
        """
    if not self.enabled:
        return []
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT\n                    model,\n                    provider,\n                    SUM(request_count) as total_requests,\n                    AVG(total_tokens / NULLIF(request_count, 0)) as avg_tokens_per_request,\n                    AVG(total_cost / NULLIF(total_tokens, 0) * 1000) as avg_cost_per_1k_tokens,\n                    AVG(avg_duration_ms) as avg_duration_ms,\n                    SUM(has_tools_count) as tool_requests,\n                    SUM(has_images_count) as image_requests\n                FROM daily_model_stats\n                WHERE date >= ?\n                GROUP BY model, provider\n                HAVING total_requests > 0\n                ORDER BY total_requests DESC\n            ', (since,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({'model': row['model'], 'provider': row['provider'], 'total_requests': row['total_requests'], 'avg_tokens_per_request': round(row['avg_tokens_per_request'] or 0, 0), 'avg_cost_per_1k_tokens': round(row['avg_cost_per_1k_tokens'] or 0, 4), 'avg_duration_ms': round(row['avg_duration_ms'] or 0, 1), 'tool_requests': row['tool_requests'], 'image_requests': row['image_requests']})
        return result
    except Exception as e:
        logger.error(f'Failed to get model comparison: {e}')
        return []
```

### Method: `get_savings_data`
**Logic & Purpose:**
```text
Get savings achieved through smart routing.

Returns:
    Total savings, savings by model pair, cost comparison
```

**Parameters:** `self, days`
**Variables Used:** `cursor, result, rows, since, conn`
**Implementation:**
```python
def get_savings_data(self, days: int=14) -> List[Dict[str, Any]]:
    """
        Get savings achieved through smart routing.

        Returns:
            Total savings, savings by model pair, cost comparison
        """
    if not self.enabled:
        return []
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT\n                    original_model,\n                    routed_model,\n                    SUM(request_count) as total_requests,\n                    SUM(original_cost) as total_original_cost,\n                    SUM(actual_cost) as total_actual_cost,\n                    SUM(savings) as total_savings,\n                    AVG(savings_percent) as avg_savings_percent\n                FROM savings_tracking\n                WHERE date >= ?\n                GROUP BY original_model, routed_model\n                ORDER BY total_savings DESC\n            ', (since,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({'original_model': row['original_model'], 'routed_model': row['routed_model'], 'request_count': row['total_requests'], 'original_cost': round(row['total_original_cost'] or 0, 4), 'actual_cost': round(row['total_actual_cost'] or 0, 4), 'total_savings': round(row['total_savings'] or 0, 4), 'avg_savings_percent': round(row['avg_savings_percent'] or 0, 1)})
        return result
    except Exception as e:
        logger.error(f'Failed to get savings data: {e}')
        return []
```

### Method: `get_token_breakdown_stats`
**Logic & Purpose:**
```text
Get detailed token breakdown statistics.

Returns percentages of:
- Prompt tokens
- Completion tokens
- Reasoning tokens
- Cached tokens
- Tool use tokens
- Audio tokens
```

**Parameters:** `self, days`
**Variables Used:** `cursor, since, total, conn, row`
**Implementation:**
```python
def get_token_breakdown_stats(self, days: int=14) -> Dict[str, Any]:
    """
        Get detailed token breakdown statistics.

        Returns percentages of:
        - Prompt tokens
        - Completion tokens
        - Reasoning tokens
        - Cached tokens
        - Tool use tokens
        - Audio tokens
        """
    if not self.enabled:
        return {}
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT\n                    SUM(prompt_tokens) as total_prompt,\n                    SUM(completion_tokens) as total_completion,\n                    SUM(reasoning_tokens) as total_reasoning,\n                    SUM(cached_tokens) as total_cached,\n                    SUM(tool_use_tokens) as total_tool_use,\n                    SUM(audio_tokens) as total_audio,\n                    SUM(total_tokens) as total_tokens,\n                    COUNT(*) as request_count\n                FROM token_breakdown\n                WHERE timestamp >= ?\n            ', (since,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row[7]:
            return {}
        total = row[6] or 0
        if total == 0:
            return {}
        return {'total_tokens': total, 'request_count': row[7], 'prompt': {'absolute': row[0] or 0, 'percentage': round((row[0] or 0) / total * 100, 1)}, 'completion': {'absolute': row[1] or 0, 'percentage': round((row[1] or 0) / total * 100, 1)}, 'reasoning': {'absolute': row[2] or 0, 'percentage': round((row[2] or 0) / total * 100, 1)}, 'cached': {'absolute': row[3] or 0, 'percentage': round((row[3] or 0) / total * 100, 1)}, 'tool_use': {'absolute': row[4] or 0, 'percentage': round((row[4] or 0) / total * 100, 1)}, 'audio': {'absolute': row[5] or 0, 'percentage': round((row[5] or 0) / total * 100, 1)}}
    except Exception as e:
        logger.error(f'Failed to get token breakdown: {e}')
        return {}
```

### Method: `get_provider_stats`
**Logic & Purpose:**
```text
Get provider-level statistics.

Shows which providers are being used and their cost efficiency.
```

**Parameters:** `self, days`
**Variables Used:** `cursor, result, rows, since, tokens, conn`
**Implementation:**
```python
def get_provider_stats(self, days: int=14) -> List[Dict[str, Any]]:
    """
        Get provider-level statistics.

        Shows which providers are being used and their cost efficiency.
        """
    if not self.enabled:
        return []
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cursor.execute('\n                SELECT\n                    provider,\n                    SUM(request_count) as total_requests,\n                    SUM(total_tokens) as total_tokens,\n                    SUM(total_cost) as total_cost,\n                    AVG(avg_duration_ms) as avg_duration_ms,\n                    SUM(has_tools_count) as tool_requests\n                FROM daily_model_stats\n                WHERE date >= ? AND provider IS NOT NULL\n                GROUP BY provider\n                ORDER BY total_cost DESC\n            ', (since,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            tokens = row['total_tokens'] or 0
            result.append({'provider': row['provider'], 'total_requests': row['total_requests'], 'total_tokens': tokens, 'total_cost': round(row['total_cost'] or 0, 4), 'avg_cost_per_1k_tokens': round((row['total_cost'] or 0) / tokens * 1000 if tokens > 0 else 0, 4), 'avg_duration_ms': round(row['avg_duration_ms'] or 0, 1), 'tool_requests': row['tool_requests']})
        return result
    except Exception as e:
        logger.error(f'Failed to get provider stats: {e}')
        return []
```

### Method: `get_dashboard_summary`
**Logic & Purpose:**
```text
Get comprehensive dashboard summary with all visualization data.

Combines all analytics into one call for efficient dashboard rendering.
```

**Parameters:** `self, days`
**Variables Used:** `token_stats, total_savings, avg_savings_percent, savings, models, overall, providers, time_series`
**Implementation:**
```python
def get_dashboard_summary(self, days: int=7) -> Dict[str, Any]:
    """
        Get comprehensive dashboard summary with all visualization data.

        Combines all analytics into one call for efficient dashboard rendering.
        """
    if not self.enabled:
        return {}
    try:
        time_series = self.get_time_series_data(days)
        models = self.get_model_comparison(days)
        savings = self.get_savings_data(days)
        token_stats = self.get_token_breakdown_stats(days)
        providers = self.get_provider_stats(days)
        overall = self.get_cost_summary(days)
        total_savings = sum((s['total_savings'] for s in savings))
        avg_savings_percent = sum((s['avg_savings_percent'] for s in savings)) / len(savings) if savings else 0
        return {'summary': {'total_requests': overall.get('total_requests', 0), 'total_tokens': overall.get('total_tokens', 0), 'total_cost': overall.get('total_cost', 0), 'avg_latency_ms': overall.get('avg_duration_ms', 0), 'total_savings': round(total_savings, 4), 'avg_savings_percent': round(avg_savings_percent, 1), 'days': days}, 'time_series': time_series, 'models': models, 'savings': savings, 'token_breakdown': token_stats, 'providers': providers}
    except Exception as e:
        logger.error(f'Failed to get dashboard summary: {e}')
        return {}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/usage/model_limits.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/usage/model_limits.py`

**Module Overview**: 
```text
Model context window and output limits database.

Loads model limits from scraped OpenRouter data (CSV/JSON files).
Falls back to static database if files don't exist.

Run `python dev/scripts/scrape_openrouter_models.py` to update the database.

NOTE: This module uses dynamic model family detection as a fallback when specific
model limits aren't found. See src/services/models/model_family.py for detection logic.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `FAMILY_FALLBACK_LIMITS` = `{ModelFamily.OPENAI_O_SERIES: {'context': 128000, 'output': 32768}, ModelFamily.OPENAI_GPT: {'context': 128000, 'output': 16384}, ModelFamily.ANTHROPIC_CLAUDE: {'context': 200000, 'output': 16384}, ModelFamily.GEMINI_FLASH: {'context': 1000000, 'output': 8192}, ModelFamily.GEMINI_PRO: {'context': 1000000, 'output': 8192}, ModelFamily.GEMINI_OTHER: {'context': 1000000, 'output': 8192}}`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent.parent`
- `MODELS_DIR` = `Path(__file__).parent.parent.parent / 'models'`
- `JSON_PATH` = `MODELS_DIR / 'model_limits.json'`
- `ENRICHED_PATH` = `PROJECT_ROOT / 'data' / 'openrouter_models_enriched.json'`

## Dependencies & Imports
typing.Dict, typing.Optional, typing.Tuple, logging, json, pathlib.Path, src.services.models.model_family.detect_model_family, src.services.models.model_family.ModelFamily

## Feature Function: `_load_model_limits`
**Logic & Purpose:**
```text
Load model limits from JSON file or return fallback.

Priority order:
1. data/openrouter_models_enriched.json (richest, most up-to-date)
2. models/model_limits.json (legacy)
3. Static fallback
```

**Parameters:** ``
**Variables Used:** `model_id, limits, _MODEL_LIMITS_CACHE, data`
**Implementation:**
```python
def _load_model_limits() -> Dict[str, Dict[str, int]]:
    """Load model limits from JSON file or return fallback.

    Priority order:
    1. data/openrouter_models_enriched.json (richest, most up-to-date)
    2. models/model_limits.json (legacy)
    3. Static fallback
    """
    global _MODEL_LIMITS_CACHE
    if _MODEL_LIMITS_CACHE is not None:
        return _MODEL_LIMITS_CACHE
    if ENRICHED_PATH.exists():
        try:
            with open(ENRICHED_PATH, 'r') as f:
                data = json.load(f)
                if 'models' in data:
                    limits = {}
                    for model in data['models']:
                        model_id = model.get('id', '')
                        if model_id:
                            limits[model_id] = {'context': model.get('context_length', 128000), 'output': model.get('max_completion_tokens', 4096) or 4096}
                    _MODEL_LIMITS_CACHE = limits
                    logger.info(f'Loaded {len(limits)} model limits from enriched data ({ENRICHED_PATH.name})')
                    return _MODEL_LIMITS_CACHE
        except Exception as e:
            logger.warning(f'Failed to load enriched model limits: {e}')
    if JSON_PATH.exists():
        try:
            with open(JSON_PATH, 'r') as f:
                data = json.load(f)
                _MODEL_LIMITS_CACHE = data
                logger.info(f'Loaded {len(data)} model limits from {JSON_PATH}')
                return _MODEL_LIMITS_CACHE
        except Exception as e:
            logger.warning(f'Failed to load model limits from {JSON_PATH}: {e}')
    logger.info('Using static fallback model limits (run scraper to update)')
    _MODEL_LIMITS_CACHE = _get_fallback_limits()
    return _MODEL_LIMITS_CACHE
```

---

## Feature Function: `_get_fallback_limits`
**Logic & Purpose:**
```text
Get static fallback model limits.
```

**Parameters:** ``
**Implementation:**
```python
def _get_fallback_limits() -> Dict[str, Dict[str, int]]:
    """Get static fallback model limits."""
    return {'openai/gpt-4o': {'context': 128000, 'output': 16384}, 'openai/gpt-4o-mini': {'context': 128000, 'output': 16384}, 'openai/o1-preview': {'context': 128000, 'output': 32768}, 'openai/o1-mini': {'context': 128000, 'output': 65536}, 'openai/gpt-5': {'context': 200000, 'output': 100000}, 'anthropic/claude-opus-4-20250514': {'context': 200000, 'output': 16384}, 'anthropic/claude-sonnet-4-20250514': {'context': 200000, 'output': 16384}, 'anthropic/claude-3-5-sonnet-20241022': {'context': 200000, 'output': 8192}, 'google/gemini-2.5-flash-preview-04-17': {'context': 1000000, 'output': 8192}, 'google/gemini-2.0-flash': {'context': 1000000, 'output': 8192}, 'google/gemini-3-flash': {'context': 1000000, 'output': 8192}, 'gemini-3-flash': {'context': 1000000, 'output': 8192}, 'google/gemini-3-Pro-preview': {'context': 1000000, 'output': 8192}, 'gemini-3-pro-preview': {'context': 1000000, 'output': 8192}, 'openrouter/pony-alpha': {'context': 128000, 'output': 4096}, 'openrouter/gpt-oss-120b-medium': {'context': 128000, 'output': 4096}, 'openrouter/hunter-alpha': {'context': 128000, 'output': 4096}, 'openai/gpt-oss-120b:free': {'context': 128000, 'output': 4096}, 'nvidia/nemotron-nano-9b-v2:free': {'context': 128000, 'output': 16384}, 'nvidia/nemotron-3-super-120b-a12b:free': {'context': 131072, 'output': 16384}, 'minimax/minimax-m2.5:free': {'context': 196608, 'output': 16384}, 'openai/gpt-oss-120b:free': {'context': 131072, 'output': 16384}, 'qwen/qwen3-235b-a22b:free': {'context': 40960, 'output': 8192}, 'qwen/qwen3-30b-a3b:free': {'context': 40960, 'output': 8192}, 'meta-llama/llama-3.3-70b': {'context': 128000, 'output': 4096}, 'deepseek/deepseek-v3': {'context': 64000, 'output': 8192}, 'qwen/qwen-2.5-72b': {'context': 32768, 'output': 8192}, 'x-ai/grok-2': {'context': 131072, 'output': 32768}, 'x-ai/grok-4.1-fast:free': {'context': 128000, 'output': 4096}}
```

---

## Feature Function: `get_model_limits`
**Logic & Purpose:**
```text
Get context window and output limits for a model.

Resolution order:
1. Exact match in loaded data
2. Case-insensitive match
3. Partial match (for versioned models)
4. Provider prefix variations
5. Family-based fallback (dynamic detection)
6. Conservative default

Args:
    model_name: Model identifier (e.g., "gpt-4o", "openai/gpt-5")

Returns:
    Tuple of (context_limit, output_limit) in tokens
```

**Parameters:** `model_name`
**Variables Used:** `limits, model_lower, family_info, MODEL_LIMITS, base_name, prefixed`
**Implementation:**
```python
def get_model_limits(model_name: str) -> Tuple[int, int]:
    """
    Get context window and output limits for a model.

    Resolution order:
    1. Exact match in loaded data
    2. Case-insensitive match
    3. Partial match (for versioned models)
    4. Provider prefix variations
    5. Family-based fallback (dynamic detection)
    6. Conservative default

    Args:
        model_name: Model identifier (e.g., "gpt-4o", "openai/gpt-5")

    Returns:
        Tuple of (context_limit, output_limit) in tokens
    """
    MODEL_LIMITS = _load_model_limits()
    if model_name in MODEL_LIMITS:
        limits = MODEL_LIMITS[model_name]
        return (limits['context'], limits['output'])
    model_lower = model_name.lower()
    for key, limits in MODEL_LIMITS.items():
        if key.lower() == model_lower:
            return (limits['context'], limits['output'])
    for key, limits in MODEL_LIMITS.items():
        if key in model_name or model_name in key:
            logger.debug(f'Partial match for {model_name}: using limits from {key}')
            return (limits['context'], limits['output'])
    if '/' in model_name:
        base_name = model_name.split('/', 1)[1]
        if base_name in MODEL_LIMITS:
            limits = MODEL_LIMITS[base_name]
            return (limits['context'], limits['output'])
    if '/' not in model_name:
        for prefix in ['openai/', 'anthropic/', 'google/', 'meta-llama/', 'deepseek/', 'qwen/', 'x-ai/']:
            prefixed = f'{prefix}{model_name}'
            if prefixed in MODEL_LIMITS:
                limits = MODEL_LIMITS[prefixed]
                logger.debug(f'Found {model_name} with prefix: {prefixed}')
                return (limits['context'], limits['output'])
    try:
        family_info = detect_model_family(model_name)
        if family_info.family in FAMILY_FALLBACK_LIMITS:
            limits = FAMILY_FALLBACK_LIMITS[family_info.family]
            logger.debug(f'Using family-based fallback for {model_name}: family={family_info.family.value}')
            return (limits['context'], limits['output'])
    except Exception as e:
        logger.debug(f'Family detection failed for {model_name}: {e}')
    logger.warning(f'Model limits not found for {model_name}, using defaults (1M/32k)')
    return (1000000, 32768)
```

---

## Feature Function: `get_context_limit`
**Logic & Purpose:**
```text
Get context window limit for a model.
```

**Parameters:** `model_name`
**Implementation:**
```python
def get_context_limit(model_name: str) -> int:
    """Get context window limit for a model."""
    context, _ = get_model_limits(model_name)
    return context
```

---

## Feature Function: `get_output_limit`
**Logic & Purpose:**
```text
Get max output tokens for a model.
```

**Parameters:** `model_name`
**Implementation:**
```python
def get_output_limit(model_name: str) -> int:
    """Get max output tokens for a model."""
    _, output = get_model_limits(model_name)
    return output
```

---

## Feature Function: `format_model_info`
**Logic & Purpose:**
```text
Format model limits as a readable string.

Returns:
    String like "128k context / 16k output"
```

**Parameters:** `model_name`
**Implementation:**
```python
def format_model_info(model_name: str) -> str:
    """
    Format model limits as a readable string.

    Returns:
        String like "128k context / 16k output"
    """
    context, output = get_model_limits(model_name)

    def format_tokens(count):
        if count >= 1000000:
            return f'{count / 1000000:.1f}M'
        elif count >= 1000:
            return f'{count / 1000:.0f}k'
        return str(count)
    return f'{format_tokens(context)} context / {format_tokens(output)} output'
```

---

## Feature Function: `reload_model_limits`
**Logic & Purpose:**
```text
Reload model limits from file (useful after running scraper).

Returns:
    Number of models loaded
```

**Parameters:** ``
**Variables Used:** `limits, _MODEL_LIMITS_CACHE`
**Implementation:**
```python
def reload_model_limits() -> int:
    """
    Reload model limits from file (useful after running scraper).

    Returns:
        Number of models loaded
    """
    global _MODEL_LIMITS_CACHE
    _MODEL_LIMITS_CACHE = None
    limits = _load_model_limits()
    return len(limits)
```

---

## Feature Function: `check_model_limits`
**Logic & Purpose:**
```text
Check if request exceeds model limits.

Args:
    model_name: Model identifier
    input_tokens: Estimated input tokens
    max_output_tokens: Requested max output tokens

Returns:
    Tuple of (is_valid, error_message)
```

**Parameters:** `model_name, input_tokens, max_output_tokens`
**Variables Used:** `total_tokens`
**Implementation:**
```python
def check_model_limits(model_name: str, input_tokens: int, max_output_tokens: int=0) -> Tuple[bool, str]:
    """
    Check if request exceeds model limits.

    Args:
        model_name: Model identifier
        input_tokens: Estimated input tokens
        max_output_tokens: Requested max output tokens

    Returns:
        Tuple of (is_valid, error_message)
    """
    context_limit, output_limit = get_model_limits(model_name)
    total_tokens = input_tokens + max_output_tokens
    if total_tokens > context_limit:
        return (False, f'Total tokens ({total_tokens}) exceeds model context limit ({context_limit})')
    if max_output_tokens > output_limit:
        return (False, f'Requested output tokens ({max_output_tokens}) exceeds model output limit ({output_limit})')
    return (True, '')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/ide/ide_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/ide/ide_detector.py`

**Module Overview**: 
```text
IDE Detector Module

Detects the source IDE from incoming requests to apply appropriate
tool name and parameter transformations.

Supported IDEs:
- Claude Code (Anthropic format)
- Antigravity (Anthropic format)
- Codex CLI (OpenAI format)
- Gemini CLI (OpenAI-compatible)
- Qwen Code (OpenAI-compatible)
- OpenCode (OpenAI format)
```

## Global Presets & Variables
- `IDE_CONFIG` = `{IDE.CLAUDE_CODE.value: {'api_format': APIFormat.ANTHROPIC.value, 'user_agent_patterns': ['claude', 'anthropic'], 'tool_prefix': ''}, IDE.ANTIGRAVITY.value: {'api_format': APIFormat.ANTHROPIC.value, 'user_agent_patterns': ['antigravity', 'gemini-ide'], 'tool_prefix': ''}, IDE.CODEX_CLI.value: {'api_format': APIFormat.OPENAI.value, 'user_agent_patterns': ['codex', 'openai-codex'], 'header_markers': ['x-codex-version', 'x-openai-codex'], 'tool_prefix': ''}, IDE.GEMINI_CLI.value: {'api_format': APIFormat.OPENAI.value, 'user_agent_patterns': ['gemini-cli', 'google-gemini'], 'header_markers': ['x-gemini-cli'], 'tool_prefix': ''}, IDE.QWEN_CODE.value: {'api_format': APIFormat.OPENAI.value, 'user_agent_patterns': ['qwen', 'qwen-code'], 'header_markers': ['x-qwen-code'], 'tool_prefix': ''}, IDE.OPENCODE.value: {'api_format': APIFormat.OPENAI.value, 'user_agent_patterns': ['opencode', 'go-opencode'], 'header_markers': ['x-opencode-version'], 'tool_prefix': ''}}`

## Dependencies & Imports
enum.Enum, typing.Optional, typing.Dict, typing.Any

## Feature Class: `IDE`
**Description:**
```text
Supported IDE clients.
```

---

## Feature Class: `APIFormat`
**Description:**
```text
API format types.
```

---

## Feature Function: `detect_ide_from_headers`
**Logic & Purpose:**
```text
Detect IDE from request headers.

Args:
    headers: Request headers dict
    
Returns:
    IDE identifier string
```

**Parameters:** `headers`
**Variables Used:** `user_agent, header_markers, patterns`
**Implementation:**
```python
def detect_ide_from_headers(headers: Dict[str, str]) -> str:
    """
    Detect IDE from request headers.
    
    Args:
        headers: Request headers dict
        
    Returns:
        IDE identifier string
    """
    user_agent = headers.get('user-agent', '').lower()
    for ide, config in IDE_CONFIG.items():
        header_markers = config.get('header_markers', [])
        for marker in header_markers:
            if marker.lower() in [h.lower() for h in headers.keys()]:
                return ide
    for ide, config in IDE_CONFIG.items():
        patterns = config.get('user_agent_patterns', [])
        for pattern in patterns:
            if pattern.lower() in user_agent:
                return ide
    return IDE.UNKNOWN.value
```

---

## Feature Function: `detect_ide_from_endpoint`
**Logic & Purpose:**
```text
Detect IDE type from endpoint path.

Args:
    path: Request URL path
    
Returns:
    API format (anthropic or openai)
```

**Parameters:** `path`
**Variables Used:** `path_lower`
**Implementation:**
```python
def detect_ide_from_endpoint(path: str) -> str:
    """
    Detect IDE type from endpoint path.
    
    Args:
        path: Request URL path
        
    Returns:
        API format (anthropic or openai)
    """
    path_lower = path.lower()
    if '/messages' in path_lower:
        return APIFormat.ANTHROPIC.value
    if '/chat/completions' in path_lower:
        return APIFormat.OPENAI.value
    return APIFormat.ANTHROPIC.value
```

---

## Feature Function: `detect_ide_from_body`
**Logic & Purpose:**
```text
Detect IDE from request body structure.

Args:
    body: Request body dict
    
Returns:
    IDE identifier or UNKNOWN
```

**Parameters:** `body`
**Variables Used:** `first_msg, messages, content, tools, first_tool`
**Implementation:**
```python
def detect_ide_from_body(body: Dict[str, Any]) -> str:
    """
    Detect IDE from request body structure.
    
    Args:
        body: Request body dict
        
    Returns:
        IDE identifier or UNKNOWN
    """
    if 'messages' in body:
        messages = body.get('messages', [])
        if messages and isinstance(messages, list):
            first_msg = messages[0] if messages else {}
            content = first_msg.get('content', '')
            if isinstance(content, list):
                return IDE.CLAUDE_CODE.value
    tools = body.get('tools', [])
    if tools and isinstance(tools, list):
        first_tool = tools[0] if tools else {}
        if 'input_schema' in first_tool:
            return IDE.CLAUDE_CODE.value
        if 'function' in first_tool:
            return IDE.CODEX_CLI.value
    return IDE.UNKNOWN.value
```

---

## Feature Function: `detect_ide`
**Logic & Purpose:**
```text
Detect the source IDE from request data.

Priority:
1. Specific headers (most reliable)
2. User-Agent patterns
3. Request body structure
4. Endpoint path

Args:
    headers: Request headers
    path: Request URL path
    body: Request body
    
Returns:
    IDE identifier string
```

**Parameters:** `headers, path, body`
**Variables Used:** `api_format, ide`
**Implementation:**
```python
def detect_ide(headers: Optional[Dict[str, str]]=None, path: Optional[str]=None, body: Optional[Dict[str, Any]]=None) -> str:
    """
    Detect the source IDE from request data.
    
    Priority:
    1. Specific headers (most reliable)
    2. User-Agent patterns
    3. Request body structure
    4. Endpoint path
    
    Args:
        headers: Request headers
        path: Request URL path
        body: Request body
        
    Returns:
        IDE identifier string
    """
    if headers:
        ide = detect_ide_from_headers(headers)
        if ide != IDE.UNKNOWN.value:
            return ide
    if body:
        ide = detect_ide_from_body(body)
        if ide != IDE.UNKNOWN.value:
            return ide
    if path:
        api_format = detect_ide_from_endpoint(path)
        if api_format == APIFormat.ANTHROPIC.value:
            return IDE.CLAUDE_CODE.value
        elif api_format == APIFormat.OPENAI.value:
            return IDE.CODEX_CLI.value
    return IDE.UNKNOWN.value
```

---

## Feature Function: `get_api_format`
**Logic & Purpose:**
```text
Get the API format for an IDE.

Args:
    ide: IDE identifier
    
Returns:
    API format (anthropic or openai)
```

**Parameters:** `ide`
**Variables Used:** `config`
**Implementation:**
```python
def get_api_format(ide: str) -> str:
    """
    Get the API format for an IDE.
    
    Args:
        ide: IDE identifier
        
    Returns:
        API format (anthropic or openai)
    """
    config = IDE_CONFIG.get(ide, {})
    return config.get('api_format', APIFormat.OPENAI.value)
```

---

## Feature Function: `is_anthropic_format`
**Logic & Purpose:**
```text
Check if IDE uses Anthropic API format.
```

**Parameters:** `ide`
**Implementation:**
```python
def is_anthropic_format(ide: str) -> bool:
    """Check if IDE uses Anthropic API format."""
    return get_api_format(ide) == APIFormat.ANTHROPIC.value
```

---

## Feature Function: `is_openai_format`
**Logic & Purpose:**
```text
Check if IDE uses OpenAI API format.
```

**Parameters:** `ide`
**Implementation:**
```python
def is_openai_format(ide: str) -> bool:
    """Check if IDE uses OpenAI API format."""
    return get_api_format(ide) == APIFormat.OPENAI.value
```

---

## Feature Function: `get_ide_info`
**Logic & Purpose:**
```text
Get full configuration for an IDE.

Args:
    ide: IDE identifier
    
Returns:
    IDE configuration dict
```

**Parameters:** `ide`
**Implementation:**
```python
def get_ide_info(ide: str) -> Dict[str, Any]:
    """
    Get full configuration for an IDE.
    
    Args:
        ide: IDE identifier
        
    Returns:
        IDE configuration dict
    """
    return IDE_CONFIG.get(ide, {'api_format': APIFormat.OPENAI.value, 'user_agent_patterns': [], 'tool_prefix': ''})
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/ide/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/ide/__init__.py`

**Module Overview**: 
```text
IDE Services Module

Provides IDE detection and configuration for cross-IDE support.
```

## Global Presets & Variables
- `__all__` = `['IDE', 'APIFormat', 'IDE_CONFIG', 'detect_ide', 'detect_ide_from_headers', 'detect_ide_from_endpoint', 'detect_ide_from_body', 'get_api_format', 'is_anthropic_format', 'is_openai_format', 'get_ide_info']`

## Dependencies & Imports
ide_detector.IDE, ide_detector.APIFormat, ide_detector.IDE_CONFIG, ide_detector.detect_ide, ide_detector.detect_ide_from_headers, ide_detector.detect_ide_from_endpoint, ide_detector.detect_ide_from_body, ide_detector.get_api_format, ide_detector.is_anthropic_format, ide_detector.is_openai_format, ide_detector.get_ide_info


# File Audit: /home/cheta/code/claude-code-proxy/src/services/providers/kiro_token_manager.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/providers/kiro_token_manager.py`

**Module Overview**: 
```text
Kiro Token Manager - Access & Refresh Token Handling

Manages Kiro authentication tokens (access + refresh) for the Kiro provider.
Kiro uses OAuth-style token authentication similar to VibeProxy.

Features:
- Token storage and retrieval
- Access token management
- Refresh token handling (for future auto-refresh)
- Token validation
- Token refresh capability

Author: AI Architect
Date: 2026-01-05
```

## Dependencies & Imports
os, json, time, typing.Optional, typing.Dict, typing.Any, datetime.datetime, datetime.timedelta, dataclasses.dataclass, dataclasses.asdict, src.core.logging.logger

## Feature Class: `KiroTokens`
**Description:**
```text
Kiro authentication tokens.
```

### Method: `is_expired`
**Logic & Purpose:**
```text
Check if access token is expired.
```

**Parameters:** `self`
**Implementation:**
```python
def is_expired(self) -> bool:
    """Check if access token is expired."""
    if not self.expires_at:
        return False
    return time.time() >= self.expires_at
```

### Method: `is_valid`
**Logic & Purpose:**
```text
Check if tokens are valid.
```

**Parameters:** `self`
**Implementation:**
```python
def is_valid(self) -> bool:
    """Check if tokens are valid."""
    if not self.access_token:
        return False
    if self.is_expired():
        return False
    return True
```

### Method: `to_dict`
**Logic & Purpose:**
```text
Convert to dictionary for storage.
```

**Parameters:** `self`
**Implementation:**
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary for storage."""
    return asdict(self)
```

### Method: `from_dict`
**Logic & Purpose:**
```text
Create from dictionary.
```

**Parameters:** `cls, data`
**Implementation:**
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'KiroTokens':
    """Create from dictionary."""
    return cls(access_token=data.get('access_token', ''), refresh_token=data.get('refresh_token'), token_type=data.get('token_type', 'Bearer'), expires_at=data.get('expires_at'))
```

---

## Feature Class: `KiroTokenManager`
**Description:**
```text
Manager for Kiro authentication tokens.
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize Kiro token manager.

Args:
    storage_path: Optional path for token storage file
```

**Parameters:** `self, storage_path`
**Implementation:**
```python
def __init__(self, storage_path: str=None):
    """
        Initialize Kiro token manager.

        Args:
            storage_path: Optional path for token storage file
        """
    self.storage_path = storage_path or os.path.expanduser('~/.claude-proxy/kiro_tokens.json')
    self.tokens: Optional[KiroTokens] = None
    self._load_tokens()
```

### Method: `_load_tokens`
**Logic & Purpose:**
```text
Load tokens from storage.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def _load_tokens(self):
    """Load tokens from storage."""
    try:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.tokens = KiroTokens.from_dict(data)
                logger.info(f'✅ Loaded Kiro tokens from {self.storage_path}')
        else:
            logger.debug('No existing Kiro tokens found')
    except Exception as e:
        logger.error(f'❌ Failed to load Kiro tokens: {e}')
        self.tokens = None
```

### Method: `_save_tokens`
**Logic & Purpose:**
```text
Save tokens to storage.
```

**Parameters:** `self`
**Implementation:**
```python
def _save_tokens(self):
    """Save tokens to storage."""
    try:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            if self.tokens:
                json.dump(self.tokens.to_dict(), f, indent=2)
            else:
                json.dump({}, f)
        logger.debug(f'💾 Saved Kiro tokens to {self.storage_path}')
    except Exception as e:
        logger.error(f'❌ Failed to save Kiro tokens: {e}')
```

### Method: `store_tokens`
**Logic & Purpose:**
```text
Store Kiro tokens.

Args:
    access_token: The access token
    refresh_token: Optional refresh token
    expires_in: Token lifetime in seconds (optional)
```

**Parameters:** `self, access_token, refresh_token, expires_in`
**Variables Used:** `expires_at`
**Implementation:**
```python
def store_tokens(self, access_token: str, refresh_token: str=None, expires_in: int=None):
    """
        Store Kiro tokens.

        Args:
            access_token: The access token
            refresh_token: Optional refresh token
            expires_in: Token lifetime in seconds (optional)
        """
    expires_at = None
    if expires_in:
        expires_at = int(time.time()) + expires_in
    self.tokens = KiroTokens(access_token=access_token, refresh_token=refresh_token, expires_at=expires_at)
    self._save_tokens()
    logger.info('✅ Kiro tokens stored successfully')
```

### Method: `get_access_token`
**Logic & Purpose:**
```text
Get current access token.

Args:
    auto_refresh: If True and token is expired, attempt auto-refresh

Returns:
    Access token string or None if not available/expired
```

**Parameters:** `self, auto_refresh`
**Implementation:**
```python
def get_access_token(self, auto_refresh: bool=True) -> Optional[str]:
    """
        Get current access token.

        Args:
            auto_refresh: If True and token is expired, attempt auto-refresh

        Returns:
            Access token string or None if not available/expired
        """
    if not self.tokens:
        logger.debug('No Kiro tokens available')
        return None
    if self.tokens.is_expired():
        logger.warning('⚠️ Kiro access token has expired')
        if auto_refresh and self.tokens.refresh_token:
            logger.info('🔄 Attempting auto-refresh...')
            if self.refresh_tokens():
                logger.info('✅ Token refresh successful')
                return self.tokens.access_token
            else:
                logger.error('❌ Token refresh failed')
        return None
    if not self.tokens.is_valid():
        logger.warning('⚠️ Kiro tokens are invalid')
        return None
    return self.tokens.access_token
```

### Method: `has_valid_token`
**Logic & Purpose:**
```text
Check if valid token is available.
```

**Parameters:** `self`
**Variables Used:** `token`
**Implementation:**
```python
def has_valid_token(self) -> bool:
    """Check if valid token is available."""
    token = self.get_access_token()
    return token is not None
```

### Method: `clear_tokens`
**Logic & Purpose:**
```text
Clear stored tokens.
```

**Parameters:** `self`
**Implementation:**
```python
def clear_tokens(self):
    """Clear stored tokens."""
    self.tokens = None
    try:
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
            logger.info('🗑️ Cleared Kiro tokens')
    except Exception as e:
        logger.error(f'❌ Failed to clear tokens: {e}')
```

### Method: `get_auth_header`
**Logic & Purpose:**
```text
Get authentication header for Kiro requests.

Returns:
    Dictionary with Authorization header or empty dict
```

**Parameters:** `self`
**Variables Used:** `token`
**Implementation:**
```python
def get_auth_header(self) -> Optional[Dict[str, str]]:
    """
        Get authentication header for Kiro requests.

        Returns:
            Dictionary with Authorization header or empty dict
        """
    token = self.get_access_token()
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}
```

### Method: `refresh_tokens`
**Logic & Purpose:**
```text
Refresh tokens using refresh token.

Kiro uses OAuth2-style token refresh:
POST https://auth.kiro.dev/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token={refresh_token}
&client_id={client_id}
&client_secret={client_secret}

Returns:
    True if refresh successful, False otherwise
```

**Parameters:** `self`
**Variables Used:** `result, client_id, data, client_secret, new_refresh, new_access, response, expires_in, token_url`
**Implementation:**
```python
def refresh_tokens(self) -> bool:
    """
        Refresh tokens using refresh token.
        
        Kiro uses OAuth2-style token refresh:
        POST https://auth.kiro.dev/oauth/token
        Content-Type: application/x-www-form-urlencoded
        
        grant_type=refresh_token
        &refresh_token={refresh_token}
        &client_id={client_id}
        &client_secret={client_secret}
        
        Returns:
            True if refresh successful, False otherwise
        """
    if not self.tokens or not self.tokens.refresh_token:
        logger.warning('⚠️ No refresh token available')
        return False
    try:
        import httpx
        token_url = 'https://auth.kiro.dev/oauth/token'
        client_id = os.getenv('KIRO_CLIENT_ID', 'kiro-cli')
        client_secret = os.getenv('KIRO_CLIENT_SECRET', '')
        data = {'grant_type': 'refresh_token', 'refresh_token': self.tokens.refresh_token, 'client_id': client_id, 'client_secret': client_secret}
        logger.debug(f'🔄 Refreshing Kiro token from {token_url}')
        with httpx.Client(timeout=30.0) as client:
            response = client.post(token_url, data=data)
            response.raise_for_status()
            result = response.json()
            new_access = result.get('access_token')
            new_refresh = result.get('refresh_token')
            expires_in = result.get('expires_in', 3600)
            if new_access:
                self.store_tokens(access_token=new_access, refresh_token=new_refresh or self.tokens.refresh_token, expires_in=expires_in)
                logger.info('✅ Kiro tokens refreshed successfully')
                return True
            else:
                logger.error('❌ No access token in refresh response')
                return False
    except httpx.HTTPStatusError as e:
        logger.error(f'❌ Token refresh HTTP error: {e.response.status_code} - {e.response.text}')
        return False
    except httpx.RequestError as e:
        logger.error(f'❌ Token refresh request failed: {e}')
        return False
    except Exception as e:
        logger.error(f'❌ Token refresh failed: {e}')
        return False
```

### Method: `get_token_info`
**Logic & Purpose:**
```text
Get token information for diagnostics.

Returns:
    Dictionary with token metadata
```

**Parameters:** `self`
**Variables Used:** `info`
**Implementation:**
```python
def get_token_info(self) -> Dict[str, Any]:
    """
        Get token information for diagnostics.

        Returns:
            Dictionary with token metadata
        """
    if not self.tokens:
        return {'status': 'no_tokens'}
    info = {'status': 'valid' if self.tokens.is_valid() else 'invalid', 'expired': self.tokens.is_expired(), 'has_refresh_token': self.tokens.refresh_token is not None}
    if self.tokens.expires_at:
        info['expires_at'] = datetime.fromtimestamp(self.tokens.expires_at).isoformat()
        info['seconds_until_expiry'] = max(0, self.tokens.expires_at - int(time.time()))
    return info
```

---

## Feature Function: `get_token_manager`
**Logic & Purpose:**
```text
Get or create global Kiro token manager instance.
```

**Parameters:** ``
**Variables Used:** `_token_manager`
**Implementation:**
```python
def get_token_manager() -> KiroTokenManager:
    """Get or create global Kiro token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = KiroTokenManager()
    return _token_manager
```

---

## Feature Function: `store_kiro_tokens`
**Logic & Purpose:**
```text
Convenience function to store Kiro tokens.

Args:
    access_token: Access token from Kiro
    refresh_token: Refresh token (optional)
    expires_in: Token lifetime in seconds

Returns:
    True if successful
```

**Parameters:** `access_token, refresh_token, expires_in`
**Variables Used:** `manager`
**Implementation:**
```python
def store_kiro_tokens(access_token: str, refresh_token: str=None, expires_in: int=None) -> bool:
    """
    Convenience function to store Kiro tokens.

    Args:
        access_token: Access token from Kiro
        refresh_token: Refresh token (optional)
        expires_in: Token lifetime in seconds

    Returns:
        True if successful
    """
    try:
        manager = get_token_manager()
        manager.store_tokens(access_token, refresh_token, expires_in)
        return True
    except Exception as e:
        logger.error(f'Failed to store Kiro tokens: {e}')
        return False
```

---

## Feature Function: `get_kiro_auth_header`
**Logic & Purpose:**
```text
Get authentication header for Kiro API requests.

Returns:
    Dict with Authorization header or empty dict if no valid token
```

**Parameters:** ``
**Variables Used:** `manager`
**Implementation:**
```python
def get_kiro_auth_header() -> Dict[str, str]:
    """
    Get authentication header for Kiro API requests.

    Returns:
        Dict with Authorization header or empty dict if no valid token
    """
    manager = get_token_manager()
    return manager.get_auth_header()
```

---

## Feature Function: `has_kiro_token`
**Logic & Purpose:**
```text
Check if valid Kiro token is available.
```

**Parameters:** ``
**Variables Used:** `manager`
**Implementation:**
```python
def has_kiro_token() -> bool:
    """Check if valid Kiro token is available."""
    manager = get_token_manager()
    return manager.has_valid_token()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/providers/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/providers/__init__.py`

**Module Overview**: 
```text
Provider detection and adapter module for multi-provider support.
```

## Global Presets & Variables
- `__all__` = `['Provider', 'NormalizationLevel', 'AuthType', 'detect_provider', 'get_normalization_level', 'get_auth_type', 'get_provider_info', 'requires_oauth', 'requires_full_normalization', 'skip_normalization', 'get_provider_config', 'PROVIDER_CONFIG']`

## Dependencies & Imports
src.services.providers.provider_detector.Provider, src.services.providers.provider_detector.NormalizationLevel, src.services.providers.provider_detector.AuthType, src.services.providers.provider_detector.detect_provider, src.services.providers.provider_detector.get_normalization_level, src.services.providers.provider_detector.get_auth_type, src.services.providers.provider_detector.get_provider_info, src.services.providers.provider_detector.requires_oauth, src.services.providers.provider_detector.requires_full_normalization, src.services.providers.provider_detector.skip_normalization, src.services.providers.provider_detector.get_provider_config, src.services.providers.provider_detector.PROVIDER_CONFIG


# File Audit: /home/cheta/code/claude-code-proxy/src/services/providers/provider_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/providers/provider_detector.py`

**Module Overview**: 
```text
Provider Detection and Adapter Module.

This module provides provider detection and normalization level configuration
for multi-provider proxy support. It enables the Claude Code proxy to work
with any LLM provider (Gemini, OpenRouter, OpenAI, Anthropic, Azure, etc.)
by applying appropriate transformations based on the detected provider.
```

## Global Presets & Variables
- `PROVIDER_CONFIG` = `{Provider.GEMINI.value: {'name': 'Gemini (VibeProxy)', 'normalization': NormalizationLevel.FULL.value, 'auth': AuthType.OAUTH.value, 'supports_streaming': True, 'has_ghost_streams': True, 'requires_deduplication': True}, Provider.OPENROUTER.value: {'name': 'OpenRouter', 'normalization': NormalizationLevel.LIGHT.value, 'auth': AuthType.API_KEY.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}, Provider.OPENAI.value: {'name': 'OpenAI', 'normalization': NormalizationLevel.NONE.value, 'auth': AuthType.API_KEY.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}, Provider.ANTHROPIC.value: {'name': 'Anthropic', 'normalization': NormalizationLevel.SCHEMA_CONVERT.value, 'auth': AuthType.API_KEY.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}, Provider.AZURE.value: {'name': 'Azure OpenAI', 'normalization': NormalizationLevel.NONE.value, 'auth': AuthType.AZURE.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}, Provider.KIRO.value: {'name': 'Kiro (Claude API Compatible)', 'normalization': NormalizationLevel.LIGHT.value, 'auth': AuthType.KIRO_TOKEN.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}, Provider.OPENAI_COMPATIBLE.value: {'name': 'OpenAI-Compatible', 'normalization': NormalizationLevel.LIGHT.value, 'auth': AuthType.API_KEY.value, 'supports_streaming': True, 'has_ghost_streams': False, 'requires_deduplication': False}}`

## Dependencies & Imports
typing.Tuple, enum.Enum

## Feature Class: `Provider`
**Description:**
```text
Supported LLM providers.
```

---

## Feature Class: `NormalizationLevel`
**Description:**
```text
Tool call normalization intensity levels.

NONE: Pass through unchanged (OpenAI, Azure)
LIGHT: Common mismatches only (OpenRouter, unknown)
FULL: All 18+ tool transformations (Gemini)
SCHEMA_CONVERT: Convert different schema format (Anthropic direct)
```

---

## Feature Class: `AuthType`
**Description:**
```text
Authentication types for different providers.
```

---

## Feature Function: `detect_provider`
**Logic & Purpose:**
```text
Detect the LLM provider from the base URL.

Args:
    base_url: The API base URL
    
Returns:
    Provider identifier string
```

**Parameters:** `base_url`
**Variables Used:** `url_lower`
**Implementation:**
```python
def detect_provider(base_url: str) -> str:
    """
    Detect the LLM provider from the base URL.
    
    Args:
        base_url: The API base URL
        
    Returns:
        Provider identifier string
    """
    if not base_url:
        return Provider.OPENAI_COMPATIBLE.value
    url_lower = base_url.lower()
    if '127.0.0.1:8317' in url_lower or 'localhost:8317' in url_lower:
        return Provider.GEMINI.value
    if 'generativelanguage.googleapis.com' in url_lower or 'gemini' in url_lower:
        return Provider.GEMINI.value
    if 'openrouter.ai' in url_lower:
        return Provider.OPENROUTER.value
    if 'anthropic.com' in url_lower:
        return Provider.ANTHROPIC.value
    if 'azure' in url_lower or '.openai.azure.com' in url_lower:
        return Provider.AZURE.value
    if 'api.openai.com' in url_lower:
        return Provider.OPENAI.value
    if 'kiro' in url_lower or '127.0.0.1:8083' in url_lower or 'localhost:8083' in url_lower or ('kiro.ai' in url_lower):
        return Provider.KIRO.value
    return Provider.OPENAI_COMPATIBLE.value
```

---

## Feature Function: `get_normalization_level`
**Logic & Purpose:**
```text
Get the appropriate normalization level for a provider.

Args:
    provider: Provider identifier from detect_provider()
    
Returns:
    NormalizationLevel value
```

**Parameters:** `provider`
**Variables Used:** `normalization_map`
**Implementation:**
```python
def get_normalization_level(provider: str) -> str:
    """
    Get the appropriate normalization level for a provider.
    
    Args:
        provider: Provider identifier from detect_provider()
        
    Returns:
        NormalizationLevel value
    """
    normalization_map = {Provider.GEMINI.value: NormalizationLevel.FULL.value, Provider.OPENROUTER.value: NormalizationLevel.LIGHT.value, Provider.OPENAI.value: NormalizationLevel.NONE.value, Provider.ANTHROPIC.value: NormalizationLevel.SCHEMA_CONVERT.value, Provider.AZURE.value: NormalizationLevel.NONE.value, Provider.KIRO.value: NormalizationLevel.LIGHT.value, Provider.OPENAI_COMPATIBLE.value: NormalizationLevel.LIGHT.value}
    return normalization_map.get(provider, NormalizationLevel.LIGHT.value)
```

---

## Feature Function: `get_auth_type`
**Logic & Purpose:**
```text
Get the authentication type for a provider.

Args:
    provider: Provider identifier from detect_provider()
    
Returns:
    AuthType value
```

**Parameters:** `provider`
**Variables Used:** `auth_map`
**Implementation:**
```python
def get_auth_type(provider: str) -> str:
    """
    Get the authentication type for a provider.
    
    Args:
        provider: Provider identifier from detect_provider()
        
    Returns:
        AuthType value
    """
    auth_map = {Provider.GEMINI.value: AuthType.OAUTH.value, Provider.AZURE.value: AuthType.AZURE.value, Provider.KIRO.value: AuthType.KIRO_TOKEN.value}
    return auth_map.get(provider, AuthType.API_KEY.value)
```

---

## Feature Function: `get_provider_info`
**Logic & Purpose:**
```text
Get complete provider information from a base URL.

Args:
    base_url: The API base URL
    
Returns:
    Tuple of (provider, normalization_level, auth_type)
```

**Parameters:** `base_url`
**Variables Used:** `normalization, auth, provider`
**Implementation:**
```python
def get_provider_info(base_url: str) -> Tuple[str, str, str]:
    """
    Get complete provider information from a base URL.
    
    Args:
        base_url: The API base URL
        
    Returns:
        Tuple of (provider, normalization_level, auth_type)
    """
    provider = detect_provider(base_url)
    normalization = get_normalization_level(provider)
    auth = get_auth_type(provider)
    return (provider, normalization, auth)
```

---

## Feature Function: `requires_oauth`
**Logic & Purpose:**
```text
Check if a URL requires OAuth authentication (Gemini/VibeProxy).

Args:
    base_url: The API base URL

Returns:
    True if OAuth is required
```

**Parameters:** `base_url`
**Variables Used:** `provider`
**Implementation:**
```python
def requires_oauth(base_url: str) -> bool:
    """
    Check if a URL requires OAuth authentication (Gemini/VibeProxy).

    Args:
        base_url: The API base URL

    Returns:
        True if OAuth is required
    """
    provider = detect_provider(base_url)
    return get_auth_type(provider) == AuthType.OAUTH.value
```

---

## Feature Function: `requires_kiro_token`
**Logic & Purpose:**
```text
Check if a URL requires Kiro token authentication.

Args:
    base_url: The API base URL

Returns:
    True if Kiro token auth is required
```

**Parameters:** `base_url`
**Variables Used:** `provider`
**Implementation:**
```python
def requires_kiro_token(base_url: str) -> bool:
    """
    Check if a URL requires Kiro token authentication.

    Args:
        base_url: The API base URL

    Returns:
        True if Kiro token auth is required
    """
    provider = detect_provider(base_url)
    return get_auth_type(provider) == AuthType.KIRO_TOKEN.value
```

---

## Feature Function: `requires_full_normalization`
**Logic & Purpose:**
```text
Check if a URL requires full tool call normalization.

Args:
    base_url: The API base URL
    
Returns:
    True if full normalization is needed
```

**Parameters:** `base_url`
**Variables Used:** `provider`
**Implementation:**
```python
def requires_full_normalization(base_url: str) -> bool:
    """
    Check if a URL requires full tool call normalization.
    
    Args:
        base_url: The API base URL
        
    Returns:
        True if full normalization is needed
    """
    provider = detect_provider(base_url)
    return get_normalization_level(provider) == NormalizationLevel.FULL.value
```

---

## Feature Function: `skip_normalization`
**Logic & Purpose:**
```text
Check if normalization can be skipped entirely.

Args:
    base_url: The API base URL
    
Returns:
    True if no normalization is needed
```

**Parameters:** `base_url`
**Variables Used:** `provider`
**Implementation:**
```python
def skip_normalization(base_url: str) -> bool:
    """
    Check if normalization can be skipped entirely.
    
    Args:
        base_url: The API base URL
        
    Returns:
        True if no normalization is needed
    """
    provider = detect_provider(base_url)
    return get_normalization_level(provider) == NormalizationLevel.NONE.value
```

---

## Feature Function: `get_provider_config`
**Logic & Purpose:**
```text
Get full configuration for a provider.

Args:
    provider: Provider identifier
    
Returns:
    Configuration dictionary
```

**Parameters:** `provider`
**Implementation:**
```python
def get_provider_config(provider: str) -> dict:
    """
    Get full configuration for a provider.
    
    Args:
        provider: Provider identifier
        
    Returns:
        Configuration dictionary
    """
    return PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG[Provider.OPENAI_COMPATIBLE.value])
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/metrics/session_tracker.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/metrics/session_tracker.py`

**Module Overview**: 
```text
Session Metrics Tracker

Tracks per-session metrics in real-time:
- Token counts (input, output, thinking, cached)
- Tokens/second
- Cost (correlated with model)
- Tool call success/failure rates
- Cache usage
- Request latency

Data is stored in-memory for real-time access and periodically flushed to database.
```

## Dependencies & Imports
asyncio, json, time, collections.defaultdict, dataclasses.dataclass, dataclasses.field, dataclasses.asdict, datetime.datetime, datetime.timedelta, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Any, sqlite3, threading, src.core.logging.logger

## Feature Class: `SessionMetrics`
**Description:**
```text
Metrics for a single session.
```

### Method: `to_dict`
**Logic & Purpose:**
```text
Convert to dictionary.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    data = asdict(self)
    if self.total_latency_ms > 0:
        data['avg_latency_ms'] = round(self.total_latency_ms / max(self.requests, 1), 1)
    if self.output_tokens > 0 and self.total_latency_ms > 0:
        data['tokens_per_second'] = round(self.output_tokens / (self.total_latency_ms / 1000), 1)
    if self.tool_calls_total > 0:
        data['tool_success_rate'] = round(self.tool_calls_success / self.tool_calls_total * 100, 1)
    if self.cached_tokens + self.total_tokens > 0:
        data['cache_hit_rate'] = round(self.cached_tokens / (self.cached_tokens + self.total_tokens) * 100, 1)
    return data
```

---

## Feature Class: `SessionMetricsTracker`
**Description:**
```text
Real-time session metrics tracker.

Usage:
    tracker = SessionMetricsTracker()
    tracker.record_request(session_id, {...})
    tracker.record_tool_call(session_id, "Bash", success=True)
    tracker.get_session_metrics(session_id)
```

### Method: `__init__`
**Parameters:** `self, db_path`
**Implementation:**
```python
def __init__(self, db_path: str='usage_tracking.db'):
    self.sessions: Dict[str, SessionMetrics] = {}
    self.db_path = db_path
    self._lock = threading.Lock()
    self._cleanup_interval = 3600
    self._flush_interval = 60
    self._running = True
    self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    self._flush_task = asyncio.create_task(self._flush_loop())
    logger.info('Session metrics tracker initialized')
```

### Method: `_cleanup_loop`
**Logic & Purpose:**
```text
Clean up stale sessions periodically.
```

**Parameters:** `self`
**Implementation:**
```python
async def _cleanup_loop(self):
    """Clean up stale sessions periodically."""
    while self._running:
        await asyncio.sleep(self._cleanup_interval)
        self._cleanup_stale_sessions()
```

### Method: `_flush_loop`
**Logic & Purpose:**
```text
Flush metrics to database periodically.
```

**Parameters:** `self`
**Implementation:**
```python
async def _flush_loop(self):
    """Flush metrics to database periodically."""
    while self._running:
        await asyncio.sleep(self._flush_interval)
        self._flush_to_database()
```

### Method: `_cleanup_stale_sessions`
**Logic & Purpose:**
```text
Remove sessions inactive for more than 24 hours.
```

**Parameters:** `self`
**Variables Used:** `stale, cutoff, last_activity`
**Implementation:**
```python
def _cleanup_stale_sessions(self):
    """Remove sessions inactive for more than 24 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    stale = []
    with self._lock:
        for session_id, metrics in self.sessions.items():
            last_activity = datetime.fromisoformat(metrics.last_activity)
            if last_activity < cutoff:
                stale.append(session_id)
        for session_id in stale:
            del self.sessions[session_id]
    if stale:
        logger.info(f'Cleaned up {len(stale)} stale sessions')
```

### Method: `_flush_to_database`
**Logic & Purpose:**
```text
Flush current metrics to database.
```

**Parameters:** `self`
**Variables Used:** `conn, cursor`
**Implementation:**
```python
def _flush_to_database(self):
    """Flush current metrics to database."""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('\n                CREATE TABLE IF NOT EXISTS session_metrics (\n                    session_id TEXT PRIMARY KEY,\n                    started_at TEXT,\n                    last_activity TEXT,\n                    input_tokens INTEGER,\n                    output_tokens INTEGER,\n                    thinking_tokens INTEGER,\n                    cached_tokens INTEGER,\n                    total_tokens INTEGER,\n                    requests INTEGER,\n                    total_latency_ms REAL,\n                    estimated_cost REAL,\n                    tool_calls_total INTEGER,\n                    tool_calls_success INTEGER,\n                    tool_calls_failure INTEGER,\n                    cache_hits INTEGER,\n                    cache_misses INTEGER,\n                    models_used TEXT,\n                    tool_call_names TEXT\n                )\n            ')
        with self._lock:
            for session_id, metrics in self.sessions.items():
                cursor.execute('\n                        INSERT OR REPLACE INTO session_metrics \n                        (session_id, started_at, last_activity, input_tokens, output_tokens,\n                         thinking_tokens, cached_tokens, total_tokens, requests,\n                         total_latency_ms, estimated_cost, tool_calls_total,\n                         tool_calls_success, tool_calls_failure, cache_hits,\n                         cache_misses, models_used, tool_call_names)\n                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n                    ', (session_id, metrics.started_at, metrics.last_activity, metrics.input_tokens, metrics.output_tokens, metrics.thinking_tokens, metrics.cached_tokens, metrics.total_tokens, metrics.requests, metrics.total_latency_ms, metrics.estimated_cost, metrics.tool_calls_total, metrics.tool_calls_success, metrics.tool_calls_failure, metrics.cache_hits, metrics.cache_misses, json.dumps(metrics.models_used), json.dumps(metrics.tool_call_names)))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f'Failed to flush session metrics: {e}')
```

### Method: `_get_model_pricing`
**Logic & Purpose:**
```text
Get pricing for a model (input, output per 1M tokens).
```

**Parameters:** `self, model`
**Variables Used:** `model_lower`
**Implementation:**
```python
def _get_model_pricing(self, model: str) -> tuple:
    """Get pricing for a model (input, output per 1M tokens)."""
    model_lower = model.lower()
    for key, pricing in self.MODEL_PRICING.items():
        if key in model_lower:
            return pricing
    return self.MODEL_PRICING['default']
```

### Method: `_calculate_cost`
**Logic & Purpose:**
```text
Calculate estimated cost for a request.
```

**Parameters:** `self, model, input_tokens, output_tokens, cached_tokens`
**Variables Used:** `cached_cost, cached_discount, output_cost, input_cost, effective_input`
**Implementation:**
```python
def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int, cached_tokens: int=0) -> float:
    """Calculate estimated cost for a request."""
    input_price, output_price = self._get_model_pricing(model)
    cached_discount = 0.9
    effective_input = input_tokens - cached_tokens
    cached_cost = cached_tokens / 1000000 * input_price * (1 - cached_discount)
    input_cost = effective_input / 1000000 * input_price
    output_cost = output_tokens / 1000000 * output_price
    return round(input_cost + output_cost + cached_cost, 6)
```

### Method: `record_request`
**Logic & Purpose:**
```text
Record a request for a session.
```

**Parameters:** `self, session_id, model, input_tokens, output_tokens, thinking_tokens, cached_tokens, latency_ms`
**Variables Used:** `cost, metrics, total_tokens`
**Implementation:**
```python
def record_request(self, session_id: str, model: str, input_tokens: int=0, output_tokens: int=0, thinking_tokens: int=0, cached_tokens: int=0, latency_ms: float=0, **kwargs):
    """Record a request for a session."""
    total_tokens = input_tokens + output_tokens + thinking_tokens
    cost = self._calculate_cost(model, input_tokens, output_tokens, cached_tokens)
    with self._lock:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(session_id=session_id)
        metrics = self.sessions[session_id]
        metrics.input_tokens += input_tokens
        metrics.output_tokens += output_tokens
        metrics.thinking_tokens += thinking_tokens
        metrics.cached_tokens += cached_tokens
        metrics.total_tokens += total_tokens
        metrics.requests += 1
        metrics.total_latency_ms += latency_ms
        metrics.estimated_cost += cost
        metrics.last_activity = datetime.utcnow().isoformat()
        if model not in metrics.models_used:
            metrics.models_used[model] = 0
        metrics.models_used[model] += 1
    logger.debug(f'Session {session_id[:8]}: {model} - {total_tokens} tokens, {latency_ms:.0f}ms, ${cost:.6f}')
```

### Method: `record_tool_call`
**Logic & Purpose:**
```text
Record a tool call for a session.
```

**Parameters:** `self, session_id, tool_name, success, error`
**Variables Used:** `metrics`
**Implementation:**
```python
def record_tool_call(self, session_id: str, tool_name: str, success: bool=True, error: Optional[str]=None, **kwargs):
    """Record a tool call for a session."""
    with self._lock:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(session_id=session_id)
        metrics = self.sessions[session_id]
        metrics.tool_calls_total += 1
        if success:
            metrics.tool_calls_success += 1
        else:
            metrics.tool_calls_failure += 1
        if tool_name not in metrics.tool_call_names:
            metrics.tool_call_names.append(tool_name)
        metrics.last_activity = datetime.utcnow().isoformat()
    logger.debug(f"Session {session_id[:8]}: Tool {tool_name} - {('success' if success else 'failure')}")
```

### Method: `record_cache_usage`
**Logic & Purpose:**
```text
Record cache usage for a session.
```

**Parameters:** `self, session_id, cache_hit, cached_tokens, total_tokens`
**Variables Used:** `metrics`
**Implementation:**
```python
def record_cache_usage(self, session_id: str, cache_hit: bool, cached_tokens: int=0, total_tokens: int=0, **kwargs):
    """Record cache usage for a session."""
    with self._lock:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(session_id=session_id)
        metrics = self.sessions[session_id]
        if cache_hit:
            metrics.cache_hits += 1
            metrics.cached_tokens += cached_tokens
        else:
            metrics.cache_misses += 1
        metrics.last_activity = datetime.utcnow().isoformat()
```

### Method: `get_session_metrics`
**Logic & Purpose:**
```text
Get metrics for a specific session.
```

**Parameters:** `self, session_id`
**Implementation:**
```python
def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Get metrics for a specific session."""
    with self._lock:
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id].to_dict()
```

### Method: `get_all_sessions`
**Logic & Purpose:**
```text
Get metrics for all active sessions.
```

**Parameters:** `self`
**Implementation:**
```python
def get_all_sessions(self) -> List[Dict[str, Any]]:
    """Get metrics for all active sessions."""
    with self._lock:
        return [metrics.to_dict() for metrics in self.sessions.values()]
```

### Method: `get_aggregate_metrics`
**Logic & Purpose:**
```text
Get aggregate metrics across all sessions.
```

**Parameters:** `self`
**Variables Used:** `total_sessions, total_tool_success, total_cache_hits, total_cost, avg_tokens, avg_tokens_per_sec, avg_latency, total_tool_calls, total_tokens, total_cached_tokens, total_requests`
**Implementation:**
```python
def get_aggregate_metrics(self) -> Dict[str, Any]:
    """Get aggregate metrics across all sessions."""
    with self._lock:
        total_sessions = len(self.sessions)
        total_requests = sum((m.requests for m in self.sessions.values()))
        total_tokens = sum((m.total_tokens for m in self.sessions.values()))
        total_cost = sum((m.estimated_cost for m in self.sessions.values()))
        total_tool_calls = sum((m.tool_calls_total for m in self.sessions.values()))
        total_tool_success = sum((m.tool_calls_success for m in self.sessions.values()))
        total_cache_hits = sum((m.cache_hits for m in self.sessions.values()))
        total_cached_tokens = sum((m.cached_tokens for m in self.sessions.values()))
        avg_tokens = total_tokens / max(total_requests, 1)
        avg_latency = sum((m.total_latency_ms for m in self.sessions.values())) / max(total_requests, 1)
        avg_tokens_per_sec = sum((m.output_tokens for m in self.sessions.values())) / max(sum((m.total_latency_ms for m in self.sessions.values())) / 1000, 1)
        return {'total_sessions': total_sessions, 'total_requests': total_requests, 'total_tokens': total_tokens, 'total_cost': round(total_cost, 4), 'total_tool_calls': total_tool_calls, 'tool_success_rate': round(total_tool_success / max(total_tool_calls, 1) * 100, 1), 'cache_hit_rate': round(total_cache_hits / max(total_cache_hits + sum((m.cache_misses for m in self.sessions.values())), 1) * 100, 1), 'cached_tokens': total_cached_tokens, 'avg_tokens_per_request': round(avg_tokens, 1), 'avg_latency_ms': round(avg_latency, 1), 'avg_tokens_per_second': round(avg_tokens_per_sec, 1), 'active_sessions': [{'session_id': m.session_id[:8] + '...', 'requests': m.requests, 'tokens': m.total_tokens, 'cost': round(m.estimated_cost, 4), 'tool_success_rate': m.to_dict().get('tool_success_rate', 0)} for m in sorted(self.sessions.values(), key=lambda x: x.last_activity, reverse=True)[:10]]}
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop background tasks and flush final metrics.
```

**Parameters:** `self`
**Implementation:**
```python
def stop(self):
    """Stop background tasks and flush final metrics."""
    self._running = False
    self._flush_to_database()
    logger.info('Session metrics tracker stopped')
```

---

## Feature Function: `get_tracker`
**Logic & Purpose:**
```text
Get or create global tracker instance.
```

**Parameters:** ``
**Variables Used:** `_tracker`
**Implementation:**
```python
def get_tracker() -> SessionMetricsTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SessionMetricsTracker()
    return _tracker
```

---

## Feature Function: `record_request`
**Logic & Purpose:**
```text
Convenience function for recording requests.
```

**Parameters:** ``
**Implementation:**
```python
def record_request(**kwargs):
    """Convenience function for recording requests."""
    get_tracker().record_request(**kwargs)
```

---

## Feature Function: `record_tool_call`
**Logic & Purpose:**
```text
Convenience function for recording tool calls.
```

**Parameters:** ``
**Implementation:**
```python
def record_tool_call(**kwargs):
    """Convenience function for recording tool calls."""
    get_tracker().record_tool_call(**kwargs)
```

---

## Feature Function: `record_cache_usage`
**Logic & Purpose:**
```text
Convenience function for recording cache usage.
```

**Parameters:** ``
**Implementation:**
```python
def record_cache_usage(**kwargs):
    """Convenience function for recording cache usage."""
    get_tracker().record_cache_usage(**kwargs)
```

---

## Feature Function: `get_session_metrics`
**Logic & Purpose:**
```text
Get metrics for a session.
```

**Parameters:** `session_id`
**Implementation:**
```python
def get_session_metrics(session_id: str) -> Optional[Dict[str, Any]]:
    """Get metrics for a session."""
    return get_tracker().get_session_metrics(session_id)
```

---

## Feature Function: `get_all_sessions`
**Logic & Purpose:**
```text
Get all session metrics.
```

**Parameters:** ``
**Implementation:**
```python
def get_all_sessions() -> List[Dict[str, Any]]:
    """Get all session metrics."""
    return get_tracker().get_all_sessions()
```

---

## Feature Function: `get_aggregate_metrics`
**Logic & Purpose:**
```text
Get aggregate metrics.
```

**Parameters:** ``
**Implementation:**
```python
def get_aggregate_metrics() -> Dict[str, Any]:
    """Get aggregate metrics."""
    return get_tracker().get_aggregate_metrics()
```

---


