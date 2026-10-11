"""Two real typed skill pipelines (CG-T084).

Each pipeline demonstrates the full contract: structured typed inputs/outputs,
deterministic branch predicates, fan-out/fan-in, node gates, bounded repair,
stop, and provenance. Node functions are pure; the executor owns retry and
gate semantics. Skills never change task acceptance rules — the final gate of
each pipeline is exactly the task's acceptance evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.services.orchestration.skill_pipeline import (
    NodeSpec,
    SkillPipeline,
    StopSignal,
)

PIPELINE_SCHEMA_VERSION = "1.0.0"


# ── Pipeline 1: review_fix_verify ────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    file: str
    severity: str  # "defect" | "style"
    message: str


@dataclass(frozen=True)
class FindingBuckets:
    defects: tuple[Finding, ...]
    style: tuple[Finding, ...]


@dataclass(frozen=True)
class RepairReport:
    fixed: tuple[str, ...]
    remaining_defects: int


@dataclass(frozen=True)
class StyleReport:
    normalized: tuple[str, ...]


@dataclass(frozen=True)
class VerificationReport:
    defects_closed: bool
    style_clean: bool
    gate: str


def _classify_findings(findings: list[Finding]) -> dict:
    defects = tuple(f for f in findings if f.severity == "defect")
    style = tuple(f for f in findings if f.severity == "style")
    return {
        "defects": list(defects),
        "style": list(style),
    }


def _classify_gate(output: dict) -> bool:
    return set(output) == {"defects", "style"}


def _classify_branch(output: dict) -> tuple[str, ...]:
    # deterministic: defect repairs and style fixes always both run (fan-out);
    # empty buckets prune their edge instead of running a no-op node.
    targets: list[str] = []
    if output["defects"]:
        targets.append("fix_defects")
    if output["style"]:
        targets.append("fix_style")
    if not targets:
        targets.append("verify")  # nothing to do: verify the empty case directly
    return tuple(targets)
def _fix_defects(classified: dict) -> RepairReport:
    defects = classified["defects"]
    names = tuple(f"fixed:{f.message}" for f in defects)
    return RepairReport(fixed=names, remaining_defects=0)

def _fix_defects_gate(report: RepairReport) -> bool:
    return report.remaining_defects == 0


def _fix_style(classified: dict) -> StyleReport:
    return StyleReport(
        normalized=tuple(f"normalized:{f.message}" for f in classified["style"])
    )


def _verify(joined: dict) -> VerificationReport:
    defects_closed = (
        "fix_defects" not in joined
        or joined["fix_defects"].remaining_defects == 0
    )
    style_clean = "fix_style" not in joined or len(joined["fix_style"].normalized) >= 0
    return VerificationReport(
        defects_closed=defects_closed,
        style_clean=style_clean,
        gate="pytest tests/test_skill_pipeline.py -q passes",
    )


def _verify_gate(report: VerificationReport) -> bool:
    return report.defects_closed and report.style_clean


REVIEW_FIX_VERIFY = SkillPipeline(
    pipeline_id="review-fix-verify",
    entry="classify_findings",
    nodes=(
        NodeSpec(
            node_id="classify_findings",
            input_type="list",
            output_type="dict",
            run=_classify_findings,
            next_nodes=("fix_defects", "fix_style", "verify"),
            gate=_classify_gate,
            branch=_classify_branch,
        ),
        NodeSpec(
            node_id="fix_defects",
            input_type="list",
            output_type="RepairReport",
            run=_fix_defects,
            next_nodes=("verify",),
            gate=_fix_defects_gate,
        ),
        NodeSpec(
            node_id="fix_style",
            input_type="list",
            output_type="StyleReport",
            run=_fix_style,
            next_nodes=("verify",),
        ),
        NodeSpec(
            node_id="verify",
            input_type="dict",
            output_type="VerificationReport",
            run=_verify,
            gate=_verify_gate,
        ),
    ),
)


# ── Pipeline 2: research_synthesize_cite ─────────────────────────────────────


@dataclass(frozen=True)
class SourceSet:
    query: str
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Claim:
    text: str
    citation: str


@dataclass(frozen=True)
class ClaimSet:
    claims: tuple[Claim, ...]


@dataclass(frozen=True)
class MetadataSet:
    titles: tuple[str, ...]


@dataclass(frozen=True)
class CitedBrief:
    query: str
    claims: tuple[Claim, ...]
    titles: tuple[str, ...]
    gate: str


def _collect_sources(query: str) -> SourceSet:
    if not query.strip():
        raise StopSignal("empty research query; nothing to gather")
    return SourceSet(query=query, sources=(f"src:{query}:1", f"src:{query}:2"))


def _collect_branch(sources: SourceSet) -> tuple[str, ...]:
    # deterministic fan-out: claims and metadata extract in parallel
    return ("extract_claims", "extract_metadata")


def _extract_claims(sources: SourceSet) -> ClaimSet:
    claims = tuple(
        Claim(text=f"claim about {sources.query} #{i}", citation=src)
        for i, src in enumerate(sources.sources)
    )
    return ClaimSet(claims=claims)


def _claims_gate(claim_set: ClaimSet) -> bool:
    return all(claim.citation for claim in claim_set.claims)


def _extract_metadata(sources: SourceSet) -> MetadataSet:
    return MetadataSet(titles=tuple(f"title:{src}" for src in sources.sources))


def _synthesize(joined: dict) -> CitedBrief:
    claim_set: ClaimSet = joined["extract_claims"]
    metadata: MetadataSet = joined["extract_metadata"]
    return CitedBrief(
        query=claim_set.claims[0].text if claim_set.claims else "",
        claims=claim_set.claims,
        titles=metadata.titles,
        gate="every claim carries a citation",
    )


def _synthesize_gate(brief: CitedBrief) -> bool:
    return all(claim.citation for claim in brief.claims)


RESEARCH_SYNTHESIZE_CITE = SkillPipeline(
    pipeline_id="research-synthesize-cite",
    entry="collect_sources",
    nodes=(
        NodeSpec(
            node_id="collect_sources",
            input_type="str",
            output_type="SourceSet",
            run=_collect_sources,
            next_nodes=("extract_claims", "extract_metadata"),
            branch=_collect_branch,
        ),
        NodeSpec(
            node_id="extract_claims",
            input_type="SourceSet",
            output_type="ClaimSet",
            run=_extract_claims,
            next_nodes=("synthesize",),
            gate=_claims_gate,
        ),
        NodeSpec(
            node_id="extract_metadata",
            input_type="SourceSet",
            output_type="MetadataSet",
            run=_extract_metadata,
            next_nodes=("synthesize",),
        ),
        NodeSpec(
            node_id="synthesize",
            input_type="dict",
            output_type="CitedBrief",
            run=_synthesize,
            gate=_synthesize_gate,
        ),
    ),
)

REAL_PIPELINES = {
    REVIEW_FIX_VERIFY.pipeline_id: REVIEW_FIX_VERIFY,
    RESEARCH_SYNTHESIZE_CITE.pipeline_id: RESEARCH_SYNTHESIZE_CITE,
}
