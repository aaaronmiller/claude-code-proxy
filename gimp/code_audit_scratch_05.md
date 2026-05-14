# File Audit: /home/cheta/code/claude-code-proxy/src/cli/crosstalk_runner.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/crosstalk_runner.py`

**Module Overview**: 
```text
Crosstalk Runner - Programmatic API for Model-to-Model Conversations

Enables running crosstalk sessions from:
- JSON config files
- Inline configuration dictionaries
- Saved preset names

Designed for MCP integration and CLI scripting.
Returns transcript and saves to output file.
```

## Global Presets & Variables
- `console` = `Console()`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent`
- `PRESETS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'presets'`
- `SESSIONS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'sessions'`
- `PROMPTS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'prompts'`
- `TEMPLATES_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'templates'`

## Dependencies & Imports
asyncio, json, os, sys, pathlib.Path, datetime.datetime, typing.Union, typing.Dict, typing.Any, typing.Optional, typing.List, dataclasses.asdict, rich.console.Console

## Feature Function: `load_prompt_manifest`
**Logic & Purpose:**
```text
Load the prompts manifest.yaml file.
```

**Parameters:** ``
**Variables Used:** `manifest_path`
**Implementation:**
```python
def load_prompt_manifest() -> Dict[str, Any]:
    """Load the prompts manifest.yaml file."""
    manifest_path = PROMPTS_DIR / 'manifest.yaml'
    if manifest_path.exists():
        import yaml
        with open(manifest_path) as f:
            return yaml.safe_load(f) or {}
    return {'prompts': []}
```

---

## Feature Function: `load_template_manifest`
**Logic & Purpose:**
```text
Load the templates manifest.yaml file.
```

**Parameters:** ``
**Variables Used:** `manifest_path`
**Implementation:**
```python
def load_template_manifest() -> Dict[str, Any]:
    """Load the templates manifest.yaml file."""
    manifest_path = TEMPLATES_DIR / 'manifest.yaml'
    if manifest_path.exists():
        import yaml
        with open(manifest_path) as f:
            return yaml.safe_load(f) or {}
    return {'templates': []}
```

---

## Feature Function: `get_prompt_content`
**Logic & Purpose:**
```text
Load a system prompt by name from the prompts directory.

Args:
    prompt_name: Name of the prompt (without .md extension)
    
Returns:
    Prompt content as string, or None if not found
```

**Parameters:** `prompt_name`
**Variables Used:** `manifest, file_path, prompt_file`
**Implementation:**
```python
def get_prompt_content(prompt_name: str) -> Optional[str]:
    """
    Load a system prompt by name from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt (without .md extension)
        
    Returns:
        Prompt content as string, or None if not found
    """
    prompt_file = PROMPTS_DIR / f'{prompt_name}.md'
    if prompt_file.exists():
        return prompt_file.read_text()
    manifest = load_prompt_manifest()
    for p in manifest.get('prompts', []):
        if p.get('name') == prompt_name:
            file_path = PROMPTS_DIR / p.get('file', f'{prompt_name}.md')
            if file_path.exists():
                return file_path.read_text()
    return None
```

---

## Feature Function: `get_template_content`
**Logic & Purpose:**
```text
Load a Jinja template by name from the templates directory.

Args:
    template_name: Name of the template (without .j2 extension)
    
Returns:
    Template content as string, or None if not found
```

**Parameters:** `template_name`
**Variables Used:** `manifest, file_path, template_file`
**Implementation:**
```python
def get_template_content(template_name: str) -> Optional[str]:
    """
    Load a Jinja template by name from the templates directory.
    
    Args:
        template_name: Name of the template (without .j2 extension)
        
    Returns:
        Template content as string, or None if not found
    """
    template_file = TEMPLATES_DIR / f'{template_name}.j2'
    if template_file.exists():
        return template_file.read_text()
    manifest = load_template_manifest()
    for t in manifest.get('templates', []):
        if t.get('name') == template_name:
            file_path = TEMPLATES_DIR / t.get('file', f'{template_name}.j2')
            if file_path.exists():
                return file_path.read_text()
    return None
```

---

## Feature Function: `list_available_prompts`
**Logic & Purpose:**
```text
List all available prompts from the manifest.
```

**Parameters:** ``
**Variables Used:** `manifest`
**Implementation:**
```python
def list_available_prompts() -> List[Dict[str, str]]:
    """List all available prompts from the manifest."""
    manifest = load_prompt_manifest()
    return manifest.get('prompts', [])
```

---

## Feature Function: `list_available_templates`
**Logic & Purpose:**
```text
List all available templates from the manifest.
```

**Parameters:** ``
**Variables Used:** `manifest`
**Implementation:**
```python
def list_available_templates() -> List[Dict[str, str]]:
    """List all available templates from the manifest."""
    manifest = load_template_manifest()
    return manifest.get('templates', [])
```

---

## Feature Function: `load_config`
**Logic & Purpose:**
```text
Load crosstalk configuration from various sources.

Args:
    config_source: One of:
        - Path to JSON file (str or Path)
        - Preset name (str without .json)
        - Inline config dict
        
Returns:
    Parsed configuration dictionary
```

**Parameters:** `config_source`
**Variables Used:** `path, preset_path`
**Implementation:**
```python
def load_config(config_source: Union[str, Dict, Path]) -> Dict[str, Any]:
    """
    Load crosstalk configuration from various sources.
    
    Args:
        config_source: One of:
            - Path to JSON file (str or Path)
            - Preset name (str without .json)
            - Inline config dict
            
    Returns:
        Parsed configuration dictionary
    """
    if isinstance(config_source, dict):
        return config_source
    path = Path(config_source)
    if path.exists() and path.suffix == '.json':
        with open(path) as f:
            return json.load(f)
    preset_path = PRESETS_DIR / f'{config_source}.json'
    if preset_path.exists():
        with open(preset_path) as f:
            return json.load(f)
    if not path.suffix:
        path = Path(f'{config_source}.json')
        if path.exists():
            with open(path) as f:
                return json.load(f)
    raise FileNotFoundError(f'Could not find config: {config_source}')
```

---

## Feature Function: `validate_config`
**Logic & Purpose:**
```text
Validate a crosstalk configuration.
```

**Parameters:** `config`
**Variables Used:** `required`
**Implementation:**
```python
def validate_config(config: Dict[str, Any]) -> bool:
    """Validate a crosstalk configuration."""
    required = ['models']
    for key in required:
        if key not in config:
            raise ValueError(f'Missing required key: {key}')
    if not config['models']:
        raise ValueError('At least one model is required')
    return True
```

---

## Feature Function: `run_from_config`
**Logic & Purpose:**
```text
Run a crosstalk session from configuration.

Args:
    config_source: Config file path, preset name, or inline dict
    output_file: Optional path for transcript output
    stream: If True, print responses in real-time
    
Returns:
    Dict with:
        - transcript: List of messages
        - output_file: Path to saved transcript
        - config: Configuration used
        - status: "completed" or "error"
```

**Parameters:** `config_source, output_file, stream`
**Variables Used:** `timestamp, output_file, topology, config, output_data, slot, stop_data, topo_data, models, transcript, session, stop_conditions`
**Implementation:**
```python
async def run_from_config(config_source: Union[str, Dict, Path], output_file: Optional[str]=None, stream: bool=False) -> Dict[str, Any]:
    """
    Run a crosstalk session from configuration.
    
    Args:
        config_source: Config file path, preset name, or inline dict
        output_file: Optional path for transcript output
        stream: If True, print responses in real-time
        
    Returns:
        Dict with:
            - transcript: List of messages
            - output_file: Path to saved transcript
            - config: Configuration used
            - status: "completed" or "error"
    """
    config = load_config(config_source)
    validate_config(config)
    from src.cli.crosstalk_studio import CrosstalkSession, ModelSlot, TopologyConfig, StopConditions
    models = []
    for i, m in enumerate(config.get('models', [])):
        if isinstance(m, dict):
            slot = ModelSlot(slot_id=m.get('slot_id', i + 1), model_id=m.get('model_id', 'anthropic/claude-3-opus'), system_prompt_file=m.get('system_prompt_file', ''), system_prompt_inline=m.get('system_prompt_inline', ''), jinja_template=m.get('jinja_template', 'basic'), temperature=m.get('temperature', 0.9), max_tokens=m.get('max_tokens', 4096))
        else:
            slot = ModelSlot(slot_id=i + 1, model_id=m)
        models.append(slot)
    topo_data = config.get('topology', {})
    topology = TopologyConfig(type=topo_data.get('type', 'ring'), order=topo_data.get('order', []), center=topo_data.get('center', 1), spokes=topo_data.get('spokes', []))
    stop_data = config.get('stop_conditions', {})
    stop_conditions = StopConditions(max_time_seconds=stop_data.get('max_time_seconds', 0), max_cost_dollars=stop_data.get('max_cost_dollars', 0.0), max_turns=stop_data.get('max_turns', 0), stop_keywords=stop_data.get('stop_keywords', []))
    session = CrosstalkSession(models=models, rounds=config.get('rounds', 5), paradigm=config.get('paradigm', 'relay'), topology=topology, initial_prompt=config.get('initial_prompt', 'Begin the conversation.'), memory_file=config.get('memory_file'), infinite=config.get('infinite', False), stop_conditions=stop_conditions, summarize_every=config.get('summarize_every', 0))
    from src.cli.crosstalk_engine import run_crosstalk
    try:
        transcript = await run_crosstalk(session)
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = SESSIONS_DIR / f'session_{timestamp}.json'
        else:
            output_file = Path(output_file)
        output_data = {'config': config, 'messages': [asdict(m) for m in transcript.messages] if transcript else [], 'started_at': transcript.started_at if transcript else '', 'ended_at': transcript.ended_at if transcript else '', 'status': 'completed' if transcript else 'error'}
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        return {'transcript': output_data['messages'], 'output_file': str(output_file), 'config': config, 'status': 'completed'}
    except Exception as e:
        return {'transcript': [], 'output_file': None, 'config': config, 'status': 'error', 'error': str(e)}
```

---

## Feature Function: `run_quick`
**Logic & Purpose:**
```text
Quick crosstalk session with minimal configuration.

Args:
    models: List of model IDs
    prompt: Initial prompt
    rounds: Number of rounds
    paradigm: Communication paradigm
    
Returns:
    Same as run_from_config
