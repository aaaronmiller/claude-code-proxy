#!/usr/bin/env python3
"""
Interactive Prompt Injection Configurator

Configure which dashboard modules to inject into Claude Code prompts.
Supports large, medium, and small size variants.
"""

import sys
from pathlib import Path

# ASCII art header with Nerd Fonts
HEADER = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   🔧  Claude Code Prompt Injection Configurator                  ║
║                                                                   ║
║   Inject live proxy stats into your Claude Code prompts!         ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""

MODULES = {
    'status': {
        'name': 'Proxy Status',
        'icon': '🔧',
        'description': 'Provider, models, reasoning config',
        'large': '~250 chars (5 lines)',
        'medium': '~80 chars (1 line)',
        'small': '~8 chars (icons)'
    },
    'performance': {
        'name': 'Performance',
        'icon': '⚡',
        'description': 'Requests, latency, speed, cost',
        'large': '~250 chars (5 lines)',
        'medium': '~60 chars (1 line)',
        'small': '~15 chars'
    },
    'errors': {
        'name': 'Error Tracking',
        'icon': '⚠️',
        'description': 'Success rate, error types',
        'large': '~250 chars (5 lines)',
        'medium': '~50 chars (1 line)',
        'small': '~8 chars'
    },
    'models': {
        'name': 'Model Usage',
        'icon': '🤖',
        'description': 'Top models and usage stats',
        'large': '~300 chars (7 lines)',
        'medium': '~60 chars (1 line)',
        'small': '~12 chars'
    }
}

SIZE_INFO = {
    'large': {
        'name': 'Large (Multi-line)',
        'description': 'Detailed boxes with full information',
        'token_cost': '~200-300 tokens',
        'use_case': 'When you need comprehensive context'
    },
    'medium': {
        'name': 'Medium (Single-line)',
        'description': 'Compact single lines per module',
        'token_cost': '~50-100 tokens',
        'use_case': 'Balanced - good for most cases'
    },
    'small': {
        'name': 'Small (Inline)',
        'description': 'Ultra-compact icons and numbers',
        'token_cost': '~20-40 tokens',
        'use_case': 'Minimal token usage, status bar style'
    }
}


def print_header():
    """Print header with colors"""
    print("\033[1;36m" + HEADER + "\033[0m")


def print_module_info():
    """Display available modules"""
    print("\n\033[1;33m📦 Available Modules:\033[0m\n")

    for i, (key, info) in enumerate(MODULES.items(), 1):
        print(f"  \033[1;32m{i}. {info['icon']}  {info['name']}\033[0m")
        print(f"     {info['description']}")
        print(f"     Sizes: {info['large']} | {info['medium']} | {info['small']}")
        print()


def print_size_info():
    """Display size variant information"""
    print("\n\033[1;33m📏 Size Variants:\033[0m\n")

    for key, info in SIZE_INFO.items():
        print(f"  \033[1;32m{key.upper()}\033[0m - {info['name']}")
        print(f"     {info['description']}")
        print(f"     Token cost: {info['token_cost']}")
        print(f"     Use case: {info['use_case']}")
        print()


def show_preview(modules: list, size: str):
    """Show preview of selected configuration"""
    print(f"\n\033[1;35m👀 Preview ({size.upper()}):\033[0m\n")

    # Mock stats for preview
    mock_stats = {
        'total_requests': 847,
        'success_count': 835,
        'error_count': 12,
        'avg_latency_ms': 1234,
        'avg_tokens_per_sec': 78,
        'total_cost': 12.45,
        'total_input_tokens': 45000,
        'total_output_tokens': 12000,
        'error_types': {
            'Rate Limit': 8,
            'Timeout': 4
        },
        'top_models': [
            {'name': 'openai/gpt-4o', 'requests': 420, 'cost': 8.32},
            {'name': 'anthropic/claude-3.5-sonnet', 'requests': 312, 'cost': 3.21},
            {'name': 'gpt-4o-mini', 'requests': 115, 'cost': 0.92}
        ]
    }

    try:
        from src.dashboard.prompt_modules import prompt_dashboard_renderer

        output = prompt_dashboard_renderer.render(modules, size, mock_stats)

        if output:
            print("\033[90m" + "─" * 60 + "\033[0m")
            print(output)
            print("\033[90m" + "─" * 60 + "\033[0m")
        else:
            print("\033[91m✗ No output (check module selection)\033[0m")

    except Exception as e:
        print(f"\033[91m✗ Error generating preview: {e}\033[0m")


