# File Audit: /home/cheta/code/claude-code-proxy/inspect_db_safe_2.py
**Path**: `/home/cheta/code/claude-code-proxy/inspect_db_safe_2.py`

## Global Presets & Variables
- `db_path` = `'usage_tracking.db'`
- `copy_path` = `'usage_tracking_copy_2.db'`

## Dependencies & Imports
sqlite3, json, shutil, os, sys


# File Audit: /home/cheta/code/claude-code-proxy/test_model.py
**Path**: `/home/cheta/code/claude-code-proxy/test_model.py`

## Global Presets & Variables
- `url` = `'http://127.0.0.1:8317/v1/chat/completions'`
- `headers` = `{'Content-Type': 'application/json', 'Authorization': 'Bearer pass'}`
- `data` = `{'model': 'gemini-3-pro', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 1}`

## Dependencies & Imports
requests, json, sys


# File Audit: /home/cheta/code/claude-code-proxy/compress-monitor-web.py
**Path**: `/home/cheta/code/claude-code-proxy/compress-monitor-web.py`

**Module Overview**: 
```text
Compression Stack Web Dashboard
Serves a web UI for monitoring Headroom + RTK compression layers
Usage: ./compress-monitor-web.py [--port 8899]
```

## Global Presets & Variables
- `PORT` = `int(sys.argv[1]) if len(sys.argv) > 1 else 8899`
- `HTML_PAGE` = `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>Compression Stack Monitor</title>\n    <style>\n        * { margin: 0; padding: 0; box-sizing: border-box; }\n        body { font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 20px; }\n        .container { max-width: 1400px; margin: 0 auto; }\n        h1 { color: #00d4ff; margin-bottom: 10px; font-size: 28px; }\n        h2 { color: #7b68ee; margin: 20px 0 10px; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 5px; }\n        .subtitle { color: #888; margin-bottom: 20px; font-size: 14px; }\n        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }\n        .card { background: #1a1a2e; border-radius: 8px; padding: 20px; border: 1px solid #333; }\n        .card h3 { color: #00d4ff; margin-bottom: 15px; font-size: 16px; }\n        .status-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a3e; }\n        .status-row:last-child { border-bottom: none; }\n        .label { color: #aaa; }\n        .value { font-weight: bold; }\n        .value.good { color: #00ff88; }\n        .value.bad { color: #ff4757; }\n        .value.warn { color: #ffa502; }\n        table { width: 100%; border-collapse: collapse; margin-top: 10px; }\n        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #2a2a3e; }\n        th { color: #7b68ee; font-weight: 600; font-size: 13px; }\n        td { font-size: 13px; }\n        .tool-claude { color: #00ff88; }\n        .tool-qwen { color: #00d4ff; }\n        .tool-codex { color: #ffa502; }\n        .tool-opencode { color: #ff6b9d; }\n        .refresh-btn { background: #7b68ee; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; margin-bottom: 20px; }\n        .refresh-btn:hover { background: #6a5acd; }\n        .auto-refresh { color: #666; font-size: 12px; margin-left: 10px; }\n        .metric-big { font-size: 24px; font-weight: bold; color: #00d4ff; }\n        .metric-label { color: #888; font-size: 12px; margin-top: 5px; }\n    </style>\n</head>\n<body>\n    <div class="container">\n        <h1>🔧 Compression Stack Monitor</h1>\n        <p class="subtitle">Headroom + RTK Real-time Status</p>\n        <button class="refresh-btn" onclick="loadData()">↻ Refresh</button>\n        <span class="auto-refresh">Auto-refresh: 5s</span>\n        <div id="dashboard"></div>\n    </div>\n    \n    <script>\n        function formatTime(ts) {\n            const diff = Math.floor((Date.now() / 1000) - ts);\n            if (diff < 60) return diff + \'s ago\';\n            if (diff < 3600) return Math.floor(diff / 60) + \'m ago\';\n            if (diff < 86400) return Math.floor(diff / 3600) + \'h ago\';\n            return Math.floor(diff / 86400) + \'d ago\';\n        }\n        \n        function formatNumber(n) { return n.toLocaleString(); }\n        function formatSize(bytes) {\n            if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + \'MB\';\n            if (bytes > 1024) return (bytes / 1024).toFixed(1) + \'KB\';\n            return bytes + \'B\';\n        }\n        \n        function renderCard(title, content) {\n            return `<div class="card"><h3>${title}</h3>${content}</div>`;\n        }\n        \n        function renderStatusRow(label, value, className = \'\') {\n            return `<div class="status-row"><span class="label">${label}</span><span class="value ${className}">${value}</span></div>`;\n        }\n        \n        function loadData() {\n            fetch(\'/api/data\')\n                .then(r => r.json())\n                .then(data => {\n                    let html = \'\';\n                    \n                    // Headroom Status\n                    const hr = data.headroom;\n                    html += \'<h2>Headroom Compression</h2><div class="grid">\';\n                    \n                    html += renderCard(\'Default Tier (:8787)\', \n                        renderStatusRow(\'Status\', hr.default.running ? \'✓ Running\' : \'✗ Offline\', hr.default.running ? \'good\' : \'bad\') +\n                        renderStatusRow(\'Compression\', hr.default.optimize ? \'ON\' : \'OFF\', hr.default.optimize ? \'good\' : \'warn\') +\n                        renderStatusRow(\'Cache\', hr.default.cache ? \'ON\' : \'OFF\', hr.default.cache ? \'good\' : \'warn\')\n                    );\n                    \n                    html += renderCard(\'Small Tier (:8790)\',\n                        renderStatusRow(\'Status\', hr.small.running ? \'✓ Running\' : \'✗ Offline\', hr.small.running ? \'good\' : \'bad\') +\n                        renderStatusRow(\'Compression\', hr.small.optimize ? \'ON\' : \'OFF\', hr.small.optimize ? \'good\' : \'warn\') +\n                        renderStatusRow(\'Cache\', hr.small.cache ? \'ON\' : \'OFF\', hr.small.cache ? \'good\' : \'warn\')\n                    );\n                    \n                    html += renderCard(\'Default Stats\',\n                        `<div class="metric-big">${formatNumber(hr.default_stats.requests)}</div><div class="metric-label">Total Requests</div>` +\n                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.default_stats.tokens_in)}</div><div class="metric-label">Tokens In</div>` +\n                        `<div style="margin-top:15px" class="metric-big">${formatNumber(hr.default_stats.tokens_out)}</div><div class="metric-label">Tokens Out</div>`\n                    );\n                    \n                    html += \'</div>\';\n                    \n                    // RTK Status\n                    html += \'<h2>RTK (Real-Time Kompression)</h2><div class="grid">\';\n                    \n                    html += renderCard(\'RTK Status\',\n                        renderStatusRow(\'Installed\', data.rtk.installed ? \'✓ Yes\' : \'✗ No\', data.rtk.installed ? \'good\' : \'bad\') +\n                        renderStatusRow(\'Version\', data.rtk.version || \'N/A\')\n                    );\n                    \n                    html += renderCard(\'RTK Stats\',\n                        `<div class="metric-big">${formatNumber(data.rtk_stats.total_compressions)}</div><div class="metric-label">Total Compressions</div>` +\n                        `<div style="margin-top:15px" class="metric-big">${formatNumber(data.rtk_stats.tokens_saved)}</div><div class="metric-label">Tokens Saved</div>`\n                    );\n                    \n                    html += \'</div>\';\n                    \n                    // CLI Sessions\n                    html += \'<h2>CLI Sessions (Recent)</h2>\';\n                    if (data.sessions.length > 0) {\n                        html += \'<table><thead><tr><th>Tool</th><th>Session</th><th>Msg</th><th>Size</th><th>Age</th><th>Workspace</th></tr></thead><tbody>\';\n                        data.sessions.forEach(s => {\n                            const toolClass = \'tool-\' + s.tool.toLowerCase().replace(\' \', \'-\');\n                            html += `<tr>\n                                <td class="${toolClass}">${s.tool}</td>\n                                <td>${s.session.substring(0, 12)}${s.session.length > 12 ? \'...\' : \'\'}</td>\n                                <td>${s.messages}</td>\n                                <td>${formatSize(s.size)}</td>\n                                <td>${formatTime(s.modified)}</td>\n                                <td>${s.cwd.substring(Math.max(0, s.cwd.length - 30))}</td>\n                            </tr>`;\n                        });\n                        html += \'</tbody></table>\';\n                    } else {\n                        html += \'<p style="color:#666;padding:20px;text-align:center">No sessions found</p>\';\n                    }\n                    \n                    document.getElementById(\'dashboard\').innerHTML = html;\n                    document.querySelector(\'.subtitle\').textContent = \'Last updated: \' + new Date(data.timestamp).toLocaleTimeString();\n                })\n                .catch(err => {\n                    document.getElementById(\'dashboard\').innerHTML = \'<p style="color:#ff4757">Error loading data: \' + err + \'</p>\';\n                });\n        }\n        \n        loadData();\n        setInterval(loadData, 5000);\n    </script>\n</body>\n</html>\n'`

## Dependencies & Imports
http.server, socketserver, json, subprocess, sys, pathlib.Path, datetime.datetime

## Feature Function: `get_headroom_health`
**Parameters:** `port`
**Variables Used:** `data`
**Implementation:**
```python
def get_headroom_health(port):
    try:
        import urllib.request
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return {'running': True, 'optimize': data.get('config', {}).get('optimize', False), 'cache': data.get('config', {}).get('cache', False)}
    except:
        return {'running': False, 'optimize': False, 'cache': False}
```

---

## Feature Function: `get_headroom_stats`
**Parameters:** `log_file`
**Variables Used:** `stats, event`
**Implementation:**
```python
def get_headroom_stats(log_file):
    stats = {'requests': 0, 'compressed': 0, 'tokens_in': 0, 'tokens_out': 0}
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    stats['requests'] += 1
                    if any((k in str(event).lower() for k in ['compress', 'optimize', 'save'])):
                        stats['compressed'] += 1
                    stats['tokens_in'] += event.get('tokens_in', event.get('input_tokens', 0))
                    stats['tokens_out'] += event.get('tokens_out', event.get('output_tokens', 0))
                except:
                    continue
    except:
        pass
    return stats
```

---

## Feature Function: `get_rtk_status`
**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
def get_rtk_status():
    try:
        result = subprocess.run(['rtk', '--version'], capture_output=True, text=True, timeout=5)
        return {'installed': True, 'version': result.stdout.strip() if result.returncode == 0 else 'unknown'}
    except:
        return {'installed': False, 'version': None}
```

---

## Feature Function: `get_rtk_stats`
**Parameters:** ``
**Variables Used:** `stats, lines, result`
**Implementation:**
```python
def get_rtk_stats():
    stats = {'total_compressions': 0, 'tokens_saved': 0, 'last_compression': None}
    try:
        result = subprocess.run(['rtk', 'gain', '--history'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            stats['total_compressions'] = len([l for l in lines if l.strip()])
            if lines and lines[0].strip():
                stats['last_compression'] = lines[0].strip()[:100]
    except:
        pass
    return stats
```

---

## Feature Function: `get_cli_sessions`
**Parameters:** ``
**Variables Used:** `sessions, stat, session_dirs, data`
**Implementation:**
```python
def get_cli_sessions():
    sessions = []
    session_dirs = [(Path.home() / '.claude' / 'sessions', 'Claude Code'), (Path.home() / '.qwen' / 'sessions', 'Qwen Code'), (Path.home() / '.codex' / 'sessions', 'Codex CLI'), (Path.home() / '.opencode' / 'sessions', 'OpenCode')]
    for session_dir, tool_name in session_dirs:
        if not session_dir.exists():
            continue
        for session_file in session_dir.glob('*.json'):
            try:
                stat = session_file.stat()
                with open(session_file) as f:
                    data = json.load(f)
                sessions.append({'tool': tool_name, 'session': session_file.stem, 'modified': int(stat.st_mtime), 'size': stat.st_size, 'messages': len(data.get('messages', [])), 'cwd': data.get('cwd', data.get('workspace', 'N/A'))})
            except:
                continue
    sessions.sort(key=lambda x: x['modified'], reverse=True)
    return sessions[:20]
```

---

## Feature Function: `get_dashboard_data`
**Parameters:** ``
**Implementation:**
```python
def get_dashboard_data():
    return {'timestamp': datetime.now().isoformat(), 'headroom': {'default': get_headroom_health(8787), 'small': get_headroom_health(8790), 'default_stats': get_headroom_stats(Path.home() / '.local/share/headroom/proxy-default.jsonl'), 'small_stats': get_headroom_stats(Path.home() / '.local/share/headroom/proxy-small.jsonl')}, 'rtk': get_rtk_status(), 'rtk_stats': get_rtk_stats(), 'sessions': get_cli_sessions()}
```

---

## Feature Class: `Handler`
### Method: `do_GET`
**Parameters:** `self`
**Implementation:**
```python
def do_GET(self):
    if self.path == '/':
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode())
    elif self.path == '/api/data':
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(get_dashboard_data()).encode())
    else:
        self.send_response(404)
        self.end_headers()
```

