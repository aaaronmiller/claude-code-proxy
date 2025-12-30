#!/usr/bin/env python3
"""
Skill-Based E2E Test Runner

Creates a test workspace with a Claude skill file, runs Claude Code in headless mode,
analyzes output and usage_tracking.db, and generates a comprehensive results table.

Usage:
    python tests/integration/skill_test_runner.py
"""

import os
import sys
import time
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROXY_URL = "http://127.0.0.1:8082"
CLAUDE_TIMEOUT = 25  # seconds - minimal viable
DB_PATH = PROJECT_ROOT / "usage_tracking.db"
LOGS_DIR = PROJECT_ROOT / "tests" / "integration" / "session_logs"

# Import usage tracker for terminal output logging
from services.usage.usage_tracker import UsageTracker

# Skill content that instructs Claude to create poem and list folder
SKILL_INSTRUCTIONS = """# Poem Creation Skill

You are a helpful assistant that creates poetry files.

## Task

When asked to create a poem:
1. Write a short poem (4-8 lines) about coding, programming, or technology
2. Save the poem to a file called `poem.txt` in the current directory
3. After saving, list the contents of the current directory to confirm the file was created
4. Report back with the poem content and confirmation that the file exists

## Important

- Always save the poem to exactly `poem.txt`
- Always list the directory after saving
- Be concise in your response
"""

# Model configurations to test
TEST_CONFIGS = [
    {
        "name": "vibeproxy_gemini",
        "description": "VibeProxy Gemini (FREE)",
        "env": {
            "BIG_MODEL": "vibeproxy/gemini-3-pro",
            "MIDDLE_MODEL": "vibeproxy/gemini-2.5-flash",
            "SMALL_MODEL": "vibeproxy/gemini-3-flash",
        }
    },
    {
        "name": "vibeproxy_claude",
        "description": "VibeProxy Claude (FREE)",
        "env": {
            "BIG_MODEL": "vibeproxy/claude-sonnet-4",
            "MIDDLE_MODEL": "vibeproxy/claude-sonnet-4",
            "SMALL_MODEL": "vibeproxy/gemini-3-flash",
        }
    },
    {
        "name": "gemini_flash_only",
        "description": "Gemini Flash Only (CHEAP/FAST)",
        "env": {
            "BIG_MODEL": "vibeproxy/gemini-2.5-flash",
            "MIDDLE_MODEL": "vibeproxy/gemini-3-flash",
            "SMALL_MODEL": "vibeproxy/gemini-3-flash",
        }
    },
]


@dataclass
class TestResult:
    """Result of a single test run."""
    config_name: str
    timestamp: str
    success: bool
    poem_created: bool
    poem_content: str
    folder_listed: bool
    claude_exit_code: int
    claude_stdout: str
    claude_stderr: str
    db_requests: List[Dict]
    db_errors: List[str]
    duration_seconds: float
    session_analysis: Dict = field(default_factory=dict)  # Full session token analysis
    error_message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

def create_test_workspace(test_name: str) -> Path:
    """Create a test workspace with .claude folder and skill file."""
    workspace = Path(f"/tmp/claude_skill_test_{test_name}_{int(time.time())}")
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create .claude directory
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(exist_ok=True)
    
    # Create INSTRUCTIONS.md skill file
    instructions_file = claude_dir / "INSTRUCTIONS.md"
    instructions_file.write_text(SKILL_INSTRUCTIONS)
    
    # Create settings.local.json for project permissions
    # Claude Code expects specific format for local settings
    settings = {
        "permissions": {
            "allow": [
                "Bash(*)",
                "Read(*)",
                "Write(*)",
                "Edit(*)"
            ],
            "deny": []
        }
    }
    settings_file = claude_dir / "settings.local.json"
    settings_file.write_text(json.dumps(settings, indent=2))
    
    return workspace


