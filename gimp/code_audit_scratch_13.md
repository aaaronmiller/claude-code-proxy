# File Audit: /home/cheta/code/claude-code-proxy/src/services/billing/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/billing/__init__.py`

**Module Overview**: 
```text
Billing integration package for real-time cost tracking.
```

## Global Presets & Variables
- `__all__` = `['billing_manager']`

## Dependencies & Imports
src.services.billing.billing_integrations.billing_manager


# File Audit: /home/cheta/code/claude-code-proxy/src/services/billing/billing_integrations.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/billing/billing_integrations.py`

**Module Overview**: 
```text
Real-time Billing Integrations

Fetches actual billing data from provider APIs to track real costs
instead of relying on estimates.
```

## Global Presets & Variables
- `billing_manager` = `BillingManager()`

## Dependencies & Imports
typing.Dict, typing.Any, typing.Optional, typing.List, datetime.datetime, datetime.timedelta, abc.ABC, abc.abstractmethod, os, httpx, asyncio, src.core.logging.logger

## Feature Class: `BillingProvider`
**Description:**
```text
Base class for billing provider integrations
```

### Method: `__init__`
**Parameters:** `self, api_key`
**Implementation:**
```python
def __init__(self, api_key: Optional[str]=None):
    self.api_key = api_key
    self.enabled = bool(api_key)
```

### Method: `fetch_usage`
**Logic & Purpose:**
```text
Fetch usage data from provider API
```

**Parameters:** `self, start_date, end_date`
**Implementation:**
```python
@abstractmethod
async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Fetch usage data from provider API"""
    pass
```

### Method: `fetch_current_balance`
**Logic & Purpose:**
```text
Fetch current account balance/credits
```

**Parameters:** `self`
**Implementation:**
```python
@abstractmethod
async def fetch_current_balance(self) -> Dict[str, Any]:
    """Fetch current account balance/credits"""
    pass
```

---

## Feature Class: `OpenAIBilling`
**Description:**
```text
OpenAI billing integration
```

### Method: `__init__`
**Parameters:** `self, api_key`
**Implementation:**
```python
def __init__(self, api_key: Optional[str]=None):
    super().__init__(api_key or os.getenv('OPENAI_API_KEY'))
    self.base_url = 'https://api.openai.com/v1'
```

### Method: `fetch_usage`
**Logic & Purpose:**
```text
Fetch OpenAI usage data.

Note: OpenAI deprecated the /dashboard/billing endpoints.
This returns estimated data based on local tracking.
```

**Parameters:** `self, start_date, end_date`
**Implementation:**
```python
async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """
        Fetch OpenAI usage data.

        Note: OpenAI deprecated the /dashboard/billing endpoints.
        This returns estimated data based on local tracking.
        """
    if not self.enabled:
        return {'error': 'OpenAI API key not configured'}
    try:
        return {'provider': 'openai', 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'total_cost': 0.0, 'note': 'OpenAI does not provide programmatic billing access. Check dashboard.openai.com'}
    except Exception as e:
        logger.warning(f'OpenAI billing fetch skipped (API deprecated): {e}')
        logger.debug(f'Detailed error: {e}')
        return {'error': 'Billing API deprecated by provider'}
```

### Method: `fetch_current_balance`
**Logic & Purpose:**
```text
Fetch current OpenAI balance
```

**Parameters:** `self`
**Implementation:**
```python
async def fetch_current_balance(self) -> Dict[str, Any]:
    """Fetch current OpenAI balance"""
    if not self.enabled:
        return {'error': 'OpenAI API key not configured'}
    return {'provider': 'openai', 'balance': None, 'note': 'Check dashboard.openai.com for balance'}
```

---

## Feature Class: `OpenRouterBilling`
**Description:**
```text
OpenRouter billing integration
```

### Method: `__init__`
**Parameters:** `self, api_key`
**Implementation:**
```python
def __init__(self, api_key: Optional[str]=None):
    super().__init__(api_key or os.getenv('OPENAI_API_KEY'))
    self.base_url = 'https://openrouter.ai/api/v1'
```

### Method: `fetch_usage`
**Logic & Purpose:**
```text
Fetch OpenRouter usage data
```

**Parameters:** `self, start_date, end_date`
**Variables Used:** `response, data`
**Implementation:**
```python
async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Fetch OpenRouter usage data"""
    if not self.enabled:
        return {'error': 'OpenRouter API key not configured'}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/auth/key', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return {'provider': 'openrouter', 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'usage': data.get('data', {}), 'note': 'OpenRouter billing data from key stats'}
            else:
                return {'error': f'OpenRouter API returned {response.status_code}'}
    except Exception as e:
        logger.error(f'Failed to fetch OpenRouter usage: {e}')
        return {'error': str(e)}
```

### Method: `fetch_current_balance`
**Logic & Purpose:**
```text
Fetch current OpenRouter credits
```

