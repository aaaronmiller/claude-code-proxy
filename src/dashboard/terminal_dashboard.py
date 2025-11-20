"""
Terminal Dashboard with Edge Modules and Central Waterfall

This replaces the standard proxy terminal output with a Rich-based TUI that shows:
- Modules on edges (top, bottom, left, right)
- Central waterfall area for live request flow
- Moveable module positioning
- Interactive controls
"""

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
from collections import deque
import threading


class EdgeModule:
    """Base class for edge modules"""

    def __init__(self, name: str, position: str = "top"):
        self.name = name
        self.position = position  # top, bottom, left, right, corner_tl, corner_tr, corner_bl, corner_br
        self.data = {}
        self.visible = True
        self.size = "normal"  # compact, normal, expanded

    def update(self, data: Dict[str, Any]):
        """Update module data"""
        self.data = data

    def render(self) -> Panel:
        """Render module as Rich Panel"""
        raise NotImplementedError


class PerformanceEdgeModule(EdgeModule):
    """Performance metrics module"""

    def __init__(self, position: str = "top"):
        super().__init__("Performance", position)

    def render(self) -> Panel:
        if not self.visible:
            return Panel("", title="", border_style="dim")

        table = Table(show_header=False, box=None, padding=0)
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="white bold")

        req_count = self.data.get('total_requests', 0)
        avg_lat = self.data.get('avg_latency_ms', 0)
        tokens_sec = self.data.get('avg_tokens_per_sec', 0)
        total_cost = self.data.get('total_cost', 0)

        if self.size == "compact":
            table.add_row("Req", f"{req_count}")
            table.add_row("Lat", f"{avg_lat}ms")
            table.add_row("$/h", f"${total_cost:.2f}")
        elif self.size == "expanded":
            table.add_row("Requests", f"{req_count:,}")
            table.add_row("Latency", f"{avg_lat:,}ms avg")
            table.add_row("Speed", f"{tokens_sec} tok/s")
            table.add_row("Cost", f"${total_cost:.2f}")
            table.add_row("Success", f"{self.data.get('success_rate', 100):.1f}%")
        else:  # normal
            table.add_row("Req", f"{req_count:,}")
            table.add_row("Lat", f"{avg_lat}ms")
            table.add_row("Speed", f"{tokens_sec}t/s")
            table.add_row("Cost", f"${total_cost:.2f}")

        return Panel(
            table,
            title=f"[bold cyan]⚡ {self.name}[/]",
            border_style="cyan"
        )


class RoutingEdgeModule(EdgeModule):
    """Routing configuration module"""

    def __init__(self, position: str = "right"):
        super().__init__("Routing", position)

    def render(self) -> Panel:
        if not self.visible:
            return Panel("", title="", border_style="dim")

        provider = self.data.get('provider', 'Unknown')
        big = self.data.get('big_model', '')[:20]
        middle = self.data.get('middle_model', '')[:20]
        small = self.data.get('small_model', '')[:20]
        mode = "Passthrough" if self.data.get('passthrough_mode') else "Proxy"

        content = Text()
        content.append(f"Mode: ", style="dim")
        content.append(f"{mode}\n", style="yellow bold" if mode == "Passthrough" else "green bold")
        content.append(f"Provider: ", style="dim")
        content.append(f"{provider}\n\n", style="cyan")

        if self.size != "compact":
            content.append("Routes:\n", style="bold")
            content.append(f"  O → ", style="dim")
            content.append(f"{big}\n", style="white")
            content.append(f"  M → ", style="dim")
            content.append(f"{middle}\n", style="white")
            content.append(f"  S → ", style="dim")
            content.append(f"{small}", style="white")

        return Panel(
            content,
            title=f"[bold yellow]🎯 {self.name}[/]",
            border_style="yellow"
        )


class ActivityEdgeModule(EdgeModule):
    """Activity feed module"""

    def __init__(self, position: str = "left"):
        super().__init__("Activity", position)
        self.recent_requests = deque(maxlen=10)

    def update(self, data: Dict[str, Any]):
        super().update(data)
        # Add to recent requests
        if 'request' in data:
            self.recent_requests.append(data['request'])

    def render(self) -> Panel:
        if not self.visible:
            return Panel("", title="", border_style="dim")

        content = Text()

        for req in list(self.recent_requests)[-5:]:
            status = req.get('status', 'pending')
            model = req.get('model', '')[:15]
            duration = req.get('duration_ms', 0)

            if status == 'completed':
                icon = "🟢"
                style = "green"
            elif status == 'error':
                icon = "🔴"
                style = "red"
            else:
                icon = "🔵"
                style = "blue"

            content.append(f"{icon} ", style=style)
            content.append(f"{model}", style="white")
            if duration:
                content.append(f" {duration}ms", style="dim")
            content.append("\n")

        return Panel(
            content if content.plain else "No recent activity",
            title=f"[bold green]📊 {self.name}[/]",
            border_style="green"
        )


class ModelUsageEdgeModule(EdgeModule):
    """Model usage stats module"""

    def __init__(self, position: str = "bottom"):
        super().__init__("Model Usage", position)

    def render(self) -> Panel:
        if not self.visible:
            return Panel("", title="", border_style="dim")

        top_models = self.data.get('top_models', [])

        content = Text()
        for i, model in enumerate(top_models[:3], 1):
            name = model.get('name', '')[:20]
            count = model.get('requests', 0)
            cost = model.get('cost', 0)

            content.append(f"#{i} ", style="dim")
            content.append(f"{name}", style="white")
            content.append(f" ({count})", style="cyan")
            if cost == 0:
                content.append(" FREE", style="green bold")
            content.append("\n")

        return Panel(
            content if content.plain else "No usage data",
            title=f"[bold magenta]🤖 {self.name}[/]",
            border_style="magenta"
        )


