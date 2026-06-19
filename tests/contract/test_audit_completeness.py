"""Adversarial test: audit log completeness under concurrent writes (SC-011).

We simulate multiple threads performing config writes simultaneously and
verify that every successful write produces exactly one audit entry, with
no successful write missing and no failed write recorded as successful.

Requires: pytest, threading
"""

import json
import os
import threading
import time
from pathlib import Path

import pytest

from src.core.config_resolver import get_resolver
from src.services.observability.audit_log import append_audit, mask_secret

# Use a test-specific audit log to avoid polluting production log
TEST_AUDIT_LOG = Path("logs/test-audit-completeness.log")


@pytest.fixture(autouse=True)
def isolate_audit_log(tmp_path, monkeypatch):
    """Redirect audit log to a temp file for each test."""
    test_log = tmp_path / "config-audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(test_log))  # if supported
    # Patch the log_file path in audit_log module
    import src.services.observability.audit_log as audit_mod

    original_append = audit_mod.append_audit

    def patched_append(*args, **kwargs):
        # temporarily change log_file
        old_log_file = audit_mod.log_file if hasattr(audit_mod, "log_file") else None
        audit_mod.log_file = test_log
        try:
            return original_append(*args, **kwargs)
        finally:
            audit_mod.log_file = old_log_file

    monkeypatch.setattr(audit_mod, "append_audit", patched_append)
    yield test_log
    # cleanup automatic via tmp_path


def test_audit_log_append_basic(tmp_path):
    """Sanity: one append produces one line with required fields."""
    log_file = tmp_path / "config-audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Directly call append_audit
    from src.services.observability.audit_log import append_audit

    append_audit(
        principal="tester",
        surface="stored",
        endpoint="test.endpoint",
        field_path="assignments.big.model",
        before_value="old-model",
        after_value="new-model",
        client_ip="127.0.0.1",
    )

    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["principal"] == "tester"
    assert entry["surface"] == "stored"
    assert entry["field_path"] == "assignments.big.model"
    assert entry["before_value"] == "old-model"
    assert entry["after_value"] == "new-model"
    assert "timestamp" in entry
    assert "seq" in entry


def test_concurrent_writes_all_appear(tmp_path):
    """Multiple threads writing concurrently: all entries present, no lost writes."""
    log_file = tmp_path / "config-audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    from src.services.observability.audit_log import append_audit

    num_threads = 10
    writes_per_thread = 20
    barrier = threading.Barrier(num_threads)

    def worker(thread_id: int):
        # Wait for all threads to be ready, then burst writes
        barrier.wait()
        for i in range(writes_per_thread):
            append_audit(
                principal=f"user{thread_id}",
                surface="stored",
                endpoint="test.concurrent",
                field_path=f"assignments.slot{thread_id}.model",
                before_value="old",
                after_value=f"new{i}",
                client_ip=None,
            )

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = log_file.read_text().strip().splitlines()
    expected = num_threads * writes_per_thread
    assert len(lines) == expected, (
        f"Expected {expected} audit entries, got {len(lines)}"
    )

    # Spot-check: each thread's last write should be present
    last_seq_per_thread = {}
    for line in lines:
        e = json.loads(line)
        tid = int(e["principal"][4:])  # from "userX"
        seq = e["seq"]
        last_seq_per_thread[tid] = max(last_seq_per_thread.get(tid, 0), seq)

    # All threads should have written at least one entry
    assert len(last_seq_per_thread) == num_threads


def test_failed_write_not_recorded(tmp_path):
    """If append_audit raises (e.g., permission error), no partial entry is written."""
    log_file = tmp_path / "config-audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Simulate failure by making directory read-only after first write? Hard.
    # Instead, we can directly test that malformed data doesn't crash, but
    # the spec says no failed write is recorded as successful. append_audit
    # catches all exceptions and discards. So write zero entries after an error.
    from src.services.observability.audit_log import append_audit

    # First, a normal write
    append_audit("user", "stored", "test", "field", "old", "new")
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1

    # Force an exception inside append_audit by monkeypatching open to raise
    import builtins

    original_open = builtins.open

    def failing_open(*args, **kwargs):
        raise OSError("simulated disk full")

    builtins.open = failing_open
    try:
        # This should not write a line
        append_audit("user", "stored", "test", "field2", "old2", "new2")
    except Exception:
        pass
    finally:
        builtins.open = original_open

    # Should still only have the first line
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1, "No audit entry should be written after a failure"


def test_seq_is_monotonic(tmp_path):
    """Sequence numbers increase monotonically across calls."""
    log_file = tmp_path / "config-audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    from src.services.observability.audit_log import append_audit

    seqs = []
    for i in range(5):
        append_audit(f"user{i}", "stored", "test", f"field{i}", "old", "new")
        # We can't directly read seq from file, but we can read back entry
    lines = log_file.read_text().splitlines()
    seqs = [json.loads(l)["seq"] for l in lines]
    assert seqs == sorted(seqs)
    # Also consecutively increasing by 1 each time (monotonic + contiguous)
    for i in range(1, len(seqs)):
        assert seqs[i] == seqs[i - 1] + 1
