"""
Prompt Injection Middleware

Automatically injects proxy status into Claude Code prompts
based on configuration and request patterns.
"""

from typing import Dict, Any, Optional
import os
from src.core.logging import logger


class PromptInjectionMiddleware:
    """Middleware to inject proxy status into requests"""

    def __init__(self):
        # Load configuration from environment
        self.enabled = os.getenv('PROMPT_INJECTION_ENABLED', 'false').lower() == 'true'
        self.size = os.getenv('PROMPT_INJECTION_SIZE', 'medium')  # 'large', 'medium', 'small'

        # Parse modules from env
        modules_str = os.getenv('PROMPT_INJECTION_MODULES', 'status,performance')
        self.modules = [m.strip() for m in modules_str.split(',') if m.strip()]

        self.inject_mode = os.getenv('PROMPT_INJECTION_MODE', 'auto')  # 'auto', 'always', 'manual', 'header'

    def configure(self,
                 enabled: bool = True,
                 size: str = 'medium',
                 modules: list = None,
                 inject_mode: str = 'auto'):
        """Configure injection settings"""
        self.enabled = enabled
        self.size = size
        if modules:
            self.modules = modules
        self.inject_mode = inject_mode

    def should_inject(self, request: Dict[str, Any]) -> bool:
        """Determine if we should inject into this request"""
        if not self.enabled:
            return False

        if self.inject_mode == 'manual':
            return False

        if self.inject_mode == 'always':
            return True

        if self.inject_mode == 'header':
            return False  # Only inject in headers

        # Auto mode: inject based on request characteristics
        messages = request.get('messages', [])
        if not messages:
            return False

        # Check if system message exists
        has_system = any(msg.get('role') == 'system' for msg in messages)

        # Inject if:
        # 1. No system message (we can add one)
        # 2. Request has tools (likely complex task)
        # 3. Request is streaming (long-running)
        has_tools = bool(request.get('tools'))
        is_streaming = request.get('stream', False)

        return has_system or has_tools or is_streaming

    def inject_into_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Inject proxy status into request messages"""
        if not self.should_inject(request):
            return request

        try:
            from src.dashboard.prompt_modules import prompt_dashboard_renderer

            # Generate injection content
            injection = prompt_dashboard_renderer.render(
                modules=self.modules,
                size=self.size
            )

            if not injection:
                return request

            # Add marker for user visibility
            injection = f"<!-- Proxy Status (auto-injected) -->\n{injection}"

            # Find or create system message
            messages = request.get('messages', [])
            system_idx = None

            for i, msg in enumerate(messages):
                if msg.get('role') == 'system':
                    system_idx = i
                    break

            if system_idx is not None:
                # Append to existing system message
                existing_content = messages[system_idx].get('content', '')
                messages[system_idx]['content'] = f"{existing_content}\n\n{injection}"
            else:
                # Prepend new system message
                messages.insert(0, {
                    'role': 'system',
                    'content': injection
                })

            request['messages'] = messages
            logger.debug(f"Injected proxy status ({self.size} size, {len(self.modules)} modules) into request")

        except Exception as e:
            logger.warning(f"Failed to inject proxy status: {e}")

        return request

    def get_compact_header(self) -> str:
        """Get ultra-compact header for all requests"""
        try:
            from src.dashboard.prompt_modules import prompt_dashboard_renderer

            return prompt_dashboard_renderer.render_header(
                modules=self.modules,
                size='small'
            )
        except Exception as e:
            logger.warning(f"Failed to generate compact header: {e}")
            return ""

    def inject_into_system_prompt(self, system_prompt: str) -> str:
        """Inject into existing system prompt string"""
        if not self.enabled:
            return system_prompt

        try:
            from src.dashboard.prompt_modules import prompt_dashboard_renderer

            injection = prompt_dashboard_renderer.render(
                modules=self.modules,
                size=self.size
            )

            if not injection:
                return system_prompt

            # Append to system prompt
            if system_prompt:
                return f"{system_prompt}\n\n<!-- Proxy Status -->\n{injection}"
            else:
                return f"<!-- Proxy Status -->\n{injection}"
        except Exception:
            return system_prompt


# Global middleware instance
prompt_injection_middleware = PromptInjectionMiddleware()


def update_proxy_status(status_data: Dict[str, Any]):
    """
    Update proxy status data for injection.

    Args:
        status_data: Dict with keys matching module names:
            {
                'status': {'passthrough_mode': False, 'provider': 'OpenRouter', ...},
                'performance': {'total_requests': 847, 'avg_latency_ms': 3421, ...},
                'errors': {'success_count': 847, 'total_count': 859, ...},
                'models': {'top_models': [...], 'usage_by_type': {...}, ...}
            }
    """
    prompt_injector.update_all(status_data)
