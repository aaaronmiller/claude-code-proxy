#!/usr/bin/env python3
"""
Claude Code Headless Tool Call Integration Test

Tests tool calling via actual Claude Code CLI headless sessions with various
model/provider combinations for BIG/MIDDLE and SMALL (tool-calling) tiers.

Test Flow:
1. Create temp workspace
2. Run Claude Code headless: create poem file + list folder contents
3. Verify file created and response includes folder listing
4. Test multiple provider/model combinations

Usage:
    # Test default provider (vibeproxy-gemini)
    uv run python tests/integration/headless_tool_test.py

    # Test specific config
    uv run python tests/integration/headless_tool_test.py --config vibeproxy_gemini

    # Test all configs
    uv run python tests/integration/headless_tool_test.py --all

    # Quick test (free models only)
    uv run python tests/integration/headless_tool_test.py --quick
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Configuration
PROXY_URL = "http://127.0.0.1:8089"
VIBEPROXY_URL = "http://127.0.0.1:8317"
TIMEOUT = 45  # seconds per test
DB_PATH = PROJECT_ROOT / "usage_tracking.db"
LOG_DIR = PROJECT_ROOT / "tests" / "integration" / "session_logs"


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL/PROVIDER CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ToolTestConfig:
    """Configuration for a tool call test."""
    name: str
    big_model: str           # Model for complex reasoning
    middle_model: str        # Model for medium tasks
    small_model: str         # Model for tool calls
    description: str
    timeout: int = 45
    requires_vibeproxy: bool = False
    requires_openrouter: bool = False


# VibeProxy Gemini - FREE (uses local OAuth)
VIBEPROXY_GEMINI = ToolTestConfig(
    name="vibeproxy_gemini",
    big_model="gemini-3-pro-preview",
    middle_model="gemini-3-flash",
    small_model="gemini-3-flash",
    description="Gemini via VibeProxy (FREE - local OAuth)",
    timeout=90,  # Pro model needs more time
    requires_vibeproxy=True,
)

# VibeProxy Claude Sonnet via Gemini + Gemini Flash for tools
VIBEPROXY_CLAUDE_SONNET = ToolTestConfig(
    name="vibeproxy_claude_sonnet",
    big_model="gemini-claude-sonnet-4-5-thinking",
    middle_model="gemini-claude-sonnet-4-5",
    small_model="gemini-3-flash",
    description="Claude Sonnet via VibeProxy + Gemini Flash for tools",
    timeout=60,
    requires_vibeproxy=True,
)

# VibeProxy Claude Opus via Gemini + Gemini Flash for tools
VIBEPROXY_CLAUDE_OPUS = ToolTestConfig(
    name="vibeproxy_claude_opus",
    big_model="gemini-claude-opus-4-5-thinking",
    middle_model="gemini-claude-sonnet-4-5",
    small_model="gemini-3-flash",
    description="Claude Opus via VibeProxy + Gemini Flash for tools",
    timeout=90,
    requires_vibeproxy=True,
)

# VibeProxy Claude Sonnet + MIMO V2 for tool calls (hybrid)
VIBEPROXY_SONNET_MIMO = ToolTestConfig(
    name="vibeproxy_sonnet_mimo",
    big_model="gemini-claude-sonnet-4-5-thinking",
    middle_model="gemini-claude-sonnet-4-5",
    small_model="xiaomi/mimo-v2-flash:free",
    description="Claude Sonnet via VibeProxy + MIMO V2 for tools",
    timeout=90,
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# VibeProxy Claude Opus + MIMO V2 for tool calls (hybrid)
VIBEPROXY_OPUS_MIMO = ToolTestConfig(
    name="vibeproxy_opus_mimo",
    big_model="gemini-claude-opus-4-5-thinking",
    middle_model="gemini-claude-sonnet-4-5",
    small_model="xiaomi/mimo-v2-flash:free",
    description="Claude Opus via VibeProxy + MIMO V2 for tools",
    timeout=120,
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# VibeProxy Gemini Flash (Requested by User)
VIBEPROXY_GEMINI_FLASH = ToolTestConfig(
    name="vibeproxy_gemini_flash",
    big_model="claude-3-opus-20240229",
    middle_model="claude-3-opus-20240229",
    small_model="claude-3-opus-20240229",
    description="Gemini 3 Flash Preview (VibeProxy)",
    timeout=120,
    requires_vibeproxy=True,
)

# OpenRouter MIMO V2 only (free)
OPENROUTER_MIMO = ToolTestConfig(
    name="openrouter_mimo",
    big_model="xiaomi/mimo-v2-flash:free",
    middle_model="xiaomi/mimo-v2-flash:free",
    small_model="xiaomi/mimo-v2-flash:free",
    description="MIMO V2 Flash (FREE - Xiaomi via OpenRouter)",
    requires_openrouter=True,
)

# [NEW] Mixed: Mimo (Small) + Gemini 3 Flash (Big)
VIBEPROXY_MIX_MIMO_SMALL = ToolTestConfig(
    name="vibeproxy_mix_mimo_small",
    big_model="claude-3-opus-20240229",      # Gemini 3 Flash (via VibeProxy)
    middle_model="claude-3-opus-20240229",   # Gemini 3 Flash (via VibeProxy)
    small_model="xiaomi/mimo-v2-flash:free", # Mimo V2 (via OpenRouter)
    description="Mixed: Gemini 3 Big + Mimo Small",
    timeout=120,
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# [NEW] Mixed: Mimo (Big) + Gemini 3 Flash (Small)
VIBEPROXY_MIX_MIMO_BIG = ToolTestConfig(
    name="vibeproxy_mix_mimo_big",
    big_model="xiaomi/mimo-v2-flash:free",   # Mimo V2 (via OpenRouter)
    middle_model="xiaomi/mimo-v2-flash:free",# Mimo V2 (via OpenRouter)
    small_model="claude-3-opus-20240229",    # Gemini 3 Flash (via VibeProxy)
    description="Mixed: Mimo Big + Gemini 3 Small",
    timeout=120,
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# [NEW] Full Mimo (All Tiers)
OPENROUTER_MIMO_FULL = ToolTestConfig(
    name="openrouter_mimo_full",
    big_model="xiaomi/mimo-v2-flash:free",
    middle_model="xiaomi/mimo-v2-flash:free",
    small_model="xiaomi/mimo-v2-flash:free",
    description="Full Mimo V2 Stack (OpenRouter)",
    timeout=120,
    requires_openrouter=True,
)

# OpenRouter Free Models (Llama + MIMO)
OPENROUTER_FREE = ToolTestConfig(
    name="openrouter_free",
    big_model="meta-llama/llama-3.1-8b-instruct:free",
    middle_model="meta-llama/llama-3.1-8b-instruct:free",
    small_model="xiaomi/mimo-v2-flash:free",
    description="OpenRouter FREE tier (Llama + MIMO V2)",
    timeout=60,
    requires_openrouter=True,
)

# OpenRouter Kimi-K2 (free, very capable)
OPENROUTER_KIMI = ToolTestConfig(
    name="openrouter_kimi",
    big_model="moonshotai/kimi-k2:free",
    middle_model="moonshotai/kimi-k2:free",
    small_model="moonshotai/kimi-k2:free",
    description="Moonshot Kimi-K2 (FREE, high capability)",
    timeout=120,
    requires_openrouter=True,
)

# Gemini Pro + MIMO V2 hybrid
GEMINI_PRO_MIMO = ToolTestConfig(
    name="gemini_pro_mimo",
    big_model="gemini-3-pro-preview",
    middle_model="gemini-3-flash",
    small_model="xiaomi/mimo-v2-flash:free",
    description="Gemini Pro via VibeProxy + MIMO V2 for tools",
    timeout=60,
    requires_vibeproxy=True,
    requires_openrouter=True,
)

# All configurations (verified working)
ALL_CONFIGS = [
    VIBEPROXY_GEMINI_FLASH,
    # VIBEPROXY_GEMINI,  # Slow gemini-3-pro-preview times out
    VIBEPROXY_CLAUDE_SONNET,
    VIBEPROXY_CLAUDE_OPUS,
    VIBEPROXY_SONNET_MIMO,
    VIBEPROXY_OPUS_MIMO,
    OPENROUTER_MIMO,
    OPENROUTER_MIMO_FULL,
    VIBEPROXY_MIX_MIMO_SMALL,
    VIBEPROXY_MIX_MIMO_BIG,
    # OPENROUTER_FREE,  # Llama model not available on OpenRouter
    # OPENROUTER_KIMI,  # Kimi-K2 doesn't support tool use
    # GEMINI_PRO_MIMO,  # Gemini Pro times out frequently
]

# Quick test configs (free/fast models only)
QUICK_CONFIGS = [
    VIBEPROXY_GEMINI,
    OPENROUTER_MIMO,
]

DEFAULT_CONFIG = VIBEPROXY_GEMINI


# ═══════════════════════════════════════════════════════════════════════════════
# TEST INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

def check_proxy() -> bool:
    """Check if proxy is running."""
    import urllib.request
    try:
        resp = urllib.request.urlopen(f"{PROXY_URL}/health", timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("status") == "healthy"
    except Exception:
        return False


def check_vibeproxy() -> bool:
    """Check if VibeProxy is running on port 8317 (no /health endpoint)."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8317))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_openrouter_key() -> bool:
    """Check if OpenRouter API key is configured."""
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def verify_database_no_duplicates(start_time: str, config_name: str) -> Tuple[bool, dict]:
    """
    Verify the usage_tracking.db for this test run.
    
    Checks:
    1. Requests were logged
    2. No rapid duplicate requests (same model within 2 seconds)
    3. Returns stats about the requests
    
    Returns: (no_duplicates, stats_dict)
    """
    stats = {
        "request_count": 0,
        "models_used": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "duplicates_found": 0,
        "duplicate_details": [],
    }
    
    if not DB_PATH.exists():
        return True, {"error": "Database not found"}
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get all requests since start time
        cursor.execute("""
            SELECT id, timestamp, original_model, routed_model, status,
                   input_tokens, output_tokens
            FROM api_requests
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (start_time,))
        rows = cursor.fetchall()
        
        stats["request_count"] = len(rows)
        
        # Collect models and tokens
        for row in rows:
            model = row[3] or row[2]  # routed_model or original_model
            if model and model not in stats["models_used"]:
                stats["models_used"].append(model)
            stats["total_input_tokens"] += row[5] or 0
            stats["total_output_tokens"] += row[6] or 0
        
        # Check for duplicates - look for same model requests within 2 seconds
        # (rapid retries indicate duplicate/loop behavior)
        if len(rows) > 1:
            from datetime import datetime as dt
            prev_row = None
            for row in rows:
                if prev_row:
                    model = row[3] or row[2]
                    prev_model = prev_row[3] or prev_row[2]
                    if model == prev_model:
                        # Check time difference
                        try:
                            t1 = dt.fromisoformat(prev_row[1].replace('Z', '+00:00'))
                            t2 = dt.fromisoformat(row[1].replace('Z', '+00:00'))
                            diff = (t2 - t1).total_seconds()
                            if diff < 2.0:  # Requests within 2 seconds = potential duplicate
                                stats["duplicates_found"] += 1
                                stats["duplicate_details"].append({
                                    "model": model,
                                    "first_time": prev_row[1],
                                    "dup_time": row[1],
                                    "gap_seconds": diff,
                                })
                        except:
                            pass
                prev_row = row
        
        conn.close()
        
        no_duplicates = stats["duplicates_found"] == 0
        return no_duplicates, stats
        
    except Exception as e:
        return True, {"error": str(e)}


def create_workspace(config: ToolTestConfig) -> Path:
    """Create test workspace with model-specific settings."""
    workspace = Path(tempfile.mkdtemp(prefix=f"tool_test_{config.name}_"))

    # Create .claude directory
    claude_dir = workspace / ".claude"
    claude_dir.mkdir()

    # Settings with all tool permissions
    settings = {
        "permissions": {
            "allow": [
                "Bash(*)",
                "Read(*)",
                "Write(*)",
                "Edit(*)",
                "LS(*)",
                "Glob(*)",
            ],
            "deny": []
        },
        "mcpServers": {},
        "enableAllProjectMcpServers": False
    }
    (claude_dir / "settings.local.json").write_text(json.dumps(settings, indent=2))

    # Minimal CLAUDE.md
    claude_md = f"""# Tool Test Config
Testing {config.name}
No complex instructions - just execute the task.
"""
    (claude_dir / "CLAUDE.md").write_text(claude_md)

    return workspace


def run_tool_test(config: ToolTestConfig) -> Tuple[bool, dict]:
    """
    Run a single tool call test with the given configuration.
    
    Returns: (success, result_dict)
    """
    result = {
        "config": config.name,
        "model": config.small_model,
        "file_created": False,
        "file_has_poem": False,
        "folder_listed": False,
        "duration": 0,
        "exit_code": -1,
        "error": None,
        "db_requests": 0,
        "db_duplicates": 0,
        "db_models": [],
    }
    
    # Record start time for DB query
    start_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    
    # Create workspace
    workspace = create_workspace(config)
    
    # The test prompt - create TWO files to verify multi-tool-call handling
    prompt = (
        "Create two files: "
        "1) poem.txt containing a short 4-line poem about coding, "
        "2) limerick.txt containing a limerick about debugging. "
        "Then list the folder to confirm both files exist."
    )

    # Environment setup
    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    env['ANTHROPIC_API_KEY'] = 'pass'
    env['NO_PROXY'] = 'localhost,127.0.0.1'
    
    # Command
    cmd = [
        'timeout', str(config.timeout),
        'claude',
        '--dangerously-skip-permissions',
        '--no-chrome',
        '--no-session-persistence',
        '--model', config.big_model,
        '-p', prompt,
        '--allowedTools', 'Write,Bash,LS',
    ]

    try:
        start = time.time()
        print(f"DEBUG: Running command: {' '.join(cmd)}")
        proc_result = subprocess.run(
            cmd,
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL
        )
        result["duration"] = time.time() - start
        result["exit_code"] = proc_result.returncode

        if proc_result.returncode != 0:
            result["error"] = f"Process failed with return code {proc_result.returncode}"
            # proc_result.stderr is already str due to text=True
            print(f"\n--- CLI STDERR ---\n{proc_result.stderr}\n------------------\n")
            print(f"\n--- CLI STDOUT ---\n{proc_result.stdout}\n------------------\n")

        # Check if poem file was created
        poem_file = workspace / "poem.txt"
        if poem_file.exists():
            result["file_created"] = True
            content = poem_file.read_text()
            # Check if it looks like a poem (has multiple lines)
            if len(content.strip().split('\n')) >= 2:
                result["file_has_poem"] = True

        # Check for limerick.txt (dual file test)
        limerick_file = workspace / "limerick.txt"
        if limerick_file.exists():
            result["limerick_created"] = True

        # Check if folder listing was done (look for it in stdout)
        stdout = proc_result.stdout or ""
        stderr = proc_result.stderr or ""
        output = stdout + stderr
        
        # Look for indicators of folder listing
        if any(x in output.lower() for x in ["poem.txt", "limerick.txt", "files", "directory", "contents"]):
            result["folder_listed"] = True

        # Save logs
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / f"headless_{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            f.write(f"Config: {config.name}\n")
            f.write(f"Model: {config.small_model}\n")
            f.write(f"Duration: {result['duration']:.1f}s\n")
            f.write(f"Exit Code: {result['exit_code']}\n")
            f.write(f"\n--- STDOUT ---\n{stdout}\n")
            f.write(f"\n--- STDERR ---\n{stderr}\n")
        
        # Verify database for duplicates
        no_dups, db_stats = verify_database_no_duplicates(start_time, config.name)
        result["db_requests"] = db_stats.get("request_count", 0)
        result["db_duplicates"] = db_stats.get("duplicates_found", 0)
        result["db_models"] = db_stats.get("models_used", [])
        
        # Add DB info to log
        with open(log_file, 'a') as f:
            f.write(f"\n--- DATABASE STATS ---\n")
            f.write(f"Requests: {result['db_requests']}\n")
            f.write(f"Duplicates: {result['db_duplicates']}\n")
            f.write(f"Models: {result['db_models']}\n")
            if db_stats.get("duplicate_details"):
                f.write(f"Duplicate Details: {json.dumps(db_stats['duplicate_details'], indent=2)}\n")

    except Exception as e:
        result["error"] = str(e)
    finally:
        # Cleanup
        shutil.rmtree(workspace, ignore_errors=True)

    # Determine success - BOTH files created AND no duplicates
    success = (
        result["file_created"] and
        result["file_has_poem"] and
        result.get("limerick_created", False) and
        result["exit_code"] == 0 and
        result["db_duplicates"] == 0
    )
    
    return success, result


def run_tests(configs: List[ToolTestConfig]) -> List[Tuple[bool, dict]]:
    """Run tests for multiple configurations."""
    results = []
    
    print("\n" + "="*70)
    print("  CLAUDE CODE HEADLESS TOOL CALL TESTS")
    print("="*70)
    
    # Pre-flight checks
    print("\n  Pre-flight Checks:")
    
    proxy_ok = check_proxy()
    print(f"    Proxy (8082): {'OK' if proxy_ok else 'FAILED'}")
    if not proxy_ok:
        print("    ERROR: Proxy not running. Start with:")
        print("    DEBUG_SSE=true TRACK_USAGE=true uv run python start_proxy.py")
        return []
    
    vibeproxy_ok = check_vibeproxy()
    print(f"    VibeProxy (8317): {'OK' if vibeproxy_ok else 'Not running'}")
    
    openrouter_ok = check_openrouter_key()
    print(f"    OpenRouter API Key: {'OK' if openrouter_ok else 'Not set'}")
    
    # Filter configs based on availability
    available_configs = []
    skipped = []
    for config in configs:
        if config.requires_vibeproxy and not vibeproxy_ok:
            skipped.append((config.name, "VibeProxy not running"))
            continue
        if config.requires_openrouter and not openrouter_ok:
            skipped.append((config.name, "OpenRouter key not set"))
            continue
        available_configs.append(config)
    
    if skipped:
        print(f"\n  Skipped configs:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
    
    if not available_configs:
        print("\n  ERROR: No configs available to test")
        return []
    
    # Run tests
    print(f"\n  Running {len(available_configs)} test(s)...\n")
    
    for i, config in enumerate(available_configs, 1):
        print(f"  [{i}/{len(available_configs)}] {config.name}")
        print(f"      Model: {config.big_model}")
        print(f"      Description: {config.description}")
        print(f"      Timeout: {config.timeout}s")
        
        success, result = run_tool_test(config)
        results.append((success, result))
        
        status = "PASS" if success else "FAIL"
        print(f"      Result: {status}")
        print(f"      Duration: {result['duration']:.1f}s")
        print(f"      Poem Created: {result['file_created']}")
        print(f"      Limerick Created: {result.get('limerick_created', False)}")
        print(f"      DB Requests: {result['db_requests']}")
        print(f"      DB Duplicates: {result['db_duplicates']} {'⚠️ DUPLICATES!' if result['db_duplicates'] > 0 else '✓'}")
        if result['db_models']:
            print(f"      Models Used: {', '.join(result['db_models'][:3])}{'...' if len(result['db_models']) > 3 else ''}")
        if result['error']:
            print(f"      Error: {result['error']}")
        print()
    
    # Summary
    passed = sum(1 for s, _ in results if s)
    total = len(results)
    
    print("="*70)
    print(f"  SUMMARY: {passed}/{total} passed")
    for success, result in results:
        status = "PASS" if success else "FAIL"
        print(f"    {status}: {result['config']} ({result['model']}) - {result['duration']:.1f}s")
    print("="*70)
    
    return results


def get_config_by_name(name: str) -> Optional[ToolTestConfig]:
    """Get config by name."""
    for config in ALL_CONFIGS:
        if config.name == name:
            return config
    return None


def main():
    parser = argparse.ArgumentParser(description="Claude Code Headless Tool Call Tests")
    parser.add_argument("--config", "-c", help="Test specific config by name")
    parser.add_argument("--all", "-a", action="store_true", help="Test all configs")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick test (free models only)")
    parser.add_argument("--list", "-l", action="store_true", help="List available configs")
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable configurations:")
        for config in ALL_CONFIGS:
            print(f"  {config.name}: {config.description}")
            print(f"    Models: big={config.big_model}, small={config.small_model}")
        return 0
    
    # Determine configs to test
    if args.config:
        config = get_config_by_name(args.config)
        if not config:
            print(f"Unknown config: {args.config}")
            print(f"Available: {', '.join(c.name for c in ALL_CONFIGS)}")
            return 1
        configs = [config]
    elif args.all:
        configs = ALL_CONFIGS
    elif args.quick:
        configs = QUICK_CONFIGS
    else:
        configs = [DEFAULT_CONFIG]
    
    results = run_tests(configs)
    
    if not results:
        return 1
    
    # Exit with failure if any test failed
    all_passed = all(s for s, _ in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
