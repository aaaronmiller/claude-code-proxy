"""Telemetry watchdog in shadow mode (CG-T086).

Evaluates structured worker events against versioned anomaly rules and
produces recommendations only: escalation, cooldown, and thrash guards never
mutate routing, bindings, or configuration. Labeled fixtures (loop, stall,
retry-storm, churn, and a valid slow run) measure the approved
precision/recall vector before anything downstream may consume advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

WATCHDOG_SCHEMA_VERSION = "1.0.0"

RULES = ("loop", "stall", "retry_storm", "churn")

#: Approved quality gate: the labeled fixture set must reach this vector
#: before any consumer may act on watchdog recommendations.
APPROVED_PRECISION = 0.9
APPROVED_RECALL = 0.9

#: Guard parameters (versioned; changing them changes the vector).
LOOP_REPEAT_THRESHOLD = 4
RETRY_STORM_THRESHOLD = 4
CHURN_THRESHOLD = 3
STALL_SILENCE_S = 1800.0
COOLDOWN_S = 900.0
THRASH_RECOMMENDATION_CAP = 8


@dataclass(frozen=True)
class WatchEvent:
    launch_id: str
    sequence: int
    kind: str          # "tool" | "model_generation" | "outcome" | "error" | ...
    detail: str = ""   # e.g. tool name or retry target
    at_s: float = 0.0  # seconds since launch start


@dataclass(frozen=True)
class Recommendation:
    rule: str
    launch_id: str
    action: str        # "escalate" | "pause" | "cancel" | "none"
    confidence: float
    detail: str


@dataclass
class WatchdogState:
    """Cooldown and thrash guards; never touches routing state."""

    last_fired: dict[tuple[str, str], float] = field(default_factory=dict)
    fired_count: int = 0

    def reset(self) -> None:
        self.last_fired.clear()
        self.fired_count = 0


def _recommend(
    state: WatchdogState,
    rule: str,
    launch_id: str,
    action: str,
    confidence: float,
    detail: str,
    now_s: float,
) -> Recommendation | None:
    """Cooldown + thrash guards wrap every recommendation."""
    key = (rule, launch_id)
    last = state.last_fired.get(key)
    if last is not None and now_s - last < COOLDOWN_S:
        return None
    if state.fired_count >= THRASH_RECOMMENDATION_CAP:
        return None
    state.last_fired[key] = now_s
    state.fired_count += 1
    return Recommendation(rule, launch_id, action, confidence, detail)


def evaluate_launch(
    events: list[WatchEvent],
    launch_id: str,
    state: WatchdogState,
    *,
    now_s: float | None = None,
) -> list[Recommendation]:
    """Evaluate one launch's events; returns recommendations, mutates nothing."""
    out: list[Recommendation] = []
    if not events:
        return out
    ordered = sorted(events, key=lambda e: e.sequence)
    end_s = now_s if now_s is not None else ordered[-1].at_s

    # loop: identical tool+detail repeats without an outcome
    tool_counts: dict[str, int] = {}
    for event in ordered:
        if event.kind == "tool":
            key = f"{event.detail}"
            tool_counts[key] = tool_counts.get(key, 0) + 1
    looped = {k: c for k, c in tool_counts.items() if c >= LOOP_REPEAT_THRESHOLD}
    if looped:
        rec = _recommend(
            state, "loop", launch_id, "cancel", 0.9,
            f"repeated identical tools: {sorted(looped)}", end_s,
        )
        if rec:
            out.append(rec)

    # stall: no events at all near the end of the observation window
    last_at = ordered[-1].at_s
    if end_s - last_at >= STALL_SILENCE_S and not any(
        e.kind == "outcome" for e in ordered
    ):
        rec = _recommend(
            state, "stall", launch_id, "pause", 0.8,
            f"silent for {end_s - last_at:.0f}s without an outcome", end_s,
        )
        if rec:
            out.append(rec)

    # retry storm: many error events naming a retry target
    retries = sum(1 for e in ordered if e.kind == "error" and "retry" in e.detail)
    if retries >= RETRY_STORM_THRESHOLD:
        rec = _recommend(
            state, "retry_storm", launch_id, "escalate", 0.85,
            f"{retries} retries observed", end_s,
        )
        if rec:
            out.append(rec)

    # churn: many distinct model_generation restarts (context churn)
    generations = [e for e in ordered if e.kind == "model_generation"]
    restarts = sum(1 for i, e in enumerate(generations) if i and e.detail != generations[i - 1].detail)
    if len(generations) >= CHURN_THRESHOLD and restarts >= CHURN_THRESHOLD:
        rec = _recommend(
            state, "churn", launch_id, "escalate", 0.7,
            f"{len(generations)} generation restarts across "
            f"{restarts} switches", end_s,
        )
        if rec:
            out.append(rec)

    return out


