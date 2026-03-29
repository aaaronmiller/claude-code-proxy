"""
Main entry point for OpenRouter Model Scout.
Orchestrates the full pipeline: fetch → normalize → leaderboard.
"""

import argparse
import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
import random

from openrouter_model_scout.config import (
    Config,
    load_env_vars,
    validate_config,
    get_cli_flags,
)
from openrouter_model_scout.logger import setup_logger
from openrouter_model_scout.fetcher_api import fetch_models
from openrouter_model_scout.normalizer import normalize_data
from openrouter_model_scout.change_detector import (
    calculate_checksum,
    detect_pricing_delta,
    queue_new_models,
)
from openrouter_model_scout.leaderboard import (
    generate_smartest_leaderboard,
    generate_coding_leaderboard,
    generate_free_leaderboard,
    generate_value_leaderboard,
    write_leaderboard,
    validate_lists,
)
from openrouter_model_scout.io import load_json, atomic_json_write
from openrouter_model_scout.meta import load_meta, append_run, write_meta
from openrouter_model_scout.token_utils import track_api_call
from openrouter_model_scout.cost import calculate_estimated_cost
from openrouter_model_scout.models import Model, Meta, Leaderboard
from openrouter_model_scout.scraper_web import (
    ScraperManager,
    process_model_queue,
    convert_scrape_results_to_enrichment,
    estimate_scrape_cost,
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="OpenRouter Model Scout")
    flags = get_cli_flags()

    for flag, opts in flags.items():
        parser.add_argument(f"--{flag}", **opts)

    args = parser.parse_args()
    return args


def should_run_auto(data_dir: Path, last_run_str: str, max_age_hours: int) -> bool:
    """
    Check if automatic run is needed based on timestamp.

    Args:
        data_dir: Data directory path
        last_run_str: ISO timestamp of last run
        max_age_hours: Max age threshold in hours

    Returns:
        True if run needed, False otherwise
    """
    if not last_run_str:
        return True

    last_run = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    age = now - last_run

    return age.total_seconds() > (max_age_hours * 3600)


def load_previous_models(models_path: Path) -> list:
    """Load previous models.json if exists, else empty list."""
    if not models_path.exists():
        return []
    try:
        models_data = load_json(models_path)
        from openrouter_model_scout.models import Model

        return [Model.model_validate(m) for m in models_data]
    except Exception as e:
        logger.error(f"Failed to load previous models: {e}")
        return []


def orchestrate_api_sync(config: Config, args) -> tuple[list[Model], dict]:
    """
    Execute API sync phase.

    Returns:
        (models, token_usage)
    """
    start = time.time()
    logger.info("Starting API sync phase")

    # Run async fetch
    models = asyncio.run(fetch_models(config))

    duration = time.time() - start
    logger.info(f"API sync completed in {duration:.2f}s, fetched {len(models)} models")

    # Estimate token usage (GET request size we could measure response size)

    response_size = sum(len(m.model_dump_json()) for m in models)
    token_est = estimate_response_size(models)

    token_usage = {
        "prompt_tokens": 0,  # GET request has no body
        "completion_tokens": token_est["completion_tokens"],
        "estimated_cost_usd": 0.0,  # Will calculate after applying pricing if needed
    }

    return models, token_usage


def estimate_response_size(models: list[Model]) -> dict:
    """Estimate token count for API response."""
    total_chars = sum(len(m.model_dump_json()) for m in models)
    tokens = total_chars // 4  # Rough approximation
    return {"completion_tokens": tokens}


