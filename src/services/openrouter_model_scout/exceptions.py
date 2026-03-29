"""
Custom exception hierarchy for OpenRouter Model Scout.
Implements: APIError, ScraperError, DataCorruptionError, ConfigurationError
"""

from typing import Any, Dict, Optional


class ScoutError(Exception):
    """Base exception for all scout errors."""
    pass


class APIError(ScoutError):
    """Raised when OpenRouter API interaction fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ScraperError(ScoutError):
    """Raised when web scraping fails."""

    def __init__(
        self,
        message: str,
        model_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.model_id = model_id
        self.details = details or {}


class DataCorruptionError(ScoutError):
    """Raised when data files are corrupted and backed up."""

    def __init__(
        self,
        message: str,
        file_path: str,
        backup_path: Optional[str] = None
    ):
        super().__init__(message)
        self.file_path = file_path
        self.backup_path = backup_path


class ConfigurationError(ScoutError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, missing_keys: Optional[list] = None):
        super().__init__(message)
        self.missing_keys = missing_keys or []
