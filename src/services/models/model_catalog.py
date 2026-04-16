"""
Model Catalog Service

Integrates model-scraper output with main proxy to provide:
- Curated model lists (free, smartest, coding, value)
- Recently used models from selection history
- Model specifications (context length, throughput, pricing)
- Daily usage tracking for cascade fallback

Usage:
    from src.services.models.model_catalog import model_catalog

    # Get curated lists
    free_models = model_catalog.get_models("free", limit=5)
    smartest = model_catalog.get_models("smartest", limit=5)

    # Get model specs
    specs = model_catalog.get_model_spec("openai/gpt-4o")

    # Get recent models
    recent = model_catalog.get_recent_models(limit=5)
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.services.models.selection_history import get_recent_models

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
CATALOG_PATH = MODELS_DIR / "model_catalog.json"
USAGE_PATH = MODELS_DIR / "daily_usage.json"

DEFAULT_CATEGORIES = ["free", "smartest", "coding", "value"]


@dataclass
class ModelSpec:
    """Specification for a model."""

    id: str
    name: str
    provider: str
    context_length: int
    max_output: int
    price_per_1m_input: float = 0.0
    price_per_1m_output: float = 0.0
    throughput_tps: Optional[float] = None
    intelligence_score: Optional[float] = None
    is_free: bool = False
    category: Optional[str] = None


@dataclass
class ModelCatalog:
    """Model catalog with curated lists."""

    generated_at: str
    models: Dict[str, List[Dict]]  # category -> list of model dicts
    all_models: Dict[str, ModelSpec]  # model_id -> ModelSpec

    @classmethod
    def from_dict(cls, data: dict) -> "ModelCatalog":
        """Create from dictionary."""
        # Convert model dicts to ModelSpec
        all_models = {}
        for model_list in data.get("models", {}).values():
            for m in model_list:
                spec = ModelSpec(
                    id=m.get("id", ""),
                    name=m.get("name", m.get("id", "")),
                    provider=m.get("id", "").split("/")[0]
                    if "/" in m.get("id", "")
                    else "unknown",
                    context_length=m.get("context_length", 128000),
                    max_output=m.get("max_output", 4096),
                    price_per_1m_input=m.get("price_per_1m_input", 0.0),
                    price_per_1m_output=m.get("price_per_1m_output", 0.0),
                    throughput_tps=m.get("throughput_tps"),
                    intelligence_score=m.get("intelligence_score"),
                    is_free=m.get("is_free", ":free" in m.get("id", "").lower()),
                    category=m.get("category"),
                )
                all_models[spec.id] = spec

        return cls(
            generated_at=data.get("generated_at", ""),
            models=data.get("models", {}),
            all_models=all_models,
        )


class ModelCatalogService:
    """Service for managing model catalog."""

    def __init__(self):
        self._catalog: Optional[ModelCatalog] = None
        self._daily_usage: Dict[
            str, Dict[str, int]
        ] = {}  # date -> {model_id: request_count}
        self._load()

    def _load(self):
        """Load catalog and usage data."""
        # Load catalog
        if CATALOG_PATH.exists():
            try:
                data = json.loads(CATALOG_PATH.read_text())
                self._catalog = ModelCatalog.from_dict(data)
                logger.info(f"Loaded model catalog from {CATALOG_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load catalog: {e}")
                self._catalog = None

        # Load daily usage
        if USAGE_PATH.exists():
            try:
                self._daily_usage = json.loads(USAGE_PATH.read_text())
            except Exception as e:
                logger.warning(f"Failed to load daily usage: {e}")
                self._daily_usage = {}

    def _save(self):
        """Save catalog and usage data."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        # Save catalog if present
        if self._catalog:
            data = {
                "generated_at": self._catalog.generated_at,
                "models": self._catalog.models,
                "all_models": {
                    k: asdict(v) for k, v in self._catalog.all_models.items()
                },
            }
            CATALOG_PATH.write_text(json.dumps(data, indent=2))

        # Save daily usage
        USAGE_PATH.write_text(json.dumps(self._daily_usage, indent=2))

    def reload(self):
        """Reload catalog from disk."""
        self._load()

    def get_models(self, category: str, limit: int = 5) -> List[ModelSpec]:
        """Get models from a specific category."""
        if not self._catalog:
            return self._get_default_models(category, limit)

        models = self._catalog.models.get(category, [])
        result = []
        for m in models[:limit]:
            model_id = m.get("id", "")
            if model_id in self._catalog.all_models:
                result.append(self._catalog.all_models[model_id])
            else:
                # Create on-the-fly
                result.append(
                    ModelSpec(
                        id=model_id,
                        name=m.get("name", model_id),
                        provider=model_id.split("/")[0]
                        if "/" in model_id
                        else "unknown",
                        context_length=m.get("context_length", 128000),
                        max_output=m.get("max_output", 4096),
                        is_free=":free" in model_id.lower(),
                    )
                )
        return result

    def get_all_curated(
        self, limit_per_category: int = 5
    ) -> Dict[str, List[ModelSpec]]:
        """Get all curated models organized by category."""
        return {
            category: self.get_models(category, limit_per_category)
            for category in DEFAULT_CATEGORIES
        }

    def get_recent_models(self, limit: int = 5) -> List[ModelSpec]:
        """Get recently used models from selection history."""
        recent_ids = get_recent_models(limit=limit)

        if not self._catalog:
            return [
                ModelSpec(
                    id=mid,
                    name=mid,
                    provider=mid.split("/")[0] if "/" in mid else "unknown",
                )
                for mid in recent_ids
            ]

        result = []
        for mid in recent_ids:
            if mid in self._catalog.all_models:
                result.append(self._catalog.all_models[mid])
            else:
                result.append(
                    ModelSpec(
                        id=mid,
                        name=mid,
                        provider=mid.split("/")[0] if "/" in mid else "unknown",
                    )
                )
        return result

    def get_model_spec(self, model_id: str) -> Optional[ModelSpec]:
        """Get specifications for a specific model."""
        if not self._catalog:
            return ModelSpec(
                id=model_id,
                name=model_id,
                provider=model_id.split("/")[0] if "/" in model_id else "unknown",
                context_length=128000,
                max_output=4096,
            )

        return self._catalog.all_models.get(model_id)

    def get_all_models(self) -> List[ModelSpec]:
        """Get all available models."""
        if not self._catalog:
            return []
        return list(self._catalog.all_models.values())

    def search_models(self, query: str, limit: int = 20) -> List[ModelSpec]:
        """Search models by name or ID."""
        if not self._catalog:
            return []

        query_lower = query.lower()
        results = []

        for spec in self._catalog.all_models.values():
            if query_lower in spec.id.lower() or query_lower in spec.name.lower():
                results.append(spec)
            if len(results) >= limit:
                break

        return results

    def _get_default_models(self, category: str, limit: int) -> List[ModelSpec]:
        """Get default models when catalog is not available."""
        defaults = {
            "free": [
                # Best free models with tool calling (verified via API + benchmarks - March 2026)
                # MiniMax M2.5: BEST benchmarks - Intelligence 41.9, Coding 37.4, Agentic 55.6
                "minimax/minimax-m2.5:free",  # 197K ctx - BEST (better than 91%!)
                "nvidia/nemotron-3-super-120b-a12b:free",  # 1M ctx - best context, good benchmarks
                "nvidia/nemotron-nano-9b-v2:free",  # 128K ctx - fast background model
                "qwen/qwen3-next-80b-a3b-instruct:free",  # 262K ctx
                "openrouter/free",  # Router (unpredictable)
            ],
            "smartest": [
                "anthropic/claude-3.5-sonnet-20241022",
                "openai/gpt-4o",
                "google/gemini-2.5-pro-preview-05-20",
                "anthropic/claude-3-opus-20240229",
                "meta-llama/llama-3.3-70b-instruct",
            ],
            "coding": [
                "anthropic/claude-3.5-sonnet-20241022",
                "deepseek/deepseek-coder",
                "openai/gpt-4o",
                "qwen/qwen-2.5-coder-32b-instruct",
                "openai/o1-mini",
            ],
            "value": [
                "openai/gpt-4o-mini",
                "anthropic/claude-3.5-haiku-20240307",
                "google/gemini-2.0-flash-exp:free",
                "mistralai/mistral-small",
                "cohere/command-r-plus",
            ],
        }

        model_ids = defaults.get(category, defaults["smartest"])[:limit]
        return [
            ModelSpec(
                id=mid,
                name=mid,
                provider=mid.split("/")[0] if "/" in mid else "unknown",
                context_length=128000,
                max_output=4096,
                is_free=":free" in mid.lower(),
            )
            for mid in model_ids
        ]

    # === Daily Usage Tracking for Cascade ===

    def _get_today_key(self) -> str:
        """Get today's date key."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def record_request(self, model_id: str):
        """Record a request to a model for today."""
        today = self._get_today_key()

        if today not in self._daily_usage:
            self._daily_usage = {
                k: v for k, v in self._daily_usage.items() if k >= self._get_week_ago()
            }
            self._daily_usage[today] = {}

        self._daily_usage[today][model_id] = (
            self._daily_usage[today].get(model_id, 0) + 1
        )
        self._save()

    def get_daily_usage(self, model_id: str) -> int:
        """Get today's request count for a model."""
        today = self._get_today_key()
        return self._daily_usage.get(today, {}).get(model_id, 0)

    def is_at_limit(self, model_id: str, limit: int = 1000) -> bool:
        """Check if model has hit daily limit."""
        return self.get_daily_usage(model_id) >= limit

    def get_cascade_next(
        self, model_id: str, cascade_list: List[str], limit: int = 1000
    ) -> Optional[str]:
        """
        Get the next model in cascade if current is at limit.

        Args:
            model_id: Current model ID
            cascade_list: List of models to cascade through (in order of preference)
            limit: Daily limit threshold

        Returns:
            Next model ID if current is at limit, None otherwise
        """
        if model_id not in cascade_list:
            return cascade_list[0] if cascade_list else None

        current_idx = cascade_list.index(model_id)

        for i, candidate in enumerate(cascade_list[current_idx:], start=current_idx):
            if i == current_idx:
                continue  # Skip current
            if not self.is_at_limit(candidate, limit):
                return candidate

        return None  # All models at limit

    def _get_week_ago(self) -> str:
        """Get date key for 7 days ago."""
        from datetime import timedelta

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        return week_ago.strftime("%Y-%m-%d")

    def get_usage_stats(self, days: int = 7) -> Dict[str, int]:
        """Get usage stats for the last N days."""
        stats = {}
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
            "%Y-%m-%d"
        )

        for day, models in self._daily_usage.items():
            if day >= cutoff:
                for model_id, count in models.items():
                    stats[model_id] = stats.get(model_id, 0) + count

        return stats

    def get_all_lists(self) -> Dict[str, List[ModelSpec]]:
        """Get all curated lists plus recent models for UI display."""
        result = self.get_all_curated(limit=5)
        result["recent"] = self.get_recent_models(limit=5)
        return result


# Singleton instance
model_catalog = ModelCatalogService()
