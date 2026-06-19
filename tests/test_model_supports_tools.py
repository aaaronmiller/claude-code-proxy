"""S1-03: tool-capability must come from the capability registry, not hardcoded
model/family name prefixes. See ai-gateway/plan/recon/RECON-01-hardcoded-models.md."""
import src.services.usage.model_limits as ml
from src.core import model_router


def test_capability_from_registry_unknown_family(monkeypatch):
    # An unknown-family model the registry reports as tool-capable -> True,
    # proving capability is data-driven, not name-prefix.
    monkeypatch.setattr(
        ml, "get_model_info",
        lambda m: {"tool_call": True} if m == "acme/zeta-9" else {},
    )
    monkeypatch.setattr(model_router, "_get_tool_capable_models", lambda: set())
    assert model_router._model_supports_tools("acme/zeta-9") is True


def test_no_hardcoded_family_prefix(monkeypatch):
    # Previously "claude-*" returned True via a hardcoded prefix. With the registry
    # empty and no dynamic signal, it must now be data-driven (False), proving the
    # hardcoded prefix is gone.
    monkeypatch.setattr(ml, "get_model_info", lambda m: {})
    monkeypatch.setattr(model_router, "_get_tool_capable_models", lambda: set())
    assert model_router._model_supports_tools("claude-foo-unknown") is False


def test_dynamic_cache_fallback_full_and_family(monkeypatch):
    monkeypatch.setattr(ml, "get_model_info", lambda m: {})
    monkeypatch.setattr(
        model_router, "_get_tool_capable_models", lambda: {"acme/zeta-9"}
    )
    # full id match
    assert model_router._model_supports_tools("acme/zeta-9") is True
    # bare family id after provider prefix also matches the dynamic set
    monkeypatch.setattr(
        model_router, "_get_tool_capable_models", lambda: {"zeta-9"}
    )
    assert model_router._model_supports_tools("other/zeta-9") is True


def test_empty_model_id():
    assert model_router._model_supports_tools("") is False
