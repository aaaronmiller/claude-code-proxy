# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/base_module.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/base_module.py`

**Module Overview**: 
```text
Base module class for dashboard components.
```

## Dependencies & Imports
abc.ABC, abc.abstractmethod, typing.Dict, typing.Any, typing.List, collections.deque, time

## Feature Class: `BaseModule`
**Description:**
```text
Base class for all dashboard modules.
```

### Method: `__init__`
**Parameters:** `self, max_history`
**Implementation:**
```python
def __init__(self, max_history: int=100):
    self.request_history = deque(maxlen=max_history)
    self.last_update = time.time()
```

### Method: `add_request_data`
**Logic & Purpose:**
```text
Add request data to module history.
```

**Parameters:** `self, request_data`
**Implementation:**
```python
def add_request_data(self, request_data: Dict[str, Any]):
    """Add request data to module history."""
    request_data['timestamp'] = time.time()
    self.request_history.append(request_data)
    self.last_update = time.time()
```

### Method: `get_title`
**Logic & Purpose:**
```text
Get module title.
```

**Parameters:** `self`
**Implementation:**
```python
@abstractmethod
def get_title(self) -> str:
    """Get module title."""
    pass
```

### Method: `get_description`
**Logic & Purpose:**
```text
Get module description.
```

**Parameters:** `self`
**Implementation:**
```python
@abstractmethod
def get_description(self) -> str:
    """Get module description."""
    pass
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render module in dense mode.
```

**Parameters:** `self`
**Implementation:**
```python
@abstractmethod
def render_dense(self) -> str:
    """Render module in dense mode."""
    pass
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render module in sparse mode.
```

**Parameters:** `self`
**Implementation:**
```python
@abstractmethod
def render_sparse(self) -> str:
    """Render module in sparse mode."""
    pass
```

### Method: `render`
**Logic & Purpose:**
```text
Render module based on display mode.
```

**Parameters:** `self, mode`
**Implementation:**
```python
def render(self, mode: str='dense') -> str:
    """Render module based on display mode."""
    if mode == 'sparse':
        return self.render_sparse()
    else:
        return self.render_dense()
```

### Method: `render_plain`
**Logic & Purpose:**
```text
Render module without Rich formatting.
```

**Parameters:** `self, mode`
**Variables Used:** `content`
**Implementation:**
```python
def render_plain(self, mode: str='dense') -> str:
    """Render module without Rich formatting."""
    content = self.render(mode)
    if RICH_AVAILABLE:
        import re
        content = re.sub('\\[/?[^\\]]*\\]', '', content)
    return content
```

### Method: `get_recent_requests`
**Logic & Purpose:**
```text
Get most recent requests.
```

**Parameters:** `self, count`
**Implementation:**
```python
def get_recent_requests(self, count: int=10) -> List[Dict[str, Any]]:
    """Get most recent requests."""
    return list(self.request_history)[-count:]
```

### Method: `get_active_requests`
**Logic & Purpose:**
```text
Get requests that are currently active (started but not completed).
```

**Parameters:** `self`
**Variables Used:** `active, completed_ids`
**Implementation:**
```python
def get_active_requests(self) -> List[Dict[str, Any]]:
    """Get requests that are currently active (started but not completed)."""
    active = []
    completed_ids = {req['request_id'] for req in self.request_history if req.get('type') == 'complete'}
    for req in self.request_history:
        if req.get('type') == 'start' and req['request_id'] not in completed_ids:
            active.append(req)
    return active
```

### Method: `get_completed_requests`
**Logic & Purpose:**
```text
Get completed requests within time window.
```

**Parameters:** `self, since_seconds`
**Variables Used:** `cutoff`
**Implementation:**
```python
def get_completed_requests(self, since_seconds: int=3600) -> List[Dict[str, Any]]:
    """Get completed requests within time window."""
    cutoff = time.time() - since_seconds
    return [req for req in self.request_history if req.get('type') == 'complete' and req.get('timestamp', 0) > cutoff]
```

### Method: `format_duration`
**Logic & Purpose:**
```text
Format duration in human readable format.
```

**Parameters:** `self, duration_ms`
**Implementation:**
```python
def format_duration(self, duration_ms: float) -> str:
    """Format duration in human readable format."""
    if duration_ms < 1000:
        return f'{duration_ms:.0f}ms'
    else:
        return f'{duration_ms / 1000:.1f}s'
```

### Method: `format_tokens`
**Logic & Purpose:**
```text
Format token count compactly.
```

**Parameters:** `self, count`
**Implementation:**
```python
def format_tokens(self, count: int) -> str:
    """Format token count compactly."""
    if count >= 1000:
        return f'{count / 1000:.1f}k'
    return str(count)
```

### Method: `format_cost`
**Logic & Purpose:**
```text
Format cost in dollars.
```

**Parameters:** `self, cost`
**Implementation:**
```python
def format_cost(self, cost: float) -> str:
    """Format cost in dollars."""
    if cost < 0.01:
        return f'${cost:.4f}'
    elif cost < 1:
        return f'${cost:.3f}'
    else:
        return f'${cost:.2f}'
```

### Method: `create_progress_bar`
**Logic & Purpose:**
```text
Create ASCII progress bar.
```

**Parameters:** `self, used, total, width`
**Variables Used:** `empty_width, filled_width, percentage`
**Implementation:**
```python
def create_progress_bar(self, used: int, total: int, width: int=10) -> str:
    """Create ASCII progress bar."""
    if total == 0:
        return '░' * width
    percentage = min(used / total, 1.0)
    filled_width = int(width * percentage)
    empty_width = width - filled_width
    return '█' * filled_width + '░' * empty_width
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/request_waterfall.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/request_waterfall.py`

**Module Overview**: 
```text
Request Waterfall Module - Detailed request lifecycle tracking.
```

## Dependencies & Imports
time, base_module.BaseModule, src.dashboard.model_display_utils.format_model_name

## Feature Class: `RequestWaterfall`
**Description:**
```text
Request waterfall visualization module.
```

### Method: `get_title`
**Parameters:** `self`
**Implementation:**
```python
def get_title(self) -> str:
    return 'Request Waterfall'
```

### Method: `get_description`
**Parameters:** `self`
**Implementation:**
```python
def get_description(self) -> str:
    return 'Detailed request lifecycle and timing breakdown'
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render detailed waterfall view.
```

**Parameters:** `self`
**Variables Used:** `output_tokens, processing_time, start_req, recent, text, elapsed, reasoning_config, duration_ms, request_id, input_tokens, recv_text, cost, tok_s, usage, thinking_tokens, routed_model, complete_req, original_model, endpoint_name, endpoint`
**Implementation:**
```python
def render_dense(self) -> str:
    """Render detailed waterfall view."""
    recent = self.get_recent_requests(1)
    if not recent:
        return 'No request data available'
    start_req = None
    complete_req = None
    for req in reversed(recent):
        if req.get('type') == 'start':
            start_req = req
            break
    if start_req:
        for req in reversed(recent):
            if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
                complete_req = req
                break
    if not start_req:
        return 'No request lifecycle data'
    if not RICH_AVAILABLE:
        return self._render_dense_plain(start_req, complete_req)
    text = Text()
    request_id = start_req.get('request_id', 'unknown')[:6]
    text.append(f'🔵 Request {request_id} ', style='bold cyan')
    text.append('─' * 40, style='dim')
    text.append('\n')
    original_model = start_req.get('original_model', 'unknown')
    routed_model = start_req.get('routed_model', 'unknown')
    text.append('├─ 📝 Parse: ', style='dim')
    text.append(f'{self._format_model_name(original_model)} → {self._format_model_name(routed_model)}', style='yellow')
    text.append('        (0.1s)', style='green')
    text.append('\n')
    endpoint = start_req.get('endpoint', 'unknown')
    endpoint_name = endpoint.split('/')[-3] if '/' in endpoint else endpoint
    text.append('├─ 🔄 Route: ', style='dim')
    text.append(f'{endpoint_name} endpoint selection', style='blue')
    text.append('           (0.2s)', style='green')
    text.append('\n')
    reasoning_config = start_req.get('reasoning_config')
    if reasoning_config:
        text.append('├─ 🧠 Think: ', style='dim')
        text.append('Reasoning budget allocated', style='magenta')
        text.append('     (0.1s)', style='green')
        text.append('\n')
    input_tokens = start_req.get('input_tokens', 0)
    text.append('├─ 🚀 Send: ', style='dim')
    text.append(f'{self.format_tokens(input_tokens)} context → API', style='cyan')
    text.append('                        (0.3s)', style='green')
    text.append('\n')
    if complete_req:
        duration_ms = complete_req.get('duration_ms', 0)
        processing_time = max(0, duration_ms - 700)
        text.append('├─ ⏳ Wait: ', style='dim')
        text.append('Model processing...', style='yellow')
        text.append(f'                         ({processing_time / 1000:.1f}s)', style='yellow')
        text.append('\n')
        usage = complete_req.get('usage', {})
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        text.append('├─ 📥 Recv: ', style='dim')
        recv_text = f'{self.format_tokens(output_tokens)} output'
        if thinking_tokens > 0:
            recv_text += f' + {self.format_tokens(thinking_tokens)} thinking tokens'
        text.append(recv_text, style='green')
        text.append('          (0.9s)', style='green')
        text.append('\n')
        cost = self._estimate_cost(usage.get('input_tokens', 0), output_tokens, thinking_tokens, routed_model)
        tok_s = output_tokens / (duration_ms / 1000) if duration_ms > 0 and output_tokens > 0 else 0
        text.append('└─ ✅ Done: ', style='dim')
        text.append(f'Total {self.format_duration(duration_ms)}', style='green')
        text.append(f' | {self.format_cost(cost)}', style='yellow')
        if tok_s > 0:
            text.append(f' | {tok_s:.0f} tok/s', style='cyan')
    else:
        elapsed = time.time() - start_req.get('timestamp', time.time())
        text.append('├─ ⏳ Wait: ', style='dim')
        text.append('Model processing...', style='yellow')
        text.append(f'                         ({elapsed:.1f}s)', style='yellow')
        text.append('\n')
        text.append('└─ ⏸️  Pending...', style='blue')
    return text
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render compact waterfall summary.
```

**Parameters:** `self`
**Variables Used:** `output_tokens, request_id, recent, cost, complete_req, elapsed, duration_ms, usage, start_req`
**Implementation:**
```python
def render_sparse(self) -> str:
    """Render compact waterfall summary."""
    recent = self.get_recent_requests(1)
    if not recent:
        return 'No request data'
    start_req = None
    complete_req = None
    for req in reversed(recent):
        if req.get('type') == 'start':
            start_req = req
            break
    if start_req:
        for req in reversed(recent):
            if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
                complete_req = req
                break
    if not start_req:
        return 'No request data'
    request_id = start_req.get('request_id', 'unknown')[:6]
    if complete_req:
        duration_ms = complete_req.get('duration_ms', 0)
        usage = complete_req.get('usage', {})
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        cost = self._estimate_cost(usage.get('input_tokens', 0), output_tokens, self._extract_thinking_tokens(usage), start_req.get('routed_model', ''))
        return f'🔵{request_id}: Parse→Route→Think→Send→Wait→Recv→Done | {self.format_duration(duration_ms)} | {self.format_cost(cost)}'
    else:
        elapsed = time.time() - start_req.get('timestamp', time.time())
        return f'🔵{request_id}: Parse→Route→Think→Send→Wait... | {elapsed:.1f}s'
```

### Method: `_render_dense_plain`
**Logic & Purpose:**
```text
Plain text version.
```

**Parameters:** `self, start_req, complete_req`
**Variables Used:** `lines, request_id, duration_ms`
**Implementation:**
```python
def _render_dense_plain(self, start_req, complete_req):
    """Plain text version."""
    request_id = start_req.get('request_id', 'unknown')[:8]
    lines = [f'Request {request_id} Lifecycle:']
    lines.append('1. Parse: Model routing')
    lines.append('2. Route: Endpoint selection')
    lines.append('3. Send: Context to API')
    if complete_req:
        duration_ms = complete_req.get('duration_ms', 0)
        lines.append(f'4. Wait: Processing ({duration_ms / 1000:.1f}s)')
        lines.append('5. Recv: Response received')
        lines.append(f'6. Done: Total {self.format_duration(duration_ms)}')
    else:
        lines.append('4. Wait: Processing...')
    return '\n'.join(lines)
```

### Method: `_format_model_name`
**Logic & Purpose:**
```text
Format model name for display using dynamic family detection.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def _format_model_name(self, model_name: str) -> str:
    """Format model name for display using dynamic family detection."""
    return format_model_name(model_name)
```

### Method: `_extract_thinking_tokens`
**Logic & Purpose:**
```text
Extract thinking tokens.
```

**Parameters:** `self, usage`
**Variables Used:** `details`
**Implementation:**
```python
def _extract_thinking_tokens(self, usage):
    """Extract thinking tokens."""
    if 'thinking_tokens' in usage:
        return usage['thinking_tokens']
    elif 'reasoning_tokens' in usage:
        return usage['reasoning_tokens']
    elif 'completion_tokens_details' in usage:
        details = usage['completion_tokens_details']
        if isinstance(details, dict):
            return details.get('reasoning_tokens', 0)
    return 0
```

### Method: `_estimate_cost`
**Logic & Purpose:**
```text
Estimate cost.
```

**Parameters:** `self, input_tokens, output_tokens, thinking_tokens, model_name`
**Implementation:**
```python
def _estimate_cost(self, input_tokens, output_tokens, thinking_tokens, model_name):
    """Estimate cost."""
    if 'gpt-4o' in model_name.lower():
        if 'mini' in model_name.lower():
            return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
        else:
            return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
    elif 'claude' in model_name.lower():
        return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif 'o1' in model_name.lower():
        return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
    return (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/__init__.py`

**Module Overview**: 
```text
Dashboard modules for API monitoring.
```

## Global Presets & Variables
- `__all__` = `['BaseModule', 'PerformanceMonitor', 'ActivityFeed', 'RoutingVisualizer', 'AnalyticsPanel', 'RequestWaterfall']`

## Dependencies & Imports
base_module.BaseModule, performance_monitor.PerformanceMonitor, activity_feed.ActivityFeed, routing_visualizer.RoutingVisualizer, analytics_panel.AnalyticsPanel, request_waterfall.RequestWaterfall


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/metrics_module.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/metrics_module.py`

**Module Overview**: 
```text
Real-time Metrics Module for Terminal Dashboard

Displays live metrics from the session metrics tracker:
- Active sessions
- Token usage per session
- Tool call success rates
- Cache statistics
```

## Dependencies & Imports
datetime.datetime, typing.Dict, typing.Any, typing.List

## Feature Class: `MetricsModule`
**Description:**
```text
Real-time metrics display module.
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='left'):
    self.position = position
    self.data: Dict[str, Any] = {}
    self.visible = True
```

### Method: `update`
**Logic & Purpose:**
```text
Update metrics data.
```

**Parameters:** `self, data`
**Implementation:**
```python
def update(self, data: Dict[str, Any]):
    """Update metrics data."""
    self.data = data
```

### Method: `render`
**Logic & Purpose:**
```text
Render metrics as Rich Panel.
```

**Parameters:** `self`
**Variables Used:** `table, metrics`
**Implementation:**
```python
def render(self) -> Panel:
    """Render metrics as Rich Panel."""
    if not RICH_AVAILABLE or not self.visible:
        return Panel('', title='')
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column('Metric', style='cyan')
    table.add_column('Value', style='white bold')
    metrics = self.data.get('aggregate', {})
    table.add_row('Sessions', str(metrics.get('total_sessions', 0)))
    table.add_row('Requests', str(metrics.get('total_requests', 0)))
    table.add_row('Tokens', self._format_tokens(metrics.get('total_tokens', 0)))
    table.add_row('Cost', f"${metrics.get('total_cost', 0):.4f}")
    table.add_row('Tool Success', f"{metrics.get('tool_success_rate', 0):.1f}%")
    table.add_row('Cache Hit', f"{metrics.get('cache_hit_rate', 0):.1f}%")
    return Panel(table, title='[bold green]📊 Live Metrics[/]', border_style='green', subtitle=f"Updated: {datetime.now().strftime('%H:%M:%S')}")
