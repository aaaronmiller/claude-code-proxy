#!/usr/bin/env python3
"""
Rich-based TUI Dashboard for claude-code-proxy
Displays live tmux pane outputs in a beautifully formatted 3-column layout.
"""
import sys
import time
import re
import subprocess
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Group
from rich.text import Text
from rich.style import Style
from rich import box
from rich.spinner import Spinner

# ANSI color stripping regex
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)

def capture_tmux_pane(session_name: str, pane_idx: int, lines: int = 50) -> str:
    target = f"{session_name}:0.{pane_idx}"
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", target, "-p", "-S", f"-{lines}"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return strip_ansi(result.stdout)
        else:
            return "Pane not active or tmux session missing."
    except Exception as e:
        return f"Error capturing pane: {e}"

def generate_pane_content(text: str, color: str) -> Text:
    """Format the text content with semantic styling."""
    t = Text()
    for line in text.splitlines():
        if not line.strip():
            continue
        # Apply basic semantic color highlights based on keywords
        if "error" in line.lower() or "failed" in line.lower() or "exception" in line.lower():
            t.append(line + "\n", style="bold red")
        elif "warn" in line.lower() or "⚠" in line:
            t.append(line + "\n", style="bold yellow")
        elif "success" in line.lower() or "✓" in line:
            t.append(line + "\n", style="bold green")
        else:
            t.append(line + "\n", style=color)
    return t

def main():
    if len(sys.argv) < 3:
        print("Usage: watch_dashboard.py <session_name> <mode> [lines]")
        sys.exit(1)

    session_name = sys.argv[1]
    mode = sys.argv[2]
    try:
        lines = int(sys.argv[3])
    except IndexError:
        lines = 40

    # Create root layout
    layout = Layout()
    
    # Check mode to determine active panes
    # full: 3 panes (0: CLIProxy, 1: ClaudeProxy, 2: Headroom)
    # proxy: 2 panes (0: CLIProxy(dead/placeholder), 1: ClaudeProxy(OpenRouter), 2: Headroom)
    # comp: 2 panes (0: CLIProxy, 1: placeholder, 2: Headroom)

    # Divide root into header and body
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )

    # Determine columns based on mode
    has_cli = (mode == "full" or mode == "comp")
    has_claude = (mode == "full" or mode == "proxy")

    columns = []
    
    if has_cli:
        columns.append(Layout(name="cli_proxy"))
        
    if has_claude:
        columns.append(Layout(name="claude_proxy"))
        
    columns.append(Layout(name="headroom"))
    
    # Split body into active columns
    layout["body"].split_row(*columns)

    start_time = time.time()

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                uptime = int(time.time() - start_time)
                mins, secs = divmod(uptime, 60)
                
                header_text = Text(f" Compression Stack Monitor  |  ⏱ Uptime: {mins:02d}:{secs:02d}  |  ⚡ Mode: {mode.upper()}", style="bold white on blue")
                layout["header"].update(Panel(Spinner("point", text=header_text), style="blue", box=box.ROUNDED))

                # Headroom is always on pane 2
                hr_out = capture_tmux_pane(session_name, 2, lines)
                layout["headroom"].update(
                    Panel(
                        generate_pane_content(hr_out, "yellow"),
                        title="[bold yellow]Headroom (Optimization Layer)[/]",
                        subtitle=f"[dim]lines: {lines}[/]",
                        border_style="yellow",
                        box=box.ROUNDED
                    )
                )

                if has_claude:
                    # Claude proxy is on pane 1
                    cp_out = capture_tmux_pane(session_name, 1, lines)
                    layout["claude_proxy"].update(
                        Panel(
                            generate_pane_content(cp_out, "cyan"),
                            title="[bold cyan]Claude Proxy (Controller)[/]",
                            subtitle=f"[dim]lines: {lines}[/]",
                            border_style="cyan",
                            box=box.ROUNDED
                        )
                    )

                if has_cli:
                    # CLI proxy is on pane 0
                    api_out = capture_tmux_pane(session_name, 0, lines)
                    layout["cli_proxy"].update(
                        Panel(
                            generate_pane_content(api_out, "green"),
                            title="[bold green]CLIProxyAPI (Destination)[/]",
                            subtitle=f"[dim]lines: {lines}[/]",
                            border_style="green",
                            box=box.ROUNDED
                        )
                    )

                time.sleep(0.5)
        except KeyboardInterrupt:
            # Handle exit gracefully
            pass

if __name__ == "__main__":
    main()