**Parameters:** `self`
**Variables Used:** `key_data, response, data`
**Implementation:**
```python
async def fetch_current_balance(self) -> Dict[str, Any]:
    """Fetch current OpenRouter credits"""
    if not self.enabled:
        return {'error': 'OpenRouter API key not configured'}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{self.base_url}/auth/key', headers={'Authorization': f'Bearer {self.api_key}'}, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                key_data = data.get('data', {})
                return {'provider': 'openrouter', 'limit': key_data.get('limit'), 'usage': key_data.get('usage'), 'remaining': key_data.get('limit', 0) - key_data.get('usage', 0) if key_data.get('limit') else None, 'is_free_tier': key_data.get('is_free_tier', False), 'rate_limit': key_data.get('rate_limit', {})}
            else:
                return {'error': f'OpenRouter API returned {response.status_code}'}
    except Exception as e:
        logger.error(f'Failed to fetch OpenRouter balance: {e}')
        return {'error': str(e)}
```

---

## Feature Class: `AnthropicBilling`
**Description:**
```text
Anthropic billing integration
```

### Method: `__init__`
**Parameters:** `self, api_key`
**Implementation:**
```python
def __init__(self, api_key: Optional[str]=None):
    super().__init__(api_key or os.getenv('ANTHROPIC_API_KEY'))
    self.base_url = 'https://api.anthropic.com/v1'
```

### Method: `fetch_usage`
**Logic & Purpose:**
```text
Fetch Anthropic usage data
```

**Parameters:** `self, start_date, end_date`
**Implementation:**
```python
async def fetch_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Fetch Anthropic usage data"""
    if not self.enabled:
        return {'error': 'Anthropic API key not configured'}
    return {'provider': 'anthropic', 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'note': 'Anthropic does not provide programmatic billing access. Check console.anthropic.com'}
```

### Method: `fetch_current_balance`
**Logic & Purpose:**
```text
Fetch current Anthropic balance
```

**Parameters:** `self`
**Implementation:**
```python
async def fetch_current_balance(self) -> Dict[str, Any]:
    """Fetch current Anthropic balance"""
    if not self.enabled:
        return {'error': 'Anthropic API key not configured'}
    return {'provider': 'anthropic', 'note': 'Check console.anthropic.com for usage'}
```

---

## Feature Class: `BillingManager`
**Description:**
```text
Manages billing integrations across multiple providers
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.providers: Dict[str, BillingProvider] = {'openai': OpenAIBilling(), 'openrouter': OpenRouterBilling(), 'anthropic': AnthropicBilling()}
```

### Method: `fetch_all_usage`
**Logic & Purpose:**
```text
Fetch usage from all configured providers
```

**Parameters:** `self, days`
**Variables Used:** `provider_results, results, end_date, start_date, tasks`
**Implementation:**
```python
async def fetch_all_usage(self, days: int=7) -> Dict[str, Any]:
    """Fetch usage from all configured providers"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    results = {}
    tasks = []
    for name, provider in self.providers.items():
        if provider.enabled:
            tasks.append(self._fetch_provider_usage(name, provider, start_date, end_date))
    if tasks:
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in provider_results:
            results[name] = result
    return {'period': {'start': start_date.isoformat(), 'end': end_date.isoformat(), 'days': days}, 'providers': results}
```

### Method: `_fetch_provider_usage`
**Logic & Purpose:**
```text
Helper to fetch usage from a single provider
```

**Parameters:** `self, name, provider, start_date, end_date`
**Variables Used:** `result`
**Implementation:**
```python
async def _fetch_provider_usage(self, name: str, provider: BillingProvider, start_date: datetime, end_date: datetime) -> tuple:
    """Helper to fetch usage from a single provider"""
    try:
        result = await provider.fetch_usage(start_date, end_date)
        return (name, result)
    except Exception as e:
        logger.error(f'Failed to fetch {name} usage: {e}')
        return (name, {'error': str(e)})
```

### Method: `fetch_all_balances`
**Logic & Purpose:**
```text
Fetch current balance from all configured providers
```

**Parameters:** `self`
**Variables Used:** `results, tasks, provider_results`
**Implementation:**
```python
async def fetch_all_balances(self) -> Dict[str, Any]:
    """Fetch current balance from all configured providers"""
    results = {}
    tasks = []
    for name, provider in self.providers.items():
        if provider.enabled:
            tasks.append(self._fetch_provider_balance(name, provider))
    if tasks:
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in provider_results:
            results[name] = result
    return {'providers': results}
```

### Method: `_fetch_provider_balance`
**Logic & Purpose:**
```text
Helper to fetch balance from a single provider
```

**Parameters:** `self, name, provider`
**Variables Used:** `result`
**Implementation:**
```python
async def _fetch_provider_balance(self, name: str, provider: BillingProvider) -> tuple:
    """Helper to fetch balance from a single provider"""
    try:
        result = await provider.fetch_current_balance()
        return (name, result)
    except Exception as e:
        logger.error(f'Failed to fetch {name} balance: {e}')
        return (name, {'error': str(e)})
```

### Method: `get_provider`
**Logic & Purpose:**
```text
Get a specific provider by name
```

