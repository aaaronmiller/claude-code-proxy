# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/cost.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/cost.py`

**Module Overview**: 
```text
Cost estimation utilities.
Calculates estimated cost from token usage and model pricing.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
logging, typing.Dict, typing.Any

## Feature Function: `calculate_estimated_cost`
**Logic & Purpose:**
```text
Calculate estimated cost for a run based on token usage and pricing.

Args:
    pricing: Pricing model object OR dict with keys: prompt (per 1M), completion (per 1M), cache_read, cache_write (optional)
    token_usage: Dict with prompt_tokens, completion_tokens, (optional) cache_read_tokens, cache_write_tokens

Returns:
    Estimated cost in USD
```

**Parameters:** `pricing, token_usage`
**Variables Used:** `cache_read_tokens, cache_read_rate, completion_tokens, cost, prompt_rate, completion_rate, cache_write_rate, prompt_tokens, cache_write_tokens`
**Implementation:**
```python
def calculate_estimated_cost(pricing, token_usage: Dict[str, int]) -> float:
    """
    Calculate estimated cost for a run based on token usage and pricing.

    Args:
        pricing: Pricing model object OR dict with keys: prompt (per 1M), completion (per 1M), cache_read, cache_write (optional)
        token_usage: Dict with prompt_tokens, completion_tokens, (optional) cache_read_tokens, cache_write_tokens

    Returns:
        Estimated cost in USD
    """
    if hasattr(pricing, 'prompt'):
        prompt_rate = pricing.prompt
        completion_rate = pricing.completion
        cache_read_rate = getattr(pricing, 'cache_read', 0.0)
        cache_write_rate = getattr(pricing, 'cache_write', 0.0)
    else:
        prompt_rate = pricing.get('prompt', 0.0)
        completion_rate = pricing.get('completion', 0.0)
        cache_read_rate = pricing.get('cache_read', 0.0)
        cache_write_rate = pricing.get('cache_write', 0.0)
    prompt_tokens = token_usage.get('prompt_tokens', 0)
    completion_tokens = token_usage.get('completion_tokens', 0)
    cache_read_tokens = token_usage.get('cache_read_tokens', 0)
    cache_write_tokens = token_usage.get('cache_write_tokens', 0)
    cost = prompt_tokens / 1000000 * prompt_rate + completion_tokens / 1000000 * completion_rate + cache_read_tokens / 1000000 * cache_read_rate + cache_write_tokens / 1000000 * (cache_write_rate or 0.0)
    return round(cost, 6)
```

---


Error parsing /home/cheta/code/claude-code-proxy/model-scraper/.specify/scripts/bash/update-agent-context.sh: closing parenthesis ')' does not match opening parenthesis '{' on line 247 (<unknown>, line 251)

Error parsing /home/cheta/code/claude-code-proxy/model-scraper/.specify/scripts/bash/create-new-feature.sh: closing parenthesis ')' does not match opening parenthesis '[' on line 10 (<unknown>, line 13)

Error parsing /home/cheta/code/claude-code-proxy/model-scraper/.specify/scripts/bash/setup-plan.sh: unmatched ')' (<unknown>, line 11)

Error parsing /home/cheta/code/claude-code-proxy/model-scraper/.specify/scripts/bash/check-prerequisites.sh: unmatched ')' (<unknown>, line 32)

Error parsing /home/cheta/code/claude-code-proxy/model-scraper/.specify/scripts/bash/common.sh: closing parenthesis '}' does not match opening parenthesis '(' on line 42 (<unknown>, line 58)

Error parsing /home/cheta/code/claude-code-proxy/model-scraper/htmlcov/coverage_html_cb_dd2e7eb5.js: unterminated string literal (detected at line 85) (<unknown>, line 85)

# File Audit: /home/cheta/code/claude-code-proxy/config/custom_router.example.py
**Path**: `/home/cheta/code/claude-code-proxy/config/custom_router.example.py`

**Module Overview**: 
```text
Custom Router Example
────────────────────
Drop a copy of this file anywhere and point ROUTER_CUSTOM_PATH at it:

    ROUTER_CUSTOM_PATH=config/my_router.py

The proxy calls route(request, config) before every request.
Return a model string to override the selected model, or None to keep it.

JavaScript variant (.js) is also supported — see custom_router.example.js.
```

## Feature Function: `route`
**Logic & Purpose:**
```text
Args:
    request: The OpenAI-format request body (dict).
             Keys: messages, model, stream, tools, thinking, ...
    config:  Current router config values (dict).
             Keys: default, background, think, long_context, web_search, image.

Returns:
    A model string like "provider/model-name" to use for this request,
    or None to fall through to the built-in routing logic.
