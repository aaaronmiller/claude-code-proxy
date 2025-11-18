"""
Dashboard Manager - Orchestrates multiple dashboard modules.
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .modules.performance_monitor import PerformanceMonitor
from .modules.activity_feed import ActivityFeed
from .modules.routing_visualizer import RoutingVisualizer
from .modules.analytics_panel import AnalyticsPanel
from .modules.request_waterfall import RequestWaterfall


class DisplayMode(Enum):
    DENSE = "dense"
    SPARSE = "sparse"


class ModuleType(Enum):
    PERFORMANCE = "performance"
    ACTIVITY = "activity"
    ROUTING = "routing"
    ANALYTICS = "analytics"
    WATERFALL = "waterfall"


@dataclass
class ModuleConfig:
    module_type: ModuleType
    display_mode: DisplayMode
    position: int = 0
    enabled: bool = True


class DashboardManager:
    """Manages multiple dashboard modules with user-configurable layouts."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.modules = {}
        self.active_configs: List[ModuleConfig] = []
        self.live_display: Optional[Live] = None
        self.running = False
        
        # Initialize all available modules
        self._init_modules()
        
        # Load configuration from environment
        self._load_config()
    
    def _init_modules(self):
        """Initialize all dashboard modules."""
        self.modules = {
            ModuleType.PERFORMANCE: PerformanceMonitor(),
            ModuleType.ACTIVITY: ActivityFeed(),
            ModuleType.ROUTING: RoutingVisualizer(),
            ModuleType.ANALYTICS: AnalyticsPanel(),
            ModuleType.WATERFALL: RequestWaterfall()
        }
    
    def _load_config(self):
        """Load dashboard configuration from environment variables."""
        # Default configuration
        default_modules = [
            ModuleConfig(ModuleType.PERFORMANCE, DisplayMode.DENSE, 0),
            ModuleConfig(ModuleType.ACTIVITY, DisplayMode.SPARSE, 1)
        ]
        
        # Load from environment
        dashboard_config = os.environ.get("DASHBOARD_MODULES", "performance:dense,activity:sparse")
        
        if dashboard_config:
            self.active_configs = self._parse_config_string(dashboard_config)
        else:
            self.active_configs = default_modules
    
    def _parse_config_string(self, config_str: str) -> List[ModuleConfig]:
        """Parse dashboard configuration string."""
        configs = []
        
        for i, module_config in enumerate(config_str.split(",")):
            if ":" in module_config:
                module_name, mode = module_config.strip().split(":")
                try:
                    module_type = ModuleType(module_name.lower())
                    display_mode = DisplayMode(mode.lower())
                    configs.append(ModuleConfig(module_type, display_mode, i))
                except ValueError:
                    continue
        
        return configs
    
    def configure_modules(self, configs: List[ModuleConfig]):
        """Configure active dashboard modules."""
        self.active_configs = sorted(configs, key=lambda x: x.position)
    
    def add_module(self, module_type: ModuleType, display_mode: DisplayMode = DisplayMode.DENSE):
        """Add a module to the dashboard."""
        config = ModuleConfig(module_type, display_mode, len(self.active_configs))
        self.active_configs.append(config)
    
    def remove_module(self, module_type: ModuleType):
        """Remove a module from the dashboard."""
        self.active_configs = [c for c in self.active_configs if c.module_type != module_type]
    
    def log_request_data(self, request_data: Dict[str, Any]):
        """Log request data to all active modules."""
        for config in self.active_configs:
            if config.enabled and config.module_type in self.modules:
                module = self.modules[config.module_type]
                module.add_request_data(request_data)
    
    def render_dashboard(self) -> str:
        """Render the complete dashboard."""
        if not RICH_AVAILABLE:
            return self._render_plain_dashboard()
        
        if not self.active_configs:
            return "No dashboard modules configured."
        
        # Create layout based on number of modules
        layout = self._create_layout()
        
        # Render each module
        for i, config in enumerate(self.active_configs):
            if config.enabled and config.module_type in self.modules:
                module = self.modules[config.module_type]
                content = module.render(config.display_mode)
                
                # Add to layout
                section_name = f"module_{i}"
                if hasattr(layout, section_name):
                    layout[section_name].update(Panel(content, title=module.get_title()))
        
        return layout
    
    def _create_layout(self) -> Layout:
        """Create Rich layout based on active modules."""
        num_modules = len([c for c in self.active_configs if c.enabled])
        
        if num_modules == 1:
            layout = Layout(name="root")
            layout.add_split(Layout(name="module_0"))
        elif num_modules == 2:
            layout = Layout(name="root")
            layout.split_row(
                Layout(name="module_0"),
                Layout(name="module_1")
            )
        elif num_modules == 3:
            layout = Layout(name="root")
            layout.split_column(
                Layout(name="module_0"),
                Layout(name="bottom")
            )
            layout["bottom"].split_row(
                Layout(name="module_1"),
                Layout(name="module_2")
            )
        elif num_modules == 4:
            layout = Layout(name="root")
            layout.split_column(
                Layout(name="top"),
                Layout(name="bottom")
            )
            layout["top"].split_row(
                Layout(name="module_0"),
                Layout(name="module_1")
            )
            layout["bottom"].split_row(
                Layout(name="module_2"),
                Layout(name="module_3")
            )
        else:
            # For more than 4 modules, use a grid layout
            layout = Layout(name="root")
            # Create a simple vertical stack for now
            for i in range(min(num_modules, 6)):  # Limit to 6 modules max
                layout.add_split(Layout(name=f"module_{i}"))
        
        return layout
    
    def _render_plain_dashboard(self) -> str:
        """Render dashboard without Rich formatting."""
        lines = []
        lines.append("=" * 80)
        lines.append("API DASHBOARD")
        lines.append("=" * 80)
        
        for config in self.active_configs:
            if config.enabled and config.module_type in self.modules:
                module = self.modules[config.module_type]
                content = module.render_plain(config.display_mode)
                lines.append(f"\n--- {module.get_title()} ---")
                lines.append(content)
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    async def start_live_dashboard(self, refresh_rate: float = 1.0):
        """Start live updating dashboard."""
        if not RICH_AVAILABLE:
            print("Rich library not available. Live dashboard disabled.")
            return
        
        self.running = True
        
        with Live(self.render_dashboard(), console=self.console, refresh_per_second=refresh_rate) as live:
            self.live_display = live
            
            while self.running:
                try:
                    live.update(self.render_dashboard())
                    await asyncio.sleep(1.0 / refresh_rate)
                except KeyboardInterrupt:
                    break
        
        self.running = False
    
    def stop_live_dashboard(self):
        """Stop live dashboard."""
        self.running = False
    
    def print_dashboard(self):
        """Print current dashboard state."""
        if RICH_AVAILABLE and self.console:
            self.console.print(self.render_dashboard())
        else:
            print(self._render_plain_dashboard())
    
    def get_available_modules(self) -> List[str]:
        """Get list of available module types."""
        return [module.value for module in ModuleType]
    
    def get_module_info(self) -> Dict[str, str]:
        """Get information about each module."""
        info = {}
        for module_type, module in self.modules.items():
            info[module_type.value] = module.get_description()
        return info


# Global dashboard instance
dashboard_manager = DashboardManager()