"""
Model Catalog Sync Script

Syncs model-scraper output into the main proxy's model catalog.
Can be run manually or scheduled weekly.

Usage:
    python -m src.services.models.catalog_sync          # Sync from scraper
    python -m src.services.models.catalog_sync --force # Force refresh
    python -m src.services.models.catalog_sync --show  # Show current catalog
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(
    __file__
).parent.parent.parent.parent  # src/services/models -> src -> project root
MODELS_DIR = PROJECT_ROOT / "models"
SCRAPER_DIR = PROJECT_ROOT / "model-scraper"
SCRAPER_DATA_DIR = SCRAPER_DIR / "data"
SCRAPER_LEADERBOARD = SCRAPER_DATA_DIR / "leaderboard.json"
SCRAPER_MODELS = SCRAPER_DATA_DIR / "models.json"
CATALOG_PATH = MODELS_DIR / "model_catalog.json"


def sync_from_scraper() -> bool:
    """Sync model catalog from scraper output."""
    logger.info("Syncing model catalog from scraper...")

    # Check if scraper has output
    if not SCRAPER_LEADERBOARD.exists():
        logger.warning(f"Scraper output not found at {SCRAPER_LEADERBOARD}")
        return False

    try:
        # Load scraper data
        with open(SCRAPER_LEADERBOARD) as f:
            leaderboard = json.load(f)

        # Also try to load full models data
        models_data = {}
        if SCRAPER_MODELS.exists():
            with open(SCRAPER_MODELS) as f:
                models_data = json.load(f)

        # Build catalog
        catalog = {
            "generated_at": leaderboard.get(
                "generated_at", datetime.now(timezone.utc).isoformat()
            ),
            "models": {},
            "all_models": {},
        }

        # Process each category from leaderboard
        for category in ["smartest", "coding", "free", "value"]:
            category_models = leaderboard.get(category, [])
            catalog["models"][category] = []

            for rank, model in enumerate(category_models, 1):
                model_id = model.get("id", "")

                # Look up full specs from models.json if available
                full_spec = {}
                if models_data:
                    for m in models_data:
                        if m.get("id") == model_id:
                            full_spec = m
                            break

                # Build model spec
                spec = {
                    "id": model_id,
                    "name": model.get("name", model_id),
                    "provider": model_id.split("/")[0]
                    if "/" in model_id
                    else "unknown",
                    "context_length": full_spec.get("context_length")
                    or model.get("context_length")
                    or 128000,
                    "max_output": full_spec.get("max_output_tokens")
                    or full_spec.get("max_output")
                    or 4096,
                    "price_per_1m_input": full_spec.get("price_per_1m_input", 0.0),
                    "price_per_1m_output": full_spec.get("price_per_1m_output", 0.0),
                    "throughput_tps": model.get("throughput_tps"),
                    "intelligence_score": model.get("intelligence_score"),
                    "is_free": ":free" in model_id.lower(),
                    "category": category,
                    "rank": rank,
                }

                catalog["models"][category].append(spec)
                catalog["all_models"][model_id] = spec

        # Save catalog
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(CATALOG_PATH, "w") as f:
            json.dump(catalog, f, indent=2)

        logger.info(f"Saved model catalog to {CATALOG_PATH}")
        logger.info(
            f"Catalog contains {len(catalog['all_models'])} models across {len(catalog['models'])} categories"
        )

        return True

    except Exception as e:
        logger.error(f"Error syncing catalog: {e}")
        return False


def show_catalog():
    """Display current model catalog."""
    if not CATALOG_PATH.exists():
        print("No model catalog found. Run with --sync to create one.")
        return

    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    print(f"\n📦 Model Catalog (generated: {catalog.get('generated_at', 'unknown')})\n")

    for category in ["free", "smartest", "coding", "value"]:
        models = catalog.get("models", {}).get(category, [])
        print(f"━━━ {category.upper()} ━━━")

        for m in models[:5]:
            free_badge = " 🆓" if m.get("is_free") else ""
            ctx = m.get("context_length", 0)
            ctx_str = f"{ctx / 1000:.0f}k" if ctx else "?"
            print(f"  {m.get('name', m['id'])} [{ctx_str} ctx]{free_badge}")

        print()


def main():
    parser = argparse.ArgumentParser(description="Model Catalog Sync Tool")
    parser.add_argument("--sync", action="store_true", help="Sync from scraper")
    parser.add_argument(
        "--run-scraper", action="store_true", help="Run scraper then sync"
    )
    parser.add_argument("--show", action="store_true", help="Show current catalog")
    parser.add_argument("--force", action="store_true", help="Force refresh")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    if args.show:
        show_catalog()
        return

    if args.run_scraper or args.sync:
        if args.run_scraper:
            if not run_scraper():
                logger.error("Failed to run scraper")
                sys.exit(1)

        if not sync_from_scraper():
            logger.error("Failed to sync catalog")
            sys.exit(1)

        show_catalog()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
