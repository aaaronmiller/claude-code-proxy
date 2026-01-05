#!/usr/bin/env python3
"""
OpenRouter Model Fetcher with Auto-Refresh

Fetches models from OpenRouter API on startup (with caching) and provides
model data for TUI and WebUI model selectors.

Features:
- Auto-refresh on startup if cache is stale
- Configurable cache TTL (default 24 hours)
- Fallback to cached data on network failure
- JSON and CSV storage formats
- Rich model metadata extraction
"""

import asyncio
import csv
import httpx
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

from .openrouter_enricher import enrich_model

logger = logging.getLogger(__name__)

# Default cache TTL in hours
DEFAULT_CACHE_TTL_HOURS = 24

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"


def get_data_dir() -> Path:
    """Get the data directory for storing model files."""
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cache_paths() -> Tuple[Path, Path]:
    """Get paths for JSON and CSV cache files."""
    data_dir = get_data_dir()
    return (
        data_dir / "openrouter_models.json",
        data_dir / "openrouter_models.csv"
    )


def is_cache_stale(cache_path: Path, ttl_hours: int = DEFAULT_CACHE_TTL_HOURS) -> bool:
    """Check if cache file is stale (older than TTL)."""
    if not cache_path.exists():
        return True

    try:
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age > timedelta(hours=ttl_hours)
    except Exception:
        return True


def load_cached_models() -> Optional[Dict[str, Any]]:
    """Load models from cache file."""
    json_path, _ = get_cache_paths()

    if not json_path.exists():
        return None

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load cached models: {e}")
        return None


def save_models_json(data: Dict[str, Any], path: Path):
    """Save models to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data.get('models', []))} models to {path}")


def save_models_csv(models: List[Dict[str, Any]], path: Path):
    """Save models to CSV file for easy import into spreadsheets."""
    if not models:
        return

    # Define CSV columns (flattened structure)
    fieldnames = [
        'id', 'name', 'provider', 'description',
        'context_length', 'max_completion_tokens',
        'input_price_per_million', 'output_price_per_million', 'is_free',
        'supports_reasoning', 'supports_tools', 'supports_vision',
        'supports_audio', 'supports_files',
        'modality', 'input_modalities', 'output_modalities',
        'tokenizer', 'is_moderated', 'created'
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for model in models:
            row = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'provider': model.get('provider', ''),
                'description': model.get('description', '')[:200],  # Truncate
                'context_length': model.get('context_length', 0),
                'max_completion_tokens': model.get('max_completion_tokens', 0),
                'input_price_per_million': model.get('pricing', {}).get('input_per_million', 0),
                'output_price_per_million': model.get('pricing', {}).get('output_per_million', 0),
                'is_free': model.get('pricing', {}).get('is_free', False),
                'supports_reasoning': model.get('supports_reasoning', False),
                'supports_tools': model.get('supports_tools', False),
                'supports_vision': model.get('supports_vision', False),
                'supports_audio': model.get('supports_audio', False),
                'supports_files': model.get('supports_files', False),
                'modality': model.get('modality', ''),
                'input_modalities': ','.join(model.get('input_modalities', [])),
                'output_modalities': ','.join(model.get('output_modalities', [])),
                'tokenizer': model.get('tokenizer', ''),
                'is_moderated': model.get('is_moderated', False),
                'created': model.get('created', 0),
            }
            writer.writerow(row)

    logger.info(f"Saved {len(models)} models to {path}")


async def fetch_openrouter_models(
    api_key: Optional[str] = None,
    timeout: float = 30.0
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetch models from OpenRouter API.

    Args:
        api_key: Optional OpenRouter API key (allows viewing more models)
        timeout: Request timeout in seconds

    Returns:
        Tuple of (models list, error message or None)
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(OPENROUTER_API_URL, headers=headers)

            if response.status_code != 200:
                return [], f"HTTP {response.status_code}: {response.text[:100]}"

            data = response.json()
            models = data.get('data', [])

            if not models:
                return [], "No models returned from API"

            return models, None

    except httpx.TimeoutException:
        return [], "Request timed out"
    except httpx.ConnectError as e:
        return [], f"Connection failed: {str(e)}"
    except Exception as e:
        return [], f"Error: {str(e)}"


def enrich_and_process_models(raw_models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enrich raw models and compute statistics.

    Returns:
        Dict with models list and stats
    """
    enriched = []
    stats = {
        "total": len(raw_models),
        "free": 0,
        "reasoning": 0,
        "vision": 0,
        "tools": 0,
        "by_provider": {}
    }

    for model in raw_models:
        enriched_model = enrich_model(model)
        enriched.append(enriched_model)

        # Update stats
        provider = enriched_model['provider']
        stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1

        if enriched_model['pricing']['is_free']:
            stats['free'] += 1
        if enriched_model['supports_reasoning']:
            stats['reasoning'] += 1
        if enriched_model['supports_vision']:
            stats['vision'] += 1
        if enriched_model['supports_tools']:
            stats['tools'] += 1

    # Sort by provider, then by name
    enriched.sort(key=lambda m: (m['provider'], m['name']))

    return {
        "fetched_at": datetime.now().isoformat(),
        "source": OPENROUTER_API_URL,
        "stats": stats,
        "models": enriched
    }


