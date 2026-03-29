"""
Fast API fetcher for OpenRouter models endpoint.
Implements: fetch_models(), parse_response(), retry logic
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from pydantic import ValidationError

from openrouter_model_scout.config import Config
from openrouter_model_scout.exceptions import APIError
from openrouter_model_scout.models import Model
from openrouter_model_scout.logger import setup_logger

logger = logging.getLogger(__name__)


async def fetch_models(
    config: Config,
    client: Optional[httpx.AsyncClient] = None
) -> List[Model]:
    """
    Fetch model list from OpenRouter API.

    Args:
        config: Configuration object with API key
        client: Optional httpx client (for testing/mocking)

    Returns:
        List of Model objects

    Raises:
        APIError: If API request fails after retries
    """
    endpoint = "https://openrouter.ai/api/v1/models"
    headers = {
        "Authorization": f"Bearer {config.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=30.0)

    try:
        for attempt in range(config.scraper_max_retries):
            try:
                logger.info(f"Fetching models from OpenRouter API (attempt {attempt + 1})")
                response = await client.get(endpoint, headers=headers)

                if response.status_code != 200:
                    raise APIError(
                        f"API returned status {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                    )

                data = response.json()
                # API returns {"data": [...]} - extract the list
                models_list = data.get('data', data) if isinstance(data, dict) else data

                # Defensive filtering: remove entries with missing/invalid required pricing
                filtered_models = []
                for item in models_list:
                    pricing = item.get('pricing')
                    if not isinstance(pricing, dict):
                        logger.warning(f"Skipping model {item.get('id')}: pricing field missing or not a dict")
                        continue
                    if pricing.get('prompt') is None or pricing.get('completion') is None:
                        logger.warning(f"Skipping model {item.get('id')}: missing required pricing fields (prompt/completion)")
                        continue
                    filtered_models.append(item)

                # Parse with strict contract validation
                try:
                    models = parse_response(filtered_models)
                except ValidationError as batch_err:
                    # Batch validation failed - salvage individually
                    logger.error(f"Batch validation failed: {batch_err}. Attempting individual model parsing...")
                    models = []
                    for item in filtered_models:
                        try:
                            cleaned = _clean_model_dict(item)
                            model = Model(**cleaned)
                            models.append(model)
                        except ValidationError as ve:
                            logger.warning(f"Skipping invalid model {item.get('id')}: {ve}")
                            continue

                # Apply model filter if specified (T051)
                if config.model_filter:
                    import re
                    pattern = re.compile(config.model_filter)
                    filtered = [m for m in models if pattern.search(m.id)]
                    logger.info(f"Filtered models with pattern '{config.model_filter}': {len(filtered)} of {len(models)} remain")
                    models = filtered

                logger.info(f"Successfully fetched {len(models)} models")
                return models

            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt < config.scraper_max_retries - 1:
                    wait = 2 ** attempt  # exponential backoff
                    logger.warning(f"API request failed, retrying in {wait}s: {e}")
                    await asyncio.sleep(wait)
                    continue
                raise APIError(f"API request failed after {config.scraper_max_retries} retries: {e}")

    finally:
        if own_client:
            await client.aclose()


def parse_response(api_data: List[Dict[str, Any]]) -> List[Model]:
    """
    Parse OpenRouter API response into Model objects.

    Args:
        api_data: List of model dictionaries from API

    Returns:
        List of validated Model instances

    Raises:
        ValidationError: If any model fails validation (strict contract)
    """
    models = []
    for item in api_data:
        # Clean/coerce fields that come as strings from API
        cleaned = _clean_model_dict(item)
        # Let ValidationError propagate (strict schema enforcement)
        model = Model(**cleaned)
        models.append(model)

    return models

def _clean_model_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and coerce API data to match Model expectations.
    """
    cleaned = item.copy()
    
    # Convert numeric strings to float/int
    def coerce_numeric(value, target_type=float):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                # Handle "-1" which means not available
                val = float(value) if '.' in value else int(value)
                return val
            except ValueError:
                return value
        return value
    
    # Clean pricing fields
    if 'pricing' in cleaned and isinstance(cleaned['pricing'], dict):
        pricing = cleaned['pricing'].copy()
        for key in ['prompt', 'completion', 'cache_read', 'cache_write', 'cache_creation', 'web_search']:
            if key in pricing:
                pricing[key] = coerce_numeric(pricing[key])
                # Treat -1 as None (unavailable)
                if pricing[key] == -1:
                    pricing[key] = None
        cleaned['pricing'] = pricing
    
    # Clean other numeric fields
    for field in ['context_length', 'max_output_tokens', 'created']:
        if field in cleaned:
            cleaned[field] = coerce_numeric(cleaned[field])
    
    return cleaned
