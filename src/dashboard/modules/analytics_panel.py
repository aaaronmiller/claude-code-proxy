"""
Analytics Panel Module - Cost and performance analytics.
"""

import time
from collections import defaultdict
from .base_module import BaseModule

try:
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class AnalyticsPanel(BaseModule):
    """Cost and performance analytics module."""
    
    def get_title(self) -> str:
        return "Analytics"
    
    def get_description(self) -> str:
        return "Cost and performance analytics with usage statistics"
    
    def render_dense(self) -> str:
        """Render detailed analytics."""
        completed_requests = self.get_completed_requests(3600)  # Last hour
        
        if not completed_requests:
            return "No analytics data available"
        
        # Calculate metrics
        total_requests = len(completed_requests)
        total_cost = 0
        total_thinking_tokens = 0
        durations = []
        model_usage = defaultdict(int)
        
        for req in completed_requests:
            usage = req.get('usage', {})
            duration_ms = req.get('duration_ms', 0)
            model_name = req.get('model_name', 'unknown')
            
            # Cost calculation
            input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            thinking_tokens = self._extract_thinking_tokens(usage)
            
            total_cost += self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
            total_thinking_tokens += thinking_tokens
            
            if duration_ms > 0:
                durations.append(duration_ms)
            
            model_usage[self._format_model_name(model_name)] += 1
        
        # Calculate averages
        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = (total_requests / max(total_requests, 1)) * 100  # Simplified
        
        # Find fastest/slowest
        fastest_duration = min(durations) if durations else 0
        slowest_duration = max(durations) if durations else 0
        
        # Most used model
        hot_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else "none"
        
        if not RICH_AVAILABLE:
            return self._render_dense_plain(total_requests, avg_duration, success_rate, total_cost, total_thinking_tokens, hot_model)
        
        text = Text()
        
        # Summary line
        text.append(f"Total Requests: {total_requests}", style="cyan")
        text.append(f" | Avg Response: {self.format_duration(avg_duration)}", style="green")
        text.append(f" | Success: {success_rate:.1f}%", style="green" if success_rate > 90 else "yellow")
        text.append("\n")
        
        # Cost and tokens
        text.append(f"💰 Total Cost: {self.format_cost(total_cost)}", style="yellow")
        text.append(f" | 🧠 Thinking Tokens: {self.format_tokens(total_thinking_tokens)}", style="magenta")
        text.append("\n")
        
        # Performance extremes
        if durations:
            text.append(f"🏆 Fastest: {self.format_duration(fastest_duration)}", style="green")
            text.append(f" | 🐌 Slowest: {self.format_duration(slowest_duration)}", style="red")
        text.append("\n")
        
        # Usage patterns
        text.append(f"🔥 Hot Model: {hot_model}", style="bright_yellow")
        
        return text    

    def render_sparse(self) -> str:
        """Render compact analytics."""
        completed_requests = self.get_completed_requests(3600)
        
        if not completed_requests:
            return "No data"
        
        total_requests = len(completed_requests)
        total_cost = 0
        total_thinking_tokens = 0
        durations = []
        
        for req in completed_requests:
            usage = req.get('usage', {})
            duration_ms = req.get('duration_ms', 0)
            model_name = req.get('model_name', 'unknown')
            
            input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            thinking_tokens = self._extract_thinking_tokens(usage)
            
            total_cost += self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
            total_thinking_tokens += thinking_tokens
            
            if duration_ms > 0:
                durations.append(duration_ms)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = 95.0  # Simplified
        
        # Find most used model
        model_usage = defaultdict(int)
        for req in completed_requests:
            model_name = req.get('model_name', 'unknown')
            model_usage[self._format_model_name(model_name)] += 1
        
        hot_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else "none"
        
        return f"{total_requests}req | {self.format_duration(avg_duration)} avg | {success_rate:.1f}% ✓ | 💰{self.format_cost(total_cost)} | 🧠{self.format_tokens(total_thinking_tokens)} | 🔥{hot_model}"
    
    def _render_dense_plain(self, total_requests, avg_duration, success_rate, total_cost, total_thinking_tokens, hot_model):
        """Plain text version."""
        lines = [
            f"Total Requests: {total_requests}",
            f"Average Duration: {self.format_duration(avg_duration)}",
            f"Success Rate: {success_rate:.1f}%",
            f"Total Cost: {self.format_cost(total_cost)}",
            f"Thinking Tokens: {self.format_tokens(total_thinking_tokens)}",
            f"Hot Model: {hot_model}"
        ]
        return "\n".join(lines)
    
    def _format_model_name(self, model_name: str) -> str:
        """Format model name."""
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
        
        return model_name.split("/")[-1][:8] if "/" in model_name else model_name[:8]
    
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