"""
Provider Detection and Adapter Module.

This module provides provider detection and normalization level configuration
for multi-provider proxy support. It enables the Claude Code proxy to work
with any LLM provider (Gemini, OpenRouter, OpenAI, Anthropic, Azure, etc.)
by applying appropriate transformations based on the detected provider.
"""

from typing import Tuple
from enum import Enum


class Provider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"           # Gemini via VibeProxy (Antigravity)
    OPENROUTER = "openrouter"   # OpenRouter unified API
    OPENAI = "openai"           # OpenAI direct
    ANTHROPIC = "anthropic"     # Anthropic direct
    AZURE = "azure"             # Azure OpenAI
    KIRO = "kiro"               # Kiro provider (Claude API compatible, token-based)
    OPENAI_COMPATIBLE = "openai_compatible"  # Unknown OpenAI-compatible endpoint


class NormalizationLevel(str, Enum):
    """
    Tool call normalization intensity levels.
    
    NONE: Pass through unchanged (OpenAI, Azure)
    LIGHT: Common mismatches only (OpenRouter, unknown)
    FULL: All 18+ tool transformations (Gemini)
    SCHEMA_CONVERT: Convert different schema format (Anthropic direct)
    """
    NONE = "none"
    LIGHT = "light"
    FULL = "full"
    SCHEMA_CONVERT = "schema_convert"


class AuthType(str, Enum):
    """Authentication types for different providers."""
    API_KEY = "api_key"         # Standard API key header
    OAUTH = "oauth"             # OAuth token (Gemini/VibeProxy)
    AZURE = "azure"             # Azure-specific auth
    KIRO_TOKEN = "kiro_token"   # Kiro access/refresh token auth


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
    
    # VibeProxy/Gemini (Antigravity) - local proxy on port 8317
    if "127.0.0.1:8317" in url_lower or "localhost:8317" in url_lower:
        return Provider.GEMINI.value
    
    # Google AI Studio / Gemini direct
    if "generativelanguage.googleapis.com" in url_lower or "gemini" in url_lower:
        return Provider.GEMINI.value
    
    # OpenRouter
    if "openrouter.ai" in url_lower:
        return Provider.OPENROUTER.value
    
    # Anthropic direct
    if "anthropic.com" in url_lower:
        return Provider.ANTHROPIC.value
    
    # Azure OpenAI
    if "azure" in url_lower or ".openai.azure.com" in url_lower:
        return Provider.AZURE.value
    
    # OpenAI direct
    if "api.openai.com" in url_lower:
        return Provider.OPENAI.value

    # Kiro provider - Claude API compatible, typically local proxy
    # Common patterns: kiro endpoints, kiro2cc proxy, kiro.ai domains
    if "kiro" in url_lower or "127.0.0.1:8083" in url_lower or "localhost:8083" in url_lower or "kiro.ai" in url_lower:
        return Provider.KIRO.value

    # Default to openai-compatible for unknown endpoints
    return Provider.OPENAI_COMPATIBLE.value


def get_normalization_level(provider: str) -> str:
    """
    Get the appropriate normalization level for a provider.
    
    Args:
        provider: Provider identifier from detect_provider()
        
    Returns:
        NormalizationLevel value
    """
    normalization_map = {
        Provider.GEMINI.value: NormalizationLevel.FULL.value,
        Provider.OPENROUTER.value: NormalizationLevel.LIGHT.value,
        Provider.OPENAI.value: NormalizationLevel.NONE.value,
        Provider.ANTHROPIC.value: NormalizationLevel.SCHEMA_CONVERT.value,
        Provider.AZURE.value: NormalizationLevel.NONE.value,
        Provider.KIRO.value: NormalizationLevel.LIGHT.value,
        Provider.OPENAI_COMPATIBLE.value: NormalizationLevel.LIGHT.value,
    }
    
    return normalization_map.get(provider, NormalizationLevel.LIGHT.value)


def get_auth_type(provider: str) -> str:
    """
    Get the authentication type for a provider.
    
    Args:
        provider: Provider identifier from detect_provider()
        
    Returns:
        AuthType value
    """
    auth_map = {
        Provider.GEMINI.value: AuthType.OAUTH.value,
        Provider.AZURE.value: AuthType.AZURE.value,
        Provider.KIRO.value: AuthType.KIRO_TOKEN.value,
    }
    
    return auth_map.get(provider, AuthType.API_KEY.value)


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
    
    return provider, normalization, auth


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


# Provider-specific configuration
PROVIDER_CONFIG = {
    Provider.GEMINI.value: {
        "name": "Gemini (VibeProxy)",
        "normalization": NormalizationLevel.FULL.value,
        "auth": AuthType.OAUTH.value,
        "supports_streaming": True,
        "has_ghost_streams": True,
        "requires_deduplication": True,
    },
    Provider.OPENROUTER.value: {
        "name": "OpenRouter",
        "normalization": NormalizationLevel.LIGHT.value,
        "auth": AuthType.API_KEY.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
    Provider.OPENAI.value: {
        "name": "OpenAI",
        "normalization": NormalizationLevel.NONE.value,
        "auth": AuthType.API_KEY.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
    Provider.ANTHROPIC.value: {
        "name": "Anthropic",
        "normalization": NormalizationLevel.SCHEMA_CONVERT.value,
        "auth": AuthType.API_KEY.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
    Provider.AZURE.value: {
        "name": "Azure OpenAI",
        "normalization": NormalizationLevel.NONE.value,
        "auth": AuthType.AZURE.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
    Provider.KIRO.value: {
        "name": "Kiro (Claude API Compatible)",
        "normalization": NormalizationLevel.LIGHT.value,
        "auth": AuthType.KIRO_TOKEN.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
    Provider.OPENAI_COMPATIBLE.value: {
        "name": "OpenAI-Compatible",
        "normalization": NormalizationLevel.LIGHT.value,
        "auth": AuthType.API_KEY.value,
        "supports_streaming": True,
        "has_ghost_streams": False,
        "requires_deduplication": False,
    },
}


def get_provider_config(provider: str) -> dict:
    """
    Get full configuration for a provider.
    
    Args:
        provider: Provider identifier
        
    Returns:
        Configuration dictionary
    """
    return PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG[Provider.OPENAI_COMPATIBLE.value])
