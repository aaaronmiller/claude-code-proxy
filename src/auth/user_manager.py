"""
Multi-User Authentication System

Manages users, API keys, and per-user usage tracking.
"""

import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.core.logging import logger


class UserManager:
    """Manages users and API keys for multi-user deployments"""

    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                role TEXT DEFAULT 'user',
                quota_requests_per_day INTEGER DEFAULT 1000,
                quota_tokens_per_day INTEGER DEFAULT 1000000,
                quota_cost_per_day REAL DEFAULT 10.0
            )
        """)

        # API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # User usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                request_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_usage_date ON user_usage(user_id, date)")

        conn.commit()
        conn.close()

    def create_user(
        self,
        username: str,
        email: str,
        role: str = "user",
        quota_requests: int = 1000,
        quota_tokens: int = 1000000,
        quota_cost: float = 10.0
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Returns user details including generated API key.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create user
            cursor.execute("""
                INSERT INTO users (username, email, created_at, role, quota_requests_per_day, quota_tokens_per_day, quota_cost_per_day)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, email, datetime.utcnow().isoformat(), role, quota_requests, quota_tokens, quota_cost))

            user_id = cursor.lastrowid

            # Generate API key
            api_key = self._generate_api_key()
            key_hash = self._hash_key(api_key)
            key_prefix = api_key[:8]

            cursor.execute("""
                INSERT INTO api_keys (user_id, key_hash, key_prefix, name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, key_hash, key_prefix, "Default Key", datetime.utcnow().isoformat()))

            conn.commit()
            conn.close()

            logger.info(f"Created user: {username} (ID: {user_id})")

            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "role": role,
                "api_key": api_key,  # Only returned once!
                "created_at": datetime.utcnow().isoformat()
            }

        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create user: {e}")
            raise ValueError("Username or email already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

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

            cursor.execute("""
                SELECT u.*, a.id as key_id
                FROM users u
                JOIN api_keys a ON u.id = a.user_id
                WHERE a.key_hash = ? AND a.active = 1 AND u.active = 1
            """, (key_hash,))

            row = cursor.fetchone()

            if row:
                # Update last used
                cursor.execute("""
                    UPDATE api_keys
                    SET last_used_at = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), row["key_id"]))
                conn.commit()

                user = dict(row)
                conn.close()
                return user

            conn.close()
            return None

        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return None

    def check_user_quota(self, user_id: int) -> Dict[str, Any]:
        """
        Check if user has remaining quota for today.

        Returns quota status.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get user limits
            cursor.execute("""
                SELECT quota_requests_per_day, quota_tokens_per_day, quota_cost_per_day
                FROM users
                WHERE id = ?
            """, (user_id,))

            user = cursor.fetchone()
            if not user:
                conn.close()
                return {"error": "User not found"}

            # Get today's usage
            today = datetime.utcnow().date().isoformat()
            cursor.execute("""
                SELECT request_count, token_count, cost
                FROM user_usage
                WHERE user_id = ? AND date = ?
            """, (user_id, today))

            usage = cursor.fetchone()
            conn.close()

            if usage:
                requests_used = usage["request_count"]
                tokens_used = usage["token_count"]
                cost_used = usage["cost"]
            else:
                requests_used = 0
                tokens_used = 0
                cost_used = 0.0

            requests_remaining = user["quota_requests_per_day"] - requests_used
            tokens_remaining = user["quota_tokens_per_day"] - tokens_used
            cost_remaining = user["quota_cost_per_day"] - cost_used

            return {
                "user_id": user_id,
                "date": today,
                "requests": {
                    "limit": user["quota_requests_per_day"],
                    "used": requests_used,
                    "remaining": max(0, requests_remaining),
                    "exceeded": requests_remaining < 0
                },
                "tokens": {
                    "limit": user["quota_tokens_per_day"],
                    "used": tokens_used,
                    "remaining": max(0, tokens_remaining),
                    "exceeded": tokens_remaining < 0
                },
                "cost": {
                    "limit": user["quota_cost_per_day"],
                    "used": cost_used,
                    "remaining": max(0, cost_remaining),
                    "exceeded": cost_remaining < 0
                },
                "quota_ok": requests_remaining > 0 and tokens_remaining > 0 and cost_remaining > 0
            }

        except Exception as e:
            logger.error(f"Failed to check quota: {e}")
            return {"error": str(e)}

    def record_usage(self, user_id: int, requests: int = 1, tokens: int = 0, cost: float = 0.0):
        """Record usage for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.utcnow().date().isoformat()

            cursor.execute("""
                INSERT INTO user_usage (user_id, date, request_count, token_count, cost)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    request_count = request_count + ?,
                    token_count = token_count + ?,
                    cost = cost + ?
            """, (user_id, today, requests, tokens, cost, requests, tokens, cost))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")

    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"sk-{secrets.token_urlsafe(32)}"

    def _hash_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()


# Global user manager instance
user_manager = UserManager()
