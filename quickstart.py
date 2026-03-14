#!/usr/bin/env python3
"""
Quick Start Script for The Ultimate Proxy

This script automates the complete setup process:
- Checks system requirements (Python, uv/pip)
- Creates virtual environment (if needed)
- Installs dependencies
- Sets up environment configuration
- Initializes the database
- Launches the proxy

Usage:
    python quickstart.py              # Interactive setup
    python quickstart.py --non-interactive  # Auto setup with defaults
    python quickstart.py --help       # Show help
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple


# Colors for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def run_command(
    command: list, cwd: Optional[Path] = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=False, check=check)
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise e
        return e


def check_python_version() -> Tuple[bool, str]:
    """Check if Python 3.9+ is installed."""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 9:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return (
            False,
            f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)",
        )
    except Exception as e:
        return False, f"Error checking Python version: {e}"


def check_uv() -> bool:
    """Check if uv is installed."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def check_pip() -> bool:
    """Check if pip is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"], capture_output=True, text=True
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def ensure_gcc_compat() -> bool:
    """Ensure gcc-12 is available or set CC environment variable as fallback."""
    if not sys.platform.startswith("linux"):
        return True

    try:
        result = subprocess.run(["gcc-12", "--version"], capture_output=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(["gcc", "--version"], capture_output=True)
        if result.returncode == 0:
            print_warning(
                "gcc-12 not found, using gcc and setting CC environment variable"
            )
            os.environ["CC"] = "gcc"
            return True
    except FileNotFoundError:
        print_error("gcc not found. Please install gcc to build dependencies.")
        print_info("On Fedora/RHEL: sudo dnf install gcc")
        print_info("On Ubuntu/Debian: sudo apt install gcc")
        return False

    return False


def create_venv(project_root: Path) -> bool:
    """Create a virtual environment if it doesn't exist."""
    venv_dir = project_root / ".venv"

    if venv_dir.exists():
        print_info("Virtual environment already exists")
        return True

    print_info("Creating virtual environment...")
    try:
        run_command([sys.executable, "-m", "venv", str(venv_dir)])
        print_success("Virtual environment created")
        return True
    except Exception as e:
        print_error(f"Failed to create venv: {e}")
        return False


