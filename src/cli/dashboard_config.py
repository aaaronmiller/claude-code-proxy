#!/usr/bin/env python3
"""
Dashboard Configuration Tool (TUI Redesign)

A slick, grid-based interface to configure the API monitoring dashboard.
Supports 10 slots: 4 Left, 4 Right, Top, Bottom.
"""

import sys
import os
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple

# Try imports
try:
    import readchar
    READCHAR_AVAILABLE = True
except ImportError:
    READCHAR_AVAILABLE = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.text import Text
    from rich.box import ROUNDED, HEAVY
    from rich.align import Align
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# --- Constants ---

class SlotInfo:
    def __init__(self, id: str, name: str, row: int, col: int, width: int = 30):
        self.id = id
        self.name = name
        self.row = row  # Simple grid coord for nav (0-5)
        self.col = col  # 0=Left, 1=Center, 2=Right
        self.width = width
        self.module: Optional[str] = None
        self.mode: str = "sparse"

SLOTS = [
    # Top Center
    SlotInfo("T1", "Top Bar", 0, 1, width=60),
    
    # Left Column
    SlotInfo("L1", "Left 1", 1, 0),
    SlotInfo("L2", "Left 2", 2, 0),
    SlotInfo("L3", "Left 3", 3, 0),
    SlotInfo("L4", "Left 4", 4, 0),

    # Right Column
    SlotInfo("R1", "Right 1", 1, 2),
    SlotInfo("R2", "Right 2", 2, 2),
    SlotInfo("R3", "Right 3", 3, 2),
    SlotInfo("R4", "Right 4", 4, 2),

    # Bottom Center
    SlotInfo("B1", "Bottom Bar", 5, 1, width=60),
]

MODULES = {
    "performance": {
        "icon": "⚡",
        "name": "Performance",
        "desc": "Real-time latency & tokens",
        "preview_sparse": "⚡ 15.8s | 82 t/s\n📊 43k ctx | $0.02",
        "preview_dense": "⚡ 15.8s | 82 tok/s\n📊 CTX: 43.7k/200k\n🧠 Think: 920 tok\n💰 Est: $0.0234"
    },
    "activity": {
        "icon": "📝",
        "name": "Activity Feed",
        "desc": "Recent request history",
        "preview_sparse": "🔵 abc123 → OK\n🟢 def456 → OK",
        "preview_dense": "🔵 abc123 claude→gpt4\n🟢 def456 gpt4→sonnet\n🔴 ghi789 gemini→ERR\n⚡ Avg: 3.2s"
    },
    "routing": {
        "icon": "🔄",
        "name": "Routing",
        "desc": "Model flow visualizer",
        "preview_sparse": "claude → gpt4o\n43k → 1.3k",
        "preview_dense": "[Claude]──>[GPT-4o]\n ↓ 43k      ↓ 1.3k\n 🧠 920     ⚡ 82t/s"
    },
    "analytics": {
        "icon": "📈",
        "name": "Analytics",
        "desc": "Cost & usage stats",
        "preview_sparse": "47 req | $12.45\n94% Success",
        "preview_dense": "Reqs: 47 | $12.45\nAvg: 2.3s | 94% OK\n🏆 Fast: gpt-4o-mini\n🔥 Hot: sonnet"
    },
    "waterfall": {
        "icon": "🌊",
        "name": "Waterfall",
        "desc": "Request stages",
        "preview_sparse": "Parse→Route→Send\nWait→Recv→Done",
        "preview_dense": "Parse.. 0.1s\nRoute.. 0.2s\nSend... 0.3s\nWait... 14s"
    },
    "empty": {
        "icon": "⚫",
        "name": "Empty Slot",
        "desc": "Clear this slot",
        "preview_sparse": "",
        "preview_dense": ""
    }
}

# --- TUI Class ---

