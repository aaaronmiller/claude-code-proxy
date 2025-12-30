"""
Output validators for E2E integration tests.

Validates proxy logs, Claude Code output, and file system state.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    details: Optional[str] = None


class ProxyLogValidator:
    """Validates proxy server logs."""
    
    def __init__(self, log_content: str):
        self.log_content = log_content
        self.lines = log_content.split('\n')
    
    def check_no_errors(self, ignore_patterns: List[str] = None) -> ValidationResult:
        """Check that no ERROR level logs are present."""
        ignore_patterns = ignore_patterns or []
        error_lines = []
        
        for line in self.lines:
            if 'ERROR' in line:
                # Check if this error should be ignored
                should_ignore = any(pattern in line for pattern in ignore_patterns)
                if not should_ignore:
                    error_lines.append(line)
        
        if error_lines:
            return ValidationResult(
                passed=False,
                message=f"Found {len(error_lines)} unexpected ERROR(s) in proxy logs",
                details='\n'.join(error_lines[:5])  # First 5 errors
            )
        
        return ValidationResult(passed=True, message="No unexpected errors in proxy logs")
    
    def check_request_logged(self, request_patterns: list = None) -> ValidationResult:
        """Check that at least one API request was logged."""
        request_patterns = request_patterns or [
            "POST /v1/chat/completions",
            "POST /v1/messages",
            "chat completion request",
            "v1/chat/completions",
            "v1/messages",
        ]
        
        request_count = 0
        for line in self.lines:
            if any(pattern.lower() in line.lower() for pattern in request_patterns):
                request_count += 1
        
        if request_count == 0:
            return ValidationResult(
                passed=False,
                message="No API requests logged by proxy",
                details="Proxy may not have received any Claude Code API requests. Check if Claude CLI is configured correctly."
            )
        
        return ValidationResult(
            passed=True,
            message=f"Logged {request_count} API request(s)"
        )
    
    def check_model_routing(self, expected_provider: str) -> ValidationResult:
        """Check that requests were routed to the expected provider."""
        # Look for routing indicators in logs
        provider_indicators = {
            'vibeproxy': ['127.0.0.1:8317', 'VibeProxy'],
            'openrouter': ['openrouter.ai', 'OpenRouter'],
            'openai': ['api.openai.com', 'OpenAI'],
            'anthropic': ['api.anthropic.com', 'Anthropic'],
            'google': ['googleapis.com', 'Gemini'],
        }
        
        indicators = provider_indicators.get(expected_provider.lower(), [])
        found = any(
            any(ind in line for ind in indicators)
            for line in self.lines
        )
        
        if not found:
            return ValidationResult(
                passed=False,
                message=f"Expected routing to {expected_provider} not found in logs"
            )
        
        return ValidationResult(
            passed=True,
            message=f"Confirmed routing to {expected_provider}"
        )


class ClaudeOutputValidator:
    """Validates Claude Code CLI output."""
    
    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
    
    def check_exit_code(self, expected: int = 0) -> ValidationResult:
        """Check exit code matches expected."""
        if self.exit_code != expected:
            return ValidationResult(
                passed=False,
                message=f"Exit code {self.exit_code}, expected {expected}",
                details=self.stderr[:500] if self.stderr else None
            )
        return ValidationResult(passed=True, message=f"Exit code {self.exit_code} as expected")
    
    def check_no_api_errors(self) -> ValidationResult:
        """Check for API error indicators in output."""
        error_patterns = [
            r'API Error:',
            r'Error: \d{3}',
            r'rate_limit',
            r'unauthorized',
            r'authentication failed',
        ]
        
        combined = self.stdout + self.stderr
        for pattern in error_patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return ValidationResult(
                    passed=False,
                    message=f"API error pattern found: {pattern}",
                    details=combined[:500]
                )
        
        return ValidationResult(passed=True, message="No API errors detected")
    
    def check_task_completion(self, task_indicators: List[str]) -> ValidationResult:
        """Check that task completion indicators are present in output."""
        combined = self.stdout + self.stderr
        found = [ind for ind in task_indicators if ind.lower() in combined.lower()]
        
        if not found:
            return ValidationResult(
                passed=False,
                message=f"Task completion indicators not found",
                details=f"Looked for: {task_indicators}"
            )
        
        return ValidationResult(
            passed=True,
            message=f"Found task indicators: {found}"
        )


class FileSystemValidator:
    """Validates file system state after Claude Code operations."""
    
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path
    
    def check_file_exists(self, filename: str) -> ValidationResult:
        """Check that a file exists in the workspace."""
        file_path = self.workspace / filename
        
        if not file_path.exists():
            return ValidationResult(
                passed=False,
                message=f"File not found: {filename}",
                details=f"Expected at: {file_path}"
            )
        
        return ValidationResult(passed=True, message=f"File exists: {filename}")
    
    def check_file_content(self, filename: str, min_length: int = 20) -> ValidationResult:
        """Check that file has minimum content length."""
        file_path = self.workspace / filename
        
        if not file_path.exists():
            return ValidationResult(
                passed=False,
                message=f"File not found: {filename}"
            )
        
        content = file_path.read_text()
        if len(content) < min_length:
            return ValidationResult(
                passed=False,
                message=f"File content too short: {len(content)} chars (min: {min_length})",
                details=content
            )
        
        return ValidationResult(
            passed=True,
            message=f"File has {len(content)} characters"
        )
    
    def check_file_contains(self, filename: str, patterns: List[str]) -> ValidationResult:
        """Check that file contains specific patterns."""
        file_path = self.workspace / filename
        
        if not file_path.exists():
            return ValidationResult(
                passed=False,
                message=f"File not found: {filename}"
            )
        
        content = file_path.read_text().lower()
        found = [p for p in patterns if p.lower() in content]
        missing = [p for p in patterns if p.lower() not in content]
        
        if missing:
            return ValidationResult(
                passed=False,
                message=f"Missing patterns in file: {missing}",
                details=f"Found: {found}"
            )
        
        return ValidationResult(passed=True, message=f"All patterns found: {patterns}")
    
    def list_files(self) -> List[str]:
        """List all files in workspace."""
        return [f.name for f in self.workspace.iterdir() if f.is_file()]


class UsageTrackingValidator:
    """Validates requests logged in usage_tracking.db."""
    
    def __init__(self, db_path: str = "usage_tracking.db"):
        self.db_path = db_path
    
    def get_recent_requests(self, limit: int = 20, since_timestamp: str = None) -> List[dict]:
        """Get recent API requests from the database."""
        import sqlite3
        
        if not os.path.exists(self.db_path):
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if since_timestamp:
                cursor.execute("""
                    SELECT * FROM api_requests 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (since_timestamp, limit))
            else:
                cursor.execute("""
                    SELECT * FROM api_requests 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            return []
    
    def check_requests_received(self, min_count: int = 1, since_timestamp: str = None) -> ValidationResult:
        """Check that at least min_count requests were received."""
        requests = self.get_recent_requests(limit=50, since_timestamp=since_timestamp)
        
        if len(requests) < min_count:
            return ValidationResult(
                passed=False,
                message=f"Expected at least {min_count} request(s), found {len(requests)}",
                details="Check if Claude Code is sending requests to the proxy"
            )
        
        return ValidationResult(
            passed=True,
            message=f"Found {len(requests)} request(s) in database"
        )
    
    def check_success_rate(self, min_rate: float = 0.5, since_timestamp: str = None) -> ValidationResult:
        """Check that success rate meets minimum threshold."""
        requests = self.get_recent_requests(limit=100, since_timestamp=since_timestamp)
        
        if not requests:
            return ValidationResult(
                passed=False,
                message="No requests found in database"
            )
        
        success_count = sum(1 for r in requests if r.get('status') == 'success')
        rate = success_count / len(requests)
        
        if rate < min_rate:
            error_messages = [r.get('error_message', 'Unknown') for r in requests if r.get('status') == 'error'][:3]
            return ValidationResult(
                passed=False,
                message=f"Success rate {rate:.0%} below threshold {min_rate:.0%}",
                details=f"Recent errors: {error_messages}"
            )
        
        return ValidationResult(
            passed=True,
            message=f"Success rate {rate:.0%} ({success_count}/{len(requests)})"
        )
    
    def check_model_routing(self, expected_model: str = None, since_timestamp: str = None) -> ValidationResult:
        """Check that requests were routed to the expected model."""
        requests = self.get_recent_requests(limit=20, since_timestamp=since_timestamp)
        
        if not requests:
            return ValidationResult(
                passed=False,
                message="No requests found in database"
            )
        
        routed_models = set(r.get('routed_model') for r in requests)
        
        if expected_model:
            if expected_model not in routed_models:
                return ValidationResult(
                    passed=False,
                    message=f"Expected model '{expected_model}' not found in routing",
                    details=f"Found: {routed_models}"
                )
        
        return ValidationResult(
            passed=True,
            message=f"Routed to models: {routed_models}"
        )
    
    def get_error_summary(self, since_timestamp: str = None) -> dict:
        """Get summary of errors for debugging."""
        requests = self.get_recent_requests(limit=50, since_timestamp=since_timestamp)
        
        errors = [r for r in requests if r.get('status') == 'error']
        
        return {
            'total_requests': len(requests),
            'error_count': len(errors),
            'error_messages': [r.get('error_message') for r in errors[:5]],
            'models_attempted': list(set(r.get('original_model') for r in requests)),
            'models_routed': list(set(r.get('routed_model') for r in requests)),
        }


def run_all_validations(
    proxy_logs: str,
    claude_stdout: str,
    claude_stderr: str,
    claude_exit_code: int,
    workspace: Path,
    expected_files: List[str],
    expected_provider: str = None
) -> Tuple[bool, List[ValidationResult]]:
    """
    Run all validations and return overall result.
    
    Returns:
        Tuple of (all_passed, list of ValidationResult)
    """
    results = []
    
    # Proxy validations
    proxy_validator = ProxyLogValidator(proxy_logs)
    results.append(proxy_validator.check_no_errors())
    results.append(proxy_validator.check_request_logged())
    if expected_provider:
        results.append(proxy_validator.check_model_routing(expected_provider))
    
    # Claude output validations
    claude_validator = ClaudeOutputValidator(claude_stdout, claude_stderr, claude_exit_code)
    results.append(claude_validator.check_exit_code())
    results.append(claude_validator.check_no_api_errors())
    
    # File system validations
    fs_validator = FileSystemValidator(workspace)
    for filename in expected_files:
        results.append(fs_validator.check_file_exists(filename))
        results.append(fs_validator.check_file_content(filename))
    
    all_passed = all(r.passed for r in results)
    return all_passed, results