### Method: `log_message`
**Parameters:** `self, format`
**Implementation:**
```python
def log_message(self, format, *args):
    pass
```

---


# File Audit: /home/cheta/code/claude-code-proxy/quickstart.py
**Path**: `/home/cheta/code/claude-code-proxy/quickstart.py`

**Module Overview**: 
```text
Quick Start Script for The Ultimate Proxy

This script automates the complete setup process:
- Checks system requirements (Python, uv/pip)
- Creates virtual environment (if needed)
- Installs dependencies
- Sets up environment configuration
- Initializes the database
- Launches the proxy

Usage:
    python quickstart.py              # Interactive setup
    python quickstart.py --non-interactive  # Auto setup with defaults
    python quickstart.py --help       # Show help
```

## Dependencies & Imports
os, sys, subprocess, argparse, pathlib.Path, typing.Optional, typing.Tuple

## Feature Class: `Colors`
---

## Feature Function: `print_header`
**Parameters:** `text`
**Implementation:**
```python
def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f'{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}')
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")
```

---

## Feature Function: `print_success`
**Parameters:** `text`
**Implementation:**
```python
def print_success(text: str):
    print(f'{Colors.OKGREEN}✓ {text}{Colors.ENDC}')
```

---

## Feature Function: `print_error`
**Parameters:** `text`
**Implementation:**
```python
def print_error(text: str):
    print(f'{Colors.FAIL}✗ {text}{Colors.ENDC}')
```

---

## Feature Function: `print_warning`
**Parameters:** `text`
**Implementation:**
```python
def print_warning(text: str):
    print(f'{Colors.WARNING}⚠ {text}{Colors.ENDC}')
```

---

## Feature Function: `print_info`
**Parameters:** `text`
**Implementation:**
```python
def print_info(text: str):
    print(f'{Colors.OKCYAN}ℹ {text}{Colors.ENDC}')
```

---

## Feature Function: `run_command`
**Logic & Purpose:**
```text
Run a shell command and return the result.
```

**Parameters:** `command, cwd, check`
**Variables Used:** `result`
**Implementation:**
```python
def run_command(command: list, cwd: Optional[Path]=None, check: bool=True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=False, check=check)
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise e
        return e
```

---

## Feature Function: `check_python_version`
**Logic & Purpose:**
```text
Check if Python 3.9+ is installed.
```

**Parameters:** ``
**Variables Used:** `version`
**Implementation:**
```python
def check_python_version() -> Tuple[bool, str]:
    """Check if Python 3.9+ is installed."""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 9:
            return (True, f'Python {version.major}.{version.minor}.{version.micro}')
        return (False, f'Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)')
    except Exception as e:
        return (False, f'Error checking Python version: {e}')
```

---

## Feature Function: `check_uv`
**Logic & Purpose:**
```text
Check if uv is installed.
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
def check_uv() -> bool:
    """Check if uv is installed."""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
```

---

## Feature Function: `check_pip`
**Logic & Purpose:**
```text
Check if pip is installed.
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
def check_pip() -> bool:
    """Check if pip is installed."""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False
```

---

## Feature Function: `ensure_gcc_compat`
**Logic & Purpose:**
```text
Ensure gcc-12 is available or set CC environment variable as fallback.
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
def ensure_gcc_compat() -> bool:
    """Ensure gcc-12 is available or set CC environment variable as fallback."""
    if not sys.platform.startswith('linux'):
        return True
    try:
        result = subprocess.run(['gcc-12', '--version'], capture_output=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    try:
        result = subprocess.run(['gcc', '--version'], capture_output=True)
        if result.returncode == 0:
            print_warning('gcc-12 not found, using gcc and setting CC environment variable')
            os.environ['CC'] = 'gcc'
            return True
    except FileNotFoundError:
        print_error('gcc not found. Please install gcc to build dependencies.')
        print_info('On Fedora/RHEL: sudo dnf install gcc')
        print_info('On Ubuntu/Debian: sudo apt install gcc')
        return False
    return False
```

---

## Feature Function: `create_venv`
**Logic & Purpose:**
```text
Create a virtual environment if it doesn't exist.
```

**Parameters:** `project_root`
**Variables Used:** `venv_dir`
**Implementation:**
```python
def create_venv(project_root: Path) -> bool:
    """Create a virtual environment if it doesn't exist."""
    venv_dir = project_root / '.venv'
    if venv_dir.exists():
        print_info('Virtual environment already exists')
        return True
    print_info('Creating virtual environment...')
    try:
        run_command([sys.executable, '-m', 'venv', str(venv_dir)])
        print_success('Virtual environment created')
        return True
    except Exception as e:
        print_error(f'Failed to create venv: {e}')
        return False
```

---

## Feature Function: `install_dependencies_uv`
**Logic & Purpose:**
```text
Install dependencies using uv.
```

**Parameters:** `project_root`
**Implementation:**
```python
def install_dependencies_uv(project_root: Path) -> bool:
    """Install dependencies using uv."""
    print_info('Installing dependencies with uv...')
    try:
        if not ensure_gcc_compat():
            print_error('Cannot install dependencies: build tools missing')
            return False
        run_command(['uv', 'sync'], cwd=project_root)
        print_success('Dependencies installed')
        return True
    except Exception as e:
        print_error(f'Failed to install dependencies: {e}')
        return False
```

---

## Feature Function: `install_dependencies_pip`
**Logic & Purpose:**
```text
Install dependencies using pip.
```

**Parameters:** `project_root, venv_path`
**Variables Used:** `pip_exe`
**Implementation:**
```python
def install_dependencies_pip(project_root: Path, venv_path: Path) -> bool:
    """Install dependencies using pip."""
    print_info('Installing dependencies with pip...')
    if not ensure_gcc_compat():
        print_error('Cannot install dependencies: build tools missing')
        return False
    if sys.platform == 'win32':
        pip_exe = venv_path / 'Scripts' / 'pip'
    else:
        pip_exe = venv_path / 'bin' / 'pip'
    if not pip_exe.exists():
        pip_exe = Path(sys.executable)
    try:
        run_command([str(pip_exe), 'install', '-e', '.'], cwd=project_root)
        print_success('Dependencies installed')
        return True
    except Exception as e:
        print_error(f'Failed to install dependencies: {e}')
        return False
```

---

## Feature Function: `setup_environment`
**Logic & Purpose:**
```text
Create and configure .env file.
```

**Parameters:** `project_root, non_interactive`
**Variables Used:** `has_valid_config, use_defaults, env_file, middle_model, line, env_content, api_key, big_model, small_model, provider_choice, content, response, port, host, env_example`
**Implementation:**
```python
def setup_environment(project_root: Path, non_interactive: bool=False) -> bool:
    """Create and configure .env file."""
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    if env_file.exists():
        print_info('.env file already exists')
        has_valid_config = False
        with open(env_file, 'r') as f:
            content = f.read()
            if 'OPENROUTER_API_KEY=' in content or 'OPENAI_API_KEY=' in content or 'OPENAI_BASE_URL=' in content or ('PROVIDER_API_KEY=' in content) or ('BIG_MODEL=' in content):
                has_valid_config = True
        if has_valid_config:
            print_success('Existing configuration detected - preserving it')
            print_info('To reconfigure, delete .env and run again')
            return True
        if non_interactive:
            return True
        try:
            response = input('\n⚙️  .env exists but appears incomplete. Reconfigure? [y/N]: ').strip().lower()
            if response not in ['y', 'yes']:
                return True
        except (EOFError, KeyboardInterrupt):
            return True
    print_header('ENVIRONMENT CONFIGURATION')
    env_content = {}
    if env_example.exists():
        print_info('Using .env.example as template')
        with open(env_example, 'r') as f:
            for line in f:
                line = line.strip()
                if line and (not line.startswith('#')) and ('=' in line):
                    key, value = line.split('=', 1)
                    env_content[key] = value.strip('"').strip("'")
    print('\n📝 Configure your proxy:\n')
    print('Choose your API provider:')
    print('  1. OpenRouter (recommended - access to multiple models)')
    print('  2. OpenAI')
    print('  3. Google Gemini')
    print('  4. VibeProxy (free premium models)')
    print('  5. Skip configuration (edit .env manually later)')
    if not non_interactive:
        try:
            provider_choice = input('\nSelect provider [1-5]: ').strip()
        except (EOFError, KeyboardInterrupt):
            provider_choice = '5'
    else:
        provider_choice = '1'
    if provider_choice == '1':
        env_content['OPENROUTER_API_KEY'] = 'sk-or-v1-your-key-here'
        env_content['OPENAI_BASE_URL'] = 'https://openrouter.ai/api/v1'
        print_info('Provider: OpenRouter')
        if not non_interactive:
            api_key = input('Enter your OpenRouter API key (or press Enter to skip): ').strip()
            if api_key:
                env_content['OPENROUTER_API_KEY'] = api_key
    elif provider_choice == '2':
        env_content['OPENAI_API_KEY'] = 'sk-your-key-here'
        print_info('Provider: OpenAI')
        if not non_interactive:
            api_key = input('Enter your OpenAI API key (or press Enter to skip): ').strip()
            if api_key:
                env_content['OPENAI_API_KEY'] = api_key
    elif provider_choice == '3':
        env_content['GOOGLE_API_KEY'] = 'your-key-here'
        env_content['OPENAI_BASE_URL'] = 'https://generativelanguage.googleapis.com/v1beta/openai/'
        print_info('Provider: Google Gemini')
        if not non_interactive:
            api_key = input('Enter your Google API key (or press Enter to skip): ').strip()
            if api_key:
                env_content['GOOGLE_API_KEY'] = api_key
    elif provider_choice == '4':
        env_content['OPENAI_BASE_URL'] = 'http://localhost:8317/v1'
        env_content['OPENAI_API_KEY'] = 'vibeproxy-key'
        print_info('Provider: VibeProxy')
        print_warning('Make sure VibeProxy is running on port 8317')
    else:
        print_warning('Skipping API configuration')
        env_content['OPENAI_API_KEY'] = 'your-key-here'
    if not non_interactive:
        print('\n📦 Configure model routing:')
        use_defaults = input('Use default model routing? [Y/n]: ').strip().lower()
        if use_defaults not in ['n', 'no', '']:
            big_model = input(f"BIG_MODEL [{env_content.get('BIG_MODEL', 'anthropic/claude-sonnet-4-20250514')}]: ").strip()
            middle_model = input(f"MIDDLE_MODEL [{env_content.get('MIDDLE_MODEL', 'google/gemini-2.0-flash-001')}]: ").strip()
            small_model = input(f"SMALL_MODEL [{env_content.get('SMALL_MODEL', 'google/gemini-2.0-flash-001')}]: ").strip()
            if big_model:
                env_content['BIG_MODEL'] = big_model
            if middle_model:
                env_content['MIDDLE_MODEL'] = middle_model
            if small_model:
                env_content['SMALL_MODEL'] = small_model
    if not non_interactive:
        print('\n🌐 Server configuration:')
        host = input(f"HOST [{env_content.get('HOST', '0.0.0.0')}]: ").strip()
        port = input(f"PORT [{env_content.get('PORT', '8082')}]: ").strip()
        if host:
            env_content['HOST'] = host
        if port:
            env_content['PORT'] = port
    env_content['ENABLE_DASHBOARD'] = 'true'
    env_content['TRACK_USAGE'] = 'true'
    with open(env_file, 'w') as f:
        f.write('# Claude Code Proxy Configuration\n')
        f.write('# Generated by quickstart.py\n\n')
        for key, value in env_content.items():
            f.write(f'{key}="{value}"\n')
    print_success(f'.env file created at {env_file}')
    print('\n' + '=' * 60)
    print('📝 NEXT STEPS:')
    print('=' * 60)
    if 'your-key' in str(env_content.values()) or 'sk-or-v1-your' in str(env_content.values()):
        print_warning('⚠️  You need to add your actual API key to .env')
        print(f'   Edit: {env_file}')
    print('\nTo start the proxy:')
    print(f'   cd {project_root}')
    print('   python start_proxy.py')
    print('\nTo use with Claude Code:')
    print('   export ANTHROPIC_BASE_URL=http://localhost:8082')
    print('   export ANTHROPIC_API_KEY=pass')
    print('   claude')
    print('=' * 60 + '\n')
    return True
```

---

## Feature Function: `initialize_database`
**Logic & Purpose:**
```text
Initialize the database by running a dry-run.
```

**Parameters:** `project_root`
**Variables Used:** `db_path`
**Implementation:**
```python
def initialize_database(project_root: Path) -> bool:
    """Initialize the database by running a dry-run."""
    print_info('Initializing database...')
    db_path = project_root / 'usage_tracking.db'
    if db_path.exists():
        print_info('Database already exists')
        return True
    print_success('Database will be created on first run')
    return True
```

---

## Feature Function: `launch_proxy`
**Logic & Purpose:**
```text
Launch the proxy server.
```

