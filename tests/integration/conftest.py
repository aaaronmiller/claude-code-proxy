"""
Pytest fixtures for E2E integration tests.

Provides fixtures for:
- Starting/stopping the proxy server
- Creating test workspaces
- Model configuration injection
"""

import os
import sys
import time
import signal
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Tuple, Optional
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from .model_configs import ModelConfig, ALL_CONFIGS, QUICK_CONFIGS


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8099  # Use different port to avoid conflicts with running proxy
PROXY_STARTUP_TIMEOUT = 15  # seconds
CLAUDE_CODE_TIMEOUT = 120  # seconds per operation


def is_vibeproxy_available() -> bool:
    """Check if VibeProxy is running on port 8317."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8317))
        sock.close()
        return result == 0
    except Exception:
        return False


def is_openrouter_configured() -> bool:
    """Check if OpenRouter API key is configured."""
    return bool(os.getenv('OPENROUTER_API_KEY') or os.getenv('PROVIDER_API_KEY'))


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def test_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create an isolated test workspace directory.
    
    This directory is where Claude Code will create files during tests.
    Cleaned up automatically after the test.
    """
    workspace = tmp_path / "claude_test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal .claude directory to indicate this is a workspace
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(exist_ok=True)
    
    yield workspace
    
    # Cleanup is automatic with tmp_path


@pytest.fixture(scope="function")
def proxy_process(
    request,
    model_config: ModelConfig,
) -> Generator[Tuple[subprocess.Popen, str], None, None]:
    """
    Start the proxy server with the specified model configuration.
    
    Yields:
        Tuple of (process, log_path) for the running proxy
    """
    # Check requirements
    if model_config.requires_vibeproxy and not is_vibeproxy_available():
        pytest.skip("VibeProxy not available on port 8317")
    
    if model_config.requires_openrouter and not is_openrouter_configured():
        pytest.skip("OpenRouter API key not configured")
    
    # Create log file
    log_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    log_path = log_file.name
    
    # Build environment
    env = os.environ.copy()
    env['BIG_MODEL'] = model_config.big_model
    env['MIDDLE_MODEL'] = model_config.middle_model
    env['SMALL_MODEL'] = model_config.small_model
    env['HOST'] = PROXY_HOST
    env['PORT'] = str(PROXY_PORT)
    env['LOG_LEVEL'] = 'DEBUG'
    
    # Set base URL based on config
    if 'vibeproxy' in model_config.big_model.lower():
        env['PROVIDER_BASE_URL'] = 'http://127.0.0.1:8317/v1'
    elif 'openrouter' in model_config.big_model.lower():
        env['PROVIDER_BASE_URL'] = 'https://openrouter.ai/api/v1'
    
    # Start proxy
    cmd = [sys.executable, "start_proxy.py"]
    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
    )
    
    # Wait for startup
    start_time = time.time()
    while time.time() - start_time < PROXY_STARTUP_TIMEOUT:
        # Check if process is still running
        if process.poll() is not None:
            log_file.close()
            with open(log_path, 'r') as f:
                logs = f.read()
            pytest.fail(f"Proxy failed to start. Logs:\n{logs[:2000]}")
        
        # Check if port is listening
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((PROXY_HOST, PROXY_PORT))
            sock.close()
            if result == 0:
                break
        except Exception:
            pass
        
        time.sleep(0.5)
    else:
        process.terminate()
        log_file.close()
        with open(log_path, 'r') as f:
            logs = f.read()
        pytest.fail(f"Proxy startup timeout. Logs:\n{logs[:2000]}")
    
    # Small delay for full initialization
    time.sleep(1)
    
    yield process, log_path
    
    # Cleanup
    log_file.close()
    
    # Terminate proxy
    if process.poll() is None:
        try:
            # Try graceful shutdown first
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    
    # Optionally clean up log file
    # os.unlink(log_path)


@pytest.fixture(params=QUICK_CONFIGS, ids=lambda c: c.name)
def model_config(request) -> ModelConfig:
    """
    Parametrized fixture providing different model configurations.
    
    Use QUICK_CONFIGS for faster testing, ALL_CONFIGS for comprehensive testing.
    """
    return request.param


@pytest.fixture
def claude_runner(test_workspace: Path):
    """
    Factory fixture to run Claude Code CLI commands.
    
    Returns a function that runs Claude Code with the specified prompt.
    """
    def run_claude(
        prompt: str,
        timeout: int = CLAUDE_CODE_TIMEOUT,
        api_url: str = f"http://{PROXY_HOST}:{PROXY_PORT}",
    ) -> Tuple[str, str, int]:
        """
        Run Claude Code CLI with a prompt.
        
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        # Build command
        # Claude Code CLI uses ANTHROPIC_BASE_URL for API endpoint
        env = os.environ.copy()
        env['ANTHROPIC_BASE_URL'] = api_url
        env['ANTHROPIC_API_KEY'] = 'pass'  # Proxy handles auth
        
        cmd = [
            'claude',
            '--print',  # Print output instead of interactive mode
            '--dangerously-skip-permissions',  # Skip permission prompts for testing
            '-p', prompt,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(test_workspace),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout expired", -1
        except FileNotFoundError:
            pytest.skip("Claude Code CLI not installed")
            return "", "", -1
    
    return run_claude


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_proxy_logs(log_path: str) -> str:
    """Read proxy logs from file."""
    try:
        with open(log_path, 'r') as f:
            return f.read()
    except Exception:
        return ""


def wait_for_file(workspace: Path, filename: str, timeout: int = 30) -> bool:
    """Wait for a file to appear in the workspace."""
    start = time.time()
    while time.time() - start < timeout:
        if (workspace / filename).exists():
            return True
        time.sleep(0.5)
    return False
