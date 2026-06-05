#!/usr/bin/env python3
"""Inspect usage_tracking.db for recent activity and errors."""
import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "usage_tracking.db"

def main():
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r["name"] for r in cur.fetchall()]
    print(f"Tables: {tables}\n")

    # For each table, show schema and recent rows
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [(r["name"], r["type"]) for r in cur.fetchall()]
        print(f"── {table} ({len(cols)} columns) ──")
        for name, typ in cols:
            print(f"  {name}: {typ}")

        cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        count = cur.fetchone()["cnt"]
        print(f"  Total rows: {count}")

        if count > 0:
            # Show last 10 rows
            cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 10")
            rows = cur.fetchall()
            print(f"  Last {len(rows)} rows:")
            for row in rows:
                d = dict(row)
                # Truncate long values
                for k, v in d.items():
                    if isinstance(v, str) and len(v) > 100:
                        d[k] = v[:100] + "..."
                print(f"    {d}")
        print()

    conn.close()

if __name__ == "__main__":
    main()
