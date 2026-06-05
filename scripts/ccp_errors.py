#!/usr/bin/env python3
"""Tail/filter the unified ccp error sink."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

ERRORS_FILE = Path("~/.ccp/errors.jsonl").expanduser()


def _matches(row: dict, args) -> bool:
    if args.tool and row.get("tool") != args.tool:
        return False
    if args.provider and row.get("provider") != args.provider:
        return False
    if args.session and row.get("session_id") != args.session:
        return False
    return True


def _format(row: dict) -> str:
    ts = row.get("timestamp", "")
    session = row.get("session_id") or "-"
    provider = row.get("provider") or "-"
    tool = row.get("tool") or "-"
    msg = row.get("message") or row.get("error") or ""
    return f"{ts} session={session} tool={tool} provider={provider} {msg}"


def _iter_rows(path: Path, start_at_end: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with path.open("r", encoding="utf-8") as fh:
        if start_at_end:
            fh.seek(0, 2)
        while True:
            line = fh.readline()
            if not line:
                yield None
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"timestamp": "", "message": line.strip()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--follow", "-f", action="store_true")
    p.add_argument("--tool")
    p.add_argument("--provider")
    p.add_argument("--session")
    p.add_argument("--limit", type=int, default=100)
    args = p.parse_args()

    if args.follow:
        for row in _iter_rows(ERRORS_FILE, start_at_end=True):
            if row is None:
                time.sleep(0.5)
                continue
            if _matches(row, args):
                print(_format(row), flush=True)
        return 0

    rows = []
    for line in ERRORS_FILE.read_text(encoding="utf-8").splitlines() if ERRORS_FILE.exists() else []:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _matches(row, args):
            rows.append(row)
    for row in rows[-args.limit:]:
        print(_format(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
