"""
Billing API Endpoints

Provides access to real-time billing data from provider APIs.
"""

from fastapi import APIRouter, Query, HTTPException
from src.billing.billing_integrations import billing_manager
from src.core.logging import logger

router = APIRouter()


@router.get("/api/billing/usage")
async def get_billing_usage(
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Fetch actual billing usage from all configured providers.

    Returns real billing data where available, falls back to estimates.
    """
    try:
        usage_data = await billing_manager.fetch_all_usage(days=days)
        return usage_data
    except Exception as e:
        logger.error(f"Failed to fetch billing usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/billing/balance")
async def get_billing_balance():
    """
    Fetch current account balance/credits from all configured providers.

    Returns current billing status and remaining credits.
    """
    try:
        balance_data = await billing_manager.fetch_all_balances()
        return balance_data
    except Exception as e:
        logger.error(f"Failed to fetch billing balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/billing/provider/{provider_name}")
async def get_provider_billing(
    provider_name: str,
    days: int = Query(7, ge=1, le=90, description="Number of days")
):
    """
    Fetch billing data for a specific provider.

    Supported providers: openai, openrouter, anthropic
    """
    provider = billing_manager.get_provider(provider_name)

    if not provider:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider_name}' not found. Available: openai, openrouter, anthropic"
        )

    if not provider.enabled:
        raise HTTPException(
            status_code=503,
            detail=f"Provider '{provider_name}' is not configured. Add API key to environment."
        )

    try:
        from datetime import datetime, timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        usage_data = await provider.fetch_usage(start_date, end_date)
        balance_data = await provider.fetch_current_balance()

        return {
            "provider": provider_name,
            "usage": usage_data,
            "balance": balance_data
        }
    except Exception as e:
        logger.error(f"Failed to fetch {provider_name} billing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
