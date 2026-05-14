# File Audit: /home/cheta/code/claude-code-proxy/src/cli/fix_keys.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/fix_keys.py`

**Module Overview**: 
```text
API Key Wizard (Python Version)
Fixes API keys in the global profile.
```

## Dependencies & Imports
os, sys, re, datetime, pathlib.Path, typing.Optional, typing.Dict

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `api_key, profile_path, project_root, choice, provider, providers`
**Implementation:**
```python
def main():
    if RICH_AVAILABLE:
        console.print(Panel.fit('[bold cyan]🧙 API Key Wizard for Claude Code Proxy[/bold cyan]', border_style='cyan'))
        console.print('This wizard will help you fix your API keys in your shell profile.\n')
    else:
        print('\n🧙 API Key Wizard for Claude Code Proxy')
        print('This wizard will help you fix your API keys in your shell profile.\n')
    project_root = Path(__file__).parent.parent.parent
    profile_path = project_root / '.env'
    if not profile_path.exists():
        console.print(f'[yellow]Creating new config file at {profile_path}[/yellow]')
        profile_path.touch()
    else:
        console.print(f'Using config file: [yellow]{profile_path}[/yellow]\n')
    providers = {'1': {'name': 'Anthropic (Claude)', 'var': 'ANTHROPIC_API_KEY', 'url_var': 'ANTHROPIC_BASE_URL', 'url': 'https://api.anthropic.com', 'prefix': 'sk-ant-'}, '2': {'name': 'OpenRouter', 'var': 'OPENROUTER_API_KEY', 'url_var': 'OPENROUTER_BASE_URL', 'url': 'https://openrouter.ai/api/v1', 'prefix': 'sk-or-'}, '3': {'name': 'OpenAI', 'var': 'OPENAI_API_KEY', 'url_var': 'OPENAI_BASE_URL', 'url': 'https://api.openai.com/v1', 'prefix': 'sk-'}, '4': {'name': 'Google Gemini', 'var': 'GOOGLE_API_KEY', 'url_var': 'GOOGLE_BASE_URL', 'url': 'https://generativelanguage.googleapis.com/v1beta/openai', 'prefix': ''}, '5': {'name': 'Perplexity', 'var': 'PERPLEXITY_API_KEY', 'url_var': 'PERPLEXITY_BASE_URL', 'url': 'https://api.perplexity.ai', 'prefix': 'pplx-'}}
    if RICH_AVAILABLE:
        console.print('[bold]Select your provider:[/bold]')
        for k, v in providers.items():
            console.print(f"{k}) {v['name']}")
        choice = Prompt.ask('Enter number', choices=list(providers.keys()), default='1')
    else:
        print('Select your provider:')
        for k, v in providers.items():
            print(f"{k}) {v['name']}")
        choice = input('Enter number (1-5): ')
    if choice not in providers:
        console.print('[red]Invalid choice. Exiting.[/red]')
        sys.exit(1)
    provider = providers[choice]
    console.print(f"\nSelected Provider: [green]{provider['name']}[/green]")
    api_key = Prompt.ask(f"Enter your REAL {provider['name']} API Key", password=True)
    if not api_key:
        console.print('[red]API Key cannot be empty. Exiting.[/red]')
        sys.exit(1)
    if provider['prefix'] and (not api_key.startswith(provider['prefix'])):
        if RICH_AVAILABLE:
            if not Confirm.ask(f"[yellow]Warning: Key usually starts with '{provider['prefix']}'. Continue?[/yellow]"):
                sys.exit(1)
        elif input(f"Warning: Key usually starts with '{provider['prefix']}'. Continue? (y/n): ") != 'y':
            sys.exit(1)
    console.print(f'\nWriting to {profile_path}...')
    try:
        _update_profile(profile_path, provider, api_key)
        console.print(f'[green]✅ Successfully updated {profile_path}[/green]')
        console.print(f'\n[blue]Note: The proxy will automatically pick up these changes.[/blue]')
    except Exception as e:
        console.print(f'[red]Error updating config: {e}[/red]')
        sys.exit(1)
```

---

## Feature Function: `_update_profile`
**Parameters:** `path, provider, api_key`
**Variables Used:** `new_lines, updates, lines, found, updated_line, content, prefix`
**Implementation:**
```python
def _update_profile(path: Path, provider: Dict, api_key: str):
    content = path.read_text()
    lines = content.splitlines()
    new_lines = []
    updates = {provider['var']: api_key, provider['url_var']: provider['url'], 'PROVIDER_API_KEY': f"${provider['var']}", 'PROVIDER_BASE_URL': f"${provider['url_var']}"}
    found = {k: False for k in updates.keys()}
    for line in lines:
        updated_line = line
        for var, val in updates.items():
            if re.match(f'^\\s*(export\\s+)?{var}=', line):
                prefix = 'export ' if 'export' in line else ''
                updated_line = f'{prefix}{var}="{val}"'
                found[var] = True
                break
        new_lines.append(updated_line)
    if any((not v for v in found.values())):
        if new_lines and new_lines[-1] != '':
            new_lines.append('')
        new_lines.append(f'# Updated by Claude Code Proxy Wizard {datetime.datetime.now()}')
        for var, val in updates.items():
            if not found[var]:
                new_lines.append(f'{var}="{val}"')
    path.write_text('\n'.join(new_lines) + '\n')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/prompt_config.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/prompt_config.py`

**Module Overview**: 
```text
Interactive Prompt Injection Configurator

Configure which dashboard modules to inject into Claude Code prompts.
Supports large, medium, and small size variants.
```

## Global Presets & Variables
- `HEADER` = `'\n╔═══════════════════════════════════════════════════════════════════╗\n║                                                                   ║\n║   🔧  Claude Code Prompt Injection Configurator                  ║\n║                                                                   ║\n║   Inject live proxy stats into your Claude Code prompts!         ║\n║                                                                   ║\n╚═══════════════════════════════════════════════════════════════════╝\n'`
- `MODULES` = `{'status': {'name': 'Proxy Status', 'icon': '🔧', 'description': 'Provider, models, reasoning config', 'large': '~250 chars (5 lines)', 'medium': '~80 chars (1 line)', 'small': '~8 chars (icons)'}, 'performance': {'name': 'Performance', 'icon': '⚡', 'description': 'Requests, latency, speed, cost', 'large': '~250 chars (5 lines)', 'medium': '~60 chars (1 line)', 'small': '~15 chars'}, 'errors': {'name': 'Error Tracking', 'icon': '⚠️', 'description': 'Success rate, error types', 'large': '~250 chars (5 lines)', 'medium': '~50 chars (1 line)', 'small': '~8 chars'}, 'models': {'name': 'Model Usage', 'icon': '🤖', 'description': 'Top models and usage stats', 'large': '~300 chars (7 lines)', 'medium': '~60 chars (1 line)', 'small': '~12 chars'}}`
- `SIZE_INFO` = `{'large': {'name': 'Large (Multi-line)', 'description': 'Detailed boxes with full information', 'token_cost': '~200-300 tokens', 'use_case': 'When you need comprehensive context'}, 'medium': {'name': 'Medium (Single-line)', 'description': 'Compact single lines per module', 'token_cost': '~50-100 tokens', 'use_case': 'Balanced - good for most cases'}, 'small': {'name': 'Small (Inline)', 'description': 'Ultra-compact icons and numbers', 'token_cost': '~20-40 tokens', 'use_case': 'Minimal token usage, status bar style'}}`

## Dependencies & Imports
sys, pathlib.Path

## Feature Function: `print_header`
**Logic & Purpose:**
```text
Print header with colors
```

**Parameters:** ``
**Implementation:**
```python
def print_header():
    """Print header with colors"""
    print('\x1b[1;36m' + HEADER + '\x1b[0m')
```

---

## Feature Function: `print_module_info`
**Logic & Purpose:**
```text
Display available modules
```

**Parameters:** ``
**Implementation:**
```python
def print_module_info():
    """Display available modules"""
    print('\n\x1b[1;33m📦 Available Modules:\x1b[0m\n')
    for i, (key, info) in enumerate(MODULES.items(), 1):
        print(f"  \x1b[1;32m{i}. {info['icon']}  {info['name']}\x1b[0m")
        print(f"     {info['description']}")
        print(f"     Sizes: {info['large']} | {info['medium']} | {info['small']}")
        print()
```

---

## Feature Function: `print_size_info`
**Logic & Purpose:**
```text
Display size variant information
```

**Parameters:** ``
**Implementation:**
```python
def print_size_info():
    """Display size variant information"""
    print('\n\x1b[1;33m📏 Size Variants:\x1b[0m\n')
    for key, info in SIZE_INFO.items():
        print(f"  \x1b[1;32m{key.upper()}\x1b[0m - {info['name']}")
        print(f"     {info['description']}")
        print(f"     Token cost: {info['token_cost']}")
        print(f"     Use case: {info['use_case']}")
        print()
```

---

## Feature Function: `show_preview`
**Logic & Purpose:**
```text
Show preview of selected configuration
```

**Parameters:** `modules, size`
**Variables Used:** `mock_stats, injector, info, icon, output, output_lines, name`
**Implementation:**
```python
def show_preview(modules: list, size: str):
    """Show preview of selected configuration"""
    print(f'\n\x1b[1;35m👀 Preview ({size.upper()}):\x1b[0m\n')
    mock_stats = {'total_requests': 847, 'success_count': 835, 'error_count': 12, 'avg_latency_ms': 1234, 'avg_tokens_per_sec': 78, 'total_cost': 12.45, 'total_input_tokens': 45000, 'total_output_tokens': 12000, 'error_types': {'Rate Limit': 8, 'Timeout': 4}, 'top_models': [{'name': 'openai/gpt-4o', 'requests': 420, 'cost': 8.32}, {'name': 'anthropic/claude-3.5-sonnet', 'requests': 312, 'cost': 3.21}, {'name': 'gpt-4o-mini', 'requests': 115, 'cost': 0.92}]}
    try:
        from src.services.prompts.prompt_injector import PromptInjector
        injector = PromptInjector()
        output_lines = []
        for module in modules:
            info = MODULES.get(module, {})
            icon = info.get('icon', '?')
            name = info.get('name', module)
            if size == 'large':
                output_lines.append(f'┌─ {icon} {name} ─────────────────────────┐')
                output_lines.append(f"│ Requests: {mock_stats['total_requests']:,}")
                output_lines.append(f"│ Success: {mock_stats['success_count']:,}")
                output_lines.append(f"│ Errors: {mock_stats['error_count']}")
                output_lines.append(f'└────────────────────────────────────────┘')
            elif size == 'medium':
                output_lines.append(f"{icon} {name}: {mock_stats['total_requests']} reqs | {mock_stats['avg_tokens_per_sec']} t/s | ${mock_stats['total_cost']:.2f}")
            else:
                output_lines.append(f"{icon}{mock_stats['total_requests']}")
        output = '\n'.join(output_lines)
        if output:
            print('\x1b[90m' + '─' * 60 + '\x1b[0m')
            print(output)
            print('\x1b[90m' + '─' * 60 + '\x1b[0m')
        else:
            print('\x1b[91m✗ No output (check module selection)\x1b[0m')
    except Exception as e:
        print(f'\x1b[91m✗ Error generating preview: {e}\x1b[0m')
```

---

## Feature Function: `generate_commands`
**Logic & Purpose:**
```text
Generate configuration commands
```

**Parameters:** `modules, size, injection_mode`
**Variables Used:** `script_path, script_content, module_config`
**Implementation:**
```python
def generate_commands(modules: list, size: str, injection_mode: str):
    """Generate configuration commands"""
    print(f'\n\x1b[1;36m🎯 Configuration Generated!\x1b[0m\n')
    module_config = ','.join(modules)
    print('\x1b[1;33m1. Environment Variable:\x1b[0m')
    print(f'\n   export PROMPT_INJECTION_MODULES="{module_config}"')
    print(f'   export PROMPT_INJECTION_SIZE="{size}"')
    print(f'   export PROMPT_INJECTION_MODE="{injection_mode}"')
    print('\n\x1b[1;33m2. Add to .env file:\x1b[0m')
    print(f'\n   PROMPT_INJECTION_MODULES="{module_config}"')
    print(f'   PROMPT_INJECTION_SIZE="{size}"')
    print(f'   PROMPT_INJECTION_MODE="{injection_mode}"')
    print('\n\x1b[1;33m3. Add to .zshrc (persistent):\x1b[0m')
    print(f'\n   # Claude Code Prompt Injection')
    print(f'   export PROMPT_INJECTION_MODULES="{module_config}"')
    print(f'   export PROMPT_INJECTION_SIZE="{size}"')
    print(f'   export PROMPT_INJECTION_MODE="{injection_mode}"')
    print('\n\x1b[1;33m4. For p10k integration:\x1b[0m')
    print('\n   # Add to ~/.p10k.zsh in POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS:')
    print(f"   # custom_proxy_status  # Shows: {', '.join([MODULES[m]['icon'] for m in modules[:3]])}")
    script_path = Path('start_with_prompt_injection.sh')
    script_content = f'#!/bin/bash\n# Claude Code Proxy with Prompt Injection\n# Generated by configure_prompt_injection.py\n\nexport PROMPT_INJECTION_MODULES="{module_config}"\nexport PROMPT_INJECTION_SIZE="{size}"\nexport PROMPT_INJECTION_MODE="{injection_mode}"\n\necho "🔧 Prompt Injection Configured:"\necho "   Modules: {module_config}"\necho "   Size: {size}"\necho "   Mode: {injection_mode}"\necho ""\n\n# Start proxy\npython start_proxy.py "$@"\n'
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        script_path.chmod(493)
        print(f'\n\x1b[1;32m✓ Created executable script: {script_path}\x1b[0m')
        print(f'  Run with: ./{script_path}')
    except Exception as e:
        print(f'\n\x1b[91m✗ Could not create script: {e}\x1b[0m')
```

