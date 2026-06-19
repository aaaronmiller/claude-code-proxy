"""Selection-policy tests (T022/T024, selection slice of T056).

Pins the policy semantics the binder and rotation depend on:
  * free picks only zero-price candidates;
  * budget excludes both over-ceiling and unknown-price candidates;
  * quality admits unknown price;
  * roles respects each role's eval_mode;
  * the cascade always excludes the primary and the blocklist;
  * nothing qualifying yields (None, []), which keeps the static value.
"""

from __future__ import annotations

import pytest

from src.core.assignments import Assignment
from src.core.model_scan_binder import ResolvedBinding, SelectionPolicy, bind
from src.services.models.model_scan_snapshot import Candidate, RoleSelection, RoutingSnapshot


def _cand(model_id, price, *, provider="p", fitness=50.0, tier="A") -> Candidate:
    return Candidate(
        model_id=model_id,
        provider=provider,
        api_model=f"{provider}/{model_id}",
        base_url="",
        fitness=fitness,
        price_blended=price,
        tier=tier,
        has_tools=True,
        has_vision=False,
    )


def _role(candidates, *, eval_mode="cost_basis") -> RoleSelection:
    best = candidates[0] if candidates else None
    return RoleSelection(label="r", eval_mode=eval_mode, best=best, candidates=tuple(candidates))


# Ranked best-first: paid S, free A, paid-unknown, paid-expensive.
def _mixed_role(eval_mode="cost_basis") -> RoleSelection:
    return _role(
        [
            _cand("paid_s", 18.0, fitness=96.0, tier="S"),
            _cand("free_a", 0.0, fitness=81.0, tier="A"),
            _cand("unknown_b", None, fitness=70.0, tier="B"),
            _cand("paid_cheap", 0.30, fitness=65.0, tier="B"),
        ],
        eval_mode=eval_mode,
    )


# ── parse ───────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "spec,kind,ceiling",
    [
        ("static", "static", None),
        ("free", "free", None),
        ("quality", "quality", None),
        ("roles", "roles", None),
        ("budget:0.50", "budget", 0.50),
        ("budget:1", "budget", 1.0),
    ],
)
def test_parse_valid(spec, kind, ceiling):
    p = SelectionPolicy.parse(spec)
    assert p.kind == kind
    assert p.price_ceiling == ceiling


@pytest.mark.parametrize("spec", ["budget", "budget:abc", "cheap", "Free", ""])
def test_parse_invalid_or_default(spec):
    if spec == "":
        assert SelectionPolicy.parse(spec).kind == "static"
    else:
        with pytest.raises(ValueError):
            SelectionPolicy.parse(spec)


# ── static ──────────────────────────────────────────────────────────────────────


def test_static_chooses_nothing():
    primary, cascade = SelectionPolicy.parse("static").choose(_mixed_role(), frozenset())
    assert primary is None
    assert cascade == []


# ── free ────────────────────────────────────────────────────────────────────────


def test_free_picks_only_zero_price():
    primary, cascade = SelectionPolicy.parse("free").choose(_mixed_role(), frozenset())
    assert primary.model_id == "free_a"
    assert primary.price_blended == 0.0
    assert cascade == []  # only one free candidate in the pool


# ── budget ──────────────────────────────────────────────────────────────────────


def test_budget_excludes_over_ceiling_and_unknown_price():
    primary, cascade = SelectionPolicy.parse("budget:0.50").choose(_mixed_role(), frozenset())
    # paid_s (18.0) over ceiling, unknown_b null both excluded; free_a and paid_cheap remain.
    chosen = [primary.model_id] + [c.model_id for c in cascade]
    assert chosen == ["free_a", "paid_cheap"]


def test_budget_zero_ceiling_is_free_only():
    primary, cascade = SelectionPolicy.parse("budget:0").choose(_mixed_role(), frozenset())
    assert primary.model_id == "free_a"
    assert cascade == []


# ── quality ─────────────────────────────────────────────────────────────────────


def test_quality_admits_unknown_price_and_keeps_rank():
    primary, cascade = SelectionPolicy.parse("quality").choose(_mixed_role(), frozenset())
    chosen = [primary.model_id] + [c.model_id for c in cascade]
    assert chosen == ["paid_s", "free_a", "unknown_b", "paid_cheap"]


# ── roles (respects eval_mode) ──────────────────────────────────────────────────


