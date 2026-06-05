"""Shared JSONL error sink for proxy, launcher, and chain components."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ERRORS_FILE = Path(os.environ.get("CCP_ERRORS_FILE", "~/.ccp/errors.jsonl")).expanduser()


def emit_error(
    message: Any,
    *,
    tool: str = "",
    provider: str = "",
    session_id: str = "",
    model: str = "",
    request_id: str = "",
    component: str = "proxy",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one structured error row and return it.

    The append uses a single OS-level write to avoid interleaved JSON from concurrent writers.
    """
    row: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "tool": tool,
        "provider": provider,
        "session_id": session_id,
        "model": model,
        "request_id": request_id,
        "message": str(message),
    }
    if extra:
        row["extra"] = extra

    ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(row, sort_keys=True, default=str) + "\n").encode("utf-8")
    fd = os.open(str(ERRORS_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, payload)
    finally:
        os.close(fd)
    return row


def tail_errors(limit: int = 50) -> list[dict[str, Any]]:
    if not ERRORS_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ERRORS_FILE.read_text(encoding="utf-8").splitlines()[-max(1, limit):]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"timestamp": "", "message": line})
    return rows
