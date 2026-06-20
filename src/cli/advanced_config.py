#!/usr/bin/env python3
"""
Advanced Settings Configurator
Configures Reasoning, Network, and Feature Flags with .env persistence.
"""

import os
import sys
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

# Import shared env utility
from src.cli.env_utils import update_env_values

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# ENV FILE MANAGEMENT (using shared utility)
# ═══════════════════════════════════════════════════════════════════════════════


def update_env_file(updates: Dict[str, Optional[str]]):
    """Wrapper for shared utility for backward compatibility."""
    return update_env_values(updates, verbose=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MENUS
# ═══════════════════════════════════════════════════════════════════════════════


def configure_reasoning():
    """Configure Reasoning/Thinking settings."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold magenta]🧠 Reasoning Configuration[/]\n"
                "[dim]Control Claude's thinking process[/]",
                border_style="magenta",
            )
        )

        # Current Values
        effort = os.getenv("REASONING_EFFORT", "disabled")
        tokens = os.getenv("REASONING_MAX_TOKENS", "not set")
        exclude = os.getenv("REASONING_EXCLUDE", "false")
        big_reasoning = os.getenv("BIG_MODEL_REASONING", "")
        middle_reasoning = os.getenv("MIDDLE_MODEL_REASONING", "")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  Effort:      [cyan]{effort}[/]")
        console.print(f"  Max Tokens:  [cyan]{tokens}[/]")
        console.print(
            f"  Exclude:     [cyan]{exclude}[/] (Don't reason on non-coding tasks)"
        )
        console.print(f"  BIG Override:    [cyan]{big_reasoning or '(none)'}[/]")
        console.print(f"  MIDDLE Override: [cyan]{middle_reasoning or '(none)'}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  [1] Set Effort (low/medium/high)")
        console.print("  [2] Set Max Budget Tokens")
        console.print("  [3] Toggle Exclusion")
        console.print("  [4] Set BIG tier reasoning override")
        console.print("  [5] Set MIDDLE tier reasoning override")
        console.print("  [6] [red]Disable Reasoning[/] (Unset variables)")
        console.print("  [0] Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "5", "6", "0"], default="0"
        )

        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            new_effort = Prompt.ask(
                "Select effort", choices=["low", "medium", "high"], default="medium"
            )
            updates["REASONING_EFFORT"] = new_effort
        elif choice == "2":
            new_tokens = Prompt.ask("Enter max tokens (int)", default="12000")
            updates["REASONING_MAX_TOKENS"] = new_tokens
        elif choice == "3":
            new_val = "true" if exclude.lower() != "true" else "false"
            updates["REASONING_EXCLUDE"] = new_val
        elif choice == "4":
            updates["BIG_MODEL_REASONING"] = Prompt.ask(
                "BIG tier reasoning override", default=big_reasoning
            )
        elif choice == "5":
            updates["MIDDLE_MODEL_REASONING"] = Prompt.ask(
                "MIDDLE tier reasoning override", default=middle_reasoning
            )
        elif choice == "6":
            if Confirm.ask("Disable reasoning features?"):
                updates["REASONING_EFFORT"] = None
                updates["REASONING_MAX_TOKENS"] = None
                # We might keep EXCLUDE or remove it, usually good to remove
                updates["REASONING_EXCLUDE"] = None
                updates["BIG_MODEL_REASONING"] = None
                updates["MIDDLE_MODEL_REASONING"] = None

        if updates:
            update_env_file(updates)
            # Update current os.environ for immediate feedback in loop
            for k, v in updates.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_network():
    """Configure Network & Server settings."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold green]🌐 Network & Server Config[/]\n"
                "[dim]Host, Port, and Logging details[/]",
                border_style="green",
            )
        )

        host = os.getenv("HOST", "0.0.0.0")
        port = os.getenv("PORT", "8082")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        timeout = os.getenv("TIMEOUT", "not set")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  Host:      [cyan]{host}[/]")
        console.print(f"  Port:      [cyan]{port}[/]")
        console.print(f"  Log Level: [cyan]{log_level}[/]")
        console.print(f"  Timeout:   [cyan]{timeout}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  [1] Set Host")
        console.print("  [2] Set Port")
        console.print("  [3] Set Log Level")
        console.print("  [4] Set Timeout")
        console.print("  [0] Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            updates["HOST"] = Prompt.ask("Enter Host", default="0.0.0.0")
        elif choice == "2":
            updates["PORT"] = Prompt.ask("Enter Port", default="8082")
        elif choice == "3":
            updates["LOG_LEVEL"] = Prompt.ask(
                "Select Level",
                choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                default="INFO",
            )
        elif choice == "4":
            val = Prompt.ask("Enter Timeout (seconds)", default="120")
            updates["TIMEOUT"] = val

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_features():
    """Configure Feature Flags."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold blue]🚩 Feature Flags[/]\n"
                "[dim]Toggle experimental or optional features[/]",
                border_style="blue",
            )
        )

        compact = os.getenv("COMPACT_LOGGER", "false")
        usage = os.getenv("TRACK_USAGE", "false")
        refresh = os.getenv("DASHBOARD_REFRESH", "0.5")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Compact Logger:  [cyan]{compact}[/]")
        console.print(f"  2. Track Usage:     [cyan]{usage}[/]")
        console.print(f"  3. Dash Refresh:    [cyan]{refresh}[/]s")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to toggle/edit, or [0] to Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            new_val = "true" if compact.lower() != "true" else "false"
            updates["COMPACT_LOGGER"] = new_val
        elif choice == "2":
            new_val = "true" if usage.lower() != "true" else "false"
            updates["TRACK_USAGE"] = new_val
        elif choice == "3":
            updates["DASHBOARD_REFRESH"] = Prompt.ask(
                "Enter Refresh Rate (float)", default="0.5"
            )

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            # No input wait for toggles to make it snappy, unless it was a text input
            if choice == "3":
                input("\nPress Enter to continue...")


def configure_api_keys():
    """Configure API Keys and Provider settings."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold yellow]🔑 API Keys & Provider[/]\n"
                "[dim]Configure endpoints and authentication[/]",
                border_style="yellow",
            )
        )

        provider_url = os.getenv("BIG_ENDPOINT", "not set")
        proxy_key = os.getenv("PROXY_AUTH_KEY", "not set")
        openrouter = (
            os.getenv("OPENROUTER_API_KEY", "not set")[:8] + "..."
            if os.getenv("OPENROUTER_API_KEY")
            else "not set"
        )
        exa = (
            os.getenv("EXA_API_KEY", "not set")[:8] + "..."
            if os.getenv("EXA_API_KEY")
            else "not set"
        )
        aa = (
            os.getenv("AA_API_KEY", "not set")[:8] + "..."
            if os.getenv("AA_API_KEY")
            else "not set"
        )

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Provider URL:        [cyan]{provider_url}[/]")
        console.print(f"  2. Proxy Auth Key:      [cyan]{proxy_key}[/]")
        console.print(f"  3. OpenRouter Key:      [cyan]{openrouter}[/]")
        console.print(f"  4. Exa API Key:         [cyan]{exa}[/]")
        console.print(f"  5. Artificial Analysis: [cyan]{aa}[/] [dim](benchmark scores)[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "5", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            updates["BIG_ENDPOINT"] = Prompt.ask(
                "Enter Provider URL", default="http://127.0.0.1:8317/v1"
            )
        elif choice == "2":
            updates["PROXY_AUTH_KEY"] = Prompt.ask(
                "Enter Proxy Auth Key", default="pass"
            )
        elif choice == "3":
            updates["OPENROUTER_API_KEY"] = Prompt.ask("Enter OpenRouter API Key")
        elif choice == "4":
            updates["EXA_API_KEY"] = Prompt.ask("Enter Exa API Key (for model ranking)")
        elif choice == "5":
            updates["AA_API_KEY"] = Prompt.ask("Enter Artificial Analysis API Key")

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_analytics():
    """Configure Analytics & Usage Tracking settings."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold magenta]📈 Analytics Configuration[/]\n"
                "[dim]Usage tracking and data collection settings[/]",
                border_style="magenta",
            )
        )

        # Current values
        track_usage = os.getenv("TRACK_USAGE", "false")
        log_content = os.getenv("LOG_FULL_CONTENT", "false")
        db_path = os.getenv(
            "USAGE_TRACKING_DB_PATH",
            os.getenv("USAGE_DB_PATH", "usage_tracking.db"),
        )
        silence_deps = os.getenv("SILENCE_DEPRECATION_WARNINGS", "false")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Track Usage:      [cyan]{track_usage}[/]")
        console.print(
            f"  2. Log Full Content: [cyan]{log_content}[/] (WARNING: stores request/response data)"
        )
        console.print(f"  3. Database Path:    [cyan]{db_path}[/]")
        console.print(f"  4. Silence Deprecation Warnings: [cyan]{silence_deps}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  1-4 - Edit setting")
        console.print("  [5] Launch Analytics Viewer")
        console.print("  [6] Export Data")
        console.print("  [7] Reset/Clear Analytics Data")
        console.print("  [0] Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "5", "6", "7", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            new_val = "true" if track_usage.lower() != "true" else "false"
            updates["TRACK_USAGE"] = new_val
        elif choice == "2":
            new_val = "true" if log_content.lower() != "true" else "false"
            updates["LOG_FULL_CONTENT"] = new_val
        elif choice == "3":
            updates["USAGE_TRACKING_DB_PATH"] = Prompt.ask(
                "Enter database path", default=db_path
            )
        elif choice == "4":
            new_val = "true" if silence_deps.lower() != "true" else "false"
            updates["SILENCE_DEPRECATION_WARNINGS"] = new_val
        elif choice == "5":
            # Launch analytics viewer
            console.clear()
            console.print("[bold cyan]Launching Analytics Viewer...[/bold cyan]\n")
            try:
                from src.cli.analytics import main as analytics_main

                analytics_main()
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                input("\nPress Enter to continue...")
            continue
        elif choice == "6":
            # Export
            from src.cli.analytics import export_to_csv

            export_to_csv()
            continue
        elif choice == "7":
            if Confirm.ask(
                "[red]Delete all analytics data? This cannot be undone![/red]"
            ):
                try:
                    import sqlite3

                    db_path_resolved = os.getenv(
                        "USAGE_TRACKING_DB_PATH",
                        os.getenv("USAGE_DB_PATH", "usage_tracking.db"),
                    )
                    if os.path.exists(db_path_resolved):
                        os.remove(db_path_resolved)
                        console.print("\n[green]✓ Analytics database deleted.[/green]")
                        console.print(
                            "[yellow]Note: Tracking must be re-enabled to create new data.[/yellow]"
                        )
                    else:
                        console.print("\n[dim]No database file found to delete.[/dim]")
                except Exception as e:
                    console.print(f"\n[red]Error deleting database: {e}[/red]")
                input("\nPress Enter to continue...")
            continue

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_hybrid_mode():
    """Configure Hybrid Mode (per-model routing)."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold red]🔀 Hybrid Mode[/]\n"
                "[dim]Route different model tiers to different providers[/]",
                border_style="red",
            )
        )

        # Current values
        big_enabled = os.getenv("ENABLE_BIG_ENDPOINT", "false")
        big_endpoint = os.getenv("BIG_ENDPOINT", "not set")
        middle_enabled = os.getenv("ENABLE_MIDDLE_ENDPOINT", "false")
        middle_endpoint = os.getenv("MIDDLE_ENDPOINT", "not set")
        small_enabled = os.getenv("ENABLE_SMALL_ENDPOINT", "false")
        small_endpoint = os.getenv("SMALL_ENDPOINT", "not set")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(
            f"  [bold]BIG[/]    Enabled: [cyan]{big_enabled}[/]  Endpoint: [cyan]{big_endpoint}[/]"
        )
        console.print(
            f"  [bold]MIDDLE[/] Enabled: [cyan]{middle_enabled}[/]  Endpoint: [cyan]{middle_endpoint}[/]"
        )
        console.print(
            f"  [bold]SMALL[/]  Enabled: [cyan]{small_enabled}[/]  Endpoint: [cyan]{small_endpoint}[/]"
        )

        console.print("\n[bold cyan]Options:[/]")
        console.print("  [1] Configure BIG endpoint")
        console.print("  [2] Configure MIDDLE endpoint")
        console.print("  [3] Configure SMALL endpoint")
        console.print("  [4] Disable all hybrid routing")
        console.print("  [0] Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice in ["1", "2", "3"]:
            tier = {"1": "BIG", "2": "MIDDLE", "3": "SMALL"}[choice]
            enabled = Confirm.ask(f"Enable {tier} endpoint override?")
            updates[f"ENABLE_{tier}_ENDPOINT"] = "true" if enabled else "false"
            if enabled:
                updates[f"{tier}_ENDPOINT"] = Prompt.ask(
                    f"Enter {tier} endpoint URL", default="https://openrouter.ai/api/v1"
                )
                updates[f"{tier}_API_KEY"] = Prompt.ask(f"Enter {tier} API key")
        elif choice == "4":
            if Confirm.ask("Disable all hybrid routing?"):
                updates = {
                    "ENABLE_BIG_ENDPOINT": "false",
                    "ENABLE_MIDDLE_ENDPOINT": "false",
                    "ENABLE_SMALL_ENDPOINT": "false",
                }

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_token_limits():
    """Configure Token Limits and Timeouts."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold cyan]📊 Token Limits & Timeouts[/]\n"
                "[dim]Control request sizes and timing[/]",
                border_style="cyan",
            )
        )

        max_tokens = os.getenv("MAX_TOKENS_LIMIT", "65536")
        min_tokens = os.getenv("MIN_TOKENS_LIMIT", "4096")
        timeout = os.getenv("REQUEST_TIMEOUT", "120")
        retries = os.getenv("MAX_RETRIES", "2")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Max Tokens:      [cyan]{max_tokens}[/]")
        console.print(f"  2. Min Tokens:      [cyan]{min_tokens}[/]")
        console.print(f"  3. Request Timeout: [cyan]{timeout}[/]s")
        console.print(f"  4. Max Retries:     [cyan]{retries}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            updates["MAX_TOKENS_LIMIT"] = Prompt.ask(
                "Enter Max Tokens", default="65536"
            )
        elif choice == "2":
            updates["MIN_TOKENS_LIMIT"] = Prompt.ask("Enter Min Tokens", default="4096")
        elif choice == "3":
            updates["REQUEST_TIMEOUT"] = Prompt.ask(
                "Enter Timeout (seconds)", default="120"
            )
        elif choice == "4":
            updates["MAX_RETRIES"] = Prompt.ask("Enter Max Retries", default="2")

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_custom_prompts():
    """Configure Custom System Prompts."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold magenta]📝 Custom System Prompts[/]\n"
                "[dim]Override system prompts per model tier[/]",
                border_style="magenta",
            )
        )

        big_enabled = os.getenv("ENABLE_CUSTOM_BIG_PROMPT", "false")
        middle_enabled = os.getenv("ENABLE_CUSTOM_MIDDLE_PROMPT", "false")
        small_enabled = os.getenv("ENABLE_CUSTOM_SMALL_PROMPT", "false")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. BIG Custom Prompt:    [cyan]{big_enabled}[/]")
        console.print(f"  2. MIDDLE Custom Prompt: [cyan]{middle_enabled}[/]")
        console.print(f"  3. SMALL Custom Prompt:  [cyan]{small_enabled}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to configure, or [0] to Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice in ["1", "2", "3"]:
            tier = {"1": "BIG", "2": "MIDDLE", "3": "SMALL"}[choice]
            enabled = Confirm.ask(f"Enable custom prompt for {tier}?")
            updates[f"ENABLE_CUSTOM_{tier}_PROMPT"] = "true" if enabled else "false"
            if enabled:
                use_file = Confirm.ask("Load prompt from file?")
                if use_file:
                    updates[f"{tier}_SYSTEM_PROMPT_FILE"] = Prompt.ask(
                        "Enter prompt file path"
                    )
                else:
                    updates[f"{tier}_SYSTEM_PROMPT"] = Prompt.ask(
                        "Enter system prompt (short)"
                    )

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_crosstalk():
    """Configure Crosstalk (Model-to-Model conversations)."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold white]💬 Crosstalk Configuration[/]\n"
                "[dim]Enable model-to-model conversations[/]",
                border_style="white",
            )
        )

        enabled = os.getenv("CROSSTALK_ENABLED", "false")
        paradigm = os.getenv("CROSSTALK_PARADIGM", "relay")
        iterations = os.getenv("CROSSTALK_ITERATIONS", "20")
        models = os.getenv("CROSSTALK_MODELS", "not set")

        console.print("\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Enabled:    [cyan]{enabled}[/]")
        console.print(
            f"  2. Paradigm:   [cyan]{paradigm}[/] [dim](memory, report, relay, debate)[/]"
        )
        console.print(f"  3. Iterations: [cyan]{iterations}[/]")
        console.print(f"  4. Models:     [cyan]{models}[/]")

        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")

        choice = Prompt.ask(
            "\nSelect option", choices=["1", "2", "3", "4", "0"], default="0"
        )
        updates = {}

        if choice == "0":
            return
        elif choice == "1":
            new_val = "true" if enabled.lower() != "true" else "false"
            updates["CROSSTALK_ENABLED"] = new_val
        elif choice == "2":
            updates["CROSSTALK_PARADIGM"] = Prompt.ask(
                "Select paradigm",
                choices=["memory", "report", "relay", "debate"],
                default="relay",
            )
        elif choice == "3":
            updates["CROSSTALK_ITERATIONS"] = Prompt.ask(
                "Enter iterations", default="20"
            )
        elif choice == "4":
            updates["CROSSTALK_MODELS"] = Prompt.ask(
                "Enter models (comma-separated)", default="gpt-4o,gemini-3-pro-preview"
            )

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def main():
    """Main Advanced Config Menu."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold white]Advanced Configuration[/]\n\n"
                "[dim]Deep dive into proxy behavior. Changes update .env directly.[/]",
                title="⚙️  Parameter Tuner",
                border_style="yellow",
            )
        )

        console.print("\n[bold cyan]Categories:[/]")
        console.print("  [1] 🤖 Models & Cascade      [dim](BIG/MIDDLE/SMALL, fallbacks)[/]")
        console.print("  [2] 🧠 Reasoning / Thinking  [dim](Extended CoT, effort level)[/]")
        console.print("  [3] 💰 Budget & Cost Controls[dim](Token/USD limits, mid-stream)[/]")
        console.print("  [4] 🗺️  Router Slots          [dim](Use-case model assignments)[/]")
        console.print("  [5] 🗜️  Compression & Cache   [dim](Headroom bypass, semantic cache)[/]")
        console.print("  [6] 🖥️  Local GPU Inference   [dim](ollama/llamafile, 4th tier)[/]")
        console.print("  [7] 🔄 Cascade & Circuit Bkr [dim](Fallback lists, CB thresholds)[/]")
        console.print("  [8] 🔧 Tool Calls            [dim](Tool-capable models, truncation)[/]")
        console.print("  [9] 🔑 API Keys & Provider   [dim](Endpoints, Auth, API keys)[/]")
        console.print("  [J] 🧬 OpenRouter Fusion     [dim](Fusion profiles and aliases)[/]")
        console.print("  [A] 🌐 Network & Server      [dim](Host, Port, Timeouts)[/]")
        console.print("  [B] 📋 Logging               [dim](Log file, rotation, debug)[/]")
        console.print("  [C] 📈 Analytics & Tracking  [dim](Usage tracking config)[/]")
        console.print("  [D] 🐕 Watchdog              [dim](Auto-recovery, health checks)[/]")
        console.print("  [E] 📝 Custom Prompts        [dim](System prompt overrides)[/]")
        console.print("  [F] 🔀 Hybrid Mode           [dim](Per-tier endpoint routing)[/]")
        console.print("  [G] 📊 Token Limits          [dim](Max tokens, context limits)[/]")
        console.print("  [H] 🚩 Feature Flags         [dim](Toggles & Options)[/]")
        console.print("  [I] 💬 Crosstalk             [dim](Model-to-model chat)[/]")
        console.print("  [0] 🔙 Back to Main Menu")

        choice = Prompt.ask(
            "\nSelect category",
            choices=["1","2","3","4","5","6","7","8","9","A","B","C","D","E","F","G","H","I","J","0"],
            default="0",
        ).upper()

        if choice == "0":
            return
        elif choice == "1":
            configure_models()
        elif choice == "2":
            configure_reasoning()
        elif choice == "3":
            configure_budgets()
        elif choice == "4":
            configure_router_slots()
        elif choice == "5":
            configure_compression()
        elif choice == "6":
            configure_local_gpu()
        elif choice == "7":
            configure_cascade_cb()
        elif choice == "8":
            configure_toolcalls()
        elif choice == "9":
            configure_api_keys()
        elif choice == "J":
            configure_fusion()
        elif choice == "A":
            configure_network()
        elif choice == "B":
            configure_logging_advanced()
        elif choice == "C":
            configure_analytics()
        elif choice == "D":
            configure_watchdog()
        elif choice == "E":
            configure_custom_prompts()
        elif choice == "F":
            configure_hybrid_mode()
        elif choice == "G":
            configure_token_limits()
        elif choice == "H":
            configure_features()
        elif choice == "I":
            configure_crosstalk()


