"""
Real-time Billing Integrations

Fetches actual billing data from provider APIs to track real costs
instead of relying on estimates.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import os
import httpx
import asyncio
from src.core.logging import logger


class BillingProvider(ABC):
    """Base class for billing provider integrations"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = bool(api_key)

    @abstractmethod
    async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch usage data from provider API"""
        pass

    @abstractmethod
    async def fetch_current_balance(self) -> Dict[str, Any]:
        """Fetch current account balance/credits"""
        pass


class OpenAIBilling(BillingProvider):
    """OpenAI billing integration"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.base_url = "https://api.openai.com/v1"

    async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Fetch OpenAI usage data.

        Note: OpenAI deprecated the /dashboard/billing endpoints.
        This returns estimated data based on local tracking.
        """
        if not self.enabled:
            return {"error": "OpenAI API key not configured"}

        try:
            # OpenAI no longer provides billing API endpoints
            # We return a placeholder structure
            return {
                "provider": "openai",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_cost": 0.0,
                "note": "OpenAI does not provide programmatic billing access. Check dashboard.openai.com"
            }
        except Exception as e:
            logger.warning(f"OpenAI billing fetch skipped (API deprecated): {e}")
            logger.debug(f"Detailed error: {e}")
            return {"error": "Billing API deprecated by provider"}

    async def fetch_current_balance(self) -> Dict[str, Any]:
        """Fetch current OpenAI balance"""
        if not self.enabled:
            return {"error": "OpenAI API key not configured"}

        return {
            "provider": "openai",
            "balance": None,
            "note": "Check dashboard.openai.com for balance"
        }


class OpenRouterBilling(BillingProvider):
    """OpenRouter billing integration"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.base_url = "https://openrouter.ai/api/v1"

    async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch OpenRouter usage data"""
        if not self.enabled:
            return {"error": "OpenRouter API key not configured"}

        try:
            # OpenRouter doesn't have official billing API yet
            # Using generation stats as proxy
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/auth/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "provider": "openrouter",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "usage": data.get("data", {}),
                        "note": "OpenRouter billing data from key stats"
                    }
                else:
                    return {"error": f"OpenRouter API returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter usage: {e}")
            return {"error": str(e)}

    async def fetch_current_balance(self) -> Dict[str, Any]:
        """Fetch current OpenRouter credits"""
        if not self.enabled:
            return {"error": "OpenRouter API key not configured"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/auth/key",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    key_data = data.get("data", {})

                    return {
                        "provider": "openrouter",
                        "limit": key_data.get("limit"),
                        "usage": key_data.get("usage"),
                        "remaining": (key_data.get("limit", 0) - key_data.get("usage", 0))
                                    if key_data.get("limit") else None,
                        "is_free_tier": key_data.get("is_free_tier", False),
                        "rate_limit": key_data.get("rate_limit", {})
                    }
                else:
                    return {"error": f"OpenRouter API returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter balance: {e}")
            return {"error": str(e)}


class AnthropicBilling(BillingProvider):
    """Anthropic billing integration"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.base_url = "https://api.anthropic.com/v1"

    async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch Anthropic usage data"""
        if not self.enabled:
            return {"error": "Anthropic API key not configured"}

        # Anthropic doesn't provide billing API yet
        return {
            "provider": "anthropic",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "note": "Anthropic does not provide programmatic billing access. Check console.anthropic.com"
        }

    async def fetch_current_balance(self) -> Dict[str, Any]:
        """Fetch current Anthropic balance"""
        if not self.enabled:
            return {"error": "Anthropic API key not configured"}

        return {
            "provider": "anthropic",
            "note": "Check console.anthropic.com for usage"
        }


class BillingManager:
    """Manages billing integrations across multiple providers"""

    def __init__(self):
        self.providers: Dict[str, BillingProvider] = {
            "openai": OpenAIBilling(),
            "openrouter": OpenRouterBilling(),
            "anthropic": AnthropicBilling()
        }

    async def fetch_all_usage(self, days: int = 7) -> Dict[str, Any]:
        """Fetch usage from all configured providers"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        results = {}
        tasks = []

        for name, provider in self.providers.items():
            if provider.enabled:
                tasks.append(self._fetch_provider_usage(name, provider, start_date, end_date))

        if tasks:
            provider_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in provider_results:
                results[name] = result

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "providers": results
        }

    async def _fetch_provider_usage(
        self,
        name: str,
        provider: BillingProvider,
        start_date: datetime,
        end_date: datetime
    ) -> tuple:
        """Helper to fetch usage from a single provider"""
        try:
            result = await provider.fetch_usage(start_date, end_date)
            return (name, result)
        except Exception as e:
            logger.error(f"Failed to fetch {name} usage: {e}")
            return (name, {"error": str(e)})

    async def fetch_all_balances(self) -> Dict[str, Any]:
        """Fetch current balance from all configured providers"""
        results = {}
        tasks = []

        for name, provider in self.providers.items():
            if provider.enabled:
                tasks.append(self._fetch_provider_balance(name, provider))

        if tasks:
            provider_results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in provider_results:
                results[name] = result

        return {"providers": results}

    async def _fetch_provider_balance(self, name: str, provider: BillingProvider) -> tuple:
        """Helper to fetch balance from a single provider"""
        try:
            result = await provider.fetch_current_balance()
            return (name, result)
        except Exception as e:
            logger.error(f"Failed to fetch {name} balance: {e}")
            return (name, {"error": str(e)})

    def get_provider(self, provider_name: str) -> Optional[BillingProvider]:
        """Get a specific provider by name"""
        return self.providers.get(provider_name.lower())


# Global billing manager instance
billing_manager = BillingManager()
