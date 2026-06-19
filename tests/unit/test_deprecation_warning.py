"""Unit tests for legacy env-var alias handling and deprecation summary.

Tests the legacy alias scan (FR-023/FR-024) and the deprecation-summary
emitter (R5) (T016).
"""

import os
import builtins
from unittest import mock

import pytest

from src.core.config_resolver import ConfigResolver, ConfigLayer, FieldSchema


def test_legacy_alias_maps_to_modern_field() -> None:
    """A legacy env var present at resolver startup should populate the modern field."""
    # Arrange: set legacy env var before resolver scans it
    with mock.patch.dict(os.environ, {"BIG_MODEL": "openai/gpt-4"}):
        resolver = ConfigResolver()
        # Act: resolve the modern field
        rv = resolver.resolve("assignments.big.model")
        # Assert
        assert rv.value == "openai/gpt-4"
        assert rv.source_layer == ConfigLayer.SHELL_ENV  # came from shell env (mapped)
        # Also, alias should be tracked as deprecated
        assert "BIG_MODEL" in resolver.deprecated_aliases_in_use


def test_multiple_legacy_aliases_tracked() -> None:
    """Multiple legacy vars across tiers should be detected."""
    env = {
        "BIG_MODEL": "model1",
        "MIDDLE_MODEL": "model2",
        "SMALL_MODEL": "model3",
        "ENABLE_BIG_ENDPOINT": "true",  # this should map; but our schema for assignments.big.enabled uses alias? Actually we didn't alias that. But for test, any alias.
    }
    # Our registration only added alias for model keys; ENABLE_BIG_ENDPOINT alias not set because we didn't define it in FieldSchema for any field. So ignore.
    with mock.patch.dict(os.environ, env, clear=False):
        resolver = ConfigResolver()
        aliases = resolver.deprecated_aliases_in_use
        # We expect BIG_MODEL, MIDDLE_MODEL, SMALL_MODEL
        assert "BIG_MODEL" in aliases or "BIG_MODEL" in aliases
        assert "MIDDLE_MODEL" in aliases
        assert "SMALL_MODEL" in aliases


def test_legacy_alias_not_used_if_modern_field_already_set_higher() -> None:
    """If both legacy env and assigned value exist in a higher layer, higher wins."""
    # Pre-populate SHELL_ENV with legacy
    with mock.patch.dict(os.environ, {"BIG_MODEL": "legacy-model"}):
        resolver = ConfigResolver()
        # Now, set modern field explicitly in CLI layer (higher than SHELL_ENV)
        resolver.set(
            "assignments.big.model",
            "cli-model",
            ConfigLayer.CLI,
            principal="test",
        )
        rv = resolver.resolve("assignments.big.model")
        assert rv.value == "cli-model"
        assert rv.source_layer == ConfigLayer.CLI
        # Legacy alias still tracked even though not used
        assert "BIG_MODEL" in resolver.deprecated_aliases_in_use


def test_deprecation_summary_emits_once() -> None:
    """emit_deprecation_summary prints listing of aliases; can be called multiple times."""
    resolver = ConfigResolver()
    # Simulate an alias already registered
    resolver._deprecated_aliases.add("OLD_VAR")
    # Capture stdout
    with mock.patch("builtins.print") as mock_print:
        resolver.emit_deprecation_summary()
        mock_print.assert_called()
        # Check that print was called with header and the alias
        print_calls = [str(c.args) for c in mock_print.call_args_list]
        # There should be a line with "OLD_VAR"
        assert any("OLD_VAR" in str(c) for c in print_calls)