**Parameters:** `self, provider_name`
**Implementation:**
```python
def get_provider(self, provider_name: str) -> Optional[BillingProvider]:
    """Get a specific provider by name"""
    return self.providers.get(provider_name.lower())
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/tools/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/tools/__init__.py`

**Module Overview**: 
```text
Tools Services Module

Provides universal tool mapping and normalization for cross-IDE support.
```

## Global Presets & Variables
- `__all__` = `['ToolCategory', 'TOOL_REGISTRY', 'get_canonical_tool_name', 'convert_tool_name', 'normalize_tool_params', 'get_tool_params_for_ide', 'list_all_tools', 'get_tools_by_category', 'get_tool_info', 'sanitize_function_name', 'sanitize_tool_declarations']`

## Dependencies & Imports
tool_mapper.ToolCategory, tool_mapper.TOOL_REGISTRY, tool_mapper.get_canonical_tool_name, tool_mapper.convert_tool_name, tool_mapper.normalize_tool_params, tool_mapper.get_tool_params_for_ide, tool_mapper.list_all_tools, tool_mapper.get_tools_by_category, tool_mapper.get_tool_info, tool_mapper.sanitize_function_name, tool_mapper.sanitize_tool_declarations


# File Audit: /home/cheta/code/claude-code-proxy/src/services/tools/tool_mapper.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/tools/tool_mapper.py`

**Module Overview**: 
```text
Universal Tool Mapper

Maps tool names and parameters between different IDE formats.
Enables any IDE to work with any backend provider through
canonical tool name normalization.

Supported mappings:
- Claude Code ↔ Codex CLI ↔ Gemini CLI ↔ Qwen Code ↔ OpenCode
```