def test_roles_free_evalmode_behaves_free():
    primary, cascade = SelectionPolicy.parse("roles").choose(
        _mixed_role(eval_mode="free"), frozenset()
    )
    assert primary.model_id == "free_a"
    assert cascade == []


def test_roles_cost_evalmode_admits_all():
    primary, cascade = SelectionPolicy.parse("roles").choose(
        _mixed_role(eval_mode="cost_basis"), frozenset()
    )
    assert primary.model_id == "paid_s"
    assert len(cascade) == 3


# ── blocklist + cascade-excludes-primary ────────────────────────────────────────


def test_cascade_excludes_blocklist_and_primary():
    block = frozenset({"p/paid_s"})  # blocklist by api_model
    primary, cascade = SelectionPolicy.parse("quality").choose(_mixed_role(), block)
    assert primary.model_id == "free_a"  # blocked paid_s dropped, next becomes primary
    cascade_ids = [c.model_id for c in cascade]
    assert "paid_s" not in cascade_ids
    assert "free_a" not in cascade_ids  # primary never repeats in its own cascade
    assert cascade_ids == ["unknown_b", "paid_cheap"]


def test_empty_candidates_keep_static():
    primary, cascade = SelectionPolicy.parse("quality").choose(_role([]), frozenset())
    assert primary is None
    assert cascade == []


# ── binder ─────────────────────────────────────────────────────────────────────


def _snapshot(slots: dict[str, RoleSelection], blocklist=frozenset()) -> RoutingSnapshot:
    return RoutingSnapshot(
        schema_version="1.0.0",
        generated_at="2026-05-31T18:42:00Z",
        scan_id=1487,
        slots=slots,
        provider_health={},
        provider_quota={},
        blocklist=frozenset(blocklist),
        loaded_at=1.0,
    )


def test_bind_updates_default_tiers_from_snapshot_and_records_cascade():
    snap = _snapshot(
        {
            "R1_primary": _role(
                [
                    _cand("paid_s", 18.0, provider="anthropic"),
                    _cand("free_a", 0.0, provider="openrouter"),
                    _cand("free_b", 0.0, provider="ollama_cloud"),
                ]
            )
        }
    )

    result = bind(
        snap,
        SelectionPolicy.parse("free"),
        {"default": {"big": "R1_primary"}},
    )

    assert result.scan_id == 1487
    assert result.global_tiers["big"] == ResolvedBinding(
        api_model="openrouter/free_a",
        base_url="",
        cascade=("ollama_cloud/free_b",),
        source="snapshot",
        provider="openrouter",
        role="R1_primary",
    )
    assert result.provenance["default.big"] == "snapshot"


def test_bind_missing_role_keeps_static_assignment():
    static = {
        "big": Assignment(
            id="big",
            kind="tier",
            model="static/big",
            provider="static_provider",
            base_url="https://static.example/v1",
            cascade=["static/fallback"],
        )
    }
    result = bind(
        _snapshot({}),
        SelectionPolicy.parse("quality"),
        {"default": {"big": "R_missing"}},
        static_bindings=static,
    )

    assert result.global_tiers["big"].api_model == "static/big"
    assert result.global_tiers["big"].cascade == ("static/fallback",)
    assert result.global_tiers["big"].provider == "static_provider"
    assert result.provenance["default.big"] == "static"


def test_bind_profile_overlay_differs_from_default_without_mutating_global_tier():
    snap = _snapshot(
        {
            "R1_primary": _role([_cand("primary", 1.0, provider="anthropic")]),
            "R8_web_extract": _role(
                [_cand("extract", 0.0, provider="openrouter")],
                eval_mode="free",
            ),
        }
    )

    result = bind(
        snap,
        SelectionPolicy.parse("roles"),
        {
            "default": {"big": "R1_primary"},
            "codex": {"big": "R8_web_extract"},
        },
    )

    assert result.global_tiers["big"].api_model == "anthropic/primary"
    assert result.overlay["codex"]["big"].api_model == "openrouter/extract"
    assert "default" not in result.overlay
    assert result.provenance["codex.big"] == "snapshot"


def test_bind_standby_lane_uses_free_policy():
    snap = _snapshot(
        {
            "R1_primary": _role(
                [
                    _cand("paid", 1.0, provider="paid"),
                    _cand("free", 0.0, provider="openrouter"),
                ]
            )
        }
    )

    result = bind(
        snap,
        SelectionPolicy.parse("quality"),
        {"default": {"big": "R1_primary"}},
        profile_lanes={"default": "standby"},
    )

    assert result.global_tiers["big"].api_model == "openrouter/free"
