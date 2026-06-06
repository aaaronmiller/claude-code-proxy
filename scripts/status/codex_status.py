#!/usr/bin/env python3
"""Render compact Codex session status from local rollout JSONL files."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_INPUT_PER_1M = 1.75
DEFAULT_CACHED_INPUT_PER_1M = 0.175
DEFAULT_OUTPUT_PER_1M = 14.00


def compact_number(value: int | float | None) -> str:
    if value is None:
        return "?"
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value:.0f}"


def _iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows


def _session_cwd(path: Path) -> str | None:
    for row in _iter_jsonl(path):
        if row.get("type") == "turn_context":
            payload = row.get("payload") or {}
            cwd = payload.get("cwd")
            if isinstance(cwd, str):
                return cwd
    return None


def find_latest_session(sessions_root: Path, cwd: str | None = None) -> Path | None:
    root = Path(sessions_root).expanduser()
    if not root.exists():
        return None

    files = sorted(
        root.rglob("*.jsonl"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    if not files:
        return None

    if cwd:
        cwd_path = str(Path(cwd).expanduser())
        for path in files:
            if _session_cwd(path) == cwd_path:
                return path

    return files[0]


def _permission_label(turn_context: dict[str, Any]) -> str:
    sandbox = turn_context.get("sandbox_policy") or {}
    profile = turn_context.get("permission_profile") or {}
    sandbox_type = sandbox.get("type") if isinstance(sandbox, dict) else None
    profile_type = profile.get("type") if isinstance(profile, dict) else None

    if sandbox_type == "danger-full-access" or profile_type == "disabled":
        return "danger"
    if sandbox_type == "workspace-write":
        return "write"
    if sandbox_type == "read-only":
        return "read"
    return str(sandbox_type or profile_type or "?")


def _reasoning_effort(turn_context: dict[str, Any]) -> str:
    collaboration = turn_context.get("collaboration_mode") or {}
    settings = collaboration.get("settings") if isinstance(collaboration, dict) else {}
    return str(
        turn_context.get("effort")
        or (settings or {}).get("reasoning_effort")
        or turn_context.get("reasoning_effort")
        or "?"
    )


def _rate_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def estimate_cost_usd(tokens: dict[str, int]) -> float:
    input_rate = _rate_float("CODEX_STATUS_INPUT_PER_1M", DEFAULT_INPUT_PER_1M)
    cached_rate = _rate_float("CODEX_STATUS_CACHED_INPUT_PER_1M", DEFAULT_CACHED_INPUT_PER_1M)
    output_rate = _rate_float("CODEX_STATUS_OUTPUT_PER_1M", DEFAULT_OUTPUT_PER_1M)

    cached = max(tokens.get("cached", 0), 0)
    input_tokens = max(tokens.get("input", 0) - cached, 0)
    output_tokens = max(tokens.get("output", 0), 0) + max(tokens.get("reasoning", 0), 0)

    return (
        input_tokens * input_rate
        + cached * cached_rate
        + output_tokens * output_rate
    ) / 1_000_000


def read_session(path: Path) -> dict[str, Any]:
    turn_context: dict[str, Any] = {}
    token_info: dict[str, Any] = {}
    rate_limits: dict[str, Any] = {}

    for row in _iter_jsonl(Path(path)):
        if row.get("type") == "turn_context":
            turn_context = row.get("payload") or {}
        elif row.get("type") == "event_msg":
            payload = row.get("payload") or {}
            if payload.get("type") == "token_count":
                token_info = payload.get("info") or {}
                rate_limits = payload.get("rate_limits") or {}

    total = token_info.get("total_token_usage") or {}
    last = token_info.get("last_token_usage") or {}
    window = int(token_info.get("model_context_window") or 0)
    used_tokens = int(last.get("total_tokens") or 0)
    used_pct = round((used_tokens / window * 100), 1) if window else 0.0

    tokens = {
        "input": int(total.get("input_tokens") or 0),
        "cached": int(total.get("cached_input_tokens") or 0),
        "output": int(total.get("output_tokens") or 0),
        "reasoning": int(total.get("reasoning_output_tokens") or 0),
        "total": int(total.get("total_tokens") or 0),
    }
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}

    return {
        "session": str(path),
        "cwd": turn_context.get("cwd"),
        "model": str(turn_context.get("model") or "?"),
        "reasoning_effort": _reasoning_effort(turn_context),
        "permission": _permission_label(turn_context),
        "approval": str(turn_context.get("approval_policy") or "?"),
        "context": {
            "used_pct": used_pct,
            "used_tokens": used_tokens,
            "window": window,
        },
        "tokens": tokens,
        "limits": {
            "primary_pct": float(primary.get("used_percent") or 0),
            "secondary_pct": float(secondary.get("used_percent") or 0),
            "plan": rate_limits.get("plan_type") or "?",
        },
        "estimated_cost_usd": estimate_cost_usd(tokens),
    }


def format_right(data: dict[str, Any], now: Callable[[], str] | None = None) -> str:
    now = now or (lambda: datetime.now().strftime("%a %H:%M"))
    reasoning = str(data.get("reasoning_effort") or "?")[:1]
    model = data.get("model") or "?"
    permission = data.get("permission") or "?"
    context = data.get("context") or {}
    tokens = data.get("tokens") or {}
    limits = data.get("limits") or {}
    cost = float(data.get("estimated_cost_usd") or 0)

    ctx_pct = context.get("used_pct") or 0
    used_tokens = compact_number(context.get("used_tokens"))
    window = compact_number(context.get("window"))
    primary = float(limits.get("primary_pct") or 0)
    secondary = float(limits.get("secondary_pct") or 0)

    return " │ ".join(
        [
            f"#[fg=cyan]{model}/{reasoning}#[default]",
            f"#[fg=yellow]perm:{permission}#[default]",
            f"ctx:{ctx_pct:.0f}% {used_tokens}/{window}",
            f"in:{compact_number(tokens.get('input'))} out:{compact_number(tokens.get('output'))} cache:{compact_number(tokens.get('cached'))}",
            f"${cost:.2f}",
            f"lim:{primary:.0f}/{secondary:.0f}%",
            now(),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--side", choices=["right", "json"], default="right")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS_ROOT)
    args = parser.parse_args()

    session = find_latest_session(args.sessions_root, args.cwd)
    if session is None:
        print("#[fg=yellow]codex:no-session#[default]" if args.side == "right" else "{}")
        return 0

    data = read_session(session)
    if args.side == "json":
        print(json.dumps(data, sort_keys=True))
    else:
        print(format_right(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
