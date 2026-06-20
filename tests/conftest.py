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
        "BIG_API_KEY",
        "BIG_ENDPOINT",
        "PROXY_AUTH_KEY",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_API_KEY",
        "ENABLE_LEGACY_PROXY_AUTH",
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
        "FUSION_PROFILE",
        "FUSION_ALIASES",
        "FUSION_PROFILES",
        "FUSION_FREE_ANALYSIS_MODELS",
        "FUSION_FREE_MODEL",
        "FUSION_FREE_PRESET",
        "FUSION_FREE_FORCE",
        "FUSION_FREE_ENABLED",
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    return monkeypatch


@pytest.fixture
def sample_config(monkeypatch):
    """Sample valid configuration"""
    monkeypatch.setenv("BIG_API_KEY", "sk-test-1234567890123456789012345678")
    monkeypatch.setenv("BIG_ENDPOINT", "https://api.openai.com/v1")
    monkeypatch.setenv("BIG_MODEL", "gpt-4o")
    monkeypatch.setenv("MIDDLE_MODEL", "gpt-4o")
    monkeypatch.setenv("SMALL_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8082")

    return monkeypatch


@pytest.fixture(autouse=True)
def _isolate_proxy_chain_file(tmp_path, monkeypatch):
    """Prevent any test from mutating the repo's real config/proxy_chain.json.

    The chain API and AssignmentRegistry persist via ProxyChain.save(), which writes to
    config/proxy_chain.json (path overridable via PROXY_CHAIN_FILE). Chain/assignment tests that
    POST/PATCH/DELETE entries were saving to the real file, polluting it with test entries and
    breaking later runs (e.g. a leftover 'tobedeleted' entry made test_delete_chain_entry fail).

    This autouse fixture copies the real chain to a per-test temp file and points
    PROXY_CHAIN_FILE at it, so reads see identical content but writes stay isolated. Tests that set
    PROXY_CHAIN_FILE themselves run after this setup and override it, keeping their own behavior.
    """
    from src.core.proxy_chain import DEFAULT_CHAIN_FILE, reload_chain

    real = Path(DEFAULT_CHAIN_FILE)
    if real.exists():
        tmp = tmp_path / "proxy_chain.json"
        tmp.write_text(real.read_text())
        monkeypatch.setenv("PROXY_CHAIN_FILE", str(tmp))
        reload_chain()
    yield
    # monkeypatch restores the env automatically; reset the singleton best-effort. A test may have
    # repointed PROXY_CHAIN_FILE at a deliberately-malformed file (e.g. migration-halt tests) that
    # is still active during teardown, so a reload here must never raise.
    try:
        reload_chain()
    except Exception:
        pass
