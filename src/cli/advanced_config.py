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
        console.print(Panel(
            "[bold magenta]🧠 Reasoning Configuration[/]\n"
            "[dim]Control Claude's thinking process[/]",
            border_style="magenta"
        ))
        
        # Current Values
        effort = os.getenv("REASONING_EFFORT", "disabled")
        tokens = os.getenv("REASONING_MAX_TOKENS", "not set")
        exclude = os.getenv("REASONING_EXCLUDE", "false")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  Effort:      [cyan]{effort}[/]")
        console.print(f"  Max Tokens:  [cyan]{tokens}[/]")
        console.print(f"  Exclude:     [cyan]{exclude}[/] (Don't reason on non-coding tasks)")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  [1] Set Effort (low/medium/high)")
        console.print("  [2] Set Max Budget Tokens")
        console.print("  [3] Toggle Exclusion")
        console.print("  [4] [red]Disable Reasoning[/] (Unset variables)")
        console.print("  [0] Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        
        updates = {}
        
        if choice == "0":
            return
        elif choice == "1":
            new_effort = Prompt.ask("Select effort", choices=["low", "medium", "high"], default="medium")
            updates["REASONING_EFFORT"] = new_effort
        elif choice == "2":
            new_tokens = Prompt.ask("Enter max tokens (int)", default="12000")
            updates["REASONING_MAX_TOKENS"] = new_tokens
        elif choice == "3":
            new_val = "true" if exclude.lower() != "true" else "false"
            updates["REASONING_EXCLUDE"] = new_val
        elif choice == "4":
            if Confirm.ask("Disable reasoning features?"):
                updates["REASONING_EFFORT"] = None
                updates["REASONING_MAX_TOKENS"] = None
                # We might keep EXCLUDE or remove it, usually good to remove
                updates["REASONING_EXCLUDE"] = None
        
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
        console.print(Panel(
            "[bold green]🌐 Network & Server Config[/]\n"
            "[dim]Host, Port, and Logging details[/]",
            border_style="green"
        ))
        
        host = os.getenv("HOST", "0.0.0.0")
        port = os.getenv("PORT", "8082")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        timeout = os.getenv("TIMEOUT", "not set")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
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
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        
        if choice == "0":
            return
        elif choice == "1":
            updates["HOST"] = Prompt.ask("Enter Host", default="0.0.0.0")
        elif choice == "2":
            updates["PORT"] = Prompt.ask("Enter Port", default="8082")
        elif choice == "3":
            updates["LOG_LEVEL"] = Prompt.ask("Select Level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
        elif choice == "4":
            val = Prompt.ask("Enter Timeout (seconds)", default="120")
            updates["TIMEOUT"] = val
            
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
            input("\nPress Enter to continue...")

def configure_features():
    """Configure Feature Flags."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold blue]🚩 Feature Flags[/]\n"
            "[dim]Toggle experimental or optional features[/]",
            border_style="blue"
        ))
        
        compact = os.getenv("COMPACT_LOGGER", "false")
        usage = os.getenv("TRACK_USAGE", "false")
        refresh = os.getenv("DASHBOARD_REFRESH", "0.5")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Compact Logger:  [cyan]{compact}[/]")
        console.print(f"  2. Track Usage:     [cyan]{usage}[/]")
        console.print(f"  3. Dash Refresh:    [cyan]{refresh}[/]s")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to toggle/edit, or [0] to Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "0"], default="0")
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
            updates["DASHBOARD_REFRESH"] = Prompt.ask("Enter Refresh Rate (float)", default="0.5")
            
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v is None: os.environ.pop(k, None)
                else: os.environ[k] = v
            # No input wait for toggles to make it snappy, unless it was a text input
            if choice == "3":
                input("\nPress Enter to continue...")

def configure_api_keys():
    """Configure API Keys and Provider settings."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold yellow]🔑 API Keys & Provider[/]\n"
            "[dim]Configure endpoints and authentication[/]",
            border_style="yellow"
        ))
        
        provider_url = os.getenv("PROVIDER_BASE_URL", "not set")
        proxy_key = os.getenv("PROXY_AUTH_KEY", "not set")
        openrouter = os.getenv("OPENROUTER_API_KEY", "not set")[:20] + "..." if os.getenv("OPENROUTER_API_KEY") else "not set"
        exa = os.getenv("EXA_API_KEY", "not set")[:20] + "..." if os.getenv("EXA_API_KEY") else "not set"
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Provider URL:    [cyan]{provider_url}[/]")
        console.print(f"  2. Proxy Auth Key:  [cyan]{proxy_key}[/]")
        console.print(f"  3. OpenRouter Key:  [cyan]{openrouter}[/]")
        console.print(f"  4. Exa API Key:     [cyan]{exa}[/]")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        
        if choice == "0":
            return
        elif choice == "1":
            updates["PROVIDER_BASE_URL"] = Prompt.ask("Enter Provider URL", default="http://127.0.0.1:8317/v1")
        elif choice == "2":
            updates["PROXY_AUTH_KEY"] = Prompt.ask("Enter Proxy Auth Key", default="pass")
        elif choice == "3":
            updates["OPENROUTER_API_KEY"] = Prompt.ask("Enter OpenRouter API Key")
        elif choice == "4":
            updates["EXA_API_KEY"] = Prompt.ask("Enter Exa API Key (for model ranking)")
            
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v: os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_hybrid_mode():
    """Configure Hybrid Mode (per-model routing)."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold red]🔀 Hybrid Mode[/]\n"
            "[dim]Route different model tiers to different providers[/]",
            border_style="red"
        ))
        
        # Current values
        big_enabled = os.getenv("ENABLE_BIG_ENDPOINT", "false")
        big_endpoint = os.getenv("BIG_ENDPOINT", "not set")
        middle_enabled = os.getenv("ENABLE_MIDDLE_ENDPOINT", "false")
        middle_endpoint = os.getenv("MIDDLE_ENDPOINT", "not set")
        small_enabled = os.getenv("ENABLE_SMALL_ENDPOINT", "false")
        small_endpoint = os.getenv("SMALL_ENDPOINT", "not set")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  [bold]BIG[/]    Enabled: [cyan]{big_enabled}[/]  Endpoint: [cyan]{big_endpoint}[/]")
        console.print(f"  [bold]MIDDLE[/] Enabled: [cyan]{middle_enabled}[/]  Endpoint: [cyan]{middle_endpoint}[/]")
        console.print(f"  [bold]SMALL[/]  Enabled: [cyan]{small_enabled}[/]  Endpoint: [cyan]{small_endpoint}[/]")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  [1] Configure BIG endpoint")
        console.print("  [2] Configure MIDDLE endpoint")
        console.print("  [3] Configure SMALL endpoint")
        console.print("  [4] Disable all hybrid routing")
        console.print("  [0] Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        
        if choice == "0":
            return
        elif choice in ["1", "2", "3"]:
            tier = {"1": "BIG", "2": "MIDDLE", "3": "SMALL"}[choice]
            enabled = Confirm.ask(f"Enable {tier} endpoint override?")
            updates[f"ENABLE_{tier}_ENDPOINT"] = "true" if enabled else "false"
            if enabled:
                updates[f"{tier}_ENDPOINT"] = Prompt.ask(f"Enter {tier} endpoint URL", default="https://openrouter.ai/api/v1")
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
                if v: os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_token_limits():
    """Configure Token Limits and Timeouts."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold cyan]📊 Token Limits & Timeouts[/]\n"
            "[dim]Control request sizes and timing[/]",
            border_style="cyan"
        ))
        
        max_tokens = os.getenv("MAX_TOKENS_LIMIT", "65536")
        min_tokens = os.getenv("MIN_TOKENS_LIMIT", "4096")
        timeout = os.getenv("REQUEST_TIMEOUT", "120")
        retries = os.getenv("MAX_RETRIES", "2")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Max Tokens:      [cyan]{max_tokens}[/]")
        console.print(f"  2. Min Tokens:      [cyan]{min_tokens}[/]")
        console.print(f"  3. Request Timeout: [cyan]{timeout}[/]s")
        console.print(f"  4. Max Retries:     [cyan]{retries}[/]")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        
        if choice == "0":
            return
        elif choice == "1":
            updates["MAX_TOKENS_LIMIT"] = Prompt.ask("Enter Max Tokens", default="65536")
        elif choice == "2":
            updates["MIN_TOKENS_LIMIT"] = Prompt.ask("Enter Min Tokens", default="4096")
        elif choice == "3":
            updates["REQUEST_TIMEOUT"] = Prompt.ask("Enter Timeout (seconds)", default="120")
        elif choice == "4":
            updates["MAX_RETRIES"] = Prompt.ask("Enter Max Retries", default="2")
            
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v: os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_custom_prompts():
    """Configure Custom System Prompts."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold magenta]📝 Custom System Prompts[/]\n"
            "[dim]Override system prompts per model tier[/]",
            border_style="magenta"
        ))
        
        big_enabled = os.getenv("ENABLE_CUSTOM_BIG_PROMPT", "false")
        middle_enabled = os.getenv("ENABLE_CUSTOM_MIDDLE_PROMPT", "false")
        small_enabled = os.getenv("ENABLE_CUSTOM_SMALL_PROMPT", "false")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. BIG Custom Prompt:    [cyan]{big_enabled}[/]")
        console.print(f"  2. MIDDLE Custom Prompt: [cyan]{middle_enabled}[/]")
        console.print(f"  3. SMALL Custom Prompt:  [cyan]{small_enabled}[/]")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to configure, or [0] to Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "0"], default="0")
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
                    updates[f"{tier}_SYSTEM_PROMPT_FILE"] = Prompt.ask(f"Enter prompt file path")
                else:
                    updates[f"{tier}_SYSTEM_PROMPT"] = Prompt.ask(f"Enter system prompt (short)")
                    
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v: os.environ[k] = v
            input("\nPress Enter to continue...")


def configure_crosstalk():
    """Configure Crosstalk (Model-to-Model conversations)."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold white]💬 Crosstalk Configuration[/]\n"
            "[dim]Enable model-to-model conversations[/]",
            border_style="white"
        ))
        
        enabled = os.getenv("CROSSTALK_ENABLED", "false")
        paradigm = os.getenv("CROSSTALK_PARADIGM", "relay")
        iterations = os.getenv("CROSSTALK_ITERATIONS", "20")
        models = os.getenv("CROSSTALK_MODELS", "not set")
        
        console.print(f"\n[bold yellow]Current Settings:[/]")
        console.print(f"  1. Enabled:    [cyan]{enabled}[/]")
        console.print(f"  2. Paradigm:   [cyan]{paradigm}[/] [dim](memory, report, relay, debate)[/]")
        console.print(f"  3. Iterations: [cyan]{iterations}[/]")
        console.print(f"  4. Models:     [cyan]{models}[/]")
        
        console.print("\n[bold cyan]Options:[/]")
        console.print("  Enter number to edit, or [0] to Back")
        
        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "0"], default="0")
        updates = {}
        
        if choice == "0":
            return
        elif choice == "1":
            new_val = "true" if enabled.lower() != "true" else "false"
            updates["CROSSTALK_ENABLED"] = new_val
        elif choice == "2":
            updates["CROSSTALK_PARADIGM"] = Prompt.ask("Select paradigm", choices=["memory", "report", "relay", "debate"], default="relay")
        elif choice == "3":
            updates["CROSSTALK_ITERATIONS"] = Prompt.ask("Enter iterations", default="20")
        elif choice == "4":
            updates["CROSSTALK_MODELS"] = Prompt.ask("Enter models (comma-separated)", default="gpt-4o,gemini-3-pro-preview")
            
        if updates:
            update_env_file(updates)
            for k, v in updates.items():
                if v: os.environ[k] = v
            input("\nPress Enter to continue...")


