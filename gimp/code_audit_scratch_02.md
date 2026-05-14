# File Audit: /home/cheta/code/claude-code-proxy/cli/setup.py
**Path**: `/home/cheta/code/claude-code-proxy/cli/setup.py`

**Module Overview**: 
```text
Setup script for Claude Proxy CLI

Usage:
    pip install .
    claude-proxy --help
```

## Dependencies & Imports
setuptools.setup, setuptools.find_packages


# File Audit: /home/cheta/code/claude-code-proxy/src/main.py
**Path**: `/home/cheta/code/claude-code-proxy/src/main.py`

## Global Presets & Variables
- `app` = `FastAPI(title='The Ultimate Proxy', version='2.1.0', lifespan=lifespan)`
- `svelte_build_dir` = `Path(__file__).parent.parent / 'web-ui' / 'build'`
- `legacy_static_dir` = `Path(__file__).parent / 'static'`

## Dependencies & Imports
fastapi.FastAPI, fastapi.staticfiles.StaticFiles, fastapi.responses.FileResponse, src.api.endpoints.router, src.api.web_ui.router, src.api.websocket_dashboard.router, src.api.websocket_logs.router, src.api.analytics.router, src.api.billing.router, src.api.benchmarks.router, src.api.users.router, src.api.openai_endpoints.router, src.api.docs_routes.router, src.api.system_monitor.router, src.api.websocket_live.router, src.api.websocket_live.start_live_metrics, src.api.websocket_live.stop_live_metrics, src.api.alerts.router, src.api.reports.router, src.api.predictive.router, src.api.integrations.router, src.api.dashboards.router, src.api.users_rbac.router, src.api.providers.router, src.api.graphql_schema.get_graphql_router, uvicorn, sys, os, pathlib.Path, src.core.config.config, contextlib.asynccontextmanager

## Feature Function: `lifespan`
**Logic & Purpose:**
```text
Lifespan events for startup and shutdown.
```

**Parameters:** `app`
**Variables Used:** `conn, cursor, scheduler_task, col_defs`
**Implementation:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    try:
        import sqlite3
        conn = sqlite3.connect(config.usage_tracking_db_path)
        cursor = conn.cursor()

        def create_table_if_not_exists(table_name: str, columns: dict):
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                col_defs = ', '.join((f'{k} {v}' for k, v in columns.items()))
                cursor.execute(f'CREATE TABLE {table_name} ({col_defs})')
                conn.commit()
                print(f'✅ Created table: {table_name}')
        create_table_if_not_exists('api_requests', {'id': 'INTEGER PRIMARY KEY', 'timestamp': 'TEXT', 'model': 'TEXT', 'input_tokens': 'INTEGER', 'output_tokens': 'INTEGER', 'cost': 'REAL', 'duration_ms': 'INTEGER', 'status': 'TEXT', 'error': 'TEXT', 'request_count': 'INTEGER DEFAULT 1'})
        create_table_if_not_exists('alert_rules', {'id': 'TEXT PRIMARY KEY', 'name': 'TEXT', 'description': 'TEXT', 'condition_json': 'TEXT', 'condition_logic': 'TEXT', 'actions_json': 'TEXT', 'cooldown_minutes': 'INTEGER', 'priority': 'INTEGER', 'time_window': 'INTEGER', 'is_active': 'INTEGER', 'last_triggered': 'TEXT', 'trigger_count': 'INTEGER', 'created_at': 'TEXT', 'created_by': 'TEXT', 'muted_until': 'TEXT'})
        create_table_if_not_exists('alert_history', {'id': 'TEXT PRIMARY KEY', 'rule_id': 'TEXT', 'rule_name': 'TEXT', 'triggered_at': 'TEXT', 'severity': 'TEXT', 'alert_data_json': 'TEXT'})
        create_table_if_not_exists('scheduled_reports', {'id': 'TEXT PRIMARY KEY', 'template_id': 'TEXT', 'name': 'TEXT', 'frequency': 'TEXT', 'recipients': 'TEXT', 'timezone': 'TEXT', 'is_active': 'INTEGER', 'next_run': 'TEXT', 'last_run': 'TEXT', 'delivery_method': "TEXT DEFAULT 'email'", 'config': 'TEXT'})

        def add_column_if_not_exists(table: str, column: str, definition: str):
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
                conn.commit()
                print(f'✅ Added column {column} to {table}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    pass
                else:
                    raise
        add_column_if_not_exists('api_requests', 'request_count', 'INTEGER DEFAULT 1')
        add_column_if_not_exists('alert_rules', 'actions_json', 'TEXT DEFAULT \'{"channels": ["in_app"]}\'')
        add_column_if_not_exists('scheduled_reports', 'delivery_method', "TEXT DEFAULT 'email'")
        add_column_if_not_exists('alert_rules', 'created_by', 'TEXT')
        add_column_if_not_exists('alert_rules', 'created_at', 'TEXT')
        add_column_if_not_exists('alert_rules', 'muted_until', 'TEXT')
        conn.close()
    except Exception as e:
        print(f'❌  Failed to run DB migrations: {e}')
    try:
        await start_live_metrics()
        print('✅ Live metrics system started')
    except Exception as e:
        print(f'⚠️  Failed to start live metrics: {e}')
    try:
        from src.services.notifications import notification_service
        await notification_service.initialize()
        print('✅ Notification service initialized')
    except Exception as e:
        print(f'⚠️  Failed to initialize notification service: {e}')
    try:
        from src.services.user_management import user_service, create_default_admin
        user_service.initialize()
        create_default_admin()
        print('✅ User management initialized')
    except Exception as e:
        print(f'⚠️  Failed to initialize user management: {e}')
    try:
        from src.services.alert_engine import alert_engine
        await alert_engine.start()
        print('✅ Alert engine started')
    except Exception as e:
        print(f'⚠️  Failed to start alert engine: {e}')
    try:
        from src.services.advanced_scheduler import advanced_scheduler
        import asyncio
        scheduler_task = asyncio.create_task(advanced_scheduler.start())
        print('✅ Advanced scheduler started')
    except Exception as e:
        print(f'⚠️  Failed to start advanced scheduler: {e}')
    yield
    try:
        from src.services.advanced_scheduler import advanced_scheduler
        await advanced_scheduler.stop()
        print('✅ Advanced scheduler stopped')
    except Exception as e:
        print(f'⚠️  Failed to stop advanced scheduler: {e}')
    try:
        from src.services.alert_engine import alert_engine
        await alert_engine.stop()
        print('✅ Alert engine stopped')
    except Exception as e:
        print(f'⚠️  Failed to stop alert engine: {e}')
    try:
        from src.services.notifications import notification_service
        await notification_service.close()
        print('✅ Notification service closed')
    except Exception as e:
        print(f'⚠️  Failed to close notification service: {e}')
    try:
        await stop_live_metrics()
        print('✅ Live metrics system stopped')
    except Exception as e:
        print(f'⚠️  Failed to stop live metrics: {e}')
```

---

## Feature Function: `live_tracking_middleware`
**Logic & Purpose:**
```text
Add live request tracking
```

**Parameters:** `request, call_next`
**Variables Used:** `start_time, metrics, response, duration_ms`
**Implementation:**
```python
@app.middleware('http')
async def live_tracking_middleware(request, call_next):
    """Add live request tracking"""
    from src.api.websocket_live import broadcast_request_event
    from datetime import datetime
    import time
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    if request.url.path.startswith('/v1/chat') and hasattr(request.state, 'metrics'):
        metrics = request.state.metrics
        try:
            await broadcast_request_event({'path': request.url.path, 'method': request.method, 'duration_ms': duration_ms, 'status': 'success' if response.status_code < 400 else 'error', 'model': metrics.get('model', 'unknown'), 'cost': metrics.get('cost', 0), 'tokens': metrics.get('total_tokens', 0)})
        except Exception as _e:
            pass
    return response
```

---

## Feature Function: `serve_config_ui`
**Logic & Purpose:**
```text
Serve the web UI at /config path for convenience
```

**Parameters:** ``
**Variables Used:** `index_file`
**Implementation:**
```python
@app.get('/config')
async def serve_config_ui():
    """Serve the web UI at /config path for convenience"""
    if svelte_build_dir.exists():
        index_file = svelte_build_dir / 'index.html'
    else:
        index_file = legacy_static_dir / 'index.html'
    if index_file.exists():
        return FileResponse(index_file)
    return {'message': 'Web UI not available'}
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main entry point with optional environment updates.
```

**Parameters:** `env_updates, skip_validation`
**Variables Used:** `limits, scraper_path, msg, _reasoning_dir, dashboard_thread, json_data, valid_levels, models_dir, model_limits, _NOISE, wizard, env_key, _access_logger, json_path, enable_dashboard, log_level, _pruned, _cutoff, validation_passed, models, response`
**Implementation:**
```python
def main(env_updates: dict=None, skip_validation: bool=False):
    """Main entry point with optional environment updates."""
    if env_updates:
        for key, value in env_updates.items():
            env_key = key.replace('CLAUDE_', '')
            os.environ[env_key] = value
        config.__init__()
    enable_dashboard = '--dashboard' in sys.argv or config.enable_dashboard
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print('Claude-to-OpenAI API Proxy v1.0.0')
        print('')
        print('Usage: python src/main.py [--dashboard]')
        print('')
        print('Options:')
        print('  --dashboard  Enable terminal dashboard with live metrics')
        print('')
        print('Required environment variables:')
        print('  OPENAI_API_KEY - Your OpenAI API key')
        print('')
        print('Optional environment variables:')
        print('  PROXY_AUTH_KEY - Expected client API key for proxy validation')
        print('                   If set, clients must provide this exact key')
        print('  ENABLE_LEGACY_PROXY_AUTH=true')
        print('                   Re-enable legacy ANTHROPIC_API_KEY proxy auth behavior')
        print(f'  OPENAI_BASE_URL - OpenAI API base URL (default: https://api.openai.com/v1)')
        print(f'  BIG_MODEL - Model for opus requests (default: gpt-4o)')
        print(f'  MIDDLE_MODEL - Model for sonnet requests (default: gpt-4o)')
        print(f'  SMALL_MODEL - Model for haiku requests (default: gpt-4o-mini)')
        print(f'  HOST - Server host (default: 0.0.0.0)')
        print(f'  PORT - Server port (default: 8082)')
        print(f'  LOG_LEVEL - Logging level (default: WARNING)')
        print(f'  MAX_TOKENS_LIMIT - Token limit (default: 131072)')
        print(f'  MIN_TOKENS_LIMIT - Minimum token limit (default: 100)')
        print(f'  REQUEST_TIMEOUT - Request timeout in seconds (default: 90)')
        print('')
        print('Dashboard environment variables:')
        print(f'  ENABLE_DASHBOARD - Enable terminal dashboard (default: false)')
        print(f'  DASHBOARD_LAYOUT - Layout: default, compact, detailed (default: default)')
        print(f'  DASHBOARD_REFRESH - Refresh rate in seconds (default: 0.5)')
        print(f'  DASHBOARD_WATERFALL_SIZE - Completed requests to show (default: 20)')
        print(f'  TRACK_USAGE - Enable usage tracking (default: true if dashboard enabled)')
        print(f'  COMPACT_LOGGER - Reduce console noise (default: true if dashboard enabled)')
        print('')
        print('Model mapping:')
        print(f'  Claude haiku models -> {config.small_model}')
        print(f'  Claude sonnet/opus models -> {config.big_model}')
        sys.exit(0)
    try:
        from src.services.models.openrouter_fetcher import startup_refresh
        startup_refresh()
    except Exception as e:
        print(f'⚠️  OpenRouter model fetch failed: {e}')
    try:
        import asyncio
        import json
        scraper_path = Path(__file__).parent.parent / 'scripts' / 'maintenance' / 'scrape_openrouter_models.py'
        if scraper_path.exists():
            sys.path.insert(0, str(scraper_path.parent))
            from scrape_openrouter_models import fetch_openrouter_models, parse_model_limits
            models = asyncio.run(fetch_openrouter_models())
            if models:
                model_limits = []
                for model in models:
                    limits = parse_model_limits(model)
                    if limits['model_id'] and limits['context_limit'] > 0:
                        model_limits.append(limits)
                models_dir = Path(__file__).parent.parent / 'models'
                models_dir.mkdir(exist_ok=True)
                json_path = models_dir / 'model_limits.json'
                json_data = {item['model_id']: {'context': item['context_limit'], 'output': item['output_limit'], 'name': item['name']} for item in model_limits}
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2)
    except Exception as e:
        pass
    from src.services.logging.startup_display import print_startup_banner
    from src.services.logging.compact_logger import CompactLogger
    from src.services.models.provider_detector import validate_provider_configuration
    print_startup_banner(config)
    if not skip_validation:
        from src.core.validator import validate_config_on_startup
        validation_passed = validate_config_on_startup(strict=False)
        if not validation_passed:
            print('\n💡 Configuration issues detected!')
            if sys.stdin.isatty() and '--no-wizard' not in sys.argv:
                try:
                    response = input('Would you like to run the setup wizard now? [Y/n]: ').strip().lower()
                    if response in ['', 'y', 'yes']:
                        print('\n🧙 Launching Setup Wizard...\n')
                        from src.cli.wizard import SetupWizard
                        wizard = SetupWizard()
                        wizard.run()
                        print('\n🔄 Reloading configuration...')
                        from dotenv import load_dotenv
                        load_dotenv(override=True)
                        config.__init__()
                        validation_passed = validate_config_on_startup(strict=False)
                        if not validation_passed:
                            print('\n❌ Configuration still has issues. Please check .env manually.')
                            sys.exit(1)
                    else:
                        print("\n💡 Run 'python start_proxy.py --setup' to fix configuration issues")
                        print('💡 Or use --skip-validation to bypass this check')
                        sys.exit(1)
                except (EOFError, KeyboardInterrupt):
                    print('\n\n❌ Setup cancelled.')
                    sys.exit(1)
            else:
                print("\n💡 Run 'python start_proxy.py --setup' to fix configuration issues")
                print('💡 Or use --skip-validation to bypass this check')
                sys.exit(1)
    log_level = config.log_level.split()[0].lower()
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'
    if enable_dashboard:
        import threading
        from src.dashboard.terminal_dashboard import terminal_dashboard
        from src.dashboard.dashboard_hooks import dashboard_hooks
        print('\n🎨 Starting Terminal Dashboard...')
        print('   Dashboard will display live metrics and request flow')
        print('   Press Ctrl+C to stop\n')
        dashboard_hooks.enable()
        dashboard_thread = threading.Thread(target=terminal_dashboard.start, daemon=True)
        dashboard_thread.start()
        import time
        time.sleep(0.5)
    import logging as _logging

    class _QuietPollFilter(_logging.Filter):
        """Drop access-log records for high-frequency polling endpoints."""
        _NOISE = {'/health', '/api/stats', '/api/system/health'}

        def filter(self, record: _logging.LogRecord) -> bool:
            msg = record.getMessage()
            return not any((ep in msg for ep in self._NOISE))
    _access_logger = _logging.getLogger('uvicorn.access')
    _access_logger.addFilter(_QuietPollFilter())
    try:
        from pathlib import Path as _Path
        import time as _time
        _reasoning_dir = _Path('~/.cache/claude-code-proxy/reasoning').expanduser()
        if _reasoning_dir.is_dir():
            _cutoff = _time.time() - 7 * 86400
            _pruned = 0
            for _f in _reasoning_dir.glob('*.log'):
                try:
                    if _f.stat().st_mtime < _cutoff:
                        _f.unlink()
                        _pruned += 1
                except OSError:
                    pass
            if _pruned:
                _logging.getLogger(__name__).info(f'Pruned {_pruned} reasoning log(s) older than 7 days')
    except Exception as _prune_err:
        _logging.getLogger(__name__).debug(f'Reasoning log prune skipped: {_prune_err}')
    try:
        uvicorn.run('src.main:app', host=config.host, port=config.port, log_level=log_level, reload=False)
    finally:
        if enable_dashboard:
            terminal_dashboard.stop()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/__init__.py`

**Module Overview**: 
```text
Claude Code Proxy

A proxy server that enables Claude Code to work with OpenAI-compatible API providers.
```

## Global Presets & Variables
- `__version__` = `'1.0.0'`
- `__author__` = `'Claude Code Proxy'`

## Dependencies & Imports
dotenv.load_dotenv


# File Audit: /home/cheta/code/claude-code-proxy/src/core/proxy_chain.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/proxy_chain.py`

**Module Overview**: 
```text
Proxy Chain Configuration

Manages the ordered list of upstream proxies that Claude Code Proxy routes through.
Each entry in the chain is an HTTP service or CLI wrapper. The chain defines topology:

  Client → :8082 (this proxy) → chain[0] → chain[1] → ... → AI provider

Chain is stored in config/proxy_chain.json (path overridable via PROXY_CHAIN_FILE env).
```