## Global Presets & Variables
- `TOOL_REGISTRY` = `{'bash': {'category': ToolCategory.SHELL.value, 'names': {'claude_code': 'Bash', 'antigravity': 'Bash', 'codex_cli': 'run_command', 'gemini_cli': 'shell', 'qwen_code': 'execute', 'opencode': 'execute'}, 'params': {'command': ['prompt', 'code', 'cmd', 'script', 'input'], 'timeout': ['timeout_ms', 'time_limit']}}, 'repl': {'category': ToolCategory.SHELL.value, 'names': {'claude_code': 'Repl', 'antigravity': 'Repl', 'codex_cli': 'run_code', 'gemini_cli': 'execute_code', 'qwen_code': 'run_code', 'opencode': 'run_code'}, 'params': {'command': ['code', 'script', 'prompt']}}, 'read': {'category': ToolCategory.FILE_READ.value, 'names': {'claude_code': 'Read', 'antigravity': 'Read', 'codex_cli': 'read_file', 'gemini_cli': 'read_file', 'qwen_code': 'read', 'opencode': 'read'}, 'params': {'file_path': ['path', 'filename', 'file', 'filepath'], 'start_line': ['start', 'from_line', 'line_start'], 'end_line': ['end', 'to_line', 'line_end']}}, 'write': {'category': ToolCategory.FILE_WRITE.value, 'names': {'claude_code': 'Write', 'antigravity': 'Write', 'codex_cli': 'write_file', 'gemini_cli': 'write_file', 'qwen_code': 'write', 'opencode': 'write'}, 'params': {'file_path': ['path', 'filename', 'file', 'filepath'], 'content': ['text', 'data', 'contents', 'body']}}, 'edit': {'category': ToolCategory.FILE_EDIT.value, 'names': {'claude_code': 'Edit', 'antigravity': 'Edit', 'codex_cli': 'patch_file', 'gemini_cli': 'edit_file', 'qwen_code': 'edit', 'opencode': 'edit'}, 'params': {'file_path': ['path', 'file', 'filename'], 'old_text': ['original', 'before', 'search', 'find'], 'new_text': ['replacement', 'after', 'replace', 'with']}}, 'multiedit': {'category': ToolCategory.FILE_EDIT.value, 'names': {'claude_code': 'MultiEdit', 'antigravity': 'MultiEdit', 'codex_cli': 'multi_patch', 'gemini_cli': 'batch_edit', 'qwen_code': 'multiedit', 'opencode': 'multiedit'}, 'params': {'file_path': ['path', 'file'], 'edits': ['changes', 'modifications', 'patches']}}, 'grep': {'category': ToolCategory.SEARCH.value, 'names': {'claude_code': 'Grep', 'antigravity': 'Grep', 'codex_cli': 'search_files', 'gemini_cli': 'grep', 'qwen_code': 'search', 'opencode': 'search'}, 'params': {'pattern': ['query', 'search', 'regex', 'term'], 'path': ['directory', 'dir', 'folder', 'root'], 'include': ['include_pattern', 'file_pattern']}}, 'glob': {'category': ToolCategory.SEARCH.value, 'names': {'claude_code': 'Glob', 'antigravity': 'Glob', 'codex_cli': 'find_files', 'gemini_cli': 'glob', 'qwen_code': 'find', 'opencode': 'find'}, 'params': {'pattern': ['glob', 'glob_pattern', 'file_pattern'], 'path': ['directory', 'dir', 'root']}}, 'ls': {'category': ToolCategory.NAVIGATION.value, 'names': {'claude_code': 'LS', 'antigravity': 'LS', 'codex_cli': 'list_directory', 'gemini_cli': 'ls', 'qwen_code': 'list', 'opencode': 'list'}, 'params': {'path': ['directory', 'dir', 'folder']}}, 'task': {'category': ToolCategory.TASK.value, 'names': {'claude_code': 'Task', 'antigravity': 'Task', 'codex_cli': 'spawn_task', 'gemini_cli': 'create_task', 'qwen_code': 'task', 'opencode': 'task'}, 'params': {'description': ['prompt', 'task', 'instruction'], 'subagent_type': ['agent_type', 'type', 'mode']}}, 'agentdispatch': {'category': ToolCategory.TASK.value, 'names': {'claude_code': 'AgentDispatch', 'antigravity': 'AgentDispatch', 'codex_cli': 'dispatch_agent', 'gemini_cli': 'agent', 'qwen_code': 'dispatch', 'opencode': 'dispatch'}, 'params': {'agent_id': ['id', 'agent'], 'task': ['prompt', 'instruction', 'message']}}, 'webfetch': {'category': ToolCategory.WEB.value, 'names': {'claude_code': 'WebFetch', 'antigravity': 'WebFetch', 'codex_cli': 'fetch_url', 'gemini_cli': 'browse', 'qwen_code': 'fetch', 'opencode': 'fetch'}, 'params': {'url': ['link', 'href', 'address', 'uri']}}, 'websearch': {'category': ToolCategory.WEB.value, 'names': {'claude_code': 'WebSearch', 'antigravity': 'WebSearch', 'codex_cli': 'web_search', 'gemini_cli': 'search_web', 'qwen_code': 'websearch', 'opencode': 'websearch'}, 'params': {'query': ['search', 'q', 'term', 'keywords']}}, 'browser': {'category': ToolCategory.WEB.value, 'names': {'claude_code': 'Browser', 'antigravity': 'Browser', 'codex_cli': 'browser', 'gemini_cli': 'open_browser', 'qwen_code': 'browser', 'opencode': 'browser'}, 'params': {'url': ['link', 'address'], 'action': ['command', 'operation']}}, 'notebookedit': {'category': ToolCategory.NOTEBOOK.value, 'names': {'claude_code': 'NotebookEdit', 'antigravity': 'NotebookEdit', 'codex_cli': 'edit_notebook', 'gemini_cli': 'notebook_edit', 'qwen_code': 'notebookedit', 'opencode': 'notebookedit'}, 'params': {'notebook_path': ['path', 'file', 'notebook'], 'cell_id': ['cell', 'index', 'cell_index'], 'content': ['code', 'source']}}, 'notebookread': {'category': ToolCategory.NOTEBOOK.value, 'names': {'claude_code': 'NotebookRead', 'antigravity': 'NotebookRead', 'codex_cli': 'read_notebook', 'gemini_cli': 'notebook_read', 'qwen_code': 'notebookread', 'opencode': 'notebookread'}, 'params': {'notebook_path': ['path', 'file', 'notebook']}}, 'todoread': {'category': ToolCategory.TODO.value, 'names': {'claude_code': 'TodoRead', 'antigravity': 'TodoRead', 'codex_cli': 'read_todos', 'gemini_cli': 'get_todos', 'qwen_code': 'todoread', 'opencode': 'todoread'}, 'params': {}}, 'todowrite': {'category': ToolCategory.TODO.value, 'names': {'claude_code': 'TodoWrite', 'antigravity': 'TodoWrite', 'codex_cli': 'write_todos', 'gemini_cli': 'set_todos', 'qwen_code': 'todowrite', 'opencode': 'todowrite'}, 'params': {'todos': ['tasks', 'items', 'list']}}}`

## Dependencies & Imports
typing.Dict, typing.Any, typing.Optional, typing.List, enum.Enum, re

## Feature Class: `ToolCategory`
**Description:**
```text
Tool categories for organization.
```

---

## Feature Function: `get_canonical_tool_name`
**Logic & Purpose:**
```text
Get the canonical tool name from any IDE-specific name.

Args:
    tool_name: Tool name from any IDE
    
Returns:
    Canonical tool name or None if not found
```

**Parameters:** `tool_name`
**Variables Used:** `tool_lower, names`
**Implementation:**
```python
def get_canonical_tool_name(tool_name: str) -> Optional[str]:
    """
    Get the canonical tool name from any IDE-specific name.
    
    Args:
        tool_name: Tool name from any IDE
        
    Returns:
        Canonical tool name or None if not found
    """
    tool_lower = tool_name.lower()
    if tool_lower in TOOL_REGISTRY:
        return tool_lower
    for canonical, config in TOOL_REGISTRY.items():
        names = config.get('names', {})
        for ide_name in names.values():
            if ide_name.lower() == tool_lower:
                return canonical
    return None
```

