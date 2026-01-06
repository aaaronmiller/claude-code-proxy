"""
Provider Authentication API

Endpoints for managing provider authentication tokens and credentials.

Author: AI Architect
Date: 2026-01-05
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.logging import logger
from src.services.providers.kiro_token_manager import (
    KiroTokenManager,
    get_token_manager,
    store_kiro_tokens,
    has_kiro_token
)
from src.services.providers.provider_detector import (
    detect_provider,
    get_provider_info,
    get_provider_config,
    requires_kiro_token
)

router = APIRouter()


@router.get("/api/providers/{base_url}/info")
async def get_provider_info_endpoint(base_url: str):
    """
    Get provider information for a given base URL.

    Args:
        base_url: The API base URL to analyze

    Returns:
        Provider detection results
    """
    try:
        provider, normalization, auth_type = get_provider_info(base_url)
        config = get_provider_config(provider)

        return {
            "base_url": base_url,
            "detected_provider": provider,
            "normalization_level": normalization,
            "auth_type": auth_type,
            "config": config,
            "requires_kiro_token": requires_kiro_token(base_url)
        }
    except Exception as e:
        logger.error(f"Failed to get provider info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/providers/kiro/tokens")
async def set_kiro_tokens(token_data: Dict[str, Any]):
    """
    Set Kiro authentication tokens.

    Args:
        token_data: Dictionary containing:
            - access_token (required): Kiro access token
            - refresh_token (optional): Kiro refresh token
            - expires_in (optional): Token lifetime in seconds

    Returns:
        Success confirmation
    """
    try:
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="access_token is required")

        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        success = store_kiro_tokens(access_token, refresh_token, expires_in)

        if success:
            return {
                "success": True,
                "provider": "kiro",
                "status": "tokens_stored",
                "stored_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store tokens")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store Kiro tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/providers/kiro/tokens")
async def get_kiro_tokens_info():
    """
    Get information about stored Kiro tokens.

    Returns:
        Token status and metadata
    """
    try:
        manager = get_token_manager()
        info = manager.get_token_info()

        return {
            "provider": "kiro",
            "tokens": info,
            "has_valid_token": has_kiro_token()
        }
    except Exception as e:
        logger.error(f"Failed to get Kiro token info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/providers/kiro/tokens")
async def clear_kiro_tokens():
    """
    Clear stored Kiro tokens.

    Returns:
        Success confirmation
    """
    try:
        manager = get_token_manager()
        manager.clear_tokens()

        return {
            "success": True,
            "provider": "kiro",
            "status": "tokens_cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear Kiro tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/providers/kiro/refresh")
async def refresh_kiro_tokens():
    """
    Refresh Kiro tokens using refresh token (if available).

    Returns:
        New token information or error
    """
    try:
        manager = get_token_manager()
        success = manager.refresh_tokens()

        if success:
            return {
                "success": True,
                "provider": "kiro",
                "status": "refreshed",
                "new_tokens": manager.get_token_info()
            }
        else:
            raise HTTPException(status_code=400, detail="No refresh token available or refresh failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh Kiro tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/providers/kiro/health")
async def kiro_health_check():
    """
    Check if Kiro provider is configured and ready.

    Returns:
        Health status
    """
    try:
        manager = get_token_manager()
        has_token = manager.has_valid_token()
        token_info = manager.get_token_info()

        return {
            "provider": "kiro",
            "status": "healthy" if has_token else "unconfigured",
            "has_valid_token": has_token,
            "token_info": token_info,
            "config_instructions": {
                "environment_variable": "KIRO_ACCESS_TOKEN",
                "api_endpoint": "/api/providers/kiro/tokens (POST)",
                "required_data": {"access_token": "your-kiro-access-token"}
            }
        }
    except Exception as e:
        logger.error(f"Kiro health check failed: {e}")
        return {
            "provider": "kiro",
            "status": "error",
            "error": str(e)
        }


@router.post("/api/providers/{provider}/test")
async def test_provider_auth(provider: str, config: Dict[str, Any]):
    """
    Test authentication for a specific provider.

    Args:
        provider: Provider name (e.g., 'kiro')
        config: Configuration data for testing

    Returns:
        Authentication test results
    """
    try:
        # This is a placeholder for future provider authentication testing
        # For Kiro, it would verify the access token works with the API

        if provider.lower() == "kiro":
            has_token = has_kiro_token()
            return {
                "provider": provider,
                "auth_test": "pending",
                "status": "configured" if has_token else "unconfigured",
                "message": "Token exists - ready for API calls" if has_token else "No token configured"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not supported for auth testing")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth test failed for {provider}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
