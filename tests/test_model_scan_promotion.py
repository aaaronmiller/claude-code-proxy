"""CG-T043 — the promotion vector and rollback gate.

Promotion of validated canary evidence requires a complete eight-dimension
evidence vector plus a passing required regression gate. Missing, unknown, or
failing evidence blocks promotion without touching the active binding.
Rollback restores the captured previous binding in memory only.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.model_scan_promotion import (
    DIMENSIONS,
    DimensionEvidence,
    PromotionBlocked,
    RegressionEvidence,
    build_promotion_vector,
    promote,
    rollback,
)
from src.core.model_scan_runtime import get_active_binding

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tests" / "fixtures" / "snapshots" / "valid_snapshot.json"


def _write_state(tmp_path: Path) -> tuple[Path, Path]:
    chain_path = tmp_path / "proxy_chain.json"
    chain_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "entries": [],
                "router": {},
                "assignments": [
                    {
                        "id": "big",
                        "kind": "tier",
                        "model": "static/big",
                        "provider": "static",
                        "base_url": "",
                        "api_key": "must-not-appear",
                        "enabled": True,
                        "cascade": ["static/fallback"],
                    }
                ],
                "identifier_mappings": [],
                "model_scan": {
                    "enabled": True,
                    "policy": "free",
                    "snapshot_path": str(SNAPSHOT),
                    "staleness_limit_s": 315360000,
                },
            }
        ),
        encoding="utf-8",
    )
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "default": {"lane": "interactive", "slot_bindings": {"big": "R1_primary"}},
                "normal": {
                    "lane": "interactive",
                    "slot_bindings": {"big": "R8_web_extract"},
                },
            }
        ),
        encoding="utf-8",
    )
    return chain_path, profiles_path


def _prepare(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _write_state(tmp_path)
    monkeypatch.setenv("PROXY_CHAIN_FILE", str(chain_path))
    monkeypatch.setattr(model_scan_runtime, "DEFAULT_PROFILES_PATH", profiles_path)
    monkeypatch.setattr(profiles, "DEFAULT_PROFILES_PATH", profiles_path)
    profiles._cache = {}
    profiles._cache_path = None
    from src.core.model_scan_binder import BindResult, ResolvedBinding

    baseline = BindResult(
        global_tiers={},
        overlay={
            "normal": {
                "big": ResolvedBinding(
                    api_model="normal/model",
                    base_url="",
                    cascade=("normal/fallback",),
                    source="snapshot",
                    provider="normal",
                    role="R8_web_extract",
                )
            }
        },
        scan_id=7,
        schema_version="baseline",
    )
    monkeypatch.setattr(model_scan_runtime, "_ACTIVE_BINDING", baseline)
    profiles._ephemeral_profiles.clear()
    proxy_chain_module.reload_chain()
    return chain_path, profiles_path


_PASSING_EVIDENCE = {
    "protocol": DimensionEvidence(
        "protocol",
        "pass",
        "tests/test_request_converter_reasoning.py",
        "request conversion preserves protocol shape",
    ),
    "streaming": DimensionEvidence(
        "streaming", "pass", "tests/test_reasoning_integration.py", "streamed deltas intact"
    ),
    "tools": DimensionEvidence(
        "tools", "pass", "tests/test_model_supports_tools.py", "tool support verified"
    ),
    "response_identity": DimensionEvidence(
        "response_identity",
        "pass",
        "tests/test_normalize_tool_arguments.py",
        "response identity preserved",
    ),
    "latency": DimensionEvidence(
        "latency",
        "pass",
        "tests/fixtures/snapshots/valid_snapshot.json#latency",
        "latency evidence present in snapshot",
    ),
    "quota_cost": DimensionEvidence(
        "quota_cost",
        "pass",
        "tests/test_quota_store.py",
        "typed meters distinguish quota and cost",
    ),
    "fallback": DimensionEvidence(
        "fallback",
        "pass",
        "shadow:comparison#fallbacks",
        "cascade fallbacks resolved for the canary binding",
    ),
    "rollback": DimensionEvidence(
        "rollback",
        "pass",
        "tests/test_model_scan_promotion.py::test_rollback_restores_previous_binding",
        "rollback drill proven",
    ),
}

_PASSING_REGRESSION = RegressionEvidence(
    gate="offline-regression",
    passed=True,
    ran_at="2026-08-29T00:00:00Z",
    result_ref="tests/test_model_scan_promotion.py",
)


def _complete_vector(canary: dict) -> dict:
    return build_promotion_vector(
        canary=canary,
        dimension_evidence=dict(_PASSING_EVIDENCE),
        regression=_PASSING_REGRESSION,
    )


def _create_canary():
    from src.core import model_scan_runtime

    return model_scan_runtime.create_model_scan_canary(ttl_s=600)


def test_complete_vector_promotes_and_rollback_restores(monkeypatch, tmp_path):
    from src.core import model_scan_runtime
    from src.core import profiles
    from src.core import proxy_chain as proxy_chain_module

    chain_path, profiles_path = _prepare(monkeypatch, tmp_path)
    chain_before = chain_path.read_bytes()
    profiles_before = profiles_path.read_bytes()
    previous_active = get_active_binding()
    previous_global = dict(previous_active.global_tiers)

    canary = _create_canary()
    vector = _complete_vector(canary)
    assert vector.vector_id.startswith("sha256:")
    assert tuple(vector.dimensions.keys()) == DIMENSIONS

    record = promote(vector)

    assert record["record_kind"] == "promotion"
    assert record["applied_assignments"] == ["big"]
    assert record["persistent_writes"] == []
    assert record["traffic_sent"] is False
    promoted = get_active_binding()
    assert promoted is not previous_active
    assert promoted.global_tiers["big"].api_model == (
        "openrouter/deepseek/deepseek-v4-flash:free"
    )
    assert promoted.global_tiers["big"].source == "canary"
    assert promoted.provenance["canary.big"] == "canary"
    assert promoted.schema_version.startswith("canary:sha256:")
    # per-profile overlays are preserved through promotion
    assert "normal" in promoted.overlay
    # exact canary bindings remain profile-scoped; active overlay never leaks them
    assert profiles.resolve_profile(canary["profile_id"]).kind == "canary"

    rollback_summary = rollback(record)
    assert rollback_summary["restored"] is True
    assert rollback_summary["persistent_writes"] == []
    restored = get_active_binding()
    assert dict(restored.global_tiers) == previous_global
    assert restored.schema_version == previous_active.schema_version
    assert restored.scan_id == previous_active.scan_id
    with pytest.raises(PromotionBlocked):
        rollback(record)
    assert chain_path.read_bytes() == chain_before
    assert profiles_path.read_bytes() == profiles_before
    assert proxy_chain_module.get_chain() is not None


def test_missing_or_unknown_or_failing_dimension_blocks(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    canary = _create_canary()

    incomplete = dict(_PASSING_EVIDENCE)
    incomplete.pop("latency")
    with pytest.raises(PromotionBlocked, match="latency"):
        build_promotion_vector(
            canary=canary,
            dimension_evidence=incomplete,
            regression=_PASSING_REGRESSION,
        )

    unknown = dict(_PASSING_EVIDENCE)
    unknown["tools"] = DimensionEvidence("tools", "unknown", "nowhere", "unmeasured")
    with pytest.raises(PromotionBlocked, match="no decided evidence"):
        build_promotion_vector(
            canary=canary,
            dimension_evidence=unknown,
            regression=_PASSING_REGRESSION,
        )

    failing = dict(_PASSING_EVIDENCE)
    failing["fallback"] = DimensionEvidence(
        "fallback", "fail", "shadow:comparison#fallbacks", "cascade unresolved"
    )
    with pytest.raises(PromotionBlocked, match="fallback"):
        build_promotion_vector(
            canary=canary,
            dimension_evidence=failing,
            regression=_PASSING_REGRESSION,
        )
    assert get_active_binding() is not None


def test_failed_regression_blocks_promotion(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    canary = _create_canary()
    failed = RegressionEvidence(
        gate="offline-regression",
        passed=False,
        ran_at="2026-08-29T00:00:00Z",
        result_ref="tests/test_model_scan_promotion.py",
    )
    with pytest.raises(PromotionBlocked, match="regression"):
        build_promotion_vector(
            canary=canary,
            dimension_evidence=dict(_PASSING_EVIDENCE),
            regression=failed,
        )


def test_promotion_requires_live_unexpired_canary(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    canary = _create_canary()
    vector = _complete_vector(canary)
    stale = type(vector)(
        canary_profile_id="canary-not-real",
        comparison_ids=vector.comparison_ids,
        dimensions=dict(vector.dimensions),
        regression=vector.regression,
        vector_id="sha256:" + "0" * 64,
    )
    with pytest.raises(PromotionBlocked, match="not a live canary"):
        promote(stale)

    import time

    from src.core import profiles

    profiles._ephemeral_profiles[canary["profile_id"]]["expires_at"] = time.time() - 1
    with pytest.raises(PromotionBlocked, match="not a live canary"):
        promote(vector)


def test_promotion_rejects_changed_source_comparisons(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    canary = _create_canary()
    vector = _complete_vector(canary)
    from src.core import profiles

    profiles._ephemeral_profiles[canary["profile_id"]]["source_comparison_ids"] = [
        "sha256:" + "1" * 64
    ]
    with pytest.raises(PromotionBlocked, match="changed"):
        promote(vector)
