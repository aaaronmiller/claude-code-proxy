"""
Actual API usage tracking system (opt-in).

Tracks real API requests for analytics, cost analysis, and optimization.
Stores data in SQLite for persistence and efficient querying.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


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

    def __init__(self, db_path: str = "usage_tracking.db", enabled: bool = None):
        """
        Initialize usage tracker.

        Args:
            db_path: Path to SQLite database
            enabled: Override environment variable (for testing)
        """
        self.db_path = db_path

        # Check if tracking is enabled
        if enabled is None:
            enabled = os.getenv("TRACK_USAGE", "false").lower() == "true"
        self.enabled = enabled

        if self.enabled:
            self._init_db()
            logger.info(f"Usage tracking enabled. Database: {self.db_path}")
        else:
            logger.debug("Usage tracking disabled. Set TRACK_USAGE=true to enable")

    def _init_db(self):
        """Initialize SQLite database with schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,

                -- Model info
                original_model TEXT NOT NULL,
                routed_model TEXT NOT NULL,
                provider TEXT,
                endpoint TEXT,

                -- Token usage
                input_tokens INTEGER,
                output_tokens INTEGER,
                thinking_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER,

                -- Performance
                duration_ms REAL,
                tokens_per_second REAL,

                -- Cost estimation
                estimated_cost REAL DEFAULT 0.0,

                -- Request metadata
                stream BOOLEAN,
                message_count INTEGER,
                has_system BOOLEAN,
                has_tools BOOLEAN,
                has_images BOOLEAN,

                -- Status
                status TEXT DEFAULT 'success',
                error_message TEXT,

                -- Session tracking
                session_id TEXT,
                client_ip TEXT,

                -- JSON detection (for TOON analysis)
                has_json_content BOOLEAN DEFAULT 0,
                json_size_bytes INTEGER DEFAULT 0
            )
        """)

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

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON api_requests(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model ON api_requests(routed_model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON api_requests(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON api_requests(status)")

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
        json_size_bytes: int = 0
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
            tokens_per_second = output_tokens / (duration_ms / 1000) if duration_ms > 0 and output_tokens > 0 else 0.0

            # Insert request
            cursor.execute("""
                INSERT INTO api_requests (
                    request_id, timestamp,
                    original_model, routed_model, provider, endpoint,
                    input_tokens, output_tokens, thinking_tokens, total_tokens,
                    duration_ms, tokens_per_second, estimated_cost,
                    stream, message_count, has_system, has_tools, has_images,
                    status, error_message,
                    session_id, client_ip,
                    has_json_content, json_size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id, datetime.utcnow().isoformat(),
                original_model, routed_model, provider, endpoint,
                input_tokens, output_tokens, thinking_tokens, total_tokens,
                duration_ms, tokens_per_second, estimated_cost,
                stream, message_count, has_system, has_tools, has_images,
                status, error_message,
                session_id, client_ip,
                has_json_content, json_size_bytes
            ))

            # Update model summary
            cursor.execute("""
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
            """, (
                routed_model,
                input_tokens, output_tokens, thinking_tokens,
                estimated_cost, duration_ms, datetime.utcnow().isoformat()
            ))

            # Update session summary if session_id provided
            if session_id:
                cursor.execute("""
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
                """, (
                    session_id,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    total_tokens,
                    estimated_cost,
                    1 if has_json_content else 0,
                    json_size_bytes
                ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
            return False

    def get_top_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used models by request count."""
        if not self.enabled:
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM model_usage_summary
                ORDER BY request_count DESC
                LIMIT ?
            """, (limit,))

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get top models: {e}")
            return []

    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for last N days."""
        if not self.enabled:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            since = (datetime.utcnow() - timedelta(days=days)).isoformat()

            cursor.execute("""
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
            """, (since,))

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
                    "days": days
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
                json_percentage = (json_requests / total_requests * 100) if total_requests > 0 else 0

                return {
                    "total_requests": total_requests,
                    "json_requests": json_requests,
                    "json_percentage": round(json_percentage, 1),
                    "total_json_bytes": total_json_bytes,
                    "avg_json_size": round(avg_json_size, 0),
                    "estimated_toon_savings_bytes": estimated_toon_savings,
                    "recommended": json_percentage > 30 and avg_json_size > 500
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

            cursor.execute("""
                SELECT * FROM api_requests
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (since,))

            rows = cursor.fetchall()

            if rows:
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(row) for row in rows])

                logger.info(f"Exported {len(rows)} records to {output_file}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False


# Global instance
usage_tracker = UsageTracker()
