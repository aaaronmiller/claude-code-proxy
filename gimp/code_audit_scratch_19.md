# File Audit: /home/cheta/code/claude-code-proxy/src/api/mcp_server.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/mcp_server.py`

**Module Overview**: 
```text
MCP Server for Claude Code Proxy Crosstalk System
Provides tools for LLM integration with model-to-model conversations.
```

## Global Presets & Variables
- `app` = `Server('claude-code-proxy-crosstalk')`

## Dependencies & Imports
asyncio, sys, os, typing.Any, typing.Dict, typing.List, typing.Optional, mcp.server.Server, mcp.types.Tool, mcp.types.TextContent, src.conversation.crosstalk.crosstalk_orchestrator, src.conversation.crosstalk.CrosstalkParadigm, src.core.config.config

## Feature Function: `handle_list_tools`
**Logic & Purpose:**
```text
List all available crosstalk tools.
```

**Parameters:** ``
**Implementation:**
```python
@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List all available crosstalk tools.
    """
    return [Tool(name='crosstalk_setup', description='Setup a new model-to-model crosstalk conversation session', inputSchema={'type': 'object', 'properties': {'models': {'type': 'array', 'items': {'type': 'string'}, 'description': "List of models to use (e.g., ['big', 'small'])", 'example': ['big', 'small']}, 'system_prompts': {'type': 'object', 'description': 'System prompts for each model', 'example': {'big': 'You are Alice', 'small': 'You are Bob'}, 'additionalProperties': {'type': 'string'}}, 'paradigm': {'type': 'string', 'enum': ['memory', 'report', 'relay', 'debate'], 'description': 'Communication paradigm', 'default': 'relay', 'example': 'debate'}, 'iterations': {'type': 'integer', 'description': 'Number of conversation exchanges', 'minimum': 1, 'maximum': 100, 'default': 20, 'example': 20}, 'topic': {'type': 'string', 'description': 'Initial topic or message', 'example': 'hery whats up'}}, 'required': ['models']}), Tool(name='crosstalk_run', description='Execute a configured crosstalk session and return the conversation', inputSchema={'type': 'object', 'properties': {'session_id': {'type': 'string', 'description': 'Session ID from crosstalk_setup', 'example': '550e8400-e29b-41d4-a716-446655440000'}}, 'required': ['session_id']}), Tool(name='crosstalk_status', description='Get the status of a crosstalk session', inputSchema={'type': 'object', 'properties': {'session_id': {'type': 'string', 'description': 'Session ID to check', 'example': '550e8400-e29b-41d4-a716-446655440000'}}, 'required': ['session_id']}), Tool(name='crosstalk_list', description='List all active crosstalk sessions', inputSchema={'type': 'object', 'properties': {}}), Tool(name='crosstalk_delete', description='Delete a completed or errored crosstalk session', inputSchema={'type': 'object', 'properties': {'session_id': {'type': 'string', 'description': 'Session ID to delete', 'example': '550e8400-e29b-41d4-a716-446655440000'}}, 'required': ['session_id']}), Tool(name='load_system_prompt', description='Load a custom system prompt from file for a specific model', inputSchema={'type': 'object', 'properties': {'model': {'type': 'string', 'enum': ['big', 'middle', 'small'], 'description': 'Model to configure', 'example': 'big'}, 'prompt_file': {'type': 'string', 'description': 'Path to system prompt file', 'example': 'prompts/alice.txt'}, 'enable': {'type': 'boolean', 'description': 'Enable custom system prompt for this model', 'default': True, 'example': True}}, 'required': ['model', 'prompt_file']}), Tool(name='crosstalk_health', description='Check if the crosstalk system is healthy and ready', inputSchema={'type': 'object', 'properties': {}}), Tool(name='crosstalk_run_from_config', description='Run a complete crosstalk session from a full JSON configuration. Supports all advanced features: topologies, jinja templates, stop conditions, named prompts.', inputSchema={'type': 'object', 'properties': {'config': {'type': 'object', 'description': 'Full crosstalk configuration matching schema.json format. See configs/crosstalk/schema.json for complete schema.', 'properties': {'name': {'type': 'string'}, 'models': {'type': 'array', 'items': {'type': 'object', 'properties': {'model_id': {'type': 'string'}, 'system_prompt_file': {'type': 'string'}, 'system_prompt_inline': {'type': 'string'}, 'jinja_template': {'type': 'string'}, 'temperature': {'type': 'number'}, 'max_tokens': {'type': 'integer'}}, 'required': ['model_id']}}, 'paradigm': {'type': 'string', 'enum': ['relay', 'memory', 'debate', 'report']}, 'rounds': {'type': 'integer'}, 'initial_prompt': {'type': 'string'}, 'topology': {'type': 'object'}, 'stop_conditions': {'type': 'object'}, 'infinite': {'type': 'boolean'}}, 'required': ['models']}}, 'required': ['config']}), Tool(name='list_prompts', description='List all available system prompts from the prompts directory', inputSchema={'type': 'object', 'properties': {}}), Tool(name='list_templates', description='List all available Jinja templates from the templates directory', inputSchema={'type': 'object', 'properties': {}}), Tool(name='get_prompt', description='Get the content of a specific system prompt by name', inputSchema={'type': 'object', 'properties': {'name': {'type': 'string', 'description': 'Name of the prompt (without .md extension)', 'example': 'backrooms-explorer'}}, 'required': ['name']})]
```

---

## Feature Function: `handle_call_tool`
**Logic & Purpose:**
```text
Handle tool execution requests.
```

**Parameters:** `name, arguments`
**Variables Used:** `error_msg`
**Implementation:**
```python
@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle tool execution requests.
    """
    try:
        if name == 'crosstalk_setup':
            return await _handle_crosstalk_setup(arguments)
        elif name == 'crosstalk_run':
            return await _handle_crosstalk_run(arguments)
        elif name == 'crosstalk_status':
            return await _handle_crosstalk_status(arguments)
        elif name == 'crosstalk_list':
            return await _handle_crosstalk_list(arguments)
        elif name == 'crosstalk_delete':
            return await _handle_crosstalk_delete(arguments)
        elif name == 'load_system_prompt':
            return await _handle_load_system_prompt(arguments)
        elif name == 'crosstalk_health':
            return await _handle_crosstalk_health(arguments)
        elif name == 'crosstalk_run_from_config':
            return await _handle_crosstalk_run_from_config(arguments)
        elif name == 'list_prompts':
            return await _handle_list_prompts(arguments)
        elif name == 'list_templates':
            return await _handle_list_templates(arguments)
        elif name == 'get_prompt':
            return await _handle_get_prompt(arguments)
        else:
            return [TextContent(type='text', text=f'❌ Unknown tool: {name}')]
    except Exception as e:
        import traceback
        error_msg = f'❌ Error executing {name}: {str(e)}\n\n{traceback.format_exc()}'
        return [TextContent(type='text', text=error_msg)]
```

---

## Feature Function: `_handle_crosstalk_setup`
**Logic & Purpose:**
```text
Handle crosstalk setup.
```

**Parameters:** `arguments`
**Variables Used:** `paradigm, iterations, models, response, system_prompts, topic, session_id`
**Implementation:**
```python
async def _handle_crosstalk_setup(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk setup."""
    models = arguments.get('models', [])
    if not models:
        return [TextContent(type='text', text='❌ Error: models parameter is required')]
    system_prompts = arguments.get('system_prompts')
    paradigm = arguments.get('paradigm', 'relay')
    iterations = arguments.get('iterations', 20)
    topic = arguments.get('topic', "Hello, let's talk")
    if paradigm not in ['memory', 'report', 'relay', 'debate']:
        return [TextContent(type='text', text=f'❌ Invalid paradigm: {paradigm}')]
    session_id = await crosstalk_orchestrator.setup_crosstalk(models=models, system_prompts=system_prompts, paradigm=paradigm, iterations=iterations, topic=topic)
    response = f"✅ Crosstalk session configured successfully!\n\nSession ID: {session_id}\nModels: {', '.join(models)}\nParadigm: {paradigm.upper()}\nIterations: {iterations}\nTopic: {topic}\n\nTo execute this session, use the crosstalk_run tool with session_id: {session_id}"
    return [TextContent(type='text', text=response)]
```

---

## Feature Function: `_handle_crosstalk_run`
**Logic & Purpose:**
```text
Handle crosstalk execution.
```

**Parameters:** `arguments`
**Variables Used:** `msg_text, session_id, start_time, output, conversation, duration`
**Implementation:**
```python
async def _handle_crosstalk_run(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk execution."""
    session_id = arguments.get('session_id')
    if not session_id:
        return [TextContent(type='text', text='❌ Error: session_id parameter is required')]
    import time
    start_time = time.time()
    conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)
    duration = time.time() - start_time
    output = [TextContent(type='text', text='✅ Crosstalk completed!\n')]
    output.append(TextContent(type='text', text=f'Duration: {duration:.2f} seconds\nTotal messages: {len(conversation)}\n'))
    output.append(TextContent(type='text', text='=' * 70))
    output.append(TextContent(type='text', text='CONVERSATION TRANSCRIPT'))
    output.append(TextContent(type='text', text='=' * 70))
    for i, msg in enumerate(conversation, 1):
        msg_text = f"\n[{i}] {msg['speaker'].upper()} → {msg['listener'].upper()} (iter {msg['iteration']})"
        if msg.get('confidence'):
            msg_text += f"\nConfidence: {msg['confidence']:.2f}"
        msg_text += f"\n{msg['content']}"
        output.append(TextContent(type='text', text=msg_text))
    return output
```

---

## Feature Function: `_handle_crosstalk_status`
**Logic & Purpose:**
```text
Handle crosstalk status check.
```

**Parameters:** `arguments`
**Variables Used:** `status, response, session_id`
**Implementation:**
```python
async def _handle_crosstalk_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle crosstalk status check."""
    session_id = arguments.get('session_id')
    if not session_id:
        return [TextContent(type='text', text='❌ Error: session_id parameter is required')]
    status = crosstalk_orchestrator.get_session_status(session_id)
    if 'error' in status:
        return [TextContent(type='text', text=f"❌ {status['error']}")]
    response = f"📊 Crosstalk Session Status\n\nSession ID: {status['session_id']}\nStatus: {status['status'].upper()}\nModels: {', '.join(status['models'])}\nParadigm: {status['paradigm'].upper()}\nIterations: {status['iterations']}\nCurrent Iteration: {status['current_iteration']}\nMessages: {status['message_count']}\nCreated: {status['created_at']}"
    return [TextContent(type='text', text=response)]
```

---

## Feature Function: `_handle_crosstalk_list`
**Logic & Purpose:**
```text
Handle listing all sessions.
```

**Parameters:** `arguments`
**Variables Used:** `status, sessions, response`
**Implementation:**
```python
async def _handle_crosstalk_list(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle listing all sessions."""
    sessions = []
    for sid in crosstalk_orchestrator.active_sessions:
        status = crosstalk_orchestrator.get_session_status(sid)
        sessions.append(status)
    if not sessions:
        return [TextContent(type='text', text='No active crosstalk sessions')]
    response = [TextContent(type='text', text=f'📋 Active Crosstalk Sessions ({len(sessions)})\n')]
    for status in sessions:
        response.append(TextContent(type='text', text=f"\nSession: {status['session_id'][:8]}...\nStatus: {status['status'].upper()}\nModels: {', '.join(status['models'])}\nParadigm: {status['paradigm'].upper()}\nMessages: {status['message_count']}\n"))
    return response
```

