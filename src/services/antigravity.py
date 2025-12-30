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
    
    def get_auth_data(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get full auth data from Antigravity's local database.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data from database
        
        Returns:
            Dictionary with name, email, apiKey, or None if not available
        """
        if self._auth_data and not force_refresh:
            print(f"DEBUG [AntigravityAuth]: Using CACHED auth data")
            return self._auth_data
        
        if not self.DB_PATH.exists():
            print(f"ERROR [AntigravityAuth]: Database not found at {self.DB_PATH}")
            return None
        
        print(f"DEBUG [AntigravityAuth]: Accessing SQLite database at {self.DB_PATH}")
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
                print(f"DEBUG [AntigravityAuth]: Successfully loaded auth data from database")
                return self._auth_data
            else:
                print(f"ERROR [AntigravityAuth]: No row found for key '{self.AUTH_KEY}'")
        except Exception as e:
            print(f"ERROR [AntigravityAuth]: Database access failed - {type(e).__name__}: {str(e)}")
            pass
        
        return None
    
    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get OAuth Bearer token for Antigravity API.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh token from database
        
        Returns:
            Bearer token string or None if not available
        """
        # DEBUG: Track token retrieval pattern
        if self._cached_token and not force_refresh:
            print(f"DEBUG [AntigravityAuth]: Using CACHED token (first 20 chars): {self._cached_token[:20]}...")
            return self._cached_token
        
        print(f"DEBUG [AntigravityAuth]: Fetching FRESH token from database (force_refresh={force_refresh})")
        auth_data = self.get_auth_data(force_refresh=force_refresh)
        if auth_data:
            new_token = auth_data.get('apiKey')
            if new_token:
                # Detect token changes
                if self._cached_token and self._cached_token != new_token:
                    print(f"WARNING [AntigravityAuth]: Token CHANGED! Old: {self._cached_token[:20]}... New: {new_token[:20]}...")
                else:
                    print(f"DEBUG [AntigravityAuth]: Token retrieved successfully (first 20 chars): {new_token[:20]}...")
                
                self._cached_token = new_token
                return self._cached_token
            else:
                print(f"ERROR [AntigravityAuth]: Auth data found but apiKey is missing!")
        else:
            print(f"ERROR [AntigravityAuth]: No auth data found in database at {self.DB_PATH}")
        
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


# Available Antigravity/VibeProxy models (from VibeProxy /v1/models endpoint - Dec 2025)
ANTIGRAVITY_MODELS = [
    # Gemini 3 Series (Bleeding Edge)
    "gemini-3-flash",
    "gemini-3-pro-preview",
    "gemini-3-pro-image-preview",
    # Gemini 2.5 Series (Stable/Fast)
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-thinking-exp",
    "gemini-2.5-computer-use-preview-10-2025",
    # Claude via VibeProxy
    "claude-sonnet-4",
    "claude-opus-4",
    "gemini-claude-sonnet-4-5",
    "gemini-claude-sonnet-4-5-thinking",
    "gemini-claude-opus-4-5-thinking",
    # OpenAI via VibeProxy
    "gpt-4o",
    "gpt-4o-mini",
    # Qwen via VibeProxy
    "qwen-2.5-max",
    "qwen-2.5-coder-32b",
    # Open Source / Other
    "gpt-oss-120b-medium",
]

# Friendly aliases for VibeProxy models (maps user-friendly names to actual IDs)
# Both vibeproxy/ and antigravity/ prefixes are supported
ANTIGRAVITY_ALIASES = {
    # ═══════════════════════════════════════════════════════════════════════════════
    # VIBEPROXY/ PREFIX (Recommended - clearer intent)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Gemini via VibeProxy
    "vibeproxy/gemini-2.5-pro": "gemini-2.5-pro",
    "vibeproxy/gemini-2.5-flash": "gemini-2.5-flash",
    "vibeproxy/gemini-2.0-flash-thinking": "gemini-2.0-flash-thinking-exp",
    "vibeproxy/gemini-3-pro": "gemini-3-pro-preview",
    "vibeproxy/gemini-3-flash": "gemini-3-flash",
    
    # Claude via VibeProxy
    "vibeproxy/claude-sonnet-4": "claude-sonnet-4",
    "vibeproxy/claude-opus-4": "claude-opus-4",
    "vibeproxy/claude-sonnet-4.5": "gemini-claude-sonnet-4-5",
    "vibeproxy/claude-sonnet-4.5-thinking": "gemini-claude-sonnet-4-5-thinking",
    "vibeproxy/claude-opus-4.5": "gemini-claude-opus-4-5-thinking",
    
    # OpenAI via VibeProxy
    "vibeproxy/gpt-4o": "gpt-4o",
    "vibeproxy/gpt-4o-mini": "gpt-4o-mini",
    
    # Qwen via VibeProxy
    "vibeproxy/qwen-2.5-max": "qwen-2.5-max",
    "vibeproxy/qwen-2.5-coder": "qwen-2.5-coder-32b",
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ANTIGRAVITY/ PREFIX (Legacy - still supported for backward compatibility)
    # ═══════════════════════════════════════════════════════════════════════════════
    
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