**Parameters:** `project_root, non_interactive`
**Variables Used:** `venv_python, response`
**Implementation:**
```python
def launch_proxy(project_root: Path, non_interactive: bool=False) -> bool:
    """Launch the proxy server."""
    if not non_interactive:
        print('\n' + '=' * 60)
        print('🚀 Ready to start the proxy!')
        print('=' * 60)
        try:
            response = input('\nStart the proxy now? [Y/n]: ').strip().lower()
            if response in ['n', 'no']:
                print_info('You can start the proxy later with: python start_proxy.py')
                return True
        except (EOFError, KeyboardInterrupt):
            pass
    print_info('Starting proxy server...')
    print('\n' + '=' * 60)
    print('📊 Proxy will be available at: http://localhost:8082')
    print('=' * 60 + '\n')
    try:
        venv_python = project_root / '.venv' / 'bin' / 'python'
        if not venv_python.exists():
            venv_python = Path(sys.executable)
        run_command([str(venv_python), 'start_proxy.py'], cwd=project_root, check=False)
        return True
    except Exception as e:
        print_error(f'Failed to start proxy: {e}')
        return False
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `args, venv_path, parser, project_root, use_uv, use_pip`
**Implementation:**
```python
def main():
    parser = argparse.ArgumentParser(description='Quick Start Script for The Ultimate Proxy', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  python quickstart.py              # Interactive setup\n  python quickstart.py --non-interactive  # Auto setup with defaults\n  python quickstart.py --no-launch    # Setup without launching proxy\n        ')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode (use defaults)')
    parser.add_argument('--no-launch', action='store_true', help='Setup without launching the proxy')
    parser.add_argument('--skip-venv', action='store_true', help='Skip virtual environment creation')
    args = parser.parse_args()
    project_root = Path(__file__).parent.absolute()
    print_header('🚀 THE ULTIMATE PROXY - QUICK START')
    print_header('STEP 1: CHECKING REQUIREMENTS')
    python_ok, python_version = check_python_version()
    if python_ok:
        print_success(python_version)
    else:
        print_error(python_version)
        print_error('Please install Python 3.9 or higher')
        print_info('Download from: https://www.python.org/downloads/')
        sys.exit(1)
    print('\n📦 Checking package manager...')
    use_uv = check_uv()
    use_pip = check_pip()
    if use_uv:
        print_success('uv found - will use for dependency management')
    elif use_pip:
        print_warning('uv not found - will use pip instead')
        print_info('Consider installing uv for faster installs: https://docs.astral.sh/uv/')
    else:
        print_error('Neither uv nor pip found')
        print_error('Please install pip or uv')
        sys.exit(1)
    if not args.skip_venv:
        print_header('STEP 2: CREATING VIRTUAL ENVIRONMENT')
        if not create_venv(project_root):
            print_error('Failed to create virtual environment')
            sys.exit(1)
    print_header('STEP 3: INSTALLING DEPENDENCIES')
    if use_uv and (not args.skip_venv):
        if not install_dependencies_uv(project_root):
            print_error('Failed to install dependencies')
            sys.exit(1)
    else:
        venv_path = project_root / '.venv'
        if not install_dependencies_pip(project_root, venv_path):
            print_error('Failed to install dependencies')
            sys.exit(1)
    print_header('STEP 4: CONFIGURING ENVIRONMENT')
    if not setup_environment(project_root, non_interactive=args.non_interactive):
        print_error('Failed to configure environment')
        sys.exit(1)
    print_header('STEP 5: INITIALIZING DATABASE')
    if not initialize_database(project_root):
        print_warning('Database initialization skipped')
    if not args.no_launch:
        print_header('STEP 6: LAUNCH PROXY')
        launch_proxy(project_root, non_interactive=args.non_interactive)
    else:
        print_header('SETUP COMPLETE!')
        print_success('All dependencies installed and configured')
        print('\n📊 To start the proxy:')
        print(f'   cd {project_root}')
        print('   python start_proxy.py')
        print('\n🌐 Web dashboard: http://localhost:8082')
        print('\n📝 To use with Claude Code:')
        print('   export ANTHROPIC_BASE_URL=http://localhost:8082')
        print('   export ANTHROPIC_API_KEY=pass')
        print('   claude')
    print('\n' + '=' * 60)
    print(f'{Colors.OKGREEN}✨ Setup complete!{Colors.ENDC}')
    print('=' * 60 + '\n')
```

---


Error parsing /home/cheta/code/claude-code-proxy/test_proxy.py: unexpected indent (<unknown>, line 2)

# File Audit: /home/cheta/code/claude-code-proxy/fix_ghosts.py
**Path**: `/home/cheta/code/claude-code-proxy/fix_ghosts.py`

## Dependencies & Imports
os, re

## Feature Function: `fix_file`
**Parameters:** `filepath`
**Variables Used:** `pattern, inner_indent, indent, content`
**Implementation:**
```python
def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return
    pattern = re.compile('^([ \\t]*)except Exception as _e:\\s+pass', re.MULTILINE)

    def replacement(match):
        indent = match.group(1)
        inner_indent = indent + '    '
        return f'{indent}except Exception as _e:\n{inner_indent}import logging\n{inner_indent}logging.getLogger(__name__).debug(f"Ghost exception handled: {{_e}}")'
    new_content, count = pattern.subn(replacement, content)
    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Fixed {count} instances in {filepath}')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/restart_chain.sh
**Path**: `/home/cheta/code/claude-code-proxy/restart_chain.sh`


Error parsing /home/cheta/code/claude-code-proxy/run_proxy_bg.sh: Missing parentheses in call to 'exec'. Did you mean exec(...)? (<unknown>, line 4)

Error parsing /home/cheta/code/claude-code-proxy/install-all.sh: closing parenthesis ')' does not match opening parenthesis '{' on line 127 (<unknown>, line 159)

# File Audit: /home/cheta/code/claude-code-proxy/inspect_db_tmp.py
**Path**: `/home/cheta/code/claude-code-proxy/inspect_db_tmp.py`

## Global Presets & Variables
- `db_path` = `'usage_tracking.db'`
- `copy_path` = `'/tmp/usage_tracking_debug.db'`

## Dependencies & Imports
sqlite3, json, shutil, os, sys, time


# File Audit: /home/cheta/code/claude-code-proxy/inspect_db_safe.py
**Path**: `/home/cheta/code/claude-code-proxy/inspect_db_safe.py`

## Global Presets & Variables
- `db_path` = `'usage_tracking.db'`
- `copy_path` = `'usage_tracking_copy.db'`

## Dependencies & Imports
sqlite3, json, shutil, os, sys


# File Audit: /home/cheta/code/claude-code-proxy/cs-dashboard.py
**Path**: `/home/cheta/code/claude-code-proxy/cs-dashboard.py`

**Module Overview**: 
```text
Compression Stack + Claude Code Proxy — CLI Dashboard
Displays live usage stats from both Headroom compression proxies AND
Claude Code Proxy (when present). Auto-detects what's running.

Usage:
    python3 cs-dashboard.py              # One-shot display
    python3 cs-dashboard.py --watch      # Live refresh every 2s
    python3 cs-dashboard.py --port 9999  # Custom web dashboard port
```

## Global Presets & Variables
- `C_RESET` = `'\x1b[0m'`
- `C_BOLD` = `'\x1b[1m'`
- `C_DIM` = `'\x1b[2m'`
- `C_RED` = `'\x1b[38;5;196m'`
- `C_GREEN` = `'\x1b[38;5;82m'`
- `C_YELLOW` = `'\x1b[38;5;226m'`
- `C_CYAN` = `'\x1b[38;5;87m'`
- `C_MAGENTA` = `'\x1b[38;5;212m'`
- `C_WHITE` = `'\x1b[38;5;255m'`
- `C_GRAY` = `'\x1b[38;5;245m'`
- `C_ORANGE` = `'\x1b[38;5;208m'`
- `C_BLUE` = `'\x1b[38;5;75m'`

## Dependencies & Imports
json, subprocess, sys, time, os, pathlib.Path, datetime.datetime

## Feature Function: `fmt`
**Logic & Purpose:**
```text
Format number with commas.
```

**Parameters:** `num`
**Implementation:**
```python
def fmt(num):
    """Format number with commas."""
    if isinstance(num, (int, float)):
        return f'{num:,.0f}'
    return str(num)
```

---

## Feature Function: `tok_fmt`
**Logic & Purpose:**
```text
Format tokens with K/M suffix.
```

**Parameters:** `n`
**Variables Used:** `n`
**Implementation:**
```python
def tok_fmt(n):
    """Format tokens with K/M suffix."""
    n = int(n)
    if n >= 1000000:
        return f'{n / 1000000:.1f}M'
    if n >= 1000:
        return f'{n / 1000:.1f}K'
    return str(n)
```

---

## Feature Function: `ms_fmt`
**Logic & Purpose:**
```text
Format milliseconds.
```

**Parameters:** `ms`
**Variables Used:** `ms`
**Implementation:**
```python
def ms_fmt(ms):
    """Format milliseconds."""
    ms = int(ms)
    if ms >= 1000:
        return f'{ms / 1000:.1f}s'
    return f'{ms}ms'
```

---

## Feature Function: `status_dot`
**Parameters:** `ok`
**Implementation:**
```python
def status_dot(ok):
    return f'{C_GREEN}●{C_RESET}' if ok else f'{C_RED}●{C_RESET}'
```

---

## Feature Function: `pct`
**Logic & Purpose:**
```text
Draw a mini progress bar.
```

**Parameters:** `val, total, width`
**Variables Used:** `bar, filled`
**Implementation:**
```python
def pct(val, total, width=20):
    """Draw a mini progress bar."""
    if total == 0:
        filled = 0
    else:
        filled = int(val / total * width)
    bar = f"{C_GREEN}{'█' * filled}{C_DIM}{'░' * (width - filled)}{C_RESET}"
    return bar
```

---

## Feature Function: `http_get`
**Logic & Purpose:**
```text
Simple HTTP GET returning parsed JSON or None.
```

**Parameters:** `url, timeout`
**Implementation:**
```python
def http_get(url, timeout=2):
    """Simple HTTP GET returning parsed JSON or None."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except:
        return None
```

---

## Feature Function: `get_headroom_health`
**Parameters:** `port`
**Variables Used:** `data`
**Implementation:**
```python
def get_headroom_health(port):
    data = http_get(f'http://127.0.0.1:{port}/health')
    if data:
        return {'running': True, 'version': data.get('version', '?'), 'optimize': data.get('config', {}).get('optimize', False), 'cache': data.get('config', {}).get('cache', False), 'rate_limit': data.get('config', {}).get('rate_limit', False)}
    return {'running': False, 'version': '?', 'optimize': False, 'cache': False, 'rate_limit': False}
```

---

## Feature Function: `parse_headroom_logs`
**Logic & Purpose:**
```text
Parse Headroom JSONL log for stats.
```

**Parameters:** `log_file`
**Variables Used:** `line, evt, saved, lat, stats, to, ti, tags`
**Implementation:**
```python
def parse_headroom_logs(log_file):
    """Parse Headroom JSONL log for stats."""
    stats = {'requests': 0, 'compressed': 0, 'tokens_in': 0, 'tokens_out': 0, 'tokens_saved': 0, 'latencies': []}
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    stats['requests'] += 1
                    ti = evt.get('tokens_in', evt.get('input_tokens', 0))
                    to = evt.get('tokens_out', evt.get('output_tokens', 0))
                    stats['tokens_in'] += ti
                    stats['tokens_out'] += to
                    if ti > 0:
                        saved = max(0, ti - to)
                        stats['tokens_saved'] += saved
                    lat = evt.get('latency_ms', evt.get('latency', 0))
                    if lat:
                        stats['latencies'].append(lat)
                    tags = json.dumps(evt).lower()
                    if any((k in tags for k in ['compress', 'optimize', 'cache_hit', 'save'])):
                        stats['compressed'] += 1
                except:
                    continue
    except:
        pass
    return stats
```

---

## Feature Function: `get_ccp_stats`
**Logic & Purpose:**
```text
Get Claude Code Proxy usage stats.
```

**Parameters:** ``
**Variables Used:** `data`
**Implementation:**
```python
def get_ccp_stats():
    """Get Claude Code Proxy usage stats."""
    data = http_get('http://127.0.0.1:8082/api/stats')
    if not data:
        return None
    return {'running': True, 'requests_today': data.get('requests_today', 0), 'total_tokens': data.get('total_tokens', 0), 'est_cost': data.get('est_cost', 0), 'avg_latency': data.get('avg_latency', 0), 'recent_requests': data.get('recent_requests', [])}
```

---

## Feature Function: `get_ccp_health`
**Logic & Purpose:**
```text
Get CCP health status.
```

**Parameters:** ``
**Variables Used:** `data`
**Implementation:**
```python
def get_ccp_health():
    """Get CCP health status."""
    data = http_get('http://127.0.0.1:8082/health')
    if data:
        return {'running': True, 'timestamp': data.get('timestamp', '?')}
    return {'running': False}
```

---

## Feature Function: `get_rtk_version`
**Parameters:** ``
**Variables Used:** `r`
**Implementation:**
```python
def get_rtk_version():
    try:
        r = subprocess.run(['rtk', '--version'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()
    except:
        pass
    return None
```

---

## Feature Function: `get_gpu_info`
**Logic & Purpose:**
```text
Detect GPU info for display.
```

**Parameters:** ``
**Variables Used:** `name, r`
**Implementation:**
```python
def get_gpu_info():
    """Detect GPU info for display."""
    try:
        r = subprocess.run(['clinfo'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for line in r.stdout.split('\n'):
                if 'Device Name' in line and '0x569' in line:
                    name = line.split('Intel(R)')[-1].strip()
                    return f'Intel Arc {name}'
    except:
        pass
    try:
        r = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return f'NVIDIA {r.stdout.strip().split(chr(10))[0]}'
    except:
        pass
    return None
```

---

## Feature Function: `get_cli_sessions`
**Logic & Purpose:**
```text
Get recent CLI sessions.
```

**Parameters:** `limit`
**Variables Used:** `sessions, stat, session_dirs, data`
**Implementation:**
```python
def get_cli_sessions(limit=10):
    """Get recent CLI sessions."""
    sessions = []
    session_dirs = [(Path.home() / '.claude' / 'sessions', 'Claude Code', C_GREEN), (Path.home() / '.qwen' / 'sessions', 'Qwen Code', C_CYAN), (Path.home() / '.codex' / 'sessions', 'Codex CLI', C_ORANGE), (Path.home() / '.opencode' / 'sessions', 'OpenCode', C_MAGENTA), (Path.home() / '.hermes' / 'sessions', 'Hermes', C_YELLOW)]
    for session_dir, tool_name, color in session_dirs:
        if not session_dir.exists():
            continue
        for session_file in sorted(session_dir.glob('*.json'), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                stat = session_file.stat()
                with open(session_file) as f:
                    data = json.load(f)
                sessions.append({'tool': tool_name, 'color': color, 'session': session_file.stem, 'modified': int(stat.st_mtime), 'size': stat.st_size, 'messages': len(data.get('messages', [])), 'cwd': data.get('cwd', data.get('workspace', 'N/A'))})
            except:
                continue
    sessions.sort(key=lambda x: x['modified'], reverse=True)
    return sessions[:limit]
```

---

## Feature Function: `draw_separator`
**Parameters:** `char, color`
**Variables Used:** `cols`
**Implementation:**
```python
def draw_separator(char='─', color=C_DIM):
    cols = os.get_terminal_size().columns if os.isatty(1) else 80
    print(f'{color}{char * cols}{C_RESET}')
```

---

## Feature Function: `draw_header`
**Parameters:** ``
**Variables Used:** `ts, cols, title, pad`
**Implementation:**
```python
def draw_header():
    cols = os.get_terminal_size().columns if os.isatty(1) else 80
    title = f'{C_BOLD}{C_CYAN}⚡ Compression Stack Monitor{C_RESET}'
    ts = f"{C_DIM}{datetime.now().strftime('%H:%M:%S')}{C_RESET}"
    pad = cols - len(title.replace('\x1b[0m', '').replace('\x1b[1m', '').replace('\x1b[38;5;87m', '')) - len(ts.replace('\x1b[2m', '').replace('\x1b[0m', ''))
    if pad < 0:
        pad = 0
    print(f"\n{title}{' ' * pad}{ts}")
    draw_separator('═', C_CYAN)
```

---

## Feature Function: `draw_section`
**Parameters:** `title, icon`
**Implementation:**
```python
def draw_section(title, icon='◆'):
    print(f'\n{C_BOLD}{C_MAGENTA}{icon} {title}{C_RESET}')
    draw_separator('─', C_MAGENTA)
```

---

## Feature Function: `draw_kv`
**Parameters:** `label, value, color, indent`
**Variables Used:** `prefix`
**Implementation:**
```python
def draw_kv(label, value, color=C_WHITE, indent=0):
    prefix = '  ' * indent
    print(f'{prefix}{C_DIM}{label}:{C_RESET} {color}{value}{C_RESET}')
```

---

## Feature Function: `draw_metric`
**Parameters:** `label, value, sub, indent`
**Variables Used:** `prefix`
**Implementation:**
```python
def draw_metric(label, value, sub='', indent=0):
    prefix = '  ' * indent
    print(f'{prefix}{C_BOLD}{C_CYAN}{label}{C_RESET}  {C_WHITE}{value}{C_RESET}{C_DIM} {sub}{C_RESET}')
```

---

## Feature Function: `draw_bar`
**Parameters:** `label, val, total, width, indent`
**Variables Used:** `p, bar, prefix, filled`
**Implementation:**
```python
def draw_bar(label, val, total, width=30, indent=0):
    prefix = '  ' * indent
    if total == 0:
        filled = 0
        p = 0
    else:
        filled = int(val / total * width)
        p = val / total * 100
    bar = f"{C_GREEN}{'█' * filled}{C_DIM}{'░' * (width - filled)}{C_RESET}"
    print(f'{prefix}{C_DIM}{label}:{C_RESET} {bar} {C_CYAN}{p:.0f}%{C_RESET}')
```

---

## Feature Function: `display_dashboard`
**Parameters:** ``
**Variables Used:** `comp_rate, lat, hr_default, hr_default_log, sessions, gpu, h_age, ccp_stats, tok, h_msgs, ccp_health, saved, hr_default_stats, h_tool, s_dot, age, selector, hr_small_stats, now_ts, hr_small, rtk_ver, h_cwd, sz, tool, color, model, avg_lat, now, ver, cwd, diff, hr_small_log, h_size`
**Implementation:**
```python
def display_dashboard():
    now = datetime.now()
    hr_default = get_headroom_health(8787)
    hr_small = get_headroom_health(8790)
    ccp_health = get_ccp_health()
    ccp_stats = get_ccp_stats() if ccp_health['running'] else None
    rtk_ver = get_rtk_version()
    gpu = get_gpu_info()
    hr_default_log = Path.home() / '.local/share/headroom/proxy-default.jsonl'
    hr_small_log = Path.home() / '.local/share/headroom/proxy-small.jsonl'
    hr_default_stats = parse_headroom_logs(hr_default_log) if hr_default_log.exists() else None
    hr_small_stats = parse_headroom_logs(hr_small_log) if hr_small_log.exists() else None
    draw_header()
    if gpu:
        draw_section('GPU Hardware', '\U000f08ae')
        draw_kv('Device', gpu, C_GREEN)
        selector = os.environ.get('ONEAPI_DEVICE_SELECTOR', os.environ.get('CUDA_VISIBLE_DEVICES', 'N/A'))
        draw_kv('Device Selector', selector, C_CYAN)
    draw_section('Headroom Compression', '\U000f1059')
    s_dot = status_dot(hr_default['running'])
    ver = hr_default['version'] if hr_default['running'] else 'offline'
    draw_metric(f'Default {C_DIM}(:8787){C_RESET}', f'{s_dot}  {ver}', f"compress={('ON' if hr_default['optimize'] else 'OFF')}  cache={('ON' if hr_default['cache'] else 'OFF')}")
    s_dot = status_dot(hr_small['running'])
    ver = hr_small['version'] if hr_small['running'] else 'offline'
    draw_metric(f'Small   {C_DIM}(:8790){C_RESET}', f'{s_dot}  {ver}', f"compress={('ON' if hr_small['optimize'] else 'OFF')}  cache={('ON' if hr_small['cache'] else 'OFF')}")
    if hr_default_stats and hr_default_stats['requests'] > 0:
        print()
        draw_metric('Default Requests', fmt(hr_default_stats['requests']), 'total')
        draw_metric('Tokens In', tok_fmt(hr_default_stats['tokens_in']), '')
        draw_metric('Tokens Out', tok_fmt(hr_default_stats['tokens_out']), '')
        saved = hr_default_stats['tokens_saved']
        comp_rate = saved / hr_default_stats['tokens_in'] * 100 if hr_default_stats['tokens_in'] > 0 else 0
        draw_metric('Tokens Saved', tok_fmt(saved), f'({comp_rate:.0f}% reduction)')
        if hr_default_stats['latencies']:
            avg_lat = sum(hr_default_stats['latencies']) / len(hr_default_stats['latencies'])
            draw_metric('Avg Latency', ms_fmt(avg_lat), '')
    if hr_small_stats and hr_small_stats['requests'] > 0:
        print()
        draw_metric('Small Requests', fmt(hr_small_stats['requests']), 'total')
        draw_metric('Tokens In', tok_fmt(hr_small_stats['tokens_in']), '')
        draw_metric('Tokens Out', tok_fmt(hr_small_stats['tokens_out']), '')
        saved = hr_small_stats['tokens_saved']
        comp_rate = saved / hr_small_stats['tokens_in'] * 100 if hr_small_stats['tokens_in'] > 0 else 0
        draw_metric('Tokens Saved', tok_fmt(saved), f'({comp_rate:.0f}% reduction)')
    if (not hr_default_stats or hr_default_stats['requests'] == 0) and (not hr_small_stats or hr_small_stats['requests'] == 0):
        print(f'\n{C_DIM}  No requests processed yet — traffic will appear here after use{C_RESET}')
    if ccp_health['running']:
        draw_section('Claude Code Proxy', '\U000f10d7')
        draw_kv('Status', f'{status_dot(True)} Healthy {C_DIM}(:8082){C_RESET}', C_GREEN)
        if ccp_stats:
            print()
            draw_metric('Requests Today', fmt(ccp_stats['requests_today']), '')
            draw_metric('Total Tokens', tok_fmt(ccp_stats['total_tokens']), '')
            draw_metric('Est. Cost', f"${ccp_stats['est_cost']:.4f}", '')
            if ccp_stats['avg_latency'] > 0:
                draw_metric('Avg Latency', ms_fmt(ccp_stats['avg_latency']), '')
            if ccp_stats['recent_requests']:
                print()
                print(f'  {C_DIM}Recent:{C_RESET}')
                for req in ccp_stats['recent_requests'][-5:]:
                    model = req.get('model', 'unknown')[:30]
                    lat = req.get('latency_ms', 0)
                    tok = req.get('total_tokens', 0)
                    print(f'  {C_DIM}→{C_RESET} {C_CYAN}{model}{C_RESET}  {C_GRAY}{ms_fmt(lat)}{C_RESET}  {C_GRAY}{tok_fmt(tok)} tok{C_RESET}')
        else:
            print(f'\n{C_DIM}  No usage data yet — make some requests{C_RESET}')
    else:
        draw_section('Claude Code Proxy', '\U000f10d7')
        print(f'  {C_RED}●{C_RESET} {C_YELLOW}Not running{C_RESET}  {C_DIM}(headroom compression active){C_RESET}')
    draw_section('RTK (Command Compression)', '\U000f0787')
    if rtk_ver:
        draw_kv('Version', rtk_ver, C_GREEN)
    else:
        draw_kv('Status', 'Not installed', C_YELLOW)
    sessions = get_cli_sessions(8)
    if sessions:
        draw_section('CLI Sessions', '\U000f02c1')
        h_tool = f"{'Tool':<14}"
        h_age = f"{'Age':<8}"
        h_msgs = f"{'Msgs':>5}"
        h_size = f"{'Size':>7}"
        h_cwd = f"{'Workspace'}"
        print(f'  {C_DIM}{h_tool} {h_age} {h_msgs} {h_size}  {h_cwd}{C_RESET}')
        draw_separator('─', C_DIM)
        now_ts = now.timestamp()
        for s in sessions:
            diff = now_ts - s['modified']
            if diff < 60:
                age = f'{int(diff)}s'
            elif diff < 3600:
                age = f'{int(diff / 60)}m'
            elif diff < 86400:
                age = f'{int(diff / 3600)}h'
            else:
                age = f'{int(diff / 86400)}d'
            sz = f"{s['size'] / 1024:.0f}K" if s['size'] < 1048576 else f"{s['size'] / 1048576:.1f}M"
            tool = s['tool'][:13]
            cwd = s['cwd'].split('/')[-1] if '/' in s['cwd'] else s['cwd']
            if len(cwd) > 25:
                cwd = '…' + cwd[-24:]
            color = s['color']
            print(f"  {color}{tool:<14}{C_RESET} {C_GRAY}{age:<8}{C_RESET} {C_WHITE}{s['messages']:>5}{C_RESET} {C_GRAY}{sz:>7}{C_RESET}  {C_DIM}{cwd}{C_RESET}")
    print()
    draw_separator('═', C_CYAN)
    print(f'  {C_DIM}Auto-refresh: press Ctrl+C to stop | Data from Headroom (:8787/:8790) + CCP (:8082){C_RESET}')
    print()
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `watch`
**Implementation:**
```python
def main():
    watch = '--watch' in sys.argv
    if watch:
        try:
            while True:
                os.system('clear' if os.name != 'nt' else 'cls')
                display_dashboard()
                time.sleep(2)
        except KeyboardInterrupt:
            print(f'\n{C_DIM}Dashboard stopped{C_RESET}')
    else:
        display_dashboard()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/generate_shame.py
**Path**: `/home/cheta/code/claude-code-proxy/generate_shame.py`


# File Audit: /home/cheta/code/claude-code-proxy/inspect_db.py
**Path**: `/home/cheta/code/claude-code-proxy/inspect_db.py`

## Global Presets & Variables
- `db_path` = `'\\\\wsl.localhost\\Ubuntu\\home\\cheta\\code\\claude-code-proxy\\usage_tracking.db'`

## Dependencies & Imports
sqlite3, json


# File Audit: /home/cheta/code/claude-code-proxy/extract_prompts.py
**Path**: `/home/cheta/code/claude-code-proxy/extract_prompts.py`

**Module Overview**: 
```text
Extract user prompts from Claude Code session logs for this project.
```

## Global Presets & Variables
- `PROJECT_DIR` = `Path.home() / '.claude' / 'projects' / '-home-cheta-code-claude-code-proxy'`
- `OUTPUT_FILE` = `Path('/home/cheta/code/claude-code-proxy/USERPROMPTS.md')`
- `OUTPUT_FILE_V2` = `Path('/home/cheta/code/claude-code-proxy/USERPROMPTS-v2.md')`

## Dependencies & Imports
json, os, sys, pathlib.Path, datetime.datetime

## Feature Function: `extract_text_from_content`
**Logic & Purpose:**
```text
Extract readable text from message content (string or list).
```

**Parameters:** `content`
**Variables Used:** `text, btype, parts`
**Implementation:**
```python
def extract_text_from_content(content):
    """Extract readable text from message content (string or list)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get('type', '')
                if btype == 'text':
                    parts.append(block.get('text', ''))
        text = '\n'.join((p for p in parts if p.strip()))
        return text.strip()
    return ''
```

---

## Feature Function: `extract_prompts_from_jsonl`
**Logic & Purpose:**
```text
Extract user prompts from a single JSONL session file.
```

**Parameters:** `jsonl_path`
**Variables Used:** `parent, line, entry, message, text, is_first_msg, timestamp, all_tool_results, content, prompts`
**Implementation:**
```python
def extract_prompts_from_jsonl(jsonl_path: Path) -> list[dict]:
    """Extract user prompts from a single JSONL session file."""
    prompts = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get('type') != 'user':
                    continue
                message = entry.get('message', {})
                if message.get('role') != 'user':
                    continue
                content = message.get('content', '')
                text = extract_text_from_content(content)
                if not text or len(text.strip()) == 0:
                    continue
                parent = entry.get('parentUuid')
                is_first_msg = parent is None
                if isinstance(content, list):
                    all_tool_results = all((isinstance(b, dict) and b.get('type') == 'tool_result' for b in content if isinstance(b, dict)))
                    if all_tool_results and (not any((isinstance(b, dict) and b.get('type') == 'text' for b in content))):
                        continue
                timestamp = entry.get('timestamp', '')
                prompts.append({'text': text, 'timestamp': timestamp, 'session': jsonl_path.stem, 'line': line_num, 'is_first': is_first_msg})
    except Exception as e:
        print(f'  Error reading {jsonl_path.name}: {e}', file=sys.stderr)
    return prompts
```

---

## Feature Function: `normalize_for_dedup`
**Logic & Purpose:**
```text
Normalize text for deduplication: collapse whitespace, lowercase, strip.
```

**Parameters:** `text`
**Implementation:**
```python
def normalize_for_dedup(text: str) -> str:
    """Normalize text for deduplication: collapse whitespace, lowercase, strip."""
    import re
    return re.sub('\\s+', ' ', text.strip().lower())
```

---

## Feature Function: `deduplicate_prompts`
**Logic & Purpose:**
```text
Remove duplicate prompts, keeping the first occurrence.

Returns (deduped_list, num_removed).
```

**Parameters:** `prompts`
**Variables Used:** `key, seen, result`
**Implementation:**
```python
def deduplicate_prompts(prompts: list[dict]) -> tuple[list[dict], int]:
    """Remove duplicate prompts, keeping the first occurrence.

    Returns (deduped_list, num_removed).
    """
    seen = set()
    result = []
    for p in prompts:
        key = normalize_for_dedup(p['text'])
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return (result, len(prompts) - len(result))
```

---

## Feature Function: `write_prompts_md`
**Logic & Purpose:**
```text
Write prompts to a markdown file.
```

**Parameters:** `prompts, output_path, num_sessions, dupes_removed, truncate`
**Variables Used:** `ts_str, text, prompt_num, current_session, ts, marker`
**Implementation:**
```python
def write_prompts_md(prompts: list[dict], output_path: Path, num_sessions: int, dupes_removed: int=0, truncate: bool=False):
    """Write prompts to a markdown file."""
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('# User Prompts — Claude Code Sessions\n\n')
        out.write(f'> Extracted **{len(prompts)}** unique prompts from {num_sessions} sessions\n')
        if dupes_removed > 0:
            out.write(f'> Deduplicated: {dupes_removed} duplicate prompts removed\n')
        out.write(f'> Project: `~/code/claude-code-proxy`\n')
        out.write(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if not truncate:
            out.write(f'> Full-length prompts (no truncation)\n')
        out.write('\n---\n\n')
        current_session = None
        prompt_num = 0
        for p in prompts:
            if p['session'] != current_session:
                current_session = p['session']
                prompt_num = 0
                out.write(f'\n## Session: `{current_session}`\n\n')
            prompt_num += 1
            ts = p['timestamp']
            ts_str = str(ts) if ts else '(no timestamp)'
            marker = '🟢 INITIAL' if p['is_first'] else ''
            out.write(f'### Prompt {prompt_num} {marker} — {ts_str}\n\n')
            text = p['text']
            if truncate and len(text) > 3000:
                text = text[:3000] + f"\n\n... (truncated, {len(p['text'])} chars total)"
            out.write(f'```\n{text}\n```\n\n')
```

---

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `mtime, all_prompts, jsonl_files, prompts, size_kb`
**Implementation:**
```python
def main():
    if not PROJECT_DIR.exists():
        print(f'Project dir not found: {PROJECT_DIR}', file=sys.stderr)
        sys.exit(1)
    jsonl_files = sorted(PROJECT_DIR.glob('*.jsonl'), key=lambda p: p.stat().st_mtime)
    print(f'Found {len(jsonl_files)} session files in {PROJECT_DIR}')
    all_prompts = []
    for jf in jsonl_files:
        size_kb = jf.stat().st_size / 1024
        mtime = datetime.fromtimestamp(jf.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f'  Processing {jf.name} ({size_kb:.0f}KB, modified {mtime})')
        prompts = extract_prompts_from_jsonl(jf)
        all_prompts.extend(prompts)
        print(f'    → {len(prompts)} user prompts extracted')
    deduped, dupes_removed = deduplicate_prompts(all_prompts)
    print(f'\nDeduplication: {len(all_prompts)} → {len(deduped)} ({dupes_removed} duplicates removed)')
    write_prompts_md(deduped, OUTPUT_FILE_V2, len(jsonl_files), dupes_removed=dupes_removed, truncate=False)
    print(f'✅ Written {len(deduped)} prompts to {OUTPUT_FILE_V2} (full-length, deduped)')
    write_prompts_md(deduped, OUTPUT_FILE, len(jsonl_files), dupes_removed=dupes_removed, truncate=True)
    print(f'✅ Updated {OUTPUT_FILE} (truncated, deduped)')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/start_proxy.py
**Path**: `/home/cheta/code/claude-code-proxy/start_proxy.py`

**Module Overview**: 
```text
Start Claude Code Proxy server.
```

## Dependencies & Imports
sys, os, argparse

## Feature Function: `main`
**Logic & Purpose:**
```text
Parse CLI arguments and start the proxy.
```

**Parameters:** ``
**Variables Used:** `model_config_group, parser, issues, env_updates, reasoning_group, tools_group, config, changes, skip_validation, host, key, validation_group, result, has_key, env_key, mode_group, passed, crosstalk_group, temp_config, sock, server_group, model_group, key_preview, port`
**Implementation:**
```python
def main():
    """Parse CLI arguments and start the proxy."""
    parser = argparse.ArgumentParser(description='Claude Code Proxy - Use Claude API with OpenAI-compatible providers', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\n✨ Usage Tips:\n  → All Settings:        %(prog)s --settings\n  → Configure Models:    %(prog)s --select-models\n  → View Analytics:      %(prog)s --analytics\n  → Health Check:        %(prog)s --doctor\n  → Dry Run:             %(prog)s --dry-run\n  \n  → Standard Start:      %(prog)s\n  → Force Setup:         %(prog)s --setup\n\nFor more details, see docs/guides/configuration.md\n        ')
    model_group = parser.add_argument_group('🤖 Model Configuration')
    reasoning_group = parser.add_argument_group('🧠 Reasoning & Thinking')
    server_group = parser.add_argument_group('🔌 Server Settings')
    mode_group = parser.add_argument_group('💾 Profile/Mode Management')
    crosstalk_group = parser.add_argument_group('🗣️  Crosstalk Orchestration')
    tools_group = parser.add_argument_group('🛠️  Interactive Tools & Config')
    validation_group = parser.add_argument_group('✅ Validation & Diagnostics')
    model_group.add_argument('--big-model', dest='big_model', metavar='MODEL', help='Model for Claude Opus requests')
    model_group.add_argument('--middle-model', dest='middle_model', metavar='MODEL', help='Model for Claude Sonnet requests')
    model_group.add_argument('--small-model', dest='small_model', metavar='MODEL', help='Model for Claude Haiku requests')
    model_group.add_argument('--select-models', action='store_true', help='Launch interactive model selector')
    model_group.add_argument('--model-cascade', dest='model_cascade', action='store_true', help='Enable model cascade fallback on provider errors')
    reasoning_group.add_argument('--reasoning-effort', dest='reasoning_effort', choices=['low', 'medium', 'high'], help='Reasoning effort level (low, medium, high)')
    reasoning_group.add_argument('--verbosity', dest='verbosity', help='Response verbosity level')
    reasoning_group.add_argument('--reasoning-exclude', dest='reasoning_exclude', choices=['true', 'false'], help='Whether to exclude reasoning tokens from response')
    server_group.add_argument('--host', dest='host', metavar='HOST', help='Server host (default: 0.0.0.0)')
    server_group.add_argument('--port', dest='port', type=int, metavar='PORT', help='Server port (default: 8082)')
    server_group.add_argument('--log-level', dest='log_level', choices=['debug', 'info', 'warning', 'error', 'critical'], help='Logging level')
    mode_group.add_argument('--list-modes', action='store_true', help='List all saved modes')
    mode_group.add_argument('--load-mode', dest='load_mode', metavar='ID/NAME', help='Load a saved mode (ID or name)')
    mode_group.add_argument('--save-mode', dest='save_mode', metavar='NAME', help='Save current configuration as a mode')
    mode_group.add_argument('--delete-mode', dest='delete_mode', metavar='ID/NAME', help='Delete a saved mode')
    mode_group.add_argument('--mode', dest='mode_name', metavar='NAME', help='Shorthand for --save-mode')
    crosstalk_group.add_argument('--crosstalk-studio', action='store_true', help='Launch Crosstalk Studio TUI (visual multi-model chat)')
    crosstalk_group.add_argument('--crosstalk-init', action='store_true', help='Launch interactive crosstalk setup wizard')
    crosstalk_group.add_argument('--crosstalk', dest='crosstalk_models', help='Quick setup (comma-separated models)')
    crosstalk_group.add_argument('--system-prompt-big', dest='big_system_prompt', help='System prompt for BIG model')
    crosstalk_group.add_argument('--system-prompt-middle', dest='middle_system_prompt', help='System prompt for MIDDLE model')
    crosstalk_group.add_argument('--system-prompt-small', dest='small_system_prompt', help='System prompt for SMALL model')
    crosstalk_group.add_argument('--crosstalk-iterations', dest='crosstalk_iterations', type=int, help='Number of iterations (default: 20)')
    crosstalk_group.add_argument('--crosstalk-topic', dest='crosstalk_topic', help='Initial topic')
    crosstalk_group.add_argument('--crosstalk-paradigm', dest='crosstalk_paradigm', choices=['memory', 'report', 'relay', 'debate'], help='Communication paradigm')
    tools_group.add_argument('--setup', action='store_true', help='Launch first-time setup wizard')
    tools_group.add_argument('--configure-prompts', action='store_true', help='Launch prompt injection configurator')
    tools_group.add_argument('--configure-terminal', action='store_true', help='Launch terminal output configurator')
    tools_group.add_argument('--configure-dashboard', action='store_true', help='Launch dashboard module configurator')
    tools_group.add_argument('--analytics', action='store_true', help='View usage analytics')
    tools_group.add_argument('--settings', action='store_true', help='Launch unified settings TUI (models, terminal, dashboard, prompts)')
    tools_group.add_argument('--doctor', action='store_true', help='Run health check and auto-fix common issues')
    tools_group.add_argument('--configure-advanced', action='store_true', help='Launch advanced configuration TUI (reasoning, prompts, hybrid mode)')
    tools_group.add_argument('--fix-keys', action='store_true', help='(Deprecated, use --doctor) Launch API key repair wizard')
    model_config_group = parser.add_argument_group('⚡ Quick Model Setup')
    model_config_group.add_argument('--set-big', metavar='MODEL', help='Quick set BIG model (e.g., vibeproxy/gemini-opus)')
    model_config_group.add_argument('--set-middle', metavar='MODEL', help='Quick set MIDDLE model (e.g., vibeproxy/gemini-pro-3)')
    model_config_group.add_argument('--set-small', metavar='MODEL', help='Quick set SMALL model (e.g., openrouter/gpt-4o-mini)')
    model_config_group.add_argument('--show-models', action='store_true', help='Show available models from all configured endpoints')
    model_config_group.add_argument('--check-endpoints', action='store_true', help='Check endpoint connectivity and API key validity')
    model_config_group.add_argument('--update-models', action='store_true', help='Scrape latest model stats (pricing, limits) from providers')
    model_config_group.add_argument('--rank-models', action='store_true', help='AI-rank free models for coding capability')
    validation_group.add_argument('--config', dest='show_config', action='store_true', help='Show current configuration and exit')
    validation_group.add_argument('--validate-config', action='store_true', help='Validate configuration and exit')
    validation_group.add_argument('--skip-validation', action='store_true', help='Skip configuration validation on startup')
    validation_group.add_argument('--dry-run', action='store_true', help='Validate config and check readiness without starting server')
    validation_group.add_argument('--client', action='store_true', help='Run as client wrapper (internal use)')
    args, unknown = parser.parse_known_args()
    if args.settings:
        from src.cli.settings import main as settings_main
        settings_main()
        return
    if getattr(args, 'crosstalk_studio', False):
        from src.cli.crosstalk_studio import main as crosstalk_main
        crosstalk_main()
        return
    if args.doctor or args.fix_keys:
        from src.cli.fix_keys import main as fix_keys_main
        if args.fix_keys:
            print('⚠️  --fix-keys is deprecated. Use --doctor instead.')
        fix_keys_main()
        return
    if getattr(args, 'configure_advanced', False):
        from src.cli.advanced_config import main as advanced_main
        advanced_main()
        return
    if args.client:
        from src.cli.client_wrapper import main as client_main
        client_main(unknown)
        return
    if args.set_big or args.set_middle or args.set_small:
        from src.cli.quick_config import set_model
        changes = False
        if args.set_big:
            print('\n🔧 Configuring BIG model...')
            if set_model('big', args.set_big):
                changes = True
        if args.set_middle:
            print('\n🔧 Configuring MIDDLE model...')
            if set_model('middle', args.set_middle):
                changes = True
        if args.set_small:
            print('\n🔧 Configuring SMALL model...')
            if set_model('small', args.set_small):
                changes = True
        if changes:
            print('\n💡 Restart the proxy for changes to take effect.')
        return
    if args.show_models:
        import asyncio
        from src.cli.quick_config import show_models
        asyncio.run(show_models())
        return
    if args.check_endpoints:
        import asyncio
        from src.cli.quick_config import check_endpoints
        asyncio.run(check_endpoints())
        return
    if args.update_models:
        import asyncio
        from src.services.models.scrape_model_stats import update_model_database, get_scraper_model
        print(f'🤖 Using model: {get_scraper_model()}')
        print('   (Set SCRAPER_MODEL env var to use a different model)')
        asyncio.run(update_model_database('openrouter'))
        return
    if args.rank_models:
        import asyncio
        from src.services.models.model_ranker import update_rankings, get_ranker_model
        print(f'🤖 Using model: {get_ranker_model()}')
        print('   (Set RANKER_MODEL env var to use a different model)')
        asyncio.run(update_rankings())
        return
    if args.validate_config:
        from src.core.validator import validate_config_on_startup
        passed = validate_config_on_startup(strict=False)
        sys.exit(0 if passed else 1)
    if args.show_config:
        from src.core.config import Config
        from src.services.logging.startup_display import display_startup_config
        config = Config()
        display_startup_config(config)
        sys.exit(0)
    if args.dry_run:
        from src.core.config import Config
        import socket
        print('\n🔍 Dry Run - Checking configuration...\n')
        config = Config()
        issues = []
        if config.openai_api_key and 'dummy' not in config.openai_api_key:
            key_preview = config.openai_api_key[:8] + '...' + config.openai_api_key[-4:]
            print(f'✓ Provider API Key: {key_preview}')
        else:
            issues.append('No valid API key configured')
            print('✗ Provider API Key: Not configured')
        print(f'✓ Provider URL: {config.openai_base_url}')
        print(f'✓ Big Model: {config.big_model}')
        print(f'✓ Middle Model: {config.middle_model}')
        print(f'✓ Small Model: {config.small_model}')
        port = config.port
        host = config.host
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host if host != '0.0.0.0' else '127.0.0.1', port))
            sock.close()
            if result == 0:
                issues.append(f'Port {port} is already in use')
                print(f'✗ Port {port}: Already in use')
            else:
                print(f'✓ Port {port}: Available')
        except Exception as e:
            print(f'? Port {port}: Could not check ({e})')
        print(f"✓ Dashboard: {('enabled' if config.enable_dashboard else 'disabled')}")
        print(f"✓ Tracking: {('enabled' if config.track_usage else 'disabled')}")
        print()
        if issues:
            print(f'⚠️  Found {len(issues)} issue(s):')
            for issue in issues:
                print(f'   - {issue}')
            print('\nRun with --doctor to attempt auto-fix.')
            sys.exit(1)
        else:
            print('✅ All checks passed. Ready to launch.')
            print('   Run without --dry-run to start the server.')
            sys.exit(0)
    if args.setup:
        from src.cli.wizard import main as wizard_main
        wizard_main()
        return
    if not args.skip_validation:
        from src.core.config import Config
        temp_config = Config()
        key = temp_config.openai_api_key
        has_key = key and 'dummy' not in key and ('your-' not in key)
        if not has_key:
            print('\n⚠️  No Provider API Key detected!')
            print('   Redirecting to setup wizard...\n')
            try:
                from src.cli.wizard import main as wizard_main
                wizard_main()
                return
            except ImportError:
                print('❌ Wizard not found. Please configure .env manually.')
                sys.exit(1)
            except Exception as e:
                print(f'❌ Error launching wizard: {e}')
                sys.exit(1)
    from src.cli.crosstalk_cli import handle_crosstalk_operations
    if handle_crosstalk_operations(args):
        return
    if args.configure_prompts:
        from src.cli.prompt_config import main as prompt_main
        prompt_main()
        return
    if args.configure_terminal:
        from src.cli.terminal_config import main as terminal_main
        terminal_main()
        return
    if args.analytics:
        from src.cli.analytics import main as analytics_main
        analytics_main()
        return
    if args.configure_dashboard:
        from src.cli.dashboard_config import main as dashboard_main
        dashboard_main()
        return
    if args.select_models:
        from src.cli.model_selector import run_model_selector
        run_model_selector()
        return
    from src.services.logging.startup_display import print_startup_banner
    from src.services.models.provider_detector import validate_provider_config
    from src.services.models.modes import ModeManager
    if ModeManager.handle_mode_operations(args):
        return
    env_updates = {}
    skip_validation = args.skip_validation
    for key, value in vars(args).items():
        if value is not None and key not in ['show_config', 'select_models', 'validate_config', 'skip_validation']:
            env_key = key.upper().replace('-', '_')
            env_updates[f'CLAUDE_{env_key}'] = str(value)
    from src.main import main as start_main
    start_main(env_updates, skip_validation=skip_validation)