def cleanup_workspace(workspace: Path) -> None:
    """Clean up test workspace."""
    if workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_claude_with_skill(workspace: Path, config: Dict) -> Tuple[str, str, int]:
    """
    Run Claude Code in headless mode with the skill.
    
    Uses --print mode for non-interactive output.
    15 second timeout per session for simple tasks.
    """
    env = os.environ.copy()
    env['ANTHROPIC_BASE_URL'] = PROXY_URL
    # Proven config from user aliases
    env['ANTHROPIC_API_KEY'] = 'pass'
    env['NO_PROXY'] = 'localhost,127.0.0.1'
    # Enable full content logging for request/response capture
    env['TRACK_USAGE'] = 'true'
    env['LOG_FULL_CONTENT'] = 'true'
    
    # Apply model config
    for key, value in config.get('env', {}).items():
        env[key] = value
    
    # Prompt that triggers the skill
    prompt = "Please create a poem about coding and save it as poem.txt, then list the folder contents."
    
    cmd = [
        'timeout', str(CLAUDE_TIMEOUT),
        'claude',
        '--dangerously-skip-permissions',
        '--no-chrome',
        '--no-session-persistence',
        '--verbose',
        '-p', prompt,
        '--allowedTools', 'Read,Edit,Bash',
    ]
    
    # Create stream log files for real-time debugging
    stream_stdout = LOGS_DIR / f"claude_stream_stdout_{config['name']}_{int(time.time())}.log"
    stream_stderr = LOGS_DIR / f"claude_stream_stderr_{config['name']}_{int(time.time())}.log"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"  Streaming debug output to: {stream_stdout}")
    print(f"  Command: {' '.join(cmd)}")
    
    with open(stream_stdout, 'wb') as f_out, open(stream_stderr, 'wb') as f_err:
        try:
            print("  Starting process (subprocess.run)...")
            result = subprocess.run(
                cmd,
                cwd=str(workspace),
                env=env,
                stdout=f_out,
                stderr=f_err,
                stdin=subprocess.DEVNULL,
                check=False
            )
            print(f"  Process finished. Exit code: {result.returncode}")
            
            return stream_stdout.read_text(errors='replace'), stream_stderr.read_text(errors='replace'), result.returncode
                
        except Exception as e:
            return "", f"ERROR: {str(e)}", -3


def save_claude_output(config_name: str, timestamp: str, stdout: str, stderr: str) -> Path:
    """Save Claude stdout/stderr to a log file for analysis."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_timestamp = timestamp.replace(' ', '_').replace(':', '-')
    log_filename = f"claude_output_{config_name}_{safe_timestamp}.log"
    log_path = LOGS_DIR / log_filename
    
    log_content = f"""================================================================================
CLAUDE CODE SESSION OUTPUT
================================================================================
Config: {config_name}
Timestamp: {timestamp}
================================================================================

=== STDOUT ===
{stdout if stdout else "(empty)"}

=== STDERR ===
{stderr if stderr else "(empty)"}

