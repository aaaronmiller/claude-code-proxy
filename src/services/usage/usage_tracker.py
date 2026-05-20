"""
Actual API usage tracking system (opt-in).

Tracks real API requests for analytics, cost analysis, and optimization.
Stores data in SQLite for persistence and efficient querying.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


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

    # Check for empty or whitespace-only content
    stripped = content.strip()
    if not stripped:
        return None

    # Filter out "(no content)" and similar placeholders
    no_content_patterns = [
        "(no content)",
        "no content",
        "claude: (no content)",
        "claude: no content",
    ]

    # Check if content is just a placeholder
    content_lower = stripped.lower()
    for pattern in no_content_patterns:
        if content_lower == pattern:
            return None
        # Also filter if the content is dominated by these patterns
        if pattern in content_lower:
            # Remove the pattern and check what's left
            remaining = content_lower.replace(pattern, "").strip()
            # If nothing meaningful left after removing placeholders, skip
            if not remaining or remaining in [".", "..."]:
                return None

    # For content that passes filters, limit length to prevent token waste in logs
    if len(stripped) > 500:
        return stripped[:500] + "..."

    return stripped


class UsageTracker:
    """
    Track actual API usage for analytics and cost optimization.

    Features:
    - Persistent SQLite storage
    - Session-based tracking
    - Cost estimation
    - Performance metrics
    - Privacy-focused (opt-in, no content storage)
    """

    def __init__(self, db_path: str = None, enabled: bool = None):
        """
        Initialize usage tracker.

        Args:
            db_path: Path to SQLite database
            enabled: Override environment variable (for testing)
        """
        self.db_path = db_path or os.getenv("USAGE_DB_PATH", "usage_tracking.db")

        # Check if tracking is enabled
        if enabled is None:
            enabled = os.getenv("TRACK_USAGE", "false").lower() == "true"
        self.enabled = enabled

        # Check if full content logging is enabled (for debugging/testing)
        self.log_full_content = os.getenv("LOG_FULL_CONTENT", "false").lower() == "true"

        if self.enabled:
            self._init_db()
            logger.info(f"Usage tracking enabled. Database: {self.db_path}")
            if self.log_full_content:
                logger.info("Full request/response content logging enabled")
        else:
            logger.debug("Usage tracking disabled. Set TRACK_USAGE=true to enable")

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def _migrate_api_requests_table(self, cursor) -> None:
        """Migrate api_requests table from old schema to new RequestMetric schema (T072)."""
        # Read all existing data
        cursor.execute("SELECT * FROM api_requests")
        rows = cursor.fetchall()
        old_cols = [col[0] for col in cursor.description]

        # Drop old table
        cursor.execute("DROP TABLE api_requests")

        # Create new table with full RequestMetric schema
        cursor.execute("""
            CREATE TABLE api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                attempt_index INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                incoming_identifier TEXT,
                resolved_assignment_id TEXT,
                resolved_model TEXT,
                original_model TEXT NOT NULL,
                routed_model TEXT NOT NULL,
                provider TEXT,
                endpoint TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                thinking_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER,
                duration_ms REAL,
                tokens_per_second REAL,
                estimated_cost REAL DEFAULT 0.0,
                stream BOOLEAN,
                message_count INTEGER,
                has_system BOOLEAN,
                has_tools BOOLEAN,
                has_images BOOLEAN,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                session_id TEXT,
                client_ip TEXT,
                has_json_content BOOLEAN DEFAULT 0,
                json_size_bytes INTEGER DEFAULT 0,
                request_content TEXT,
                response_content TEXT,
                profile TEXT,
                UNIQUE (request_id, attempt_index)
            )
        """)

        # Map old rows → new table
        for row in rows:
            old_data = dict(zip(old_cols, row))
            # Map columns: original_model → incoming_identifier; routed_model → resolved_model
            cursor.execute(
                """
                INSERT INTO api_requests (
                    request_id, attempt_index, timestamp,
                    incoming_identifier, resolved_assignment_id, resolved_model,
                    original_model, routed_model, provider, endpoint,
                    input_tokens, output_tokens, thinking_tokens, total_tokens,
                    duration_ms, tokens_per_second, estimated_cost,
                    stream, message_count, has_system, has_tools, has_images,
                    status, error_message,
                    session_id, client_ip,
                    has_json_content, json_size_bytes,
                    request_content, response_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    old_data.get("request_id"),
                    0,  # attempt_index = 0 for legacy rows
                    old_data.get("timestamp"),
                    old_data.get(
                        "original_model"
                    ),  # incoming_identifier = original_model
                    None,  # resolved_assignment_id unknown
                    old_data.get("routed_model"),  # resolved_model = routed_model
                    old_data.get("original_model"),
                    old_data.get("routed_model"),
                    old_data.get("provider"),
                    old_data.get("endpoint"),
                    old_data.get("input_tokens"),
                    old_data.get("output_tokens"),
                    old_data.get("thinking_tokens"),
                    old_data.get("total_tokens"),
                    old_data.get("duration_ms"),
                    old_data.get("tokens_per_second"),
                    old_data.get("estimated_cost"),
                    old_data.get("stream"),
                    old_data.get("message_count"),
                    old_data.get("has_system"),
                    old_data.get("has_tools"),
                    old_data.get("has_images"),
                    old_data.get("status"),
                    old_data.get("error_message"),
                    old_data.get("session_id"),
                    old_data.get("client_ip"),
                    old_data.get("has_json_content"),
                    old_data.get("json_size_bytes"),
                    old_data.get("request_content"),
                    old_data.get("response_content"),
                ),
            )

    def _init_db(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # --- Migration for RequestMetric schema (T072) ---
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_requests'"
        )
        table_exists = cursor.fetchone() is not None
        needs_migration = False
        if table_exists:
            cursor.execute("PRAGMA table_info(api_requests)")
            cols = [row[1] for row in cursor.fetchall()]
            if "attempt_index" not in cols:
                needs_migration = True

        if needs_migration:
            self._migrate_api_requests_table(cursor)
            conn.commit()

        # Main usage table (new schema for fresh or post-migration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                attempt_index INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                incoming_identifier TEXT,
                resolved_assignment_id TEXT,
                resolved_model TEXT,
                original_model TEXT NOT NULL,
                routed_model TEXT NOT NULL,
                provider TEXT,
                endpoint TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                thinking_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER,
                duration_ms REAL,
                tokens_per_second REAL,
                estimated_cost REAL DEFAULT 0.0,
                stream BOOLEAN,
                message_count INTEGER,
                has_system BOOLEAN,
                has_tools BOOLEAN,
                has_images BOOLEAN,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                session_id TEXT,
                client_ip TEXT,
                has_json_content BOOLEAN DEFAULT 0,
                json_size_bytes INTEGER DEFAULT 0,
                request_content TEXT,
                response_content TEXT,
                profile TEXT,
                UNIQUE (request_id, attempt_index)
            )
        """)
        # Migration: add `profile` column to pre-existing DBs created before
        # this column was introduced (Phase 3 of Option C-slim). No-op if present.
        try:
            cursor.execute("ALTER TABLE api_requests ADD COLUMN profile TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists, expected on fresh DBs

        # Model usage summary (aggregated view)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_usage_summary (
                model TEXT PRIMARY KEY,
                request_count INTEGER DEFAULT 0,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_thinking_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                avg_duration_ms REAL DEFAULT 0.0,
                last_used TEXT
            )
        """)

        # Session summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_summary (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                request_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,

                -- JSON/TOON analysis
                json_requests INTEGER DEFAULT 0,
                total_json_bytes INTEGER DEFAULT 0,
                potential_toon_savings INTEGER DEFAULT 0
            )
        """)

        # Terminal output table for Claude Code session capture
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terminal_output (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                test_config TEXT,
                timestamp TEXT NOT NULL,

                -- Terminal capture
                stdout TEXT,
                stderr TEXT,
                exit_code INTEGER,

                -- Execution metadata
                workspace_path TEXT,
                prompt TEXT,
                duration_seconds REAL,

                -- Test results
                poem_created BOOLEAN DEFAULT 0,
                poem_content TEXT,
                folder_listed BOOLEAN DEFAULT 0,

                -- Status
                success BOOLEAN DEFAULT 0,
                error_message TEXT
            )
        """)

        # Extended analytics tables for visualization
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_model_stats (
                date TEXT NOT NULL,
                model TEXT NOT NULL,
                provider TEXT,
                request_count INTEGER DEFAULT 0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                thinking_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                avg_duration_ms REAL DEFAULT 0.0,
                has_tools_count INTEGER DEFAULT 0,
                has_images_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                PRIMARY KEY (date, model)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_comparison_stats (
                date TEXT NOT NULL,
                model_tier TEXT NOT NULL,  -- 'big', 'middle', 'small', 'free'
                model TEXT NOT NULL,
                cost_per_1k_tokens REAL DEFAULT 0.0,
                tokens_per_request REAL DEFAULT 0.0,
                avg_latency_ms REAL DEFAULT 0.0,
                request_count INTEGER DEFAULT 0,
                PRIMARY KEY (date, model_tier, model)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings_tracking (
                date TEXT NOT NULL,
                original_model TEXT NOT NULL,
                routed_model TEXT NOT NULL,
                original_cost REAL DEFAULT 0.0,
                actual_cost REAL DEFAULT 0.0,
                savings REAL DEFAULT 0.0,
                savings_percent REAL DEFAULT 0.0,
                request_count INTEGER DEFAULT 1,
                PRIMARY KEY (date, original_model, routed_model)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_breakdown (
                request_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                reasoning_tokens INTEGER DEFAULT 0,
                cached_tokens INTEGER DEFAULT 0,
                tool_use_tokens INTEGER DEFAULT 0,
                audio_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        """)

        # Indexes for performance (extended for new columns)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON api_requests(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_model ON api_requests(routed_model)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON api_requests(session_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON api_requests(status)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_assignment ON api_requests(resolved_assignment_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_request_id ON api_requests(request_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_terminal_session ON terminal_output(session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_terminal_timestamp ON terminal_output(timestamp)"
        )

        # New indexes for analytics
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_model_stats(date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_daily_stats_model ON daily_model_stats(model)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_savings_date ON savings_tracking(date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_token_breakdown_model ON token_breakdown(model)"
        )

        conn.commit()
        conn.close()

    def log_request(
        self,
        request_id: str,
        original_model: str,
        routed_model: str,
        provider: str,
        endpoint: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        thinking_tokens: int = 0,
        duration_ms: float = 0.0,
        estimated_cost: float = 0.0,
        stream: bool = False,
        message_count: int = 0,
        has_system: bool = False,
        has_tools: bool = False,
        has_images: bool = False,
        status: str = "success",
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        has_json_content: bool = False,
        json_size_bytes: int = 0,
        request_content: Optional[str] = None,
        response_content: Optional[str] = None,
        # Enhanced token breakdown for detailed analytics
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        reasoning_tokens: Optional[int] = None,
        cached_tokens: Optional[int] = None,
        tool_use_tokens: Optional[int] = None,
        audio_tokens: Optional[int] = None,
        # Savings calculation
        original_cost: Optional[float] = None,
        model_tier: Optional[str] = None,
        # RequestMetric extensions (T072, T073)
        attempt_index: int = 0,
        resolved_assignment_id: Optional[str] = None,
        incoming_identifier: Optional[str] = None,
        resolved_model: Optional[str] = None,
        # Profile routing (Option C-slim Phase 3)
        profile: Optional[str] = None,
    ) -> bool:
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

            # Calculate derived metrics
            total_tokens = input_tokens + output_tokens + thinking_tokens
            tokens_per_second = (
                output_tokens / (duration_ms / 1000)
                if duration_ms > 0 and output_tokens > 0
                else 0.0
            )

            # Resolve RequestMetric fields (T072)
            incoming_identifier = incoming_identifier or original_model
            resolved_model = resolved_model or routed_model

            # Conditionally store content if enabled, with sanitization to prevent token waste
            req_content = (
                sanitize_content_for_logging(request_content)
                if self.log_full_content and request_content
                else None
            )
            resp_content = (
                sanitize_content_for_logging(response_content)
                if self.log_full_content and response_content
                else None
            )

            # Insert request (ignore duplicates or handle via exception)
            # New schema uses UNIQUE(request_id, attempt_index)
            try:
                cursor.execute(
                    """
                    INSERT INTO api_requests (
                        request_id, attempt_index, timestamp,
                        incoming_identifier, resolved_assignment_id, resolved_model,
                        original_model, routed_model, provider, endpoint,
                        input_tokens, output_tokens, thinking_tokens, total_tokens,
                        duration_ms, tokens_per_second, estimated_cost,
                        stream, message_count, has_system, has_tools, has_images,
                        status, error_message,
                        session_id, client_ip,
                        has_json_content, json_size_bytes,
                        request_content, response_content,
                        profile
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        request_id,
                        attempt_index,
                        datetime.utcnow().isoformat(),
                        incoming_identifier,
                        resolved_assignment_id,
                        resolved_model,
                        original_model,
                        routed_model,
                        provider,
                        endpoint,
                        input_tokens,
                        output_tokens,
                        thinking_tokens,
                        total_tokens,
                        duration_ms,
                        tokens_per_second,
                        estimated_cost,
                        stream,
                        message_count,
                        has_system,
                        has_tools,
                        has_images,
                        status,
                        error_message,
                        session_id,
                        client_ip,
                        has_json_content,
                        json_size_bytes,
                        req_content,
                        resp_content,
                        profile,
                    ),
                )
            except sqlite3.IntegrityError:
                # Duplicate (request_id, attempt_index) — update status/error instead
                cursor.execute(
                    """
                    UPDATE api_requests SET
                        status = ?, error_message = ?
                    WHERE request_id = ? AND attempt_index = ?
                """,
                    (status, error_message, request_id, attempt_index),
                )

            # Update model summary
            cursor.execute(
                """
                INSERT INTO model_usage_summary (
                    model, request_count,
                    total_input_tokens, total_output_tokens, total_thinking_tokens,
                    total_cost, avg_duration_ms, last_used
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model) DO UPDATE SET
                    request_count = request_count + 1,
                    total_input_tokens = total_input_tokens + excluded.total_input_tokens,
                    total_output_tokens = total_output_tokens + excluded.total_output_tokens,
                    total_thinking_tokens = total_thinking_tokens + excluded.total_thinking_tokens,
                    total_cost = total_cost + excluded.total_cost,
                    avg_duration_ms = (avg_duration_ms * request_count + excluded.avg_duration_ms) / (request_count + 1),
                    last_used = excluded.last_used
            """,
                (
                    routed_model,
                    input_tokens,
                    output_tokens,
                    thinking_tokens,
                    estimated_cost,
                    duration_ms,
                    datetime.utcnow().isoformat(),
                ),
            )

            # Update session summary if session_id provided
            if session_id:
                cursor.execute(
                    """
                    INSERT INTO session_summary (
                        session_id, start_time, end_time,
                        request_count, total_tokens, total_cost,
                        json_requests, total_json_bytes
                    ) VALUES (?, ?, ?, 1, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        end_time = excluded.end_time,
                        request_count = request_count + 1,
                        total_tokens = total_tokens + excluded.total_tokens,
                        total_cost = total_cost + excluded.total_cost,
                        json_requests = json_requests + excluded.json_requests,
                        total_json_bytes = total_json_bytes + excluded.total_json_bytes
                """,
                    (
                        session_id,
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                        total_tokens,
                        estimated_cost,
                        1 if has_json_content else 0,
                        json_size_bytes,
                    ),
                )

            # ===== EXTENDED ANALYTICS LOGGING =====

            # Get today's date for daily stats
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Update daily model stats
            cursor.execute(
                """
                INSERT INTO daily_model_stats (
                    date, model, provider,
                    request_count, input_tokens, output_tokens, thinking_tokens,
                    total_tokens, total_cost, avg_duration_ms,
                    has_tools_count, has_images_count, success_count, error_count
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date, model) DO UPDATE SET
                    request_count = request_count + 1,
                    input_tokens = input_tokens + excluded.input_tokens,
                    output_tokens = output_tokens + excluded.output_tokens,
                    thinking_tokens = thinking_tokens + excluded.thinking_tokens,
                    total_tokens = total_tokens + excluded.total_tokens,
                    total_cost = total_cost + excluded.total_cost,
                    avg_duration_ms = (avg_duration_ms * request_count + excluded.avg_duration_ms) / (request_count + 1),
                    has_tools_count = has_tools_count + excluded.has_tools_count,
                    has_images_count = has_images_count + excluded.has_images_count,
                    success_count = success_count + excluded.success_count,
                    error_count = error_count + excluded.error_count
            """,
                (
                    today,
                    routed_model,
                    provider,
                    input_tokens,
                    output_tokens,
                    thinking_tokens,
                    total_tokens,
                    estimated_cost,
                    duration_ms,
                    1 if has_tools else 0,
                    1 if has_images else 0,
                    1 if status == "success" else 0,
                    1 if status != "success" else 0,
                ),
            )

            # Update model comparison stats (if model tier is provided)
            if model_tier:
                # Calculate cost per 1K tokens
                cost_per_1k = (
                    (estimated_cost / total_tokens * 1000) if total_tokens > 0 else 0.0
                )
                tokens_per_req = total_tokens
                cursor.execute(
                    """
                    INSERT INTO model_comparison_stats (
                        date, model_tier, model, cost_per_1k_tokens, tokens_per_request, avg_latency_ms
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(date, model_tier, model) DO UPDATE SET
                        cost_per_1k_tokens = (cost_per_1k_tokens * request_count + excluded.cost_per_1k_tokens) / (request_count + 1),
                        tokens_per_request = (tokens_per_request * request_count + excluded.tokens_per_request) / (request_count + 1),
                        avg_latency_ms = (avg_latency_ms * request_count + excluded.avg_latency_ms) / (request_count + 1)
                """,
                    (
                        today,
                        model_tier,
                        routed_model,
                        cost_per_1k,
                        tokens_per_req,
                        duration_ms,
                    ),
                )

            # Update savings tracking (if original cost is provided)
            if original_cost is not None and original_cost > 0:
                savings = original_cost - estimated_cost
                savings_percent = (
                    (savings / original_cost * 100) if original_cost > 0 else 0.0
                )
                cursor.execute(
                    """
                    INSERT INTO savings_tracking (
                        date, original_model, routed_model,
                        original_cost, actual_cost, savings, savings_percent, request_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(date, original_model, routed_model) DO UPDATE SET
                        original_cost = original_cost + excluded.original_cost,
                        actual_cost = actual_cost + excluded.actual_cost,
                        savings = savings + excluded.savings,
                        savings_percent = (savings_percent * request_count + excluded.savings_percent) / (request_count + 1),
                        request_count = request_count + 1
                """,
                    (
                        today,
                        original_model,
                        routed_model,
                        original_cost,
                        estimated_cost,
                        savings,
                        savings_percent,
                    ),
                )

            # Store detailed token breakdown (if provided)
            if prompt_tokens is not None or completion_tokens is not None:
                # Use the breakdown values or fall back to input/output tokens
                p_tokens = prompt_tokens if prompt_tokens is not None else input_tokens
                c_tokens = (
                    completion_tokens
                    if completion_tokens is not None
                    else output_tokens
                )
                r_tokens = (
                    reasoning_tokens
                    if reasoning_tokens is not None
                    else thinking_tokens
                )

                # Total tokens from breakdown (or use calculated total)
                bd_total = (p_tokens or 0) + (c_tokens or 0) + (r_tokens or 0)
                if bd_total == 0:
                    bd_total = total_tokens

                cursor.execute(
                    """
                    INSERT INTO token_breakdown (
                        request_id, timestamp, model,
                        prompt_tokens, completion_tokens, reasoning_tokens,
                        cached_tokens, tool_use_tokens, audio_tokens, total_tokens
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(request_id) DO UPDATE SET
                        prompt_tokens = excluded.prompt_tokens,
                        completion_tokens = excluded.completion_tokens,
                        reasoning_tokens = excluded.reasoning_tokens,
                        cached_tokens = excluded.cached_tokens,
                        tool_use_tokens = excluded.tool_use_tokens,
                        audio_tokens = excluded.audio_tokens,
                        total_tokens = excluded.total_tokens
                """,
                    (
                        request_id,
                        datetime.utcnow().isoformat(),
                        routed_model,
                        p_tokens or 0,
                        c_tokens or 0,
                        r_tokens or 0,
                        cached_tokens or 0,
                        tool_use_tokens or 0,
                        audio_tokens or 0,
                        bd_total,
                    ),
                )

            conn.commit()
            conn.close()

            # Mirror to Prometheus metrics. Wrapped in try so a metrics import
            # failure (or library issue) NEVER breaks the usage logging path.
            # Only fires on the canonical request (attempt_index=0) so cascade
            # retries don't double-count requests_total.
            if attempt_index == 0:
                try:
                    from src.api.metrics_api import record_request
                    record_request(
                        profile=profile or "",
                        model=routed_model or original_model or "",
                        status=status,
                        duration_seconds=(duration_ms or 0) / 1000.0,
                        input_tokens=input_tokens or 0,
                        output_tokens=output_tokens or 0,
                        thinking_tokens=thinking_tokens or 0,
                        cost_usd=estimated_cost or 0.0,
                        cascade_depth=0,  # cascade depth lives in events.jsonl
                    )
                except Exception:
                    pass
            return True

        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
            return False

    def log_terminal_output(
        self,
        session_id: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        test_config: Optional[str] = None,
        workspace_path: Optional[str] = None,
        prompt: Optional[str] = None,
        duration_seconds: float = 0.0,
        poem_created: bool = False,
        poem_content: Optional[str] = None,
        folder_listed: bool = False,
        success: bool = False,
        error_message: Optional[str] = None,
    ) -> bool:
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

            cursor.execute(
                """
                INSERT INTO terminal_output (
                    session_id, test_config, timestamp,
                    stdout, stderr, exit_code,
                    workspace_path, prompt, duration_seconds,
                    poem_created, poem_content, folder_listed,
                    success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    test_config,
                    datetime.utcnow().isoformat(),
                    stdout,
                    stderr,
                    exit_code,
                    workspace_path,
                    prompt,
                    duration_seconds,
                    poem_created,
                    poem_content,
                    folder_listed,
                    success,
                    error_message,
                ),
            )

            conn.commit()
            conn.close()
            logger.debug(f"Terminal output logged for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to log terminal output: {e}")
            return False

    def get_terminal_output(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get terminal output for a session."""
        if not self.enabled:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM terminal_output
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (session_id,),
            )

            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

        except Exception as e:
            logger.error(f"Failed to get terminal output: {e}")
            return None

    def get_top_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used models by request count."""
        if not self.enabled:
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM model_usage_summary
                ORDER BY request_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get top models: {e}")
            return []

    def get_daily_total_tokens(self, date_utc: Optional[str] = None) -> int:
        """Get total tokens consumed today across all models."""
        if not self.enabled:
            return 0
        target_date = date_utc or datetime.utcnow().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM daily_model_stats WHERE date = ?",
                (target_date,),
            )
            row = cursor.fetchone()
            conn.close()
            return int(row[0]) if row else 0
        except Exception as e:
            logger.error(f"Failed to get daily total tokens: {e}")
            return 0

    def get_daily_total_cost(self, date_utc: Optional[str] = None) -> float:
        """Get total estimated cost (USD) consumed today across all models."""
        if not self.enabled:
            return 0.0
        target_date = date_utc or datetime.utcnow().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(total_cost), 0.0) FROM daily_model_stats WHERE date = ?",
                (target_date,),
            )
            row = cursor.fetchone()
            conn.close()
            return float(row[0]) if row else 0.0
        except Exception as e:
            logger.error(f"Failed to get daily total cost: {e}")
            return 0.0

    def get_daily_model_request_count(
        self, model: str, date_utc: Optional[str] = None
    ) -> int:
        """Get request count for a model on a UTC calendar day."""
        if not self.enabled:
            return 0
        target_date = date_utc or datetime.utcnow().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT request_count
                FROM daily_model_stats
                WHERE date = ? AND model = ?
                """,
                (target_date, model),
            )
            row = cursor.fetchone()
            conn.close()
            return int(row[0]) if row and row[0] is not None else 0
        except Exception as e:
            logger.error(f"Failed to get daily model request count: {e}")
            return 0

    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for last N days."""
        if not self.enabled:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(thinking_tokens) as total_thinking_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(estimated_cost) as total_cost,
                    AVG(duration_ms) as avg_duration_ms,
                    AVG(tokens_per_second) as avg_tokens_per_second
                FROM api_requests
                WHERE timestamp >= ? AND status = 'success'
            """,
                (since,),
            )

            row = cursor.fetchone()
            conn.close()

            if row and row[0]:
                return {
                    "total_requests": row[0] or 0,
                    "total_input_tokens": row[1] or 0,
                    "total_output_tokens": row[2] or 0,
                    "total_thinking_tokens": row[3] or 0,
                    "total_tokens": row[4] or 0,
                    "total_cost": round(row[5] or 0.0, 4),
                    "avg_duration_ms": round(row[6] or 0.0, 2),
                    "avg_tokens_per_second": round(row[7] or 0.0, 2),
                    "days": days,
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get cost summary: {e}")
            return {}

    def get_json_toon_analysis(self) -> Dict[str, Any]:
        """Analyze JSON usage to determine if TOON conversion would help."""
        if not self.enabled:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN has_json_content = 1 THEN 1 ELSE 0 END) as json_requests,
                    SUM(json_size_bytes) as total_json_bytes,
                    AVG(CASE WHEN has_json_content = 1 THEN json_size_bytes ELSE 0 END) as avg_json_size
                FROM api_requests
                WHERE timestamp >= datetime('now', '-7 days')
            """)

            row = cursor.fetchone()
            conn.close()

            if row:
                total_requests = row[0] or 0
                json_requests = row[1] or 0
                total_json_bytes = row[2] or 0
                avg_json_size = row[3] or 0

                # Estimate TOON savings (typically 20-40% for JSON)
                estimated_toon_savings = int(total_json_bytes * 0.3)
                json_percentage = (
                    (json_requests / total_requests * 100) if total_requests > 0 else 0
                )

                return {
                    "total_requests": total_requests,
                    "json_requests": json_requests,
                    "json_percentage": round(json_percentage, 1),
                    "total_json_bytes": total_json_bytes,
                    "avg_json_size": round(avg_json_size, 0),
                    "estimated_toon_savings_bytes": estimated_toon_savings,
                    "recommended": json_percentage > 30 and avg_json_size > 500,
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to analyze JSON usage: {e}")
            return {}

    def export_to_csv(self, output_file: str, days: int = 30) -> bool:
        """Export usage data to CSV."""
        if not self.enabled:
            return False

        try:
            import csv

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                SELECT * FROM api_requests
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since,),
            )

            rows = cursor.fetchall()

            if rows:
                with open(output_file, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in rows])

                logger.info(f"Exported {len(rows)} records to {output_file}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False

    def export_to_json(self, output_file: str, days: int = 30) -> bool:
        """Export usage data to JSON."""
        if not self.enabled:
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute(
                """
                SELECT * FROM api_requests
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since,),
            )

            rows = cursor.fetchall()

            if rows:
                data = [dict(row) for row in rows]
                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "exported_at": datetime.utcnow().isoformat(),
                            "days": days,
                            "record_count": len(data),
                            "records": data,
                        },
                        f,
                        indent=2,
                    )

                logger.info(f"Exported {len(rows)} records to {output_file}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False

    # ===== NEW ANALYTICS METHODS FOR VISUALIZATION =====

    def get_time_series_data(self, days: int = 14) -> Dict[str, Any]:
        """
        Get time-series data for line charts and graphs.

        Returns data points by date for:
        - Total tokens per day
        - Cost per day
        - Request count per day
        - Token breakdown per day
        """
        if not self.enabled:
            return {"dates": [], "tokens": [], "cost": [], "requests": []}

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get date range
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            # Get daily aggregates from the new daily_model_stats table
            cursor.execute(
                """
                SELECT
                    date,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost) as total_cost,
                    SUM(request_count) as total_requests,
                    SUM(input_tokens) as input_tokens,
                    SUM(output_tokens) as output_tokens,
                    SUM(thinking_tokens) as thinking_tokens,
                    SUM(success_count) as success_count,
                    SUM(error_count) as error_count
                FROM daily_model_stats
                WHERE date >= ?
                GROUP BY date
                ORDER BY date
            """,
                (since,),
            )

            rows = cursor.fetchall()
            conn.close()

            result = {
                "dates": [],
                "tokens": [],
                "cost": [],
                "requests": [],
                "token_breakdown": {"input": [], "output": [], "thinking": []},
                "success_rate": [],
            }

            for row in rows:
                result["dates"].append(row["date"])
                result["tokens"].append(row["total_tokens"] or 0)
                result["cost"].append(round(row["total_cost"] or 0, 4))
                result["requests"].append(row["total_requests"] or 0)
                result["token_breakdown"]["input"].append(row["input_tokens"] or 0)
                result["token_breakdown"]["output"].append(row["output_tokens"] or 0)
                result["token_breakdown"]["thinking"].append(
                    row["thinking_tokens"] or 0
                )

                total = (row["success_count"] or 0) + (row["error_count"] or 0)
                success_rate = (
                    (row["success_count"] / total * 100) if total > 0 else 100
                )
                result["success_rate"].append(round(success_rate, 1))

            return result

        except Exception as e:
            logger.error(f"Failed to get time series data: {e}")
            return {"dates": [], "tokens": [], "cost": [], "requests": []}

    def get_model_comparison(self, days: int = 14) -> List[Dict[str, Any]]:
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

            # Aggregate model performance data
            cursor.execute(
                """
                SELECT
                    model,
                    provider,
                    SUM(request_count) as total_requests,
                    AVG(total_tokens / NULLIF(request_count, 0)) as avg_tokens_per_request,
                    AVG(total_cost / NULLIF(total_tokens, 0) * 1000) as avg_cost_per_1k_tokens,
                    AVG(avg_duration_ms) as avg_duration_ms,
                    SUM(has_tools_count) as tool_requests,
                    SUM(has_images_count) as image_requests
                FROM daily_model_stats
                WHERE date >= ?
                GROUP BY model, provider
                HAVING total_requests > 0
                ORDER BY total_requests DESC
            """,
                (since,),
            )

            rows = cursor.fetchall()
            conn.close()

            result = []
            for row in rows:
                result.append(
                    {
                        "model": row["model"],
                        "provider": row["provider"],
                        "total_requests": row["total_requests"],
                        "avg_tokens_per_request": round(
                            row["avg_tokens_per_request"] or 0, 0
                        ),
                        "avg_cost_per_1k_tokens": round(
                            row["avg_cost_per_1k_tokens"] or 0, 4
                        ),
                        "avg_duration_ms": round(row["avg_duration_ms"] or 0, 1),
                        "tool_requests": row["tool_requests"],
                        "image_requests": row["image_requests"],
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get model comparison: {e}")
            return []

    def get_savings_data(self, days: int = 14) -> List[Dict[str, Any]]:
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

            cursor.execute(
                """
                SELECT
                    original_model,
                    routed_model,
                    SUM(request_count) as total_requests,
                    SUM(original_cost) as total_original_cost,
                    SUM(actual_cost) as total_actual_cost,
                    SUM(savings) as total_savings,
                    AVG(savings_percent) as avg_savings_percent
                FROM savings_tracking
                WHERE date >= ?
                GROUP BY original_model, routed_model
                ORDER BY total_savings DESC
            """,
                (since,),
            )

            rows = cursor.fetchall()
            conn.close()

            result = []
            for row in rows:
                result.append(
                    {
                        "original_model": row["original_model"],
                        "routed_model": row["routed_model"],
                        "request_count": row["total_requests"],
                        "original_cost": round(row["total_original_cost"] or 0, 4),
                        "actual_cost": round(row["total_actual_cost"] or 0, 4),
                        "total_savings": round(row["total_savings"] or 0, 4),
                        "avg_savings_percent": round(
                            row["avg_savings_percent"] or 0, 1
                        ),
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get savings data: {e}")
            return []

    def get_token_breakdown_stats(self, days: int = 14) -> Dict[str, Any]:
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

            cursor.execute(
                """
                SELECT
                    SUM(prompt_tokens) as total_prompt,
                    SUM(completion_tokens) as total_completion,
                    SUM(reasoning_tokens) as total_reasoning,
                    SUM(cached_tokens) as total_cached,
                    SUM(tool_use_tokens) as total_tool_use,
                    SUM(audio_tokens) as total_audio,
                    SUM(total_tokens) as total_tokens,
                    COUNT(*) as request_count
                FROM token_breakdown
                WHERE timestamp >= ?
            """,
                (since,),
            )

            row = cursor.fetchone()
            conn.close()

            if not row or not row[7]:  # No requests
                return {}

            total = row[6] or 0
            if total == 0:
                return {}

            return {
                "total_tokens": total,
                "request_count": row[7],
                "prompt": {
                    "absolute": row[0] or 0,
                    "percentage": round((row[0] or 0) / total * 100, 1),
                },
                "completion": {
                    "absolute": row[1] or 0,
                    "percentage": round((row[1] or 0) / total * 100, 1),
                },
                "reasoning": {
                    "absolute": row[2] or 0,
                    "percentage": round((row[2] or 0) / total * 100, 1),
                },
                "cached": {
                    "absolute": row[3] or 0,
                    "percentage": round((row[3] or 0) / total * 100, 1),
                },
                "tool_use": {
                    "absolute": row[4] or 0,
                    "percentage": round((row[4] or 0) / total * 100, 1),
                },
                "audio": {
                    "absolute": row[5] or 0,
                    "percentage": round((row[5] or 0) / total * 100, 1),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get token breakdown: {e}")
            return {}

    def get_provider_stats(self, days: int = 14) -> List[Dict[str, Any]]:
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

            cursor.execute(
                """
                SELECT
                    provider,
                    SUM(request_count) as total_requests,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost) as total_cost,
                    AVG(avg_duration_ms) as avg_duration_ms,
                    SUM(has_tools_count) as tool_requests
                FROM daily_model_stats
                WHERE date >= ? AND provider IS NOT NULL
                GROUP BY provider
                ORDER BY total_cost DESC
            """,
                (since,),
            )

            rows = cursor.fetchall()
            conn.close()

            result = []
            for row in rows:
                tokens = row["total_tokens"] or 0
                result.append(
                    {
                        "provider": row["provider"],
                        "total_requests": row["total_requests"],
                        "total_tokens": tokens,
                        "total_cost": round(row["total_cost"] or 0, 4),
                        "avg_cost_per_1k_tokens": round(
                            (row["total_cost"] or 0) / tokens * 1000
                            if tokens > 0
                            else 0,
                            4,
                        ),
                        "avg_duration_ms": round(row["avg_duration_ms"] or 0, 1),
                        "tool_requests": row["tool_requests"],
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get provider stats: {e}")
            return []

    def get_dashboard_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary with all visualization data.

        Combines all analytics into one call for efficient dashboard rendering.
        """
        if not self.enabled:
            return {}

        try:
            # Get time series data
            time_series = self.get_time_series_data(days)

            # Get model comparison
            models = self.get_model_comparison(days)

            # Get savings data
            savings = self.get_savings_data(days)

            # Get token breakdown
            token_stats = self.get_token_breakdown_stats(days)

            # Get provider stats
            providers = self.get_provider_stats(days)

            # Get overall stats
            overall = self.get_cost_summary(days)

            # Calculate additional metrics
            total_savings = sum(s["total_savings"] for s in savings)
            avg_savings_percent = (
                sum(s["avg_savings_percent"] for s in savings) / len(savings)
                if savings
                else 0
            )

            return {
                "summary": {
                    "total_requests": overall.get("total_requests", 0),
                    "total_tokens": overall.get("total_tokens", 0),
                    "total_cost": overall.get("total_cost", 0),
                    "avg_latency_ms": overall.get("avg_duration_ms", 0),
                    "total_savings": round(total_savings, 4),
                    "avg_savings_percent": round(avg_savings_percent, 1),
                    "days": days,
                },
                "time_series": time_series,
                "models": models,
                "savings": savings,
                "token_breakdown": token_stats,
                "providers": providers,
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {}


# Global instance
usage_tracker = UsageTracker()