---

## Feature Function: `convert_tool_name`
**Logic & Purpose:**
```text
Convert a tool name to the target IDE's format.

Args:
    tool_name: Source tool name (any format)
    target_ide: Target IDE identifier
    
Returns:
    Tool name in target IDE's format
```

**Parameters:** `tool_name, target_ide`
**Variables Used:** `names, config, canonical`
**Implementation:**
```python
def convert_tool_name(tool_name: str, target_ide: str) -> str:
    """
    Convert a tool name to the target IDE's format.
    
    Args:
        tool_name: Source tool name (any format)
        target_ide: Target IDE identifier
        
    Returns:
        Tool name in target IDE's format
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return tool_name
    config = TOOL_REGISTRY.get(canonical, {})
    names = config.get('names', {})
    return names.get(target_ide, tool_name)
```

---

## Feature Function: `normalize_tool_params`
**Logic & Purpose:**
```text
Normalize tool parameters to target IDE format.

Args:
    tool_name: Tool name (any format)
    params: Parameter dict
    target_ide: Target IDE identifier
    
Returns:
    Normalized parameter dict
```

**Parameters:** `tool_name, params, target_ide`
**Variables Used:** `result, param_mappings, config, canonical`
**Implementation:**
```python
def normalize_tool_params(tool_name: str, params: Dict[str, Any], target_ide: str='claude_code') -> Dict[str, Any]:
    """
    Normalize tool parameters to target IDE format.
    
    Args:
        tool_name: Tool name (any format)
        params: Parameter dict
        target_ide: Target IDE identifier
        
    Returns:
        Normalized parameter dict
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return params
    config = TOOL_REGISTRY.get(canonical, {})
    param_mappings = config.get('params', {})
    result = dict(params)
    for canonical_param, variants in param_mappings.items():
        for variant in variants:
            if variant in result and canonical_param not in result:
                result[canonical_param] = result.pop(variant)
                break
    return result
```

---

## Feature Function: `get_tool_params_for_ide`
**Logic & Purpose:**
```text
Get the expected parameter names for a tool in a specific IDE.

Args:
    canonical_tool: Canonical tool name
    ide: IDE identifier
    
Returns:
    List of expected parameter names
```

**Parameters:** `canonical_tool, ide`
**Variables Used:** `config, param_mappings`
**Implementation:**
```python
def get_tool_params_for_ide(canonical_tool: str, ide: str) -> List[str]:
    """
    Get the expected parameter names for a tool in a specific IDE.
    
    Args:
        canonical_tool: Canonical tool name
        ide: IDE identifier
        
    Returns:
        List of expected parameter names
    """
    config = TOOL_REGISTRY.get(canonical_tool, {})
    param_mappings = config.get('params', {})
    if ide in ['claude_code', 'antigravity']:
        return list(param_mappings.keys())
    return list(param_mappings.keys())
```

---

## Feature Function: `list_all_tools`
**Logic & Purpose:**
```text
Get list of all canonical tool names.
```

**Parameters:** ``
**Implementation:**
```python
def list_all_tools() -> List[str]:
    """Get list of all canonical tool names."""
    return list(TOOL_REGISTRY.keys())
```

---

## Feature Function: `get_tools_by_category`
**Logic & Purpose:**
```text
Get all tools in a category.
```

**Parameters:** `category`
**Implementation:**
```python
def get_tools_by_category(category: str) -> List[str]:
    """Get all tools in a category."""
    return [name for name, config in TOOL_REGISTRY.items() if config.get('category') == category]
```

---

## Feature Function: `get_tool_info`
**Logic & Purpose:**
```text
Get full information about a tool.

Args:
    tool_name: Tool name (any format)
    
Returns:
    Tool configuration dict or None
```

**Parameters:** `tool_name`
**Variables Used:** `canonical`
**Implementation:**
```python
def get_tool_info(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get full information about a tool.
    
    Args:
        tool_name: Tool name (any format)
        
    Returns:
        Tool configuration dict or None
    """
    canonical = get_canonical_tool_name(tool_name)
    if not canonical:
        return None
    return TOOL_REGISTRY.get(canonical)
```

---

## Feature Function: `sanitize_function_name`
**Logic & Purpose:**
```text
Sanitize a function/tool name to be compatible with all providers.

Addresses the INVALID_ARGUMENT errors that occur when tool names:
- Start with dots, colons, dashes, or digits
- Contain invalid characters or uppercase letters (some providers)
- Exceed the maximum length (64 chars for most providers)

This is equivalent to the SanitizeFunctionName utility in
CLIProxyAPI PR #803, with added lowercase conversion for Google/Gemini compatibility.

Args:
    name: Original function/tool name
    max_length: Maximum allowed length (default 64)

Returns:
    Sanitized function name safe for all providers
```