---

## Feature Function: `select_modules`
**Logic & Purpose:**
```text
Interactive module selection
```

**Parameters:** ``
**Variables Used:** `indices, choice, module_list, selected`
**Implementation:**
```python
def select_modules():
    """Interactive module selection"""
    print('\n\x1b[1;33m📦 Select modules to inject (comma-separated, e.g., 1,2,4):\x1b[0m')
    print("   Or type 'all' for all modules")
    module_list = list(MODULES.keys())
    while True:
        choice = input('\n   Your selection: ').strip().lower()
        if choice == 'all':
            return module_list
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected = [module_list[i] for i in indices if 0 <= i < len(module_list)]
            if selected:
                return selected
            else:
                print('   \x1b[91m✗ Invalid selection. Try again.\x1b[0m')
        except (ValueError, IndexError):
            print('   \x1b[91m✗ Invalid input. Use numbers like: 1,2,3\x1b[0m')
```

---

## Feature Function: `select_size`
**Logic & Purpose:**
```text
Interactive size selection
```

**Parameters:** ``
**Variables Used:** `size_map, choice`
**Implementation:**
```python
def select_size():
    """Interactive size selection"""
    print('\n\x1b[1;33m📏 Select size variant:\x1b[0m')
    print('   1. Large (multi-line, ~200-300 tokens)')
    print('   2. Medium (single-line, ~50-100 tokens) [RECOMMENDED]')
    print('   3. Small (inline, ~20-40 tokens)')
    while True:
        choice = input('\n   Your selection (1-3): ').strip()
        size_map = {'1': 'large', '2': 'medium', '3': 'small'}
        if choice in size_map:
            return size_map[choice]
        else:
            print('   \x1b[91m✗ Invalid selection. Choose 1, 2, or 3.\x1b[0m')
```

---

## Feature Function: `select_injection_mode`
**Logic & Purpose:**
```text
Select when to inject
```

**Parameters:** ``
**Variables Used:** `mode_map, choice`
**Implementation:**
```python
def select_injection_mode():
    """Select when to inject"""
    print('\n\x1b[1;33m⚙️  Select injection mode:\x1b[0m')
    print('   1. Always - Inject on every request')
    print('   2. Auto - Inject on tool calls and streaming (smart)')
    print('   3. Manual - Only when explicitly requested')
    print('   4. Header - Always inject as compact header')
    while True:
        choice = input('\n   Your selection (1-4): ').strip()
        mode_map = {'1': 'always', '2': 'auto', '3': 'manual', '4': 'header'}
        if choice in mode_map:
            return mode_map[choice]
        else:
            print('   \x1b[91m✗ Invalid selection. Choose 1-4.\x1b[0m')
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main configuration flow
```

**Parameters:** ``
**Variables Used:** `injection_mode, confirm, size, modules, choice`
**Implementation:**
```python
def main():
    """Main configuration flow"""
    while True:
        print_header()
        print('\n\x1b[1;36mℹ️  This tool configures prompt injection for Claude Code.\x1b[0m')
        print('   Dashboard module data will be injected into your prompts.')
        print()
        print('\n\x1b[1;33mOptions:\x1b[0m')
        print('   1. ⚙️  Configure Prompt Injection')
        print('   0. 🔙 Back to Main Menu')
        choice = input('\n   Your selection: ').strip()
        if choice == '0':
            return
        elif choice != '1':
            continue
        print_module_info()
        print_size_info()
        modules = select_modules()
        size = select_size()
        injection_mode = select_injection_mode()
        show_preview(modules, size)
        print(f'\n\x1b[1;33m✓ Selected: {len(modules)} modules, {size} size, {injection_mode} mode\x1b[0m')
        confirm = input('\n   Generate configuration? (y/n): ').strip().lower()
        if confirm == 'y':
            generate_commands(modules, size, injection_mode)
            print('\n\x1b[1;32m✓ Configuration complete!\x1b[0m\n')
            input('Press Enter to return...')
        else:
            print('\n\x1b[90mCancelled.\x1b[0m\n')
            input('Press Enter to return...')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/dashboard_config.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/dashboard_config.py`

**Module Overview**: 
```text
Dashboard Configuration Tool (TUI Redesign)

A slick, grid-based interface to configure the API monitoring dashboard.
Supports 10 slots: 4 Left, 4 Right, Top, Bottom.
```

## Global Presets & Variables
- `SLOTS` = `[SlotInfo('T1', 'Top Bar', 0, 1, width=60), SlotInfo('L1', 'Left 1', 1, 0), SlotInfo('L2', 'Left 2', 2, 0), SlotInfo('L3', 'Left 3', 3, 0), SlotInfo('L4', 'Left 4', 4, 0), SlotInfo('R1', 'Right 1', 1, 2), SlotInfo('R2', 'Right 2', 2, 2), SlotInfo('R3', 'Right 3', 3, 2), SlotInfo('R4', 'Right 4', 4, 2), SlotInfo('B1', 'Bottom Bar', 5, 1, width=60)]`
- `MODULES` = `{'performance': {'icon': '⚡', 'name': 'Performance', 'desc': 'Real-time latency & tokens', 'preview_sparse': '⚡ 15.8s | 82 t/s\n📊 43k ctx | $0.02', 'preview_dense': '⚡ 15.8s | 82 tok/s\n📊 CTX: 43.7k/200k\n🧠 Think: 920 tok\n💰 Est: $0.0234'}, 'activity': {'icon': '📝', 'name': 'Activity Feed', 'desc': 'Recent request history', 'preview_sparse': '🔵 abc123 → OK\n🟢 def456 → OK', 'preview_dense': '🔵 abc123 claude→gpt4\n🟢 def456 gpt4→sonnet\n🔴 ghi789 gemini→ERR\n⚡ Avg: 3.2s'}, 'routing': {'icon': '🔄', 'name': 'Routing', 'desc': 'Model flow visualizer', 'preview_sparse': 'claude → gpt4o\n43k → 1.3k', 'preview_dense': '[Claude]──>[GPT-4o]\n ↓ 43k      ↓ 1.3k\n 🧠 920     ⚡ 82t/s'}, 'analytics': {'icon': '📈', 'name': 'Analytics', 'desc': 'Cost & usage stats', 'preview_sparse': '47 req | $12.45\n94% Success', 'preview_dense': 'Reqs: 47 | $12.45\nAvg: 2.3s | 94% OK\n🏆 Fast: gpt-4o-mini\n🔥 Hot: sonnet'}, 'waterfall': {'icon': '🌊', 'name': 'Waterfall', 'desc': 'Request stages', 'preview_sparse': 'Parse→Route→Send\nWait→Recv→Done', 'preview_dense': 'Parse.. 0.1s\nRoute.. 0.2s\nSend... 0.3s\nWait... 14s'}, 'empty': {'icon': '⚫', 'name': 'Empty Slot', 'desc': 'Clear this slot', 'preview_sparse': '', 'preview_dense': ''}}`

## Dependencies & Imports
sys, os, json, enum.Enum, typing.Dict, typing.List, typing.Optional, typing.Tuple

## Feature Class: `SlotInfo`
### Method: `__init__`
**Parameters:** `self, id, name, row, col, width`
**Implementation:**
```python
def __init__(self, id: str, name: str, row: int, col: int, width: int=30):
    self.id = id
    self.name = name
    self.row = row
    self.col = col
    self.width = width
    self.module: Optional[str] = None
    self.mode: str = 'sparse'
```

---

## Feature Class: `DashboardTUI`
### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.cursor_idx = 0
    self.running = True
    self.get_slot('L1').module = 'performance'
    self.get_slot('L1').mode = 'dense'
    self.get_slot('L2').module = 'activity'
    self.get_slot('L3').module = 'routing'
    self.get_slot('L4').module = 'analytics'
    self.get_slot('R1').module = 'waterfall'
    self.get_slot('R1').mode = 'dense'
    self.get_slot('R2').module = 'performance'
    self.get_slot('R3').module = 'activity'
    self.get_slot('R4').module = 'routing'
    self.get_slot('T1').module = 'analytics'
    self.get_slot('T1').mode = 'sparse'
    self.get_slot('B1').module = 'performance'
    self.get_slot('B1').mode = 'sparse'
```

### Method: `get_slot`
**Parameters:** `self, id`
**Implementation:**
```python
def get_slot(self, id: str) -> SlotInfo:
    return next((s for s in SLOTS if s.id == id))
```

### Method: `clear_screen`
**Parameters:** `self`
**Implementation:**
```python
def clear_screen(self):
    os.system('cls' if os.name == 'nt' else 'clear')
```

### Method: `draw_screen`
**Parameters:** `self`
**Variables Used:** `header_text, left_stack, mod, grid, b1_slot, border, slot, title, t1_slot, is_focused, right_stack, content, terminal_view, style`
**Implementation:**
```python
def draw_screen(self):
    self.clear_screen()
    header_text = Text('🚀 API Dashboard Configurator', style='bold cyan')
    console.print(Panel(Align.center(Group(Spinner('dots', text=header_text), Text('Arrow keys to move • Enter to select • s to toggle size • q to save & back', style='dim'))), border_style='cyan', box=ROUNDED))
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column('Left', ratio=1)
    grid.add_column('Center', ratio=3)
    grid.add_column('Right', ratio=1)

    def render_slot(slot: SlotInfo, is_focused: bool):
        if slot.module:
            mod = MODULES[slot.module]
            content = mod[f'preview_{slot.mode}']
            title = f"{mod['icon']} {mod['name']}"
            style = 'green' if is_focused else 'blue'
        else:
            content = '[dim]Empty Slot[/dim]'
            title = slot.name
            style = 'yellow' if is_focused else 'dim'
        border = HEAVY if is_focused else ROUNDED
        return Panel(Align.center(content), title=title, border_style=style, box=border, height=4 if slot.mode == 'sparse' else 8)
    t1_slot = self.get_slot('T1')
    is_focused = SLOTS[self.cursor_idx].id == 'T1'
    console.print(Align.center(render_slot(t1_slot, is_focused), width=60))
    console.print()
    left_stack = Table.grid(expand=True, padding=(0, 0))
    for i in range(1, 5):
        slot = self.get_slot(f'L{i}')
        is_focused = SLOTS[self.cursor_idx].id == slot.id
        left_stack.add_row(render_slot(slot, is_focused))
        left_stack.add_row('')
    right_stack = Table.grid(expand=True, padding=(0, 0))
    for i in range(1, 5):
        slot = self.get_slot(f'R{i}')
        is_focused = SLOTS[self.cursor_idx].id == slot.id
        right_stack.add_row(render_slot(slot, is_focused))
        right_stack.add_row('')
    terminal_view = Panel('\n[dim]  ╰─❯ tail -f /tmp/proxy-logs/headroom.log[/dim]\n' + '\n[dim]  ... terminal output ...[/dim]\n' * 6, title='Terminal Area (Live Output)', border_style='dim', box=ROUNDED)
    grid.add_row(left_stack, terminal_view, right_stack)
    console.print(grid)
    console.print()
    b1_slot = self.get_slot('B1')
    is_focused = SLOTS[self.cursor_idx].id == 'B1'
    console.print(Align.center(render_slot(b1_slot, is_focused), width=60))
```

### Method: `handle_input`
**Parameters:** `self`
**Variables Used:** `key, current`
**Implementation:**
```python
def handle_input(self):
    key = readchar.readkey()
    current = SLOTS[self.cursor_idx]
    if key == readchar.key.UP:
        if current.id.startswith('L'):
            if current.id == 'L1':
                self.cursor_idx = 0
            else:
                self.cursor_idx -= 1
        elif current.id.startswith('R'):
            if current.id == 'R1':
                self.cursor_idx = 0
            else:
                self.cursor_idx -= 1
        elif current.id == 'B1':
            self.cursor_idx = 0
            self.cursor_idx = 4
        elif current.id == 'T1':
            self.cursor_idx = 9
    elif key == readchar.key.DOWN:
        if current.id == 'T1':
            self.cursor_idx = 1
        elif current.id.startswith('L'):
            if current.id == 'L4':
                self.cursor_idx = 9
            else:
                self.cursor_idx += 1
        elif current.id.startswith('R'):
            if current.id == 'R4':
                self.cursor_idx = 9
            else:
                self.cursor_idx += 1
        elif current.id == 'B1':
            self.cursor_idx = 0
    elif key == readchar.key.LEFT:
        if current.id.startswith('R'):
            self.cursor_idx -= 4
        elif current.id.startswith('L'):
            self.cursor_idx += 4
        elif current.id == 'T1' or current.id == 'B1':
            pass
    elif key == readchar.key.RIGHT:
        if current.id.startswith('L'):
            self.cursor_idx += 4
        elif current.id.startswith('R'):
            self.cursor_idx -= 4
        elif current.id == 'T1' or current.id == 'B1':
            pass
    elif key == readchar.key.ENTER or key == ' ':
        self.pick_module(current)
    elif key == 's':
        current.mode = 'dense' if current.mode == 'sparse' else 'sparse'
    elif key == 'x' or key == readchar.key.BACKSPACE:
        current.module = None
    elif key == 'q':
        self.running = False
