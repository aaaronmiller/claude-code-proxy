"""
Real-time Metrics Module for Terminal Dashboard

Displays live metrics from the session metrics tracker:
- Active sessions
- Token usage per session
- Tool call success rates
- Cache statistics
"""

from datetime import datetime
from typing import Dict, Any, List

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class MetricsModule:
    """Real-time metrics display module."""
    
    def __init__(self, position: str = "left"):
        self.position = position
        self.data: Dict[str, Any] = {}
        self.visible = True
    
    def update(self, data: Dict[str, Any]):
        """Update metrics data."""
        self.data = data
    
    def render(self) -> Panel:
        """Render metrics as Rich Panel."""
        if not RICH_AVAILABLE or not self.visible:
            return Panel("", title="")
        
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white bold")
        
        # Aggregate metrics
        metrics = self.data.get('aggregate', {})
        
        table.add_row("Sessions", str(metrics.get('total_sessions', 0)))
        table.add_row("Requests", str(metrics.get('total_requests', 0)))
        table.add_row("Tokens", self._format_tokens(metrics.get('total_tokens', 0)))
        table.add_row("Cost", f"${metrics.get('total_cost', 0):.4f}")
        table.add_row("Tool Success", f"{metrics.get('tool_success_rate', 0):.1f}%")
        table.add_row("Cache Hit", f"{metrics.get('cache_hit_rate', 0):.1f}%")
        
        return Panel(
            table,
            title="[bold green]📊 Live Metrics[/]",
            border_style="green",
            subtitle=f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def _format_tokens(self, tokens: int) -> str:
        """Format token count."""
        if tokens >= 1_000_000:
            return f"{tokens/1_000_000:.1f}M"
        elif tokens >= 1_000:
            return f"{tokens/1_000:.1f}k"
        return str(tokens)


class SessionListModule:
    """Active sessions list module."""
    
    def __init__(self, position: str = "right"):
        self.position = position
        self.sessions: List[Dict[str, Any]] = []
        self.visible = True
    
    def update(self, sessions: List[Dict[str, Any]]):
        """Update sessions list."""
        self.sessions = sessions[:10]  # Top 10
    
    def render(self) -> Panel:
        """Render sessions as Rich Panel."""
        if not RICH_AVAILABLE or not self.visible:
            return Panel("", title="")
        
        if not self.sessions:
            return Panel(
                "[dim]No active sessions[/]",
                title="[bold blue]🖥️ Sessions[/]",
                border_style="blue"
            )
        
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("ID", style="dim", width=8)
        table.add_column("Req", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right")
        
        for session in self.sessions:
            session_id = session.get('session_id', 'unknown')[:8]
            table.add_row(
                session_id,
                str(session.get('requests', 0)),
                self._format_tokens(session.get('tokens', 0)),
                f"${session.get('cost', 0):.3f}"
            )
        
        return Panel(
            table,
            title="[bold blue]🖥️ Active Sessions[/]",
            border_style="blue",
            subtitle=f"{len(self.sessions)} sessions"
        )
    
    def _format_tokens(self, tokens: int) -> str:
        """Format token count."""
        if tokens >= 1_000_000:
            return f"{tokens/1_000_000:.1f}M"
        elif tokens >= 1_000:
            return f"{tokens/1_000:.1f}k"
        return str(tokens)


class CLIToolsModule:
    """CLI tools status module."""
    
    def __init__(self, position: str = "bottom"):
        self.position = position
        self.tools_data: Dict[str, Any] = {}
        self.visible = True
    
    def update(self, tools_data: Dict[str, Any]):
        """Update CLI tools data."""
        self.tools_data = tools_data
    
    def render(self) -> Panel:
        """Render CLI tools status."""
        if not RICH_AVAILABLE or not self.visible:
            return Panel("", title="")
        
        summary = self.tools_data.get('summary', {})
        total_tools = summary.get('total_tools', 0)
        total_sessions = summary.get('total_sessions', 0)
        
        text = Text()
        text.append(f"📦 CLI Tools: ", style="bold")
        text.append(f"{total_tools} active\n", style="green")
        text.append(f"📝 Sessions: ", style="bold")
        text.append(f"{total_sessions} total\n", style="cyan")
        text.append(f"📄 Config Files: ", style="bold")
        text.append(f"{summary.get('total_config_files', 0)} found", style="yellow")
        
        return Panel(
            text,
            title="[bold magenta]🛠️ CLI Tools[/]",
            border_style="magenta"
        )