**Parameters:** `name, max_length`
**Variables Used:** `sanitized`
**Implementation:**
```python
def sanitize_function_name(name: str, max_length: int=64) -> str:
    """
    Sanitize a function/tool name to be compatible with all providers.

    Addresses the INVALID_ARGUMENT errors that occur when tool names:
    - Start with dots, colons, dashes, or digits
    - Contain invalid characters or uppercase letters (some providers)
    - Exceed the maximum length (64 chars for most providers)

    This is equivalent to the SanitizeFunctionName utility in
    CLIProxyAPI PR #803, with added lowercase conversion for Google/Gemini compatibility.

    Args:
        name: Original function/tool name
        max_length: Maximum allowed length (default 64)

    Returns:
        Sanitized function name safe for all providers
    """
    if not name:
        return '_unnamed'
    sanitized = name.lower()
    sanitized = re.sub('[^a-z0-9_.:\\-]', '', sanitized)
    sanitized = sanitized.lstrip('.:-')
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    if not sanitized:
        sanitized = '_tool'
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized
```

---

## Feature Function: `sanitize_tool_declarations`
**Logic & Purpose:**
```text
Sanitize all tool declarations in a list for provider compatibility.

Args:
    tools: List of tool definitions (OpenAI function calling format)
    
Returns:
    Tools with sanitized function names
```

**Parameters:** `tools`
**Variables Used:** `func, original_name, result, tool_copy`
**Implementation:**
```python
def sanitize_tool_declarations(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize all tool declarations in a list for provider compatibility.
    
    Args:
        tools: List of tool definitions (OpenAI function calling format)
        
    Returns:
        Tools with sanitized function names
    """
    if not tools:
        return tools
    result = []
    for tool in tools:
        tool_copy = dict(tool)
        if 'function' in tool_copy:
            func = dict(tool_copy['function'])
            original_name = func.get('name', '')
            func['name'] = sanitize_function_name(original_name)
            tool_copy['function'] = func
        result.append(tool_copy)
    return result
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/io.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/io.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/scraper_web.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/scraper_web.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/logger.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/logger.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/fetcher_api.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/fetcher_api.py`

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
**Variables Used:** `models_list, cleaned, data, filtered_models, headers, filtered, own_client, pattern, pricing, wait, models, response, model, client, endpoint`
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
                    if pricing.get('prompt') is None or pricing.get('completion') is None:
                        logger.warning(f"Skipping model {item.get('id')}: missing required pricing fields (prompt/completion)")
                        continue
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
**Variables Used:** `pricing, cleaned, val`
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
                pricing[key] = coerce_numeric(pricing[key])
                if pricing[key] == -1:
                    pricing[key] = None
        cleaned['pricing'] = pricing
    for field in ['context_length', 'max_output_tokens', 'created']:
        if field in cleaned:
            cleaned[field] = coerce_numeric(cleaned[field])
    return cleaned
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/models.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/models.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/config.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/config.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/exceptions.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/exceptions.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/main.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/main.py`

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
**Variables Used:** `scraped_data, results, cost, start, scrape_duration, total_token_usage`
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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/meta.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/meta.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/__init__.py`

**Module Overview**: 
```text
OpenRouter Model Scout package.
```

## Global Presets & Variables
- `__version__` = `'0.1.0'`


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/normalizer.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/normalizer.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/change_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/change_detector.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/integration.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/integration.py`

**Module Overview**: 
```text
Model Scout Integration

Integrates the model-scraper with the proxy to:
- Run model-scraper to fetch/update OpenRouter models
- Convert scraper output to proxy's model catalog format
- Expose APIs for curated model lists

Usage:
    from src.services.openrouter_model_scout.integration import ModelScoutIntegration

    scout = ModelScoutIntegration()

    # Run a sync
    await scout.run_sync()

    # Get curated models
    free_models = scout.get_free_models()
    smartest = scout.get_smartest_models()
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `SCOUT_DIR` = `Path(__file__).parent`
- `REPO_ROOT` = `Path(__file__).parent.parent.parent.parent`
- `SCOUT_DATA_DIR` = `REPO_ROOT / 'models' / 'scout'`
- `SCOUT_MODELS_PATH` = `SCOUT_DATA_DIR / 'models.json'`
- `SCOUT_LEADERBOARD_PATH` = `SCOUT_DATA_DIR / 'leaderboard.json'`
- `SCOUT_META_PATH` = `SCOUT_DATA_DIR / 'meta.json'`
- `PROXY_MODELS_DIR` = `REPO_ROOT / 'models'`
- `PROXY_CATALOG_PATH` = `PROXY_MODELS_DIR / 'model_catalog.json'`

## Dependencies & Imports
json, logging, os, subprocess, time, datetime.datetime, datetime.timezone, pathlib.Path, typing.Dict, typing.List, typing.Optional, typing.Any

## Feature Class: `ModelScoutIntegration`
**Description:**
```text
Integration layer between model-scraper and proxy.
```