```

### Method: `pick_module`
**Parameters:** `self, slot`
**Variables Used:** `mods, m, choice, k`
**Implementation:**
```python
def pick_module(self, slot: SlotInfo):
    self.clear_screen()
    console.print(Panel(f'[bold]Select Module for {slot.name}[/bold]', border_style='cyan'))
    mods = list(MODULES.keys())
    for i, m_key in enumerate(mods):
        m = MODULES[m_key]
        console.print(f"[{i + 1}] {m['icon']} {m['name']} - [dim]{m['desc']}[/dim]")
    console.print('\n[dim]Press number to select or q to cancel[/dim]')
    k = readchar.readkey()
    if k.isdigit() and 1 <= int(k) <= len(mods):
        choice = mods[int(k) - 1]
        if choice == 'empty':
            slot.module = None
        else:
            slot.module = choice
```

### Method: `generate_config`
**Parameters:** `self`
**Variables Used:** `config_parts, config_str`
**Implementation:**
```python
def generate_config(self):
    config_parts = []
    for slot in SLOTS:
        if slot.module:
            config_parts.append(f'{slot.id}:{slot.module}:{slot.mode}')
    config_str = ','.join(config_parts)
    console.print('\n[bold green]✅ Configuration Generated![/bold green]')
    console.print(Panel(f"export DASHBOARD_CONFIG='{config_str}'", title='Environment Variable'))
    console.print('[dim]Add this variable to your .env file or shell profile.[/dim]')
```

### Method: `run`
**Parameters:** `self`
**Implementation:**
```python
def run(self):
    if not RICH_AVAILABLE or not READCHAR_AVAILABLE:
        print("Error: 'rich' and 'readchar' libraries are required.")
        print('Run: uv sync')
        return
    while self.running:
        self.draw_screen()
        self.handle_input()
    self.generate_config()
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `tui`
**Implementation:**
```python
def main():
    tui = DashboardTUI()
    tui.run()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/profile_manager.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/profile_manager.py`

**Module Overview**: 
```text
Profile Manager CLI for Claude Code Proxy

Manage configuration profiles for easy switching between different setups.
```

## Global Presets & Variables
- `console` = `Console()`
- `custom_style` = `Style([('qmark', 'fg:#673ab7 bold'), ('question', 'bold'), ('answer', 'fg:#f44336 bold'), ('pointer', 'fg:#673ab7 bold'), ('highlighted', 'fg:#673ab7 bold'), ('selected', 'fg:#cc5454'), ('separator', 'fg:#cc5454'), ('instruction', ''), ('text', '')])`

## Dependencies & Imports
os, sys, shutil, pathlib.Path, typing.List, typing.Dict, typing.Optional, datetime.datetime, questionary, questionary.Style, rich.console.Console, rich.table.Table, rich.panel.Panel

## Feature Class: `ProfileManager`
**Description:**
```text
Manage configuration profiles
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.project_root = Path(__file__).parent.parent.parent
    self.profiles_dir = self.project_root / 'profiles'
    self.env_file = self.project_root / '.env'
    self.profiles_dir.mkdir(exist_ok=True)
```

### Method: `list_profiles`
**Logic & Purpose:**
```text
List all saved profiles
```

**Parameters:** `self`
**Variables Used:** `profiles, line, description, config, stats, modified`
**Implementation:**
```python
def list_profiles(self) -> List[Dict]:
    """List all saved profiles"""
    profiles = []
    for profile_file in sorted(self.profiles_dir.glob('*.env')):
        stats = profile_file.stat()
        modified = datetime.fromtimestamp(stats.st_mtime)
        description = ''
        try:
            with open(profile_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# Description:'):
                        description = line.replace('# Description:', '').strip()
                        break
                    if line and (not line.startswith('#')):
                        break
        except Exception:
            pass
        config = self._read_profile_config(profile_file)
        profiles.append({'name': profile_file.stem, 'path': profile_file, 'modified': modified, 'description': description, 'provider': config.get('PROVIDER_BASE_URL', '').replace('https://', '').replace('/v1', ''), 'big_model': config.get('BIG_MODEL', ''), 'size': stats.st_size})
    return profiles
```

### Method: `_read_profile_config`
**Logic & Purpose:**
```text
Read configuration from a profile file
```

**Parameters:** `self, profile_path`
**Variables Used:** `value, key, line, config`
**Implementation:**
```python
def _read_profile_config(self, profile_path: Path) -> Dict[str, str]:
    """Read configuration from a profile file"""
    config = {}
    try:
        with open(profile_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and (not line.startswith('#')):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        config[key] = value
    except Exception as e:
        console.print(f'[yellow]⚠️  Error reading profile: {e}[/yellow]')
    return config
```

### Method: `display_profiles`
**Logic & Purpose:**
```text
Display profiles in a nice table
```

**Parameters:** `self`
**Variables Used:** `profiles, table, big_model, description, provider, modified_str`
**Implementation:**
```python
def display_profiles(self):
    """Display profiles in a nice table"""
    profiles = self.list_profiles()
    if not profiles:
        console.print('\n[yellow]No profiles found in profiles/[/yellow]')
        console.print('Create a profile with: [cyan]python -m src.cli.profile_manager create[/cyan]\n')
        return
    table = Table(title='💾 Saved Profiles', show_header=True, header_style='bold cyan')
    table.add_column('Name', style='cyan')
    table.add_column('Provider', style='green')
    table.add_column('BIG Model', style='yellow')
    table.add_column('Modified', style='dim')
    table.add_column('Description', style='dim')
    for profile in profiles:
        modified_str = profile['modified'].strftime('%Y-%m-%d %H:%M')
        provider = profile['provider'] or 'Not set'
        big_model = profile['big_model'] or 'Not set'
        description = profile['description'] or ''
        table.add_row(profile['name'], provider, big_model, modified_str, description)
    console.print()
    console.print(table)
    console.print()
```

### Method: `switch_profile`
**Logic & Purpose:**
```text
Switch to a profile by copying it to .env
```

**Parameters:** `self, profile_name`
**Variables Used:** `backup_path, config, profile_path`
**Implementation:**
```python
def switch_profile(self, profile_name: str) -> bool:
    """Switch to a profile by copying it to .env"""
    profile_path = self.profiles_dir / f'{profile_name}.env'
    if not profile_path.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return False
    try:
        if self.env_file.exists():
            backup_path = self.env_file.with_suffix(f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(self.env_file, backup_path)
            console.print(f'[dim]📦 Backed up current .env to {backup_path.name}[/dim]')
        shutil.copy2(profile_path, self.env_file)
        console.print(f'\n[green]✅ Switched to profile: {profile_name}[/green]\n')
        config = self._read_profile_config(profile_path)
        console.print('[bold]Active Configuration:[/bold]')
        console.print(f"  Provider: [cyan]{config.get('PROVIDER_BASE_URL', 'Not set')}[/cyan]")
        console.print(f"  BIG Model: [yellow]{config.get('BIG_MODEL', 'Not set')}[/yellow]")
        console.print(f"  MIDDLE Model: [yellow]{config.get('MIDDLE_MODEL', 'Not set')}[/yellow]")
        console.print(f"  SMALL Model: [yellow]{config.get('SMALL_MODEL', 'Not set')}[/yellow]")
        console.print()
        return True
    except Exception as e:
        console.print(f'[red]❌ Error switching profile: {e}[/red]')
        return False
```

### Method: `create_profile`
**Logic & Purpose:**
```text
Create a new profile from current .env
```

**Parameters:** `self, profile_name, description`
**Variables Used:** `overwrite, content, profile_path`
**Implementation:**
```python
def create_profile(self, profile_name: str, description: str='') -> bool:
    """Create a new profile from current .env"""
    if not self.env_file.exists():
        console.print('[red]❌ No .env file found to save as profile[/red]')
        console.print('[yellow]💡 Run: python setup_wizard.py[/yellow]')
        return False
    profile_path = self.profiles_dir / f'{profile_name}.env'
    if profile_path.exists():
        overwrite = questionary.confirm(f"Profile '{profile_name}' already exists. Overwrite?", default=False, style=custom_style).ask()
        if not overwrite:
            console.print('[yellow]❌ Profile creation cancelled[/yellow]')
            return False
    try:
        with open(self.env_file, 'r') as f:
            content = f.read()
        with open(profile_path, 'w') as f:
            if description:
                f.write(f'# Description: {description}\n')
            f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f'#\n')
            f.write(content)
        console.print(f"\n[green]✅ Profile '{profile_name}' created successfully[/green]\n")
        return True
    except Exception as e:
        console.print(f'[red]❌ Error creating profile: {e}[/red]')
        return False
```

### Method: `delete_profile`
**Logic & Purpose:**
```text
Delete a profile
```

**Parameters:** `self, profile_name`
**Variables Used:** `confirm, profile_path`
**Implementation:**
```python
def delete_profile(self, profile_name: str) -> bool:
    """Delete a profile"""
    profile_path = self.profiles_dir / f'{profile_name}.env'
    if not profile_path.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return False
    confirm = questionary.confirm(f"Are you sure you want to delete profile '{profile_name}'?", default=False, style=custom_style).ask()
    if not confirm:
        console.print('[yellow]❌ Deletion cancelled[/yellow]')
        return False
    try:
        profile_path.unlink()
        console.print(f"\n[green]✅ Profile '{profile_name}' deleted[/green]\n")
        return True
    except Exception as e:
        console.print(f'[red]❌ Error deleting profile: {e}[/red]')
        return False
```

### Method: `compare_profiles`
**Logic & Purpose:**
```text
Compare two profiles
```

**Parameters:** `self, profile1_name, profile2_name`
**Variables Used:** `status, profile1_path, table, all_keys, val1, val2, config2, profile2_path, config1`
**Implementation:**
```python
def compare_profiles(self, profile1_name: str, profile2_name: str):
    """Compare two profiles"""
    profile1_path = self.profiles_dir / f'{profile1_name}.env'
    profile2_path = self.profiles_dir / f'{profile2_name}.env'
    if not profile1_path.exists():
        console.print(f"[red]❌ Profile '{profile1_name}' not found[/red]")
        return
    if not profile2_path.exists():
        console.print(f"[red]❌ Profile '{profile2_name}' not found[/red]")
        return
    config1 = self._read_profile_config(profile1_path)
    config2 = self._read_profile_config(profile2_path)
    all_keys = sorted(set(config1.keys()) | set(config2.keys()))
    table = Table(title=f'Comparing: {profile1_name} vs {profile2_name}', show_header=True)
    table.add_column('Variable', style='cyan')
    table.add_column(profile1_name, style='green')
    table.add_column(profile2_name, style='yellow')
    table.add_column('Status', style='bold')
    for key in all_keys:
        val1 = config1.get(key, '[dim]Not set[/dim]')
        val2 = config2.get(key, '[dim]Not set[/dim]')
        if val1 == val2:
            status = '[green]✓ Same[/green]'
        elif key not in config1:
            status = '[yellow]← Missing[/yellow]'
        elif key not in config2:
            status = '[yellow]Missing →[/yellow]'
        else:
            status = '[red]✗ Different[/red]'
        table.add_row(key, val1, val2, status)
    console.print()
    console.print(table)
    console.print()
```

### Method: `export_profile`
**Logic & Purpose:**
```text
Export a profile to a file
```

**Parameters:** `self, profile_name, export_path`
**Variables Used:** `profile_path`
**Implementation:**
```python
def export_profile(self, profile_name: str, export_path: Path):
    """Export a profile to a file"""
    profile_path = self.profiles_dir / f'{profile_name}.env'
    if not profile_path.exists():
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return False
    try:
        shutil.copy2(profile_path, export_path)
        console.print(f'\n[green]✅ Profile exported to: {export_path}[/green]\n')
        return True
    except Exception as e:
        console.print(f'[red]❌ Error exporting profile: {e}[/red]')
        return False
```

### Method: `import_profile`
**Logic & Purpose:**
```text
Import a profile from a file
```

**Parameters:** `self, import_path, profile_name`
**Variables Used:** `profile_name, overwrite, profile_path`
**Implementation:**
```python
def import_profile(self, import_path: Path, profile_name: str=None):
    """Import a profile from a file"""
    if not import_path.exists():
        console.print(f'[red]❌ File not found: {import_path}[/red]')
        return False
    if not profile_name:
        profile_name = import_path.stem
    profile_path = self.profiles_dir / f'{profile_name}.env'
    if profile_path.exists():
        overwrite = questionary.confirm(f"Profile '{profile_name}' already exists. Overwrite?", default=False, style=custom_style).ask()
        if not overwrite:
            console.print('[yellow]❌ Import cancelled[/yellow]')
            return False
    try:
        shutil.copy2(import_path, profile_path)
        console.print(f'\n[green]✅ Profile imported as: {profile_name}[/green]\n')
        return True
    except Exception as e:
        console.print(f'[red]❌ Error importing profile: {e}[/red]')
        return False
```

### Method: `interactive_menu`
**Logic & Purpose:**
```text
Show interactive menu for profile management
```

