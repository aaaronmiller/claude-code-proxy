"""CG-T086 — watchdog shadow mode: labeled fixtures, guards, no mutations."""

from __future__ import annotations

from src.services.orchestration.watchdog import (
    APPROVED_PRECISION,
    APPROVED_RECALL,
    WatchEvent,
    WatchdogState,
    evaluate_launch,
    labeled_fixtures,
    precision_recall_vector,
)


def test_labeled_fixtures_reach_the_approved_precision_recall_vector():
    vector = precision_recall_vector()
    assert vector["precision"] >= APPROVED_PRECISION
    assert vector["recall"] >= APPROVED_RECALL
    assert vector["approved"] is True
    # every labeled anomaly fires; the valid slow run does not
    per = vector["per_fixture"]
    for name in ("loop", "stall", "retry_storm", "churn"):
        assert per[name]["fired"] is True, name
    assert per["valid_slow_run"]["fired"] is False


def test_valid_slow_run_with_progress_is_never_an_anomaly():
    state = WatchdogState()
    events = labeled_fixtures()["valid_slow_run"]["events"]
    recs = evaluate_launch(list(events), "launch-fx", state)
    assert recs == []


def test_stall_requires_silence_and_no_outcome():
    state = WatchdogState()
    events = [
        WatchEvent("l1", 0, "tool", "edit", 0.0),
        WatchEvent("l1", 1, "outcome", "accepted", 4000.0),
    ]
    assert evaluate_launch(events, "l1", state, now_s=4000.0) == []


def test_cooldown_suppresses_repeat_recommendations():
    state = WatchdogState()
    events = [WatchEvent("l1", i, "tool", "grep", float(i)) for i in range(6)]
    first = evaluate_launch(events, "l1", state, now_s=10.0)
    assert first and first[0].rule == "loop"
    # same launch fires again immediately -> cooldown suppresses
    second = evaluate_launch(events, "l1", state, now_s=20.0)
    assert second == []
    # after the cooldown window the rule may fire again
    third = evaluate_launch(events, "l1", state, now_s=2000.0)
    assert third and third[0].rule == "loop"


def test_thrash_guard_caps_recommendations():
    state = WatchdogState()
    events = [WatchEvent("l1", i, "tool", f"grep{i}", float(i)) for i in range(6)]
    fired = 0
    for i in range(100):
        recs = evaluate_launch(events, f"launch-{i}", state, now_s=float(10_000 * i))
        fired += len(recs)
    assert fired <= state.fired_count
    assert state.fired_count < 100  # cap held


def test_shadow_mode_mutates_nothing():
    state = WatchdogState()
    events = labeled_fixtures()["loop"]["events"]
    before_last_fired = dict(state.last_fired)
    recs = evaluate_launch(list(events), "launch-fx", state)
    assert recs
    # the only state change is the watchdog's own cooldown bookkeeping
    assert set(state.last_fired) >= set(before_last_fired)
    vector = precision_recall_vector()
    assert vector["mutations"] == []

    # routing-adjacent runtime state is untouched by construction
    from src.core import model_scan_runtime

    binding_before = model_scan_runtime.get_active_binding()
    precision_recall_vector()
    assert model_scan_runtime.get_active_binding() is binding_before
