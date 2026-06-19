"""Property-based precedence tests for ConfigResolver.

Verifies that resolve() returns the value from the highest-precedence layer
among those that contain the requested field (T015).

Per resolver.md contract: every readable field must be registered via
register_schema() first. Direct layer dict mutation is a test-only escape
hatch since set() rejects writes to read-only layers (SHELL_ENV/DOTENV/DEFAULT).
"""

from typing import Any

import pytest
from hypothesis import given, strategies as st

from src.core.config_resolver import ConfigLayer, ConfigResolver, FieldSchema


def _populate_layer(
    resolver: ConfigResolver, field: str, value: Any, layer: ConfigLayer
) -> None:
    with resolver._lock:
        resolver._layers[layer][field] = value


def _make_resolver_with_field(field: str, type_: type = str) -> ConfigResolver:
    resolver = ConfigResolver()
    resolver._initialized = True  # skip lazy init side-effects
    resolver.register_schema(field, FieldSchema(type=type_, default=None))
    # Clear any layer-prepopulated env vars that might collide with our test field
    for layer in ConfigLayer:
        resolver._layers[layer].pop(field, None)
    return resolver


@given(
    st.lists(
        st.tuples(
            st.sampled_from(list(ConfigLayer)),
            st.integers(min_value=-1000, max_value=1000),
        ),
        min_size=1,
        max_size=10,
    )
)
def test_precedence_with_integers(assignments: list[tuple[ConfigLayer, int]]) -> None:
    """For a single field, ensure the highest-precedence layer wins."""
    field = "test_int_field"
    resolver = _make_resolver_with_field(field, int)

    for layer, value in assignments:
        _populate_layer(resolver, field, value, layer)

    expected_layer = next(
        layer for layer in ConfigLayer if any(layer == l for l, _ in assignments)
    )
    expected_value = next(v for l, v in reversed(assignments) if l == expected_layer)

    rv = resolver.resolve(field)
    assert rv.value == expected_value
    assert rv.source_layer == expected_layer


@given(
    st.lists(
        st.tuples(
            st.sampled_from(list(ConfigLayer)),
            st.text(min_size=1, max_size=20).filter(
                lambda s: "${" not in s and "\x00" not in s
            ),
        ),
        min_size=1,
        max_size=10,
    )
)
def test_precedence_with_strings(assignments: list[tuple[ConfigLayer, str]]) -> None:
    """Same test but with string values (no ${VAR} references to avoid expansion)."""
    field = "test_string_field"
    resolver = _make_resolver_with_field(field, str)

    for layer, value in assignments:
        _populate_layer(resolver, field, value, layer)

    expected_layer = next(
        layer for layer in ConfigLayer if any(layer == l for l, _ in assignments)
    )
    expected_value = next(v for l, v in reversed(assignments) if l == expected_layer)

    rv = resolver.resolve(field)
    assert rv.value == expected_value
    assert rv.source_layer == expected_layer


def test_default_layer_wins_when_no_other_layer() -> None:
    """If no layer provides a value but a schema default exists, DEFAULT wins."""
    field = "default_only_field"
    resolver = _make_resolver_with_field(field, str)
    # Override schema with explicit default
    resolver.register_schema(
        field, FieldSchema(type=str, default="fallback-value")
    )

    rv = resolver.resolve(field)
    assert rv.value == "fallback-value"
    assert rv.source_layer == ConfigLayer.DEFAULT


def test_unknown_field_raises_keyerror() -> None:
    """Per contract: unknown field paths raise KeyError."""
    resolver = ConfigResolver()
    resolver._initialized = True
    with pytest.raises(KeyError):
        resolver.resolve("never.registered.field")
