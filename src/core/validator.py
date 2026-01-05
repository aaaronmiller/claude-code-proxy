"""
Configuration validation for Claude Code Proxy

Validates environment variables, API keys, and configuration
on startup to catch errors early and provide helpful feedback.
"""

import os
import sys
import requests
from typing import List, Tuple, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

console = Console()


class ConfigValidator:
    """Validates proxy configuration on startup"""

    def __init__(self, config=None):
        """Initialize validator with optional config object"""
        self.config = config
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_all(self, strict: bool = False) -> bool:
        """
        Run all validation checks

        Args:
            strict: If True, warnings are treated as errors

        Returns:
            True if validation passed, False otherwise
        """
        console.print("\n[bold cyan]🔍 Validating configuration...[/bold cyan]\n")

        # Run all checks
        self._check_required_variables()
        self._check_deprecated_variables()
        self._check_model_configuration()
        self._check_hybrid_mode()
        self._check_reasoning_config()
        self._check_api_keys()
        self._check_common_mistakes()
        self._check_port_availability()

        # Display results
        self._display_results()

        # Determine if validation passed
        has_errors = len(self.errors) > 0
        has_critical_warnings = strict and len(self.warnings) > 0

        if has_errors or has_critical_warnings:
            console.print("\n[bold red]❌ Configuration validation failed[/bold red]\n")
            return False
        else:
            console.print("\n[bold green]✅ Configuration validated successfully[/bold green]\n")
            return True

    def _check_required_variables(self):
        """Check that required environment variables are set"""
        # Core variables
        provider_key = os.getenv("PROVIDER_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider_url = os.getenv("PROVIDER_BASE_URL") or os.getenv("OPENAI_BASE_URL")

        if not provider_key:
            self.errors.append(
                "PROVIDER_API_KEY is not set\n"
                "  → Run: python setup_wizard.py\n"
                "  → Or add to .env: PROVIDER_API_KEY=\"your-key-here\""
            )

        if not provider_url:
            self.errors.append(
                "PROVIDER_BASE_URL is not set\n"
                "  → Run: python setup_wizard.py\n"
                "  → Or add to .env: PROVIDER_BASE_URL=\"https://api.provider.com/v1\""
            )

        # Model configuration (at least one should be set)
        big_model = os.getenv("BIG_MODEL")
        middle_model = os.getenv("MIDDLE_MODEL")
        small_model = os.getenv("SMALL_MODEL")

        if not any([big_model, middle_model, small_model]):
            self.errors.append(
                "No models configured (BIG_MODEL, MIDDLE_MODEL, SMALL_MODEL)\n"
                "  → Run: python setup_wizard.py\n"
                "  → Or add to .env: BIG_MODEL=\"your-model-name\""
            )

    def _check_deprecated_variables(self):
        """Warn about deprecated variable names"""
        # User requested to support global keys without warnings.
        # The system supports OPENAI_API_KEY etc. as fallbacks, so we suppress these warnings.
        pass

    def _check_model_configuration(self):
        """Validate model configuration"""
        big_model = os.getenv("BIG_MODEL")
        middle_model = os.getenv("MIDDLE_MODEL")
        small_model = os.getenv("SMALL_MODEL")

        # Check if models are set
        if not big_model:
            self.warnings.append("BIG_MODEL not configured (Claude Opus requests will fail)")

        # MIDDLE_MODEL defaults to BIG_MODEL in config.py, so only warn if neither is set
        if not middle_model and not big_model:
            self.warnings.append("MIDDLE_MODEL not configured (Claude Sonnet requests will fail)")

        if not small_model:
            self.warnings.append("SMALL_MODEL not configured (Claude Haiku requests will fail)")

        # Check for OpenRouter format
        provider_url = os.getenv("PROVIDER_BASE_URL", "")
        if "openrouter.ai" in provider_url:
            for model_name, model_var in [
                (big_model, "BIG_MODEL"),
                (middle_model, "MIDDLE_MODEL"),
                (small_model, "SMALL_MODEL"),
            ]:
                if model_name and "/" not in model_name:
                    self.warnings.append(
                        f"{model_var}=\"{model_name}\" may be incorrect for OpenRouter\n"
                        f"  → OpenRouter models use format: provider/model\n"
                        f"  → Example: anthropic/claude-sonnet-4\n"
                        f"  → Run: python -m src.cli.model_selector"
                    )

    def _check_hybrid_mode(self):
        """Validate hybrid mode configuration"""
        # Import config to check auto-resolved values
        try:
            from src.core.config import config as resolved_config
        except:
            resolved_config = None
            
        for tier in ["BIG", "MIDDLE", "SMALL"]:
            enabled = os.getenv(f"ENABLE_{tier}_ENDPOINT", "").lower() == "true"

            if enabled:
                endpoint = os.getenv(f"{tier}_ENDPOINT")
                api_key = os.getenv(f"{tier}_API_KEY")
                
                # Also check if config has auto-resolved a key
                config_has_key = False
                if resolved_config:
                    config_key = getattr(resolved_config, f"{tier.lower()}_api_key", None)
                    config_has_key = config_key is not None

                if not endpoint:
                    self.errors.append(
                        f"ENABLE_{tier}_ENDPOINT is true but {tier}_ENDPOINT not set\n"
                        f"  → Add: {tier}_ENDPOINT=\"https://api.provider.com/v1\""
                    )

                if not api_key and not config_has_key:
                    self.warnings.append(
                        f"ENABLE_{tier}_ENDPOINT is true but {tier}_API_KEY not set\n"
                        f"  → Add: {tier}_API_KEY=\"your-key\" (or \"dummy\" for local)"
                    )
                elif not api_key and config_has_key:
                    # Auto-detection worked - show info instead of warning
                    provider = getattr(resolved_config, f"{tier.lower()}_provider", "auto")
                    self.info.append(f"{tier} endpoint using auto-detected {provider.upper()} API key")

                self.info.append(f"Hybrid mode enabled for {tier} tier → {endpoint}")


    def _check_reasoning_config(self):
        """Validate reasoning configuration"""
        reasoning_effort = os.getenv("REASONING_EFFORT")
        reasoning_max_tokens = os.getenv("REASONING_MAX_TOKENS")

        if reasoning_effort:
            valid_efforts = ["low", "medium", "high"]
            if reasoning_effort not in valid_efforts:
                self.warnings.append(
                    f"REASONING_EFFORT=\"{reasoning_effort}\" is invalid\n"
                    f"  → Valid values: {', '.join(valid_efforts)}\n"
                    f"  → For OpenAI o-series models"
                )

        if reasoning_max_tokens:
            try:
                tokens = int(reasoning_max_tokens)
                if tokens < 1024 or tokens > 128000:
                    self.warnings.append(
                        f"REASONING_MAX_TOKENS={tokens} is outside recommended range\n"
                        f"  → Claude: 1024-128000 tokens\n"
                        f"  → Gemini: 0-24576 tokens"
                    )
            except ValueError:
                self.errors.append(
                    f"REASONING_MAX_TOKENS=\"{reasoning_max_tokens}\" is not a valid number"
                )

    def _check_api_keys(self):
        """Test API keys with providers and cache results"""
        from src.core.config import validate_api_key_format, set_provider_status

        # Get provider config
        provider_key = os.getenv("PROVIDER_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider_url = os.getenv("PROVIDER_BASE_URL") or os.getenv("OPENAI_BASE_URL")

        if not provider_key or not provider_url:
            return  # Already flagged in required variables check

        # Test main provider and cache result
        result = self._test_api_key(provider_url, provider_key, "Main Provider")
        if result:
            set_provider_status("main", result)

        # Test hybrid endpoints
        for tier in ["BIG", "MIDDLE", "SMALL"]:
            enabled = os.getenv(f"ENABLE_{tier}_ENDPOINT", "").lower() == "true"
            if enabled:
                endpoint = os.getenv(f"{tier}_ENDPOINT")
                api_key = os.getenv(f"{tier}_API_KEY")
                if endpoint and api_key:
                    result = self._test_api_key(endpoint, api_key, f"{tier} Endpoint")
                    if result:
                        set_provider_status(tier.lower(), result)

        # Test all known provider API keys for status caching
        self._test_all_provider_keys()

    def _test_api_key(self, base_url: str, api_key: str, name: str) -> Optional[Dict]:
        """
        Test an API key with a provider and return result for caching.

        Returns:
            Dict with status info, or None if validation skipped
        """
        from src.core.config import validate_api_key_format

        result = {
            "name": name,
            "endpoint": base_url,
            "key_preview": f"{api_key[:10]}..." if api_key and len(api_key) > 10 else api_key,
            "is_valid": False,
            "is_connected": False,
            "status": "unknown",
            "models_available": 0,
        }

        # Skip validation for local providers
        if "localhost" in base_url or "127.0.0.1" in base_url:
            self.info.append(f"{name}: Using local endpoint (skipping validation)")
            result["status"] = "local"
            result["is_valid"] = True
            return result

        # Skip if dummy key (for local models)
        if api_key.lower() in ["dummy", "test", "none"]:
            self.info.append(f"{name}: Using dummy key (skipping validation)")
            result["status"] = "dummy"
            return result

        # First, validate key format
        is_format_valid, format_msg = validate_api_key_format(api_key)
        if not is_format_valid:
            self.warnings.append(f"{name}: {format_msg}")
            result["status"] = "invalid_format"
            return result

        try:
            # Try to list models (common endpoint)
            models_url = f"{base_url.rstrip('/')}/models"

            response = requests.get(
                models_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )

            result["is_connected"] = True

            if response.status_code == 401:
                self.errors.append(
                    f"{name}: Invalid API key (401 Unauthorized)\n"
                    f"  → Check your API key in .env\n"
                    f"  → URL: {base_url}\n"
                    f"  → Key: {api_key[:10]}..."
                )
                result["status"] = "invalid_key"
            elif response.status_code == 403:
                self.warnings.append(
                    f"{name}: API key valid but insufficient permissions (403 Forbidden)\n"
                    f"  → Check your account status\n"
                    f"  → For OpenRouter: Check credits at https://openrouter.ai/settings/credits"
                )
                result["status"] = "no_permission"
                result["is_valid"] = True  # Key is valid, just lacks permissions
            elif response.status_code == 404:
                # Some providers don't have /models endpoint
                self.info.append(f"{name}: Cannot validate (no /models endpoint, assuming valid)")
                result["status"] = "assumed_valid"
                result["is_valid"] = True
            elif response.status_code == 200:
                self.info.append(f"{name}: API key validated ✓")
                result["status"] = "valid"
                result["is_valid"] = True
                # Try to count models
                try:
                    data = response.json()
                    if "data" in data:
                        result["models_available"] = len(data["data"])
                except:
                    pass
            else:
                self.warnings.append(
                    f"{name}: Unexpected response ({response.status_code})\n"
                    f"  → Provider may be experiencing issues"
                )
                result["status"] = f"http_{response.status_code}"

            return result

        except requests.exceptions.Timeout:
            self.warnings.append(
                f"{name}: Connection timeout (provider may be slow)\n"
                f"  → URL: {base_url}"
            )
            result["status"] = "timeout"
            return result
        except requests.exceptions.ConnectionError:
            self.warnings.append(
                f"{name}: Cannot connect to provider\n"
                f"  → Check URL: {base_url}\n"
                f"  → Check internet connection"
            )
            result["status"] = "connection_error"
            return result
        except Exception as e:
            self.warnings.append(
                f"{name}: Validation failed: {str(e)}\n"
                f"  → Assuming configuration is correct"
            )
            result["status"] = "error"
            return result

    def _test_all_provider_keys(self):
        """Test all available provider API keys and cache their status"""
        from src.core.config import validate_api_key_format, set_provider_status

        # Provider configurations: (provider_name, env_var, endpoint)
        providers_to_test = [
            ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
            ("openai", "OPENAI_API_KEY", "https://api.openai.com/v1"),
            ("google", "GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai"),
            ("gemini", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai"),
            ("anthropic", "ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
            ("azure", "AZURE_API_KEY", None),  # Azure needs custom endpoint
        ]

        for provider_name, env_var, default_endpoint in providers_to_test:
            api_key = os.getenv(env_var)
            if not api_key:
                # No key set - mark as unavailable
                set_provider_status(provider_name, {
                    "name": provider_name,
                    "status": "no_key",
                    "is_valid": False,
                    "is_connected": False,
                })
                continue

            # Validate format first
            is_format_valid, format_msg = validate_api_key_format(api_key, provider_name)
            if not is_format_valid:
                set_provider_status(provider_name, {
                    "name": provider_name,
                    "status": "invalid_format",
                    "is_valid": False,
                    "is_connected": False,
                    "message": format_msg,
                })
                continue

            # Skip live testing for now (too slow on startup) - just mark as format-valid
            set_provider_status(provider_name, {
                "name": provider_name,
                "status": "key_set",
                "is_valid": True,  # Format valid, assume working
                "is_connected": False,  # Not tested yet
                "key_preview": f"{api_key[:10]}..." if len(api_key) > 10 else api_key,
            })

    def _check_common_mistakes(self):
        """Check for common configuration mistakes"""
        # Check if API key looks valid
        provider_key = os.getenv("PROVIDER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if provider_key:
            if len(provider_key) < 20:
                self.warnings.append(
                    f"PROVIDER_API_KEY is very short ({len(provider_key)} chars)\n"
                    f"  → Most API keys are 30+ characters\n"
                    f"  → Make sure you copied the full key"
                )

            if provider_key.startswith("sk-ant-"):
                self.warnings.append(
                    "PROVIDER_API_KEY looks like an Anthropic key (sk-ant-...)\n"
                    "  → This proxy is for NON-Anthropic providers\n"
                    "  → Use OpenRouter, Gemini, OpenAI, or local models\n"
                    "  → See: README.md for provider setup"
                )

        # Check URL format
        provider_url = os.getenv("PROVIDER_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        if provider_url:
            if not provider_url.startswith(("http://", "https://")):
                self.errors.append(
                    f"PROVIDER_BASE_URL must start with http:// or https://\n"
                    f"  → Current value: {provider_url}"
                )

            if not provider_url.endswith("/v1"):
                self.warnings.append(
                    f"PROVIDER_BASE_URL should typically end with /v1\n"
                    f"  → Current value: {provider_url}\n"
                    f"  → Example: https://api.openai.com/v1"
                )
            
            # Check for localhost loop
            if "localhost" in provider_url or "127.0.0.1" in provider_url:
                # Check if it matches the server port
                server_port = os.getenv("PORT", "8082")
                if f":{server_port}" in provider_url:
                    self.warnings.append(
                        f"PROVIDER_BASE_URL appears to be pointing to THIS proxy ({provider_url})\n"
                        f"  → This will cause an infinite loop!\n"
                        f"  → PROVIDER_BASE_URL should point to the UPSTREAM provider (e.g. OpenAI, OpenRouter)\n"
                        f"  → The 'localhost:{server_port}' address is for your Claude Code client, not this config."
                    )

    def _check_port_availability(self):
        """Check if configured port is available"""
        import socket

        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8082"))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Try to bind to the port
            sock.bind((host, port))
            self.info.append(f"Port {port} is available")
        except OSError:
            self.warnings.append(
                f"Port {port} is already in use\n"
                f"  → Change PORT in .env\n"
                f"  → Or stop the process using: lsof -ti:{port} | xargs kill -9"
            )
        finally:
            sock.close()

    def _display_results(self):
        """Display validation results"""
        # Errors
        if self.errors:
            console.print("\n[bold red]ERRORS:[/bold red]")
            for i, error in enumerate(self.errors, 1):
                console.print(f"\n[red]{i}. {error}[/red]")

        # Warnings
        if self.warnings:
            console.print("\n[bold yellow]WARNINGS:[/bold yellow]")
            for i, warning in enumerate(self.warnings, 1):
                console.print(f"\n[yellow]{i}. {warning}[/yellow]")

        # Info (only if no errors/warnings)
        if not self.errors and not self.warnings and self.info:
            console.print("\n[bold green]CONFIGURATION:[/bold green]")
            for item in self.info:
                console.print(f"  [green]• {item}[/green]")


def validate_config_on_startup(strict: bool = False) -> bool:
    """
    Validate configuration on startup

    Args:
        strict: If True, warnings are treated as errors

    Returns:
        True if validation passed, False otherwise
    """
    # Load .env file
    load_dotenv()

    # Run validation
    validator = ConfigValidator()
    passed = validator.validate_all(strict=strict)

    return passed


def main():
    """CLI entry point for config validation"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Claude Code Proxy configuration")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors (suppress info)",
    )

    args = parser.parse_args()

    # Run validation
    passed = validate_config_on_startup(strict=args.strict)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