```

---


Error parsing /home/cheta/code/claude-code-proxy/test_startup.sh: unterminated string literal (detected at line 7) (<unknown>, line 7)

# File Audit: /home/cheta/code/claude-code-proxy/test_keyword_detection.py
**Path**: `/home/cheta/code/claude-code-proxy/test_keyword_detection.py`

**Module Overview**: 
```text
Quick verification: keyword-based model capability detection.
```

## Global Presets & Variables
- `tests` = `[('gemini-claude-opus-4-6-thinking', True, 'thinking_budget'), ('claude-opus-4-20250514', True, 'thinking_tokens'), ('claude-sonnet-4-20250514', True, 'thinking_tokens'), ('claude-3-7-sonnet-20250219', True, 'thinking_tokens'), ('o4-mini', True, 'effort'), ('gpt-5', True, 'effort'), ('gemini-2.5-flash-preview-04-17', False, ''), ('gemini-4-flash-thinking', True, 'thinking_budget'), ('gpt-4o', False, ''), ('anthropic/claude-opus-4', True, 'thinking_tokens'), ('vibeproxy/claude-opus-4-6-thinking', True, 'thinking_budget'), ('gemini-claude-opus-4-7-thinking', True, 'thinking_budget'), ('claude-opus-5-future', True, 'thinking_tokens')]`
- `all_pass` = `True`

## Dependencies & Imports
src.core.reasoning_validator.is_reasoning_capable_model


# File Audit: /home/cheta/code/claude-code-proxy/inspect_usage_db.py
**Path**: `/home/cheta/code/claude-code-proxy/inspect_usage_db.py`

**Module Overview**: 
```text
Inspect usage_tracking.db for recent activity and errors.
```

## Global Presets & Variables
- `DB_PATH` = `Path(__file__).parent / 'usage_tracking.db'`

## Dependencies & Imports
sqlite3, os, pathlib.Path, datetime.datetime

## Feature Function: `main`
**Parameters:** ``
**Variables Used:** `count, cur, rows, cols, d, conn, tables`
**Implementation:**
```python
def main():
    if not DB_PATH.exists():
        print(f'DB not found: {DB_PATH}')
        return
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r['name'] for r in cur.fetchall()]
    print(f'Tables: {tables}\n')
    for table in tables:
        cur.execute(f'PRAGMA table_info({table})')
        cols = [(r['name'], r['type']) for r in cur.fetchall()]
        print(f'── {table} ({len(cols)} columns) ──')
        for name, typ in cols:
            print(f'  {name}: {typ}')
        cur.execute(f'SELECT COUNT(*) as cnt FROM {table}')
        count = cur.fetchone()['cnt']
        print(f'  Total rows: {count}')
        if count > 0:
            cur.execute(f'SELECT * FROM {table} ORDER BY rowid DESC LIMIT 10')
            rows = cur.fetchall()
            print(f'  Last {len(rows)} rows:')
            for row in rows:
                d = dict(row)
                for k, v in d.items():
                    if isinstance(v, str) and len(v) > 100:
                        d[k] = v[:100] + '...'
                print(f'    {d}')
        print()
    conn.close()
