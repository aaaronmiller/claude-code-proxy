#!/usr/bin/env python3
"""Cached RTK gain stats for tmux/status bars and API routes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_CACHE_PATH = Path(
    os.environ.get("RTK_STATUS_CACHE", "/tmp/claude-code-proxy/rtk-status.json")
)
DEFAULT_TTL_SECONDS = int(os.environ.get("RTK_STATUS_TTL", "10"))
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("RTK_STATUS_TIMEOUT", "1.5"))

Runner = Callable[[list[str], str | None, float], tuple[int, str, str]]


def _run(cmd: list[str], cwd: str | None, timeout: float) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _utc_now(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def _rtk_command(scope: str) -> list[str]:
    cmd = ["rtk", "gain"]
    if scope == "project":
        cmd.append("--project")
    cmd.extend(["--format", "json"])
    return cmd


def _summary(raw: dict[str, Any]) -> dict[str, Any]:
    source = raw.get("summary", raw)
    return {
        "total_commands": int(source.get("total_commands", 0) or 0),
        "total_input": int(source.get("total_input", 0) or 0),
        "total_output": int(source.get("total_output", 0) or 0),
        "total_saved": int(source.get("total_saved", 0) or 0),
        "avg_savings_pct": float(source.get("avg_savings_pct", 0) or 0),
        "total_time_ms": int(source.get("total_time_ms", 0) or 0),
        "avg_time_ms": int(source.get("avg_time_ms", 0) or 0),
    }


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        delete=False,
    ) as tmp:
        json.dump(data, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _load_cache(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _with_error(data: dict[str, Any], error: str) -> dict[str, Any]:
    stale = dict(data)
    stale["status"] = "stale"
    stale["stale"] = True
    stale["error"] = error.strip() or "rtk gain failed"
    return stale


def refresh_cache(
    cache_path: Path = DEFAULT_CACHE_PATH,
    scope: str = "project",
    cwd: str | None = None,
    runner: Runner = _run,
    now: Callable[[], float] = time.time,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    ts = now()
    cmd = _rtk_command(scope)
    try:
        code, stdout, stderr = runner(cmd, cwd, timeout_seconds)
        if code != 0:
            raise RuntimeError(stderr.strip() or f"rtk exited {code}")
        raw = json.loads(stdout)
        data = {
            "status": "ok",
            "scope": scope,
            "source": " ".join(cmd),
            "generated_at": _utc_now(ts),
            "generated_at_unix": ts,
            "stale": False,
            "summary": _summary(raw),
        }
        _atomic_write_json(cache_path, data)
        return data
    except Exception as exc:
        cached = _load_cache(cache_path)
        if cached:
            return _with_error(cached, str(exc))
        return {
            "status": "error",
            "scope": scope,
            "source": " ".join(cmd),
            "generated_at": _utc_now(ts),
            "generated_at_unix": ts,
            "stale": False,
            "error": str(exc),
            "summary": _summary({}),
        }


def get_stats(
    cache_path: Path = DEFAULT_CACHE_PATH,
    scope: str = "project",
    cwd: str | None = None,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    runner: Runner = _run,
    now: Callable[[], float] = time.time,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    force: bool = False,
) -> dict[str, Any]:
    cached = _load_cache(cache_path)
    if cached and not force:
        age = now() - float(cached.get("generated_at_unix", 0) or 0)
        if cached.get("scope") == scope and age <= ttl_seconds:
            return cached
    return refresh_cache(cache_path, scope, cwd, runner, now, timeout_seconds)


def _compact_tokens(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def format_tmux(data: dict[str, Any]) -> str:
    summary = data.get("summary", {})
    saved = _compact_tokens(int(summary.get("total_saved", 0) or 0))
    pct = float(summary.get("avg_savings_pct", 0) or 0)
    cmds = int(summary.get("total_commands", 0) or 0)
    stale = " │ #[fg=yellow]stale#[default]" if data.get("stale") else ""
    if data.get("status") == "error":
        return "#[fg=yellow]● RTK#[default] │ #[fg=red]stats unavailable#[default]"
    return (
        "#[fg=green]● RTK#[default]"
        f" │ #[fg=cyan]{pct:.0f}%#[default] avg"
        f" │ {saved}tok saved"
        f" │ {cmds} cmds"
        f"{stale}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read cached RTK token savings stats")
    parser.add_argument("--scope", choices=["project", "global"], default="project")
    parser.add_argument("--format", choices=["json", "tmux"], default="json")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)

    data = get_stats(
        cache_path=args.cache,
        scope=args.scope,
        cwd=args.cwd,
        ttl_seconds=args.ttl,
        timeout_seconds=args.timeout,
        force=args.refresh,
    )
    if args.format == "tmux":
        print(format_tmux(data))
    else:
        print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data.get("status") != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