---

## Feature Function: `_handle_crosstalk_delete`
**Logic & Purpose:**
```text
Handle session deletion.
```

**Parameters:** `arguments`
**Variables Used:** `success, session_id`
**Implementation:**
```python
async def _handle_crosstalk_delete(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle session deletion."""
    session_id = arguments.get('session_id')
    if not session_id:
        return [TextContent(type='text', text='❌ Error: session_id parameter is required')]
    success = crosstalk_orchestrator.delete_session(session_id)
    if success:
        return [TextContent(type='text', text=f'✅ Session {session_id} deleted successfully')]
    else:
        return [TextContent(type='text', text=f'❌ Session {session_id} not found')]
```

---

## Feature Function: `_handle_load_system_prompt`
**Logic & Purpose:**
```text
Handle loading system prompt.
```

**Parameters:** `arguments`
**Variables Used:** `prompt, env_key, enable, prompt_file, enable_key, model`
**Implementation:**
```python
async def _handle_load_system_prompt(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle loading system prompt."""
    model = arguments.get('model')
    prompt_file = arguments.get('prompt_file')
    enable = arguments.get('enable', True)
    if not model or not prompt_file:
        return [TextContent(type='text', text='❌ Error: model and prompt_file are required')]
    if model not in ['big', 'middle', 'small']:
        return [TextContent(type='text', text="❌ Error: model must be 'big', 'middle', or 'small'")]
    try:
        with open(prompt_file, 'r') as f:
            prompt = f.read().strip()
        env_key = f'{model.upper()}_SYSTEM_PROMPT_FILE'
        os.environ[env_key] = prompt_file
        enable_key = f'ENABLE_CUSTOM_{model.upper()}_PROMPT'
        os.environ[enable_key] = 'true' if enable else 'false'
        return [TextContent(type='text', text=f'✅ System prompt loaded for {model.upper()} model\n\nFile: {prompt_file}\nLength: {len(prompt)} characters\nEnabled: {enable}\n\nThe system will now use this custom system prompt for the {model.upper()} model.\nNote: Changes will take effect when the proxy server restarts.')]
    except FileNotFoundError:
        return [TextContent(type='text', text=f'❌ File not found: {prompt_file}')]
    except Exception as e:
        return [TextContent(type='text', text=f'❌ Error loading prompt: {str(e)}')]
```

---

## Feature Function: `_handle_crosstalk_health`
**Logic & Purpose:**
```text
Handle health check.
```

**Parameters:** `arguments`
**Variables Used:** `orchestrator_status, response, active_count`
**Implementation:**
```python
async def _handle_crosstalk_health(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle health check."""
    try:
        orchestrator_status = '✅ Healthy' if crosstalk_orchestrator else '❌ Not initialized'
        active_count = len(crosstalk_orchestrator.active_sessions)
        response = f"🏥 Crosstalk System Health Check\n\nOrchestrator: {orchestrator_status}\nActive Sessions: {active_count}\n\nConfiguration:\n  BIG Model: {config.big_model}\n  MIDDLE Model: {config.middle_model}\n  SMALL Model: {config.small_model}\n\nStatus: {('✅ All systems operational' if orchestrator_status == '✅ Healthy' else '❌ Issues detected')}"
        return [TextContent(type='text', text=response)]
    except Exception as e:
        return [TextContent(type='text', text=f'❌ Health check failed: {str(e)}')]
```

---

## Feature Function: `_handle_crosstalk_run_from_config`
**Logic & Purpose:**
```text
Handle running a crosstalk session from a full JSON configuration.
```

**Parameters:** `arguments`
**Variables Used:** `error, result, config_data, prompt_content, model_id, output_file, start_time, response, content, transcript, role, duration`
**Implementation:**
```python
async def _handle_crosstalk_run_from_config(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle running a crosstalk session from a full JSON configuration."""
    config_data = arguments.get('config')
    if not config_data:
        return [TextContent(type='text', text='❌ Error: config parameter is required')]
    try:
        from src.cli.crosstalk_runner import run_from_config, get_prompt_content
        for model in config_data.get('models', []):
            if model.get('system_prompt_file') and (not model.get('system_prompt_inline')):
                prompt_content = get_prompt_content(model['system_prompt_file'])
                if prompt_content:
                    model['system_prompt_inline'] = prompt_content
        import time
        start_time = time.time()
        result = await run_from_config(config_data)
        duration = time.time() - start_time
        if result.get('status') == 'completed':
            transcript = result.get('transcript', [])
            output_file = result.get('output_file', '')
            response = f"✅ Crosstalk session completed!\n\nDuration: {duration:.2f} seconds\nMessages: {len(transcript)}\nOutput File: {output_file}\n\n{'=' * 60}\nCONVERSATION TRANSCRIPT\n{'=' * 60}\n"
            for i, msg in enumerate(transcript):
                role = msg.get('role', 'unknown')
                model_id = msg.get('model_id', 'unknown')
                content = msg.get('content', '')[:500]
                response += f'\n[{i + 1}] {role.upper()} ({model_id})\n{content}\n'
            return [TextContent(type='text', text=response)]
        else:
            error = result.get('error', 'Unknown error')
            return [TextContent(type='text', text=f'❌ Session failed: {error}')]
    except Exception as e:
        import traceback
        return [TextContent(type='text', text=f'❌ Error running session: {str(e)}\n\n{traceback.format_exc()}')]
```

---

## Feature Function: `_handle_list_prompts`
**Logic & Purpose:**
```text
Handle listing available prompts.
```

**Parameters:** `arguments`
**Variables Used:** `temp, response, prompts, desc, category, name`
**Implementation:**
```python
async def _handle_list_prompts(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle listing available prompts."""
    try:
        from src.cli.crosstalk_runner import list_available_prompts
        prompts = list_available_prompts()
        if not prompts:
            return [TextContent(type='text', text='No prompts found in manifest.yaml')]
        response = '📝 Available System Prompts\n\n'
        for p in prompts:
            name = p.get('name', 'unknown')
            desc = p.get('description', 'No description')
            category = p.get('category', '')
            temp = p.get('recommended_temp', '')
            response += f'• **{name}**'
            if category:
                response += f' [{category}]'
            response += f'\n  {desc}'
            if temp:
                response += f'\n  Recommended temp: {temp}'
            response += '\n\n'
        return [TextContent(type='text', text=response)]
    except Exception as e:
        return [TextContent(type='text', text=f'❌ Error listing prompts: {str(e)}')]
```

---

## Feature Function: `_handle_list_templates`
**Logic & Purpose:**
```text
Handle listing available templates.
```

**Parameters:** `arguments`
**Variables Used:** `variables, templates, response, desc, name`
**Implementation:**
```python
async def _handle_list_templates(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle listing available templates."""
    try:
        from src.cli.crosstalk_runner import list_available_templates
        templates = list_available_templates()
        if not templates:
            return [TextContent(type='text', text='No templates found in manifest.yaml')]
        response = '📄 Available Jinja Templates\n\n'
        for t in templates:
            name = t.get('name', 'unknown')
            desc = t.get('description', 'No description')
            variables = t.get('variables', [])
            response += f'• **{name}**\n  {desc}'
            if variables:
                response += f"\n  Variables: {', '.join(variables)}"
            response += '\n\n'
        return [TextContent(type='text', text=response)]
    except Exception as e:
        return [TextContent(type='text', text=f'❌ Error listing templates: {str(e)}')]
```

---

## Feature Function: `_handle_get_prompt`
**Logic & Purpose:**
```text
Handle getting a specific prompt's content.
```

**Parameters:** `arguments`
**Variables Used:** `response, name, content`
**Implementation:**
```python
async def _handle_get_prompt(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle getting a specific prompt's content."""
    name = arguments.get('name')
    if not name:
        return [TextContent(type='text', text='❌ Error: name parameter is required')]
    try:
        from src.cli.crosstalk_runner import get_prompt_content
        content = get_prompt_content(name)
        if content:
            response = f"📝 Prompt: {name}\n\n{'=' * 60}\n{content}\n{'=' * 60}"
            return [TextContent(type='text', text=response)]
        else:
            return [TextContent(type='text', text=f'❌ Prompt not found: {name}')]
    except Exception as e:
        return [TextContent(type='text', text=f'❌ Error getting prompt: {str(e)}')]
```

---


Error parsing /home/cheta/code/claude-code-proxy/src/static/js/app.js: invalid character '═' (U+2550) (<unknown>, line 3)

# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/io.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/io.py`

**Module Overview**: 
```text
Atomic file I/O utilities.
Provides crash-safe writes and corruption recovery.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
json, logging, os, tempfile, datetime.datetime, pathlib.Path, datetime.timezone, typing.Any, typing.Optional

## Feature Function: `atomic_json_write`
**Logic & Purpose:**
```text
Write data to JSON file atomically (write to temp, then rename).

Args:
    data: Serializable data to write
    target_path: Destination file path
```

**Parameters:** `data, target_path`
**Variables Used:** `target_path, tmp_path`
**Implementation:**
```python
def atomic_json_write(data: Any, target_path: str | Path) -> None:
    """
    Write data to JSON file atomically (write to temp, then rename).

    Args:
        data: Serializable data to write
        target_path: Destination file path
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target_path.parent, suffix='.tmp', delete=False, encoding='utf-8') as tmp:
        tmp_path = Path(tmp.name)
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
    tmp_path.replace(target_path)
```

---

## Feature Function: `load_json`
**Logic & Purpose:**
```text
Load and deserialize JSON file.

Args:
    file_path: Path to JSON file

Returns:
    Deserialized data

Raises:
    FileNotFoundError: If file doesn't exist
    json.JSONDecodeError: If file contains invalid JSON
```

**Parameters:** `file_path`
**Implementation:**
```python
def load_json(file_path: str | Path) -> Any:
    """
    Load and deserialize JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Deserialized data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

---

## Feature Function: `backup_corrupted_file`
**Logic & Purpose:**
```text
Backup corrupted file with timestamp suffix.

Args:
    corrupted_path: Path to corrupted file

Returns:
    Path to backup file if created, None otherwise
```

**Parameters:** `corrupted_path`
**Variables Used:** `backup_path, timestamp, path`
**Implementation:**
```python
def backup_corrupted_file(corrupted_path: str | Path) -> Optional[str]:
    """
    Backup corrupted file with timestamp suffix.

    Args:
        corrupted_path: Path to corrupted file

    Returns:
        Path to backup file if created, None otherwise
    """
    path = Path(corrupted_path)
    if not path.exists():
        return None
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_path = path.with_suffix(f'.corrupt.{timestamp}{path.suffix}')
    try:
        path.rename(backup_path)
        logger.warning(f'Backed up corrupted file to: {backup_path}')
        return str(backup_path)
    except Exception as e:
        logger.error(f'Failed to backup corrupted file: {e}')
        return None
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/scraper_web.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/scraper_web.py`

**Module Overview**: 
```text
Deep Web Scraper: Conditional scraping for OpenRouter model pages.
Implements: browser management, stealth configuration, page fetching, benchmark extraction.

Uses: camoufox (stealth browser) and crawl4AI (LLM-powered extraction).
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
asyncio, logging, random, time, typing.Optional, typing.Dict, typing.Any, typing.List, pathlib.Path, camoufox.sync_api.Camoufox, crawl4ai.AsyncWebCrawler, crawl4ai.extraction_strategy.LLMExtractionStrategy, pydantic.BaseModel, pydantic.Field, openrouter_model_scout.models.Performance, openrouter_model_scout.models.Benchmarks, openrouter_model_scout.models.IntelligenceMetrics, openrouter_model_scout.models.CodingMetrics, openrouter_model_scout.models.AgenticMetrics, openrouter_model_scout.exceptions.ScraperError

## Feature Class: `ScrapeResult`
**Description:**
```text
Result of scraping a single model page.
```

---

## Feature Class: `ScraperManager`
**Description:**
```text
Manages the deep scraper for OpenRouter model pages.

