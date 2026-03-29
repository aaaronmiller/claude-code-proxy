"""
Leaderboard generation: top-N lists for quick proxy access.
Implements:
  - generate_smartest_leaderboard()
  - generate_coding_leaderboard()
  - generate_free_leaderboard()
  - generate_value_leaderboard()
  - write_leaderboard(), validate_lists()
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from openrouter_model_scout.models import (
    Model,
    Leaderboard,
    SmartestEntry,
    CodingEntry,
    FreeEntry,
    ValueEntry,
)

logger = logging.getLogger(__name__)


def generate_smartest_leaderboard(
    models: List[Model],
    top_n: int = 5,
    generated_at: Optional[str] = None
) -> Leaderboard:
    """
    Generate leaderboard of top N smartest models.

    Sorted by intelligence.score descending.
    Excludes models with missing intelligence score.

    Args:
        models: List of normalized Model objects
        top_n: Number of top entries to include
        generated_at: ISO 8601 timestamp (default: now)

    Returns:
        Leaderboard object with smartest list populated
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    # Filter and sort
    candidates = [
        m for m in models
        if m.benchmarks and m.benchmarks.intelligence_score is not None
    ]
    candidates.sort(key=lambda m: m.benchmarks.intelligence_score, reverse=True)

    top_models = candidates[:top_n]

    smartest_entries = [
        SmartestEntry(
            id=m.id,
            name=m.name,
            intelligence_score=m.benchmarks.intelligence_score,
            percentile=m.benchmarks.intelligence_percentile or 0.0,
            price_per_1m=m.pricing.prompt,
        )
        for m in top_models
    ]

    return Leaderboard(
        generated_at=generated_at,
        smartest=smartest_entries,
        coding=[],
        free=[],
        value=[],
    )


def generate_coding_leaderboard(
    models: List[Model],
    top_n: int = 5,
    generated_at: Optional[str] = None
) -> Leaderboard:
    """Generate leaderboard of top N coding models."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    candidates = [
        m for m in models
        if m.benchmarks and m.benchmarks.coding_score is not None
    ]
    candidates.sort(key=lambda m: m.benchmarks.coding_score, reverse=True)

    top_models = candidates[:top_n]

    coding_entries = [
        CodingEntry(
            id=m.id,
            name=m.name,
            coding_score=m.benchmarks.coding_score,
            agentic_score=m.benchmarks.agentic_score or 0.0,
            price_per_1m=m.pricing.prompt,
        )
        for m in top_models
    ]

    return Leaderboard(
        generated_at=generated_at,
        smartest=[],
        coding=coding_entries,
        free=[],
        value=[],
    )


def generate_free_leaderboard(
    models: List[Model],
    top_n: int = 5,
    generated_at: Optional[str] = None
) -> Leaderboard:
    """Generate leaderboard of top N free models."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    candidates = [m for m in models if m.is_free]
    # Sort by intelligence score (if available), then by context length as tiebreaker
    candidates.sort(
        key=lambda m: (
            m.benchmarks.intelligence_score if m.benchmarks and m.benchmarks.intelligence_score else 0,
            m.context_length
        ),
        reverse=True
    )

    top_models = candidates[:top_n]

    free_entries = [
        FreeEntry(
            id=m.id,
            name=m.name,
            intelligence_score=(m.benchmarks.intelligence_score if m.benchmarks and m.benchmarks.intelligence else 0.0),
            context_length=m.context_length,
            throughput_tps=m.performance.throughput_tps if m.performance else None,
        )
        for m in top_models
    ]

    return Leaderboard(
        generated_at=generated_at,
        smartest=[],
        coding=[],
        free=free_entries,
        value=[],
    )


def generate_value_leaderboard(
    models: List[Model],
    top_n: int = 5,
    generated_at: Optional[str] = None
) -> Leaderboard:
    """
    Generate leaderboard of top N value models (intelligence / prompt cost).

    Excludes free models (they would have infinite ratio).
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()

    candidates = [
        m for m in models
        if not m.is_free and m.benchmarks and m.benchmarks.intelligence_score is not None
    ]

    # Sort by value_score descending
    candidates.sort(key=lambda m: m.value_score, reverse=True)

    top_models = candidates[:top_n]

    value_entries = [
        ValueEntry(
            id=m.id,
            name=m.name,
            value_score=m.value_score,
            price_per_1m=m.pricing.prompt,
            intelligence_percentile=m.benchmarks.intelligence_percentile or 0.0,
        )
        for m in top_models
    ]

    return Leaderboard(
        generated_at=generated_at,
        smartest=[],
        coding=[],
        free=[],
        value=value_entries,
    )


def write_leaderboard(leaderboard: Leaderboard, output_path: str) -> None:
    """
    Write leaderboard to JSON file.

    Args:
        leaderboard: Leaderboard object
        output_path: Destination file path
    """
    # Validate lists have minimum entries (per spec)
    # But don't fail if fewer than top_n - just note in logs
    if len(leaderboard.smartest) < 3:
        logger.warning(f"Smartest leaderboard has only {len(leaderboard.smartest)} entries (<3)")
    if len(leaderboard.coding) < 3:
        logger.warning(f"Coding leaderboard has only {len(leaderboard.coding)} entries (<3)")
    if len(leaderboard.free) < 3:
        logger.warning(f"Free leaderboard has only {len(leaderboard.free)} entries (<3)")
    if len(leaderboard.value) < 3:
        logger.warning(f"Value leaderboard has only {len(leaderboard.value)} entries (<3)")

    # Convert to dict and write
    data = leaderboard.model_dump(mode='json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def validate_lists(leaderboard: Leaderboard) -> None:
    """
    Validate leaderboard lists meet requirements.

    Args:
        leaderboard: Leaderboard to validate

    Raises:
        ValueError: If validation fails
    """
    # Check no duplicate IDs within each list
    for list_name in ['smartest', 'coding', 'free', 'value']:
        entries = getattr(leaderboard, list_name)
        ids = [e.id for e in entries]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate entries in {list_name} leaderboard")


def write_leaderboard_csv(leaderboard: Leaderboard, output_path: str) -> None:
    """
    Write leaderboard to CSV file(s).
    
    Creates separate CSV files for each leaderboard list:
    - leaderboard_smartest.csv
    - leaderboard_coding.csv
    - leaderboard_free.csv
    - leaderboard_value.csv
    
    Args:
        leaderboard: Leaderboard object
        output_path: Base path (will append list name before extension)
    """
    import csv
    from pathlib import Path
    
    base = Path(output_path)
    stem = base.stem
    parent = base.parent
    
    # Define columns for each leaderboard type
    smartest_fields = ['id', 'name', 'intelligence_score', 'percentile', 'price_per_1m']
    coding_fields = ['id', 'name', 'coding_score', 'agentic_score', 'price_per_1m']
    free_fields = ['id', 'name', 'intelligence_score', 'context_length', 'throughput_tps']
    value_fields = ['id', 'name', 'value_score', 'price_per_1m', 'intelligence_percentile']
    
    def write_csv(entries, fields, suffix):
        if not entries:
            logger.warning(f"No entries for {suffix}, skipping CSV")
            return
        
        csv_path = parent / f"{stem}_{suffix}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for entry in entries:
                row = {field: getattr(entry, field, None) for field in fields}
                writer.writerow(row)
        logger.info(f"Wrote {len(entries)} rows to {csv_path}")
    
    write_csv(leaderboard.smartest, smartest_fields, 'smartest')
    write_csv(leaderboard.coding, coding_fields, 'coding')
    write_csv(leaderboard.free, free_fields, 'free')
    write_csv(leaderboard.value, value_fields, 'value')