```

**Parameters:** `models, prompt, rounds, paradigm`
**Variables Used:** `config`
**Implementation:**
```python
async def run_quick(models: List[str], prompt: str, rounds: int=5, paradigm: str='relay') -> Dict[str, Any]:
    """
    Quick crosstalk session with minimal configuration.
    
    Args:
        models: List of model IDs
        prompt: Initial prompt
        rounds: Number of rounds
        paradigm: Communication paradigm
        
    Returns:
        Same as run_from_config
    """
    config = {'models': [{'model_id': m} for m in models], 'initial_prompt': prompt, 'rounds': rounds, 'paradigm': paradigm}
    return await run_from_config(config)
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
CLI entry point for crosstalk runner.
```

**Parameters:** ``
**Variables Used:** `args, parser, result, models, presets`
**Implementation:**
```python
def main():
    """CLI entry point for crosstalk runner."""
    import argparse
    parser = argparse.ArgumentParser(description='Run crosstalk sessions from configuration files', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  # Run from preset\n  python -m src.cli.crosstalk_runner --config backrooms\n  \n  # Run from file\n  python -m src.cli.crosstalk_runner --config configs/crosstalk/presets/my_config.json\n  \n  # Quick run\n  python -m src.cli.crosstalk_runner --quick "claude-3-opus,gemini-pro" --prompt "Explore consciousness"\n  \n  # With output file\n  python -m src.cli.crosstalk_runner --config backrooms --output my_session.json\n        ')
    parser.add_argument('--config', '-c', type=str, help='Config file path or preset name')
    parser.add_argument('--output', '-o', type=str, help='Output file path for transcript')
    parser.add_argument('--quick', '-q', type=str, help='Quick run: comma-separated model IDs')
    parser.add_argument('--prompt', '-p', type=str, default='Begin.', help='Initial prompt for quick run')
    parser.add_argument('--rounds', '-r', type=int, default=5, help='Number of rounds')
    parser.add_argument('--paradigm', type=str, default='relay', choices=['relay', 'memory', 'debate', 'report'], help='Communication paradigm')
    parser.add_argument('--list-presets', '-l', action='store_true', help='List available presets')
    parser.add_argument('--json', '-j', action='store_true', help='Output result as JSON (for MCP)')
    args = parser.parse_args()
    if args.list_presets:
        presets = list(PRESETS_DIR.glob('*.json'))
        if presets:
            print('Available presets:')
            for p in presets:
                print(f'  - {p.stem}')
        else:
            print('No presets found. Create one with Crosstalk Studio.')
        return
    if args.quick:
        models = [m.strip() for m in args.quick.split(',')]
        result = asyncio.run(run_quick(models=models, prompt=args.prompt, rounds=args.rounds, paradigm=args.paradigm))
    elif args.config:
        result = asyncio.run(run_from_config(config_source=args.config, output_file=args.output))
    else:
        parser.print_help()
        return
    if args.json:
        print(json.dumps(result, indent=2))
    elif result.get('status') == 'completed':
        print(f'\n✅ Session completed')
        print(f"   Messages: {len(result.get('transcript', []))}")
        print(f"   Output: {result.get('output_file')}")
    else:
        print(f"\n❌ Session failed: {result.get('error')}")
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/client_wrapper.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/client_wrapper.py`

**Module Overview**: 
```text
Client Wrapper (Python Version)
Wraps the Claude Code client to handle 401 errors and auto-heal.
```

## Global Presets & Variables
- `RED` = `'\x1b[0;31m'`
- `YELLOW` = `'\x1b[1;33m'`
- `CYAN` = `'\x1b[0;36m'`
- `NC` = `'\x1b[0m'`

## Dependencies & Imports
os, sys, subprocess, shutil, pathlib.Path, src.cli.fix_keys.main

## Feature Function: `main`
**Parameters:** `args`
**Variables Used:** `args, char, base_url, is_proxy_mode, process, env, stderr_output, return_code, stderr_str`
**Implementation:**
```python
def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if not args:
        print('Usage: python start_proxy.py --client -- <command>')
        sys.exit(1)
    base_url = os.environ.get('ANTHROPIC_BASE_URL', '') or os.environ.get('PROVIDER_BASE_URL', '')
    is_proxy_mode = 'localhost' in base_url or '127.0.0.1' in base_url
    env = os.environ.copy()
    if is_proxy_mode:
        env['ANTHROPIC_API_KEY'] = 'pass'
        env['PROXY_AUTH_KEY'] = 'pass'
    print(f'{CYAN}🚀 Starting Client Wrapper...{NC}')
    while True:
        process = subprocess.Popen(args, env=env, stderr=subprocess.PIPE, stdout=sys.stdout, stdin=sys.stdin, bufsize=0, universal_newlines=True)
        stderr_output = []
        while True:
            char = process.stderr.read(1)
            if not char and process.poll() is not None:
                break
            if char:
                sys.stderr.write(char)
                sys.stderr.flush()
                stderr_output.append(char)
        stderr_str = ''.join(stderr_output)
        return_code = process.poll()
        if return_code != 0:
            if '401' in stderr_str or 'Unauthorized' in stderr_str or 'Invalid API key' in stderr_str:
                print(f'\n{RED}🛑 Authentication Error Detected!{NC}')
                print(f'{YELLOW}🚀 Launching Auto-Healing Wizard...{NC}\n')
                try:
                    fix_keys_main()
                except SystemExit as e:
                    if e.code != 0:
                        print(f'{RED}Wizard cancelled. Exiting.{NC}')
                        sys.exit(return_code)
                print(f'\n{CYAN}🔄 Restarting command...{NC}\n')
                if is_proxy_mode:
                    print(f'{RED}⚠️  ACTION REQUIRED ⚠️{NC}')
                    print(f'{YELLOW}You are running in PROXY MODE.{NC}')
                    print('The proxy server should auto-detect the key change within 5 minutes.')
                    print("If it doesn't, restart the proxy terminal.")
                    input('Press Enter to retry the client command...')
                if not is_proxy_mode:
                    from src.utils.key_reloader import key_reloader
                    key_reloader.check_for_updates()
                    env = os.environ.copy()
                continue
        sys.exit(return_code)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/analytics_tui.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/analytics_tui.py`

**Module Overview**: 
```text
Analytics Configurator & Viewer TUI

Unified interface for:
1. Enabling/disabling usage tracking
2. Viewing comprehensive analytics
3. Exporting data
4. Managing analytics settings
```

## Global Presets & Variables
- `console` = `Console()`

## Dependencies & Imports
sys, os, rich.console.Console, rich.panel.Panel, rich.table.Table, rich.box, rich.prompt.Prompt, rich.prompt.Confirm, src.cli.env_utils.update_env_values, src.cli.env_utils.get_env_value, src.services.usage.usage_tracker.UsageTracker

## Feature Class: `AnalyticsConfigurator`
**Description:**
```text
Analytics configuration and viewing TUI.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.running = True
    self.usage_tracker = UsageTracker()
```

### Method: `draw_header`
**Logic & Purpose:**
```text
Draw the header.
```

**Parameters:** `self`
**Variables Used:** `status_color, track_usage, status_text, tracking_status`
**Implementation:**
```python
def draw_header(self):
    """Draw the header."""
    track_usage = get_env_value('TRACK_USAGE', 'false').lower() == 'true'
    status_color = 'green' if track_usage else 'yellow'
    status_text = 'ENABLED' if track_usage else 'DISABLED'
    tracking_status = f'[{status_color}]{status_text}[/{status_color}]'
    console.print(Panel(f'[bold cyan]📊 Analytics Configurator & Viewer[/]\n\n[dim]Track, analyze, and optimize your API usage[/]\nTracking Status: {tracking_status}', box=box.DOUBLE, style='cyan', padding=(1, 2), expand=False))
```

### Method: `draw_menu`
**Logic & Purpose:**
```text
Draw the main menu.
```

**Parameters:** `self`
**Variables Used:** `table, options`
**Implementation:**
```python
def draw_menu(self):
    """Draw the main menu."""
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2))
    table.add_column('', width=3)
    table.add_column('Option', width=35)
    table.add_column('Description', width=35)
    options = [('1', '🚀 Enable/Disable Tracking', 'Turn usage tracking on/off'), ('2', '📈 View Summary (7d)', 'Quick stats overview'), ('3', '💰 Smart Routing Savings', 'Cost optimization analysis'), ('4', '🔧 Token Breakdown', 'Detailed token composition'), ('5', '🏢 Provider Performance', 'Provider comparison'), ('6', '📊 Model Comparison', 'Model efficiency stats'), ('7', '💡 AI Insights', 'Personalized recommendations'), ('8', '📤 Export Data', 'CSV/JSON export'), ('9', '🔮 Full Analytics Dashboard', 'View ALL analytics'), ('0', '🚪 Exit', 'Return to settings')]
    for marker, label, desc in options:
        table.add_row(marker, label, desc)
    console.print(table)
```

### Method: `draw`
**Logic & Purpose:**
```text
Draw the full screen.
```

**Parameters:** `self`
**Implementation:**
```python
def draw(self):
    """Draw the full screen."""
    console.clear()
    self.draw_header()
    console.print()
    self.draw_menu()
```

### Method: `handle_input`
**Logic & Purpose:**
```text
Handle keyboard input.
```

**Parameters:** `self`
**Variables Used:** `choice`
**Implementation:**
```python
def handle_input(self):
    """Handle keyboard input."""
    choice = Prompt.ask('\n→ Select option', default='0').strip()
    return choice
```

### Method: `toggle_tracking`
**Logic & Purpose:**
```text
Toggle TRACK_USAGE setting.
```

**Parameters:** `self`
**Variables Used:** `current, new_value`
**Implementation:**
```python
def toggle_tracking(self):
    """Toggle TRACK_USAGE setting."""
    current = get_env_value('TRACK_USAGE', 'false').lower() == 'true'
    new_value = 'false' if current else 'true'
    console.print(f"\n[yellow]Current status: {('ENABLED' if current else 'DISABLED')}[/yellow]")
    if Confirm.ask(f"Turn usage tracking {('OFF' if current else 'ON')}?"):
        update_env_values({'TRACK_USAGE': new_value}, verbose=True)
        os.environ['TRACK_USAGE'] = new_value
        if new_value == 'true':
            console.print('\n[green]✓ Usage tracking ENABLED[/green]')
            console.print('[dim]   Note: Restart proxy to start collecting data[/dim]')
        else:
            console.print('\n[yellow]○ Usage tracking DISABLED[/yellow]')
        input('\nPress Enter to continue...')
```

### Method: `check_tracking_enabled`
**Logic & Purpose:**
```text
Check if tracking is enabled and show warning if not.
```

**Parameters:** `self`
**Variables Used:** `enabled`
**Implementation:**
```python
def check_tracking_enabled(self) -> bool:
    """Check if tracking is enabled and show warning if not."""
    enabled = self.usage_tracker.enabled
    if not enabled:
        console.print('\n[bold red]⚠️  Usage tracking is DISABLED[/bold red]')
        console.print('[yellow]   Enable it first to view analytics[/yellow]')
        console.print('[dim]   Option 1: Enable tracking[/dim]')
        input('\nPress Enter to continue...')
    return enabled
```

### Method: `view_summary`
**Logic & Purpose:**
```text
View cost summary.
```

**Parameters:** `self`
**Variables Used:** `days, top_models, summary`
**Implementation:**
```python
def view_summary(self):
    """View cost summary."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold cyan]📊 Cost Summary (Last {days} Days)[/]', border_style='cyan'))
    summary = self.usage_tracker.get_cost_summary(days=days)
    top_models = self.usage_tracker.get_top_models(limit=10)
    if not summary:
        console.print('\n[dim]No data available yet.[/dim]')
        input('\nPress Enter to continue...')
        return
    console.print(f'\n[bold yellow]Overview:[/bold yellow]')
    console.print(f"  Total Requests: {summary.get('total_requests', 0):,}")
    console.print(f"  Total Tokens: {summary.get('total_tokens', 0):,}")
    console.print(f"    - Input: {summary.get('total_input_tokens', 0):,}")
    console.print(f"    - Output: {summary.get('total_output_tokens', 0):,}")
    console.print(f"    - Thinking: {summary.get('total_thinking_tokens', 0):,}")
    console.print(f"  Estimated Cost: ${summary.get('total_cost', 0.0):.4f}")
    console.print(f"  Avg Duration: {summary.get('avg_duration_ms', 0.0):.0f}ms")
    console.print(f"  Avg Speed: {summary.get('avg_tokens_per_second', 0.0):.0f} tokens/sec")
    if top_models:
        console.print(f'\n[bold cyan]Top Models:[/bold cyan]')
        for i, model in enumerate(top_models[:5], 1):
            console.print(f"  {i}. {model['model'][:40]} - {model['request_count']} reqs")
    input('\nPress Enter to continue...')
```

### Method: `view_savings`
**Logic & Purpose:**
```text
View smart routing savings.
```

**Parameters:** `self`
**Variables Used:** `total_savings, route, savings_amt, pct, savings, days, reqs`
**Implementation:**
```python
def view_savings(self):
    """View smart routing savings."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold green]💰 Smart Routing Savings (Last {days} Days)[/]', border_style='green'))
    savings = self.usage_tracker.get_savings_data(days=days)
    if not savings:
        console.print('\n[dim]No savings data available yet.[/dim]')
        console.print('[dim]Savings are tracked when original_cost differs from actual cost.[/dim]')
        input('\nPress Enter to continue...')
        return
    total_savings = sum((s['total_savings'] for s in savings))
    console.print(f'\n[bold yellow]Total Savings: ${total_savings:.4f}[/bold yellow]')
    print(f"\n{'Route':<50} {'Reqs':<8} {'Savings':<12} {'Avg %'}")
    print('-' * 85)
    for saving in savings:
        route = f"{saving['original_model'][:20]} → {saving['routed_model'][:20]}"
        reqs = saving['request_count']
        savings_amt = f"${saving['total_savings']:.4f}"
        pct = f"{saving['avg_savings_percent']:.1f}%"
        print(f'{route:<50} {reqs:<8} {savings_amt:<12} {pct}')
    input('\nPress Enter to continue...')
