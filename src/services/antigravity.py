"""Antigravity token extraction and API client.

This module provides functionality to extract OAuth tokens from the
local Antigravity IDE installation and make API calls using those credentials.
"""

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)

# VibeProxy configuration
VIBEPROXY_BASE_URL = os.getenv("VIBEPROXY_URL", "http://127.0.0.1:1337")
VIBEPROXY_HEALTH_TIMEOUT = float(os.getenv("VIBEPROXY_HEALTH_TIMEOUT", "2.0"))

# Health check cache
_vibeproxy_health_cache: Dict[str, Any] = {
    "available": None,
    "last_check": 0,
    "cache_ttl": 30.0,  # Cache health status for 30 seconds
}


def check_vibeproxy_health(force_refresh: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check if VibeProxy is available and responding.

    Args:
        force_refresh: Bypass cache and check immediately

    Returns:
        Tuple of (is_available, error_message)
    """
    global _vibeproxy_health_cache

    now = time.time()
    cache_age = now - _vibeproxy_health_cache["last_check"]

    # Return cached result if still valid
    if not force_refresh and cache_age < _vibeproxy_health_cache["cache_ttl"]:
        if _vibeproxy_health_cache["available"] is not None:
            return _vibeproxy_health_cache["available"], None

    # Perform health check
    try:
        response = httpx.get(
            f"{VIBEPROXY_BASE_URL}/health",
            timeout=VIBEPROXY_HEALTH_TIMEOUT
        )
        is_available = response.status_code == 200

        _vibeproxy_health_cache["available"] = is_available
        _vibeproxy_health_cache["last_check"] = now

        if is_available:
            logger.debug(f"VibeProxy health check passed")
        else:
            logger.warning(f"VibeProxy health check failed: status {response.status_code}")

        return is_available, None if is_available else f"Status {response.status_code}"

    except httpx.ConnectError as e:
        _vibeproxy_health_cache["available"] = False
        _vibeproxy_health_cache["last_check"] = now
        error_msg = "VibeProxy not reachable (connection refused)"
        logger.warning(f"{error_msg}: {e}")
        return False, error_msg

    except httpx.TimeoutException:
        _vibeproxy_health_cache["available"] = False
        _vibeproxy_health_cache["last_check"] = now
        error_msg = f"VibeProxy health check timed out ({VIBEPROXY_HEALTH_TIMEOUT}s)"
        logger.warning(error_msg)
        return False, error_msg

    except Exception as e:
        _vibeproxy_health_cache["available"] = False
        _vibeproxy_health_cache["last_check"] = now
        error_msg = f"VibeProxy health check error: {type(e).__name__}"
        logger.error(f"{error_msg}: {e}")
        return False, error_msg


def is_vibeproxy_available() -> bool:
    """Quick check if VibeProxy is available (uses cache)."""
    available, _ = check_vibeproxy_health()
    return available


def clear_vibeproxy_health_cache():
    """Clear the health check cache to force fresh check."""
    global _vibeproxy_health_cache
    _vibeproxy_health_cache["available"] = None
    _vibeproxy_health_cache["last_check"] = 0


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
            logger.debug(f"[AntigravityAuth] Using CACHED auth data")
            return self._auth_data
        
        if not self.DB_PATH.exists():
            print(f"ERROR [AntigravityAuth]: Database not found at {self.DB_PATH}")
            return None
        
        logger.debug(f"[AntigravityAuth] Accessing SQLite database at {self.DB_PATH}")
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
                logger.debug(f"[AntigravityAuth] Successfully loaded auth data from database")
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
            logger.debug(f"[AntigravityAuth] Using CACHED token (first 20 chars): {self._cached_token[:20]}...")
            return self._cached_token
        
        logger.debug(f"[AntigravityAuth] Fetching FRESH token from database (force_refresh={force_refresh})")
        auth_data = self.get_auth_data(force_refresh=force_refresh)
        if auth_data:
            new_token = auth_data.get('apiKey')
            if new_token:
                # Detect token changes
                if self._cached_token and self._cached_token != new_token:
                    print(f"WARNING [AntigravityAuth]: Token CHANGED! Old: {self._cached_token[:20]}... New: {new_token[:20]}...")
                else:
                    logger.debug(f"[AntigravityAuth] Token retrieved successfully (first 20 chars): {new_token[:20]}...")
                
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

