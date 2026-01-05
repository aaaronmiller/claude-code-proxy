"""
User Management & RBAC Service - Phase 4

Features:
- User authentication & authorization
- Role-based access control (RBAC)
- API key management
- Session management
- Permissions system

Author: AI Architect
Date: 2026-01-05
"""

import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.core.logging import logger


class UserRole(Enum):
    """User roles with permission levels"""
    ADMIN = "admin"           # Full access
    MODERATOR = "moderator"   # Can manage alerts, reports
    ANALYST = "analyst"       # Can view analytics, reports
    VIEWER = "viewer"         # Read-only access
    API_USER = "api_user"     # API access only


class Permission(Enum):
    """Granular permissions"""
    # Dashboard
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_EDIT = "dashboard:edit"
    DASHBOARD_DELETE = "dashboard:delete"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_CUSTOM = "analytics:custom"

    # Alerts
    ALERTS_VIEW = "alerts:view"
    ALERTS_CREATE = "alerts:create"
    ALERTS_EDIT = "alerts:edit"
    ALERTS_DELETE = "alerts:delete"
    ALERTS_MANAGE = "alerts:manage"

    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_CREATE = "reports:create"
    REPORTS_SCHEDULE = "reports:schedule"
    REPORTS_EXPORT = "reports:export"

    # Integrations
    INTEGRATIONS_VIEW = "integrations:view"
    INTEGRATIONS_MANAGE = "integrations:manage"

    # Predictive
    PREDICTIVE_VIEW = "predictive:view"
    PREDICTIVE_MANAGE = "predictive:manage"

    # Admin
    USERS_MANAGE = "users:manage"
    SETTINGS_MANAGE = "settings:manage"
    API_KEYS_MANAGE = "api_keys:manage"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        p.value for p in Permission
    ],
    UserRole.MODERATOR: [
        Permission.DASHBOARD_VIEW.value,
        Permission.DASHBOARD_EDIT.value,
        Permission.ANALYTICS_VIEW.value,
        Permission.ANALYTICS_EXPORT.value,
        Permission.ALERTS_VIEW.value,
        Permission.ALERTS_CREATE.value,
        Permission.ALERTS_EDIT.value,
        Permission.ALERTS_MANAGE.value,
        Permission.REPORTS_VIEW.value,
        Permission.REPORTS_CREATE.value,
        Permission.REPORTS_SCHEDULE.value,
        Permission.REPORTS_EXPORT.value,
        Permission.INTEGRATIONS_VIEW.value,
        Permission.PREDICTIVE_VIEW.value,
    ],
    UserRole.ANALYST: [
        Permission.DASHBOARD_VIEW.value,
        Permission.ANALYTICS_VIEW.value,
        Permission.ANALYTICS_EXPORT.value,
        Permission.ANALYTICS_CUSTOM.value,
        Permission.ALERTS_VIEW.value,
        Permission.REPORTS_VIEW.value,
        Permission.REPORTS_EXPORT.value,
        Permission.PREDICTIVE_VIEW.value,
    ],
    UserRole.VIEWER: [
        Permission.DASHBOARD_VIEW.value,
        Permission.ANALYTICS_VIEW.value,
        Permission.ALERTS_VIEW.value,
        Permission.REPORTS_VIEW.value,
    ],
    UserRole.API_USER: [
        Permission.ANALYTICS_VIEW.value,
        Permission.ANALYTICS_CUSTOM.value,
        Permission.ALERTS_VIEW.value,
    ]
}


@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: str
    last_login: Optional[str]


@dataclass
class APIKey:
    """API Key model"""
    key: str
    user_id: str
    name: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    usage_count: int


@dataclass
class Session:
    """Session model"""
    token: str
    user_id: str
    created_at: str
    expires_at: str
    is_valid: bool


