#!/usr/bin/env python3
"""
Multi-Tool Call Verification Test

Tests that multiple tool calls (2 file writes) complete without:
- Duplicate requests
- Looping behavior
- SSE stream errors

Verifies hybrid configurations work correctly.
"""

import os
import sys
import time
import tempfile
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

PROXY_URL = "http://127.0.0.1:8082"
DB_PATH = PROJECT_ROOT / "usage_tracking.db"

# Test prompt requiring TWO file writes
MULTI_TOOL_PROMPT = """Create two files:
1. poem.txt - containing a short 4-line poem about coding
2. limerick.txt - containing a limerick about debugging

After creating both files, list the folder contents to confirm both files exist."""

CONFIGS = {
    "vibeproxy_gemini_flash": {
        "model": "gemini-3-flash",  # Direct model name for VibeProxy
        "description": "Gemini 3 Flash via VibeProxy",
    },
    "vibeproxy_claude_sonnet": {
        "model": "gemini-claude-sonnet-4-5-thinking",
        "description": "Claude Sonnet via VibeProxy",
    },
    "openrouter_mimo": {
        "model": "xiaomi/mimo-v2-flash:free",
        "description": "Mimo V2 via OpenRouter",
    },
}


def get_db_requests_since(start_time: str) -> list:
    """Get all requests from DB since start_time."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, original_model, routed_model, provider, status, 
               error_message, has_tools, input_tokens, output_tokens
        FROM api_requests 
        WHERE timestamp >= ?
        ORDER BY id ASC
    """, (start_time,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def run_multi_tool_test(config_name: str, config: dict) -> dict:
    """Run test with multi-tool prompt."""
    print(f"\n{'='*60}")
    print(f"Testing: {config_name}")
    print(f"Model: {config['model']}")
    print(f"Description: {config['description']}")
    print(f"{'='*60}")
    
    # Create temp directory
    with tempfile.TemporaryDirectory(prefix=f"multi_tool_{config_name}_") as tmpdir:
        # Record start time for DB query
        start_time = datetime.utcnow().isoformat()
        
        # Build claude command
        cmd = [
            "timeout", "120",
            "claude",
            "--dangerously-skip-permissions",
            "--no-chrome",
            "--no-session-persistence",
            f"--model", config["model"],
            "-p", MULTI_TOOL_PROMPT,
            "--allowedTools", "Write,Bash,LS"
        ]
        
        # Set environment
        env = os.environ.copy()
        env["ANTHROPIC_BASE_URL"] = PROXY_URL
        env["ANTHROPIC_API_KEY"] = "pass"
        env["NO_PROXY"] = "localhost,127.0.0.1"
        
        print(f"\nRunning in: {tmpdir}")
        print(f"Command: {' '.join(cmd[:6])}...")
        
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )
            duration = time.time() - start
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            duration = 120
            exit_code = -1
            stdout = ""
            stderr = "TIMEOUT"
        except Exception as e:
            duration = time.time() - start
            exit_code = -2
            stdout = ""
            stderr = str(e)
        
        # Check for created files
        poem_exists = (Path(tmpdir) / "poem.txt").exists()
        limerick_exists = (Path(tmpdir) / "limerick.txt").exists()
        
        poem_content = ""
        limerick_content = ""
        if poem_exists:
            poem_content = (Path(tmpdir) / "poem.txt").read_text()
        if limerick_exists:
            limerick_content = (Path(tmpdir) / "limerick.txt").read_text()
        
        # Get DB requests during this test
        db_requests = get_db_requests_since(start_time)
        
        # Analyze for duplicates
        request_models = [r[3] for r in db_requests]  # routed_model
        errors = [r for r in db_requests if r[5] == 'error']
        successes = [r for r in db_requests if r[5] == 'success']
        
        result = {
            "config": config_name,
            "model": config["model"],
            "duration": duration,
            "exit_code": exit_code,
            "poem_created": poem_exists,
            "limerick_created": limerick_exists,
            "poem_content": poem_content[:100] if poem_content else "",
            "limerick_content": limerick_content[:100] if limerick_content else "",
            "db_total_requests": len(db_requests),
            "db_successes": len(successes),
            "db_errors": len(errors),
            "request_models": request_models,
            "passed": poem_exists and limerick_exists and exit_code == 0,
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else "",
        }
        
        # Print results
        print(f"\n--- Results ---")
        print(f"Duration: {duration:.1f}s")
        print(f"Exit Code: {exit_code}")
        print(f"Poem Created: {poem_exists}")
        print(f"Limerick Created: {limerick_exists}")
        print(f"DB Requests: {len(db_requests)} (Success: {len(successes)}, Errors: {len(errors)})")
        
        if poem_content:
            print(f"\n--- poem.txt ---")
            print(poem_content[:200])
        
        if limerick_content:
            print(f"\n--- limerick.txt ---")
            print(limerick_content[:200])
        
        if errors:
            print(f"\n--- DB Errors ---")
            for err in errors:
                print(f"  ID {err[0]}: {err[6][:80]}...")
        
        if stderr and "error" in stderr.lower():
            print(f"\n--- STDERR ---")
            print(stderr[:300])
        
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"\n{status}: {config_name}")
        
        return result


def main():
    print("="*70)
    print("  MULTI-TOOL CALL VERIFICATION TEST")
    print("  Testing: 2 file writes (poem + limerick)")
    print("="*70)
    
    results = []
    
    for config_name, config in CONFIGS.items():
        result = run_multi_tool_test(config_name, config)
        results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\nResults: {passed}/{total} passed\n")
    
    for r in results:
        status = "✅" if r["passed"] else "❌"
        files = f"poem:{r['poem_created']} limerick:{r['limerick_created']}"
        print(f"{status} {r['config']:30} | {r['duration']:5.1f}s | {files} | DB:{r['db_total_requests']}")
    
    # Check for any duplicates or anomalies
    print("\n--- Duplicate/Loop Analysis ---")
    for r in results:
        if r['db_total_requests'] > 10:
            print(f"⚠️  {r['config']}: High request count ({r['db_total_requests']}) - possible loop")
        elif r['db_errors'] > 0:
            print(f"⚠️  {r['config']}: {r['db_errors']} errors in DB")
        else:
            print(f"✓  {r['config']}: Request count normal ({r['db_total_requests']})")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