def main():
    """Main Advanced Config Menu."""
    while True:
        console.clear()
        console.print(Panel(
            "[bold white]Advanced Configuration[/]\n\n"
            "[dim]Deep dive into proxy behavior. Changes update .env directly.[/]",
            title="⚙️  Parameter Tuner",
            border_style="yellow"
        ))
        
        console.print("\n[bold cyan]Categories:[/]")
        console.print("  [1] 🔑 API Keys & Provider   [dim](Endpoints, Auth)[/]")
        console.print("  [2] 🧠 Reasoning / Thinking  [dim](Extended CoT models)[/]")
        console.print("  [3] 🌐 Network & Server      [dim](Host, Port, Logging)[/]")
        console.print("  [4] 📊 Token Limits          [dim](Max tokens, Timeouts)[/]")
        console.print("  [5] 🔀 Hybrid Mode           [dim](Per-model routing)[/]")
        console.print("  [6] 📝 Custom Prompts        [dim](System prompt overrides)[/]")
        console.print("  [7] 💬 Crosstalk             [dim](Model-to-model chat)[/]")
        console.print("  [8] 🚩 Feature Flags         [dim](Toggles & Options)[/]")
        console.print("  [0] 🔙 Back to Main Menu")
        
        choice = Prompt.ask("\nSelect category", choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"], default="0")
        
        if choice == "0":
            return
        elif choice == "1":
            configure_api_keys()
        elif choice == "2":
            configure_reasoning()
        elif choice == "3":
            configure_network()
        elif choice == "4":
            configure_token_limits()
        elif choice == "5":
            configure_hybrid_mode()
        elif choice == "6":
            configure_custom_prompts()
        elif choice == "7":
            configure_crosstalk()
        elif choice == "8":
            configure_features()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")