**Parameters:** `self`
**Variables Used:** `profile2, profiles, export_path, import_path, description, profile_name, choices, profile1, action`
**Implementation:**
```python
def interactive_menu(self):
    """Show interactive menu for profile management"""
    while True:
        console.print('\n' + '=' * 70)
        console.print('[bold cyan]💾 Profile Manager[/bold cyan]')
        console.print('=' * 70 + '\n')
        action = questionary.select('What would you like to do?', choices=['📋 List profiles', '🔄 Switch to profile', '➕ Create new profile', '❌ Delete profile', '🔍 Compare profiles', '📤 Export profile', '📥 Import profile', '🚪 Exit'], style=custom_style).ask()
        if action is None or 'Exit' in action:
            console.print('\n[green]👋 Goodbye![/green]\n')
            break
        if 'List' in action:
            self.display_profiles()
        elif 'Switch' in action:
            profiles = self.list_profiles()
            if not profiles:
                console.print('[yellow]No profiles available[/yellow]')
                continue
            choices = [p['name'] for p in profiles]
            profile_name = questionary.select('Select profile to switch to:', choices=choices, style=custom_style).ask()
            if profile_name:
                self.switch_profile(profile_name)
        elif 'Create' in action:
            profile_name = questionary.text('Profile name:', style=custom_style).ask()
            if profile_name:
                description = questionary.text('Description (optional):', default='', style=custom_style).ask()
                self.create_profile(profile_name, description)
        elif 'Delete' in action:
            profiles = self.list_profiles()
            if not profiles:
                console.print('[yellow]No profiles available[/yellow]')
                continue
            choices = [p['name'] for p in profiles]
            profile_name = questionary.select('Select profile to delete:', choices=choices, style=custom_style).ask()
            if profile_name:
                self.delete_profile(profile_name)
        elif 'Compare' in action:
            profiles = self.list_profiles()
            if len(profiles) < 2:
                console.print('[yellow]Need at least 2 profiles to compare[/yellow]')
                continue
            choices = [p['name'] for p in profiles]
            profile1 = questionary.select('First profile:', choices=choices, style=custom_style).ask()
            profile2 = questionary.select('Second profile:', choices=choices, style=custom_style).ask()
            if profile1 and profile2:
                self.compare_profiles(profile1, profile2)
        elif 'Export' in action:
            profiles = self.list_profiles()
            if not profiles:
                console.print('[yellow]No profiles available[/yellow]')
                continue
            choices = [p['name'] for p in profiles]
            profile_name = questionary.select('Select profile to export:', choices=choices, style=custom_style).ask()
            if profile_name:
                export_path = questionary.path('Export to:', default=f'{profile_name}.env').ask()
                if export_path:
                    self.export_profile(profile_name, Path(export_path))
        elif 'Import' in action:
            import_path = questionary.path('Import from:').ask()
            if import_path:
                profile_name = questionary.text('Save as profile name (leave blank to use filename):', default='', style=custom_style).ask()
                self.import_profile(Path(import_path), profile_name or None)
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
CLI entry point
```

**Parameters:** ``
**Variables Used:** `args, parser, import_path, description, manager, profile_name`
**Implementation:**
```python
def main():
    """CLI entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Claude Code Proxy Profile Manager', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  %(prog)s                              # Interactive menu\n  %(prog)s list                         # List all profiles\n  %(prog)s switch production            # Switch to production profile\n  %(prog)s create dev "Development"     # Create new profile\n  %(prog)s delete old-config            # Delete a profile\n  %(prog)s compare dev production       # Compare two profiles\n  %(prog)s export production prod.env   # Export profile\n  %(prog)s import custom.env custom     # Import profile\n        ')
    parser.add_argument('action', nargs='?', choices=['list', 'switch', 'create', 'delete', 'compare', 'export', 'import'], help='Action to perform (omit for interactive menu)')
    parser.add_argument('args', nargs='*', help='Arguments for the action')
    args = parser.parse_args()
    manager = ProfileManager()
    if not args.action:
        manager.interactive_menu()
        return
    if args.action == 'list':
        manager.display_profiles()
    elif args.action == 'switch':
        if not args.args:
            console.print('[red]❌ Profile name required[/red]')
            console.print('Usage: profile_manager switch <profile_name>')
            sys.exit(1)
        manager.switch_profile(args.args[0])
    elif args.action == 'create':
        if not args.args:
            console.print('[red]❌ Profile name required[/red]')
            console.print('Usage: profile_manager create <profile_name> [description]')
            sys.exit(1)
        profile_name = args.args[0]
        description = ' '.join(args.args[1:]) if len(args.args) > 1 else ''
        manager.create_profile(profile_name, description)
    elif args.action == 'delete':
        if not args.args:
            console.print('[red]❌ Profile name required[/red]')
            console.print('Usage: profile_manager delete <profile_name>')
            sys.exit(1)
        manager.delete_profile(args.args[0])
    elif args.action == 'compare':
        if len(args.args) < 2:
            console.print('[red]❌ Two profile names required[/red]')
            console.print('Usage: profile_manager compare <profile1> <profile2>')
            sys.exit(1)
        manager.compare_profiles(args.args[0], args.args[1])
    elif args.action == 'export':
        if len(args.args) < 2:
            console.print('[red]❌ Profile name and export path required[/red]')
            console.print('Usage: profile_manager export <profile_name> <export_path>')
            sys.exit(1)
        manager.export_profile(args.args[0], Path(args.args[1]))
    elif args.action == 'import':
        if not args.args:
            console.print('[red]❌ Import path required[/red]')
            console.print('Usage: profile_manager import <import_path> [profile_name]')
            sys.exit(1)
        import_path = Path(args.args[0])
        profile_name = args.args[1] if len(args.args) > 1 else None
        manager.import_profile(import_path, profile_name)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/crosstalk_engine.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/crosstalk_engine.py`

**Module Overview**: 
```text
Crosstalk Engine - Async Multi-Model Conversation Executor

Executes crosstalk sessions by routing messages between models in sequence,
applying jinja templates, and managing conversation history.

Paradigms:
- relay: Each model gets only the previous model's response
- memory: Each model gets full conversation history
- report: Models summarize before passing to next
- debate: Models can challenge and critique each other
```

## Global Presets & Variables
- `console` = `Console()`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent`
- `TEMPLATES_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'templates'`
- `SESSIONS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'sessions'`
- `CHECKPOINTS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'checkpoints'`

## Dependencies & Imports
asyncio, json, os, time, httpx, datetime.datetime, pathlib.Path, typing.List, typing.Dict, typing.Any, typing.Optional, typing.AsyncGenerator, dataclasses.dataclass, dataclasses.asdict, dataclasses.field, jinja2.Template, rich.console.Console, rich.panel.Panel, rich.live.Live, rich.text.Text, rich.markdown.Markdown

## Feature Class: `Message`
**Description:**
```text
A single message in the conversation.
```

### Method: `__post_init__`
**Parameters:** `self`
**Implementation:**
```python
def __post_init__(self):
    if not self.timestamp:
        self.timestamp = datetime.now().isoformat()
```

---

## Feature Class: `ConversationTranscript`
**Description:**
```text
Full conversation record.
```

### Method: `save`
**Logic & Purpose:**
```text
Save transcript to JSON file.
```

**Parameters:** `self, filename`
**Variables Used:** `filename, timestamp, data`
**Implementation:**
```python
def save(self, filename: Optional[str]=None) -> Path:
    """Save transcript to JSON file."""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = SESSIONS_DIR / f'session_{timestamp}.json'
    else:
        filename = Path(filename)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    data = {'messages': [asdict(m) for m in self.messages], 'config': self.config, 'started_at': self.started_at, 'ended_at': self.ended_at or datetime.now().isoformat()}
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return filename
```

### Method: `save_markdown`
**Logic & Purpose:**
```text
Save transcript to Markdown file.
```

**Parameters:** `self, filename`
**Variables Used:** `model_name, timestamp, md, models, filename`
**Implementation:**
```python
def save_markdown(self, filename: Optional[str]=None) -> Path:
    """Save transcript to Markdown file."""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = SESSIONS_DIR / f'session_{timestamp}.md'
    else:
        filename = Path(filename)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    md = '# Crosstalk Session\n\n'
    md += f'**Started:** {self.started_at}\n'
    md += f'**Ended:** {self.ended_at}\n'
    md += f"**Paradigm:** {self.config.get('paradigm', 'relay')}\n"
    md += f"**Topology:** {self.config.get('topology', {}).get('type', 'ring')}\n"
    models = self.config.get('models', [])
    if models:
        md += f"**Models:** {', '.join((m.get('model_id', 'unknown') for m in models))}\n"
    md += '\n---\n\n'
    for msg in self.messages:
        if msg.slot_id == 0:
            md += f'## 💬 User\n\n{msg.content}\n\n---\n\n'
        else:
            model_name = msg.model_id.split('/')[-1] if '/' in msg.model_id else msg.model_id
            md += f'## 🤖 AI {msg.slot_id} ({model_name})\n\n{msg.content}\n\n---\n\n'
    with open(filename, 'w') as f:
        f.write(md)
    return filename
```

---

## Feature Function: `load_template`
**Logic & Purpose:**
```text
Load a jinja template by name.
```

**Parameters:** `template_name`
**Variables Used:** `template_path`
**Implementation:**
```python
def load_template(template_name: str) -> Template:
    """Load a jinja template by name."""
    template_path = TEMPLATES_DIR / f'{template_name}.j2'
    if template_path.exists():
        return Template(template_path.read_text())
    from src.cli.crosstalk_studio import DEFAULT_TEMPLATES
    if template_name in DEFAULT_TEMPLATES:
        return Template(DEFAULT_TEMPLATES[template_name])
    return Template('{{ message }}')
```

---

## Feature Function: `apply_template`
**Logic & Purpose:**
```text
Apply a jinja template to a message.
```

**Parameters:** `template_name, message, context`
**Variables Used:** `template, ctx`
**Implementation:**
```python
def apply_template(template_name: str, message: str, context: Dict[str, Any]=None) -> str:
    """Apply a jinja template to a message."""
    template = load_template(template_name)
    ctx = {'message': message}
    if context:
        ctx.update(context)
    return template.render(**ctx)
```

---

## Feature Function: `call_model`
**Logic & Purpose:**
```text
Call a model via OpenRouter API with streaming.

Yields chunks of the response.

Args:
    endpoint: Custom API endpoint (defaults to OpenRouter)
    api_key_env: Environment variable name for API key