## Global Presets & Variables
- `DEFAULT_CHAIN_FILE` = `Path(__file__).parent.parent.parent / 'config' / 'proxy_chain.json'`

## Dependencies & Imports
__future__.annotations, json, os, subprocess, dataclasses.dataclass, dataclasses.field, dataclasses.asdict, pathlib.Path, typing.Optional, urllib.parse.urlparse

## Feature Class: `ProxyEntry`
**Description:**
```text
A single entry in the proxy chain.
```

### Method: `effective_auth_key`
**Logic & Purpose:**
```text
Resolve auth key — expand ${ENV_VAR} references.
```

**Parameters:** `self`
**Variables Used:** `env_name`
**Implementation:**
```python
def effective_auth_key(self) -> str:
    """Resolve auth key — expand ${ENV_VAR} references."""
    if not self.auth_key:
        return ''
    if self.auth_key.startswith('${') and self.auth_key.endswith('}'):
        env_name = self.auth_key[2:-1]
        return os.environ.get(env_name, '')
    return self.auth_key
```

### Method: `is_http`
**Parameters:** `self`
**Implementation:**
```python
@property
def is_http(self) -> bool:
    return self.type == 'http' and bool(self.url)
```

### Method: `display_url`
**Parameters:** `self`
**Implementation:**
```python
@property
def display_url(self) -> str:
    if self.type == 'cli_wrapper':
        return '(CLI wrapper)'
    return self.url or '(not configured)'
```

---

## Feature Class: `RouteTarget`
### Method: `to_dict`
**Parameters:** `self`
**Implementation:**
```python
def to_dict(self):
    return {'model': self.model, 'base_url': self.base_url, 'api_key': self.api_key}
```

### Method: `from_any`
**Parameters:** `cls, val`
**Implementation:**
```python
@classmethod
def from_any(cls, val) -> 'RouteTarget':
    if isinstance(val, str):
        return cls(model=val)
    if isinstance(val, dict):
        return cls(model=val.get('model', ''), base_url=val.get('base_url', ''), api_key=val.get('api_key', ''))
    return cls(model='')
```

---

## Feature Class: `RouterConfig`
**Description:**
```text
Per-use-case model routing (mirrors Claude Code Router semantics).
```

---

## Feature Class: `ProxyChain`
**Description:**
```text
The full proxy chain configuration, including ordered chain entries
and per-use-case model routing.
```

### Method: `to_dict`
**Parameters:** `self`
**Implementation:**
```python
def to_dict(self) -> dict:
    return {'entries': [asdict(e) for e in self.entries], 'router': asdict(self.router)}
```

### Method: `from_dict`
**Parameters:** `cls, data`
**Variables Used:** `parsed_router_data, router_data, entries, router, _router_fields`
**Implementation:**
```python
@classmethod
def from_dict(cls, data: dict) -> 'ProxyChain':
    entries = [ProxyEntry(**e) for e in data.get('entries', [])]
    router_data = data.get('router', {})
    parsed_router_data = {}
    if router_data.get('_disabled'):
        parsed_router_data['disabled'] = True
    if router_data.get('_passthrough'):
        parsed_router_data['passthrough'] = True
    _router_fields = RouterConfig.__dataclass_fields__
    for k, v in router_data.items():
        if k.startswith('_'):
            continue
        if k not in _router_fields:
            continue
        if k in ['default', 'background', 'think', 'long_context', 'web_search', 'image']:
            parsed_router_data[k] = RouteTarget.from_any(v)
        else:
            parsed_router_data[k] = v
    router = RouterConfig(**parsed_router_data)
    entries.sort(key=lambda e: e.order)
    return cls(entries=entries, router=router)
```

### Method: `load`
**Parameters:** `cls, path`
**Variables Used:** `p, data`
**Implementation:**
```python
@classmethod
def load(cls, path: Optional[Path]=None) -> 'ProxyChain':
    p = Path(os.environ.get('PROXY_CHAIN_FILE', path or DEFAULT_CHAIN_FILE))
    if not p.exists():
        return cls._default_chain()
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        return cls.from_dict(data)
    except Exception:
        return cls._default_chain()
```

### Method: `save`
**Parameters:** `self, path`
**Variables Used:** `p`
**Implementation:**
```python
def save(self, path: Optional[Path]=None) -> None:
    p = Path(os.environ.get('PROXY_CHAIN_FILE', path or DEFAULT_CHAIN_FILE))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')
```

### Method: `move_up`
**Parameters:** `self, idx`
**Implementation:**
```python
def move_up(self, idx: int) -> None:
    if idx > 0:
        self.entries[idx - 1], self.entries[idx] = (self.entries[idx], self.entries[idx - 1])
        self._renumber()
```

### Method: `move_down`
**Parameters:** `self, idx`
**Implementation:**
```python
def move_down(self, idx: int) -> None:
    if idx < len(self.entries) - 1:
        self.entries[idx], self.entries[idx + 1] = (self.entries[idx + 1], self.entries[idx])
        self._renumber()
```

### Method: `add`
**Parameters:** `self, entry`
**Implementation:**
```python
def add(self, entry: ProxyEntry) -> None:
    entry.order = len(self.entries)
    self.entries.append(entry)
    self._renumber()
```

### Method: `remove`
**Parameters:** `self, idx`
**Implementation:**
```python
def remove(self, idx: int) -> None:
    if 0 <= idx < len(self.entries):
        self.entries.pop(idx)
        self._renumber()
```

### Method: `_renumber`
**Parameters:** `self`
**Implementation:**
```python
def _renumber(self) -> None:
    for i, e in enumerate(self.entries):
        e.order = i
```

### Method: `upstream_url`
**Logic & Purpose:**
```text
The URL this proxy should use as PROVIDER_BASE_URL.
Returns the URL of the first enabled upstream HTTP entry in the chain.
Falls back to empty string (direct OpenRouter via env) if no HTTP entries.
```

**Parameters:** `self`
**Implementation:**
```python
def upstream_url(self) -> str:
    """
        The URL this proxy should use as PROVIDER_BASE_URL.
        Returns the URL of the first enabled upstream HTTP entry in the chain.
        Falls back to empty string (direct OpenRouter via env) if no HTTP entries.
        """
    for e in self.entries:
        if e.enabled and e.is_http and (not _is_local_proxy_entry(e)):
            return e.url
    return ''
```

### Method: `enabled_http_entries`
**Parameters:** `self`
**Implementation:**
```python
def enabled_http_entries(self) -> list[ProxyEntry]:
    return [e for e in self.entries if e.enabled and e.is_http]
```

### Method: `service_entries`
**Logic & Purpose:**
```text
Entries that have a service_cmd (can be started/stopped).
```

**Parameters:** `self`
**Implementation:**
```python
def service_entries(self) -> list[ProxyEntry]:
    """Entries that have a service_cmd (can be started/stopped)."""
    return [e for e in self.entries if e.service_cmd]
```

### Method: `start_services`
**Logic & Purpose:**
```text
Start all enabled services in REVERSE order (last service first,
so each service's upstream is ready before the next starts).
Returns list of (service_name, success, message).
```

**Parameters:** `self, dry_run`
**Variables Used:** `results`
**Implementation:**
```python
def start_services(self, dry_run: bool=False) -> list[tuple[str, bool, str]]:
    """
        Start all enabled services in REVERSE order (last service first,
        so each service's upstream is ready before the next starts).
        Returns list of (service_name, success, message).
        """
    results = []
    for entry in reversed(self.entries):
        if not entry.enabled or not entry.service_cmd:
            continue
        if dry_run:
            results.append((entry.name, True, f'would run: {entry.service_cmd}'))
            continue
        try:
            subprocess.Popen(entry.service_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            results.append((entry.name, True, f'started: {entry.service_cmd}'))
        except Exception as ex:
            results.append((entry.name, False, str(ex)))
    return results
```

### Method: `_default_chain`
**Logic & Purpose:**
```text
Default topology:
  Claude Proxy → Headroom (:8787) → RTK (CLI wrapper) → [AI provider via env]
CLIProxyAPI is included but DISABLED by default (Google banning TOS violations).
```

**Parameters:** `cls`
**Variables Used:** `router, entries`
**Implementation:**
```python
@classmethod
def _default_chain(cls) -> 'ProxyChain':
    """
        Default topology:
          Claude Proxy → Headroom (:8787) → RTK (CLI wrapper) → [AI provider via env]
        CLIProxyAPI is included but DISABLED by default (Google banning TOS violations).
        """
    entries = [ProxyEntry(id='headroom', name='Headroom Compression', url='http://127.0.0.1:8787/v1', auth_key='${OPENROUTER_API_KEY}', enabled=True, order=0, port=8787, health_path='/health', service_cmd='headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry', type='http'), ProxyEntry(id='rtk', name='RTK Terminal Compression', url='', auth_key='', enabled=True, order=1, type='cli_wrapper', service_cmd=''), ProxyEntry(id='cliproxyapi', name='CLIProxyAPI (Antigravity)', url='http://127.0.0.1:8317/v1', auth_key='', enabled=False, order=2, port=8317, health_path='/v1/models', service_cmd='/home/cheta/code/cliproxyapi/cli-proxy-api-plus --config /home/cheta/code/cliproxyapi/config.yaml', type='http')]
    router = RouterConfig(default=RouteTarget(''), background=RouteTarget('nvidia/nemotron-nano-9b-v2:free'), think=RouteTarget(''), long_context=RouteTarget('minimax/minimax-m2.5:free'), long_context_threshold=60000, web_search=RouteTarget(''), image=RouteTarget('qwen/qwen2.5-vl-72b-instruct'), custom_router_path='')
    return cls(entries=entries, router=router)
```

---

## Feature Function: `get_chain`
**Logic & Purpose:**
```text
Return the loaded chain, loading from disk if needed.
```

**Parameters:** ``
**Variables Used:** `_chain`
**Implementation:**
```python
def get_chain() -> ProxyChain:
    """Return the loaded chain, loading from disk if needed."""
    global _chain
    if _chain is None:
        _chain = ProxyChain.load()
    return _chain
```

---

## Feature Function: `reload_chain`
**Logic & Purpose:**
```text
Force reload from disk.
```

**Parameters:** ``
**Variables Used:** `_chain`
**Implementation:**
```python
def reload_chain() -> ProxyChain:
    """Force reload from disk."""
    global _chain
    _chain = ProxyChain.load()
    return _chain
```

---

## Feature Function: `_is_local_proxy_entry`
**Logic & Purpose:**
```text
Skip self-referential chain entries when deriving the proxy upstream URL.
```

**Parameters:** `entry`
**Variables Used:** `parsed, hostname`
**Implementation:**
```python
def _is_local_proxy_entry(entry: ProxyEntry) -> bool:
    """Skip self-referential chain entries when deriving the proxy upstream URL."""
    if entry.id == 'claude_code_proxy':
        return True
    try:
        parsed = urlparse(entry.url)
    except Exception:
        return False
    hostname = (parsed.hostname or '').lower()
    return hostname in {'127.0.0.1', 'localhost', '0.0.0.0'} and parsed.port == 8082
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/validator.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/validator.py`

**Module Overview**: 
```text
Configuration validation for Claude Code Proxy

Validates environment variables, API keys, and configuration
on startup to catch errors early and provide helpful feedback.
```

## Global Presets & Variables
- `console` = `Console()`

## Dependencies & Imports
os, sys, requests, typing.List, typing.Tuple, typing.Optional, typing.Dict, typing.Any, rich.console.Console, rich.panel.Panel, rich.table.Table, dotenv.load_dotenv

## Feature Class: `ConfigValidator`
**Description:**
```text
Validates proxy configuration on startup
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize validator with optional config object
```

**Parameters:** `self, config`
**Implementation:**
```python
def __init__(self, config=None):
    """Initialize validator with optional config object"""
    self.config = config
    self.errors: List[str] = []
    self.warnings: List[str] = []
    self.info: List[str] = []
```

### Method: `validate_all`
**Logic & Purpose:**
```text
Run all validation checks

Args:
    strict: If True, warnings are treated as errors

Returns:
    True if validation passed, False otherwise
```

**Parameters:** `self, strict`
**Variables Used:** `has_critical_warnings, has_errors`
**Implementation:**
```python
def validate_all(self, strict: bool=False) -> bool:
    """
        Run all validation checks

        Args:
            strict: If True, warnings are treated as errors

        Returns:
            True if validation passed, False otherwise
        """
    console.print('\n[bold cyan]🔍 Validating configuration...[/bold cyan]\n')
    self._check_required_variables()
    self._check_deprecated_variables()
    self._check_model_configuration()
    self._check_hybrid_mode()
    self._check_reasoning_config()
    self._check_api_keys()
    self._check_common_mistakes()
    self._check_port_availability()
    self._display_results()
    has_errors = len(self.errors) > 0
    has_critical_warnings = strict and len(self.warnings) > 0
    if has_errors or has_critical_warnings:
        console.print('\n[bold red]❌ Configuration validation failed[/bold red]\n')
        return False
    else:
        console.print('\n[bold green]✅ Configuration validated successfully[/bold green]\n')
        return True
```

### Method: `_check_required_variables`
**Logic & Purpose:**
```text
Check that required environment variables are set
```

**Parameters:** `self`
**Variables Used:** `provider_key, middle_model, big_model, small_model, provider_url`
**Implementation:**
```python
def _check_required_variables(self):
    """Check that required environment variables are set"""
    provider_key = os.getenv('PROVIDER_API_KEY') or os.getenv('OPENAI_API_KEY')
    provider_url = os.getenv('PROVIDER_BASE_URL') or os.getenv('OPENAI_BASE_URL')
    if not provider_key:
        self.errors.append('PROVIDER_API_KEY is not set\n  → Run: python setup_wizard.py\n  → Or add to .env: PROVIDER_API_KEY="your-key-here"')
    if not provider_url:
        self.errors.append('PROVIDER_BASE_URL is not set\n  → Run: python setup_wizard.py\n  → Or add to .env: PROVIDER_BASE_URL="https://api.provider.com/v1"')
    big_model = os.getenv('BIG_MODEL')
    middle_model = os.getenv('MIDDLE_MODEL')
    small_model = os.getenv('SMALL_MODEL')
    if not any([big_model, middle_model, small_model]):
        self.errors.append('No models configured (BIG_MODEL, MIDDLE_MODEL, SMALL_MODEL)\n  → Run: python setup_wizard.py\n  → Or add to .env: BIG_MODEL="your-model-name"')
```

### Method: `_check_deprecated_variables`
**Logic & Purpose:**
```text
Warn about deprecated variable names
```

**Parameters:** `self`
**Implementation:**
```python
def _check_deprecated_variables(self):
    """Warn about deprecated variable names"""
    pass
```

### Method: `_check_model_configuration`
**Logic & Purpose:**
```text
Validate model configuration
```

**Parameters:** `self`
**Variables Used:** `big_model, middle_model, provider_url, small_model`
**Implementation:**
```python
def _check_model_configuration(self):
    """Validate model configuration"""
    big_model = os.getenv('BIG_MODEL')
    middle_model = os.getenv('MIDDLE_MODEL')
    small_model = os.getenv('SMALL_MODEL')
    if not big_model:
        self.warnings.append('BIG_MODEL not configured (Claude Opus requests will fail)')
    if not middle_model and (not big_model):
        self.warnings.append('MIDDLE_MODEL not configured (Claude Sonnet requests will fail)')
    if not small_model:
        self.warnings.append('SMALL_MODEL not configured (Claude Haiku requests will fail)')
    provider_url = os.getenv('PROVIDER_BASE_URL', '')
    if 'openrouter.ai' in provider_url:
        for model_name, model_var in [(big_model, 'BIG_MODEL'), (middle_model, 'MIDDLE_MODEL'), (small_model, 'SMALL_MODEL')]:
            if model_name and '/' not in model_name:
                self.warnings.append(f'{model_var}="{model_name}" may be incorrect for OpenRouter\n  → OpenRouter models use format: provider/model\n  → Example: anthropic/claude-sonnet-4\n  → Run: python -m src.cli.model_selector')
```

### Method: `_check_hybrid_mode`
**Logic & Purpose:**
```text
Validate hybrid mode configuration
```

