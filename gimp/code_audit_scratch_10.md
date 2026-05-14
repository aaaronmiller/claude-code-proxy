# File Audit: /home/cheta/code/claude-code-proxy/src/services/prompts/system_prompt_loader.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/prompts/system_prompt_loader.py`

**Module Overview**: 
```text
System prompt loader for custom model prompts.
Supports file-based loading and inline prompts.
```

## Dependencies & Imports
os, pathlib.Path, typing.Optional

## Feature Class: `SecurityError`
**Description:**
```text
Raised when a security violation is detected (e.g., path traversal).
```

---

## Feature Function: `load_system_prompt`
**Logic & Purpose:**
```text
Load system prompt from various sources.

Args:
    prompt_source: Can be:
        - "path:/path/to/file.txt" - Load from file
        - Direct text - Return as-is

Returns:
    The loaded prompt text

Raises:
    ValueError: If prompt_source is None
    FileNotFoundError: If file path doesn't exist
    RuntimeError: If file cannot be read
    SecurityError: If file path is unsafe (path traversal)
```

**Parameters:** `prompt_source`
**Variables Used:** `file_path, file_path_resolved, content, base_dir`
**Implementation:**
```python
def load_system_prompt(prompt_source: str) -> str:
    """
    Load system prompt from various sources.

    Args:
        prompt_source: Can be:
            - "path:/path/to/file.txt" - Load from file
            - Direct text - Return as-is

    Returns:
        The loaded prompt text

    Raises:
        ValueError: If prompt_source is None
        FileNotFoundError: If file path doesn't exist
        RuntimeError: If file cannot be read
        SecurityError: If file path is unsafe (path traversal)
    """
    if prompt_source is None:
        raise ValueError('prompt_source cannot be None')
    if not prompt_source:
        return ''
    if prompt_source.startswith('path:'):
        file_path = prompt_source[5:]
        try:
            base_dir = Path(__file__).parent.parent.parent.resolve()
            file_path_resolved = Path(file_path).resolve()
            file_path_resolved.relative_to(base_dir)
        except (ValueError, OSError) as e:
            raise SecurityError(f'Unsafe file path (path traversal attempt): {file_path}')
        try:
            with open(file_path_resolved, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 50000:
                    raise ValueError(f'System prompt too long ({len(content)} chars). Max 50,000 characters.')
                if len(content) < 3:
                    raise ValueError(f'System prompt too short ({len(content)} chars). Minimum 3 characters.')
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f'System prompt file not found: {file_path}')
        except UnicodeDecodeError as e:
            raise RuntimeError(f'File encoding error: {file_path}. Use UTF-8 encoding. {str(e)}')
        except Exception as e:
            raise RuntimeError(f'Error loading system prompt from {file_path}: {str(e)}')
    if len(prompt_source) > 50000:
        raise ValueError(f'Inline system prompt too long ({len(prompt_source)} chars). Max 50,000 characters.')
    if len(prompt_source) < 3 and len(prompt_source) > 0:
        raise ValueError(f'Inline system prompt too short ({len(prompt_source)} chars). Minimum 3 characters.')
    return prompt_source
```

---

## Feature Function: `get_model_system_prompt`
**Logic & Purpose:**
```text
Get the system prompt for a specific model size.

Args:
    model_size: "big", "middle", or "small"
    config: Configuration object

Returns:
    The system prompt text or None if not configured
```

**Parameters:** `model_size, config`
**Implementation:**
```python
def get_model_system_prompt(model_size: str, config) -> Optional[str]:
    """
    Get the system prompt for a specific model size.

    Args:
        model_size: "big", "middle", or "small"
        config: Configuration object

    Returns:
        The system prompt text or None if not configured
    """
    if model_size.lower() == 'big':
        if not config.enable_custom_big_prompt:
            return None
        if config.big_system_prompt_file:
            return load_system_prompt(f'path:{config.big_system_prompt_file}')
        if config.big_system_prompt:
            return load_system_prompt(config.big_system_prompt)
    elif model_size.lower() == 'middle':
        if not config.enable_custom_middle_prompt:
            return None
        if config.middle_system_prompt_file:
            return load_system_prompt(f'path:{config.middle_system_prompt_file}')
        if config.middle_system_prompt:
            return load_system_prompt(config.middle_system_prompt)
    elif model_size.lower() == 'small':
        if not config.enable_custom_small_prompt:
            return None
        if config.small_system_prompt_file:
            return load_system_prompt(f'path:{config.small_system_prompt_file}')
        if config.small_system_prompt:
            return load_system_prompt(config.small_system_prompt)
    return None
```

---

## Feature Function: `inject_system_prompt`
**Logic & Purpose:**
```text
Inject custom system prompt into messages if configured.

Args:
    messages: List of message dictionaries
    model_size: "big", "middle", or "small"
    config: Configuration object

Returns:
    Messages list with system prompt injected
```

**Parameters:** `messages, model_size, config`
**Variables Used:** `system_prompt, has_system`
**Implementation:**
```python
def inject_system_prompt(messages: list, model_size: str, config) -> list:
    """
    Inject custom system prompt into messages if configured.

    Args:
        messages: List of message dictionaries
        model_size: "big", "middle", or "small"
        config: Configuration object

    Returns:
        Messages list with system prompt injected
    """
    system_prompt = get_model_system_prompt(model_size, config)
    if not system_prompt:
        return messages
    has_system = any((msg.get('role') == 'system' for msg in messages))
    if has_system:
        for msg in messages:
            if msg.get('role') == 'system':
                msg['content'] = system_prompt
                break
    else:
        messages.insert(0, {'role': 'system', 'content': system_prompt})
    return messages
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/prompts/prompt_injection_middleware.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/prompts/prompt_injection_middleware.py`

**Module Overview**: 
```text
Prompt Injection Middleware

Automatically injects proxy status into Claude Code prompts
based on configuration and request patterns.
```

## Global Presets & Variables
- `prompt_injection_middleware` = `PromptInjectionMiddleware()`

## Dependencies & Imports
typing.Dict, typing.Any, typing.Optional, os, src.core.logging.logger

## Feature Class: `PromptInjectionMiddleware`
**Description:**
```text
Middleware to inject proxy status into requests
```

### Method: `__init__`
**Parameters:** `self`
**Variables Used:** `modules_str`
**Implementation:**
```python
def __init__(self):
    self.enabled = os.getenv('PROMPT_INJECTION_ENABLED', 'false').lower() == 'true'
    self.size = os.getenv('PROMPT_INJECTION_SIZE', 'medium')
    modules_str = os.getenv('PROMPT_INJECTION_MODULES', 'status,performance')
    self.modules = [m.strip() for m in modules_str.split(',') if m.strip()]
    self.inject_mode = os.getenv('PROMPT_INJECTION_MODE', 'auto')
```

### Method: `configure`
**Logic & Purpose:**
```text
Configure injection settings
```

**Parameters:** `self, enabled, size, modules, inject_mode`
**Implementation:**
```python
def configure(self, enabled: bool=True, size: str='medium', modules: list=None, inject_mode: str='auto'):
    """Configure injection settings"""
    self.enabled = enabled
    self.size = size
    if modules:
        self.modules = modules
    self.inject_mode = inject_mode
```

### Method: `should_inject`
**Logic & Purpose:**
```text
Determine if we should inject into this request
```

**Parameters:** `self, request`
**Variables Used:** `is_streaming, messages, has_tools, has_system`
**Implementation:**
```python
def should_inject(self, request: Dict[str, Any]) -> bool:
    """Determine if we should inject into this request"""
    if not self.enabled:
        return False
    if self.inject_mode == 'manual':
        return False
    if self.inject_mode == 'always':
        return True
    if self.inject_mode == 'header':
        return False
    messages = request.get('messages', [])
    if not messages:
        return False
    has_system = any((msg.get('role') == 'system' for msg in messages))
    has_tools = bool(request.get('tools'))
    is_streaming = request.get('stream', False)
    return has_system or has_tools or is_streaming
```

### Method: `inject_into_request`
**Logic & Purpose:**
```text
Inject proxy status into request messages
```

**Parameters:** `self, request`
**Variables Used:** `existing_content, messages, system_idx, injection`
**Implementation:**
```python
def inject_into_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Inject proxy status into request messages"""
    if not self.should_inject(request):
        return request
    try:
        from src.dashboard.prompt_modules import prompt_dashboard_renderer
        injection = prompt_dashboard_renderer.render(modules=self.modules, size=self.size)
        if not injection:
            return request
        injection = f'<!-- Proxy Status (auto-injected) -->\n{injection}'
        messages = request.get('messages', [])
        system_idx = None
        for i, msg in enumerate(messages):
            if msg.get('role') == 'system':
                system_idx = i
                break
        if system_idx is not None:
            existing_content = messages[system_idx].get('content', '')
            messages[system_idx]['content'] = f'{existing_content}\n\n{injection}'
        else:
            messages.insert(0, {'role': 'system', 'content': injection})
        request['messages'] = messages
        logger.debug(f'Injected proxy status ({self.size} size, {len(self.modules)} modules) into request')
    except Exception as e:
        logger.warning(f'Failed to inject proxy status: {e}')
    return request
```

### Method: `get_compact_header`
**Logic & Purpose:**
```text
Get ultra-compact header for all requests
```

**Parameters:** `self`
**Implementation:**
```python
def get_compact_header(self) -> str:
    """Get ultra-compact header for all requests"""
    try:
        from src.dashboard.prompt_modules import prompt_dashboard_renderer
        return prompt_dashboard_renderer.render_header(modules=self.modules, size='small')
    except Exception as e:
        logger.warning(f'Failed to generate compact header: {e}')
        return ''
```

### Method: `inject_into_system_prompt`
**Logic & Purpose:**
```text
Inject into existing system prompt string
```

**Parameters:** `self, system_prompt`
**Variables Used:** `injection`
**Implementation:**
```python
def inject_into_system_prompt(self, system_prompt: str) -> str:
    """Inject into existing system prompt string"""
    if not self.enabled:
        return system_prompt
    try:
        from src.dashboard.prompt_modules import prompt_dashboard_renderer
        injection = prompt_dashboard_renderer.render(modules=self.modules, size=self.size)
        if not injection:
            return system_prompt
        if system_prompt:
            return f'{system_prompt}\n\n<!-- Proxy Status -->\n{injection}'
        else:
            return f'<!-- Proxy Status -->\n{injection}'
    except Exception:
        return system_prompt
```

---

## Feature Function: `inject_system_prompts`
**Logic & Purpose:**
```text
Inject system prompts into a list of messages.
Wrapper for prompt_injection_middleware logic.
```

**Parameters:** `messages`
**Variables Used:** `request`
**Implementation:**
```python
def inject_system_prompts(messages: list) -> list:
    """
    Inject system prompts into a list of messages.
    Wrapper for prompt_injection_middleware logic.
    """
    request = {'messages': messages}
    if prompt_injection_middleware.should_inject(request):
        prompt_injection_middleware.inject_into_request(request)
        return request['messages']
    return messages
```

---

## Feature Function: `update_proxy_status`
**Logic & Purpose:**
```text
Update proxy status data for injection.
```

**Parameters:** `status_data`
**Implementation:**
```python
def update_proxy_status(status_data: Dict[str, Any]):
    """
    Update proxy status data for injection.
    """
    pass
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/prompts/templates.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/prompts/templates.py`

**Module Overview**: 
```text
Pre-built mode templates for quick setup.
```

## Dependencies & Imports
typing.Dict, typing.List, typing.Any

## Feature Class: `ModeTemplates`
**Description:**
```text
Pre-configured mode templates.
```

### Method: `get_template_names`
**Logic & Purpose:**
```text
Get list of all template names.
```

**Parameters:** `cls`
**Implementation:**
```python
@classmethod
def get_template_names(cls) -> List[str]:
    """Get list of all template names."""
    return list(cls.TEMPLATES.keys())
```

### Method: `get_template`
**Logic & Purpose:**
```text
Get a specific template by name.
```

**Parameters:** `cls, name`
**Implementation:**
```python
@classmethod
def get_template(cls, name: str) -> Dict[str, Any]:
    """Get a specific template by name."""
    return cls.TEMPLATES.get(name)
```

### Method: `list_templates`
**Logic & Purpose:**
```text
Get list of all templates with metadata.
```

