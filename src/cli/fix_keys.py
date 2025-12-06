#!/usr/bin/env python3
"""
API Key Wizard (Python Version)
Fixes API keys in the global profile.
"""

import os
import sys
import re
import datetime
from pathlib import Path
from typing import Optional, Dict

# Try to import rich for better UI
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback helpers
    class Console:
        def print(self, *args, **kwargs): print(*args)
    class Prompt:
        @staticmethod
        def ask(text, choices=None, default=None, password=False):
            if choices:
                print(f"{text} ({'/'.join(choices)}) [{default}]: ", end="")
            else:
                print(f"{text} [{default}]: " if default else f"{text}: ", end="")
            return input()
    console = Console()

def main():
    if RICH_AVAILABLE:
        console.print(Panel.fit("[bold cyan]🧙 API Key Wizard for Claude Code Proxy[/bold cyan]", border_style="cyan"))
        console.print("This wizard will help you fix your API keys in your shell profile.\n")
    else:
        print("\n🧙 API Key Wizard for Claude Code Proxy")
        print("This wizard will help you fix your API keys in your shell profile.\n")

    # 1. Target Config File
    # We use the .env file in the project root
    project_root = Path(__file__).parent.parent.parent
    profile_path = project_root / ".env"
    
    if not profile_path.exists():
        console.print(f"[yellow]Creating new config file at {profile_path}[/yellow]")
        profile_path.touch()
    else:
        console.print(f"Using config file: [yellow]{profile_path}[/yellow]\n")

    # 2. Select Provider
    providers = {
        "1": {"name": "Anthropic (Claude)", "var": "ANTHROPIC_API_KEY", "url_var": "ANTHROPIC_BASE_URL", "url": "https://api.anthropic.com", "prefix": "sk-ant-"},
        "2": {"name": "OpenRouter", "var": "OPENROUTER_API_KEY", "url_var": "OPENROUTER_BASE_URL", "url": "https://openrouter.ai/api/v1", "prefix": "sk-or-"},
        "3": {"name": "OpenAI", "var": "OPENAI_API_KEY", "url_var": "OPENAI_BASE_URL", "url": "https://api.openai.com/v1", "prefix": "sk-"},
        "4": {"name": "Google Gemini", "var": "GOOGLE_API_KEY", "url_var": "GOOGLE_BASE_URL", "url": "https://generativelanguage.googleapis.com/v1beta/openai", "prefix": ""},
        "5": {"name": "Perplexity", "var": "PERPLEXITY_API_KEY", "url_var": "PERPLEXITY_BASE_URL", "url": "https://api.perplexity.ai", "prefix": "pplx-"},
    }

    if RICH_AVAILABLE:
        console.print("[bold]Select your provider:[/bold]")
        for k, v in providers.items():
            console.print(f"{k}) {v['name']}")
        choice = Prompt.ask("Enter number", choices=list(providers.keys()), default="1")
    else:
        print("Select your provider:")
        for k, v in providers.items():
            print(f"{k}) {v['name']}")
        choice = input("Enter number (1-5): ")

    if choice not in providers:
        console.print("[red]Invalid choice. Exiting.[/red]")
        sys.exit(1)

    provider = providers[choice]
    console.print(f"\nSelected Provider: [green]{provider['name']}[/green]")

    # 3. Input Key
    api_key = Prompt.ask(f"Enter your REAL {provider['name']} API Key", password=True)
    
    if not api_key:
        console.print("[red]API Key cannot be empty. Exiting.[/red]")
        sys.exit(1)

    # Validation
    if provider["prefix"] and not api_key.startswith(provider["prefix"]):
        if RICH_AVAILABLE:
            if not Confirm.ask(f"[yellow]Warning: Key usually starts with '{provider['prefix']}'. Continue?[/yellow]"):
                sys.exit(1)
        else:
            if input(f"Warning: Key usually starts with '{provider['prefix']}'. Continue? (y/n): ") != "y":
                sys.exit(1)

    # 4. Write to Config File
    console.print(f"\nWriting to {profile_path}...")
    
    try:
        _update_profile(profile_path, provider, api_key)
        console.print(f"[green]✅ Successfully updated {profile_path}[/green]")
        console.print(f"\n[blue]Note: The proxy will automatically pick up these changes.[/blue]")
    except Exception as e:
        console.print(f"[red]Error updating config: {e}[/red]")
        sys.exit(1)

def _update_profile(path: Path, provider: Dict, api_key: str):
    # Backup
    # backup_path = path.with_suffix(f"{path.suffix}.bak.{int(datetime.datetime.now().timestamp())}")
    # shutil.copy2(path, backup_path)
    
    content = path.read_text()
    lines = content.splitlines()
    new_lines = []
    
    # Variables to update
    updates = {
        provider["var"]: api_key,
        provider["url_var"]: provider["url"],
        "PROVIDER_API_KEY": f"${provider['var']}",
        "PROVIDER_BASE_URL": f"${provider['url_var']}"
    }
    
    # Track which ones we found
    found = {k: False for k in updates.keys()}
    
    # Simple .env format: KEY=VALUE (no export needed usually, but python-dotenv handles export)
    # We will stick to KEY="VALUE" for safety
    
    for line in lines:
        updated_line = line
        for var, val in updates.items():
            # Regex to match VAR=... or export VAR=...
            if re.match(fr'^\s*(export\s+)?{var}=', line):
                # Keep 'export' if it was there, otherwise just VAR=
                prefix = "export " if "export" in line else ""
                updated_line = f'{prefix}{var}="{val}"'
                found[var] = True
                break
        new_lines.append(updated_line)
    
    # Append missing
    if any(not v for v in found.values()):
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(f"# Updated by Claude Code Proxy Wizard {datetime.datetime.now()}")
        for var, val in updates.items():
            if not found[var]:
                # Default to just VAR="VAL" for .env, unless we want to be shell compatible
                # Let's use export for maximum compatibility if user sources it
                new_lines.append(f'{var}="{val}"')
    
    path.write_text("\n".join(new_lines) + "\n")

if __name__ == "__main__":
    main()