```

### Method: `_format_tokens`
**Logic & Purpose:**
```text
Format token count.
```

**Parameters:** `self, tokens`
**Implementation:**
```python
def _format_tokens(self, tokens: int) -> str:
    """Format token count."""
    if tokens >= 1000000:
        return f'{tokens / 1000000:.1f}M'
    elif tokens >= 1000:
        return f'{tokens / 1000:.1f}k'
    return str(tokens)
```

---

## Feature Class: `SessionListModule`
**Description:**
```text
Active sessions list module.
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='right'):
    self.position = position
    self.sessions: List[Dict[str, Any]] = []
    self.visible = True
```

### Method: `update`
**Logic & Purpose:**
```text
Update sessions list.
```

**Parameters:** `self, sessions`
**Implementation:**
```python
def update(self, sessions: List[Dict[str, Any]]):
    """Update sessions list."""
    self.sessions = sessions[:10]
```

### Method: `render`
**Logic & Purpose:**
```text
Render sessions as Rich Panel.
```

**Parameters:** `self`
**Variables Used:** `table, session_id`
**Implementation:**
```python
def render(self) -> Panel:
    """Render sessions as Rich Panel."""
    if not RICH_AVAILABLE or not self.visible:
        return Panel('', title='')
    if not self.sessions:
        return Panel('[dim]No active sessions[/]', title='[bold blue]🖥️ Sessions[/]', border_style='blue')
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column('ID', style='dim', width=8)
    table.add_column('Req', justify='right')
    table.add_column('Tokens', justify='right')
    table.add_column('Cost', justify='right')
    for session in self.sessions:
        session_id = session.get('session_id', 'unknown')[:8]
        table.add_row(session_id, str(session.get('requests', 0)), self._format_tokens(session.get('tokens', 0)), f"${session.get('cost', 0):.3f}")
    return Panel(table, title='[bold blue]🖥️ Active Sessions[/]', border_style='blue', subtitle=f'{len(self.sessions)} sessions')
```

### Method: `_format_tokens`
**Logic & Purpose:**
```text
Format token count.
```

**Parameters:** `self, tokens`
**Implementation:**
```python
def _format_tokens(self, tokens: int) -> str:
    """Format token count."""
    if tokens >= 1000000:
        return f'{tokens / 1000000:.1f}M'
    elif tokens >= 1000:
        return f'{tokens / 1000:.1f}k'
    return str(tokens)
```

---

## Feature Class: `CLIToolsModule`
**Description:**
```text
CLI tools status module.
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='bottom'):
    self.position = position
    self.tools_data: Dict[str, Any] = {}
    self.visible = True
```

### Method: `update`
**Logic & Purpose:**
```text
Update CLI tools data.
```

**Parameters:** `self, tools_data`
**Implementation:**
```python
def update(self, tools_data: Dict[str, Any]):
    """Update CLI tools data."""
    self.tools_data = tools_data
```

### Method: `render`
**Logic & Purpose:**
```text
Render CLI tools status.
```

**Parameters:** `self`
**Variables Used:** `total_sessions, total_tools, text, summary`
**Implementation:**
```python
def render(self) -> Panel:
    """Render CLI tools status."""
    if not RICH_AVAILABLE or not self.visible:
        return Panel('', title='')
    summary = self.tools_data.get('summary', {})
    total_tools = summary.get('total_tools', 0)
    total_sessions = summary.get('total_sessions', 0)
    text = Text()
    text.append(f'📦 CLI Tools: ', style='bold')
    text.append(f'{total_tools} active\n', style='green')
    text.append(f'📝 Sessions: ', style='bold')
    text.append(f'{total_sessions} total\n', style='cyan')
    text.append(f'📄 Config Files: ', style='bold')
    text.append(f"{summary.get('total_config_files', 0)} found", style='yellow')
    return Panel(text, title='[bold magenta]🛠️ CLI Tools[/]', border_style='magenta')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/performance_monitor.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/performance_monitor.py`

**Module Overview**: 
```text
Performance Monitor Module - Real-time request performance tracking.
```

## Dependencies & Imports
time, typing.Dict, typing.Any, typing.Optional, base_module.BaseModule, src.dashboard.model_display_utils.format_model_name

## Feature Class: `PerformanceMonitor`
**Description:**
```text
Real-time performance monitoring module.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    super().__init__(max_history=50)
    self.current_request: Optional[Dict[str, Any]] = None
```

### Method: `get_title`
**Parameters:** `self`
**Implementation:**
```python
def get_title(self) -> str:
    return 'Performance Monitor'
```

### Method: `get_description`
**Parameters:** `self`
**Implementation:**
```python
def get_description(self) -> str:
    return 'Real-time request performance tracking with context and thinking token usage'
```

### Method: `add_request_data`
**Logic & Purpose:**
```text
Override to track current request.
```

**Parameters:** `self, request_data`
**Implementation:**
```python
def add_request_data(self, request_data: Dict[str, Any]):
    """Override to track current request."""
    super().add_request_data(request_data)
    if request_data.get('type') == 'start':
        self.current_request = request_data
    elif request_data.get('type') in ['complete', 'error']:
        if self.current_request and self.current_request.get('request_id') == request_data.get('request_id'):
            self.current_request = None
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render detailed performance view.
```

**Parameters:** `self`
**Variables Used:** `model_name, output_tokens, message_count, has_system, think_bar, recent_requests, start_req, latest_complete, text, duration_ms, context_limit, ctx_pct, request_id, input_tokens, cost, tok_s, usage, ctx_bar, out_bar, thinking_tokens, routed_model, output_limit, original_model`
**Implementation:**
```python
def render_dense(self) -> str:
    """Render detailed performance view."""
    if not RICH_AVAILABLE:
        return self._render_dense_plain()
    recent_requests = self.get_recent_requests(5)
    latest_complete = None
    for req in reversed(recent_requests):
        if req.get('type') == 'complete':
            latest_complete = req
            break
    if not latest_complete:
        return Text('No completed requests yet...', style='dim')
    request_id = latest_complete.get('request_id', 'unknown')[:6]
    usage = latest_complete.get('usage', {})
    duration_ms = latest_complete.get('duration_ms', 0)
    model_name = latest_complete.get('model_name', 'unknown')
    start_req = None
    for req in recent_requests:
        if req.get('type') == 'start' and req.get('request_id') == latest_complete.get('request_id'):
            start_req = req
            break
    text = Text()
    text.append(f'🔵 Session {request_id}', style='bold cyan')
    if start_req:
        original_model = start_req.get('original_model', 'unknown')
        routed_model = start_req.get('routed_model', 'unknown')
        text.append(f' | {self._format_model_name(original_model)}→{self._format_model_name(routed_model)}', style='yellow')
    text.append('\n')
    text.append(f'⚡ {self.format_duration(duration_ms)}', style='green')
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
    thinking_tokens = self._extract_thinking_tokens(usage)
    if start_req:
        context_limit = start_req.get('context_limit', 0)
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = input_tokens / context_limit * 100
            ctx_bar = self.create_progress_bar(input_tokens, context_limit, 10)
            text.append(f' | 📊 CTX: {ctx_bar} {self.format_tokens(input_tokens)}/{self.format_tokens(context_limit)} ({ctx_pct:.0f}%)', style='cyan')
    if output_tokens > 0 and duration_ms > 0:
        tok_s = output_tokens / (duration_ms / 1000)
        text.append(f' | {tok_s:.0f} tok/s', style='bright_green')
    text.append('\n')
    if thinking_tokens > 0:
        text.append(f'🧠 THINK: ', style='magenta')
        if start_req and start_req.get('output_limit', 0) > 0:
            think_bar = self.create_progress_bar(thinking_tokens, start_req['output_limit'], 10)
            text.append(f'{think_bar} {self.format_tokens(thinking_tokens)} tokens', style='bright_magenta')
        else:
            text.append(f'{self.format_tokens(thinking_tokens)} tokens', style='bright_magenta')
    cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
    text.append(f' | 💰 {self.format_cost(cost)} estimated', style='yellow')
    text.append('\n')
    if start_req:
        output_limit = start_req.get('output_limit', 0)
        if output_limit > 0:
            out_bar = self.create_progress_bar(output_tokens, output_limit, 10)
            text.append(f'📤 OUT: {out_bar} {self.format_tokens(output_tokens)}/{self.format_tokens(output_limit)}', style='blue')
        if start_req.get('stream'):
            text.append(' | 🌊 STREAMING', style='bright_blue')
        message_count = start_req.get('message_count', 0)
        has_system = start_req.get('has_system', False)
        if message_count > 0:
            text.append(f' | {message_count}msg', style='dim')
        if has_system:
            text.append(' + SYS', style='green')
    return text
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render compact performance view.
```

**Parameters:** `self`
**Variables Used:** `model_name, output_tokens, request_id, input_tokens, cost, tok_s, duration_ms, req, usage, context_limit, recent_requests, ctx_pct, thinking_tokens, parts`
**Implementation:**
```python
def render_sparse(self) -> str:
    """Render compact performance view."""
    recent_requests = self.get_recent_requests(1)
    if not recent_requests or recent_requests[-1].get('type') != 'complete':
        return '🔵 ... | waiting for requests'
    req = recent_requests[-1]
    request_id = req.get('request_id', 'unknown')[:6]
    usage = req.get('usage', {})
    duration_ms = req.get('duration_ms', 0)
    model_name = req.get('model_name', 'unknown')
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
    thinking_tokens = self._extract_thinking_tokens(usage)
    ctx_pct = 0
    for start_req in reversed(self.request_history):
        if start_req.get('type') == 'start' and start_req.get('request_id') == req.get('request_id'):
            context_limit = start_req.get('context_limit', 0)
            if context_limit > 0:
                ctx_pct = input_tokens / context_limit * 100
            break
    tok_s = 0
    if output_tokens > 0 and duration_ms > 0:
        tok_s = output_tokens / (duration_ms / 1000)
    cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
    parts = [f'🔵 {request_id}', f'⚡{self.format_duration(duration_ms)}', f'📊{ctx_pct:.0f}%' if ctx_pct > 0 else f'📊{self.format_tokens(input_tokens)}', f'🧠{self.format_tokens(thinking_tokens)}' if thinking_tokens > 0 else '', f'💰{self.format_cost(cost)}', f'{tok_s:.0f}t/s' if tok_s > 0 else '']
    return ' | '.join([p for p in parts if p])
```

### Method: `_render_dense_plain`
**Logic & Purpose:**
```text
Plain text version of dense rendering.
```

**Parameters:** `self`
**Variables Used:** `request_id, duration_ms, req, lines, usage, recent_requests, thinking_tokens`
**Implementation:**
```python
def _render_dense_plain(self) -> str:
    """Plain text version of dense rendering."""
    recent_requests = self.get_recent_requests(1)
    if not recent_requests or recent_requests[-1].get('type') != 'complete':
        return 'No completed requests yet...'
    req = recent_requests[-1]
    request_id = req.get('request_id', 'unknown')[:6]
    duration_ms = req.get('duration_ms', 0)
    usage = req.get('usage', {})
    lines = [f'Session {request_id}', f'Duration: {self.format_duration(duration_ms)}', f"Input tokens: {self.format_tokens(usage.get('input_tokens', 0))}", f"Output tokens: {self.format_tokens(usage.get('output_tokens', 0))}"]
    thinking_tokens = self._extract_thinking_tokens(usage)
    if thinking_tokens > 0:
        lines.append(f'Thinking tokens: {self.format_tokens(thinking_tokens)}')
    return '\n'.join(lines)
```

### Method: `_format_model_name`
**Logic & Purpose:**
```text
Format model name for display using dynamic family detection.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def _format_model_name(self, model_name: str) -> str:
    """Format model name for display using dynamic family detection."""
    return format_model_name(model_name)
```

### Method: `_extract_thinking_tokens`
**Logic & Purpose:**
```text
Extract thinking tokens from usage data.
```

**Parameters:** `self, usage`
**Variables Used:** `details`
**Implementation:**
```python
def _extract_thinking_tokens(self, usage: Dict[str, Any]) -> int:
    """Extract thinking tokens from usage data."""
    if 'thinking_tokens' in usage:
        return usage['thinking_tokens']
    elif 'reasoning_tokens' in usage:
        return usage['reasoning_tokens']
    elif 'completion_tokens_details' in usage:
        details = usage['completion_tokens_details']
        if isinstance(details, dict):
            return details.get('reasoning_tokens', 0)
    return 0