def _prompt_val(label: str, env_key: str, default: str = "", secret: bool = False) -> Optional[str]:
    """Helper: prompt for a value, show current, return new value or None if unchanged."""
    current = os.environ.get(env_key, default)
    display = "***" if secret and current else (current or "[dim](not set)[/]")
    console.print(f"  [dim]{env_key}[/] current: [cyan]{display}[/]")
    new_val = Prompt.ask(f"  → {label}", default=current)
    return new_val if new_val != current else None


def configure_budgets():
    """Configure Budget & Cost Controls."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Budget & Cost Controls[/]\n[dim]Prevent API bankruptcy with token and USD limits.[/]",
            border_style="red", title="💰 Budgets"
        ))

        daily_tok = os.environ.get("DAILY_TOKEN_BUDGET", "0")
        per_req = os.environ.get("PER_REQUEST_TOKEN_BUDGET", "0")
        daily_cost = os.environ.get("DAILY_COST_BUDGET", "0.0")
        mid_stream = os.environ.get("MID_STREAM_OUTPUT_BUDGET", "0")

        console.print(f"\n  [1] Daily token budget     [cyan]{daily_tok}[/] tokens  [dim](0=disabled)[/]")
        console.print(f"  [2] Per-request token cap  [cyan]{per_req}[/] tokens  [dim](0=disabled)[/]")
        console.print(f"  [3] Daily cost budget      [cyan]${daily_cost}[/] USD  [dim](0=disabled)[/]")
        console.print(f"  [4] Mid-stream output cap  [cyan]{mid_stream}[/] tokens  [dim](0=disabled; stops expensive model, routes next turn cheaper)[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            v = Prompt.ask("Daily token budget (0=disabled)", default=daily_tok)
            updates["DAILY_TOKEN_BUDGET"] = v
        elif choice == "2":
            v = Prompt.ask("Per-request token cap (0=disabled)", default=per_req)
            updates["PER_REQUEST_TOKEN_BUDGET"] = v
        elif choice == "3":
            v = Prompt.ask("Daily cost budget in USD (0=disabled)", default=daily_cost)
            updates["DAILY_COST_BUDGET"] = v
        elif choice == "4":
            v = Prompt.ask("Mid-stream output budget tokens (0=disabled)", default=mid_stream)
            updates["MID_STREAM_OUTPUT_BUDGET"] = v
        if updates:
            update_env_file(updates)


def configure_cascade_cb():
    """Configure Cascade Fallbacks and Circuit Breaker."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Cascade Fallbacks & Circuit Breaker[/]\n[dim]Control how the proxy handles model failures.[/]",
            border_style="yellow", title="🔄 Cascade & CB"
        ))

        big_c = os.environ.get("BIG_CASCADE", "")
        mid_c = os.environ.get("MIDDLE_CASCADE", "")
        sml_c = os.environ.get("SMALL_CASCADE", "")
        cb_fail = os.environ.get("CB_FAILURE_THRESHOLD", "3")
        cb_succ = os.environ.get("CB_SUCCESS_THRESHOLD", "1")
        cb_tmot = os.environ.get("CB_TIMEOUT_SECONDS", "300")

        console.print(f"\n  [1] BIG cascade models    [cyan]{big_c[:60] or '(none)'}[/]")
        console.print(f"  [2] MIDDLE cascade models [cyan]{mid_c[:60] or '(none)'}[/]")
        console.print(f"  [3] SMALL cascade models  [cyan]{sml_c[:60] or '(none)'}[/]")
        console.print(f"  [4] CB failure threshold  [cyan]{cb_fail}[/] failures before open")
        console.print(f"  [5] CB success threshold  [cyan]{cb_succ}[/] successes to close")
        console.print(f"  [6] CB timeout            [cyan]{cb_tmot}[/] seconds cooldown")
        console.print("\n  [7] View/reset breakers   [dim](requires proxy running)[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect option", choices=["1","2","3","4","5","6","7","0"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            v = Prompt.ask("BIG cascade (comma-separated model IDs)", default=big_c)
            updates["BIG_CASCADE"] = v
        elif choice == "2":
            v = Prompt.ask("MIDDLE cascade (comma-separated model IDs)", default=mid_c)
            updates["MIDDLE_CASCADE"] = v
        elif choice == "3":
            v = Prompt.ask("SMALL cascade (comma-separated model IDs)", default=sml_c)
            updates["SMALL_CASCADE"] = v
        elif choice == "4":
            v = Prompt.ask("CB failure threshold", default=cb_fail)
            updates["CB_FAILURE_THRESHOLD"] = v
        elif choice == "5":
            v = Prompt.ask("CB success threshold", default=cb_succ)
            updates["CB_SUCCESS_THRESHOLD"] = v
        elif choice == "6":
            v = Prompt.ask("CB timeout seconds", default=cb_tmot)
            updates["CB_TIMEOUT_SECONDS"] = v
        elif choice == "7":
            try:
                import urllib.request
                import json
                data = json.loads(urllib.request.urlopen("http://127.0.0.1:8082/api/breakers", timeout=3).read())
                breakers = data.get("breakers", [])
                if not breakers:
                    console.print("[dim]No circuit breakers active yet.[/]")
                else:
                    for b in breakers:
                        color = "red" if b["state"] == "open" else "green"
                        console.print(f"  [{color}]{b['state']:10}[/{color}] {b['model']} — fails: {b['failure_count']}")
            except Exception as e:
                console.print(f"[red]Could not reach proxy: {e}[/]")
        if updates:
            update_env_file(updates)


def configure_local_gpu():
    """Configure Local GPU Inference (ollama/llamafile)."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Local GPU Inference[/]\n[dim]Use ollama or llamafile as the 4th cascade tier (free, private).[/]",
            border_style="green", title="🖥️  Local GPU"
        ))

        enabled = os.environ.get("LOCAL_ENABLED", "false").lower() in ("true","1")
        model = os.environ.get("LOCAL_MODEL", "")
        endpoint = os.environ.get("LOCAL_ENDPOINT", "http://localhost:11434/v1")

        status = "[green]ENABLED[/]" if enabled else "[dim]disabled[/]"
        console.print(f"\n  [1] Enable/disable         {status}")
        console.print(f"  [2] Model name             [cyan]{model or '(not set)'}[/]  [dim](e.g. llama3.2, mistral, phi3)[/]")
        console.print(f"  [3] Endpoint URL           [cyan]{endpoint}[/]  [dim](ollama: :11434/v1, llamafile: :8080/v1)[/]")
        console.print("\n  [dim]Setup: install ollama → ollama pull llama3.2 → set LOCAL_MODEL=llama3.2[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect option", choices=["1","2","3","0"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            new_enabled = not enabled
            updates["LOCAL_ENABLED"] = "true" if new_enabled else "false"
            console.print(f"[cyan]Local GPU: {'ENABLED' if new_enabled else 'DISABLED'}[/]")
        elif choice == "2":
            v = Prompt.ask("Local model name", default=model)
            updates["LOCAL_MODEL"] = v
        elif choice == "3":
            v = Prompt.ask("Local endpoint URL", default=endpoint)
            updates["LOCAL_ENDPOINT"] = v
        if updates:
            update_env_file(updates)


def configure_compression():
    """Configure Compression & Semantic Cache."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Compression & Cache[/]\n[dim]Headroom bypass, tool schema stripping, semantic dedup cache.[/]",
            border_style="cyan", title="🗜️  Compression"
        ))

        bypass = os.environ.get("HEADROOM_BYPASS_THRESHOLD", "0")
        strip = os.environ.get("TOOL_SCHEMA_STRIP", "true").lower() in ("true","1")
        tool_desc = os.environ.get("TOOL_DESC_MAX", "200")
        tool_param_desc = os.environ.get("TOOL_PARAM_DESC_MAX", "120")
        sc_on = os.environ.get("SEMANTIC_CACHE_ENABLED", "true").lower() in ("true","1")
        sc_thr = os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.97")
        sc_ttl = os.environ.get("SEMANTIC_CACHE_TTL", "3600")
        sc_sz = os.environ.get("SEMANTIC_CACHE_SIZE", "256")
        token_cache = os.environ.get("TOKEN_COUNT_CACHE_SIZE", "512")

        console.print(f"\n  [1] Headroom bypass threshold  [cyan]{bypass}[/] tokens [dim](0=disabled; skip compression for small requests)[/]")
        console.print(f"  [2] Tool schema stripping      {'[green]ON[/]' if strip else '[dim]off[/]'}  [dim](9-52% tool JSON reduction)[/]")
        console.print(f"  [3] Tool description max       [cyan]{tool_desc}[/] chars")
        console.print(f"  [4] Tool parameter desc max    [cyan]{tool_param_desc}[/] chars")
        console.print(f"  [5] Semantic cache             {'[green]ON[/]' if sc_on else '[dim]off[/]'}  [dim](near-dup prompt dedup)[/]")
        console.print(f"  [6] Semantic cache threshold   [cyan]{sc_thr}[/]  [dim](0.97 = 97% similarity)[/]")
        console.print(f"  [7] Semantic cache TTL         [cyan]{sc_ttl}[/]s  [dim](entry expiry)[/]")
        console.print(f"  [8] Semantic cache size        [cyan]{sc_sz}[/] entries  [dim](LRU max)[/]")
        console.print(f"  [9] Token count cache size     [cyan]{token_cache}[/] entries")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect option", choices=["1","2","3","4","5","6","7","8","9","0"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            v = Prompt.ask("Headroom bypass threshold tokens (0=disabled)", default=bypass)
            updates["HEADROOM_BYPASS_THRESHOLD"] = v
        elif choice == "2":
            updates["TOOL_SCHEMA_STRIP"] = "false" if strip else "true"
            console.print(f"[cyan]Tool schema stripping: {'ON' if not strip else 'OFF'}[/]")
        elif choice == "3":
            updates["TOOL_DESC_MAX"] = Prompt.ask("Max tool description chars", default=tool_desc)
        elif choice == "4":
            updates["TOOL_PARAM_DESC_MAX"] = Prompt.ask(
                "Max parameter description chars", default=tool_param_desc
            )
        elif choice == "5":
            updates["SEMANTIC_CACHE_ENABLED"] = "false" if sc_on else "true"
            console.print(f"[cyan]Semantic cache: {'ON' if not sc_on else 'OFF'}[/]")
        elif choice == "6":
            v = Prompt.ask("Similarity threshold (0.0-1.0)", default=sc_thr)
            updates["SEMANTIC_CACHE_THRESHOLD"] = v
        elif choice == "7":
            v = Prompt.ask("TTL seconds", default=sc_ttl)
            updates["SEMANTIC_CACHE_TTL"] = v
        elif choice == "8":
            v = Prompt.ask("Max cache entries", default=sc_sz)
            updates["SEMANTIC_CACHE_SIZE"] = v
        elif choice == "9":
            updates["TOKEN_COUNT_CACHE_SIZE"] = Prompt.ask(
                "Token count cache entries", default=token_cache
            )
        if updates:
            update_env_file(updates)


