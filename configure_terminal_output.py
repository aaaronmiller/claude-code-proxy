#!/usr/bin/env python3
"""
Interactive Terminal Output Configuration for Claude Code Proxy

This script helps you configure terminal output display settings similar to
the prompt injection configuration system. Customize what metrics you want
to see and how they're displayed.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import print as rprint

console = Console()


def show_example_output(mode: str, show_workspace: bool, show_context: bool, show_task: bool, show_speed: bool, show_cost: bool):
    """Show an example of what the terminal output will look like"""
    console.print("\n[bold cyan]Preview of Terminal Output:[/]")
    console.print("─" * 80)

    # Create a mock example based on settings
    text = Text()

    if show_workspace:
        text.append(" claude-code-proxy ", style="bold white on bright_cyan")
        text.append("  ", style="")

    text.append("▶ ", style="bold bright_cyan")
    text.append("a1b2c3d4 ", style="bold bright_cyan")
    text.append("| ", style="dim")

    text.append("claude-3.5", style="dim bright_cyan")
    text.append("-sonnet", style="dim bright_cyan")
    text.append("→", style="dim")
    text.append("gpt-4o", style="bold bright_cyan")
    text.append("-mini", style="bold bright_cyan")
    text.append(" | ", style="dim")

    if show_context:
        text.append("CTX:", style="dim")
        text.append("12.3k", style="green")
        text.append("/200k", style="dim")
        text.append("(6%) ", style="green")

    text.append("OUT:", style="dim")
    text.append("16k ", style="blue")

    text.append("| ", style="dim")

    if show_task:
        text.append("🧠 ", style="magenta")
        text.append("REASON ", style="bold magenta")

    text.append("STREAM ", style="bold bright_cyan")
    text.append("3msg ", style="dim")

    console.print(text)

    # Completion line
    comp_text = Text()
    comp_text.append("  ✓ ", style="bold green")
    comp_text.append("a1b2c3d4 ", style="bold bright_cyan")
    comp_text.append("| ", style="dim")
    comp_text.append("5.2s ", style="yellow")
    comp_text.append("| ", style="dim")

    comp_text.append("IN:", style="dim")
    comp_text.append("12.3k ", style="cyan")

    if show_context:
        comp_text.append("(6%) ", style="green")

    comp_text.append("OUT:", style="dim")
    comp_text.append("2.1k ", style="bold blue")

    if show_context:
        comp_text.append("(13%) ", style="green")

    comp_text.append("| ", style="dim")

    if show_speed:
        comp_text.append("⚡", style="green")
        comp_text.append("82t/s ", style="bold green")

    if show_cost:
        comp_text.append("$", style="dim")
        comp_text.append("0.0042", style="green")

    console.print(comp_text)
    console.print("─" * 80)


def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Claude Code Proxy[/]\n"
        "[white]Terminal Output Configuration[/]\n\n"
        "[dim]Configure your terminal output to show exactly what you need[/]",
        border_style="cyan"
    ))

    # Current settings
    console.print("\n[bold yellow]Current Settings:[/]")
    current_mode = os.getenv("TERMINAL_DISPLAY_MODE", "detailed")
    current_show_workspace = os.getenv("TERMINAL_SHOW_WORKSPACE", "true")
    current_show_context = os.getenv("TERMINAL_SHOW_CONTEXT_PCT", "true")
    current_show_task = os.getenv("TERMINAL_SHOW_TASK_TYPE", "true")
    current_show_speed = os.getenv("TERMINAL_SHOW_SPEED", "true")
    current_show_cost = os.getenv("TERMINAL_SHOW_COST", "true")
    current_color_scheme = os.getenv("TERMINAL_COLOR_SCHEME", "auto")

    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Display Mode", current_mode)
    table.add_row("Show Workspace", current_show_workspace)
    table.add_row("Show Context %", current_show_context)
    table.add_row("Show Task Type", current_show_task)
    table.add_row("Show Speed", current_show_speed)
    table.add_row("Show Cost", current_show_cost)
    table.add_row("Color Scheme", current_color_scheme)
    console.print(table)

    # Interactive configuration
    console.print("\n[bold cyan]═══ Step 1: Display Mode ═══[/]")
    console.print("Choose how much information to display:\n")
    console.print("  [dim]1.[/] [white]minimal[/]  - Request ID + model only")
    console.print("  [dim]2.[/] [yellow]normal[/]   - Add tokens + speed")
    console.print("  [dim]3.[/] [green]detailed[/] - All metrics (context %, task type, cost)")
    console.print("  [dim]4.[/] [red]debug[/]    - Everything including system flags\n")

    mode_choice = Prompt.ask(
        "Select display mode",
        choices=["1", "2", "3", "4"],
        default="3"
    )
    mode_map = {"1": "minimal", "2": "normal", "3": "detailed", "4": "debug"}
    selected_mode = mode_map[mode_choice]

    # Metric toggles (only for detailed/debug modes)
    show_workspace = True
    show_context = True
    show_task = True
    show_speed = True
    show_cost = True

    if selected_mode in ["detailed", "debug"]:
        console.print("\n[bold cyan]═══ Step 2: Metric Visibility ═══[/]")
        console.print("Toggle individual metrics:\n")

        show_workspace = Confirm.ask("Show workspace/project name?", default=True)
        show_context = Confirm.ask("Show context window percentage?", default=True)
        show_task = Confirm.ask("Show task type (REASON, TOOLS, IMAGE)?", default=True)
        show_speed = Confirm.ask("Show tokens per second (t/s)?", default=True)
        show_cost = Confirm.ask("Show cost estimates?", default=True)

    # Color scheme
    console.print("\n[bold cyan]═══ Step 3: Color Scheme ═══[/]")
    console.print("Choose your color preference:\n")
    console.print("  [dim]1.[/] [bright_cyan]auto[/]    - Rich colors with session differentiation (default)")
    console.print("  [dim]2.[/] [bright_magenta]vibrant[/] - Bright, high-contrast colors")
    console.print("  [dim]3.[/] [dim cyan]subtle[/]  - Muted colors for less distraction")
    console.print("  [dim]4.[/] [white]mono[/]    - Minimal colors, mostly white/gray\n")

    color_choice = Prompt.ask(
        "Select color scheme",
        choices=["1", "2", "3", "4"],
        default="1"
    )
    color_map = {"1": "auto", "2": "vibrant", "3": "subtle", "4": "mono"}
    selected_color = color_map[color_choice]

    # Show preview
    show_example_output(selected_mode, show_workspace, show_context, show_task, show_speed, show_cost)

    # Confirm
    if not Confirm.ask("\n[bold yellow]Apply this configuration?[/]", default=True):
        console.print("[red]Configuration cancelled.[/]")
        return

    # Generate environment variables
    console.print("\n[bold green]═══ Configuration Complete! ═══[/]")
    console.print("\nAdd these to your [cyan].env[/] file or [cyan].zshrc[/]/[cyan].bashrc[/]:\n")

    env_vars = [
        f'export TERMINAL_DISPLAY_MODE="{selected_mode}"',
        f'export TERMINAL_SHOW_WORKSPACE="{str(show_workspace).lower()}"',
        f'export TERMINAL_SHOW_CONTEXT_PCT="{str(show_context).lower()}"',
        f'export TERMINAL_SHOW_TASK_TYPE="{str(show_task).lower()}"',
        f'export TERMINAL_SHOW_SPEED="{str(show_speed).lower()}"',
        f'export TERMINAL_SHOW_COST="{str(show_cost).lower()}"',
        f'export TERMINAL_COLOR_SCHEME="{selected_color}"',
        'export TERMINAL_SESSION_COLORS="true"',
    ]

    for var in env_vars:
        console.print(f"  [cyan]{var}[/]")

    # Offer to write to .env
    console.print()
    if Confirm.ask("Write to [cyan].env[/] file?", default=True):
        env_file = ".env"
        mode = "a" if os.path.exists(env_file) else "w"

        with open(env_file, mode) as f:
            f.write("\n# Terminal Output Configuration\n")
            for var in env_vars:
                # Extract just the KEY=VALUE part
                f.write(var.replace("export ", "") + "\n")

        console.print(f"[green]✓[/] Configuration written to {env_file}")

    console.print("\n[bold cyan]Usage:[/]")
    console.print("  Restart your proxy to apply the new settings:")
    console.print("  [dim]$[/] python start_proxy.py\n")

    console.print("[dim]You can run this script again anytime to change settings:[/]")
    console.print("  [dim]$[/] python configure_terminal_output.py\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Configuration cancelled.[/]")
        sys.exit(0)