```

---


Error parsing /home/cheta/code/claude-code-proxy/restart_proxy.sh: invalid syntax (<unknown>, line 4)

Error parsing /home/cheta/code/claude-code-proxy/find_headroom.sh: invalid syntax (<unknown>, line 2)

# File Audit: /home/cheta/code/claude-code-proxy/docs/examples/demo_prompt_injection.py
**Path**: `/home/cheta/code/claude-code-proxy/docs/examples/demo_prompt_injection.py`

**Module Overview**: 
```text
Demo script for prompt injection system.

Shows all three output formats with sample data.
```

## Dependencies & Imports
sys, pathlib.Path, src.utils.prompt_injector.prompt_injector, src.utils.prompt_injection_middleware.prompt_injection_middleware, src.utils.prompt_injection_middleware.update_proxy_status

## Feature Function: `generate_sample_data`
**Logic & Purpose:**
```text
Generate sample proxy status data
```

**Parameters:** ``
**Implementation:**
```python
def generate_sample_data():
    """Generate sample proxy status data"""
    return {'status': {'passthrough_mode': False, 'provider': 'OpenRouter', 'base_url': 'https://openrouter.ai/api/v1', 'big_model': 'openai/gpt-4o', 'middle_model': 'openai/gpt-4o', 'small_model': 'gpt-4o-mini', 'reasoning_effort': 'high', 'reasoning_max_tokens': '8000', 'track_usage': True, 'compact_logger': False}, 'performance': {'total_requests': 847, 'today_requests': 94, 'avg_latency_ms': 3421, 'min_latency_ms': 1234, 'max_latency_ms': 8765, 'avg_tokens_per_sec': 78, 'max_tokens_per_sec': 234, 'total_input_tokens': 2145678, 'total_output_tokens': 456789, 'total_thinking_tokens': 12345, 'avg_input_tokens': 2534, 'avg_output_tokens': 539, 'avg_thinking_tokens': 15, 'avg_context_tokens': 43700, 'avg_context_limit': 200000, 'total_cost': 12.34, 'today_cost': 2.47, 'avg_cost_per_request': 0.015}, 'errors': {'success_count': 847, 'total_count': 859, 'error_types': {'Rate Limit': 7, 'Invalid Key': 3, 'Model Not Found': 2}, 'recent_errors': [{'time': '14:23', 'type': 'Rate Limit', 'message': 'Rate limit exceeded', 'model': 'openai/gpt-4o'}, {'time': '14:18', 'type': 'Invalid Key', 'message': 'Invalid API key', 'model': 'anthropic/claude-3.5-sonnet'}, {'time': '14:05', 'type': 'Model Not Found', 'message': 'Model not found', 'model': 'fake/model-123'}]}, 'models': {'top_models': [{'name': 'openai/gpt-4o', 'requests': 245, 'tokens': 125300, 'cost': 1.45}, {'name': 'anthropic/claude-3.5-sonnet', 'requests': 89, 'tokens': 52100, 'cost': 0.89}, {'name': 'ollama/qwen2.5:72b', 'requests': 34, 'tokens': 18900, 'cost': 0}], 'usage_by_type': {'text_only': 312, 'with_tools': 45, 'with_images': 23}, 'recommendations': ['34 requests to FREE model (saved $0.45)', 'Consider: qwen/qwen-2.5-thinking for reasoning tasks'], 'free_savings': 0.45}}
