#!/usr/bin/env python3
"""
Claude Code Proxy - First-Time Setup Wizard

Interactive wizard for configuring .env file with feature-based organization.
Supports provider selection, model configuration, and advanced features.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
import questionary
from questionary import Style

# Custom style for the wizard
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', ''),
    ('text', ''),
])


class SetupWizard:
    """Interactive setup wizard for Claude Code Proxy"""

    def __init__(self):
        self.config = {}
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.profiles_dir = self.project_root / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

    def welcome(self):
        """Display welcome message"""
        print("\n" + "="*70)
        print("🔄 Claude Code Proxy - First-Time Setup Wizard")
        print("="*70)
        print("\nThis wizard will help you configure your proxy in minutes.")
        print("You can always change these settings later in .env or the Web UI.\n")

        if self.env_file.exists():
            overwrite = questionary.confirm(
                "⚠️  .env file already exists. Overwrite?",
                default=False,
                style=custom_style
            ).ask()

            if not overwrite:
                print("\n✅ Setup cancelled. Your existing .env is safe.")
                sys.exit(0)

    def select_provider(self):
        """Select API provider"""
        print("\n" + "─"*70)
        print("STEP 1: Choose Your API Provider")
        print("─"*70)

        provider_choices = [
            {
                "name": "🚀 OpenRouter (352+ models, free tier)",
                "value": "openrouter"
            },
            {
                "name": "🌟 Google Gemini (free, excellent for dev)",
                "value": "gemini"
            },
            {
                "name": "🤖 OpenAI (official API)",
                "value": "openai"
            },
            {
                "name": "☁️  Azure OpenAI (enterprise)",
                "value": "azure"
            },
            {
                "name": "🏠 Ollama (local, 100% free)",
                "value": "ollama"
            },
            {
                "name": "💻 LM Studio (local, GUI)",
                "value": "lmstudio"
            },
            {
                "name": "⚙️  Custom provider",
                "value": "custom"
            }
        ]

        provider = questionary.select(
            "Select your provider:",
            choices=provider_choices,
            style=custom_style
        ).ask()

        if provider is None:
            print("\n❌ Setup cancelled.")
            sys.exit(0)

        return self._configure_provider(provider)

    def _configure_provider(self, provider: str) -> Dict[str, str]:
        """Configure specific provider settings"""
        config = {}

        if provider == "openrouter":
            print("\n📝 OpenRouter Configuration")
            print("Get your API key at: https://openrouter.ai/keys\n")

            config["PROVIDER_API_KEY"] = questionary.password(
                "Enter your OpenRouter API key:",
                style=custom_style
            ).ask() or ""

            config["PROVIDER_BASE_URL"] = "https://openrouter.ai/api/v1"

            # Suggest popular models
            model_choices = [
                "anthropic/claude-sonnet-4",
                "openai/gpt-4o",
                "google/gemini-pro-1.5",
                "x-ai/grok-beta",
                "meta-llama/llama-3.1-70b-instruct",
                "Custom model..."
            ]

            big_model = questionary.select(
                "Select BIG model (for Claude Opus requests):",
                choices=model_choices,
                style=custom_style
            ).ask()

            if big_model == "Custom model...":
                big_model = questionary.text(
                    "Enter custom model name:",
                    style=custom_style
                ).ask() or "anthropic/claude-sonnet-4"

            config["BIG_MODEL"] = big_model

            # Reuse for middle/small or customize
            use_same = questionary.confirm(
                "Use the same model for MIDDLE and SMALL?",
                default=True,
                style=custom_style
            ).ask()

            if use_same:
                config["MIDDLE_MODEL"] = big_model
                config["SMALL_MODEL"] = big_model
            else:
                middle_model = questionary.select(
                    "Select MIDDLE model (for Claude Sonnet requests):",
                    choices=model_choices,
                    style=custom_style
                ).ask()

                if middle_model == "Custom model...":
                    middle_model = questionary.text(
                        "Enter custom model name:",
                        style=custom_style
                    ).ask() or "google/gemini-pro-1.5"

                config["MIDDLE_MODEL"] = middle_model

                small_choices = model_choices + ["google/gemini-flash-1.5", "openai/gpt-4o-mini"]
                small_model = questionary.select(
                    "Select SMALL model (for Claude Haiku requests):",
                    choices=small_choices,
                    style=custom_style
                ).ask()

                if small_model == "Custom model...":
                    small_model = questionary.text(
                        "Enter custom model name:",
                        style=custom_style
                    ).ask() or "google/gemini-flash-1.5"

                config["SMALL_MODEL"] = small_model

        elif provider == "gemini":
            print("\n📝 Google Gemini Configuration")
            print("Get your API key at: https://makersuite.google.com/app/apikey\n")

            config["PROVIDER_API_KEY"] = questionary.password(
                "Enter your Gemini API key:",
                style=custom_style
            ).ask() or ""

            config["PROVIDER_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"

            # Gemini models
            model_choices = [
                "gemini-3-pro-preview-11-2025",
                "gemini-3-pro-preview-11-2025-thinking",
                "gemini-2.5-flash-preview-04-17",
                "gemini-2.5-pro-preview-03-25"
            ]

            big_model = questionary.select(
                "Select model:",
                choices=model_choices,
                style=custom_style
            ).ask()

            config["BIG_MODEL"] = big_model
            config["MIDDLE_MODEL"] = big_model
            config["SMALL_MODEL"] = big_model

        elif provider == "openai":
            print("\n📝 OpenAI Configuration")
            print("Get your API key at: https://platform.openai.com/api-keys\n")

            config["PROVIDER_API_KEY"] = questionary.password(
                "Enter your OpenAI API key:",
                style=custom_style
            ).ask() or ""

            config["PROVIDER_BASE_URL"] = "https://api.openai.com/v1"

            model_choices = [
                "gpt-4o",
                "gpt-4o-mini",
                "o1",
                "o1-mini",
                "gpt-4-turbo"
            ]

            big_model = questionary.select(
                "Select BIG model:",
                choices=model_choices,
                style=custom_style
            ).ask()

            config["BIG_MODEL"] = big_model
            config["MIDDLE_MODEL"] = questionary.select(
                "Select MIDDLE model:",
                choices=model_choices,
                style=custom_style
            ).ask()
            config["SMALL_MODEL"] = questionary.select(
                "Select SMALL model:",
                choices=model_choices,
                style=custom_style
            ).ask()

        elif provider == "azure":
            print("\n📝 Azure OpenAI Configuration\n")

            config["PROVIDER_API_KEY"] = questionary.password(
                "Enter your Azure API key:",
                style=custom_style
            ).ask() or ""

            resource_name = questionary.text(
                "Enter Azure resource name:",
                style=custom_style
            ).ask() or "your-resource"

            deployment_name = questionary.text(
                "Enter deployment name:",
                style=custom_style
            ).ask() or "your-deployment"

            config["PROVIDER_BASE_URL"] = f"https://{resource_name}.openai.azure.com/openai/deployments/{deployment_name}"
            config["AZURE_API_VERSION"] = "2024-03-01-preview"
            config["BIG_MODEL"] = "gpt-4"
            config["MIDDLE_MODEL"] = "gpt-4"
            config["SMALL_MODEL"] = "gpt-35-turbo"

        elif provider == "ollama":
            print("\n📝 Ollama Configuration")
            print("Make sure Ollama is running: ollama serve\n")

            config["PROVIDER_API_KEY"] = "dummy"
            config["PROVIDER_BASE_URL"] = "http://localhost:11434/v1"

            model = questionary.text(
                "Enter Ollama model name (e.g., qwen2.5:72b, llama3.1:70b):",
                default="qwen2.5:72b",
                style=custom_style
            ).ask() or "qwen2.5:72b"

            config["BIG_MODEL"] = model
            config["MIDDLE_MODEL"] = model
            config["SMALL_MODEL"] = model

        elif provider == "lmstudio":
            print("\n📝 LM Studio Configuration")
            print("Make sure LM Studio server is running\n")

            config["PROVIDER_API_KEY"] = "dummy"

            port = questionary.text(
                "Enter LM Studio port:",
                default="1234",
                style=custom_style
            ).ask() or "1234"

            config["PROVIDER_BASE_URL"] = f"http://127.0.0.1:{port}/v1"

            model = questionary.text(
                "Enter model name:",
                style=custom_style
            ).ask() or "local-model"

            config["BIG_MODEL"] = model
            config["MIDDLE_MODEL"] = model
            config["SMALL_MODEL"] = model

        else:  # custom
            print("\n📝 Custom Provider Configuration\n")

            config["PROVIDER_API_KEY"] = questionary.password(
                "Enter API key:",
                style=custom_style
            ).ask() or ""

            config["PROVIDER_BASE_URL"] = questionary.text(
                "Enter base URL:",
                default="https://api.example.com/v1",
                style=custom_style
            ).ask() or ""

            config["BIG_MODEL"] = questionary.text(
                "Enter BIG model name:",
                style=custom_style
            ).ask() or ""

            config["MIDDLE_MODEL"] = questionary.text(
                "Enter MIDDLE model name:",
                style=custom_style
            ).ask() or ""

            config["SMALL_MODEL"] = questionary.text(
                "Enter SMALL model name:",
                style=custom_style
            ).ask() or ""

        return config

    def configure_features(self):
        """Configure optional features by category"""
        print("\n" + "─"*70)
        print("STEP 2: Configure Features")
        print("─"*70)

        feature_categories = questionary.checkbox(
            "Which feature categories would you like to configure?",
            choices=[
                questionary.Choice("🧠 Reasoning & Extended Thinking", checked=False),
                questionary.Choice("📊 Dashboard & Monitoring", checked=False),
                questionary.Choice("🎨 Terminal Output Customization", checked=False),
                questionary.Choice("💬 Crosstalk Mode (Multi-Agent)", checked=False),
                questionary.Choice("✏️  Custom System Prompts", checked=False),
                questionary.Choice("📈 Usage Tracking & Analytics", checked=False),
                questionary.Choice("🔀 Hybrid Mode (Multi-Provider)", checked=False),
            ],
            style=custom_style
        ).ask()

        if not feature_categories:
            return {}

        config = {}

        # Reasoning features
        if "🧠 Reasoning & Extended Thinking" in feature_categories:
            config.update(self._configure_reasoning())

        # Dashboard features
        if "📊 Dashboard & Monitoring" in feature_categories:
            config.update(self._configure_dashboard())

        # Terminal output
        if "🎨 Terminal Output Customization" in feature_categories:
            config.update(self._configure_terminal())

        # Crosstalk mode
        if "💬 Crosstalk Mode (Multi-Agent)" in feature_categories:
            config.update(self._configure_crosstalk())

        # Custom prompts
        if "✏️  Custom System Prompts" in feature_categories:
            config.update(self._configure_custom_prompts())

        # Usage tracking
        if "📈 Usage Tracking & Analytics" in feature_categories:
            config.update(self._configure_tracking())

        # Hybrid mode
        if "🔀 Hybrid Mode (Multi-Provider)" in feature_categories:
            config.update(self._configure_hybrid())

        return config

    def _configure_reasoning(self) -> Dict[str, str]:
        """Configure reasoning/extended thinking features"""
        print("\n🧠 Reasoning Configuration")
        print("Enable extended thinking for reasoning models (GPT-5, Claude 4+, Gemini 2+)\n")

        config = {}

        effort = questionary.select(
            "Reasoning effort level (for OpenAI o-series):",
            choices=[
                questionary.Choice("None (disabled)", value=""),
                questionary.Choice("Low (~20% tokens for thinking)", value="low"),
                questionary.Choice("Medium (~50% tokens for thinking)", value="medium"),
                questionary.Choice("High (~80% tokens for thinking)", value="high"),
            ],
            style=custom_style
        ).ask()

        if effort:
            config["REASONING_EFFORT"] = effort

        # Claude/Gemini thinking tokens
        max_tokens = questionary.text(
            "Max thinking tokens for Claude/Gemini (1024-24576, or leave blank):",
            validate=lambda x: x == "" or (x.isdigit() and 1024 <= int(x) <= 24576),
            style=custom_style
        ).ask()

        if max_tokens:
            config["REASONING_MAX_TOKENS"] = max_tokens

        return config

    def _configure_dashboard(self) -> Dict[str, str]:
        """Configure dashboard features"""
        print("\n📊 Dashboard Configuration\n")

        config = {}

        enable = questionary.confirm(
            "Enable live terminal dashboard?",
            default=False,
            style=custom_style
        ).ask()

        if enable:
            config["ENABLE_DASHBOARD"] = "true"

            layout = questionary.select(
                "Dashboard layout:",
                choices=["default", "compact", "detailed"],
                style=custom_style
            ).ask()

            config["DASHBOARD_LAYOUT"] = layout

        return config

    def _configure_terminal(self) -> Dict[str, str]:
        """Configure terminal output"""
        print("\n🎨 Terminal Output Configuration\n")

        config = {}

        mode = questionary.select(
            "Terminal display mode:",
            choices=["minimal", "normal", "detailed", "debug"],
            default="detailed",
            style=custom_style
        ).ask()

        config["TERMINAL_DISPLAY_MODE"] = mode

        color_scheme = questionary.select(
            "Color scheme:",
            choices=["auto", "vibrant", "subtle", "mono"],
            default="auto",
            style=custom_style
        ).ask()

        config["TERMINAL_COLOR_SCHEME"] = color_scheme

        # Quick toggles
        show_cost = questionary.confirm(
            "Show cost estimates?",
            default=True,
            style=custom_style
        ).ask()

        config["TERMINAL_SHOW_COST"] = "true" if show_cost else "false"

        return config

    def _configure_crosstalk(self) -> Dict[str, str]:
        """Configure crosstalk mode"""
        print("\n💬 Crosstalk Mode Configuration")
        print("Multi-agent collaboration for complex tasks\n")

        config = {}

        # For now, just inform user about crosstalk
        info = questionary.confirm(
            "Crosstalk mode uses python -m src.cli.crosstalk_cli. Configure now?",
            default=False,
            style=custom_style
        ).ask()

        if info:
            print("\nℹ️  Run 'python -m src.cli.crosstalk_cli' to launch crosstalk mode.")
            print("You can create crosstalk.yaml config files for different agent setups.")

        return config

    def _configure_custom_prompts(self) -> Dict[str, str]:
        """Configure custom system prompts"""
        print("\n✏️  Custom System Prompts\n")

        config = {}

        for model_tier in ["BIG", "MIDDLE", "SMALL"]:
            enable = questionary.confirm(
                f"Enable custom prompt for {model_tier} model?",
                default=False,
                style=custom_style
            ).ask()

            if enable:
                config[f"ENABLE_CUSTOM_{model_tier}_PROMPT"] = "true"

                prompt_type = questionary.select(
                    f"How to provide {model_tier} prompt?",
                    choices=["From file", "Inline text"],
                    style=custom_style
                ).ask()

                if prompt_type == "From file":
                    file_path = questionary.text(
                        f"Enter path to {model_tier} prompt file:",
                        style=custom_style
                    ).ask()

                    config[f"{model_tier}_SYSTEM_PROMPT_FILE"] = file_path
                else:
                    prompt = questionary.text(
                        f"Enter {model_tier} system prompt:",
                        style=custom_style
                    ).ask()

                    config[f"{model_tier}_SYSTEM_PROMPT"] = prompt

        return config

    def _configure_tracking(self) -> Dict[str, str]:
        """Configure usage tracking"""
        print("\n📈 Usage Tracking Configuration")
        print("Local SQLite database for analytics (no data sent anywhere)\n")

        config = {}

        enable = questionary.confirm(
            "Enable usage tracking?",
            default=False,
            style=custom_style
        ).ask()

        if enable:
            config["TRACK_USAGE"] = "true"

            db_path = questionary.text(
                "Database path:",
                default="usage_tracking.db",
                style=custom_style
            ).ask()

            config["USAGE_DB_PATH"] = db_path

        return config

    def _configure_hybrid(self) -> Dict[str, str]:
        """Configure hybrid mode (multi-provider routing)"""
        print("\n🔀 Hybrid Mode Configuration")
        print("Route different model tiers to different providers!\n")

        config = {}

        print("Example: Use local Ollama for BIG model, OpenRouter for MIDDLE/SMALL\n")

        for tier in ["BIG", "MIDDLE", "SMALL"]:
            enable = questionary.confirm(
                f"Enable custom endpoint for {tier} model?",
                default=False,
                style=custom_style
            ).ask()

            if enable:
                config[f"ENABLE_{tier}_ENDPOINT"] = "true"

                endpoint = questionary.text(
                    f"{tier} endpoint URL:",
                    style=custom_style
                ).ask()

                config[f"{tier}_ENDPOINT"] = endpoint

                api_key = questionary.password(
                    f"{tier} API key (or 'dummy' for local):",
                    style=custom_style
                ).ask()

                config[f"{tier}_API_KEY"] = api_key

        return config

    def save_configuration(self, config: Dict[str, str]):
        """Save configuration to .env file"""
        print("\n" + "─"*70)
        print("STEP 3: Save Configuration")
        print("─"*70)

        # Ask if they want to save as a profile
        save_profile = questionary.confirm(
            "Save this configuration as a named profile?",
            default=False,
            style=custom_style
        ).ask()

        if save_profile:
            profile_name = questionary.text(
                "Profile name:",
                default="default",
                style=custom_style
            ).ask() or "default"

            profile_file = self.profiles_dir / f"{profile_name}.env"

            self._write_env_file(profile_file, config)
            print(f"\n✅ Profile saved to: {profile_file}")

            # Also save to .env
            use_as_active = questionary.confirm(
                "Use this profile as active .env?",
                default=True,
                style=custom_style
            ).ask()

            if use_as_active:
                self._write_env_file(self.env_file, config)
                print(f"✅ Configuration saved to: {self.env_file}")
        else:
            self._write_env_file(self.env_file, config)
            print(f"\n✅ Configuration saved to: {self.env_file}")

    def _write_env_file(self, path: Path, config: Dict[str, str]):
        """Write configuration to .env file"""
        with open(path, 'w') as f:
            f.write("# Claude Code Proxy Configuration\n")
            f.write("# Generated by setup wizard\n\n")

            # Core settings
            f.write("# ═══════════════════════════════════════════════════════════════\n")
            f.write("# CORE CONFIGURATION\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n\n")

            for key in ["PROVIDER_API_KEY", "PROVIDER_BASE_URL", "PROXY_AUTH_KEY"]:
                if key in config:
                    f.write(f'{key}="{config[key]}"\n')

            # Models
            f.write("\n# ═══════════════════════════════════════════════════════════════\n")
            f.write("# MODEL CONFIGURATION\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n\n")

            for key in ["BIG_MODEL", "MIDDLE_MODEL", "SMALL_MODEL"]:
                if key in config:
                    f.write(f'{key}="{config[key]}"\n')

            # Azure specific
            if "AZURE_API_VERSION" in config:
                f.write(f'\nAZURE_API_VERSION="{config["AZURE_API_VERSION"]}"\n')

            # Reasoning
            if any(k in config for k in ["REASONING_EFFORT", "REASONING_MAX_TOKENS"]):
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# REASONING CONFIGURATION\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                if "REASONING_EFFORT" in config:
                    f.write(f'REASONING_EFFORT="{config["REASONING_EFFORT"]}"\n')
                if "REASONING_MAX_TOKENS" in config:
                    f.write(f'REASONING_MAX_TOKENS="{config["REASONING_MAX_TOKENS"]}"\n')

            # Dashboard
            if any(k.startswith("ENABLE_DASHBOARD") or k.startswith("DASHBOARD_") for k in config):
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# DASHBOARD CONFIGURATION\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                for key in ["ENABLE_DASHBOARD", "DASHBOARD_LAYOUT", "DASHBOARD_REFRESH"]:
                    if key in config:
                        f.write(f'{key}="{config[key]}"\n')

            # Terminal
            if any(k.startswith("TERMINAL_") for k in config):
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# TERMINAL OUTPUT CONFIGURATION\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                for key, value in config.items():
                    if key.startswith("TERMINAL_"):
                        f.write(f'{key}="{value}"\n')

            # Custom prompts
            if any(k.startswith("ENABLE_CUSTOM_") or k.endswith("_SYSTEM_PROMPT") or k.endswith("_PROMPT_FILE") for k in config):
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# CUSTOM SYSTEM PROMPTS\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                for key, value in config.items():
                    if key.startswith("ENABLE_CUSTOM_") or key.endswith("_SYSTEM_PROMPT") or key.endswith("_PROMPT_FILE"):
                        f.write(f'{key}="{value}"\n')

            # Usage tracking
            if "TRACK_USAGE" in config:
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# USAGE TRACKING\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                for key in ["TRACK_USAGE", "USAGE_DB_PATH"]:
                    if key in config:
                        f.write(f'{key}="{config[key]}"\n')

            # Hybrid mode
            if any(k.startswith("ENABLE_") and k.endswith("_ENDPOINT") for k in config):
                f.write("\n# ═══════════════════════════════════════════════════════════════\n")
                f.write("# HYBRID MODE (MULTI-PROVIDER ROUTING)\n")
                f.write("# ═══════════════════════════════════════════════════════════════\n\n")

                for tier in ["BIG", "MIDDLE", "SMALL"]:
                    if f"ENABLE_{tier}_ENDPOINT" in config:
                        f.write(f'\nENABLE_{tier}_ENDPOINT="{config[f"ENABLE_{tier}_ENDPOINT"]}"\n')
                        if f"{tier}_ENDPOINT" in config:
                            f.write(f'{tier}_ENDPOINT="{config[f"{tier}_ENDPOINT"]}"\n')
                        if f"{tier}_API_KEY" in config:
                            f.write(f'{tier}_API_KEY="{config[f"{tier}_API_KEY"]}"\n')

            # Server settings
            f.write("\n# ═══════════════════════════════════════════════════════════════\n")
            f.write("# SERVER SETTINGS\n")
            f.write("# ═══════════════════════════════════════════════════════════════\n\n")
            f.write('HOST="0.0.0.0"\n')
            f.write('PORT="8082"\n')
            f.write('LOG_LEVEL="INFO"\n')

    def finish(self):
        """Display completion message"""
        print("\n" + "="*70)
        print("🎉 Setup Complete!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Start the proxy: python start_proxy.py")
        print("  2. In another terminal: export ANTHROPIC_BASE_URL=http://localhost:8082")
        print("  3. Run Claude Code: claude \"your prompt\"")
        print("\nWeb UI: http://localhost:8082")
        print("Documentation: README.md and docs/CONFIGURATION.md")
        print("\nHappy coding! 🚀\n")

    def run(self):
        """Run the setup wizard"""
        try:
            # Welcome
            self.welcome()

            # Step 1: Provider selection
            provider_config = self.select_provider()
            self.config.update(provider_config)

            # Step 2: Optional features
            feature_config = self.configure_features()
            self.config.update(feature_config)

            # Step 3: Save configuration
            self.save_configuration(self.config)

            # Finish
            self.finish()

        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    # Check for questionary
    try:
        import questionary
    except ImportError:
        print("❌ Error: questionary package not found.")
        print("\nInstall it with: pip install questionary")
        print("Or if using uv: uv pip install questionary")
        sys.exit(1)

    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