Handles browser lifecycle, rate limiting, and extraction.
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize scraper manager.

Args:
    stealth_mode: Enable stealth features (random delays, user-agent rotation)
    max_concurrent: Maximum concurrent browser instances (keep at 1 for stealth)
    delay_range: Min/max seconds between page loads (for rate limiting)
```

**Parameters:** `self, stealth_mode, max_concurrent, delay_range`
**Implementation:**
```python
def __init__(self, stealth_mode: bool=True, max_concurrent: int=1, delay_range: tuple[float, float]=(2.0, 5.0)):
    """
        Initialize scraper manager.

        Args:
            stealth_mode: Enable stealth features (random delays, user-agent rotation)
            max_concurrent: Maximum concurrent browser instances (keep at 1 for stealth)
            delay_range: Min/max seconds between page loads (for rate limiting)
        """
    self.stealth_mode = stealth_mode
    self.max_concurrent = max_concurrent
    self.delay_range = delay_range
    self._browser: Optional[Camoufox] = None
    self._semaphore = asyncio.Semaphore(max_concurrent)
```

### Method: `__enter__`
**Logic & Purpose:**
```text
Context manager entry: start browser.
```

**Parameters:** `self`
**Implementation:**
```python
def __enter__(self):
    """Context manager entry: start browser."""
    self.start()
    return self
```

### Method: `__exit__`
**Logic & Purpose:**
```text
Context manager exit: close browser.
```

**Parameters:** `self, exc_type, exc_val, exc_tb`
**Implementation:**
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit: close browser."""
    self.stop()
```

### Method: `start`
**Logic & Purpose:**
```text
Initialize the browser.
```

**Parameters:** `self`
**Implementation:**
```python
def start(self) -> None:
    """Initialize the browser."""
    if self._browser is None:
        logger.info('Starting Camoufox browser...')
        self._browser = Camoufox(headless=True)
        self._browser.__enter__()
        logger.info('Browser started successfully')
```

### Method: `stop`
**Logic & Purpose:**
```text
Close the browser.
```

**Parameters:** `self`
**Implementation:**
```python
def stop(self) -> None:
    """Close the browser."""
    if self._browser is not None:
        logger.info('Stopping Camoufox browser...')
        try:
            self._browser.__exit__(None, None, None)
        except Exception as e:
            logger.warning(f'Error closing browser: {e}')
        finally:
            self._browser = None
```

### Method: `fetch_model_page`
**Logic & Purpose:**
```text
Fetch and extract data from a model's page.

Args:
    model_id: Model identifier (e.g., "openai/gpt-4")
    base_url: Base OpenRouter URL

Returns:
    ScrapeResult with extracted data

Raises:
    ScraperError: If extraction fails
```

**Parameters:** `self, model_id, base_url`
**Variables Used:** `url, delay, result`
**Implementation:**
```python
async def fetch_model_page(self, model_id: str, base_url: str='https://openrouter.ai') -> ScrapeResult:
    """
        Fetch and extract data from a model's page.

        Args:
            model_id: Model identifier (e.g., "openai/gpt-4")
            base_url: Base OpenRouter URL

        Returns:
            ScrapeResult with extracted data

        Raises:
            ScraperError: If extraction fails
        """
    async with self._semaphore:
        if self.stealth_mode:
            delay = random.uniform(*self.delay_range)
            await asyncio.sleep(delay)
        url = f"{base_url.rstrip('/')}/{model_id}"
        logger.debug(f'Fetching {url}')
        try:
            result = await self._crawl_with_crawl4ai(url)
            return ScrapeResult(model_id=model_id, **result)
        except Exception as e:
            logger.error(f'Failed to scrape {model_id}: {e}')
            raise ScraperError(f'Scrape failed for {model_id}: {e}') from e
```

### Method: `_crawl_with_crawl4ai`
**Logic & Purpose:**
```text
Use crawl4AI to extract structured data from page.

Args:
    url: Target URL

Returns:
    Dictionary with extracted fields
```

**Parameters:** `self, url`
**Variables Used:** `extraction_strategy, result, data`
**Implementation:**
```python
async def _crawl_with_crawl4ai(self, url: str) -> Dict[str, Any]:
    """
        Use crawl4AI to extract structured data from page.

        Args:
            url: Target URL

        Returns:
            Dictionary with extracted fields
        """
    extraction_strategy = LLMExtractionStrategy(llm_provider='openai', llm_model='gpt-4o-mini', api_key=None, temperature=0.0, max_tokens=2000)
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url, extraction_strategy=extraction_strategy, bypass_cache=True)
        if not result.extracted_content:
            raise ScraperError('No content extracted')
        try:
            import json
            data = json.loads(result.extracted_content)
            return self._normalize_extracted_data(data)
        except json.JSONDecodeError as e:
            logger.warning(f'Failed to parse extracted JSON: {e}')
            return {}
```

### Method: `_normalize_extracted_data`
**Logic & Purpose:**
```text
Normalize raw extraction results into expected fields.

The LLM extraction might return various field names; map to our schema.
```

**Parameters:** `self, raw`
**Variables Used:** `bench_fields, perf_fields, normalized`
**Implementation:**
```python
def _normalize_extracted_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
    """
        Normalize raw extraction results into expected fields.

        The LLM extraction might return various field names; map to our schema.
        """
    normalized = {}
    bench_fields = ['benchmarks', 'benchmark', 'scores', 'metrics']
    for field in bench_fields:
        if field in raw and isinstance(raw[field], dict):
            normalized['benchmarks'] = raw[field]
            break
    perf_fields = ['performance', 'perf', 'throughput', 'latency']
    for field in perf_fields:
        if field in raw and isinstance(raw[field], dict):
            normalized['performance'] = raw[field]
            break
    if 'description_short' in raw:
        normalized['description_short'] = raw['description_short']
    if 'description_full' in raw:
        normalized['description_full'] = raw['description_full']
    if 'release_date' in raw:
        normalized['release_date'] = raw['release_date']
    if 'parameter_size' in raw:
        normalized['parameter_size'] = raw['parameter_size']
    if 'quantization' in raw:
        normalized['quantization'] = raw['quantization']
    return normalized
```

---

## Feature Function: `estimate_scrape_cost`
**Logic & Purpose:**
```text
Estimate token usage for a single scrape operation.

Args:
    model_id: Model being scraped
    approx_tokens: Approximate tokens used by crawl4AI LLM extraction

Returns:
    Dict with prompt_tokens, completion_tokens
```

**Parameters:** `model_id, approx_tokens`
**Variables Used:** `prompt_tokens, completion_tokens`
**Implementation:**
```python
def estimate_scrape_cost(model_id: str, approx_tokens: int=500) -> Dict[str, int]:
    """
    Estimate token usage for a single scrape operation.

    Args:
        model_id: Model being scraped
        approx_tokens: Approximate tokens used by crawl4AI LLM extraction

    Returns:
        Dict with prompt_tokens, completion_tokens
    """
    prompt_tokens = 8000
    completion_tokens = approx_tokens
    return {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': prompt_tokens + completion_tokens}
```

---

## Feature Function: `parse_benchmark_scores`
**Logic & Purpose:**
```text
Parse benchmark data from scraped content into structured Benchmarks object.

Args:
    data: Raw scraped benchmark dict

Returns:
    Benchmarks object (may have missing fields if data incomplete)
```

**Parameters:** `data`
**Variables Used:** `coding, intel, bench_data, agentic`
**Implementation:**
```python
def parse_benchmark_scores(data: Dict[str, Any]) -> Benchmarks:
    """
    Parse benchmark data from scraped content into structured Benchmarks object.

    Args:
        data: Raw scraped benchmark dict

    Returns:
        Benchmarks object (may have missing fields if data incomplete)
    """
    bench_data = {}
    if 'intelligence' in data:
        intel = data['intelligence']
        if isinstance(intel, dict):
            bench_data['intelligence'] = IntelligenceMetrics(score=float(intel.get('score', 0)), percentile=float(intel.get('percentile', 0)))
    if 'coding' in data:
        coding = data['coding']
        if isinstance(coding, dict):
            bench_data['coding'] = CodingMetrics(score=float(coding.get('score', 0)), percentile=float(coding.get('percentile', 0)))
    if 'agentic' in data:
        agentic = data['agentic']
        if isinstance(agentic, dict):
            bench_data['agentic'] = AgenticMetrics(score=float(agentic.get('score', 0)), percentile=float(agentic.get('percentile', 0)))
    return Benchmarks(**bench_data)
```

---

## Feature Function: `parse_performance_metrics`
**Logic & Purpose:**
```text
Parse performance metrics from scraped data.

Args:
    data: Raw scraped performance dict

Returns:
    Performance object or None if no data
```

**Parameters:** `data`
**Variables Used:** `perf_kwargs, perf_fields`
**Implementation:**
```python
def parse_performance_metrics(data: Dict[str, Any]) -> Optional[Performance]:
    """
    Parse performance metrics from scraped data.

    Args:
        data: Raw scraped performance dict

    Returns:
        Performance object or None if no data
    """
    perf_fields = ['throughput_tps', 'latency_seconds', 'e2e_latency_seconds', 'tool_error_rate', 'uptime_percent']
    if not any((field in data for field in perf_fields)):
        return None
    perf_kwargs = {}
    for field in perf_fields:
        if field in data:
            try:
                perf_kwargs[field] = float(data[field])
            except (ValueError, TypeError):
                pass
    return Performance(**perf_kwargs) if perf_kwargs else None
```

---

## Feature Function: `process_model_queue`
**Logic & Purpose:**
```text
Process a queue of model IDs, scraping each with retry logic.
```

**Parameters:** `model_ids, manager, max_retries, initial_backoff`
**Variables Used:** `backoff, result, results, jitter, wait_time, retries`
**Implementation:**
```python
async def process_model_queue(model_ids: List[str], manager: ScraperManager, max_retries: int=3, initial_backoff: float=1.0) -> Dict[str, ScrapeResult]:
    """
    Process a queue of model IDs, scraping each with retry logic.
    """
    results = {}
    for model_id in model_ids:
        retries = 0
        backoff = initial_backoff
        while retries <= max_retries:
            try:
                logger.info(f'Scraping model {model_id} (attempt {retries + 1}/{max_retries + 1})')
                result = await manager.fetch_model_page(model_id)
                results[model_id] = result
                logger.info(f'Successfully scraped {model_id}')
                break
            except ScraperError as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f'Failed to scrape {model_id} after {max_retries} retries: {e}')
                    break
                else:
                    jitter = random.uniform(0, 0.1 * backoff)
                    wait_time = backoff + jitter
                    logger.warning(f'Scrape failed for {model_id}, retrying in {wait_time:.2f}s...')
                    await asyncio.sleep(wait_time)
                    backoff *= 2
        if model_id != model_ids[-1]:
            await asyncio.sleep(0.5)
    return results
```

---

## Feature Function: `convert_scrape_results_to_enrichment`
**Logic & Purpose:**
```text
Convert ScrapeResult objects into enrichment dict for normalizer.
```

