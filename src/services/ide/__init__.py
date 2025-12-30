"""
IDE Services Module

Provides IDE detection and configuration for cross-IDE support.
"""

from .ide_detector import (
    IDE,
    APIFormat,
    IDE_CONFIG,
    detect_ide,
    detect_ide_from_headers,
    detect_ide_from_endpoint,
    detect_ide_from_body,
    get_api_format,
    is_anthropic_format,
    is_openai_format,
    get_ide_info
)

__all__ = [
    "IDE",
    "APIFormat",
    "IDE_CONFIG",
    "detect_ide",
    "detect_ide_from_headers",
    "detect_ide_from_endpoint",
    "detect_ide_from_body",
    "get_api_format",
    "is_anthropic_format",
    "is_openai_format",
    "get_ide_info"
]
