"""Provider detection and adapter module for multi-provider support."""

from src.services.providers.provider_detector import (
    Provider,
    NormalizationLevel,
    AuthType,
    detect_provider,
    get_normalization_level,
    get_auth_type,
    get_provider_info,
    requires_oauth,
    requires_full_normalization,
    skip_normalization,
    get_provider_config,
    PROVIDER_CONFIG,
)

__all__ = [
    "Provider",
    "NormalizationLevel",
    "AuthType",
    "detect_provider",
    "get_normalization_level",
    "get_auth_type",
    "get_provider_info",
    "requires_oauth",
    "requires_full_normalization",
    "skip_normalization",
    "get_provider_config",
    "PROVIDER_CONFIG",
]
