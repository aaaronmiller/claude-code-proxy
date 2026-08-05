"""Hard filters run before deterministic rank and never relax on empty."""

from dataclasses import replace

import pytest

from src.services.models.callable_catalog import CallableRecord
from src.services.models.candidate_selection import (
    CandidateEvidence,
    CandidateSelectionRejected,
    SelectionPolicy,
    select_candidates,
)
from src.services.models.task_classification import TaskClassification


def _record(
    callable_id,
    *,
    provider="openrouter",
    reachable=True,
):
    return CallableRecord(
        callable_id=callable_id,
        provider_id=provider,
        api_model_id=callable_id.split(":", 1)[-1],
        base_url=f"https://{provider}.example/v1",
        credential_ref=f"{provider.upper()}_API_KEY",
        observed_at="2026-07-23T13:00:00Z",
        reachable=reachable,
        features=("tools", "code_edit"),
        provenance=("catalog:fixture",),
    )


def _classification(privacy_class="public"):
    return TaskClassification(
        schema_version="1.0.0",
        classification_id="sha256:" + "1" * 64,
        classified_at="2026-07-23T13:00:00Z",
        classifier_version="fixture:1",
        taxonomy_version="taxonomy:1",
        input_ref="request:fixture",
        task_class="single_file_patch",
        task_family="code_patch",
        required_capabilities=("tools", "code_edit"),
        privacy_class=privacy_class,
        importance="high",
        confidence=0.9,
        decision_provenance=("classifier:fixture",),
    )


def _candidate(
    callable_id="openrouter:model-a",
    *,
    provider="openrouter",
    reachable=True,
    capabilities=frozenset({"tools", "code_edit"}),
    cost_class="free",
    cost=0.0,
    quality=0.8,
    quota=True,
):
    return CandidateEvidence(
        record=_record(
            callable_id,
            provider=provider,
            reachable=reachable,
        ),
        capability_ref=f"capability:{callable_id}",
        supported_capabilities=capabilities,
        cost_class=cost_class,
        expected_accepted_cost_usd=cost,
        quality_score=quality,
        quota_available=quota,
        quota_ref=f"quota:{callable_id}",
        evidence_refs=("catalog:fixture", "capability:fixture", "quota:fixture"),
    )


def _policy(**overrides):
    values = {
        "version": "policy:fixture",
        "allowed_provider_ids": frozenset({"openrouter", "anthropic"}),
        "funded_callable_ids": frozenset({"anthropic:paid-a"}),
        "allowed_cost_classes": frozenset({"free", "subscription", "metered"}),
        "blocked_callable_ids": frozenset(),
        "max_expected_accepted_cost_usd": 1.0,
        "allow_unknown_cost": False,
    }
    values.update(overrides)
    return SelectionPolicy(**values)


def test_public_free_candidate_is_eligible_with_full_reasons():
    result = select_candidates(
        _classification("public"),
        [_candidate()],
        _policy(),
    )
    assert result.outcome == "ranked"
    assert result.ranked[0].rank == 1
    assert "privacy:public-compatible" in result.ranked[0].eligibility_reasons
    assert result.excluded == ()


def test_proprietary_traffic_excludes_free_and_keeps_funded_paid():
    free = _candidate()
    paid = _candidate(
        "anthropic:paid-a",
        provider="anthropic",
        cost_class="subscription",
        cost=0.25,
    )
    result = select_candidates(
        _classification("proprietary"),
        [free, paid],
        _policy(),
    )
    assert [item.candidate.record.callable_id for item in result.ranked] == ["anthropic:paid-a"]
    assert result.excluded[0].reasons == ("privacy:proprietary-free-endpoint",)


