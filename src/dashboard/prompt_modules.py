"""
Prompt Dashboard Modules

Renders dashboard data for injection into Claude Code prompts.
Supports multiple size variants (large, medium, small) with Nerd Fonts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from src.dashboard.dashboard_hooks import dashboard_hooks


class PromptDashboardModule:
    """Base class for prompt-injectable dashboard modules"""

    def __init__(self, name: str):
        self.name = name

    def render_large(self, stats: Dict[str, Any]) -> str:
        """Multi-line detailed format (~200-300 chars)"""
        raise NotImplementedError

    def render_medium(self, stats: Dict[str, Any]) -> str:
        """Single-line compact format (~80-120 chars)"""
        raise NotImplementedError

    def render_small(self, stats: Dict[str, Any]) -> str:
        """Ultra-compact inline format (~30-50 chars)"""
        raise NotImplementedError


class ProxyStatusPromptModule(PromptDashboardModule):
    """Proxy status and configuration for prompts"""

    def render_large(self, stats: Dict[str, Any]) -> str:
        from src.core.config import config

        provider = self._get_provider_name(config.openai_base_url)

        return f"""┌─ 🔧 Proxy Status ─────────────────────────────────────┐
│ Provider: {provider:12} │ Mode: {'Passthrough' if config.passthrough_mode else 'Proxy'}              │
│ BIG:    {config.big_model[:28]:28} │
│ MIDDLE: {config.middle_model[:28]:28} │
│ SMALL:  {config.small_model[:28]:28} │
│ Reasoning: {(config.reasoning_effort or 'none')[:10]:10} │ Max Tokens: {str(config.reasoning_max_tokens or 'auto')[:8]:8} │
└────────────────────────────────────────────────────────┘"""

    def render_medium(self, stats: Dict[str, Any]) -> str:
        from src.core.config import config

        provider = self._get_provider_name(config.openai_base_url)
        big_short = config.big_model.split('/')[-1][:12]
        reasoning = config.reasoning_effort or 'none'

        return f"🔧 {provider} | 🤖 {big_short} | 🧠 {reasoning} | {'🔓' if config.passthrough_mode else '🔒'}"

    def render_small(self, stats: Dict[str, Any]) -> str:
        from src.core.config import config

        provider_icon = '🌐' if 'openrouter' in config.openai_base_url.lower() else '🔧'
        reasoning_icon = '🧠' if config.reasoning_effort else '💭'

        return f"{provider_icon}{reasoning_icon}"

    def _get_provider_name(self, url: str) -> str:
        if 'openrouter' in url.lower():
            return 'OpenRouter'
        elif 'openai' in url.lower():
            return 'OpenAI'
        elif 'anthropic' in url.lower():
            return 'Anthropic'
        return 'Custom'


class PerformancePromptModule(PromptDashboardModule):
    """Performance metrics for prompts"""

    def render_large(self, stats: Dict[str, Any]) -> str:
        total_req = stats.get('total_requests', 0)
        avg_lat = stats.get('avg_latency_ms', 0)
        tps = stats.get('avg_tokens_per_sec', 0)
        cost = stats.get('total_cost', 0.0)
        success_rate = stats.get('success_count', 0) / max(total_req, 1) * 100

        return f"""┌─ ⚡ Performance ──────────────────────────────────────┐
│ Requests: {total_req:5} │ Success: {success_rate:5.1f}%             │
│ Latency:  {avg_lat:5.0f}ms │ Speed: {tps:5.0f} tok/s          │
│ Cost:     ${cost:7.3f} │ Avg/req: ${cost/max(total_req, 1):6.4f}     │
│ Tokens: ↑{stats.get('total_input_tokens', 0):7,} ↓{stats.get('total_output_tokens', 0):7,}           │
└────────────────────────────────────────────────────────┘"""

    def render_medium(self, stats: Dict[str, Any]) -> str:
        total_req = stats.get('total_requests', 0)
        avg_lat = stats.get('avg_latency_ms', 0)
        tps = stats.get('avg_tokens_per_sec', 0)
        cost = stats.get('total_cost', 0.0)

        return f"⚡ {total_req}req | {avg_lat:.0f}ms | {tps:.0f}t/s | ${cost:.3f}"

    def render_small(self, stats: Dict[str, Any]) -> str:
        total_req = stats.get('total_requests', 0)
        tps = stats.get('avg_tokens_per_sec', 0)

        return f"⚡{total_req}r·{tps:.0f}t/s"


class ErrorTrackingPromptModule(PromptDashboardModule):
    """Error tracking and reliability for prompts"""

    def render_large(self, stats: Dict[str, Any]) -> str:
        success = stats.get('success_count', 0)
        errors = stats.get('error_count', 0)
        total = success + errors
        success_rate = (success / max(total, 1)) * 100

        error_types = stats.get('error_types', {})
        top_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]

        error_lines = []
        for err_type, count in top_errors:
            error_lines.append(f"  • {err_type[:20]:20} {count:3}x")

        error_display = '\n'.join(error_lines) if error_lines else "  • No errors yet! ✓"

        return f"""┌─ ⚠️  Error Tracking ──────────────────────────────────┐
