"""CG-T084 — typed skill pipelines: gates, branches, fan-out/in, repair, stop."""

from __future__ import annotations

import pytest

from src.services.orchestration.pipelines import (
    Finding,
    RESEARCH_SYNTHESIZE_CITE,
    REVIEW_FIX_VERIFY,
    REAL_PIPELINES,
)
from src.services.orchestration.skill_pipeline import (
    NodeSpec,
    PipelineError,
    PipelineRun,
    SkillPipeline,
    StopSignal,
    run_pipeline,
)


def test_review_fix_verify_completes_with_fan_out_fan_in():
    run = run_pipeline(
        REVIEW_FIX_VERIFY,
        [Finding("a.py", "defect", "off-by-one"), Finding("b.py", "style", "quote")],
    )
    assert run.status == "completed"
    assert set(run.outputs) == {
        "classify_findings",
        "fix_defects",
        "fix_style",
        "verify",
    }
    report = run.outputs["verify"]
    assert report.defects_closed and report.style_clean
    # fan-out produced two sibling branches; fan-in joined both into verify
    node_ids = [p.node_id for p in run.provenance]
    assert node_ids.count("verify") == 1
    assert "fix_defects" in node_ids and "fix_style" in node_ids
    # provenance covers every executed step with typed I/O
    for record in run.provenance:
        assert record.pipeline_id == "review-fix-verify"
        assert record.status in {"ok", "gate_failed", "stopped", "failed"}


def test_branch_predicates_are_deterministic_and_prune_empty_buckets():
    findings = [Finding("a.py", "defect", "x")]
    run_a = run_pipeline(REVIEW_FIX_VERIFY, list(findings))
    run_b = run_pipeline(REVIEW_FIX_VERIFY, list(findings))
    # same input -> same executed node set (no style work for style-less input)
    assert sorted(run_a.outputs) == sorted(run_b.outputs)
    assert "fix_style" not in run_a.outputs


def test_research_pipeline_produces_cited_brief():
    run = run_pipeline(RESEARCH_SYNTHESIZE_CITE, "quota precedence")
    assert run.status == "completed"
    brief = run.outputs["synthesize"]
    assert brief.claims and all(c.citation for c in brief.claims)
    assert brief.titles


def test_stop_signal_stops_the_pipeline_with_reason():
    run = run_pipeline(RESEARCH_SYNTHESIZE_CITE, "   ")
    assert run.status == "stopped"
    assert run.stopped_reason == "empty research query; nothing to gather"
    assert run.outputs == {}


def test_typed_inputs_are_enforced():
    with pytest.raises(PipelineError, match="expects"):
        run_pipeline(RESEARCH_SYNTHESIZE_CITE, 12345)


def test_unknown_branch_target_fails_closed():
    def branch(_):
        return ("nowhere",)

    pipeline = SkillPipeline(
        pipeline_id="bad-branch",
        entry="a",
        nodes=(
            NodeSpec("a", "str", "str", lambda v: v + "!", next_nodes=("b",), branch=branch),
            NodeSpec("b", "str", "str", lambda v: v),
        ),
    )
    run = run_pipeline(pipeline, "x")
    assert run.status == "failed"
    assert "non-successors" in run.stopped_reason


def test_node_gate_with_bounded_repair_then_success():
    calls = {"n": 0}

    def flaky(_: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "BAD"  # fails the gate on the first attempt
        return "GOOD"

    def gate(value: str) -> bool:
        return value == "GOOD"

    pipeline = SkillPipeline(
        pipeline_id="repair-one",
        entry="only",
        nodes=(
            NodeSpec(
                "only", "str", "str", flaky, gate=gate, repair=1,
            ),
        ),
    )
    run = run_pipeline(pipeline, "in")
    assert run.status == "completed"
    assert run.outputs["only"] == "GOOD"
    statuses = [p.status for p in run.provenance]
    assert statuses == ["gate_failed", "ok"]


def test_gate_failure_after_bounded_repair_stops_the_pipeline():
    def always_bad(_: str) -> str:
        return "BAD"

    pipeline = SkillPipeline(
        pipeline_id="repair-none",
        entry="only",
        nodes=(
            NodeSpec("only", "str", "str", always_bad, gate=lambda v: False, repair=1),
        ),
    )
    run = run_pipeline(pipeline, "in")
    assert run.status == "stopped"
    assert "gate failed after bounded repair" in run.stopped_reason


def test_type_mismatch_fails_the_run():
    pipeline = SkillPipeline(
        pipeline_id="bad-types",
        entry="a",
        nodes=(
            NodeSpec("a", "str", "list", lambda v: v),  # declares list, returns str
        ),
    )
    run = run_pipeline(pipeline, "x")
    assert run.status == "failed"
    assert "declared list" in run.stopped_reason


def test_both_real_pipelines_are_registered_and_valid():
    assert set(REAL_PIPELINES) == {"review-fix-verify", "research-synthesize-cite"}
    for pipeline in REAL_PIPELINES.values():
        nodes = pipeline.validate()
        assert pipeline.entry in nodes
        for node in nodes.values():
            assert node.input_type and node.output_type
            assert callable(node.run)