class DashboardTUI:
    def __init__(self):
        self.cursor_idx = 0  # Index in SLOTS list
        self.running = True
        # Pre-fill slots for demo mode (Showcase all modules)
        self.get_slot("L1").module = "performance"
        self.get_slot("L1").mode = "dense"
        self.get_slot("L2").module = "activity"
        self.get_slot("L3").module = "routing"
        self.get_slot("L4").module = "analytics"
        
        self.get_slot("R1").module = "waterfall"
        self.get_slot("R1").mode = "dense"
        self.get_slot("R2").module = "performance"
        self.get_slot("R3").module = "activity"
        self.get_slot("R4").module = "routing"

        self.get_slot("T1").module = "analytics"
        self.get_slot("T1").mode = "sparse"
        
        self.get_slot("B1").module = "performance"
        self.get_slot("B1").mode = "sparse"

    def get_slot(self, id: str) -> SlotInfo:
        return next(s for s in SLOTS if s.id == id)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def draw_screen(self):
        self.clear_screen()
        
        # 1. Header
        console.print(Panel(
            Align.center("[bold cyan]🚀 API Dashboard Configurator[/bold cyan]\n[dim]Arrow keys to move • Enter to select • s to toggle size • q to save[/dim]"),
            border_style="cyan",
            box=ROUNDED
        ))

        # 2. Main Grid
        # We construct a table with 3 columns: Left Stack, Center (Terminal), Right Stack
        
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column("Left", ratio=1)
        grid.add_column("Center", ratio=3)
        grid.add_column("Right", ratio=1)

        # Helper to render a slot
        def render_slot(slot: SlotInfo, is_focused: bool):
            if slot.module:
                mod = MODULES[slot.module]
                content = mod[f"preview_{slot.mode}"]
                title = f"{mod['icon']} {mod['name']}"
                style = "green" if is_focused else "blue"
            else:
                content = "[dim]Empty Slot[/dim]"
                title = slot.name
                style = "yellow" if is_focused else "dim"
            
            border = HEAVY if is_focused else ROUNDED
            return Panel(
                Align.center(content),
                title=title,
                border_style=style,
                box=border,
                height=4 if slot.mode == "sparse" else 8
            )

        # Top Bar (T1) - Spans Center
        # We can't easily span in a simple grid, so we render T1 above the main columns
        t1_slot = self.get_slot("T1")
        is_focused = (SLOTS[self.cursor_idx].id == "T1")
        console.print(Align.center(render_slot(t1_slot, is_focused), width=60))
        console.print()

        # Middle Section (L1-4, Terminal, R1-4)
        # We need to assemble the stacks
        left_stack = Table.grid(expand=True, padding=(0, 0))
        for i in range(1, 5):
            slot = self.get_slot(f"L{i}")
            is_focused = (SLOTS[self.cursor_idx].id == slot.id)
            left_stack.add_row(render_slot(slot, is_focused))
            left_stack.add_row("") # Spacer

        right_stack = Table.grid(expand=True, padding=(0, 0))
        for i in range(1, 5):
            slot = self.get_slot(f"R{i}")
            is_focused = (SLOTS[self.cursor_idx].id == slot.id)
            right_stack.add_row(render_slot(slot, is_focused))
            right_stack.add_row("") # Spacer

        # Center "Terminal" Placeholder
        terminal_view = Panel(
            "\n[dim]... terminal output ...[/dim]\n" * 8,
            title="Terminal Area (Live Output)",
            border_style="dim",
            box=ROUNDED
        )

        grid.add_row(left_stack, terminal_view, right_stack)
        console.print(grid)
        console.print()

        # Bottom Bar (B1)
        b1_slot = self.get_slot("B1")
        is_focused = (SLOTS[self.cursor_idx].id == "B1")
        console.print(Align.center(render_slot(b1_slot, is_focused), width=60))

    def handle_input(self):
        key = readchar.readkey()
        
        # Navigation logic (flat list mapped to grid)
        # 0=T1
        # 1-4=L1-L4
        # 5-8=R1-R4  (Indices in SLOTS list are different: T1=0, L1=1..4, R1=5..8, B1=9 is wrong order in list vs visual)
        # Wait, my SLOTS list order was: T1(0), L1-4(1-4), R1-4(5-8), B1(9)
        
        # Determine logical row/col
        current = SLOTS[self.cursor_idx]
        
        if key == readchar.key.UP:
             # Logic is tricky. Let's use simple neighbor finding.
             # If T1, wrap to B1? No.
             if current.id.startswith('L'):
                 if current.id == 'L1': self.cursor_idx = 0 # To T1
                 else: self.cursor_idx -= 1
             elif current.id.startswith('R'):
                 if current.id == 'R1': self.cursor_idx = 0 # To T1
                 else: self.cursor_idx -= 1
             elif current.id == 'B1':
                 self.cursor_idx = 0 # To T1 (wrap) or neighbor?
                 # B1 -> L4 or R4 depending on last pos? let's go to L4 default
                 self.cursor_idx = 4 
             elif current.id == 'T1':
                 self.cursor_idx = 9 # Wrap to B1

        elif key == readchar.key.DOWN:
            if current.id == 'T1':
                self.cursor_idx = 1 # To L1
            elif current.id.startswith('L'):
                if current.id == 'L4': self.cursor_idx = 9 # To B1
                else: self.cursor_idx += 1
            elif current.id.startswith('R'):
                if current.id == 'R4': self.cursor_idx = 9 # To B1
                else: self.cursor_idx += 1
            elif current.id == 'B1':
                self.cursor_idx = 0 # To T1

        elif key == readchar.key.LEFT:
            if current.id.startswith('R'):
                # Go to corresponding L
                # R1(5) -> L1(1)
                self.cursor_idx -= 4
            elif current.id.startswith('L'):
                # Go to R (wrap) or stay?
                self.cursor_idx += 4 # To R
            elif current.id == 'T1' or current.id == 'B1':
                pass # Already centered

        elif key == readchar.key.RIGHT:
            if current.id.startswith('L'):
                # Go to R
                self.cursor_idx += 4
            elif current.id.startswith('R'):
                # Go to L (wrap)
                self.cursor_idx -= 4
            elif current.id == 'T1' or current.id == 'B1':
                pass

        elif key == readchar.key.ENTER or key == ' ':
             self.pick_module(current)
        
        elif key == 's':
            # Toggle sparse/dense
            current.mode = "dense" if current.mode == "sparse" else "sparse"

        elif key == 'x' or key == readchar.key.BACKSPACE:
            current.module = None

        elif key == 'q':
            self.running = False

    def pick_module(self, slot: SlotInfo):
        self.clear_screen()
        console.print(Panel(
            f"[bold]Select Module for {slot.name}[/bold]",
            border_style="cyan"
        ))
        
        # Simple list loop
        mods = list(MODULES.keys())
        for i, m_key in enumerate(mods):
            m = MODULES[m_key]
            console.print(f"[{i+1}] {m['icon']} {m['name']} - [dim]{m['desc']}[/dim]")
        
        console.print("\n[dim]Press number to select or q to cancel[/dim]")
        
        k = readchar.readkey()
        if k.isdigit() and 1 <= int(k) <= len(mods):
            choice = mods[int(k)-1]
            if choice == "empty":
                slot.module = None
            else:
                slot.module = choice
                
    def generate_config(self):
        # Format: "L1:perf:sparse,R1:routing:dense,..."
        config_parts = []
        for slot in SLOTS:
            if slot.module:
                config_parts.append(f"{slot.id}:{slot.module}:{slot.mode}")
        
        config_str = ",".join(config_parts)
        
        # Save command
        console.print("\n[bold green]✅ Configuration Generated![/bold green]")
        console.print(Panel(f"export DASHBOARD_CONFIG='{config_str}'", title="Environment Variable"))
        
        # Save to file option? For now just print.
        # Use python-dotenv to save if needed, but standard print is safer.
        console.print("[dim]Add this variable to your .env file or shell profile.[/dim]")

    def run(self):
        if not RICH_AVAILABLE or not READCHAR_AVAILABLE:
            print("Error: 'rich' and 'readchar' libraries are required.")
            print("Run: uv sync")
            return

        while self.running:
            self.draw_screen()
            self.handle_input()
        
        self.generate_config()

def main():
    tui = DashboardTUI()
    tui.run()

if __name__ == "__main__":
    main()