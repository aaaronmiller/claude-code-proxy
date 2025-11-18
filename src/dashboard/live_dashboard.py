#!/usr/bin/env python3
"""
Live Dashboard - Real-time API monitoring interface.

Replaces standard terminal output with a rich dashboard interface.
"""

import os
import sys
import asyncio
import signal
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.dashboard.dashboard_manager import dashboard_manager
from src.utils.request_logger import RequestLogger


class LiveDashboard:
    """Live updating dashboard that replaces terminal logging."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.running = False
        self.live_display = None
        
        # Override the request logger to feed data to dashboard
        self._setup_dashboard_integration()
    
    def _setup_dashboard_integration(self):
        """Integrate dashboard with request logging."""
        # Store original methods
        original_log_complete = RequestLogger.log_request_complete
        original_log_start = RequestLogger.log_request_start
        original_log_error = RequestLogger.log_request_error
        
        def dashboard_log_start(*args, **kwargs):
            """Enhanced log_request_start that feeds dashboard."""
            # Call original method for any file logging
            original_log_start(*args, **kwargs)
            
            # Extract data for dashboard
            request_data = {
                'type': 'start',
                'request_id': kwargs.get('request_id', args[0] if args else 'unknown'),
                'original_model': kwargs.get('original_model', args[1] if len(args) > 1 else 'unknown'),
                'routed_model': kwargs.get('routed_model', args[2] if len(args) > 2 else 'unknown'),
                'endpoint': kwargs.get('endpoint', args[3] if len(args) > 3 else 'unknown'),
                'reasoning_config': kwargs.get('reasoning_config'),
                'stream': kwargs.get('stream', False),
                'context_limit': kwargs.get('context_limit', 0),
                'output_limit': kwargs.get('output_limit', 0),
                'input_tokens': kwargs.get('input_tokens', 0),
                'message_count': kwargs.get('message_count', 0),
                'has_system': kwargs.get('has_system', False),
                'client_info': kwargs.get('client_info', 'unknown')
            }
            
            # Feed to dashboard
            dashboard_manager.log_request_data(request_data)
        
        def dashboard_log_complete(*args, **kwargs):
            """Enhanced log_request_complete that feeds dashboard."""
            # Call original method for any file logging
            original_log_complete(*args, **kwargs)
            
            # Extract data for dashboard
            request_data = {
                'type': 'complete',
                'request_id': kwargs.get('request_id', args[0] if args else 'unknown'),
                'usage': kwargs.get('usage', {}),
                'duration_ms': kwargs.get('duration_ms', 0),
                'status': kwargs.get('status', 'OK'),
                'model_name': kwargs.get('model_name', 'unknown'),
                'stream': kwargs.get('stream', False),
                'message_count': kwargs.get('message_count', 0),
                'has_system': kwargs.get('has_system', False),
                'client_info': kwargs.get('client_info', 'unknown')
            }
            
            # Feed to dashboard
            dashboard_manager.log_request_data(request_data)
        
        def dashboard_log_error(*args, **kwargs):
            """Enhanced log_request_error that feeds dashboard."""
            # Call original method for any file logging
            original_log_error(*args, **kwargs)
            
            # Extract data for dashboard
            request_data = {
                'type': 'error',
                'request_id': kwargs.get('request_id', args[0] if args else 'unknown'),
                'error': kwargs.get('error', args[1] if len(args) > 1 else 'unknown'),
                'duration_ms': kwargs.get('duration_ms', 0)
            }
            
            # Feed to dashboard
            dashboard_manager.log_request_data(request_data)
        
        # Replace methods
        RequestLogger.log_request_start = staticmethod(dashboard_log_start)
        RequestLogger.log_request_complete = staticmethod(dashboard_log_complete)
        RequestLogger.log_request_error = staticmethod(dashboard_log_error)
    
    def create_header(self) -> Panel:
        """Create dashboard header."""
        header_text = Text()
        header_text.append("🚀 API Dashboard", style="bold cyan")
        header_text.append(" | ", style="dim")
        header_text.append("Live Monitoring", style="green")
        header_text.append(" | ", style="dim")
        header_text.append("Press Ctrl+C to exit", style="dim")
        
        return Panel(header_text, style="cyan")
    
    def create_layout(self) -> Layout:
        """Create the main dashboard layout."""
        layout = Layout(name="root")
        
        # Add header
        layout.split_column(
            Layout(self.create_header(), name="header", size=3),
            Layout(name="main")
        )
        
        # Get dashboard content
        dashboard_content = dashboard_manager.render_dashboard()
        layout["main"].update(dashboard_content)
        
        return layout
    
    async def start(self, refresh_rate: float = 2.0):
        """Start the live dashboard."""
        if not RICH_AVAILABLE:
            print("Rich library not available. Falling back to standard logging.")
            return
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            with Live(
                self.create_layout(),
                console=self.console,
                refresh_per_second=refresh_rate,
                screen=True
            ) as live:
                self.live_display = live
                
                while self.running:
                    try:
                        # Update layout
                        layout = self.create_layout()
                        live.update(layout)
                        
                        # Sleep
                        await asyncio.sleep(1.0 / refresh_rate)
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        # Log error but continue
                        if self.console:
                            self.console.print(f"[red]Dashboard error: {e}[/red]")
                        await asyncio.sleep(1.0)
        
        except Exception as e:
            if self.console:
                self.console.print(f"[red]Failed to start dashboard: {e}[/red]")
            print(f"Failed to start dashboard: {e}")
        
        finally:
            self.running = False
    
    def stop(self):
        """Stop the dashboard."""
        self.running = False


def main():
    """Main entry point for live dashboard."""
    # Check for configuration
    config = os.environ.get("DASHBOARD_MODULES")
    if not config:
        print("No dashboard configuration found.")
        print("Run 'python configure_dashboard.py' to set up your dashboard.")
        return
    
    print(f"Starting dashboard with modules: {config}")
    
    # Create and start dashboard
    dashboard = LiveDashboard()
    
    try:
        asyncio.run(dashboard.start())
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Dashboard error: {e}")


if __name__ == "__main__":
    main()