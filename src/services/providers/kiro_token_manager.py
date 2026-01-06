"""
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
"""

import os
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.core.logging import logger


@dataclass
class KiroTokens:
    """Kiro authentication tokens."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[int] = None  # Unix timestamp

    def is_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        return time.time() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if tokens are valid."""
        if not self.access_token:
            return False
        if self.is_expired():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KiroTokens':
        """Create from dictionary."""
        return cls(
            access_token=data.get('access_token', ''),
            refresh_token=data.get('refresh_token'),
            token_type=data.get('token_type', 'Bearer'),
            expires_at=data.get('expires_at')
        )


class KiroTokenManager:
    """Manager for Kiro authentication tokens."""

    def __init__(self, storage_path: str = None):
        """
        Initialize Kiro token manager.

        Args:
            storage_path: Optional path for token storage file
        """
        self.storage_path = storage_path or os.path.expanduser("~/.claude-proxy/kiro_tokens.json")
        self.tokens: Optional[KiroTokens] = None
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.tokens = KiroTokens.from_dict(data)
                    logger.info(f"✅ Loaded Kiro tokens from {self.storage_path}")
            else:
                logger.debug("No existing Kiro tokens found")
        except Exception as e:
            logger.error(f"❌ Failed to load Kiro tokens: {e}")
            self.tokens = None

    def _save_tokens(self):
        """Save tokens to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                if self.tokens:
                    json.dump(self.tokens.to_dict(), f, indent=2)
                else:
                    json.dump({}, f)
            logger.debug(f"💾 Saved Kiro tokens to {self.storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save Kiro tokens: {e}")

    def store_tokens(self, access_token: str, refresh_token: str = None, expires_in: int = None):
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

        self.tokens = KiroTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        self._save_tokens()
        logger.info("✅ Kiro tokens stored successfully")

    def get_access_token(self) -> Optional[str]:
        """
        Get current access token.

        Returns:
            Access token string or None if not available/expired
        """
        if not self.tokens:
            logger.debug("No Kiro tokens available")
            return None

        if self.tokens.is_expired():
            logger.warning("⚠️ Kiro access token has expired")
            # TODO: Implement auto-refresh if we have refresh token
            return None

        if not self.tokens.is_valid():
            logger.warning("⚠️ Kiro tokens are invalid")
            return None

        return self.tokens.access_token

    def has_valid_token(self) -> bool:
        """Check if valid token is available."""
        token = self.get_access_token()
        return token is not None

    def clear_tokens(self):
        """Clear stored tokens."""
        self.tokens = None
        try:
            if os.path.exists(self.storage_path):
                os.remove(self.storage_path)
                logger.info("🗑️ Cleared Kiro tokens")
        except Exception as e:
            logger.error(f"❌ Failed to clear tokens: {e}")

    def get_auth_header(self) -> Optional[Dict[str, str]]:
        """
        Get authentication header for Kiro requests.

        Returns:
            Dictionary with Authorization header or empty dict
        """
        token = self.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def refresh_tokens(self) -> bool:
        """
        Refresh tokens using refresh token (if available).
        This is a placeholder - actual refresh logic depends on Kiro's API.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.tokens or not self.tokens.refresh_token:
            logger.warning("⚠️ No refresh token available")
            return False

        # TODO: Implement actual token refresh with Kiro's auth API
        # For now, this is a placeholder
        logger.info("🔄 Token refresh would be called here")
        return False

    def get_token_info(self) -> Dict[str, Any]:
        """
        Get token information for diagnostics.

        Returns:
            Dictionary with token metadata
        """
        if not self.tokens:
            return {"status": "no_tokens"}

        info = {
            "status": "valid" if self.tokens.is_valid() else "invalid",
            "expired": self.tokens.is_expired(),
            "has_refresh_token": self.tokens.refresh_token is not None,
        }

        if self.tokens.expires_at:
            info["expires_at"] = datetime.fromtimestamp(self.tokens.expires_at).isoformat()
            info["seconds_until_expiry"] = max(0, self.tokens.expires_at - int(time.time()))

        return info


# Global instance for convenience
_token_manager: Optional[KiroTokenManager] = None


def get_token_manager() -> KiroTokenManager:
    """Get or create global Kiro token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = KiroTokenManager()
    return _token_manager


def store_kiro_tokens(access_token: str, refresh_token: str = None, expires_in: int = None) -> bool:
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
        logger.error(f"Failed to store Kiro tokens: {e}")
        return False


def get_kiro_auth_header() -> Dict[str, str]:
    """
    Get authentication header for Kiro API requests.

    Returns:
        Dict with Authorization header or empty dict if no valid token
    """
    manager = get_token_manager()
    return manager.get_auth_header()


def has_kiro_token() -> bool:
    """Check if valid Kiro token is available."""
    manager = get_token_manager()
    return manager.has_valid_token()
