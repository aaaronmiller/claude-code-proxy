from __future__ import annotations

import json
import logging
import sqlite3


def test_error_sink_appends_jsonl(monkeypatch, tmp_path):
    from src.services.observability import error_sink

    target = tmp_path / "errors.jsonl"
    monkeypatch.setattr(error_sink, "ERRORS_FILE", target)

    row = error_sink.emit_error(
        "boom",
        tool="codex",
        provider="openrouter",
        session_id="session-a",
        model="openrouter/m",
        request_id="rid",
    )

    loaded = json.loads(target.read_text())
    assert loaded["message"] == "boom"
    assert loaded["tool"] == "codex"
    assert row["session_id"] == "session-a"


def test_session_logging_filter_uses_active_profile():
    from src.core.logging import SessionContextFilter
    from src.core.profiles import ACTIVE_PROFILE, ProfileContext

    record = logging.LogRecord("x", logging.INFO, __file__, 1, "msg", (), None)
    token = ACTIVE_PROFILE.set(ProfileContext(name="ephemeral-1", slots={}))
    try:
        assert SessionContextFilter().filter(record) is True
    finally:
        ACTIVE_PROFILE.reset(token)
    assert record.session_id == "ephemeral-1"


def test_reliability_aggregation_from_usage_db(tmp_path):
    from src.services.observability.reliability_feedback import aggregate_reliability

    db = tmp_path / "usage.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE api_requests (
            timestamp TEXT,
            provider TEXT,
            resolved_model TEXT,
            routed_model TEXT,
            duration_ms REAL,
            status TEXT,
            error_message TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO api_requests VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)",
        [
            ("openrouter", "openrouter/a", "openrouter/a", 100.0, "success", None),
            ("openrouter", "openrouter/a", "openrouter/a", 300.0, "error", "429 rate limit"),
            ("anthropic", "anthropic/b", "anthropic/b", 200.0, "success", None),
        ],
    )
    conn.commit()
    conn.close()

    payload = aggregate_reliability(db)

    assert payload["providers"]["openrouter"]["requests"] == 2
    assert payload["providers"]["openrouter"]["error_rate"] == 0.5
    assert payload["providers"]["openrouter"]["rate_limit_frequency"] == 0.5
    assert payload["models"]["anthropic/b"]["latency_p95_ms"] == 200.0