def install_dependencies_uv(project_root: Path) -> bool:
    """Install dependencies using uv."""
    print_info("Installing dependencies with uv...")
    try:
        # Ensure GCC compatibility for building native extensions
        if not ensure_gcc_compat():
            print_error("Cannot install dependencies: build tools missing")
            return False
        run_command(["uv", "sync"], cwd=project_root)
        print_success("Dependencies installed")
        return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def install_dependencies_pip(project_root: Path, venv_path: Path) -> bool:
    """Install dependencies using pip."""
    print_info("Installing dependencies with pip...")

    # Ensure GCC compatibility
    if not ensure_gcc_compat():
        print_error("Cannot install dependencies: build tools missing")
        return False

    # Determine pip executable
    if sys.platform == "win32":
        pip_exe = venv_path / "Scripts" / "pip"
    else:
        pip_exe = venv_path / "bin" / "pip"

    if not pip_exe.exists():
        pip_exe = Path(sys.executable)

    try:
        # Use -e . to install from pyproject.toml
        run_command([str(pip_exe), "install", "-e", "."], cwd=project_root)
        print_success("Dependencies installed")
        return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def setup_environment(project_root: Path, non_interactive: bool = False) -> bool:
    """Create and configure .env file."""
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        print_info(".env file already exists")
        if non_interactive:
            return True

        # Ask if user wants to reconfigure
        try:
            response = input("\n⚙️  .env exists. Reconfigure? [y/N]: ").strip().lower()
            if response not in ["y", "yes"]:
                return True
        except (EOFError, KeyboardInterrupt):
            return True

    print_header("ENVIRONMENT CONFIGURATION")

    # Copy from .env.example or create new
    env_content = {}
    if env_example.exists():
        print_info("Using .env.example as template")
        with open(env_example, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_content[key] = value.strip('"').strip("'")

    # Get user configuration
    print("\n📝 Configure your proxy:\n")

    # Provider selection
    print("Choose your API provider:")
    print("  1. OpenRouter (recommended - access to multiple models)")
    print("  2. OpenAI")
    print("  3. Google Gemini")
    print("  4. VibeProxy (free premium models)")
    print("  5. Skip configuration (edit .env manually later)")

    if not non_interactive:
        try:
            provider_choice = input("\nSelect provider [1-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            provider_choice = "5"
    else:
        provider_choice = "1"  # Default to OpenRouter

    if provider_choice == "1":
        env_content["OPENROUTER_API_KEY"] = "sk-or-v1-your-key-here"
        env_content["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        print_info("Provider: OpenRouter")
        if not non_interactive:
            api_key = input(
                "Enter your OpenRouter API key (or press Enter to skip): "
            ).strip()
            if api_key:
                env_content["OPENROUTER_API_KEY"] = api_key
    elif provider_choice == "2":
        env_content["OPENAI_API_KEY"] = "sk-your-key-here"
        print_info("Provider: OpenAI")
        if not non_interactive:
            api_key = input(
                "Enter your OpenAI API key (or press Enter to skip): "
            ).strip()
            if api_key:
                env_content["OPENAI_API_KEY"] = api_key
    elif provider_choice == "3":
        env_content["GOOGLE_API_KEY"] = "your-key-here"
        env_content["OPENAI_BASE_URL"] = (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        print_info("Provider: Google Gemini")
        if not non_interactive:
            api_key = input(
                "Enter your Google API key (or press Enter to skip): "
            ).strip()
            if api_key:
                env_content["GOOGLE_API_KEY"] = api_key
    elif provider_choice == "4":
        env_content["OPENAI_BASE_URL"] = "http://localhost:8317/v1"
        env_content["OPENAI_API_KEY"] = "vibeproxy-key"
        print_info("Provider: VibeProxy")
        print_warning("Make sure VibeProxy is running on port 8317")
    else:
        print_warning("Skipping API configuration")
        env_content["OPENAI_API_KEY"] = "your-key-here"

    # Model configuration
    if not non_interactive:
        print("\n📦 Configure model routing:")
        use_defaults = input("Use default model routing? [Y/n]: ").strip().lower()
        if use_defaults not in ["n", "no", ""]:
            big_model = input(
                f"BIG_MODEL [{env_content.get('BIG_MODEL', 'anthropic/claude-sonnet-4-20250514')}]: "
            ).strip()
            middle_model = input(
                f"MIDDLE_MODEL [{env_content.get('MIDDLE_MODEL', 'google/gemini-2.0-flash-001')}]: "
            ).strip()
            small_model = input(
                f"SMALL_MODEL [{env_content.get('SMALL_MODEL', 'google/gemini-2.0-flash-001')}]: "
            ).strip()

            if big_model:
                env_content["BIG_MODEL"] = big_model
            if middle_model:
                env_content["MIDDLE_MODEL"] = middle_model
            if small_model:
                env_content["SMALL_MODEL"] = small_model

    # Server configuration
    if not non_interactive:
        print("\n🌐 Server configuration:")
        host = input(f"HOST [{env_content.get('HOST', '0.0.0.0')}]: ").strip()
        port = input(f"PORT [{env_content.get('PORT', '8082')}]: ").strip()

        if host:
            env_content["HOST"] = host
        if port:
            env_content["PORT"] = port

    # Features
    env_content["ENABLE_DASHBOARD"] = "true"
    env_content["TRACK_USAGE"] = "true"

    # Write .env file
    with open(env_file, "w") as f:
        f.write("# Claude Code Proxy Configuration\n")
        f.write("# Generated by quickstart.py\n\n")
        for key, value in env_content.items():
            f.write(f'{key}="{value}"\n')

    print_success(f".env file created at {env_file}")

    # Display next steps
    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("=" * 60)
    if "your-key" in str(env_content.values()) or "sk-or-v1-your" in str(
        env_content.values()
    ):
        print_warning("⚠️  You need to add your actual API key to .env")
        print(f"   Edit: {env_file}")
    print("\nTo start the proxy:")
    print(f"   cd {project_root}")
    print("   python start_proxy.py")
    print("\nTo use with Claude Code:")
    print("   export ANTHROPIC_BASE_URL=http://localhost:8082")
    print("   export ANTHROPIC_API_KEY=pass")
    print("   claude")
    print("=" * 60 + "\n")

    return True


def initialize_database(project_root: Path) -> bool:
    """Initialize the database by running a dry-run."""
    print_info("Initializing database...")

    # The database is created automatically on first run
    # We'll just verify the setup is ready
    db_path = project_root / "usage_tracking.db"

    if db_path.exists():
        print_info("Database already exists")
        return True

    print_success("Database will be created on first run")
    return True


def launch_proxy(project_root: Path, non_interactive: bool = False) -> bool:
    """Launch the proxy server."""
    if not non_interactive:
        print("\n" + "=" * 60)
        print("🚀 Ready to start the proxy!")
        print("=" * 60)
        try:
            response = input("\nStart the proxy now? [Y/n]: ").strip().lower()
            if response in ["n", "no"]:
                print_info("You can start the proxy later with: python start_proxy.py")
                return True
        except (EOFError, KeyboardInterrupt):
            pass

    print_info("Starting proxy server...")
    print("\n" + "=" * 60)
    print("📊 Proxy will be available at: http://localhost:8082")
    print("=" * 60 + "\n")

    try:
        # Use the venv python if available
        venv_python = project_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        run_command([str(venv_python), "start_proxy.py"], cwd=project_root, check=False)
        return True
    except Exception as e:
        print_error(f"Failed to start proxy: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Quick Start Script for The Ultimate Proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quickstart.py              # Interactive setup
  python quickstart.py --non-interactive  # Auto setup with defaults
  python quickstart.py --no-launch    # Setup without launching proxy
        """,
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (use defaults)",
    )

    parser.add_argument(
        "--no-launch", action="store_true", help="Setup without launching the proxy"
    )

    parser.add_argument(
        "--skip-venv", action="store_true", help="Skip virtual environment creation"
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.absolute()

    print_header("🚀 THE ULTIMATE PROXY - QUICK START")

    # Step 1: Check Python version
    print_header("STEP 1: CHECKING REQUIREMENTS")
    python_ok, python_version = check_python_version()
    if python_ok:
        print_success(python_version)
    else:
        print_error(python_version)
        print_error("Please install Python 3.9 or higher")
        print_info("Download from: https://www.python.org/downloads/")
        sys.exit(1)

    # Step 2: Check package manager
    print("\n📦 Checking package manager...")
    use_uv = check_uv()
    use_pip = check_pip()

    if use_uv:
        print_success("uv found - will use for dependency management")
    elif use_pip:
        print_warning("uv not found - will use pip instead")
        print_info(
            "Consider installing uv for faster installs: https://docs.astral.sh/uv/"
        )
    else:
        print_error("Neither uv nor pip found")
        print_error("Please install pip or uv")
        sys.exit(1)

    # Step 3: Create virtual environment
    if not args.skip_venv:
        print_header("STEP 2: CREATING VIRTUAL ENVIRONMENT")
        if not create_venv(project_root):
            print_error("Failed to create virtual environment")
            sys.exit(1)

    # Step 4: Install dependencies
    print_header("STEP 3: INSTALLING DEPENDENCIES")
    if use_uv and not args.skip_venv:
        if not install_dependencies_uv(project_root):
            print_error("Failed to install dependencies")
            sys.exit(1)
    else:
        venv_path = project_root / ".venv"
        if not install_dependencies_pip(project_root, venv_path):
            print_error("Failed to install dependencies")
            sys.exit(1)

    # Step 5: Setup environment
    print_header("STEP 4: CONFIGURING ENVIRONMENT")
    if not setup_environment(project_root, non_interactive=args.non_interactive):
        print_error("Failed to configure environment")
        sys.exit(1)

    # Step 6: Initialize database
    print_header("STEP 5: INITIALIZING DATABASE")
    if not initialize_database(project_root):
        print_warning("Database initialization skipped")

    # Step 7: Launch proxy
    if not args.no_launch:
        print_header("STEP 6: LAUNCH PROXY")
        launch_proxy(project_root, non_interactive=args.non_interactive)
    else:
        print_header("SETUP COMPLETE!")
        print_success("All dependencies installed and configured")
        print("\n📊 To start the proxy:")
        print(f"   cd {project_root}")
        print("   python start_proxy.py")
        print("\n🌐 Web dashboard: http://localhost:8082")
        print("\n📝 To use with Claude Code:")
        print("   export ANTHROPIC_BASE_URL=http://localhost:8082")
        print("   export ANTHROPIC_API_KEY=pass")
        print("   claude")

    print("\n" + "=" * 60)
    print(f"{Colors.OKGREEN}✨ Setup complete!{Colors.ENDC}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + Colors.WARNING + "Setup cancelled by user" + Colors.ENDC)
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        print("\nPlease check the error message above and try again.")
        print(
            "If the problem persists, visit: https://github.com/holegots/claude-code-proxy/issues"
        )
        sys.exit(1)
