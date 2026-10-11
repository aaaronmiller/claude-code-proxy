"""Typed skill pipelines with gates, bounded repair, and provenance (CG-T084).

Nodes are typed (declared structured input/output), edges are static, branch
predicates are pure functions of a node's typed output choosing among its
static successors, fan-out is a branch returning several successors, fan-in is
a node typed to receive a dict of all its producers' outputs, every node can
carry a gate, repair is bounded, and a run can stop explicitly. Every executed
step appends a provenance record. Skills cannot change task safety or
acceptance rules: the executor never mutates routing, quota, or persistent
configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

PIPELINE_SCHEMA_VERSION = "1.0.0"


class PipelineError(ValueError):
    """Raised when a pipeline structure violates the contract."""


class StopSignal(Exception):
    """Raised by a node to stop the pipeline with an explicit reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class NodeFailed(RuntimeError):
    """Raised internally when a node exhausts repair or fails its gate."""


@dataclass(frozen=True)
class NodeSpec:
    """One typed pipeline node with static edges and optional gate/branch."""

    node_id: str
    input_type: str          # declared structured input type name ("dict" = fan-in)
    output_type: str
    run: Callable[[Any], Any]
    next_nodes: tuple[str, ...] = ()
    gate: Callable[[Any], bool] | None = None
    branch: Callable[[Any], tuple[str, ...]] | None = None
    repair: int = 0          # bounded repair attempts before the node fails

    def validate(self, nodes: Mapping[str, "NodeSpec"]) -> None:
        if not self.node_id:
            raise PipelineError("node requires an id")
        if not self.input_type or not self.output_type:
            raise PipelineError(f"node {self.node_id} must declare typed I/O")
        if not callable(self.run):
            raise PipelineError(f"node {self.node_id} requires a run function")
        for target in self.next_nodes:
            if target not in nodes:
                raise PipelineError(
                    f"node {self.node_id} targets unknown node {target!r}"
                )


@dataclass(frozen=True)
class SkillPipeline:
    """A typed DAG with an entry node and static edges."""

    pipeline_id: str
    entry: str
    nodes: tuple[NodeSpec, ...]
    schema_version: str = PIPELINE_SCHEMA_VERSION

    def validate(self) -> dict[str, NodeSpec]:
        if self.schema_version != PIPELINE_SCHEMA_VERSION:
            raise PipelineError("pipeline schema version drift")
        nodes = {node.node_id: node for node in self.nodes}
        if not nodes:
            raise PipelineError("pipeline requires nodes")
        if self.entry not in nodes:
            raise PipelineError(f"entry {self.entry!r} is not a node")
        if len(nodes) != len(self.nodes):
            raise PipelineError("pipeline node ids must be unique")
        for node in self.nodes:
            node.validate(nodes)
        return nodes


@dataclass(frozen=True)
class ProvenanceRecord:
    pipeline_id: str
    node_id: str
    attempt: int
    input_type: str
    output_type: str
    status: str  # "ok" | "gate_failed" | "stopped" | "failed"
    detail: str = ""


@dataclass
class PipelineRun:
    pipeline_id: str
    status: str  # "completed" | "stopped" | "failed"
    outputs: dict[str, Any] = field(default_factory=dict)
    provenance: list[ProvenanceRecord] = field(default_factory=list)
    stopped_reason: str = ""


def _type_name(value: Any) -> str:
    if isinstance(value, Mapping):
        return "dict"
    if isinstance(value, (list, tuple)):
        return "list"
    return type(value).__name__


def _execute_node(
    pipeline: SkillPipeline,
    node: NodeSpec,
    value: Any,
    run: PipelineRun,
) -> Any:
    """Run one node honoring type checks, gates, bounded repair, and stop."""
    attempt = 0
    while True:
        attempt += 1
        try:
            output = node.run(value)
        except StopSignal as stop:
            run.status = "stopped"
            run.stopped_reason = stop.reason
            run.provenance.append(
                ProvenanceRecord(
                    pipeline.pipeline_id, node.node_id, attempt,
                    node.input_type, node.output_type, "stopped", stop.reason,
                )
            )
            raise
        except Exception as exc:
            if attempt <= node.repair:
                continue
            run.status = "failed"
            run.stopped_reason = f"node {node.node_id} failed: {exc}"
            run.provenance.append(
                ProvenanceRecord(
                    pipeline.pipeline_id, node.node_id, attempt,
                    node.input_type, node.output_type, "failed", str(exc),
                )
            )
            raise

        produced = _type_name(output)
        if produced != node.output_type:
            if attempt <= node.repair:
                continue
            run.status = "failed"
            run.stopped_reason = (
                f"node {node.node_id} produced {produced}, declared {node.output_type}"
            )
            run.provenance.append(
                ProvenanceRecord(
                    pipeline.pipeline_id, node.node_id, attempt,
                    node.input_type, node.output_type, "failed",
                    run.stopped_reason,
                )
            )
            raise NodeFailed(run.stopped_reason)

        if node.gate is not None and not node.gate(output):
            if attempt <= node.repair:
                run.provenance.append(
                    ProvenanceRecord(
                        pipeline.pipeline_id, node.node_id, attempt,
                        node.input_type, node.output_type, "gate_failed",
                        "gate rejected output; bounded repair applies",
                    )
                )
                continue
            run.status = "stopped"
            run.stopped_reason = (
                f"node {node.node_id} gate failed after bounded repair"
            )
            run.provenance.append(
                ProvenanceRecord(
                    pipeline.pipeline_id, node.node_id, attempt,
                    node.input_type, node.output_type, "stopped",
                    "gate failed after bounded repair",
                )
            )
            raise NodeFailed(run.stopped_reason)

        run.provenance.append(
            ProvenanceRecord(
                pipeline.pipeline_id, node.node_id, attempt,
                node.input_type, node.output_type, "ok",
            )
        )
        return output