```

### Method: `view_token_breakdown`
**Logic & Purpose:**
```text
View detailed token breakdown.
```

**Parameters:** `self`
**Variables Used:** `data, abs_val, bar_length, stats, pct, bar, days, types`
**Implementation:**
```python
def view_token_breakdown(self):
    """View detailed token breakdown."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold magenta]🔧 Token Composition (Last {days} Days)[/]', border_style='magenta'))
    stats = self.usage_tracker.get_token_breakdown_stats(days=days)
    if not stats:
        console.print('\n[dim]No token breakdown data available yet.[/dim]')
        input('\nPress Enter to continue...')
        return
    console.print(f"\n[bold yellow]Total: {stats['total_tokens']:,} tokens in {stats['request_count']} requests[/bold yellow]")
    types = [('prompt', 'Prompt'), ('completion', 'Completion'), ('reasoning', 'Reasoning'), ('cached', 'Cached'), ('tool_use', 'Tool Use'), ('audio', 'Audio')]
    for key, label in types:
        if key in stats and stats[key]['absolute'] > 0:
            data = stats[key]
            pct = data['percentage']
            abs_val = data['absolute']
            bar_length = int(pct / 2)
            bar = '█' * bar_length
            console.print(f'  [cyan]{label.ljust(12)}[/cyan]: {pct:5.1f}% | {bar} {abs_val:,} tokens')
    input('\nPress Enter to continue...')
```

### Method: `view_providers`
**Logic & Purpose:**
```text
View provider performance.
```

**Parameters:** `self`
**Variables Used:** `cost, tokens, per_k, latency, providers, days, name, reqs`
**Implementation:**
```python
def view_providers(self):
    """View provider performance."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold blue]🏢 Provider Performance (Last {days} Days)[/]', border_style='blue'))
    providers = self.usage_tracker.get_provider_stats(days=days)
    if not providers:
        console.print('\n[dim]No provider data available yet.[/dim]')
        input('\nPress Enter to continue...')
        return
    print(f"\n{'Provider':<18} {'Reqs':<6} {'Tokens':<9} {'Cost':<10} {'$/1K':<8} {'Latency'}")
    print('-' * 80)
    for p in providers:
        name = p['provider'][:16]
        reqs = p['total_requests']
        tokens = f"{p['total_tokens'] / 1000:.0f}k" if p['total_tokens'] >= 1000 else str(p['total_tokens'])
        cost = f"${p['total_cost']:.2f}"
        per_k = f"${p['avg_cost_per_1k_tokens']:.3f}"
        latency = f"{p['avg_duration_ms']:.0f}ms"
        print(f'{name:<18} {reqs:<6} {tokens:<9} {cost:<10} {per_k:<8} {latency}')
    input('\nPress Enter to continue...')
```

### Method: `view_model_comparison`
**Logic & Purpose:**
```text
View model comparison.
```

**Parameters:** `self`
**Variables Used:** `filtered, tok_per_req, per_k, latency, models, min_reqs, tools, days, name, reqs`
**Implementation:**
```python
def view_model_comparison(self):
    """View model comparison."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    min_reqs = Prompt.ask('Min requests per model', default='1').strip()
    try:
        min_reqs = int(min_reqs)
    except ValueError:
        min_reqs = 1
    console.clear()
    console.print(Panel(f'[bold yellow]📊 Model Comparison (Last {days} Days)[/]', border_style='yellow'))
    models = self.usage_tracker.get_model_comparison(days=days)
    filtered = [m for m in models if m['total_requests'] >= min_reqs]
    if not filtered:
        console.print('\n[dim]No model comparison data available yet.[/dim]')
        input('\nPress Enter to continue...')
        return
    print(f"\n{'Model':<32} {'Reqs':<6} {'Tok/Req':<9} {'$/1K':<8} {'Latency':<8} {'Tools'}")
    print('-' * 80)
    for m in filtered:
        name = m['model'][:30]
        reqs = m['total_requests']
        tok_per_req = f"{m['avg_tokens_per_request']:.0f}"
        per_k = f"${m['avg_cost_per_1k_tokens']:.2f}"
        latency = f"{m['avg_duration_ms']:.0f}ms"
        tools = m['tool_requests']
        if m['avg_cost_per_1k_tokens'] < 5:
            per_k = f'[green]{per_k}[/green]'
        elif m['avg_cost_per_1k_tokens'] < 10:
            per_k = f'[yellow]{per_k}[/yellow]'
        else:
            per_k = f'[red]{per_k}[/red]'
        console.print(f'{name:<32} {reqs:<6} {tok_per_req:<9} {per_k:<8} {latency:<8} {tools}')
    input('\nPress Enter to continue...')
```

### Method: `view_insights`
**Logic & Purpose:**
```text
View AI insights.
```

**Parameters:** `self`
**Variables Used:** `priority_color, top_p, total_savings, data, second_p, reasoning_pct, inefficient, pct, top_ineff, top_saving, models, cached_pct, providers, days, insights, token_bd`
**Implementation:**
```python
def view_insights(self):
    """View AI insights."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold magenta]💡 AI Insights & Recommendations (Last {days} Days)[/]', border_style='magenta'))
    data = self.usage_tracker.get_dashboard_summary(days=days)
    if not data or not data.get('summary'):
        console.print('\n[dim]No data available for insights.[/dim]')
        input('\nPress Enter to continue...')
        return
    insights = []
    total_savings = sum((s['total_savings'] for s in data.get('savings', [])))
    if total_savings > 0:
        top_saving = max(data.get('savings', []), key=lambda x: x['total_savings']) if data.get('savings') else None
        if top_saving:
            insights.append(('💰 Cost Savings', f"Saved ${total_savings:.4f} ({top_saving['avg_savings_percent']:.1f}%) by routing {top_saving['request_count']} requests", 'HIGH' if top_saving['avg_savings_percent'] > 20 else 'MED'))
    token_bd = data.get('token_breakdown', {})
    if token_bd and token_bd.get('total_tokens', 0) > 0:
        reasoning_pct = token_bd.get('reasoning', {}).get('percentage', 0)
        if reasoning_pct > 30:
            insights.append(('⚡ High Reasoning Usage', f'{reasoning_pct:.1f}% tokens are reasoning. Consider simpler prompts', 'MED'))
        cached_pct = token_bd.get('cached', {}).get('percentage', 0)
        if cached_pct < 5:
            insights.append(('🔄 Low Cache Utilization', f'Only {cached_pct:.1f}% cached. Use prompt caching', 'LOW'))
    providers = data.get('providers', [])
    if len(providers) > 1:
        top_p = providers[0]
        second_p = providers[1]
        if top_p['total_cost'] > second_p['total_cost'] * 2:
            pct = top_p['total_cost'] / (top_p['total_cost'] + second_p['total_cost']) * 100
            insights.append(('🏢 Provider Concentration', f"{top_p['provider']} is {pct:.1f}% of costs", 'LOW'))
    if data['summary'].get('avg_duration_ms', 0) > 5000:
        insights.append(('⏱️ High Latency', f"Avg {data['summary']['avg_duration_ms']:.0f}ms. Try faster models", 'MED'))
    models = data.get('models', [])
    if len(models) > 3:
        inefficient = [m for m in models if m['avg_cost_per_1k_tokens'] > 10 and m['total_requests'] > 10]
        if inefficient:
            top_ineff = inefficient[0]
            insights.append(('📊 Expensive Models', f"{top_ineff['model']} costs ${top_ineff['avg_cost_per_1k_tokens']:.2f}/1K", 'MED'))
    console.print(f'\n[bold cyan]{len(insights)} Insights Found:[/bold cyan]\n')
    for i, (title, desc, priority) in enumerate(insights, 1):
        priority_color = 'red' if priority == 'HIGH' else 'yellow' if priority == 'MED' else 'cyan'
        console.print(f'  {i}. [bold]{title}[/bold] [{priority_color}]{priority}[/{priority_color}]')
        console.print(f'     {desc}\n')
    input('\nPress Enter to continue...')
```

### Method: `export_data`
**Logic & Purpose:**
```text
Export analytics data.
```

**Parameters:** `self`
**Variables Used:** `success, fmt, choice, filename, days`
**Implementation:**
```python
def export_data(self):
    """Export analytics data."""
    if not self.check_tracking_enabled():
        return
    console.print('\n[cyan]Export Options:[/cyan]')
    console.print('  1. CSV format')
    console.print('  2. JSON format')
    choice = Prompt.ask('\nSelect format', choices=['1', '2'], default='1')
    filename = Prompt.ask('\nFilename (default: analytics_export)', default='analytics_export').strip()
    if choice == '1':
        filename += '.csv'
        fmt = 'csv'
    else:
        filename += '.json'
        fmt = 'json'
    days = Prompt.ask('Days of data (default: 30)', default='30').strip()
    try:
        days = int(days)
    except ValueError:
        days = 30
    console.print(f'\n[yellow]Exporting {fmt} data to {filename}...[/yellow]')
    if fmt == 'csv':
        success = self.usage_tracker.export_to_csv(filename, days=days)
    else:
        success = self.usage_tracker.export_to_json(filename, days=days)
    if success:
        console.print(f'[green]✓ Export successful: {filename}[/green]')
    else:
        console.print(f'[red]✗ Export failed[/red]')
    input('\nPress Enter to continue...')
```

### Method: `full_dashboard`
**Logic & Purpose:**
```text
Display all analytics.
```

**Parameters:** `self`
**Variables Used:** `days`
**Implementation:**
```python
def full_dashboard(self):
    """Display all analytics."""
    if not self.check_tracking_enabled():
        return
    days = Prompt.ask('\nDays to analyze', default='7').strip()
    try:
        days = int(days)
    except ValueError:
        days = 7
    console.clear()
    console.print(Panel(f'[bold white]🔮 Full Analytics Dashboard (Last {days} Days)[/]', border_style='white'))
    try:
        from src.cli.analytics import display_top_models, display_cost_summary, display_savings_analysis, display_token_breakdown, display_provider_stats, display_model_comparison, display_json_toon_analysis, display_ai_insights
        self.usage_tracker.get_dashboard_summary(days=days)
        display_top_models()
        display_cost_summary()
        display_savings_analysis()
        display_token_breakdown()
        display_provider_stats()
        display_model_comparison()
        display_json_toon_analysis()
        display_ai_insights()
    except Exception as e:
        console.print(f'[red]Error displaying dashboard: {e}[/red]')
    input('\nPress Enter to continue...')
