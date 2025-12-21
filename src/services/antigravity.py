"""Antigravity token extraction and API client.

This module provides functionality to extract OAuth tokens from the
local Antigravity IDE installation and make API calls using those credentials.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any


class AntigravityAuth:
    """Extract and manage Antigravity OAuth tokens."""
    
    DB_PATH = Path.home() / "Library/Application Support/Antigravity/User/globalStorage/state.vscdb"
    AUTH_KEY = "antigravityAuthStatus"
    
    def __init__(self):
        self._cached_token: Optional[str] = None
        self._auth_data: Optional[Dict[str, Any]] = None
    
    def get_auth_data(self) -> Optional[Dict[str, Any]]:
        """
        Get full auth data from Antigravity's local database.
        
        Returns:
            Dictionary with name, email, apiKey, or None if not available
        """
        if self._auth_data:
            return self._auth_data
        
        if not self.DB_PATH.exists():
            return None
        
        try:
            conn = sqlite3.connect(str(self.DB_PATH))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM ItemTable WHERE key=?;",
                (self.AUTH_KEY,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self._auth_data = json.loads(row[0])
                return self._auth_data
        except Exception:
            pass
        
        return None
    
    def get_token(self) -> Optional[str]:
        """
        Get OAuth Bearer token for Antigravity API.
        
        Returns:
            Bearer token string or None if not available
        """
        if self._cached_token:
            return self._cached_token
        
        auth_data = self.get_auth_data()
        if auth_data:
            self._cached_token = auth_data.get('apiKey')
            return self._cached_token
        
        return None
    
    def get_email(self) -> Optional[str]:
        """Get user email."""
        auth_data = self.get_auth_data()
        return auth_data.get('email') if auth_data else None
    
    def get_name(self) -> Optional[str]:
        """Get user name."""
        auth_data = self.get_auth_data()
        return auth_data.get('name') if auth_data else None
    
    def is_available(self) -> bool:
        """Check if Antigravity auth is available."""
        return self.get_token() is not None
    
    def clear_cache(self) -> None:
        """Clear cached token (refresh on next call)."""
        self._cached_token = None
        self._auth_data = None


# Singleton instance
_auth_instance: Optional[AntigravityAuth] = None


def get_antigravity_auth() -> AntigravityAuth:
    """Get or create the Antigravity auth singleton."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AntigravityAuth()
    return _auth_instance


def get_antigravity_token() -> Optional[str]:
    """Convenience function to get Antigravity OAuth token."""
    return get_antigravity_auth().get_token()


# Available Antigravity models (from VibeProxy /v1/models endpoint - Dec 2025)
ANTIGRAVITY_MODELS = [
    # Gemini 3 Series (Bleeding Edge)
    "gemini-3-flash",
    "gemini-3-pro-preview",
    "gemini-3-pro-image-preview",
    # Gemini 2.5 Series (Stable/Fast)
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-computer-use-preview-10-2025",
    # Claude via Antigravity
    "gemini-claude-sonnet-4-5",
    "gemini-claude-sonnet-4-5-thinking",
    "gemini-claude-opus-4-5-thinking",
    # Open Source / Other
    "gpt-oss-120b-medium",
]

# Friendly aliases for Antigravity models (maps user-friendly names to actual IDs)
ANTIGRAVITY_ALIASES = {
    # Gemini 3 aliases
    "antigravity/gemini-3-pro": "gemini-3-pro-preview",
    "antigravity/gemini-3-pro-high": "gemini-3-pro-preview",
    "antigravity/gemini-3-pro-low": "gemini-3-pro-preview",
    "antigravity/gemini-3-flash": "gemini-3-flash",
    # Claude via Antigravity aliases
    "antigravity/claude-sonnet-4.5": "gemini-claude-sonnet-4-5",
    "antigravity/claude-sonnet-4.5-thinking": "gemini-claude-sonnet-4-5-thinking",
    "antigravity/claude-opus-4.5": "gemini-claude-opus-4-5-thinking",
    # GPT-OSS alias
    "antigravity/gpt-oss-120b": "gpt-oss-120b-medium",
}