```

---

## Feature Function: `demo_all_formats`
**Logic & Purpose:**
```text
Demonstrate all output formats
```

**Parameters:** ``
**Variables Used:** `data, header, single, expanded, mini`
**Implementation:**
```python
def demo_all_formats():
    """Demonstrate all output formats"""
    data = generate_sample_data()
    update_proxy_status(data)
    print('=' * 80)
    print('PROMPT INJECTION DEMO - ALL FORMATS')
    print('=' * 80)
    print()
    print('╔' + '═' * 78 + '╗')
    print('║' + ' ' * 24 + 'FORMAT 1: EXPANDED (Multi-line Detailed)' + ' ' * 14 + '║')
    print('╚' + '═' * 78 + '╝')
    print()
    expanded = prompt_injector.generate_prompt_context(format='expanded')
    print(expanded)
    print()
    print(f'Token cost: ~400-500 tokens')
    print(f'Use case: Complex tasks, debugging, full context needed')
    print()
    print()
    print('╔' + '═' * 78 + '╗')
    print('║' + ' ' * 24 + 'FORMAT 2: SINGLE (One-line Compact)' + ' ' * 19 + '║')
    print('╚' + '═' * 78 + '╝')
    print()
    single = prompt_injector.generate_prompt_context(format='single')
    print(single)
    print()
    print(f'Token cost: ~150-200 tokens')
    print(f'Use case: Standard tasks, balanced info/noise ratio')
    print()
    print()
    print('╔' + '═' * 78 + '╗')
    print('║' + ' ' * 21 + 'FORMAT 3: MINI (Ultra-compact Partial Line)' + ' ' * 13 + '║')
    print('╚' + '═' * 78 + '╝')
    print()
    mini = prompt_injector.generate_prompt_context(format='mini')
    print(mini)
    print()
    print(f'Token cost: ~50-80 tokens')
    print(f'Use case: Moderate visibility, compact format')
    print()
    print()
    print('╔' + '═' * 78 + '╗')
    print('║' + ' ' * 20 + 'FORMAT 4: COMPACT HEADER (Always-on Mode)' + ' ' * 17 + '║')
    print('╚' + '═' * 78 + '╝')
    print()
    header = prompt_injection_middleware.get_compact_header()
    print(f'[{header}]')
    print()
    print(f'Token cost: ~20-30 tokens')
    print(f'Use case: Every request, minimal overhead')
    print()
    print()