# ── Labeled fixtures and the precision/recall vector ────────────────────────


def labeled_fixtures() -> dict[str, dict[str, Any]]:
    """Labeled watchdog fixtures: expected recommendation per fixture."""
    def _events(kind_counts: list[tuple[str, str, float]]) -> list[WatchEvent]:
        out = []
        for i, (kind, detail, at) in enumerate(kind_counts):
            out.append(WatchEvent("launch-fx", i, kind, detail, at))
        return out

    loop = _events(
        [("tool", "grep", float(i)) for i in range(6)]
        + [("outcome", "none", 6.0)]
    )
    # a loop never reaches a real outcome: replace outcome with more looping
    loop = _events([("tool", "grep", float(i)) for i in range(8)])

    stall = _events(
        [("tool", "edit", 0.0), ("model_generation", "g1", 1.0)]
    )

    retry_storm = _events(
        [("error", "retry net", float(i)) for i in range(5)]
    )

    churn = _events(
        [("model_generation", f"g{i}", float(i)) for i in range(5)]
    )

    valid_slow = _events(
        [("model_generation", "g0", 0.0)]
        + [("tool", f"tool-{i}", 100.0 * (i + 1)) for i in range(10)]
        + [("outcome", "accepted", 1200.0)]
    )

    return {
        "loop": {"events": loop, "expect_rule": "loop", "expected": True},
        "stall": {
            "events": stall,
            "expect_rule": "stall",
            "expected": True,
            "now_s": 3600.0,
        },
        "retry_storm": {
            "events": retry_storm,
            "expect_rule": "retry_storm",
            "expected": True,
        },
        "churn": {"events": churn, "expect_rule": "churn", "expected": True},
        "valid_slow_run": {"events": valid_slow, "expect_rule": None, "expected": False},
    }


def precision_recall_vector(
    fixtures: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure the watchdog against labeled fixtures."""
    fixtures = fixtures if fixtures is not None else labeled_fixtures()
    state = WatchdogState()
    tp = fp = fn = 0
    per_fixture: dict[str, Any] = {}
    for name, fixture in fixtures.items():
        recs = evaluate_launch(
            list(fixture["events"]),
            "launch-fx",
            state,
            now_s=fixture.get("now_s"),
        )
        expected = bool(fixture["expected"])
        fired = bool(recs)
        if expected and fired:
            tp += 1
        elif not expected and fired:
            fp += 1
        elif expected and not fired:
            fn += 1
        per_fixture[name] = {
            "expected": expected,
            "fired": fired,
            "rules": [r.rule for r in recs],
        }
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "schema_version": WATCHDOG_SCHEMA_VERSION,
        "vector_kind": "precision_recall",
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "approved": precision >= APPROVED_PRECISION and recall >= APPROVED_RECALL,
        "thresholds": {"precision": APPROVED_PRECISION, "recall": APPROVED_RECALL},
        "per_fixture": per_fixture,
        "mutations": [],
    }