### Method: `__init__`
**Parameters:** `self, data_dir`
**Implementation:**
```python
def __init__(self, data_dir: Optional[Path]=None):
    self.data_dir = data_dir or SCOUT_DATA_DIR
    self.data_dir.mkdir(parents=True, exist_ok=True)
    self._leaderboard: Optional[Dict] = None
    self._models: Optional[List[Dict]] = None
    self._last_sync: Optional[datetime] = None
    self._load()
```

### Method: `_load`
**Logic & Purpose:**
```text
Load cached data from disk.
```

**Parameters:** `self`
**Variables Used:** `last_run, meta`
**Implementation:**
```python
def _load(self):
    """Load cached data from disk."""
    if SCOUT_LEADERBOARD_PATH.exists():
        try:
            self._leaderboard = json.loads(SCOUT_LEADERBOARD_PATH.read_text())
            logger.info(f'Loaded leaderboard from {SCOUT_LEADERBOARD_PATH}')
        except Exception as e:
            logger.warning(f'Failed to load leaderboard: {e}')
            self._leaderboard = None
    if SCOUT_MODELS_PATH.exists():
        try:
            self._models = json.loads(SCOUT_MODELS_PATH.read_text())
            logger.info(f'Loaded {len(self._models)} models from cache')
        except Exception as e:
            logger.warning(f'Failed to load models: {e}')
            self._models = None
    if SCOUT_META_PATH.exists():
        try:
            meta = json.loads(SCOUT_META_PATH.read_text())
            last_run = meta.get('last_run')
            if last_run and isinstance(last_run, str):
                self._last_sync = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f'Failed to load meta: {e}')
```

### Method: `_save_leaderboard`
**Logic & Purpose:**
```text
Save leaderboard data.
```

**Parameters:** `self, data`
**Implementation:**
```python
def _save_leaderboard(self, data: Dict):
    """Save leaderboard data."""
    SCOUT_LEADERBOARD_PATH.write_text(json.dumps(data, indent=2))
    self._leaderboard = data
```

### Method: `_save_models`
**Logic & Purpose:**
```text
Save models data.
```

**Parameters:** `self, models`
**Implementation:**
```python
def _save_models(self, models: List[Dict]):
    """Save models data."""
    SCOUT_MODELS_PATH.write_text(json.dumps(models, indent=2))
    self._models = models
```

### Method: `is_sync_needed`
**Logic & Purpose:**
```text
Check if a new sync is needed.
```

**Parameters:** `self, max_age_hours`
**Variables Used:** `age, now`
**Implementation:**
```python
def is_sync_needed(self, max_age_hours: int=24) -> bool:
    """Check if a new sync is needed."""
    if not self._last_sync:
        return True
    now = datetime.now(timezone.utc)
    age = (now - self._last_sync).total_seconds()
    return age > max_age_hours * 3600
```

### Method: `run_sync`
**Logic & Purpose:**
```text
Run model-scraper sync.

Args:
    force: Force sync even if not needed

Returns:
    Dict with sync results
```

**Parameters:** `self, force`
**Variables Used:** `result, config, api_key`
**Implementation:**
```python
async def run_sync(self, force: bool=False) -> Dict[str, Any]:
    """
        Run model-scraper sync.

        Args:
            force: Force sync even if not needed

        Returns:
            Dict with sync results
        """
    if not force and (not self.is_sync_needed()):
        logger.info('Model sync not needed (recently synced)')
        return {'status': 'skipped', 'reason': 'recently_synced'}
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        from src.core.config import Config
        config = Config()
        api_key = config.provider_api_key or os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return {'status': 'error', 'error': 'No OPENROUTER_API_KEY available'}
    logger.info('Starting model-scraper sync...')
    try:
        result = await self._run_scout(api_key, force=force)
        if result['returncode'] == 0:
            self._load()
            self._convert_to_proxy_catalog()
            return {'status': 'success', 'models_count': len(self._models) if self._models else 0, 'leaderboard': list(self._leaderboard.keys()) if self._leaderboard else []}
        else:
            logger.error(f"Model-scraper failed: {result.get('stderr', '')}")
            return {'status': 'error', 'error': result.get('stderr', 'Unknown error')}
    except Exception as e:
        logger.exception('Model sync failed')
        return {'status': 'error', 'error': str(e)}
```

### Method: `_run_scout`
**Logic & Purpose:**
```text
Run the model-scraper CLI.
```

**Parameters:** `self, api_key, force`
**Variables Used:** `env, result, python_path, scout_cmd`
**Implementation:**
```python
async def _run_scout(self, api_key: str, force: bool=True) -> Dict[str, Any]:
    """Run the model-scraper CLI."""
    env = os.environ.copy()
    env['OPENROUTER_API_KEY'] = api_key
    env['DATA_DIR'] = str(self.data_dir)
    env['LOG_LEVEL'] = 'INFO'
    python_path = str(SCOUT_DIR.parent)
    env['PYTHONPATH'] = python_path + ':' + env.get('PYTHONPATH', '')
    scout_cmd = ['python', '-m', 'openrouter_model_scout.main', '--fast-only']
    if force:
        scout_cmd.append('--force')
    result = subprocess.run(scout_cmd, capture_output=True, text=True, env=env, cwd=str(SCOUT_DIR), timeout=300)
    return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
```

