#!/usr/bin/env python3
"""
Dashboard Configuration Tool

Interactive tool to configure API monitoring dashboard modules.
Shows previews and generates commands for Claude Code and .zshrc integration.
"""

import os
import sys
from typing import List, Dict, Tuple
from enum import Enum

# Try to import Rich for better UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.layout import Layout
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


class ModuleType(Enum):
    PERFORMANCE = "performance"
    ACTIVITY = "activity" 
    ROUTING = "routing"
    ANALYTICS = "analytics"
    WATERFALL = "waterfall"


class DisplayMode(Enum):
    DENSE = "dense"
    SPARSE = "sparse"


class DashboardConfigurator:
    """Interactive dashboard configuration tool."""
    
    def __init__(self):
        self.selected_modules = []
        self.module_previews = self._generate_previews()
        
    def _generate_previews(self) -> Dict[str, Dict[str, str]]:
        """Generate preview content for each module in both modes."""
        return {
            "performance": {
                "dense": """┌─ API Performance Monitor ─────────────────────────────────────┐
│ 🔵 Session abc123 | anthropic/claude-3.5-sonnet→openai/gpt-4o │
│ ⚡ 15.8s | 📊 CTX: ████████░░ 43.7k/200k (22%) | 82 tok/s    │
│ 🧠 THINK: ███░░░░░░░ 920 tokens | 💰 $0.0234 estimated       │
│ 📤 OUT: ██░░░░░░░░ 1.3k/16k | 🌊 STREAMING | 3msg + SYS     │
└───────────────────────────────────────────────────────────────┘""",
                "sparse": "🔵 abc123 | claude→gpt4o | ⚡15.8s | 📊22% | 🧠920 | 💰$0.02 | 🌊STR"
            },
            "activity": {
                "dense": """┌─ Multi-Session Activity Feed ─────────────────────────────────┐
│ 🔵 abc123 anthropic/claude-opus→openai/o1-preview | 🧠45k | ⚡3.2s | 💰$1.23 │
│ 🟢 def456 openai/gpt-4→anthropic/claude-sonnet | 🧠8k | ⚡1.8s | 💰$0.45   │
│ 🔴 ghi789 google/gemini-pro→ERROR | Rate limit | ⚡0.5s | 💰$0.00        │
│ 🔵 jkl012 anthropic/claude-haiku→openai/gpt-4o-mini | 🧠2k | ⚡0.9s | 💰$0.12 │
└─────────────────────────────────────────────────────────────────────────────┘""",
                "sparse": "🔵abc123→OK 🟢def456→OK 🔴ghi789→ERR 🔵jkl012→OK | 4req 3.2s avg"
            },
            "routing": {
                "dense": """┌─ Model Routing Flow ──────────────────────────────────────────┐
│                                                               │
│  [Claude 3.5 Sonnet] ──routing──> [GPT-4o Mini]             │
│       ↓ 43.7k ctx                    ↓ 1.3k out              │
│   🧠 Thinking: 920 tokens        ⚡ Speed: 82 tok/s          │
│   💰 Cost: $0.0234              📊 Efficiency: 94%           │
│                                                               │
└───────────────────────────────────────────────────────────────┘""",
                "sparse": "claude-sonnet→gpt4o-mini | 43.7k→1.3k | 🧠920 | ⚡82t/s | 💰$0.02"
            },
            "analytics": {
                "dense": """┌─ Cost & Performance Analytics (Last Hour) ────────────────────┐
│ Total Requests: 47 | Avg Response: 2.3s | Success: 94.7%   │
│ 💰 Total Cost: $12.45 | 🧠 Thinking Tokens: 234k          │
│ 🏆 Fastest: gpt-4o-mini (0.8s) | 🐌 Slowest: o1-preview (8.2s) │
│ 📈 Peak Usage: 14:30 (12 req/min) | 🔥 Hot Model: claude-sonnet │
└─────────────────────────────────────────────────────────────┘""",
                "sparse": "47req | 2.3s avg | 94.7% ✓ | 💰$12.45 | 🧠234k | 🏆gpt4o-mini | 🔥claude"
            },
            "waterfall": {
                "dense": """┌─ Live Request Waterfall ──────────────────────────────────────┐
│ 🔵 Request abc123 ────────────────────────────────────────────────  │
│ ├─ 📝 Parse: claude-3.5-sonnet:8k → gpt-4o-mini        (0.1s) │
│ ├─ 🔄 Route: openrouter.ai endpoint selection           (0.2s) │
│ ├─ 🧠 Think: Reasoning budget allocated (8k tokens)     (0.1s) │
│ ├─ 🚀 Send: 43.7k context → API                        (0.3s) │
│ ├─ ⏳ Wait: Model processing...                         (14.2s) │
│ ├─ 📥 Recv: 1.3k output + 920 thinking tokens          (0.9s) │
│ └─ ✅ Done: Total 15.8s | $0.0234 | 82 tok/s                  │
└─────────────────────────────────────────────────────────────────┘""",
                "sparse": "🔵abc123: Parse→Route→Think→Send→Wait→Recv→Done | 15.8s | $0.02"
            }
        }
    
    def show_welcome(self):
        """Show welcome message and instructions."""
        if RICH_AVAILABLE:
            welcome_text = Text()
            welcome_text.append("🚀 API Dashboard Configurator\n\n", style="bold cyan")
            welcome_text.append("Configure your API monitoring dashboard with modular components.\n")
            welcome_text.append("Select 1-4 modules and choose dense or sparse display modes.\n\n")
            welcome_text.append("Available modules:\n", style="bold")
            welcome_text.append("• Performance Monitor - Real-time request performance\n")
            welcome_text.append("• Activity Feed - Multi-session request history\n") 
            welcome_text.append("• Routing Visualizer - Model routing flow display\n")
            welcome_text.append("• Analytics Panel - Cost and performance analytics\n")
            welcome_text.append("• Request Waterfall - Detailed request lifecycle\n")
            
            console.print(Panel(welcome_text, title="Dashboard Configuration", border_style="cyan"))
        else:
            print("=" * 60)
            print("🚀 API Dashboard Configurator")
            print("=" * 60)
            print("Configure your API monitoring dashboard with modular components.")
            print("Select 1-4 modules and choose dense or sparse display modes.")
            print("\nAvailable modules:")
            print("• Performance Monitor - Real-time request performance")
            print("• Activity Feed - Multi-session request history") 
            print("• Routing Visualizer - Model routing flow display")
            print("• Analytics Panel - Cost and performance analytics")
            print("• Request Waterfall - Detailed request lifecycle")
            print()
    
    def show_module_previews(self):
        """Show previews of all available modules."""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Module Previews:[/bold cyan]\n")
            
            for module_name, modes in self.module_previews.items():
                console.print(f"[bold yellow]{module_name.upper()}[/bold yellow]")
                
                # Show dense and sparse side by side
                dense_panel = Panel(modes["dense"], title="Dense Mode", border_style="green")
                sparse_panel = Panel(modes["sparse"], title="Sparse Mode", border_style="blue")
                
                console.print(Columns([dense_panel, sparse_panel]))
                console.print()
        else:
            print("\nModule Previews:")
            print("=" * 40)
            
            for module_name, modes in self.module_previews.items():
                print(f"\n{module_name.upper()}:")
                print(f"Dense Mode:\n{modes['dense']}")
                print(f"Sparse Mode:\n{modes['sparse']}")
                print("-" * 40)
    
    def select_modules(self) -> List[Tuple[str, str]]:
        """Interactive module selection."""
        selected = []
        
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Select your dashboard modules (1-4):[/bold cyan]")
            
            while len(selected) < 4:
                # Show current selection
                if selected:
                    current = ", ".join([f"{m}:{d}" for m, d in selected])
                    console.print(f"[dim]Current selection: {current}[/dim]")
                
                # Module selection
                available_modules = [m.value for m in ModuleType if m.value not in [s[0] for s in selected]]
                if not available_modules:
                    break
                
                module_choice = Prompt.ask(
                    "Choose module",
                    choices=available_modules + ["done"],
                    default="done" if selected else available_modules[0]
                )
                
                if module_choice == "done":
                    break
                
                # Mode selection
                mode_choice = Prompt.ask(
                    f"Display mode for {module_choice}",
                    choices=["dense", "sparse"],
                    default="dense"
                )
                
                selected.append((module_choice, mode_choice))
                
                # Show preview of selection
                self._show_selection_preview(selected)
                
                if not Confirm.ask("Add another module?", default=False):
                    break
        else:
            print("\nSelect your dashboard modules (1-4):")
            
            while len(selected) < 4:
                print(f"\nAvailable modules: {', '.join([m.value for m in ModuleType])}")
                if selected:
                    current = ", ".join([f"{m}:{d}" for m, d in selected])
                    print(f"Current selection: {current}")
                
                module_choice = input("Choose module (or 'done'): ").strip().lower()
                if module_choice == "done" or not module_choice:
                    break
                
                if module_choice not in [m.value for m in ModuleType]:
                    print("Invalid module choice.")
                    continue
                
                mode_choice = input("Display mode (dense/sparse): ").strip().lower()
                if mode_choice not in ["dense", "sparse"]:
                    mode_choice = "dense"
                
                selected.append((module_choice, mode_choice))
                
                add_more = input("Add another module? (y/n): ").strip().lower()
                if add_more not in ["y", "yes"]:
                    break
        
        return selected
    
    def _show_selection_preview(self, selected: List[Tuple[str, str]]):
        """Show preview of current selection."""
        if not RICH_AVAILABLE:
            return
        
        console.print("\n[bold green]Preview of your dashboard:[/bold green]")
        
        panels = []
        for module_name, mode in selected:
            if module_name in self.module_previews:
                preview_content = self.module_previews[module_name][mode]
                title = f"{module_name.title()} ({mode})"
                panel = Panel(preview_content, title=title, border_style="green" if mode == "dense" else "blue")
                panels.append(panel)
        
        # Show panels in a grid layout
        if len(panels) == 1:
            console.print(panels[0])
        elif len(panels) == 2:
            console.print(Columns(panels))
        else:
            # For 3-4 panels, show in rows
            if len(panels) >= 3:
                console.print(Columns(panels[:2]))
                if len(panels) == 4:
                    console.print(Columns(panels[2:]))
                else:
                    console.print(panels[2])
    
    def generate_commands(self, selected_modules: List[Tuple[str, str]]) -> Dict[str, str]:
        """Generate configuration commands."""
        # Create dashboard config string
        config_string = ",".join([f"{module}:{mode}" for module, mode in selected_modules])
        
        # Generate environment variable
        env_var = f'export DASHBOARD_MODULES="{config_string}"'
        
        # Generate Claude Code command
        claude_command = f"""# Add to your Claude Code project settings or .env file:
DASHBOARD_MODULES={config_string}

# Or run directly:
DASHBOARD_MODULES="{config_string}" python -m src.dashboard.live_dashboard"""
        
        # Generate .zshrc addition
        zshrc_addition = f"""
# API Dashboard Configuration
{env_var}

# Dashboard aliases
alias dashboard-live="DASHBOARD_MODULES='{config_string}' python -m src.dashboard.live_dashboard"
alias dashboard-config="python configure_dashboard.py"
alias dashboard-preview="DASHBOARD_MODULES='{config_string}' python -c 'from src.dashboard import dashboard_manager; dashboard_manager.print_dashboard()'"
"""
        
        # Generate startup script
        startup_script = f"""#!/bin/bash
# API Dashboard Startup Script
export DASHBOARD_MODULES="{config_string}"

echo "🚀 Starting API Dashboard with modules: {config_string}"
python -m src.dashboard.live_dashboard
"""
        
        return {
            "env_var": env_var,
            "claude_command": claude_command,
            "zshrc_addition": zshrc_addition,
            "startup_script": startup_script,
            "config_string": config_string
        }
    
    def show_commands(self, commands: Dict[str, str]):
        """Display generated commands."""
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Generated Configuration Commands:[/bold cyan]\n")
            
            # Environment Variable
            console.print(Panel(
                commands["env_var"],
                title="Environment Variable",
                border_style="green"
            ))
            
            # Claude Code Integration
            console.print(Panel(
                commands["claude_command"],
                title="Claude Code Integration",
                border_style="blue"
            ))
            
            # .zshrc Addition
            console.print(Panel(
                commands["zshrc_addition"],
                title=".zshrc Addition",
                border_style="yellow"
            ))
            
            # Startup Script
            console.print(Panel(
                commands["startup_script"],
                title="Startup Script (save as start_dashboard.sh)",
                border_style="magenta"
            ))
            
        else:
            print("\nGenerated Configuration Commands:")
            print("=" * 50)
            
            print("\nEnvironment Variable:")
            print(commands["env_var"])
            
            print("\nClaude Code Integration:")
            print(commands["claude_command"])
            
            print("\n.zshrc Addition:")
            print(commands["zshrc_addition"])
            
            print("\nStartup Script (save as start_dashboard.sh):")
            print(commands["startup_script"])
    
    def save_startup_script(self, commands: Dict[str, str]):
        """Save the startup script to file."""
        script_content = commands["startup_script"]
        
        with open("start_dashboard.sh", "w") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod("start_dashboard.sh", 0o755)
        
        if RICH_AVAILABLE:
            console.print(f"\n[green]✅ Startup script saved as 'start_dashboard.sh'[/green]")
            console.print("[dim]Run with: ./start_dashboard.sh[/dim]")
        else:
            print("\n✅ Startup script saved as 'start_dashboard.sh'")
            print("Run with: ./start_dashboard.sh")
    
    def run(self):
        """Run the interactive configuration process."""
        self.show_welcome()
        
        # Show previews
        show_previews = True
        if RICH_AVAILABLE:
            show_previews = Confirm.ask("Show module previews?", default=True)
        else:
            show_previews = input("Show module previews? (y/n): ").strip().lower() in ["y", "yes", ""]
        
        if show_previews:
            self.show_module_previews()
        
        # Select modules
        selected_modules = self.select_modules()
        
        if not selected_modules:
            if RICH_AVAILABLE:
                console.print("[red]No modules selected. Exiting.[/red]")
            else:
                print("No modules selected. Exiting.")
            return
        
        # Generate commands
        commands = self.generate_commands(selected_modules)
        
        # Show final preview
        self._show_selection_preview(selected_modules)
        
        # Show commands
        self.show_commands(commands)
        
        # Offer to save startup script
        save_script = True
        if RICH_AVAILABLE:
            save_script = Confirm.ask("Save startup script?", default=True)
        else:
            save_script = input("Save startup script? (y/n): ").strip().lower() in ["y", "yes", ""]
        
        if save_script:
            self.save_startup_script(commands)
        
        if RICH_AVAILABLE:
            console.print("\n[bold green]🎉 Dashboard configuration complete![/bold green]")
            console.print("[dim]Copy the commands above to integrate with your workflow.[/dim]")
        else:
            print("\n🎉 Dashboard configuration complete!")
            print("Copy the commands above to integrate with your workflow.")


def main():
    """Main entry point."""
    configurator = DashboardConfigurator()
    configurator.run()


if __name__ == "__main__":
    main()