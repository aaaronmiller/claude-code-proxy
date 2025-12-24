#!/usr/bin/env python3
"""
Test runner for Claude Code Proxy

Runs pytest with appropriate configuration and displays results.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run tests with pytest"""
    project_root = Path(__file__).parent

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed")
        print("\nInstall with: uv pip install pytest pytest-asyncio")
        sys.exit(1)

    # Run pytest
    args = [
        "pytest",
        "tests/",
        "-v",  # Verbose
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
    ]

    # Add coverage if requested
    if "--cov" in sys.argv:
        try:
            import pytest_cov
            args.extend([
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term",
            ])
        except ImportError:
            print("⚠️  pytest-cov not installed (skipping coverage)")
            print("   Install with: uv pip install pytest-cov")

    # Add any additional arguments from command line
    args.extend(arg for arg in sys.argv[1:] if arg != "--cov")

    print("🧪 Running tests...\n")
    result = subprocess.run(args, cwd=project_root)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
