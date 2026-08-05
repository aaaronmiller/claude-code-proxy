#!/usr/bin/env python3
"""
Quick Headless Claude Code Test

Simple test to verify:
1. Claude Code can run headless
2. It connects to claude-code-proxy (8082)
3. Proxy forwards to backend (VibeProxy/OpenRouter)
4. Tool calls work correctly

Timeout: 30s (single simple task)
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

PROXY_URL = "http://127.0.0.1:8082"
TIMEOUT = 25  # seconds - minimal viable
DB_PATH = PROJECT_ROOT / "usage_tracking.db"


def create_workspace():
    """Create minimal test workspace with disabled MCP/skills."""
    workspace = Path(tempfile.mkdtemp(prefix="claude_quick_test_"))

    # Create .claude directory with permissions and disabled MCP
    claude_dir = workspace / ".claude"
    claude_dir.mkdir()

    settings = {
        "permissions": {
            "allow": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)"],
            "deny": []
        },
        "mcpServers": {},
        "enableAllProjectMcpServers": False
    }
    (claude_dir / "settings.local.json").write_text(json.dumps(settings))

    # Create empty CLAUDE.md to override global one
    (claude_dir / "CLAUDE.md").write_text("# Minimal test config\nNo skills or complex instructions.")

    return workspace


def run_simple_test():
    """Run a simple test with Claude Code headless."""
    print("\n" + "="*60)
    print("  QUICK HEADLESS CLAUDE CODE TEST")
    print("="*60)

    # Check proxy
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"{PROXY_URL}/health", timeout=5)
        health = resp.read().decode()
        print(f"  Proxy: OK - {health[:50]}...")
    except Exception as e:
        print(f"  Proxy: FAILED - {e}")
        return False

    # Create workspace
    workspace = create_workspace()
    print(f"  Workspace: {workspace}")

    # Record start time for DB query
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    print(f"  Start time: {start_time}")

    # Simple prompt - just create a file (no multi-step)
    prompt = "Create a file called hello.txt containing the text 'Hello World' and nothing else."

    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    env['ANTHROPIC_API_KEY'] = 'pass'
    env['NO_PROXY'] = 'localhost,127.0.0.1'

    cmd = [
        'timeout', str(TIMEOUT),
        'claude',
        '--dangerously-skip-permissions',
        '--no-chrome',
        '--no-session-persistence',
        '-p', prompt,
        '--allowedTools', 'Write,Bash',
    ]

    print(f"  Command: {' '.join(cmd[:6])}...")
    print(f"  Running Claude Code headless...")

    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=str(workspace),
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL
    )
    duration = time.time() - start

    print(f"  Exit code: {result.returncode}")
    print(f"  Duration: {duration:.1f}s")

    # Check if file was created
    hello_file = workspace / "hello.txt"
    file_created = hello_file.exists()
    file_content = hello_file.read_text().strip() if file_created else ""

    print(f"\n  Results:")
    print(f"    File created: {file_created}")
    if file_created:
        print(f"    Content: '{file_content}'")

    # Check stdout/stderr
    if result.stdout:
        print(f"\n  Stdout (last 500 chars):")
        print(f"    {result.stdout[-500:]}")
    if result.stderr:
        print(f"\n  Stderr (last 300 chars):")
        print(f"    {result.stderr[-300:]}")

    # Check database
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM api_requests
                WHERE timestamp >= ?
            """, (start_time,))
            count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT strftime('%H:%M:%S', timestamp), original_model, status,
                       input_tokens, output_tokens
                FROM api_requests
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (start_time,))
            rows = cursor.fetchall()
            conn.close()

            print(f"\n  DB Requests since test start: {count}")
            for row in rows[:5]:
                print(f"    {row[0]} | {row[1]} | {row[2]} | in:{row[3]} out:{row[4]}")
        except Exception as e:
            print(f"\n  DB Error: {e}")

    # Cleanup
    import shutil
    shutil.rmtree(workspace, ignore_errors=True)

    # Verdict
    success = file_created and "Hello" in file_content and result.returncode == 0
    print(f"\n  {'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
    print("="*60)

    return success


if __name__ == "__main__":
    success = run_simple_test()
    sys.exit(0 if success else 1)