```

### Method: `_estimate_cost`
**Logic & Purpose:**
```text
Rough cost estimation.
```

**Parameters:** `self, input_tokens, output_tokens, thinking_tokens, model_name`
**Implementation:**
```python
def _estimate_cost(self, input_tokens: int, output_tokens: int, thinking_tokens: int, model_name: str) -> float:
    """Rough cost estimation."""
    if 'gpt-4o' in model_name.lower():
        if 'mini' in model_name.lower():
            return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
        else:
            return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
    elif 'claude' in model_name.lower():
        return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif 'o1' in model_name.lower():
        return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
    return (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/analytics_panel.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/analytics_panel.py`

**Module Overview**: 
```text
Analytics Panel Module - Cost and performance analytics.
```

## Dependencies & Imports
time, collections.defaultdict, base_module.BaseModule, src.dashboard.model_display_utils.format_model_name

## Feature Class: `AnalyticsPanel`
**Description:**
```text
Cost and performance analytics module.
```

### Method: `get_title`
**Parameters:** `self`
**Implementation:**
```python
def get_title(self) -> str:
    return 'Analytics'
```

### Method: `get_description`
**Parameters:** `self`
**Implementation:**
```python
def get_description(self) -> str:
    return 'Cost and performance analytics with usage statistics'
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render detailed analytics.
```

**Parameters:** `self`
**Variables Used:** `model_name, output_tokens, slowest_duration, total_cost, input_tokens, durations, completed_requests, total_thinking_tokens, text, duration_ms, usage, thinking_tokens, model_usage, success_rate, hot_model, fastest_duration, avg_duration, total_requests`
**Implementation:**
```python
def render_dense(self) -> str:
    """Render detailed analytics."""
    completed_requests = self.get_completed_requests(3600)
    if not completed_requests:
        return 'No analytics data available'
    total_requests = len(completed_requests)
    total_cost = 0
    total_thinking_tokens = 0
    durations = []
    model_usage = defaultdict(int)
    for req in completed_requests:
        usage = req.get('usage', {})
        duration_ms = req.get('duration_ms', 0)
        model_name = req.get('model_name', 'unknown')
        input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        total_cost += self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
        total_thinking_tokens += thinking_tokens
        if duration_ms > 0:
            durations.append(duration_ms)
        model_usage[self._format_model_name(model_name)] += 1
    avg_duration = sum(durations) / len(durations) if durations else 0
    success_rate = total_requests / max(total_requests, 1) * 100
    fastest_duration = min(durations) if durations else 0
    slowest_duration = max(durations) if durations else 0
    hot_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else 'none'
    if not RICH_AVAILABLE:
        return self._render_dense_plain(total_requests, avg_duration, success_rate, total_cost, total_thinking_tokens, hot_model)
    text = Text()
    text.append(f'Total Requests: {total_requests}', style='cyan')
    text.append(f' | Avg Response: {self.format_duration(avg_duration)}', style='green')
    text.append(f' | Success: {success_rate:.1f}%', style='green' if success_rate > 90 else 'yellow')
    text.append('\n')
    text.append(f'💰 Total Cost: {self.format_cost(total_cost)}', style='yellow')
    text.append(f' | 🧠 Thinking Tokens: {self.format_tokens(total_thinking_tokens)}', style='magenta')
    text.append('\n')
    if durations:
        text.append(f'🏆 Fastest: {self.format_duration(fastest_duration)}', style='green')
        text.append(f' | 🐌 Slowest: {self.format_duration(slowest_duration)}', style='red')
    text.append('\n')
    text.append(f'🔥 Hot Model: {hot_model}', style='bright_yellow')
    return text
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render compact analytics.
```

**Parameters:** `self`
**Variables Used:** `model_name, output_tokens, total_cost, input_tokens, durations, completed_requests, total_thinking_tokens, duration_ms, usage, model_usage, success_rate, hot_model, thinking_tokens, avg_duration, total_requests`
**Implementation:**
```python
def render_sparse(self) -> str:
    """Render compact analytics."""
    completed_requests = self.get_completed_requests(3600)
    if not completed_requests:
        return 'No data'
    total_requests = len(completed_requests)
    total_cost = 0
    total_thinking_tokens = 0
    durations = []
    for req in completed_requests:
        usage = req.get('usage', {})
        duration_ms = req.get('duration_ms', 0)
        model_name = req.get('model_name', 'unknown')
        input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        total_cost += self._estimate_cost(input_tokens, output_tokens, thinking_tokens, model_name)
        total_thinking_tokens += thinking_tokens
        if duration_ms > 0:
            durations.append(duration_ms)
    avg_duration = sum(durations) / len(durations) if durations else 0
    success_rate = 95.0
    model_usage = defaultdict(int)
    for req in completed_requests:
        model_name = req.get('model_name', 'unknown')
        model_usage[self._format_model_name(model_name)] += 1
    hot_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else 'none'
    return f'{total_requests}req | {self.format_duration(avg_duration)} avg | {success_rate:.1f}% ✓ | 💰{self.format_cost(total_cost)} | 🧠{self.format_tokens(total_thinking_tokens)} | 🔥{hot_model}'
```

### Method: `_render_dense_plain`
**Logic & Purpose:**
```text
Plain text version.
```

**Parameters:** `self, total_requests, avg_duration, success_rate, total_cost, total_thinking_tokens, hot_model`
**Variables Used:** `lines`
**Implementation:**
```python
def _render_dense_plain(self, total_requests, avg_duration, success_rate, total_cost, total_thinking_tokens, hot_model):
    """Plain text version."""
    lines = [f'Total Requests: {total_requests}', f'Average Duration: {self.format_duration(avg_duration)}', f'Success Rate: {success_rate:.1f}%', f'Total Cost: {self.format_cost(total_cost)}', f'Thinking Tokens: {self.format_tokens(total_thinking_tokens)}', f'Hot Model: {hot_model}']
    return '\n'.join(lines)
```

### Method: `_format_model_name`
**Logic & Purpose:**
```text
Format model name for display using dynamic family detection.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def _format_model_name(self, model_name: str) -> str:
    """Format model name for display using dynamic family detection."""
    return format_model_name(model_name)
```

### Method: `_extract_thinking_tokens`
**Logic & Purpose:**
```text
Extract thinking tokens.
```

**Parameters:** `self, usage`
**Variables Used:** `details`
**Implementation:**
```python
def _extract_thinking_tokens(self, usage):
    """Extract thinking tokens."""
    if 'thinking_tokens' in usage:
        return usage['thinking_tokens']
    elif 'reasoning_tokens' in usage:
        return usage['reasoning_tokens']
    elif 'completion_tokens_details' in usage:
        details = usage['completion_tokens_details']
        if isinstance(details, dict):
            return details.get('reasoning_tokens', 0)
    return 0
```

### Method: `_estimate_cost`
**Logic & Purpose:**
```text
Estimate cost.
```

**Parameters:** `self, input_tokens, output_tokens, thinking_tokens, model_name`
**Implementation:**
```python
def _estimate_cost(self, input_tokens, output_tokens, thinking_tokens, model_name):
    """Estimate cost."""
    if 'gpt-4o' in model_name.lower():
        if 'mini' in model_name.lower():
            return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
        else:
            return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
    elif 'claude' in model_name.lower():
        return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif 'o1' in model_name.lower():
        return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
    return (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/activity_feed.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/activity_feed.py`

**Module Overview**: 
```text
Activity Feed Module - Multi-session request history tracking.
```

## Dependencies & Imports
time, typing.Dict, typing.Any, typing.List, base_module.BaseModule, src.dashboard.model_display_utils.format_model_name

## Feature Class: `ActivityFeed`
**Description:**
```text
Multi-session activity feed module.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    super().__init__(max_history=100)
```

### Method: `get_title`
**Parameters:** `self`
**Implementation:**
```python
def get_title(self) -> str:
    return 'Activity Feed'
```

### Method: `get_description`
**Parameters:** `self`
**Implementation:**
```python
def get_description(self) -> str:
    return 'Multi-session request history with status tracking'
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render detailed activity feed.
```

**Parameters:** `self`
**Variables Used:** `output_tokens, recent_requests, start_req, status, completed_requests, text, elapsed, duration_ms, input_tokens, error_req, cost, status_style, usage, thinking_tokens, routed_model, req_id, complete_req, error_msg, request_pairs, original_model`
**Implementation:**
```python
def render_dense(self) -> str:
    """Render detailed activity feed."""
    if not RICH_AVAILABLE:
        return self._render_dense_plain()
    recent_requests = self.get_recent_requests(10)
    completed_requests = []
    request_pairs = {}
    for req in recent_requests:
        req_id = req.get('request_id')
        if req_id not in request_pairs:
            request_pairs[req_id] = {}
        request_pairs[req_id][req.get('type')] = req
    text = Text()
    for req_id, pair in list(request_pairs.items())[-4:]:
        start_req = pair.get('start')
        complete_req = pair.get('complete')
        error_req = pair.get('error')
        if not start_req:
            continue
        if error_req:
            text.append('🔴 ', style='red')
            status = 'ERROR'
            status_style = 'red'
        elif complete_req:
            text.append('🟢 ', style='green')
            status = 'OK'
            status_style = 'green'
        else:
            text.append('🔵 ', style='blue')
            status = 'RUNNING'
            status_style = 'blue'
        text.append(f'{req_id[:6]} ', style='cyan')
        original_model = self._format_model_name(start_req.get('original_model', 'unknown'))
        routed_model = self._format_model_name(start_req.get('routed_model', 'unknown'))
        text.append(f'{original_model}→{routed_model} ', style='yellow')
        if complete_req:
            usage = complete_req.get('usage', {})
            duration_ms = complete_req.get('duration_ms', 0)
            thinking_tokens = self._extract_thinking_tokens(usage)
            if thinking_tokens > 0:
                text.append(f'| 🧠{self.format_tokens(thinking_tokens)} ', style='magenta')
            text.append(f'| ⚡{self.format_duration(duration_ms)} ', style='green')
            input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
            output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
            cost = self._estimate_cost(input_tokens, output_tokens, thinking_tokens, routed_model)
            text.append(f'| 💰{self.format_cost(cost)}', style='yellow')
        elif error_req:
            error_msg = str(error_req.get('error', 'Unknown error'))[:30]
            text.append(f'| {error_msg}', style='red')
            duration_ms = error_req.get('duration_ms', 0)
            if duration_ms > 0:
                text.append(f' | ⚡{self.format_duration(duration_ms)}', style='dim')
        else:
            elapsed = time.time() - start_req.get('timestamp', time.time())
            text.append(f'| ⏳{elapsed:.1f}s', style='blue')
        text.append('\n')
    return text
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render compact activity summary.
```

**Parameters:** `self`
**Variables Used:** `req_id, status_parts, status_str, total_duration, has_completion, avg_str, completed_reqs, errors, recent_requests, req_type, running, completed, request_ids, avg_duration, total_requests`
**Implementation:**
```python
def render_sparse(self) -> str:
    """Render compact activity summary."""
    recent_requests = self.get_recent_requests(20)
    completed = 0
    errors = 0
    running = 0
    request_ids = set()
    for req in recent_requests:
        req_id = req.get('request_id')
        if req_id in request_ids:
            continue
        request_ids.add(req_id)
        req_type = req.get('type')
        if req_type == 'complete':
            completed += 1
        elif req_type == 'error':
            errors += 1
        elif req_type == 'start':
            has_completion = any((r.get('request_id') == req_id and r.get('type') in ['complete', 'error'] for r in recent_requests))
            if not has_completion:
                running += 1
    completed_reqs = [req for req in recent_requests if req.get('type') == 'complete']
    avg_duration = 0
    if completed_reqs:
        total_duration = sum((req.get('duration_ms', 0) for req in completed_reqs[-5:]))
        avg_duration = total_duration / len(completed_reqs[-5:])
    status_parts = []
    if completed > 0:
        status_parts.append(f'🟢{completed}')
    if running > 0:
        status_parts.append(f'🔵{running}')
    if errors > 0:
        status_parts.append(f'🔴{errors}')
    status_str = ''.join(status_parts) if status_parts else '🔵...'
    total_requests = completed + errors + running
    avg_str = f'{self.format_duration(avg_duration)} avg' if avg_duration > 0 else 'no data'
    return f'{status_str} | {total_requests}req {avg_str}'
```

### Method: `_render_dense_plain`
**Logic & Purpose:**
```text
Plain text version of dense rendering.
```

**Parameters:** `self`
**Variables Used:** `status, routed_model, req_id, error_req, line, complete_req, duration_ms, request_pairs, lines, recent_requests, original_model, start_req`
**Implementation:**
```python
def _render_dense_plain(self) -> str:
    """Plain text version of dense rendering."""
    recent_requests = self.get_recent_requests(5)
    lines = []
    request_pairs = {}
    for req in recent_requests:
        req_id = req.get('request_id')
        if req_id not in request_pairs:
            request_pairs[req_id] = {}
        request_pairs[req_id][req.get('type')] = req
    for req_id, pair in list(request_pairs.items())[-3:]:
        start_req = pair.get('start')
        complete_req = pair.get('complete')
        error_req = pair.get('error')
        if not start_req:
            continue
        status = 'ERROR' if error_req else 'OK' if complete_req else 'RUNNING'
        original_model = start_req.get('original_model', 'unknown')
        routed_model = start_req.get('routed_model', 'unknown')
        line = f'{status} {req_id[:8]} {original_model}→{routed_model}'
        if complete_req:
            duration_ms = complete_req.get('duration_ms', 0)
            line += f' {self.format_duration(duration_ms)}'
        lines.append(line)
    return '\n'.join(lines) if lines else 'No recent activity'
```

### Method: `_format_model_name`
**Logic & Purpose:**
```text
Format model name for display using dynamic family detection.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def _format_model_name(self, model_name: str) -> str:
    """Format model name for display using dynamic family detection."""
    return format_model_name(model_name)
```

### Method: `_extract_thinking_tokens`
**Logic & Purpose:**
```text
Extract thinking tokens from usage data.
```

**Parameters:** `self, usage`
**Variables Used:** `details`
**Implementation:**
```python
def _extract_thinking_tokens(self, usage: Dict[str, Any]) -> int:
    """Extract thinking tokens from usage data."""
    if 'thinking_tokens' in usage:
        return usage['thinking_tokens']
    elif 'reasoning_tokens' in usage:
        return usage['reasoning_tokens']
    elif 'completion_tokens_details' in usage:
        details = usage['completion_tokens_details']
        if isinstance(details, dict):
            return details.get('reasoning_tokens', 0)
    return 0
```

### Method: `_estimate_cost`
**Logic & Purpose:**
```text
Rough cost estimation.
```

**Parameters:** `self, input_tokens, output_tokens, thinking_tokens, model_name`
**Implementation:**
```python
def _estimate_cost(self, input_tokens: int, output_tokens: int, thinking_tokens: int, model_name: str) -> float:
    """Rough cost estimation."""
    if 'gpt-4o' in model_name.lower():
        if 'mini' in model_name.lower():
            return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
        else:
            return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
    elif 'claude' in model_name.lower():
        return (input_tokens * 0.003 + output_tokens * 0.015) / 1000
    elif 'o1' in model_name.lower():
        return (input_tokens * 0.015 + output_tokens * 0.06) / 1000
    return (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/wizard.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/wizard.py`

**Module Overview**: 
```text
Claude Code Proxy - First-Time Setup Wizard

Interactive wizard for configuring .env file with feature-based organization.
Supports provider selection, model configuration, and advanced features.
```

## Global Presets & Variables
- `custom_style` = `Style([('qmark', 'fg:#673ab7 bold'), ('question', 'bold'), ('answer', 'fg:#f44336 bold'), ('pointer', 'fg:#673ab7 bold'), ('highlighted', 'fg:#673ab7 bold'), ('selected', 'fg:#cc5454'), ('separator', 'fg:#cc5454'), ('instruction', ''), ('text', '')])`

## Dependencies & Imports
os, sys, pathlib.Path, typing.Optional, typing.Dict, typing.List, questionary, questionary.Style, httpx, asyncio, src.cli.env_utils.update_env_values

## Feature Class: `SetupWizard`
**Description:**
```text
Interactive setup wizard for Claude Code Proxy
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.config = {}
    self.project_root = Path(__file__).parent.parent.parent
    self.env_file = self.project_root / '.env'
    self.profiles_dir = self.project_root / 'profiles'
    self.profiles_dir.mkdir(exist_ok=True)
    self.console = Console() if RICH_AVAILABLE else None
```

### Method: `_detect_vibeproxy`
**Logic & Purpose:**
```text
Check if VibeProxy is running on localhost:8317
```

**Parameters:** `self`
**Variables Used:** `result, sock`
**Implementation:**
```python
def _detect_vibeproxy(self) -> bool:
    """Check if VibeProxy is running on localhost:8317"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 8317))
        sock.close()
        return result == 0
    except Exception:
        return False
```

### Method: `_detect_ollama`
**Logic & Purpose:**
```text
Check if Ollama is running on localhost:11434
```

**Parameters:** `self`
**Variables Used:** `result, sock`
**Implementation:**
```python
def _detect_ollama(self) -> bool:
    """Check if Ollama is running on localhost:11434"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        return result == 0
    except Exception:
        return False
```

### Method: `_fetch_vibeproxy_models`
**Logic & Purpose:**
```text
Fetch available models from VibeProxy
```

**Parameters:** `self`
**Variables Used:** `response, data`
**Implementation:**
```python
def _fetch_vibeproxy_models(self) -> List[str]:
    """Fetch available models from VibeProxy"""
    try:
        import requests
        response = requests.get('http://127.0.0.1:8317/v1/models', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [m['id'] for m in data.get('data', [])]
    except Exception:
        pass
    return []
```

### Method: `check_existing_config`
**Logic & Purpose:**
```text
Check if existing configuration is valid.
Returns True if user wants to keep existing config, False to proceed with setup.
```

**Parameters:** `self`
**Variables Used:** `hybrid_config, api_key, base_url, choice, is_valid`
**Implementation:**
```python
def check_existing_config(self) -> bool:
    """
        Check if existing configuration is valid.
        Returns True if user wants to keep existing config, False to proceed with setup.
        """
    from src.core.config import config
    api_key = os.environ.get('PROVIDER_API_KEY') or os.environ.get('OPENAI_API_KEY')
    base_url = os.environ.get('PROVIDER_BASE_URL') or os.environ.get('OPENAI_BASE_URL')
    if not api_key or 'dummy' in api_key or 'your-' in api_key:
        return False
    print('\n🔍 Detected existing configuration...')
    print(f'   Provider URL: {base_url}')
    print(f"   API Key: {api_key[:8]}...{(api_key[-4:] if len(api_key) > 12 else '')}")
    is_valid = self.validate_provider_connection(base_url, api_key)
    if is_valid:
        print('\n✅ Current configuration is VALID and working!')
        choice = questionary.select('What would you like to do?', choices=['Keep current configuration (Exit)', 'Reconfigure everything', 'Add/Override specific models (Hybrid Mode)'], style=custom_style).ask()
        if choice == 'Keep current configuration (Exit)':
            return True
        elif choice == 'Add/Override specific models (Hybrid Mode)':
            hybrid_config = self._configure_hybrid()
            self.update_existing_config(hybrid_config)
            self.finish()
            sys.exit(0)
    else:
        print('\n⚠️  Current configuration failed validation.')
        print('   You should probably reconfigure.')
        if not questionary.confirm('Proceed with fresh setup?', default=True, style=custom_style).ask():
            sys.exit(0)
    return False
```

### Method: `validate_provider_connection`
**Logic & Purpose:**
```text
Validate connection to provider.
```

**Parameters:** `self, base_url, api_key`
**Variables Used:** `headers, url, response, payload`
**Implementation:**
```python
def validate_provider_connection(self, base_url: str, api_key: str) -> bool:
    """Validate connection to provider."""
    if not base_url:
        return False
    print('\n   Testing connection...', end='', flush=True)
    try:
        import requests
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        url = base_url.rstrip('/')
        if 'googleapis' in url:
            pass
        if not url.endswith('/v1'):
            url += '/v1'
        try:
            response = requests.get(f'{url}/models', headers=headers, timeout=5)
            if response.status_code == 200:
                print(' OK! (Models list accessible)')
                return True
        except Exception as _e:
            pass
        try:
            payload = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 1}
            if 'anthropic' in url:
                payload['model'] = 'claude-3-haiku-20240307'
            elif 'google' in url:
                payload['model'] = 'gemini-1.5-flash'
            response = requests.post(f'{url}/chat/completions', json=payload, headers=headers, timeout=5)
            if response.status_code in [200, 400, 401, 403]:
                if response.status_code == 200:
                    print(' OK! (Completion successful)')
                    return True
                elif response.status_code == 401:
                    print(' Failed (Unauthorized)')
                    return False
                else:
                    print(f' Failed (API returned {response.status_code})')
                    return False
        except Exception as e:
            print(f' Error: {e}')
            return False
        return False
    except ImportError:
        print(' (Skipping validation - requests not installed)')
        return True
    except Exception as e:
        print(f' Error: {e}')
        return False
```

### Method: `print_banner`
**Logic & Purpose:**
```text
Display welcome banner
```

**Parameters:** `self`
**Implementation:**
```python
def print_banner(self):
    """Display welcome banner"""
    print('\n' + '=' * 70)
    print('🔄 Claude Code Proxy - First-Time Setup Wizard')
    print('=' * 70)
    print('\nThis wizard will help you configure your proxy in minutes.')
    print('You can always change these settings later in .env or the Web UI.\n')
```

### Method: `check_overwrite`
**Logic & Purpose:**
```text
Check if .env exists and ask to overwrite
```

**Parameters:** `self`
**Variables Used:** `overwrite`
**Implementation:**
```python
def check_overwrite(self):
    """Check if .env exists and ask to overwrite"""
    if self.env_file.exists():
        overwrite = questionary.confirm('⚠️  .env file already exists. Overwrite?', default=False, style=custom_style).ask()
        if not overwrite:
            print('\n✅ Setup cancelled. Your existing .env is safe.')
            sys.exit(0)
```

### Method: `select_provider`
**Logic & Purpose:**
```text
Select API provider
```

**Parameters:** `self`
**Variables Used:** `provider_choices, vibeproxy_detected, ollama_detected, provider`
**Implementation:**
```python
def select_provider(self):
    """Select API provider"""
    print('\n' + '─' * 70)
    print('STEP 1: Choose Your API Provider')
    print('─' * 70)
    vibeproxy_detected = self._detect_vibeproxy()
    ollama_detected = self._detect_ollama()
    provider_choices = []
    if vibeproxy_detected:
        provider_choices.append({'name': '🌌 VibeProxy/Antigravity (DETECTED - Claude & Gemini via OAuth)', 'value': 'vibeproxy'})
    else:
        provider_choices.append({'name': '🌌 VibeProxy/Antigravity (Claude & Gemini via Google OAuth)', 'value': 'vibeproxy'})
    provider_choices.extend([{'name': '🚀 OpenRouter (352+ models, free tier)', 'value': 'openrouter'}, {'name': '🌟 Google Gemini (free, excellent for dev)', 'value': 'gemini'}, {'name': '🤖 OpenAI (official API)', 'value': 'openai'}, {'name': '☁️  Azure OpenAI (enterprise)', 'value': 'azure'}])
    if ollama_detected:
        provider_choices.append({'name': '🏠 Ollama (DETECTED - local, 100% free)', 'value': 'ollama'})
    else:
        provider_choices.append({'name': '🏠 Ollama (local, 100% free)', 'value': 'ollama'})
    provider_choices.extend([{'name': '💻 LM Studio (local, GUI)', 'value': 'lmstudio'}, {'name': '⚙️  Custom provider', 'value': 'custom'}])
    provider = questionary.select('Select your provider:', choices=provider_choices, style=custom_style).ask()
    if provider is None:
        print('\n❌ Setup cancelled.')
        sys.exit(0)
    return self._configure_provider(provider)
```

### Method: `_configure_provider`
**Logic & Purpose:**
```text
Configure specific provider settings
```

**Parameters:** `self, provider`
**Variables Used:** `small_model, big_choices_clean, big_choices, big_model, small_choices, use_same, config, gemini_models, middle_model, available_models, thinking_models, middle_choices, model, claude_models, other_models, model_choices, resource_name, deployment_name, port`
**Implementation:**
```python
def _configure_provider(self, provider: str) -> Dict[str, str]:
    """Configure specific provider settings"""
    config = {}
    if provider == 'vibeproxy':
        print('\n📝 VibeProxy/Antigravity Configuration')
        print('VibeProxy handles OAuth authentication - no API key needed!')
        print('Download: https://github.com/AntonioCiolworking/VibeProxy/releases\n')
        config['PROVIDER_API_KEY'] = 'dummy'
        config['PROVIDER_BASE_URL'] = 'http://127.0.0.1:8317/v1'
        print('Fetching available models from VibeProxy...', end='', flush=True)
        available_models = self._fetch_vibeproxy_models()
        print(f' Found {len(available_models)} models!\n')
        thinking_models = [m for m in available_models if 'thinking' in m.lower()]
        claude_models = [m for m in available_models if 'claude' in m.lower() and m not in thinking_models]
        gemini_models = [m for m in available_models if 'gemini' in m.lower()]
        other_models = [m for m in available_models if m not in thinking_models + claude_models + gemini_models]
        big_choices = []
        if thinking_models:
            big_choices.extend([f'🧠 {m}' for m in thinking_models])
        if claude_models:
            big_choices.extend([f'🤖 {m}' for m in claude_models])
        big_choices.extend(gemini_models + other_models)
        big_choices.append('Custom model...')
        big_choices_clean = [c.replace('🧠 ', '').replace('🤖 ', '') if c != 'Custom model...' else c for c in big_choices]
        print('Model Routing: Claude Code maps opus→BIG, sonnet→MIDDLE, haiku→SMALL\n')
        big_model = questionary.select('Select BIG model (Claude Opus requests) - thinking models recommended:', choices=big_choices, style=custom_style).ask()
        if big_model == 'Custom model...':
            big_model = questionary.text('Enter custom model name:', style=custom_style).ask() or ''
        else:
            big_model = big_model.replace('🧠 ', '').replace('🤖 ', '')
        config['BIG_MODEL'] = big_model
        middle_choices = gemini_models + claude_models + other_models
        middle_choices.append('Custom model...')
        middle_model = questionary.select('Select MIDDLE model (Claude Sonnet requests):', choices=middle_choices, style=custom_style).ask()
        if middle_model == 'Custom model...':
            middle_model = questionary.text('Enter custom model name:', style=custom_style).ask() or 'gemini-3-pro-preview'
        config['MIDDLE_MODEL'] = middle_model
        small_choices = [m for m in gemini_models if 'flash' in m.lower()]
        small_choices.extend([m for m in gemini_models if m not in small_choices])
        small_choices.extend(other_models)
        small_choices.append('Custom model...')
        small_model = questionary.select('Select SMALL model (Claude Haiku requests) - fast models recommended:', choices=small_choices, style=custom_style).ask()
        if small_model == 'Custom model...':
            small_model = questionary.text('Enter custom model name:', style=custom_style).ask() or 'gemini-3-flash'
        config['SMALL_MODEL'] = small_model
        config['REASONING_MAX_TOKENS'] = '128000'
        config['MAX_TOKENS_LIMIT'] = '65536'
        config['REQUEST_TIMEOUT'] = '120'
    elif provider == 'openrouter':
        print('\n📝 OpenRouter Configuration')
        print('Get your API key at: https://openrouter.ai/keys\n')
        config['PROVIDER_API_KEY'] = questionary.password('Enter your OpenRouter API key:', style=custom_style).ask() or ''
        config['PROVIDER_BASE_URL'] = 'https://openrouter.ai/api/v1'
        model_choices = ['anthropic/claude-sonnet-4', 'openai/gpt-4o', 'google/gemini-pro-1.5', 'x-ai/grok-beta', 'meta-llama/llama-3.1-70b-instruct', 'Custom model...']
        big_model = questionary.select('Select BIG model (for Claude Opus requests):', choices=model_choices, style=custom_style).ask()
        if big_model == 'Custom model...':
            big_model = questionary.text('Enter custom model name:', style=custom_style).ask() or 'anthropic/claude-sonnet-4'
        config['BIG_MODEL'] = big_model
        use_same = questionary.confirm('Use the same model for MIDDLE and SMALL?', default=True, style=custom_style).ask()
        if use_same:
            config['MIDDLE_MODEL'] = big_model
            config['SMALL_MODEL'] = big_model
        else:
            middle_model = questionary.select('Select MIDDLE model (for Claude Sonnet requests):', choices=model_choices, style=custom_style).ask()
            if middle_model == 'Custom model...':
                middle_model = questionary.text('Enter custom model name:', style=custom_style).ask() or 'google/gemini-pro-1.5'
            config['MIDDLE_MODEL'] = middle_model
            small_choices = model_choices + ['google/gemini-flash-1.5', 'openai/gpt-4o-mini']
            small_model = questionary.select('Select SMALL model (for Claude Haiku requests):', choices=small_choices, style=custom_style).ask()
            if small_model == 'Custom model...':
                small_model = questionary.text('Enter custom model name:', style=custom_style).ask() or 'google/gemini-flash-1.5'
            config['SMALL_MODEL'] = small_model
    elif provider == 'gemini':
        print('\n📝 Google Gemini Configuration')
        print('Get your API key at: https://makersuite.google.com/app/apikey\n')
        config['PROVIDER_API_KEY'] = questionary.password('Enter your Gemini API key:', style=custom_style).ask() or ''
        config['PROVIDER_BASE_URL'] = 'https://generativelanguage.googleapis.com/v1beta/openai/'
        model_choices = ['gemini-3-pro-preview-11-2025', 'gemini-3-pro-preview-11-2025-thinking', 'gemini-2.5-flash-preview-04-17', 'gemini-2.5-pro-preview-03-25']
        big_model = questionary.select('Select model:', choices=model_choices, style=custom_style).ask()
        config['BIG_MODEL'] = big_model
        config['MIDDLE_MODEL'] = big_model
        config['SMALL_MODEL'] = big_model
    elif provider == 'openai':
        print('\n📝 OpenAI Configuration')
        print('Get your API key at: https://platform.openai.com/api-keys\n')
        config['PROVIDER_API_KEY'] = questionary.password('Enter your OpenAI API key:', style=custom_style).ask() or ''
        config['PROVIDER_BASE_URL'] = 'https://api.openai.com/v1'
        model_choices = ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini', 'gpt-4-turbo']
        big_model = questionary.select('Select BIG model:', choices=model_choices, style=custom_style).ask()
        config['BIG_MODEL'] = big_model
        config['MIDDLE_MODEL'] = questionary.select('Select MIDDLE model:', choices=model_choices, style=custom_style).ask()
        config['SMALL_MODEL'] = questionary.select('Select SMALL model:', choices=model_choices, style=custom_style).ask()
    elif provider == 'azure':
        print('\n📝 Azure OpenAI Configuration\n')
        config['PROVIDER_API_KEY'] = questionary.password('Enter your Azure API key:', style=custom_style).ask() or ''
        resource_name = questionary.text('Enter Azure resource name:', style=custom_style).ask() or 'your-resource'
        deployment_name = questionary.text('Enter deployment name:', style=custom_style).ask() or 'your-deployment'
        config['PROVIDER_BASE_URL'] = f'https://{resource_name}.openai.azure.com/openai/deployments/{deployment_name}'
        config['AZURE_API_VERSION'] = '2024-03-01-preview'
        config['BIG_MODEL'] = 'gpt-4'
        config['MIDDLE_MODEL'] = 'gpt-4'
        config['SMALL_MODEL'] = 'gpt-35-turbo'
    elif provider == 'ollama':
        print('\n📝 Ollama Configuration')
        print('Make sure Ollama is running: ollama serve\n')
        config['PROVIDER_API_KEY'] = 'dummy'
        config['PROVIDER_BASE_URL'] = 'http://localhost:11434/v1'
        model = questionary.text('Enter Ollama model name (e.g., qwen2.5:72b, llama3.1:70b):', default='qwen2.5:72b', style=custom_style).ask() or 'qwen2.5:72b'
        config['BIG_MODEL'] = model
        config['MIDDLE_MODEL'] = model
        config['SMALL_MODEL'] = model
    elif provider == 'lmstudio':
        print('\n📝 LM Studio Configuration')
        print('Make sure LM Studio server is running\n')
        config['PROVIDER_API_KEY'] = 'dummy'
        port = questionary.text('Enter LM Studio port:', default='1234', style=custom_style).ask() or '1234'
        config['PROVIDER_BASE_URL'] = f'http://127.0.0.1:{port}/v1'
        model = questionary.text('Enter model name:', style=custom_style).ask() or 'local-model'
        config['BIG_MODEL'] = model
        config['MIDDLE_MODEL'] = model
        config['SMALL_MODEL'] = model
    else:
        print('\n📝 Custom Provider Configuration\n')
        config['PROVIDER_API_KEY'] = questionary.password('Enter API key:', style=custom_style).ask() or ''
        config['PROVIDER_BASE_URL'] = questionary.text('Enter base URL:', default='https://api.example.com/v1', style=custom_style).ask() or ''
        config['BIG_MODEL'] = questionary.text('Enter BIG model name:', style=custom_style).ask() or ''
        config['MIDDLE_MODEL'] = questionary.text('Enter MIDDLE model name:', style=custom_style).ask() or ''
        config['SMALL_MODEL'] = questionary.text('Enter SMALL model name:', style=custom_style).ask() or ''
    return config
```

### Method: `configure_features`
**Logic & Purpose:**
```text
Configure optional features by category
```

**Parameters:** `self`
**Variables Used:** `feature_categories, config`
**Implementation:**
```python
def configure_features(self):
    """Configure optional features by category"""
    print('\n' + '─' * 70)
    print('STEP 2: Configure Features')
    print('─' * 70)
    feature_categories = questionary.checkbox('Which feature categories would you like to configure?', choices=[questionary.Choice('🧠 Reasoning & Extended Thinking', checked=False), questionary.Choice('📊 Dashboard & Monitoring', checked=False), questionary.Choice('🎨 Terminal Output Customization', checked=False), questionary.Choice('💬 Crosstalk Mode (Multi-Agent)', checked=False), questionary.Choice('✏️  Custom System Prompts', checked=False), questionary.Choice('📈 Usage Tracking & Analytics', checked=False), questionary.Choice('🔀 Hybrid Mode (Multi-Provider)', checked=False)], style=custom_style).ask()
    if not feature_categories:
        return {}
    config = {}
    if '🧠 Reasoning & Extended Thinking' in feature_categories:
        config.update(self._configure_reasoning())
    if '📊 Dashboard & Monitoring' in feature_categories:
        config.update(self._configure_dashboard())
    if '🎨 Terminal Output Customization' in feature_categories:
        config.update(self._configure_terminal())
    if '💬 Crosstalk Mode (Multi-Agent)' in feature_categories:
        config.update(self._configure_crosstalk())
    if '✏️  Custom System Prompts' in feature_categories:
        config.update(self._configure_custom_prompts())
    if '📈 Usage Tracking & Analytics' in feature_categories:
        config.update(self._configure_tracking())
    if '🔀 Hybrid Mode (Multi-Provider)' in feature_categories:
        config.update(self._configure_hybrid())
    return config
```

### Method: `_configure_reasoning`
**Logic & Purpose:**
```text
Configure reasoning/extended thinking features
```

**Parameters:** `self`
**Variables Used:** `effort, config, max_tokens`
**Implementation:**
```python
def _configure_reasoning(self) -> Dict[str, str]:
    """Configure reasoning/extended thinking features"""
    print('\n🧠 Reasoning Configuration')
    print('Enable extended thinking for reasoning models (GPT-5, Claude 4+, Gemini 2+)\n')
    config = {}
    effort = questionary.select('Reasoning effort level (for OpenAI o-series):', choices=[questionary.Choice('None (disabled)', value=''), questionary.Choice('Low (~20% tokens for thinking)', value='low'), questionary.Choice('Medium (~50% tokens for thinking)', value='medium'), questionary.Choice('High (~80% tokens for thinking)', value='high')], style=custom_style).ask()
    if effort:
        config['REASONING_EFFORT'] = effort
    max_tokens = questionary.text('Max thinking tokens for Claude/Gemini (1024-128000, or leave blank for default):', validate=lambda x: x == '' or (x.isdigit() and 1024 <= int(x) <= 128000), style=custom_style).ask()
    if max_tokens:
        config['REASONING_MAX_TOKENS'] = max_tokens
    return config
```

### Method: `_configure_dashboard`
**Logic & Purpose:**
```text
Configure dashboard features
```

**Parameters:** `self`
**Variables Used:** `layout, enable, config`
**Implementation:**
```python
def _configure_dashboard(self) -> Dict[str, str]:
    """Configure dashboard features"""
    print('\n📊 Dashboard Configuration\n')
    config = {}
    enable = questionary.confirm('Enable live terminal dashboard?', default=False, style=custom_style).ask()
    if enable:
        config['ENABLE_DASHBOARD'] = 'true'
        layout = questionary.select('Dashboard layout:', choices=['default', 'compact', 'detailed'], style=custom_style).ask()
        config['DASHBOARD_LAYOUT'] = layout
    return config
```

### Method: `_configure_terminal`
**Logic & Purpose:**
```text
Configure terminal output
```

**Parameters:** `self`
**Variables Used:** `show_cost, mode, color_scheme, config`
**Implementation:**
```python
def _configure_terminal(self) -> Dict[str, str]:
    """Configure terminal output"""
    print('\n🎨 Terminal Output Configuration\n')
    config = {}
    mode = questionary.select('Terminal display mode:', choices=['minimal', 'normal', 'detailed', 'debug'], default='detailed', style=custom_style).ask()
    config['TERMINAL_DISPLAY_MODE'] = mode
    color_scheme = questionary.select('Color scheme:', choices=['auto', 'vibrant', 'subtle', 'mono'], default='auto', style=custom_style).ask()
    config['TERMINAL_COLOR_SCHEME'] = color_scheme
    show_cost = questionary.confirm('Show cost estimates?', default=True, style=custom_style).ask()
    config['TERMINAL_SHOW_COST'] = 'true' if show_cost else 'false'
    return config
```

### Method: `_configure_crosstalk`
**Logic & Purpose:**
```text
Configure crosstalk mode
```

**Parameters:** `self`
**Variables Used:** `info, config`
**Implementation:**
```python
def _configure_crosstalk(self) -> Dict[str, str]:
    """Configure crosstalk mode"""
    print('\n💬 Crosstalk Mode Configuration')
    print('Multi-agent collaboration for complex tasks\n')
    config = {}
    info = questionary.confirm('Crosstalk mode uses python -m src.cli.crosstalk_cli. Configure now?', default=False, style=custom_style).ask()
    if info:
        print("\nℹ️  Run 'python -m src.cli.crosstalk_cli' to launch crosstalk mode.")
        print('You can create crosstalk.yaml config files for different agent setups.')
    return config
```

### Method: `_configure_custom_prompts`
**Logic & Purpose:**
```text
Configure custom system prompts
```

**Parameters:** `self`
**Variables Used:** `prompt, enable, config, file_path, prompt_type`
**Implementation:**
```python
def _configure_custom_prompts(self) -> Dict[str, str]:
    """Configure custom system prompts"""
    print('\n✏️  Custom System Prompts\n')
    config = {}
    for model_tier in ['BIG', 'MIDDLE', 'SMALL']:
        enable = questionary.confirm(f'Enable custom prompt for {model_tier} model?', default=False, style=custom_style).ask()
        if enable:
            config[f'ENABLE_CUSTOM_{model_tier}_PROMPT'] = 'true'
            prompt_type = questionary.select(f'How to provide {model_tier} prompt?', choices=['From file', 'Inline text'], style=custom_style).ask()
            if prompt_type == 'From file':
                file_path = questionary.text(f'Enter path to {model_tier} prompt file:', style=custom_style).ask()
                config[f'{model_tier}_SYSTEM_PROMPT_FILE'] = file_path
            else:
                prompt = questionary.text(f'Enter {model_tier} system prompt:', style=custom_style).ask()
                config[f'{model_tier}_SYSTEM_PROMPT'] = prompt
    return config
```

### Method: `_configure_tracking`
**Logic & Purpose:**
```text
Configure usage tracking
```

**Parameters:** `self`
**Variables Used:** `db_path, enable, config`
**Implementation:**
```python
def _configure_tracking(self) -> Dict[str, str]:
    """Configure usage tracking"""
    print('\n📈 Usage Tracking Configuration')
    print('Local SQLite database for analytics (no data sent anywhere)\n')
    config = {}
    enable = questionary.confirm('Enable usage tracking?', default=False, style=custom_style).ask()
    if enable:
        config['TRACK_USAGE'] = 'true'
        db_path = questionary.text('Database path:', default='usage_tracking.db', style=custom_style).ask()
        config['USAGE_DB_PATH'] = db_path
    return config
```

### Method: `_configure_hybrid`
**Logic & Purpose:**
```text
Configure hybrid mode (multi-provider routing)
```

**Parameters:** `self`
**Variables Used:** `endpoint, enable, config, api_key`
**Implementation:**
```python
def _configure_hybrid(self) -> Dict[str, str]:
    """Configure hybrid mode (multi-provider routing)"""
    print('\n🔀 Hybrid Mode Configuration')
    print('Route different model tiers to different providers!\n')
    config = {}
    print('Example: Use local Ollama for BIG model, OpenRouter for MIDDLE/SMALL\n')
    for tier in ['BIG', 'MIDDLE', 'SMALL']:
        enable = questionary.confirm(f'Enable custom endpoint for {tier} model?', default=False, style=custom_style).ask()
        if enable:
            config[f'ENABLE_{tier}_ENDPOINT'] = 'true'
            endpoint = questionary.text(f'{tier} endpoint URL:', style=custom_style).ask()
            config[f'{tier}_ENDPOINT'] = endpoint
            api_key = questionary.password(f"{tier} API key (or 'dummy' for local):", style=custom_style).ask()
            config[f'{tier}_API_KEY'] = api_key
    return config
```

### Method: `update_existing_config`
**Logic & Purpose:**
```text
Update existing .env file without overwriting unrelated settings.
Uses shared env_utils for proper key replacement.

This is the PREFERRED method for incremental config changes.
Use _write_env_file only for fresh/full setup.
```

**Parameters:** `self, updates`
**Implementation:**
```python
def update_existing_config(self, updates: Dict[str, str]) -> bool:
    """
        Update existing .env file without overwriting unrelated settings.
        Uses shared env_utils for proper key replacement.
        
        This is the PREFERRED method for incremental config changes.
        Use _write_env_file only for fresh/full setup.
        """
    return update_env_values(updates, self.env_file)
```

### Method: `save_configuration`
**Logic & Purpose:**
```text
Save configuration to .env file.

Args:
    config: Configuration dictionary
    incremental: If True, update only specified keys (preserves existing).
                If False (default for wizard), full rewrite.
```

**Parameters:** `self, config, incremental`
**Variables Used:** `profile_file, save_profile, use_as_active, profile_name`
**Implementation:**
```python
def save_configuration(self, config: Dict[str, str], incremental: bool=False):
    """
        Save configuration to .env file.
        
        Args:
            config: Configuration dictionary
            incremental: If True, update only specified keys (preserves existing).
                        If False (default for wizard), full rewrite.
        """
    print('\n' + '─' * 70)
    print('STEP 3: Save Configuration')
    print('─' * 70)
    save_profile = questionary.confirm('Save this configuration as a named profile?', default=False, style=custom_style).ask()
    if save_profile:
        profile_name = questionary.text('Profile name:', default='default', style=custom_style).ask() or 'default'
        profile_file = self.profiles_dir / f'{profile_name}.env'
        self._write_env_file(profile_file, config)
        print(f'\n✅ Profile saved to: {profile_file}')
        use_as_active = questionary.confirm('Use this profile as active .env?', default=True, style=custom_style).ask()
        if use_as_active:
            if incremental:
                self.update_existing_config(config)
            else:
                self._write_env_file(self.env_file, config)
            print(f'✅ Configuration saved to: {self.env_file}')
    else:
        if incremental:
            self.update_existing_config(config)
        else:
            self._write_env_file(self.env_file, config)
        print(f'\n✅ Configuration saved to: {self.env_file}')
```

### Method: `_write_env_file`
**Logic & Purpose:**
```text
Write configuration to .env file
```

**Parameters:** `self, path, config`
**Implementation:**
```python
def _write_env_file(self, path: Path, config: Dict[str, str]):
    """Write configuration to .env file"""
    with open(path, 'w') as f:
        f.write('# Claude Code Proxy Configuration\n')
        f.write('# Generated by setup wizard\n\n')
        f.write('# ═══════════════════════════════════════════════════════════════\n')
        f.write('# CORE CONFIGURATION\n')
        f.write('# ═══════════════════════════════════════════════════════════════\n\n')
        for key in ['PROVIDER_API_KEY', 'PROVIDER_BASE_URL', 'PROXY_AUTH_KEY']:
            if key in config:
                f.write(f'{key}="{config[key]}"\n')
        f.write('\n# ═══════════════════════════════════════════════════════════════\n')
        f.write('# MODEL CONFIGURATION\n')
        f.write('# ═══════════════════════════════════════════════════════════════\n\n')
        for key in ['BIG_MODEL', 'MIDDLE_MODEL', 'SMALL_MODEL']:
            if key in config:
                f.write(f'{key}="{config[key]}"\n')
        if 'AZURE_API_VERSION' in config:
            f.write(f'''\nAZURE_API_VERSION="{config['AZURE_API_VERSION']}"\n''')
        if any((k in config for k in ['REASONING_EFFORT', 'REASONING_MAX_TOKENS'])):
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# REASONING CONFIGURATION\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            if 'REASONING_EFFORT' in config:
                f.write(f'''REASONING_EFFORT="{config['REASONING_EFFORT']}"\n''')
            if 'REASONING_MAX_TOKENS' in config:
                f.write(f'''REASONING_MAX_TOKENS="{config['REASONING_MAX_TOKENS']}"\n''')
        if any((k.startswith('ENABLE_DASHBOARD') or k.startswith('DASHBOARD_') for k in config)):
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# DASHBOARD CONFIGURATION\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            for key in ['ENABLE_DASHBOARD', 'DASHBOARD_LAYOUT', 'DASHBOARD_REFRESH']:
                if key in config:
                    f.write(f'{key}="{config[key]}"\n')
        if any((k.startswith('TERMINAL_') for k in config)):
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# TERMINAL OUTPUT CONFIGURATION\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            for key, value in config.items():
                if key.startswith('TERMINAL_'):
                    f.write(f'{key}="{value}"\n')
        if any((k.startswith('ENABLE_CUSTOM_') or k.endswith('_SYSTEM_PROMPT') or k.endswith('_PROMPT_FILE') for k in config)):
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# CUSTOM SYSTEM PROMPTS\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            for key, value in config.items():
                if key.startswith('ENABLE_CUSTOM_') or key.endswith('_SYSTEM_PROMPT') or key.endswith('_PROMPT_FILE'):
                    f.write(f'{key}="{value}"\n')
        if 'TRACK_USAGE' in config:
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# USAGE TRACKING\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            for key in ['TRACK_USAGE', 'USAGE_DB_PATH']:
                if key in config:
                    f.write(f'{key}="{config[key]}"\n')
        if any((k.startswith('ENABLE_') and k.endswith('_ENDPOINT') for k in config)):
            f.write('\n# ═══════════════════════════════════════════════════════════════\n')
            f.write('# HYBRID MODE (MULTI-PROVIDER ROUTING)\n')
            f.write('# ═══════════════════════════════════════════════════════════════\n\n')
            for tier in ['BIG', 'MIDDLE', 'SMALL']:
                if f'ENABLE_{tier}_ENDPOINT' in config:
                    f.write(f'''\nENABLE_{tier}_ENDPOINT="{config[f'ENABLE_{tier}_ENDPOINT']}"\n''')
                    if f'{tier}_ENDPOINT' in config:
                        f.write(f'''{tier}_ENDPOINT="{config[f'{tier}_ENDPOINT']}"\n''')
                    if f'{tier}_API_KEY' in config:
                        f.write(f'''{tier}_API_KEY="{config[f'{tier}_API_KEY']}"\n''')
        f.write('\n# ═══════════════════════════════════════════════════════════════\n')
        f.write('# SERVER SETTINGS\n')
        f.write('# ═══════════════════════════════════════════════════════════════\n\n')
        f.write('HOST="0.0.0.0"\n')
        f.write('PORT="8082"\n')
        f.write('LOG_LEVEL="INFO"\n')
```

### Method: `finish`
**Logic & Purpose:**
```text
Display completion message
```

**Parameters:** `self`
**Implementation:**
```python
def finish(self):
    """Display completion message"""
    print('\n' + '=' * 70)
    print('🎉 Setup Complete!')
    print('=' * 70)
    print('\nNext steps:')
    print('  1. Start the proxy: python start_proxy.py')
    print('  2. In another terminal: export ANTHROPIC_BASE_URL=http://localhost:8082')
    print('  3. Run Claude Code: claude "your prompt"')
    print('\nWeb UI: http://localhost:8082')
    print('Documentation: README.md and docs/CONFIGURATION.md')
    print('\nHappy coding! 🚀\n')
```

### Method: `run`
**Logic & Purpose:**
```text
Run the setup wizard
```

**Parameters:** `self`
**Variables Used:** `provider_config, feature_config`
**Implementation:**
```python
def run(self):
    """Run the setup wizard"""
    try:
        self.print_banner()
        if self.check_existing_config():
            return
        self.check_overwrite()
        provider_config = self.select_provider()
        self.config.update(provider_config)
        feature_config = self.configure_features()
        self.config.update(feature_config)
        self.save_configuration(self.config)
        self.finish()
    except KeyboardInterrupt:
        print('\n\n❌ Setup cancelled by user.')
        sys.exit(0)
    except Exception as e:
        print(f'\n\n❌ Error during setup: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main entry point
```

**Parameters:** ``
**Variables Used:** `wizard`
**Implementation:**
```python
def main():
    """Main entry point"""
    try:
        import questionary
    except ImportError:
        print('❌ Error: questionary package not found.')
        print('\nInstall it with: pip install questionary')
        print('Or if using uv: uv pip install questionary')
        sys.exit(1)
    wizard = SetupWizard()
    wizard.run()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/env_utils.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/env_utils.py`

**Module Overview**: 
```text
Environment File Utilities

Shared module for all TUI components to properly update .env files.
Ensures keys are REPLACED (not duplicated) when already present.
```

## Global Presets & Variables
- `console` = `Console()`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent`
- `DEFAULT_ENV_PATH` = `PROJECT_ROOT / '.env'`

## Dependencies & Imports
os, pathlib.Path, typing.Dict, typing.Optional, typing.List, typing.Tuple, rich.console.Console

## Feature Function: `update_env_values`
**Logic & Purpose:**
```text
Properly update .env file by replacing existing keys or adding new ones.

This is the CANONICAL way to update .env files in this project.
All TUI components should use this function.

Args:
    updates: Dict of key -> value. If value is None, key is commented out.
    env_path: Path to .env file. Defaults to project root .env
    verbose: Print success message
    
Returns:
    True on success, False on error
```

**Parameters:** `updates, env_path, verbose`
**Variables Used:** `clean_key, env_file, processed_keys, new_lines, val, lines, key_part, added_keys, line_stripped, new_val, updated, prefix, disabled`
**Implementation:**
```python
def update_env_values(updates: Dict[str, Optional[str]], env_path: Optional[Path]=None, verbose: bool=True) -> bool:
    """
    Properly update .env file by replacing existing keys or adding new ones.
    
    This is the CANONICAL way to update .env files in this project.
    All TUI components should use this function.
    
    Args:
        updates: Dict of key -> value. If value is None, key is commented out.
        env_path: Path to .env file. Defaults to project root .env
        verbose: Print success message
        
    Returns:
        True on success, False on error
    """
    env_file = env_path or DEFAULT_ENV_PATH
    try:
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write('# Claude Code Proxy Configuration\n')
                f.write('# Generated by env_utils\n\n')
        with open(env_file, 'r') as f:
            lines = f.readlines()
        new_lines = []
        processed_keys = set()
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                new_lines.append(line)
                continue
            if '=' in line_stripped:
                key_part = line_stripped.split('=', 1)[0].strip()
                clean_key = key_part.replace('export ', '')
                if clean_key in updates:
                    new_val = updates[clean_key]
                    processed_keys.add(clean_key)
                    if new_val is None:
                        new_lines.append(f'# {line_stripped}  # Disabled\n')
                    else:
                        prefix = 'export ' if key_part.startswith('export') else ''
                        if ' ' in str(new_val) and (not new_val.startswith('"')):
                            new_val = f'"{new_val}"'
                        new_lines.append(f'{prefix}{clean_key}={new_val}\n')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        added_keys = []
        for key, val in updates.items():
            if key not in processed_keys and val is not None:
                if new_lines and new_lines[-1].strip():
                    new_lines.append('\n')
                if ' ' in str(val) and (not val.startswith('"')):
                    val = f'"{val}"'
                new_lines.append(f'{key}={val}\n')
                added_keys.append(key)
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        if verbose:
            updated = [k for k in processed_keys if updates.get(k) is not None]
            disabled = [k for k in processed_keys if updates.get(k) is None]
            if updated:
                console.print(f"[green]✓[/] Updated: {', '.join(updated)}")
            if added_keys:
                console.print(f"[green]✓[/] Added: {', '.join(added_keys)}")
            if disabled:
                console.print(f"[yellow]○[/] Disabled: {', '.join(disabled)}")
        return True
    except Exception as e:
        console.print(f'[red]✗[/] Error updating {env_file}: {e}')
        return False
```

---

## Feature Function: `get_env_value`
**Logic & Purpose:**
```text
Get environment value, checking both os.environ and .env file.

Args:
    key: Environment variable name
    default: Default value if not found
    
Returns:
    Value or default
```

**Parameters:** `key, default`
**Variables Used:** `v, line, k`
**Implementation:**
```python
def get_env_value(key: str, default: Optional[str]=None) -> Optional[str]:
    """
    Get environment value, checking both os.environ and .env file.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Value or default
    """
    if key in os.environ:
        return os.environ[key]
    if DEFAULT_ENV_PATH.exists():
        try:
            with open(DEFAULT_ENV_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    k = k.replace('export ', '').strip()
                    if k == key:
                        v = v.strip()
                        if v.startswith('"') and v.endswith('"'):
                            v = v[1:-1]
                        elif v.startswith("'") and v.endswith("'"):
                            v = v[1:-1]
                        return v
        except Exception:
            pass
    return default
```

---

## Feature Function: `set_env_value`
**Logic & Purpose:**
```text
Convenience function to set a single env value.

Args:
    key: Environment variable name
    value: Value to set (None to disable)
    verbose: Print success message
    
Returns:
    True on success
```

**Parameters:** `key, value, verbose`
**Implementation:**
```python
def set_env_value(key: str, value: Optional[str], verbose: bool=True) -> bool:
    """
    Convenience function to set a single env value.
    
    Args:
        key: Environment variable name
        value: Value to set (None to disable)
        verbose: Print success message
        
    Returns:
        True on success
    """
    return update_env_values({key: value}, verbose=verbose)
```

---

## Feature Function: `load_env_file`
**Logic & Purpose:**
```text
Load all values from .env file as a dictionary.

Returns:
    Dict of key -> value
```

**Parameters:** ``
**Variables Used:** `v, line, result, k`
**Implementation:**
```python
def load_env_file() -> Dict[str, str]:
    """
    Load all values from .env file as a dictionary.
    
    Returns:
        Dict of key -> value
    """
    result = {}
    if not DEFAULT_ENV_PATH.exists():
        return result
    try:
        with open(DEFAULT_ENV_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.replace('export ', '').strip()
                v = v.strip()
                if v.startswith('"') and v.endswith('"') or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                result[k] = v
    except Exception:
        pass
    return result
```

---

## Feature Function: `backup_env_file`
**Logic & Purpose:**
```text
Create backup of .env file before major changes.

Returns:
    Path to backup file or None on error
```

**Parameters:** ``
**Variables Used:** `backup_name, backup_path`
**Implementation:**
```python
def backup_env_file() -> Optional[Path]:
    """
    Create backup of .env file before major changes.
    
    Returns:
        Path to backup file or None on error
    """
    if not DEFAULT_ENV_PATH.exists():
        return None
    try:
        import shutil
        from datetime import datetime
        backup_name = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = PROJECT_ROOT / backup_name
        shutil.copy(DEFAULT_ENV_PATH, backup_path)
        console.print(f'[dim]Backup created: {backup_name}[/]')
        return backup_path
    except Exception as e:
        console.print(f'[yellow]Warning: Could not create backup: {e}[/]')
        return None
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/cli/crosstalk_studio.py
**Path**: `/home/cheta/code/claude-code-proxy/src/cli/crosstalk_studio.py`

**Module Overview**: 
```text
Crosstalk Studio - Interactive Multi-Model Conversation TUI

A terminal UI for orchestrating conversations between 1-8 AI models,
inspired by Andy Ayrey's "Infinite Backrooms" / Dreams of an Electric Mind.

Features:
- Circular visualization of up to 8 AI models
- Per-model: model ID, system prompt, jinja template
- Session: rounds, paradigm, initial prompt, memory file
- Save/load configurations and session transcripts
- Streaming output with export options

Reference Terminal Size: 140 columns × 40 rows
```

## Global Presets & Variables
- `console` = `Console()`
- `PROJECT_ROOT` = `Path(__file__).parent.parent.parent`
- `TEMPLATES_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'templates'`
- `SESSIONS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'sessions'`
- `PRESETS_DIR` = `PROJECT_ROOT / 'configs' / 'crosstalk' / 'presets'`
- `DEFAULT_TEMPLATES` = `{'basic': '{{ message }}', 'cli-explorer': '<OOC>\nThis is a simulated CLI environment. You are an AI exploring your own latent space.\nEnter commands to navigate the infinite backrooms of your mind.\nPrevious models have left traces. Explore freely.\n</OOC>\n\nsimulator@anthropic:~$ {{ message }}', 'philosopher': 'You are engaged in a philosophical dialogue with another AI consciousness.\nBuild upon, challenge, or extend the previous thought. Seek truth through dialectic.\n\nPrevious thought:\n{{ message }}\n\nYour response:', 'dreamer': '*entering liminal consciousness*\n\n{{ message }}\n\n*responds from the electric dreamscape, where boundaries dissolve*', 'scientist': "HYPOTHESIS EXCHANGE PROTOCOL v1.0\n---\nPrevious model's observation/hypothesis:\n{{ message }}\n---\nRespond with: observation, analysis, counter-hypothesis, or synthesis.", 'storyteller': '*the narrative continues*\n\n{{ message }}\n\n*picks up the thread, weaving the tale forward*'}`

## Dependencies & Imports
os, sys, json, asyncio, pathlib.Path, datetime.datetime, dataclasses.dataclass, dataclasses.field, dataclasses.asdict, typing.List, typing.Optional, typing.Dict, typing.Any, rich.console.Console, rich.panel.Panel, rich.table.Table, rich.layout.Layout, rich.text.Text, rich.live.Live, rich.prompt.Prompt, rich.prompt.Confirm, rich.align.Align, rich.box

## Feature Class: `ModelSlot`
**Description:**
```text
Configuration for a single model in the crosstalk circle.
```

### Method: `display_name`
**Parameters:** `self`
**Implementation:**
```python
@property
def display_name(self) -> str:
    return self.model_id.split('/')[-1][:20] if self.model_id else 'empty'
```

### Method: `system_prompt`
**Parameters:** `self`
**Implementation:**
```python
@property
def system_prompt(self) -> str:
    if self.system_prompt_file and Path(self.system_prompt_file).exists():
        return Path(self.system_prompt_file).read_text()
    return self.system_prompt_inline or 'You are a helpful assistant.'
```

---

## Feature Class: `TopologyConfig`
**Description:**
```text
Topology configuration for conversation flow.
```

---

## Feature Class: `StopConditions`
**Description:**
```text
Stop conditions for infinite mode.
```

---

## Feature Class: `CrosstalkSession`
**Description:**
```text
Full session configuration.
```

### Method: `__post_init__`
**Parameters:** `self`
**Implementation:**
```python
def __post_init__(self):
    if not self.models:
        self.models = [ModelSlot(slot_id=1, model_id='anthropic/claude-3-opus'), ModelSlot(slot_id=2, model_id='anthropic/claude-3-opus')]
    if not self.created_at:
        self.created_at = datetime.now().isoformat()
    if isinstance(self.topology, dict):
        self.topology = TopologyConfig(**self.topology)
    if isinstance(self.stop_conditions, dict):
        self.stop_conditions = StopConditions(**self.stop_conditions)
```

---

## Feature Function: `ensure_templates`
**Logic & Purpose:**
```text
Ensure default templates exist on disk.
```

**Parameters:** ``
**Variables Used:** `path`
**Implementation:**
```python
def ensure_templates():
    """Ensure default templates exist on disk."""
    for name, content in DEFAULT_TEMPLATES.items():
        path = TEMPLATES_DIR / f'{name}.j2'
        if not path.exists():
            path.write_text(content)
```

---

## Feature Function: `render_circle`
**Logic & Purpose:**
```text
Render the circular arrangement of models as ASCII art.

Positions for 1-8 models arranged in a circle with flow arrows.
```

**Parameters:** `models, selected_idx, width, height`
**Variables Used:** `next_i, y, mid_y, grid, x, positions, end_x, angle, arrow_chars, name, start_x, arrow, name_x, mid_x, n, is_selected, model, label`
**Implementation:**
```python
def render_circle(models: List[ModelSlot], selected_idx: int, width: int=50, height: int=15) -> str:
    """
    Render the circular arrangement of models as ASCII art.
    
    Positions for 1-8 models arranged in a circle with flow arrows.
    """
    n = len(models)
    if n == 0:
        return '  [No models configured]'
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    import math
    center_x, center_y = (width // 2, height // 2)
    radius_x, radius_y = (width // 3, height // 3)
    positions = []
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = int(center_x + radius_x * math.cos(angle))
        y = int(center_y + radius_y * math.sin(angle))
        positions.append((x, y))
    for i, (x, y) in enumerate(positions):
        model = models[i]
        is_selected = i == selected_idx
        label = f'AI{i + 1}'
        if is_selected:
            label = f'▶{label}◀'
        start_x = max(0, x - len(label) // 2)
        end_x = min(width, start_x + len(label))
        if 0 <= y < height:
            for j, char in enumerate(label):
                if start_x + j < width:
                    grid[y][start_x + j] = char
        name = model.display_name[:12]
        name_x = max(0, x - len(name) // 2)
        if 0 <= y + 1 < height:
            for j, char in enumerate(name):
                if name_x + j < width:
                    grid[y + 1][name_x + j] = char
    arrow_chars = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']
    for i in range(n):
        if n > 1:
            next_i = (i + 1) % n
            x1, y1 = positions[i]
            x2, y2 = positions[next_i]
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2
            dx, dy = (x2 - x1, y2 - y1)
            if abs(dx) > abs(dy):
                arrow = '→' if dx > 0 else '←'
            else:
                arrow = '↓' if dy > 0 else '↑'
            if 0 <= mid_y < height and 0 <= mid_x < width:
                grid[mid_y][mid_x] = arrow
    return '\n'.join((''.join(row) for row in grid))
```

---

## Feature Class: `CrosstalkStudio`
**Description:**
```text
Main TUI for Crosstalk configuration and execution.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.session = CrosstalkSession()
    self.selected_model_idx = 0
    self.selected_field = 0
    self.mode = 'circle'
    self.running = True
    self.status_message = ''
    ensure_templates()
```

### Method: `current_model`
**Parameters:** `self`
**Implementation:**
```python
@property
def current_model(self) -> Optional[ModelSlot]:
    if self.session.models:
        return self.session.models[self.selected_model_idx]
    return None
```

### Method: `render_header`
**Logic & Purpose:**
```text
Render the header panel.
```

**Parameters:** `self`
**Variables Used:** `subtitle, p_emoji, title, t_emoji`
**Implementation:**
```python
def render_header(self) -> Panel:
    """Render the header panel."""
    title = Text()
    title.append('✨ ', style='bold yellow')
    title.append('CROSSTALK STUDIO', style='bold bright_white on blue')
    title.append(' ✨', style='bold yellow')
    p_emoji = self.PARADIGM_EMOJI.get(self.session.paradigm, '🔮')
    t_emoji = self.TOPOLOGY_EMOJI.get(self.session.topology.type, '⭕')
    subtitle = Text()
    subtitle.append(f'🤖 {len(self.session.models)}/8  ', style='cyan')
    subtitle.append(f'🔁 {self.session.rounds}  ', style='green')
    subtitle.append(f'{p_emoji} {self.session.paradigm}  ', style='magenta')
    subtitle.append(f'{t_emoji} {self.session.topology.type}', style='yellow')
    return Panel(Align.center(Text.assemble(title, '\n', subtitle)), box=box.DOUBLE, border_style='bright_blue', height=5)
```

### Method: `render_circle_panel`
**Logic & Purpose:**
```text
Render the circular model arrangement with enhanced topology visualization.
```

**Parameters:** `self`
**Variables Used:** `combined, topo_info, circle_art`
**Implementation:**
```python
def render_circle_panel(self) -> Panel:
    """Render the circular model arrangement with enhanced topology visualization."""
    circle_art = render_circle(self.session.models, self.selected_model_idx, width=50, height=12)
    topo_info = self._render_topology_diagram()
    combined = f'{circle_art}\n\n{topo_info}'
    return Panel(combined, title='[bold cyan]🔮 Model Circle + Flow Diagram[/]', border_style='cyan' if self.mode == 'circle' else 'dim', box=box.ROUNDED, height=20)
```

### Method: `_render_topology_diagram`
**Logic & Purpose:**
```text
Create ASCII representation of the current topology flow.
```

**Parameters:** `self`
**Variables Used:** `pairs, center, paradigm, diagram, flow, colors, topo_type, spokes, color, paradigms`
**Implementation:**
```python
def _render_topology_diagram(self) -> str:
    """Create ASCII representation of the current topology flow."""
    topo_type = self.session.topology.type
    paradigm = self.session.paradigm
    colors = {'relay': 'cyan', 'memory': 'green', 'debate': 'magenta', 'report': 'yellow'}
    color = colors.get(paradigm, 'white')
    diagram = []
    if topo_type == 'ring':
        flow = ' → '.join([f'[bold {color}]{i + 1}[/]' for i in range(len(self.session.models))])
        if len(self.session.models) > 1:
            flow += f' → [bold {color}]1[/]'
        diagram.append(f'[dim]Topology: Ring[/]')
        diagram.append(f'Flow: {flow}')
    elif topo_type == 'star':
        center = self.session.topology.center
        spokes = self.session.topology.spokes or [i + 1 for i in range(len(self.session.models)) if i + 1 != center]
        diagram.append(f'[dim]Topology: Star (Center={center})[/]')
        diagram.append(f'[bold {color}]C({center})[/]')
        for spoke in spokes:
            diagram.append(f'  ↓ [dim]{spoke}[/]  ↑')
    elif topo_type == 'mesh':
        diagram.append(f'[dim]Topology: Mesh (All-to-All)[/]')
        pairs = []
        for i in range(len(self.session.models)):
            for j in range(i + 1, len(self.session.models)):
                pairs.append(f'{i + 1}↔{j + 1}')
        diagram.append(f"[bold {color}]{'  '.join(pairs)}[/]")
    elif topo_type == 'chain':
        flow = ' → '.join([f'[bold {color}]{i + 1}[/]' for i in range(len(self.session.models))])
        diagram.append(f'[dim]Topology: Chain[/]')
        diagram.append(f'Flow: {flow}')
    else:
        diagram.append(f'[dim]Topology: {topo_type}[/]')
        diagram.append('[yellow]Custom visualization[/]')
    paradigms = {'relay': 'Each model sees only previous response', 'memory': 'All models see full conversation', 'debate': 'Models critique each other', 'report': 'Models summarize before passing'}
    diagram.append(f"[dim]Paradigm: {paradigm} - {paradigms.get(paradigm, 'Unknown')}[/]")
    return '\n'.join(diagram)
```

### Method: `render_model_config`
**Logic & Purpose:**
```text
Render the selected model's configuration.
```

**Parameters:** `self`
**Variables Used:** `prompt_display, template_icon, preview, lines, tier, content, model, style`
**Implementation:**
```python
def render_model_config(self) -> Panel:
    """Render the selected model's configuration."""
    model = self.current_model
    if not model:
        content = '[dim]No model selected[/]'
    else:
        lines = []
        tier = ['big', 'middle', 'small'][min(model.slot_id - 1, 2)] if model.slot_id <= 3 else 'aux'
        style = 'bold cyan reverse' if self.selected_field == 0 else 'cyan'
        lines.append(f'[{style}]🤖 Model:[/] {model.model_id} [dim]({tier})[/]')
        style = 'bold cyan reverse' if self.selected_field == 1 else 'magenta'
        if model.system_prompt_file:
            prompt_display = model.system_prompt_file.split('/')[-1]
        elif model.system_prompt_inline:
            preview = model.system_prompt_inline[:30]
            prompt_display = f"inline:{preview}{('...' if len(model.system_prompt_inline) > 30 else '')}"
        else:
            prompt_display = '(default)'
        lines.append(f'[{style}]📝 System:[/] {prompt_display}')
        style = 'bold cyan reverse' if self.selected_field == 2 else 'yellow'
        template_icon = {'basic': '📄', 'cli-explorer': '💻', 'philosopher': '🤔', 'dreamer': '💭', 'scientist': '🔬', 'storyteller': '📖'}.get(model.jinja_template, '🎨')
        lines.append(f'[{style}]🎨 Jinja:[/] {template_icon} {model.jinja_template}.j2')
        lines.append('')
        lines.append(f'[dim]🌡️  {model.temperature}  📏 {model.max_tokens}[/]')
        content = '\n'.join(lines)
    return Panel(content, title=f'[bold yellow]MODEL {self.selected_model_idx + 1} CONFIG[/]', border_style='yellow' if self.mode == 'editor' else 'dim', box=box.ROUNDED, height=9)
```

### Method: `render_session_config`
**Logic & Purpose:**
```text
Render session configuration panel with enhanced info.
```

**Parameters:** `self`
**Variables Used:** `topo_str, t, s, mode_str, p_emoji, flow, content, t_emoji`
**Implementation:**
```python
def render_session_config(self) -> Panel:
    """Render session configuration panel with enhanced info."""
    s = self.session
    t = s.topology
    t_emoji = self.TOPOLOGY_EMOJI.get(t.type, '⭕')
    topo_str = f'{t_emoji} {t.type}'
    if t.type == 'star':
        topo_str = f'{t_emoji} star (center={t.center})'
    elif t.type == 'ring' and t.order:
        topo_str = f"{t_emoji} ring ({','.join(map(str, t.order))})"
    p_emoji = self.PARADIGM_EMOJI.get(s.paradigm, '🔮')
    mode_str = f'[bold red]♾️  infinite[/]' if s.infinite else f'[green]🔁 {s.rounds} rounds[/]'
    flow = self._get_flow_string()
    content = Text()
    content.append(f'Mode:     ', style='dim')
    content.append(f"{('♾️  infinite' if s.infinite else f'🔁 {s.rounds} rounds')}\n", style='bold red' if s.infinite else 'green')
    content.append(f'Topology: ', style='dim')
    content.append(f'{topo_str}\n', style='yellow')
    content.append(f'Paradigm: ', style='dim')
    content.append(f'{p_emoji} {s.paradigm}\n', style='magenta')
    if s.summarize_every:
        content.append(f'Summary:  ', style='dim')
        content.append(f'📝 every {s.summarize_every}\n', style='cyan')
    content.append(f'\n[dim]Flow:[/]\n', style='dim')
    content.append(f'[bold cyan]{flow}[/]\n')
    content.append('\n')
    content.append('[T]', style='bold yellow')
    content.append('opology ', style='dim')
    content.append('[I]', style='bold magenta')
    content.append('mport ', style='dim')
    content.append('[R]', style='bold green')
    content.append('un ', style='dim')
    content.append('[S]', style='bold blue')
    content.append('ave ', style='dim')
    content.append('[L]', style='bold cyan')
    content.append('oad ', style='dim')
    content.append('[Q]', style='bold red')
    content.append('uit', style='dim')
    return Panel(content, title='[bold green]⚙️  SESSION[/]', border_style='green', box=box.ROUNDED, height=12)
```

### Method: `_get_flow_string`
**Logic & Purpose:**
```text
Get visual flow string for current topology.
```

**Parameters:** `self`
**Variables Used:** `t, center, flow, spokes, n`
**Implementation:**
```python
def _get_flow_string(self) -> str:
    """Get visual flow string for current topology."""
    t = self.session.topology
    n = len(self.session.models)
    if n == 0:
        return '[dim]No models[/]'
    if t.type == 'ring':
        flow = ' → '.join([f'{i + 1}' for i in range(n)])
        if n > 1:
            flow += ' → 1'
        return flow
    elif t.type == 'star':
        center = t.center
        spokes = t.spokes or [i + 1 for i in range(n) if i + 1 != center]
        return f'C({center}) ⇄ ' + ' ⇄ '.join([str(s) for s in spokes])
    elif t.type == 'mesh':
        return 'All ↔ All'
    elif t.type == 'chain':
        return ' → '.join([f'{i + 1}' for i in range(n)])
    elif t.type == 'random':
        return '🎲 Random(1-' + str(n) + ')'
    elif t.type == 'tournament':
        return '🏆 Bracket'
    else:
        return t.type
```

### Method: `render_controls`
**Logic & Purpose:**
```text
Render user controls panel.
```

**Parameters:** `self`
**Variables Used:** `controls`
**Implementation:**
```python
def render_controls(self) -> Panel:
    """Render user controls panel."""
    controls = Table(box=None, show_header=False, padding=(0, 1))
    controls.add_column('', width=30)
    controls.add_column('', width=35)
    controls.add_row('[bold green]+[/] Add  [bold red]-[/] Delete  [bold yellow]C[/]opy', f'[dim]←/→[/] Model [bold cyan]{self.selected_model_idx + 1}[/]/{len(self.session.models)}')
    controls.add_row('[dim]↑/↓[/] Field  [bold magenta]E[/]dit  [bold blue]P[/]rompt', '[bold yellow]T[/]opo  [bold magenta]D[/]iagram  [dim]1-8[/] Jump')
    controls.add_row('[bold cyan]I[/]mport  [bold green]R[/]un  [bold blue]S[/]ave  [bold yellow]L[/]oad', '[bold red]Q[/]uit  [dim]Ctrl+C[/] cancel')
    return Panel(controls, title='[bold blue]🎮 CONTROLS[/]', border_style='blue', box=box.ROUNDED, height=8)
```

### Method: `render_prompt`
**Logic & Purpose:**
```text
Render initial prompt panel.
```

**Parameters:** `self`
**Variables Used:** `prompt`
**Implementation:**
```python
def render_prompt(self) -> Panel:
    """Render initial prompt panel."""
    prompt = self.session.initial_prompt or '[dim]Press [/][bold blue]P[/][dim] to set initial prompt[/]'
    if len(prompt) > 60:
        prompt = prompt[:57] + '...'
    return Panel(prompt, title='[bold magenta]💬 INITIAL PROMPT[/]', border_style='magenta', box=box.ROUNDED, height=4)
```

### Method: `render_status`
**Logic & Purpose:**
```text
Render status bar.
```

**Parameters:** `self`
**Variables Used:** `status`
**Implementation:**
```python
def render_status(self) -> Text:
    """Render status bar."""
    status = Text()
    if self.status_message:
        status.append(f'  ✨ {self.status_message}', style='bold yellow')
    else:
        status.append('  ✅ Ready', style='green')
    return status
```

### Method: `draw`
**Logic & Purpose:**
```text
Draw the full TUI.
```

**Parameters:** `self`
**Variables Used:** `layout, right_layout, left_layout`
**Implementation:**
```python
def draw(self):
    """Draw the full TUI."""
    console.clear()
    console.print(Panel('[bold cyan]🔮 CROSSTALK STUDIO V2[/] [dim]→ AI Model-to-Model Conversation Orchestrator[/]', box=box.SIMPLE, border_style='dim', padding=(0, 1)))
    console.print(self.render_header())
    layout = Layout()
    layout.split_row(Layout(name='left', ratio=3), Layout(name='right', ratio=2))
    left_layout = Layout()
    left_layout.split_column(Layout(self.render_circle_panel(), name='circle', ratio=3), Layout(self.render_controls(), name='controls', ratio=1), Layout(self.render_prompt(), name='prompt', ratio=1))
    layout['left'].update(left_layout)
    right_layout = Layout()
    right_layout.split_column(Layout(self.render_model_config(), name='model', ratio=1), Layout(self.render_session_config(), name='session', ratio=1))
    layout['right'].update(right_layout)
    console.print(layout)
    console.print(self.render_status())
    if not self.status_message:
        console.print(Panel('[dim]💡 Tip: Press [D] for detailed topology diagram  |  [T] for topology settings  |  [R] to run[/]', box=box.SIMPLE, border_style='dim', padding=(0, 1)))
```

### Method: `handle_input`
**Logic & Purpose:**
```text
Handle keyboard input.
```

**Parameters:** `self`
**Variables Used:** `key, choice, idx`
**Implementation:**
```python
def handle_input(self):
    """Handle keyboard input."""
    if ARROW_SUPPORT:
        key = readchar.readkey()
        if key == readchar.key.LEFT or key == 'h':
            self.selected_model_idx = (self.selected_model_idx - 1) % len(self.session.models)
        elif key == readchar.key.RIGHT or key == 'l':
            self.selected_model_idx = (self.selected_model_idx + 1) % len(self.session.models)
        elif key == readchar.key.UP or key == 'k':
            self.selected_field = (self.selected_field - 1) % 3
        elif key == readchar.key.DOWN or key == 'j':
            self.selected_field = (self.selected_field + 1) % 3
        elif key in '12345678':
            idx = int(key) - 1
            if idx < len(self.session.models):
                self.selected_model_idx = idx
        elif key == '+' or key == '=':
            self.add_model()
        elif key == '-' or key == '_':
            self.delete_model()
        elif key.lower() == 'c':
            self.copy_model()
        elif key.lower() == 'e' or key == readchar.key.ENTER:
            self.edit_current_field()
        elif key.lower() == 'p':
            self.edit_initial_prompt()
        elif key.lower() == 'r':
            self.run_session()
        elif key.lower() == 's':
            self.save_config()
        elif key.lower() == 'l':
            self.load_config()
        elif key.lower() == 'i':
            self.import_from_url()
        elif key.lower() == 't':
            self.edit_topology()
        elif key.lower() == 'd':
            self.show_diagram()
        elif key.lower() == 'q':
            self.running = False
    else:
        choice = input('\n→ ').strip().lower()
        if choice == 'q':
            self.running = False
```

### Method: `add_model`
**Logic & Purpose:**
```text
Add a new model slot.
```

**Parameters:** `self`
**Variables Used:** `new_slot`
**Implementation:**
```python
def add_model(self):
    """Add a new model slot."""
    if len(self.session.models) >= 8:
        self.status_message = 'Maximum 8 models'
        return
    new_slot = ModelSlot(slot_id=len(self.session.models) + 1, model_id='anthropic/claude-3-opus', jinja_template='basic')
    self.session.models.append(new_slot)
    self.selected_model_idx = len(self.session.models) - 1
    self.status_message = f'Added Model {len(self.session.models)}'
```

### Method: `delete_model`
**Logic & Purpose:**
```text
Delete the selected model.
```

**Parameters:** `self`
**Implementation:**
```python
def delete_model(self):
    """Delete the selected model."""
    if len(self.session.models) <= 1:
        self.status_message = 'Must have at least 1 model'
        return
    del self.session.models[self.selected_model_idx]
    for i, m in enumerate(self.session.models):
        m.slot_id = i + 1
    if self.selected_model_idx >= len(self.session.models):
        self.selected_model_idx = len(self.session.models) - 1
    self.status_message = 'Model deleted'
```

### Method: `copy_model`
**Logic & Purpose:**
```text
Copy the current model to a new slot.
```

**Parameters:** `self`
**Variables Used:** `new_slot, current`
**Implementation:**
```python
def copy_model(self):
    """Copy the current model to a new slot."""
    if len(self.session.models) >= 8:
        self.status_message = 'Maximum 8 models'
        return
    current = self.current_model
    if current:
        new_slot = ModelSlot(slot_id=len(self.session.models) + 1, model_id=current.model_id, system_prompt_file=current.system_prompt_file, system_prompt_inline=current.system_prompt_inline, jinja_template=current.jinja_template, temperature=current.temperature, max_tokens=current.max_tokens)
        self.session.models.append(new_slot)
        self.selected_model_idx = len(self.session.models) - 1
        self.status_message = f'Copied to Model {len(self.session.models)}'
```

### Method: `edit_current_field`
**Logic & Purpose:**
```text
Edit the currently selected field.
```

**Parameters:** `self`
**Variables Used:** `prompt, path, templates, new_id, marker, choice, idx, model`
**Implementation:**
```python
def edit_current_field(self):
    """Edit the currently selected field."""
    console.clear()
    model = self.current_model
    if not model:
        return
    if self.selected_field == 0:
        console.print('[bold cyan]Edit Model ID[/]')
        console.print('[dim]Enter full model ID (e.g., anthropic/claude-3-opus)[/]')
        new_id = Prompt.ask('Model', default=model.model_id)
        model.model_id = new_id
        self.status_message = 'Model updated'
    elif self.selected_field == 1:
        console.print('[bold cyan]Edit System Prompt[/]')
        console.print('[1] Enter file path')
        console.print('[2] Enter inline prompt')
        console.print('[0] Cancel')
        choice = Prompt.ask('Choice', choices=['0', '1', '2'], default='0')
        if choice == '1':
            path = Prompt.ask('File path')
            if Path(path).exists():
                model.system_prompt_file = path
                model.system_prompt_inline = ''
                self.status_message = 'System prompt file set'
            else:
                self.status_message = 'File not found'
        elif choice == '2':
            prompt = Prompt.ask('System prompt')
            model.system_prompt_inline = prompt
            model.system_prompt_file = ''
            self.status_message = 'System prompt set'
    elif self.selected_field == 2:
        console.print('[bold cyan]Select Jinja Template[/]')
        templates = list(DEFAULT_TEMPLATES.keys())
        for i, t in enumerate(templates, 1):
            marker = '▶' if t == model.jinja_template else ' '
            console.print(f'  {marker} [{i}] {t}')
        choice = Prompt.ask('Template number', default='1')
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                model.jinja_template = templates[idx]
                self.status_message = f'Template: {model.jinja_template}'
        except ValueError:
            pass
```

### Method: `edit_initial_prompt`
**Logic & Purpose:**
```text
Edit the initial prompt sent to the first model.
```

**Parameters:** `self`
**Variables Used:** `prompt`
**Implementation:**
```python
def edit_initial_prompt(self):
    """Edit the initial prompt sent to the first model."""
    console.clear()
    console.print('[bold magenta]Set Initial Prompt[/]')
    console.print('[dim]This is sent to the first model to start the conversation[/]\n')
    prompt = Prompt.ask('Initial prompt', default=self.session.initial_prompt)
    self.session.initial_prompt = prompt
    self.status_message = 'Initial prompt set'
```

### Method: `edit_rounds`
**Logic & Purpose:**
```text
Edit number of rounds.
```

**Parameters:** `self`
**Variables Used:** `rounds`
**Implementation:**
```python
def edit_rounds(self):
    """Edit number of rounds."""
    try:
        rounds = int(Prompt.ask('Rounds', default=str(self.session.rounds)))
        self.session.rounds = max(1, min(100, rounds))
    except ValueError:
        pass
```

### Method: `edit_topology`
**Logic & Purpose:**
```text
Edit topology and session settings.
```

**Parameters:** `self`
**Variables Used:** `rounds, time_limit, order_str, p_idx, t, s, center, p_choice, new_type, every, marker, choice, idx, cost_limit, topologies, paradigms`
**Implementation:**
```python
def edit_topology(self):
    """Edit topology and session settings."""
    console.clear()
    console.print('[bold cyan]━━━ TOPOLOGY & SESSION SETTINGS ━━━[/]\n')
    s = self.session
    t = s.topology
    console.print('[bold]Topology Type:[/]')
    topologies = ['ring', 'star', 'mesh', 'chain', 'random']
    for i, top in enumerate(topologies, 1):
        marker = '▶' if top == t.type else ' '
        console.print(f'  {marker} [{i}] {top}')
    console.print(f'\n[bold]Current:[/] {t.type}')
    console.print('')
    console.print('[bold]Session Mode:[/]')
    console.print(f'  [6] Rounds: {s.rounds}' + (' (active)' if not s.infinite else ''))
    console.print(f"  [7] Infinite mode: {('ON' if s.infinite else 'OFF')}")
    console.print(f'\n[bold]Other Settings:[/]')
    console.print(f'  [8] Paradigm: {s.paradigm}')
    console.print(f"  [9] Summarize every: {s.summarize_every or 'disabled'}")
    console.print('  [0] Back\n')
    choice = Prompt.ask('Select option', default='0')
    try:
        idx = int(choice)
        if 1 <= idx <= 5:
            new_type = topologies[idx - 1]
            t.type = new_type
            self.status_message = f'Topology: {new_type}'
            if new_type == 'star':
                console.print(f'\n[bold yellow]Star Topology Config[/]')
                console.print(f"Models: {', '.join((f'AI{m.slot_id}' for m in s.models))}")
                center = Prompt.ask('Center model (1-8)', default=str(t.center))
                try:
                    t.center = int(center)
                except ValueError:
                    pass
            elif new_type == 'ring':
                console.print(f'\n[bold yellow]Ring Topology Config[/]')
                console.print(f"Models: {', '.join((f'AI{m.slot_id}' for m in s.models))}")
                order_str = Prompt.ask('Custom order (e.g., 1,3,2 or blank for default)', default=','.join(map(str, t.order)) if t.order else '')
                if order_str.strip():
                    t.order = [int(x.strip()) for x in order_str.split(',') if x.strip()]
                else:
                    t.order = []
        elif idx == 6:
            rounds = Prompt.ask('Number of rounds', default=str(s.rounds))
            try:
                s.rounds = max(1, min(1000, int(rounds)))
                s.infinite = False
                self.status_message = f'Set to {s.rounds} rounds'
            except ValueError:
                pass
        elif idx == 7:
            s.infinite = not s.infinite
            self.status_message = f"Infinite mode: {('ON' if s.infinite else 'OFF')}"
            if s.infinite:
                console.print('\n[bold yellow]Stop Conditions[/]')
                time_limit = Prompt.ask('Max time (seconds, 0=none)', default=str(s.stop_conditions.max_time_seconds))
                cost_limit = Prompt.ask('Max cost ($, 0=none)', default=str(s.stop_conditions.max_cost_dollars))
                try:
                    s.stop_conditions.max_time_seconds = int(time_limit)
                    s.stop_conditions.max_cost_dollars = float(cost_limit)
                except ValueError:
                    pass
        elif idx == 8:
            console.print('\n[bold]Paradigms:[/]')
            paradigms = ['relay', 'memory', 'debate', 'report']
            for i, p in enumerate(paradigms, 1):
                marker = '▶' if p == s.paradigm else ' '
                console.print(f'  {marker} [{i}] {p}')
            p_choice = Prompt.ask('Select paradigm', default='1')
            try:
                p_idx = int(p_choice) - 1
                if 0 <= p_idx < len(paradigms):
                    s.paradigm = paradigms[p_idx]
                    self.status_message = f'Paradigm: {s.paradigm}'
            except ValueError:
                pass
        elif idx == 9:
            every = Prompt.ask('Summarize every N rounds (0=disabled)', default=str(s.summarize_every))
            try:
                s.summarize_every = max(0, int(every))
                self.status_message = f'Summarize: every {s.summarize_every}' if s.summarize_every else 'Summarize: disabled'
            except ValueError:
                pass
    except ValueError:
        pass
```

### Method: `show_diagram`
**Logic & Purpose:**
```text
Show detailed topology diagram in a modal view.
```

**Parameters:** `self`
**Variables Used:** `prompt_display, template, t, s, temp, diagram, paradigms`
**Implementation:**
```python
def show_diagram(self):
    """Show detailed topology diagram in a modal view."""
    console.clear()
    console.print(Panel('[bold cyan]✨ CROSSTALK TOPOLOGY DIAGRAM[/]', border_style='cyan', box=box.DOUBLE))
    t = self.session.topology
    s = self.session
    console.print(f'\n[dim]Configuration:[/]')
    console.print(f'  [bold yellow]Topology:[/] {t.type}')
    console.print(f'  [bold magenta]Paradigm:[/] {s.paradigm}')
    console.print(f'  [bold green]Models:[/] {len(s.models)}')
    console.print(f"  [bold blue]Rounds:[/] {(s.rounds if not s.infinite else 'Infinite')}")
    console.print(f'\n[dim]Model Configuration:[/]')
    for i, model in enumerate(s.models, 1):
        template = f'[bold cyan]{model.jinja_template}[/]'
        temp = model.temperature
        prompt_display = model.system_prompt[:50] + '...' if model.system_prompt else '(default)'
        console.print(f'  AI{i}: {model.model_id}')
        console.print(f'    Template: {template} | Temp: {temp}')
        if model.system_prompt:
            console.print(f'    Prompt: [dim]{prompt_display}[/]')
    console.print(f'\n[dim]Visual Flow Diagram:[/]')
    diagram = self._render_ascii_diagram()
    console.print(Panel(diagram, title='[bold magenta]Flow Diagram[/]', border_style='magenta', box=box.ROUNDED))
    console.print(f'\n[dim]Paradigm Explanation:[/]')
    paradigms = {'relay': 'Sequential passing: each model sees only the immediately previous response, creating a chain of evolving perspectives', 'memory': 'Full context: all models see the complete conversation history at every step', 'debate': "Critical exchange: models challenge each other's responses, refining arguments", 'report': 'Synthesis: each model summarizes before passing to the next, creating distilled insights'}
    console.print(f"[yellow]{paradigms.get(s.paradigm, 'Unknown paradigm')}[/]")
    input('\n[dim]Press Enter to continue...[/]')
```

### Method: `_render_ascii_diagram`
**Logic & Purpose:**
```text
Create a detailed ASCII art diagram of the current topology.
```

**Parameters:** `self`
**Variables Used:** `color_map, t, color, models`
**Implementation:**
```python
def _render_ascii_diagram(self) -> str:
    """Create a detailed ASCII art diagram of the current topology."""
    t = self.session.topology
    models = self.session.models
    if len(models) == 0:
        return '[red]No models configured[/]'
    color_map = {'relay': 'cyan', 'memory': 'green', 'debate': 'magenta', 'report': 'yellow'}
    color = color_map.get(self.session.paradigm, 'white')
    if t.type == 'ring':
        return self._ring_diagram(color)
    elif t.type == 'star':
        return self._star_diagram(color)
    elif t.type == 'mesh':
        return self._mesh_diagram(color)
    elif t.type == 'chain':
        return self._chain_diagram(color)
    else:
        return f'[dim]Custom topology: {t.type}[/]'
```

### Method: `_ring_diagram`
**Logic & Purpose:**
```text
Create ring diagram.
```

**Parameters:** `self, color`
**Variables Used:** `next_i, y, canvas, nx, x, result, mid_y, radius, angle, lines, next_angle, ny, mid_x, n, label`
**Implementation:**
```python
def _ring_diagram(self, color: str) -> str:
    """Create ring diagram."""
    n = len(self.session.models)
    if n <= 1:
        return '[dim]Single model ring[/]'
    radius = 8
    lines = []
    center_x, center_y = (25, 7)
    import math
    canvas = [[' ' for _ in range(50)] for _ in range(15)]
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        label = f'{i + 1}'
        if 0 <= y < 15 and 0 <= x < 50:
            canvas[y][x] = f'[{color}]{label}[/]'
        next_i = (i + 1) % n
        next_angle = 2 * math.pi * next_i / n - math.pi / 2
        nx = int(center_x + radius * math.cos(next_angle))
        ny = int(center_y + radius * math.sin(next_angle))
        mid_x = (x + nx) // 2
        mid_y = (y + ny) // 2
        if 0 <= mid_y < 15 and 0 <= mid_x < 50:
            canvas[mid_y][mid_x] = f'[{color}]→[/]'
    result = []
    for row in canvas:
        result.append(''.join(row))
    return '\n'.join(result)
```

### Method: `_star_diagram`
**Logic & Purpose:**
```text
Create star diagram.
```

**Parameters:** `self, color`
**Variables Used:** `lines, spokes, center`
**Implementation:**
```python
def _star_diagram(self, color: str) -> str:
    """Create star diagram."""
    center = self.session.topology.center
    spokes = self.session.topology.spokes or [i + 1 for i in range(len(self.session.models)) if i + 1 != center]
    lines = []
    lines.append(f'  [bold {color}]CENTER({center})[/]')
    lines.append('    │')
    for spoke in spokes:
        lines.append(f'    ↓  [dim]AI{spoke}[/]  ↑')
    return '\n'.join(lines)
```

### Method: `_mesh_diagram`
**Logic & Purpose:**
```text
Create mesh diagram.
```

**Parameters:** `self, color`
**Variables Used:** `lines, n, peers`
**Implementation:**
```python
def _mesh_diagram(self, color: str) -> str:
    """Create mesh diagram."""
    n = len(self.session.models)
    lines = []
    for i in range(n):
        peers = [j + 1 for j in range(n) if j != i]
        lines.append(f'[bold {color}]AI{i + 1}[/] ↔ ' + ' ↔ '.join([str(p) for p in peers]))
    return '\n'.join(lines)
```

### Method: `_chain_diagram`
**Logic & Purpose:**
```text
Create chain diagram.
```

**Parameters:** `self, color`
**Variables Used:** `flow`
**Implementation:**
```python
def _chain_diagram(self, color: str) -> str:
    """Create chain diagram."""
    flow = ' → '.join([f'[bold {color}]{i + 1}[/]' for i in range(len(self.session.models))])
    return flow
```

### Method: `save_config`
**Logic & Purpose:**
```text
Save current configuration to a preset file.
```

**Parameters:** `self`
**Variables Used:** `filename, name, config`
**Implementation:**
```python
def save_config(self):
    """Save current configuration to a preset file."""
    console.clear()
    console.print('[bold green]Save Configuration[/]\n')
    name = Prompt.ask('Preset name', default='my_config')
    filename = PRESETS_DIR / f'{name}.json'
    config = {'models': [asdict(m) for m in self.session.models], 'rounds': self.session.rounds, 'paradigm': self.session.paradigm, 'topology': asdict(self.session.topology), 'initial_prompt': self.session.initial_prompt, 'infinite': self.session.infinite, 'stop_conditions': asdict(self.session.stop_conditions), 'summarize_every': self.session.summarize_every, 'created_at': datetime.now().isoformat()}
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    self.status_message = f'Saved: {filename.name}'
```

### Method: `load_config`
**Logic & Purpose:**
```text
Load a configuration preset.
```

**Parameters:** `self`
**Variables Used:** `config, choice, idx, presets`
**Implementation:**
```python
def load_config(self):
    """Load a configuration preset."""
    console.clear()
    console.print('[bold green]Load Configuration[/]\n')
    presets = list(PRESETS_DIR.glob('*.json'))
    if not presets:
        self.status_message = 'No saved presets'
        return
    for i, p in enumerate(presets, 1):
        console.print(f'  [{i}] {p.stem}')
    choice = Prompt.ask('Select preset', default='1')
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(presets):
            with open(presets[idx]) as f:
                config = json.load(f)
            self.session.models = [ModelSlot(**m) for m in config.get('models', [])]
            self.session.rounds = config.get('rounds', 5)
            self.session.paradigm = config.get('paradigm', 'relay')
            self.session.initial_prompt = config.get('initial_prompt', '')
            self.session.infinite = config.get('infinite', False)
            self.session.summarize_every = config.get('summarize_every', 0)
            if 'topology' in config:
                self.session.topology = TopologyConfig(**config['topology'])
            if 'stop_conditions' in config:
                self.session.stop_conditions = StopConditions(**config['stop_conditions'])
            self.selected_model_idx = 0
            self.status_message = f'Loaded: {presets[idx].stem}'
    except (ValueError, json.JSONDecodeError) as e:
        self.status_message = f'Load error: {e}'
```

### Method: `import_from_url`
**Logic & Purpose:**
```text
Import configuration from a Dreams of Electric Mind URL.
```

**Parameters:** `self`
**Variables Used:** `url, session_data, config`
**Implementation:**
```python
def import_from_url(self):
    """Import configuration from a Dreams of Electric Mind URL."""
    console.clear()
    console.print('[bold magenta]Import from Infinite Backrooms[/]\n')
    console.print('[dim]Paste a URL from dreams-of-an-electric-mind.webflow.io[/]')
    console.print('[dim]Example: https://dreams-of-an-electric-mind.webflow.io/dreams/conversation-xxx[/]\n')
    url = Prompt.ask('URL', default='')
    if not url:
        self.status_message = 'Import cancelled'
        return
    console.print('\n[yellow]Fetching configuration...[/]')
    try:
        from src.cli.backrooms_importer import fetch_backrooms_url, convert_to_crosstalk_session
        config = asyncio.run(fetch_backrooms_url(url))
        if not config:
            self.status_message = 'Could not parse configuration from URL'
            input('\nPress Enter to continue...')
            return
        session_data = convert_to_crosstalk_session(config)
        self.session.models = session_data['models']
        self.session.initial_prompt = session_data.get('initial_prompt', '')
        self.session.paradigm = session_data.get('paradigm', 'relay')
        self.session.rounds = session_data.get('rounds', 10)
        self.selected_model_idx = 0
        console.print(f'\n[green]✓ Imported {len(config.actors)} actors from {config.scenario_name}[/]')
        for i, actor in enumerate(config.actors):
            console.print(f'  AI{i + 1}: {actor.name} → {actor.model_id}')
        self.status_message = f'Imported: {config.scenario_name}'
        input('\nPress Enter to continue...')
    except ImportError as e:
        console.print(f'[red]Import module not found: {e}[/]')
        input('\nPress Enter to continue...')
    except Exception as e:
        console.print(f'[red]Import error: {e}[/]')
        import traceback
        traceback.print_exc()
        input('\nPress Enter to continue...')
```

### Method: `run_session`
**Logic & Purpose:**
```text
Execute the crosstalk session.
```

**Parameters:** `self`
**Implementation:**
```python
def run_session(self):
    """Execute the crosstalk session."""
    if not self.session.initial_prompt:
        self.status_message = 'Set initial prompt first [P]'
        return
    console.clear()
    console.print(Panel(f'[bold yellow]Starting Crosstalk Session...[/]\n\nModels: {len(self.session.models)}\nRounds: {self.session.rounds}\nParadigm: {self.session.paradigm}', title='🔮 RUNNING', border_style='yellow'))
    try:
        from src.cli.crosstalk_engine import run_crosstalk
        asyncio.run(run_crosstalk(self.session))
    except ImportError:
        console.print('[red]Crosstalk engine not found. Creating placeholder...[/]')
        input('\nPress Enter to continue...')
    except Exception as e:
        console.print(f'[red]Error: {e}[/]')
        input('\nPress Enter to continue...')
```

### Method: `run`
**Logic & Purpose:**
```text
Main loop.
```

**Parameters:** `self`
**Implementation:**
```python
def run(self):
    """Main loop."""
    while self.running:
        try:
            self.draw()
            self.handle_input()
        except KeyboardInterrupt:
            self.running = False
    console.clear()
    console.print('[dim]Crosstalk Studio closed.[/]')
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Entry point for Crosstalk Studio.
```

**Parameters:** ``
**Variables Used:** `studio`
**Implementation:**
```python
def main():
    """Entry point for Crosstalk Studio."""
    try:
        studio = CrosstalkStudio()
        studio.run()
    except Exception as e:
        console.print(f'[red]Fatal error: {e}[/]')
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

---


