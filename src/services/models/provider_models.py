"""
Provider Model Fetcher

Fetches available models from each configured provider endpoint using live API calls.
This validates API keys and gets real-time model availability.

Supports:
- VibeProxy (local Gemini proxy)
- OpenRouter
- OpenAI
- Anthropic
- Any OpenAI-compatible endpoint
"""

import asyncio
import httpx
import os
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a model with full statistics."""
    id: str
    name: str
    provider: str
    context_length: int = 128000
    max_output: int = 4096
    pricing_input: float = 0.0  # per million tokens
    pricing_output: float = 0.0
    is_free: bool = False
    created: int = 0
    # Extended fields from OpenRouter
    description: str = ""
    modality: str = "text->text"  # e.g., "text->text", "text+image->text"
    hugging_face_id: str = ""
    input_modalities: List[str] = None  # ["text"], ["text", "image"]
    output_modalities: List[str] = None  # ["text"]
    tokenizer: str = ""
    supported_parameters: List[str] = None  # ["temperature", "top_p", etc.]
    is_moderated: bool = False
    
    def __post_init__(self):
        if self.input_modalities is None:
            self.input_modalities = ["text"]
        if self.output_modalities is None:
            self.output_modalities = ["text"]
        if self.supported_parameters is None:
            self.supported_parameters = []


@dataclass
class EndpointStatus:
    """Status of an endpoint check."""
    endpoint: str
    provider: str
    is_connected: bool
    api_key_valid: bool
    models: List[ModelInfo]
    error: Optional[str] = None


class ProviderModelFetcher:
    """Fetches models from provider endpoints."""
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        await self.client.aclose()
    
    async def fetch_models(
        self,
        endpoint: str,
        api_key: Optional[str] = None
    ) -> EndpointStatus:
        """
        Fetch available models from an endpoint.
        
        Args:
            endpoint: API endpoint URL (e.g., http://127.0.0.1:8317/v1)
            api_key: Optional API key (uses global key if not provided)
            
        Returns:
            EndpointStatus with connection status and model list
        """
        # Detect provider from URL
        provider = self._detect_provider(endpoint)
        
        try:
            if provider == "openrouter":
                return await self._fetch_openrouter_models(endpoint, api_key)
            elif provider == "anthropic":
                return await self._fetch_anthropic_models(endpoint, api_key)
            else:
                # OpenAI-compatible (VibeProxy, OpenAI, Azure, etc.)
                return await self._fetch_openai_models(endpoint, api_key, provider)
        except httpx.TimeoutException:
            return EndpointStatus(
                endpoint=endpoint,
                provider=provider,
                is_connected=False,
                api_key_valid=False,
                models=[],
                error="Connection timeout"
            )
        except httpx.ConnectError as e:
            return EndpointStatus(
                endpoint=endpoint,
                provider=provider,
                is_connected=False,
                api_key_valid=False,
                models=[],
                error=f"Connection failed: {str(e)}"
            )
        except Exception as e:
            return EndpointStatus(
                endpoint=endpoint,
                provider=provider,
                is_connected=False,
                api_key_valid=False,
                models=[],
                error=str(e)
            )
    
    def _detect_provider(self, endpoint: str) -> str:
        """Detect provider from endpoint URL."""
        url_lower = endpoint.lower()
        
        if "openrouter.ai" in url_lower:
            return "openrouter"
        elif "api.anthropic.com" in url_lower:
            return "anthropic"
        elif "api.openai.com" in url_lower:
            return "openai"
        elif ".openai.azure.com" in url_lower:
            return "azure"
        elif "127.0.0.1" in url_lower or "localhost" in url_lower:
            return "vibeproxy"
        else:
            return "openai_compatible"
    
    async def _fetch_openai_models(
        self,
        endpoint: str,
        api_key: Optional[str],
        provider: str
    ) -> EndpointStatus:
        """Fetch models from OpenAI-compatible endpoint."""
        # Ensure endpoint ends properly
        base_url = endpoint.rstrip("/")
        if not base_url.endswith("/v1"):
            if "/v1" not in base_url:
                base_url += "/v1"
        
        models_url = f"{base_url}/models"
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = await self.client.get(models_url, headers=headers)
        
        if response.status_code == 401:
            return EndpointStatus(
                endpoint=endpoint,
                provider=provider,
                is_connected=True,
                api_key_valid=False,
                models=[],
                error="Invalid API key"
            )
        
        if response.status_code != 200:
            return EndpointStatus(
                endpoint=endpoint,
                provider=provider,
                is_connected=True,
                api_key_valid=True,
                models=[],
                error=f"HTTP {response.status_code}"
            )
        
        data = response.json()
        models = []
        
        for model in data.get("data", []):
            model_id = model.get("id", "")
            models.append(ModelInfo(
                id=model_id,
                name=model.get("name", model_id),
                provider=provider,
                context_length=model.get("context_length", 128000),
                max_output=model.get("max_output", 4096),
                created=model.get("created", 0)
            ))
        
        return EndpointStatus(
            endpoint=endpoint,
            provider=provider,
            is_connected=True,
            api_key_valid=True,
            models=models
        )
    
    async def _fetch_openrouter_models(
        self,
        endpoint: str,
        api_key: Optional[str]
    ) -> EndpointStatus:
        """Fetch models from OpenRouter with pricing data."""
        models_url = "https://openrouter.ai/api/v1/models"
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = await self.client.get(models_url, headers=headers)
        
        if response.status_code == 401:
            return EndpointStatus(
                endpoint=endpoint,
                provider="openrouter",
                is_connected=True,
                api_key_valid=False,
                models=[],
                error="Invalid API key"
            )
        
        if response.status_code != 200:
            return EndpointStatus(
                endpoint=endpoint,
                provider="openrouter",
                is_connected=True,
                api_key_valid=True,
                models=[],
                error=f"HTTP {response.status_code}"
            )
        
        data = response.json()
        models = []
        
        for model in data.get("data", []):
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})
            context = model.get("context_length", 128000)
            architecture = model.get("architecture", {})
            top_provider = model.get("top_provider", {})
            
            # Calculate pricing per million tokens
            prompt_price = float(pricing.get("prompt", 0)) * 1_000_000
            completion_price = float(pricing.get("completion", 0)) * 1_000_000
            
            models.append(ModelInfo(
                id=model_id,
                name=model.get("name", model_id),
                provider="openrouter",
                context_length=context,
                max_output=top_provider.get("max_completion_tokens", 4096),
                pricing_input=prompt_price,
                pricing_output=completion_price,
                is_free=(prompt_price == 0 and completion_price == 0),
                created=model.get("created", 0),
                # Extended fields
                description=model.get("description", "")[:500],  # Truncate long descriptions
                modality=architecture.get("modality", "text->text"),
                hugging_face_id=model.get("hugging_face_id", ""),
                input_modalities=architecture.get("input_modalities", ["text"]),
                output_modalities=architecture.get("output_modalities", ["text"]),
                tokenizer=architecture.get("tokenizer", ""),
                supported_parameters=model.get("supported_parameters", []),
                is_moderated=top_provider.get("is_moderated", False)
            ))
        
        return EndpointStatus(
            endpoint=endpoint,
            provider="openrouter",
            is_connected=True,
            api_key_valid=True,
            models=models
        )
    
    async def _fetch_anthropic_models(
        self,
        endpoint: str,
        api_key: Optional[str]
    ) -> EndpointStatus:
        """Fetch/validate Anthropic endpoint (no /models endpoint, so we validate with a minimal request)."""
        # Anthropic doesn't have a /models endpoint, return known models
        headers = {
            "x-api-key": api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Try a minimal messages request to validate API key
        test_url = f"{endpoint.rstrip('/')}/messages"
        
        try:
            response = await self.client.post(
                test_url,
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "test"}]
                }
            )
            
            # 401 = bad key, 400 = key valid but request bad (expected), 200 = success
            if response.status_code == 401:
                return EndpointStatus(
                    endpoint=endpoint,
                    provider="anthropic",
                    is_connected=True,
                    api_key_valid=False,
                    models=[],
                    error="Invalid API key"
                )
            
            # Key is valid, return known Anthropic models
            models = [
                ModelInfo(id="claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet", provider="anthropic", context_length=200000, max_output=8192),
                ModelInfo(id="claude-3-5-haiku-20241022", name="Claude 3.5 Haiku", provider="anthropic", context_length=200000, max_output=8192),
                ModelInfo(id="claude-3-opus-20240229", name="Claude 3 Opus", provider="anthropic", context_length=200000, max_output=4096),
                ModelInfo(id="claude-sonnet-4-20250514", name="Claude Sonnet 4", provider="anthropic", context_length=200000, max_output=16384),
                ModelInfo(id="claude-opus-4-20250514", name="Claude Opus 4", provider="anthropic", context_length=200000, max_output=16384),
            ]
            
            return EndpointStatus(
                endpoint=endpoint,
                provider="anthropic",
                is_connected=True,
                api_key_valid=True,
                models=models
            )
            
        except Exception as e:
            return EndpointStatus(
                endpoint=endpoint,
                provider="anthropic",
                is_connected=False,
                api_key_valid=False,
                models=[],
                error=str(e)
            )


async def get_all_endpoint_models() -> Dict[str, EndpointStatus]:
    """
    Fetch models from all configured endpoints.
    
    Returns:
        Dict mapping endpoint names to their status
    """
    from src.core.config import config
    
    fetcher = ProviderModelFetcher()
    results = {}
    
    try:
        # Check each configured endpoint
        endpoints_to_check = []
        
        # Default endpoint
        if config.openai_base_url:
            endpoints_to_check.append(("default", config.openai_base_url, config.openai_api_key))
        
        # Per-model endpoints
        if config.enable_big_endpoint and config.big_endpoint:
            endpoints_to_check.append(("big", config.big_endpoint, config.big_api_key))
        
        if config.enable_middle_endpoint and config.middle_endpoint:
            endpoints_to_check.append(("middle", config.middle_endpoint, config.middle_api_key))
        
        if config.enable_small_endpoint and config.small_endpoint:
            endpoints_to_check.append(("small", config.small_endpoint, config.small_api_key))
        
        # Fetch in parallel
        tasks = []
        for name, endpoint, api_key in endpoints_to_check:
            tasks.append((name, fetcher.fetch_models(endpoint, api_key)))
        
        for name, task in tasks:
            results[name] = await task
        
    finally:
        await fetcher.close()
    
    return results


def get_top_models_per_provider(
    status: EndpointStatus,
    n: int = 5,
    filter_openrouter: bool = True
) -> List[ModelInfo]:
    """
    Get top N models from an endpoint, sorted by popularity/capability.
    
    For OpenRouter: Filters to only top-ranked models (overall + programming leaderboards)
    For other providers: Shows all (smaller lists, no filtering needed)
    
    Sorting priority:
    1. NEW free models (created in last 30 days) - most important!
    2. Other free models
    3. Larger context window
    4. Alphabetically by name
    """
    import time
    models = status.models
    
    # For OpenRouter: Filter to only top-ranked models
    if status.provider == "openrouter" and filter_openrouter:
        try:
            from src.services.models.openrouter_rankings import filter_top_openrouter_models, OpenRouterRankings
            
            # Get model IDs
            model_ids = [m.id for m in models]
            
            # Filter to top models (keeps free models too)
            top_ids = set(filter_top_openrouter_models(
                model_ids,
                include_top_overall=25,
                include_top_programming=20,
                include_top_tool_calls=15
            ))
            
            # If we have rankings data, filter models
            db = OpenRouterRankings()
            if db.get_top_models("overall"):  # Rankings exist
                models = [m for m in models if m.id in top_ids or m.is_free]
        except ImportError:
            pass  # Rankings not available, show all
    
    # Calculate "new" threshold (30 days ago)
    thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
    
    def is_new(model: ModelInfo) -> bool:
        return model.created > thirty_days_ago
    
    # Sort: new free first, then free, then by context length
    sorted_models = sorted(
        models,
        key=lambda m: (
            not (m.is_free and is_new(m)),  # New free models first
            not m.is_free,  # Then other free models
            -m.context_length,  # Larger context first
            m.id  # Alphabetical
        )
    )
    
    return sorted_models[:n]
    """Format a model for display in the selector."""
    def fmt_tokens(n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1000:
            return f"{n/1000:.0f}k"
        return str(n)
    
    # Price formatting
    if model.is_free:
        price_str = "🆓 FREE"
    elif model.pricing_input > 0:
        price_str = f"${model.pricing_input:.2f}/M"
    else:
        price_str = ""
    
    name = model.id
    if len(name) > 40:
        name = name[:37] + "..."
    
    return f"{name:<40} {fmt_tokens(model.context_length):>6} {fmt_tokens(model.max_output):>6}  {price_str}"


# CLI interface for testing
if __name__ == "__main__":
    async def main():
        fetcher = ProviderModelFetcher()
        
        # Test endpoints
        test_endpoints = [
            ("VibeProxy", "http://127.0.0.1:8317/v1", None),
            ("OpenRouter", "https://openrouter.ai/api/v1", os.environ.get("OPENROUTER_API_KEY")),
        ]
        
        for name, endpoint, key in test_endpoints:
            print(f"\n{'='*60}")
            print(f"Testing: {name} ({endpoint})")
            print(f"{'='*60}")
            
            status = await fetcher.fetch_models(endpoint, key)
            
            if status.is_connected:
                print(f"✅ Connected")
                if status.api_key_valid:
                    print(f"✅ API Key Valid")
                    print(f"📊 {len(status.models)} models available")
                    
                    top_5 = get_top_models_per_provider(status, 5)
                    print(f"\nTop 5 models:")
                    for i, model in enumerate(top_5, 1):
                        print(f"  {i}. {format_model_display(model)}")
                else:
                    print(f"❌ API Key Invalid: {status.error}")
            else:
                print(f"❌ Connection failed: {status.error}")
        
        await fetcher.close()
    
    asyncio.run(main())