**Parameters:** `cls`
**Implementation:**
```python
@classmethod
def list_templates(cls) -> List[Dict[str, Any]]:
    """Get list of all templates with metadata."""
    return [{'name': name, 'display_name': data['name'], 'description': data['description'], 'tags': data['tags']} for name, data in cls.TEMPLATES.items()]
```

### Method: `get_config`
**Logic & Purpose:**
```text
Get the configuration for a template.
```

**Parameters:** `cls, name`
**Variables Used:** `template`
**Implementation:**
```python
@classmethod
def get_config(cls, name: str) -> Dict[str, str]:
    """Get the configuration for a template."""
    template = cls.TEMPLATES.get(name)
    if template:
        return template['config']
    return None
```

### Method: `get_requirements`
**Logic & Purpose:**
```text
Get the requirements for a template.
```

**Parameters:** `cls, name`
**Variables Used:** `template`
**Implementation:**
```python
@classmethod
def get_requirements(cls, name: str) -> Dict[str, Any]:
    """Get the requirements for a template."""
    template = cls.TEMPLATES.get(name)
    if template:
        return template.get('requirements', {})
    return {}
```

---

## Feature Function: `get_available_templates`
**Logic & Purpose:**
```text
Get list of available template names.
```

**Parameters:** ``
**Implementation:**
```python
def get_available_templates() -> List[str]:
    """Get list of available template names."""
    return ModeTemplates.get_template_names()
```

---

## Feature Function: `get_template`
**Logic & Purpose:**
```text
Get template details by name.
```

**Parameters:** `name`
**Implementation:**
```python
def get_template(name: str) -> Dict[str, Any]:
    """Get template details by name."""
    return ModeTemplates.get_template(name)
```

---

## Feature Function: `apply_template`
**Logic & Purpose:**
```text
Get configuration for a template.
Returns the config dict if found, None otherwise.
```

**Parameters:** `name`
**Implementation:**
```python
def apply_template(name: str) -> Dict[str, str]:
    """
    Get configuration for a template.
    Returns the config dict if found, None otherwise.
    """
    return ModeTemplates.get_config(name)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/model_parser.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/model_parser.py`

**Module Overview**: 
```text
Model name parser utility for extracting reasoning parameters from model name suffixes.

Supports parsing model names with reasoning suffixes like:
- OpenAI o-series: o4-mini:high, o3:low
- Anthropic Claude: claude-opus-4-20250514:4k, claude-sonnet-4-20250514:8000
- Google Gemini: gemini-2.5-flash-preview-04-17:4k
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `K_NOTATION_MAP` = `{'1k': 1024, '4k': 4096, '8k': 8192, '16k': 16384, '24k': 24576}`
- `parse_model_id` = `parse_model_name`

## Dependencies & Imports
re, dataclasses.dataclass, typing.Optional, typing.Union, logging, src.core.reasoning_validator._is_openai_reasoning_model, src.core.reasoning_validator._is_anthropic_thinking_model, src.core.reasoning_validator._is_gemini_thinking_model

## Feature Class: `ParsedModel`
**Description:**
```text
Parsed model name with reasoning parameters.
```

---

## Feature Function: `_convert_k_notation`
**Logic & Purpose:**
```text
Convert k-notation to exact token count.

Args:
    value: String value like '1k', '4k', '8k', '16k'

Returns:
    Exact token count as integer

Raises:
    ValueError: If k-notation is not recognized
```

**Parameters:** `value`
**Variables Used:** `value_lower, num`
**Implementation:**
```python
def _convert_k_notation(value: str) -> int:
    """
    Convert k-notation to exact token count.

    Args:
        value: String value like '1k', '4k', '8k', '16k'

    Returns:
        Exact token count as integer

    Raises:
        ValueError: If k-notation is not recognized
    """
    value_lower = value.lower()
    if value_lower in K_NOTATION_MAP:
        return K_NOTATION_MAP[value_lower]
    if value_lower.endswith('k'):
        try:
            num = int(value_lower[:-1])
            return num * 1024
        except ValueError:
            pass
    raise ValueError(f'Invalid k-notation: {value}')
```

---

## Feature Function: `_detect_reasoning_type`
**Logic & Purpose:**
```text
Detect reasoning type based on model family and suffix.

Uses keyword-based detection from reasoning_validator so new model versions
are automatically supported without code changes.

Args:
    base_model: Base model name without suffix
    suffix: Optional suffix to help determine type

Returns:
    Reasoning type: 'effort', 'thinking_tokens', 'thinking_budget', or None
```

**Parameters:** `base_model, suffix`
**Variables Used:** `model_lower`
**Implementation:**
```python
def _detect_reasoning_type(base_model: str, suffix: Optional[str]=None) -> Optional[str]:
    """
    Detect reasoning type based on model family and suffix.

    Uses keyword-based detection from reasoning_validator so new model versions
    are automatically supported without code changes.

    Args:
        base_model: Base model name without suffix
        suffix: Optional suffix to help determine type

    Returns:
        Reasoning type: 'effort', 'thinking_tokens', 'thinking_budget', or None
    """
    model_lower = base_model.lower()
    if '/' in model_lower:
        model_lower = model_lower.split('/', 1)[1]
    if _is_openai_reasoning_model(model_lower):
        if suffix and suffix.isdigit():
            return 'thinking_tokens'
        return 'effort'
    elif _is_gemini_thinking_model(model_lower):
        return 'thinking_budget'
    elif _is_anthropic_thinking_model(model_lower):
        return 'thinking_tokens'
    return None
```

---

## Feature Function: `parse_model_name`
**Logic & Purpose:**
```text
Parse model name with optional reasoning suffix.

Suffix format: model_name:suffix

Handles hybrid tier/provider format:
- 'opus/qwen-2.5-72b' → base_model='qwen-2.5-72b' (tier prefix stripped)
- 'sonnet/openai/gpt-4o' → base_model='openai/gpt-4o' (tier prefix stripped)

Examples:
    'claude-opus-4-20250514:4k' → ParsedModel(
        base_model='claude-opus-4-20250514',
        reasoning_type='thinking_tokens',
        reasoning_value=4096,
        original_model='claude-opus-4-20250514:4k'
    )
    'o4-mini:high' → ParsedModel(
        base_model='o4-mini',
        reasoning_type='effort',
        reasoning_value='high',
        original_model='o4-mini:high'
    )
    'opus/qwen-2.5-72b' → ParsedModel(
        base_model='qwen-2.5-72b',
        reasoning_type=None,
        reasoning_value=None,
        original_model='opus/qwen-2.5-72b'
    )
    'gpt-4' → ParsedModel(
        base_model='gpt-4',
        reasoning_type=None,
        reasoning_value=None,
        original_model='gpt-4'
    )

Args:
    model_name: Model name with optional reasoning suffix

Returns:
    ParsedModel with extracted components
