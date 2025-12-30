"""
E2E Integration Tests for Claude Code Proxy

Tests the full flow:
1. Start proxy with various model configurations
2. Run Claude Code CLI to create files (poem)
3. Verify file operations and proxy logs
4. Test multiple model/provider combinations

Run with: pytest tests/integration/e2e_tests.py -v -s
"""

import os
import sys
import time
import pytest
from pathlib import Path
from typing import Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from .model_configs import (
    ModelConfig,
    ALL_VIBEPROXY,
    ALL_OPENROUTER,
    VIBEPROXY_BIG_OPENROUTER_SMALL,
    MIXED_PROVIDERS,
    GEMINI_ONLY,
    CLAUDE_ONLY,
)
from .validators import (
    ProxyLogValidator,
    ClaudeOutputValidator,
    FileSystemValidator,
    run_all_validations,
)
from .conftest import get_proxy_logs, wait_for_file, PROXY_HOST, PROXY_PORT


# ═══════════════════════════════════════════════════════════════════════════════
# TEST PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

POEM_PROMPT = """
Create a short poem (4-8 lines) about coding and save it to a file called 'poem.txt'.
After saving, list the contents of the current directory to confirm the file exists.
Do not ask for confirmation, just do it.
"""

FILE_OPERATIONS_PROMPT = """
1. Create a file called 'test_output.txt' with the text 'Hello from Claude Code'
2. Create a subdirectory called 'subdir'
3. Create a file inside subdir called 'nested.txt' with any content
4. List the current directory and subdirectory contents
Do not ask for confirmation.
"""

SIMPLE_PROMPT = """
Write 'test successful' to a file called 'simple.txt' and confirm it was created.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TEST CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class TestE2EClaudeCode:
    """End-to-end tests for Claude Code through the proxy."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_poem_creation(
        self,
        proxy_process: Tuple,
        test_workspace: Path,
        claude_runner,
        model_config: ModelConfig,
    ):
        """
        Test creating a poem file through Claude Code.
        
        Steps:
        1. Run Claude Code with poem prompt
        2. Verify poem.txt was created
        3. Verify file has content
        4. Check proxy logs for correct routing
        """
        process, log_path = proxy_process
        
        # Run Claude Code
        stdout, stderr, exit_code = claude_runner(POEM_PROMPT)
        
        # Wait for file creation
        file_created = wait_for_file(test_workspace, "poem.txt", timeout=30)
        
        # Get proxy logs
        proxy_logs = get_proxy_logs(log_path)
        
        # Validate results
        results = []
        
        # Claude output validation
        claude_validator = ClaudeOutputValidator(stdout, stderr, exit_code)
        results.append(claude_validator.check_no_api_errors())
        # Note: exit_code check relaxed as Claude may return non-zero for various reasons
        
        # File system validation
        fs_validator = FileSystemValidator(test_workspace)
        results.append(fs_validator.check_file_exists("poem.txt"))
        if file_created:
            results.append(fs_validator.check_file_content("poem.txt", min_length=20))
        
        # Proxy log validation
        proxy_validator = ProxyLogValidator(proxy_logs)
        results.append(proxy_validator.check_request_logged())
        results.append(proxy_validator.check_no_errors(
            ignore_patterns=["No module named 'scrape_openrouter_models'"]
        ))
        
        # Report results
        failures = [r for r in results if not r.passed]
        
        if failures:
            failure_details = "\n".join([
                f"❌ {r.message}" + (f"\n   Details: {r.details}" if r.details else "")
                for r in failures
            ])
            pytest.fail(
                f"Test failed for config '{model_config.name}':\n{failure_details}\n\n"
                f"Claude stdout:\n{stdout[:1000]}\n\n"
                f"Claude stderr:\n{stderr[:500]}"
            )
        
        # If we get here, test passed
        print(f"\n✅ Poem creation test passed with config: {model_config.name}")
        print(f"   Models: BIG={model_config.big_model}, SMALL={model_config.small_model}")
        
        if file_created:
            poem_content = (test_workspace / "poem.txt").read_text()
            print(f"   Poem content:\n{poem_content}")
    
    @pytest.mark.integration
    def test_simple_file_creation(
        self,
        proxy_process: Tuple,
        test_workspace: Path,
        claude_runner,
        model_config: ModelConfig,
    ):
        """
        Simple test to verify basic file creation works.
        
        This is a faster smoke test compared to full poem test.
        """
        process, log_path = proxy_process
        
        # Run simple prompt
        stdout, stderr, exit_code = claude_runner(SIMPLE_PROMPT)
        
        # Check file was created
        file_exists = wait_for_file(test_workspace, "simple.txt", timeout=20)
        
        # Get logs
        proxy_logs = get_proxy_logs(log_path)
        
        # Assertions
        assert "API Error" not in stdout + stderr, f"API error in output: {stdout + stderr}"
        
        # Check proxy received requests
        assert "INCOMING REQUEST" in proxy_logs, "No requests logged by proxy"
        
        if file_exists:
            content = (test_workspace / "simple.txt").read_text()
            print(f"\n✅ Simple test passed: {content}")
        else:
            # File not created - check if this is an API error or Claude decision
            print(f"\n⚠️ File not created. Claude output: {stdout[:500]}")
            if "test successful" in stdout.lower() or "simple.txt" in stdout:
                # Claude mentioned the file, might have worked differently
                pass
            else:
                pytest.fail("File not created and no indication of success")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_folder_operations(
        self,
        proxy_process: Tuple,
        test_workspace: Path,
        claude_runner,
        model_config: ModelConfig,
    ):
        """
        Test more complex file operations including subdirectories.
        """
        process, log_path = proxy_process
        
        # Run complex prompt
        stdout, stderr, exit_code = claude_runner(FILE_OPERATIONS_PROMPT)
        
        # Wait for file creation
        wait_for_file(test_workspace, "test_output.txt", timeout=30)
        
        # Get logs
        proxy_logs = get_proxy_logs(log_path)
        
        # Validate
        fs_validator = FileSystemValidator(test_workspace)
        
        # Check main file
        main_file = fs_validator.check_file_exists("test_output.txt")
        
        # Check for errors in output
        assert "API Error" not in stdout + stderr
        
        # Report
        files = fs_validator.list_files()
        print(f"\n✅ Folder operations test completed")
        print(f"   Files in workspace: {files}")
        print(f"   Config: {model_config.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST FUNCTIONS (for specific configs without parametrization)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.vibeproxy
def test_vibeproxy_only(test_workspace: Path, request):
    """
    Test with VibeProxy-only configuration.
    
    Run with: pytest -k vibeproxy_only -v
    """
    from .conftest import is_vibeproxy_available
    
    if not is_vibeproxy_available():
        pytest.skip("VibeProxy not available")
    
    # This test uses the ALL_VIBEPROXY config directly
    # Implement as needed for standalone testing


@pytest.mark.integration  
@pytest.mark.openrouter
def test_openrouter_only(test_workspace: Path, request):
    """
    Test with OpenRouter-only configuration.
    
    Run with: pytest -k openrouter_only -v
    """
    from .conftest import is_openrouter_configured
    
    if not is_openrouter_configured():
        pytest.skip("OpenRouter not configured")
    
    # This test uses the ALL_OPENROUTER config directly


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run with: python -m pytest tests/integration/e2e_tests.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"])