```

**Parameters:** `request, config`
**Variables Used:** `messages, last_user`
**Implementation:**
```python
def route(request: dict, config: dict) -> str | None:
    """
    Args:
        request: The OpenAI-format request body (dict).
                 Keys: messages, model, stream, tools, thinking, ...
        config:  Current router config values (dict).
                 Keys: default, background, think, long_context, web_search, image.

    Returns:
        A model string like "provider/model-name" to use for this request,
        or None to fall through to the built-in routing logic.
    """
    messages = request.get('messages', [])
    last_user = next((m.get('content', '') for m in reversed(messages) if m.get('role') == 'user'), '')
    if isinstance(last_user, str):
        if any((kw in last_user.lower() for kw in ('write a function', 'refactor', 'debug'))):
            return 'qwen/qwen3-235b-a22b:free'
    if len(request.get('tools', [])) > 10:
        return 'openai/gpt-oss-120b:free'
    if request.get('thinking', {}).get('type') == 'enabled':
        return config.get('think') or None
    return None
```

---


Error parsing /home/cheta/code/claude-code-proxy/scripts/statusline_segments.sh: unterminated string literal (detected at line 34) (<unknown>, line 34)

Error parsing /home/cheta/code/claude-code-proxy/scripts/tmux_status.sh: unterminated string literal (detected at line 42) (<unknown>, line 42)

Error parsing /home/cheta/code/claude-code-proxy/scripts/statusline_render.sh: unterminated string literal (detected at line 48) (<unknown>, line 48)

Error parsing /home/cheta/code/claude-code-proxy/scripts/api_key_wizard.sh: unmatched ')' (<unknown>, line 50)

# File Audit: /home/cheta/code/claude-code-proxy/scripts/watch_dashboard.py
**Path**: `/home/cheta/code/claude-code-proxy/scripts/watch_dashboard.py`

**Module Overview**: 
```text
Rich-based TUI Dashboard for claude-code-proxy
Displays live tmux pane outputs in a beautifully formatted 3-column layout.
```

## Global Presets & Variables
- `ANSI_ESCAPE` = `re.compile('\\x1B(?:[@-Z\\\\-_]|\\[[0-?]*[ -/]*[@-~])')`

## Dependencies & Imports
sys, time, re, subprocess, rich.live.Live, rich.layout.Layout, rich.panel.Panel, rich.console.Group, rich.text.Text, rich.style.Style, rich.box, rich.spinner.Spinner

## Feature Function: `strip_ansi`
**Parameters:** `text`
**Implementation:**
```python
def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)
```

---

## Feature Function: `capture_tmux_pane`
**Parameters:** `session_name, pane_idx, lines`
**Variables Used:** `target, result`
**Implementation:**
```python
def capture_tmux_pane(session_name: str, pane_idx: int, lines: int=50) -> str:
    target = f'{session_name}:0.{pane_idx}'
    try:
        result = subprocess.run(['tmux', 'capture-pane', '-t', target, '-p', '-S', f'-{lines}'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return strip_ansi(result.stdout)
        else:
            return 'Pane not active or tmux session missing.'
    except Exception as e:
        return f'Error capturing pane: {e}'
```

---

## Feature Function: `generate_pane_content`
**Logic & Purpose:**
```text
Format the text content with semantic styling.
```

**Parameters:** `text, color`
**Variables Used:** `t`
**Implementation:**
```python
def generate_pane_content(text: str, color: str) -> Text:
    """Format the text content with semantic styling."""
    t = Text()
    for line in text.splitlines():
        if not line.strip():
            continue
        if 'error' in line.lower() or 'failed' in line.lower() or 'exception' in line.lower():
            t.append(line + '\n', style='bold red')
        elif 'warn' in line.lower() or '⚠' in line:
            t.append(line + '\n', style='bold yellow')
        elif 'success' in line.lower() or '✓' in line:
            t.append(line + '\n', style='bold green')
        else:
            t.append(line + '\n', style=color)
    return t
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `header_text, layout, api_out, uptime, start_time, has_cli, lines, mode, columns, cp_out, session_name, hr_out, has_claude`
**Implementation:**
```python
def main():
    if len(sys.argv) < 3:
        print('Usage: watch_dashboard.py <session_name> <mode> [lines]')
        sys.exit(1)
    session_name = sys.argv[1]
    mode = sys.argv[2]
    try:
        lines = int(sys.argv[3])
    except IndexError:
        lines = 40
    layout = Layout()
    layout.split_column(Layout(name='header', size=3), Layout(name='body'))
    has_cli = mode == 'full' or mode == 'comp'
    has_claude = mode == 'full' or mode == 'proxy'
    columns = []
    if has_cli:
        columns.append(Layout(name='cli_proxy'))
    if has_claude:
        columns.append(Layout(name='claude_proxy'))
    columns.append(Layout(name='headroom'))
    layout['body'].split_row(*columns)
    start_time = time.time()
    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                uptime = int(time.time() - start_time)
                mins, secs = divmod(uptime, 60)
                header_text = Text(f' Compression Stack Monitor  |  ⏱ Uptime: {mins:02d}:{secs:02d}  |  ⚡ Mode: {mode.upper()}', style='bold white on blue')
                layout['header'].update(Panel(Spinner('point', text=header_text), style='blue', box=box.ROUNDED))
                hr_out = capture_tmux_pane(session_name, 2, lines)
                layout['headroom'].update(Panel(generate_pane_content(hr_out, 'yellow'), title='[bold yellow]Headroom (Optimization Layer)[/]', subtitle=f'[dim]lines: {lines}[/]', border_style='yellow', box=box.ROUNDED))
                if has_claude:
                    cp_out = capture_tmux_pane(session_name, 1, lines)
                    layout['claude_proxy'].update(Panel(generate_pane_content(cp_out, 'cyan'), title='[bold cyan]Claude Proxy (Controller)[/]', subtitle=f'[dim]lines: {lines}[/]', border_style='cyan', box=box.ROUNDED))
                if has_cli:
                    api_out = capture_tmux_pane(session_name, 0, lines)
                    layout['cli_proxy'].update(Panel(generate_pane_content(api_out, 'green'), title='[bold green]CLIProxyAPI (Destination)[/]', subtitle=f'[dim]lines: {lines}[/]', border_style='green', box=box.ROUNDED))
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
```

---


Error parsing /home/cheta/code/claude-code-proxy/scripts/run_router.sh: invalid syntax (<unknown>, line 14)

Error parsing /home/cheta/code/claude-code-proxy/scripts/cc_statusline_metrics.sh: unterminated string literal (detected at line 74) (<unknown>, line 74)

Error parsing /home/cheta/code/claude-code-proxy/tools/spawn_mission.sh: unterminated string literal (detected at line 42) (<unknown>, line 42)

# File Audit: /home/cheta/code/claude-code-proxy/tools/refresh_model_rankings.py
**Path**: `/home/cheta/code/claude-code-proxy/tools/refresh_model_rankings.py`

**Module Overview**: 
```text
Refresh the free-model rankings cache used by the cascade fallback system.

Fetches live model data from OpenRouter, scores each free model on:
  - tool_use support  (required for agentic tasks)
  - context length
  - output length
  - recency (stealth-free models get a recency bonus)

Writes ranked results to data/free_model_rankings.json.
Run this periodically (e.g. every 6 hours via cron) so the cascade
always has an up-to-date list of working free models.

Usage:
  python tools/refresh_model_rankings.py            # incremental (skips if cache fresh)
  python tools/refresh_model_rankings.py --force    # always re-fetch from OpenRouter
  python tools/refresh_model_rankings.py --top 10   # print top N models after refresh
```

## Global Presets & Variables
- `ROOT` = `Path(__file__).parent.parent`

## Dependencies & Imports
argparse, sys, pathlib.Path, src.services.models.free_model_rankings.build_free_model_rankings, src.services.models.free_model_rankings.save_free_model_rankings, src.services.models.free_model_rankings.get_or_build_free_model_rankings, src.services.models.free_model_rankings.RANKINGS_PATH

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `args, tool_capable, parser, rankings`
**Implementation:**
```python
def main():
    parser = argparse.ArgumentParser(description='Refresh OpenRouter free model rankings cache')
    parser.add_argument('--force', action='store_true', help='Force re-fetch even if cache exists')
    parser.add_argument('--top', type=int, default=0, help='Print top N models after refresh')
    args = parser.parse_args()
    print(f'[rankings] Refreshing model rankings (force={args.force})…')
    rankings = get_or_build_free_model_rankings(force_refresh=args.force)
    tool_capable = [r for r in rankings if r.supports_tools]
    print(f'[rankings] Total free models: {len(rankings)} | Tool-capable: {len(tool_capable)}')
    print(f'[rankings] Saved to: {RANKINGS_PATH}')
    if args.top > 0:
        print(f'\nTop {args.top} tool-capable free models:')
        for i, r in enumerate(tool_capable[:args.top], 1):
            print(f'  {i:2}. {r.model_id:<60} score={r.score:.1f}  ctx={r.context_length // 1000}k')
```

---


