#!/usr/bin/env python3
"""
Unified Settings TUI

A single entry point to configure all proxy settings:
- Models (Big/Middle/Small)
- Terminal Output (colors, metrics, display mode)
- Dashboard Layout (10-slot grid)
- Prompt Injection (modules to inject)
- Advanced (Crosstalk, Modes, etc.)
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import readchar
    ARROW_SUPPORT = True
except ImportError:
    ARROW_SUPPORT = False

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich import box

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# MENU STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

MAIN_MENU = [
    ("models", "🤖 Model Selection", "Choose Big/Middle/Small models"),
    ("routing", "🔀 Model Routing", "Route tiers to different providers"),
    ("terminal", "🖥️  Terminal Output", "Colors, metrics, display mode"),
    ("dashboard", "📊 Dashboard Layout", "Arrange the 10-slot grid"),
    ("prompts", "💉 Prompt Configuration", "Stats injected into Claude's context"),
    ("analytics", "📈 Analytics", "Usage tracking and insights"),
    ("advanced", "⚙️  Advanced", "Reasoning, Server, Crosstalk"),
    ("exit", "🚪 Exit", "Return to command line"),
]


class UnifiedSettings:
    """Unified settings TUI."""

    def __init__(self):
        self.cursor = 0
        self.running = True

    def draw_header(self):
        """Draw the header."""
        console.print(Panel(
            "[bold white]Claude Code Proxy Settings[/]\n\n[dim]Configure all aspects of your proxy[/]",
            box=box.DOUBLE,
            style="cyan",
            padding=(1, 2),
            expand=False
        ))

    def draw_menu(self):
        """Draw the main menu."""
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
        table.add_column("", width=3)
        table.add_column("Option", width=35)  # Increased width for longer name
        table.add_column("Description", width=35)

        for i, (key, label, desc) in enumerate(MAIN_MENU):
            if i == self.cursor:
                marker = "▶"
                style = "bold cyan"
            else:
                marker = " "
                style = ""

            table.add_row(marker, label, desc, style=style)

        console.print(table)

    def draw_footer(self):
        """Draw navigation hints."""
        if ARROW_SUPPORT:
            hints = "[↑/↓] Navigate  [Enter] Select  [q] Quit"
        else:
            hints = "Type number (1-6) and press Enter"
        console.print(f"\n[dim]{hints}[/dim]")

    def draw(self):
        """Draw the full screen."""
        console.clear()
        self.draw_header()
        console.print()
        self.draw_menu()
        self.draw_footer()

    def handle_input(self):
        """Handle keyboard input."""
        if ARROW_SUPPORT:
            key = readchar.readkey()
            if key == readchar.key.UP:
                self.cursor = (self.cursor - 1) % len(MAIN_MENU)
            elif key == readchar.key.DOWN:
                self.cursor = (self.cursor + 1) % len(MAIN_MENU)
            elif key == readchar.key.ENTER:
                return self.select_current()
            elif key.lower() == 'q':
                self.running = False
        else:
            try:
                choice = input("\n→ ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(MAIN_MENU):
                        self.cursor = idx
                        return self.select_current()
                elif choice.lower() == 'q':
                    self.running = False
            except (EOFError, KeyboardInterrupt):
                self.running = False
        return None

    def select_current(self):
        """Handle selection of current menu item."""
        key, _, _ = MAIN_MENU[self.cursor]
        return key

    def launch_models(self):
        """Launch model selector."""
        console.clear()
        console.print("[bold cyan]Launching Model Selector...[/bold cyan]\n")
        try:
            from src.cli.model_selector import run_model_selector
            run_model_selector()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_terminal(self):
        """Launch terminal configurator."""
        console.clear()
        console.print("[bold cyan]Launching Terminal Configurator...[/bold cyan]\n")
        try:
            from src.cli.terminal_config import main as terminal_main
            terminal_main()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_dashboard(self):
        """Launch dashboard configurator."""
        console.clear()
        console.print("[bold cyan]Launching Dashboard Configurator...[/bold cyan]\n")
        try:
            from src.cli.dashboard_config import main as dashboard_main
            dashboard_main()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_prompts(self):
        """Launch prompt injection configurator."""
        console.clear()
        console.print("[bold cyan]Launching Prompt Configurator...[/bold cyan]\n")
        try:
            from src.cli.prompt_config import main as prompt_main
            prompt_main()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_advanced(self):
        """Show advanced options submenu."""
        console.clear()
        console.print("[bold cyan]Launching Advanced Configuration...[/bold cyan]\n")
        try:
            from src.cli.advanced_config import main as advanced_main
            advanced_main()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_routing(self):
        """Launch model routing configurator (formerly hybrid mode)."""
        console.clear()
        console.print("[bold cyan]Launching Model Routing...[/bold cyan]\n")
        try:
            from src.cli.advanced_config import configure_hybrid_mode
            configure_hybrid_mode()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def launch_analytics(self):
        """Launch analytics configurator and viewer."""
        console.clear()
        console.print("[bold cyan]Launching Analytics...[/bold cyan]\n")
        try:
            from src.cli.analytics_tui import AnalyticsConfigurator
            configurator = AnalyticsConfigurator()
            configurator.run()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            input("\nPress Enter to continue...")

    def run(self):
        """Main loop."""
        while self.running:
            self.draw()
            selection = self.handle_input()

            if selection == "models":
                self.launch_models()
            elif selection == "routing":
                self.launch_routing()
            elif selection == "terminal":
                self.launch_terminal()
            elif selection == "dashboard":
                self.launch_dashboard()
            elif selection == "prompts":
                self.launch_prompts()
            elif selection == "analytics":
                self.launch_analytics()
            elif selection == "advanced":
                self.launch_advanced()
            elif selection == "exit":
                self.running = False

        console.clear()
        console.print("[dim]Settings closed.[/dim]\n")


def main():
    """Entry point."""
    try:
        app = UnifiedSettings()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Cancelled.[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