class WaterfallDisplay:
    """Central waterfall display for live request flow"""

    def __init__(self):
        self.active_requests = {}  # request_id -> request_data
        self.completed_requests = deque(maxlen=20)
        self.lock = threading.Lock()

    def add_request(self, request_id: str, request_data: Dict[str, Any]):
        """Add new request to waterfall"""
        with self.lock:
            self.active_requests[request_id] = {
                **request_data,
                'phase': 'parse',
                'start_time': time.time(),
                'phases': []
            }

    def update_phase(self, request_id: str, phase: str):
        """Update request phase"""
        with self.lock:
            if request_id in self.active_requests:
                req = self.active_requests[request_id]
                req['phase'] = phase
                req['phases'].append({
                    'phase': phase,
                    'timestamp': time.time()
                })

    def complete_request(self, request_id: str, status: str, data: Dict[str, Any] = None):
        """Complete a request"""
        with self.lock:
            if request_id in self.active_requests:
                req = self.active_requests.pop(request_id)
                req['status'] = status
                req['end_time'] = time.time()
                req['duration_ms'] = int((req['end_time'] - req['start_time']) * 1000)
                if data:
                    req.update(data)
                self.completed_requests.append(req)

    def render(self) -> Panel:
        """Render waterfall display"""
        content = Text()

        # Active requests
        with self.lock:
            if self.active_requests:
                content.append("ACTIVE REQUESTS\n", style="bold cyan")
                content.append("─" * 60 + "\n", style="dim")

                for req_id, req in list(self.active_requests.items())[:5]:
                    short_id = req_id[:8]
                    model = req.get('model', '')[:20]
                    phase = req.get('phase', 'unknown')
                    elapsed = int((time.time() - req['start_time']) * 1000)

                    # Status icon
                    content.append("🔵 ", style="blue")
                    content.append(f"{short_id}", style="cyan")
                    content.append(f" {model}", style="white")
                    content.append(f" {phase}", style="yellow")
                    content.append(f" {elapsed}ms", style="dim")
                    content.append("\n")

                    # Phase progress bar
                    phases = ['parse', 'route', 'think', 'send', 'wait', 'recv', 'done']
                    current_idx = phases.index(phase) if phase in phases else 0
                    progress_bar = ""
                    for i, p in enumerate(phases):
                        if i < current_idx:
                            progress_bar += "━"
                        elif i == current_idx:
                            progress_bar += "╸"
                        else:
                            progress_bar += "┄"
                    content.append(f"  {progress_bar}\n", style="blue")

                content.append("\n")

            # Completed requests
            if self.completed_requests:
                content.append("COMPLETED REQUESTS\n", style="bold green")
                content.append("─" * 60 + "\n", style="dim")

                for req in list(self.completed_requests)[-10:]:
                    short_id = req.get('request_id', '')[:8] if isinstance(req.get('request_id'), str) else "unknown"
                    model = req.get('model', '')[:20]
                    status = req.get('status', 'unknown')
                    duration = req.get('duration_ms', 0)

                    if status == 'completed':
                        icon = "🟢"
                        style = "green"
                    else:
                        icon = "🔴"
                        style = "red"

                    content.append(f"{icon} ", style=style)
                    content.append(f"{short_id}", style="cyan")
                    content.append(f" {model}", style="white")
                    content.append(f" {duration}ms", style="dim")

                    if status == 'error':
                        error = req.get('error', '')[:30]
                        content.append(f" ✗ {error}", style="red")
                    elif 'tokens' in req:
                        tokens = req.get('tokens', 0)
                        content.append(f" {tokens} tokens", style="cyan")

                    content.append("\n")

        if not content.plain:
            content.append("Waiting for requests...\n", style="dim italic")

        return Panel(
            content,
            title="[bold white]🌊 REQUEST WATERFALL[/]",
            border_style="white"
        )


class TerminalDashboard:
    """Main terminal dashboard with edge modules and waterfall"""

    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.waterfall = WaterfallDisplay()

        # Initialize modules
        self.modules = {
            'performance': PerformanceEdgeModule('top'),
            'routing': RoutingEdgeModule('right'),
            'activity': ActivityEdgeModule('left'),
            'models': ModelUsageEdgeModule('bottom')
        }

        self.live = None
        self.running = False

    def setup_layout(self):
        """Setup the dashboard layout"""
        # Create layout structure
        self.layout.split_column(
            Layout(name="top", size=7),
            Layout(name="middle"),
            Layout(name="bottom", size=6)
        )

        # Split middle into left, center, right
        self.layout["middle"].split_row(
            Layout(name="left", size=25),
            Layout(name="center"),
            Layout(name="right", size=25)
        )

    def update_module(self, module_name: str, data: Dict[str, Any]):
        """Update a module with new data"""
        if module_name in self.modules:
            self.modules[module_name].update(data)

    def render(self):
        """Render the entire dashboard"""
        self.layout["top"].update(self.modules['performance'].render())
        self.layout["bottom"].update(self.modules['models'].render())
        self.layout["left"].update(self.modules['activity'].render())
        self.layout["right"].update(self.modules['routing'].render())
        self.layout["center"].update(self.waterfall.render())

        return self.layout

    def start(self):
        """Start the live dashboard"""
        self.setup_layout()
        self.running = True
        self.live = Live(self.render(), console=self.console, refresh_per_second=2)
        self.live.start()

    def stop(self):
        """Stop the dashboard"""
        self.running = False
        if self.live:
            self.live.stop()

    def update(self):
        """Update the dashboard display"""
        if self.live:
            self.live.update(self.render())


# Global dashboard instance
terminal_dashboard = TerminalDashboard()
