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
import httpx
import asyncio
try:
    from rich.spinner import Spinner
    from rich.console import Console
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


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
        # src/cli/wizard.py -> src/cli -> src -> root
        self.project_root = Path(__file__).parent.parent.parent
        self.env_file = self.project_root / ".env"
        self.profiles_dir = self.project_root / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        self.console = Console() if RICH_AVAILABLE else None

    def _detect_vibeproxy(self) -> bool:
        """Check if VibeProxy is running on localhost:8317"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 8317))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _detect_ollama(self) -> bool:
        """Check if Ollama is running on localhost:11434"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 11434))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _fetch_vibeproxy_models(self) -> List[str]:
        """Fetch available models from VibeProxy"""
        try:
            import requests
            response = requests.get('http://127.0.0.1:8317/v1/models', timeout=3)
            if response.status_code == 200:
                data = response.json()
                return [m['id'] for m in data.get('data', [])]
        except Exception:
            pass
        # Fallback to known models
        return [
            "gemini-claude-opus-4-5-thinking",
            "gemini-claude-sonnet-4-5-thinking",
            "gemini-claude-sonnet-4-5",
            "gemini-3-pro-preview",
            "gemini-3-flash",
            "gemini-2.5-flash",
            "gpt-oss-120b-medium",
        ]

    def check_existing_config(self) -> bool:
        """
        Check if existing configuration is valid.
        Returns True if user wants to keep existing config, False to proceed with setup.
        """
        # Load current env vars (including those from .env if loaded by main)
        from src.core.config import config
        
        # Check for provider key
        api_key = os.environ.get("PROVIDER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("PROVIDER_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        
        if not api_key or "dummy" in api_key or "your-" in api_key:
            return False
            
        print("\n🔍 Detected existing configuration...")
        print(f"   Provider URL: {base_url}")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
        
        # Validate connection
        is_valid = self.validate_provider_connection(base_url, api_key)
        
        if is_valid:
            print("\n✅ Current configuration is VALID and working!")
            
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "Keep current configuration (Exit)",
                    "Reconfigure everything",
                    "Add/Override specific models (Hybrid Mode)"
                ],
                style=custom_style
            ).ask()
            
            if choice == "Keep current configuration (Exit)":
                return True
            elif choice == "Add/Override specific models (Hybrid Mode)":
                # Load existing config into self.config so we don't lose it
                self.config["PROVIDER_API_KEY"] = api_key
                self.config["PROVIDER_BASE_URL"] = base_url
                # Copy other known keys
                for k, v in os.environ.items():
                    if k in ["BIG_MODEL", "MIDDLE_MODEL", "SMALL_MODEL", "PROXY_AUTH_KEY"]:
                        self.config[k] = v
                
                # Jump straight to hybrid config
                hybrid_config = self._configure_hybrid()
                self.config.update(hybrid_config)
                self.save_configuration(self.config)
                self.finish()
                sys.exit(0)
                
        else:
            print("\n⚠️  Current configuration failed validation.")
            print("   You should probably reconfigure.")
            
            if not questionary.confirm("Proceed with fresh setup?", default=True, style=custom_style).ask():
                sys.exit(0)
                
        return False

    def validate_provider_connection(self, base_url: str, api_key: str) -> bool:
        """Validate connection to provider."""
        if not base_url:
            return False
            
        print("\n   Testing connection...", end="", flush=True)
        
        try:
            # Use a simple synchronous check for the wizard
            import requests
            
            # Construct a lightweight request
            # Try /models endpoint first as it's standard
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Handle different provider quirks
            url = base_url.rstrip('/')
            if "googleapis" in url:
                # Gemini needs key in query param usually, but let's try standard first
                pass
            
            if not url.endswith("/v1"):
                url += "/v1"
                
            try:
                response = requests.get(f"{url}/models", headers=headers, timeout=5)
                if response.status_code == 200:
                    print(" OK! (Models list accessible)")
                    return True
            except:
                pass
                
            # Fallback: Try a tiny completion
            try:
                payload = {
                    "model": "gpt-3.5-turbo", # Default guess
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1
                }
                # Adjust model for known providers
                if "anthropic" in url:
                    payload["model"] = "claude-3-haiku-20240307"
                elif "google" in url:
                    payload["model"] = "gemini-1.5-flash"
                
                response = requests.post(
                    f"{url}/chat/completions", 
                    json=payload, 
                    headers=headers, 
                    timeout=5
                )
                
                if response.status_code in [200, 400, 401, 403]:
                    # 400/401/403 means we reached the server, even if auth/model failed
                    # strictly speaking 401/403 means auth failed, but 200 is success
                    if response.status_code == 200:
                        print(" OK! (Completion successful)")
                        return True
                    elif response.status_code == 401:
                        print(" Failed (Unauthorized)")
                        return False
                    else:
                        # 400 might be invalid model, but connection works. 
                        # Let's be strict for "Smart" wizard.
                        print(f" Failed (API returned {response.status_code})")
                        return False
            except Exception as e:
                print(f" Error: {e}")
                return False
                
            return False
            
        except ImportError:
            print(" (Skipping validation - requests not installed)")
            return True # Assume valid if we can't test
        except Exception as e:
            print(f" Error: {e}")
            return False


    def print_banner(self):
        """Display welcome banner"""
        print("\n" + "="*70)
        print("🔄 Claude Code Proxy - First-Time Setup Wizard")
        print("="*70)
        print("\nThis wizard will help you configure your proxy in minutes.")
        print("You can always change these settings later in .env or the Web UI.\n")

    def check_overwrite(self):
        """Check if .env exists and ask to overwrite"""
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

        # Check for running local providers
        vibeproxy_detected = self._detect_vibeproxy()
        ollama_detected = self._detect_ollama()

        provider_choices = []

        # Add VibeProxy first if detected
        if vibeproxy_detected:
            provider_choices.append({
                "name": "🌌 VibeProxy/Antigravity (DETECTED - Claude & Gemini via OAuth)",
                "value": "vibeproxy"
            })
        else:
            provider_choices.append({
                "name": "🌌 VibeProxy/Antigravity (Claude & Gemini via Google OAuth)",
                "value": "vibeproxy"
            })

        provider_choices.extend([
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
        ])

        # Add Ollama with detection status
        if ollama_detected:
            provider_choices.append({
                "name": "🏠 Ollama (DETECTED - local, 100% free)",
                "value": "ollama"
            })
        else:
            provider_choices.append({
                "name": "🏠 Ollama (local, 100% free)",
                "value": "ollama"
            })

        provider_choices.extend([
            {
                "name": "💻 LM Studio (local, GUI)",
                "value": "lmstudio"
            },
            {
                "name": "⚙️  Custom provider",
                "value": "custom"
            }
        ])

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

        if provider == "vibeproxy":
            print("\n📝 VibeProxy/Antigravity Configuration")
            print("VibeProxy handles OAuth authentication - no API key needed!")
            print("Download: https://github.com/AntonioCiolworking/VibeProxy/releases\n")

            config["PROVIDER_API_KEY"] = "dummy"
            config["PROVIDER_BASE_URL"] = "http://127.0.0.1:8317/v1"

            # Fetch available models
            print("Fetching available models from VibeProxy...", end="", flush=True)
            available_models = self._fetch_vibeproxy_models()
            print(f" Found {len(available_models)} models!\n")

            # Categorize models for better UX
            thinking_models = [m for m in available_models if "thinking" in m.lower()]
            claude_models = [m for m in available_models if "claude" in m.lower() and m not in thinking_models]
            gemini_models = [m for m in available_models if "gemini" in m.lower()]
            other_models = [m for m in available_models if m not in thinking_models + claude_models + gemini_models]

            # BIG model - recommend thinking model
            big_choices = []
            if thinking_models:
                big_choices.extend([f"🧠 {m}" for m in thinking_models])
            if claude_models:
                big_choices.extend([f"🤖 {m}" for m in claude_models])
            big_choices.extend(gemini_models + other_models)
            big_choices.append("Custom model...")

            # Clean up display names for selection
            big_choices_clean = [c.replace("🧠 ", "").replace("🤖 ", "") if c != "Custom model..." else c for c in big_choices]

            print("Model Routing: Claude Code maps opus→BIG, sonnet→MIDDLE, haiku→SMALL\n")

            big_model = questionary.select(
                "Select BIG model (Claude Opus requests) - thinking models recommended:",
                choices=big_choices,
                style=custom_style
            ).ask()

            if big_model == "Custom model...":
                big_model = questionary.text(
                    "Enter custom model name:",
                    style=custom_style
                ).ask() or "gemini-claude-opus-4-5-thinking"
            else:
                # Strip emoji prefix
                big_model = big_model.replace("🧠 ", "").replace("🤖 ", "")

            config["BIG_MODEL"] = big_model

            # MIDDLE model
            middle_choices = gemini_models + claude_models + other_models
            middle_choices.append("Custom model...")

            middle_model = questionary.select(
                "Select MIDDLE model (Claude Sonnet requests):",
                choices=middle_choices,
                style=custom_style
            ).ask()

            if middle_model == "Custom model...":
                middle_model = questionary.text(
                    "Enter custom model name:",
                    style=custom_style
                ).ask() or "gemini-3-pro-preview"

            config["MIDDLE_MODEL"] = middle_model

            # SMALL model - fast models
            small_choices = [m for m in gemini_models if "flash" in m.lower()]
            small_choices.extend([m for m in gemini_models if m not in small_choices])
            small_choices.extend(other_models)
            small_choices.append("Custom model...")

            small_model = questionary.select(
                "Select SMALL model (Claude Haiku requests) - fast models recommended:",
                choices=small_choices,
                style=custom_style
            ).ask()

            if small_model == "Custom model...":
                small_model = questionary.text(
                    "Enter custom model name:",
                    style=custom_style
                ).ask() or "gemini-3-flash"

            config["SMALL_MODEL"] = small_model

            # Set recommended defaults for VibeProxy
            config["REASONING_MAX_TOKENS"] = "128000"
            config["MAX_TOKENS_LIMIT"] = "65536"
            config["REQUEST_TIMEOUT"] = "120"

        elif provider == "openrouter":
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
            "Max thinking tokens for Claude/Gemini (1024-128000, or leave blank for default):",
            validate=lambda x: x == "" or (x.isdigit() and 1024 <= int(x) <= 128000),
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
            self.print_banner()
            
            # Check existing config
            if self.check_existing_config():
                return
                
            # Check overwrite (only if we didn't return above)
            self.check_overwrite()

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