```

---

## Feature Function: `demo_injection_strategies`
**Logic & Purpose:**
```text
Demonstrate different injection strategies
```

**Parameters:** ``
**Variables Used:** `request, system_prompt, enhanced, header, modified`
**Implementation:**
```python
def demo_injection_strategies():
    """Demonstrate different injection strategies"""
    print('=' * 80)
    print('INJECTION STRATEGIES')
    print('=' * 80)
    print()
    print('┌─ Strategy 1: Auto-Inject ─────────────────────────────────────────┐')
    print('│ Automatically inject based on request characteristics             │')
    print('└────────────────────────────────────────────────────────────────────┘')
    print()
    request = {'model': 'claude-3-5-sonnet-20241022', 'messages': [{'role': 'user', 'content': 'Write a Python function to calculate fibonacci...'}], 'stream': True, 'tools': [{'name': 'execute_code', 'description': 'Execute Python code'}]}
    prompt_injection_middleware.configure(enabled=True, format='single', inject_mode='auto')
    modified = prompt_injection_middleware.inject_into_request(request)
    print('Original request has streaming and tools → Auto-inject ENABLED')
    print()
    print('Modified request messages:')
    for i, msg in enumerate(modified['messages']):
        print(f"  Message {i} ({msg['role']}): {msg['content'][:100]}...")
    print()
    print()
    print('┌─ Strategy 2: Compact Header Always ───────────────────────────────┐')
    print('│ Add compact header to every request (minimal tokens)              │')
    print('└────────────────────────────────────────────────────────────────────┘')
    print()
    header = prompt_injection_middleware.get_compact_header()
    print(f'Compact header: [{header}]')
    print()
    print('Prepend to first user message:')
    print(f'  messages[0]["content"] = "[{header}]\\n\\n{{original_content}}"')
    print()
    print()
    print('┌─ Strategy 3: System Prompt Injection ─────────────────────────────┐')
    print('│ Inject into system prompt only                                    │')
    print('└────────────────────────────────────────────────────────────────────┘')
    print()
    system_prompt = 'You are a helpful coding assistant. You write clean, efficient code.'
    enhanced = prompt_injection_middleware.inject_into_system_prompt(system_prompt)
    print('Original system prompt:')
    print(f'  {system_prompt}')
    print()
    print('Enhanced system prompt preview:')
    print(f'  {enhanced[:100]}...')
    print()
    print()
```

---

## Feature Function: `demo_module_selection`
**Logic & Purpose:**
```text
Demonstrate selective module injection
```

**Parameters:** ``
**Variables Used:** `perf_only, debug, status_only, data`
**Implementation:**
```python
def demo_module_selection():
    """Demonstrate selective module injection"""
    print('=' * 80)
    print('SELECTIVE MODULE INJECTION')
    print('=' * 80)
    print()
    data = generate_sample_data()
    update_proxy_status(data)
    print('┌─ Only Status Module ───────────────────────────────────────────────┐')
    print('│ For basic routing awareness                                        │')
    print('└─────────────────────────────────────────────────────────────────────┘')
    print()
    status_only = prompt_injector.generate_prompt_context(format='single', modules=['status'])
    print(status_only)
    print()
    print('┌─ Only Performance Module ──────────────────────────────────────────┐')
    print('│ For optimization and speed insights                                │')
    print('└─────────────────────────────────────────────────────────────────────┘')
    print()
    perf_only = prompt_injector.generate_prompt_context(format='single', modules=['performance'])
    print(perf_only)
    print()
    print('┌─ Status + Errors (Debugging) ──────────────────────────────────────┐')
    print('│ For troubleshooting and error analysis                             │')
    print('└─────────────────────────────────────────────────────────────────────┘')
    print()
    debug = prompt_injector.generate_prompt_context(format='single', modules=['status', 'errors'])
    print(debug)
    print()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/cli/claude_proxy.py
**Path**: `/home/cheta/code/claude-code-proxy/cli/claude_proxy.py`

**Module Overview**: 
```text
Claude Proxy CLI Tool - Phase 4

Command-line interface for interacting with the Claude Proxy analytics platform.

Features:
- Authentication and API key management
- Query analytics data
- Generate reports
- Manage alerts
- Predictive analytics
- Integration with CI/CD

Author: AI Architect
Date: 2026-01-05

Usage:
    claude-proxy analytics --start 2026-01-01 --end 2026-01-05
    claude-proxy alerts list
    claude-proxy report generate --template weekly --format pdf
    claude-proxy predictive forecast --days 7
    claude-proxy auth login --api-key your_key_here
```

## Dependencies & Imports
argparse, json, sys, requests, datetime.datetime, datetime.timedelta, typing.Dict, typing.Any, typing.Optional, os, pathlib.Path, csv

## Feature Class: `ClaudeProxyClient`
**Description:**
```text
Python SDK for Claude Proxy API
```

### Method: `__init__`
**Parameters:** `self, base_url, api_key`
**Implementation:**
```python
def __init__(self, base_url: str='http://localhost:8082', api_key: Optional[str]=None):
    self.base_url = base_url.rstrip('/')
    self.api_key = api_key
    self.session = requests.Session()
    if api_key:
        self.session.headers.update({'Authorization': api_key})
```

### Method: `set_api_key`
**Logic & Purpose:**
```text
Set API key for authentication
```

**Parameters:** `self, api_key`
**Implementation:**
```python
def set_api_key(self, api_key: str):
    """Set API key for authentication"""
    self.api_key = api_key
    self.session.headers['Authorization'] = api_key
```

### Method: `get_analytics`
**Logic & Purpose:**
```text
Get analytics data
```

