"""
Performance Monitor Module - Real-time request performance tracking.
"""

import time
from typing import Dict, Any, Optional
from .base_module import BaseModule

try:
    from rich.text import Text
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PerformanceMonitor(BaseModule):
    """Real-time performance monitoring module."""
    
    def __init__(self):
        super().__init__(max_history=50)
        self.current_request: Optional[Dict[str, Any]] = None
    
    def get_title(self) -> str:
        return "Performance Monitor"
    
    def get_description(self) -> str:
        return "Real-time request performance tracking with context and thinking token usage"
    
    def add_request_data(self, request_data: Dict[str, Any]):
        """Override to track current request."""
        super().add_request_data(request_data)
        
        if request_data.get('type') == 'start':
            self.current_request = request_data
        elif request_data.get('type') in ['complete', 'error']:
            if self.current_request and self.current_request.get('request_id') == request_data.get('request_id'):
                self.current_request = None
    
    def render_dense(self) -> str:
        """Render detailed performance view."""
        if not RICH_AVAILABLE:
            return self._render_dense_plain()
        
        # Get latest completed request for display
        recent_requests = self.get_recent_requests(5)
        latest_complete = None
        
        for req in reversed(recent_requests):
            if req.get('type') == 'complete':
                latest_complete = req
                break
        
        if not latest_complete:
            return Text("No completed requests yet...", style="dim")
        
        # Extract data
        request_id = latest_complete.get('request_id', 'unknown')[:6]
        usage = latest_complete.get('usage', {})
        duration_ms = latest_complete.get('duration_ms', 0)
        model_name = latest_complete.get('model_name', 'unknown')
        
        # Get corresponding start request for routing info
        start_req = None
        for req in recent_requests:
            if req.get('type') == 'start' and req.get('request_id') == latest_complete.get('request_id'):
                start_req = req
                break
        
        # Build display
        text = Text()
        
        # Header with session info
        text.append(f"🔵 Session {request_id}", style="bold cyan")
        
        if start_req:
            original_model = start_req.get('original_model', 'unknown')
            routed_model = start_req.get('routed_model', 'unknown')
            text.append(f" | {self._format_model_name(original_model)}→{self._format_model_name(routed_model)}", style="yellow")
        
        text.append("\n")
        
        # Performance metrics
        text.append(f"⚡ {self.format_duration(duration_ms)}", style="green")
        
        # Context usage
        input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        
        if start_req:
            context_limit = start_req.get('context_limit', 0)
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = (input_tokens / context_limit) * 100
                ctx_bar = self.create_progress_bar(input_tokens, context_limit, 10)
                text.append(f" | 📊 CTX: {ctx_bar} {self.format_tokens(input_tokens)}/{self.format_tokens(context_limit)} ({ctx_pct:.0f}%)", style="cyan")
        
        # Performance
        if output_tokens > 0 and duration_ms > 0:
            tok_s = output_tokens / (duration_ms / 1000)
            text.append(f" | {tok_s:.0f} tok/s", style="bright_green")
        
        text.append("\n")
        
        # Thinking tokens
        if thinking_tokens > 0:
            text.append(f"🧠 THINK: ", style="magenta")
            if start_req and start_req.get('output_limit', 0) > 0:
                think_bar = self.create_progress_bar(thinking_tokens, start_req['output_limit'], 10)
                text.append(f"{think_bar} {self.format_tokens(thinking_tokens)} tokens", style="bright_magenta")
            else:
                text.append(f"{self.format_tokens(thinking_tokens)} tokens", style="bright_magenta")
        
        # Cost estimate (rough)
        cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
        text.append(f" | 💰 {self.format_cost(cost)} estimated", style="yellow")
        
        text.append("\n")
        
        # Output info
        if start_req:
            output_limit = start_req.get('output_limit', 0)
            if output_limit > 0:
                out_bar = self.create_progress_bar(output_tokens, output_limit, 10)
                text.append(f"📤 OUT: {out_bar} {self.format_tokens(output_tokens)}/{self.format_tokens(output_limit)}", style="blue")
            
            # Request metadata
            if start_req.get('stream'):
                text.append(" | 🌊 STREAMING", style="bright_blue")
            
            message_count = start_req.get('message_count', 0)
            has_system = start_req.get('has_system', False)
            if message_count > 0:
                text.append(f" | {message_count}msg", style="dim")
            if has_system:
                text.append(" + SYS", style="green")
        
        return text
    
    def render_sparse(self) -> str:
        """Render compact performance view."""
        recent_requests = self.get_recent_requests(1)
        if not recent_requests or recent_requests[-1].get('type') != 'complete':
            return "🔵 ... | waiting for requests"
        
        req = recent_requests[-1]
        request_id = req.get('request_id', 'unknown')[:6]
        usage = req.get('usage', {})
        duration_ms = req.get('duration_ms', 0)
        model_name = req.get('model_name', 'unknown')
        
        # Get tokens
        input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        
        # Get context percentage
        ctx_pct = 0
        for start_req in reversed(self.request_history):
            if start_req.get('type') == 'start' and start_req.get('request_id') == req.get('request_id'):
                context_limit = start_req.get('context_limit', 0)
                if context_limit > 0:
                    ctx_pct = (input_tokens / context_limit) * 100
                break
        
        # Performance
        tok_s = 0
        if output_tokens > 0 and duration_ms > 0:
            tok_s = output_tokens / (duration_ms / 1000)
        
        # Cost
        cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
        
        # Build compact string
        parts = [
            f"🔵 {request_id}",
            f"⚡{self.format_duration(duration_ms)}",
            f"📊{ctx_pct:.0f}%" if ctx_pct > 0 else f"📊{self.format_tokens(input_tokens)}",
            f"🧠{self.format_tokens(thinking_tokens)}" if thinking_tokens > 0 else "",
            f"💰{self.format_cost(cost)}",
            f"{tok_s:.0f}t/s" if tok_s > 0 else ""
        ]
        
        return " | ".join([p for p in parts if p])
    
    def _render_dense_plain(self) -> str:
        """Plain text version of dense rendering."""
        recent_requests = self.get_recent_requests(1)
        if not recent_requests or recent_requests[-1].get('type') != 'complete':
            return "No completed requests yet..."
        
        req = recent_requests[-1]
        request_id = req.get('request_id', 'unknown')[:6]
        duration_ms = req.get('duration_ms', 0)
        usage = req.get('usage', {})
        
        lines = [
            f"Session {request_id}",
            f"Duration: {self.format_duration(duration_ms)}",
            f"Input tokens: {self.format_tokens(usage.get('input_tokens', 0))}",
            f"Output tokens: {self.format_tokens(usage.get('output_tokens', 0))}",
        ]
        
        thinking_tokens = self._extract_thinking_tokens(usage)
        if thinking_tokens > 0:
            lines.append(f"Thinking tokens: {self.format_tokens(thinking_tokens)}")
        
        return "\n".join(lines)
    
    def _format_model_name(self, model_name: str) -> str:
        """Format model name for display."""
        # Extract key parts
        if "claude" in model_name.lower():
            if "3.5" in model_name:
                return "claude-3.5"
            elif "3" in model_name:
                return "claude-3"
            return "claude"
        elif "gpt-4o" in model_name.lower():
            return "gpt-4o" + ("-mini" if "mini" in model_name else "")
        elif "gpt-4" in model_name.lower():
            return "gpt-4"
        elif "o1" in model_name.lower():
            return "o1" + ("-mini" if "mini" in model_name else "")
        elif "gemini" in model_name.lower():
            return "gemini"
        
        # Fallback
        return model_name.split("/")[-1] if "/" in model_name else model_name
    
    def _extract_thinking_tokens(self, usage: Dict[str, Any]) -> int:
        """Extract thinking tokens from usage data."""
        if "thinking_tokens" in usage:
            return usage["thinking_tokens"]
        elif "reasoning_tokens" in usage:
            return usage["reasoning_tokens"]
        elif "completion_tokens_details" in usage:
            details = usage["completion_tokens_details"]
            if isinstance(details, dict):
                return details.get("reasoning_tokens", 0)
        return 0
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int, thinking_tokens: int, model_name: str) -> float:
        """Rough cost estimation."""
        # Very rough estimates - would need actual pricing data
        if "gpt-4o" in model_name.lower():
            if "mini" in model_name.lower():
                return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
            else:
                return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
        elif "claude" in model_name.lower():
            return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        elif "o1" in model_name.lower():
            return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
        
        # Default estimate
        return (input_tokens * 0.001 + output_tokens * 0.002) / 1000