def run_pipeline(
    pipeline: SkillPipeline,
    inputs: Any,
    *,
    max_steps: int = 100,
) -> PipelineRun:
    """Execute a pipeline with typed I/O, gates, branching, fan-out/fan-in."""
    nodes = pipeline.validate()
    run = PipelineRun(pipeline_id=pipeline.pipeline_id, status="completed")
    entry = nodes[pipeline.entry]
    if _type_name(inputs) != entry.input_type:
        raise PipelineError(
            f"entry node {entry.node_id} expects {entry.input_type}, "
            f"got {_type_name(inputs)}"
        )
    # structural rule: a dict-typed node is a fan-in join and is fired only
    # through the producer-decided mechanism, never by a plain edge.
    producers: dict[str, list[str]] = {}
    for node in nodes.values():
        for target in node.next_nodes:
            producers.setdefault(target, []).append(node.node_id)
    for target, producer_ids in producers.items():
        if len(producer_ids) > 1 and nodes[target].input_type != "dict":
            raise PipelineError(
                f"node {target} has {len(producer_ids)} producers; "
                "multi-producer targets must be dict-typed fan-in nodes"
            )

    completed: dict[str, Any] = {}
    excluded_edges: set[tuple[str, str]] = set()
    queued: set[str] = set()
    ready: list[tuple[str, Any]] = [(pipeline.entry, inputs)]
    steps = 0

    def _fire_successors(node: NodeSpec, output: Any) -> None:
        if node.branch is not None:
            chosen = node.branch(output)
            if isinstance(chosen, str):
                chosen = (chosen,)
            chosen = tuple(chosen)
            unknown = [t for t in chosen if t not in node.next_nodes]
            if unknown:
                run.status = "failed"
                run.stopped_reason = (
                    f"node {node.node_id} branch returned non-successors {unknown}"
                )
                return
            for target in node.next_nodes:
                if target not in chosen:
                    excluded_edges.add((node.node_id, target))
            for target in chosen:
                ready.append((target, output))
                queued.add(target)
        else:
            for target in node.next_nodes:
                if nodes[target].input_type == "dict":
                    excluded_edges.discard((node.node_id, target))
                    continue  # fan-in join waits for the producer mechanism
                ready.append((target, output))
                queued.add(target)

    while ready:
        if steps >= max_steps:
            run.status = "stopped"
            run.stopped_reason = f"max_steps={max_steps} exceeded"
            run.provenance.append(
                ProvenanceRecord(
                    pipeline.pipeline_id, "", 0, "", "", "stopped",
                    run.stopped_reason,
                )
            )
            return run
        steps += 1
        node_id, value = ready.pop(0)
        queued.discard(node_id)
        node = nodes[node_id]
        try:
            output = _execute_node(pipeline, node, value, run)
        except StopSignal:
            return run
        except NodeFailed:
            return run
        completed[node_id] = output
        run.outputs[node_id] = output
        _fire_successors(node, output)
        if run.status != "completed":
            return run

        # fire fan-in joins whose producers have all decided
        for candidate_id, producer_ids in producers.items():
            if candidate_id in completed or candidate_id in queued:
                continue
            if nodes[candidate_id].input_type != "dict":
                continue
            taken = [
                p for p in producer_ids
                if (p, candidate_id) not in excluded_edges
            ]
            if not taken:
                continue
            if all(
                (p in completed) or ((p, candidate_id) in excluded_edges)
                for p in producer_ids
            ):
                joined = {p: completed[p] for p in taken}
                ready.append((candidate_id, joined))
                queued.add(candidate_id)

    return run