**Parameters:** `results`
**Variables Used:** `enrichment, data`
**Implementation:**
```python
def convert_scrape_results_to_enrichment(results: Dict[str, ScrapeResult]) -> Dict[str, Dict[str, Any]]:
    """
    Convert ScrapeResult objects into enrichment dict for normalizer.
    """
    enrichment = {}
    for model_id, result in results.items():
        data = {}
        if result.benchmarks:
            data['benchmarks'] = result.benchmarks
        if result.performance:
            data['performance'] = result.performance
        if result.description_short:
            data['description_short'] = result.description_short
        if result.description_full:
            data['description_full'] = result.description_full
        if result.release_date:
            data['release_date'] = result.release_date
        if result.parameter_size:
            data['parameter_size'] = result.parameter_size
        if result.quantization:
            data['quantization'] = result.quantization
        if data:
            enrichment[model_id] = data
    return enrichment
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/logger.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/logger.py`

**Module Overview**: 
```text
Logging configuration for the scout.
Implements: setup_logger() with levels, structured formatting, file output
```

## Dependencies & Imports
logging, sys, pathlib.Path, typing.Optional

## Feature Function: `setup_logger`
**Logic & Purpose:**
```text
Configure and return a logger with console and optional file handler.

Args:
    name: Logger name
    level: Logging level (e.g., logging.DEBUG, logging.INFO)
    log_file: Optional file path for file logging
    fmt: Optional custom format string

Returns:
    Configured Logger instance
```

**Parameters:** `name, level, log_file, fmt`
**Variables Used:** `file_handler, console_handler, log_path, logger, fmt, formatter`
**Implementation:**
```python
def setup_logger(name: str='openrouter_scout', level: int=logging.INFO, log_file: Optional[str | Path]=None, fmt: Optional[str]=None) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handler.

    Args:
        name: Logger name
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional file path for file logging
        fmt: Optional custom format string

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger
    if fmt is None:
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/fetcher_api.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/fetcher_api.py`

**Module Overview**: 
```text
Fast API fetcher for OpenRouter models endpoint.
Implements: fetch_models(), parse_response(), retry logic
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
logging, asyncio, typing.List, typing.Dict, typing.Any, typing.Optional, httpx, pydantic.ValidationError, openrouter_model_scout.config.Config, openrouter_model_scout.exceptions.APIError, openrouter_model_scout.models.Model, openrouter_model_scout.logger.setup_logger

## Feature Function: `fetch_models`
**Logic & Purpose:**
```text
Fetch model list from OpenRouter API.

Args:
    config: Configuration object with API key
    client: Optional httpx client (for testing/mocking)

Returns:
    List of Model objects

Raises:
    APIError: If API request fails after retries
```

**Parameters:** `config, client`
**Variables Used:** `models_list, cleaned, data, filtered_models, headers, filtered, own_client, pattern, pricing, wait, prompt_val, models, response, completion_val, model, client, endpoint`
**Implementation:**
```python
async def fetch_models(config: Config, client: Optional[httpx.AsyncClient]=None) -> List[Model]:
    """
    Fetch model list from OpenRouter API.

    Args:
        config: Configuration object with API key
        client: Optional httpx client (for testing/mocking)

    Returns:
        List of Model objects

    Raises:
        APIError: If API request fails after retries
    """
    endpoint = 'https://openrouter.ai/api/v1/models'
    headers = {'Authorization': f'Bearer {config.openrouter_api_key}', 'Content-Type': 'application/json'}
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(timeout=30.0)
    try:
        for attempt in range(config.scraper_max_retries):
            try:
                logger.info(f'Fetching models from OpenRouter API (attempt {attempt + 1})')
                response = await client.get(endpoint, headers=headers)
                if response.status_code != 200:
                    raise APIError(f'API returned status {response.status_code}', status_code=response.status_code, response_body=response.text)
                data = response.json()
                models_list = data.get('data', data) if isinstance(data, dict) else data
                filtered_models = []
                for item in models_list:
                    pricing = item.get('pricing')
                    if not isinstance(pricing, dict):
                        logger.warning(f"Skipping model {item.get('id')}: pricing field missing or not a dict")
                        continue
                    try:
                        prompt_val = pricing.get('prompt')
                        if prompt_val is None:
                            pricing['prompt'] = 0.0
                        elif isinstance(prompt_val, str):
                            if prompt_val.strip() == '-1':
                                pricing['prompt'] = 0.0
                            else:
                                pricing['prompt'] = float(prompt_val) if prompt_val.strip() else 0.0
                        elif not isinstance(prompt_val, (int, float)):
                            pricing['prompt'] = 0.0
                        elif prompt_val == -1:
                            pricing['prompt'] = 0.0
                        completion_val = pricing.get('completion')
                        if completion_val is None:
                            pricing['completion'] = 0.0
                        elif isinstance(completion_val, str):
                            if completion_val.strip() == '-1':
                                pricing['completion'] = 0.0
                            else:
                                pricing['completion'] = float(completion_val) if completion_val.strip() else 0.0
                        elif not isinstance(completion_val, (int, float)):
                            pricing['completion'] = 0.0
                        elif completion_val == -1:
                            pricing['completion'] = 0.0
                    except (ValueError, TypeError):
                        pricing['prompt'] = 0.0
                        pricing['completion'] = 0.0
                    filtered_models.append(item)
                try:
                    models = parse_response(filtered_models)
                except ValidationError as batch_err:
                    logger.error(f'Batch validation failed: {batch_err}. Attempting individual model parsing...')
                    models = []
                    for item in filtered_models:
                        try:
                            cleaned = _clean_model_dict(item)
                            model = Model(**cleaned)
                            models.append(model)
                        except ValidationError as ve:
                            logger.warning(f"Skipping invalid model {item.get('id')}: {ve}")
                            continue
                if config.model_filter:
                    import re
                    pattern = re.compile(config.model_filter)
                    filtered = [m for m in models if pattern.search(m.id)]
                    logger.info(f"Filtered models with pattern '{config.model_filter}': {len(filtered)} of {len(models)} remain")
                    models = filtered
                logger.info(f'Successfully fetched {len(models)} models')
                return models
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt < config.scraper_max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f'API request failed, retrying in {wait}s: {e}')
                    await asyncio.sleep(wait)
                    continue
                raise APIError(f'API request failed after {config.scraper_max_retries} retries: {e}')
    finally:
        if own_client:
            await client.aclose()
```

---

## Feature Function: `parse_response`
**Logic & Purpose:**
```text
Parse OpenRouter API response into Model objects.

Args:
    api_data: List of model dictionaries from API

Returns:
    List of validated Model instances

Raises:
    ValidationError: If any model fails validation (strict contract)
```

**Parameters:** `api_data`
**Variables Used:** `cleaned, models, model`
**Implementation:**
```python
def parse_response(api_data: List[Dict[str, Any]]) -> List[Model]:
    """
    Parse OpenRouter API response into Model objects.

    Args:
        api_data: List of model dictionaries from API

    Returns:
        List of validated Model instances

    Raises:
        ValidationError: If any model fails validation (strict contract)
    """
    models = []
    for item in api_data:
        cleaned = _clean_model_dict(item)
        model = Model(**cleaned)
        models.append(model)
    return models