class UserManagementService:
    """User management and authentication service"""

    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
        self.logger = logger

    def initialize(self):
        """Initialize user management tables"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login TEXT
                )
            """)

            # API Keys table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_valid INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to initialize user management: {e}")

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = "claude_proxy_salt_v1"  # In production, use per-user salt
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        role: UserRole = UserRole.VIEWER
    ) -> Optional[str]:
        """Create a new user"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Check if user exists
            cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return None

            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)

            conn.execute("""
                INSERT INTO users (id, username, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, email, password_hash, role.value, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            self.logger.info(f"Created user: {username} with role: {role.value}")
            return user_id

        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return None

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return user ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                "SELECT id, password_hash, is_active FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row or not row["is_active"]:
                return None

            if row["password_hash"] == self.hash_password(password):
                # Update last login
                self.update_last_login(row["id"])
                return row["id"]

            return None

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return None

    def update_last_login(self, user_id: str):
        """Update last login timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to update last login: {e}")

    def create_session(self, user_id: str, duration_hours: int = 24) -> Optional[str]:
        """Create a new session"""
        try:
            conn = sqlite3.connect(self.db_path)

            token = secrets.token_urlsafe(32)
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=duration_hours)

            conn.execute("""
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (token, user_id, created_at.isoformat(), expires_at.isoformat()))

            conn.commit()
            conn.close()

            return token

        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return None

    def validate_session(self, token: str) -> Optional[str]:
        """Validate session and return user ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            now = datetime.now().isoformat()

            cursor = conn.execute("""
                SELECT user_id, expires_at, is_valid
                FROM sessions
                WHERE token = ? AND is_valid = 1 AND expires_at > ?
            """, (token, now))

            row = cursor.fetchone()
            conn.close()

            if row:
                return row["user_id"]

            return None

        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return None

    def invalidate_session(self, token: str):
        """Invalidate a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE sessions SET is_valid = 0 WHERE token = ?",
                (token,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to invalidate session: {e}")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user details"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                role=UserRole(row["role"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                last_login=row["last_login"]
            )

        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            return None

    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        user = self.get_user(user_id)
        if not user:
            return []

        return ROLE_PERMISSIONS.get(user.role, [])

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        perms = self.get_user_permissions(user_id)
        return permission.value in perms

    def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str],
        expires_days: Optional[int] = None
    ) -> Optional[str]:
        """Create an API key"""
        try:
            conn = sqlite3.connect(self.db_path)

            # Verify user exists
            cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                conn.close()
                return None

            key = f"cp_{secrets.token_urlsafe(32)}"
            created_at = datetime.now()

            expires_at = None
            if expires_days:
                expires_at = (created_at + timedelta(days=expires_days)).isoformat()

            conn.execute("""
                INSERT INTO api_keys (key, user_id, name, permissions, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, user_id, name, json.dumps(permissions), created_at.isoformat(), expires_at))

            conn.commit()
            conn.close()

            return key

        except Exception as e:
            self.logger.error(f"Failed to create API key: {e}")
            return None

    def validate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            now = datetime.now().isoformat()

            cursor = conn.execute("""
                SELECT ak.*, u.role, u.username
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.key = ? AND ak.is_active = 1
                AND (ak.expires_at IS NULL OR ak.expires_at > ?)
            """, (key, now))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # Increment usage count
            self.increment_key_usage(key)

            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "role": row["role"],
                "permissions": json.loads(row["permissions"]),
                "name": row["name"]
            }

        except Exception as e:
            self.logger.error(f"API key validation failed: {e}")
            return None

    def increment_key_usage(self, key: str):
        """Increment API key usage count"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to increment key usage: {e}")

    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE key = ?",
                (key,)
            )
            revoked = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return revoked

        except Exception as e:
            self.logger.error(f"Failed to revoke API key: {e}")
            return False

    def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("""
                SELECT * FROM api_keys
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))

            rows = cursor.fetchall()
            conn.close()

            return [
                APIKey(
                    key=row["key"],
                    user_id=row["user_id"],
                    name=row["name"],
                    permissions=json.loads(row["permissions"]),
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    is_active=bool(row["is_active"]),
                    usage_count=row["usage_count"]
                ) for row in rows
            ]

        except Exception as e:
            self.logger.error(f"Failed to get API keys: {e}")
            return []

    def list_users(self) -> List[User]:
        """List all users"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()

            return [
                User(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    role=UserRole(row["role"]),
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"],
                    last_login=row["last_login"]
                ) for row in rows
            ]

        except Exception as e:
            self.logger.error(f"Failed to list users: {e}")
            return []

    def update_user_role(self, user_id: str, role: UserRole) -> bool:
        """Update user role"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role.value, user_id)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return updated

        except Exception as e:
            self.logger.error(f"Failed to update user role: {e}")
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            deactivated = cursor.rowcount > 0
            conn.commit()
            conn.close()

            return deactivated

        except Exception as e:
            self.logger.error(f"Failed to deactivate user: {e}")
            return False


# Singleton instance
user_service = UserManagementService()


class PermissionChecker:
    """Middleware for checking permissions"""

    @staticmethod
    def require_permission(permission: Permission):
        """Decorator to require specific permission"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract user_id from request context (would need FastAPI dependency)
                # For now, we'll check from API key or session
                user_id = kwargs.get("user_id")
                if not user_id:
                    return {"error": "Authentication required"}

                if not user_service.has_permission(user_id, permission):
                    return {"error": f"Permission '{permission.value}' required"}

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def require_role(role: UserRole):
        """Decorator to require specific role"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                user_id = kwargs.get("user_id")
                if not user_id:
                    return {"error": "Authentication required"}

                user = user_service.get_user(user_id)
                if not user or user.role.value != role.value:
                    return {"error": f"Role '{role.value}' required"}

                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Default admin creation utility
def create_default_admin():
    """Create default admin user if none exists"""
    try:
        user_service.initialize()

        # Check if any admin exists
        conn = sqlite3.connect(user_service.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            user_id = user_service.create_user(
                username="admin",
                password="admin123",  # CHANGE THIS IN PRODUCTION!
                email="admin@localhost",
                role=UserRole.ADMIN
            )

            if user_id:
                print(f"✅ Default admin created: username='admin', password='admin123'")
                print("⚠️  WARNING: Change the default password immediately!")

    except Exception as e:
        print(f"⚠️  Failed to create default admin: {e}")


# Import json for the functions that use it
import json
