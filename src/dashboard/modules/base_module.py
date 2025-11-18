"""
Base module class for dashboard components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from collections import deque
import time

try:
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class BaseModule(ABC):
    """Base class for all dashboard modules."""
    
    def __init__(self, max_history: int = 100):
        self.request_history = deque(maxlen=max_history)
        self.last_update = time.time()
    
    def add_request_data(self, request_data: Dict[str, Any]):
        """Add request data to module history."""
        request_data['timestamp'] = time.time()
        self.request_history.append(request_data)
        self.last_update = time.time()
    
    @abstractmethod
    def get_title(self) -> str:
        """Get module title."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get module description."""
        pass
    
    @abstractmethod
    def render_dense(self) -> str:
        """Render module in dense mode."""
        pass
    
    @abstractmethod
    def render_sparse(self) -> str:
        """Render module in sparse mode."""
        pass
    
    def render(self, mode: str = "dense") -> str:
        """Render module based on display mode."""
        if mode == "sparse":
            return self.render_sparse()
        else:
            return self.render_dense()
    
    def render_plain(self, mode: str = "dense") -> str:
        """Render module without Rich formatting."""
        # Default implementation strips Rich formatting
        content = self.render(mode)
        if RICH_AVAILABLE:
            # Simple Rich markup removal
            import re
            content = re.sub(r'\[/?[^\]]*\]', '', content)
        return content
    
    def get_recent_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get most recent requests."""
        return list(self.request_history)[-count:]
    
    def get_active_requests(self) -> List[Dict[str, Any]]:
        """Get requests that are currently active (started but not completed)."""
        active = []
        completed_ids = {req['request_id'] for req in self.request_history if req.get('type') == 'complete'}
        
        for req in self.request_history:
            if req.get('type') == 'start' and req['request_id'] not in completed_ids:
                active.append(req)
        
        return active
    
    def get_completed_requests(self, since_seconds: int = 3600) -> List[Dict[str, Any]]:
        """Get completed requests within time window."""
        cutoff = time.time() - since_seconds
        return [
            req for req in self.request_history 
            if req.get('type') == 'complete' and req.get('timestamp', 0) > cutoff
        ]
    
    def format_duration(self, duration_ms: float) -> str:
        """Format duration in human readable format."""
        if duration_ms < 1000:
            return f"{duration_ms:.0f}ms"
        else:
            return f"{duration_ms/1000:.1f}s"
    
    def format_tokens(self, count: int) -> str:
        """Format token count compactly."""
        if count >= 1000:
            return f"{count/1000:.1f}k"
        return str(count)
    
    def format_cost(self, cost: float) -> str:
        """Format cost in dollars."""
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"
    
    def create_progress_bar(self, used: int, total: int, width: int = 10) -> str:
        """Create ASCII progress bar."""
        if total == 0:
            return "░" * width
        
        percentage = min(used / total, 1.0)
        filled_width = int(width * percentage)
        empty_width = width - filled_width
        
        return "█" * filled_width + "░" * empty_width