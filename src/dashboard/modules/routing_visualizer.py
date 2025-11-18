"""
Routing Visualizer Module - Model routing flow display.
"""

from .base_module import BaseModule

try:
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RoutingVisualizer(BaseModule):
    """Model routing visualization module."""
    
    def get_title(self) -> str:
        return "Model Routing"
    
    def get_description(self) -> str:
        return "Visual display of model routing decisions and flow"
    
    def render_dense(self) -> str:
        """Render detailed routing visualization."""
        recent = self.get_recent_requests(1)
        if not recent:
            return "No routing data available"
        
        # Find latest start request
        start_req = None
        complete_req = None
        
        for req in reversed(recent):
            if req.get('type') == 'start':
                start_req = req
                break
        
        for req in reversed(recent):
            if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
                complete_req = req
                break
        
        if not start_req:
            return "No routing information"
        
        if not RICH_AVAILABLE:
            return self._render_dense_plain(start_req, complete_req)
        
        text = Text()
        
        # Model flow
        original = start_req.get('original_model', 'unknown')
        routed = start_req.get('routed_model', 'unknown')
        
        text.append(f"[{self._format_model_display(original)}]", style="yellow")
        text.append(" ──routing──> ", style="dim")
        text.append(f"[{self._format_model_display(routed)}]", style="green")
        text.append("\n")
        
        # Context and output flow
        context_limit = start_req.get('context_limit', 0)
        input_tokens = start_req.get('input_tokens', 0)
        
        if context_limit > 0:
            text.append(f"     ↓ {self.format_tokens(input_tokens)} ctx", style="cyan")
        
        if complete_req:
            usage = complete_req.get('usage', {})
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            text.append(f"                  ↓ {self.format_tokens(output_tokens)} out", style="blue")
            text.append("\n")
            
            # Performance metrics
            thinking_tokens = self._extract_thinking_tokens(usage)
            if thinking_tokens > 0:
                text.append(f"🧠 Thinking: {self.format_tokens(thinking_tokens)} tokens", style="magenta")
            
            duration_ms = complete_req.get('duration_ms', 0)
            if duration_ms > 0 and output_tokens > 0:
                tok_s = output_tokens / (duration_ms / 1000)
                text.append(f"      ⚡ Speed: {tok_s:.0f} tok/s", style="green")
            
            text.append("\n")
            
            # Cost and efficiency
            input_tokens_actual = usage.get('input_tokens', usage.get('prompt_tokens', 0))
            cost = self._estimate_cost(input_tokens_actual, output_tokens, thinking_tokens, routed)
            text.append(f"💰 Cost: {self.format_cost(cost)}", style="yellow")
            
            # Efficiency calculation
            if context_limit > 0 and input_tokens_actual > 0:
                efficiency = min(100, (output_tokens / input_tokens_actual) * 100)
                text.append(f"            📊 Efficiency: {efficiency:.0f}%", style="cyan")
        
        return text
    
    def render_sparse(self) -> str:
        """Render compact routing info."""
        recent = self.get_recent_requests(1)
        if not recent:
            return "No routing data"
        
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
            return "No routing info"
        
        original = self._format_model_name(start_req.get('original_model', 'unknown'))
        routed = self._format_model_name(start_req.get('routed_model', 'unknown'))
        
        parts = [f"{original}→{routed}"]
        
        input_tokens = start_req.get('input_tokens', 0)
        if input_tokens > 0:
            parts.append(f"{self.format_tokens(input_tokens)}")
        
        if complete_req:
            usage = complete_req.get('usage', {})
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            thinking_tokens = self._extract_thinking_tokens(usage)
            duration_ms = complete_req.get('duration_ms', 0)
            
            if output_tokens > 0:
                parts.append(f"→{self.format_tokens(output_tokens)}")
            
            if thinking_tokens > 0:
                parts.append(f"🧠{self.format_tokens(thinking_tokens)}")
            
            if duration_ms > 0 and output_tokens > 0:
                tok_s = output_tokens / (duration_ms / 1000)
                parts.append(f"⚡{tok_s:.0f}t/s")
            
            cost = self._estimate_cost(
                usage.get('input_tokens', 0), output_tokens, thinking_tokens, routed
            )
            parts.append(f"💰{self.format_cost(cost)}")
        
        return " | ".join(parts)
    
    def _render_dense_plain(self, start_req, complete_req):
        """Plain text version."""
        original = start_req.get('original_model', 'unknown')
        routed = start_req.get('routed_model', 'unknown')
        
        lines = [
            f"Routing: {original} -> {routed}",
            f"Context: {self.format_tokens(start_req.get('input_tokens', 0))}"
        ]
        
        if complete_req:
            usage = complete_req.get('usage', {})
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            lines.append(f"Output: {self.format_tokens(output_tokens)}")
            
            thinking_tokens = self._extract_thinking_tokens(usage)
            if thinking_tokens > 0:
                lines.append(f"Thinking: {self.format_tokens(thinking_tokens)}")
        
        return "\n".join(lines)
    
    def _format_model_display(self, model_name: str) -> str:
        """Format model name for display."""
        if "claude" in model_name.lower():
            if "3.5" in model_name and "sonnet" in model_name.lower():
                return "Claude 3.5 Sonnet"
            elif "3" in model_name and "opus" in model_name.lower():
                return "Claude 3 Opus"
            elif "3" in model_name and "haiku" in model_name.lower():
                return "Claude 3 Haiku"
            return "Claude"
        elif "gpt-4o" in model_name.lower():
            if "mini" in model_name.lower():
                return "GPT-4o Mini"
            return "GPT-4o"
        elif "o1" in model_name.lower():
            if "preview" in model_name.lower():
                return "o1-preview"
            elif "mini" in model_name.lower():
                return "o1-mini"
            return "o1"
        
        return model_name.split("/")[-1] if "/" in model_name else model_name
    
    def _format_model_name(self, model_name: str) -> str:
        """Short format for model name."""
        if "claude" in model_name.lower():
            if "sonnet" in model_name.lower():
                return "claude-sonnet"
            elif "opus" in model_name.lower():
                return "claude-opus"
            elif "haiku" in model_name.lower():
                return "claude-haiku"
            return "claude"
        elif "gpt-4o" in model_name.lower():
            return "gpt4o-mini" if "mini" in model_name else "gpt4o"
        elif "o1" in model_name.lower():
            return "o1-mini" if "mini" in model_name else "o1"
        
        return model_name.split("/")[-1][:10] if "/" in model_name else model_name[:10]
    
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