```

**Parameters:** `model_id, messages, system_prompt, temperature, max_tokens, stream, endpoint, api_key_env`
**Variables Used:** `api_messages, chunk, proxy_port, api_key, data, api_endpoint, response, content, delta`
**Implementation:**
```python
async def call_model(model_id: str, messages: List[Dict[str, str]], system_prompt: str='', temperature: float=0.9, max_tokens: int=4096, stream: bool=True, endpoint: str='', api_key_env: str='') -> AsyncGenerator[str, None]:
    """
    Call a model via OpenRouter API with streaming.
    
    Yields chunks of the response.
    
    Args:
        endpoint: Custom API endpoint (defaults to OpenRouter)
        api_key_env: Environment variable name for API key
    """
    if api_key_env:
        api_key = os.environ.get(api_key_env)
    else:
        api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('PROVIDER_API_KEY')
    if not api_key:
        yield '[ERROR: No API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY]'
        return
    api_messages = []
    if system_prompt:
        api_messages.append({'role': 'system', 'content': system_prompt})
    api_messages.extend(messages)
    if endpoint:
        api_endpoint = endpoint
    elif os.environ.get('USE_LOCAL_PROXY', '').lower() in ('true', '1', 'yes'):
        proxy_port = os.environ.get('PORT', '8082')
        api_endpoint = f'http://localhost:{proxy_port}/v1/chat/completions'
        print(f'[Crosstalk] Routing through local proxy: {api_endpoint}')
    else:
        api_endpoint = 'https://openrouter.ai/api/v1/chat/completions'
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(api_endpoint, headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json', 'HTTP-Referer': 'https://github.com/crosstalk-studio', 'X-Title': 'Crosstalk Studio'}, json={'model': model_id, 'messages': api_messages, 'temperature': temperature, 'max_tokens': max_tokens, 'stream': stream})
            if response.status_code != 200:
                yield f'[ERROR: HTTP {response.status_code}]'
                return
            if stream:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                yield content
        except Exception as e:
            yield f'[ERROR: {str(e)}]'
```

---

## Feature Function: `build_messages_relay`
**Logic & Purpose:**
```text
Relay paradigm: Model only sees the previous message.
```

**Parameters:** `conversation, current_slot`
**Implementation:**
```python
def build_messages_relay(conversation: List[Message], current_slot: int) -> List[Dict[str, str]]:
    """
    Relay paradigm: Model only sees the previous message.
    """
    for msg in reversed(conversation):
        if msg.slot_id != current_slot:
            return [{'role': 'user', 'content': msg.content}]
    return []
```

---

## Feature Function: `build_messages_memory`
**Logic & Purpose:**
```text
Memory paradigm: Model sees full conversation history.
```

**Parameters:** `conversation, current_slot`
**Variables Used:** `role, messages`
**Implementation:**
```python
def build_messages_memory(conversation: List[Message], current_slot: int) -> List[Dict[str, str]]:
    """
    Memory paradigm: Model sees full conversation history.
    """
    messages = []
    for msg in conversation:
        role = 'assistant' if msg.slot_id == current_slot else 'user'
        messages.append({'role': role, 'content': msg.content})
    return messages
```

---

## Feature Function: `build_messages_debate`
**Logic & Purpose:**
```text
Debate paradigm: Model sees history and is encouraged to critique.
```

**Parameters:** `conversation, current_slot`
**Variables Used:** `messages`
**Implementation:**
```python
def build_messages_debate(conversation: List[Message], current_slot: int) -> List[Dict[str, str]]:
    """
    Debate paradigm: Model sees history and is encouraged to critique.
    """
    messages = build_messages_memory(conversation, current_slot)
    if messages:
        messages.append({'role': 'user', 'content': '[DEBATE MODE: Challenge, critique, or extend the previous arguments. Be rigorous.]'})
    return messages
```

---

## Feature Function: `get_model_order_ring`
**Logic & Purpose:**
```text
Ring topology: Sequential or custom order.
```

**Parameters:** `models, topology`
**Variables Used:** `order_map`
**Implementation:**
```python
def get_model_order_ring(models, topology) -> List:
    """Ring topology: Sequential or custom order."""
    if topology.order:
        order_map = {m.slot_id: m for m in models}
        return [order_map.get(slot_id, models[0]) for slot_id in topology.order if slot_id in order_map]
    return models
```

---

## Feature Function: `get_model_order_star`
**Logic & Purpose:**
```text
Star topology: Center speaks to each spoke, spokes respond to center.
```

**Parameters:** `models, topology`
**Variables Used:** `result, spokes, center, center_id`
**Implementation:**
```python
def get_model_order_star(models, topology) -> List:
    """Star topology: Center speaks to each spoke, spokes respond to center."""
    center_id = topology.center
    center = next((m for m in models if m.slot_id == center_id), models[0])
    spokes = [m for m in models if m.slot_id != center_id]
    result = []
    for spoke in spokes:
        result.append(center)
        result.append(spoke)
    return result
```

---

## Feature Function: `get_model_order_mesh`
**Logic & Purpose:**
```text
Mesh topology: Every model talks to every other model.
```

**Parameters:** `models, topology`
**Variables Used:** `result`
**Implementation:**
```python
def get_model_order_mesh(models, topology) -> List:
    """Mesh topology: Every model talks to every other model."""
    result = []
    for speaker in models:
        for listener in models:
            if speaker.slot_id != listener.slot_id:
                result.append(speaker)
    return result
```

---

## Feature Function: `get_model_order_chain`
**Logic & Purpose:**
```text
Chain topology: Linear progression, same as ring but conceptually different.
```

**Parameters:** `models, topology`
**Implementation:**
```python
def get_model_order_chain(models, topology) -> List:
    """Chain topology: Linear progression, same as ring but conceptually different."""
    return models
```

---

## Feature Function: `get_model_order_random`
**Logic & Purpose:**
```text
Random topology: Shuffle models each round.
```

**Parameters:** `models, topology`
**Variables Used:** `shuffled`
**Implementation:**
```python
def get_model_order_random(models, topology) -> List:
    """Random topology: Shuffle models each round."""
    import random
    shuffled = models.copy()
    random.shuffle(shuffled)
    return shuffled
```

---

## Feature Function: `get_model_order_custom`
**Logic & Purpose:**
```text
Custom topology: Use exact pattern specified.
```

**Parameters:** `models, topology`
**Variables Used:** `pattern, seen`
**Implementation:**
```python
def get_model_order_custom(models, topology) -> List:
    """Custom topology: Use exact pattern specified."""
    pattern = topology.pattern if hasattr(topology, 'pattern') and topology.pattern else []
    if not pattern:
        return models
    seen = []
    for speaker, _ in pattern:
        if speaker not in seen:
            for m in models:
                if m.slot_id == speaker:
                    seen.append(m)
                    break
    return seen if seen else models
```

---

## Feature Function: `get_model_order_tournament`
**Logic & Purpose:**
```text
Tournament topology: Bracket-style elimination.
```

**Parameters:** `models, topology`
**Implementation:**
```python
def get_model_order_tournament(models, topology) -> List:
    """Tournament topology: Bracket-style elimination."""
    return models[:2] if len(models) >= 2 else models
```

---

## Feature Function: `generate_summary`
**Logic & Purpose:**
```text
Generate a summary of the conversation so far.
```

**Parameters:** `conversation, summarizer_model, summary_prompt`
**Variables Used:** `conv_text, messages, summary`
**Implementation:**
```python
async def generate_summary(conversation: List[Message], summarizer_model: str='anthropic/claude-3-haiku', summary_prompt: str='Summarize the key points of this discussion so far in 2-3 sentences.') -> str:
    """Generate a summary of the conversation so far."""
    conv_text = '\n\n'.join([f'[{m.model_id}]: {m.content[:500]}...' if len(m.content) > 500 else f'[{m.model_id}]: {m.content}' for m in conversation[-20:]])
    messages = [{'role': 'user', 'content': f'{summary_prompt}\n\nConversation:\n{conv_text}'}]
    summary = ''
    async for chunk in call_model(model_id=summarizer_model, messages=messages, system_prompt='You are a concise summarizer. Provide brief, accurate summaries.', temperature=0.3, max_tokens=500, stream=True):
        summary += chunk
    return summary
```

---

## Feature Function: `save_checkpoint`
**Logic & Purpose:**
```text
Save a checkpoint of the current conversation state.
```

**Parameters:** `transcript, session_id, turn`
**Variables Used:** `checkpoint_file, data`
**Implementation:**
```python
def save_checkpoint(transcript: 'ConversationTranscript', session_id: str, turn: int) -> Path:
    """Save a checkpoint of the current conversation state."""
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_file = CHECKPOINTS_DIR / f'{session_id}_turn_{turn}.json'
    data = {'messages': [asdict(m) for m in transcript.messages], 'config': transcript.config, 'started_at': transcript.started_at, 'checkpoint_turn': turn, 'checkpoint_time': datetime.now().isoformat()}
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)
    console.print(f'[dim]💾 Checkpoint saved: turn {turn}[/]')
    return checkpoint_file
```

---

## Feature Function: `load_checkpoint`
**Logic & Purpose:**
```text
Load a checkpoint file.
```

**Parameters:** `checkpoint_file`
**Implementation:**
```python
def load_checkpoint(checkpoint_file: Path) -> Dict[str, Any]:
    """Load a checkpoint file."""
    with open(checkpoint_file, 'r') as f:
        return json.load(f)
```

---

## Feature Function: `apply_context_modifiers`
**Logic & Purpose:**
```text
Apply append/prepend context modifiers to a message.

Args:
    message: The original message
    model_slot: The model slot with optional append/prepend fields
    is_input: True if this is input to the model (append), False if output (prepend)
```

**Parameters:** `message, model_slot, is_input`
**Variables Used:** `message, append, prepend`
**Implementation:**
```python
def apply_context_modifiers(message: str, model_slot, is_input: bool=True) -> str:
    """
    Apply append/prepend context modifiers to a message.
    
    Args:
        message: The original message
        model_slot: The model slot with optional append/prepend fields
        is_input: True if this is input to the model (append), False if output (prepend)
    """
    append = getattr(model_slot, 'append', None) or ''
    prepend = getattr(model_slot, 'prepend', None) or ''
    if is_input and append:
        message = f'{message}\n\n{append}'
    elif not is_input and prepend:
        message = f'{prepend}{message}'
    return message
```

---

## Feature Function: `calculate_similarity`
**Logic & Purpose:**
```text
Calculate simple Jaccard similarity between two texts.
```

**Parameters:** `text1, text2`
**Variables Used:** `words1, intersection, union, words2`
**Implementation:**
```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple Jaccard similarity between two texts."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0
```

---

## Feature Function: `detect_repetition`
**Logic & Purpose:**
```text
Detect if the conversation has become repetitive.

Returns True if recent messages are too similar.
```

**Parameters:** `conversation, threshold`
**Variables Used:** `similarity, recent`
**Implementation:**
```python
def detect_repetition(conversation: List[Message], threshold: float=0.85) -> bool:
    """
    Detect if the conversation has become repetitive.
    
    Returns True if recent messages are too similar.
    """
    if len(conversation) < 4:
        return False
    recent = [m.content for m in conversation[-4:] if m.role == 'assistant']
    if len(recent) < 2:
        return False
    for i in range(len(recent) - 1):
        similarity = calculate_similarity(recent[i], recent[i + 1])
        if similarity > threshold:
            return True
    return False
```

---

## Feature Class: `Vote`
**Description:**
```text
A single vote from a model.
```

---

## Feature Function: `tally_votes`
**Logic & Purpose:**
```text
Tally votes and determine consensus.

Methods:
    - majority: Simple majority wins
    - weighted: Weighted by model confidence or custom weights
    - unanimous: All must agree

Returns dict with:
    - winner: The winning choice
    - counts: Vote counts per choice
    - consensus: Whether consensus was reached
```

**Parameters:** `votes, method, weights`
**Variables Used:** `weights, winner, total, sorted_choices, consensus, weight`
**Implementation:**
```python
def tally_votes(votes: List[Vote], method: str='majority', weights: Dict[int, float]=None) -> Dict[str, Any]:
    """
    Tally votes and determine consensus.
    
    Methods:
        - majority: Simple majority wins
        - weighted: Weighted by model confidence or custom weights
        - unanimous: All must agree
    
    Returns dict with:
        - winner: The winning choice
        - counts: Vote counts per choice
        - consensus: Whether consensus was reached
    """
    if not votes:
        return {'winner': None, 'counts': {}, 'consensus': False}
    weights = weights or {}
    counts: Dict[str, float] = {}
    for vote in votes:
        weight = weights.get(vote.slot_id, 1.0) * vote.confidence
        counts[vote.choice] = counts.get(vote.choice, 0) + weight
    sorted_choices = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_choices[0][0] if sorted_choices else None
    if method == 'unanimous':
        consensus = len(set((v.choice for v in votes))) == 1
    elif method == 'majority':
        total = sum(counts.values())
        consensus = counts.get(winner, 0) > total / 2
    else:
        consensus = True
    return {'winner': winner, 'counts': dict(counts), 'consensus': consensus, 'method': method}
```

---

## Feature Function: `request_vote`
**Logic & Purpose:**
```text
Request a vote from a model on a question.
```

**Parameters:** `model_slot, question, options, conversation`
**Variables Used:** `reasoning, choice_text, messages, choice, response, options_str, vote_prompt`
**Implementation:**
```python
async def request_vote(model_slot, question: str, options: List[str], conversation: List[Message]) -> Vote:
    """Request a vote from a model on a question."""
    options_str = ', '.join(options)
    vote_prompt = f'\nBased on the discussion so far, please vote on this question:\n\n{question}\n\nOptions: {options_str}\n\nRespond with ONLY your choice from the options, followed by a brief reason.\nFormat: CHOICE: [your choice]\nREASON: [brief explanation]\n'
    messages = [{'role': 'user', 'content': vote_prompt}]
    response = ''
    async for chunk in call_model(model_id=model_slot.model_id, messages=messages, system_prompt='You are participating in a vote. Be decisive.', temperature=0.3, max_tokens=200):
        response += chunk
    choice = options[0]
    reasoning = ''
    for line in response.split('\n'):
        if line.upper().startswith('CHOICE:'):
            choice_text = line.split(':', 1)[1].strip()
            for opt in options:
                if opt.lower() in choice_text.lower():
                    choice = opt
                    break
        elif line.upper().startswith('REASON:'):
            reasoning = line.split(':', 1)[1].strip()
    return Vote(model_id=model_slot.model_id, slot_id=model_slot.slot_id, choice=choice, confidence=1.0, reasoning=reasoning)
```

---

## Feature Class: `RoutingRule`
**Description:**
```text
A rule for conditional message routing.
```

---

## Feature Function: `evaluate_routing_rules`
**Logic & Purpose:**
```text
Evaluate routing rules against a message.

Returns the slot ID to route to, or None if no rule matches.
```

**Parameters:** `message, rules, default_route`
**Variables Used:** `keywords`
**Implementation:**
```python
def evaluate_routing_rules(message: str, rules: List[RoutingRule], default_route: int=None) -> Optional[int]:
    """
    Evaluate routing rules against a message.
    
    Returns the slot ID to route to, or None if no rule matches.
    """
    for rule in rules:
        if rule.condition_type == 'keyword':
            keywords = rule.condition_value if isinstance(rule.condition_value, list) else [rule.condition_value]
            for kw in keywords:
                if kw.lower() in message.lower():
                    return rule.route_to
        elif rule.condition_type == 'length':
            if len(message) > rule.condition_value:
                return rule.route_to
        elif rule.condition_type == 'question':
            if '?' in message:
                return rule.route_to
    return default_route
```

---

## Feature Class: `ConversationStage`
**Description:**
```text
A stage in a multi-stage conversation.
```

---

## Feature Function: `run_crosstalk`
**Logic & Purpose:**
```text
Execute a crosstalk session.

Args:
    session: CrosstalkSession object with models, rounds, etc.

Returns:
    ConversationTranscript with full conversation record
