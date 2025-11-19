#!/usr/bin/env python3
"""
Demo script for prompt injection system.

Shows all three output formats with sample data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.prompt_injector import prompt_injector
from src.utils.prompt_injection_middleware import (
    prompt_injection_middleware,
    update_proxy_status
)


def generate_sample_data():
    """Generate sample proxy status data"""
    return {
        'status': {
            'passthrough_mode': False,
            'provider': 'OpenRouter',
            'base_url': 'https://openrouter.ai/api/v1',
            'big_model': 'openai/gpt-4o',
            'middle_model': 'openai/gpt-4o',
            'small_model': 'gpt-4o-mini',
            'reasoning_effort': 'high',
            'reasoning_max_tokens': '8000',
            'track_usage': True,
            'compact_logger': False
        },
        'performance': {
            'total_requests': 847,
            'today_requests': 94,
            'avg_latency_ms': 3421,
            'min_latency_ms': 1234,
            'max_latency_ms': 8765,
            'avg_tokens_per_sec': 78,
            'max_tokens_per_sec': 234,
            'total_input_tokens': 2145678,
            'total_output_tokens': 456789,
            'total_thinking_tokens': 12345,
            'avg_input_tokens': 2534,
            'avg_output_tokens': 539,
            'avg_thinking_tokens': 15,
            'avg_context_tokens': 43700,
            'avg_context_limit': 200000,
            'total_cost': 12.34,
            'today_cost': 2.47,
            'avg_cost_per_request': 0.015
        },
        'errors': {
            'success_count': 847,
            'total_count': 859,
            'error_types': {
                'Rate Limit': 7,
                'Invalid Key': 3,
                'Model Not Found': 2
            },
            'recent_errors': [
                {'time': '14:23', 'type': 'Rate Limit', 'message': 'Rate limit exceeded', 'model': 'openai/gpt-4o'},
                {'time': '14:18', 'type': 'Invalid Key', 'message': 'Invalid API key', 'model': 'anthropic/claude-3.5-sonnet'},
                {'time': '14:05', 'type': 'Model Not Found', 'message': 'Model not found', 'model': 'fake/model-123'}
            ]
        },
        'models': {
            'top_models': [
                {'name': 'openai/gpt-4o', 'requests': 245, 'tokens': 125300, 'cost': 1.45},
                {'name': 'anthropic/claude-3.5-sonnet', 'requests': 89, 'tokens': 52100, 'cost': 0.89},
                {'name': 'ollama/qwen2.5:72b', 'requests': 34, 'tokens': 18900, 'cost': 0}
            ],
            'usage_by_type': {
                'text_only': 312,
                'with_tools': 45,
                'with_images': 23
            },
            'recommendations': [
                '34 requests to FREE model (saved $0.45)',
                'Consider: qwen/qwen-2.5-thinking for reasoning tasks'
            ],
            'free_savings': 0.45
        }
    }


def demo_all_formats():
    """Demonstrate all output formats"""

    # Update with sample data
    data = generate_sample_data()
    update_proxy_status(data)

    print("=" * 80)
    print("PROMPT INJECTION DEMO - ALL FORMATS")
    print("=" * 80)
    print()

    # Format 1: EXPANDED
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 24 + "FORMAT 1: EXPANDED (Multi-line Detailed)" + " " * 14 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    expanded = prompt_injector.generate_prompt_context(format='expanded')
    print(expanded)
    print()
    print(f"Token cost: ~400-500 tokens")
    print(f"Use case: Complex tasks, debugging, full context needed")
    print()
    print()

    # Format 2: SINGLE
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 24 + "FORMAT 2: SINGLE (One-line Compact)" + " " * 19 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    single = prompt_injector.generate_prompt_context(format='single')
    print(single)
    print()
    print(f"Token cost: ~150-200 tokens")
    print(f"Use case: Standard tasks, balanced info/noise ratio")
    print()
    print()

    # Format 3: MINI
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 21 + "FORMAT 3: MINI (Ultra-compact Partial Line)" + " " * 13 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    mini = prompt_injector.generate_prompt_context(format='mini')
    print(mini)
    print()
    print(f"Token cost: ~50-80 tokens")
    print(f"Use case: Moderate visibility, compact format")
    print()
    print()

    # Format 4: COMPACT HEADER
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "FORMAT 4: COMPACT HEADER (Always-on Mode)" + " " * 17 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    header = prompt_injection_middleware.get_compact_header()
    print(f"[{header}]")
    print()
    print(f"Token cost: ~20-30 tokens")
    print(f"Use case: Every request, minimal overhead")
    print()
    print()


def demo_injection_strategies():
    """Demonstrate different injection strategies"""

    print("=" * 80)
    print("INJECTION STRATEGIES")
    print("=" * 80)
    print()

    # Strategy 1: Auto-inject
    print("┌─ Strategy 1: Auto-Inject ─────────────────────────────────────────┐")
    print("│ Automatically inject based on request characteristics             │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print()

    request = {
        'model': 'claude-3-5-sonnet-20241022',
        'messages': [
            {'role': 'user', 'content': 'Write a Python function to calculate fibonacci...'}
        ],
        'stream': True,
        'tools': [{'name': 'execute_code', 'description': 'Execute Python code'}]
    }

    prompt_injection_middleware.configure(
        enabled=True,
        format='single',
        inject_mode='auto'
    )

    modified = prompt_injection_middleware.inject_into_request(request)
    print("Original request has streaming and tools → Auto-inject ENABLED")
    print()
    print("Modified request messages:")
    for i, msg in enumerate(modified['messages']):
        print(f"  Message {i} ({msg['role']}): {msg['content'][:100]}...")
    print()
    print()

    # Strategy 2: Compact header
    print("┌─ Strategy 2: Compact Header Always ───────────────────────────────┐")
    print("│ Add compact header to every request (minimal tokens)              │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print()

    header = prompt_injection_middleware.get_compact_header()
    print(f"Compact header: [{header}]")
    print()
    print("Prepend to first user message:")
    print(f'  messages[0]["content"] = "[{header}]\\n\\n{{original_content}}"')
    print()
    print()

    # Strategy 3: System prompt injection
    print("┌─ Strategy 3: System Prompt Injection ─────────────────────────────┐")
    print("│ Inject into system prompt only                                    │")
    print("└────────────────────────────────────────────────────────────────────┘")
    print()

    system_prompt = "You are a helpful coding assistant. You write clean, efficient code."
    enhanced = prompt_injection_middleware.inject_into_system_prompt(system_prompt)
    print("Original system prompt:")
    print(f"  {system_prompt}")
    print()
    print("Enhanced system prompt preview:")
    print(f"  {enhanced[:100]}...")
    print()
    print()


def demo_module_selection():
    """Demonstrate selective module injection"""

    print("=" * 80)
    print("SELECTIVE MODULE INJECTION")
    print("=" * 80)
    print()

    # Update with sample data
    data = generate_sample_data()
    update_proxy_status(data)

    # Only status
    print("┌─ Only Status Module ───────────────────────────────────────────────┐")
    print("│ For basic routing awareness                                        │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    status_only = prompt_injector.generate_prompt_context(
        format='single',
        modules=['status']
    )
    print(status_only)
    print()

    # Only performance
    print("┌─ Only Performance Module ──────────────────────────────────────────┐")
    print("│ For optimization and speed insights                                │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    perf_only = prompt_injector.generate_prompt_context(
        format='single',
        modules=['performance']
    )
    print(perf_only)
    print()

    # Status + Errors (debugging)
    print("┌─ Status + Errors (Debugging) ──────────────────────────────────────┐")
    print("│ For troubleshooting and error analysis                             │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    debug = prompt_injector.generate_prompt_context(
        format='single',
        modules=['status', 'errors']
    )
    print(debug)
    print()


if __name__ == '__main__':
    demo_all_formats()
    demo_injection_strategies()
    demo_module_selection()

    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("To use in your proxy:")
    print("  1. Import: from src.utils.prompt_injection_middleware import *")
    print("  2. Configure: prompt_injection_middleware.configure(...)")
    print("  3. Update data: update_proxy_status(data)")
    print("  4. Inject: middleware.inject_into_request(request)")
    print()
    print("See examples/prompt_injection_examples.md for more details.")
    print()