def configure_router_slots():
    """Configure Router Slots (use-case model assignments)."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Router Slots[/]\n[dim]Assign specific models to use-case tags. Empty = use tier default.[/]",
            border_style="magenta", title="🗺️  Router Slots"
        ))

        slots = {
            "ROUTER_BACKGROUND": ("Background tasks", "nvidia/nemotron-nano-9b-v2:free"),
            "ROUTER_THINK": ("Reasoning/thinking", ""),
            "ROUTER_LONG_CONTEXT": ("Long-context requests", ""),
            "ROUTER_LONG_CONTEXT_THRESHOLD": ("Long-context threshold", "60000"),
            "ROUTER_WEB_SEARCH": ("Web search tool calls", ""),
            "ROUTER_IMAGE": ("Image/vision requests", ""),
        }

        for i, (key, (label, default)) in enumerate(slots.items(), 1):
            current = os.environ.get(key, default)
            display = f"[cyan]{current}[/]" if current else "[dim](tier default)[/]"
            console.print(f"  [{i}] {label:<30} {display}")
        console.print("  [0] Back")

        num_slots = len(slots)
        choice = Prompt.ask("\nSelect slot to configure", choices=[str(i) for i in range(num_slots+1)], default="0")
        if choice == "0":
            return
        idx = int(choice) - 1
        key, (label, default) = list(slots.items())[idx]
        current = os.environ.get(key, default)
        new_val = Prompt.ask(f"{label}", default=current)
        if new_val != current:
            update_env_file({key: new_val})


def configure_models():
    """Configure model selection for BIG/MIDDLE/SMALL tiers and cascade."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Model Selection[/]\n[dim]Set the model for each tier and configure cascade fallback.[/]",
            border_style="blue", title="🤖 Models"
        ))

        big = os.environ.get("BIG_MODEL", "")
        mid = os.environ.get("MIDDLE_MODEL", "")
        sml = os.environ.get("SMALL_MODEL", "")
        cascade = os.environ.get("MODEL_CASCADE", "true")
        big_c = os.environ.get("BIG_CASCADE", "")
        mid_c = os.environ.get("MIDDLE_CASCADE", "")
        sml_c = os.environ.get("SMALL_CASCADE", "")
        daily_lim = os.environ.get("MODEL_CASCADE_DAILY_LIMIT", "0")
        or_fb = os.environ.get("OPENROUTER_FALLBACK_MODELS", "")

        console.print(f"\n  [1] BIG model              [cyan]{big or '(not set)'}[/]")
        console.print(f"  [2] MIDDLE model           [cyan]{mid or '(not set)'}[/]")
        console.print(f"  [3] SMALL model            [cyan]{sml or '(not set)'}[/]")
        console.print(f"  [4] Model cascade enabled  [cyan]{cascade}[/]")
        console.print(f"  [5] BIG cascade fallbacks  [cyan]{big_c or '(none)'}[/]")
        console.print(f"  [6] MIDDLE cascade fallbacks [cyan]{mid_c or '(none)'}[/]")
        console.print(f"  [7] SMALL cascade fallbacks  [cyan]{sml_c or '(none)'}[/]")
        console.print(f"  [8] Cascade daily limit    [cyan]{daily_lim}[/] [dim](0=unlimited)[/]")
        console.print(f"  [9] OpenRouter fallback pool [cyan]{or_fb or '(auto)'}[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect", choices=[str(i) for i in range(10)], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            updates["BIG_MODEL"] = Prompt.ask("BIG model (e.g. anthropic/claude-opus-4-20250514)", default=big)
        elif choice == "2":
            updates["MIDDLE_MODEL"] = Prompt.ask("MIDDLE model (e.g. openai/claude-sonnet-4-5)", default=mid)
        elif choice == "3":
            updates["SMALL_MODEL"] = Prompt.ask("SMALL model (e.g. openai/claude-haiku-4-5)", default=sml)
        elif choice == "4":
            v = Confirm.ask("Enable model cascade?", default=cascade.lower() == "true")
            updates["MODEL_CASCADE"] = "true" if v else "false"
        elif choice == "5":
            updates["BIG_CASCADE"] = Prompt.ask("BIG cascade (comma-separated models)", default=big_c)
        elif choice == "6":
            updates["MIDDLE_CASCADE"] = Prompt.ask("MIDDLE cascade (comma-separated models)", default=mid_c)
        elif choice == "7":
            updates["SMALL_CASCADE"] = Prompt.ask("SMALL cascade (comma-separated models)", default=sml_c)
        elif choice == "8":
            updates["MODEL_CASCADE_DAILY_LIMIT"] = Prompt.ask("Daily limit per model (0=unlimited)", default=daily_lim)
        elif choice == "9":
            updates["OPENROUTER_FALLBACK_MODELS"] = Prompt.ask("OpenRouter fallback pool (comma-separated)", default=or_fb)
        if updates:
            update_env_file(updates)


def configure_fusion():
    """Configure OpenRouter Fusion profiles and aliases."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]OpenRouter Fusion[/]\n"
            "[dim]Route a request through a panel of models and a judge model.[/]",
            border_style="magenta", title="🧬 Fusion"
        ))

        profile = os.environ.get("FUSION_PROFILE", "free")
        aliases = os.environ.get("FUSION_ALIASES", "fusion,ccp/fusion,openrouter/fusion")
        analysis = os.environ.get(
            "FUSION_FREE_ANALYSIS_MODELS",
            "openrouter/free,openrouter/free,openrouter/free",
        )
        judge = os.environ.get("FUSION_FREE_MODEL", "openrouter/free")
        preset = os.environ.get("FUSION_FREE_PRESET", "")
        force = os.environ.get("FUSION_FREE_FORCE", "true")
        profiles = os.environ.get("FUSION_PROFILES", "")

        console.print(f"\n  [1] Default profile        [cyan]{profile}[/]")
        console.print(f"  [2] Fusion aliases         [cyan]{aliases}[/]")
        console.print(f"  [3] Free panel models      [cyan]{analysis}[/]")
        console.print(f"  [4] Free judge model       [cyan]{judge}[/]")
        console.print(f"  [5] Free preset            [cyan]{preset or '(none)'}[/]")
        console.print(f"  [6] Force no-tool Fusion   [cyan]{force}[/]")
        console.print(f"  [7] JSON profiles          [cyan]{profiles or '(none)'}[/]")
        console.print("  [8] Set MIDDLE_MODEL=fusion")
        console.print("  [0] Back")

        choice = Prompt.ask(
            "\nSelect",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"],
            default="0",
        )
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            updates["FUSION_PROFILE"] = Prompt.ask("Default Fusion profile", default=profile)
        elif choice == "2":
            updates["FUSION_ALIASES"] = Prompt.ask("Comma-separated aliases", default=aliases)
        elif choice == "3":
            updates["FUSION_FREE_ANALYSIS_MODELS"] = Prompt.ask(
                "Free profile panel models", default=analysis
            )
        elif choice == "4":
            updates["FUSION_FREE_MODEL"] = Prompt.ask("Free profile judge model", default=judge)
        elif choice == "5":
            updates["FUSION_FREE_PRESET"] = Prompt.ask("OpenRouter preset (blank=none)", default=preset)
        elif choice == "6":
            v = Confirm.ask(
                "Force Fusion when no other tools compete?",
                default=force.lower() == "true",
            )
            updates["FUSION_FREE_FORCE"] = "true" if v else "false"
        elif choice == "7":
            updates["FUSION_PROFILES"] = Prompt.ask("Fusion profile JSON", default=profiles)
        elif choice == "8":
            updates["MIDDLE_MODEL"] = "fusion"

        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_toolcalls():
    """Configure tool-call routing and truncation."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Tool Call Settings[/]\n[dim]Control how the proxy handles tool-call requests.[/]",
            border_style="cyan", title="🔧 Tool Calls"
        ))

        tc_models = os.environ.get("TOOLCALL_MODELS", "")
        tc_auto = os.environ.get("TOOLCALL_AUTO_ROUTE", "true")
        tc_retries = os.environ.get("TOOLCALL_MAX_RETRIES", "2")
        tc_max = os.environ.get("TOOL_OUTPUT_MAX_CHARS", "50000")
        tc_trunc = os.environ.get("TOOL_OUTPUT_TRUNCATION", "false")

        console.print(f"\n  [1] Tool-call capable models  [cyan]{tc_models or '(none — use tier)'}[/]")
        console.print(f"  [2] Auto-route tool requests  [cyan]{tc_auto}[/]")
        console.print(f"  [3] Max retries per model     [cyan]{tc_retries}[/]")
        console.print(f"  [4] Max tool output chars     [cyan]{tc_max}[/]")
        console.print(f"  [5] Enable output truncation  [cyan]{tc_trunc}[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect", choices=["0","1","2","3","4","5"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            updates["TOOLCALL_MODELS"] = Prompt.ask("Comma-separated tool-capable models", default=tc_models)
        elif choice == "2":
            v = Confirm.ask("Auto-route tool requests?", default=tc_auto.lower() == "true")
            updates["TOOLCALL_AUTO_ROUTE"] = "true" if v else "false"
        elif choice == "3":
            updates["TOOLCALL_MAX_RETRIES"] = Prompt.ask("Max retries (1-10)", default=tc_retries)
        elif choice == "4":
            updates["TOOL_OUTPUT_MAX_CHARS"] = Prompt.ask("Max output chars (e.g. 50000)", default=tc_max)
        elif choice == "5":
            v = Confirm.ask("Enable tool output truncation?", default=tc_trunc.lower() == "true")
            updates["TOOL_OUTPUT_TRUNCATION"] = "true" if v else "false"
        if updates:
            update_env_file(updates)


def configure_logging_advanced():
    """Configure log file rotation and debug traffic logging."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Logging Settings[/]\n[dim]Log file path, rotation, and debug verbosity.[/]",
            border_style="dim", title="📋 Logging"
        ))

        log_file = os.environ.get("LOG_FILE", "logs/proxy.log")
        log_max = os.environ.get("LOG_MAX_SIZE_MB", "50")
        log_ret = os.environ.get("LOG_RETENTION_DAYS", "7")
        debug_traf = os.environ.get("DEBUG_TRAFFIC_LOG", "false")
        debug_quiet = os.environ.get("DEBUG_TRAFFIC_QUIET", "false")

        console.print(f"\n  [1] Log file path       [cyan]{log_file}[/]")
        console.print(f"  [2] Max size (MB)       [cyan]{log_max}[/]")
        console.print(f"  [3] Retention (days)    [cyan]{log_ret}[/]")
        console.print(f"  [4] Debug traffic log   [cyan]{debug_traf}[/] [dim](dumps full HTTP headers)[/]")
        console.print(f"  [5] Suppress debug dump [cyan]{debug_quiet}[/] [dim](quiet traffic at LOG_LEVEL=debug)[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect", choices=["0","1","2","3","4","5"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            updates["LOG_FILE"] = Prompt.ask("Log file path", default=log_file)
        elif choice == "2":
            updates["LOG_MAX_SIZE_MB"] = Prompt.ask("Max log size MB", default=log_max)
        elif choice == "3":
            updates["LOG_RETENTION_DAYS"] = Prompt.ask("Retention days", default=log_ret)
        elif choice == "4":
            v = Confirm.ask("Enable debug traffic log?", default=debug_traf.lower() == "true")
            updates["DEBUG_TRAFFIC_LOG"] = "true" if v else "false"
        elif choice == "5":
            v = Confirm.ask(
                "Suppress full traffic dump at LOG_LEVEL=debug?",
                default=debug_quiet.lower() == "true",
            )
            updates["DEBUG_TRAFFIC_QUIET"] = "true" if v else "false"
        if updates:
            update_env_file(updates)


def configure_watchdog():
    """Configure the auto-recovery watchdog."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold]Watchdog[/]\n[dim]Auto-recovery watchdog monitors service health and restarts dead processes.[/]",
            border_style="green", title="🐕 Watchdog"
        ))

        enabled = os.environ.get("PROXY_WATCHDOG", "false")
        interval = os.environ.get("WATCHDOG_INTERVAL", "30")
        grace = os.environ.get("WATCHDOG_GRACE", "5")

        console.print(f"\n  [1] Watchdog enabled    [cyan]{enabled}[/]")
        console.print(f"  [2] Check interval      [cyan]{interval}s[/]")
        console.print(f"  [3] Grace period        [cyan]{grace}s[/] [dim](wait before restart)[/]")
        console.print("  [0] Back")

        choice = Prompt.ask("\nSelect", choices=["0","1","2","3"], default="0")
        updates = {}
        if choice == "0":
            return
        elif choice == "1":
            v = Confirm.ask("Enable watchdog?", default=enabled.lower() == "true")
            updates["PROXY_WATCHDOG"] = "true" if v else "false"
        elif choice == "2":
            updates["WATCHDOG_INTERVAL"] = Prompt.ask("Check interval (seconds, 5-300)", default=interval)
        elif choice == "3":
            updates["WATCHDOG_GRACE"] = Prompt.ask("Grace period (seconds, 1-60)", default=grace)
        if updates:
            update_env_file(updates)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