**Parameters:** `self`
**Variables Used:** `api_key, config_key, enabled, resolved_config, config_has_key, provider, endpoint`
**Implementation:**
```python
def _check_hybrid_mode(self):
    """Validate hybrid mode configuration"""
    try:
        from src.core.config import config as resolved_config
    except Exception as _e:
        resolved_config = None
    for tier in ['BIG', 'MIDDLE', 'SMALL']:
        enabled = os.getenv(f'ENABLE_{tier}_ENDPOINT', '').lower() == 'true'
        if enabled:
            endpoint = os.getenv(f'{tier}_ENDPOINT')
            api_key = os.getenv(f'{tier}_API_KEY')
            config_has_key = False
            if resolved_config:
                config_key = getattr(resolved_config, f'{tier.lower()}_api_key', None)
                config_has_key = config_key is not None
            if not endpoint:
                self.errors.append(f'ENABLE_{tier}_ENDPOINT is true but {tier}_ENDPOINT not set\n  → Add: {tier}_ENDPOINT="https://api.provider.com/v1"')
            if not api_key and (not config_has_key):
                self.warnings.append(f'ENABLE_{tier}_ENDPOINT is true but {tier}_API_KEY not set\n  → Add: {tier}_API_KEY="your-key" (or "dummy" for local)')
            elif not api_key and config_has_key:
                provider = getattr(resolved_config, f'{tier.lower()}_provider', 'auto')
                self.info.append(f'{tier} endpoint using auto-detected {provider.upper()} API key')
            self.info.append(f'Hybrid mode enabled for {tier} tier → {endpoint}')
```

### Method: `_check_reasoning_config`
**Logic & Purpose:**
```text
Validate reasoning configuration
```

**Parameters:** `self`
**Variables Used:** `tokens, reasoning_max_tokens, valid_efforts, reasoning_effort`
**Implementation:**
```python
def _check_reasoning_config(self):
    """Validate reasoning configuration"""
    reasoning_effort = os.getenv('REASONING_EFFORT')
    reasoning_max_tokens = os.getenv('REASONING_MAX_TOKENS')
    if reasoning_effort:
        valid_efforts = ['low', 'medium', 'high']
        if reasoning_effort not in valid_efforts:
            self.warnings.append(f'''REASONING_EFFORT="{reasoning_effort}" is invalid\n  → Valid values: {', '.join(valid_efforts)}\n  → For OpenAI o-series models''')
    if reasoning_max_tokens:
        try:
            tokens = int(reasoning_max_tokens)
            if tokens < 1024 or tokens > 128000:
                self.warnings.append(f'REASONING_MAX_TOKENS={tokens} is outside recommended range\n  → Claude: 1024-128000 tokens\n  → Gemini: 0-24576 tokens')
        except ValueError:
            self.errors.append(f'REASONING_MAX_TOKENS="{reasoning_max_tokens}" is not a valid number')
```

### Method: `_check_api_keys`
**Logic & Purpose:**
```text
Test API keys with providers and cache results
```

**Parameters:** `self`
**Variables Used:** `provider_key, result, api_key, enabled, provider_url, endpoint`
**Implementation:**
```python
def _check_api_keys(self):
    """Test API keys with providers and cache results"""
    from src.core.config import validate_api_key_format, set_provider_status
    provider_key = os.getenv('PROVIDER_API_KEY') or os.getenv('OPENAI_API_KEY')
    provider_url = os.getenv('PROVIDER_BASE_URL') or os.getenv('OPENAI_BASE_URL')
    if not provider_key or not provider_url:
        return
    result = self._test_api_key(provider_url, provider_key, 'Main Provider')
    if result:
        set_provider_status('main', result)
    for tier in ['BIG', 'MIDDLE', 'SMALL']:
        enabled = os.getenv(f'ENABLE_{tier}_ENDPOINT', '').lower() == 'true'
        if enabled:
            endpoint = os.getenv(f'{tier}_ENDPOINT')
            api_key = os.getenv(f'{tier}_API_KEY')
            if endpoint and api_key:
                result = self._test_api_key(endpoint, api_key, f'{tier} Endpoint')
                if result:
                    set_provider_status(tier.lower(), result)
    self._test_all_provider_keys()
```

### Method: `_test_api_key`
**Logic & Purpose:**
```text
Test an API key with a provider and return result for caching.

Returns:
    Dict with status info, or None if validation skipped
```

**Parameters:** `self, base_url, api_key, name`
**Variables Used:** `models_url, response, result, data`
**Implementation:**
```python
def _test_api_key(self, base_url: str, api_key: str, name: str) -> Optional[Dict]:
    """
        Test an API key with a provider and return result for caching.

        Returns:
            Dict with status info, or None if validation skipped
        """
    from src.core.config import validate_api_key_format
    result = {'name': name, 'endpoint': base_url, 'key_preview': f'{api_key[:10]}...' if api_key and len(api_key) > 10 else api_key, 'is_valid': False, 'is_connected': False, 'status': 'unknown', 'models_available': 0}
    if 'localhost' in base_url or '127.0.0.1' in base_url:
        self.info.append(f'{name}: Using local endpoint (skipping validation)')
        result['status'] = 'local'
        result['is_valid'] = True
        return result
    if api_key.lower() in ['dummy', 'test', 'none']:
        self.info.append(f'{name}: Using dummy key (skipping validation)')
        result['status'] = 'dummy'
        return result
    is_format_valid, format_msg = validate_api_key_format(api_key)
    if not is_format_valid:
        self.warnings.append(f'{name}: {format_msg}')
        result['status'] = 'invalid_format'
        return result
    try:
        models_url = f"{base_url.rstrip('/')}/models"
        response = requests.get(models_url, headers={'Authorization': f'Bearer {api_key}'}, timeout=5)
        result['is_connected'] = True
        if response.status_code == 401:
            self.errors.append(f'{name}: Invalid API key (401 Unauthorized)\n  → Check your API key in .env\n  → URL: {base_url}\n  → Key: {api_key[:10]}...')
            result['status'] = 'invalid_key'
        elif response.status_code == 403:
            self.warnings.append(f'{name}: API key valid but insufficient permissions (403 Forbidden)\n  → Check your account status\n  → For OpenRouter: Check credits at https://openrouter.ai/settings/credits')
            result['status'] = 'no_permission'
            result['is_valid'] = True
        elif response.status_code == 404:
            self.info.append(f'{name}: Cannot validate (no /models endpoint, assuming valid)')
            result['status'] = 'assumed_valid'
            result['is_valid'] = True
        elif response.status_code == 200:
            self.info.append(f'{name}: API key validated ✓')
            result['status'] = 'valid'
            result['is_valid'] = True
            try:
                data = response.json()
                if 'data' in data:
                    result['models_available'] = len(data['data'])
            except Exception as _e:
                pass
        else:
            self.warnings.append(f'{name}: Unexpected response ({response.status_code})\n  → Provider may be experiencing issues')
            result['status'] = f'http_{response.status_code}'
        return result
    except requests.exceptions.Timeout:
        self.warnings.append(f'{name}: Connection timeout (provider may be slow)\n  → URL: {base_url}')
        result['status'] = 'timeout'
        return result
    except requests.exceptions.ConnectionError:
        self.warnings.append(f'{name}: Cannot connect to provider\n  → Check URL: {base_url}\n  → Check internet connection')
        result['status'] = 'connection_error'
        return result
    except Exception as e:
        self.warnings.append(f'{name}: Validation failed: {str(e)}\n  → Assuming configuration is correct')
        result['status'] = 'error'
        return result
```

### Method: `_test_all_provider_keys`
**Logic & Purpose:**
```text
Test all available provider API keys and cache their status
```

**Parameters:** `self`
**Variables Used:** `providers_to_test, api_key`
**Implementation:**
```python
def _test_all_provider_keys(self):
    """Test all available provider API keys and cache their status"""
    from src.core.config import validate_api_key_format, set_provider_status
    providers_to_test = [('openrouter', 'OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1'), ('openai', 'OPENAI_API_KEY', 'https://api.openai.com/v1'), ('google', 'GOOGLE_API_KEY', 'https://generativelanguage.googleapis.com/v1beta/openai'), ('gemini', 'GEMINI_API_KEY', 'https://generativelanguage.googleapis.com/v1beta/openai'), ('anthropic', 'ANTHROPIC_API_KEY', 'https://api.anthropic.com/v1'), ('azure', 'AZURE_API_KEY', None)]
    for provider_name, env_var, default_endpoint in providers_to_test:
        api_key = os.getenv(env_var)
        if not api_key:
            set_provider_status(provider_name, {'name': provider_name, 'status': 'no_key', 'is_valid': False, 'is_connected': False})
            continue
        is_format_valid, format_msg = validate_api_key_format(api_key, provider_name)
        if not is_format_valid:
            set_provider_status(provider_name, {'name': provider_name, 'status': 'invalid_format', 'is_valid': False, 'is_connected': False, 'message': format_msg})
            continue
        set_provider_status(provider_name, {'name': provider_name, 'status': 'key_set', 'is_valid': True, 'is_connected': False, 'key_preview': f'{api_key[:10]}...' if len(api_key) > 10 else api_key})
```

### Method: `_check_common_mistakes`
**Logic & Purpose:**
```text
Check for common configuration mistakes
```

**Parameters:** `self`
**Variables Used:** `provider_key, provider_url, server_port`
**Implementation:**
```python
def _check_common_mistakes(self):
    """Check for common configuration mistakes"""
    provider_key = os.getenv('PROVIDER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if provider_key:
        if len(provider_key) < 20:
            self.warnings.append(f'PROVIDER_API_KEY is very short ({len(provider_key)} chars)\n  → Most API keys are 30+ characters\n  → Make sure you copied the full key')
        if provider_key.startswith('sk-ant-'):
            self.warnings.append('PROVIDER_API_KEY looks like an Anthropic key (sk-ant-...)\n  → This proxy is for NON-Anthropic providers\n  → Use OpenRouter, Gemini, OpenAI, or local models\n  → See: README.md for provider setup')
    provider_url = os.getenv('PROVIDER_BASE_URL') or os.getenv('OPENAI_BASE_URL')
    if provider_url:
        if not provider_url.startswith(('http://', 'https://')):
            self.errors.append(f'PROVIDER_BASE_URL must start with http:// or https://\n  → Current value: {provider_url}')
        if not provider_url.endswith('/v1'):
            self.warnings.append(f'PROVIDER_BASE_URL should typically end with /v1\n  → Current value: {provider_url}\n  → Example: https://api.openai.com/v1')
        if 'localhost' in provider_url or '127.0.0.1' in provider_url:
            server_port = os.getenv('PORT', '8082')
            if f':{server_port}' in provider_url:
                self.warnings.append(f"PROVIDER_BASE_URL appears to be pointing to THIS proxy ({provider_url})\n  → This will cause an infinite loop!\n  → PROVIDER_BASE_URL should point to the UPSTREAM provider (e.g. OpenAI, OpenRouter)\n  → The 'localhost:{server_port}' address is for your Claude Code client, not this config.")
```

### Method: `_check_port_availability`
**Logic & Purpose:**
```text
Check if configured port is available
```

**Parameters:** `self`
**Variables Used:** `port, host, sock`
**Implementation:**
```python
def _check_port_availability(self):
    """Check if configured port is available"""
    import socket
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8082'))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        self.info.append(f'Port {port} is available')
    except OSError:
        self.warnings.append(f'Port {port} is already in use\n  → Change PORT in .env\n  → Or stop the process using: lsof -ti:{port} | xargs kill -9')
    finally:
        sock.close()
```

### Method: `_display_results`
**Logic & Purpose:**
```text
Display validation results
```

**Parameters:** `self`
**Implementation:**
```python
def _display_results(self):
    """Display validation results"""
    if self.errors:
        console.print('\n[bold red]ERRORS:[/bold red]')
        for i, error in enumerate(self.errors, 1):
            console.print(f'\n[red]{i}. {error}[/red]')
    if self.warnings:
        console.print('\n[bold yellow]WARNINGS:[/bold yellow]')
        for i, warning in enumerate(self.warnings, 1):
            console.print(f'\n[yellow]{i}. {warning}[/yellow]')
    if not self.errors and (not self.warnings) and self.info:
        console.print('\n[bold green]CONFIGURATION:[/bold green]')
        for item in self.info:
            console.print(f'  [green]• {item}[/green]')
```

---

## Feature Function: `validate_config_on_startup`
**Logic & Purpose:**
```text
Validate configuration on startup

Args:
    strict: If True, warnings are treated as errors

Returns:
    True if validation passed, False otherwise
```

**Parameters:** `strict`
**Variables Used:** `passed, validator`
**Implementation:**
```python
def validate_config_on_startup(strict: bool=False) -> bool:
    """
    Validate configuration on startup

    Args:
        strict: If True, warnings are treated as errors

    Returns:
        True if validation passed, False otherwise
    """
    load_dotenv()
    validator = ConfigValidator()
    passed = validator.validate_all(strict=strict)
    return passed
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
CLI entry point for config validation
```

**Parameters:** ``
**Variables Used:** `args, passed, parser`
**Implementation:**
```python
def main():
    """CLI entry point for config validation"""
    import argparse
    parser = argparse.ArgumentParser(description='Validate Claude Code Proxy configuration')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    parser.add_argument('--quiet', action='store_true', help='Only show errors (suppress info)')
    args = parser.parse_args()
    passed = validate_config_on_startup(strict=args.strict)
    sys.exit(0 if passed else 1)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/model_manager.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/model_manager.py`

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `REASONING_TYPE_META` = `{'effort': {'default_effort': 'medium'}, 'thinking_tokens': {'min_tokens': 1024, 'max_tokens': 128000}, 'thinking_budget': {'min_budget': 0, 'max_budget': 24576}}`
- `model_manager` = `ModelManager(config)`

## Dependencies & Imports
logging, typing.Optional, typing.Tuple, typing.Dict, typing.Any, src.core.config.config, src.services.models.model_parser.parse_model_name, src.services.models.model_parser.ParsedModel, src.core.reasoning_validator.validate_openai_reasoning, src.core.reasoning_validator.validate_anthropic_thinking, src.core.reasoning_validator.validate_gemini_thinking, src.core.reasoning_validator.is_reasoning_capable_model, src.core.reasoning_validator._is_openai_reasoning_model, src.models.reasoning.ReasoningConfig, src.models.reasoning.OpenAIReasoningConfig, src.models.reasoning.AnthropicThinkingConfig, src.models.reasoning.GeminiThinkingConfig

## Feature Class: `ModelManager`
### Method: `__init__`
**Parameters:** `self, config`
**Implementation:**
```python
def __init__(self, config):
    self.config = config
```

### Method: `is_newer_openai_model`
**Logic & Purpose:**
```text
Check if the model is a newer OpenAI reasoning model (o1, o3, o4, gpt-5).
These models require max_completion_tokens instead of max_tokens and temperature=1.

Args:
    model_name: Model name to check

Returns:
    True if the model is o1, o3, o4, or gpt-5
```

**Parameters:** `self, model_name`
**Variables Used:** `model_lower`
**Implementation:**
```python
def is_newer_openai_model(self, model_name: str) -> bool:
    """
        Check if the model is a newer OpenAI reasoning model (o1, o3, o4, gpt-5).
        These models require max_completion_tokens instead of max_tokens and temperature=1.

        Args:
            model_name: Model name to check

        Returns:
            True if the model is o1, o3, o4, or gpt-5
        """
    model_lower = model_name.lower()
    if any((pattern in model_lower for pattern in ['o1-', 'o1mini', 'o3-', 'o3mini', 'o4-', 'o4mini'])):
        return True
    if 'gpt-5' in model_lower or 'gpt5' in model_lower:
        return True
    return False
```

### Method: `is_o3_model`
**Logic & Purpose:**
```text
Check if the model is an OpenAI o3 model.

Args:
    model_name: Model name to check

Returns:
    True if the model is an o3 variant
```

**Parameters:** `self, model_name`
**Variables Used:** `model_lower`
**Implementation:**
```python
def is_o3_model(self, model_name: str) -> bool:
    """
        Check if the model is an OpenAI o3 model.

        Args:
            model_name: Model name to check

        Returns:
            True if the model is an o3 variant
        """
    model_lower = model_name.lower()
    return 'o3-' in model_lower or 'o3mini' in model_lower
```

### Method: `map_claude_model_to_openai`
**Logic & Purpose:**
```text
Map Claude model names to OpenAI model names based on BIG/SMALL pattern.

Only maps Claude-specific model family names (haiku/sonnet/opus).
All other model names — including Gemini, OpenAI, custom, or
provider-prefixed models — pass through as-is.

Handles hybrid tier/provider format:
- 'opus/qwen-2.5-72b' → returns 'qwen-2.5-72b' (uses provider model directly)
- 'sonnet/openai/gpt-4o' → returns 'openai/gpt-4o' (uses provider model directly)
```

