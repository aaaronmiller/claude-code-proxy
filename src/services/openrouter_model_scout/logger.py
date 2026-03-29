"""
Logging configuration for the scout.
Implements: setup_logger() with levels, structured formatting, file output
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "openrouter_scout",
    level: int = logging.INFO,
    log_file: Optional[str | Path] = None,
    fmt: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handler.

    Args:
        name: Logger name
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional file path for file logging
        fmt: Optional custom format string

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Default format
    if fmt is None:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)

    # Console handler (stderr for errors/info, stdout for debug)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