def test_every_hard_filter_reason_is_retained_in_order():
    candidate = _candidate(
        "unfunded:bad",
        provider="unfunded",
        reachable=False,
        capabilities=frozenset(),
        cost_class="metered",
        cost=5.0,
        quota=False,
    )
    policy = _policy(
        allowed_cost_classes=frozenset({"free"}),
        blocked_callable_ids=frozenset({"unfunded:bad"}),
        funded_callable_ids=frozenset(),
        max_expected_accepted_cost_usd=1.0,
    )
    result = select_candidates(
        _classification("proprietary"),
        [candidate],
        policy,
    )
    assert result.excluded[0].reasons == (
        "provider:not-allowed",
        "cost-class:not-allowed:metered",
        "funding:not-confirmed",
        "capability:missing:code_edit",
        "capability:missing:tools",
        "reachability:not-confirmed",
        "blocklist:matched",
        "quota:unavailable",
        "cost:above-ceiling",
    )


@pytest.mark.parametrize(
    "candidate, reason",
    [
        (_candidate(quota=None), "quota:unknown"),
        (_candidate(cost=None), "cost:unknown"),
        (
            _candidate(capabilities=frozenset({"tools"})),
            "capability:missing:code_edit",
        ),
    ],
)
def test_unknown_or_missing_hard_facts_are_excluded(candidate, reason):
    result = select_candidates(_classification(), [candidate], _policy())
    assert reason in result.excluded[0].reasons


def test_unknown_cost_requires_explicit_policy_permission():
    candidate = _candidate(cost=None)
    result = select_candidates(
        _classification(),
        [candidate],
        _policy(allow_unknown_cost=True),
    )
    assert result.outcome == "ranked"
    assert "cost:unknown-explicitly-permitted" in result.ranked[0].eligibility_reasons


def test_empty_set_never_relaxes_a_filter():
    blocked = _candidate()
    result = select_candidates(
        _classification(),
        [blocked],
        _policy(blocked_callable_ids=frozenset({blocked.record.callable_id})),
    )
    assert result.outcome == "no-eligible-candidates"
    assert result.ranked == ()
    assert result.empty_set_reason == (
        "all candidates failed one or more hard filters; no filter was relaxed"
    )
    assert result.excluded[0].reasons == ("blocklist:matched",)


def test_rank_is_deterministic_by_cost_quality_then_callable_id():
    candidates = [
        _candidate("openrouter:c", cost=0.2, quality=0.99),
        _candidate("openrouter:b", cost=0.1, quality=0.7),
        _candidate("openrouter:a", cost=0.1, quality=0.7),
        _candidate("openrouter:d", cost=0.1, quality=0.9),
    ]
    expected = ["openrouter:d", "openrouter:a", "openrouter:b", "openrouter:c"]
    first = select_candidates(_classification(), candidates, _policy())
    second = select_candidates(_classification(), list(reversed(candidates)), _policy())
    assert [item.candidate.record.callable_id for item in first.ranked] == expected
    assert [item.candidate.record.callable_id for item in second.ranked] == expected


def test_duplicate_or_invalid_candidate_evidence_is_rejected():
    candidate = _candidate()
    with pytest.raises(CandidateSelectionRejected, match="duplicate"):
        select_candidates(
            _classification(),
            [candidate, candidate],
            _policy(),
        )
    with pytest.raises(CandidateSelectionRejected, match="quality_score"):
        select_candidates(
            _classification(),
            [replace(candidate, quality_score=1.1)],
            _policy(),
        )


def test_empty_policy_inventory_produces_explicit_empty_set():
    result = select_candidates(
        _classification(),
        [_candidate()],
        _policy(
            allowed_provider_ids=frozenset(),
            allowed_cost_classes=frozenset(),
        ),
    )
    assert result.outcome == "no-eligible-candidates"
    assert result.excluded[0].reasons == (
        "provider:not-allowed",
        "cost-class:not-allowed:free",
    )


def test_unknown_privacy_cannot_reach_selection():
    with pytest.raises(CandidateSelectionRejected, match="privacy"):
        select_candidates(
            _classification("unknown"),
            [_candidate()],
            _policy(),
        )