**Parameters:** `self, claude_model`
**Variables Used:** `model_lower, parts, provider_model`
**Implementation:**
```python
def map_claude_model_to_openai(self, claude_model: str) -> str:
    """Map Claude model names to OpenAI model names based on BIG/SMALL pattern.

        Only maps Claude-specific model family names (haiku/sonnet/opus).
        All other model names — including Gemini, OpenAI, custom, or
        provider-prefixed models — pass through as-is.
        
        Handles hybrid tier/provider format:
        - 'opus/qwen-2.5-72b' → returns 'qwen-2.5-72b' (uses provider model directly)
        - 'sonnet/openai/gpt-4o' → returns 'openai/gpt-4o' (uses provider model directly)
        """
    model_lower = claude_model.lower()
    if '/' in model_lower:
        parts = model_lower.split('/', 1)
        if parts[0] in ['opus', 'sonnet', 'haiku']:
            provider_model = parts[1]
            logger.debug(f"Hybrid model detected: '{claude_model}' → using '{provider_model}'")
            return provider_model
    if 'haiku' in model_lower:
        return self.config.small_model
    elif 'sonnet' in model_lower:
        return self.config.middle_model
    elif 'opus' in model_lower:
        return self.config.big_model
    else:
        return claude_model
```

### Method: `parse_and_map_model`
**Logic & Purpose:**
```text
Parse model name with reasoning suffix and map to OpenAI model.

Args:
    claude_model: Claude model name with optional reasoning suffix

Returns:
    Tuple of (openai_model, reasoning_config)
    - openai_model: Mapped OpenAI model name
    - reasoning_config: ReasoningConfig object or None
```

**Parameters:** `self, claude_model`
**Variables Used:** `parsed, reasoning_config, openai_model`
**Implementation:**
```python
def parse_and_map_model(self, claude_model: str) -> Tuple[str, Optional[ReasoningConfig]]:
    """
        Parse model name with reasoning suffix and map to OpenAI model.

        Args:
            claude_model: Claude model name with optional reasoning suffix

        Returns:
            Tuple of (openai_model, reasoning_config)
            - openai_model: Mapped OpenAI model name
            - reasoning_config: ReasoningConfig object or None
        """
    parsed = parse_model_name(claude_model)
    openai_model = self.map_claude_model_to_openai(parsed.base_model)
    if not parsed.reasoning_type or parsed.reasoning_value is None:
        reasoning_config = self._get_default_reasoning_config(openai_model)
        return (openai_model, reasoning_config)
    reasoning_config = self._create_reasoning_config(parsed.reasoning_type, parsed.reasoning_value, openai_model)
    logger.info(f"Parsed model '{claude_model}' → base='{openai_model}', reasoning_type='{parsed.reasoning_type}', reasoning_value={parsed.reasoning_value}")
    return (openai_model, reasoning_config)
```

### Method: `_get_default_reasoning_config`
**Logic & Purpose:**
```text
Get default reasoning configuration from environment variables.

Args:
    model_name: Model name to check for reasoning capability

Returns:
    ReasoningConfig object or None
```

**Parameters:** `self, model_name`
**Variables Used:** `default_effort, validated_effort, validated_budget, default_max_tokens`
**Implementation:**
```python
def _get_default_reasoning_config(self, model_name: str) -> Optional[ReasoningConfig]:
    """
        Get default reasoning configuration from environment variables.

        Args:
            model_name: Model name to check for reasoning capability

        Returns:
            ReasoningConfig object or None
        """
    is_capable, reasoning_type = is_reasoning_capable_model(model_name)
    if not is_capable:
        return None
    default_effort = self.config.reasoning_effort
    default_max_tokens = self.config.reasoning_max_tokens
    if reasoning_type == 'effort' and default_effort:
        try:
            validated_effort = validate_openai_reasoning(default_effort)
            return OpenAIReasoningConfig(enabled=True, effort=validated_effort, exclude=self.config.reasoning_exclude)
        except ValueError as e:
            logger.warning(f'Invalid default reasoning effort: {e}')
            return None
    elif reasoning_type == 'thinking_tokens' and default_max_tokens:
        validated_budget = validate_anthropic_thinking(default_max_tokens)
        return AnthropicThinkingConfig(type='enabled', budget=validated_budget)
    elif reasoning_type == 'thinking_budget' and default_max_tokens:
        validated_budget = validate_gemini_thinking(default_max_tokens)
        return GeminiThinkingConfig(budget=validated_budget)
    return None
```

### Method: `_create_reasoning_config`
**Logic & Purpose:**
```text
Create reasoning configuration based on type and value.

Args:
    reasoning_type: Type of reasoning ('effort', 'thinking_tokens', 'thinking_budget')
    reasoning_value: Value for reasoning parameter
    model_name: Model name for validation

Returns:
    ReasoningConfig object or None
```

**Parameters:** `self, reasoning_type, reasoning_value, model_name`
**Variables Used:** `validated_effort, validated_budget, is_openai`
**Implementation:**
```python
def _create_reasoning_config(self, reasoning_type: str, reasoning_value: Any, model_name: str) -> Optional[ReasoningConfig]:
    """
        Create reasoning configuration based on type and value.

        Args:
            reasoning_type: Type of reasoning ('effort', 'thinking_tokens', 'thinking_budget')
            reasoning_value: Value for reasoning parameter
            model_name: Model name for validation

        Returns:
            ReasoningConfig object or None
        """
    try:
        if reasoning_type == 'effort':
            validated_effort = validate_openai_reasoning(str(reasoning_value))
            return OpenAIReasoningConfig(enabled=True, effort=validated_effort, max_tokens=None, exclude=self.config.reasoning_exclude)
        elif reasoning_type == 'thinking_tokens':
            is_openai = _is_openai_reasoning_model(model_name.lower())
            if is_openai:
                return OpenAIReasoningConfig(enabled=True, effort=None, max_tokens=int(reasoning_value), exclude=self.config.reasoning_exclude)
            else:
                validated_budget = validate_anthropic_thinking(int(reasoning_value))
                return AnthropicThinkingConfig(type='enabled', budget=validated_budget)
        elif reasoning_type == 'thinking_budget':
            validated_budget = validate_gemini_thinking(int(reasoning_value))
            return GeminiThinkingConfig(budget=validated_budget)
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to create reasoning config for model '{model_name}': {e}")
        return None
    return None
```

### Method: `get_model_capabilities`
**Logic & Purpose:**
```text
Get model capabilities including reasoning support.

Args:
    model_name: Model name to check

Returns:
    Dictionary with capability information:
    {
        'supports_reasoning': bool,
        'reasoning_type': str,
        'max_reasoning_tokens': int,
        'default_reasoning': Optional[ReasoningConfig]
    }
```

**Parameters:** `self, model_name`
**Variables Used:** `capabilities`
**Implementation:**
```python
def get_model_capabilities(self, model_name: str) -> Dict[str, Any]:
    """
        Get model capabilities including reasoning support.

        Args:
            model_name: Model name to check

        Returns:
            Dictionary with capability information:
            {
                'supports_reasoning': bool,
                'reasoning_type': str,
                'max_reasoning_tokens': int,
                'default_reasoning': Optional[ReasoningConfig]
            }
        """
    is_capable, reasoning_type = is_reasoning_capable_model(model_name)
    capabilities = {'supports_reasoning': is_capable, 'reasoning_type': reasoning_type, 'max_reasoning_tokens': None, 'default_reasoning': None}
    if not is_capable:
        return capabilities
    if reasoning_type == 'thinking_tokens':
        capabilities['max_reasoning_tokens'] = REASONING_TYPE_META['thinking_tokens']['max_tokens']
    elif reasoning_type == 'thinking_budget':
        capabilities['max_reasoning_tokens'] = REASONING_TYPE_META['thinking_budget']['max_budget']
    capabilities['default_reasoning'] = self._get_default_reasoning_config(model_name)
    return capabilities
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/model_router.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/model_router.py`

**Module Overview**: 
```text
Model Router

Routes incoming requests to the appropriate model based on use-case signals,
mirroring the Claude Code Router routing strategy:

  default       → general tasks (falls back to BIG_MODEL from env)
  background    → lightweight/background tasks (smaller, cheaper model)
  think         → reasoning-heavy tasks, Plan Mode (thinking model)
  long_context  → requests exceeding long_context_threshold tokens
  web_search    → requests that need live web data (:online suffix for OR)
  image         → image-capable requests (vision model)
  custom        → custom_router.py script for advanced routing logic

Custom Router Contract (Python):
  # custom_router.py
  def route(request: dict, config: object) -> str | None:
      # Return "provider/model" string or None to fall through to default routing
      ...

Custom Router Contract (JavaScript, via Node.js subprocess):
  // custom_router.js
  module.exports = async function route(request, config) {
      return "provider/model" or null;
  }
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `_CHARS_PER_TOKEN` = `4`

## Dependencies & Imports
__future__.annotations, importlib.util, json, logging, os, subprocess, sys, pathlib.Path, typing.Optional

## Feature Function: `_estimate_tokens`
**Logic & Purpose:**
```text
Rough token estimate from message content length.
```

**Parameters:** `request`
**Variables Used:** `total_chars, content`
**Implementation:**
```python
def _estimate_tokens(request: dict) -> int:
    """Rough token estimate from message content length."""
    total_chars = 0
    for msg in request.get('messages', []):
        content = msg.get('content', '')
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total_chars += len(str(block.get('text', '') or block.get('content', '')))
    return total_chars // _CHARS_PER_TOKEN
