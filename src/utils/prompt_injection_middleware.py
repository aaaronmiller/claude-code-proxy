"""
Prompt Injection Middleware

Automatically injects proxy status into Claude Code prompts
based on configuration and request patterns.
"""

from typing import Dict, Any, Optional
from src.utils.prompt_injector import prompt_injector
from src.core.logging import logger


class PromptInjectionMiddleware:
    """Middleware to inject proxy status into requests"""

    def __init__(self):
        self.enabled = False
        self.format = 'single'  # 'expanded', 'single', 'mini'
        self.modules = ['status', 'performance', 'errors', 'models']
        self.inject_mode = 'auto'  # 'auto', 'always', 'never', 'compact_only'

    def configure(self,
                 enabled: bool = True,
                 format: str = 'single',
                 modules: list = None,
                 inject_mode: str = 'auto'):
        """Configure injection settings"""
        self.enabled = enabled
        self.format = format
        if modules:
            self.modules = modules
        self.inject_mode = inject_mode

    def should_inject(self, request: Dict[str, Any]) -> bool:
        """Determine if we should inject into this request"""
        if not self.enabled:
            return False

        if self.inject_mode == 'never':
            return False

        if self.inject_mode == 'always':
            return True

        if self.inject_mode == 'compact_only':
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

        # Generate injection content
        injection = prompt_injector.generate_prompt_context(
            format=self.format,
            modules=self.modules
        )

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
        logger.debug(f"Injected proxy status ({self.format} format) into request")

        return request

    def get_compact_header(self) -> str:
        """Get ultra-compact header for all requests"""
        return prompt_injector.generate_compact_header()

    def inject_into_system_prompt(self, system_prompt: str) -> str:
        """Inject into existing system prompt string"""
        if not self.enabled:
            return system_prompt

        injection = prompt_injector.generate_prompt_context(
            format=self.format,
            modules=self.modules
        )

        # Append to system prompt
        if system_prompt:
            return f"{system_prompt}\n\n{injection}"
        else:
            return injection


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
