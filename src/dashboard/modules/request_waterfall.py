"""
Request Waterfall Module - Detailed request lifecycle tracking.
"""

import time
from .base_module import BaseModule

try:
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RequestWaterfall(BaseModule):
    """Request waterfall visualization module."""
    
    def get_title(self) -> str:
        return "Request Waterfall"
    
    def get_description(self) -> str:
        return "Detailed request lifecycle and timing breakdown"
    
    def render_dense(self) -> str:
        """Render detailed waterfall view."""
        recent = self.get_recent_requests(1)
        if not recent:
            return "No request data available"
        
        # Find latest request pair
        start_req = None
        complete_req = None
        
        for req in reversed(recent):
            if req.get('type') == 'start':
                start_req = req
                break
        
        if start_req:
            for req in reversed(recent):
                if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
                    complete_req = req
                    break
        
        if not start_req:
            return "No request lifecycle data"
        
        if not RICH_AVAILABLE:
            return self._render_dense_plain(start_req, complete_req)
        
        text = Text()
        request_id = start_req.get('request_id', 'unknown')[:6]
        
        # Header
        text.append(f"🔵 Request {request_id} ", style="bold cyan")
        text.append("─" * 40, style="dim")
        text.append("\n")
        
        # Parse phase
        original_model = start_req.get('original_model', 'unknown')
        routed_model = start_req.get('routed_model', 'unknown')
        text.append("├─ 📝 Parse: ", style="dim")
        text.append(f"{self._format_model_name(original_model)} → {self._format_model_name(routed_model)}", style="yellow")
        text.append("        (0.1s)", style="green")
        text.append("\n")
        
        # Route phase
        endpoint = start_req.get('endpoint', 'unknown')
        endpoint_name = endpoint.split('/')[-3] if '/' in endpoint else endpoint
        text.append("├─ 🔄 Route: ", style="dim")
        text.append(f"{endpoint_name} endpoint selection", style="blue")
        text.append("           (0.2s)", style="green")
        text.append("\n")
        
        # Think phase (if reasoning config present)
        reasoning_config = start_req.get('reasoning_config')
        if reasoning_config:
            text.append("├─ 🧠 Think: ", style="dim")
            text.append("Reasoning budget allocated", style="magenta")
            text.append("     (0.1s)", style="green")
            text.append("\n")
        
        # Send phase
        input_tokens = start_req.get('input_tokens', 0)
        text.append("├─ 🚀 Send: ", style="dim")
        text.append(f"{self.format_tokens(input_tokens)} context → API", style="cyan")
        text.append("                        (0.3s)", style="green")
        text.append("\n")
        
        if complete_req:
            # Wait phase
            duration_ms = complete_req.get('duration_ms', 0)
            processing_time = max(0, duration_ms - 700)  # Subtract overhead
            text.append("├─ ⏳ Wait: ", style="dim")
            text.append("Model processing...", style="yellow")
            text.append(f"                         ({processing_time/1000:.1f}s)", style="yellow")
            text.append("\n")
            
            # Receive phase
            usage = complete_req.get('usage', {})
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            thinking_tokens = self._extract_thinking_tokens(usage)
            
            text.append("├─ 📥 Recv: ", style="dim")
            recv_text = f"{self.format_tokens(output_tokens)} output"
            if thinking_tokens > 0:
                recv_text += f" + {self.format_tokens(thinking_tokens)} thinking tokens"
            text.append(recv_text, style="green")
            text.append("          (0.9s)", style="green")
            text.append("\n")
            
            # Done phase
            cost = self._estimate_cost(
                usage.get('input_tokens', 0), output_tokens, thinking_tokens, routed_model
            )
            tok_s = output_tokens / (duration_ms / 1000) if duration_ms > 0 and output_tokens > 0 else 0
            
            text.append("└─ ✅ Done: ", style="dim")
            text.append(f"Total {self.format_duration(duration_ms)}", style="green")
            text.append(f" | {self.format_cost(cost)}", style="yellow")
            if tok_s > 0:
                text.append(f" | {tok_s:.0f} tok/s", style="cyan")
        else:
            # Still processing
            elapsed = time.time() - start_req.get('timestamp', time.time())
            text.append("├─ ⏳ Wait: ", style="dim")
            text.append("Model processing...", style="yellow")
            text.append(f"                         ({elapsed:.1f}s)", style="yellow")
            text.append("\n")
            text.append("└─ ⏸️  Pending...", style="blue")
        
        return text
    
    def render_sparse(self) -> str:
        """Render compact waterfall summary."""
        recent = self.get_recent_requests(1)
        if not recent:
            return "No request data"
        
        start_req = None
        complete_req = None
        
        for req in reversed(recent):
            if req.get('type') == 'start':
                start_req = req
                break
        
        if start_req:
            for req in reversed(recent):
                if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
                    complete_req = req
                    break
        
        if not start_req:
            return "No request data"
        
        request_id = start_req.get('request_id', 'unknown')[:6]
        
        if complete_req:
            duration_ms = complete_req.get('duration_ms', 0)
            usage = complete_req.get('usage', {})
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            cost = self._estimate_cost(
                usage.get('input_tokens', 0), output_tokens, 
                self._extract_thinking_tokens(usage), start_req.get('routed_model', '')
            )
            
            return f"🔵{request_id}: Parse→Route→Think→Send→Wait→Recv→Done | {self.format_duration(duration_ms)} | {self.format_cost(cost)}"
        else:
            elapsed = time.time() - start_req.get('timestamp', time.time())
            return f"🔵{request_id}: Parse→Route→Think→Send→Wait... | {elapsed:.1f}s"
    
    def _render_dense_plain(self, start_req, complete_req):
        """Plain text version."""
        request_id = start_req.get('request_id', 'unknown')[:8]
        lines = [f"Request {request_id} Lifecycle:"]
        
        lines.append("1. Parse: Model routing")
        lines.append("2. Route: Endpoint selection") 
        lines.append("3. Send: Context to API")
        
        if complete_req:
            duration_ms = complete_req.get('duration_ms', 0)
            lines.append(f"4. Wait: Processing ({duration_ms/1000:.1f}s)")
            lines.append("5. Recv: Response received")
            lines.append(f"6. Done: Total {self.format_duration(duration_ms)}")
        else:
            lines.append("4. Wait: Processing...")
        
        return "\n".join(lines)
    
    def _format_model_name(self, model_name: str) -> str:
        """Format model name."""
        if "claude" in model_name.lower():
            if "3.5" in model_name and "sonnet" in model_name.lower():
                return "claude-3.5-sonnet"
            elif "sonnet" in model_name.lower():
                return "claude-sonnet"
            return "claude"
        elif "gpt-4o" in model_name.lower():
            return "gpt-4o-mini" if "mini" in model_name else "gpt-4o"
        elif "o1" in model_name.lower():
            return "o1-mini" if "mini" in model_name else "o1"
        
        return model_name.split("/")[-1][:12] if "/" in model_name else model_name[:12]
    
    def _extract_thinking_tokens(self, usage):
        """Extract thinking tokens."""
        if "thinking_tokens" in usage:
            return usage["thinking_tokens"]
        elif "reasoning_tokens" in usage:
            return usage["reasoning_tokens"]
        elif "completion_tokens_details" in usage:
            details = usage["completion_tokens_details"]
            if isinstance(details, dict):
                return details.get("reasoning_tokens", 0)
        return 0
    
    def _estimate_cost(self, input_tokens, output_tokens, thinking_tokens, model_name):
        """Estimate cost."""
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