```

---

## Feature Function: `_has_image`
**Logic & Purpose:**
```text
Return True if any message contains an image block.
```

**Parameters:** `request`
**Variables Used:** `content`
**Implementation:**
```python
def _has_image(request: dict) -> bool:
    """Return True if any message contains an image block."""
    for msg in request.get('messages', []):
        content = msg.get('content', [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'image':
                    return True
    return False
```

---

## Feature Function: `_is_web_search_request`
**Logic & Purpose:**
```text
Return True if the request appears to be a web search task.
```

**Parameters:** `request`
**Variables Used:** `tools, name`
**Implementation:**
```python
def _is_web_search_request(request: dict) -> bool:
    """Return True if the request appears to be a web search task."""
    tools = request.get('tools', [])
    for tool in tools:
        name = tool.get('name', '').lower()
        if any((k in name for k in ('web_search', 'search_web', 'brave', 'exa', 'perplexity'))):
            return True
    return False
```

---

## Feature Function: `_is_background_request`
**Logic & Purpose:**
```text
Return True if this is a background / lightweight task.

Claude Code sends haiku-family models for background work (file scanning,
auto-complete context, tool result summaries). We detect this from the
original Claude model name stored in _original_model by endpoints.py,
or by a low max_tokens cap that signals a cheap background call.
```

**Parameters:** `request`
**Variables Used:** `orig, max_tokens`
**Implementation:**
```python
def _is_background_request(request: dict) -> bool:
    """
    Return True if this is a background / lightweight task.

    Claude Code sends haiku-family models for background work (file scanning,
    auto-complete context, tool result summaries). We detect this from the
    original Claude model name stored in _original_model by endpoints.py,
    or by a low max_tokens cap that signals a cheap background call.
    """
    if request.get('_is_background'):
        return True
    orig = request.get('_original_model', '')
    if orig and 'haiku' in orig.lower():
        return True
    max_tokens = request.get('max_tokens', 0)
    if max_tokens and max_tokens <= 256:
        return True
    return False
```

---

## Feature Function: `_detect_think_mode`
**Logic & Purpose:**
```text
Return True if this is a reasoning/planning request.
Heuristics: extended_thinking enabled, or system prompt contains planning keywords.
```

**Parameters:** `request`
**Variables Used:** `system, plan_keywords, c`
**Implementation:**
```python
def _detect_think_mode(request: dict) -> bool:
    """
    Return True if this is a reasoning/planning request.
    Heuristics: extended_thinking enabled, or system prompt contains planning keywords.
    """
    if request.get('thinking', {}).get('type') == 'enabled':
        return True
    system = ''
    for msg in request.get('messages', []):
        if msg.get('role') == 'system':
            c = msg.get('content', '')
            system = c if isinstance(c, str) else str(c)
            break
    plan_keywords = ('plan mode', 'planning mode', 'think step by step', 'think carefully')
    return any((k in system.lower() for k in plan_keywords))
```

---

## Feature Function: `_load_python_router`
**Logic & Purpose:**
```text
Load a Python custom router module. Returns the route() callable or None.
```

**Parameters:** `path`
**Variables Used:** `mod, spec`
**Implementation:**
```python
def _load_python_router(path: str):
    """Load a Python custom router module. Returns the route() callable or None."""
    try:
        spec = importlib.util.spec_from_file_location('custom_router', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'route'):
            return mod.route
    except Exception as e:
        logger.error(f'[ModelRouter] Failed to load Python custom router {path}: {e}')
    return None
```

---

## Feature Function: `_call_js_router`
**Logic & Purpose:**
```text
Call a JavaScript custom router via Node.js subprocess.
```

**Parameters:** `path, request, config_dict`
**Variables Used:** `wrapper, val, result`
**Implementation:**
```python
def _call_js_router(path: str, request: dict, config_dict: dict) -> Optional[str]:
    """Call a JavaScript custom router via Node.js subprocess."""
    wrapper = f'\nconst router = require({json.dumps(path)});\nconst req = {json.dumps(request)};\nconst cfg = {json.dumps(config_dict)};\n(async () => {{\n    const result = await router(req, cfg);\n    process.stdout.write(JSON.stringify(result ?? null));\n}})();\n'
    try:
        result = subprocess.run(['node', '-e', wrapper], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            val = json.loads(result.stdout.strip())
            return val if isinstance(val, str) else None
    except Exception as e:
        logger.error(f'[ModelRouter] JS custom router error: {e}')
    return None
```

---

## Feature Class: `ModelRouter`
**Description:**
```text
Decides which model to use for a given request.
Falls back to the configured BIG_MODEL when no route matches.
```

### Method: `__init__`
**Logic & Purpose:**
```text
router_config: RouterConfig from proxy_chain.py
base_config: The main Config object (used for BIG/MIDDLE/SMALL models)
```

**Parameters:** `self, router_config, base_config`
**Implementation:**
```python
def __init__(self, router_config, base_config=None):
    """
        router_config: RouterConfig from proxy_chain.py
        base_config: The main Config object (used for BIG/MIDDLE/SMALL models)
        """
    self._rc = router_config
    self._base = base_config
    self._python_router = None
    self._router_loaded = False
```

### Method: `_get_python_router`
**Parameters:** `self`
**Variables Used:** `path`
**Implementation:**
```python
def _get_python_router(self):
    if self._router_loaded:
        return self._python_router
    self._router_loaded = True
    path = self._rc.custom_router_path
    if path and Path(path).exists():
        if path.endswith('.py'):
            self._python_router = _load_python_router(path)
    return self._python_router
```

### Method: `route`
**Logic & Purpose:**
```text
Return the RouteTarget to use, or None to leave the existing model unchanged.

Priority:
  0. Disabled/passthrough flags (short-circuit)
  1. Custom router script
  2. Image detection
  3. Web search detection
  4. Long context detection
  5. Think/Plan mode detection
  6. Background task detection (caller must pass metadata)
  7. Default model (or None → caller keeps original)
```

**Parameters:** `self, request`
**Variables Used:** `result, config_dict, path, python_router, tokens, rc`
**Implementation:**
```python
def route(self, request: dict):
    """
        Return the RouteTarget to use, or None to leave the existing model unchanged.

        Priority:
          0. Disabled/passthrough flags (short-circuit)
          1. Custom router script
          2. Image detection
          3. Web search detection
          4. Long context detection
          5. Think/Plan mode detection
          6. Background task detection (caller must pass metadata)
          7. Default model (or None → caller keeps original)
        """
    rc = self._rc
    if rc.passthrough or rc.disabled:
        return None
    python_router = self._get_python_router()
    if python_router:
        try:
            config_dict = {'default': rc.default, 'background': rc.background, 'think': rc.think, 'long_context': rc.long_context, 'web_search': rc.web_search, 'image': rc.image}
            result = python_router(request, config_dict)
            if result:
                logger.debug(f'[ModelRouter] Custom Python router → {result}')
                from src.core.proxy_chain import RouteTarget
                return RouteTarget.from_any(result)
        except Exception as e:
            logger.error(f'[ModelRouter] Custom router exception: {e}')
    path = rc.custom_router_path
    if path and path.endswith('.js') and Path(path).exists():
        config_dict = {'default': rc.default.to_dict(), 'background': rc.background.to_dict()}
        result = _call_js_router(path, request, config_dict)
        if result:
            logger.debug(f'[ModelRouter] Custom JS router → {result}')
            from src.core.proxy_chain import RouteTarget
            return RouteTarget.from_any(result)
    if rc.image and rc.image.model and _has_image(request):
        logger.debug(f'[ModelRouter] Image request → {rc.image.model}')
        return rc.image
    if rc.web_search and rc.web_search.model and _is_web_search_request(request):
        logger.debug(f'[ModelRouter] Web search request → {rc.web_search.model}')
        return rc.web_search
    if rc.long_context and rc.long_context.model:
        tokens = _estimate_tokens(request)
        if tokens > rc.long_context_threshold:
            logger.debug(f'[ModelRouter] Long context (~{tokens} tokens) → {rc.long_context.model}')
            return rc.long_context
    if rc.think and rc.think.model and _detect_think_mode(request):
        logger.debug(f'[ModelRouter] Think mode → {rc.think.model}')
        return rc.think
    if rc.background and rc.background.model and _is_background_request(request):
        logger.debug(f'[ModelRouter] Background request → {rc.background.model}')
        return rc.background
    if rc.default and rc.default.model:
        return rc.default
    return None
```

---

## Feature Function: `get_router`
**Logic & Purpose:**
```text
Return the module-level router, initializing if needed.

When a Config object is supplied, env-var overrides (ROUTER_*) are merged
on top of the proxy_chain.json router section so that .env always wins.
```

**Parameters:** `config`
**Variables Used:** `_router, chain, rc`
**Implementation:**
```python
def get_router(config=None) -> ModelRouter:
    """
    Return the module-level router, initializing if needed.

    When a Config object is supplied, env-var overrides (ROUTER_*) are merged
    on top of the proxy_chain.json router section so that .env always wins.
    """
    global _router
    if _router is None:
        from src.core.proxy_chain import get_chain, RouterConfig
        chain = get_chain()
        rc = chain.router
        if config is not None:
            rc = RouterConfig(default=getattr(config, 'router_default', rc.default) or rc.default, background=getattr(config, 'router_background', rc.background) or rc.background, think=getattr(config, 'router_think', rc.think) or rc.think, long_context=getattr(config, 'router_long_context', rc.long_context) or rc.long_context, long_context_threshold=getattr(config, 'router_long_context_threshold', rc.long_context_threshold), web_search=getattr(config, 'router_web_search', rc.web_search) or rc.web_search, image=getattr(config, 'router_image', rc.image) or rc.image, custom_router_path=getattr(config, 'router_custom_path', rc.custom_router_path) or rc.custom_router_path)
        _router = ModelRouter(rc, base_config=config)
    return _router
```

---

## Feature Function: `reload_router`
**Logic & Purpose:**
```text
Force reload router from chain config.
```

**Parameters:** `config`
**Variables Used:** `_router, chain`
**Implementation:**
```python
def reload_router(config=None) -> ModelRouter:
    """Force reload router from chain config."""
    global _router
    from src.core.proxy_chain import get_chain, reload_chain
    chain = reload_chain()
    _router = ModelRouter(chain.router, base_config=config)
    return _router
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/config.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/config.py`

## Dependencies & Imports
os, sys, re, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Tuple

## Feature Function: `validate_api_key_format`
**Logic & Purpose:**
```text
Validate API key format for a specific provider.

Args:
    key: The API key to validate
    provider: Optional provider name (openai, openrouter, anthropic, google, azure)
             If not specified, tries to auto-detect from key format

Returns:
    Tuple of (is_valid, message)
```

**Parameters:** `key, provider`
**Variables Used:** `pattern, provider`
**Implementation:**
```python
def validate_api_key_format(key: str, provider: str=None) -> Tuple[bool, str]:
    """
    Validate API key format for a specific provider.

    Args:
        key: The API key to validate
        provider: Optional provider name (openai, openrouter, anthropic, google, azure)
                 If not specified, tries to auto-detect from key format

    Returns:
        Tuple of (is_valid, message)
    """
    if not key:
        return (False, 'No API key provided')
    if not provider:
        if key.startswith('sk-or-'):
            provider = 'openrouter'
        elif key.startswith('sk-ant-'):
            provider = 'anthropic'
        elif key.startswith('AIza'):
            provider = 'google'
        elif key.startswith('ya29.'):
            provider = 'vibeproxy'
        elif key.startswith('sk-'):
            provider = 'openai'
        elif len(key) == 32 and all((c in '0123456789abcdef' for c in key.lower())):
            provider = 'azure'
        else:
            if len(key) >= 20:
                return (True, 'Unknown key format (accepted)')
            return (False, 'Key too short (minimum 20 characters)')
    pattern = API_KEY_PATTERNS.get(provider.lower())
    if pattern:
        if pattern.match(key):
            return (True, f'Valid {provider} key format')
        else:
            if provider == 'openrouter' and key.startswith('sk-or-'):
                return (True, f'Valid OpenRouter key (relaxed validation)')
            elif provider in ('google', 'gemini') and key.startswith('AIza'):
                return (True, f'Valid Google key (relaxed validation)')
            return (False, f'Invalid {provider} key format')
    if len(key) >= 10:
        return (True, f'Accepted key for {provider}')
    return (False, 'Key too short')
```

---

## Feature Function: `get_provider_status_cache`
**Logic & Purpose:**
```text
Get cached provider status from startup validation.
```

**Parameters:** ``
**Implementation:**
```python
def get_provider_status_cache() -> Dict[str, dict]:
    """Get cached provider status from startup validation."""
    return _provider_status_cache
```

---

## Feature Function: `set_provider_status`
**Logic & Purpose:**
```text
Update provider status in cache.
```

**Parameters:** `provider, status`
**Implementation:**
```python
def set_provider_status(provider: str, status: dict):
    """Update provider status in cache."""
    _provider_status_cache[provider] = status
```

---

## Feature Class: `Config`
### Method: `__init__`
**Parameters:** `self`
**Variables Used:** `proxy_auth_key, _fallback_raw, _fallback_str, key, override, url, _rc, provider_api_key, reasoning_max_tokens, legacy_openai_url, provider_base_url, enable_legacy_proxy_auth, provider_key_map, legacy_anthropic_key, auto_key, legacy_openai_key, model`
**Implementation:**
```python
def __init__(self):
    provider_api_key = os.environ.get('PROVIDER_API_KEY')
    provider_base_url = os.environ.get('PROVIDER_BASE_URL')
    proxy_auth_key = os.environ.get('PROXY_AUTH_KEY')
    legacy_openai_key = os.environ.get('OPENAI_API_KEY')
    legacy_openai_url = os.environ.get('OPENAI_BASE_URL')
    legacy_anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    enable_legacy_proxy_auth = os.environ.get('ENABLE_LEGACY_PROXY_AUTH', 'false').lower() == 'true'
    if provider_api_key:
        self.openai_api_key = provider_api_key
    elif legacy_openai_key:
        self.openai_api_key = legacy_openai_key
    elif os.environ.get('OPENROUTER_API_KEY'):
        self.openai_api_key = os.environ.get('OPENROUTER_API_KEY')
    else:
        self.openai_api_key = None
    if provider_base_url:
        self.openai_base_url = provider_base_url
    elif legacy_openai_url:
        self.openai_base_url = legacy_openai_url
    else:
        self.openai_base_url = ''
    if proxy_auth_key:
        self.anthropic_api_key = proxy_auth_key
    elif legacy_anthropic_key and enable_legacy_proxy_auth:
        self.anthropic_api_key = legacy_anthropic_key
    else:
        self.anthropic_api_key = None
    self.passthrough_mode = False
    if not self.openai_api_key:
        print('INFO: PROVIDER_API_KEY not configured - enabling passthrough mode')
        print('INFO: Users must provide their own API keys via request headers')
        self.passthrough_mode = True
    elif self.openai_api_key in ('pass', 'dummy', 'your-api-key-here', 'sk-your-openai-api-key-here') or 'your-' in self.openai_api_key.lower():
        print('WARNING: PROVIDER_API_KEY is set to a placeholder value')
        print('INFO: Enabling passthrough mode - users must provide their own API keys')
        self.passthrough_mode = True
        self.openai_api_key = None
    self.azure_api_version = os.environ.get('AZURE_API_VERSION')
    self.host = os.environ.get('HOST', '0.0.0.0')
    self.port = int(os.environ.get('PORT', '8082'))
    self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
    self.log_tier = os.environ.get('LOG_TIER', 'production').lower()
    self.logs_dir = os.environ.get('LOGS_DIR', 'logs')
    self.log_max_size_mb = int(os.environ.get('LOG_MAX_SIZE_MB', '50'))
    self.log_retention_days = int(os.environ.get('LOG_RETENTION_DAYS', '7'))
    self.tool_output_max_chars = int(os.environ.get('TOOL_OUTPUT_MAX_CHARS', '50000'))
    self.tool_output_truncation = os.environ.get('TOOL_OUTPUT_TRUNCATION', 'true').lower() == 'true'
    self.max_tokens_limit = int(os.environ.get('MAX_TOKENS_LIMIT')) if os.environ.get('MAX_TOKENS_LIMIT') else None
    self.min_tokens_limit = int(os.environ.get('MIN_TOKENS_LIMIT')) if os.environ.get('MIN_TOKENS_LIMIT') else None
    self.enable_openrouter_selection = os.environ.get('ENABLE_OPENROUTER_SELECTION', 'true').lower() == 'true'
    self.request_timeout = int(os.environ.get('REQUEST_TIMEOUT', '90'))
    self.max_retries = int(os.environ.get('MAX_RETRIES', '2'))
    self.big_model = os.environ.get('BIG_MODEL') or ''
    self.middle_model = os.environ.get('MIDDLE_MODEL') or ''
    self.small_model = os.environ.get('SMALL_MODEL') or ''
    self.model_cascade = os.environ.get('MODEL_CASCADE', 'false').lower() == 'true'
    self.big_cascade = self._parse_cascade(os.environ.get('BIG_CASCADE', ''))
    self.middle_cascade = self._parse_cascade(os.environ.get('MIDDLE_CASCADE', ''))
    self.small_cascade = self._parse_cascade(os.environ.get('SMALL_CASCADE', ''))
    self.model_cascade_daily_limit = int(os.environ.get('MODEL_CASCADE_DAILY_LIMIT', '1000'))
    _fallback_raw = os.environ.get('FALLBACK_METHOD', 'cascade').lower().replace(' ', '')
    self.fallback_methods: set = set(_fallback_raw.split(','))
    _fallback_str = os.environ.get('OPENROUTER_FALLBACK_MODELS') or ''
    self.openrouter_fallback_models: list = [m.strip() for m in _fallback_str.split(',') if m.strip()]
    try:
        from src.core.proxy_chain import get_chain as _get_chain_rc
        _rc = _get_chain_rc().router
    except Exception:
        from src.core.proxy_chain import RouterConfig, RouteTarget
        _rc = RouterConfig()
    from src.core.proxy_chain import RouteTarget

    def _get_router_env(name: str, fallback_rt) -> RouteTarget:
        model = os.environ.get(f'ROUTER_{name}')
        if model is None:
            model = fallback_rt.model
        url = os.environ.get(f'ROUTER_{name}_URL')
        if url is None:
            url = fallback_rt.base_url
        key = os.environ.get(f'ROUTER_{name}_KEY')
        if key is None:
            key = fallback_rt.api_key
        return RouteTarget(model=model, base_url=url, api_key=key)
    self.router_default = _get_router_env('DEFAULT', _rc.default)
    self.router_background = _get_router_env('BACKGROUND', _rc.background)
    self.router_think = _get_router_env('THINK', _rc.think)
    self.router_long_context = _get_router_env('LONG_CONTEXT', _rc.long_context)
    self.router_long_context_threshold = int(os.environ.get('ROUTER_LONG_CONTEXT_THRESHOLD', str(_rc.long_context_threshold)))
    self.router_web_search = _get_router_env('WEB_SEARCH', _rc.web_search)
    self.router_image = _get_router_env('IMAGE', _rc.image)
    self.router_custom_path = os.environ.get('ROUTER_CUSTOM_PATH', _rc.custom_router_path)
    self.provider_registry: Dict[str, Dict[str, Optional[str]]] = {}
    self._parse_provider_registry()
    self.tier_provider_overrides: Dict[str, str] = {}
    for tier in ('big', 'middle', 'small'):
        override = os.environ.get(f'{tier.upper()}_PROVIDER')
        if override:
            self.tier_provider_overrides[tier] = override.lower()
    self.enable_big_endpoint = os.environ.get('ENABLE_BIG_ENDPOINT', 'false').lower() == 'true'
    self.enable_middle_endpoint = os.environ.get('ENABLE_MIDDLE_ENDPOINT', 'false').lower() == 'true'
    self.enable_small_endpoint = os.environ.get('ENABLE_SMALL_ENDPOINT', 'false').lower() == 'true'
    self.big_endpoint = os.environ.get('BIG_ENDPOINT', self.openai_base_url)
    self.middle_endpoint = os.environ.get('MIDDLE_ENDPOINT', self.openai_base_url)
    self.small_endpoint = os.environ.get('SMALL_ENDPOINT', self.openai_base_url)
    self.big_api_key = self._get_legacy_tier_key('big', self.openai_api_key)
    self.middle_api_key = self._get_legacy_tier_key('middle', self.openai_api_key)
    self.small_api_key = self._get_legacy_tier_key('small', self.openai_api_key)
    self.big_provider = self._get_tier_provider('big')
    self.middle_provider = self._get_tier_provider('middle')
    self.small_provider = self._get_tier_provider('small')
    from src.services.providers.provider_detector import detect_provider
    self.default_provider = os.environ.get('DEFAULT_PROVIDER', detect_provider(self.openai_base_url))
    if 'BIG_PROVIDER' in os.environ:
        self.big_provider = os.environ['BIG_PROVIDER'].lower()
    if 'MIDDLE_PROVIDER' in os.environ:
        self.middle_provider = os.environ['MIDDLE_PROVIDER'].lower()
    if 'SMALL_PROVIDER' in os.environ:
        self.small_provider = os.environ['SMALL_PROVIDER'].lower()
    provider_key_map = {'openrouter': os.environ.get('OPENROUTER_API_KEY'), 'openai': os.environ.get('OPENAI_API_KEY'), 'anthropic': os.environ.get('ANTHROPIC_API_KEY'), 'google': os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY'), 'gemini': os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY'), 'azure': os.environ.get('AZURE_API_KEY') or os.environ.get('AZURE_OPENAI_API_KEY'), 'vibeproxy': self.openai_api_key, 'kiro': os.environ.get('KIRO_ACCESS_TOKEN'), 'local': 'dummy'}
    if self.enable_big_endpoint and self.big_api_key is None:
        auto_key = provider_key_map.get(self.big_provider.lower())
        if auto_key:
            print(f'✅ AUTO: Using {self.big_provider.upper()}_API_KEY for BIG endpoint')
            self.big_api_key = auto_key
        else:
            print(f'⚠️  WARNING: BIG endpoint enabled but no API key found')
            print(f'   → Set BIG_API_KEY or {self.big_provider.upper()}_API_KEY in .env')
    if self.enable_middle_endpoint and self.middle_api_key is None:
        auto_key = provider_key_map.get(self.middle_provider.lower())
        if auto_key:
            print(f'✅ AUTO: Using {self.middle_provider.upper()}_API_KEY for MIDDLE endpoint')
            self.middle_api_key = auto_key
        else:
            print(f'⚠️  WARNING: MIDDLE endpoint enabled but no API key found')
            print(f'   → Set MIDDLE_API_KEY or {self.middle_provider.upper()}_API_KEY in .env')
    if self.enable_small_endpoint and self.small_api_key is None:
        auto_key = provider_key_map.get(self.small_provider.lower())
        if auto_key:
            print(f'✅ AUTO: Using {self.small_provider.upper()}_API_KEY for SMALL endpoint')
            self.small_api_key = auto_key
        else:
            print(f'⚠️  WARNING: SMALL endpoint enabled but no API key found')
            print(f'   → Set SMALL_API_KEY or {self.small_provider.upper()}_API_KEY in .env')
    self.enable_custom_big_prompt = os.environ.get('ENABLE_CUSTOM_BIG_PROMPT', 'false').lower() == 'true'
    self.enable_custom_middle_prompt = os.environ.get('ENABLE_CUSTOM_MIDDLE_PROMPT', 'false').lower() == 'true'
    self.enable_custom_small_prompt = os.environ.get('ENABLE_CUSTOM_SMALL_PROMPT', 'false').lower() == 'true'
    self.big_system_prompt_file = os.environ.get('BIG_SYSTEM_PROMPT_FILE', '')
    self.middle_system_prompt_file = os.environ.get('MIDDLE_SYSTEM_PROMPT_FILE', '')
    self.small_system_prompt_file = os.environ.get('SMALL_SYSTEM_PROMPT_FILE', '')
    self.big_system_prompt = os.environ.get('BIG_SYSTEM_PROMPT', '')
    self.middle_system_prompt = os.environ.get('MIDDLE_SYSTEM_PROMPT', '')
    self.small_system_prompt = os.environ.get('SMALL_SYSTEM_PROMPT', '')
    self.reasoning_effort = os.environ.get('REASONING_EFFORT')
    self.verbosity = os.environ.get('VERBOSITY')
    self.reasoning_exclude = os.environ.get('REASONING_EXCLUDE', 'false').lower() == 'true'
    reasoning_max_tokens = os.environ.get('REASONING_MAX_TOKENS')
    self.reasoning_max_tokens = int(reasoning_max_tokens) if reasoning_max_tokens else None
    self.big_model_reasoning = os.environ.get('BIG_MODEL_REASONING')
    self.middle_model_reasoning = os.environ.get('MIDDLE_MODEL_REASONING')
    self.small_model_reasoning = os.environ.get('SMALL_MODEL_REASONING')
    self._validate_reasoning_config()
    self.enable_dashboard = os.environ.get('ENABLE_DASHBOARD', 'false').lower() == 'true'
    self.dashboard_layout = os.environ.get('DASHBOARD_LAYOUT', 'default')
    self.dashboard_refresh = float(os.environ.get('DASHBOARD_REFRESH', '0.5'))
    self.dashboard_waterfall_size = int(os.environ.get('DASHBOARD_WATERFALL_SIZE', '20'))
    self.track_usage = os.environ.get('TRACK_USAGE', 'true' if self.enable_dashboard else 'false').lower() == 'true'
    self.usage_tracking_db_path = os.environ.get('USAGE_DB_PATH', 'usage_tracking.db')
    self.compact_logger = os.environ.get('COMPACT_LOGGER', 'true' if self.enable_dashboard else 'false').lower() == 'true'
    self.terminal_display_mode = os.environ.get('TERMINAL_DISPLAY_MODE', 'detailed').lower()
    self.terminal_show_workspace = os.environ.get('TERMINAL_SHOW_WORKSPACE', 'true').lower() == 'true'
    self.terminal_show_context_pct = os.environ.get('TERMINAL_SHOW_CONTEXT_PCT', 'true').lower() == 'true'
    self.terminal_show_task_type = os.environ.get('TERMINAL_SHOW_TASK_TYPE', 'true').lower() == 'true'
    self.terminal_show_speed = os.environ.get('TERMINAL_SHOW_SPEED', 'true').lower() == 'true'
    self.terminal_show_cost = os.environ.get('TERMINAL_SHOW_COST', 'true').lower() == 'true'
    self.terminal_show_duration_colors = os.environ.get('TERMINAL_SHOW_DURATION_COLORS', 'true').lower() == 'true'
    self.terminal_color_scheme = os.environ.get('TERMINAL_COLOR_SCHEME', 'auto').lower()
    self.terminal_session_colors = os.environ.get('TERMINAL_SESSION_COLORS', 'true').lower() == 'true'
```

### Method: `_validate_reasoning_config`
**Logic & Purpose:**
```text
Validate reasoning configuration values
```

**Parameters:** `self`
**Variables Used:** `valid_effort_levels`
**Implementation:**
```python
def _validate_reasoning_config(self):
    """Validate reasoning configuration values"""
    valid_effort_levels = {'low', 'medium', 'high'}
    if self.reasoning_effort and self.reasoning_effort.lower() not in valid_effort_levels:
        print(f"Warning: Invalid REASONING_EFFORT '{self.reasoning_effort}'. Valid options: {', '.join(sorted(valid_effort_levels))}. Ignoring.")
        self.reasoning_effort = None
    for model_type, reasoning_value in [('BIG_MODEL_REASONING', self.big_model_reasoning), ('MIDDLE_MODEL_REASONING', self.middle_model_reasoning), ('SMALL_MODEL_REASONING', self.small_model_reasoning)]:
        if reasoning_value and reasoning_value.lower() not in valid_effort_levels:
            print(f"Warning: Invalid {model_type} '{reasoning_value}'. Valid options: {', '.join(sorted(valid_effort_levels))}. Ignoring.")
            if model_type == 'BIG_MODEL_REASONING':
                self.big_model_reasoning = None
            elif model_type == 'MIDDLE_MODEL_REASONING':
                self.middle_model_reasoning = None
            elif model_type == 'SMALL_MODEL_REASONING':
                self.small_model_reasoning = None
    if self.reasoning_max_tokens is not None:
        if self.reasoning_max_tokens < 0:
            print(f'Warning: REASONING_MAX_TOKENS {self.reasoning_max_tokens} is negative. Setting to 0.')
            self.reasoning_max_tokens = 0
        elif self.reasoning_max_tokens > 131072:
            print(f'Warning: REASONING_MAX_TOKENS {self.reasoning_max_tokens} exceeds maximum (131072). Will be adjusted per provider limits.')
```

### Method: `validate_api_key`
**Logic & Purpose:**
```text
Validate API key format with provider-aware validation.

Args:
    api_key: API key to validate. If None, uses self.openai_api_key
    provider: Optional provider name for format validation

Returns:
    True if valid, False otherwise
```

**Parameters:** `self, api_key, provider`
**Variables Used:** `key_to_validate`
**Implementation:**
```python
def validate_api_key(self, api_key: str=None, provider: str=None) -> bool:
    """
        Validate API key format with provider-aware validation.

        Args:
            api_key: API key to validate. If None, uses self.openai_api_key
            provider: Optional provider name for format validation

        Returns:
            True if valid, False otherwise
        """
    key_to_validate = api_key if api_key is not None else self.openai_api_key
    if not key_to_validate:
        return False
    is_valid, _ = validate_api_key_format(key_to_validate, provider)
    return is_valid
```

### Method: `validate_client_api_key`
**Logic & Purpose:**
```text
Validate client's Anthropic API key
```

**Parameters:** `self, client_api_key`
**Implementation:**
```python
def validate_client_api_key(self, client_api_key):
    """Validate client's Anthropic API key"""
    if not self.anthropic_api_key:
        return True
    return client_api_key == self.anthropic_api_key
```

### Method: `get_custom_headers`
**Logic & Purpose:**
```text
Get custom headers from environment variables
```

**Parameters:** `self`
**Variables Used:** `custom_headers, env_vars, header_name`
**Implementation:**
```python
def get_custom_headers(self):
    """Get custom headers from environment variables"""
    custom_headers = {}
    env_vars = dict(os.environ)
    for env_key, env_value in env_vars.items():
        if env_key.startswith('CUSTOM_HEADER_'):
            header_name = env_key[14:]
            if header_name:
                header_name = header_name.replace('_', '-')
                custom_headers[header_name] = env_value
    return custom_headers
```

### Method: `_parse_cascade`
**Logic & Purpose:**
```text
Parse comma-separated cascade list into list of model strings.
```

**Parameters:** `self, cascade_str`
**Implementation:**
```python
def _parse_cascade(self, cascade_str: str) -> list:
    """Parse comma-separated cascade list into list of model strings."""
    if not cascade_str:
        return []
    return [m.strip() for m in cascade_str.split(',') if m.strip()]
```

### Method: `_parse_provider_registry`
**Logic & Purpose:**
```text
Parse PROVIDERS_<name>_URL/_API_KEY env vars into a provider registry.
```

**Parameters:** `self`
**Variables Used:** `key_key, suffix_url, url_key, api_key, url, suffix_key, provider_names, prefix, name`
**Implementation:**
```python
def _parse_provider_registry(self):
    """Parse PROVIDERS_<name>_URL/_API_KEY env vars into a provider registry."""
    prefix = 'PROVIDERS_'
    suffix_url = '_URL'
    suffix_key = '_API_KEY'
    provider_names = set()
    for key in os.environ:
        if key.startswith(prefix) and key.endswith(suffix_url):
            name = key[len(prefix):-len(suffix_url)]
            provider_names.add(name.lower())
    for name in provider_names:
        url_key = f'{prefix}{name}{suffix_url}'
        key_key = os.environ.get(f'{prefix}{name}_API_KEY')
        if key_key is None:
            key_key = os.environ.get(f'{prefix}{name}_KEY')
        url = os.environ.get(url_key, '').strip()
        api_key = (key_key or '').strip() or None
        if url:
            self.provider_registry[name] = {'url': url, 'api_key': api_key}
    if not self.provider_registry:
        self.provider_registry['default'] = {'url': self.openai_base_url, 'api_key': self.openai_api_key}
```

### Method: `_get_tier_provider_from_model`
**Logic & Purpose:**
```text
Extract provider name from the model configured for a tier.
```

**Parameters:** `self, tier`
**Variables Used:** `model_name, model_map`
**Implementation:**
```python
def _get_tier_provider_from_model(self, tier: str) -> str:
    """Extract provider name from the model configured for a tier."""
    model_map = {'big': self.big_model, 'middle': self.middle_model, 'small': self.small_model}
    model_name = model_map.get(tier, '')
    if '/' in model_name:
        return model_name.split('/', 1)[0].lower()
    return 'default'
```

### Method: `_get_tier_provider`
**Logic & Purpose:**
```text
Resolve which provider handles a tier (with override support).
```

**Parameters:** `self, tier`
**Implementation:**
```python
def _get_tier_provider(self, tier: str) -> str:
    """Resolve which provider handles a tier (with override support)."""
    if tier in self.tier_provider_overrides:
        return self.tier_provider_overrides[tier]
    return self._get_tier_provider_from_model(tier)
```

### Method: `get_provider_endpoint`
**Logic & Purpose:**
```text
Get base URL for a provider from the registry.
```

**Parameters:** `self, provider_name`
**Variables Used:** `entry`
**Implementation:**
```python
def get_provider_endpoint(self, provider_name: str) -> Optional[str]:
    """Get base URL for a provider from the registry."""
    entry = self.provider_registry.get(provider_name)
    return entry.get('url') if entry else None
```

### Method: `get_provider_api_key`
**Logic & Purpose:**
```text
Get API key for a provider from the registry.
```

**Parameters:** `self, provider_name`
**Variables Used:** `entry`
**Implementation:**
```python
def get_provider_api_key(self, provider_name: str) -> Optional[str]:
    """Get API key for a provider from the registry."""
    entry = self.provider_registry.get(provider_name)
    return entry.get('api_key') if entry else None
```

### Method: `_get_legacy_tier_key`
**Logic & Purpose:**
```text
Get API key for a tier using provider registry first, then legacy env vars.
```

**Parameters:** `self, tier, fallback`
**Variables Used:** `reg_key, key, env_key, provider`
**Implementation:**
```python
def _get_legacy_tier_key(self, tier: str, fallback: Optional[str]) -> Optional[str]:
    """Get API key for a tier using provider registry first, then legacy env vars."""
    provider = self._get_tier_provider(tier)
    reg_key = self.get_provider_api_key(provider)
    if reg_key:
        return reg_key
    env_key = f'{tier.upper()}_API_KEY'
    key = os.environ.get(env_key)
    if key:
        return key
    return fallback
```

### Method: `get_cascade_for_tier`
**Logic & Purpose:**
```text
Get cascade list for a model tier (big, middle, small).
```

**Parameters:** `self, tier`
**Variables Used:** `cascades`
**Implementation:**
```python
def get_cascade_for_tier(self, tier: str) -> list:
    """Get cascade list for a model tier (big, middle, small)."""
    cascades = {'big': self.big_cascade, 'middle': self.middle_cascade, 'small': self.small_cascade}
    return cascades.get(tier.lower(), [])
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/client.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/client.py`

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
asyncio, json, logging, os, fastapi.HTTPException, typing.Optional, typing.AsyncGenerator, typing.Dict, typing.Any, typing.Tuple, openai.AsyncOpenAI, openai.AsyncAzureOpenAI, openai.types.chat.ChatCompletion, openai.types.chat.ChatCompletionChunk, openai._exceptions.APIError, openai._exceptions.RateLimitError, openai._exceptions.AuthenticationError, openai._exceptions.BadRequestError

## Feature Function: `_get_circuit_breaker`
**Logic & Purpose:**
```text
Return (or lazily create) the circuit breaker for a model via the registry.
```

**Parameters:** `model`
**Implementation:**
```python
def _get_circuit_breaker(model: str):
    """Return (or lazily create) the circuit breaker for a model via the registry."""
    from src.core.circuit_breaker import get_circuit_breaker_registry
    return get_circuit_breaker_registry().get_sync(name=model, failure_threshold=3, success_threshold=1, timeout=300.0)
```

---

## Feature Function: `_is_cb_open`
**Logic & Purpose:**
```text
Return True if the circuit breaker for this model is OPEN (should be skipped).
```

**Parameters:** `model`
**Variables Used:** `registry`
**Implementation:**
```python
def _is_cb_open(model: str) -> bool:
    """Return True if the circuit breaker for this model is OPEN (should be skipped)."""
    from src.core.circuit_breaker import get_circuit_breaker_registry
    registry = get_circuit_breaker_registry()
    if model not in registry._breakers:
        return False
    return registry._breakers[model].is_open
```

---

## Feature Function: `_build_or_models_list`
**Logic & Purpose:**
```text
Build the ordered model list for OR native injection, filtering out any
models whose circuit breakers are currently OPEN.

Dead models in the OR `models` array waste OR's routing budget evaluating
endpoints we already know are broken.  The primary model is always kept
as the first entry (OR needs at least one model to route).
```

**Parameters:** `primary, fallback_models`
**Variables Used:** `candidates, filtered`
**Implementation:**
```python
def _build_or_models_list(primary: str, fallback_models: list) -> list:
    """
    Build the ordered model list for OR native injection, filtering out any
    models whose circuit breakers are currently OPEN.

    Dead models in the OR `models` array waste OR's routing budget evaluating
    endpoints we already know are broken.  The primary model is always kept
    as the first entry (OR needs at least one model to route).
    """
    candidates = [primary] + [m for m in fallback_models if m != primary]
    filtered = [m for m in candidates if not _is_cb_open(m)]
    if not filtered:
        filtered = [primary]
    return filtered[:3]
```

---

## Feature Function: `_get_dynamic_fallback_models`
**Logic & Purpose:**
```text
Return the top tool-capable free models from the cached rankings file.
Falls back to an empty list if the cache doesn't exist yet.
Only models that *support_tools* are included — unusable for agentic tasks otherwise.
```

**Parameters:** `limit`
**Variables Used:** `capable, rankings`
**Implementation:**
```python
def _get_dynamic_fallback_models(limit: int=10) -> list:
    """
    Return the top tool-capable free models from the cached rankings file.
    Falls back to an empty list if the cache doesn't exist yet.
    Only models that *support_tools* are included — unusable for agentic tasks otherwise.
    """
    try:
        from src.services.models.free_model_rankings import load_free_model_rankings, RANKINGS_PATH
        rankings = load_free_model_rankings(RANKINGS_PATH)
        capable = [r.model_id for r in rankings if r.supports_tools]
        return capable[:limit]
    except Exception:
        return []
```

---

## Feature Class: `VibeProxyUnavailableError`
**Description:**
```text
Raised when VibeProxy is not available.
```

---

## Feature Class: `OpenAIClient`
**Description:**
```text
Async OpenAI client with cancellation support and multi-endpoint routing.
```

### Method: `__init__`
**Parameters:** `self, api_key, base_url, timeout, api_version, custom_headers`
**Implementation:**
```python
def __init__(self, api_key: str, base_url: str, timeout: int=90, api_version: Optional[str]=None, custom_headers: Optional[Dict[str, str]]=None):
    if custom_headers is not None:
        if not isinstance(custom_headers, dict):
            raise ValueError('custom_headers must be a dictionary')
        if not all((isinstance(k, str) and isinstance(v, str) for k, v in custom_headers.items())):
            raise ValueError('custom_headers must contain only string keys and values')
    self.default_api_key = api_key
    self.default_base_url = base_url
    self.default_api_version = api_version
    self.timeout = timeout
    self.custom_headers = custom_headers
    self.client = self._create_client(api_key, base_url, api_version, custom_headers)
    self._provider_clients: Dict[str, Any] = {}
    self._config = None
    self._vibeproxy_available = None
    self._vibeproxy_error = None
    self.active_requests: Dict[str, asyncio.Event] = {}
```

### Method: `_create_client`
**Logic & Purpose:**
```text
Create an OpenAI or Azure client.
```

**Parameters:** `self, api_key, base_url, api_version, custom_headers, check_health`
**Variables Used:** `kiro_manager, is_vibeproxy, is_kiro, token, api_key, timestamp, antigravity_token, provider`
**Implementation:**
```python
def _create_client(self, api_key: str, base_url: str, api_version: Optional[str]=None, custom_headers: Optional[Dict[str, str]]=None, check_health: bool=True):
    """Create an OpenAI or Azure client."""
    import time
    timestamp = time.strftime('%H:%M:%S')
    from src.services.providers.provider_detector import detect_provider, requires_kiro_token
    provider = detect_provider(base_url)
    is_vibeproxy = '127.0.0.1:8317' in base_url or 'localhost:8317' in base_url
    is_kiro = requires_kiro_token(base_url)
    if is_kiro:
        from src.services.providers.kiro_token_manager import get_token_manager
        logger.debug(f'[Kiro {timestamp}] CLIENT CREATION for Kiro provider')
        kiro_manager = get_token_manager()
        token = kiro_manager.get_access_token()
        if token:
            logger.debug(f'[Kiro {timestamp}] Using Kiro access token (first 8 chars): {token[:8]}...')
            api_key = token
        else:
            logger.error(f'[Kiro {timestamp}] No Kiro token found! Authentication will FAIL.')
            logger.error(f'[Kiro {timestamp}] Please set Kiro tokens via /api/providers/kiro/tokens endpoint')
    elif is_vibeproxy:
        if check_health:
            from src.services.antigravity import check_vibeproxy_health
            available, error_msg = check_vibeproxy_health()
            if not available:
                logger.warning(f'[VibeProxy {timestamp}] VibeProxy/CLIProxyAPI is NOT available: {error_msg}')
                self._vibeproxy_available = False
                self._vibeproxy_error = error_msg
            else:
                self._vibeproxy_available = True
                self._vibeproxy_error = None
        if api_key and api_key not in ('dummy', 'your-api-key-here', ''):
            logger.debug(f'[VibeProxy {timestamp}] Using provided API key for CLIProxyAPI (first 8 chars): {api_key[:8]}...')
        else:
            from src.services.antigravity import get_antigravity_token
            logger.debug(f'[VibeProxy {timestamp}] No explicit API key - fetching Antigravity token...')
            antigravity_token = get_antigravity_token()
            if antigravity_token:
                logger.debug(f'[VibeProxy {timestamp}] Token retrieved successfully (first 8 chars): {antigravity_token[:8]}...')
                api_key = antigravity_token
            else:
                logger.error(f'[VibeProxy {timestamp}] No Antigravity token found! Authentication will FAIL.')
                logger.error(f"[VibeProxy {timestamp}] Please ensure you're logged into Antigravity IDE.")
    if is_vibeproxy:
        logger.debug(f'[VibeProxy {timestamp}] Creating NEW OpenAI client instance')
        logger.debug(f'[VibeProxy {timestamp}] Endpoint: {base_url}')
        logger.debug(f"[VibeProxy {timestamp}] Token in use (first 8 chars): {(api_key[:8] if api_key else 'None')}...")
        logger.debug(f'[VibeProxy {timestamp}] Custom headers: {custom_headers}')
    elif is_kiro:
        logger.debug(f'[Kiro {timestamp}] Creating NEW OpenAI client instance for Kiro')
        logger.debug(f'[Kiro {timestamp}] Endpoint: {base_url}')
        logger.debug(f'[Kiro {timestamp}] Custom headers: {custom_headers}')
    if is_kiro and (not api_key):
        api_key = os.environ.get('KIRO_ACCESS_TOKEN', '')
    if not api_key:
        api_key = 'passthrough-no-server-key'
    if api_version:
        return AsyncAzureOpenAI(api_key=api_key, azure_endpoint=base_url, api_version=api_version, timeout=self.timeout, default_headers=custom_headers)
    else:
        return AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=self.timeout, default_headers=custom_headers)
```

### Method: `configure_per_model_clients`
**Logic & Purpose:**
```text
Store config reference for per-request routing.
```

**Parameters:** `self, config`
**Implementation:**
```python
def configure_per_model_clients(self, config):
    """Store config reference for per-request routing."""
    self._config = config
```

### Method: `_get_provider_client`
**Logic & Purpose:**
```text
Get or lazily create a client for a registered provider.
```

**Parameters:** `self, provider_name`
**Variables Used:** `url, key, client, config`
**Implementation:**
```python
def _get_provider_client(self, provider_name: str) -> Any:
    """Get or lazily create a client for a registered provider."""
    if provider_name in self._provider_clients:
        return self._provider_clients[provider_name]
    config = self._config
    if not config:
        return None
    url = config.get_provider_endpoint(provider_name)
    key = config.get_provider_api_key(provider_name)
    if url is None:
        return None
    if key is None:
        key = self.default_api_key
    client = self._create_client(key, url, self.default_api_version, self.custom_headers)
    self._provider_clients[provider_name] = client
    return client
```

### Method: `_resolve_provider_for_tier`
**Logic & Purpose:**
```text
Determine the provider name for a tier's configured model.
```

**Parameters:** `self, config, tier_model, tier_lower`
**Variables Used:** `override, prefix`
**Implementation:**
```python
def _resolve_provider_for_tier(self, config, tier_model: str, tier_lower: str) -> str:
    """Determine the provider name for a tier's configured model."""
    if not tier_model:
        return ''
    override = config.tier_provider_overrides.get(tier_lower)
    if override:
        return override
    if '/' in tier_model:
        prefix = tier_model.split('/', 1)[0].lower()
        if prefix in config.provider_registry:
            return prefix
    return 'default'
```

### Method: `get_client_for_model`
**Logic & Purpose:**
```text
Resolve provider client for a model using the provider registry.

Logic:
1. Compare the model name (with/without provider prefix) against each tier's configured model
2. If matched, route to that tier's resolved provider
3. Fall back to the default client (OpenRouter)
```

**Parameters:** `self, model, config`
**Variables Used:** `timestamp, tiers, stripped_requested, raw_requested, stripped_config, provider, tier_lower, client`
**Implementation:**
```python
def get_client_for_model(self, model: str, config=None) -> Any:
    """Resolve provider client for a model using the provider registry.

        Logic:
        1. Compare the model name (with/without provider prefix) against each tier's configured model
        2. If matched, route to that tier's resolved provider
        3. Fall back to the default client (OpenRouter)
        """
    import time
    timestamp = time.strftime('%H:%M:%S')
    if not config:
        return self.client

    def norm(name: str) -> str:
        if name and '/' in name:
            return name.split('/', 1)[1]
        return name or ''
    raw_requested = model
    stripped_requested = norm(model)
    tiers = [('BIG', config.big_model), ('MIDDLE', config.middle_model), ('SMALL', config.small_model)]
    for tier_name, configured_model in tiers:
        if not configured_model:
            continue
        stripped_config = norm(configured_model)
        tier_lower = tier_name.lower()
        if raw_requested == configured_model or raw_requested == stripped_config or stripped_requested == configured_model or (stripped_requested == stripped_config):
            provider = self._resolve_provider_for_tier(config, configured_model, tier_lower)
            client = self._get_provider_client(provider)
            if client:
                logger.debug(f"[Client Selection {timestamp}] {tier_name}→provider '{provider}' for '{model}'")
                return client
            logger.debug(f"[Client Selection {timestamp}] {tier_name} matched but provider '{provider}' not in registry, using DEFAULT")
            return self.client
    logger.debug(f"[Client Selection {timestamp}] No tier matched for '{model}', using DEFAULT client")
    return self.client
```

### Method: `create_chat_completion`
**Logic & Purpose:**
```text
Send chat completion to OpenAI API with cancellation support.

Args:
    request: OpenAI request dictionary
    request_id: Optional request ID for cancellation tracking
    config: Optional config object
    api_key: Optional per-request API key (for passthrough mode)
```

**Parameters:** `self, request, request_id, config, api_key`
**Variables Used:** `fresh_token, status_code, or_models, is_vibeproxy, request, base_url, timestamp, cancel_event, big_api_key, completion, primary, auth, completion_task, cancel_task, client, model, fallback_models`
**Implementation:**
```python
async def create_chat_completion(self, request: Dict[str, Any], request_id: Optional[str]=None, config=None, api_key: Optional[str]=None) -> Dict[str, Any]:
    """Send chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
    import time
    timestamp = time.strftime('%H:%M:%S')
    if api_key:
        client = self._create_client(api_key, config.openai_base_url if config else self.default_base_url, config.azure_api_version if config else self.default_api_version, self.custom_headers)
    else:
        client = self.get_client_for_model(request.get('model', ''), config)
        model = request.get('model', '')
        base_url = str(client.base_url)
        is_vibeproxy = '127.0.0.1:8317' in base_url or 'localhost:8317' in base_url
        if is_vibeproxy:
            from src.services.antigravity import check_vibeproxy_health
            available, error_msg = check_vibeproxy_health()
            if not available:
                logger.error(f'[VibeProxy {timestamp}] CLIProxyAPI/VibeProxy is NOT available: {error_msg}')
                raise VibeProxyUnavailableError(f'VibeProxy is not available: {error_msg}. Please ensure CLIProxyAPI or Antigravity IDE is running. Alternatively, use a different model/provider.')
            big_api_key = config.big_api_key if config else None
            if big_api_key and big_api_key not in ('dummy', 'your-api-key-here', ''):
                logger.debug(f'[VibeProxy {timestamp}] CLIProxyAPI mode - using provided API key, skipping token refresh')
            else:
                from src.services.antigravity import get_antigravity_auth
                logger.debug(f'[VibeProxy {timestamp}] Refreshing client with fresh Antigravity token for request')
                auth = get_antigravity_auth()
                fresh_token = auth.get_token(force_refresh=True)
                if fresh_token:
                    logger.debug(f'[VibeProxy {timestamp}] Creating new client with fresh token (first 8 chars): {fresh_token[:8]}...')
                    client = self._create_client(fresh_token, base_url, config.azure_api_version if config else self.default_api_version, self.custom_headers, check_health=False)
                else:
                    logger.error(f'[VibeProxy {timestamp}] Failed to retrieve fresh token! Using cached client (may fail)')
    if config and 'openrouter_native' in getattr(config, 'fallback_methods', set()):
        base_url = str(client.base_url)
        if 'openrouter.ai' in base_url or '8787' in base_url:
            fallback_models = getattr(config, 'openrouter_fallback_models', [])
            primary = request.get('model', '')
            if fallback_models and primary not in ('', None):
                or_models = _build_or_models_list(primary, fallback_models)
                request = {**request, 'model': or_models[0], 'extra_body': {**request.get('extra_body', {}), 'models': or_models, 'provider': {**request.get('extra_body', {}).get('provider', {}), 'require_parameters': True, 'sort': {'by': 'throughput', 'partition': 'none'}}}}
    if request_id:
        cancel_event = asyncio.Event()
        self.active_requests[request_id] = cancel_event
    try:
        completion_task = asyncio.create_task(client.chat.completions.create(**request))
        if request_id:
            cancel_task = asyncio.create_task(cancel_event.wait())
            done, pending = await asyncio.wait([completion_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if cancel_task in done:
                completion_task.cancel()
                raise HTTPException(status_code=499, detail='Request cancelled by client')
            completion = await completion_task
        else:
            completion = await completion_task
        return completion.model_dump()
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
    except APIError as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unexpected error: {str(e)}')
    finally:
        if request_id and request_id in self.active_requests:
            del self.active_requests[request_id]
```

### Method: `create_chat_completion_stream`
**Logic & Purpose:**
```text
Send streaming chat completion to OpenAI API with cancellation support.

Args:
    request: OpenAI request dictionary
    request_id: Optional request ID for cancellation tracking
    config: Optional config object
    api_key: Optional per-request API key (for passthrough mode)
```

**Parameters:** `self, request, request_id, config, api_key`
**Variables Used:** `chunk_json, timestamp, streaming_completion, auth, cancel_event, or_models, big_api_key, primary, small_client, client, chunk_dict, is_small_tier, model, fallback_models, fresh_token, status_code, is_vibeproxy, request, base_url`
**Implementation:**
```python
async def create_chat_completion_stream(self, request: Dict[str, Any], request_id: Optional[str]=None, config=None, api_key: Optional[str]=None) -> AsyncGenerator[str, None]:
    """Send streaming chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
    import time
    timestamp = time.strftime('%H:%M:%S')
    if api_key:
        client = self._create_client(api_key, config.openai_base_url if config else self.default_base_url, config.azure_api_version if config else self.default_api_version, self.custom_headers)
    else:
        client = self.get_client_for_model(request.get('model', ''), config)
        model = request.get('model', '')
        small_client = getattr(self, 'small_client', None)
        is_small_tier = config and small_client and (model == config.small_model)
        base_url = str(client.base_url)
        is_vibeproxy = '127.0.0.1:8317' in base_url or 'localhost:8317' in base_url
        if is_vibeproxy:
            big_api_key = config.big_api_key if config else None
            if big_api_key and big_api_key not in ('dummy', 'your-api-key-here', ''):
                logger.debug(f'[VibeProxy {timestamp}] CLIProxyAPI mode - using provided API key for streaming, skipping token refresh')
            else:
                logger.debug(f'[VibeProxy {timestamp}] Refreshing client with fresh Antigravity token for streaming request')
                from src.services.antigravity import get_antigravity_auth
                auth = get_antigravity_auth()
                fresh_token = auth.get_token(force_refresh=True)
                if fresh_token:
                    logger.debug(f'[VibeProxy {timestamp}] Creating new client with fresh token (first 8 chars): {fresh_token[:8]}...')
                    client = self._create_client(fresh_token, base_url, config.azure_api_version if config else self.default_api_version, self.custom_headers)
                else:
                    logger.error(f'[VibeProxy {timestamp}] Failed to retrieve fresh token! Using cached client (may fail)')
        elif is_small_tier:
            logger.debug(f'[Client Selection {timestamp}] SMALL tier streaming - routing to {config.small_endpoint} (not VibeProxy)')
    if config and 'openrouter_native' in getattr(config, 'fallback_methods', set()):
        base_url = str(client.base_url)
        if 'openrouter.ai' in base_url or '8787' in base_url:
            fallback_models = getattr(config, 'openrouter_fallback_models', [])
            primary = request.get('model', '')
            if fallback_models and primary not in ('', None):
                or_models = _build_or_models_list(primary, fallback_models)
                request = {**request, 'model': or_models[0], 'extra_body': {**request.get('extra_body', {}), 'models': or_models, 'provider': {**request.get('extra_body', {}).get('provider', {}), 'require_parameters': True, 'sort': {'by': 'throughput', 'partition': 'none'}}}}
    if request_id:
        cancel_event = asyncio.Event()
        self.active_requests[request_id] = cancel_event
    try:
        if 'stream_options' not in request:
            request['stream_options'] = {}
        request['stream_options']['include_usage'] = True
        request['stream'] = True
        streaming_completion = await client.chat.completions.create(**request)
        async for chunk in streaming_completion:
            if request_id and request_id in self.active_requests:
                if self.active_requests[request_id].is_set():
                    raise HTTPException(status_code=499, detail='Request cancelled by client')
            chunk_dict = chunk.model_dump()
            chunk_json = json.dumps(chunk_dict, ensure_ascii=False)
            yield f'data: {chunk_json}'
        yield 'data: [DONE]'
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
    except APIError as e:
        status_code = getattr(e, 'status_code', 500)
        raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unexpected error: {str(e)}')
    finally:
        if request_id and request_id in self.active_requests:
            del self.active_requests[request_id]
```

### Method: `classify_openai_error`
**Logic & Purpose:**
```text
Provide specific error guidance for common API issues.
```

**Parameters:** `self, error_detail`
**Variables Used:** `error_str`
**Implementation:**
```python
def classify_openai_error(self, error_detail: Any) -> str:
    """Provide specific error guidance for common API issues."""
    error_str = str(error_detail).lower()
    logger.debug(f'Classifying error: {error_str}')
    if 'gemini code assist license' in error_str or 'subscription_required' in error_str:
        return 'Gemini Code Assist license required. Your Google Cloud Project needs a Gemini Code Assist license. Contact your administrator or use a different model/provider.'
    if 'auth_unavailable' in error_str or 'no auth available' in error_str:
        return "VibeProxy authentication unavailable. Please ensure Antigravity IDE is running and you're logged in. Try restarting Antigravity IDE."
    if 'permission_denied' in error_str and ('googleapis' in error_str or 'cloudaicompanion' in error_str):
        return 'Google Cloud permission denied. Check your Gemini/Antigravity credentials and project permissions.'
    if 'unsupported_country_region_territory' in error_str or 'country, region, or territory not supported' in error_str:
        return 'API is not available in your region. Consider using a VPN or different provider.'
    if 'invalid_api_key' in error_str or 'unauthorized' in error_str or 'user not found' in error_str:
        return 'Invalid API key or user not found. Please check your OPENAI_API_KEY configuration and ensure your provider account is active. Note: OPENAI_API_KEY is used for any provider (OpenRouter, OpenAI, Azure, etc.)'
    if 'rate_limit' in error_str or 'quota' in error_str:
        return 'Rate limit exceeded. Please wait and try again, or upgrade your API plan with your provider.'
    if 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str):
        return 'Model not found. Please check your BIG_MODEL and SMALL_MODEL configuration.'
    if 'billing' in error_str or 'payment' in error_str:
        return 'Billing issue. Please check your provider account billing status.'
    return str(error_detail)
