"""
Dashboard Integration Hooks

Provides hooks for integrating proxy request/response flow with the terminal dashboard.
"""

from typing import Dict, Any, Optional
from src.core.config import config
import time
import asyncio


class DashboardHooks:
    """Hooks for feeding data to dashboard and prompt injection system"""

    def __init__(self):
        self.enabled = False
        self.terminal_dashboard = None
        self.websocket_enabled = False
        self.request_stats = {
            'total_requests': 0,
            'today_requests': 0,
            'total_cost': 0.0,
            'today_cost': 0.0,
            'avg_latency_ms': 0,
            'min_latency_ms': 0,
            'max_latency_ms': 0,
            'avg_tokens_per_sec': 0,
            'max_tokens_per_sec': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_thinking_tokens': 0,
            'avg_input_tokens': 0,
            'avg_output_tokens': 0,
            'avg_thinking_tokens': 0,
            'avg_context_tokens': 0,
            'avg_context_limit': 0,
            'avg_cost_per_request': 0.0,
            'success_count': 0,
            'error_count': 0,
            'error_types': {},
            'recent_errors': [],
            'top_models': [],
            'usage_by_type': {
                'text_only': 0,
                'with_tools': 0,
                'with_images': 0
            },
            'free_savings': 0.0
        }
        self.latency_samples = []
        self.tokens_per_sec_samples = []
        self.model_usage = {}

    def enable(self):
        """Enable dashboard hooks"""
        if config.enable_dashboard:
            try:
                from src.dashboard.terminal_dashboard import terminal_dashboard
                self.terminal_dashboard = terminal_dashboard
                self.enabled = True
            except ImportError:
                pass

        # Always try to enable WebSocket broadcasting
        try:
            from src.api.websocket_dashboard import dashboard_broadcaster
            self.websocket_enabled = True
        except ImportError:
            pass

    def _broadcast_websocket(self, message_type: str, data: Dict[str, Any]):
        """Broadcast message via WebSocket if enabled"""
        if not self.websocket_enabled:
            return

        try:
            from src.api.websocket_dashboard import broadcast_dashboard_update
            # Create async task to broadcast
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(broadcast_dashboard_update(message_type, data))
        except Exception:
            pass

    def on_request_start(self, request_id: str, request_data: Dict[str, Any]):
        """Called when a request starts"""
        # Terminal dashboard update
        if self.enabled and self.terminal_dashboard:
            try:
                self.terminal_dashboard.waterfall.add_request(request_id, request_data)
                self.terminal_dashboard.update()
            except Exception:
                pass

        # WebSocket broadcast
        self._broadcast_websocket('request_start', {
            'request_id': request_id,
            **request_data
        })

    def on_request_phase(self, request_id: str, phase: str):
        """Called when a request enters a new phase"""
        if not self.enabled or not self.terminal_dashboard:
            return

        try:
            self.terminal_dashboard.waterfall.update_phase(request_id, phase)
            self.terminal_dashboard.update()
        except Exception:
            pass

    def on_request_complete(self, request_id: str, status: str, data: Dict[str, Any]):
        """Called when a request completes (success or error)"""
        if not self.enabled:
            return

        # Update stats
        self.request_stats['total_requests'] += 1

        if status == 'completed':
            self.request_stats['success_count'] += 1
        else:
            self.request_stats['error_count'] += 1

            # Track error types
            error_type = data.get('error_type', 'Unknown')
            self.request_stats['error_types'][error_type] = \
                self.request_stats['error_types'].get(error_type, 0) + 1

            # Add to recent errors (keep last 10)
            self.request_stats['recent_errors'].append({
                'time': time.strftime('%H:%M'),
                'type': error_type,
                'message': data.get('error', '')[:50],
                'model': data.get('model', '')
            })
            if len(self.request_stats['recent_errors']) > 10:
                self.request_stats['recent_errors'].pop(0)

        # Track latency
        if 'duration_ms' in data:
            duration = data['duration_ms']
            self.latency_samples.append(duration)
            if len(self.latency_samples) > 100:
                self.latency_samples.pop(0)

            self.request_stats['avg_latency_ms'] = int(
                sum(self.latency_samples) / len(self.latency_samples)
            )
            self.request_stats['min_latency_ms'] = min(self.latency_samples)
            self.request_stats['max_latency_ms'] = max(self.latency_samples)

        # Track tokens
        if 'input_tokens' in data:
            self.request_stats['total_input_tokens'] += data['input_tokens']
        if 'output_tokens' in data:
            self.request_stats['total_output_tokens'] += data['output_tokens']
        if 'thinking_tokens' in data:
            self.request_stats['total_thinking_tokens'] += data['thinking_tokens']

        # Track cost
        if 'cost' in data:
            self.request_stats['total_cost'] += data['cost']

        # Track tokens per second
        if 'tokens_per_sec' in data:
            tps = data['tokens_per_sec']
            self.tokens_per_sec_samples.append(tps)
            if len(self.tokens_per_sec_samples) > 100:
                self.tokens_per_sec_samples.pop(0)

            self.request_stats['avg_tokens_per_sec'] = int(
                sum(self.tokens_per_sec_samples) / len(self.tokens_per_sec_samples)
            )
            self.request_stats['max_tokens_per_sec'] = max(self.tokens_per_sec_samples)

        # Track model usage
        model = data.get('model', 'unknown')
        if model not in self.model_usage:
            self.model_usage[model] = {
                'requests': 0,
                'tokens': 0,
                'cost': 0.0
            }

        self.model_usage[model]['requests'] += 1
        if 'input_tokens' in data and 'output_tokens' in data:
            self.model_usage[model]['tokens'] += data['input_tokens'] + data['output_tokens']
        if 'cost' in data:
            self.model_usage[model]['cost'] += data['cost']

        # Update top models
        top_models = sorted(
            self.model_usage.items(),
            key=lambda x: x[1]['requests'],
            reverse=True
        )[:5]

        self.request_stats['top_models'] = [
            {
                'name': model,
                'requests': stats['requests'],
                'tokens': stats['tokens'],
                'cost': stats['cost']
            }
            for model, stats in top_models
        ]

        # Track usage by type
        if data.get('has_tools'):
            self.request_stats['usage_by_type']['with_tools'] += 1
        elif data.get('has_images'):
            self.request_stats['usage_by_type']['with_images'] += 1
        else:
            self.request_stats['usage_by_type']['text_only'] += 1

        # Calculate averages
        if self.request_stats['total_requests'] > 0:
            self.request_stats['avg_input_tokens'] = int(
                self.request_stats['total_input_tokens'] / self.request_stats['total_requests']
            )
            self.request_stats['avg_output_tokens'] = int(
                self.request_stats['total_output_tokens'] / self.request_stats['total_requests']
            )
            self.request_stats['avg_thinking_tokens'] = int(
                self.request_stats['total_thinking_tokens'] / self.request_stats['total_requests']
            )
            self.request_stats['avg_cost_per_request'] = (
                self.request_stats['total_cost'] / self.request_stats['total_requests']
            )

        # Update terminal dashboard
        if self.terminal_dashboard:
            try:
                self.terminal_dashboard.waterfall.complete_request(request_id, status, data)

                # Update modules with latest stats
                self.terminal_dashboard.update_module('performance', {
                    'total_requests': self.request_stats['total_requests'],
                    'today_requests': self.request_stats['today_requests'],
                    'avg_latency_ms': self.request_stats['avg_latency_ms'],
                    'min_latency_ms': self.request_stats['min_latency_ms'],
                    'max_latency_ms': self.request_stats['max_latency_ms'],
                    'avg_tokens_per_sec': self.request_stats['avg_tokens_per_sec'],
                    'max_tokens_per_sec': self.request_stats['max_tokens_per_sec'],
                    'total_input_tokens': self.request_stats['total_input_tokens'],
                    'total_output_tokens': self.request_stats['total_output_tokens'],
                    'total_thinking_tokens': self.request_stats['total_thinking_tokens'],
                    'avg_input_tokens': self.request_stats['avg_input_tokens'],
                    'avg_output_tokens': self.request_stats['avg_output_tokens'],
                    'avg_thinking_tokens': self.request_stats['avg_thinking_tokens'],
                    'avg_context_tokens': data.get('context_tokens', 0),
                    'avg_context_limit': data.get('context_limit', 0),
                    'total_cost': self.request_stats['total_cost'],
                    'today_cost': self.request_stats['today_cost'],
                    'avg_cost_per_request': self.request_stats['avg_cost_per_request'],
                    'success_rate': (
                        self.request_stats['success_count'] / self.request_stats['total_requests'] * 100
                        if self.request_stats['total_requests'] > 0 else 100
                    )
                })

                self.terminal_dashboard.update_module('routing', {
                    'provider': self._get_provider_name(config.openai_base_url),
                    'base_url': config.openai_base_url,
                    'big_model': config.big_model,
                    'middle_model': config.middle_model,
                    'small_model': config.small_model,
                    'passthrough_mode': config.passthrough_mode,
                    'reasoning_effort': config.reasoning_effort or 'none',
                    'reasoning_max_tokens': config.reasoning_max_tokens
                })

                self.terminal_dashboard.update_module('activity', {
                    'request': {
                        'status': status,
                        'model': data.get('model', ''),
                        'duration_ms': data.get('duration_ms', 0)
                    }
                })

                self.terminal_dashboard.update_module('models', {
                    'top_models': self.request_stats['top_models'],
                    'usage_by_type': self.request_stats['usage_by_type']
                })

                self.terminal_dashboard.update()
            except Exception:
                pass

        # WebSocket broadcast: request complete
        self._broadcast_websocket('request_complete' if status == 'completed' else 'request_error', {
            'request_id': request_id,
            'status': status,
            **data
        })

        # WebSocket broadcast: stats update
        self._broadcast_websocket('stats_update', self.request_stats)

        # Update prompt injection middleware
        try:
            from src.utils.prompt_injection_middleware import update_proxy_status

            # Calculate success rate
            total_count = self.request_stats['success_count'] + self.request_stats['error_count']
            success_count = self.request_stats['success_count']

            update_proxy_status({
                'status': {
                    'passthrough_mode': config.passthrough_mode,
                    'provider': self._get_provider_name(config.openai_base_url),
                    'base_url': config.openai_base_url,
                    'big_model': config.big_model,
                    'middle_model': config.middle_model,
                    'small_model': config.small_model,
                    'reasoning_effort': config.reasoning_effort or 'none',
                    'reasoning_max_tokens': config.reasoning_max_tokens,
                    'track_usage': config.track_usage,
                    'compact_logger': config.compact_logger
                },
                'performance': self.request_stats,
                'errors': {
                    'success_count': success_count,
                    'total_count': total_count,
                    'error_types': self.request_stats['error_types'],
                    'recent_errors': self.request_stats['recent_errors']
                },
                'models': {
                    'top_models': self.request_stats['top_models'],
                    'usage_by_type': self.request_stats['usage_by_type'],
                    'recommendations': [],
                    'free_savings': self.request_stats['free_savings']
                }
            })
        except ImportError:
            pass

    def _get_provider_name(self, base_url: str) -> str:
        """Extract provider name from base URL"""
        if 'openrouter' in base_url.lower():
            return 'OpenRouter'
        elif 'azure' in base_url.lower():
            return 'Azure'
        elif 'anthropic' in base_url.lower():
            return 'Anthropic'
        elif 'openai' in base_url.lower():
            return 'OpenAI'
        else:
            return 'Custom'

    def get_stats(self) -> Dict[str, Any]:
        """Get current stats snapshot"""
        return self.request_stats.copy()


# Global dashboard hooks instance
dashboard_hooks = DashboardHooks()
