#!/usr/bin/env python3
"""
Direct Model Tier Validation Script

Tests Claude Code tool calls through the proxy for each model tier configuration.
Uses the user's running proxy on port 8082 instead of starting a new one.

Usage:
    python tests/integration/run_tier_tests.py
"""

import os
import sys
import time
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Tuple, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@dataclass
class TestConfig:
    """Test configuration for a model tier."""
    name: str
    big_model: str
    middle_model: str
    small_model: str


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CONFIGURATIONS (FREE/CHEAP MODELS ONLY)
# ═══════════════════════════════════════════════════════════════════════════════

TIER_TESTS = [
    # VibeProxy Gemini (FREE)
    TestConfig(
        name="vibeproxy_gemini",
        big_model="vibeproxy/gemini-3-pro",
        middle_model="vibeproxy/gemini-2.5-flash",
        small_model="vibeproxy/gemini-3-flash",
    ),
    # VibeProxy Claude (FREE via VibeProxy)
    TestConfig(
        name="vibeproxy_claude",
        big_model="vibeproxy/claude-opus-4",
        middle_model="vibeproxy/claude-sonnet-4",
        small_model="vibeproxy/claude-sonnet-4",
    ),
    # OpenRouter Free Models
    TestConfig(
        name="openrouter_free",
        big_model="openrouter/meta-llama/llama-3.1-8b-instruct:free",
        middle_model="openrouter/qwen/qwen-2.5-7b-instruct:free",
        small_model="openrouter/mistralai/mistral-7b-instruct:free",
    ),
    # Gemini Flash (CHEAP)
    TestConfig(
        name="gemini_flash",
        big_model="vibeproxy/gemini-2.5-flash",
        middle_model="vibeproxy/gemini-3-flash",
        small_model="vibeproxy/gemini-3-flash",
    ),
]


PROXY_URL = "http://127.0.0.1:8082"
CLAUDE_TIMEOUT = 60


def update_env_models(config: TestConfig) -> None:
    """Update .env file with model configuration."""
    env_path = PROJECT_ROOT / ".env"
    
    # Read current .env
    if env_path.exists():
        content = env_path.read_text()
    else:
        content = ""
    
    # Update or add model lines
    lines = content.split('\n')
    new_lines = []
    updated = {'BIG_MODEL': False, 'MIDDLE_MODEL': False, 'SMALL_MODEL': False}
    
    for line in lines:
        if line.startswith('BIG_MODEL='):
            new_lines.append(f'BIG_MODEL="{config.big_model}"')
            updated['BIG_MODEL'] = True
        elif line.startswith('MIDDLE_MODEL='):
            new_lines.append(f'MIDDLE_MODEL="{config.middle_model}"')
            updated['MIDDLE_MODEL'] = True
        elif line.startswith('SMALL_MODEL='):
            new_lines.append(f'SMALL_MODEL="{config.small_model}"')
            updated['SMALL_MODEL'] = True
        else:
            new_lines.append(line)
    
    # Add any missing model lines
    if not updated['BIG_MODEL']:
        new_lines.append(f'BIG_MODEL="{config.big_model}"')
    if not updated['MIDDLE_MODEL']:
        new_lines.append(f'MIDDLE_MODEL="{config.middle_model}"')
    if not updated['SMALL_MODEL']:
        new_lines.append(f'SMALL_MODEL="{config.small_model}"')
    
    env_path.write_text('\n'.join(new_lines))


def run_claude_command(prompt: str, workspace: Path) -> Tuple[str, str, int]:
    """Run Claude Code CLI with a prompt."""
    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    env['ANTHROPIC_API_KEY'] = 'pass'
    
    cmd = [
        'claude',
        '--print',
        '--dangerously-skip-permissions',
        '-p', prompt,
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", -1
    except FileNotFoundError:
        return "", "Claude CLI not found", -1


def get_recent_requests(db_path: str, since: str, limit: int = 10) -> List[dict]:
    """Get API requests from usage_tracking.db since timestamp."""
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT original_model, routed_model, status, error_message, input_tokens, output_tokens
            FROM api_requests 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (since, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  DB Error: {e}")
        return []


def test_tier(config: TestConfig, results: List[dict]) -> None:
    """Run a single tier test."""
    print(f"\n{'='*60}")
    print(f"Testing: {config.name}")
    print(f"  BIG:    {config.big_model}")
    print(f"  MIDDLE: {config.middle_model}")
    print(f"  SMALL:  {config.small_model}")
    print(f"{'='*60}")
    
    # Create test workspace
    workspace = Path(f"/tmp/tier_test_{config.name}_{int(time.time())}")
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Record start time for DB query
    start_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    # Simple test prompt (minimizes tokens)
    prompt = "Write 'hello' to test.txt"
    
    print(f"\n  Running Claude with prompt: '{prompt}'")
    stdout, stderr, exit_code = run_claude_command(prompt, workspace)
    
    # Check results
    test_file = workspace / "test.txt"
    file_created = test_file.exists()
    
    # Check database for request
    db_path = str(PROJECT_ROOT / "usage_tracking.db")
    requests = get_recent_requests(db_path, start_time, limit=5)
    
    # Determine status
    if file_created:
        status = "✅ PASS"
    elif requests and any(r.get('status') == 'success' for r in requests):
        status = "⚠️ PARTIAL (request succeeded but file not created)"
    elif requests:
        error = requests[0].get('error_message', 'Unknown')
        status = f"❌ FAIL (API Error: {error[:50]})"
    else:
        status = "❌ FAIL (No requests logged)"
    
    print(f"\n  Result: {status}")
    print(f"  File created: {file_created}")
    print(f"  Exit code: {exit_code}")
    if requests:
        print(f"  Requests logged: {len(requests)}")
        for r in requests[:2]:
            print(f"    - {r.get('original_model')} -> {r.get('routed_model')} [{r.get('status')}]")
    
    # Record result
    results.append({
        'config': config.name,
        'status': status,
        'file_created': file_created,
        'exit_code': exit_code,
        'request_count': len(requests),
        'models': {
            'big': config.big_model,
            'middle': config.middle_model,
            'small': config.small_model,
        }
    })
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    if workspace.exists():
        workspace.rmdir()


def main():
    """Run all tier tests."""
    print("\n" + "="*70)
    print("  MODEL TIER VALIDATION TESTS")
    print("  Testing BIG/MIDDLE/SMALL tool calls for each model configuration")
    print("="*70)
    
    results = []
    
    for config in TIER_TESTS:
        try:
            test_tier(config, results)
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append({
                'config': config.name,
                'status': f"❌ ERROR: {str(e)[:50]}",
                'file_created': False,
                'exit_code': -1,
                'request_count': 0,
            })
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    
    for r in results:
        print(f"\n  {r['config']}: {r['status']}")
    
    passed = sum(1 for r in results if "PASS" in r['status'])
    total = len(results)
    print(f"\n  Total: {passed}/{total} passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