```

**Parameters:** `session`
**Variables Used:** `total_cost, weights, max_rounds, vote_msg, should_stop, elapsed_str, summarize_every, mode_str, topo_generators, method, msg, initial_msg, stop_conditions, options, final_vote, elapsed, full_response, build_messages, start_time, summarizer_model, messages, model_order, templated, session_id, checkpoint_every, result, summary_msg, last_content, topology, slot_id, infinite, votes, summary, topo_type, transcript, question, filename, model_id, round_num, stop_reason, vote, get_order, paradigm_builders`
**Implementation:**
```python
async def run_crosstalk(session) -> Optional[ConversationTranscript]:
    """
    Execute a crosstalk session.
    
    Args:
        session: CrosstalkSession object with models, rounds, etc.
    
    Returns:
        ConversationTranscript with full conversation record
    """
    from src.cli.crosstalk_studio import ModelSlot, CrosstalkSession, TopologyConfig, StopConditions
    topology = getattr(session, 'topology', None)
    topo_type = topology.type if topology else 'ring'
    infinite = getattr(session, 'infinite', False)
    stop_conditions = getattr(session, 'stop_conditions', None)
    summarize_every = getattr(session, 'summarize_every', 0)
    mode_str = '∞ infinite' if infinite else f'{session.rounds} rounds'
    console.print(Panel(f'[bold cyan]🔮 CROSSTALK SESSION STARTING[/]\n\n[dim]Models: {len(session.models)} | Mode: {mode_str} | Paradigm: {session.paradigm} | Topology: {topo_type}[/]', border_style='cyan'))
    conversation: List[Message] = []
    transcript = ConversationTranscript(messages=[], config={'models': [asdict(m) for m in session.models], 'rounds': session.rounds, 'paradigm': session.paradigm, 'topology': asdict(topology) if topology else {'type': 'ring'}, 'infinite': infinite, 'initial_prompt': session.initial_prompt}, started_at=datetime.now().isoformat())
    initial_msg = Message(role='user', content=session.initial_prompt, model_id='user', slot_id=0)
    conversation.append(initial_msg)
    transcript.messages.append(initial_msg)
    console.print(f'\n[bold magenta]USER:[/] {session.initial_prompt}\n')
    paradigm_builders = {'relay': build_messages_relay, 'memory': build_messages_memory, 'debate': build_messages_debate, 'report': build_messages_relay}
    build_messages = paradigm_builders.get(session.paradigm, build_messages_relay)
    topo_generators = {'ring': get_model_order_ring, 'star': get_model_order_star, 'mesh': get_model_order_mesh, 'chain': get_model_order_chain, 'random': get_model_order_random, 'custom': get_model_order_custom, 'tournament': get_model_order_tournament}
    get_order = topo_generators.get(topo_type, get_model_order_ring)
    try:
        round_num = 0
        max_rounds = 10000 if infinite else session.rounds
        start_time = time.time()
        total_cost = 0.0
        should_stop = False
        stop_reason = ''
        while round_num < max_rounds and (not should_stop):
            round_num += 1
            if stop_conditions and stop_conditions.max_time_seconds > 0:
                elapsed = time.time() - start_time
                if elapsed >= stop_conditions.max_time_seconds:
                    stop_reason = f'⏱️  Time limit ({stop_conditions.max_time_seconds}s)'
                    should_stop = True
                    break
            if stop_conditions and stop_conditions.max_cost_dollars > 0:
                if total_cost >= stop_conditions.max_cost_dollars:
                    stop_reason = f'💰 Cost limit (${stop_conditions.max_cost_dollars:.2f})'
                    should_stop = True
                    break
            if infinite:
                elapsed_str = f'{time.time() - start_time:.0f}s'
                console.print(f'\n[bold white]━━━ ROUND {round_num} (∞) [{elapsed_str}] ━━━[/]\n')
            else:
                console.print(f'\n[bold white]━━━ ROUND {round_num}/{session.rounds} ━━━[/]\n')
            model_order = get_order(session.models, topology)
            for model_slot in model_order:
                slot_id = model_slot.slot_id
                model_id = model_slot.model_id
                console.print(f'[bold cyan]AI {slot_id} ({model_slot.display_name}):[/]')
                messages = build_messages(conversation, slot_id)
                if messages:
                    last_content = messages[-1]['content']
                    templated = apply_template(model_slot.jinja_template, last_content, {'round': round_num, 'slot': slot_id, 'model': model_id})
                    messages[-1]['content'] = templated
                full_response = ''
                async for chunk in call_model(model_id=model_id, messages=messages, system_prompt=model_slot.system_prompt, temperature=model_slot.temperature, max_tokens=model_slot.max_tokens, stream=True, endpoint=getattr(model_slot, 'endpoint', '') or '', api_key_env=getattr(model_slot, 'api_key_env', '') or ''):
                    full_response += chunk
                    console.print(chunk, end='')
                console.print('\n')
                total_cost += len(full_response) * 1e-06
                if stop_conditions and stop_conditions.stop_keywords:
                    for kw in stop_conditions.stop_keywords:
                        if kw.lower() in full_response.lower():
                            stop_reason = f"🔑 Stop keyword: '{kw}'"
                            should_stop = True
                            break
                msg = Message(role='assistant', content=full_response, model_id=model_id, slot_id=slot_id)
                conversation.append(msg)
                transcript.messages.append(msg)
            if summarize_every > 0 and round_num % summarize_every == 0:
                console.print(f'\n[bold yellow]📝 Generating summary...[/]')
                summarizer_model = session.models[0].model_id if session.models else 'anthropic/claude-3-haiku'
                summary = await generate_summary(conversation, summarizer_model=summarizer_model, summary_prompt='Summarize the key points and progress made so far.')
                summary_msg = Message(role='system', content=f'[SUMMARY after round {round_num}]: {summary}', model_id='summarizer', slot_id=0)
                conversation.append(summary_msg)
                transcript.messages.append(summary_msg)
                console.print(f'[dim]Summary: {summary[:200]}...[/]\n')
            checkpoint_every = getattr(session, 'checkpoint_every', 10) if infinite else 0
            if checkpoint_every > 0 and round_num % checkpoint_every == 0:
                session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_checkpoint(transcript, session_id, round_num)
            if infinite and detect_repetition(conversation):
                stop_reason = '🔄 Conversation became repetitive'
                should_stop = True
        final_vote = getattr(session, 'final_round_vote', None)
        if final_vote and (not should_stop):
            console.print(Panel('[bold yellow]🗳️ FINAL ROUND VOTING[/]', border_style='yellow'))
            question = final_vote.get('question', 'What is your final verdict?')
            options = final_vote.get('options', ['yes', 'no', 'undecided'])
            method = final_vote.get('tally_method', 'majority')
            weights = final_vote.get('weights', {})
            votes = []
            for model_slot in session.models:
                console.print(f'[dim]Requesting vote from {model_slot.display_name}...[/]')
                vote = await request_vote(model_slot, question, options, conversation)
                votes.append(vote)
                console.print(f'  [cyan]{model_slot.display_name}[/]: {vote.choice} - {vote.reasoning[:50]}...')
            result = tally_votes(votes, method=method, weights=weights)
            console.print(Panel(f"[bold]Vote Results:[/]\n\nWinner: [bold cyan]{result['winner']}[/]\nCounts: {result['counts']}\nConsensus: {('✓ Yes' if result['consensus'] else '✗ No')}", border_style='green' if result['consensus'] else 'yellow'))
            vote_msg = Message(role='system', content=f"[VOTE RESULT]: Winner={result['winner']}, Counts={result['counts']}, Consensus={result['consensus']}", model_id='voting_system', slot_id=0)
            transcript.messages.append(vote_msg)
        transcript.ended_at = datetime.now().isoformat()
        elapsed = time.time() - start_time
        if should_stop and stop_reason:
            console.print(Panel(f'[bold yellow]⚡ SESSION STOPPED[/]\n\n[dim]Reason: {stop_reason}[/]\n[dim]Rounds: {round_num} | Messages: {len(transcript.messages)} | Time: {elapsed:.1f}s | Est. cost: ${total_cost:.4f}[/]', border_style='yellow'))
        else:
            console.print(Panel(f'[bold green]✓ CROSSTALK SESSION COMPLETE[/]\n\n[dim]Messages: {len(transcript.messages)} | Time: {elapsed:.1f}s | Est. cost: ${total_cost:.4f}[/]', border_style='green'))
        from rich.prompt import Confirm
        if Confirm.ask('\nSave transcript?'):
            filename = transcript.save()
            console.print(f'[green]Saved: {filename}[/]')
        input('\nPress Enter to continue...')
        return transcript
    except KeyboardInterrupt:
        console.print('\n[yellow]Session interrupted by user[/]')
        transcript.ended_at = datetime.now().isoformat()
        from rich.prompt import Confirm
        if Confirm.ask('Save partial transcript?'):
            filename = transcript.save()
            console.print(f'[green]Saved: {filename}[/]')
        input('\nPress Enter to continue...')
        return transcript
    except Exception as e:
        console.print(f'\n[red]Error during session: {e}[/]')
        import traceback
        traceback.print_exc()
        input('\nPress Enter to continue...')
        return None
```

---

## Feature Function: `quick_crosstalk`
**Logic & Purpose:**
```text
Quick crosstalk session from command line.
```

**Parameters:** `prompt, model1, model2, rounds, paradigm`
**Variables Used:** `session`
**Implementation:**
```python
async def quick_crosstalk(prompt: str, model1: str='anthropic/claude-3-opus', model2: str='anthropic/claude-3-opus', rounds: int=3, paradigm: str='relay'):
    """Quick crosstalk session from command line."""
    from src.cli.crosstalk_studio import CrosstalkSession, ModelSlot
    session = CrosstalkSession(models=[ModelSlot(slot_id=1, model_id=model1), ModelSlot(slot_id=2, model_id=model2)], rounds=rounds, paradigm=paradigm, initial_prompt=prompt)
    await run_crosstalk(session)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/backrooms_importer.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/backrooms_importer.py`

**Module Overview**: 
```text
Dreams of an Electric Mind Importer

Imports configuration from Andy Ayrey's Infinite Backrooms format.
Parses URLs from dreams-of-an-electric-mind.webflow.io and extracts:
- actors (persona names)
- models (model IDs)
- temp (temperatures)
- system prompts per actor
- context arrays

Also exports sessions in compatible format.

Reference: https://dreams-of-an-electric-mind.webflow.io/
```

## Dependencies & Imports
re, json, httpx, dataclasses.dataclass, typing.List, typing.Dict, typing.Optional, typing.Tuple, pathlib.Path

## Feature Class: `BackroomsActor`
**Description:**
```text
Actor configuration from Infinite Backrooms format.
```

---

## Feature Class: `BackroomsConfig`
**Description:**
```text
Full configuration parsed from Infinite Backrooms.
```

---

## Feature Function: `parse_backrooms_config`
**Logic & Purpose:**
```text
Parse Infinite Backrooms configuration from raw text.

Format example:
```
actors: backrooms-8b-schizo-magic, claude-4-freeform
models: openpipe:backrooms-fullset-8b, claude-sonnet-4-20250514
temp: 0.96, 1

<backrooms-8b-schizo-magic-openpipe:backrooms-fullset-8b#SYSTEM>
System prompt here

<claude-4-freeform-claude-sonnet-4-20250514#SYSTEM>
Another system prompt
```
```

**Parameters:** `text, source_url`
**Variables Used:** `actors_match, models_match, temps, system_prompt, actors, model_id, temp, context, sys_match, ctx_match, model_ids, pattern, ctx_pattern, name_match, temps_match, actor_names, scenario_name`
**Implementation:**
```python
def parse_backrooms_config(text: str, source_url: str='') -> Optional[BackroomsConfig]:
    """
    Parse Infinite Backrooms configuration from raw text.
    
    Format example:
    ```
    actors: backrooms-8b-schizo-magic, claude-4-freeform
    models: openpipe:backrooms-fullset-8b, claude-sonnet-4-20250514
    temp: 0.96, 1
    
    <backrooms-8b-schizo-magic-openpipe:backrooms-fullset-8b#SYSTEM>
    System prompt here
    
    <claude-4-freeform-claude-sonnet-4-20250514#SYSTEM>
    Another system prompt
    ```
    """
    actors = []
    actors_match = re.search('actors:\\s*([^\\n]+)', text)
    if not actors_match:
        return None
    actor_names = [a.strip() for a in actors_match.group(1).split(',')]
    models_match = re.search('models:\\s*([^\\n]+)', text)
    if not models_match:
        return None
    model_ids = [m.strip() for m in models_match.group(1).split(',')]
    temps_match = re.search('temp:\\s*([^\\n]+)', text)
    temps = [0.9] * len(actor_names)
    if temps_match:
        try:
            temps = [float(t.strip()) for t in temps_match.group(1).split(',')]
        except ValueError:
            pass
    while len(model_ids) < len(actor_names):
        model_ids.append(model_ids[-1] if model_ids else 'anthropic/claude-3-opus')
    while len(temps) < len(actor_names):
        temps.append(temps[-1] if temps else 0.9)
    for i, actor_name in enumerate(actor_names):
        model_id = model_ids[i]
        temp = temps[i]
        system_prompt = ''
        context = []
        pattern = f'<{re.escape(actor_name)}-[^#]+#SYSTEM>\\s*(.*?)(?=<[^>]+#|$)'
        sys_match = re.search(pattern, text, re.DOTALL)
        if sys_match:
            system_prompt = sys_match.group(1).strip()
            system_prompt = system_prompt.replace('\\n', '\n').replace('\\\\n', '\n')
        ctx_pattern = f'<{re.escape(actor_name)}-[^#]+#CONTEXT>\\s*(\\[.*?\\])'
        ctx_match = re.search(ctx_pattern, text, re.DOTALL)
        if ctx_match:
            try:
                context = json.loads(ctx_match.group(1).replace('\\n', '\n'))
            except json.JSONDecodeError:
                pass
        if not '/' in model_id and ':' in model_id:
            model_id = model_id.split(':')[-1]
        elif not '/' in model_id:
            if 'claude' in model_id.lower():
                model_id = f'anthropic/{model_id}'
            elif 'gpt' in model_id.lower():
                model_id = f'openai/{model_id}'
            elif 'gemini' in model_id.lower():
                model_id = f'google/{model_id}'
        actors.append(BackroomsActor(name=actor_name, model_id=model_id, temperature=temp, system_prompt=system_prompt, context=context))
    scenario_name = 'imported'
    if source_url:
        name_match = re.search('scenario[_-]([^.]+)', source_url)
        if name_match:
            scenario_name = name_match.group(1)
    return BackroomsConfig(actors=actors, scenario_name=scenario_name, source_url=source_url)
