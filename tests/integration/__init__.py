"""
Integration tests for Claude Code Proxy.

This package contains end-to-end tests that:
- Start the proxy with various model configurations
- Run Claude Code CLI commands
- Verify file operations and proxy behavior
- Test multiple provider combinations
"""

from .model_configs import ModelConfig, ALL_CONFIGS, QUICK_CONFIGS
from .validators import (
    ProxyLogValidator,
    ClaudeOutputValidator, 
    FileSystemValidator,
    run_all_validations,
)