**Parameters:** `self, start_date, end_date, metric, group_by`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_analytics(self, start_date: str, end_date: str, metric: str='tokens', group_by: str='day') -> Dict[str, Any]:
    """Get analytics data"""
    params = {'metric': metric, 'start_date': start_date, 'end_date': end_date, 'group_by': group_by}
    response = self.session.get(f'{self.base_url}/api/analytics/timeseries', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `get_custom_query`
**Logic & Purpose:**
```text
Execute custom query
```

**Parameters:** `self, metrics, start_date, end_date`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_custom_query(self, metrics: str, start_date: str, end_date: str, **kwargs) -> Dict[str, Any]:
    """Execute custom query"""
    params = {'metrics': metrics, 'start_date': start_date, 'end_date': end_date, **kwargs}
    response = self.session.get(f'{self.base_url}/api/analytics/custom', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `get_aggregate_stats`
**Logic & Purpose:**
```text
Get aggregate statistics
```

**Parameters:** `self, start_date, end_date`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_aggregate_stats(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get aggregate statistics"""
    params = {'start_date': start_date, 'end_date': end_date}
    response = self.session.get(f'{self.base_url}/api/analytics/aggregate', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `get_predictions`
**Logic & Purpose:**
```text
Get predictive forecast
```

**Parameters:** `self, days`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_predictions(self, days: int=7) -> Dict[str, Any]:
    """Get predictive forecast"""
    params = {'days': days}
    response = self.session.get(f'{self.base_url}/api/predictive/forecast', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `get_smart_thresholds`
**Logic & Purpose:**
```text
Get smart thresholds
```

**Parameters:** `self, metric`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_smart_thresholds(self, metric: str) -> Dict[str, Any]:
    """Get smart thresholds"""
    params = {'metric': metric}
    response = self.session.get(f'{self.base_url}/api/predictive/thresholds', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `detect_anomaly`
**Logic & Purpose:**
```text
Detect if request is anomalous
```

**Parameters:** `self, request_data`
**Variables Used:** `response`
**Implementation:**
```python
def detect_anomaly(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detect if request is anomalous"""
    response = self.session.post(f'{self.base_url}/api/predictive/detect-anomaly', json=request_data)
    response.raise_for_status()
    return response.json()
```

### Method: `list_alerts`
**Logic & Purpose:**
```text
List all alert rules
```

**Parameters:** `self`
**Variables Used:** `response`
**Implementation:**
```python
def list_alerts(self) -> Dict[str, Any]:
    """List all alert rules"""
    response = self.session.get(f'{self.base_url}/api/alerts/rules')
    response.raise_for_status()
    return response.json()
```

### Method: `create_alert`
**Logic & Purpose:**
```text
Create alert rule
```

**Parameters:** `self, name, condition, priority`
**Variables Used:** `response, payload`
**Implementation:**
```python
def create_alert(self, name: str, condition: Dict[str, Any], priority: int=2) -> Dict[str, Any]:
    """Create alert rule"""
    payload = {'name': name, 'description': f'CLI created alert: {name}', 'condition_json': json.dumps(condition), 'priority': priority}
    response = self.session.post(f'{self.base_url}/api/alerts/rules', json=payload)
    response.raise_for_status()
    return response.json()
```

### Method: `get_alert_history`
**Logic & Purpose:**
```text
Get alert history
```

**Parameters:** `self, limit`
**Variables Used:** `params, response`
**Implementation:**
```python
def get_alert_history(self, limit: int=50) -> Dict[str, Any]:
    """Get alert history"""
    params = {'limit': limit}
    response = self.session.get(f'{self.base_url}/api/alerts/history', params=params)
    response.raise_for_status()
    return response.json()
```

### Method: `list_templates`
**Logic & Purpose:**
```text
List report templates
```

**Parameters:** `self`
**Variables Used:** `response`
**Implementation:**
```python
def list_templates(self) -> Dict[str, Any]:
    """List report templates"""
    response = self.session.get(f'{self.base_url}/api/reports/templates')
    response.raise_for_status()
    return response.json()
```

### Method: `generate_report`
**Logic & Purpose:**
```text
Generate report
```

**Parameters:** `self, template_id, start_date, end_date, format_type`
**Variables Used:** `response, payload`
**Implementation:**
```python
def generate_report(self, template_id: str, start_date: str, end_date: str, format_type: str='excel') -> Dict[str, Any]:
    """Generate report"""
    payload = {'template_id': template_id, 'start_date': start_date, 'end_date': end_date, 'format': format_type}
    response = self.session.post(f'{self.base_url}/api/reports/generate', json=payload)
    response.raise_for_status()
    return response.json()
```

### Method: `get_scheduled_reports`
**Logic & Purpose:**
```text
Get scheduled reports
```

**Parameters:** `self`
**Variables Used:** `response`
**Implementation:**
```python
def get_scheduled_reports(self) -> Dict[str, Any]:
    """Get scheduled reports"""
    response = self.session.get(f'{self.base_url}/api/reports/schedule')
    response.raise_for_status()
    return response.json()
```

### Method: `list_integrations`
**Logic & Purpose:**
```text
List integrations
```

**Parameters:** `self`
**Variables Used:** `response`
**Implementation:**
```python
def list_integrations(self) -> Dict[str, Any]:
    """List integrations"""
    response = self.session.get(f'{self.base_url}/api/integrations')
    response.raise_for_status()
    return response.json()
```

### Method: `test_integration`
**Logic & Purpose:**
```text
Test integration
```

**Parameters:** `self, name`
**Variables Used:** `response`
**Implementation:**
```python
def test_integration(self, name: str) -> Dict[str, Any]:
    """Test integration"""
    response = self.session.post(f'{self.base_url}/api/integrations/{name}/test')
    response.raise_for_status()
    return response.json()
```

### Method: `login`
**Logic & Purpose:**
```text
Login and get session token
```

**Parameters:** `self, username, password`
**Variables Used:** `response`
**Implementation:**
```python
def login(self, username: str, password: str) -> Dict[str, Any]:
    """Login and get session token"""
    response = self.session.post(f'{self.base_url}/api/auth/login', json={'username': username, 'password': password})
    response.raise_for_status()
    return response.json()
```

### Method: `create_api_key`
**Logic & Purpose:**
```text
Create API key
```

**Parameters:** `self, name, permissions`
**Variables Used:** `response`
**Implementation:**
```python
def create_api_key(self, name: str, permissions: list) -> Dict[str, Any]:
    """Create API key"""
    response = self.session.post(f'{self.base_url}/api/api-keys', json={'name': name, 'permissions': permissions})
    response.raise_for_status()
    return response.json()
```

### Method: `list_api_keys`
**Logic & Purpose:**
```text
List API keys
```

**Parameters:** `self`
**Variables Used:** `response`
**Implementation:**
```python
def list_api_keys(self) -> Dict[str, Any]:
    """List API keys"""
    response = self.session.get(f'{self.base_url}/api/api-keys')
    response.raise_for_status()
    return response.json()
```

### Method: `graphql_query`
**Logic & Purpose:**
```text
Execute GraphQL query
```

**Parameters:** `self, query, variables`
**Variables Used:** `response, payload`
**Implementation:**
```python
def graphql_query(self, query: str, variables: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
    """Execute GraphQL query"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    response = self.session.post(f'{self.base_url}/graphql', json=payload)
    response.raise_for_status()
    return response.json()
```

---

## Feature Function: `config_command`
**Logic & Purpose:**
```text
Configure CLI settings
```

**Parameters:** `args`
**Variables Used:** `config_dir, config_file, config`
**Implementation:**
```python
def config_command(args):
    """Configure CLI settings"""
    config_dir = Path.home() / '.claude_proxy'
    config_file = config_dir / 'config.json'
    if args.action == 'set':
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        config[args.key] = args.value
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f'✅ Set {args.key} = {args.value}')
    elif args.action == 'get':
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(config.get(args.key, ''))
        else:
            print('')
    elif args.action == 'show':
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(json.dumps(config, indent=2))
        else:
            print('No configuration found')
```

---

## Feature Function: `analytics_command`
**Logic & Purpose:**
```text
Query analytics data
```

**Parameters:** `client, args`
**Variables Used:** `writer, result, end_date, metric, start_date, metrics`
**Implementation:**
```python
def analytics_command(client, args):
    """Query analytics data"""
    try:
        start_date = args.start
        end_date = args.end
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if args.custom:
            metrics = args.metrics or 'tokens,cost,requests'
            result = client.get_custom_query(metrics=metrics, start_date=start_date, end_date=end_date, group_by=args.group_by)
        else:
            metric = args.metric or 'tokens'
            result = client.get_analytics(start_date, end_date, metric, args.group_by)
        print(json.dumps(result, indent=2))
        if args.export:
            if 'data' in result and result['data']:
                with open(args.export, 'w', newline='') as f:
                    if isinstance(result['data'], list) and result['data']:
                        writer = csv.DictWriter(f, fieldnames=result['data'][0].keys())
                        writer.writeheader()
                        writer.writerows(result['data'])
                print(f'📊 Exported to {args.export}')
    except Exception as e:
        print(f'❌ Error: {e}')
        sys.exit(1)
```

---

## Feature Function: `predictive_command`
**Logic & Purpose:**
```text
Get predictive analytics
```

**Parameters:** `client, args`
**Variables Used:** `metric, result, data`
**Implementation:**
```python
def predictive_command(client, args):
    """Get predictive analytics"""
    try:
        if args.action == 'forecast':
            result = client.get_predictions(args.days)
            print(json.dumps(result, indent=2))
        elif args.action == 'thresholds':
            metric = args.metric or 'cost'
            result = client.get_smart_thresholds(metric)
            print(json.dumps(result, indent=2))
        elif args.action == 'detect':
            if not args.data:
                print('❌ --data required for anomaly detection')
                return
            data = json.loads(args.data)
            result = client.detect_anomaly(data)
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `alerts_command`
**Logic & Purpose:**
```text
Manage alerts
```

**Parameters:** `client, args`
**Variables Used:** `condition, parts, result`
**Implementation:**
```python
def alerts_command(client, args):
    """Manage alerts"""
    try:
        if args.action == 'list':
            result = client.list_alerts()
            print(json.dumps(result, indent=2))
        elif args.action == 'create':
            condition = {'metric': 'cost', 'operator': '>', 'threshold': 100}
            if args.condition:
                parts = args.condition.split('>')
                if len(parts) == 2:
                    condition = {'metric': parts[0], 'operator': '>', 'threshold': float(parts[1])}
            result = client.create_alert(args.name, condition, args.priority)
            print(json.dumps(result, indent=2))
        elif args.action == 'history':
            result = client.get_alert_history(args.limit)
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `reports_command`
**Logic & Purpose:**
```text
Manage reports
```

**Parameters:** `client, args`
**Variables Used:** `result, data`
**Implementation:**
```python
def reports_command(client, args):
    """Manage reports"""
    try:
        if args.action == 'templates':
            result = client.list_templates()
            print(json.dumps(result, indent=2))
        elif args.action == 'generate':
            result = client.generate_report(args.template, args.start, args.end, args.format)
            print(json.dumps(result, indent=2))
            if result.get('data') and args.output:
                try:
                    import binascii
                    data = binascii.unhexlify(result['data'])
                    with open(args.output, 'wb') as f:
                        f.write(data)
                    print(f'📄 Report saved to {args.output}')
                except:
                    print('⚠️ Could not decode report data')
        elif args.action == 'schedule':
            result = client.get_scheduled_reports()
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `integrations_command`
**Logic & Purpose:**
```text
Manage integrations
```

**Parameters:** `client, args`
**Variables Used:** `result`
**Implementation:**
```python
def integrations_command(client, args):
    """Manage integrations"""
    try:
        if args.action == 'list':
            result = client.list_integrations()
            print(json.dumps(result, indent=2))
        elif args.action == 'test':
            result = client.test_integration(args.name)
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `auth_command`
**Logic & Purpose:**
```text
Authentication
```

**Parameters:** `client, args`
**Variables Used:** `permissions, result, config, config_dir, config_file`
**Implementation:**
```python
def auth_command(client, args):
    """Authentication"""
    try:
        if args.action == 'login':
            if args.api_key:
                config_dir = Path.home() / '.claude_proxy'
                config_file = config_dir / 'config.json'
                config_dir.mkdir(parents=True, exist_ok=True)
                config = {}
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                config['api_key'] = args.api_key
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                print('✅ API key saved to config')
            elif args.username and args.password:
                result = client.login(args.username, args.password)
                print(json.dumps(result, indent=2))
        elif args.action == 'keys':
            if args.create:
                permissions = ['analytics:view', 'alerts:view']
                result = client.create_api_key(args.create, permissions)
                print(json.dumps(result, indent=2))
            else:
                result = client.list_api_keys()
                print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `graphql_command`
**Logic & Purpose:**
```text
Execute GraphQL query
```

**Parameters:** `client, args`
**Variables Used:** `query, result`
**Implementation:**
```python
def graphql_command(client, args):
    """Execute GraphQL query"""
    try:
        query = args.query or '\n        query {\n            health\n            metrics(startDate: "2026-01-01", endDate: "2026-01-05", groupBy: "day") {\n                timestamp\n                tokens\n                cost\n                requests\n            }\n        }\n        '
        result = client.graphql_query(query)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f'❌ Error: {e}')
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main CLI entry point
```

**Parameters:** ``
**Variables Used:** `config_parser, args, parser, analytics_parser, api_key, subparsers, base_url, alerts_parser, auth_parser, config, reports_parser, integrations_parser, config_file, client, graphql_parser, predictive_parser`
**Implementation:**
```python
def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Claude Proxy CLI - Analytics and Monitoring', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="\nExamples:\n  claude-proxy analytics --start 2026-01-01 --end 2026-01-05\n  claude-proxy predictive forecast --days 7\n  claude-proxy alerts list\n  claude-proxy auth login --api-key cp_xxx\n  claude-proxy graphql --query '{ health }'\n        ")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    config_parser = subparsers.add_parser('config', help='Configure CLI')
    config_parser.add_argument('action', choices=['set', 'get', 'show'], help='Action')
    config_parser.add_argument('key', nargs='?', help='Config key')
    config_parser.add_argument('value', nargs='?', help='Config value')
    analytics_parser = subparsers.add_parser('analytics', help='Query analytics')
    analytics_parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    analytics_parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    analytics_parser.add_argument('--metric', help='Metric (tokens, cost, requests)')
    analytics_parser.add_argument('--group-by', default='day', choices=['hour', 'day', 'week'])
    analytics_parser.add_argument('--custom', action='store_true', help='Use custom query')
    analytics_parser.add_argument('--metrics', help='Metrics for custom query (comma-separated)')
    analytics_parser.add_argument('--export', help='Export to CSV file')
    predictive_parser = subparsers.add_parser('predictive', help='Predictive analytics')
    predictive_parser.add_argument('action', choices=['forecast', 'thresholds', 'detect'])
    predictive_parser.add_argument('--days', type=int, default=7, help='Days to forecast')
    predictive_parser.add_argument('--metric', help='Metric for thresholds')
    predictive_parser.add_argument('--data', help='JSON data for anomaly detection')
    alerts_parser = subparsers.add_parser('alerts', help='Manage alerts')
    alerts_parser.add_argument('action', choices=['list', 'create', 'history'])
    alerts_parser.add_argument('--name', help='Alert name')
    alerts_parser.add_argument('--condition', help='Condition (e.g., cost>100)')
    alerts_parser.add_argument('--priority', type=int, default=2, help='Priority 0-3')
    alerts_parser.add_argument('--limit', type=int, default=50, help='History limit')
    reports_parser = subparsers.add_parser('reports', help='Manage reports')
    reports_parser.add_argument('action', choices=['templates', 'generate', 'schedule'])
    reports_parser.add_argument('--template', help='Template ID')
    reports_parser.add_argument('--start', help='Start date')
    reports_parser.add_argument('--end', help='End date')
    reports_parser.add_argument('--format', default='excel', choices=['pdf', 'excel', 'csv'])
    reports_parser.add_argument('--output', help='Output file')
    integrations_parser = subparsers.add_parser('integrations', help='Manage integrations')
    integrations_parser.add_argument('action', choices=['list', 'test'])
    integrations_parser.add_argument('--name', help='Integration name')
    auth_parser = subparsers.add_parser('auth', help='Authentication')
    auth_parser.add_argument('action', choices=['login', 'keys'])
    auth_parser.add_argument('--username', help='Username')
    auth_parser.add_argument('--password', help='Password')
    auth_parser.add_argument('--api-key', help='API key')
    auth_parser.add_argument('--create', help='Create API key with name')
    graphql_parser = subparsers.add_parser('graphql', help='GraphQL queries')
    graphql_parser.add_argument('--query', help='GraphQL query string')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    config_file = Path.home() / '.claude_proxy' / 'config.json'
    config = {}
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    base_url = config.get('base_url', 'http://localhost:8082')
    api_key = config.get('api_key')
    client = ClaudeProxyClient(base_url, api_key)
    if args.command == 'config':
        config_command(args)
    elif args.command == 'analytics':
        analytics_command(client, args)
    elif args.command == 'predictive':
        predictive_command(client, args)
    elif args.command == 'alerts':
        alerts_command(client, args)
    elif args.command == 'reports':
        reports_command(client, args)
    elif args.command == 'integrations':
        integrations_command(client, args)
    elif args.command == 'auth':
        auth_command(client, args)
    elif args.command == 'graphql':
        graphql_command(client, args)
```

---