│ Success: {success:5} ({success_rate:5.1f}%) │ Errors: {errors:5}       │
│ {error_display:50} │
└────────────────────────────────────────────────────────┘"""

    def render_medium(self, stats: Dict[str, Any]) -> str:
        success = stats.get('success_count', 0)
        errors = stats.get('error_count', 0)
        total = success + errors
        success_rate = (success / max(total, 1)) * 100

        status_icon = '✓' if success_rate >= 95 else '⚠️' if success_rate >= 80 else '❌'

        return f"{status_icon} {success}/{total} OK ({success_rate:.1f}%) | {errors} ERR"

    def render_small(self, stats: Dict[str, Any]) -> str:
        success = stats.get('success_count', 0)
        errors = stats.get('error_count', 0)
        total = success + errors
        success_rate = (success / max(total, 1)) * 100

        return f"{'✓' if success_rate >= 95 else '⚠️'}{success_rate:.0f}%"


class ModelUsagePromptModule(PromptDashboardModule):
    """Model usage statistics for prompts"""

    def render_large(self, stats: Dict[str, Any]) -> str:
        top_models = stats.get('top_models', [])[:5]

        model_lines = []
        for i, model in enumerate(top_models, 1):
            name = model['name'].split('/')[-1][:24]
            requests = model['requests']
            cost = model.get('cost', 0.0)
            model_lines.append(f"  {i}. {name:24} {requests:3}req ${cost:6.3f}")

        model_display = '\n'.join(model_lines) if model_lines else "  No data yet"

        return f"""┌─ 🤖 Model Usage ──────────────────────────────────────┐
│ {model_display:50} │
└────────────────────────────────────────────────────────┘"""

    def render_medium(self, stats: Dict[str, Any]) -> str:
        top_models = stats.get('top_models', [])[:3]

        if not top_models:
            return "🤖 No model data"

        models_str = ' | '.join([
            f"{m['name'].split('/')[-1][:12]}:{m['requests']}"
            for m in top_models
        ])

        return f"🤖 {models_str}"

    def render_small(self, stats: Dict[str, Any]) -> str:
        top_models = stats.get('top_models', [])

        if not top_models:
            return "🤖-"

        top_model = top_models[0]['name'].split('/')[-1][:8]
        return f"🤖{top_model}"


class PromptDashboardRenderer:
    """Renders dashboard modules for Claude Code prompt injection"""

    def __init__(self):
        self.modules = {
            'status': ProxyStatusPromptModule('status'),
            'performance': PerformancePromptModule('performance'),
            'errors': ErrorTrackingPromptModule('errors'),
            'models': ModelUsagePromptModule('models')
        }

    def render(
        self,
        modules: List[str],
        size: str = 'medium',
        stats: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render selected modules at specified size.

        Args:
            modules: List of module names to render
            size: 'large', 'medium', or 'small'
            stats: Statistics dict (uses live data if None)

        Returns:
            Rendered prompt text
        """
        if stats is None:
            stats = dashboard_hooks.get_stats()

        render_method = f'render_{size}'
        outputs = []

        for module_name in modules:
            if module_name not in self.modules:
                continue

            module = self.modules[module_name]
            if not hasattr(module, render_method):
                continue

            try:
                output = getattr(module, render_method)(stats)
                outputs.append(output)
            except Exception as e:
                # Silently skip errors
                pass

        if not outputs:
            return ""

        # Join with appropriate separator based on size
        if size == 'large':
            separator = '\n\n'
        elif size == 'medium':
            separator = '\n'
        else:  # small
            separator = ' '

        return separator.join(outputs)

    def render_header(
        self,
        modules: List[str],
        size: str = 'medium',
        stats: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render as compact header (single line regardless of size).

        Uses small rendering for all modules and joins horizontally.
        """
        if stats is None:
            stats = dashboard_hooks.get_stats()

        outputs = []

        for module_name in modules:
            if module_name not in self.modules:
                continue

            module = self.modules[module_name]

            try:
                output = module.render_small(stats)
                outputs.append(output)
            except Exception:
                pass

        return ' '.join(outputs) if outputs else ""

    def get_available_modules(self) -> List[str]:
        """Get list of available module names"""
        return list(self.modules.keys())


# Global renderer instance
prompt_dashboard_renderer = PromptDashboardRenderer()
