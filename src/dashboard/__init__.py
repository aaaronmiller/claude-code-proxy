"""
Dashboard package for terminal and web-based monitoring.
"""

from src.dashboard.terminal_dashboard import terminal_dashboard
from src.dashboard.dashboard_hooks import dashboard_hooks

__all__ = ['terminal_dashboard', 'dashboard_hooks']
