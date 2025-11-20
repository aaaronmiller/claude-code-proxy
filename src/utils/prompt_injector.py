"""
Prompt-Injectable Dashboard Modules

These modules format proxy state information that can be injected into
Claude Code's system prompt to give it awareness of:
- Current routing configuration
- Performance metrics
- Token usage patterns
- Cost tracking
- Recent errors

Formats:
- EXPANDED: Multi-line detailed format (10-20 lines)
- SINGLE: One-line compact format (1 line)
- MINI: Ultra-compact partial line (20-40 chars)
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class PromptDashboardModule:
    """Base class for prompt-injectable dashboard modules"""

    def __init__(self):
        self.last_update = time.time()
        self.data = {}

    def update(self, data: Dict[str, Any]):
        """Update module data"""
        self.data = data
        self.last_update = time.time()

    def render_expanded(self) -> str:
        """Multi-line detailed format (10-20 lines)"""
        raise NotImplementedError

    def render_single(self) -> str:
        """Single-line compact format"""
        raise NotImplementedError

    def render_mini(self) -> str:
        """Ultra-compact partial line (20-40 chars)"""
        raise NotImplementedError


class ProxyStatusModule(PromptDashboardModule):
    """Proxy status and routing configuration"""

    def render_expanded(self) -> str:
        """
        Example output:
        ╔═══════════════════════════════════════════════════════════╗
        ║ PROXY STATUS & ROUTING                                    ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Mode: Proxy (server key) / Passthrough (user keys)        ║
        ║ Provider: OpenRouter (https://openrouter.ai/api/v1)       ║
        ║ Routing:                                                  ║
        ║   • BIG (Opus)    → openai/gpt-4o                         ║
        ║   • MIDDLE (Sonnet) → openai/gpt-4o                       ║
        ║   • SMALL (Haiku)  → gpt-4o-mini                          ║
        ║ Reasoning: High effort, 8000 max tokens                   ║
        ║ Features: Usage tracking ✓ | Compact logger ✗            ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        mode = self.data.get('passthrough_mode', False)
        provider = self.data.get('provider', 'Unknown')
        base_url = self.data.get('base_url', '')
        big = self.data.get('big_model', '')
        middle = self.data.get('middle_model', '')
        small = self.data.get('small_model', '')
        reasoning = self.data.get('reasoning_effort', '')
        reasoning_tokens = self.data.get('reasoning_max_tokens', '')
        track_usage = self.data.get('track_usage', False)
        compact_log = self.data.get('compact_logger', False)

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║ PROXY STATUS & ROUTING                                    ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Mode: {'Passthrough (user keys)' if mode else 'Proxy (server key)':51}║",
            f"║ Provider: {provider:48}║",
            f"║ Base URL: {base_url[:45]:48}║",
            "║ Routing:                                                  ║",
            f"║   • BIG (Opus)      → {big[:38]:38} ║",
            f"║   • MIDDLE (Sonnet) → {middle[:38]:38} ║",
            f"║   • SMALL (Haiku)   → {small[:38]:38} ║",
        ]

        if reasoning or reasoning_tokens:
            reasoning_str = f"{reasoning or 'N/A'}"
            if reasoning_tokens:
                reasoning_str += f", {reasoning_tokens} max tokens"
            lines.append(f"║ Reasoning: {reasoning_str[:45]:48}║")

        features = []
        if track_usage:
            features.append("Usage tracking ✓")
        else:
            features.append("Usage tracking ✗")

        if compact_log:
            features.append("Compact logger ✓")
        else:
            features.append("Compact logger ✗")

        lines.append(f"║ Features: {' | '.join(features)[:45]:48}║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    def render_single(self) -> str:
        """
        Example: [Proxy] OpenRouter: O→gpt-4o M→gpt-4o S→gpt-4o-mini | R:high/8k | Track✓ Log✗
        """
        mode = "Pass" if self.data.get('passthrough_mode') else "Proxy"
        provider = self.data.get('provider', 'Unknown')
        big = self.data.get('big_model', '')[:15]
        middle = self.data.get('middle_model', '')[:15]
        small = self.data.get('small_model', '')[:15]
        reasoning = self.data.get('reasoning_effort', 'N/A')
        tokens = self.data.get('reasoning_max_tokens', '')
        track = "✓" if self.data.get('track_usage') else "✗"
        log = "✓" if self.data.get('compact_logger') else "✗"

        r_str = f"{reasoning}/{tokens}" if tokens else reasoning

        return f"[{mode}] {provider}: O→{big} M→{middle} S→{small} | R:{r_str} | Track{track} Log{log}"

    def render_mini(self) -> str:
        """
        Example: Proxy|OR|gpt4o|high
        """
        mode = "P" if self.data.get('passthrough_mode') else "S"
        provider_map = {
            'OpenRouter': 'OR',
            'OpenAI': 'OAI',
            'Azure': 'AZ',
            'Anthropic': 'ANT',
            'Ollama': 'OL'
        }
        provider = provider_map.get(self.data.get('provider', ''), 'XX')
        model = self.data.get('big_model', '')[:8]
        reasoning = (self.data.get('reasoning_effort', '') or 'N')[:1]

        return f"{mode}|{provider}|{model}|{reasoning}"


class PerformanceModule(PromptDashboardModule):
    """Performance metrics and token usage"""

    def render_expanded(self) -> str:
        """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ PERFORMANCE METRICS (Last 10 Requests)                    ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Requests: 847 total (94 today)                            ║
        ║ Latency:  3,421ms avg | 1,234ms min | 8,765ms max        ║
        ║ Speed:    78 tok/s avg | 234 tok/s max                    ║
        ║ Tokens:                                                   ║
        ║   • Input:    2,145,678 (avg: 2,534/req)                 ║
        ║   • Output:     456,789 (avg: 539/req)                   ║
        ║   • Thinking:    12,345 (avg: 15/req)                    ║
        ║ Context: 43.7k/200k avg (22% utilization)                ║
        ║ Cost: $12.34 total | $2.47 today | $0.015 avg/req        ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        total_req = self.data.get('total_requests', 0)
        today_req = self.data.get('today_requests', 0)
        avg_lat = self.data.get('avg_latency_ms', 0)
        min_lat = self.data.get('min_latency_ms', 0)
        max_lat = self.data.get('max_latency_ms', 0)
        avg_speed = self.data.get('avg_tokens_per_sec', 0)
        max_speed = self.data.get('max_tokens_per_sec', 0)
        input_tok = self.data.get('total_input_tokens', 0)
        output_tok = self.data.get('total_output_tokens', 0)
        think_tok = self.data.get('total_thinking_tokens', 0)
        avg_input = self.data.get('avg_input_tokens', 0)
        avg_output = self.data.get('avg_output_tokens', 0)
        avg_think = self.data.get('avg_thinking_tokens', 0)
        avg_ctx = self.data.get('avg_context_tokens', 0)
        ctx_limit = self.data.get('avg_context_limit', 200000)
        ctx_pct = int((avg_ctx / ctx_limit * 100)) if ctx_limit else 0
        total_cost = self.data.get('total_cost', 0)
        today_cost = self.data.get('today_cost', 0)
        avg_cost = self.data.get('avg_cost_per_request', 0)

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║ PERFORMANCE METRICS (Last 10 Requests)                    ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Requests: {total_req:,} total ({today_req} today){' ' * (24 - len(str(total_req)) - len(str(today_req)))}║",
            f"║ Latency:  {avg_lat:,}ms avg | {min_lat:,}ms min | {max_lat:,}ms max{' ' * (11 - len(f'{avg_lat:,}') - len(f'{min_lat:,}') - len(f'{max_lat:,}'))}║",
            f"║ Speed:    {avg_speed} tok/s avg | {max_speed} tok/s max{' ' * (19 - len(str(avg_speed)) - len(str(max_speed)))}║",
            "║ Tokens:                                                   ║",
            f"║   • Input:    {input_tok:,} (avg: {avg_input:,}/req){' ' * (21 - len(f'{input_tok:,}') - len(f'{avg_input:,}'))}║",
            f"║   • Output:   {output_tok:,} (avg: {avg_output:,}/req){' ' * (20 - len(f'{output_tok:,}') - len(f'{avg_output:,}'))}║",
            f"║   • Thinking: {think_tok:,} (avg: {avg_think:,}/req){' ' * (18 - len(f'{think_tok:,}') - len(f'{avg_think:,}'))}║",
            f"║ Context: {avg_ctx/1000:.1f}k/{ctx_limit/1000:.0f}k avg ({ctx_pct}% utilization){' ' * (15 - len(str(ctx_pct)))}║",
            f"║ Cost: ${total_cost:.2f} total | ${today_cost:.2f} today | ${avg_cost:.4f} avg/req{' ' * (5 - len(f'{avg_cost:.4f}'))}║",
            "╚═══════════════════════════════════════════════════════════╝"
        ]

        return "\n".join(lines)

    def render_single(self) -> str:
        """
        Example: Perf: 847req 3.4s⌀ 78t/s | Tok: 2.1M→456k💭12k | Ctx:44k/200k(22%) | Cost:$12.34
        """
        total_req = self.data.get('total_requests', 0)
        avg_lat = self.data.get('avg_latency_ms', 0) / 1000
        avg_speed = self.data.get('avg_tokens_per_sec', 0)
        input_tok = self.data.get('total_input_tokens', 0)
        output_tok = self.data.get('total_output_tokens', 0)
        think_tok = self.data.get('total_thinking_tokens', 0)
        avg_ctx = self.data.get('avg_context_tokens', 0)
        ctx_limit = self.data.get('avg_context_limit', 200000)
        ctx_pct = int((avg_ctx / ctx_limit * 100)) if ctx_limit else 0
        total_cost = self.data.get('total_cost', 0)

        return (f"Perf: {total_req}req {avg_lat:.1f}s⌀ {avg_speed}t/s | "
                f"Tok: {input_tok/1000:.1f}k→{output_tok/1000:.1f}k💭{think_tok/1000:.1f}k | "
                f"Ctx:{avg_ctx/1000:.0f}k/{ctx_limit/1000:.0f}k({ctx_pct}%) | "
                f"Cost:${total_cost:.2f}")

    def render_mini(self) -> str:
        """
        Example: 847r|3.4s|78t/s|$12
        """
        total_req = self.data.get('total_requests', 0)
        avg_lat = self.data.get('avg_latency_ms', 0) / 1000
        avg_speed = self.data.get('avg_tokens_per_sec', 0)
        total_cost = self.data.get('total_cost', 0)

        return f"{total_req}r|{avg_lat:.1f}s|{avg_speed}t/s|${total_cost:.0f}"


class ErrorTrackerModule(PromptDashboardModule):
    """Error tracking and recent issues"""

    def render_expanded(self) -> str:
        """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ ERROR TRACKING (Last 24 Hours)                            ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Success Rate: 98.7% (847/859 requests)                    ║
        ║ Errors: 12 total                                          ║
        ║   • Rate Limit:     7 (58%)                               ║
        ║   • Invalid Key:    3 (25%)                               ║
        ║   • Model Not Found: 2 (17%)                              ║
        ║                                                           ║
        ║ Recent Errors:                                            ║
        ║   [14:23] Rate limit exceeded (openai/gpt-4o)             ║
        ║   [14:18] Invalid API key (anthropic/claude-3.5-sonnet)   ║
        ║   [14:05] Model not found (fake/model-123)                ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        success_count = self.data.get('success_count', 0)
        total_count = self.data.get('total_count', 0)
        error_count = total_count - success_count
        success_rate = (success_count / total_count * 100) if total_count else 100
        error_types = self.data.get('error_types', {})
        recent_errors = self.data.get('recent_errors', [])

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║ ERROR TRACKING (Last 24 Hours)                            ║",
            "╠═══════════════════════════════════════════════════════════╣",
            f"║ Success Rate: {success_rate:.1f}% ({success_count}/{total_count} requests){' ' * (17 - len(str(success_count)) - len(str(total_count)))}║",
            f"║ Errors: {error_count} total{' ' * (43 - len(str(error_count)))}║"
        ]

        # Add error breakdown
        if error_types:
            for error_type, count in sorted(error_types.items(), key=lambda x: -x[1])[:3]:
                pct = int((count / error_count * 100)) if error_count else 0
                lines.append(f"║   • {error_type[:20]:20} {count:3} ({pct}%){' ' * (14 - len(str(count)) - len(str(pct)))}║")

        lines.append("║                                                           ║")
        lines.append("║ Recent Errors:                                            ║")

        # Add recent errors
        for error in recent_errors[:3]:
            timestamp = error.get('time', '')[:5]  # HH:MM
            message = error.get('message', '')[:44]
            model = error.get('model', '')
            if model:
                message = f"{message[:30]} ({model[:10]})"
            lines.append(f"║   [{timestamp}] {message:48}║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    def render_single(self) -> str:
        """
        Example: Errors: 12/859 (98.7% OK) | RateLimit:7 InvalidKey:3 NotFound:2 | Last:[14:23]RateLimit
        """
        success_count = self.data.get('success_count', 0)
        total_count = self.data.get('total_count', 0)
        error_count = total_count - success_count
        success_rate = (success_count / total_count * 100) if total_count else 100
        error_types = self.data.get('error_types', {})
        recent_errors = self.data.get('recent_errors', [])

        error_str = " ".join([f"{k}:{v}" for k, v in sorted(error_types.items(), key=lambda x: -x[1])[:3]])

        last_error = ""
        if recent_errors:
            last = recent_errors[0]
            last_error = f" | Last:[{last.get('time', '')[:5]}]{last.get('type', '')}"

        return f"Errors: {error_count}/{total_count} ({success_rate:.1f}% OK) | {error_str}{last_error}"

    def render_mini(self) -> str:
        """
        Example: 12err|98.7%OK
        """
        success_count = self.data.get('success_count', 0)
        total_count = self.data.get('total_count', 0)
        error_count = total_count - success_count
        success_rate = (success_count / total_count * 100) if total_count else 100

        return f"{error_count}err|{success_rate:.1f}%OK"


class ModelUsageModule(PromptDashboardModule):
    """Model usage patterns and recommendations"""

    def render_expanded(self) -> str:
        """
        Example:
        ╔═══════════════════════════════════════════════════════════╗
        ║ MODEL USAGE PATTERNS (Last 7 Days)                        ║
        ╠═══════════════════════════════════════════════════════════╣
        ║ Top Models by Request Count:                              ║
        ║   #1  openai/gpt-4o           245 req  125.3k tok  $1.45  ║
        ║   #2  anthropic/claude-3.5... 89 req   52.1k tok   $0.89  ║
        ║   #3  ollama/qwen2.5:72b       34 req   18.9k tok   FREE  ║
        ║                                                           ║
        ║ Usage by Type:                                            ║
        ║   • Text-only:  312 req (82%)                             ║
        ║   • With tools:  45 req (12%)                             ║
        ║   • With images: 23 req (6%)                              ║
        ║                                                           ║
        ║ Recommendations:                                          ║
        ║   💡 34 requests to FREE model (saved $0.45)              ║
        ║   💡 Consider: qwen/qwen-2.5-thinking for reasoning tasks ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        top_models = self.data.get('top_models', [])
        usage_by_type = self.data.get('usage_by_type', {})
        recommendations = self.data.get('recommendations', [])

        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║ MODEL USAGE PATTERNS (Last 7 Days)                        ║",
            "╠═══════════════════════════════════════════════════════════╣",
            "║ Top Models by Request Count:                              ║"
        ]

        for i, model in enumerate(top_models[:3], 1):
            name = model.get('name', '')[:25]
            req = model.get('requests', 0)
            tok = model.get('tokens', 0) / 1000
            cost = model.get('cost', 0)
            cost_str = "FREE" if cost == 0 else f"${cost:.2f}"
            lines.append(f"║   #{i}  {name:25} {req:3} req  {tok:5.1f}k tok  {cost_str:5} ║")

        lines.append("║                                                           ║")
        lines.append("║ Usage by Type:                                            ║")

        text_only = usage_by_type.get('text_only', 0)
        with_tools = usage_by_type.get('with_tools', 0)
        with_images = usage_by_type.get('with_images', 0)
        total = text_only + with_tools + with_images
        if total:
            lines.append(f"║   • Text-only:  {text_only:3} req ({text_only/total*100:.0f}%){' ' * 29}║")
            lines.append(f"║   • With tools:  {with_tools:2} req ({with_tools/total*100:.0f}%){' ' * 30}║")
            lines.append(f"║   • With images: {with_images:2} req ({with_images/total*100:.0f}%){' ' * 29}║")

        if recommendations:
            lines.append("║                                                           ║")
            lines.append("║ Recommendations:                                          ║")
            for rec in recommendations[:2]:
                lines.append(f"║   💡 {rec[:53]:53}║")

        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    def render_single(self) -> str:
        """
        Example: Models: gpt-4o:245 claude:89 qwen:34 | Text:82% Tools:12% Img:6% | 34→FREE saved $0.45
        """
        top_models = self.data.get('top_models', [])
        usage_by_type = self.data.get('usage_by_type', {})

        model_str = " ".join([f"{m.get('name', '')[:8]}:{m.get('requests', 0)}" for m in top_models[:3]])

        text_only = usage_by_type.get('text_only', 0)
        with_tools = usage_by_type.get('with_tools', 0)
        with_images = usage_by_type.get('with_images', 0)
        total = text_only + with_tools + with_images

        type_str = ""
        if total:
            type_str = f" | Text:{text_only/total*100:.0f}% Tools:{with_tools/total*100:.0f}% Img:{with_images/total*100:.0f}%"

        free_count = sum(1 for m in top_models if m.get('cost', 0) == 0)
        savings = self.data.get('free_savings', 0)
        savings_str = f" | {free_count}→FREE saved ${savings:.2f}" if free_count else ""

        return f"Models: {model_str}{type_str}{savings_str}"

    def render_mini(self) -> str:
        """
        Example: gpt4o:245|34free
        """
        top_models = self.data.get('top_models', [])
        free_count = sum(1 for m in top_models if m.get('cost', 0) == 0)

        top_model = top_models[0] if top_models else {}
        name = top_model.get('name', '')[:8]
        req = top_model.get('requests', 0)

        return f"{name}:{req}|{free_count}free"


class PromptInjector:
    """Utility to inject dashboard modules into Claude Code prompts"""

    def __init__(self):
        self.modules = {
            'status': ProxyStatusModule(),
            'performance': PerformanceModule(),
            'errors': ErrorTrackerModule(),
            'models': ModelUsageModule()
        }

    def update_all(self, data: Dict[str, Dict[str, Any]]):
        """Update all modules with new data"""
        for module_name, module_data in data.items():
            if module_name in self.modules:
                self.modules[module_name].update(module_data)

    def generate_prompt_context(self,
                                format: str = 'single',
                                modules: Optional[List[str]] = None) -> str:
        """
        Generate prompt context to inject into Claude Code system prompt.

        Args:
            format: 'expanded', 'single', or 'mini'
            modules: List of module names to include (default: all)

        Returns:
            Formatted string ready for prompt injection
        """
        if modules is None:
            modules = list(self.modules.keys())

        lines = []
        lines.append("═" * 60)
        lines.append("PROXY STATUS INFORMATION")
        lines.append("(This information is from the Claude Code Proxy layer)")
        lines.append("═" * 60)
        lines.append("")

        for module_name in modules:
            if module_name not in self.modules:
                continue

            module = self.modules[module_name]

            if format == 'expanded':
                lines.append(module.render_expanded())
            elif format == 'single':
                lines.append(module.render_single())
            elif format == 'mini':
                lines.append(module.render_mini())

            if format in ['single', 'mini']:
                lines.append("")  # Blank line between modules

        lines.append("═" * 60)
        return "\n".join(lines)

    def generate_compact_header(self) -> str:
        """
        Generate ultra-compact header for every prompt.

        Example:
        [P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free
        """
        parts = [
            self.modules['status'].render_mini(),
            self.modules['performance'].render_mini(),
            self.modules['errors'].render_mini(),
            self.modules['models'].render_mini()
        ]
        return " | ".join(parts)


# Global instance for easy access
prompt_injector = PromptInjector()