```

**Parameters:** `model_name`
**Variables Used:** `suffix, base_model, reasoning_type, parts, reasoning_value`
**Implementation:**
```python
def parse_model_name(model_name: str) -> ParsedModel:
    """
    Parse model name with optional reasoning suffix.

    Suffix format: model_name:suffix

    Handles hybrid tier/provider format:
    - 'opus/qwen-2.5-72b' → base_model='qwen-2.5-72b' (tier prefix stripped)
    - 'sonnet/openai/gpt-4o' → base_model='openai/gpt-4o' (tier prefix stripped)

    Examples:
        'claude-opus-4-20250514:4k' → ParsedModel(
            base_model='claude-opus-4-20250514',
            reasoning_type='thinking_tokens',
            reasoning_value=4096,
            original_model='claude-opus-4-20250514:4k'
        )
        'o4-mini:high' → ParsedModel(
            base_model='o4-mini',
            reasoning_type='effort',
            reasoning_value='high',
            original_model='o4-mini:high'
        )
        'opus/qwen-2.5-72b' → ParsedModel(
            base_model='qwen-2.5-72b',
            reasoning_type=None,
            reasoning_value=None,
            original_model='opus/qwen-2.5-72b'
        )
        'gpt-4' → ParsedModel(
            base_model='gpt-4',
            reasoning_type=None,
            reasoning_value=None,
            original_model='gpt-4'
        )

    Args:
        model_name: Model name with optional reasoning suffix

    Returns:
        ParsedModel with extracted components
    """
    suffix = None
    if ':' in model_name:
        model_name, suffix = model_name.rsplit(':', 1)
    base_model = model_name
    if '/' in model_name:
        parts = model_name.split('/', 1)
        if parts[0].lower() in ['opus', 'sonnet', 'haiku']:
            base_model = parts[1]
            logger.debug(f"Stripped tier prefix from '{model_name}' → base_model='{base_model}'")
    if not suffix:
        reasoning_type = _detect_reasoning_type(base_model)
        if reasoning_type:
            return ParsedModel(base_model=base_model, reasoning_type=None, reasoning_value=None, original_model=model_name + (f':{suffix}' if suffix else ''))
        return ParsedModel(base_model=base_model, reasoning_type=None, reasoning_value=None, original_model=model_name + (f':{suffix}' if suffix else ''))
    reasoning_type = _detect_reasoning_type(base_model, suffix)
    if not reasoning_type:
        logger.debug(f"Model {base_model} does not support reasoning parameters. Suffix '{suffix}' ignored.")
        return ParsedModel(base_model=base_model, reasoning_type=None, reasoning_value=None, original_model=model_name + (f':{suffix}' if suffix else ''))
    reasoning_value: Optional[Union[str, int]] = None
    try:
        if reasoning_type == 'effort':
            if suffix.isdigit():
                reasoning_value = int(suffix)
                reasoning_type = 'thinking_tokens'
            elif suffix.lower().endswith('k'):
                reasoning_value = _convert_k_notation(suffix)
                reasoning_type = 'thinking_tokens'
            else:
                reasoning_value = suffix.lower()
        elif reasoning_type in ('thinking_tokens', 'thinking_budget'):
            if suffix.lower().endswith('k'):
                reasoning_value = _convert_k_notation(suffix)
            else:
                reasoning_value = int(suffix)
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse reasoning suffix '{suffix}' for model {base_model}: {e}")
        return ParsedModel(base_model=base_model, reasoning_type=None, reasoning_value=None, original_model=model_name)
    logger.debug(f'Parsed model: {model_name} → base={base_model}, type={reasoning_type}, value={reasoning_value}')
    return ParsedModel(base_model=base_model, reasoning_type=reasoning_type, reasoning_value=reasoning_value, original_model=model_name)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/selection_history.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/selection_history.py`

**Module Overview**: 
```text
Tracks model selections from TUI/Web configuration flows.
```

## Global Presets & Variables
- `HISTORY_PATH` = `Path('data/model_selection_history.json')`

## Dependencies & Imports
__future__.annotations, json, dataclasses.dataclass, dataclasses.asdict, datetime.datetime, datetime.timezone, pathlib.Path, typing.List, typing.Optional

## Feature Class: `SelectionEvent`
---

## Feature Function: `_utc_now_iso`
**Parameters:** ``
**Implementation:**
```python
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
```

---

## Feature Function: `_load_raw`
**Parameters:** ``
**Implementation:**
```python
def _load_raw() -> dict:
    if not HISTORY_PATH.exists():
        return {'events': []}
    try:
        return json.loads(HISTORY_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {'events': []}
```

---

## Feature Function: `_save_raw`
**Parameters:** `data`
**Implementation:**
```python
def _save_raw(data: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(data, indent=2), encoding='utf-8')
```

---

## Feature Function: `record_selection`
**Parameters:** `slot, model_id, provider, source`
**Variables Used:** `event, data`
**Implementation:**
```python
def record_selection(slot: str, model_id: str, provider: Optional[str]=None, source: str='tui') -> None:
    data = _load_raw()
    event = SelectionEvent(timestamp=_utc_now_iso(), source=source, slot=slot, model_id=model_id, provider=provider)
    data.setdefault('events', []).append(asdict(event))
    data['events'] = data['events'][-500:]
    _save_raw(data)
```

---

## Feature Function: `get_recent_selections`
**Parameters:** `limit`
**Variables Used:** `rows, data`
**Implementation:**
```python
def get_recent_selections(limit: int=30) -> List[SelectionEvent]:
    data = _load_raw()
    rows = data.get('events', [])
    out: List[SelectionEvent] = []
    for row in rows[-limit:]:
        try:
            out.append(SelectionEvent(**row))
        except Exception:
            continue
    return list(reversed(out))
```

---

## Feature Function: `get_recent_models`
**Parameters:** `limit`
**Variables Used:** `seen`
**Implementation:**
```python
def get_recent_models(limit: int=30) -> List[str]:
    seen = set()
    result: List[str] = []
    for event in get_recent_selections(limit=200):
        if event.model_id in seen:
            continue
        seen.add(event.model_id)
        result.append(event.model_id)
        if len(result) >= limit:
            break
    return result
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/model_filter.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/model_filter.py`

**Module Overview**: 
```text
Smart model filtering for OpenRouter and other providers.
```

## Global Presets & Variables
- `model_filter` = `ModelFilter()`

## Dependencies & Imports
json, os, datetime.datetime, datetime.timedelta, typing.List, typing.Dict, typing.Set, pathlib.Path, src.services.models.free_model_rankings.get_top_free_models, src.services.models.selection_history.get_recent_models, src.services.models.model_family.detect_model_family, src.services.models.model_family.ModelFamily

## Feature Class: `ModelFilter`
**Description:**
```text
Filter and prioritize models based on usage, popularity, and cost.
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize model filter.

Args:
    usage_file: Path to file tracking model usage
```

**Parameters:** `self, usage_file`
**Implementation:**
```python
def __init__(self, usage_file: str='data/model_usage.json'):
    """
        Initialize model filter.

        Args:
            usage_file: Path to file tracking model usage
        """
    self.usage_file = Path(usage_file)
    self.usage_data = self._load_usage_data()
```

### Method: `_load_usage_data`
**Logic & Purpose:**
```text
Load model usage data from file.
```

**Parameters:** `self`
**Implementation:**
```python
def _load_usage_data(self) -> Dict:
    """Load model usage data from file."""
    if not self.usage_file.exists():
        return {'models': {}, 'last_updated': None}
    try:
        with open(self.usage_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {'models': {}, 'last_updated': None}
```

### Method: `_save_usage_data`
**Logic & Purpose:**
```text
Save model usage data to file.
```

**Parameters:** `self`
**Implementation:**
```python
def _save_usage_data(self):
    """Save model usage data to file."""
    try:
        self.usage_data['last_updated'] = datetime.now().isoformat()
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    except Exception:
        pass
```

### Method: `track_model_usage`
**Logic & Purpose:**
```text
Track that a model was used.

Args:
    model_name: Name of the model that was used
```

**Parameters:** `self, model_name`
**Variables Used:** `models`
**Implementation:**
```python
def track_model_usage(self, model_name: str):
    """
        Track that a model was used.

        Args:
            model_name: Name of the model that was used
        """
    models = self.usage_data.get('models', {})
    if model_name not in models:
        models[model_name] = {'count': 0, 'last_used': None, 'first_used': datetime.now().isoformat()}
    models[model_name]['count'] += 1
    models[model_name]['last_used'] = datetime.now().isoformat()
    self.usage_data['models'] = models
    self._save_usage_data()
```

### Method: `get_recently_used_models`
**Logic & Purpose:**
```text
Get most recently used models.

Args:
    limit: Maximum number of models to return

Returns:
    List of model names sorted by most recent usage
```

**Parameters:** `self, limit`
**Variables Used:** `models, sorted_models`
**Implementation:**
```python
def get_recently_used_models(self, limit: int=20) -> List[str]:
    """
        Get most recently used models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of model names sorted by most recent usage
        """
    models = self.usage_data.get('models', {})
    sorted_models = sorted(models.items(), key=lambda x: x[1].get('last_used', ''), reverse=True)
    return [model for model, _ in sorted_models[:limit]]
```

### Method: `get_most_used_models`
**Logic & Purpose:**
```text
Get most frequently used models.

Args:
    limit: Maximum number of models to return

Returns:
    List of model names sorted by usage count
```

**Parameters:** `self, limit`
**Variables Used:** `models, sorted_models`
**Implementation:**
```python
def get_most_used_models(self, limit: int=20) -> List[str]:
    """
        Get most frequently used models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of model names sorted by usage count
        """
    models = self.usage_data.get('models', {})
    sorted_models = sorted(models.items(), key=lambda x: x[1].get('count', 0), reverse=True)
    return [model for model, _ in sorted_models[:limit]]
```

### Method: `get_filtered_models`
**Logic & Purpose:**
```text
Get filtered list of models with Smart Sorting.

Sorting Order:
1. New & Free (The "Stealth" free models)
2. Recently Used (Your favorites)
3. Top Free (The best always-free ones)
4. Top Paid (High quality paid)
5. Others
```

**Parameters:** `self, all_models, include_free, include_top, include_recent, max_total`
**Variables Used:** `new_models, recent_models, merged_recent, dynamic_free, unique_models, free_models, usage_list, selection_list, top_models, rest_models`
**Implementation:**
```python
def get_filtered_models(self, all_models: List[str], include_free: bool=True, include_top: bool=True, include_recent: bool=True, max_total: int=100) -> List[str]:
    """
        Get filtered list of models with Smart Sorting.

        Sorting Order:
        1. New & Free (The "Stealth" free models)
        2. Recently Used (Your favorites)
        3. Top Free (The best always-free ones)
        4. Top Paid (High quality paid)
        5. Others
        """
    unique_models = set()
    new_models = []
    for model in self.NEW_MODELS:
        if model in all_models:
            new_models.append(model)
            unique_models.add(model)
    recent_models = []
    if include_recent:
        usage_list = self.get_recently_used_models(limit=10)
        selection_list = get_recent_models(limit=10)
        merged_recent = []
        for m in usage_list + selection_list:
            if m not in merged_recent:
                merged_recent.append(m)
        for model in usage_list:
            if model in all_models and model not in unique_models:
                recent_models.append(model)
                unique_models.add(model)
        for model in merged_recent:
            if model in all_models and model not in unique_models:
                recent_models.append(model)
                unique_models.add(model)
    free_models = []
    if include_free:
        dynamic_free = get_top_free_models(limit=40)
        for model in dynamic_free:
            if model in all_models and model not in unique_models:
                free_models.append(model)
                unique_models.add(model)
        for model in self.FREE_MODELS:
            if model in all_models and model not in unique_models:
                free_models.append(model)
                unique_models.add(model)
    top_models = []
    if include_top:
        for model in self.TOP_MODELS:
            if model in all_models and model not in unique_models:
                top_models.append(model)
                unique_models.add(model)
    rest_models = []
    if len(unique_models) < max_total:
        for model in all_models:
            if model not in unique_models:
                rest_models.append(model)
                unique_models.add(model)
                if len(unique_models) >= max_total:
                    break
    return new_models + recent_models + free_models + top_models + rest_models
```

### Method: `is_new_model`
**Logic & Purpose:**
```text
Check if model is considered 'new'.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def is_new_model(self, model_name: str) -> bool:
    """Check if model is considered 'new'."""
    return model_name in self.NEW_MODELS
```

### Method: `is_free_model`
**Logic & Purpose:**
```text
Check if a model is free.

Args:
    model_name: Model name to check

Returns:
    True if model is free
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def is_free_model(self, model_name: str) -> bool:
    """
        Check if a model is free.

        Args:
            model_name: Model name to check

        Returns:
            True if model is free
        """
    return model_name in self.FREE_MODELS
```

### Method: `is_top_model`
**Logic & Purpose:**
```text
Check if a model is in the top models list.

Args:
    model_name: Model name to check

Returns:
    True if model is a top model
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def is_top_model(self, model_name: str) -> bool:
    """
        Check if a model is in the top models list.

        Args:
            model_name: Model name to check

        Returns:
            True if model is a top model
        """
    return model_name in self.TOP_MODELS
```

### Method: `get_model_family`
**Logic & Purpose:**
```text
Get the model family for a model using dynamic detection.

Args:
    model_name: Model name to check

Returns:
    ModelFamily enum value
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def get_model_family(self, model_name: str) -> ModelFamily:
    """
        Get the model family for a model using dynamic detection.

        Args:
            model_name: Model name to check

        Returns:
            ModelFamily enum value
        """
    return detect_model_family(model_name).family
```

### Method: `is_anthropic_model`
**Logic & Purpose:**
```text
Check if model is Anthropic Claude family (dynamic detection).
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def is_anthropic_model(self, model_name: str) -> bool:
    """Check if model is Anthropic Claude family (dynamic detection)."""
    return self.get_model_family(model_name) == ModelFamily.ANTHROPIC_CLAUDE
```

### Method: `is_openai_model`
**Logic & Purpose:**
```text
Check if model is OpenAI family (GPT or O-series).
```

**Parameters:** `self, model_name`
**Variables Used:** `family`
**Implementation:**
```python
def is_openai_model(self, model_name: str) -> bool:
    """Check if model is OpenAI family (GPT or O-series)."""
    family = self.get_model_family(model_name)
    return family in (ModelFamily.OPENAI_GPT, ModelFamily.OPENAI_O_SERIES)
```

### Method: `is_gemini_model`
**Logic & Purpose:**
```text
Check if model is Google Gemini family.
```

**Parameters:** `self, model_name`
**Variables Used:** `family`
**Implementation:**
```python
def is_gemini_model(self, model_name: str) -> bool:
    """Check if model is Google Gemini family."""
    family = self.get_model_family(model_name)
    return family in (ModelFamily.GEMINI_FLASH, ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_OTHER)
```

### Method: `is_reasoning_model`
**Logic & Purpose:**
```text
Check if model supports reasoning/thinking (dynamic detection).
```

**Parameters:** `self, model_name`
**Variables Used:** `family`
**Implementation:**
```python
def is_reasoning_model(self, model_name: str) -> bool:
    """Check if model supports reasoning/thinking (dynamic detection)."""
    family = self.get_model_family(model_name)
    return family in (ModelFamily.OPENAI_O_SERIES, ModelFamily.ANTHROPIC_CLAUDE, ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_FLASH)
```

---

## Feature Function: `filter_models`
**Logic & Purpose:**
```text
Wrapper for model_filter.get_filtered_models
```

**Parameters:** `all_models`
**Implementation:**
```python
def filter_models(all_models: List[str], **kwargs) -> List[str]:
    """Wrapper for model_filter.get_filtered_models"""
    return model_filter.get_filtered_models(all_models, **kwargs)
```

---

## Feature Function: `get_available_models`
**Logic & Purpose:**
```text
Get all available models from OpenRouter/Providers.
This is a placeholder that should ideally call the client.
For now, returning the known top/free lists combined.
```

**Parameters:** ``
**Implementation:**
```python
def get_available_models() -> List[str]:
    """
    Get all available models from OpenRouter/Providers.
    This is a placeholder that should ideally call the client.
    For now, returning the known top/free lists combined.
    """
    return list(set(ModelFilter.TOP_MODELS + ModelFilter.FREE_MODELS))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/model_catalog.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/model_catalog.py`

**Module Overview**: 
```text
Model Catalog Service

Integrates model-scraper output with main proxy to provide:
- Curated model lists (free, smartest, coding, value)
- Recently used models from selection history
- Model specifications (context length, throughput, pricing)
- Daily usage tracking for cascade fallback

Usage:
    from src.services.models.model_catalog import model_catalog

    # Get curated lists
    free_models = model_catalog.get_models("free", limit=5)
    smartest = model_catalog.get_models("smartest", limit=5)

    # Get model specs
    specs = model_catalog.get_model_spec("openai/gpt-4o")

    # Get recent models
    recent = model_catalog.get_recent_models(limit=5)
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `MODELS_DIR` = `Path(__file__).parent.parent.parent / 'models'`
- `CATALOG_PATH` = `MODELS_DIR / 'model_catalog.json'`
- `USAGE_PATH` = `MODELS_DIR / 'daily_usage.json'`
- `DEFAULT_CATEGORIES` = `['free', 'smartest', 'coding', 'value']`
- `model_catalog` = `ModelCatalogService()`

## Dependencies & Imports
json, logging, dataclasses.dataclass, dataclasses.asdict, datetime.datetime, datetime.timezone, datetime.date, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Any, src.services.models.selection_history.get_recent_models

## Feature Class: `ModelSpec`
**Description:**
```text
Specification for a model.
```

---

## Feature Class: `ModelCatalog`
**Description:**
```text
Model catalog with curated lists.
```

### Method: `from_dict`
**Logic & Purpose:**
```text
Create from dictionary.
```

**Parameters:** `cls, data`
**Variables Used:** `spec, all_models`
**Implementation:**
```python
@classmethod
def from_dict(cls, data: dict) -> 'ModelCatalog':
    """Create from dictionary."""
    all_models = {}
    for model_list in data.get('models', {}).values():
        for m in model_list:
            spec = ModelSpec(id=m.get('id', ''), name=m.get('name', m.get('id', '')), provider=m.get('id', '').split('/')[0] if '/' in m.get('id', '') else 'unknown', context_length=m.get('context_length', 128000), max_output=m.get('max_output', 4096), price_per_1m_input=m.get('price_per_1m_input', 0.0), price_per_1m_output=m.get('price_per_1m_output', 0.0), throughput_tps=m.get('throughput_tps'), intelligence_score=m.get('intelligence_score'), is_free=m.get('is_free', ':free' in m.get('id', '').lower()), category=m.get('category'))
            all_models[spec.id] = spec
    return cls(generated_at=data.get('generated_at', ''), models=data.get('models', {}), all_models=all_models)
```

---

## Feature Class: `ModelCatalogService`
**Description:**
```text
Service for managing model catalog.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self._catalog: Optional[ModelCatalog] = None
    self._daily_usage: Dict[str, Dict[str, int]] = {}
    self._load()
```

### Method: `_load`
**Logic & Purpose:**
```text
Load catalog and usage data.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def _load(self):
    """Load catalog and usage data."""
    if CATALOG_PATH.exists():
        try:
            data = json.loads(CATALOG_PATH.read_text())
            self._catalog = ModelCatalog.from_dict(data)
            logger.info(f'Loaded model catalog from {CATALOG_PATH}')
        except Exception as e:
            logger.warning(f'Failed to load catalog: {e}')
            self._catalog = None
    if USAGE_PATH.exists():
        try:
            self._daily_usage = json.loads(USAGE_PATH.read_text())
        except Exception as e:
            logger.warning(f'Failed to load daily usage: {e}')
            self._daily_usage = {}
```

### Method: `_save`
**Logic & Purpose:**
```text
Save catalog and usage data.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def _save(self):
    """Save catalog and usage data."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if self._catalog:
        data = {'generated_at': self._catalog.generated_at, 'models': self._catalog.models, 'all_models': {k: asdict(v) for k, v in self._catalog.all_models.items()}}
        CATALOG_PATH.write_text(json.dumps(data, indent=2))
    USAGE_PATH.write_text(json.dumps(self._daily_usage, indent=2))
```

### Method: `reload`
**Logic & Purpose:**
```text
Reload catalog from disk.
```

**Parameters:** `self`
**Implementation:**
```python
def reload(self):
    """Reload catalog from disk."""
    self._load()
```

### Method: `get_models`
**Logic & Purpose:**
```text
Get models from a specific category.
```

**Parameters:** `self, category, limit`
**Variables Used:** `model_id, models, result`
**Implementation:**
```python
def get_models(self, category: str, limit: int=5) -> List[ModelSpec]:
    """Get models from a specific category."""
    if not self._catalog:
        return self._get_default_models(category, limit)
    models = self._catalog.models.get(category, [])
    result = []
    for m in models[:limit]:
        model_id = m.get('id', '')
        if model_id in self._catalog.all_models:
            result.append(self._catalog.all_models[model_id])
        else:
            result.append(ModelSpec(id=model_id, name=m.get('name', model_id), provider=model_id.split('/')[0] if '/' in model_id else 'unknown', context_length=m.get('context_length', 128000), max_output=m.get('max_output', 4096), is_free=':free' in model_id.lower()))
    return result
```

### Method: `get_all_curated`
**Logic & Purpose:**
```text
Get all curated models organized by category.
```

**Parameters:** `self, limit_per_category`
**Implementation:**
```python
def get_all_curated(self, limit_per_category: int=5) -> Dict[str, List[ModelSpec]]:
    """Get all curated models organized by category."""
    return {category: self.get_models(category, limit_per_category) for category in DEFAULT_CATEGORIES}
```

### Method: `get_recent_models`
**Logic & Purpose:**
```text
Get recently used models from selection history.
```

**Parameters:** `self, limit`
**Variables Used:** `result, recent_ids`
**Implementation:**
```python
def get_recent_models(self, limit: int=5) -> List[ModelSpec]:
    """Get recently used models from selection history."""
    recent_ids = get_recent_models(limit=limit)
    if not self._catalog:
        return [ModelSpec(id=mid, name=mid, provider=mid.split('/')[0] if '/' in mid else 'unknown') for mid in recent_ids]
    result = []
    for mid in recent_ids:
        if mid in self._catalog.all_models:
            result.append(self._catalog.all_models[mid])
        else:
            result.append(ModelSpec(id=mid, name=mid, provider=mid.split('/')[0] if '/' in mid else 'unknown'))
    return result
```

### Method: `get_model_spec`
**Logic & Purpose:**
```text
Get specifications for a specific model.
```

**Parameters:** `self, model_id`
**Implementation:**
```python
def get_model_spec(self, model_id: str) -> Optional[ModelSpec]:
    """Get specifications for a specific model."""
    if not self._catalog:
        return ModelSpec(id=model_id, name=model_id, provider=model_id.split('/')[0] if '/' in model_id else 'unknown', context_length=128000, max_output=4096)
    return self._catalog.all_models.get(model_id)
```

### Method: `get_all_models`
**Logic & Purpose:**
```text
Get all available models.
```

**Parameters:** `self`
**Implementation:**
```python
def get_all_models(self) -> List[ModelSpec]:
    """Get all available models."""
    if not self._catalog:
        return []
    return list(self._catalog.all_models.values())
```

### Method: `search_models`
**Logic & Purpose:**
```text
Search models by name or ID.
```

**Parameters:** `self, query, limit`
**Variables Used:** `results, query_lower`
**Implementation:**
```python
def search_models(self, query: str, limit: int=20) -> List[ModelSpec]:
    """Search models by name or ID."""
    if not self._catalog:
        return []
    query_lower = query.lower()
    results = []
    for spec in self._catalog.all_models.values():
        if query_lower in spec.id.lower() or query_lower in spec.name.lower():
            results.append(spec)
        if len(results) >= limit:
            break
    return results
```

### Method: `_get_default_models`
**Logic & Purpose:**
```text
Get default models when catalog is not available.
```

**Parameters:** `self, category, limit`
**Variables Used:** `model_ids, defaults`
**Implementation:**
```python
def _get_default_models(self, category: str, limit: int) -> List[ModelSpec]:
    """Get default models when catalog is not available."""
    defaults = {'free': ['minimax/minimax-m2.5:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'nvidia/nemotron-nano-9b-v2:free', 'qwen/qwen3-next-80b-a3b-instruct:free', 'openrouter/free'], 'smartest': ['anthropic/claude-3.5-sonnet-20241022', 'openai/gpt-4o', 'google/gemini-2.5-pro-preview-05-20', 'anthropic/claude-3-opus-20240229', 'meta-llama/llama-3.3-70b-instruct'], 'coding': ['anthropic/claude-3.5-sonnet-20241022', 'deepseek/deepseek-coder', 'openai/gpt-4o', 'qwen/qwen-2.5-coder-32b-instruct', 'openai/o1-mini'], 'value': ['openai/gpt-4o-mini', 'anthropic/claude-3.5-haiku-20240307', 'google/gemini-2.0-flash-exp:free', 'mistralai/mistral-small', 'cohere/command-r-plus']}
    model_ids = defaults.get(category, defaults['smartest'])[:limit]
    return [ModelSpec(id=mid, name=mid, provider=mid.split('/')[0] if '/' in mid else 'unknown', context_length=128000, max_output=4096, is_free=':free' in mid.lower()) for mid in model_ids]
```

### Method: `_get_today_key`
**Logic & Purpose:**
```text
Get today's date key.
```

**Parameters:** `self`
**Implementation:**
```python
def _get_today_key(self) -> str:
    """Get today's date key."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')
```

### Method: `record_request`
**Logic & Purpose:**
```text
Record a request to a model for today.
```

**Parameters:** `self, model_id`
**Variables Used:** `today`
**Implementation:**
```python
def record_request(self, model_id: str):
    """Record a request to a model for today."""
    today = self._get_today_key()
    if today not in self._daily_usage:
        self._daily_usage = {k: v for k, v in self._daily_usage.items() if k >= self._get_week_ago()}
        self._daily_usage[today] = {}
    self._daily_usage[today][model_id] = self._daily_usage[today].get(model_id, 0) + 1
    self._save()
```

### Method: `get_daily_usage`
**Logic & Purpose:**
```text
Get today's request count for a model.
```

**Parameters:** `self, model_id`
**Variables Used:** `today`
**Implementation:**
```python
def get_daily_usage(self, model_id: str) -> int:
    """Get today's request count for a model."""
    today = self._get_today_key()
    return self._daily_usage.get(today, {}).get(model_id, 0)
```

### Method: `is_at_limit`
**Logic & Purpose:**
```text
Check if model has hit daily limit.
```

**Parameters:** `self, model_id, limit`
**Implementation:**
```python
def is_at_limit(self, model_id: str, limit: int=1000) -> bool:
    """Check if model has hit daily limit."""
    return self.get_daily_usage(model_id) >= limit
```

### Method: `get_cascade_next`
**Logic & Purpose:**
```text
Get the next model in cascade if current is at limit.

Args:
    model_id: Current model ID
    cascade_list: List of models to cascade through (in order of preference)
    limit: Daily limit threshold

Returns:
    Next model ID if current is at limit, None otherwise
```

**Parameters:** `self, model_id, cascade_list, limit`
**Variables Used:** `current_idx`
**Implementation:**
```python
def get_cascade_next(self, model_id: str, cascade_list: List[str], limit: int=1000) -> Optional[str]:
    """
        Get the next model in cascade if current is at limit.

        Args:
            model_id: Current model ID
            cascade_list: List of models to cascade through (in order of preference)
            limit: Daily limit threshold

        Returns:
            Next model ID if current is at limit, None otherwise
        """
    if model_id not in cascade_list:
        return cascade_list[0] if cascade_list else None
    current_idx = cascade_list.index(model_id)
    for i, candidate in enumerate(cascade_list[current_idx:], start=current_idx):
        if i == current_idx:
            continue
        if not self.is_at_limit(candidate, limit):
            return candidate
    return None
```

### Method: `_get_week_ago`
**Logic & Purpose:**
```text
Get date key for 7 days ago.
```

**Parameters:** `self`
**Variables Used:** `week_ago`
**Implementation:**
```python
def _get_week_ago(self) -> str:
    """Get date key for 7 days ago."""
    from datetime import timedelta
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    return week_ago.strftime('%Y-%m-%d')
```

### Method: `get_usage_stats`
**Logic & Purpose:**
```text
Get usage stats for the last N days.
```

**Parameters:** `self, days`
**Variables Used:** `stats, cutoff`
**Implementation:**
```python
def get_usage_stats(self, days: int=7) -> Dict[str, int]:
    """Get usage stats for the last N days."""
    stats = {}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    for day, models in self._daily_usage.items():
        if day >= cutoff:
            for model_id, count in models.items():
                stats[model_id] = stats.get(model_id, 0) + count
    return stats
```

### Method: `get_all_lists`
**Logic & Purpose:**
```text
Get all curated lists plus recent models for UI display.
```

**Parameters:** `self`
**Variables Used:** `result`
**Implementation:**
```python
def get_all_lists(self) -> Dict[str, List[ModelSpec]]:
    """Get all curated lists plus recent models for UI display."""
    result = self.get_all_curated(limit=5)
    result['recent'] = self.get_recent_models(limit=5)
    return result
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/openrouter_fetcher.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/openrouter_fetcher.py`

**Module Overview**: 
```text
OpenRouter Model Fetcher with Auto-Refresh

Fetches models from OpenRouter API on startup (with caching) and provides
model data for TUI and WebUI model selectors.

Features:
- Auto-refresh on startup if cache is stale
- Configurable cache TTL (default 24 hours)
- Fallback to cached data on network failure
- JSON and CSV storage formats
- Rich model metadata extraction
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `DEFAULT_CACHE_TTL_HOURS` = `24`
- `OPENROUTER_API_URL` = `'https://openrouter.ai/api/v1/models'`

## Dependencies & Imports
asyncio, csv, httpx, json, os, datetime.datetime, datetime.timedelta, pathlib.Path, typing.Dict, typing.List, typing.Any, typing.Optional, typing.Tuple, logging, openrouter_enricher.enrich_model

## Feature Function: `get_data_dir`
**Logic & Purpose:**
```text
Get the data directory for storing model files.
```

**Parameters:** ``
**Variables Used:** `data_dir, project_root`
**Implementation:**
```python
def get_data_dir() -> Path:
    """Get the data directory for storing model files."""
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
```

---

## Feature Function: `get_cache_paths`
**Logic & Purpose:**
```text
Get paths for JSON and CSV cache files.
```

**Parameters:** ``
**Variables Used:** `data_dir`
**Implementation:**
```python
def get_cache_paths() -> Tuple[Path, Path]:
    """Get paths for JSON and CSV cache files."""
    data_dir = get_data_dir()
    return (data_dir / 'openrouter_models.json', data_dir / 'openrouter_models.csv')
```

---

## Feature Function: `is_cache_stale`
**Logic & Purpose:**
```text
Check if cache file is stale (older than TTL).
```

**Parameters:** `cache_path, ttl_hours`
**Variables Used:** `age, mtime`
**Implementation:**
```python
def is_cache_stale(cache_path: Path, ttl_hours: int=DEFAULT_CACHE_TTL_HOURS) -> bool:
    """Check if cache file is stale (older than TTL)."""
    if not cache_path.exists():
        return True
    try:
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age > timedelta(hours=ttl_hours)
    except Exception:
        return True
```

---

## Feature Function: `load_cached_models`
**Logic & Purpose:**
```text
Load models from cache file.
```

**Parameters:** ``
**Implementation:**
```python
def load_cached_models() -> Optional[Dict[str, Any]]:
    """Load models from cache file."""
    json_path, _ = get_cache_paths()
    if not json_path.exists():
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f'Failed to load cached models: {e}')
        return None
```

---

## Feature Function: `save_models_json`
**Logic & Purpose:**
```text
Save models to JSON file.
```

**Parameters:** `data, path`
**Implementation:**
```python
def save_models_json(data: Dict[str, Any], path: Path):
    """Save models to JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data.get('models', []))} models to {path}")
```

---

## Feature Function: `save_models_csv`
**Logic & Purpose:**
```text
Save models to CSV file for easy import into spreadsheets.
```

**Parameters:** `models, path`
**Variables Used:** `writer, fieldnames, row`
**Implementation:**
```python
def save_models_csv(models: List[Dict[str, Any]], path: Path):
    """Save models to CSV file for easy import into spreadsheets."""
    if not models:
        return
    fieldnames = ['id', 'name', 'provider', 'description', 'context_length', 'max_completion_tokens', 'input_price_per_million', 'output_price_per_million', 'is_free', 'supports_reasoning', 'supports_tools', 'supports_vision', 'supports_audio', 'supports_files', 'modality', 'input_modalities', 'output_modalities', 'tokenizer', 'is_moderated', 'created']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for model in models:
            row = {'id': model.get('id', ''), 'name': model.get('name', ''), 'provider': model.get('provider', ''), 'description': model.get('description', '')[:200], 'context_length': model.get('context_length', 0), 'max_completion_tokens': model.get('max_completion_tokens', 0), 'input_price_per_million': model.get('pricing', {}).get('input_per_million', 0), 'output_price_per_million': model.get('pricing', {}).get('output_per_million', 0), 'is_free': model.get('pricing', {}).get('is_free', False), 'supports_reasoning': model.get('supports_reasoning', False), 'supports_tools': model.get('supports_tools', False), 'supports_vision': model.get('supports_vision', False), 'supports_audio': model.get('supports_audio', False), 'supports_files': model.get('supports_files', False), 'modality': model.get('modality', ''), 'input_modalities': ','.join(model.get('input_modalities', [])), 'output_modalities': ','.join(model.get('output_modalities', [])), 'tokenizer': model.get('tokenizer', ''), 'is_moderated': model.get('is_moderated', False), 'created': model.get('created', 0)}
            writer.writerow(row)
    logger.info(f'Saved {len(models)} models to {path}')
```

---

## Feature Function: `fetch_openrouter_models`
**Logic & Purpose:**
```text
Fetch models from OpenRouter API.

Args:
    api_key: Optional OpenRouter API key (allows viewing more models)
    timeout: Request timeout in seconds

Returns:
    Tuple of (models list, error message or None)
```

**Parameters:** `api_key, timeout`
**Variables Used:** `headers, models, response, data`
**Implementation:**
```python
async def fetch_openrouter_models(api_key: Optional[str]=None, timeout: float=30.0) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetch models from OpenRouter API.

    Args:
        api_key: Optional OpenRouter API key (allows viewing more models)
        timeout: Request timeout in seconds

    Returns:
        Tuple of (models list, error message or None)
    """
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(OPENROUTER_API_URL, headers=headers)
            if response.status_code != 200:
                return ([], f'HTTP {response.status_code}: {response.text[:100]}')
            data = response.json()
            models = data.get('data', [])
            if not models:
                return ([], 'No models returned from API')
            return (models, None)
    except httpx.TimeoutException:
        return ([], 'Request timed out')
    except httpx.ConnectError as e:
        return ([], f'Connection failed: {str(e)}')
    except Exception as e:
        return ([], f'Error: {str(e)}')
```

---

## Feature Function: `enrich_and_process_models`
**Logic & Purpose:**
```text
Enrich raw models and compute statistics.

Returns:
    Dict with models list and stats
```

**Parameters:** `raw_models`
**Variables Used:** `stats, enriched, enriched_model, provider`
**Implementation:**
```python
def enrich_and_process_models(raw_models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enrich raw models and compute statistics.

    Returns:
        Dict with models list and stats
    """
    enriched = []
    stats = {'total': len(raw_models), 'free': 0, 'reasoning': 0, 'vision': 0, 'tools': 0, 'by_provider': {}}
    for model in raw_models:
        enriched_model = enrich_model(model)
        enriched.append(enriched_model)
        provider = enriched_model['provider']
        stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1
        if enriched_model['pricing']['is_free']:
            stats['free'] += 1
        if enriched_model['supports_reasoning']:
            stats['reasoning'] += 1
        if enriched_model['supports_vision']:
            stats['vision'] += 1
        if enriched_model['supports_tools']:
            stats['tools'] += 1
    enriched.sort(key=lambda m: (m['provider'], m['name']))
    return {'fetched_at': datetime.now().isoformat(), 'source': OPENROUTER_API_URL, 'stats': stats, 'models': enriched}
```

---

## Feature Function: `refresh_openrouter_models`
**Logic & Purpose:**
```text
Refresh OpenRouter models, using cache if valid.

Args:
    force: Force refresh even if cache is valid
    ttl_hours: Cache TTL in hours

Returns:
    Tuple of (models data, was_refreshed, error message or None)
```

**Parameters:** `force, ttl_hours`
**Variables Used:** `cached, data, api_key`
**Implementation:**
```python
async def refresh_openrouter_models(force: bool=False, ttl_hours: int=DEFAULT_CACHE_TTL_HOURS) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Refresh OpenRouter models, using cache if valid.

    Args:
        force: Force refresh even if cache is valid
        ttl_hours: Cache TTL in hours

    Returns:
        Tuple of (models data, was_refreshed, error message or None)
    """
    json_path, csv_path = get_cache_paths()
    if not force and (not is_cache_stale(json_path, ttl_hours)):
        cached = load_cached_models()
        if cached:
            logger.info(f"Using cached models ({len(cached.get('models', []))} models)")
            return (cached, False, None)
    api_key = os.environ.get('OPENROUTER_API_KEY')
    logger.info('Fetching models from OpenRouter API...')
    raw_models, error = await fetch_openrouter_models(api_key)
    if error:
        cached = load_cached_models()
        if cached:
            logger.warning(f'API fetch failed ({error}), using cached data')
            return (cached, False, error)
        return ({'models': [], 'stats': {}}, False, error)
    data = enrich_and_process_models(raw_models)
    save_models_json(data, json_path)
    save_models_csv(data['models'], csv_path)
    logger.info(f"Refreshed {len(data['models'])} models from OpenRouter")
    return (data, True, None)
```

---

## Feature Function: `refresh_openrouter_models_sync`
**Logic & Purpose:**
```text
Synchronous wrapper for refresh_openrouter_models.

For use in non-async contexts (startup, CLI).
```

**Parameters:** `force, ttl_hours`
**Variables Used:** `loop`
**Implementation:**
```python
def refresh_openrouter_models_sync(force: bool=False, ttl_hours: int=DEFAULT_CACHE_TTL_HOURS) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """
    Synchronous wrapper for refresh_openrouter_models.

    For use in non-async contexts (startup, CLI).
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(refresh_openrouter_models(force, ttl_hours))
```

---

## Feature Function: `get_models`
**Logic & Purpose:**
```text
Get cached models list.

Returns empty list if no cache available.
```

**Parameters:** ``
**Variables Used:** `cached`
**Implementation:**
```python
def get_models() -> List[Dict[str, Any]]:
    """
    Get cached models list.

    Returns empty list if no cache available.
    """
    cached = load_cached_models()
    if cached:
        return cached.get('models', [])
    return []
```

---

## Feature Function: `get_model_by_id`
**Logic & Purpose:**
```text
Get a specific model by ID.
```

**Parameters:** `model_id`
**Variables Used:** `models`
**Implementation:**
```python
def get_model_by_id(model_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific model by ID."""
    models = get_models()
    for model in models:
        if model.get('id') == model_id:
            return model
    return None
```

---

## Feature Function: `filter_models`
**Logic & Purpose:**
```text
Filter models by various criteria.

Args:
    provider: Filter by provider name
    supports_reasoning: Filter by reasoning support
    supports_vision: Filter by vision support
    supports_tools: Filter by tool use support
    is_free: Filter by free pricing
    min_context: Minimum context length
    search: Search in model ID and name

Returns:
    Filtered list of models
```

**Parameters:** `provider, supports_reasoning, supports_vision, supports_tools, is_free, min_context, search`
**Variables Used:** `model_name, result, model_id, models, search_lower`
**Implementation:**
```python
def filter_models(provider: Optional[str]=None, supports_reasoning: Optional[bool]=None, supports_vision: Optional[bool]=None, supports_tools: Optional[bool]=None, is_free: Optional[bool]=None, min_context: Optional[int]=None, search: Optional[str]=None) -> List[Dict[str, Any]]:
    """
    Filter models by various criteria.

    Args:
        provider: Filter by provider name
        supports_reasoning: Filter by reasoning support
        supports_vision: Filter by vision support
        supports_tools: Filter by tool use support
        is_free: Filter by free pricing
        min_context: Minimum context length
        search: Search in model ID and name

    Returns:
        Filtered list of models
    """
    models = get_models()
    result = []
    for model in models:
        if provider and model.get('provider', '').lower() != provider.lower():
            continue
        if supports_reasoning is not None and model.get('supports_reasoning') != supports_reasoning:
            continue
        if supports_vision is not None and model.get('supports_vision') != supports_vision:
            continue
        if supports_tools is not None and model.get('supports_tools') != supports_tools:
            continue
        if is_free is not None and model.get('pricing', {}).get('is_free') != is_free:
            continue
        if min_context and model.get('context_length', 0) < min_context:
            continue
        if search:
            search_lower = search.lower()
            model_id = model.get('id', '').lower()
            model_name = model.get('name', '').lower()
            if search_lower not in model_id and search_lower not in model_name:
                continue
        result.append(model)
    return result
```

---

## Feature Function: `get_model_stats`
**Logic & Purpose:**
```text
Get statistics about cached models.
```

**Parameters:** ``
**Variables Used:** `cached`
**Implementation:**
```python
def get_model_stats() -> Dict[str, Any]:
    """Get statistics about cached models."""
    cached = load_cached_models()
    if cached:
        return cached.get('stats', {})
    return {}
```

---

## Feature Function: `startup_refresh`
**Logic & Purpose:**
```text
Called on proxy startup to refresh models if needed.

Respects OPENROUTER_AUTO_REFRESH env var (default: true).
```

**Parameters:** ``
**Variables Used:** `ttl_hours, auto_refresh`
**Implementation:**
```python
def startup_refresh():
    """
    Called on proxy startup to refresh models if needed.

    Respects OPENROUTER_AUTO_REFRESH env var (default: true).
    """
    auto_refresh = os.environ.get('OPENROUTER_AUTO_REFRESH', 'true').lower() == 'true'
    if not auto_refresh:
        logger.info('OpenRouter auto-refresh disabled')
        return
    ttl_hours = int(os.environ.get('OPENROUTER_CACHE_TTL_HOURS', str(DEFAULT_CACHE_TTL_HOURS)))
    try:
        data, was_refreshed, error = refresh_openrouter_models_sync(force=False, ttl_hours=ttl_hours)
        if was_refreshed:
            print(f"✅ Refreshed {len(data.get('models', []))} models from OpenRouter")
        elif error:
            print(f'⚠️  OpenRouter refresh failed: {error}')
            if data.get('models'):
                print(f"   Using cached data ({len(data['models'])} models)")
        else:
            print(f"📦 Using cached OpenRouter models ({len(data.get('models', []))} models)")
    except Exception as e:
        logger.error(f'OpenRouter startup refresh failed: {e}')
        print(f'⚠️  OpenRouter model fetch failed: {e}')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/free_model_rankings.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/free_model_rankings.py`

**Module Overview**: 
```text
Dynamic ranking and classification for OpenRouter free models.
```

## Global Presets & Variables
- `DEFAULT_STEALTH_WINDOW_DAYS` = `30`
- `RANKINGS_PATH` = `Path('data/free_model_rankings.json')`

## Dependencies & Imports
__future__.annotations, json, math, dataclasses.dataclass, dataclasses.asdict, datetime.datetime, datetime.timezone, pathlib.Path, typing.Any, typing.Dict, typing.List, typing.Optional, src.services.models.openrouter_fetcher.get_models

## Feature Class: `FreeModelRanking`
---

## Feature Function: `_utc_now`
**Parameters:** ``
**Implementation:**
```python
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
```

---

## Feature Function: `_age_days`
**Parameters:** `created_epoch`
**Variables Used:** `created`
**Implementation:**
```python
def _age_days(created_epoch: int) -> int:
    if not created_epoch:
        return 9999
    created = datetime.fromtimestamp(created_epoch, tz=timezone.utc)
    return max(0, (_utc_now() - created).days)
```

---

## Feature Function: `_score_model`
**Parameters:** `model, stealth_window_days`
**Variables Used:** `score, context, model_id, age_days, reasoning, recency, structured, created, max_out, out_score, provider, tools, class_type, capability, context_score`
**Implementation:**
```python
def _score_model(model: Dict[str, Any], stealth_window_days: int) -> FreeModelRanking:
    model_id = model.get('id', '')
    created = int(model.get('created', 0) or 0)
    context = int(model.get('context_length', 0) or 0)
    max_out = int(model.get('max_completion_tokens', 0) or 0)
    tools = bool(model.get('supports_tools', False))
    reasoning = bool(model.get('supports_reasoning', False))
    structured = bool(model.get('supports_structured_output', False))
    provider = str(model.get('provider', 'unknown') or 'unknown')
    age_days = _age_days(created)
    class_type = 'stealth_free' if age_days <= stealth_window_days else 'evergreen_free'
    capability = 0.0
    capability += 14.0 if tools else 0.0
    capability += 8.0 if reasoning else 0.0
    capability += 3.0 if structured else 0.0
    context_score = min(20.0, 20.0 * math.log10(max(context, 1024)) / math.log10(256000))
    out_score = min(12.0, 12.0 * math.log10(max(max_out, 512)) / math.log10(65536))
    if age_days <= stealth_window_days:
        recency = 20.0 * (1.0 - age_days / max(1, stealth_window_days))
    else:
        recency = 3.0
    score = round(min(100.0, capability + context_score + out_score + recency), 2)
    return FreeModelRanking(model_id=model_id, provider=provider, age_days=age_days, class_type=class_type, context_length=context, max_completion_tokens=max_out, supports_tools=tools, supports_reasoning=reasoning, supports_structured_output=structured, score=score, created=created)
```

---

## Feature Function: `build_free_model_rankings`
**Logic & Purpose:**
```text
Build ranked list for free models only.
```

**Parameters:** `models, stealth_window_days`
**Variables Used:** `free_models, source, ranked`
**Implementation:**
```python
def build_free_model_rankings(models: Optional[List[Dict[str, Any]]]=None, stealth_window_days: int=DEFAULT_STEALTH_WINDOW_DAYS) -> List[FreeModelRanking]:
    """Build ranked list for free models only."""
    source = models if models is not None else get_models()
    free_models = [m for m in source if m.get('pricing', {}).get('is_free', False)]
    ranked = [_score_model(m, stealth_window_days) for m in free_models]
    ranked.sort(key=lambda r: (r.score, -r.context_length, -r.max_completion_tokens), reverse=True)
    return ranked
```

---

## Feature Function: `save_free_model_rankings`
**Parameters:** `rankings, path`
**Variables Used:** `payload`
**Implementation:**
```python
def save_free_model_rankings(rankings: List[FreeModelRanking], path: Path=RANKINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'generated_at': _utc_now().isoformat(), 'total': len(rankings), 'rankings': [asdict(r) for r in rankings]}
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
```

---

## Feature Function: `load_free_model_rankings`
**Parameters:** `path`
**Variables Used:** `rankings, payload`
**Implementation:**
```python
def load_free_model_rankings(path: Path=RANKINGS_PATH) -> List[FreeModelRanking]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        rankings = []
        for row in payload.get('rankings', []):
            rankings.append(FreeModelRanking(**row))
        return rankings
    except Exception:
        return []
```

---

## Feature Function: `get_or_build_free_model_rankings`
**Parameters:** `force_refresh, stealth_window_days`
**Variables Used:** `fresh, cached`
**Implementation:**
```python
def get_or_build_free_model_rankings(force_refresh: bool=False, stealth_window_days: int=DEFAULT_STEALTH_WINDOW_DAYS) -> List[FreeModelRanking]:
    if not force_refresh:
        cached = load_free_model_rankings()
        if cached:
            return cached
    fresh = build_free_model_rankings(stealth_window_days=stealth_window_days)
    save_free_model_rankings(fresh)
    return fresh
```

---

## Feature Function: `get_top_free_models`
**Parameters:** `limit, force_refresh`
**Variables Used:** `rankings`
**Implementation:**
```python
def get_top_free_models(limit: int=40, force_refresh: bool=False) -> List[str]:
    rankings = get_or_build_free_model_rankings(force_refresh=force_refresh)
    return [r.model_id for r in rankings[:max(1, limit)]]
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/model_family.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/model_family.py`

**Module Overview**: 
```text
Dynamic Model Family Detection

Provides version-agnostic model family detection. Instead of hardcoding specific
model names (e.g., "claude-opus-4-20250514"), this module uses flexible pattern
matching to detect model families (e.g., "claude-opus", "gemini-flash", "o-series").

This ensures the proxy remains functional when providers update model versions
without breaking the entire codebase.
```

## Global Presets & Variables
- `MODEL_FAMILY_PATTERNS` = `[('^(?:openai/)?(o\\d+-?mini?)', ModelFamily.OPENAI_O_SERIES), ('^(?:openai/)?(o\\d+)', ModelFamily.OPENAI_O_SERIES), ('^(?:openai/)?gpt-5', ModelFamily.OPENAI_GPT), ('^(?:openai/)?gpt-4o(?:-?\\d+)?', ModelFamily.OPENAI_GPT), ('^(?:openai/)?gpt-4turbo', ModelFamily.OPENAI_GPT), ('^(?:openai/)?gpt-4', ModelFamily.OPENAI_GPT), ('^(?:openai/)?gpt-3\\.5', ModelFamily.OPENAI_GPT), ('^(?:anthropic/)?claude-opus[-\\s]?(\\d+)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:anthropic/)?claude-sonnet[-\\s]?(\\d+)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:anthropic/)?claude-haiku[-\\s]?(\\d+)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:anthropic/)?claude-3[-\\s]?(?:opus|sonnet|haiku)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:anthropic/)?claude-3\\.5', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:anthropic/)?claude-3\\.7', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:openrouter/)?(?:anthropic/)?claude-(opus|sonnet|haiku)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:vibeproxy|antigravity)/claude-(opus|sonnet|haiku)', ModelFamily.ANTHROPIC_CLAUDE), ('^(?:google/)?gemini[-\\s]?(\\d+\\.\\d+)?[-\\s]?flash', ModelFamily.GEMINI_FLASH), ('^(?:google/)?gemini-flash', ModelFamily.GEMINI_FLASH), ('^(?:google/)?gemini[-\\s]?(\\d+\\.\\d+)?[-\\s]?pro', ModelFamily.GEMINI_PRO), ('^(?:google/)?gemini-pro', ModelFamily.GEMINI_PRO), ('^(?:google/)?gemini[-\\s]?.*thinking', ModelFamily.GEMINI_PRO), ('^(?:google/)?gemini', ModelFamily.GEMINI_OTHER)]`
- `get_model_family` = `detect_model_family`

## Dependencies & Imports
re, typing.Optional, typing.Dict, typing.Any, dataclasses.dataclass, enum.Enum

## Feature Class: `ModelFamily`
**Description:**
```text
Model family categories for routing and transformation logic.
```

---

## Feature Class: `ModelFamilyInfo`
**Description:**
```text
Information about a detected model family.
```

---

## Feature Function: `detect_model_family`
**Logic & Purpose:**
```text
Detect model family from model name using flexible pattern matching.

This function is version-agnostic - it detects model families rather than
specific versions, so it works with new model releases without code changes.

Args:
    model_name: Model identifier (with or without provider prefix)
                e.g., "claude-opus-4-20250514", "openai/o1-mini", "gemini-2.0-flash"

Returns:
    ModelFamilyInfo with detected family, provider, and metadata
```

**Parameters:** `model_name`
**Variables Used:** `potential, model_lower, provider_map, match, version, tier, provider, base_name`
**Implementation:**
```python
def detect_model_family(model_name: str) -> ModelFamilyInfo:
    """
    Detect model family from model name using flexible pattern matching.

    This function is version-agnostic - it detects model families rather than
    specific versions, so it works with new model releases without code changes.

    Args:
        model_name: Model identifier (with or without provider prefix)
                    e.g., "claude-opus-4-20250514", "openai/o1-mini", "gemini-2.0-flash"

    Returns:
        ModelFamilyInfo with detected family, provider, and metadata
    """
    model_lower = model_name.lower()
    provider = 'unknown'
    base_name = model_lower
    if '/' in model_name:
        provider_part, base_name = model_lower.split('/', 1)
        provider_map = {'openai': 'openai', 'anthropic': 'anthropic', 'google': 'google', 'vibeproxy': 'vibeproxy', 'antigravity': 'antigravity', 'openrouter': 'openrouter', 'minimax': 'minimax', 'stepfun': 'stepfun', 'nvidia': 'nvidia'}
        provider = provider_map.get(provider_part, provider_part)
    for pattern, family in MODEL_FAMILY_PATTERNS:
        match = re.match(pattern, base_name)
        if match:
            version = None
            tier = None
            if match.groups():
                potential = match.group(1)
                if potential:
                    if potential.replace('.', '').isdigit():
                        version = potential
                    else:
                        tier = potential
            if family == ModelFamily.ANTHROPIC_CLAUDE:
                if 'opus' in base_name:
                    tier = 'opus'
                elif 'sonnet' in base_name:
                    tier = 'sonnet'
                elif 'haiku' in base_name:
                    tier = 'haiku'
            elif family == ModelFamily.GEMINI_FLASH:
                tier = 'flash'
            elif family == ModelFamily.GEMINI_PRO:
                tier = 'pro'
            elif family == ModelFamily.OPENAI_O_SERIES:
                if 'mini' in base_name:
                    tier = 'mini'
            return ModelFamilyInfo(family=family, provider=provider, base_name=base_name, version=version, tier=tier)
    return ModelFamilyInfo(family=ModelFamily.OTHER, provider=provider, base_name=base_name, version=None, tier=None)
```

---

## Feature Function: `is_reasoning_model`
**Logic & Purpose:**
```text
Check if a model supports reasoning/thinking parameters.

Version-agnostic: detects any o-series, claude with thinking, or gemini with thinking.
```

**Parameters:** `model_name`
**Variables Used:** `family_info`
**Implementation:**
```python
def is_reasoning_model(model_name: str) -> bool:
    """
    Check if a model supports reasoning/thinking parameters.

    Version-agnostic: detects any o-series, claude with thinking, or gemini with thinking.
    """
    family_info = detect_model_family(model_name)
    return family_info.family in (ModelFamily.OPENAI_O_SERIES, ModelFamily.ANTHROPIC_CLAUDE, ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_FLASH)
```

---

## Feature Function: `requires_thinking_budget`
**Logic & Purpose:**
```text
Check if model requires thinking_budget parameter (Gemini-style).
```

**Parameters:** `model_name`
**Variables Used:** `family_info`
**Implementation:**
```python
def requires_thinking_budget(model_name: str) -> bool:
    """Check if model requires thinking_budget parameter (Gemini-style)."""
    family_info = detect_model_family(model_name)
    return family_info.family in (ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_FLASH)
```

---

## Feature Function: `requires_thinking_tokens`
**Logic & Purpose:**
```text
Check if model requires thinking_tokens parameter (Anthropic-style).
```

**Parameters:** `model_name`
**Variables Used:** `family_info`
**Implementation:**
```python
def requires_thinking_tokens(model_name: str) -> bool:
    """Check if model requires thinking_tokens parameter (Anthropic-style)."""
    family_info = detect_model_family(model_name)
    return family_info.family == ModelFamily.ANTHROPIC_CLAUDE
```

---

## Feature Function: `requires_effort_level`
**Logic & Purpose:**
```text
Check if model requires effort level (OpenAI o-series style).
```

**Parameters:** `model_name`
**Variables Used:** `family_info`
**Implementation:**
```python
def requires_effort_level(model_name: str) -> bool:
    """Check if model requires effort level (OpenAI o-series style)."""
    family_info = detect_model_family(model_name)
    return family_info.family == ModelFamily.OPENAI_O_SERIES
```

---

## Feature Function: `get_provider_for_model`
**Logic & Purpose:**
```text
Extract or infer provider from model name.
```

**Parameters:** `model_name`
**Variables Used:** `family_info`
**Implementation:**
```python
def get_provider_for_model(model_name: str) -> str:
    """Extract or infer provider from model name."""
    family_info = detect_model_family(model_name)
    return family_info.provider
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/recommender.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/recommender.py`

**Module Overview**: 
```text
Intelligent model recommender based on saved configuration patterns.

NOTE: This analyzes SAVED CONFIGURATION MODES (modes.json), not actual API usage.
The "usage patterns" refer to which models appear in your saved configurations,
not which models you've actually used in API requests.

For actual API usage tracking, enable usage logging with TRACK_USAGE=true.
```

## Dependencies & Imports
json, os, typing.Dict, typing.List, typing.Any, typing.Tuple, typing.Set, collections.defaultdict, collections.Counter, datetime.datetime

## Feature Class: `ModelRecommender`
**Description:**
```text
Analyze saved configuration patterns and recommend better/free alternatives.

IMPORTANT: This analyzes which models appear in saved configuration modes,
NOT actual API request usage. If you haven't saved any modes, there will
be no pattern data available.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.models_data = self._load_models()
    self.modes_data = self._load_modes()
```

### Method: `_load_models`
**Logic & Purpose:**
```text
Load models database.
```

**Parameters:** `self`
**Implementation:**
```python
def _load_models(self) -> Dict[str, Any]:
    """Load models database."""
    if os.path.exists(self.MODELS_DB):
        with open(self.MODELS_DB, 'r') as f:
            return json.load(f)
    return {}
```

### Method: `_load_modes`
**Logic & Purpose:**
```text
Load saved modes.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def _load_modes(self) -> Dict[str, Any]:
    """Load saved modes."""
    if os.path.exists(self.MODES_DB):
        with open(self.MODES_DB, 'r') as f:
            data = json.load(f)
            return data.get('modes', {})
    return {}
```

### Method: `analyze_configuration_patterns`
**Logic & Purpose:**
```text
Analyze which models appear together in saved configuration modes.

NOTE: This does NOT track actual API usage. It only counts how many
times each model appears in your saved configuration modes.
```

**Parameters:** `self`
**Variables Used:** `middle_model, big_model, small_model, config, reasoning, patterns, verbosity, provider`
**Implementation:**
```python
def analyze_configuration_patterns(self) -> Dict[str, Any]:
    """
        Analyze which models appear together in saved configuration modes.

        NOTE: This does NOT track actual API usage. It only counts how many
        times each model appears in your saved configuration modes.
        """
    patterns = {'big_models': Counter(), 'middle_models': Counter(), 'small_models': Counter(), 'reasoning_usage': Counter(), 'verbosity_usage': Counter(), 'provider_usage': Counter()}
    for mode_id, mode in self.modes_data.items():
        config = mode.get('config', {})
        big_model = config.get('BIG_MODEL', '')
        middle_model = config.get('MIDDLE_MODEL', '')
        small_model = config.get('SMALL_MODEL', '')
        if big_model:
            patterns['big_models'][big_model] += 1
        if middle_model:
            patterns['middle_models'][middle_model] += 1
        if small_model:
            patterns['small_models'][small_model] += 1
        reasoning = config.get('REASONING_EFFORT', '')
        if reasoning:
            patterns['reasoning_usage'][reasoning] += 1
        verbosity = config.get('VERBOSITY', '')
        if verbosity:
            patterns['verbosity_usage'][verbosity] += 1
        for model in [big_model, middle_model, small_model]:
            if model:
                provider = self._get_provider_from_model(model)
                if provider:
                    patterns['provider_usage'][provider] += 1
    return patterns
```

### Method: `_get_provider_from_model`
**Logic & Purpose:**
```text
Extract provider from model ID.
```

**Parameters:** `self, model_id`
**Implementation:**
```python
def _get_provider_from_model(self, model_id: str) -> str:
    """Extract provider from model ID."""
    if model_id.startswith('lmstudio/'):
        return 'lmstudio'
    elif model_id.startswith('ollama/'):
        return 'ollama'
    elif '/' in model_id:
        return model_id.split('/')[0]
    return 'unknown'
```

### Method: `find_model_alternatives`
**Logic & Purpose:**
```text
Find alternative models to a given model.
```

**Parameters:** `self, model_id, alternatives_type`
**Variables Used:** `model_name, context_diff, all_models, model_size, target_context, reasons, target_vision, score, target_source, price_ratio, match, size_diff, target_reasoning, alternatives, target_is_free, model_context, target_price, model_price, unit, num, target_size, target_name, target_model`
**Implementation:**
```python
def find_model_alternatives(self, model_id: str, alternatives_type: str='all') -> List[Dict[str, Any]]:
    """Find alternative models to a given model."""
    if not self.models_data:
        return []
    all_models = self.models_data.get('local_models', []) + self.models_data.get('reasoning_models', []) + self.models_data.get('verbosity_models', []) + self.models_data.get('standard_models', [])
    target_model = None
    for model in all_models:
        if model.get('id') == model_id:
            target_model = model
            break
    if not target_model:
        return []
    alternatives = []
    target_source = target_model.get('source', '')
    target_reasoning = target_model.get('supports_reasoning', False)
    target_vision = target_model.get('supports_vision', False)
    target_context = target_model.get('context_length', 0)
    target_price = target_model.get('pricing', {}).get('prompt_numeric', 0.0)
    target_is_free = target_model.get('is_free', False)
    for model in all_models:
        if model.get('id') == model_id:
            continue
        score = 0
        reasons = []
        if alternatives_type == 'free' and (not model.get('is_free', False)):
            continue
        elif alternatives_type == 'local' and model.get('source', '') not in ['lmstudio', 'ollama']:
            continue
        elif alternatives_type == 'reasoning' and (not model.get('supports_reasoning', False)):
            continue
        elif alternatives_type == 'vision' and (not model.get('supports_vision', False)):
            continue
        if model.get('supports_reasoning') == target_reasoning:
            score += 10
            if target_reasoning:
                reasons.append('Has same reasoning support')
        if model.get('supports_vision') == target_vision:
            score += 5
            if target_vision:
                reasons.append('Has same vision support')
        model_context = model.get('context_length', 0)
        if target_context and model_context:
            context_diff = abs(target_context - model_context) / target_context
            if context_diff < 0.2:
                score += 10
                reasons.append(f'Similar context length ({model_context:,} tokens)')
            elif context_diff < 0.5:
                score += 5
        model_price = model.get('pricing', {}).get('prompt_numeric', 0.0)
        if not target_is_free and (not model.get('is_free', False)):
            price_ratio = model_price / target_price if target_price > 0 else 0
            if price_ratio < 0.5:
                score += 15
                reasons.append(f'Much cheaper (${model_price:.6f} vs ${target_price:.6f} per 1M tokens)')
            elif price_ratio < 0.8:
                score += 8
                reasons.append(f'Cheaper (${model_price:.6f} vs ${target_price:.6f} per 1M tokens)')
        if target_price > 0 and model.get('is_free', False):
            score += 20
            reasons.append('Completely free alternative')
        if model.get('source', '') != target_source:
            score += 3
            reasons.append(f"Different provider ({model.get('source', 'unknown')})")
        target_name = target_model.get('id', '').lower()
        model_name = model.get('id', '').lower()

        def extract_size(name):
            import re
            match = re.search('(\\d+)([bm])', name)
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                return num * 1000 if unit == 'b' else num
            return 0
        target_size = extract_size(target_name)
        model_size = extract_size(model_name)
        if target_size and model_size:
            size_diff = abs(target_size - model_size) / target_size
            if size_diff < 0.3:
                score += 7
                reasons.append('Similar model size')
        if score > 0:
            alternatives.append({'model': model, 'score': score, 'reasons': reasons})
    alternatives.sort(key=lambda x: x['score'], reverse=True)
    return alternatives[:10]
```

### Method: `find_correlated_models`
**Logic & Purpose:**
```text
Find models that are commonly used together with the given model.
```

**Parameters:** `self, model_id`
**Variables Used:** `result, correlations, config, all_models, models_in_mode, sorted_correlations`
**Implementation:**
```python
def find_correlated_models(self, model_id: str) -> List[Dict[str, Any]]:
    """Find models that are commonly used together with the given model."""
    correlations = defaultdict(int)
    for mode_id, mode in self.modes_data.items():
        config = mode.get('config', {})
        models_in_mode = [config.get('BIG_MODEL', ''), config.get('MIDDLE_MODEL', ''), config.get('SMALL_MODEL', '')]
        if model_id in models_in_mode:
            for other_model in models_in_mode:
                if other_model and other_model != model_id:
                    correlations[other_model] += 1
    sorted_correlations = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
    result = []
    for correlated_model_id, count in sorted_correlations[:5]:
        all_models = self.models_data.get('local_models', []) + self.models_data.get('reasoning_models', []) + self.models_data.get('verbosity_models', []) + self.models_data.get('standard_models', [])
        for model in all_models:
            if model.get('id') == correlated_model_id:
                result.append({'model': model, 'correlation_count': count})
                break
    return result
```

### Method: `recommend_based_on_configuration`
**Logic & Purpose:**
```text
Recommend models based on saved configuration patterns.

NOTE: Based on saved configurations, not actual API usage.
```

**Parameters:** `self, slot`
**Variables Used:** `most_used, patterns, result, all_models`
**Implementation:**
```python
def recommend_based_on_configuration(self, slot: str='big') -> List[Dict[str, Any]]:
    """
        Recommend models based on saved configuration patterns.

        NOTE: Based on saved configurations, not actual API usage.
        """
    patterns = self.analyze_configuration_patterns()
    if slot == 'big':
        most_used = patterns['big_models'].most_common(10)
    elif slot == 'middle':
        most_used = patterns['middle_models'].most_common(10)
    elif slot == 'small':
        most_used = patterns['small_models'].most_common(10)
    else:
        return []
    result = []
    for model_id, count in most_used:
        all_models = self.models_data.get('local_models', []) + self.models_data.get('reasoning_models', []) + self.models_data.get('verbosity_models', []) + self.models_data.get('standard_models', [])
        for model in all_models:
            if model.get('id') == model_id:
                result.append({'model': model, 'usage_count': count})
                break
    return result
```

### Method: `get_recommendations_summary`
**Logic & Purpose:**
```text
Get a summary of configuration patterns (not actual usage).

NOTE: Based on saved configurations, not actual API requests.
```

**Parameters:** `self`
**Variables Used:** `patterns`
**Implementation:**
```python
def get_recommendations_summary(self) -> Dict[str, Any]:
    """
        Get a summary of configuration patterns (not actual usage).

        NOTE: Based on saved configurations, not actual API requests.
        """
    patterns = self.analyze_configuration_patterns()
    return {'total_modes': len(self.modes_data), 'most_used_big_model': patterns['big_models'].most_common(1)[0] if patterns['big_models'] else None, 'most_used_middle_model': patterns['middle_models'].most_common(1)[0] if patterns['middle_models'] else None, 'most_used_small_model': patterns['small_models'].most_common(1)[0] if patterns['small_models'] else None, 'preferred_reasoning': patterns['reasoning_usage'].most_common(1)[0] if patterns['reasoning_usage'] else None, 'provider_distribution': dict(patterns['provider_usage'])}
```

### Method: `suggest_free_alternatives`
**Logic & Purpose:**
```text
Suggest free alternatives to a list of paid models.
```

**Parameters:** `self, paid_models`
**Variables Used:** `suggestions, alternatives`
**Implementation:**
```python
def suggest_free_alternatives(self, paid_models: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Suggest free alternatives to a list of paid models."""
    suggestions = {}
    for model_id in paid_models:
        alternatives = self.find_model_alternatives(model_id, alternatives_type='free')
        suggestions[model_id] = alternatives[:5]
    return suggestions
```

### Method: `export_recommendations`
**Logic & Purpose:**
```text
Export recommendations for a model to a file.
```

**Parameters:** `self, model_id, output_file`
**Variables Used:** `recommendations`
**Implementation:**
```python
def export_recommendations(self, model_id: str, output_file: str) -> bool:
    """Export recommendations for a model to a file."""
    try:
        recommendations = {'model': model_id, 'alternatives': {'all': self.find_model_alternatives(model_id, 'all'), 'free': self.find_model_alternatives(model_id, 'free'), 'local': self.find_model_alternatives(model_id, 'local'), 'reasoning': self.find_model_alternatives(model_id, 'reasoning')}, 'correlated': self.find_correlated_models(model_id), 'usage_based': self.recommend_based_on_usage()}
        with open(output_file, 'w') as f:
            json.dump(recommendations, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f'Error exporting recommendations: {e}')
        return False
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Test the recommender.
```

**Parameters:** ``
**Variables Used:** `patterns, recommender, alternatives, sample_model`
**Implementation:**
```python
def main():
    """Test the recommender."""
    recommender = ModelRecommender()
    print('Model Recommender - Configuration Pattern Analysis')
    print('=' * 70)
    print('NOTE: This analyzes saved configurations, not actual API usage')
    print('=' * 70)
    patterns = recommender.analyze_configuration_patterns()
    print(f'\nTotal saved modes: {len(recommender.modes_data)}')
    print(f'\nMost used BIG models:')
    for model, count in patterns['big_models'].most_common(5):
        print(f'  - {model}: {count} modes')
    print(f'\nPreferred reasoning effort:')
    for effort, count in patterns['reasoning_usage'].most_common(3):
        print(f'  - {effort}: {count} modes')
    if patterns['big_models']:
        sample_model = patterns['big_models'].most_common(1)[0][0]
        print(f'\n\nFree alternatives to {sample_model}:')
        alternatives = recommender.find_model_alternatives(sample_model, 'free')
        for alt in alternatives[:3]:
            print(f"  - {alt['model']['id']} (score: {alt['score']})")
            for reason in alt['reasons'][:2]:
                print(f'    • {reason}')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/models/modes.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/models/modes.py`

**Module Overview**: 
```text
Mode management for saving and loading configuration presets.
```

## Global Presets & Variables
- `MODES_FILE` = `os.path.join(os.path.dirname(__file__), '..', '..', 'modes.json')`

## Dependencies & Imports
json, os, sys, typing.Dict, typing.Any, typing.Optional, typing.List, datetime.datetime

## Feature Class: `ModeManager`
**Description:**
```text
Manage saved configuration modes.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.modes_file = MODES_FILE
    self.modes = self._load_modes()
```

### Method: `_load_modes`
**Logic & Purpose:**
```text
Load modes from file.
```

**Parameters:** `self`
**Variables Used:** `data`
**Implementation:**
```python
def _load_modes(self) -> Dict[str, Any]:
    """Load modes from file."""
    if os.path.exists(self.modes_file):
        try:
            with open(self.modes_file, 'r') as f:
                data = json.load(f)
                return data.get('modes', {})
        except Exception as e:
            print(f'Warning: Could not load modes file: {e}')
    return {}
```

### Method: `_save_modes`
**Logic & Purpose:**
```text
Save modes to file.
```

**Parameters:** `self`
**Implementation:**
```python
def _save_modes(self):
    """Save modes to file."""
    try:
        with open(self.modes_file, 'w') as f:
            json.dump({'modes': self.modes, 'version': '1.0'}, f, indent=2)
    except Exception as e:
        print(f'Error: Could not save modes file: {e}')
        sys.exit(1)
```

### Method: `_get_available_id`
**Logic & Purpose:**
```text
Get the next available mode ID (1-99).
```

**Parameters:** `self`
**Variables Used:** `used_ids`
**Implementation:**
```python
def _get_available_id(self) -> str:
    """Get the next available mode ID (1-99)."""
    used_ids = set()
    for mode in self.modes.values():
        if mode.get('id'):
            used_ids.add(int(mode['id']))
    for i in range(1, 100):
        if i not in used_ids:
            return str(i)
    raise ValueError('Maximum number of modes (99) reached')
```

### Method: `save_mode`
**Logic & Purpose:**
```text
Save a configuration as a mode.
```

**Parameters:** `self, name, config, mode_id`
**Variables Used:** `mode_id`
**Implementation:**
```python
def save_mode(self, name: str, config: Dict[str, str], mode_id: Optional[str]=None) -> bool:
    """Save a configuration as a mode."""
    if not name:
        print('Error: Mode name cannot be empty')
        return False
    for mode in self.modes.values():
        if mode.get('name', '').lower() == name.lower():
            print(f"Error: Mode '{name}' already exists")
            return False
    if not mode_id:
        try:
            mode_id = self._get_available_id()
        except ValueError as e:
            print(f'Error: {e}')
            return False
    for existing_id, mode in self.modes.items():
        if mode.get('id') == mode_id:
            print(f'Error: Mode ID {mode_id} already exists')
            return False
    self.modes[mode_id] = {'id': mode_id, 'name': name, 'config': config, 'created': datetime.now().isoformat(), 'modified': datetime.now().isoformat()}
    self._save_modes()
    print(f"✓ Saved mode '{name}' (ID: {mode_id})")
    return True
```

### Method: `load_mode`
**Logic & Purpose:**
```text
Load a mode by ID or name.
```

**Parameters:** `self, identifier`
**Variables Used:** `mode, config`
**Implementation:**
```python
def load_mode(self, identifier: str) -> Optional[Dict[str, str]]:
    """Load a mode by ID or name."""
    if identifier in self.modes:
        mode = self.modes[identifier]
        config = mode['config']
        print(f"✓ Loaded mode '{mode['name']}' (ID: {mode['id']})")
        return config
    for mode in self.modes.values():
        if mode.get('name', '').lower() == identifier.lower():
            config = mode['config']
            print(f"✓ Loaded mode '{mode['name']}' (ID: {mode['id']})")
            return config
    print(f"Error: Mode '{identifier}' not found")
    return None
```

### Method: `delete_mode`
**Logic & Purpose:**
```text
Delete a mode by ID or name.
```

**Parameters:** `self, identifier`
**Variables Used:** `mode_id, mode_name`
**Implementation:**
```python
def delete_mode(self, identifier: str) -> bool:
    """Delete a mode by ID or name."""
    mode_id = None
    mode_name = None
    if identifier in self.modes:
        mode_id = identifier
        mode_name = self.modes[identifier]['name']
    else:
        for mid, mode in self.modes.items():
            if mode.get('name', '').lower() == identifier.lower():
                mode_id = mid
                mode_name = mode['name']
                break
    if mode_id:
        del self.modes[mode_id]
        self._save_modes()
        print(f"✓ Deleted mode '{mode_name}' (ID: {mode_id})")
        return True
    print(f"Error: Mode '{identifier}' not found")
    return False
```

### Method: `list_modes`
**Logic & Purpose:**
```text
List all saved modes.
```

**Parameters:** `self`
**Variables Used:** `dt, big_model, reasoning, config, sorted_modes, created`
**Implementation:**
```python
def list_modes(self) -> bool:
    """List all saved modes."""
    if not self.modes:
        print('No saved modes. Create one with --save-mode NAME')
        return True
    print('\nSaved Modes:')
    print('=' * 70)
    sorted_modes = sorted(self.modes.values(), key=lambda x: int(x['id']))
    for mode in sorted_modes:
        config = mode['config']
        created = mode.get('created', '')
        if created:
            try:
                dt = datetime.fromisoformat(created)
                created = dt.strftime('%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                pass
        print(f"\n[{mode['id']}] {mode['name']}")
        print(f'    Created: {created}')
        big_model = config.get('BIG_MODEL', 'Not set')
        reasoning = config.get('REASONING_EFFORT', 'Not set')
        if len(big_model) > 40:
            big_model = big_model[:37] + '...'
        print(f'    Big Model: {big_model}')
        if reasoning != 'Not set':
            print(f'    Reasoning: {reasoning}')
    print('=' * 70)
    print(f'\nTotal: {len(self.modes)} mode(s)')
    return True
```

### Method: `get_mode_config`
**Logic & Purpose:**
```text
Get mode configuration without printing messages.
```

**Parameters:** `self, identifier`
**Implementation:**
```python
def get_mode_config(self, identifier: str) -> Optional[Dict[str, str]]:
    """Get mode configuration without printing messages."""
    if identifier in self.modes:
        return self.modes[identifier]['config']
    for mode in self.modes.values():
        if mode.get('name', '').lower() == identifier.lower():
            return mode['config']
    return None
```

### Method: `handle_mode_operations`
**Logic & Purpose:**
```text
Handle mode-related operations from CLI arguments.
```

**Parameters:** `args`
**Variables Used:** `manager, config`
**Implementation:**
```python
@staticmethod
def handle_mode_operations(args) -> bool:
    """Handle mode-related operations from CLI arguments."""
    manager = ModeManager()
    if args.list_modes:
        manager.list_modes()
        return True
    if args.load_mode:
        config = manager.load_mode(args.load_mode)
        if config:
            for key, value in config.items():
                os.environ[key] = value
        return True
    if args.delete_mode:
        manager.delete_mode(args.delete_mode)
        return True
    if args.save_mode:
        from src.core.config import config as current_config
        config = {'BIG_MODEL': current_config.big_model, 'MIDDLE_MODEL': current_config.middle_model, 'SMALL_MODEL': current_config.small_model, 'REASONING_EFFORT': current_config.reasoning_effort or '', 'VERBOSITY': current_config.verbosity or '', 'REASONING_EXCLUDE': 'true' if current_config.reasoning_exclude else 'false', 'HOST': str(current_config.host), 'PORT': str(current_config.port), 'LOG_LEVEL': current_config.log_level}
        manager.save_mode(args.save_mode, config)
        return True
    if args.mode_name:
        config = {'BIG_MODEL': os.environ.get('BIG_MODEL', os.environ.get('CLAUDE_BIG_MODEL', '')), 'MIDDLE_MODEL': os.environ.get('MIDDLE_MODEL', os.environ.get('CLAUDE_MIDDLE_MODEL', '')), 'SMALL_MODEL': os.environ.get('SMALL_MODEL', os.environ.get('CLAUDE_SMALL_MODEL', '')), 'REASONING_EFFORT': os.environ.get('REASONING_EFFORT', os.environ.get('CLAUDE_REASONING_EFFORT', '')), 'VERBOSITY': os.environ.get('VERBOSITY', os.environ.get('CLAUDE_VERBOSITY', '')), 'REASONING_EXCLUDE': os.environ.get('REASONING_EXCLUDE', os.environ.get('CLAUDE_REASONING_EXCLUDE', 'false')), 'HOST': os.environ.get('HOST', os.environ.get('CLAUDE_HOST', '0.0.0.0')), 'PORT': os.environ.get('PORT', os.environ.get('CLAUDE_PORT', '8082')), 'LOG_LEVEL': os.environ.get('LOG_LEVEL', os.environ.get('CLAUDE_LOG_LEVEL', 'INFO'))}
        manager.save_mode(args.mode_name, config)
        return True
    return False
```

---