### Method: `_convert_to_proxy_catalog`
**Logic & Purpose:**
```text
Convert model-scraper output to proxy's catalog format.
```

**Parameters:** `self`
**Variables Used:** `catalog, model_id, models`
**Implementation:**
```python
def _convert_to_proxy_catalog(self):
    """Convert model-scraper output to proxy's catalog format."""
    if not self._leaderboard:
        logger.warning('No leaderboard data to convert')
        return
    catalog = {'generated_at': self._leaderboard.get('generated_at', datetime.now(timezone.utc).isoformat()), 'models': {}, 'all_models': {}}
    for category in ['smartest', 'coding', 'free', 'value']:
        if category in self._leaderboard:
            models = self._leaderboard[category]
            catalog['models'][category] = [{'id': m.get('id', ''), 'name': m.get('name', m.get('id', '')), 'context_length': m.get('context_length', 128000), 'max_output': m.get('max_output', 4096), 'intelligence_score': m.get('intelligence_score'), 'throughput_tps': m.get('throughput_tps'), 'price_per_1m_input': m.get('price_per_1m_input', 0), 'price_per_1m_output': m.get('price_per_1m_output', 0), 'is_free': ':free' in m.get('id', '').lower()} for m in models]
            for m in models:
                model_id = m.get('id', '')
                if model_id:
                    catalog['all_models'][model_id] = m
    PROXY_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PROXY_CATALOG_PATH.write_text(json.dumps(catalog, indent=2))
    logger.info(f'Saved proxy model catalog to {PROXY_CATALOG_PATH}')
```

### Method: `get_free_models`
**Logic & Purpose:**
```text
Get free models from leaderboard.
```

**Parameters:** `self, limit`
**Implementation:**
```python
def get_free_models(self, limit: int=10) -> List[Dict]:
    """Get free models from leaderboard."""
    if not self._leaderboard:
        return []
    return self._leaderboard.get('free', [])[:limit]
```

### Method: `get_smartest_models`
**Logic & Purpose:**
```text
Get smartest models from leaderboard.
```

**Parameters:** `self, limit`
**Implementation:**
```python
def get_smartest_models(self, limit: int=10) -> List[Dict]:
    """Get smartest models from leaderboard."""
    if not self._leaderboard:
        return []
    return self._leaderboard.get('smartest', [])[:limit]
```

### Method: `get_coding_models`
**Logic & Purpose:**
```text
Get coding models from leaderboard.
```

**Parameters:** `self, limit`
**Implementation:**
```python
def get_coding_models(self, limit: int=10) -> List[Dict]:
    """Get coding models from leaderboard."""
    if not self._leaderboard:
        return []
    return self._leaderboard.get('coding', [])[:limit]
```

### Method: `get_value_models`
**Logic & Purpose:**
```text
Get value models from leaderboard.
```

**Parameters:** `self, limit`
**Implementation:**
```python
def get_value_models(self, limit: int=10) -> List[Dict]:
    """Get value models from leaderboard."""
    if not self._leaderboard:
        return []
    return self._leaderboard.get('value', [])[:limit]
```

### Method: `get_all_models`
**Logic & Purpose:**
```text
Get all models.
```

**Parameters:** `self`
**Implementation:**
```python
def get_all_models(self) -> List[Dict]:
    """Get all models."""
    return self._models or []
```

### Method: `get_model_by_id`
**Logic & Purpose:**
```text
Get a specific model by ID.
```

**Parameters:** `self, model_id`
**Implementation:**
```python
def get_model_by_id(self, model_id: str) -> Optional[Dict]:
    """Get a specific model by ID."""
    if not self._models:
        return None
    return next((m for m in self._models if m.get('id') == model_id), None)
```

### Method: `search_models`
**Logic & Purpose:**
```text
Search models by name.
```

**Parameters:** `self, query, limit`
**Variables Used:** `results, query_lower`
**Implementation:**
```python
def search_models(self, query: str, limit: int=20) -> List[Dict]:
    """Search models by name."""
    if not self._models:
        return []
    query_lower = query.lower()
    results = [m for m in self._models if query_lower in m.get('id', '').lower() or query_lower in m.get('name', '').lower()]
    return results[:limit]
```

### Method: `get_last_sync_time`
**Logic & Purpose:**
```text
Get timestamp of last successful sync.
```

**Parameters:** `self`
**Implementation:**
```python
def get_last_sync_time(self) -> Optional[datetime]:
    """Get timestamp of last successful sync."""
    return self._last_sync
```

---

## Feature Function: `get_model_scout`
**Logic & Purpose:**
```text
Get the model scout singleton.
```

**Parameters:** ``
**Variables Used:** `_model_scout`
**Implementation:**
```python
def get_model_scout() -> ModelScoutIntegration:
    """Get the model scout singleton."""
    global _model_scout
    if _model_scout is None:
        _model_scout = ModelScoutIntegration()
    return _model_scout
```

---