async def refresh_openrouter_models(
    force: bool = False,
    ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Refresh OpenRouter models, using cache if valid.

    Args:
        force: Force refresh even if cache is valid
        ttl_hours: Cache TTL in hours

    Returns:
        Tuple of (models data, was_refreshed, error message or None)
    """
    json_path, csv_path = get_cache_paths()

    # Check if refresh is needed
    if not force and not is_cache_stale(json_path, ttl_hours):
        cached = load_cached_models()
        if cached:
            logger.info(f"Using cached models ({len(cached.get('models', []))} models)")
            return cached, False, None

    # Get API key from environment
    api_key = os.environ.get("OPENROUTER_API_KEY")

    logger.info("Fetching models from OpenRouter API...")
    raw_models, error = await fetch_openrouter_models(api_key)

    if error:
        # Try to use cached data as fallback
        cached = load_cached_models()
        if cached:
            logger.warning(f"API fetch failed ({error}), using cached data")
            return cached, False, error
        return {"models": [], "stats": {}}, False, error

    # Enrich and process models
    data = enrich_and_process_models(raw_models)

    # Save to JSON and CSV
    save_models_json(data, json_path)
    save_models_csv(data['models'], csv_path)

    logger.info(f"Refreshed {len(data['models'])} models from OpenRouter")
    return data, True, None


def refresh_openrouter_models_sync(
    force: bool = False,
    ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Synchronous wrapper for refresh_openrouter_models.

    For use in non-async contexts (startup, CLI).
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(refresh_openrouter_models(force, ttl_hours))


def get_models() -> List[Dict[str, Any]]:
    """
    Get cached models list.

    Returns empty list if no cache available.
    """
    cached = load_cached_models()
    if cached:
        return cached.get('models', [])
    return []


def get_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific model by ID."""
    models = get_models()
    for model in models:
        if model.get('id') == model_id:
            return model
    return None


def filter_models(
    provider: Optional[str] = None,
    supports_reasoning: Optional[bool] = None,
    supports_vision: Optional[bool] = None,
    supports_tools: Optional[bool] = None,
    is_free: Optional[bool] = None,
    min_context: Optional[int] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter models by various criteria.

    Args:
        provider: Filter by provider name
        supports_reasoning: Filter by reasoning support
        supports_vision: Filter by vision support
        supports_tools: Filter by tool use support
        is_free: Filter by free pricing
        min_context: Minimum context length
        search: Search in model ID and name

    Returns:
        Filtered list of models
    """
    models = get_models()
    result = []

    for model in models:
        # Provider filter
        if provider and model.get('provider', '').lower() != provider.lower():
            continue

        # Capability filters
        if supports_reasoning is not None and model.get('supports_reasoning') != supports_reasoning:
            continue
        if supports_vision is not None and model.get('supports_vision') != supports_vision:
            continue
        if supports_tools is not None and model.get('supports_tools') != supports_tools:
            continue

        # Pricing filter
        if is_free is not None and model.get('pricing', {}).get('is_free') != is_free:
            continue

        # Context filter
        if min_context and model.get('context_length', 0) < min_context:
            continue

        # Search filter
        if search:
            search_lower = search.lower()
            model_id = model.get('id', '').lower()
            model_name = model.get('name', '').lower()
            if search_lower not in model_id and search_lower not in model_name:
                continue

        result.append(model)

    return result


def get_model_stats() -> Dict[str, Any]:
    """Get statistics about cached models."""
    cached = load_cached_models()
    if cached:
        return cached.get('stats', {})
    return {}


# Auto-refresh on import (if configured)
def startup_refresh():
    """
    Called on proxy startup to refresh models if needed.

    Respects OPENROUTER_AUTO_REFRESH env var (default: true).
    """
    auto_refresh = os.environ.get("OPENROUTER_AUTO_REFRESH", "true").lower() == "true"
    if not auto_refresh:
        logger.info("OpenRouter auto-refresh disabled")
        return

    ttl_hours = int(os.environ.get("OPENROUTER_CACHE_TTL_HOURS", str(DEFAULT_CACHE_TTL_HOURS)))

    try:
        data, was_refreshed, error = refresh_openrouter_models_sync(force=False, ttl_hours=ttl_hours)
        if was_refreshed:
            print(f"✅ Refreshed {len(data.get('models', []))} models from OpenRouter")
        elif error:
            print(f"⚠️  OpenRouter refresh failed: {error}")
            if data.get('models'):
                print(f"   Using cached data ({len(data['models'])} models)")
        else:
            print(f"📦 Using cached OpenRouter models ({len(data.get('models', []))} models)")
    except Exception as e:
        logger.error(f"OpenRouter startup refresh failed: {e}")
        print(f"⚠️  OpenRouter model fetch failed: {e}")