```

---

## Feature Function: `fetch_backrooms_url`
**Logic & Purpose:**
```text
Fetch and parse configuration from a Dreams of Electric Mind URL.

Args:
    url: URL to a conversation page on dreams-of-an-electric-mind.webflow.io
    
Returns:
    BackroomsConfig if parsing succeeds, None otherwise
```

**Parameters:** `url`
**Variables Used:** `text, pre_match, response, config_text, code_match`
**Implementation:**
```python
async def fetch_backrooms_url(url: str) -> Optional[BackroomsConfig]:
    """
    Fetch and parse configuration from a Dreams of Electric Mind URL.
    
    Args:
        url: URL to a conversation page on dreams-of-an-electric-mind.webflow.io
        
    Returns:
        BackroomsConfig if parsing succeeds, None otherwise
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            text = response.text
            code_match = re.search('<code[^>]*>(.*?)</code>', text, re.DOTALL)
            if code_match:
                config_text = code_match.group(1)
                config_text = config_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                return parse_backrooms_config(config_text, url)
            pre_match = re.search('```(.*?)```', text, re.DOTALL)
            if pre_match:
                return parse_backrooms_config(pre_match.group(1), url)
            return None
        except Exception as e:
            print(f'Error fetching URL: {e}')
            return None
```

---

## Feature Function: `export_backrooms_format`
**Logic & Purpose:**
```text
Export session in Infinite Backrooms compatible format.

Args:
    actors: List of actor configurations
    conversation: List of conversation messages
    scenario_name: Name for this scenario
    
Returns:
    Text in Infinite Backrooms format
```

**Parameters:** `actors, conversation, scenario_name`
**Variables Used:** `temps, system, lines, model_ids, content, actor_names, role, name, model`
**Implementation:**
```python
def export_backrooms_format(actors: List[Dict], conversation: List[Dict], scenario_name: str='crosstalk') -> str:
    """
    Export session in Infinite Backrooms compatible format.
    
    Args:
        actors: List of actor configurations
        conversation: List of conversation messages
        scenario_name: Name for this scenario
        
    Returns:
        Text in Infinite Backrooms format
    """
    lines = []
    actor_names = [a.get('name', f'ai_{i + 1}') for i, a in enumerate(actors)]
    model_ids = [a.get('model_id', 'unknown') for a in actors]
    temps = [str(a.get('temperature', 0.9)) for a in actors]
    lines.append(f"actors: {', '.join(actor_names)}")
    lines.append(f"models: {', '.join(model_ids)}")
    lines.append(f"temp: {', '.join(temps)}")
    lines.append('')
    for actor in actors:
        name = actor.get('name', 'unknown')
        model = actor.get('model_id', 'unknown')
        system = actor.get('system_prompt', '')
        lines.append(f'<{name}-{model}#SYSTEM>')
        lines.append(system)
        lines.append('')
    lines.append('---CONVERSATION---')
    lines.append('')
    for msg in conversation:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        model = msg.get('model_id', 'unknown')
        lines.append(f'<{role}|{model}>')
        lines.append(content)
        lines.append('')
    return '\n'.join(lines)
```

---

## Feature Function: `convert_to_crosstalk_session`
**Logic & Purpose:**
```text
Convert BackroomsConfig to CrosstalkSession format.

Returns a dict that can be used to create a CrosstalkSession.
```

**Parameters:** `config`
**Variables Used:** `initial_prompt, slot, models`
**Implementation:**
```python
def convert_to_crosstalk_session(config: BackroomsConfig):
    """
    Convert BackroomsConfig to CrosstalkSession format.
    
    Returns a dict that can be used to create a CrosstalkSession.
    """
    from src.cli.crosstalk_studio import ModelSlot
    models = []
    for i, actor in enumerate(config.actors):
        slot = ModelSlot(slot_id=i + 1, model_id=actor.model_id, system_prompt_inline=actor.system_prompt, jinja_template='basic', temperature=actor.temperature)
        models.append(slot)
    initial_prompt = ''
    for actor in config.actors:
        if actor.context:
            for ctx in actor.context:
                if ctx.get('role') == 'user':
                    initial_prompt = ctx.get('content', '')
                    break
            if initial_prompt:
                break
    return {'models': models, 'initial_prompt': initial_prompt, 'paradigm': 'relay', 'rounds': 10, 'source_url': config.source_url, 'scenario_name': config.scenario_name}
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Test the importer.
```

**Parameters:** ``
**Variables Used:** `test_url, config`
**Implementation:**
```python
async def main():
    """Test the importer."""
    import asyncio
    test_url = 'https://dreams-of-an-electric-mind.webflow.io/dreams/conversation-1748868371-scenario-backrooms-x-sonnet4-txt'
    print(f'Fetching: {test_url}')
    config = await fetch_backrooms_url(test_url)
    if config:
        print(f'\nScenario: {config.scenario_name}')
        print(f'Actors: {len(config.actors)}')
        for actor in config.actors:
            print(f'\n  {actor.name}:')
            print(f'    Model: {actor.model_id}')
            print(f'    Temp: {actor.temperature}')
            print(f'    System: {actor.system_prompt[:100]}...')
    else:
        print('Failed to parse configuration')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/analytics.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/analytics.py`

**Module Overview**: 
```text
Usage Analytics Viewer

View actual API usage statistics from tracked requests.
Requires TRACK_USAGE=true to be enabled.
```

## Dependencies & Imports
sys, os, src.services.usage.usage_tracker.usage_tracker, src.services.usage.cost_calculator.calculate_cost

## Feature Class: `Colors`
---

## Feature Function: `color`
**Logic & Purpose:**
```text
Apply color to text.
```

**Parameters:** `text, color_code`
**Implementation:**
```python
def color(text: str, color_code: str) -> str:
    """Apply color to text."""
    return f'{color_code}{text}{Colors.RESET}'
```

---

## Feature Function: `display_header`
**Logic & Purpose:**
```text
Display section header.
```

**Parameters:** `title`
**Implementation:**
```python
def display_header(title: str):
    """Display section header."""
    print('\n' + '=' * 70)
    print(color(f'  {title}', Colors.BOLD + Colors.CYAN))
    print('=' * 70)
```

---

## Feature Function: `display_top_models`
**Logic & Purpose:**
```text
Display most used models.
```

**Parameters:** ``
**Variables Used:** `model_name, tokens_str, requests, cost_str, avg_cost, rank_color, models, total_tokens`
**Implementation:**
```python
def display_top_models():
    """Display most used models."""
    display_header('📊 Top Models by Request Count')
    models = usage_tracker.get_top_models(limit=15)
    if not models:
        print(color('  No usage data available.', Colors.DIM))
        print(color('  Enable tracking with TRACK_USAGE=true', Colors.YELLOW))
        return
    print('\n' + color(f"{'Rank':<6}{'Model':<45}{'Requests':<12}{'Total Tokens':<15}{'Avg Cost'}", Colors.BOLD))
    print(color('-' * 100, Colors.DIM))
    for i, model in enumerate(models, 1):
        model_name = model['model'][:43]
        requests = model['request_count']
        total_tokens = model['total_input_tokens'] + model['total_output_tokens']
        avg_cost = model['total_cost'] / requests if requests > 0 else 0.0
        tokens_str = f'{total_tokens / 1000:.1f}k' if total_tokens >= 1000 else str(total_tokens)
        cost_str = f'${avg_cost:.4f}'
        if i == 1:
            rank_color = Colors.BRIGHT_GREEN
        elif i <= 3:
            rank_color = Colors.GREEN
        elif i <= 5:
            rank_color = Colors.CYAN
        else:
            rank_color = ''
        print(f"{color(f'#{i}', rank_color):<13}{model_name:<45}{requests:<12}{tokens_str:<15}{cost_str}")
```

---

## Feature Function: `display_cost_summary`
**Logic & Purpose:**
```text
Display cost summary.
```

**Parameters:** ``
**Variables Used:** `total_cost, cost_color, summary`
**Implementation:**
```python
def display_cost_summary():
    """Display cost summary."""
    display_header('💰 Cost Summary (Last 7 Days)')
    summary = usage_tracker.get_cost_summary(days=7)
    if not summary:
        print(color('  No cost data available.', Colors.DIM))
        return
    print()
    print(f"  {color('Total Requests:', Colors.CYAN)} {summary.get('total_requests', 0):,}")
    print(f"  {color('Total Tokens:', Colors.CYAN)} {summary.get('total_tokens', 0):,}")
    print(f"    - {color('Input:', Colors.GREEN)} {summary.get('total_input_tokens', 0):,}")
    print(f"    - {color('Output:', Colors.BLUE)} {summary.get('total_output_tokens', 0):,}")
    print(f"    - {color('Thinking:', Colors.MAGENTA)} {summary.get('total_thinking_tokens', 0):,}")
    print()
    total_cost = summary.get('total_cost', 0.0)
    cost_color = Colors.GREEN if total_cost < 1.0 else Colors.YELLOW if total_cost < 10.0 else Colors.RED
    print(f"  {color('Estimated Cost:', Colors.BRIGHT_CYAN)} {color(f'${total_cost:.2f}', cost_color)}")
    print()
    print(f"  {color('Performance:', Colors.CYAN)}")
    print(f"    - Avg Duration: {summary.get('avg_duration_ms', 0.0):.0f}ms")
    print(f"    - Avg Speed: {summary.get('avg_tokens_per_second', 0.0):.0f} tokens/sec")
```

---

## Feature Function: `display_json_toon_analysis`
**Logic & Purpose:**
```text
Display JSON/TOON analysis.
```

**Parameters:** ``
**Variables Used:** `json_pct, json_requests, savings_color, savings, analysis, recommended, total_requests, savings_tokens`
**Implementation:**
```python
def display_json_toon_analysis():
    """Display JSON/TOON analysis."""
    display_header('🔍 JSON → TOON Conversion Analysis')
    analysis = usage_tracker.get_json_toon_analysis()
    if not analysis:
        print(color('  No JSON analysis data available.', Colors.DIM))
        return
    total_requests = analysis.get('total_requests', 0)
    json_requests = analysis.get('json_requests', 0)
    json_pct = analysis.get('json_percentage', 0.0)
    print()
    print(f"  {color('Total Requests:', Colors.CYAN)} {total_requests:,}")
    print(f"  {color('JSON Requests:', Colors.CYAN)} {json_requests:,} ({json_pct:.1f}%)")
    print(f"  {color('Total JSON:', Colors.CYAN)} {analysis.get('total_json_bytes', 0):,} bytes")
    print(f"  {color('Avg JSON Size:', Colors.CYAN)} {analysis.get('avg_json_size', 0):.0f} bytes")
    print()
    savings = analysis.get('estimated_toon_savings_bytes', 0)
    savings_tokens = savings // 4
    savings_color = Colors.GREEN if savings_tokens > 1000 else Colors.YELLOW
    print(f"  {color('Est. TOON Savings:', Colors.BRIGHT_CYAN)} {color(f'~{savings:,} bytes (~{savings_tokens:,} tokens)', savings_color)}")
    print()
    recommended = analysis.get('recommended', False)
    if recommended:
        print(color('  ✅ TOON conversion RECOMMENDED', Colors.BRIGHT_GREEN))
        print(color('     High JSON usage detected - TOON could save significant tokens', Colors.GREEN))
    else:
        print(color('  ℹ️  TOON conversion not needed yet', Colors.CYAN))
        if json_pct < 30:
            print(color(f'     Low JSON usage ({json_pct:.1f}% < 30%)', Colors.DIM))
        if analysis.get('avg_json_size', 0) < 500:
            print(color(f"     Small JSON payloads (avg {analysis.get('avg_json_size', 0):.0f} < 500 bytes)", Colors.DIM))
```

---

## Feature Function: `export_to_csv`
**Logic & Purpose:**
```text
Export usage data to CSV.
```

**Parameters:** ``
**Variables Used:** `filename, days`
**Implementation:**
```python
def export_to_csv():
    """Export usage data to CSV."""
    display_header('📤 Export to CSV')
    filename = input(color('\nEnter filename (default: usage_export.csv): ', Colors.BRIGHT_CYAN)).strip()
    if not filename:
        filename = 'usage_export.csv'
    if not filename.endswith('.csv'):
        filename += '.csv'
    days = input(color('Days of data to export (default: 30): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 30
    except ValueError:
        days = 30
    if usage_tracker.export_to_csv(filename, days=days):
        print(color(f'\n✓ Exported to {filename}', Colors.BRIGHT_GREEN))
    else:
        print(color(f'\n✗ Export failed', Colors.BRIGHT_RED))
```

---

## Feature Function: `display_savings_analysis`
**Logic & Purpose:**
```text
Display smart routing savings analysis.
```

**Parameters:** ``
**Variables Used:** `avg_savings, total_savings, route, requests, pct, savings, savings_data, days`
**Implementation:**
```python
def display_savings_analysis():
    """Display smart routing savings analysis."""
    display_header('💰 Smart Routing Savings Analysis')
    days = input(color('\nDays to analyze (default: 7): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7
    savings_data = usage_tracker.get_savings_data(days=days)
    if not savings_data:
        print(color('  No savings data available.', Colors.DIM))
        print(color('  Savings are tracked when original_cost differs from actual cost.', Colors.YELLOW))
        return
    total_savings = sum((s['total_savings'] for s in savings_data))
    avg_savings = sum((s['avg_savings_percent'] for s in savings_data)) / len(savings_data) if savings_data else 0
    print(f"\n  {color('Total Savings:', Colors.BRIGHT_CYAN)} {color(f'${total_savings:.4f}', Colors.BRIGHT_GREEN)}")
    print(f"  {color('Avg Savings:', Colors.BRIGHT_CYAN)} {color(f'{avg_savings:.1f}%', Colors.BRIGHT_GREEN)}")
    print()
    print(color(f"{'Route':<50}{'Requests':<12}{'Savings':<15}{'Avg %'}", Colors.BOLD))
    print(color('-' * 90, Colors.DIM))
    for saving in savings_data:
        route = f"{saving['original_model'][:20]} → {saving['routed_model'][:20]}"
        requests = saving['request_count']
        savings = f"${saving['total_savings']:.4f}"
        pct = f"{saving['avg_savings_percent']:.1f}%"
        print(f'{route:<50}{requests:<12}{savings:<15}{pct}')
```

---

## Feature Function: `display_token_breakdown`
**Logic & Purpose:**
```text
Display detailed token breakdown.
```

**Parameters:** ``
**Variables Used:** `token_stats, data, abs_val, bar_length, pct, bar, bar_color, total, days, types, req_count`
**Implementation:**
```python
def display_token_breakdown():
    """Display detailed token breakdown."""
    display_header('🔧 Token Composition Analysis')
    days = input(color('\nDays to analyze (default: 7): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7
    token_stats = usage_tracker.get_token_breakdown_stats(days=days)
    if not token_stats:
        print(color('  No token breakdown data available.', Colors.DIM))
        print(color('  Requires enhanced token tracking.', Colors.YELLOW))
        return
    total = token_stats.get('total_tokens', 0)
    req_count = token_stats.get('request_count', 0)
    print(f"\n  {color('Total Tokens:', Colors.BRIGHT_CYAN)} {total:,}")
    print(f"  {color('Request Count:', Colors.BRIGHT_CYAN)} {req_count:,}")
    print()
    print(color('Token Type Distribution:', Colors.BOLD))
    print()
    types = [('prompt', 'Prompt'), ('completion', 'Completion'), ('reasoning', 'Reasoning'), ('cached', 'Cached'), ('tool_use', 'Tool Use'), ('audio', 'Audio')]
    for key, label in types:
        if key in token_stats:
            data = token_stats[key]
            abs_val = data['absolute']
            pct = data['percentage']
            if abs_val > 0:
                bar_length = int(pct / 2)
                bar = '█' * bar_length
                if bar_length < 5:
                    bar = bar.ljust(5)
                bar_color = Colors.GREEN if pct >= 10 else Colors.YELLOW if pct >= 5 else Colors.CYAN
                print(f"  {color(label.ljust(12), Colors.CYAN)}: {color(f'{pct:5.1f}%', bar_color)} | {color(bar, bar_color)} {abs_val:,} tokens")
```

---

## Feature Function: `display_provider_stats`
**Logic & Purpose:**
```text
Display provider-level statistics.
```

**Parameters:** ``
**Variables Used:** `cost, tokens, per_k, latency, providers, days, name, reqs`
**Implementation:**
```python
def display_provider_stats():
    """Display provider-level statistics."""
    display_header('🏢 Provider Performance Analysis')
    days = input(color('\nDays to analyze (default: 7): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7
    providers = usage_tracker.get_provider_stats(days=days)
    if not providers:
        print(color('  No provider data available.', Colors.DIM))
        return
    print()
    print(color(f"{'Provider':<20}{'Requests':<10}{'Tokens':<12}{'Cost':<12}{'$/1K':<10}{'Latency'}", Colors.BOLD))
    print(color('-' * 95, Colors.DIM))
    for provider in providers:
        name = provider['provider'][:18]
        reqs = provider['total_requests']
        tokens = f"{provider['total_tokens'] / 1000:.0f}k" if provider['total_tokens'] >= 1000 else str(provider['total_tokens'])
        cost = f"${provider['total_cost']:.2f}"
        per_k = f"${provider['avg_cost_per_1k_tokens']:.3f}"
        latency = f"{provider['avg_duration_ms']:.0f}ms"
        print(f'{name:<20}{reqs:<10}{tokens:<12}{cost:<12}{per_k:<10}{latency}')
```

---

## Feature Function: `display_model_comparison`
**Logic & Purpose:**
```text
Display model comparison statistics.
```

**Parameters:** ``
**Variables Used:** `filtered, tok_per_req, per_k, latency, cost_color, models, min_reqs, tools, days, name, reqs`
**Implementation:**
```python
def display_model_comparison():
    """Display model comparison statistics."""
    display_header('📊 Model Performance Comparison')
    days = input(color('\nDays to analyze (default: 7): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7
    min_reqs = input(color('Min requests per model (default: 1): ', Colors.BRIGHT_CYAN)).strip()
    try:
        min_reqs = int(min_reqs) if min_reqs else 1
    except ValueError:
        min_reqs = 1
    models = usage_tracker.get_model_comparison(days=days)
    filtered = [m for m in models if m['total_requests'] >= min_reqs]
    if not filtered:
        print(color('  No model comparison data available.', Colors.DIM))
        return
    print()
    print(color(f"{'Model':<35}{'Reqs':<6}{'Tok/Req':<10}{'$/1K':<9}{'Latency':<9}{'Tools'}", Colors.BOLD))
    print(color('-' * 90, Colors.DIM))
    for model in filtered:
        name = model['model'][:33]
        reqs = model['total_requests']
        tok_per_req = f"{model['avg_tokens_per_request']:.0f}"
        per_k = f"${model['avg_cost_per_1k_tokens']:.2f}"
        latency = f"{model['avg_duration_ms']:.0f}ms"
        tools = model['tool_requests']
        cost_color = Colors.GREEN if model['avg_cost_per_1k_tokens'] < 5 else Colors.YELLOW if model['avg_cost_per_1k_tokens'] < 10 else Colors.RED
        print(f'{name:<35}{reqs:<6}{tok_per_req:<10}{color(per_k, cost_color):<9}{latency:<9}{tools}')
```

---

## Feature Function: `display_ai_insights`
**Logic & Purpose:**
```text
Display AI-generated insights and recommendations.
```

**Parameters:** ``
**Variables Used:** `second_provider, insights, total_savings, inefficient, pct, cached_pct, providers, days, insights_data, priority, top_provider, top_saving, summary, token_breakdown, priority_colors, reasoning_pct, savings, models, top_ineff`
**Implementation:**
```python
def display_ai_insights():
    """Display AI-generated insights and recommendations."""
    display_header('💡 AI Insights & Recommendations')
    days = input(color('\nDays to analyze (default: 7): ', Colors.BRIGHT_CYAN)).strip()
    try:
        days = int(days) if days else 7
    except ValueError:
        days = 7
    insights_data = usage_tracker.get_dashboard_summary(days=days)
    if not insights_data:
        print(color('  No data available for insights.', Colors.DIM))
        return
    print()
    print('  ' + color('Analyzing your usage patterns...', Colors.CYAN))
    print()
    summary = insights_data.get('summary', {})
    savings = insights_data.get('savings', [])
    token_breakdown = insights_data.get('token_breakdown', {})
    providers = insights_data.get('providers', [])
    models = insights_data.get('models', [])
    insights = []
    total_savings = sum((s['total_savings'] for s in savings))
    if total_savings > 0:
        top_saving = max(savings, key=lambda x: x['total_savings']) if savings else None
        if top_saving:
            priority = 'HIGH' if top_saving['avg_savings_percent'] > 20 else 'MED'
            insights.append(('💰 Cost Savings', f"Saved ${total_savings:.4f} ({top_saving['avg_savings_percent']:.1f}%) by routing {top_saving['request_count']} requests", priority))
    if token_breakdown and token_breakdown.get('total_tokens', 0) > 0:
        reasoning_pct = token_breakdown.get('reasoning', {}).get('percentage', 0)
        if reasoning_pct > 30:
            insights.append(('⚡ High Reasoning Usage', f'{reasoning_pct:.1f}% tokens are reasoning. Consider simpler prompts for cost savings', 'MED'))
        cached_pct = token_breakdown.get('cached', {}).get('percentage', 0)
        if cached_pct < 5:
            insights.append(('🔄 Low Cache Utilization', f'Only {cached_pct:.1f}% cached. Prompt caching could save costs', 'LOW'))
    if len(providers) > 1:
        top_provider = providers[0]
        second_provider = providers[1]
        if top_provider['total_cost'] > second_provider['total_cost'] * 2:
            pct = top_provider['total_cost'] / (top_provider['total_cost'] + second_provider['total_cost']) * 100
            insights.append(('🏢 Provider Concentration', f"{top_provider['provider']} is {pct:.1f}% of costs. Consider diversifying", 'LOW'))
    if summary.get('avg_duration_ms', 0) > 5000:
        insights.append(('⏱️ High Latency', f"Average {summary['avg_duration_ms']:.0f}ms. Try streaming or faster models", 'MED'))
    if len(models) > 3:
        inefficient = [m for m in models if m['avg_cost_per_1k_tokens'] > 10 and m['total_requests'] > 10]
        if inefficient:
            top_ineff = inefficient[0]
            insights.append(('📊 Expensive Model Usage', f"{top_ineff['model']} costs ${top_ineff['avg_cost_per_1k_tokens']:.2f}/1K tokens", 'MED'))
    if not insights:
        print('  ' + color('ℹ️  No specific insights available yet.', Colors.CYAN))
        print('  ' + color('Keep tracking usage to generate personalized recommendations.', Colors.DIM))
        return
    print(f"  {color(f'{len(insights)} Insights Found:', Colors.BOLD + Colors.BRIGHT_CYAN)}\n")
    priority_colors = {'HIGH': Colors.BRIGHT_RED, 'MED': Colors.BRIGHT_YELLOW, 'LOW': Colors.CYAN}
    for i, (title, desc, priority) in enumerate(insights, 1):
        print(f"  {color(f'{i}.', Colors.DIM)} {color(title, Colors.BOLD)}")
        print(f'     {desc}')
        print(f"     {color(f'[{priority}]', priority_colors[priority])}")
        print()
```

---

## Feature Function: `display_all`
**Logic & Purpose:**
```text
Display all analytics.
```

**Parameters:** ``
**Implementation:**
```python
def display_all():
    """Display all analytics."""
    display_top_models()
    display_cost_summary()
    display_savings_analysis()
    display_token_breakdown()
    display_provider_stats()
    display_model_comparison()
    display_json_toon_analysis()
    display_ai_insights()
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main menu.
```

**Parameters:** ``
**Variables Used:** `choice`
**Implementation:**
```python
def main():
    """Main menu."""
    print(color('\n╔' + '═' * 68 + '╗', Colors.CYAN))
    print(color('║' + ' ' * 20 + 'USAGE ANALYTICS VIEWER' + ' ' * 26 + '║', Colors.CYAN))
    print(color('╚' + '═' * 68 + '╝', Colors.CYAN))
    if not usage_tracker.enabled:
        print(color('\n⚠️  Usage tracking is DISABLED', Colors.BRIGHT_YELLOW))
        print(color('   Enable it by setting TRACK_USAGE=true in .env', Colors.YELLOW))
        print(color('   Then restart the proxy to start collecting data.\n', Colors.DIM))
        return
    print(color('\n✓ Usage tracking is ENABLED', Colors.BRIGHT_GREEN))
    while True:
        print('\n' + color('═' * 70, Colors.DIM))
        print(color('  Analytics Options:', Colors.BOLD))
        print(f"    {color('1', Colors.CYAN)} - Top Models & Cost Summary")
        print(f"    {color('2', Colors.CYAN)} - Smart Routing Savings")
        print(f"    {color('3', Colors.CYAN)} - Token Composition")
        print(f"    {color('4', Colors.CYAN)} - Provider Performance")
        print(f"    {color('5', Colors.CYAN)} - Model Comparison")
        print(f"    {color('6', Colors.CYAN)} - JSON/TOON Analysis")
        print(f"    {color('7', Colors.CYAN)} - AI Insights & Recommendations")
        print(f"    {color('8', Colors.CYAN)} - Export to CSV")
        print(f"    {color('9', Colors.CYAN)} - View ALL Analytics")
        print(f"    {color('0', Colors.RED)} - Exit")
        print(color('═' * 70, Colors.DIM))
        choice = input(color('\n> ', Colors.BRIGHT_GREEN)).strip()
        if choice == '1':
            display_top_models()
            display_cost_summary()
        elif choice == '2':
            display_savings_analysis()
        elif choice == '3':
            display_token_breakdown()
        elif choice == '4':
            display_provider_stats()
        elif choice == '5':
            display_model_comparison()
        elif choice == '6':
            display_json_toon_analysis()
        elif choice == '7':
            display_ai_insights()
        elif choice == '8':
            export_to_csv()
        elif choice == '9':
            display_all()
        elif choice == '0':
            print(color('\nGoodbye!\n', Colors.BRIGHT_CYAN))
            break
        else:
            print(color('\nInvalid option. Try again.', Colors.BRIGHT_RED))
```

---