```

---

## Feature Function: `_clean_model_dict`
**Logic & Purpose:**
```text
Clean and coerce API data to match Model expectations.
```

**Parameters:** `item`
**Variables Used:** `pricing, cleaned, val, supported_params`
**Implementation:**
```python
def _clean_model_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and coerce API data to match Model expectations.
    """
    cleaned = item.copy()

    def coerce_numeric(value, target_type=float):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                val = float(value) if '.' in value else int(value)
                return val
            except ValueError:
                return value
        return value
    if 'pricing' in cleaned and isinstance(cleaned['pricing'], dict):
        pricing = cleaned['pricing'].copy()
        for key in ['prompt', 'completion', 'cache_read', 'cache_write', 'cache_creation', 'web_search']:
            if key in pricing:
                if pricing[key] is None:
                    pricing[key] = 0.0
                    continue
                pricing[key] = coerce_numeric(pricing[key])
                if pricing[key] == -1:
                    pricing[key] = None
        cleaned['pricing'] = pricing
    for field in ['context_length', 'max_output_tokens', 'created']:
        if field in cleaned:
            cleaned[field] = coerce_numeric(cleaned[field])
    supported_params = cleaned.get('supported_parameters', [])
    if isinstance(supported_params, list):
        cleaned['supports_tools'] = 'tools' in supported_params
    else:
        cleaned['supports_tools'] = False
    return cleaned
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/models.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/models.py`

**Module Overview**: 
```text
Pydantic data models for OpenRouter Model Scout.
Defines Model, Leaderboard, Meta, and related schemas.
```

## Dependencies & Imports
datetime.datetime, typing.Optional, typing.List, typing.Dict, typing.Any, pydantic.BaseModel, pydantic.Field, pydantic.model_validator

## Feature Class: `IntelligenceMetrics`
**Description:**
```text
Intelligence benchmark scores.
```

---

## Feature Class: `CodingMetrics`
**Description:**
```text
Coding benchmark scores.
```

---

## Feature Class: `AgenticMetrics`
**Description:**
```text
Agentic benchmark scores.
```

---

## Feature Class: `Pricing`
**Description:**
```text
Pricing information per 1M tokens.
```

### Method: `normalize_cache_fields`
**Logic & Purpose:**
```text
Normalize cache_creation to cache_write if present.
```

**Parameters:** `self`
**Implementation:**
```python
@model_validator(mode='after')
def normalize_cache_fields(self) -> 'Pricing':
    """Normalize cache_creation to cache_write if present."""
    if self.cache_creation is not None and self.cache_write is None:
        self.cache_write = self.cache_creation
    return self
```

---

## Feature Class: `Performance`
**Description:**
```text
Performance metrics from provider.
```

---

## Feature Class: `Benchmarks`
**Description:**
```text
Benchmark scores from Artificial Analysis.
```

### Method: `intelligence_score`
**Logic & Purpose:**
```text
Convenience accessor for intelligence score.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def intelligence_score(self) -> Optional[float]:
    """Convenience accessor for intelligence score."""
    return self.intelligence.score if self.intelligence else None
```

### Method: `intelligence_percentile`
**Logic & Purpose:**
```text
Convenience accessor for intelligence percentile.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def intelligence_percentile(self) -> Optional[float]:
    """Convenience accessor for intelligence percentile."""
    return self.intelligence.percentile if self.intelligence else None
```

### Method: `coding_score`
**Logic & Purpose:**
```text
Convenience accessor for coding score.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def coding_score(self) -> Optional[float]:
    """Convenience accessor for coding score."""
    return self.coding.score if self.coding else None
```

### Method: `coding_percentile`
**Logic & Purpose:**
```text
Convenience accessor for coding percentile.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def coding_percentile(self) -> Optional[float]:
    """Convenience accessor for coding percentile."""
    return self.coding.percentile if self.coding else None
```

### Method: `agentic_score`
**Logic & Purpose:**
```text
Convenience accessor for agentic score.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def agentic_score(self) -> Optional[float]:
    """Convenience accessor for agentic score."""
    return self.agentic.score if self.agentic else None
```

### Method: `agentic_percentile`
**Logic & Purpose:**
```text
Convenience accessor for agentic percentile.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def agentic_percentile(self) -> Optional[float]:
    """Convenience accessor for agentic percentile."""
    return self.agentic.percentile if self.agentic else None
```

---

## Feature Class: `Model`
**Description:**
```text
AI model available through OpenRouter.
```

### Method: `set_organization`
**Logic & Purpose:**
```text
Derive organization from model ID if not provided.
```

**Parameters:** `self`
**Implementation:**
```python
@model_validator(mode='after')
def set_organization(self) -> 'Model':
    """Derive organization from model ID if not provided."""
    if self.organization is None and '/' in self.id:
        self.organization = self.id.split('/')[0]
    return self
```

### Method: `is_free`
**Logic & Purpose:**
```text
Derived field: True if both prompt and completion are $0.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def is_free(self) -> bool:
    """Derived field: True if both prompt and completion are $0."""
    return self.pricing.prompt == 0 and self.pricing.completion == 0
```

### Method: `value_score`
**Logic & Purpose:**
```text
Derived field: intelligence score divided by prompt cost.
```

**Parameters:** `self`
**Variables Used:** `cost`
**Implementation:**
```python
@property
def value_score(self) -> float:
    """Derived field: intelligence score divided by prompt cost."""
    if self.benchmarks and self.benchmarks.intelligence_score is not None:
        cost = max(self.pricing.prompt, 1e-06)
        return self.benchmarks.intelligence_score / cost
    return 0.0
```

### Method: `effective_price_input`
**Logic & Purpose:**
```text
Placeholder: would be computed as weighted average across providers.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def effective_price_input(self) -> float:
    """Placeholder: would be computed as weighted average across providers."""
    return self.pricing.prompt
```

### Method: `effective_price_output`
**Logic & Purpose:**
```text
Placeholder: would be computed as weighted average across providers.
```

**Parameters:** `self`
**Implementation:**
```python
@property
def effective_price_output(self) -> float:
    """Placeholder: would be computed as weighted average across providers."""
    return self.pricing.completion
```

---

## Feature Class: `SmartestEntry`
**Description:**
```text
Entry in the smartest models leaderboard.
```

---

## Feature Class: `CodingEntry`
**Description:**
```text
Entry in the coding models leaderboard.
```

---

## Feature Class: `FreeEntry`
**Description:**
```text
Entry in the free models leaderboard.
```

---

## Feature Class: `ValueEntry`
**Description:**
```text
Entry in the value models leaderboard.
```

---

## Feature Class: `Leaderboard`
**Description:**
```text
Top-5 lists generated from model database.
```

---

## Feature Class: `RunHistoryEntry`
**Description:**
```text
Single run record in meta.json.
```

---

## Feature Class: `Meta`
**Description:**
```text
Operational metadata.
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/config.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/config.py`

**Module Overview**: 
```text
Configuration management for the scout.
Implements: load_env_vars(), validate_config(), CLI flag definitions
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
os, dataclasses.dataclass, typing.Optional, typing.Dict, typing.Any, logging

## Feature Class: `Config`
**Description:**
```text
Immutable configuration object.
```

### Method: `__post_init__`
**Logic & Purpose:**
```text
Store raw env for debugging.
```

**Parameters:** `self`
**Implementation:**
```python
def __post_init__(self):
    """Store raw env for debugging."""
    if self._env is None:
        self._env = dict(os.environ)
```

---

## Feature Function: `load_env_vars`
**Logic & Purpose:**
```text
Load required environment variables.

Returns:
    Dict of env vars (keys uppercased)

Raises:
    EnvironmentError: If required vars are missing
```

**Parameters:** ``
**Variables Used:** `value, required, config`
**Implementation:**
```python
def load_env_vars() -> Dict[str, str]:
    """
    Load required environment variables.

    Returns:
        Dict of env vars (keys uppercased)

    Raises:
        EnvironmentError: If required vars are missing
    """
    required = ['OPENROUTER_API_KEY']
    config = {}
    for key in required:
        value = os.environ.get(key)
        if value is None:
            raise EnvironmentError(f'Missing required environment variable: {key}')
        config[key] = value
    config['DATA_DIR'] = os.environ.get('DATA_DIR', 'data')
    config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')
    config['LOG_FILE'] = os.environ.get('LOG_FILE', None)
    return config
```

---

## Feature Function: `validate_config`
**Logic & Purpose:**
```text
Validate configuration values.

Args:
    config: Configuration dict to validate

Raises:
    ValueError: If configuration is invalid
```

**Parameters:** `config`
**Variables Used:** `hours, valid_log_levels, threshold, valid_formats`
**Implementation:**
```python
def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.

    Args:
        config: Configuration dict to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if 'OPENROUTER_API_KEY' not in config:
        raise ValueError('Missing OPENROUTER_API_KEY')
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.get('LOG_LEVEL', 'INFO').upper() not in valid_log_levels:
        raise ValueError(f'Invalid LOG_LEVEL. Must be one of: {valid_log_levels}')
    valid_formats = ['json', 'csv', 'both']
    if config.get('OUTPUT_FORMAT', 'json').lower() not in valid_formats:
        raise ValueError(f'Invalid OUTPUT_FORMAT. Must be one of: {valid_formats}')
    if 'API_SYNC_MAX_AGE_HOURS' in config:
        try:
            hours = int(config['API_SYNC_MAX_AGE_HOURS'])
            if hours <= 0:
                raise ValueError('API_SYNC_MAX_AGE_HOURS must be positive')
        except (ValueError, TypeError):
            raise ValueError('API_SYNC_MAX_AGE_HOURS must be an integer')
    if 'PRICING_DELTA_THRESHOLD' in config:
        try:
            threshold = float(config['PRICING_DELTA_THRESHOLD'])
            if not 0 <= threshold <= 1:
                raise ValueError('PRICING_DELTA_THRESHOLD must be between 0 and 1')
        except (ValueError, TypeError):
            raise ValueError('PRICING_DELTA_THRESHOLD must be a number')
```

---

## Feature Function: `get_cli_flags`
**Logic & Purpose:**
```text
Get CLI flag definitions (for argparse integration).

Returns:
    Dict mapping flag names to argparse kwargs
```

**Parameters:** ``
**Implementation:**
```python
def get_cli_flags() -> Dict[str, Any]:
    """
    Get CLI flag definitions (for argparse integration).

    Returns:
        Dict mapping flag names to argparse kwargs
    """
    return {'force': {'action': 'store_true', 'help': 'Ignore timestamps, execute full deep scan immediately'}, 'fast-only': {'action': 'store_true', 'dest': 'fast_only', 'help': 'Only run API sync, skip web scraping entirely'}, 'dry-run': {'action': 'store_true', 'dest': 'dry_run', 'help': 'Execute logic without writing files; print to stdout'}, 'token-report': {'action': 'store_true', 'dest': 'token_report', 'help': 'Display detailed token usage and cost of the scraper itself'}, 'output-format': {'type': str, 'choices': ['json', 'csv', 'both'], 'default': 'json', 'dest': 'output_format', 'help': 'Control output formats'}, 'model-filter': {'type': str, 'dest': 'model_filter', 'help': 'Only process matching model IDs (regex pattern)'}, 'verbose': {'action': 'store_true', 'help': 'Enable debug logging'}}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/exceptions.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/exceptions.py`

**Module Overview**: 
```text
Custom exception hierarchy for OpenRouter Model Scout.
Implements: APIError, ScraperError, DataCorruptionError, ConfigurationError
```

## Dependencies & Imports
typing.Any, typing.Dict, typing.Optional

## Feature Class: `ScoutError`
**Description:**
```text
Base exception for all scout errors.
```

---

## Feature Class: `APIError`
**Description:**
```text
Raised when OpenRouter API interaction fails.
```

### Method: `__init__`
**Parameters:** `self, message, status_code, response_body`
**Implementation:**
```python
def __init__(self, message: str, status_code: Optional[int]=None, response_body: Optional[str]=None):
    super().__init__(message)
    self.status_code = status_code
    self.response_body = response_body
```

---

## Feature Class: `ScraperError`
**Description:**
```text
Raised when web scraping fails.
```

### Method: `__init__`
**Parameters:** `self, message, model_id, details`
**Implementation:**
```python
def __init__(self, message: str, model_id: Optional[str]=None, details: Optional[Dict[str, Any]]=None):
    super().__init__(message)
    self.model_id = model_id
    self.details = details or {}
```

---

## Feature Class: `DataCorruptionError`
**Description:**
```text
Raised when data files are corrupted and backed up.
```

### Method: `__init__`
**Parameters:** `self, message, file_path, backup_path`
**Implementation:**
```python
def __init__(self, message: str, file_path: str, backup_path: Optional[str]=None):
    super().__init__(message)
    self.file_path = file_path
    self.backup_path = backup_path
```

---

## Feature Class: `ConfigurationError`
**Description:**
```text
Raised when configuration is invalid or missing.
```

### Method: `__init__`
**Parameters:** `self, message, missing_keys`
**Implementation:**
```python
def __init__(self, message: str, missing_keys: Optional[list]=None):
    super().__init__(message)
    self.missing_keys = missing_keys or []
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/main.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/main.py`

**Module Overview**: 
```text
Main entry point for OpenRouter Model Scout.
Orchestrates the full pipeline: fetch → normalize → leaderboard.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
argparse, asyncio, logging, time, datetime.datetime, datetime.timezone, pathlib.Path, sys, random, openrouter_model_scout.config.Config, openrouter_model_scout.config.load_env_vars, openrouter_model_scout.config.validate_config, openrouter_model_scout.config.get_cli_flags, openrouter_model_scout.logger.setup_logger, openrouter_model_scout.fetcher_api.fetch_models, openrouter_model_scout.normalizer.normalize_data, openrouter_model_scout.change_detector.calculate_checksum, openrouter_model_scout.change_detector.detect_pricing_delta, openrouter_model_scout.change_detector.queue_new_models, openrouter_model_scout.leaderboard.generate_smartest_leaderboard, openrouter_model_scout.leaderboard.generate_coding_leaderboard, openrouter_model_scout.leaderboard.generate_free_leaderboard, openrouter_model_scout.leaderboard.generate_value_leaderboard, openrouter_model_scout.leaderboard.write_leaderboard, openrouter_model_scout.leaderboard.validate_lists, openrouter_model_scout.io.load_json, openrouter_model_scout.io.atomic_json_write, openrouter_model_scout.meta.load_meta, openrouter_model_scout.meta.append_run, openrouter_model_scout.meta.write_meta, openrouter_model_scout.token_utils.track_api_call, openrouter_model_scout.cost.calculate_estimated_cost, openrouter_model_scout.models.Model, openrouter_model_scout.models.Meta, openrouter_model_scout.models.Leaderboard, openrouter_model_scout.scraper_web.ScraperManager, openrouter_model_scout.scraper_web.process_model_queue, openrouter_model_scout.scraper_web.convert_scrape_results_to_enrichment, openrouter_model_scout.scraper_web.estimate_scrape_cost

## Feature Function: `parse_args`
**Logic & Purpose:**
```text
Parse command-line arguments.
```

**Parameters:** ``
**Variables Used:** `args, parser, flags`
**Implementation:**
```python
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='OpenRouter Model Scout')
    flags = get_cli_flags()
    for flag, opts in flags.items():
        parser.add_argument(f'--{flag}', **opts)
    args = parser.parse_args()
    return args
```

---

## Feature Function: `should_run_auto`
**Logic & Purpose:**
```text
Check if automatic run is needed based on timestamp.

Args:
    data_dir: Data directory path
    last_run_str: ISO timestamp of last run
    max_age_hours: Max age threshold in hours

Returns:
    True if run needed, False otherwise
```

**Parameters:** `data_dir, last_run_str, max_age_hours`
**Variables Used:** `age, last_run, now`
**Implementation:**
```python
def should_run_auto(data_dir: Path, last_run_str: str, max_age_hours: int) -> bool:
    """
    Check if automatic run is needed based on timestamp.

    Args:
        data_dir: Data directory path
        last_run_str: ISO timestamp of last run
        max_age_hours: Max age threshold in hours

    Returns:
        True if run needed, False otherwise
    """
    if not last_run_str:
        return True
    last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    age = now - last_run
    return age.total_seconds() > max_age_hours * 3600
```

---

## Feature Function: `load_previous_models`
**Logic & Purpose:**
```text
Load previous models.json if exists, else empty list.
```

**Parameters:** `models_path`
**Variables Used:** `models_data`
**Implementation:**
```python
def load_previous_models(models_path: Path) -> list:
    """Load previous models.json if exists, else empty list."""
    if not models_path.exists():
        return []
    try:
        models_data = load_json(models_path)
        from openrouter_model_scout.models import Model
        return [Model.model_validate(m) for m in models_data]
    except Exception as e:
        logger.error(f'Failed to load previous models: {e}')
        return []
```

---

## Feature Function: `orchestrate_api_sync`
**Logic & Purpose:**
```text
Execute API sync phase.

Returns:
    (models, token_usage)
```

**Parameters:** `config, args`
**Variables Used:** `start, token_usage, models, token_est, response_size, duration`
**Implementation:**
```python
def orchestrate_api_sync(config: Config, args) -> tuple[list[Model], dict]:
    """
    Execute API sync phase.

    Returns:
        (models, token_usage)
    """
    start = time.time()
    logger.info('Starting API sync phase')
    models = asyncio.run(fetch_models(config))
    duration = time.time() - start
    logger.info(f'API sync completed in {duration:.2f}s, fetched {len(models)} models')
    response_size = sum((len(m.model_dump_json()) for m in models))
    token_est = estimate_response_size(models)
    token_usage = {'prompt_tokens': 0, 'completion_tokens': token_est['completion_tokens'], 'estimated_cost_usd': 0.0}
    return (models, token_usage)
```

---

## Feature Function: `estimate_response_size`
**Logic & Purpose:**
```text
Estimate token count for API response.
```

**Parameters:** `models`
**Variables Used:** `tokens, total_chars`
**Implementation:**
```python
def estimate_response_size(models: list[Model]) -> dict:
    """Estimate token count for API response."""
    total_chars = sum((len(m.model_dump_json()) for m in models))
    tokens = total_chars // 4
    return {'completion_tokens': tokens}
```

---

## Feature Function: `orchestrate_deep_scrape`
**Logic & Purpose:**
```text
Execute deep web scraping for benchmark data.

Args:
    config: Configuration object
    models_to_scrape: List of models needing scrape data
    scrape_duration: Time spent in previous scrape (for resuming)

Returns:
    (scraped_data, token_usage)
```

**Parameters:** `config, models_to_scrape, scrape_duration`
**Variables Used:** `scraped_data, cost, results, start, future, scrape_duration, total_token_usage, loop`
**Implementation:**
```python
def orchestrate_deep_scrape(config: Config, models_to_scrape: list[Model], scrape_duration: float=0.0) -> tuple[dict, dict, float]:
    """
    Execute deep web scraping for benchmark data.

    Args:
        config: Configuration object
        models_to_scrape: List of models needing scrape data
        scrape_duration: Time spent in previous scrape (for resuming)

    Returns:
        (scraped_data, token_usage)
    """
    start = time.time()
    logger.info(f'Starting deep scrape for {len(models_to_scrape)} models')
    scraped_data = {}
    total_token_usage = {'prompt_tokens': 0, 'completion_tokens': 0}
    if not models_to_scrape:
        logger.info('No models require deep scraping')
        return (scraped_data, total_token_usage)
    try:
        with ScraperManager(stealth_mode=True, max_concurrent=1, delay_range=(2.0, 5.0)) as manager:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, process_model_queue([m.id for m in models_to_scrape], manager))
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(process_model_queue([m.id for m in models_to_scrape], manager))
            scraped_data = convert_scrape_results_to_enrichment(results)
            for model_id in results:
                cost = estimate_scrape_cost(model_id)
                total_token_usage['prompt_tokens'] += cost['prompt_tokens']
                total_token_usage['completion_tokens'] += cost['completion_tokens']
            scrape_duration = time.time() - start
            logger.info(f'Deep scrape completed in {scrape_duration:.2f}s, scraped {len(results)} models')
    except Exception as e:
        logger.error(f'Deep scrape failed: {e}')
        scraped_data = {}
    return (scraped_data, total_token_usage, scrape_duration)
```

---

## Feature Function: `run_scout`
**Logic & Purpose:**
```text
Core orchestration logic. Can be called programmatically.

Args:
    config: Configuration object
    dry_run: If True, don't write files

Returns:
    dict with results: {
        'models': list[Model],
        'leaderboard': Leaderboard,
        'token_usage': dict,
        'duration': float
    }
```

**Parameters:** `config, dry_run`
**Variables Used:** `new_model_ids, total_cost, timestamp, previous_ids, meta_path, previous_checksum, current_ids, leaderboard_path, needs_deep_scrape, scraped_data, scrape_duration, mode, scrape_token_usage, current_checksum, token_usage, csv_path, models_path, output_format, models_data, days_since_audit, duration, base_api_cost, meta, last_deep, start, normalized_models, models_to_scrape, leaderboard, previous_models, data_dir`
**Implementation:**
```python
def run_scout(config: Config, dry_run: bool=False) -> dict:
    """
    Core orchestration logic. Can be called programmatically.

    Args:
        config: Configuration object
        dry_run: If True, don't write files

    Returns:
        dict with results: {
            'models': list[Model],
            'leaderboard': Leaderboard,
            'token_usage': dict,
            'duration': float
        }
    """
    start = time.time()
    logger.info('=== OpenRouter Model Scout starting ===')
    data_dir = Path(config.data_dir)
    models_path = data_dir / 'models.json'
    meta_path = data_dir / 'meta.json'
    try:
        api_models, api_token_usage = orchestrate_api_sync(config, None)
        previous_models = load_previous_models(models_path)
        previous_checksum = calculate_checksum(previous_models) if previous_models else None
        current_checksum = calculate_checksum([m.model_dump() for m in api_models])
        needs_deep_scrape = False
        if config.force:
            needs_deep_scrape = True
            logger.info('Force flag set: will run deep scrape for all models')
        else:
            current_ids = {m.id for m in api_models}
            previous_ids = {m.id for m in previous_models}
            new_model_ids = queue_new_models(current_ids, previous_ids)
            if new_model_ids:
                logger.info(f'New models detected: {len(new_model_ids)} models need scraping')
                needs_deep_scrape = True
            try:
                meta = load_meta(meta_path)
                last_deep = datetime.fromisoformat(meta.last_deep_audit.replace('Z', '+00:00'))
                days_since_audit = (datetime.now(timezone.utc) - last_deep).days
                if days_since_audit >= 7:
                    logger.info(f'Weekly audit due ({days_since_audit} days since last audit)')
                    needs_deep_scrape = True
            except Exception:
                needs_deep_scrape = True
        scrape_token_usage = {'prompt_tokens': 0, 'completion_tokens': 0}
        scrape_duration = 0.0
        if needs_deep_scrape:
            models_to_scrape = api_models
            scraped_data, scrape_token_usage, scrape_duration = orchestrate_deep_scrape(config, models_to_scrape)
        else:
            scraped_data = {}
            logger.info('Skipping deep scrape (no changes detected)')
        normalized_models = normalize_data(api_models, scraped_data)
        timestamp = datetime.now(timezone.utc).isoformat()
        leaderboard = Leaderboard(generated_at=timestamp)
        leaderboard.smartest = generate_smartest_leaderboard(normalized_models, top_n=5, generated_at=timestamp).smartest
        leaderboard.coding = generate_coding_leaderboard(normalized_models, top_n=5, generated_at=timestamp).coding
        leaderboard.free = generate_free_leaderboard(normalized_models, top_n=5, generated_at=timestamp).free
        leaderboard.value = generate_value_leaderboard(normalized_models, top_n=5, generated_at=timestamp).value
        validate_lists(leaderboard)
        if not dry_run:
            models_data = [m.model_dump() for m in normalized_models]
            atomic_json_write(models_data, models_path)
            leaderboard_path = data_dir / 'leaderboard.json'
            write_leaderboard(leaderboard, leaderboard_path)
            logger.info(f'Wrote {len(normalized_models)} models to {models_path}')
            logger.info(f'Wrote leaderboard to {leaderboard_path}')
            output_format = getattr(config, 'output_format', 'json')
            if output_format in ('csv', 'both'):
                from openrouter_model_scout.leaderboard import write_leaderboard_csv
                csv_path = Path(leaderboard_path).with_suffix('.csv')
                write_leaderboard_csv(leaderboard, csv_path)
            meta = load_meta(meta_path)
            duration = time.time() - start
            base_api_cost = 0.0
            total_cost = base_api_cost
            if scrape_token_usage['completion_tokens'] > 0:
                pass
            token_usage = {'prompt_tokens': api_token_usage['prompt_tokens'] + scrape_token_usage['prompt_tokens'], 'completion_tokens': api_token_usage['completion_tokens'] + scrape_token_usage['completion_tokens'], 'estimated_cost_usd': total_cost}
            mode = 'force' if config.force else 'full' if needs_deep_scrape else 'fast'
            append_run(meta, timestamp=timestamp, mode=mode, api_duration=time.time() - start, scrape_duration=scrape_duration, models_count=len(normalized_models), token_usage=token_usage)
            write_meta(meta, meta_path)
            logger.info(f'Updated meta at {meta_path}')
        else:
            logger.info('Dry-run mode: no files written')
        duration = time.time() - start
        logger.info('=== OpenRouter Model Scout completed successfully ===')
        return {'models': normalized_models, 'leaderboard': leaderboard, 'token_usage': api_token_usage, 'duration': duration}
    except Exception as e:
        logger.exception(f'Fatal error: {e}')
        raise
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
CLI entry point.
```

**Parameters:** ``
**Variables Used:** `args, should_run, meta, result, config, usage, meta_path, data_dir, env_config, log_level`
**Implementation:**
```python
def main():
    """CLI entry point."""
    args = parse_args()
    try:
        env_config = load_env_vars()
        validate_config(env_config)
    except Exception as e:
        logger.error(f'Configuration error: {e}')
        sys.exit(1)
    config = Config(openrouter_api_key=env_config['OPENROUTER_API_KEY'], data_dir=env_config.get('DATA_DIR', 'data'), log_level=env_config.get('LOG_LEVEL', 'INFO'), log_file=env_config.get('LOG_FILE'), force=args.force, fast_only=args.fast_only, dry_run=args.dry_run, token_report=args.token_report, output_format=env_config.get('OUTPUT_FORMAT', 'json'), model_filter=args.model_filter)
    log_level = logging.DEBUG if args.verbose else getattr(logging, config.log_level)
    setup_logger(level=log_level, log_file=config.log_file)
    should_run = True
    if not config.force:
        data_dir = Path(config.data_dir)
        meta_path = data_dir / 'meta.json'
        try:
            meta = load_meta(meta_path)
            should_run = should_run_auto(data_dir, meta.last_run, config.api_sync_max_age_hours)
        except Exception:
            should_run = True
    if not should_run:
        logger.info('Auto-check: No changes detected, skipping run. Use --force to override.')
        sys.exit(0)
    try:
        result = run_scout(config, dry_run=config.dry_run)
        if config.token_report:
            usage = result['token_usage']
            print('\n=== Token Usage Report ===')
            print(f"Prompt tokens: {usage['prompt_tokens']:,}")
            print(f"Completion tokens: {usage['completion_tokens']:,}")
            print(f"Total tokens: {usage['prompt_tokens'] + usage['completion_tokens']:,}")
            print(f"Estimated cost: ${usage['estimated_cost_usd']:.6f}")
            print(f"Duration: {result['duration']:.2f}s")
        sys.exit(0)
    except Exception as e:
        logger.exception(f'Fatal error: {e}')
        sys.exit(1)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/meta.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/meta.py`

**Module Overview**: 
```text
Meta.json management for run history and timestamps.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
json, logging, datetime.datetime, datetime.timezone, pathlib.Path, typing.Dict, typing.Any, typing.List, typing.Optional, openrouter_model_scout.models.Meta

## Feature Function: `load_meta`
**Logic & Purpose:**
```text
Load meta.json, initializing if missing.

Args:
    meta_path: Path to meta.json

Returns:
    Meta model instance
```

**Parameters:** `meta_path`
**Variables Used:** `path, now, data`
**Implementation:**
```python
def load_meta(meta_path: str | Path) -> MetaModel:
    """
    Load meta.json, initializing if missing.

    Args:
        meta_path: Path to meta.json

    Returns:
        Meta model instance
    """
    path = Path(meta_path)
    if not path.exists():
        logger.info('meta.json not found, initializing new meta')
        now = datetime.now(timezone.utc).isoformat()
        return MetaModel(last_run=now, last_deep_audit=now, run_history=[])
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return MetaModel(**data)
```

---

## Feature Function: `append_run`
**Logic & Purpose:**
```text
Append a new run entry to meta and update timestamps.

Args:
    meta: Meta model (modified in place)
    timestamp: ISO 8601 timestamp of run start
    mode: Run mode (full, fast, force, etc.)
    api_duration: Seconds spent in API sync
    scrape_duration: Seconds spent in deep scrape
    models_count: Number of models processed
    token_usage: Dict with token counts and cost
```

**Parameters:** `meta, timestamp, mode, api_duration, scrape_duration, models_count, token_usage`
**Variables Used:** `entry`
**Implementation:**
```python
def append_run(meta: MetaModel, timestamp: str, mode: str, api_duration: float, scrape_duration: float, models_count: int, token_usage: Dict[str, Any]) -> None:
    """
    Append a new run entry to meta and update timestamps.

    Args:
        meta: Meta model (modified in place)
        timestamp: ISO 8601 timestamp of run start
        mode: Run mode (full, fast, force, etc.)
        api_duration: Seconds spent in API sync
        scrape_duration: Seconds spent in deep scrape
        models_count: Number of models processed
        token_usage: Dict with token counts and cost
    """
    from openrouter_model_scout.models import RunHistoryEntry
    entry = RunHistoryEntry(timestamp=timestamp, mode=mode, api_sync_duration_seconds=api_duration, scrape_duration_seconds=scrape_duration, models_count=models_count, token_usage=token_usage)
    meta.run_history.append(entry)
    meta.last_run = timestamp
    if mode in ('full', 'force'):
        meta.last_deep_audit = timestamp
    if len(meta.run_history) > 100:
        meta.run_history = meta.run_history[-100:]
```

---

## Feature Function: `write_meta`
**Logic & Purpose:**
```text
Write meta to disk atomically.

Args:
    meta: Meta model
    meta_path: Destination file path
```

**Parameters:** `meta, meta_path`
**Variables Used:** `data`
**Implementation:**
```python
def write_meta(meta: MetaModel, meta_path: str | Path) -> None:
    """
    Write meta to disk atomically.

    Args:
        meta: Meta model
        meta_path: Destination file path
    """
    from openrouter_model_scout.io import atomic_json_write
    data = meta.model_dump(mode='json')
    atomic_json_write(data, meta_path)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/__init__.py`

**Module Overview**: 
```text
OpenRouter Model Scout package.
```

## Global Presets & Variables
- `__version__` = `'0.1.0'`


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/normalizer.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/normalizer.py`

**Module Overview**: 
```text
Data normalizer: merge API model data with optional scraped enrichments.
Implements: normalize_data(), _apply_scrape_data()

Used in: User Story 1, 2, 3
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
logging, typing.List, typing.Dict, typing.Any, typing.Optional, pydantic.ValidationError, openrouter_model_scout.models.Model, openrouter_model_scout.models.Pricing, openrouter_model_scout.models.Performance, openrouter_model_scout.models.Benchmarks

## Feature Function: `normalize_data`
**Logic & Purpose:**
```text
Merge API model data with optional scraped enrichments.

Args:
    api_models: List of Model objects from API (already validated)
    scraped_data: Dict mapping model_id -> scraped enrichment fields
        Expected keys: 'benchmarks' (dict with nested structure),
        'performance' (dict), 'description_short', 'description_full',
        'release_date', 'parameter_size', 'quantization'

Returns:
    List of Model objects with enriched data where available
```

**Parameters:** `api_models, scraped_data`
**Variables Used:** `scrape, enriched_model, normalized`
**Implementation:**
```python
def normalize_data(api_models: List[Model], scraped_data: Dict[str, Dict[str, Any]]) -> List[Model]:
    """
    Merge API model data with optional scraped enrichments.

    Args:
        api_models: List of Model objects from API (already validated)
        scraped_data: Dict mapping model_id -> scraped enrichment fields
            Expected keys: 'benchmarks' (dict with nested structure),
            'performance' (dict), 'description_short', 'description_full',
            'release_date', 'parameter_size', 'quantization'

    Returns:
        List of Model objects with enriched data where available
    """
    normalized = []
    for model in api_models:
        scrape = scraped_data.get(model.id, {})
        enriched_model = _apply_scrape_data(model, scrape)
        normalized.append(enriched_model)
    return normalized
```

---

## Feature Function: `_apply_scrape_data`
**Logic & Purpose:**
```text
Apply scraped data to a model, creating new Model instance with merged fields.

Args:
    model: Original Model from API
    scrape: Scraped data dict

Returns:
    New Model with enriched fields (fields from scrape override API if both exist)
```

**Parameters:** `model, scrape`
**Variables Used:** `model_dict, merged, perf_data, bench_data, update_data`
**Implementation:**
```python
def _apply_scrape_data(model: Model, scrape: Dict[str, Any]) -> Model:
    """
    Apply scraped data to a model, creating new Model instance with merged fields.

    Args:
        model: Original Model from API
        scrape: Scraped data dict

    Returns:
        New Model with enriched fields (fields from scrape override API if both exist)
    """
    update_data = {}
    for field in ['description_short', 'description_full', 'release_date', 'parameter_size', 'quantization']:
        if field in scrape:
            update_data[field] = scrape[field]
    if 'performance' in scrape:
        perf_data = scrape['performance']
        if model.performance is None:
            update_data['performance'] = Performance(**perf_data)
        else:
            merged = model.performance.dict() | perf_data
            update_data['performance'] = Performance(**merged)
    if 'benchmarks' in scrape:
        bench_data = scrape['benchmarks']
        if model.benchmarks is None:
            update_data['benchmarks'] = Benchmarks(**bench_data)
        else:
            merged = model.benchmarks.dict() | bench_data
            update_data['benchmarks'] = Benchmarks(**merged)
    model_dict = model.model_dump()
    model_dict.update(update_data)
    return Model(**model_dict)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/change_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/change_detector.py`

## Dependencies & Imports
json, hashlib, typing.List, typing.Any, typing.Dict, typing.Set

## Feature Function: `calculate_checksum`
**Logic & Purpose:**
```text
Calculate SHA256 checksum for model data.

Args:
    models: List of model objects or dictionaries

Returns:
    Hexadecimal SHA256 hash string (64 chars)
```

**Parameters:** `models`
**Variables Used:** `content`
**Implementation:**
```python
def calculate_checksum(models: List[Any]) -> str:
    """
    Calculate SHA256 checksum for model data.

    Args:
        models: List of model objects or dictionaries

    Returns:
        Hexadecimal SHA256 hash string (64 chars)
    """
    content = json.dumps([m.model_dump() if hasattr(m, 'model_dump') else m for m in models], sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(content).hexdigest()
```

---

## Feature Function: `detect_pricing_delta`
**Logic & Purpose:**
```text
Detect models with significant pricing changes.

Args:
    previous_pricing: Previous pricing data
    current_pricing: Current pricing data
    threshold: Price change threshold (0-1)

Returns:
    List of model IDs with pricing changes above threshold
```

**Parameters:** `previous_pricing, current_pricing, threshold`
**Variables Used:** `change, changed_models, new_price, previous, old_price`
**Implementation:**
```python
def detect_pricing_delta(previous_pricing: Dict[str, Dict[str, float]], current_pricing: Dict[str, Dict[str, float]], threshold: float=0.1) -> List[str]:
    """
    Detect models with significant pricing changes.

    Args:
        previous_pricing: Previous pricing data
        current_pricing: Current pricing data
        threshold: Price change threshold (0-1)

    Returns:
        List of model IDs with pricing changes above threshold
    """
    changed_models = []
    for model_id, current in current_pricing.items():
        previous = previous_pricing.get(model_id)
        if not previous:
            continue
        for key in ['prompt', 'completion']:
            if current.get(key) is None or previous.get(key) is None:
                continue
            old_price = previous[key]
            new_price = current[key]
            if old_price == 0:
                continue
            change = abs(new_price - old_price) / old_price
            if change >= threshold:
                changed_models.append(model_id)
                break
    return changed_models
```

---

## Feature Function: `queue_new_models`
**Logic & Purpose:**
```text
Identify new models that need scraping.

Args:
    current_ids: Set of current model IDs
    previous_ids: Set of previous model IDs

Returns:
    List of new model IDs
```

**Parameters:** `current_ids, previous_ids`
**Implementation:**
```python
def queue_new_models(current_ids: Set[str], previous_ids: Set[str]) -> List[str]:
    """
    Identify new models that need scraping.

    Args:
        current_ids: Set of current model IDs
        previous_ids: Set of previous model IDs

    Returns:
        List of new model IDs
    """
    return list(current_ids - previous_ids)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/token_utils.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/token_utils.py`

**Module Overview**: 
```text
Token estimation utilities for tracking API usage.
Simple estimation based on character count (rough approximation).
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
logging

## Feature Function: `estimate_tokens`
**Logic & Purpose:**
```text
Roughly estimate number of tokens in text.
Uses approximation: 1 token ≈ 4 characters for English text.
For more accurate counts, would use tiktoken, but this is sufficient for tracking.
```

**Parameters:** `text`
**Implementation:**
```python
def estimate_tokens(text: str) -> int:
    """
    Roughly estimate number of tokens in text.
    Uses approximation: 1 token ≈ 4 characters for English text.
    For more accurate counts, would use tiktoken, but this is sufficient for tracking.
    """
    if not text:
        return 0
    return len(text) // 4
```

---

## Feature Function: `estimate_prompt_tokens`
**Logic & Purpose:**
```text
Estimate tokens in the API request (prompt to send to OpenRouter).
In this case, we're not sending a prompt; we're making a GET request.
But we can estimate response size for cost tracking.
```

**Parameters:** `models_json`
**Implementation:**
```python
def estimate_prompt_tokens(models_json: str) -> int:
    """
    Estimate tokens in the API request (prompt to send to OpenRouter).
    In this case, we're not sending a prompt; we're making a GET request.
    But we can estimate response size for cost tracking.
    """
    return 0
```

---

## Feature Function: `estimate_response_tokens`
**Logic & Purpose:**
```text
Estimate tokens in the API response (completion tokens in OpenRouter billing context).
OpenRouter may bill on response size; we estimate for our own tracking.
```

**Parameters:** `response_text`
**Implementation:**
```python
def estimate_response_tokens(response_text: str) -> int:
    """
    Estimate tokens in the API response (completion tokens in OpenRouter billing context).
    OpenRouter may bill on response size; we estimate for our own tracking.
    """
    return estimate_tokens(response_text)
```

---

## Feature Function: `track_api_call`
**Logic & Purpose:**
```text
Create a token usage record for an API call.

Args:
    request_size: Size of request payload in characters (0 for GET)
    response_size: Size of response body in characters

Returns:
    dict with prompt_tokens, completion_tokens, total_tokens
```

**Parameters:** `request_size, response_size`
**Variables Used:** `prompt_tokens, completion_tokens`
**Implementation:**
```python
def track_api_call(request_size: int, response_size: int) -> dict:
    """
    Create a token usage record for an API call.

    Args:
        request_size: Size of request payload in characters (0 for GET)
        response_size: Size of response body in characters

    Returns:
        dict with prompt_tokens, completion_tokens, total_tokens
    """
    prompt_tokens = estimate_prompt_tokens('')
    completion_tokens = estimate_response_tokens('a' * response_size)
    return {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': prompt_tokens + completion_tokens}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/leaderboard.py
**Path**: `/home/cheta/code/claude-code-proxy/model-scraper/src/openrouter_model_scout/leaderboard.py`

**Module Overview**: 
```text
Leaderboard generation: top-N lists for quick proxy access.
Implements:
  - generate_smartest_leaderboard()
  - generate_coding_leaderboard()
  - generate_free_leaderboard()
  - generate_value_leaderboard()
  - write_leaderboard(), validate_lists()
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
json, logging, datetime.datetime, datetime.timezone, typing.List, typing.Dict, typing.Any, typing.Optional, pydantic.BaseModel, openrouter_model_scout.models.Model, openrouter_model_scout.models.Leaderboard, openrouter_model_scout.models.SmartestEntry, openrouter_model_scout.models.CodingEntry, openrouter_model_scout.models.FreeEntry, openrouter_model_scout.models.ValueEntry

## Feature Function: `generate_smartest_leaderboard`
**Logic & Purpose:**
```text
Generate leaderboard of top N smartest models.

Sorted by intelligence.score descending.
Excludes models with missing intelligence score.

Args:
    models: List of normalized Model objects
    top_n: Number of top entries to include
    generated_at: ISO 8601 timestamp (default: now)

Returns:
    Leaderboard object with smartest list populated
```

**Parameters:** `models, top_n, generated_at`
**Variables Used:** `generated_at, candidates, top_models, smartest_entries`
**Implementation:**
```python
def generate_smartest_leaderboard(models: List[Model], top_n: int=5, generated_at: Optional[str]=None) -> Leaderboard:
    """
    Generate leaderboard of top N smartest models.

    Sorted by intelligence.score descending.
    Excludes models with missing intelligence score.

    Args:
        models: List of normalized Model objects
        top_n: Number of top entries to include
        generated_at: ISO 8601 timestamp (default: now)

    Returns:
        Leaderboard object with smartest list populated
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()
    candidates = [m for m in models if m.benchmarks and m.benchmarks.intelligence_score is not None]
    candidates.sort(key=lambda m: m.benchmarks.intelligence_score, reverse=True)
    top_models = candidates[:top_n]
    smartest_entries = [SmartestEntry(id=m.id, name=m.name, intelligence_score=m.benchmarks.intelligence_score, percentile=m.benchmarks.intelligence_percentile or 0.0, price_per_1m=m.pricing.prompt) for m in top_models]
    return Leaderboard(generated_at=generated_at, smartest=smartest_entries, coding=[], free=[], value=[])