def generate_commands(modules: list, size: str, injection_mode: str):
    """Generate configuration commands"""
    print(f"\n\033[1;36m🎯 Configuration Generated!\033[0m\n")

    # Create module config string
    module_config = ','.join(modules)

    print("\033[1;33m1. Environment Variable:\033[0m")
    print(f"\n   export PROMPT_INJECTION_MODULES=\"{module_config}\"")
    print(f"   export PROMPT_INJECTION_SIZE=\"{size}\"")
    print(f"   export PROMPT_INJECTION_MODE=\"{injection_mode}\"")

    print("\n\033[1;33m2. Add to .env file:\033[0m")
    print(f"\n   PROMPT_INJECTION_MODULES=\"{module_config}\"")
    print(f"   PROMPT_INJECTION_SIZE=\"{size}\"")
    print(f"   PROMPT_INJECTION_MODE=\"{injection_mode}\"")

    print("\n\033[1;33m3. Add to .zshrc (persistent):\033[0m")
    print(f"\n   # Claude Code Prompt Injection")
    print(f"   export PROMPT_INJECTION_MODULES=\"{module_config}\"")
    print(f"   export PROMPT_INJECTION_SIZE=\"{size}\"")
    print(f"   export PROMPT_INJECTION_MODE=\"{injection_mode}\"")

    print("\n\033[1;33m4. For p10k integration:\033[0m")
    print("\n   # Add to ~/.p10k.zsh in POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS:")
    print(f"   # custom_proxy_status  # Shows: {', '.join([MODULES[m]['icon'] for m in modules[:3]])}")

    # Create startup script
    script_path = Path("start_with_prompt_injection.sh")
    script_content = f"""#!/bin/bash
# Claude Code Proxy with Prompt Injection
# Generated by configure_prompt_injection.py

export PROMPT_INJECTION_MODULES="{module_config}"
export PROMPT_INJECTION_SIZE="{size}"
export PROMPT_INJECTION_MODE="{injection_mode}"

echo "🔧 Prompt Injection Configured:"
echo "   Modules: {module_config}"
echo "   Size: {size}"
echo "   Mode: {injection_mode}"
echo ""

# Start proxy
python src/main.py "$@"
"""

    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        script_path.chmod(0o755)
        print(f"\n\033[1;32m✓ Created executable script: {script_path}\033[0m")
        print(f"  Run with: ./{script_path}")
    except Exception as e:
        print(f"\n\033[91m✗ Could not create script: {e}\033[0m")


def select_modules():
    """Interactive module selection"""
    print("\n\033[1;33m📦 Select modules to inject (comma-separated, e.g., 1,2,4):\033[0m")
    print("   Or type 'all' for all modules")

    module_list = list(MODULES.keys())

    while True:
        choice = input("\n   Your selection: ").strip().lower()

        if choice == 'all':
            return module_list

        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [module_list[i] for i in indices if 0 <= i < len(module_list)]

            if selected:
                return selected
            else:
                print("   \033[91m✗ Invalid selection. Try again.\033[0m")
        except (ValueError, IndexError):
            print("   \033[91m✗ Invalid input. Use numbers like: 1,2,3\033[0m")


def select_size():
    """Interactive size selection"""
    print("\n\033[1;33m📏 Select size variant:\033[0m")
    print("   1. Large (multi-line, ~200-300 tokens)")
    print("   2. Medium (single-line, ~50-100 tokens) [RECOMMENDED]")
    print("   3. Small (inline, ~20-40 tokens)")

    while True:
        choice = input("\n   Your selection (1-3): ").strip()

        size_map = {'1': 'large', '2': 'medium', '3': 'small'}

        if choice in size_map:
            return size_map[choice]
        else:
            print("   \033[91m✗ Invalid selection. Choose 1, 2, or 3.\033[0m")


def select_injection_mode():
    """Select when to inject"""
    print("\n\033[1;33m⚙️  Select injection mode:\033[0m")
    print("   1. Always - Inject on every request")
    print("   2. Auto - Inject on tool calls and streaming (smart)")
    print("   3. Manual - Only when explicitly requested")
    print("   4. Header - Always inject as compact header")

    while True:
        choice = input("\n   Your selection (1-4): ").strip()

        mode_map = {
            '1': 'always',
            '2': 'auto',
            '3': 'manual',
            '4': 'header'
        }

        if choice in mode_map:
            return mode_map[choice]
        else:
            print("   \033[91m✗ Invalid selection. Choose 1-4.\033[0m")


def main():
    """Main configuration flow"""
    print_header()

    print("\n\033[1;36mℹ️  This tool configures prompt injection for Claude Code.\033[0m")
    print("   Dashboard module data will be injected into your prompts,")
    print("   giving Claude visibility into proxy performance and status.")
    print()

    # Show available options
    print_module_info()
    print_size_info()

    # Interactive selection
    modules = select_modules()
    size = select_size()
    injection_mode = select_injection_mode()

    # Show preview
    show_preview(modules, size)

    # Confirm
    print(f"\n\033[1;33m✓ Selected: {len(modules)} modules, {size} size, {injection_mode} mode\033[0m")
    confirm = input("\n   Generate configuration? (y/n): ").strip().lower()

    if confirm == 'y':
        generate_commands(modules, size, injection_mode)
        print("\n\033[1;32m✓ Configuration complete!\033[0m\n")
    else:
        print("\n\033[90mCancelled.\033[0m\n")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[90mCancelled by user.\033[0m\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\033[91m✗ Error: {e}\033[0m\n")
        sys.exit(1)