```

### Method: `cancel_request`
**Logic & Purpose:**
```text
Cancel an active request by request_id.
```

**Parameters:** `self, request_id`
**Implementation:**
```python
def cancel_request(self, request_id: str) -> bool:
    """Cancel an active request by request_id."""
    if request_id in self.active_requests:
        self.active_requests[request_id].set()
        return True
    return False
```

### Method: `create_chat_completion_with_cascade`
**Logic & Purpose:**
```text
Chat completion with cascade fallback on provider errors.

Args:
    request: OpenAI request dictionary
    tier: Model tier (big, middle, small)
    config: Config object with cascade settings
    request_id: Optional request ID for cancellation
    api_key: Optional per-request API key

Returns:
    ChatCompletion from first successful model
```

**Parameters:** `self, request, tier, config, request_id, api_key`
**Variables Used:** `primary_model, daily_limit, dynamic_models, model_idx, cb, last_error, timestamp, result, next_model, daily_count, backoff, cascade_models, retry_counts, error_str, MAX_RETRIES_BEFORE_CASCADE, is_alibaba_rampup, model, current_request`
**Implementation:**
```python
async def create_chat_completion_with_cascade(self, request: Dict[str, Any], tier: str, config=None, request_id: Optional[str]=None, api_key: Optional[str]=None):
    """
        Chat completion with cascade fallback on provider errors.
        
        Args:
            request: OpenAI request dictionary
            tier: Model tier (big, middle, small)
            config: Config object with cascade settings
            request_id: Optional request ID for cancellation
            api_key: Optional per-request API key
        
        Returns:
            ChatCompletion from first successful model
        """
    import ssl
    import httpx
    import time
    from src.api.websocket_logs import log_cascade
    from src.services.usage.usage_tracker import usage_tracker
    if not config or not config.model_cascade:
        return await self.create_chat_completion(request, request_id, config, api_key)
    primary_model = request.get('model', '')
    cascade_models = config.get_cascade_for_tier(tier)
    dynamic_models = _get_dynamic_fallback_models(limit=8)
    seen: set = set()
    models_to_try: list = []
    for m in [primary_model] + cascade_models + dynamic_models:
        if m and m not in seen:
            seen.add(m)
            models_to_try.append(m)
    timestamp = time.strftime('%H:%M:%S')
    last_error = None
    retry_counts = {}
    MAX_RETRIES_BEFORE_CASCADE = 5
    model_idx = 0
    while model_idx < len(models_to_try):
        model = models_to_try[model_idx]
        if not model:
            model_idx += 1
            continue
        cb = _get_circuit_breaker(model)
        if cb.is_open:
            import time as _time
            logger.debug(f"[CASCADE {_time.strftime('%H:%M:%S')}] ⚡ Circuit OPEN for {model} — skipping")
            model_idx += 1
            continue
        daily_limit = getattr(config, 'model_cascade_daily_limit', 0) if config else 0
        if daily_limit and usage_tracker.enabled:
            daily_count = usage_tracker.get_daily_model_request_count(model)
            if daily_count >= daily_limit:
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                print(f'[CASCADE {timestamp}] ⏭️  Skipping {model} (UTC-day requests={daily_count} >= threshold={daily_limit})')
                log_cascade(model=model, action='switch', tier=tier, reason='daily_limit_threshold', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts.get(model, 0))
                model_idx += 1
                continue
        if model not in retry_counts:
            retry_counts[model] = 0
        try:
            current_request = {**request, 'model': model}
            if model_idx > 0 and retry_counts[model] == 0:
                print(f'[CASCADE {timestamp}] ⚡ Trying fallback model: {model}')
                log_cascade(model=model, action='switch', tier=tier, reason='fallback_attempt', from_model=models_to_try[model_idx - 1], to_model=model, request_id=request_id, retry_count=retry_counts[model])
            result = await self.create_chat_completion(current_request, request_id, config, api_key)
            cb = _get_circuit_breaker(model)
            cb._record_success()
            cb.record_parse_ok(result)
            if model_idx > 0:
                print(f'[CASCADE {timestamp}] ✅ Success with fallback: {model}')
                log_cascade(model=model, action='success', tier=tier, reason='fallback_success', request_id=request_id)
            return result
        except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
            _get_circuit_breaker(model)._record_failure(e)
            print(f'[CASCADE {timestamp}] 🔒 SSL/Cert error on {model} - switching immediately: {e}')
            next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
            log_cascade(model=model, action='switch', tier=tier, reason='ssl_error', from_model=model, to_model=next_model, request_id=request_id, error=str(e))
            last_error = e
            model_idx += 1
            continue
        except httpx.ConnectError as e:
            retry_counts[model] += 1
            print(f'[CASCADE {timestamp}] ⚠️  Connection error on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}): {e}')
            log_cascade(model=model, action='retry', tier=tier, reason='connect_error', request_id=request_id, retry_count=retry_counts[model], error=str(e))
            last_error = e
            if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='max_connect_retries', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                model_idx += 1
            continue
        except httpx.TimeoutException as e:
            retry_counts[model] += 1
            print(f'[CASCADE {timestamp}] ⚠️  Timeout on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}): {e}')
            log_cascade(model=model, action='retry', tier=tier, reason='timeout_error', request_id=request_id, retry_count=retry_counts[model], error=str(e))
            last_error = e
            if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='max_timeout_retries', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                model_idx += 1
            continue
        except RateLimitError as e:
            error_str = str(e).lower()
            is_alibaba_rampup = 'rate increased too quickly' in error_str or 'scale requests more smoothly' in error_str
            if is_alibaba_rampup:
                print(f'[CASCADE {timestamp}] 🐌 Alibaba ramp-up limit on {model} — cascading immediately to next provider')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='alibaba_rampup_cascade', from_model=model, to_model=next_model, request_id=request_id, error=str(e))
                last_error = e
                model_idx += 1
                continue
            retry_counts[model] += 1
            import random as _random
            backoff = min(30.0, 2 ** min(retry_counts[model], 4) * _random.uniform(0.8, 1.2))
            print(f'[CASCADE {timestamp}] ⚠️  Rate limit on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}), backoff {backoff:.1f}s: {e}')
            log_cascade(model=model, action='retry', tier=tier, reason='rate_limit', request_id=request_id, retry_count=retry_counts[model], error=str(e))
            last_error = e
            if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='max_rate_limit_retries', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                model_idx += 1
            await asyncio.sleep(backoff)
            continue
        except (BadRequestError, AuthenticationError) as e:
            _get_circuit_breaker(model)._record_failure(e)
            print(f'[CASCADE {timestamp}] 🚫 Request error on {model} - switching immediately: {e}')
            next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
            log_cascade(model=model, action='switch', tier=tier, reason='request_error', from_model=model, to_model=next_model, request_id=request_id, error=str(e))
            last_error = e
            model_idx += 1
            continue
        except APIError as e:
            if hasattr(e, 'status_code') and e.status_code in [502, 503, 504]:
                retry_counts[model] += 1
                print(f'[CASCADE {timestamp}] ⚠️  Server error {e.status_code} on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE})')
                log_cascade(model=model, action='retry', tier=tier, reason=f'server_error_{e.status_code}', request_id=request_id, retry_count=retry_counts[model], error=str(e))
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                    next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                    log_cascade(model=model, action='switch', tier=tier, reason=f'max_server_error_{e.status_code}_retries', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                    model_idx += 1
                continue
            raise
    try:
        from src.core.circuit_breaker import get_circuit_breaker_registry
        get_circuit_breaker_registry().save_all()
    except Exception:
        pass
    print(f'[CASCADE {timestamp}] ❌ All cascade models exhausted')
    log_cascade(model=primary_model, action='exhausted', tier=tier, reason='all_models_failed', request_id=request_id, error=str(last_error) if last_error else None)
    if last_error:
        raise last_error
    raise APIError('All cascade models failed')
```

### Method: `create_chat_completion_stream_with_cascade`
**Logic & Purpose:**
```text
Streaming chat completion with cascade fallback on provider errors.

Args:
    request: OpenAI request dictionary
    tier: Model tier (big, middle, small)
    config: Config object with cascade settings
    request_id: Optional request ID for cancellation
    api_key: Optional per-request API key

Yields:
    OpenAI-format SSE lines ("data: ...")
```

**Parameters:** `self, request, tier, config, request_id, api_key`
**Variables Used:** `last_error, timestamp, next_model, daily_count, max_retries_before_cascade, is_alibaba_rampup, delta, current_request, _stream_had_tool_calls, daily_limit, chunk, cascade_models, retry_counts, error_str, stream, backoff, _stream_had_content, c, model, emitted_any_chunk, status_code, primary_model, _cb_stream, model_idx, _stream_finish_reason, choices, models_to_try`
**Implementation:**
```python
async def create_chat_completion_stream_with_cascade(self, request: Dict[str, Any], tier: str, config=None, request_id: Optional[str]=None, api_key: Optional[str]=None) -> AsyncGenerator[str, None]:
    """
        Streaming chat completion with cascade fallback on provider errors.

        Args:
            request: OpenAI request dictionary
            tier: Model tier (big, middle, small)
            config: Config object with cascade settings
            request_id: Optional request ID for cancellation
            api_key: Optional per-request API key

        Yields:
            OpenAI-format SSE lines ("data: ...")
        """
    import ssl
    import httpx
    import time
    from src.api.websocket_logs import log_cascade
    from src.services.usage.usage_tracker import usage_tracker
    if not config or not config.model_cascade:
        async for line in self.create_chat_completion_stream(request, request_id, config, api_key):
            yield line
        return
    primary_model = request.get('model', '')
    cascade_models = config.get_cascade_for_tier(tier)
    models_to_try = []
    for model_name in [primary_model] + cascade_models:
        if model_name and model_name not in models_to_try:
            models_to_try.append(model_name)
    timestamp = time.strftime('%H:%M:%S')
    last_error = None
    retry_counts = {}
    max_retries_before_cascade = 5
    model_idx = 0
    while model_idx < len(models_to_try):
        model = models_to_try[model_idx]
        if model not in retry_counts:
            retry_counts[model] = 0
        _cb_stream = _get_circuit_breaker(model)
        if _cb_stream.is_open:
            import time as _t
            logger.debug(f"[CASCADE {_t.strftime('%H:%M:%S')}] ⚡ Circuit OPEN for {model} (stream) — skipping")
            model_idx += 1
            continue
        daily_limit = getattr(config, 'model_cascade_daily_limit', 0) if config else 0
        if daily_limit and usage_tracker.enabled:
            daily_count = usage_tracker.get_daily_model_request_count(model)
            if daily_count >= daily_limit:
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                print(f'[CASCADE {timestamp}] ⏭️  Skipping {model} (stream) (UTC-day requests={daily_count} >= threshold={daily_limit})')
                log_cascade(model=model, action='switch', tier=tier, reason='daily_limit_threshold_stream', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                model_idx += 1
                continue
        current_request = {**request, 'model': model}
        emitted_any_chunk = False
        _stream_finish_reason: Optional[str] = None
        _stream_had_tool_calls = False
        _stream_had_content = False
        try:
            if model_idx > 0 and retry_counts[model] == 0:
                print(f'[CASCADE {timestamp}] ⚡ Trying fallback model (stream): {model}')
                log_cascade(model=model, action='switch', tier=tier, reason='fallback_attempt_stream', from_model=models_to_try[model_idx - 1], to_model=model, request_id=request_id, retry_count=retry_counts[model])
            stream = self.create_chat_completion_stream(current_request, request_id, config, api_key)
            async for line in stream:
                emitted_any_chunk = True
                if line.startswith('data: {'):
                    try:
                        chunk = json.loads(line[6:])
                        choices = chunk.get('choices', [])
                        if choices:
                            c = choices[0]
                            if c.get('finish_reason'):
                                _stream_finish_reason = c['finish_reason']
                            delta = c.get('delta', {}) or {}
                            if delta.get('tool_calls'):
                                _stream_had_tool_calls = True
                            if delta.get('content'):
                                _stream_had_content = True
                    except Exception:
                        pass
                yield line
            _get_circuit_breaker(model)._record_success()
            _get_circuit_breaker(model).record_stream_finish(_stream_finish_reason, _stream_had_tool_calls, _stream_had_content)
            if model_idx > 0:
                print(f'[CASCADE {timestamp}] ✅ Streaming success with fallback: {model}')
                log_cascade(model=model, action='success', tier=tier, reason='fallback_success_stream', request_id=request_id)
            return
        except HTTPException as e:
            if emitted_any_chunk:
                raise
            last_error = e
            status_code = e.status_code
            if status_code in (400, 401):
                print(f'[CASCADE {timestamp}] 🚫 Streaming request error on {model} - switching immediately: {e.detail}')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='request_error_stream', from_model=model, to_model=next_model, request_id=request_id, error=str(e.detail))
                model_idx += 1
                continue
            if status_code == 429:
                error_str = str(e.detail).lower()
                is_alibaba_rampup = 'rate increased too quickly' in error_str or 'scale requests more smoothly' in error_str
                if is_alibaba_rampup:
                    print(f'[CASCADE {timestamp}] 🐌 Alibaba ramp-up limit on {model} (stream) — cascading immediately to next provider')
                    next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                    log_cascade(model=model, action='switch', tier=tier, reason='alibaba_rampup_cascade_stream', from_model=model, to_model=next_model, request_id=request_id, error=str(e.detail))
                    last_error = e
                    model_idx += 1
                    continue
                import random as _random
                retry_counts[model] += 1
                backoff = min(30.0, 2 ** min(retry_counts[model], 4) * _random.uniform(0.8, 1.2))
                print(f'[CASCADE {timestamp}] ⚠️  Streaming rate limit on {model} ({retry_counts[model]}/{max_retries_before_cascade}), backoff {backoff:.1f}s')
                log_cascade(model=model, action='retry', tier=tier, reason='rate_limit_stream', request_id=request_id, retry_count=retry_counts[model], error=str(e.detail))
                if retry_counts[model] >= max_retries_before_cascade:
                    print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                    next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                    log_cascade(model=model, action='switch', tier=tier, reason='max_rate_limit_retries_stream', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                    model_idx += 1
                await asyncio.sleep(backoff)
                continue
            if status_code in (500, 502, 503, 504):
                retry_counts[model] += 1
                print(f'[CASCADE {timestamp}] ⚠️  Streaming server error {status_code} on {model} ({retry_counts[model]}/{max_retries_before_cascade})')
                log_cascade(model=model, action='retry', tier=tier, reason=f'server_error_stream_{status_code}', request_id=request_id, retry_count=retry_counts[model], error=str(e.detail))
                if retry_counts[model] >= max_retries_before_cascade:
                    print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                    next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                    log_cascade(model=model, action='switch', tier=tier, reason=f'max_server_error_stream_{status_code}_retries', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                    model_idx += 1
                continue
            raise
        except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
            if emitted_any_chunk:
                raise
            print(f'[CASCADE {timestamp}] 🔒 Streaming SSL/Cert error on {model} - switching immediately: {e}')
            next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
            log_cascade(model=model, action='switch', tier=tier, reason='ssl_error_stream', from_model=model, to_model=next_model, request_id=request_id, error=str(e))
            last_error = e
            model_idx += 1
            continue
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if emitted_any_chunk:
                raise
            retry_counts[model] += 1
            print(f'[CASCADE {timestamp}] ⚠️  Streaming network error on {model} ({retry_counts[model]}/{max_retries_before_cascade}): {e}')
            log_cascade(model=model, action='retry', tier=tier, reason='network_error_stream', request_id=request_id, retry_count=retry_counts[model], error=str(e))
            last_error = e
            if retry_counts[model] >= max_retries_before_cascade:
                print(f'[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next')
                next_model = models_to_try[model_idx + 1] if model_idx + 1 < len(models_to_try) else None
                log_cascade(model=model, action='switch', tier=tier, reason='max_network_retries_stream', from_model=model, to_model=next_model, request_id=request_id, retry_count=retry_counts[model])
                model_idx += 1
            continue
    try:
        from src.core.circuit_breaker import get_circuit_breaker_registry
        get_circuit_breaker_registry().save_all()
    except Exception:
        pass
    print(f'[CASCADE {timestamp}] ❌ All stream cascade models exhausted')
    log_cascade(model=primary_model, action='exhausted', tier=tier, reason='all_models_failed_stream', request_id=request_id, error=str(last_error) if last_error else None)
    if last_error:
        raise last_error
    raise APIError('All stream cascade models failed')
```

---


