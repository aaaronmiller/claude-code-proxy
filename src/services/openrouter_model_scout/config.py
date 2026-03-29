"""
Configuration management for the scout.
Implements: load_env_vars(), validate_config(), CLI flag definitions
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Immutable configuration object."""
    openrouter_api_key: str
    data_dir: str = "data"
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Performance thresholds
    api_sync_max_age_hours: int = 24
    deep_audit_max_age_days: int = 7
    pricing_delta_threshold: float = 0.1

    # Scraper settings
    scraper_delay_min: float = 2.0
    scraper_delay_max: float = 5.0
    scraper_max_retries: int = 3

    # CLI flags
    force: bool = False
    fast_only: bool = False
    dry_run: bool = False
    token_report: bool = False
    output_format: str = "json"  # json, csv, both
    model_filter: Optional[str] = None

    # Internal
    _env: Dict[str, str] = None

    def __post_init__(self):
        """Store raw env for debugging."""
        if self._env is None:
            self._env = dict(os.environ)


def load_env_vars() -> Dict[str, str]:
    """
    Load required environment variables.

    Returns:
        Dict of env vars (keys uppercased)

    Raises:
        EnvironmentError: If required vars are missing
    """
    required = ["OPENROUTER_API_KEY"]
    config = {}

    for key in required:
        value = os.environ.get(key)
        if value is None:
            raise EnvironmentError(f"Missing required environment variable: {key}")
        config[key] = value

    # Optional vars with defaults
    config["DATA_DIR"] = os.environ.get("DATA_DIR", "data")
    config["LOG_LEVEL"] = os.environ.get("LOG_LEVEL", "INFO")
    config["LOG_FILE"] = os.environ.get("LOG_FILE", None)

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.

    Args:
        config: Configuration dict to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Required keys
    if "OPENROUTER_API_KEY" not in config:
        raise ValueError("Missing OPENROUTER_API_KEY")

    # Log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.get("LOG_LEVEL", "INFO").upper() not in valid_log_levels:
        raise ValueError(f"Invalid LOG_LEVEL. Must be one of: {valid_log_levels}")

    # Output format
    valid_formats = ["json", "csv", "both"]
    if config.get("OUTPUT_FORMAT", "json").lower() not in valid_formats:
        raise ValueError(f"Invalid OUTPUT_FORMAT. Must be one of: {valid_formats}")

    # Numeric thresholds
    if "API_SYNC_MAX_AGE_HOURS" in config:
        try:
            hours = int(config["API_SYNC_MAX_AGE_HOURS"])
            if hours <= 0:
                raise ValueError("API_SYNC_MAX_AGE_HOURS must be positive")
        except (ValueError, TypeError):
            raise ValueError("API_SYNC_MAX_AGE_HOURS must be an integer")

    if "PRICING_DELTA_THRESHOLD" in config:
        try:
            threshold = float(config["PRICING_DELTA_THRESHOLD"])
            if not (0 <= threshold <= 1):
                raise ValueError("PRICING_DELTA_THRESHOLD must be between 0 and 1")
        except (ValueError, TypeError):
            raise ValueError("PRICING_DELTA_THRESHOLD must be a number")


def get_cli_flags() -> Dict[str, Any]:
    """
    Get CLI flag definitions (for argparse integration).

    Returns:
        Dict mapping flag names to argparse kwargs
    """
    return {
        "force": {
            "action": "store_true",
            "help": "Ignore timestamps, execute full deep scan immediately",
        },
        "fast-only": {
            "action": "store_true",
            "dest": "fast_only",
            "help": "Only run API sync, skip web scraping entirely",
        },
        "dry-run": {
            "action": "store_true",
            "dest": "dry_run",
            "help": "Execute logic without writing files; print to stdout",
        },
        "token-report": {
            "action": "store_true",
            "dest": "token_report",
            "help": "Display detailed token usage and cost of the scraper itself",
        },
        "output-format": {
            "type": str,
            "choices": ["json", "csv", "both"],
            "default": "json",
            "dest": "output_format",
            "help": "Control output formats",
        },
        "model-filter": {
            "type": str,
            "dest": "model_filter",
            "help": "Only process matching model IDs (regex pattern)",
        },
        "verbose": {
            "action": "store_true",
            "help": "Enable debug logging",
        },
    }