```

---

## Feature Function: `generate_coding_leaderboard`
**Logic & Purpose:**
```text
Generate leaderboard of top N coding models.
```

**Parameters:** `models, top_n, generated_at`
**Variables Used:** `coding_entries, candidates, top_models, generated_at`
**Implementation:**
```python
def generate_coding_leaderboard(models: List[Model], top_n: int=5, generated_at: Optional[str]=None) -> Leaderboard:
    """Generate leaderboard of top N coding models."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()
    candidates = [m for m in models if m.benchmarks and m.benchmarks.coding_score is not None]
    candidates.sort(key=lambda m: m.benchmarks.coding_score, reverse=True)
    top_models = candidates[:top_n]
    coding_entries = [CodingEntry(id=m.id, name=m.name, coding_score=m.benchmarks.coding_score, agentic_score=m.benchmarks.agentic_score or 0.0, price_per_1m=m.pricing.prompt) for m in top_models]
    return Leaderboard(generated_at=generated_at, smartest=[], coding=coding_entries, free=[], value=[])
```

---

## Feature Function: `generate_free_leaderboard`
**Logic & Purpose:**
```text
Generate leaderboard of top N free models.
```

**Parameters:** `models, top_n, generated_at`
**Variables Used:** `free_entries, candidates, top_models, generated_at`
**Implementation:**
```python
def generate_free_leaderboard(models: List[Model], top_n: int=5, generated_at: Optional[str]=None) -> Leaderboard:
    """Generate leaderboard of top N free models."""
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()
    candidates = [m for m in models if m.is_free]
    candidates.sort(key=lambda m: (m.benchmarks.intelligence_score if m.benchmarks and m.benchmarks.intelligence_score else 0, m.context_length), reverse=True)
    top_models = candidates[:top_n]
    free_entries = [FreeEntry(id=m.id, name=m.name, intelligence_score=m.benchmarks.intelligence_score if m.benchmarks and m.benchmarks.intelligence else 0.0, context_length=m.context_length, throughput_tps=m.performance.throughput_tps if m.performance else None) for m in top_models]
    return Leaderboard(generated_at=generated_at, smartest=[], coding=[], free=free_entries, value=[])
```

---

## Feature Function: `generate_value_leaderboard`
**Logic & Purpose:**
```text
Generate leaderboard of top N value models (intelligence / prompt cost).

Excludes free models (they would have infinite ratio).
```

**Parameters:** `models, top_n, generated_at`
**Variables Used:** `candidates, top_models, value_entries, generated_at`
**Implementation:**
```python
def generate_value_leaderboard(models: List[Model], top_n: int=5, generated_at: Optional[str]=None) -> Leaderboard:
    """
    Generate leaderboard of top N value models (intelligence / prompt cost).

    Excludes free models (they would have infinite ratio).
    """
    if generated_at is None:
        generated_at = datetime.now(timezone.utc).isoformat()
    candidates = [m for m in models if not m.is_free and m.benchmarks and (m.benchmarks.intelligence_score is not None)]
    candidates.sort(key=lambda m: m.value_score, reverse=True)
    top_models = candidates[:top_n]
    value_entries = [ValueEntry(id=m.id, name=m.name, value_score=m.value_score, price_per_1m=m.pricing.prompt, intelligence_percentile=m.benchmarks.intelligence_percentile or 0.0) for m in top_models]
    return Leaderboard(generated_at=generated_at, smartest=[], coding=[], free=[], value=value_entries)
```

---

## Feature Function: `write_leaderboard`
**Logic & Purpose:**
```text
Write leaderboard to JSON file.

Args:
    leaderboard: Leaderboard object
    output_path: Destination file path
```

**Parameters:** `leaderboard, output_path`
**Variables Used:** `data`
**Implementation:**
```python
def write_leaderboard(leaderboard: Leaderboard, output_path: str) -> None:
    """
    Write leaderboard to JSON file.

    Args:
        leaderboard: Leaderboard object
        output_path: Destination file path
    """
    if len(leaderboard.smartest) < 3:
        logger.warning(f'Smartest leaderboard has only {len(leaderboard.smartest)} entries (<3)')
    if len(leaderboard.coding) < 3:
        logger.warning(f'Coding leaderboard has only {len(leaderboard.coding)} entries (<3)')
    if len(leaderboard.free) < 3:
        logger.warning(f'Free leaderboard has only {len(leaderboard.free)} entries (<3)')
    if len(leaderboard.value) < 3:
        logger.warning(f'Value leaderboard has only {len(leaderboard.value)} entries (<3)')
    data = leaderboard.model_dump(mode='json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
```

---

## Feature Function: `validate_lists`
**Logic & Purpose:**
```text
Validate leaderboard lists meet requirements.

Args:
    leaderboard: Leaderboard to validate

Raises:
    ValueError: If validation fails
```

**Parameters:** `leaderboard`
**Variables Used:** `ids, entries`
**Implementation:**
```python
def validate_lists(leaderboard: Leaderboard) -> None:
    """
    Validate leaderboard lists meet requirements.

    Args:
        leaderboard: Leaderboard to validate

    Raises:
        ValueError: If validation fails
    """
    for list_name in ['smartest', 'coding', 'free', 'value']:
        entries = getattr(leaderboard, list_name)
        ids = [e.id for e in entries]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate entries in {list_name} leaderboard')
```

---

## Feature Function: `write_leaderboard_csv`
**Logic & Purpose:**
```text
Write leaderboard to CSV file(s).

Creates separate CSV files for each leaderboard list:
- leaderboard_smartest.csv
- leaderboard_coding.csv
- leaderboard_free.csv
- leaderboard_value.csv

Args:
    leaderboard: Leaderboard object
    output_path: Base path (will append list name before extension)
```

**Parameters:** `leaderboard, output_path`
**Variables Used:** `writer, base, free_fields, stem, parent, coding_fields, smartest_fields, csv_path, value_fields, row`
**Implementation:**
```python
def write_leaderboard_csv(leaderboard: Leaderboard, output_path: str) -> None:
    """
    Write leaderboard to CSV file(s).
    
    Creates separate CSV files for each leaderboard list:
    - leaderboard_smartest.csv
    - leaderboard_coding.csv
    - leaderboard_free.csv
    - leaderboard_value.csv
    
    Args:
        leaderboard: Leaderboard object
        output_path: Base path (will append list name before extension)
    """
    import csv
    from pathlib import Path
    base = Path(output_path)
    stem = base.stem
    parent = base.parent
    smartest_fields = ['id', 'name', 'intelligence_score', 'percentile', 'price_per_1m']
    coding_fields = ['id', 'name', 'coding_score', 'agentic_score', 'price_per_1m']
    free_fields = ['id', 'name', 'intelligence_score', 'context_length', 'throughput_tps']
    value_fields = ['id', 'name', 'value_score', 'price_per_1m', 'intelligence_percentile']

    def write_csv(entries, fields, suffix):
        if not entries:
            logger.warning(f'No entries for {suffix}, skipping CSV')
            return
        csv_path = parent / f'{stem}_{suffix}.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for entry in entries:
                row = {field: getattr(entry, field, None) for field in fields}
                writer.writerow(row)
        logger.info(f'Wrote {len(entries)} rows to {csv_path}')
    write_csv(leaderboard.smartest, smartest_fields, 'smartest')
    write_csv(leaderboard.coding, coding_fields, 'coding')
    write_csv(leaderboard.free, free_fields, 'free')
    write_csv(leaderboard.value, value_fields, 'value')
```

---


