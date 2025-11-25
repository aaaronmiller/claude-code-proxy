"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment for testing"""
    # Remove all proxy-related env vars
    env_vars_to_clear = [
        "PROVIDER_API_KEY",
        "PROVIDER_BASE_URL",
        "PROXY_AUTH_KEY",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "BIG_MODEL",
        "MIDDLE_MODEL",
        "SMALL_MODEL",
        "ENABLE_BIG_ENDPOINT",
        "ENABLE_MIDDLE_ENDPOINT",
        "ENABLE_SMALL_ENDPOINT",
        "BIG_ENDPOINT",
        "MIDDLE_ENDPOINT",
        "SMALL_ENDPOINT",
        "BIG_API_KEY",
        "MIDDLE_API_KEY",
        "SMALL_API_KEY",
        "REASONING_EFFORT",
        "REASONING_MAX_TOKENS",
        "HOST",
        "PORT",
        "LOG_LEVEL",
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    return monkeypatch


@pytest.fixture
def sample_config(monkeypatch):
    """Sample valid configuration"""
    monkeypatch.setenv("PROVIDER_API_KEY", "sk-test-1234567890123456789012345678")
    monkeypatch.setenv("PROVIDER_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("BIG_MODEL", "gpt-4o")
    monkeypatch.setenv("MIDDLE_MODEL", "gpt-4o")
    monkeypatch.setenv("SMALL_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8082")

    return monkeypatch
