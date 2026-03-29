import json
import hashlib
from typing import List, Any, Dict, Set


def calculate_checksum(models: List[Any]) -> str:
    """
    Calculate SHA256 checksum for model data.

    Args:
        models: List of model objects or dictionaries

    Returns:
        Hexadecimal SHA256 hash string (64 chars)
    """
    # Serialize to canonical JSON for consistent hashing
    content = json.dumps(
        [m.model_dump() if hasattr(m, "model_dump") else m for m in models],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def detect_pricing_delta(
    previous_pricing: Dict[str, Dict[str, float]],
    current_pricing: Dict[str, Dict[str, float]],
    threshold: float = 0.1,
) -> List[str]:
    """
    Detect models with significant pricing changes.

    Args:
        previous_pricing: Previous pricing data
        current_pricing: Current pricing data
        threshold: Price change threshold (0-1)

    Returns:
        List of model IDs with pricing changes above threshold
    """
    changed_models = []

    for model_id, current in current_pricing.items():
        previous = previous_pricing.get(model_id)

        if not previous:
            continue

        for key in ["prompt", "completion"]:
            if current.get(key) is None or previous.get(key) is None:
                continue

            old_price = previous[key]
            new_price = current[key]

            if old_price == 0:
                continue

            change = abs(new_price - old_price) / old_price

            if change >= threshold:
                changed_models.append(model_id)
                break

    return changed_models


def queue_new_models(current_ids: Set[str], previous_ids: Set[str]) -> List[str]:
    """
    Identify new models that need scraping.

    Args:
        current_ids: Set of current model IDs
        previous_ids: Set of previous model IDs

    Returns:
        List of new model IDs
    """
    return list(current_ids - previous_ids)
