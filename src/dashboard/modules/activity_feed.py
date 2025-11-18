"""
Activity Feed Module - Multi-session request history tracking.
"""

import time
from typing import Dict, Any, List
from .base_module import BaseModule

try:
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ActivityFeed(BaseModule):
    """Multi-session activity feed module."""
    
    def __init__(self):
        super().__init__(max_history=100)
    
    def get_title(self) -> str:
        return "Activity Feed"
    
    def get_description(self) -> str:
        return "Multi-session request history with status tracking"
    
    def render_dense(self) -> str:
        """Render detailed activity feed."""
        if not RICH_AVAILABLE:
            return self._render_dense_plain()
        
        # Get recent completed requests
        recent_requests = self.get_recent_requests(10)
        completed_requests = []
        
        # Group by request_id to match start/complete pairs
        request_pairs = {}
        for req in recent_requests:
            req_id = req.get('request_id')
            if req_id not in request_pairs:
                request_pairs[req_id] = {}
            request_pairs[req_id][req.get('type')] = req
        
        # Build activity lines
        text = Text()
        
        for req_id, pair in list(request_pairs.items())[-4:]:  # Show last 4 requests
            start_req = pair.get('start')
            complete_req = pair.get('complete')
            error_req = pair.get('error')
            
            if not start_req:
                continue
            
            # Status icon and request ID
            if error_req:
                text.append("🔴 ", style="red")
                status = "ERROR"
                status_style = "red"
            elif complete_req:
                text.append("🟢 ", style="green")
                status = "OK"
                status_style = "green"
            else:
                text.append("🔵 ", style="blue")
                status = "RUNNING"
                status_style = "blue"
            
            text.append(f"{req_id[:6]} ", style="cyan")
            
            # Model routing
            original_model = self._format_model_name(start_req.get('original_model', 'unknown'))
            routed_model = self._format_model_name(start_req.get('routed_model', 'unknown'))
            text.append(f"{original_model}→{routed_model} ", style="yellow")
            
            # Performance data
            if complete_req:
                usage = complete_req.get('usage', {})
                duration_ms = complete_req.get('duration_ms', 0)
                
                # Thinking tokens
                thinking_tokens = self._extract_thinking_tokens(usage)
                if thinking_tokens > 0:
                    text.append(f"| 🧠{self.format_tokens(thinking_tokens)} ", style="magenta")
                
                # Duration
                text.append(f"| ⚡{self.format_duration(duration_ms)} ", style="green")
                
                # Cost estimate
                input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
                output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
                cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, routed_model)
                text.append(f"| 💰{self.format_cost(cost)}", style="yellow")
            
            elif error_req:
                error_msg = str(error_req.get('error', 'Unknown error'))[:30]
                text.append(f"| {error_msg}", style="red")
                
                duration_ms = error_req.get('duration_ms', 0)
                if duration_ms > 0:
                    text.append(f" | ⚡{self.format_duration(duration_ms)}", style="dim")
            
            else:
                # Still running
                elapsed = time.time() - start_req.get('timestamp', time.time())
                text.append(f"| ⏳{elapsed:.1f}s", style="blue")
            
            text.append("\n")
        
        return text
    
    def render_sparse(self) -> str:
        """Render compact activity summary."""
        # Get recent requests for summary
        recent_requests = self.get_recent_requests(20)
        
        # Count by status
        completed = 0
        errors = 0
        running = 0
        
        request_ids = set()
        for req in recent_requests:
            req_id = req.get('request_id')
            if req_id in request_ids:
                continue
            request_ids.add(req_id)
            
            req_type = req.get('type')
            if req_type == 'complete':
                completed += 1
            elif req_type == 'error':
                errors += 1
            elif req_type == 'start':
                # Check if there's a corresponding complete/error
                has_completion = any(
                    r.get('request_id') == req_id and r.get('type') in ['complete', 'error']
                    for r in recent_requests
                )
                if not has_completion:
                    running += 1
        
        # Calculate average duration
        completed_reqs = [req for req in recent_requests if req.get('type') == 'complete']
        avg_duration = 0
        if completed_reqs:
            total_duration = sum(req.get('duration_ms', 0) for req in completed_reqs[-5:])
            avg_duration = total_duration / len(completed_reqs[-5:])
        
        # Build status icons
        status_parts = []
        if completed > 0:
            status_parts.append(f"🟢{completed}")
        if running > 0:
            status_parts.append(f"🔵{running}")
        if errors > 0:
            status_parts.append(f"🔴{errors}")
        
        status_str = "".join(status_parts) if status_parts else "🔵..."
        
        # Summary
        total_requests = completed + errors + running
        avg_str = f"{self.format_duration(avg_duration)} avg" if avg_duration > 0 else "no data"
        
        return f"{status_str} | {total_requests}req {avg_str}"
    
    def _render_dense_plain(self) -> str:
        """Plain text version of dense rendering."""
        recent_requests = self.get_recent_requests(5)
        
        lines = []
        request_pairs = {}
        
        for req in recent_requests:
            req_id = req.get('request_id')
            if req_id not in request_pairs:
                request_pairs[req_id] = {}
            request_pairs[req_id][req.get('type')] = req
        
        for req_id, pair in list(request_pairs.items())[-3:]:
            start_req = pair.get('start')
            complete_req = pair.get('complete')
            error_req = pair.get('error')
            
            if not start_req:
                continue
            
            status = "ERROR" if error_req else "OK" if complete_req else "RUNNING"
            original_model = start_req.get('original_model', 'unknown')
            routed_model = start_req.get('routed_model', 'unknown')
            
            line = f"{status} {req_id[:8]} {original_model}→{routed_model}"
            
            if complete_req:
                duration_ms = complete_req.get('duration_ms', 0)
                line += f" {self.format_duration(duration_ms)}"
            
            lines.append(line)
        
        return "\n".join(lines) if lines else "No recent activity"
    
    def _format_model_name(self, model_name: str) -> str:
        """Format model name for display."""
        if "claude" in model_name.lower():
            if "opus" in model_name.lower():
                return "claude-opus"
            elif "sonnet" in model_name.lower():
                return "claude-sonnet"
            elif "haiku" in model_name.lower():
                return "claude-haiku"
            return "claude"
        elif "gpt-4o" in model_name.lower():
            return "gpt4o" + ("-mini" if "mini" in model_name else "")
        elif "gpt-4" in model_name.lower():
            return "gpt4"
        elif "o1" in model_name.lower():
            return "o1" + ("-mini" if "mini" in model_name else "")
        elif "gemini" in model_name.lower():
            return "gemini"
        
        return model_name.split("/")[-1] if "/" in model_name else model_name[:10]
    
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
        if "gpt-4o" in model_name.lower():
            if "mini" in model_name.lower():
                return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
            else:
                return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
        elif "claude" in model_name.lower():
            return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        elif "o1" in model_name.lower():
            return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
        
        return (input_tokens * 0.001 + output_tokens * 0.002) / 1000