```

### Method: `run`
**Logic & Purpose:**
```text
Main loop.
```

**Parameters:** `self`
**Variables Used:** `choice`
**Implementation:**
```python
def run(self):
    """Main loop."""
    while self.running:
        self.draw()
        choice = self.handle_input()
        if choice == '0':
            self.running = False
        elif choice == '1':
            self.toggle_tracking()
        elif choice == '2':
            self.view_summary()
        elif choice == '3':
            self.view_savings()
        elif choice == '4':
            self.view_token_breakdown()
        elif choice == '5':
            self.view_providers()
        elif choice == '6':
            self.view_model_comparison()
        elif choice == '7':
            self.view_insights()
        elif choice == '8':
            self.export_data()
        elif choice == '9':
            self.full_dashboard()
        else:
            console.print('\n[red]Invalid option[/red]')
            input('Press Enter to continue...')
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Entry point.
```

**Parameters:** ``
**Variables Used:** `configurator`
**Implementation:**
```python
def main():
    """Entry point."""
    try:
        configurator = AnalyticsConfigurator()
        configurator.run()
    except KeyboardInterrupt:
        console.print('\n[dim]Analytics closed.[/dim]')
    except Exception as e:
        console.print(f'\n[red]Error: {e}[/red]')
        sys.exit(1)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/model_selector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/model_selector.py`

**Module Overview**: 
```text
Interactive model selector with static TUI (no scrolling spam).
```

## Global Presets & Variables
- `PROVIDERS` = `{'vibeproxy': {'name': '🌌 VibeProxy/Antigravity', 'endpoint': 'http://127.0.0.1:8317/v1', 'api_key_env': None, 'detect_port': 8317, 'description': 'Local OAuth (Claude/Gemini via Google)', 'model_prefix': ''}, 'openrouter': {'name': '🚀 OpenRouter', 'endpoint': 'https://openrouter.ai/api/v1', 'api_key_env': 'OPENROUTER_API_KEY', 'description': '352+ models, free tier available', 'model_prefix': ''}, 'gemini': {'name': '🌟 Google Gemini', 'endpoint': 'https://generativelanguage.googleapis.com/v1beta/openai/', 'api_key_env': 'GOOGLE_API_KEY', 'description': 'Direct Gemini API', 'model_prefix': ''}, 'openai': {'name': '🤖 OpenAI', 'endpoint': 'https://api.openai.com/v1', 'api_key_env': 'OPENAI_API_KEY', 'description': 'GPT-4, o1, DALL-E', 'model_prefix': ''}, 'ollama': {'name': '🏠 Ollama', 'endpoint': 'http://localhost:11434/v1', 'api_key_env': None, 'detect_port': 11434, 'description': 'Local models (free)', 'model_prefix': ''}, 'custom': {'name': '⚙️  Custom Endpoint', 'endpoint': '', 'api_key_env': None, 'description': 'Configure manually', 'model_prefix': ''}}`
- `DEFAULT_MODELS` = `['vibeproxy/gemini-2.5-pro', 'vibeproxy/gemini-2.5-flash', 'vibeproxy/gemini-2.0-flash-thinking', 'vibeproxy/claude-sonnet-4', 'vibeproxy/claude-opus-4', 'vibeproxy/gpt-4o', 'vibeproxy/qwen-2.5-max', 'antigravity/gemini-3-pro', 'antigravity/gemini-3-flash', 'antigravity/claude-sonnet-4.5', 'antigravity/claude-sonnet-4.5-thinking', 'antigravity/claude-opus-4.5', 'antigravity/gpt-oss-120b', 'openai/gpt-4o', 'openai/gpt-4o-mini', 'openai/gpt-4-turbo', 'openai/o1', 'openai/o1-mini', 'anthropic/claude-3.5-sonnet', 'anthropic/claude-3-5-haiku', 'anthropic/claude-3-opus', 'anthropic/claude-sonnet-4', 'anthropic/claude-opus-4', 'google/gemini-2.5-pro', 'google/gemini-2.5-flash', 'google/gemini-2.0-flash-thinking', 'google/gemini-pro-1.5', 'google/gemini-flash-1.5', 'openrouter/anthropic/claude-3.5-sonnet', 'openrouter/openai/gpt-4o', 'openrouter/google/gemini-pro-1.5', 'openrouter/meta-llama/llama-3.1-405b-instruct', 'openrouter/meta-llama/llama-3.1-70b-instruct', 'openrouter/qwen/qwen-2.5-72b-instruct', 'openrouter/mistral/mistral-large-2407', 'openrouter/cohere/command-r-plus-08-2024', 'meta-llama/llama-3.1-405b-instruct', 'meta-llama/llama-3.1-70b-instruct', 'mistral/mistral-large-2407', 'cohere/command-r-plus-08-2024', 'qwen/qwen-2.5-72b-instruct']`

## Dependencies & Imports
json, os, sys, socket, pathlib.Path, typing.List, typing.Optional, typing.Tuple, typing.Dict, src.services.models.model_filter.get_available_models, src.services.models.model_filter.filter_models, src.services.models.model_filter.model_filter, src.services.models.modes.ModeManager, src.services.models.recommender.ModelRecommender, src.services.models.free_model_rankings.get_or_build_free_model_rankings, src.services.models.free_model_rankings.get_top_free_models, src.services.models.selection_history.record_selection, src.services.models.selection_history.get_recent_selections, src.services.usage.model_limits.get_model_limits, src.cli.env_utils.update_env_values

## Feature Function: `detect_provider_status`
**Logic & Purpose:**
```text
Detect if a provider is available.
Returns (is_available, status_message).
```

**Parameters:** `provider_id`
**Variables Used:** `key, sock, result, provider`
**Implementation:**
```python
def detect_provider_status(provider_id: str) -> Tuple[bool, str]:
    """
    Detect if a provider is available.
    Returns (is_available, status_message).
    """
    provider = PROVIDERS.get(provider_id, {})
    if 'detect_port' in provider:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', provider['detect_port']))
            sock.close()
            if result == 0:
                return (True, '✓ RUNNING')
            else:
                return (False, '○ Not running')
        except Exception:
            return (False, '○ Error')
    if provider.get('api_key_env'):
        key = os.environ.get(provider['api_key_env'], '')
        if key and key not in ['dummy', 'your-key-here', '']:
            return (True, f'✓ Key set')
        else:
            return (False, f'○ No API key')
    if provider_id == 'custom':
        return (True, 'Manual config')
    return (False, 'Unknown')
```

---

## Feature Function: `get_available_providers`
**Logic & Purpose:**
```text
Get list of available providers with status.
Returns list of (provider_id, display_name, status, is_available).
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
def get_available_providers() -> List[Tuple[str, str, str, bool]]:
    """
    Get list of available providers with status.
    Returns list of (provider_id, display_name, status, is_available).
    """
    result = []
    for pid, pinfo in PROVIDERS.items():
        is_available, status = detect_provider_status(pid)
        result.append((pid, pinfo['name'], status, is_available))
    return result
```

---

## Feature Function: `visual_len`
**Logic & Purpose:**
```text
Calculate visual length of string, accounting for double-width emojis.
```

**Parameters:** `s`
**Variables Used:** `count, double_width_chars`
**Implementation:**
```python
def visual_len(s: str) -> int:
    """Calculate visual length of string, accounting for double-width emojis."""
    double_width_chars = '🌌🚀🌟🤖🏠⚙️▶★🆓🧠👁️🔧✨🏆⭐⚠️✅❌⏳💡'
    count = sum((1 for c in s if c in double_width_chars))
    return len(s) + count
```

---

## Feature Function: `pad_visual`
**Logic & Purpose:**
```text
Pad string to visual width.
```

**Parameters:** `s, width, align`
**Variables Used:** `right, padding, vlen, left`
**Implementation:**
```python
def pad_visual(s: str, width: int, align: str='<') -> str:
    """Pad string to visual width."""
    vlen = visual_len(s)
    padding = max(0, width - vlen)
    if align == '<':
        return s + ' ' * padding
    elif align == '>':
        return ' ' * padding + s
    elif align == '^':
        left = padding // 2
        right = padding - left
        return ' ' * left + s + ' ' * right
    return s
