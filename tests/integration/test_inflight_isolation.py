"""In-flight request isolation under concurrent config edits (T062, SC-006).

Per resolver.md invariant 5: a request that captures a config snapshot at
entry must keep using that snapshot for the duration of its work, even when
``set()`` mutates the resolver mid-flight.

The integration test uses the snapshot context plumbing directly (no FastAPI
overhead): it captures a snapshot, fires a concurrent ``set()``, then asserts
that resolves under the captured snapshot still see the pre-write value.
"""

from __future__ import annotations

import threading
import time

import pytest

from src.core.config_resolver import (
    ConfigLayer,
    ConfigResolver,
    FieldSchema,
    set_snapshot,
    reset_snapshot,
)


@pytest.fixture
def resolver_with_field() -> ConfigResolver:
    r = ConfigResolver()
    r._initialized = True  # bypass schema-discovery side effects
    r.register_schema("assignments.big.model", FieldSchema(type=str, default=""))
    r._layers[ConfigLayer.STORED]["assignments.big.model"] = "old-model"
    return r


def test_inflight_request_sees_pre_edit_value(resolver_with_field):
    """Snapshot captured before set() must keep returning the pre-edit value."""
    r = resolver_with_field
    snap = r.snapshot()
    token = set_snapshot(snap)
    try:
        # Mutate the resolver after snapshot capture
        r.set(
            "assignments.big.model",
            "new-model",
            ConfigLayer.STORED,
            principal="test",
        )
        # Within the snapshot context, reads still see the old value
        rv = r.resolve("assignments.big.model")
        assert rv.value == "old-model", (
            "in-flight request leaked post-edit value"
        )
        assert rv.source_layer == ConfigLayer.STORED
    finally:
        reset_snapshot(token)

    # Outside the snapshot context, reads see the new value
    rv = r.resolve("assignments.big.model")
    assert rv.value == "new-model"


def test_concurrent_inflight_isolation(resolver_with_field):
    """Two reader threads with their own snapshots keep their pre-write values
    even when a third thread mutates the resolver after the snapshots are taken.
    """
    r = resolver_with_field

    results: dict[str, str] = {}
    snapshots_ready = threading.Barrier(3)  # 2 readers + 1 writer
    write_done = threading.Event()

    def reader(tag: str):
        snap = r.snapshot()
        token = set_snapshot(snap)
        try:
            snapshots_ready.wait(timeout=2)
            assert write_done.wait(timeout=2), "writer never fired"
            rv = r.resolve("assignments.big.model")
            results[tag] = rv.value
        finally:
            reset_snapshot(token)

    def writer():
        snapshots_ready.wait(timeout=2)
        r.set(
            "assignments.big.model",
            "after-write",
            ConfigLayer.STORED,
            principal="test",
        )
        write_done.set()

    threads = [
        threading.Thread(target=reader, args=("reader1",)),
        threading.Thread(target=reader, args=("reader2",)),
        threading.Thread(target=writer),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    for t in threads:
        assert not t.is_alive(), "thread deadlocked"

    assert results["reader1"] == "old-model"
    assert results["reader2"] == "old-model"

    # New, post-write resolves observe the change
    new_rv = r.resolve("assignments.big.model")
    assert new_rv.value == "after-write"