def orchestrate_deep_scrape(
    config: Config, models_to_scrape: list[Model], scrape_duration: float = 0.0
) -> tuple[dict, dict, float]:
    """
    Execute deep web scraping for benchmark data.

    Args:
        config: Configuration object
        models_to_scrape: List of models needing scrape data
        scrape_duration: Time spent in previous scrape (for resuming)

    Returns:
        (scraped_data, token_usage)
    """
    start = time.time()
    logger.info(f"Starting deep scrape for {len(models_to_scrape)} models")

    scraped_data = {}
    total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0}

    if not models_to_scrape:
        logger.info("No models require deep scraping")
        return scraped_data, total_token_usage

    try:
        with ScraperManager(
            stealth_mode=True, max_concurrent=1, delay_range=(2.0, 5.0)
        ) as manager:
            # Process the queue
            results = asyncio.run(
                process_model_queue([m.id for m in models_to_scrape], manager)
            )

            # Convert to enrichment format
            scraped_data = convert_scrape_results_to_enrichment(results)

            # Accumulate token usage from scraping
            for model_id in results:
                cost = estimate_scrape_cost(model_id)
                total_token_usage["prompt_tokens"] += cost["prompt_tokens"]
                total_token_usage["completion_tokens"] += cost["completion_tokens"]

            scrape_duration = time.time() - start
            logger.info(
                f"Deep scrape completed in {scrape_duration:.2f}s, scraped {len(results)} models"
            )

    except Exception as e:
        logger.error(f"Deep scrape failed: {e}")
        # Graceful degradation: return empty scraped data, continue with API-only
        scraped_data = {}

    return scraped_data, total_token_usage, scrape_duration


def run_scout(config: Config, dry_run: bool = False) -> dict:
    """
    Core orchestration logic. Can be called programmatically.

    Args:
        config: Configuration object
        dry_run: If True, don't write files

    Returns:
        dict with results: {
            'models': list[Model],
            'leaderboard': Leaderboard,
            'token_usage': dict,
            'duration': float
        }
    """
    start = time.time()
    logger.info("=== OpenRouter Model Scout starting ===")

    # Paths
    data_dir = Path(config.data_dir)
    models_path = data_dir / "models.json"
    meta_path = data_dir / "meta.json"

    # Execute pipeline
    try:
        # Phase 1: API Sync (Tier 1)
        api_models, api_token_usage = orchestrate_api_sync(config, None)

        # Phase 2: Change Detection
        previous_models = load_previous_models(models_path)
        previous_checksum = (
            calculate_checksum(previous_models) if previous_models else None
        )
        current_checksum = calculate_checksum([m.model_dump() for m in api_models])

        # Determine if we need deep scraping
        needs_deep_scrape = False
        if config.force:
            needs_deep_scrape = True
            logger.info("Force flag set: will run deep scrape for all models")
        else:
            # Check for new models
            current_ids = {m.id for m in api_models}
            previous_ids = {m.id for m in previous_models}
            new_model_ids = queue_new_models(current_ids, previous_ids)
            if new_model_ids:
                logger.info(
                    f"New models detected: {len(new_model_ids)} models need scraping"
                )
                needs_deep_scrape = True
            # Check if weekly audit due (last_deep_audit > 7 days)
            try:
                meta = load_meta(meta_path)
                last_deep = datetime.fromisoformat(
                    meta.last_deep_audit.replace("Z", "+00:00")
                )
                days_since_audit = (datetime.now(timezone.utc) - last_deep).days
                if days_since_audit >= 7:
                    logger.info(
                        f"Weekly audit due ({days_since_audit} days since last audit)"
                    )
                    needs_deep_scrape = True
            except Exception:
                needs_deep_scrape = True  # If meta missing, do deep scrape

        # Phase 2.5: Conditional Deep Scrape
        scrape_token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        scrape_duration = 0.0

        if needs_deep_scrape:
            models_to_scrape = api_models  # For now, scrape all; can optimize later
            scraped_data, scrape_token_usage, scrape_duration = orchestrate_deep_scrape(
                config, models_to_scrape
            )
        else:
            scraped_data = {}
            logger.info("Skipping deep scrape (no changes detected)")

        # Phase 3: Normalize and Merge
        normalized_models = normalize_data(api_models, scraped_data)

        # Phase 4: Generate Leaderboards
        timestamp = datetime.now(timezone.utc).isoformat()
        leaderboard = Leaderboard(generated_at=timestamp)

        # Smartest (US1)
        leaderboard.smartest = generate_smartest_leaderboard(
            normalized_models, top_n=5, generated_at=timestamp
        ).smartest

        # Coding (US2)
        leaderboard.coding = generate_coding_leaderboard(
            normalized_models, top_n=5, generated_at=timestamp
        ).coding

        # Free (US2)
        leaderboard.free = generate_free_leaderboard(
            normalized_models, top_n=5, generated_at=timestamp
        ).free

        # Value (US2)
        leaderboard.value = generate_value_leaderboard(
            normalized_models, top_n=5, generated_at=timestamp
        ).value

        validate_lists(leaderboard)

        # Phase 5: Write outputs (unless dry-run)
        if not dry_run:
            # Write models.json
            models_data = [m.model_dump() for m in normalized_models]
            atomic_json_write(models_data, models_path)

            # Write leaderboard.json
            leaderboard_path = data_dir / "leaderboard.json"
            write_leaderboard(leaderboard, leaderboard_path)

            logger.info(f"Wrote {len(normalized_models)} models to {models_path}")
            logger.info(f"Wrote leaderboard to {leaderboard_path}")

            # Write CSV if requested
            output_format = getattr(config, "output_format", "json")
            if output_format in ("csv", "both"):
                from openrouter_model_scout.leaderboard import write_leaderboard_csv

                csv_path = Path(leaderboard_path).with_suffix(".csv")
                write_leaderboard_csv(leaderboard, csv_path)

            # Phase 6: Update meta
            meta = load_meta(meta_path)
            duration = time.time() - start

            # Calculate total cost from pricing of models that would have been called
            # Since we use GET to /models endpoint, there's no direct per-model cost
            # But we can track scraper costs if any
            base_api_cost = 0.0  # GET to /models is typically free or very cheap

            total_cost = base_api_cost

            # Add scraper token costs if any (LLM calls via crawl4AI)
            if scrape_token_usage["completion_tokens"] > 0:
                # Use the cost calculator - would need a reference pricing model
                # For now, keep as placeholder since scraper uses its own LLM
                pass

            token_usage = {
                "prompt_tokens": api_token_usage["prompt_tokens"]
                + scrape_token_usage["prompt_tokens"],
                "completion_tokens": api_token_usage["completion_tokens"]
                + scrape_token_usage["completion_tokens"],
                "estimated_cost_usd": total_cost,
            }

            mode = (
                "force" if config.force else ("full" if needs_deep_scrape else "fast")
            )
            append_run(
                meta,
                timestamp=timestamp,
                mode=mode,
                api_duration=time.time() - start,
                scrape_duration=scrape_duration,
                models_count=len(normalized_models),
                token_usage=token_usage,
            )
            write_meta(meta, meta_path)

            logger.info(f"Updated meta at {meta_path}")
        else:
            logger.info("Dry-run mode: no files written")

        duration = time.time() - start
        logger.info("=== OpenRouter Model Scout completed successfully ===")

        return {
            "models": normalized_models,
            "leaderboard": leaderboard,
            "token_usage": api_token_usage,
            "duration": duration,
        }

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise


def main():
    """CLI entry point."""
    args = parse_args()

    # Load configuration
    try:
        env_config = load_env_vars()
        validate_config(env_config)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Merge env and CLI flags into Config
    config = Config(
        openrouter_api_key=env_config["OPENROUTER_API_KEY"],
        data_dir=env_config.get("DATA_DIR", "data"),
        log_level=env_config.get("LOG_LEVEL", "INFO"),
        log_file=env_config.get("LOG_FILE"),
        force=args.force,
        fast_only=args.fast_only,
        dry_run=args.dry_run,
        token_report=args.token_report,
        output_format=env_config.get("OUTPUT_FORMAT", "json"),
        model_filter=args.model_filter,
    )

    # Setup logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, config.log_level)
    setup_logger(level=log_level, log_file=config.log_file)

    # Check if we should run (auto mode)
    should_run = True
    if not config.force:
        data_dir = Path(config.data_dir)
        meta_path = data_dir / "meta.json"
        try:
            meta = load_meta(meta_path)
            should_run = should_run_auto(
                data_dir, meta.last_run, config.api_sync_max_age_hours
            )
        except Exception:
            should_run = True

    if not should_run:
        logger.info(
            "Auto-check: No changes detected, skipping run. Use --force to override."
        )
        sys.exit(0)

    # Run orchestration
    try:
        result = run_scout(config, dry_run=config.dry_run)

        # Token report
        if config.token_report:
            usage = result["token_usage"]
            print("\n=== Token Usage Report ===")
            print(f"Prompt tokens: {usage['prompt_tokens']:,}")
            print(f"Completion tokens: {usage['completion_tokens']:,}")
            print(
                f"Total tokens: {usage['prompt_tokens'] + usage['completion_tokens']:,}"
            )
            print(f"Estimated cost: ${usage['estimated_cost_usd']:.6f}")
            print(f"Duration: {result['duration']:.2f}s")

        sys.exit(0)

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
