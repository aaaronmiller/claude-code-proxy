"""
Data normalizer: merge API model data with optional scraped enrichments.
Implements: normalize_data(), _apply_scrape_data()

Used in: User Story 1, 2, 3
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import ValidationError

from openrouter_model_scout.models import Model, Pricing, Performance, Benchmarks

logger = logging.getLogger(__name__)


def normalize_data(
    api_models: List[Model],
    scraped_data: Dict[str, Dict[str, Any]]
) -> List[Model]:
    """
    Merge API model data with optional scraped enrichments.

    Args:
        api_models: List of Model objects from API (already validated)
        scraped_data: Dict mapping model_id -> scraped enrichment fields
            Expected keys: 'benchmarks' (dict with nested structure),
            'performance' (dict), 'description_short', 'description_full',
            'release_date', 'parameter_size', 'quantization'

    Returns:
        List of Model objects with enriched data where available
    """
    normalized = []

    for model in api_models:
        scrape = scraped_data.get(model.id, {})
        enriched_model = _apply_scrape_data(model, scrape)
        normalized.append(enriched_model)

    return normalized


def _apply_scrape_data(model: Model, scrape: Dict[str, Any]) -> Model:
    """
    Apply scraped data to a model, creating new Model instance with merged fields.

    Args:
        model: Original Model from API
        scrape: Scraped data dict

    Returns:
        New Model with enriched fields (fields from scrape override API if both exist)
    """
    update_data = {}

    # Simple optional text fields
    for field in ['description_short', 'description_full', 'release_date', 'parameter_size', 'quantization']:
        if field in scrape:
            update_data[field] = scrape[field]

    # Performance (nested) - merge or create
    if 'performance' in scrape:
        perf_data = scrape['performance']
        if model.performance is None:
            update_data['performance'] = Performance(**perf_data)
        else:
            # Merge: existing performance gets updated with scraped fields (shallow merge)
            merged = model.performance.dict() | perf_data
            update_data['performance'] = Performance(**merged)

    # Benchmarks (nested) - preserve structure
    if 'benchmarks' in scrape:
        bench_data = scrape['benchmarks']
        # Expect nested structure: {'intelligence': {'score': ..., 'percentile': ...}, 'coding': {...}, ...}
        if model.benchmarks is None:
            update_data['benchmarks'] = Benchmarks(**bench_data)
        else:
            # Merge: shallow merge of nested benchmark objects
            merged = model.benchmarks.dict() | bench_data
            update_data['benchmarks'] = Benchmarks(**merged)

    # Create new model with updates
    model_dict = model.model_dump()
    model_dict.update(update_data)

    return Model(**model_dict)
