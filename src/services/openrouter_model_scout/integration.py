"""
Model Scout Integration

Integrates the model-scraper with the proxy to:
- Run model-scraper to fetch/update OpenRouter models
- Convert scraper output to proxy's model catalog format
- Expose APIs for curated model lists

Usage:
    from src.services.openrouter_model_scout.integration import ModelScoutIntegration

    scout = ModelScoutIntegration()

    # Run a sync
    await scout.run_sync()

    # Get curated models
    free_models = scout.get_free_models()
    smartest = scout.get_smartest_models()
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Paths
SCOUT_DIR = Path(__file__).parent  # openrouter_model_scout directory
REPO_ROOT = Path(
    __file__
).parent.parent.parent.parent  # repo root (src/services/openrouter_model_scout -> .)
SCOUT_DATA_DIR = REPO_ROOT / "models" / "scout"
SCOUT_MODELS_PATH = SCOUT_DATA_DIR / "models.json"
SCOUT_LEADERBOARD_PATH = SCOUT_DATA_DIR / "leaderboard.json"
SCOUT_META_PATH = SCOUT_DATA_DIR / "meta.json"

# Proxy's model catalog path
PROXY_MODELS_DIR = REPO_ROOT / "models"
PROXY_CATALOG_PATH = PROXY_MODELS_DIR / "model_catalog.json"


class ModelScoutIntegration:
    """Integration layer between model-scraper and proxy."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or SCOUT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load cached data
        self._leaderboard: Optional[Dict] = None
        self._models: Optional[List[Dict]] = None
        self._last_sync: Optional[datetime] = None

        self._load()

    def _load(self):
        """Load cached data from disk."""
        # Load leaderboard
        if SCOUT_LEADERBOARD_PATH.exists():
            try:
                self._leaderboard = json.loads(SCOUT_LEADERBOARD_PATH.read_text())
                logger.info(f"Loaded leaderboard from {SCOUT_LEADERBOARD_PATH}")
            except Exception as e:
                logger.warning(f"Failed to load leaderboard: {e}")
                self._leaderboard = None

        # Load models
        if SCOUT_MODELS_PATH.exists():
            try:
                self._models = json.loads(SCOUT_MODELS_PATH.read_text())
                logger.info(f"Loaded {len(self._models)} models from cache")
            except Exception as e:
                logger.warning(f"Failed to load models: {e}")
                self._models = None

        # Load meta for last sync time
        if SCOUT_META_PATH.exists():
            try:
                meta = json.loads(SCOUT_META_PATH.read_text())
                # meta.json has "last_run" as ISO string directly
                last_run = meta.get("last_run")
                if last_run and isinstance(last_run, str):
                    self._last_sync = datetime.fromisoformat(
                        last_run.replace("Z", "+00:00")
                    )
            except Exception as e:
                logger.warning(f"Failed to load meta: {e}")

    def _save_leaderboard(self, data: Dict):
        """Save leaderboard data."""
        SCOUT_LEADERBOARD_PATH.write_text(json.dumps(data, indent=2))
        self._leaderboard = data

    def _save_models(self, models: List[Dict]):
        """Save models data."""
        SCOUT_MODELS_PATH.write_text(json.dumps(models, indent=2))
        self._models = models

    def is_sync_needed(self, max_age_hours: int = 24) -> bool:
        """Check if a new sync is needed."""
        if not self._last_sync:
            return True

        now = datetime.now(timezone.utc)
        age = (now - self._last_sync).total_seconds()
        return age > (max_age_hours * 3600)

    async def run_sync(self, force: bool = False) -> Dict[str, Any]:
        """
        Run model-scraper sync.

        Args:
            force: Force sync even if not needed

        Returns:
            Dict with sync results
        """
        if not force and not self.is_sync_needed():
            logger.info("Model sync not needed (recently synced)")
            return {"status": "skipped", "reason": "recently_synced"}

        # Get OpenRouter API key
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            # Try to get from proxy config
            from src.core.config import Config

            config = Config()
            api_key = config.provider_api_key or os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            return {"status": "error", "error": "No OPENROUTER_API_KEY available"}

        logger.info("Starting model-scraper sync...")

        try:
            # Run the model-scraper
            result = await self._run_scout(api_key, force=force)

            if result["returncode"] == 0:
                # Reload data
                self._load()

                # Convert to proxy catalog format
                self._convert_to_proxy_catalog()

                return {
                    "status": "success",
                    "models_count": len(self._models) if self._models else 0,
                    "leaderboard": list(self._leaderboard.keys())
                    if self._leaderboard
                    else [],
                }
            else:
                logger.error(f"Model-scraper failed: {result.get('stderr', '')}")
                return {
                    "status": "error",
                    "error": result.get("stderr", "Unknown error"),
                }

        except Exception as e:
            logger.exception("Model sync failed")
            return {"status": "error", "error": str(e)}

    async def _run_scout(self, api_key: str, force: bool = True) -> Dict[str, Any]:
        """Run the model-scraper CLI."""
        env = os.environ.copy()
        env["OPENROUTER_API_KEY"] = api_key
        env["DATA_DIR"] = str(self.data_dir)
        env["LOG_LEVEL"] = "INFO"

        # Add module to PYTHONPATH so it can be imported
        # Need to add parent of openrouter_model_scout (i.e., services/)
        python_path = str(SCOUT_DIR.parent)
        env["PYTHONPATH"] = python_path + ":" + env.get("PYTHONPATH", "")

        # Build command
        scout_cmd = [
            "python",
            "-m",
            "openrouter_model_scout.main",
            "--fast-only",  # Just API sync, skip web scraping
        ]

        if force:
            scout_cmd.append("--force")

        # Change to scout directory
        result = subprocess.run(
            scout_cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=str(SCOUT_DIR),
            timeout=300,  # 5 min timeout
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def _convert_to_proxy_catalog(self):
        """Convert model-scraper output to proxy's catalog format."""
        if not self._leaderboard:
            logger.warning("No leaderboard data to convert")
            return

        # Build catalog in proxy's format
        catalog = {
            "generated_at": self._leaderboard.get(
                "generated_at", datetime.now(timezone.utc).isoformat()
            ),
            "models": {},
            "all_models": {},
        }

        # Copy leaderboard categories
        for category in ["smartest", "coding", "free", "value"]:
            if category in self._leaderboard:
                models = self._leaderboard[category]
                catalog["models"][category] = [
                    {
                        "id": m.get("id", ""),
                        "name": m.get("name", m.get("id", "")),
                        "context_length": m.get("context_length", 128000),
                        "max_output": m.get("max_output", 4096),
                        "intelligence_score": m.get("intelligence_score"),
                        "throughput_tps": m.get("throughput_tps"),
                        "price_per_1m_input": m.get("price_per_1m_input", 0),
                        "price_per_1m_output": m.get("price_per_1m_output", 0),
                        "is_free": ":free" in m.get("id", "").lower(),
                    }
                    for m in models
                ]

                # Also add to all_models
                for m in models:
                    model_id = m.get("id", "")
                    if model_id:
                        catalog["all_models"][model_id] = m

        # Save proxy catalog
        PROXY_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        PROXY_CATALOG_PATH.write_text(json.dumps(catalog, indent=2))
        logger.info(f"Saved proxy model catalog to {PROXY_CATALOG_PATH}")

    # === Public API ===

    def get_free_models(self, limit: int = 10) -> List[Dict]:
        """Get free models from leaderboard."""
        if not self._leaderboard:
            return []
        return self._leaderboard.get("free", [])[:limit]

    def get_smartest_models(self, limit: int = 10) -> List[Dict]:
        """Get smartest models from leaderboard."""
        if not self._leaderboard:
            return []
        return self._leaderboard.get("smartest", [])[:limit]

    def get_coding_models(self, limit: int = 10) -> List[Dict]:
        """Get coding models from leaderboard."""
        if not self._leaderboard:
            return []
        return self._leaderboard.get("coding", [])[:limit]

    def get_value_models(self, limit: int = 10) -> List[Dict]:
        """Get value models from leaderboard."""
        if not self._leaderboard:
            return []
        return self._leaderboard.get("value", [])[:limit]

    def get_all_models(self) -> List[Dict]:
        """Get all models."""
        return self._models or []

    def get_model_by_id(self, model_id: str) -> Optional[Dict]:
        """Get a specific model by ID."""
        if not self._models:
            return None
        return next((m for m in self._models if m.get("id") == model_id), None)

    def search_models(self, query: str, limit: int = 20) -> List[Dict]:
        """Search models by name."""
        if not self._models:
            return []

        query_lower = query.lower()
        results = [
            m
            for m in self._models
            if query_lower in m.get("id", "").lower()
            or query_lower in m.get("name", "").lower()
        ]
        return results[:limit]

    def get_last_sync_time(self) -> Optional[datetime]:
        """Get timestamp of last successful sync."""
        return self._last_sync


# Singleton instance
_model_scout: Optional[ModelScoutIntegration] = None


def get_model_scout() -> ModelScoutIntegration:
    """Get the model scout singleton."""
    global _model_scout
    if _model_scout is None:
        _model_scout = ModelScoutIntegration()
    return _model_scout