================================================================================
"""
    log_path.write_text(log_content)
    return log_path


def analyze_session_errors(
    stdout: str, 
    stderr: str, 
    exit_code: int, 
    session_analysis: Dict
) -> Dict:
    """
    Analyze session logs for errors using structured patterns.
    
    Returns structured error report with:
    - has_errors: bool
    - error_type: str (timeout, api_error, auth_error, tool_error, unknown)
    - error_summary: str
    - recommendations: list[str]
    """
    errors = {
        "has_errors": False,
        "error_type": "none",
        "error_summary": "",
        "recommendations": [],
        "details": {}
    }
    
    # Check for timeout
    if exit_code == -1 or "TIMEOUT" in stderr:
        errors["has_errors"] = True
        errors["error_type"] = "timeout"
        errors["error_summary"] = f"Claude session timed out after {CLAUDE_TIMEOUT}s"
        errors["recommendations"] = [
            "Check if Claude CLI can connect to proxy",
            "Verify ANTHROPIC_BASE_URL is set correctly",
            "Check proxy logs for incoming requests",
            "Try increasing CLAUDE_TIMEOUT if task is complex"
        ]
        return errors
    
    # Check for API errors in session analysis
    if session_analysis.get('error_count', 0) > 0:
        errors["has_errors"] = True
        api_errors = session_analysis.get('errors', [])
        
        # Classify error type
        error_msgs = [e.get('error', '') for e in api_errors]
        all_errors = ' '.join(error_msgs).lower()
        
        if 'auth' in all_errors or '401' in all_errors or 'unauthorized' in all_errors:
            errors["error_type"] = "auth_error"
            errors["error_summary"] = "Authentication failed with API provider"
            errors["recommendations"] = [
                "Check VibeProxy authentication status",
                "Verify API keys are configured correctly",
                "Run cproxy-init to refresh credentials"
            ]
        elif 'rate' in all_errors or '429' in all_errors:
            errors["error_type"] = "rate_limit"
            errors["error_summary"] = "API rate limit exceeded"
            errors["recommendations"] = [
                "Wait before retrying",
                "Switch to different model provider",
                "Check rate limit status on provider dashboard"
            ]
        else:
            errors["error_type"] = "api_error"
            errors["error_summary"] = f"API errors: {error_msgs[:2]}"
            errors["recommendations"] = [
                "Check proxy logs for detailed error",
                "Verify model routing configuration",
                "Check provider API status"
            ]
        
        errors["details"]["api_errors"] = api_errors
        return errors
    
    # Check for non-zero exit code
    if exit_code != 0:
        errors["has_errors"] = True
        errors["error_type"] = "cli_error"
        errors["error_summary"] = f"Claude CLI exited with code {exit_code}"
        errors["details"]["stderr"] = stderr[:500]
        errors["recommendations"] = [
            "Check Claude CLI is installed correctly",
            "Verify workspace permissions",
            "Check stderr for detailed error message"
        ]
        return errors
    
    # Check for no requests (Claude didn't reach proxy)
    if session_analysis.get('total_requests', 0) == 0:
        errors["has_errors"] = True
        errors["error_type"] = "no_requests"
        errors["error_summary"] = "No API requests logged - Claude may not have connected to proxy"
        errors["recommendations"] = [
            "Check ANTHROPIC_BASE_URL environment variable",
            "Verify proxy is running on correct port",
            "Check if Claude CLI is configured for proxy usage"
        ]
        return errors
    
    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE ANALYSIS - FULL SESSION TOKEN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def get_requests_since(since_timestamp: str, include_content: bool = True) -> List[Dict]:
    """Get all API requests from usage_tracking.db since timestamp with full content."""
    if not DB_PATH.exists():
        return []
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Include request/response content for full analysis
        if include_content:
            cursor.execute("""
                SELECT 
                    strftime('%H:%M:%S', timestamp) as time,
                    timestamp,
                    original_model,
                    routed_model,
                    provider,
                    status,
                    input_tokens,
                    output_tokens,
                    thinking_tokens,
                    total_tokens,
                    duration_ms,
                    error_message,
                    request_content,
                    response_content
                FROM api_requests 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            """, (since_timestamp,))
        else:
            cursor.execute("""
                SELECT 
                    strftime('%H:%M:%S', timestamp) as time,
                    original_model,
                    routed_model,
                    status,
                    input_tokens,
                    output_tokens,
                    duration_ms,
                    error_message
                FROM api_requests 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            """, (since_timestamp,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  DB Error: {e}")
        return []


def get_full_session_analysis(since_timestamp: str) -> Dict:
    """
    Comprehensive session analysis with full token and content breakdown.
    
    Returns a detailed analysis including:
    - Total requests and their status
    - Token usage breakdown (input/output/thinking)
    - Request/response content for each API call
    - Error analysis
    - Performance metrics
    """
    requests = get_requests_since(since_timestamp, include_content=True)
    
    if not requests:
        return {
            "total_requests": 0,
            "success_count": 0,
            "error_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_thinking_tokens": 0,
            "avg_duration_ms": 0,
            "errors": [],
            "request_details": [],
            "raw_session_log": "No requests recorded during session"
        }
    
    # Aggregate analysis
    success_count = sum(1 for r in requests if r.get('status') == 'success')
    error_count = sum(1 for r in requests if r.get('status') == 'error')
    total_input = sum(r.get('input_tokens', 0) or 0 for r in requests)
    total_output = sum(r.get('output_tokens', 0) or 0 for r in requests)
    total_thinking = sum(r.get('thinking_tokens', 0) or 0 for r in requests)
    
    durations = [r.get('duration_ms', 0) or 0 for r in requests if r.get('duration_ms')]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    # Extract errors
    errors = []
    for r in requests:
        if r.get('status') == 'error':
            errors.append({
                "time": r.get('time'),
                "model": r.get('original_model'),
                "error": r.get('error_message', 'Unknown error')
            })
    
    # Build detailed request log
    request_details = []
    for r in requests:
        detail = {
            "time": r.get('time'),
            "original_model": r.get('original_model'),
            "routed_model": r.get('routed_model'),
            "provider": r.get('provider'),
            "status": r.get('status'),
            "input_tokens": r.get('input_tokens', 0),
            "output_tokens": r.get('output_tokens', 0),
            "thinking_tokens": r.get('thinking_tokens', 0),
            "duration_ms": r.get('duration_ms', 0),
        }
        
        # Include content if available (truncated for display)
        if r.get('request_content'):
            try:
                req_json = json.loads(r['request_content'])
                # Extract just the messages for readability
                if 'messages' in req_json:
                    detail['request_messages'] = req_json['messages'][-2:] if len(req_json.get('messages', [])) > 2 else req_json['messages']
                else:
                    detail['request_preview'] = r['request_content'][:500]
            except:
                detail['request_preview'] = r['request_content'][:500] if r['request_content'] else None
        
        if r.get('response_content'):
            try:
                resp_json = json.loads(r['response_content'])
                # Extract the response content
                if 'choices' in resp_json:
                    content = resp_json['choices'][0].get('message', {}).get('content', '')
                    detail['response_text'] = content[:1000] if len(content) > 1000 else content
                elif 'content' in resp_json:
                    detail['response_text'] = str(resp_json['content'])[:1000]
                else:
                    detail['response_preview'] = r['response_content'][:500]
            except:
                detail['response_preview'] = r['response_content'][:500] if r['response_content'] else None
        
        if r.get('error_message'):
            detail['error'] = r['error_message']
        
        request_details.append(detail)
    
    # Build raw session log for full debugging
    raw_log_lines = ["=" * 60, "RAW SESSION LOG", "=" * 60, ""]
    for r in requests:
        raw_log_lines.append(f"--- {r.get('time')} ---")
        raw_log_lines.append(f"Model: {r.get('original_model')} -> {r.get('routed_model')}")
        raw_log_lines.append(f"Status: {r.get('status')}")
        raw_log_lines.append(f"Tokens: in={r.get('input_tokens', 0)}, out={r.get('output_tokens', 0)}, think={r.get('thinking_tokens', 0)}")
        raw_log_lines.append(f"Duration: {r.get('duration_ms', 0):.0f}ms")
        
        if r.get('request_content'):
            raw_log_lines.append(f"\nREQUEST:\n{r['request_content'][:2000]}")
        if r.get('response_content'):
            raw_log_lines.append(f"\nRESPONSE:\n{r['response_content'][:2000]}")
        if r.get('error_message'):
            raw_log_lines.append(f"\nERROR: {r['error_message']}")
        
        raw_log_lines.append("")
    
    return {
        "total_requests": len(requests),
        "success_count": success_count,
        "error_count": error_count,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_thinking_tokens": total_thinking,
        "avg_duration_ms": avg_duration,
        "errors": errors,
        "request_details": request_details,
        "raw_session_log": "\n".join(raw_log_lines)
    }


def analyze_db_results(requests: List[Dict]) -> Tuple[bool, List[str]]:
    """Analyze DB results for errors."""
    errors = []
    success = True
    
    for req in requests:
        if req.get('status') == 'error':
            error_msg = req.get('error_message', 'Unknown error')
            errors.append(f"{req.get('time')}: {error_msg[:80]}")
            success = False
    
    return success, errors


# ═══════════════════════════════════════════════════════════════════════════════
# TEST EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def run_single_test(config: Dict) -> TestResult:
    """Run a single test with the given configuration."""
    config_name = config['name']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Use UTC ISO format for DB queries (sqlite Default is UTC)
    # Ensure we look forward from NOW
    db_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    # Generate unique session ID for correlation
    session_id = f"test_{config_name}_{int(time.time())}"

    # Initialize usage tracker for terminal output storage
    usage_tracker = UsageTracker(db_path=str(DB_PATH), enabled=True)
    
    print(f"\n{'='*60}")
    print(f"  Test: {config['description']}")
    print(f"  Config: {config_name}")
    print(f"  Time: {timestamp} (DB Search: >= {db_timestamp})")
    print(f"{'='*60}")
    
    # Create workspace
    workspace = create_test_workspace(config_name)
    print(f"  Workspace: {workspace}")
    print(f"  Skill: {workspace / '.claude' / 'INSTRUCTIONS.md'}")
    
    start_time = time.time()
    
    # Run Claude
    print(f"\n  Running Claude Code...")
    stdout, stderr, exit_code = run_claude_with_skill(workspace, config)
    
    duration = time.time() - start_time
    print(f"  Exit code: {exit_code}")
    print(f"  Duration: {duration:.1f}s")
    
    # Check for poem.txt
    poem_file = workspace / "poem.txt"
    poem_created = poem_file.exists()
    poem_content = poem_file.read_text() if poem_created else ""
    
    print(f"  Poem created: {poem_created}")
    if poem_created:
        print(f"  Poem preview: {poem_content[:100]}...")
    
    # Check if folder was listed (look for ls output in stdout)
    folder_listed = any(x in stdout.lower() for x in ['poem.txt', 'directory', 'listing', 'contents'])
    
    # Get DB requests and full session analysis
    requests = get_requests_since(db_timestamp, include_content=False)
    session_analysis = get_full_session_analysis(db_timestamp)
    
    print(f"  DB requests: {len(requests)}")
    print(f"  Session tokens: in={session_analysis['total_input_tokens']}, out={session_analysis['total_output_tokens']}, think={session_analysis['total_thinking_tokens']}")
    print(f"  Success/Error: {session_analysis['success_count']}/{session_analysis['error_count']}")
    
    # Save Claude output to log file for analysis
    claude_log_path = save_claude_output(config_name, timestamp, stdout, stderr)
    print(f"  Claude log: {claude_log_path}")
    
    # Perform structured error analysis
    error_analysis = analyze_session_errors(stdout, stderr, exit_code, session_analysis)
    if error_analysis['has_errors']:
        print(f"\n  ⚠️ ERROR DETECTED: {error_analysis['error_type']}")
        print(f"  Summary: {error_analysis['error_summary']}")
        print(f"  Recommendations:")
        for rec in error_analysis['recommendations'][:3]:
            print(f"    - {rec}")
    
    # Analyze DB
    db_success, db_errors = analyze_db_results(requests)

    # Determine overall success - must have no error analysis issues too
    success = poem_created and exit_code == 0 and db_success and not error_analysis['has_errors']

    # Store terminal output in database for correlation
    prompt = "Please create a poem about coding and save it as poem.txt, then list the folder contents."
    usage_tracker.log_terminal_output(
        session_id=session_id,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        test_config=config_name,
        workspace_path=str(workspace),
        prompt=prompt,
        duration_seconds=duration,
        poem_created=poem_created,
        poem_content=poem_content,
        folder_listed=folder_listed,
        success=success,
        error_message=error_analysis.get('error_summary') if error_analysis['has_errors'] else None
    )
    print(f"  Terminal output stored in DB with session_id: {session_id}")

    # Cleanup
    cleanup_workspace(workspace)

    return TestResult(
        config_name=config_name,
        timestamp=timestamp,
        success=success,
        poem_created=poem_created,
        poem_content=poem_content,
        folder_listed=folder_listed,
        claude_exit_code=exit_code,
        claude_stdout=stdout[:2000] if stdout else "",
        claude_stderr=stderr[:500] if stderr else "",
        db_requests=requests,
        db_errors=db_errors,
        duration_seconds=duration,
        session_analysis=session_analysis,
        error_message=stderr[:200] if stderr and exit_code != 0 else None
    )


def run_all_tests(max_retries: int = 3) -> List[TestResult]:
    """Run all tests with retry logic."""
    all_results = []
    
    for config in TEST_CONFIGS:
        success = False
        retry_count = 0
        
        while not success and retry_count < max_retries:
            if retry_count > 0:
                print(f"\n  Retry {retry_count}/{max_retries}...")
                time.sleep(2)  # Brief pause before retry
            
            result = run_single_test(config)
            all_results.append(result)
            success = result.success
            retry_count += 1
        
        if success:
            print(f"\n  ✅ PASSED: {config['name']}")
        else:
            print(f"\n  ❌ FAILED after {retry_count} attempts: {config['name']}")
    
    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def generate_results_table(results: List[TestResult]) -> str:
    """Generate a formatted results table with full session analysis."""
    lines = []
    lines.append("\n" + "="*80)
    lines.append("  TEST RESULTS TABLE")
    lines.append("="*80)
    lines.append("")
    
    # Summary table with token columns
    lines.append("| Timestamp | Config | Status | Poem | Duration | In Tokens | Out Tokens | Errors |")
    lines.append("|-----------|--------|--------|------|----------|-----------|------------|--------|")
    
    for r in results:
        status = "✅ PASS" if r.success else "❌ FAIL"
        poem = "✅" if r.poem_created else "❌"
        duration = f"{r.duration_seconds:.1f}s"
        in_tokens = r.session_analysis.get('total_input_tokens', 0)
        out_tokens = r.session_analysis.get('total_output_tokens', 0)
        error_count = r.session_analysis.get('error_count', 0)
        
        lines.append(f"| {r.timestamp} | {r.config_name} | {status} | {poem} | {duration} | {in_tokens} | {out_tokens} | {error_count} |")
    
    lines.append("")
    
    # Detail section for each test
    lines.append("-"*80)
    lines.append("  DETAILED RESULTS WITH SESSION ANALYSIS")
    lines.append("-"*80)
    
    # Create logs directory
    logs_dir = PROJECT_ROOT / "tests" / "integration" / "session_logs"
    logs_dir.mkdir(exist_ok=True)
    
    for r in results:
        lines.append(f"\n### {r.config_name} ({r.timestamp})")
        lines.append(f"- Status: {'PASSED' if r.success else 'FAILED'}")
        lines.append(f"- Exit Code: {r.claude_exit_code}")
        lines.append(f"- Duration: {r.duration_seconds:.1f}s")
        
        # Session token analysis
        sa = r.session_analysis
        lines.append(f"\n#### Session Token Analysis")
        lines.append(f"- Total Requests: {sa.get('total_requests', 0)}")
        lines.append(f"- Success/Error: {sa.get('success_count', 0)}/{sa.get('error_count', 0)}")
        lines.append(f"- Input Tokens: {sa.get('total_input_tokens', 0)}")
        lines.append(f"- Output Tokens: {sa.get('total_output_tokens', 0)}")
        lines.append(f"- Thinking Tokens: {sa.get('total_thinking_tokens', 0)}")
        lines.append(f"- Avg Duration: {sa.get('avg_duration_ms', 0):.0f}ms")
        
        # Poem content
        if r.poem_created:
            lines.append(f"\n#### Poem Content\n```\n{r.poem_content}\n```")
        else:
            lines.append("\n#### Poem: NOT CREATED")
        
        # Request details (brief)
        if sa.get('request_details'):
            lines.append("\n#### Request Details")
            for detail in sa['request_details'][:5]:
                lines.append(f"- {detail.get('time')} | {detail.get('original_model')} -> {detail.get('routed_model')} | {detail.get('status')}")
                if detail.get('response_text'):
                    lines.append(f"  Response: {detail['response_text'][:150]}...")
                if detail.get('error'):
                    lines.append(f"  Error: {detail['error'][:100]}")
        
        # Errors
        if sa.get('errors'):
            lines.append("\n#### Errors")
            for err in sa['errors'][:3]:
                lines.append(f"  - {err.get('time')}: {err.get('error')[:80]}")
        
        if r.error_message:
            lines.append(f"\n#### Claude Error Message\n{r.error_message}")
        
        # Save raw session log to separate file
        if sa.get('raw_session_log') and len(sa['raw_session_log']) > 50:
            log_filename = f"session_{r.config_name}_{r.timestamp.replace(' ', '_').replace(':', '-')}.log"
            log_path = logs_dir / log_filename
            log_path.write_text(sa['raw_session_log'])
            lines.append(f"\n#### Raw Session Log")
            lines.append(f"See: {log_path}")
    
    # Summary
    lines.append("")
    lines.append("="*80)
    passed = sum(1 for r in results if r.success)
    total = len(results)
    total_input = sum(r.session_analysis.get('total_input_tokens', 0) for r in results)
    total_output = sum(r.session_analysis.get('total_output_tokens', 0) for r in results)
    lines.append(f"  SUMMARY: {passed}/{total} tests passed")
    lines.append(f"  Total Tokens Used: {total_input} input, {total_output} output")
    lines.append(f"  Session logs saved to: {logs_dir}")
    lines.append("="*80)
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run skill-based E2E tests."""
    print("\n" + "="*70)
    print("  SKILL-BASED E2E TEST RUNNER")
    print("  Testing Claude Code with poem creation skill")
    print("="*70)
    
    # Check prerequisites
    print("\n  Checking prerequisites...")
    
    # Check proxy
    try:
        import urllib.request
        urllib.request.urlopen(f"{PROXY_URL}/health", timeout=5)
        print("  ✅ Proxy is running")
    except Exception as e:
        print(f"  ❌ Proxy not available: {e}")
        return 1
    
    # Check database
    if DB_PATH.exists():
        print(f"  ✅ Database exists: {DB_PATH}")
    else:
        print(f"  ⚠️ Database not found (will be created)")
    
    # Run tests
    results = run_all_tests(max_retries=2)
    
    # Generate and print table
    table = generate_results_table(results)
    print(table)
    
    # Write results to file
    results_file = PROJECT_ROOT / "tests" / "integration" / "test_results.txt"
    results_file.write_text(table)
    print(f"\n  Results saved to: {results_file}")
    
    # Return exit code based on results
    passed = sum(1 for r in results if r.success)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