```

---

## Feature Function: `draw_provider_menu`
**Logic & Purpose:**
```text
Draw the provider selection menu.
```

**Parameters:** `cursor, slot, current_provider`
**Variables Used:** `line, current_mark, all_providers, style_start, title, marker, providers, desc`
**Implementation:**
```python
def draw_provider_menu(cursor: int, slot: str, current_provider: Optional[str]=None):
    """Draw the provider selection menu."""
    clear_screen()
    rows, cols = get_terminal_size()
    all_providers = get_available_providers()
    providers = []
    for p in all_providers:
        pid, _, _, is_avail = p
        if is_avail or pid in ['custom', 'vibeproxy', 'ollama'] or pid == current_provider:
            providers.append(p)
    if not providers:
        providers = all_providers
    print('╔' + '═' * (cols - 2) + '╗')
    title = f' SELECT PROVIDER FOR {slot.upper()} MODEL '
    print('║' + title.center(cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    print('║' + ' ' * (cols - 2) + '║')
    for i, (pid, name, status, is_available) in enumerate(providers):
        if i == cursor:
            marker = '▶'
            style_start = '★ ' if is_available else '  '
        else:
            marker = ' '
            style_start = '  ' if is_available else '  '
        current_mark = ' [CURRENT]' if pid == current_provider else ''
        line = f'  {marker} {name}  {status}{current_mark}'
        desc = f"      {PROVIDERS[pid]['description']}"
        print('║' + pad_visual(line, cols - 2) + '║')
        print('║' + pad_visual(desc, cols - 2) + '║')
    print('║' + ' ' * (cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    print('║ CONTROLS:'.ljust(cols - 1) + '║')
    print('║   ↑/↓  Navigate   Enter  Select   q  Back'.ljust(cols - 1) + '║')
    print('╚' + '═' * (cols - 2) + '╝')
    return providers
```

---

## Feature Function: `pick_provider`
**Logic & Purpose:**
```text
Let user pick a provider for the given slot.
```

**Parameters:** `slot, current_provider`
**Variables Used:** `all_p, cursor, key, cmd, idx, providers, displayed_providers, temp_providers`
**Implementation:**
```python
def pick_provider(slot: str, current_provider: Optional[str]=None) -> Optional[str]:
    """Let user pick a provider for the given slot."""
    temp_providers = get_available_providers()
    cursor = 0
    all_p = get_available_providers()
    providers = []
    for p in all_p:
        pid, _, _, is_avail = p
        if is_avail or pid in ['custom', 'vibeproxy', 'ollama'] or pid == current_provider:
            providers.append(p)
    if current_provider:
        for i, (pid, _, _, _) in enumerate(providers):
            if pid == current_provider:
                cursor = i
                break
    while True:
        if RICH_AVAILABLE:
            console.clear()
            console.print(draw_menu_rich(cursor, slot, current_provider))
            providers = all_p
        else:
            displayed_providers = draw_provider_menu(cursor, slot, current_provider)
            providers = displayed_providers
        try:
            if ARROW_SUPPORT:
                key = get_key()
                if key == 'UP' or key == 'k':
                    cursor = (cursor - 1) % len(providers)
                elif key == 'DOWN' or key == 'j':
                    cursor = (cursor + 1) % len(providers)
                elif key == 'ENTER':
                    pid, _, _, is_available = providers[cursor]
                    if not is_available and pid not in ['custom']:
                        pass
                    return pid
                elif key == 'q':
                    return None
            else:
                cmd = input('→ ').strip()
                if cmd == 'q':
                    return None
                elif cmd.isdigit():
                    idx = int(cmd) - 1
                    if 0 <= idx < len(providers):
                        return providers[idx][0]
        except (EOFError, KeyboardInterrupt):
            return None
```

---

## Feature Function: `clear_screen`
**Logic & Purpose:**
```text
Clear terminal screen.
```

**Parameters:** ``
**Implementation:**
```python
def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')
```

---

## Feature Function: `get_terminal_size`
**Logic & Purpose:**
```text
Get terminal size (rows, cols).
```

**Parameters:** ``
**Variables Used:** `size`
**Implementation:**
```python
def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size (rows, cols)."""
    try:
        size = os.get_terminal_size()
        return (size.lines, size.columns)
    except (OSError, ValueError, AttributeError):
        return (24, 80)
```

---

## Feature Function: `load_all_models`
**Logic & Purpose:**
```text
Load all available models from the enriched database or use defaults.

Args:
    refresh: If True, forces a refresh from OpenRouter API

Priority order:
1. Live fetch from OpenRouter (if refresh=True)
2. data/openrouter_models.json (new fetcher format)
3. data/openrouter_models_enriched.json (enriched data)
4. models/model_limits.json (legacy)
5. DEFAULT_MODELS (hardcoded fallback)
```

**Parameters:** `refresh`
**Variables Used:** `new_cache_path, data, enriched_path, project_root, legacy_path`
**Implementation:**
```python
def load_all_models(refresh: bool=False) -> List[str]:
    """Load all available models from the enriched database or use defaults.

    Args:
        refresh: If True, forces a refresh from OpenRouter API

    Priority order:
    1. Live fetch from OpenRouter (if refresh=True)
    2. data/openrouter_models.json (new fetcher format)
    3. data/openrouter_models_enriched.json (enriched data)
    4. models/model_limits.json (legacy)
    5. DEFAULT_MODELS (hardcoded fallback)
    """
    project_root = Path(__file__).parent.parent.parent
    if refresh:
        try:
            from src.services.models.openrouter_fetcher import refresh_openrouter_models_sync
            print('🔄 Refreshing models from OpenRouter...')
            data, was_refreshed, error = refresh_openrouter_models_sync(force=True)
            if was_refreshed and data.get('models'):
                print(f"✅ Fetched {len(data['models'])} models")
                return sorted([m['id'] for m in data['models']])
            elif error:
                print(f'⚠️  Refresh failed: {error}')
        except Exception as e:
            print(f'⚠️  Refresh error: {e}')
    new_cache_path = project_root / 'data' / 'openrouter_models.json'
    if new_cache_path.exists():
        try:
            with open(new_cache_path, 'r') as f:
                data = json.load(f)
                if 'models' in data:
                    return sorted([m['id'] for m in data['models']])
        except Exception:
            pass
    enriched_path = project_root / 'data' / 'openrouter_models_enriched.json'
    if enriched_path.exists():
        try:
            with open(enriched_path, 'r') as f:
                data = json.load(f)
                if 'models' in data:
                    return sorted([m['id'] for m in data['models']])
        except Exception:
            pass
    legacy_path = project_root / 'models' / 'model_limits.json'
    if legacy_path.exists():
        try:
            with open(legacy_path, 'r') as f:
                data = json.load(f)
                return sorted(data.keys())
        except Exception:
            pass
    return sorted(DEFAULT_MODELS)
```

---

## Feature Function: `refresh_models_cache`
**Logic & Purpose:**
```text
Force refresh the models cache from OpenRouter.

Returns:
    Tuple of (success, message)
```

**Parameters:** ``
**Implementation:**
```python
def refresh_models_cache() -> Tuple[bool, str]:
    """
    Force refresh the models cache from OpenRouter.

    Returns:
        Tuple of (success, message)
    """
    try:
        from src.services.models.openrouter_fetcher import refresh_openrouter_models_sync
        data, was_refreshed, error = refresh_openrouter_models_sync(force=True)
        if error:
            return (False, f'Refresh failed: {error}')
        if was_refreshed:
            return (True, f"Refreshed {len(data.get('models', []))} models")
        return (True, f"Using cached data ({len(data.get('models', []))} models)")
    except Exception as e:
        return (False, f'Error: {str(e)}')
```

---

## Feature Function: `get_free_ranking`
**Parameters:** `model_id`
**Variables Used:** `_free_rankings_map`
**Implementation:**
```python
def get_free_ranking(model_id: str):
    global _free_rankings_map
    if _free_rankings_map is None:
        _free_rankings_map = {}
        try:
            for row in get_or_build_free_model_rankings():
                _free_rankings_map[row.model_id] = row
        except Exception:
            _free_rankings_map = {}
    return _free_rankings_map.get(model_id)
```

---

## Feature Function: `get_enriched_model_info`
**Logic & Purpose:**
```text
Get enriched metadata for a specific model.

Returns dict with: context_length, max_completion_tokens, supports_reasoning,
supports_tools, supports_vision, pricing, description, etc.
```

**Parameters:** `model_id`
**Variables Used:** `_enriched_models_cache, project_root, data, enriched_path`
**Implementation:**
```python
def get_enriched_model_info(model_id: str) -> Optional[dict]:
    """Get enriched metadata for a specific model.
    
    Returns dict with: context_length, max_completion_tokens, supports_reasoning,
    supports_tools, supports_vision, pricing, description, etc.
    """
    global _enriched_models_cache
    if _enriched_models_cache is None:
        project_root = Path(__file__).parent.parent.parent
        enriched_path = project_root / 'data' / 'openrouter_models_enriched.json'
        if enriched_path.exists():
            try:
                with open(enriched_path, 'r') as f:
                    data = json.load(f)
                    _enriched_models_cache = {m['id']: m for m in data.get('models', [])}
            except Exception:
                _enriched_models_cache = {}
        else:
            _enriched_models_cache = {}
    return _enriched_models_cache.get(model_id)
```

---

## Feature Function: `format_model_line`
**Logic & Purpose:**
```text
Format a single model line for display with enriched capabilities.
```

**Parameters:** `idx, model_id, selected_for, max_width`
**Variables Used:** `part3, badge_str, badges, part4, context, part2, enriched, suffix_len, output, prefix_len, free_rank, badge_len, name_width, part1, display_name`
**Implementation:**
```python
def format_model_line(idx: int, model_id: str, selected_for: Optional[str]=None, max_width: int=80) -> str:
    """Format a single model line for display with enriched capabilities."""
    enriched = get_enriched_model_info(model_id)
    if enriched:
        context = enriched.get('context_length', 0)
        output = enriched.get('max_completion_tokens', 0)
    else:
        context, output = get_model_limits(model_id)

    def fmt(tokens):
        if tokens >= 1000000:
            return f'{tokens / 1000000:.1f}M'
        elif tokens >= 1000:
            return f'{tokens / 1000:.0f}k'
        return str(tokens) if tokens else '?'
    badges = []
    free_rank = get_free_ranking(model_id)
    if enriched:
        if enriched.get('pricing', {}).get('is_free', False):
            badges.append('🆓')
        if enriched.get('supports_reasoning', False):
            badges.append('🧠')
        if enriched.get('supports_vision', False):
            badges.append('👁️')
        if enriched.get('supports_tools', False):
            badges.append('🔧')
    else:
        if model_filter.is_new_model(model_id):
            badges.append('✨')
        if model_filter.is_free_model(model_id):
            badges.append('🆓')
        if model_filter.is_top_model(model_id):
            badges.append('🏆')
    if free_rank:
        if free_rank.class_type == 'stealth_free':
            badges.append('⚡STEALTH')
        elif free_rank.class_type == 'evergreen_free':
            badges.append('🌲EVERGREEN')
    if model_filter.get_recently_used_models(20) and model_id in model_filter.get_recently_used_models(20):
        badges.append('⭐')
    if selected_for:
        badges.append(f'[{selected_for}]')
    badge_str = ' '.join(badges) if badges else ''
    badge_len = visual_len(badge_str) + 1 if badge_str else 0
    suffix_len = 16 + badge_len
    prefix_len = 6
    name_width = max(10, max_width - prefix_len - suffix_len)
    display_name = model_id
    if len(display_name) > name_width:
        display_name = display_name[:name_width - 3] + '...'
    part1 = f'{idx:3}. '
    part2 = pad_visual(display_name, name_width)
    part3 = f' {fmt(context):>6} {fmt(output):>6}  '
    part4 = badge_str
    return part1 + part2 + part3 + part4
```

---

## Feature Function: `draw_ui_rich`
**Logic & Purpose:**
```text
Build the Rich UI for the model selector.
```

**Parameters:** `models, page, per_page, search_query, big_model, middle_model, small_model, show_all`
**Variables Used:** `header_text, layout, model_table, start_idx, m_id, sel_table, enriched, end_idx, mode, tag, badge_str, footer_text, sel_panel, badges, list_panel, current_page, total_pages, footer_panel, total_models, selected_map`
**Implementation:**
```python
def draw_ui_rich(models: List[str], page: int, per_page: int, search_query: str, big_model: Optional[str], middle_model: Optional[str], small_model: Optional[str], show_all: bool) -> Panel:
    """Build the Rich UI for the model selector."""
    sel_table = Table.grid(expand=True)
    sel_table.add_column(style='bold cyan', width=10)
    sel_table.add_column(style='cyan')
    sel_table.add_row('BIG:', big_model or '[dim]not set[/dim]')
    sel_table.add_row('MIDDLE:', middle_model or '[dim]not set[/dim]', style='bold green')
    sel_table.add_row('SMALL:', small_model or '[dim]not set[/dim]', style='bold yellow')
    sel_panel = Panel(sel_table, title='[bold]Current Selections[/bold]', border_style='blue', box=box.ROUNDED)
    mode = 'ALL MODELS' if show_all else 'RECOMMENDED'
    total_models = len(models)
    total_pages = (total_models + per_page - 1) // per_page
    current_page = page + 1
    header_text = f'{mode} ({total_models} models) - Page {current_page}/{total_pages}'
    if search_query:
        header_text += f" - Search: '{search_query}'"
    model_table = Table(expand=True, box=None, padding=(0, 1), show_header=True, header_style='bold magenta')
    model_table.add_column('#', justify='right', width=4)
    model_table.add_column('Model', style='cyan')
    model_table.add_column('CTX', justify='right', width=6)
    model_table.add_column('OUT', justify='right', width=6)
    model_table.add_column('Tags', style='dim')
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_models)
    selected_map = {}
    if big_model in models:
        selected_map[big_model] = '[bold cyan]B[/]'
    if middle_model in models:
        selected_map[middle_model] = '[bold green]M[/]'
    if small_model in models:
        selected_map[small_model] = '[bold yellow]S[/]'
    for i in range(start_idx, end_idx):
        m_id = models[i]
        tag = selected_map.get(m_id, '')
        enriched = get_enriched_model_info(m_id)
        if enriched:
            ctx, out = (enriched.get('context_length', 0), enriched.get('max_completion_tokens', 0))
        else:
            ctx, out = get_model_limits(m_id)

        def fmt_t(tokens):
            if tokens >= 1000000:
                return f'{tokens / 1000000:.1f}M'
            if tokens >= 1000:
                return f'{tokens / 1000:.0f}k'
            return str(tokens) if tokens else '?'
        badges = []
        if enriched:
            if enriched.get('pricing', {}).get('is_free', False):
                badges.append('🆓')
            if enriched.get('supports_reasoning', False):
                badges.append('🧠')
            if enriched.get('supports_vision', False):
                badges.append('👁️')
            if enriched.get('supports_tools', False):
                badges.append('🔧')
        badge_str = ' '.join(badges)
        if tag:
            badge_str = f'{tag} {badge_str}'
        model_table.add_row(str(i + 1), m_id, fmt_t(ctx), fmt_t(out), badge_str)
    list_panel = Panel(model_table, title=f'[bold]{header_text}[/bold]', border_style='magenta', box=box.ROUNDED)
    footer_text = Text.from_markup('[bold cyan][number] b/m/s[/] Assign  [bold cyan]n/p[/] Paging  [bold cyan]/[/] Search  [bold cyan]a[/] Toggle Recommended  [bold cyan]q[/] Quit', justify='center')
    footer_panel = Panel(footer_text, border_style='dim', box=box.ROUNDED)
    layout = Group(Panel(Align.center(Spinner('dots', text='[bold]MODEL SELECTOR[/bold]')), border_style='blue', box=box.ROUNDED), sel_panel, list_panel, footer_panel)
    return Panel(layout, box=None)
```

---

## Feature Function: `draw_menu_rich`
**Logic & Purpose:**
```text
Build the Rich UI for the main menu.
```

**Parameters:** `cursor, big_model, middle_model, small_model, big_provider, middle_provider, small_provider`
**Variables Used:** `menu_table, layout, options, name`
**Implementation:**
```python
def draw_menu_rich(cursor: int, big_model: str, middle_model: str, small_model: str, big_provider: str=None, middle_provider: str=None, small_provider: str=None) -> Panel:
    """Build the Rich UI for the main menu."""

    def fmt_provider(pid: str) -> str:
        if not pid:
            return 'default'
        name = PROVIDERS.get(pid, {}).get('name', pid)
        for icon in ['🌌 ', '🚀 ', '🌟 ', '🤖 ', '🏠 ', '⚙️  ']:
            name = name.replace(icon, '')
        return name
    options = [(f"BIG: {big_model or 'not set'} @ {fmt_provider(big_provider)}", 'cyan'), (f"MIDDLE: {middle_model or 'not set'} @ {fmt_provider(middle_provider)}", 'green'), (f"SMALL: {small_model or 'not set'} @ {fmt_provider(small_provider)}", 'yellow'), ('VIEW SELECTION HISTORY', 'white'), ('MANAGE FREE CASCADE', 'white'), ('SAVE & QUIT', 'bold red'), ('BACK TO SETTINGS', 'dim')]
    menu_table = Table.grid(expand=True)
    menu_table.add_column()
    for i, (label, color) in enumerate(options):
        if i == cursor:
            menu_table.add_row(Text(f' ▶ {label}', style=f'bold {color} reverse'))
        else:
            menu_table.add_row(Text(f'   {label}', style=color))
    layout = Group(Panel(Align.center(Spinner('bouncingBar', text='[bold]MODEL & PROVIDER SELECTOR[/bold]')), border_style='blue', box=box.ROUNDED), Panel(menu_table, border_style='blue', box=box.ROUNDED, padding=(1, 2)), Panel(Align.center('[bold cyan]↑/↓[/] Navigate  [bold cyan]Enter[/] Configure  [bold cyan]q[/] Quit'), border_style='dim', box=box.ROUNDED))
    return Panel(layout, box=None)
```

---

## Feature Function: `get_key`
**Logic & Purpose:**
```text
Get a single keypress (works with or without readchar).
```

**Parameters:** ``
**Variables Used:** `key`
**Implementation:**
```python
def get_key():
    """Get a single keypress (works with or without readchar)."""
    if ARROW_SUPPORT:
        key = readchar.readkey()
        if key == readchar.key.UP:
            return 'UP'
        elif key == readchar.key.DOWN:
            return 'DOWN'
        elif key == readchar.key.ENTER or key == '\r' or key == '\n':
            return 'ENTER'
        else:
            return key
    else:
        return input('→ ').strip()
```

---

## Feature Function: `parse_cascade`
**Parameters:** `value`
**Implementation:**
```python
def parse_cascade(value: str) -> List[str]:
    if not value:
        return []
    return [m.strip() for m in value.split(',') if m.strip()]
```

---

## Feature Function: `format_cascade`
**Parameters:** `models`
**Implementation:**
```python
def format_cascade(models: List[str]) -> str:
    return ','.join(models)
```

---

## Feature Function: `show_selection_history`
**Logic & Purpose:**
```text
Render recent model selection history.
```

**Parameters:** `limit`
**Variables Used:** `events, line`
**Implementation:**
```python
def show_selection_history(limit: int=20):
    """Render recent model selection history."""
    clear_screen()
    rows, cols = get_terminal_size()
    print('╔' + '═' * (cols - 2) + '╗')
    print('║' + ' MODEL SELECTION HISTORY '.center(cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    events = get_recent_selections(limit=limit)
    if not events:
        print('║' + pad_visual(' No history yet.', cols - 2) + '║')
    else:
        for idx, e in enumerate(events, 1):
            line = f'{idx:2}. [{e.slot}] {e.model_id} ({e.source})'
            if len(line) > cols - 4:
                line = line[:cols - 7] + '...'
            print('║ ' + pad_visual(line, cols - 3) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    print('║ Press Enter to return'.ljust(cols - 1) + '║')
    print('╚' + '═' * (cols - 2) + '╝')
    input()
```

---

## Feature Function: `manage_free_cascade`
**Logic & Purpose:**
```text
Build/edit free-model cascade ordering.
Returns env updates.
```

**Parameters:** `config, big_model, middle_model, small_model`
**Variables Used:** `auto_middle, auto_big, current_small, big, cmd, top_free, mid, current_middle, current_big, auto_small, small`
**Implementation:**
```python
def manage_free_cascade(config, big_model: str, middle_model: str, small_model: str) -> Dict[str, str]:
    """
    Build/edit free-model cascade ordering.
    Returns env updates.
    """

    def normalize_current(value) -> List[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            return parse_cascade(value)
        return []
    current_big = normalize_current(getattr(config, 'big_cascade', []))
    current_middle = normalize_current(getattr(config, 'middle_cascade', []))
    current_small = normalize_current(getattr(config, 'small_cascade', []))
    top_free = get_top_free_models(limit=25)
    auto_big = [m for m in top_free if m != big_model][:8]
    auto_middle = [m for m in top_free if m != middle_model][:8]
    auto_small = [m for m in top_free if m != small_model][:8]
    clear_screen()
    print('Free Cascade Manager')
    print('====================')
    print('\nCurrent:')
    print(f"  BIG_CASCADE   = {(', '.join(current_big) if current_big else '(empty)')}")
    print(f"  MIDDLE_CASCADE= {(', '.join(current_middle) if current_middle else '(empty)')}")
    print(f"  SMALL_CASCADE = {(', '.join(current_small) if current_small else '(empty)')}")
    print('\nRecommended Top Free Models:')
    for i, model in enumerate(top_free[:15], 1):
        print(f'  {i:2}. {model}')
    print('\nOptions:')
    print('  1) Apply auto free cascade')
    print('  2) Edit manually')
    print('  3) Disable cascade')
    print('  q) Back')
    cmd = input('\n→ ').strip().lower()
    if cmd == '1':
        return {'MODEL_CASCADE': 'true', 'BIG_CASCADE': format_cascade(auto_big), 'MIDDLE_CASCADE': format_cascade(auto_middle), 'SMALL_CASCADE': format_cascade(auto_small)}
    if cmd == '2':
        big = input('BIG_CASCADE (comma list, blank keep current): ').strip()
        mid = input('MIDDLE_CASCADE (comma list, blank keep current): ').strip()
        small = input('SMALL_CASCADE (comma list, blank keep current): ').strip()
        return {'MODEL_CASCADE': 'true', 'BIG_CASCADE': big if big else format_cascade(current_big), 'MIDDLE_CASCADE': mid if mid else format_cascade(current_middle), 'SMALL_CASCADE': small if small else format_cascade(current_small)}
    if cmd == '3':
        return {'MODEL_CASCADE': 'false', 'BIG_CASCADE': '', 'MIDDLE_CASCADE': '', 'SMALL_CASCADE': ''}
    return {}
```

---

## Feature Function: `run_model_selector`
**Logic & Purpose:**
```text
Run the interactive model selector with static UI.
```

**Parameters:** ``
**Variables Used:** `current_provider, small_model, selected, val, all_models, middle_provider, updates, big_model, cascade_updates, endpoint_url, menu_cursor, key_env_var, middle_model, slot_names, key, p, cmd, slot, providers_to_add, prov_info, small_provider, big_provider, new_provider, choice`
**Implementation:**
```python
def run_model_selector():
    """Run the interactive model selector with static UI."""
    from src.core.config import config
    all_models = load_all_models()
    if not all_models:
        print('❌ No models found. Run the scraper first.')
        return
    big_model = config.big_model
    middle_model = config.middle_model
    small_model = config.small_model

    def detect_current_provider(endpoint: str) -> Optional[str]:
        if not endpoint:
            return None
        for pid, pinfo in PROVIDERS.items():
            if pinfo.get('endpoint') and pinfo['endpoint'] in endpoint:
                return pid
        if '127.0.0.1:8317' in endpoint or 'localhost:8317' in endpoint:
            return 'vibeproxy'
        if 'openrouter.ai' in endpoint:
            return 'openrouter'
        if 'googleapis' in endpoint:
            return 'gemini'
        if 'openai.com' in endpoint:
            return 'openai'
        if ':11434' in endpoint:
            return 'ollama'
        return None
    big_provider = detect_current_provider(getattr(config, 'big_endpoint', '') or config.openai_base_url)
    middle_provider = detect_current_provider(getattr(config, 'middle_endpoint', '') or config.openai_base_url)
    small_provider = detect_current_provider(getattr(config, 'small_endpoint', '') or config.openai_base_url)
    menu_cursor = 0
    while True:
        draw_menu(menu_cursor, big_model, middle_model, small_model, big_provider, middle_provider, small_provider)
        if ARROW_SUPPORT:
            key = get_key()
            if key == 'UP' or key == 'k':
                menu_cursor = (menu_cursor - 1) % 7
                continue
            elif key == 'DOWN' or key == 'j':
                menu_cursor = (menu_cursor + 1) % 7
                continue
            elif key == 'ENTER':
                if menu_cursor == 3:
                    show_selection_history(limit=30)
                    continue
                elif menu_cursor == 4:
                    cascade_updates = manage_free_cascade(config, big_model, middle_model, small_model)
                    if cascade_updates:
                        update_env_values(cascade_updates)
                        print('\n✅ Cascade settings updated.')
                        input('Press Enter to continue...')
                    continue
                elif menu_cursor == 5:
                    updates = {'BIG_MODEL': big_model, 'MIDDLE_MODEL': middle_model, 'SMALL_MODEL': small_model}
                    providers_to_add = set()
                    for tier_name, provider_val in [('big', big_provider), ('middle', middle_provider), ('small', small_provider)]:
                        p = (provider_val or '').lower()
                        if p and p not in ['vibeproxy', 'ollama', 'custom']:
                            if p not in providers_to_add:
                                providers_to_add.add(p)
                                prov_info = PROVIDERS.get(p, {})
                                endpoint_url = prov_info.get('endpoint', '')
                                key_env_var = prov_info.get('api_key_env')
                                if endpoint_url:
                                    updates[f'PROVIDERS_{p}_URL'] = endpoint_url
                                if key_env_var:
                                    val = os.environ.get(key_env_var, '')
                                    if not val and key_env_var == 'OPENROUTER_API_KEY':
                                        val = os.environ.get('PROVIDER_API_KEY', '')
                                    if val:
                                        updates[f'PROVIDERS_{p}_API_KEY'] = val
                    print('\n⏳ Saving configuration...')
                    update_env_values(updates)
                    print(f'\n✅ Configuration saved!')
                    print(f"   BIG:    {big_model} @ {big_provider or 'default'}")
                    print(f"   MIDDLE: {middle_model} @ {middle_provider or 'default'}")
                    print(f"   SMALL:  {small_model} @ {small_provider or 'default'}")
                    print('\n💡 Restart proxy for changes to take effect.')
                    input('\nPress Enter to continue...')
                    return
                elif menu_cursor == 6:
                    print('\n🔙 Returning to settings...')
                    return
                else:
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[menu_cursor]
                    current_provider = [big_provider, middle_provider, small_provider][menu_cursor]
                    new_provider = pick_provider(slot, current_provider)
                    if new_provider:
                        selected = pick_model(all_models, slot, new_provider)
                        if selected:
                            if slot == 'big':
                                big_model = selected
                                big_provider = new_provider
                                record_selection('big', selected, provider=new_provider, source='tui')
                            elif slot == 'middle':
                                middle_model = selected
                                middle_provider = new_provider
                                record_selection('middle', selected, provider=new_provider, source='tui')
                            elif slot == 'small':
                                small_model = selected
                                small_provider = new_provider
                                record_selection('small', selected, provider=new_provider, source='tui')
            elif key == 'q':
                print('\n❌ Cancelled (no changes saved)')
                return
        else:
            cmd = input('→ ').strip()
            if cmd == 'q':
                print('\n❌ Cancelled')
                return
            elif cmd.isdigit():
                choice = int(cmd) - 1
                if choice == 3:
                    show_selection_history(limit=30)
                    continue
                elif choice == 4:
                    cascade_updates = manage_free_cascade(config, big_model, middle_model, small_model)
                    if cascade_updates:
                        update_env_values(cascade_updates)
                        print('\n✅ Cascade settings updated.')
                    continue
                elif choice == 5:
                    updates = {'BIG_MODEL': big_model, 'MIDDLE_MODEL': middle_model, 'SMALL_MODEL': small_model}
                    update_env_values(updates)
                    print(f'\n✅ Saved!')
                    return
                elif choice == 6:
                    print('\n🔙 Returning to settings...')
                    return
                elif 0 <= choice < 3:
                    slot_names = ['big', 'middle', 'small']
                    slot = slot_names[choice]
                    new_provider = pick_provider(slot)
                    if new_provider:
                        selected = pick_model(all_models, slot, new_provider)
                        if selected:
                            if slot == 'big':
                                big_model = selected
                                big_provider = new_provider
                                record_selection('big', selected, provider=new_provider, source='tui')
                            elif slot == 'middle':
                                middle_model = selected
                                middle_provider = new_provider
                                record_selection('middle', selected, provider=new_provider, source='tui')
                            elif slot == 'small':
                                small_model = selected
                                small_provider = new_provider
                                record_selection('small', selected, provider=new_provider, source='tui')
```

---

## Feature Function: `pick_model`
**Logic & Purpose:**
```text
Pick a model with arrow keys or typing.

Args:
    all_models: List of all available models
    slot: Slot name (big, middle, small)
    provider: Optional provider to filter/recommend models for
```

**Parameters:** `all_models, slot, provider`
**Variables Used:** `per_page, total_pages, key, cursor, candidates, page, cmd, selected, search_query, ranked_free, view_mode, models, idx, filtered_base_models, current_input`
**Implementation:**
```python
def pick_model(all_models: List[str], slot: str, provider: Optional[str]=None) -> Optional[str]:
    """Pick a model with arrow keys or typing.
    
    Args:
        all_models: List of all available models
        slot: Slot name (big, middle, small)
        provider: Optional provider to filter/recommend models for
    """
    view_mode = 'recommended-free'
    search_query = ''
    page = 0
    cursor = 0
    filtered_base_models = []
    if provider == 'vibeproxy':
        filtered_base_models = [m for m in all_models if m.startswith('vibeproxy/') or m.startswith('antigravity/')]
    elif provider == 'openai':
        filtered_base_models = [m for m in all_models if m.startswith('openai/') or m.startswith('gpt-')]
    elif provider == 'gemini':
        filtered_base_models = [m for m in all_models if m.startswith('google/') or m.startswith('gemini')]
    elif provider == 'ollama':
        filtered_base_models = [m for m in all_models if m.startswith('ollama') or not '/' in m]
    elif provider == 'openrouter':
        filtered_base_models = all_models
    else:
        filtered_base_models = all_models
    if not filtered_base_models and provider:
        filtered_base_models = all_models

    def get_current_models():
        candidates = filtered_base_models
        if search_query:
            return [m for m in candidates if search_query.lower() in m.lower()]
        elif view_mode == 'all':
            return candidates
        elif view_mode == 'recommended-free':
            ranked_free = get_top_free_models(limit=80)
            selected = [m for m in ranked_free if m in candidates]
            if selected:
                return selected
            return model_filter.get_filtered_models(candidates, include_free=True, include_top=True, include_recent=True, max_total=60)
        else:
            return model_filter.get_filtered_models(candidates, include_free=True, include_top=True, include_recent=True, max_total=60)
    models = get_current_models()
    rows, cols = get_terminal_size()
    per_page = rows - 15
    while True:
        draw_model_picker(models, page, per_page, cursor, search_query, slot, view_mode)
        try:
            if ARROW_SUPPORT:
                key = get_key()
                if key == 'UP' or key == 'k':
                    if cursor > 0:
                        cursor -= 1
                        if cursor < page * per_page:
                            page -= 1
                elif key == 'DOWN' or key == 'j':
                    if cursor < len(models) - 1:
                        cursor += 1
                        if cursor >= (page + 1) * per_page:
                            page += 1
                elif key == 'ENTER':
                    return models[cursor]
                elif key == 'q' or key == '\x1b':
                    return None
                elif key == 'a':
                    if view_mode == 'recommended-free':
                        view_mode = 'recommended'
                    elif view_mode == 'recommended':
                        view_mode = 'all'
                    else:
                        view_mode = 'recommended-free'
                    search_query = ''
                    models = get_current_models()
                    page = 0
                    cursor = 0
                elif key == 'h':
                    show_selection_history(limit=20)
                    models = get_current_models()
                    page = 0
                    cursor = 0
                elif key == '/':
                    search_query = input('Search: ').strip()
                    models = get_current_models()
                    page = 0
                    cursor = 0
            else:
                current_input = input('→ ').strip()
                cmd = current_input
                if not cmd:
                    continue
                if cmd.lower() == 'q':
                    return None
                elif cmd.lower() == 'n':
                    total_pages = (len(models) + per_page - 1) // per_page
                    if page < total_pages - 1:
                        page += 1
                elif cmd.lower() == 'p':
                    if page > 0:
                        page -= 1
                elif cmd.lower() == 'a':
                    if view_mode == 'recommended-free':
                        view_mode = 'recommended'
                    elif view_mode == 'recommended':
                        view_mode = 'all'
                    else:
                        view_mode = 'recommended-free'
                    search_query = ''
                    models = get_current_models()
                    page = 0
                elif cmd.lower() == 'h':
                    show_selection_history(limit=20)
                    models = get_current_models()
                    page = 0
                elif cmd.startswith('/'):
                    search_query = cmd[1:].strip()
                    models = get_current_models()
                    page = 0
                elif cmd.isdigit():
                    idx = int(cmd) - 1
                    if 0 <= idx < len(models):
                        return models[idx]
                elif cmd.lower().startswith('paste '):
                    return cmd[6:].strip()
        except (EOFError, KeyboardInterrupt):
            return None
```

---

## Feature Function: `draw_model_picker`
**Logic & Purpose:**
```text
Draw the model picker UI with cursor.
```

**Parameters:** `models, page, per_page, cursor, search_query, slot, view_mode`
**Variables Used:** `displayed, total_pages, cursor_marker, model_id, start_idx, total_models, header, selected_for, end_idx, max_display, mode, line_content, current_page, full_line`
**Implementation:**
```python
def draw_model_picker(models: List[str], page: int, per_page: int, cursor: int, search_query: str, slot: str, view_mode: str):
    """Draw the model picker UI with cursor."""
    clear_screen()
    rows, cols = get_terminal_size()
    print('╔' + '═' * (cols - 2) + '╗')
    print('║' + f' SELECT MODEL FOR {slot.upper()} '.center(cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    if view_mode == 'all':
        mode = 'ALL MODELS'
    elif view_mode == 'recommended-free':
        mode = 'RECOMMENDED FREE'
    else:
        mode = 'RECOMMENDED'
    total_models = len(models)
    total_pages = (total_models + per_page - 1) // per_page
    current_page = page + 1
    header = f' {mode} ({total_models} models) - Page {current_page}/{total_pages} '
    if search_query:
        header += f"- Search: '{search_query}' "
    print('║' + header.ljust(cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    print(f"║ {'#':<3}  {'Model':<45} {'CTX':>6} {'OUT':>6}  {'Tags':<15}║")
    print('╠' + '─' * (cols - 2) + '╣')
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_models)
    for i in range(start_idx, end_idx):
        model_id = models[i]
        selected_for = None
        cursor_marker = '→' if i == cursor else ' '
        line_content = format_model_line(i + 1, model_id, None, max_width=cols - 6)
        full_line = f' {cursor_marker} {line_content}'
        print(f'║{pad_visual(full_line, cols - 2)}║')
    displayed = end_idx - start_idx
    max_display = rows - 15
    for _ in range(max_display - displayed):
        print('║' + ' ' * (cols - 2) + '║')
    print('╠' + '═' * (cols - 2) + '╣')
    if ARROW_SUPPORT:
        print('║ CONTROLS:'.ljust(cols - 1) + '║')
        print('║   ↑/↓ or j/k  - Navigate | Enter - Select | / - Search'.ljust(cols - 1) + '║')
        print('║   a - Cycle View | h - History | q/ESC - Cancel'.ljust(cols - 1) + '║')
    else:
        print('║ COMMANDS:'.ljust(cols - 1) + '║')
        print('║   [number] - Select | n/p - Next/Prev | / - Search'.ljust(cols - 1) + '║')
        print('║   a - Cycle View | h - History | q - Cancel'.ljust(cols - 1) + '║')
    print('╚' + '═' * (cols - 2) + '╝')
    print()
```

---

## Feature Function: `run_model_selector_old`
**Logic & Purpose:**
```text
Run the interactive model selector with static UI (old text-based version).
```

**Parameters:** ``
**Variables Used:** `middle_model, per_page, total_pages, page, big_model, small_model, show_all, cmd, selected_model, search_query, slot, all_models, custom_model, models, idx, parts`
**Implementation:**
```python
def run_model_selector_old():
    """Run the interactive model selector with static UI (old text-based version)."""
    from src.core.config import config
    all_models = load_all_models()
    if not all_models:
        print('❌ No models found. Run the scraper first.')
        return
    show_all = False
    search_query = ''
    page = 0
    big_model = config.big_model
    middle_model = config.middle_model
    small_model = config.small_model

    def get_current_models():
        if search_query:
            return [m for m in all_models if search_query.lower() in m.lower()]
        elif show_all:
            return all_models
        else:
            return model_filter.get_filtered_models(all_models, include_free=True, include_top=True, include_recent=True, max_total=60)
    models = get_current_models()
    rows, cols = get_terminal_size()
    per_page = rows - 15
    while True:
        if RICH_AVAILABLE:
            console.clear()
            console.print(draw_ui_rich(models, page, per_page, search_query, big_model, middle_model, small_model, show_all))
        else:
            draw_ui(models, page, per_page, search_query, big_model, middle_model, small_model, show_all) or (clear_screen() and print('Fallback UI...'))
        try:
            cmd = input('→ ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n❌ Cancelled')
            return
        if not cmd:
            continue
        if cmd.lower() == 'q':
            print(f'\n✅ Models selected:')
            print(f'   BIG_MODEL={big_model}')
            print(f'   MIDDLE_MODEL={middle_model}')
            print(f'   SMALL_MODEL={small_model}')
            print('\nUpdate your .env file with these values.')
            return
        elif cmd.lower() == 'n':
            total_pages = (len(models) + per_page - 1) // per_page
            if page < total_pages - 1:
                page += 1
        elif cmd.lower() == 'p':
            if page > 0:
                page -= 1
        elif cmd.lower() == 'a':
            show_all = not show_all
            search_query = ''
            models = get_current_models()
            page = 0
        elif cmd.startswith('/'):
            search_query = cmd[1:].strip()
            models = get_current_models()
            page = 0
        elif cmd.lower().startswith('paste '):
            custom_model = cmd[6:].strip()
            if custom_model:
                slot = input(f"Assign '{custom_model}' to [b/m/s]: ").strip().lower()
                if slot == 'b':
                    big_model = custom_model
                elif slot == 'm':
                    middle_model = custom_model
                elif slot == 's':
                    small_model = custom_model
        else:
            parts = cmd.split()
            if len(parts) == 2 and parts[0].isdigit() and (parts[1].lower() in ['b', 'm', 's']):
                idx = int(parts[0]) - 1
                slot = parts[1].lower()
                if 0 <= idx < len(models):
                    selected_model = models[idx]
                    if slot == 'b':
                        big_model = selected_model
                    elif slot == 'm':
                        middle_model = selected_model
                    elif slot == 's':
                        small_model = selected_model
                else:
                    print(f'❌ Invalid model number: {parts[0]}')
                    input('Press Enter to continue...')
            else:
                print(f'❌ Unknown command: {cmd}')
                input('Press Enter to continue...')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/statusline_tui.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/statusline_tui.py`

**Module Overview**: 
```text
Statusline Builder TUI — visual configurator for Claude Code's status line.

Launch:
    python -m src.cli.statusline_tui
    proxies statusline

Features:
    - Toggle segments (proxy metrics, system, CC stdin-JSON fields)
    - Assign each enabled segment to line 1 or 2, left or right alignment
    - Reorder within alignment group (j/k)
    - Live preview renders using actual segment functions + mock CC JSON
    - Save writes ~/.claude/statusline-config.json + patches settings.json
      to wire up the universal renderer.

Keybindings:
    ↑ / ↓       Navigate
    space       Toggle selected segment on/off
    l / r       Switch selected segment to left / right alignment
    1 / 2       Assign selected segment to line 1 / line 2
    j / k       Move segment down / up within its group
    p           Refresh preview
    s           Save config
    q           Quit (prompts if unsaved)
```

## Global Presets & Variables
- `SCRIPT_DIR` = `Path(__file__).resolve().parent.parent.parent / 'scripts'`
- `SEGMENTS_SH` = `SCRIPT_DIR / 'statusline_segments.sh'`
- `RENDER_SH` = `SCRIPT_DIR / 'statusline_render.sh'`
- `CONFIG_PATH` = `Path.home() / '.claude' / 'statusline-config.json'`
- `CC_SETTINGS` = `Path.home() / '.claude' / 'settings.json'`
- `MOCK_CC_JSON` = `{'model': {'display_name': 'Opus 4.6', 'id': 'claude-opus-4-6'}, 'workspace': {'current_dir': str(Path.cwd())}, 'cost': {'total_cost_usd': 0.042}, 'transcript_path': '', 'session_id': 'demo'}`
- `DEFAULT_CONFIG` = `{'separator': '│', 'sep_padding': 2, 'lines': [{'left': [{'id': 'model'}, {'id': 'cwd'}, {'id': 'git_branch'}], 'right': [{'id': 'clock'}]}, {'left': [{'id': 'proxy_health'}, {'id': 'headroom_health'}, {'id': 'routing_mode'}], 'right': [{'id': 'session_tokens'}, {'id': 'tool_stats'}, {'id': 'headroom_savings'}]}]}`

## Dependencies & Imports
__future__.annotations, json, os, shutil, subprocess, dataclasses.dataclass, dataclasses.field, dataclasses.asdict, pathlib.Path, typing.List, typing.Optional, textual.on, textual.app.App, textual.app.ComposeResult, textual.binding.Binding, textual.containers.Horizontal, textual.containers.Vertical, textual.containers.VerticalScroll, textual.screen.ModalScreen, textual.widgets.Button, textual.widgets.DataTable, textual.widgets.Footer, textual.widgets.Header, textual.widgets.Label, textual.widgets.Static, rich.text.Text

## Feature Class: `Segment`
---

## Feature Function: `load_segment_catalog`
**Logic & Purpose:**
```text
Call `statusline_segments.sh list` to get the full list of available segments.
```

**Parameters:** ``
**Variables Used:** `segs, parts, result`
**Implementation:**
```python
def load_segment_catalog() -> List[Segment]:
    """Call `statusline_segments.sh list` to get the full list of available segments."""
    try:
        result = subprocess.run(['bash', str(SEGMENTS_SH), 'list'], capture_output=True, text=True, timeout=5)
        segs = []
        for line in result.stdout.strip().splitlines():
            parts = line.split('|')
            if len(parts) >= 4:
                segs.append(Segment(id=parts[0], label=parts[1], category=parts[2], sample=parts[3]))
        return segs
    except Exception:
        return []
```

---

## Feature Function: `load_config`
**Logic & Purpose:**
```text
Merge saved config with the catalog, marking enabled/line/align/order.
```

**Parameters:** `catalog`
**Variables Used:** `cfg, sid, s, remaining, by_id`
**Implementation:**
```python
def load_config(catalog: List[Segment]) -> List[Segment]:
    """Merge saved config with the catalog, marking enabled/line/align/order."""
    cfg = DEFAULT_CONFIG
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    by_id = {s.id: s for s in catalog}
    for s in catalog:
        s.enabled = False
        s.line = 1
        s.align = 'left'
    ordered: List[Segment] = []
    for line_idx, line in enumerate(cfg.get('lines', []), start=1):
        for align in ('left', 'right'):
            for seg in line.get(align, []):
                sid = seg.get('id')
                if sid in by_id:
                    s = by_id[sid]
                    s.enabled = True
                    s.line = line_idx
                    s.align = align
                    ordered.append(s)
    remaining = [s for s in catalog if s not in ordered]
    return ordered + remaining
```

---

## Feature Function: `save_config`
**Logic & Purpose:**
```text
Persist enabled segments to JSON config, preserving order.
```

**Parameters:** `segments`
**Variables Used:** `cfg`
**Implementation:**
```python
def save_config(segments: List[Segment]) -> None:
    """Persist enabled segments to JSON config, preserving order."""
    lines: dict = {1: {'left': [], 'right': []}, 2: {'left': [], 'right': []}}
    for s in segments:
        if not s.enabled:
            continue
        lines.setdefault(s.line, {'left': [], 'right': []})
        lines[s.line][s.align].append({'id': s.id})
    cfg = {'separator': '│', 'sep_padding': 2, 'lines': [lines[i] for i in sorted(lines.keys())]}
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
```

---

## Feature Function: `patch_cc_settings`
**Logic & Purpose:**
```text
Update ~/.claude/settings.json so statusLine.command points to our renderer.
```

**Parameters:** ``
**Variables Used:** `backup, cmd, settings`
**Implementation:**
```python
def patch_cc_settings() -> bool:
    """Update ~/.claude/settings.json so statusLine.command points to our renderer."""
    if not CC_SETTINGS.exists():
        return False
    try:
        settings = json.loads(CC_SETTINGS.read_text())
    except Exception:
        return False
    cmd = f'bash {RENDER_SH}'
    settings.setdefault('statusLine', {})
    if settings['statusLine'].get('command') == cmd:
        return True
    backup = CC_SETTINGS.with_suffix('.json.bak')
    shutil.copy2(CC_SETTINGS, backup)
    settings['statusLine'] = {'type': 'command', 'command': cmd, 'padding': settings['statusLine'].get('padding', 2)}
    CC_SETTINGS.write_text(json.dumps(settings, indent=2))
    return True
```

---

## Feature Function: `render_preview`
**Logic & Purpose:**
```text
Serialize current segments to a tmp config, invoke statusline_render.sh with
mock stdin JSON, and return the output (ANSI codes intact) for display.
```

**Parameters:** `segments, term_width`
**Variables Used:** `env, cfg, tf_path, proc`
**Implementation:**
```python
def render_preview(segments: List[Segment], term_width: int=120) -> str:
    """
    Serialize current segments to a tmp config, invoke statusline_render.sh with
    mock stdin JSON, and return the output (ANSI codes intact) for display.
    """
    lines: dict = {1: {'left': [], 'right': []}, 2: {'left': [], 'right': []}}
    for s in segments:
        if not s.enabled:
            continue
        lines.setdefault(s.line, {'left': [], 'right': []})
        lines[s.line][s.align].append({'id': s.id})
    cfg = {'separator': '│', 'sep_padding': 2, 'lines': [lines[i] for i in sorted(lines.keys())]}
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        json.dump(cfg, tf)
        tf_path = tf.name
    try:
        env = {**os.environ, 'STATUSLINE_CONFIG': tf_path, 'COLUMNS': str(term_width)}
        proc = subprocess.run(['bash', str(RENDER_SH)], input=json.dumps(MOCK_CC_JSON), capture_output=True, text=True, timeout=5, env=env)
        return proc.stdout
    except Exception as e:
        return f'(preview error: {e})'
    finally:
        os.unlink(tf_path)
```

---

## Feature Class: `SaveScreen`
**Description:**
```text
Confirmation screen for saving.
```

### Method: `compose`
**Parameters:** `self`
**Implementation:**
```python
def compose(self) -> ComposeResult:
    with Vertical(id='save-dialog'):
        yield Label('Save statusline config?', id='save-label')
        yield Label(f'Target: {CONFIG_PATH}', id='save-target')
        yield Label(f'Will also patch {CC_SETTINGS} to point at the renderer.', id='save-patch')
        with Horizontal():
            yield Button('Save', variant='primary', id='save-yes')
            yield Button('Cancel', id='save-no')
```

### Method: `_save`
**Parameters:** `self`
**Implementation:**
```python
@on(Button.Pressed, '#save-yes')
def _save(self) -> None:
    self.dismiss(True)
```

### Method: `_cancel`
**Parameters:** `self`
**Implementation:**
```python
@on(Button.Pressed, '#save-no')
def _cancel(self) -> None:
    self.dismiss(False)
```

---

## Feature Class: `StatuslineTUI`
### Method: `__init__`
**Parameters:** `self`
**Variables Used:** `catalog`
**Implementation:**
```python
def __init__(self) -> None:
    super().__init__()
    catalog = load_segment_catalog()
    self.segments: List[Segment] = load_config(catalog)
```

### Method: `compose`
**Parameters:** `self`
**Implementation:**
```python
def compose(self) -> ComposeResult:
    yield Header()
    with Horizontal(id='main'):
        with Vertical(id='seg-panel'):
            yield Label('Segments (space=toggle, l/r=align, 1/2=line, j/k=reorder)')
            yield DataTable(id='seg-table', cursor_type='row')
        with Vertical(id='info-panel'):
            yield Label('Segment Info')
            yield Static('', id='seg-info')
            yield Label('Help', id='help-title')
            yield Static("[b]space[/b] toggle  [b]l/r[/b] align  [b]1/2[/b] line\n[b]j/k[/b] reorder within group\n[b]p[/b] refresh preview  [b]s[/b] save  [b]q[/b] quit\n\nRight-aligned segments anchor to the terminal\nedge so long model names or folder paths\ndon't push them around.", id='help-text')
    yield Label('📺 Live Preview', id='preview-title')
    yield Static('', id='preview-box')
    yield Footer()
```

### Method: `on_mount`
**Parameters:** `self`
**Variables Used:** `table`
**Implementation:**
```python
def on_mount(self) -> None:
    table = self.query_one('#seg-table', DataTable)
    table.add_columns('✓', 'ID', 'Category', 'Line', 'Align', 'Sample')
    self._refresh_table()
    self._refresh_preview()
```

### Method: `_refresh_table`
**Parameters:** `self`
**Variables Used:** `cursor, line, table, align, check`
**Implementation:**
```python
def _refresh_table(self) -> None:
    table = self.query_one('#seg-table', DataTable)
    cursor = table.cursor_row if table.row_count > 0 else 0
    table.clear()
    for i, s in enumerate(self.segments):
        check = '●' if s.enabled else '○'
        line = str(s.line) if s.enabled else '-'
        align = s.align if s.enabled else '-'
        table.add_row(check, s.id, s.category, line, align, s.sample)
    if table.row_count > 0:
        table.move_cursor(row=min(cursor, table.row_count - 1))
```

### Method: `_current_segment`
**Parameters:** `self`
**Variables Used:** `table`
**Implementation:**
```python
def _current_segment(self) -> Optional[Segment]:
    table = self.query_one('#seg-table', DataTable)
    if table.row_count == 0:
        return None
    return self.segments[table.cursor_row]
```

### Method: `_refresh_preview`
**Parameters:** `self`
**Variables Used:** `preview, raw, term_w`
**Implementation:**
```python
def _refresh_preview(self) -> None:
    term_w = max(80, self.size.width - 4)
    raw = render_preview(self.segments, term_width=term_w)
    preview = self.query_one('#preview-box', Static)
    try:
        preview.update(Text.from_ansi(raw))
    except Exception:
        preview.update(raw)
```

### Method: `_refresh_info`
**Parameters:** `self`
**Variables Used:** `info, s`
**Implementation:**
```python
def _refresh_info(self) -> None:
    s = self._current_segment()
    if not s:
        return
    info = f"[b]{s.id}[/b] — {s.label}\nCategory: {s.category}\nEnabled: {('yes' if s.enabled else 'no')}\nPosition: line {s.line}, {s.align}-aligned\nSample:   {s.sample}"
    self.query_one('#seg-info', Static).update(info)
```

### Method: `on_data_table_row_highlighted`
**Parameters:** `self, _`
**Implementation:**
```python
def on_data_table_row_highlighted(self, _: DataTable.RowHighlighted) -> None:
    self._refresh_info()
```

### Method: `action_toggle`
**Parameters:** `self`
**Variables Used:** `s`
**Implementation:**
```python
def action_toggle(self) -> None:
    s = self._current_segment()
    if s:
        s.enabled = not s.enabled
        self._refresh_table()
        self._refresh_preview()
        self._refresh_info()
```

### Method: `action_align_left`
**Parameters:** `self`
**Variables Used:** `s`
**Implementation:**
```python
def action_align_left(self) -> None:
    s = self._current_segment()
    if s and s.enabled:
        s.align = 'left'
        self._refresh_table()
        self._refresh_preview()
```

### Method: `action_align_right`
**Parameters:** `self`
**Variables Used:** `s`
**Implementation:**
```python
def action_align_right(self) -> None:
    s = self._current_segment()
    if s and s.enabled:
        s.align = 'right'
        self._refresh_table()
        self._refresh_preview()
```

### Method: `action_set_line_1`
**Parameters:** `self`
**Variables Used:** `s`
**Implementation:**
```python
def action_set_line_1(self) -> None:
    s = self._current_segment()
    if s and s.enabled:
        s.line = 1
        self._refresh_table()
        self._refresh_preview()
```

### Method: `action_set_line_2`
**Parameters:** `self`
**Variables Used:** `s`
**Implementation:**
```python
def action_set_line_2(self) -> None:
    s = self._current_segment()
    if s and s.enabled:
        s.line = 2
        self._refresh_table()
        self._refresh_preview()
```

### Method: `action_move_up`
**Parameters:** `self`
**Variables Used:** `table, i`
**Implementation:**
```python
def action_move_up(self) -> None:
    table = self.query_one('#seg-table', DataTable)
    i = table.cursor_row
    if i <= 0:
        return
    self.segments[i], self.segments[i - 1] = (self.segments[i - 1], self.segments[i])
    self._refresh_table()
    table.move_cursor(row=i - 1)
    self._refresh_preview()
```

### Method: `action_move_down`
**Parameters:** `self`
**Variables Used:** `table, i`
**Implementation:**
```python
def action_move_down(self) -> None:
    table = self.query_one('#seg-table', DataTable)
    i = table.cursor_row
    if i >= len(self.segments) - 1:
        return
    self.segments[i], self.segments[i + 1] = (self.segments[i + 1], self.segments[i])
    self._refresh_table()
    table.move_cursor(row=i + 1)
    self._refresh_preview()
```

### Method: `action_refresh_preview`
**Parameters:** `self`
**Implementation:**
```python
def action_refresh_preview(self) -> None:
    self._refresh_preview()
```

### Method: `action_save`
**Parameters:** `self`
**Variables Used:** `patched, msg`
**Implementation:**
```python
def action_save(self) -> None:

    def _after(confirmed: bool) -> None:
        if confirmed:
            save_config(self.segments)
            patched = patch_cc_settings()
            msg = f'Saved {CONFIG_PATH}'
            if patched:
                msg += f' + patched {CC_SETTINGS}'
            self.notify(msg, severity='information')
    self.push_screen(SaveScreen(), _after)
```

---

## Feature Function: `main`
**Parameters:** ``
**Implementation:**
```python
def main() -> None:
    StatuslineTUI().run()
```

---


