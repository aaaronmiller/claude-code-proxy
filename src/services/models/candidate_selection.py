"""Pure hard-filter and deterministic ranking for exact callable evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.services.models.callable_catalog import CallableRecord
from src.services.models.task_classification import TaskClassification

VALID_COST_CLASSES = frozenset({"free", "subscription", "metered"})


class CandidateSelectionRejected(ValueError):
    """Raised when selection inputs are internally inconsistent."""


@dataclass(frozen=True)
class CandidateEvidence:
    record: CallableRecord
    capability_ref: str
    supported_capabilities: frozenset[str]
    cost_class: str
    expected_accepted_cost_usd: float | None
    quality_score: float
    quota_available: bool | None
    quota_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SelectionPolicy:
    version: str
    allowed_provider_ids: frozenset[str]
    funded_callable_ids: frozenset[str]
    allowed_cost_classes: frozenset[str]
    blocked_callable_ids: frozenset[str]
    max_expected_accepted_cost_usd: float | None
    allow_unknown_cost: bool


@dataclass(frozen=True)
class RankedCandidate:
    rank: int
    candidate: CandidateEvidence
    eligibility_reasons: tuple[str, ...]


@dataclass(frozen=True)
class CandidateExclusion:
    callable_id: str
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SelectionResult:
    classification_id: str
    policy_version: str
    outcome: str
    ranked: tuple[RankedCandidate, ...]
    excluded: tuple[CandidateExclusion, ...]
    empty_set_reason: str | None


def _validate_policy(policy: SelectionPolicy) -> None:
    if not policy.version:
        raise CandidateSelectionRejected("policy version is required")
    unknown_cost_classes = policy.allowed_cost_classes - VALID_COST_CLASSES
    if unknown_cost_classes:
        raise CandidateSelectionRejected(f"unknown cost classes: {sorted(unknown_cost_classes)}")
    if (
        policy.max_expected_accepted_cost_usd is not None
        and policy.max_expected_accepted_cost_usd < 0
    ):
        raise CandidateSelectionRejected("cost ceiling cannot be negative")


def _validate_classification(classification: TaskClassification) -> None:
    if classification.privacy_class not in {"public", "proprietary"}:
        raise CandidateSelectionRejected(
            "classification privacy must be explicit public or proprietary"
        )
    if not classification.classification_id:
        raise CandidateSelectionRejected("classification identity is required")
    if not classification.required_capabilities:
        raise CandidateSelectionRejected("required capabilities cannot be empty")


def _validate_candidate(candidate: CandidateEvidence) -> None:
    if candidate.cost_class not in VALID_COST_CLASSES:
        raise CandidateSelectionRejected(f"unknown candidate cost class {candidate.cost_class}")
    if (
        candidate.expected_accepted_cost_usd is not None
        and candidate.expected_accepted_cost_usd < 0
    ):
        raise CandidateSelectionRejected("candidate cost cannot be negative")
    if not 0 <= candidate.quality_score <= 1:
        raise CandidateSelectionRejected("quality_score must be between 0 and 1")
    if not candidate.capability_ref or not candidate.quota_ref:
        raise CandidateSelectionRejected("capability_ref and quota_ref are required")
    if not candidate.evidence_refs:
        raise CandidateSelectionRejected("candidate evidence is required")


def _hard_filter_reasons(
    classification: TaskClassification,
    candidate: CandidateEvidence,
    policy: SelectionPolicy,
) -> list[str]:
    reasons: list[str] = []
    record = candidate.record

    if classification.privacy_class == "proprietary" and candidate.cost_class == "free":
        reasons.append("privacy:proprietary-free-endpoint")
    if record.provider_id not in policy.allowed_provider_ids:
        reasons.append("provider:not-allowed")
    if candidate.cost_class not in policy.allowed_cost_classes:
        reasons.append(f"cost-class:not-allowed:{candidate.cost_class}")
    if (
        candidate.cost_class in {"subscription", "metered"}
        and record.callable_id not in policy.funded_callable_ids
    ):
        reasons.append("funding:not-confirmed")

    missing_capabilities = sorted(
        set(classification.required_capabilities) - candidate.supported_capabilities
    )
    reasons.extend(f"capability:missing:{capability}" for capability in missing_capabilities)

    if not record.reachable:
        reasons.append("reachability:not-confirmed")
    if record.callable_id in policy.blocked_callable_ids:
        reasons.append("blocklist:matched")
    if candidate.quota_available is False:
        reasons.append("quota:unavailable")
    elif candidate.quota_available is None:
        reasons.append("quota:unknown")

    cost = candidate.expected_accepted_cost_usd
    if cost is None and not policy.allow_unknown_cost:
        reasons.append("cost:unknown")
    if (
        cost is not None
        and policy.max_expected_accepted_cost_usd is not None
        and cost > policy.max_expected_accepted_cost_usd
    ):
        reasons.append("cost:above-ceiling")
    return reasons


def _eligibility_reasons(
    classification: TaskClassification,
    candidate: CandidateEvidence,
) -> tuple[str, ...]:
    if candidate.cost_class == "free":
        funding_reason = "funding:not-required-free"
    else:
        funding_reason = "funding:confirmed"
    if candidate.expected_accepted_cost_usd is None:
        cost_reason = "cost:unknown-explicitly-permitted"
    else:
        cost_reason = "cost:known-within-policy"
    return (
        f"privacy:{classification.privacy_class}-compatible",
        "provider:allowed",
        funding_reason,
        "capabilities:satisfied",
        "reachability:confirmed",
        "blocklist:clear",
        "quota:available",
        cost_reason,
    )


def _rank_key(candidate: CandidateEvidence) -> tuple[float, float, str]:
    cost = candidate.expected_accepted_cost_usd
    sortable_cost = float("inf") if cost is None else cost
    return (
        sortable_cost,
        -candidate.quality_score,
        candidate.record.callable_id,
    )


def select_candidates(
    classification: TaskClassification,
    candidates: Iterable[CandidateEvidence],
    policy: SelectionPolicy,
) -> SelectionResult:
    """Apply every hard filter before ranking; never relax an empty set."""
    _validate_policy(policy)
    _validate_classification(classification)
    candidate_list = list(candidates)
    callable_ids = [candidate.record.callable_id for candidate in candidate_list]
    if len(callable_ids) != len(set(callable_ids)):
        raise CandidateSelectionRejected("duplicate callable candidates")

    eligible: list[CandidateEvidence] = []
    excluded: list[CandidateExclusion] = []
    for candidate in candidate_list:
        _validate_candidate(candidate)
        reasons = _hard_filter_reasons(classification, candidate, policy)
        if reasons:
            excluded.append(
                CandidateExclusion(
                    callable_id=candidate.record.callable_id,
                    reasons=tuple(reasons),
                    evidence_refs=candidate.evidence_refs,
                )
            )
        else:
            eligible.append(candidate)

    ranked = tuple(
        RankedCandidate(rank, candidate, _eligibility_reasons(classification, candidate))
        for rank, candidate in enumerate(sorted(eligible, key=_rank_key), start=1)
    )
    if ranked:
        outcome = "ranked"
        empty_set_reason = None
    else:
        outcome = "no-eligible-candidates"
        empty_set_reason = "all candidates failed one or more hard filters; no filter was relaxed"
    return SelectionResult(
        classification_id=classification.classification_id,
        policy_version=policy.version,
        outcome=outcome,
        ranked=ranked,
        excluded=tuple(excluded),
        empty_set_reason=empty_set_reason,
    )
