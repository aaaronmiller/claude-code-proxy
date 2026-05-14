# File Audit: /home/cheta/code/claude-code-proxy/src/api/openai_endpoints.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/openai_endpoints.py`

**Module Overview**: 
```text
OpenAI-Compatible Endpoint

Provides /v1/chat/completions endpoint for OpenAI-format IDEs:
- Codex CLI
- Gemini CLI
- Qwen Code
- OpenCode

This enables any OpenAI-format IDE to connect to VibeProxy and other
backends through this proxy.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `router` = `APIRouter()`

## Dependencies & Imports
json, time, uuid, typing.Optional, typing.Dict, typing.Any, typing.List, fastapi.APIRouter, fastapi.Request, fastapi.HTTPException, fastapi.Response, fastapi.responses.StreamingResponse, pydantic.BaseModel, pydantic.Field, src.core.config.Config, src.core.client.OpenAIClient, src.core.model_manager.ModelManager, src.services.ide.detect_ide, src.services.ide.IDE, src.services.tools.normalize_tool_params, src.services.tools.convert_tool_name, src.services.tools.sanitize_function_name, src.services.providers.detect_provider, src.services.providers.get_normalization_level, src.services.conversion.response_converter.streaming_transform_partial, src.services.conversion.response_converter.normalize_tool_arguments, src.core.constants.Constants, logging

## Feature Class: `OpenAIMessage`
**Description:**
```text
OpenAI message format.
```

---

## Feature Class: `OpenAIFunction`
**Description:**
```text
OpenAI function definition.
```

---

## Feature Class: `OpenAITool`
**Description:**
```text
OpenAI tool definition.
```

---

## Feature Class: `OpenAIChatRequest`
**Description:**
```text
OpenAI chat completion request.
```

---

## Feature Function: `normalize_openai_tools_for_provider`
**Logic & Purpose:**
```text
Normalize tool definitions for the target provider.

Converts tool names from source IDE format to Claude Code format,
which is then properly handled by the existing normalization logic.
```

**Parameters:** `tools, provider, source_ide`
**Variables Used:** `params, tool_copy, normalized_props, props, converted_name, original_name, func, normalized`
**Implementation:**
```python
def normalize_openai_tools_for_provider(tools: List[Dict[str, Any]], provider: str, source_ide: str) -> List[Dict[str, Any]]:
    """
    Normalize tool definitions for the target provider.

    Converts tool names from source IDE format to Claude Code format,
    which is then properly handled by the existing normalization logic.
    """
    if not tools:
        return tools
    normalized = []
    for tool in tools:
        tool_copy = dict(tool)
        if 'function' in tool_copy:
            func = dict(tool_copy['function'])
            original_name = func.get('name', '')
            converted_name = convert_tool_name(original_name, 'claude_code')
            func['name'] = sanitize_function_name(converted_name)
            if 'parameters' in func and func['parameters']:
                params = func['parameters']
                if 'properties' in params:
                    props = params.get('properties', {})
                    normalized_props = {}
                    for key, val in props.items():
                        normalized_props[key] = val
                    params['properties'] = normalized_props
            tool_copy['function'] = func
        normalized.append(tool_copy)
    return normalized
```

---

## Feature Function: `normalize_tool_call_response`
**Logic & Purpose:**
```text
Normalize tool calls in response back to target IDE format.

This converts Claude Code format tool names back to the source IDE format.
```

**Parameters:** `tool_calls, provider, target_ide`
**Variables Used:** `args, tc_copy, original_name, func, normalized`
**Implementation:**
```python
def normalize_tool_call_response(tool_calls: List[Dict[str, Any]], provider: str, target_ide: str) -> List[Dict[str, Any]]:
    """
    Normalize tool calls in response back to target IDE format.

    This converts Claude Code format tool names back to the source IDE format.
    """
    if not tool_calls:
        return tool_calls
    normalized = []
    for tc in tool_calls:
        tc_copy = dict(tc)
        if 'function' in tc_copy:
            func = dict(tc_copy['function'])
            original_name = func.get('name', '')
            func['name'] = convert_tool_name(original_name, target_ide)
            if 'arguments' in func:
                try:
                    args = json.loads(func['arguments']) if isinstance(func['arguments'], str) else func['arguments']
                    args = normalize_tool_arguments(original_name, args, provider)
                    func['arguments'] = json.dumps(args) if isinstance(func['arguments'], str) else args
                except (json.JSONDecodeError, TypeError):
                    pass
            tc_copy['function'] = func
        normalized.append(tc_copy)
    return normalized
```

---

## Feature Function: `openai_chat_completions`
**Logic & Purpose:**
```text
OpenAI-compatible chat completions endpoint.

Accepts requests from Codex CLI, Gemini CLI, Qwen Code, OpenCode
and routes them to VibeProxy or other configured backends.
```

**Parameters:** `request, body`
**Variables Used:** `response_dict, openai_client, headers, cascade_enabled, _chain, req, saw_data_chunk, provider, chunk_no_usage, delta, start_time, duration_ms, config, error_chunk, choices, model_manager, client, stream, openai_request, request_id, message, stream_lines, chunk_dict, usage, chunk_usage_only, has_stop, source_ide, api_key, base_url, custom_headers, tier, response, saw_done, endpoint, payload`
**Implementation:**
```python
@router.post('/v1/chat/completions')
async def openai_chat_completions(request: Request, body: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint.

    Accepts requests from Codex CLI, Gemini CLI, Qwen Code, OpenCode
    and routes them to VibeProxy or other configured backends.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    config = Config()
    api_key = config.openai_api_key
    base_url = config.openai_base_url
    if not api_key:
        raise HTTPException(status_code=500, detail={'error': {'message': 'No API key configured. Set PROVIDER_API_KEY or OPENAI_API_KEY environment variable.', 'type': 'configuration_error', 'code': 'missing_api_key'}})
    if not base_url:
        raise HTTPException(status_code=500, detail={'error': {'message': 'No base URL configured. Set PROVIDER_BASE_URL or OPENAI_BASE_URL environment variable.', 'type': 'configuration_error', 'code': 'missing_base_url'}})
    custom_headers = config.get_custom_headers()
    openai_client = OpenAIClient(api_key, base_url, config.request_timeout, api_version=config.azure_api_version, custom_headers=custom_headers)
    openai_client.configure_per_model_clients(config)
    model_manager = ModelManager(config)
    headers = dict(request.headers)
    source_ide = detect_ide(headers=headers, path=str(request.url.path), body=body.model_dump())
    logger.info(f'[{request_id}] OpenAI endpoint request from IDE: {source_ide}')
    logger.debug(f'[{request_id}] Model requested: {body.model}')
    try:
        routed_model, reasoning_config = model_manager.parse_and_map_model(body.model)
        client = openai_client.get_client_for_model(routed_model, config)
        endpoint = str(client.base_url) if hasattr(client, 'base_url') else config.openai_base_url
        provider = config.provider_for_endpoint(endpoint) if hasattr(config, 'provider_for_endpoint') else config.default_provider
        logger.debug(f'[{request_id}] Routing to {endpoint} (provider: {provider})')
        openai_request = body.model_dump(exclude_none=True)
        openai_request['model'] = routed_model

        def infer_model_tier(model_name: str) -> Optional[str]:

            def norm(name):
                return name.split('/', 1)[1].lower() if name and '/' in name else (name or '').lower()
            req = norm(model_name)
            if req == norm(config.big_model):
                return 'big'
            if req == norm(config.middle_model):
                return 'middle'
            if req == norm(config.small_model):
                return 'small'
            return None
        if openai_request.get('tools'):
            openai_request['tools'] = normalize_openai_tools_for_provider(openai_request['tools'], provider, source_ide)
        tier = infer_model_tier(openai_request.get('model', ''))
        from src.core.proxy_chain import get_chain
        _chain = get_chain()
        cascade_enabled = config.model_cascade and (not _chain.router.passthrough)
        if body.stream:

            async def generate_stream():
                try:
                    saw_data_chunk = False
                    saw_done = False

                    def transform_chunk_dict(chunk_dict: Dict[str, Any]) -> List[str]:
                        for choice in chunk_dict.get('choices', []):
                            delta = choice.get('delta', {})
                            if 'tool_calls' in delta and delta['tool_calls']:
                                delta['tool_calls'] = normalize_tool_call_response(delta['tool_calls'], provider, source_ide)
                        usage = chunk_dict.get('usage')
                        choices = chunk_dict.get('choices', [])
                        has_stop = any((choice.get('finish_reason') for choice in choices))
                        if usage and has_stop:
                            logger.debug(f'[{request_id}] Detected merged usage/stop chunk, splitting...')
                            chunk_no_usage = chunk_dict.copy()
                            if 'usage' in chunk_no_usage:
                                del chunk_no_usage['usage']
                            chunk_usage_only = {'id': chunk_dict.get('id'), 'object': chunk_dict.get('object', 'chat.completion.chunk'), 'created': chunk_dict.get('created'), 'model': chunk_dict.get('model'), 'choices': [], 'usage': usage}
                            return [f'data: {json.dumps(chunk_no_usage)}\n\n', f'data: {json.dumps(chunk_usage_only)}\n\n']
                        return [f'data: {json.dumps(chunk_dict)}\n\n']
                    if cascade_enabled and tier:
                        stream_lines = openai_client.create_chat_completion_stream_with_cascade(openai_request, tier=tier, config=config, request_id=request_id)
                        async for line in stream_lines:
                            if not line.startswith('data: '):
                                continue
                            payload = line[6:].strip()
                            if payload == '[DONE]':
                                saw_done = True
                                yield 'data: [DONE]\n\n'
                                break
                            chunk_dict = json.loads(payload)
                            saw_data_chunk = True
                            for output in transform_chunk_dict(chunk_dict):
                                yield output
                    else:
                        openai_request.pop('stream', None)
                        stream = await client.chat.completions.create(**openai_request, stream=True)
                        async for chunk in stream:
                            chunk_dict = chunk.model_dump()
                            saw_data_chunk = True
                            for output in transform_chunk_dict(chunk_dict):
                                yield output
                        if not saw_data_chunk:
                            logger.error(f'[{request_id}] Upstream stream opened but produced no chunks (endpoint={endpoint}, provider={provider}, model={routed_model})')
                            error_chunk = {'error': {'message': 'Upstream stream closed without any chunks', 'type': 'empty_stream'}}
                            yield f'data: {json.dumps(error_chunk)}\n\n'
                            return
                        yield 'data: [DONE]\n\n'
                        saw_done = True
                    if saw_data_chunk and (not saw_done):
                        logger.warning(f'[{request_id}] Stream ended after data without explicit [DONE] (endpoint={endpoint}, provider={provider}, model={routed_model})')
                except Exception as e:
                    logger.error(f'[{request_id}] Streaming error: {e}')
                    error_chunk = {'error': {'message': str(e), 'type': 'server_error'}}
                    yield f'data: {json.dumps(error_chunk)}\n\n'
            return StreamingResponse(generate_stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'})
        else:
            if cascade_enabled and tier:
                response_dict = await openai_client.create_chat_completion_with_cascade(openai_request, tier=tier, config=config, request_id=request_id)
                response_dict = response_dict if isinstance(response_dict, dict) else response_dict.model_dump()
            else:
                response = await client.chat.completions.create(**openai_request)
                response_dict = response.model_dump()
            for choice in response_dict.get('choices', []):
                message = choice.get('message', {})
                if 'tool_calls' in message and message['tool_calls']:
                    message['tool_calls'] = normalize_tool_call_response(message['tool_calls'], provider, source_ide)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f'[{request_id}] Completed in {duration_ms:.0f}ms')
            return response_dict
    except Exception as e:
        logger.error(f'[{request_id}] Error: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail={'error': {'message': str(e), 'type': 'server_error', 'code': 'internal_error'}})
```

---

## Feature Function: `list_models`
**Logic & Purpose:**
```text
List available models endpoint.

Required for Codex CLI and other OpenAI-format tools.
```

**Parameters:** ``
**Variables Used:** `created, models, config`
**Implementation:**
```python
@router.get('/v1/models')
async def list_models():
    """
    List available models endpoint.

    Required for Codex CLI and other OpenAI-format tools.
    """
    config = Config()
    created = int(time.time())
    model_ids: list[str] = []

    def add_model(model_id: str | None) -> None:
        if model_id and model_id not in model_ids:
            model_ids.append(model_id)
    add_model(config.big_model)
    add_model(config.middle_model)
    add_model(config.small_model)
    for alias in ['opus', 'sonnet', 'sonnet[1m]', 'haiku', 'claude-opus-4-6', 'claude-sonnet-4-6', 'claude-sonnet-4-6[1m]', 'claude-haiku-4-5-20251001']:
        add_model(alias)
    models = [{'id': model_id, 'object': 'model', 'created': created, 'owned_by': 'vibeproxy'} for model_id in model_ids]
    return {'object': 'list', 'data': models}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/endpoints.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/endpoints.py`

## Global Presets & Variables
- `DEBUG_TRAFFIC_LOG` = `os.environ.get('DEBUG_TRAFFIC_LOG', 'false').lower() == 'true'`
- `traffic_logger` = `logging.getLogger('traffic_debugger')`
- `ENABLE_DEDUP` = `os.getenv('ENABLE_REQUEST_DEDUP', 'true').lower() == 'true'`
- `DEDUP_WINDOW` = `float(os.getenv('DEDUP_WINDOW_SECONDS', '3.0'))`
- `request_deduplicator` = `RequestDeduplicator(window_seconds=DEDUP_WINDOW)`
- `router` = `APIRouter()`
- `USE_COMPACT_LOGGER` = `os.getenv('USE_COMPACT_LOGGER', 'false').lower() == 'true'`
- `active_logger` = `compact_logger if USE_COMPACT_LOGGER else request_logger`
- `custom_headers` = `config.get_custom_headers()`
- `openai_client` = `OpenAIClient(config.openai_api_key or '', config.openai_base_url, config.request_timeout, api_version=config.azure_api_version, custom_headers=custom_headers)`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Request, fastapi.Header, fastapi.Depends, fastapi.responses.JSONResponse, fastapi.responses.StreamingResponse, datetime.datetime, uuid, time, os, hashlib, json, typing.Optional, typing.Dict, typing.Any, collections.OrderedDict, threading.Lock, src.core.config.config, src.core.logging.logger, src.core.client.OpenAIClient, src.core.client.VibeProxyUnavailableError, src.models.claude.ClaudeMessagesRequest, src.models.claude.ClaudeTokenCountRequest, src.services.conversion.request_converter.convert_claude_to_openai, src.services.conversion.response_converter.convert_openai_to_claude_response, src.services.conversion.response_converter.convert_openai_streaming_to_claude_with_cancellation, src.services.conversion.response_converter.convert_openai_streaming_to_claude, src.core.model_manager.model_manager, src.services.logging.request_logger.request_logger, src.services.logging.request_logger.RequestLogger, src.services.logging.compact_logger.compact_logger, src.services.usage.usage_tracker.usage_tracker, src.services.usage.model_limits.check_model_limits, src.services.models.model_filter.filter_models, src.services.prompts.prompt_injection_middleware.inject_system_prompts, src.services.usage.model_limits.get_model_limits, src.conversation.crosstalk.crosstalk_orchestrator, src.core.json_detector.json_detector, src.dashboard.dashboard_hooks.dashboard_hooks, src.models.crosstalk.CrosstalkSetupRequest, src.models.crosstalk.CrosstalkSetupResponse, src.models.crosstalk.CrosstalkRunResponse, src.models.crosstalk.CrosstalkStatusResponse, src.models.crosstalk.CrosstalkListResponse, src.models.crosstalk.CrosstalkDeleteResponse, src.models.crosstalk.CrosstalkError, logging

## Feature Class: `RequestDeduplicator`
**Description:**
```text
Deduplicates requests based on content hash within a time window.

When Claude Code retries a request (e.g., after malformed tool call response),
this prevents processing the same request multiple times and causing duplicate
terminal output.
```

### Method: `__init__`
**Parameters:** `self, window_seconds, max_cache_size`
**Implementation:**
```python
def __init__(self, window_seconds: float=5.0, max_cache_size: int=100):
    self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    self._lock = Lock()
    self._window_seconds = window_seconds
    self._max_cache_size = max_cache_size
```

### Method: `_extract_session_fingerprint`
**Logic & Purpose:**
```text
Extract a stable per-session fingerprint from Claude Code metadata.
```

**Parameters:** `self, request`
**Variables Used:** `system, text, user_id`
**Implementation:**
```python
def _extract_session_fingerprint(self, request: 'ClaudeMessagesRequest') -> str:
    """Extract a stable per-session fingerprint from Claude Code metadata."""
    if request.metadata and isinstance(request.metadata, dict):
        user_id = request.metadata.get('user_id')
        if user_id:
            return str(user_id)
    system = getattr(request, 'system', None)
    if isinstance(system, list):
        for block in system:
            if isinstance(block, dict):
                text = block.get('text', '')
            else:
                text = getattr(block, 'text', '')
            if text and 'cc_version=' in text:
                return text[:256]
    return 'unknown-session'
```

### Method: `_compute_hash`
**Logic & Purpose:**
```text
Compute a retry hash with strong session isolation.
```

**Parameters:** `self, request, client_ip`
**Variables Used:** `text, session_fingerprint, content_parts, block_type, content, tool_names, content_str`
**Implementation:**
```python
def _compute_hash(self, request: 'ClaudeMessagesRequest', client_ip: str='unknown') -> str:
    """Compute a retry hash with strong session isolation."""
    session_fingerprint = self._extract_session_fingerprint(request)
    content_parts = [session_fingerprint, client_ip, request.model]
    if request.stream is not None:
        content_parts.append(str(request.stream))
    if getattr(request, 'max_tokens', None) is not None:
        content_parts.append(str(request.max_tokens))
    if getattr(request, 'temperature', None) is not None:
        content_parts.append(str(request.temperature))
    if getattr(request, 'tool_choice', None):
        content_parts.append(json_module.dumps(request.tool_choice, sort_keys=True, default=str))
    if getattr(request, 'tools', None):
        tool_names = [getattr(tool, 'name', '') for tool in request.tools]
        content_parts.append(','.join(tool_names))
    for msg in request.messages:
        content_parts.append(getattr(msg, 'role', ''))
        if hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, str):
                content_parts.append(content[:400])
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        block_type = block.get('type', '')
                        content_parts.append(block_type)
                        if block_type == 'text':
                            text = block.get('text', '')
                            if text:
                                content_parts.append(text[:200])
                        if block_type == 'tool_use':
                            content_parts.append(block.get('id', ''))
                            content_parts.append(block.get('name', ''))
                        if block_type == 'tool_result':
                            content_parts.append(block.get('tool_use_id', ''))
                    else:
                        block_type = getattr(block, 'type', '')
                        content_parts.append(block_type)
                        if block_type == 'text':
                            text = getattr(block, 'text', '')
                            if text:
                                content_parts.append(text[:200])
                        if block_type == 'tool_use':
                            content_parts.append(getattr(block, 'id', ''))
                            content_parts.append(getattr(block, 'name', ''))
                        if block_type == 'tool_result':
                            content_parts.append(getattr(block, 'tool_use_id', ''))
    content_str = '|'.join((str(x) for x in content_parts))
    return hashlib.sha256(content_str.encode()).hexdigest()[:16]
```

### Method: `check_duplicate`
**Logic & Purpose:**
```text
Check if request is a duplicate within the time window.
Uses client IP to distinguish between different sessions.

Args:
    request: The Claude messages request
    client_ip: Client IP address to include in hash for session isolation

Returns:
    (is_duplicate, request_hash, cached_response or None)
```

**Parameters:** `self, request, client_ip`
**Variables Used:** `age, expired, request_hash, cached, current_time`
**Implementation:**
```python
def check_duplicate(self, request: 'ClaudeMessagesRequest', client_ip: str='unknown') -> tuple[bool, str, Optional[Dict]]:
    """
        Check if request is a duplicate within the time window.
        Uses client IP to distinguish between different sessions.

        Args:
            request: The Claude messages request
            client_ip: Client IP address to include in hash for session isolation

        Returns:
            (is_duplicate, request_hash, cached_response or None)
        """
    request_hash = self._compute_hash(request, client_ip)
    current_time = time.time()
    with self._lock:
        expired = []
        for h, data in self._cache.items():
            if current_time - data['timestamp'] > self._window_seconds:
                expired.append(h)
        for h in expired:
            del self._cache[h]
        if request_hash in self._cache:
            cached = self._cache[request_hash]
            age = current_time - cached['timestamp']
            if age < self._window_seconds:
                if cached.get('response') and (not getattr(request, 'stream', False)):
                    cached['count'] += 1
                    logger.warning(f"Duplicate request detected (hash={request_hash[:8]}, count={cached['count']}, age={age:.2f}s)")
                    return (True, request_hash, cached.get('response'))
                logger.debug(f"Request {request_hash[:8]} similar to in-flight request (age={age:.2f}s, count={cached['count']}) - allowing")
        self._cache[request_hash] = {'timestamp': current_time, 'count': 1, 'response': None}
        self._cache.move_to_end(request_hash)
        while len(self._cache) > self._max_cache_size:
            self._cache.popitem(last=False)
        return (False, request_hash, None)
```

### Method: `cache_response`
**Logic & Purpose:**
```text
Cache a response for potential duplicate requests.
```

**Parameters:** `self, request_hash, response`
**Implementation:**
```python
def cache_response(self, request_hash: str, response: Dict):
    """Cache a response for potential duplicate requests."""
    with self._lock:
        if request_hash in self._cache:
            self._cache[request_hash]['response'] = response
```

---

## Feature Function: `log_request_body`
**Logic & Purpose:**
```text
Middleware-like function to log request body if enabled.
```

**Parameters:** `request`
**Variables Used:** `body, body_str_filtered, body_str`
**Implementation:**
```python
async def log_request_body(request: Request):
    """Middleware-like function to log request body if enabled."""
    if not DEBUG_TRAFFIC_LOG:
        return
    try:
        body = await request.body()
        traffic_logger.info(f'--- INCOMING REQUEST: {request.method} {request.url} ---')
        traffic_logger.info(f'Headers: {dict(request.headers)}')
        try:
            body_str = body.decode('utf-8')
            body_str_filtered = body_str.replace('(no content)', '[empty]').replace('no content', '[empty]')
            if len(body_str_filtered) > 50000:
                traffic_logger.info(f'Body (Truncated): {body_str_filtered[:1000]}... [Total {len(body_str_filtered)} bytes]')
            elif len(body_str_filtered) > 1000:
                traffic_logger.info(f'Body (Truncated): {body_str_filtered[:200]}... [Total {len(body_str_filtered)} bytes]')
            else:
                traffic_logger.info(f'Body: {body_str_filtered}')
        except Exception as _e:
            traffic_logger.info(f'Body (Binary): {len(body)} bytes')
        traffic_logger.info('------------------------------------------------')
    except Exception as e:
        traffic_logger.error(f'Failed to log request: {e}')
```

---

## Feature Function: `validate_and_extract_api_key`
**Logic & Purpose:**
```text
Validate and extract API keys based on operating mode.

Returns:
    OpenAI API key to use for the request (None in proxy mode)

Raises:
    HTTPException: If validation fails
```

**Parameters:** `x_api_key, authorization, openai_api_key`
**Variables Used:** `client_api_key, openai_key`
**Implementation:**
```python
async def validate_and_extract_api_key(x_api_key: Optional[str]=Header(None), authorization: Optional[str]=Header(None), openai_api_key: Optional[str]=Header(None, alias='openai-api-key')) -> Optional[str]:
    """
    Validate and extract API keys based on operating mode.

    Returns:
        OpenAI API key to use for the request (None in proxy mode)

    Raises:
        HTTPException: If validation fails
    """
    client_api_key = None
    openai_key = None
    if x_api_key:
        client_api_key = x_api_key
        logger.debug(f'API key from x-api-key header: {client_api_key[:10]}...')
    elif authorization and authorization.startswith('Bearer '):
        client_api_key = authorization.replace('Bearer ', '')
        logger.debug(f'API key from Authorization header: {client_api_key[:10]}...')
    if openai_api_key:
        openai_key = openai_api_key
        logger.debug(f'OpenAI API key from header: {openai_key[:10]}...')
    if config.passthrough_mode:
        if not openai_key:
            raise HTTPException(status_code=401, detail="Passthrough mode: Please provide your OpenAI API key via 'openai-api-key' header")
        if not config.validate_api_key(openai_key):
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key format. Key must start with 'sk-' and be at least 20 characters")
        logger.debug('Passthrough mode: OpenAI API key validated')
        return openai_key
    if config.anthropic_api_key:
        if not client_api_key or not config.validate_client_api_key(client_api_key):
            logger.warning(f"Invalid API key provided by client. Expected: {config.anthropic_api_key}, Got: {(client_api_key[:10] if client_api_key else 'None')}...")
            raise HTTPException(status_code=401, detail='Invalid API key. Please provide a valid Anthropic API key.')
        logger.debug('Proxy mode: Anthropic API key validation passed')
    return None
```

---

## Feature Function: `create_message`
**Parameters:** `request, http_request, openai_api_key`
**Variables Used:** `api_key_preview, request_start_time, original_pricing, candidate, bg_config, stream_output, openai_response, reasoning_tokens, response_dict, message_count, custom_client, session_fingerprint, has_system, req, original_tier, daily_count, tier_name, audio_tokens, openai_stream, provider, prompt_tokens, resp_content, status, is_default_vibeproxy, model_tier, completion_tokens, claude_response, workspace_name, duration_ms, estimated_cost, match, _use_case_route, _use_case_tier, req_content, cached_tokens, input_text, client, session_id, active_openai_client, openai_request, json_size_bytes, request_id, input_tokens, client_ip, request_hash, message, _orig, stream_input, usage, retry_count, patterns, get_model_pricing, has_json_content, error_message, routed_model, bg_model_str, completion_details, has_tools, has_images, max_retries, original_cost, skip_names, is_vibeproxy_endpoint, active_api_key, tier, original_model, error_response, choices, tool_use_tokens, endpoint`
**Implementation:**
```python
@router.post('/v1/messages')
async def create_message(request: ClaudeMessagesRequest, http_request: Request, openai_api_key: Optional[str]=Depends(validate_and_extract_api_key)):
    await log_request_body(http_request)
    request_start_time = time.time()
    request_id = str(uuid.uuid4())
    client_ip = http_request.client.host if http_request.client else 'unknown'
    request_hash = None
    if ENABLE_DEDUP:
        is_duplicate, request_hash, cached_response = request_deduplicator.check_duplicate(request, client_ip)
        if is_duplicate and cached_response:
            logger.info(f'Request {request_id}: Returning cached response for duplicate request')
            return JSONResponse(content=cached_response)
    try:
        logger.debug(f'Processing Claude request: model={request.model}, stream={request.stream}')
        logger.debug(f'Request ID: {request_id}')
        logger.debug('Request deduplication check passed')
        routed_model, reasoning_config = model_manager.parse_and_map_model(request.model)
        client = openai_client.get_client_for_model(routed_model, config)
        endpoint = str(client.base_url) if hasattr(client, 'base_url') else config.openai_base_url
        provider = config.provider_for_endpoint(endpoint) if hasattr(config, 'provider_for_endpoint') else config.default_provider
        original_tier = None
        is_vibeproxy_endpoint = endpoint and ('127.0.0.1:8317' in endpoint or 'localhost:8317' in endpoint)
        is_default_vibeproxy = config.openai_base_url and ('127.0.0.1:8317' in config.openai_base_url or 'localhost:8317' in config.openai_base_url)
        if is_vibeproxy_endpoint or (original_tier is None and is_default_vibeproxy):
            from src.services.antigravity import is_vibeproxy_available
            if not is_vibeproxy_available():
                tier_name = original_tier or 'DEFAULT'
                logger.warning(f'Request {request_id}: VibeProxy unavailable, falling back from {tier_name} to DEFAULT provider')
                client = openai_client.client
                endpoint = config.openai_base_url
                provider = config.default_provider
                routed_model = config.big_model
        openai_request = convert_claude_to_openai(request, model_manager, target_provider=provider)
        openai_request['model'] = routed_model
        custom_client = None
        active_api_key = openai_api_key
        openai_request['_original_model'] = request.model
        _use_case_tier: Optional[str] = None
        try:
            from src.core.model_router import get_router
            _use_case_route = get_router(config).route(openai_request)
            if _use_case_route:
                openai_request['model'] = _use_case_route.model
                if _use_case_route.base_url:
                    endpoint = _use_case_route.base_url
                    if hasattr(config, 'provider_for_endpoint'):
                        provider = config.provider_for_endpoint(endpoint)
                    active_api_key = _use_case_route.api_key or openai_api_key
                    custom_client = OpenAIClient(active_api_key, endpoint, config.request_timeout, api_version=config.azure_api_version, custom_headers=custom_headers)
                    custom_client.configure_per_model_clients(config)
                _orig = (openai_request.get('_original_model') or '').lower()
                bg_config = getattr(config, 'router_background', '')
                bg_model_str = bg_config.model if hasattr(bg_config, 'model') else str(bg_config)
                if 'haiku' in _orig or _use_case_route.model == bg_model_str:
                    _use_case_tier = 'middle'
                else:
                    _use_case_tier = 'big'
        except Exception as _router_err:
            logger.warning(f'ModelRouter error (non-fatal): {_router_err}')
        openai_request.pop('_original_model', None)
        openai_request.pop('_is_background', None)

        def infer_model_tier(model_name: str) -> Optional[str]:

            def norm(name):
                return name.split('/', 1)[1].lower() if name and '/' in name else (name or '').lower()
            req = norm(model_name)
            if req == norm(config.big_model):
                return 'big'
            if req == norm(config.middle_model):
                return 'middle'
            if req == norm(config.small_model):
                return 'small'
            return None
        logger.debug(f'Request {request_id}: Routing to endpoint: {endpoint}')
        logger.debug(f'Request {request_id}: Using model: {routed_model}')
        if openai_api_key:
            logger.debug(f'Request {request_id}: Using passthrough mode with user-provided API key')
        else:
            api_key_preview = config.openai_api_key[:15] if config.openai_api_key else 'None'
            logger.debug(f'Request {request_id}: Using proxy mode with server API key: {api_key_preview}...')
        message_count = len(request.messages)
        has_system = bool(request.system)
        client_ip = http_request.client.host if http_request.client else 'unknown'
        input_text = ''
        workspace_name = None

        def extract_workspace_name(text: str) -> Optional[str]:
            """Extract workspace/project name from system prompt text."""
            try:
                import re
                import os
                patterns = ['Working directory:\\s+([^\\n]+)', '/git/([^/\\s]+)', '/([a-zA-Z0-9_-]+)(?:/[a-zA-Z0-9_.-]+)*\\s', 'workspace.*?:?\\s+([a-zA-Z0-9_-]+)']
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        if '/' in candidate:
                            candidate = os.path.basename(candidate.rstrip('/'))
                        skip_names = ['users', 'home', 'user', 'documents', 'projects', 'git', 'code', 'my_projects', '0my_projects']
                        if candidate.lower() not in skip_names and len(candidate) > 0:
                            if len(candidate) > 20:
                                return candidate[:17] + '...'
                            return candidate
                return None
            except Exception as e:
                logger.debug(f'Workspace name extraction failed: {e}')
                return None
        if request.system:
            if isinstance(request.system, str):
                input_text += request.system
                workspace_name = extract_workspace_name(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, 'text'):
                        input_text += block.text
                        if not workspace_name and block.text:
                            workspace_name = extract_workspace_name(block.text)
        for msg in request.messages:
            if isinstance(msg.content, str):
                input_text += msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, 'text') and block.text:
                        input_text += block.text
        from src.services.usage.model_limits import get_model_limits
        context_limit, output_limit = get_model_limits(routed_model)
        input_tokens = 0
        if input_text:
            input_tokens = max(1, len(input_text) // 4)
        has_images = False
        has_tools = bool(request.tools)
        for msg in request.messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, 'type') and block.type == 'image':
                        has_images = True
                        break
        active_logger.log_request_start(request_id=request_id, original_model=request.model, routed_model=routed_model, endpoint=endpoint, reasoning_config=reasoning_config, stream=request.stream if request.stream is not None else False, input_text=input_text, context_limit=context_limit, output_limit=output_limit, input_tokens=input_tokens, message_count=message_count, has_system=has_system, has_tools=has_tools, has_images=has_images, client_info=client_ip, workspace_name=workspace_name)
        dashboard_hooks.on_request_start(request_id, {'model': routed_model, 'stream': request.stream, 'has_tools': has_tools, 'has_images': has_images, 'input_tokens': input_tokens})
        if await http_request.is_disconnected():
            logger.warning(f'Client disconnected before processing request_id: {request_id}')
            raise HTTPException(status_code=499, detail='Client disconnected')
        session_fingerprint = request_deduplicator._extract_session_fingerprint(request)
        session_id = hashlib.sha256(session_fingerprint.encode()).hexdigest()[:8]
        if request.stream:
            logger.debug(f'Starting streaming response for request_id: {request_id}')
            try:
                active_openai_client = custom_client if custom_client else openai_client
                tier = infer_model_tier(openai_request.get('model', '')) or _use_case_tier
                if config.model_cascade and tier:
                    openai_stream = active_openai_client.create_chat_completion_stream_with_cascade(openai_request, tier=tier, config=config, request_id=request_id, api_key=active_api_key)
                else:
                    openai_stream = active_openai_client.create_chat_completion_stream(openai_request, request_id, config, api_key=active_api_key)
                logger.debug(f'OpenAI stream created for request_id: {request_id}')

                async def _on_stream_complete(stream_usage, stop_reason, duration_ms, error):
                    """Log streaming request completion to usage tracker and request logger."""
                    try:
                        status = 'error' if error else 'success'
                        stream_input = stream_usage.get('input_tokens', 0) or input_tokens
                        stream_output = stream_usage.get('output_tokens', 0)
                        active_logger.log_request_complete(request_id=request_id, usage=stream_usage, duration_ms=duration_ms, status='OK' if not error else f'ERR: {error[:60]}', model_name=routed_model, stream=True, has_reasoning=bool(reasoning_config))
                        if usage_tracker.enabled:
                            usage_tracker.log_request(request_id=request_id, original_model=request.model, routed_model=routed_model, provider=provider, endpoint=endpoint, input_tokens=stream_input, output_tokens=stream_output, duration_ms=duration_ms, stream=True, message_count=message_count, has_system=has_system, has_tools=has_tools, has_images=has_images, status=status, error_message=error, session_id=session_id, client_ip=client_ip)
                            daily_count = usage_tracker.get_daily_model_request_count(routed_model)
                            logger.info(f'Stream {request_id}: {routed_model} in:{stream_input} out:{stream_output} {duration_ms:.0f}ms {status} UTC-day={daily_count}')
                        dashboard_hooks.on_request_complete(request_id, 'completed' if not error else 'error', {'model': routed_model, 'duration_ms': int(duration_ms), 'input_tokens': stream_input, 'output_tokens': stream_output})
                    except Exception as cb_err:
                        logger.warning(f'Stream completion callback error: {cb_err}')
                return StreamingResponse(convert_openai_streaming_to_claude_with_cancellation(openai_stream, request, logger, http_request, active_openai_client, request_id, config, provider, on_complete=_on_stream_complete), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*'})
            except HTTPException as e:
                logger.error(f'Streaming HTTPException for request_id {request_id}: status={e.status_code}, detail={e.detail}')
                import traceback
                logger.error(f'Streaming traceback: {traceback.format_exc()}')
                error_message = openai_client.classify_openai_error(e.detail)
                error_response = {'type': 'error', 'error': {'type': 'api_error', 'message': error_message}}
                return JSONResponse(status_code=e.status_code, content=error_response)
            except VibeProxyUnavailableError as e:
                logger.error(f'VibeProxy unavailable for request_id {request_id}: {e}')
                error_response = {'type': 'error', 'error': {'type': 'vibeproxy_unavailable', 'message': str(e)}}
                return JSONResponse(status_code=503, content=error_response)
            except Exception as e:
                logger.error(f'Unexpected streaming error for request_id {request_id}: {e}')
                import traceback
                logger.error(f'Streaming traceback: {traceback.format_exc()}')
                error_message = openai_client.classify_openai_error(str(e))
                error_response = {'type': 'error', 'error': {'type': 'api_error', 'message': error_message}}
                return JSONResponse(status_code=500, content=error_response)
        else:
            logger.debug(f'Starting non-streaming response for request_id: {request_id}')
            logger.debug('Request deduplication check passed')
            from src.utils.key_reloader import key_reloader
            import asyncio
            max_retries = 150
            retry_count = 0
            while True:
                try:
                    active_openai_client = custom_client if custom_client else openai_client
                    tier = infer_model_tier(openai_request.get('model', '')) or _use_case_tier
                    if config.model_cascade and tier:
                        openai_response = await active_openai_client.create_chat_completion_with_cascade(openai_request, tier=tier, config=config, request_id=request_id, api_key=active_api_key)
                    else:
                        openai_response = await active_openai_client.create_chat_completion(openai_request, request_id, config, api_key=active_api_key)
                    break
                except VibeProxyUnavailableError as e:
                    logger.error(f'VibeProxy unavailable for request_id {request_id}: {e}')
                    error_response = {'type': 'error', 'error': {'type': 'vibeproxy_unavailable', 'message': str(e)}}
                    return JSONResponse(status_code=503, content=error_response)
                except HTTPException as e:
                    if e.status_code == 401 and (not openai_api_key):
                        if retry_count >= max_retries:
                            logger.error(f'Authentication failed. Timed out waiting for key update.')
                            raise e
                        if retry_count == 0:
                            logger.warning(f'Authentication failed (401). Waiting for key update in profile...')
                            logger.warning(f"Run 'cproxy-init' or the wizard to fix your key.")
                        await asyncio.sleep(2)
                        retry_count += 1
                        if key_reloader.check_for_updates():
                            logger.info('Key update detected! Retrying request...')
                            if custom_client:
                                custom_client.api_key = config.openai_api_key or ''
                                active_api_key = custom_client.api_key
                            else:
                                openai_client.api_key = config.openai_api_key or ''
                            continue
                        if retry_count % 5 == 0:
                            logger.info(f'Still waiting for key update... ({retry_count * 2}s elapsed)')
                    else:
                        raise e
            logger.debug(f'OpenAI response received for request_id: {request_id}')
            logger.debug('Request deduplication check passed')
            duration_ms = (time.time() - request_start_time) * 1000
            usage = openai_response.get('usage') or {}
            has_json_content = False
            json_size_bytes = 0
            if input_text:
                has_json, json_bytes, _ = json_detector.detect_json_in_text(input_text)
                has_json_content = has_json
                json_size_bytes = json_bytes
            provider = 'unknown'
            if 'openrouter' in endpoint.lower():
                provider = 'openrouter'
            elif 'daily-cloudcode-pa' in endpoint.lower() or 'antigravity' in routed_model.lower():
                provider = 'antigravity'
            elif 'openai' in endpoint.lower():
                provider = 'openai'
            elif 'anthropic' in endpoint.lower():
                provider = 'anthropic'
            elif 'azure' in endpoint.lower():
                provider = 'azure'
            try:
                from src.services.usage.cost_calculator import calculate_cost
                estimated_cost = calculate_cost(usage, routed_model)
            except ImportError:
                estimated_cost = 0.0
            except Exception as e:
                logger.warning(f'Failed to calculate cost: {e}')
                estimated_cost = 0.0
            active_logger.log_request_complete(request_id=request_id, usage=usage, duration_ms=duration_ms, status='OK', model_name=routed_model, stream=request.stream if request.stream is not None else False, has_reasoning=bool(reasoning_config))
            if usage_tracker.enabled:
                import json as json_module
                req_content = json_module.dumps(request.model_dump()) if hasattr(request, 'model_dump') else str(request)
                resp_content = json_module.dumps(openai_response) if openai_response else None
                usage = usage or {}
                completion_details = usage.get('completion_tokens_details', {}) or {}
                prompt_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                completion_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                reasoning_tokens = usage.get('reasoning_tokens', 0) or (completion_details.get('reasoning_tokens', 0) if completion_details else 0)
                cached_tokens = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0) if isinstance(usage.get('prompt_tokens_details'), dict) else 0
                audio_tokens = usage.get('completion_tokens_details', {}).get('audio_tokens', 0) if isinstance(usage.get('completion_tokens_details'), dict) else 0
                tool_use_tokens = 0
                if openai_response and isinstance(openai_response, dict):
                    choices = openai_response.get('choices', [])
                    if choices and isinstance(choices[0], dict):
                        message = choices[0].get('message', {})
                        if message.get('tool_calls'):
                            tool_use_tokens = completion_tokens * 0.3
                original_cost = None
                original_model = request.model
                try:
                    from src.services.usage.cost_calculator import calculate_cost, get_model_pricing
                    if routed_model != original_model:
                        original_pricing = get_model_pricing(original_model)
                        if original_pricing:
                            original_cost = calculate_cost(usage, original_model)
                except Exception:
                    get_model_pricing = lambda x: None
                model_tier = None
                if 'free' in routed_model or 'mini' in routed_model.lower() or 'flash' in routed_model.lower():
                    model_tier = 'small'
                elif 'sonnet' in routed_model.lower() or 'medium' in routed_model.lower() or 'turbo' in routed_model.lower():
                    model_tier = 'middle'
                elif 'opus' in routed_model.lower() or 'large' in routed_model.lower() or '4.5' in routed_model.lower():
                    model_tier = 'big'
                elif 'gpt-4o' in routed_model.lower() and 'mini' not in routed_model.lower():
                    model_tier = 'middle'
                try:
                    if get_model_pricing(routed_model) == (0.0, 0.0):
                        model_tier = 'free'
                except Exception:
                    pass
                usage_tracker.log_request(request_id=request_id, original_model=request.model, routed_model=routed_model, provider=provider, endpoint=endpoint, input_tokens=prompt_tokens, output_tokens=completion_tokens, thinking_tokens=reasoning_tokens, duration_ms=duration_ms, estimated_cost=estimated_cost, stream=request.stream if request.stream is not None else False, message_count=message_count, has_system=has_system, has_tools=has_tools, has_images=has_images, status='success', session_id=session_id, client_ip=client_ip, has_json_content=has_json_content, json_size_bytes=json_size_bytes, request_content=req_content, response_content=resp_content, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, reasoning_tokens=reasoning_tokens, cached_tokens=cached_tokens, tool_use_tokens=tool_use_tokens, audio_tokens=audio_tokens, original_cost=original_cost, model_tier=model_tier)
                daily_count = usage_tracker.get_daily_model_request_count(routed_model)
                logger.info(f'Request {request_id}: {routed_model} UTC-day requests={daily_count}')
            claude_response = convert_openai_to_claude_response(openai_response, request, provider)
            logger.debug(f'Claude response created for request_id: {request_id}')
            if ENABLE_DEDUP and request_hash:
                try:
                    if hasattr(claude_response, 'model_dump'):
                        response_dict = claude_response.model_dump()
                    elif hasattr(claude_response, 'dict'):
                        response_dict = claude_response.dict()
                    else:
                        response_dict = claude_response
                    request_deduplicator.cache_response(request_hash, response_dict)
                except Exception as cache_err:
                    logger.debug(f'Failed to cache response for dedup: {cache_err}')
            dashboard_hooks.on_request_complete(request_id, 'completed', {'model': routed_model, 'duration_ms': int(duration_ms), 'input_tokens': usage.get('input_tokens', usage.get('prompt_tokens', 0)), 'output_tokens': usage.get('output_tokens', usage.get('completion_tokens', 0)), 'thinking_tokens': usage.get('thinking_tokens', 0), 'tokens': usage.get('total_tokens', 0), 'cost': estimated_cost, 'tokens_per_sec': int(usage.get('total_tokens', 0) / (duration_ms / 1000)) if duration_ms > 0 else 0, 'has_tools': has_tools, 'has_images': has_images, 'context_tokens': input_tokens, 'context_limit': context_limit})
            return claude_response
    except HTTPException as e:
        duration_ms = (time.time() - request_start_time) * 1000
        logger.error(f'HTTPException in create_message for request_id {request_id}: status={e.status_code}, detail={e.detail}')
        active_logger.log_request_error(request_id=request_id, error=e.detail, duration_ms=duration_ms)
        if usage_tracker.enabled:
            usage_tracker.log_request(request_id=request_id, original_model=request.model, routed_model=routed_model, provider='unknown', endpoint=endpoint, status='error', error_message=str(e.detail), duration_ms=duration_ms, session_id=session_id, client_ip=client_ip, message_count=message_count, input_tokens=input_tokens)
        raise
    except Exception as e:
        import traceback
        duration_ms = (time.time() - request_start_time) * 1000
        logger.error(f'Unexpected error processing request {request_id}: {e}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        error_message = openai_client.classify_openai_error(str(e))
        active_logger.log_request_error(request_id=request_id, error=error_message, duration_ms=duration_ms)
        if usage_tracker.enabled:
            usage_tracker.log_request(request_id=request_id, original_model=request.model, routed_model=routed_model, provider=provider if provider else 'unknown', endpoint=endpoint if endpoint else 'unknown', status='error', error_message=error_message, duration_ms=duration_ms, session_id=session_id, client_ip=client_ip, message_count=message_count, input_tokens=input_tokens)
        dashboard_hooks.on_request_complete(request_id, 'error', {'model': routed_model, 'duration_ms': int(duration_ms), 'error': error_message, 'error_type': 'Unknown'})
        logger.error(f'Unexpected error processing request {request_id}: {e}')
        logger.error(f'Full traceback: {traceback.format_exc()}')
        raise HTTPException(status_code=500, detail=error_message)
```

---

## Feature Function: `count_tokens`
**Parameters:** `request, openai_api_key`
**Variables Used:** `estimated_tokens, total_chars`
**Implementation:**
```python
@router.post('/v1/messages/count_tokens')
async def count_tokens(request: ClaudeTokenCountRequest, openai_api_key: Optional[str]=Depends(validate_and_extract_api_key)):
    try:
        total_chars = 0
        if request.system:
            if isinstance(request.system, str):
                total_chars += len(request.system)
            elif isinstance(request.system, list):
                for block in request.system:
                    if hasattr(block, 'text'):
                        total_chars += len(block.text)
        for msg in request.messages:
            if msg.content is None:
                continue
            elif isinstance(msg.content, str):
                total_chars += len(msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, 'text') and block.text is not None:
                        total_chars += len(block.text)
        estimated_tokens = max(1, total_chars // 4)
        return {'input_tokens': estimated_tokens}
    except Exception as e:
        logger.error(f'Error counting tokens: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `health_check`
**Logic & Purpose:**
```text
Health check endpoint
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/health')
async def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'openai_api_configured': bool(config.openai_api_key), 'api_key_valid': config.validate_api_key(), 'client_api_key_validation': bool(config.anthropic_api_key)}
```

---

## Feature Function: `test_connection`
**Logic & Purpose:**
```text
Test API connectivity to OpenAI
```

**Parameters:** ``
**Variables Used:** `test_request, is_newer_model, test_response`
**Implementation:**
```python
@router.get('/test-connection')
async def test_connection():
    """Test API connectivity to OpenAI"""
    try:
        is_newer_model = model_manager.is_newer_openai_model(config.small_model)
        test_request = {'model': config.small_model, 'messages': [{'role': 'user', 'content': 'Hello'}]}
        if is_newer_model:
            test_request['max_completion_tokens'] = 200
            test_request['temperature'] = 1
        else:
            test_request['max_tokens'] = 5
        test_response = await openai_client.create_chat_completion(test_request, config=config)
        return {'status': 'success', 'message': 'Successfully connected to OpenAI API', 'model_used': config.small_model, 'timestamp': datetime.now().isoformat(), 'response_id': test_response.get('id', 'unknown')}
    except Exception as e:
        logger.error(f'API connectivity test failed: {e}')
        return JSONResponse(status_code=503, content={'status': 'failed', 'error_type': 'API Error', 'message': str(e), 'timestamp': datetime.now().isoformat(), 'suggestions': ['Check your OPENAI_API_KEY is valid', 'Verify your API key has the necessary permissions', 'Check if you have reached rate limits']})
```

---

## Feature Function: `setup_crosstalk`
**Logic & Purpose:**
```text
Setup a new crosstalk session.

This endpoint configures a model-to-model conversation using Exchange-of-Thought
(EoT) paradigms: Memory, Report, Relay, or Debate.
```

**Parameters:** `request`
**Variables Used:** `session_id`
**Implementation:**
```python
@router.post('/v1/crosstalk/setup')
async def setup_crosstalk(request: CrosstalkSetupRequest) -> CrosstalkSetupResponse:
    """
    Setup a new crosstalk session.

    This endpoint configures a model-to-model conversation using Exchange-of-Thought
    (EoT) paradigms: Memory, Report, Relay, or Debate.
    """
    try:
        session_id = await crosstalk_orchestrator.setup_crosstalk(models=request.models, system_prompts=request.system_prompts, paradigm=request.paradigm, iterations=request.iterations, topic=request.topic)
        return CrosstalkSetupResponse(session_id=session_id, status='configured', models=request.models, paradigm=request.paradigm, iterations=request.iterations)
    except Exception as e:
        logger.error(f'Crosstalk setup failed: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Feature Function: `run_crosstalk`
**Logic & Purpose:**
```text
Execute a configured crosstalk session.

Runs the model-to-model conversation and returns the complete transcript.
```

**Parameters:** `session_id`
**Variables Used:** `conversation, start_time, duration`
**Implementation:**
```python
@router.post('/v1/crosstalk/{session_id}/run')
async def run_crosstalk(session_id: str) -> CrosstalkRunResponse:
    """
    Execute a configured crosstalk session.

    Runs the model-to-model conversation and returns the complete transcript.
    """
    try:
        start_time = time.time()
        conversation = await crosstalk_orchestrator.execute_crosstalk(session_id)
        duration = time.time() - start_time
        return CrosstalkRunResponse(session_id=session_id, status='completed', conversation=conversation, duration_seconds=duration)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'Crosstalk execution failed: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `crosstalk_status`
**Logic & Purpose:**
```text
Get the status of a crosstalk session.
```

**Parameters:** `session_id`
**Variables Used:** `status`
**Implementation:**
```python
@router.get('/v1/crosstalk/{session_id}/status')
async def crosstalk_status(session_id: str) -> CrosstalkStatusResponse:
    """
    Get the status of a crosstalk session.
    """
    status = crosstalk_orchestrator.get_session_status(session_id)
    if 'error' in status:
        raise HTTPException(status_code=404, detail=status['error'])
    return CrosstalkStatusResponse(**status)
```

---

## Feature Function: `list_crosstalk_sessions`
**Logic & Purpose:**
```text
List all active crosstalk sessions.
```

**Parameters:** ``
**Variables Used:** `status, sessions`
**Implementation:**
```python
@router.get('/v1/crosstalk/list')
async def list_crosstalk_sessions() -> CrosstalkListResponse:
    """
    List all active crosstalk sessions.
    """
    sessions = []
    for session_id in crosstalk_orchestrator.active_sessions:
        status = crosstalk_orchestrator.get_session_status(session_id)
        sessions.append(status)
    return CrosstalkListResponse(sessions=sessions, total=len(sessions))
```

---

## Feature Function: `delete_crosstalk_session`
**Logic & Purpose:**
```text
Delete a completed or errored crosstalk session.
```

**Parameters:** `session_id`
**Variables Used:** `success`
**Implementation:**
```python
@router.delete('/v1/crosstalk/{session_id}/delete')
async def delete_crosstalk_session(session_id: str) -> CrosstalkDeleteResponse:
    """
    Delete a completed or errored crosstalk session.
    """
    success = crosstalk_orchestrator.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail='Session not found')
    return CrosstalkDeleteResponse(success=True, message='Session deleted successfully')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/users_rbac.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/users_rbac.py`

**Module Overview**: 
```text
User Management & RBAC API - Phase 4

Endpoints for user authentication, authorization, and API key management

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Header, fastapi.Depends, typing.Dict, typing.Any, typing.List, typing.Optional, datetime.datetime, json, src.core.logging.logger, src.services.user_management.user_service, src.services.user_management.UserRole, src.services.user_management.Permission, src.services.user_management.create_default_admin, src.services.user_management.ROLE_PERMISSIONS

## Feature Function: `get_current_user`
**Logic & Purpose:**
```text
Extract and validate user from Authorization header
```

**Parameters:** `authorization`
**Variables Used:** `token, user_id, api_key_info, user`
**Implementation:**
```python
async def get_current_user(authorization: Optional[str]=Header(None)) -> Dict[str, Any]:
    """Extract and validate user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing authorization header')
    if authorization.startswith('Bearer '):
        token = authorization[7:]
    else:
        token = authorization
    api_key_info = user_service.validate_api_key(token)
    if api_key_info:
        return {'user_id': api_key_info['user_id'], 'role': api_key_info['role'], 'permissions': api_key_info['permissions'], 'type': 'api_key'}
    user_id = user_service.validate_session(token)
    if user_id:
        user = user_service.get_user(user_id)
        if user:
            return {'user_id': user_id, 'role': user.role.value, 'permissions': user_service.get_user_permissions(user_id), 'type': 'session'}
    raise HTTPException(status_code=401, detail='Invalid or expired token')
```

---

## Feature Function: `check_permission`
**Logic & Purpose:**
```text
Check if user has required permission
```

**Parameters:** `user, permission`
**Implementation:**
```python
def check_permission(user: Dict[str, Any], permission: Permission):
    """Check if user has required permission"""
    if user['role'] == 'admin':
        return True
    return permission.value in user.get('permissions', [])
```

---

## Feature Function: `login`
**Logic & Purpose:**
```text
Login and get session token
```

**Parameters:** `credentials`
**Variables Used:** `user, token, username, password, user_id`
**Implementation:**
```python
@router.post('/api/auth/login')
async def login(credentials: Dict[str, Any]):
    """Login and get session token"""
    try:
        username = credentials.get('username')
        password = credentials.get('password')
        if not username or not password:
            raise HTTPException(status_code=400, detail='Missing credentials')
        user_id = user_service.authenticate(username, password)
        if not user_id:
            raise HTTPException(status_code=401, detail='Invalid credentials')
        token = user_service.create_session(user_id)
        if not token:
            raise HTTPException(status_code=500, detail='Failed to create session')
        user = user_service.get_user(user_id)
        return {'success': True, 'token': token, 'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role.value, 'permissions': user_service.get_user_permissions(user_id)}, 'expires_in_hours': 24}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Login failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `logout`
**Logic & Purpose:**
```text
Logout and invalidate session
```

**Parameters:** `user`
**Implementation:**
```python
@router.post('/api/auth/logout')
async def logout(user: Dict[str, Any]=Depends(get_current_user)):
    """Logout and invalidate session"""
    try:
        return {'success': True, 'message': 'Logged out'}
    except Exception as e:
        logger.error(f'Logout failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `verify_auth`
**Logic & Purpose:**
```text
Verify authentication and get current user info
```

**Parameters:** `user`
**Implementation:**
```python
@router.get('/api/auth/verify')
async def verify_auth(user: Dict[str, Any]=Depends(get_current_user)):
    """Verify authentication and get current user info"""
    return {'authenticated': True, 'user': {'id': user['user_id'], 'role': user['role'], 'permissions': user['permissions'], 'type': user['type']}}
```

---

## Feature Function: `create_user`
**Logic & Purpose:**
```text
Create a new user (requires admin or users:manage permission)
```

**Parameters:** `user_data, current_user`
**Variables Used:** `email, username, password, role_str, user_id, role`
**Implementation:**
```python
@router.post('/api/users')
async def create_user(user_data: Dict[str, Any], current_user: Dict[str, Any]=Depends(get_current_user)):
    """Create a new user (requires admin or users:manage permission)"""
    try:
        if not check_permission(current_user, Permission.USERS_MANAGE):
            raise HTTPException(status_code=403, detail='Permission denied')
        username = user_data.get('username')
        password = user_data.get('password')
        email = user_data.get('email', '')
        role_str = user_data.get('role', 'viewer')
        if not username or not password:
            raise HTTPException(status_code=400, detail='Username and password required')
        try:
            role = UserRole(role_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f'Invalid role: {role_str}')
        user_id = user_service.create_user(username, password, email, role)
        if not user_id:
            raise HTTPException(status_code=400, detail='Username already exists')
        return {'success': True, 'user_id': user_id, 'username': username, 'role': role.value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Create user failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `list_users`
**Logic & Purpose:**
```text
List all users (requires users:manage permission)
```

**Parameters:** `current_user`
**Variables Used:** `users`
**Implementation:**
```python
@router.get('/api/users')
async def list_users(current_user: Dict[str, Any]=Depends(get_current_user)):
    """List all users (requires users:manage permission)"""
    try:
        if not check_permission(current_user, Permission.USERS_MANAGE):
            raise HTTPException(status_code=403, detail='Permission denied')
        users = user_service.list_users()
        return {'users': [{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role.value, 'is_active': u.is_active, 'created_at': u.created_at, 'last_login': u.last_login} for u in users], 'count': len(users)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'List users failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `update_user_role`
**Logic & Purpose:**
```text
Update user role (requires users:manage permission)
```

**Parameters:** `user_id, role_data, current_user`
**Variables Used:** `success, role_str, role`
**Implementation:**
```python
@router.put('/api/users/{user_id}/role')
async def update_user_role(user_id: str, role_data: Dict[str, Any], current_user: Dict[str, Any]=Depends(get_current_user)):
    """Update user role (requires users:manage permission)"""
    try:
        if not check_permission(current_user, Permission.USERS_MANAGE):
            raise HTTPException(status_code=403, detail='Permission denied')
        role_str = role_data.get('role')
        if not role_str:
            raise HTTPException(status_code=400, detail='Role required')
        try:
            role = UserRole(role_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f'Invalid role: {role_str}')
        success = user_service.update_user_role(user_id, role)
        if not success:
            raise HTTPException(status_code=404, detail='User not found')
        return {'success': True, 'user_id': user_id, 'new_role': role.value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Update role failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `deactivate_user`
**Logic & Purpose:**
```text
Deactivate a user (requires users:manage permission)
```

**Parameters:** `user_id, current_user`
**Variables Used:** `success`
**Implementation:**
```python
@router.delete('/api/users/{user_id}')
async def deactivate_user(user_id: str, current_user: Dict[str, Any]=Depends(get_current_user)):
    """Deactivate a user (requires users:manage permission)"""
    try:
        if not check_permission(current_user, Permission.USERS_MANAGE):
            raise HTTPException(status_code=403, detail='Permission denied')
        success = user_service.deactivate_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail='User not found')
        return {'success': True, 'user_id': user_id, 'status': 'deactivated'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Deactivate user failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `create_api_key`
**Logic & Purpose:**
```text
Create a new API key
```

**Parameters:** `key_data, current_user`
**Variables Used:** `permissions, key, expires_days, target_user_id, name`
**Implementation:**
```python
@router.post('/api/api-keys')
async def create_api_key(key_data: Dict[str, Any], current_user: Dict[str, Any]=Depends(get_current_user)):
    """Create a new API key"""
    try:
        target_user_id = key_data.get('user_id', current_user['user_id'])
        if target_user_id != current_user['user_id']:
            if not check_permission(current_user, Permission.API_KEYS_MANAGE):
                raise HTTPException(status_code=403, detail='Cannot create keys for other users')
        name = key_data.get('name', 'Unnamed Key')
        permissions = key_data.get('permissions', [])
        expires_days = key_data.get('expires_days')
        key = user_service.create_api_key(user_id=target_user_id, name=name, permissions=permissions, expires_days=expires_days)
        if not key:
            raise HTTPException(status_code=400, detail='Failed to create API key')
        return {'success': True, 'key': key, 'message': "Store this key securely - it won't be shown again", 'permissions': permissions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Create API key failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `list_api_keys`
**Logic & Purpose:**
```text
List API keys (can view own, or all with permission)
```

**Parameters:** `user_id, current_user`
**Variables Used:** `keys, target_user_id`
**Implementation:**
```python
@router.get('/api/api-keys')
async def list_api_keys(user_id: Optional[str]=None, current_user: Dict[str, Any]=Depends(get_current_user)):
    """List API keys (can view own, or all with permission)"""
    try:
        target_user_id = user_id or current_user['user_id']
        if target_user_id != current_user['user_id']:
            if not check_permission(current_user, Permission.API_KEYS_MANAGE):
                raise HTTPException(status_code=403, detail="Cannot view other users' keys")
        keys = user_service.get_user_api_keys(target_user_id)
        return {'keys': [{'name': k.name, 'key_preview': f'{k.key[:8]}...', 'permissions': k.permissions, 'created_at': k.created_at, 'expires_at': k.expires_at, 'is_active': k.is_active, 'usage_count': k.usage_count} for k in keys], 'count': len(keys)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'List API keys failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `revoke_api_key`
**Logic & Purpose:**
```text
Revoke an API key
```

**Parameters:** `key, current_user`
**Variables Used:** `cursor, success, key_user_id, db_conn, conn, row`
**Implementation:**
```python
@router.delete('/api/api-keys/{key}')
async def revoke_api_key(key: str, current_user: Dict[str, Any]=Depends(get_current_user)):
    """Revoke an API key"""
    try:
        conn = user_service.db_path
        import sqlite3
        db_conn = sqlite3.connect(conn)
        cursor = db_conn.execute('SELECT user_id FROM api_keys WHERE key = ?', (key,))
        row = cursor.fetchone()
        db_conn.close()
        if not row:
            raise HTTPException(status_code=404, detail='API key not found')
        key_user_id = row[0]
        if key_user_id != current_user['user_id']:
            if not check_permission(current_user, Permission.API_KEYS_MANAGE):
                raise HTTPException(status_code=403, detail="Cannot revoke other users' keys")
        success = user_service.revoke_api_key(key)
        if not success:
            raise HTTPException(status_code=404, detail='API key not found')
        return {'success': True, 'key_preview': f'{key[:8]}...', 'status': 'revoked'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Revoke API key failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_permissions`
**Logic & Purpose:**
```text
Get all available permissions and user's current permissions
```

**Parameters:** `current_user`
**Variables Used:** `all_permissions, role_permissions`
**Implementation:**
```python
@router.get('/api/permissions')
async def get_permissions(current_user: Dict[str, Any]=Depends(get_current_user)):
    """Get all available permissions and user's current permissions"""
    all_permissions = [p.value for p in Permission]
    role_permissions = user_service.get_user_permissions(current_user['user_id'])
    return {'all_permissions': all_permissions, 'user_permissions': role_permissions, 'user_role': current_user['role']}
```

---

## Feature Function: `list_roles`
**Logic & Purpose:**
```text
List all available roles
```

**Parameters:** `current_user`
**Implementation:**
```python
@router.get('/api/roles')
async def list_roles(current_user: Dict[str, Any]=Depends(get_current_user)):
    """List all available roles"""
    return {'roles': [{'name': role.value, 'permissions': ROLE_PERMISSIONS[role]} for role in UserRole]}
```

---

## Feature Function: `verify_password`
**Logic & Purpose:**
```text
Verify current user's password
```

**Parameters:** `password_data, current_user`
**Variables Used:** `authenticated_user_id, user, is_valid, password`
**Implementation:**
```python
@router.post('/api/users/verify-password')
async def verify_password(password_data: Dict[str, Any], current_user: Dict[str, Any]=Depends(get_current_user)):
    """Verify current user's password"""
    try:
        password = password_data.get('password')
        if not password:
            raise HTTPException(status_code=400, detail='Password required')
        user = user_service.get_user(current_user['user_id'])
        if not user:
            raise HTTPException(status_code=404, detail='User not found')
        authenticated_user_id = user_service.authenticate(user.username, password)
        is_valid = authenticated_user_id == current_user['user_id']
        if not is_valid:
            raise HTTPException(status_code=401, detail='Invalid password')
        return {'valid': True, 'user_id': current_user['user_id']}
    except Exception as e:
        logger.error(f'Password verification failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `initialize_admin`
**Logic & Purpose:**
```text
Initialize default admin (run once on first setup)
```

**Parameters:** ``
**Implementation:**
```python
@router.get('/api/admin/initialize')
async def initialize_admin():
    """Initialize default admin (run once on first setup)"""
    try:
        create_default_admin()
        return {'success': True, 'message': 'Admin initialization attempted'}
    except Exception as e:
        logger.error(f'Admin init failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/predictive.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/predictive.py`

**Module Overview**: 
```text
Predictive Alerting API - Phase 4

Endpoints for AI-powered predictive analytics and anomaly detection

Author: AI Architect
Date: 2026-01-05
```

## Global Presets & Variables
- `router` = `APIRouter()`

## Dependencies & Imports
fastapi.APIRouter, fastapi.HTTPException, fastapi.Query, typing.Dict, typing.Any, typing.Optional, json, sqlite3, datetime.datetime, datetime.timedelta, src.core.logging.logger, src.services.predictive_alerting.predictive_alerting, src.services.predictive_alerting.anomaly_detector, src.services.predictive_alerting.PredictionAPI, src.services.usage.usage_tracker.usage_tracker

## Feature Function: `get_forecast`
**Logic & Purpose:**
```text
Get predictive forecast for usage metrics
```

**Parameters:** `days`
**Variables Used:** `result`
**Implementation:**
```python
@router.get('/api/predictive/forecast')
async def get_forecast(days: int=Query(7, ge=1, le=30, description='Number of days to forecast')):
    """Get predictive forecast for usage metrics"""
    try:
        result = await PredictionAPI.get_predictions(days)
        return result
    except Exception as e:
        logger.error(f'Forecast endpoint failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_smart_thresholds`
**Logic & Purpose:**
```text
Get intelligent thresholds based on historical analysis
```

**Parameters:** `metric`
**Variables Used:** `result`
**Implementation:**
```python
@router.get('/api/predictive/thresholds')
async def get_smart_thresholds(metric: str=Query(..., description='Metric: tokens, cost, requests, latency')):
    """Get intelligent thresholds based on historical analysis"""
    try:
        result = await PredictionAPI.get_smart_thresholds(metric)
        return result
    except Exception as e:
        logger.error(f'Thresholds endpoint failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_patterns`
**Logic & Purpose:**
```text
Get seasonal and usage patterns
```

**Parameters:** ``
**Variables Used:** `result`
**Implementation:**
```python
@router.get('/api/predictive/patterns')
async def get_patterns():
    """Get seasonal and usage patterns"""
    try:
        result = await PredictionAPI.get_patterns()
        return result
    except Exception as e:
        logger.error(f'Patterns endpoint failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `detect_anomaly`
**Logic & Purpose:**
```text
Detect if current request is anomalous
```

**Parameters:** `request_data`
**Variables Used:** `result`
**Implementation:**
```python
@router.post('/api/predictive/detect-anomaly')
async def detect_anomaly(request_data: Dict[str, Any]):
    """Detect if current request is anomalous"""
    try:
        result = await PredictionAPI.detect_current_anomaly(request_data)
        return result
    except Exception as e:
        logger.error(f'Anomaly detection failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `analyze_cost_prediction`
**Logic & Purpose:**
```text
Analyze potential cost before making request
```

**Parameters:** `request_config, model, provider`
**Variables Used:** `output_tokens, input_tokens, daily_total, forecast, estimated_cost, projected_total, response, thresholds, model`
**Implementation:**
```python
@router.post('/api/predictive/analyze-cost')
async def analyze_cost_prediction(request_config: Dict[str, Any], model: Optional[str]=None, provider: Optional[str]=None):
    """Analyze potential cost before making request"""
    try:
        forecast = predictive_alerting.predict_metrics(1)
        input_tokens = request_config.get('input_tokens', 0)
        output_tokens = request_config.get('output_tokens', 0)
        if not model:
            model = request_config.get('model', 'unknown')
        estimated_cost = (input_tokens + output_tokens) * 3e-05
        thresholds = predictive_alerting.get_smart_thresholds('cost')
        daily_total = sum((p.predicted_value for p in forecast.predictions if p.metric == 'cost'))
        projected_total = daily_total + estimated_cost
        response = {'estimated_cost': round(estimated_cost, 6), 'daily_projected_total': round(projected_total, 6), 'within_budget': projected_total < thresholds.get('warning', float('inf')), 'thresholds': thresholds, 'recommendation': ''}
        if projected_total > thresholds.get('critical', 0):
            response['recommendation'] = 'CRITICAL: Request would exceed budget threshold. Consider using a smaller model.'
            response['severity'] = 'critical'
        elif projected_total > thresholds.get('warning', 0):
            response['recommendation'] = 'WARNING: Request would exceed warning threshold. Proceed with caution.'
            response['severity'] = 'warning'
        else:
            response['recommendation'] = 'OK: Cost projection within normal range.'
            response['severity'] = 'low'
        return response
    except Exception as e:
        logger.error(f'Cost analysis failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_trend_analysis`
**Logic & Purpose:**
```text
Get detailed trend analysis
```

**Parameters:** `days`
**Variables Used:** `data, trend, growth_rate, trends, confidence, history`
**Implementation:**
```python
@router.get('/api/predictive/trend-analysis')
async def get_trend_analysis(days: int=Query(7, ge=1, le=90)):
    """Get detailed trend analysis"""
    try:
        history = predictive_alerting.get_historical_data(days=days)
        if not history:
            return {'error': 'Insufficient data'}
        trends = {}
        for metric in ['tokens', 'cost', 'requests']:
            if metric in history and len(history[metric]) >= 2:
                data = history[metric]
                trend = predictive_alerting.calculate_trend(data)
                if len(data) >= 2:
                    growth_rate = (data[-1] - data[0]) / data[0] * 100 if data[0] > 0 else 0
                else:
                    growth_rate = 0
                confidence = min(0.95, len(data) / 30)
                trends[metric] = {'trend': trend, 'growth_rate': round(growth_rate, 2), 'confidence': round(confidence, 2), 'recent_values': data[-7:] if len(data) >= 7 else data}
        return {'analysis_period_days': days, 'trends': trends, 'summary': f'Analyzed {days} days of data'}
    except Exception as e:
        logger.error(f'Trend analysis failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `create_smart_alert`
**Logic & Purpose:**
```text
Create an alert with AI-suggested thresholds
```

**Parameters:** `alert_config`
**Variables Used:** `threshold_value, metric, response, thresholds, operator, warning`
**Implementation:**
```python
@router.post('/api/predictive/smart-alert')
async def create_smart_alert(alert_config: Dict[str, Any]):
    """Create an alert with AI-suggested thresholds"""
    try:
        metric = alert_config.get('metric', 'cost')
        operator = alert_config.get('operator', '>')
        thresholds = predictive_alerting.get_smart_thresholds(metric)
        threshold_value = alert_config.get('threshold')
        if threshold_value is None:
            threshold_value = thresholds.get('warning', 0)
        if threshold_value > thresholds.get('critical', 0) * 1.5:
            warning = 'Threshold is significantly higher than historical 90th percentile'
        elif threshold_value < thresholds.get('critical', 0) * 0.5:
            warning = 'Threshold may trigger too frequently'
        else:
            warning = None
        response = {'alert_config': {'metric': metric, 'operator': operator, 'threshold': threshold_value, 'time_window': alert_config.get('time_window', '5m')}, 'smart_thresholds': thresholds, 'validation': {'is_recommended': warning is None, 'warning': warning, 'source': '30-day historical analysis'}, 'predicted_alerts': []}
        return response
    except Exception as e:
        logger.error(f'Smart alert creation failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `predictive_health`
**Logic & Purpose:**
```text
Health check for predictive services
```

**Parameters:** ``
**Variables Used:** `has_data, history`
**Implementation:**
```python
@router.get('/api/predictive/health')
async def predictive_health():
    """Health check for predictive services"""
    try:
        history = predictive_alerting.get_historical_data(days=3)
        has_data = bool(history and len(history.get('tokens', [])) > 0)
        return {'status': 'healthy' if has_data else 'degraded', 'data_available': has_data, 'services': {'forecasting': has_data, 'anomaly_detection': True, 'pattern_analysis': has_data}, 'recommendation': 'Run some requests to generate training data' if not has_data else 'Ready'}
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return {'status': 'error', 'error': str(e)}
```

---

## Feature Function: `get_recommendations`
**Logic & Purpose:**
```text
Get actionable recommendations based on AI analysis
```

**Parameters:** `days`
**Variables Used:** `forecast, recommendations, peak, patterns`
**Implementation:**
```python
@router.get('/api/predictive/recommendations')
async def get_recommendations(days: int=Query(7, ge=1, le=90)):
    """Get actionable recommendations based on AI analysis"""
    try:
        forecast = predictive_alerting.predict_metrics(days)
        patterns = predictive_alerting.detect_seasonal_patterns()
        recommendations = []
        if forecast.risk_level == 'high':
            recommendations.append({'priority': 'high', 'category': 'budget_protection', 'message': forecast.recommended_action, 'action': 'Consider setting up strict rate limits or model restrictions'})
        elif forecast.risk_level == 'medium':
            recommendations.append({'priority': 'medium', 'category': 'monitoring', 'message': forecast.recommended_action, 'action': 'Enable detailed logging and set up alerts'})
        if forecast.cost_prediction > 100:
            recommendations.append({'priority': 'medium', 'category': 'optimization', 'message': f'Projected cost: ${forecast.cost_prediction:.2f} for next {days} days', 'action': 'Review model selection for cost optimization'})
        if patterns.get('peak_hour') is not None:
            peak = patterns['peak_hour']
            if peak >= 9 and peak <= 17:
                recommendations.append({'priority': 'low', 'category': 'scheduling', 'message': f'Peak usage during business hours ({peak}:00)', 'action': 'Consider batch processing during off-peak hours'})
        if not recommendations:
            recommendations.append({'priority': 'low', 'category': 'general', 'message': 'No critical issues detected. System operating normally.', 'action': 'Continue monitoring'})
        return {'risk_level': forecast.risk_level, 'forecast_summary': {'tokens': round(forecast.total_tokens_predicted, 0), 'cost': round(forecast.cost_prediction, 4), 'days_ahead': days}, 'recommendations': recommendations, 'generated_at': datetime.now().isoformat()}
    except Exception as e:
        logger.error(f'Recommendations failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Feature Function: `get_anomaly_history`
**Logic & Purpose:**
```text
Get history of detected anomalies
```

**Parameters:** `limit`
**Variables Used:** `cursor, cutoff, anomalies, rows, query, conn`
**Implementation:**
```python
@router.get('/api/predictive/anomaly-history')
async def get_anomaly_history(limit: int=Query(50, ge=1, le=500)):
    """Get history of detected anomalies"""
    try:
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        query = "\n            SELECT\n                timestamp,\n                estimated_cost,\n                total_tokens,\n                duration_ms,\n                provider,\n                routed_model,\n                CASE\n                    WHEN estimated_cost > (SELECT AVG(estimated_cost) * 3 FROM api_requests) THEN 'cost'\n                    WHEN total_tokens > (SELECT AVG(total_tokens) * 3 FROM api_requests) THEN 'tokens'\n                    WHEN duration_ms > (SELECT AVG(duration_ms) * 3 FROM api_requests) THEN 'latency'\n                END as anomaly_type\n            FROM api_requests\n            WHERE timestamp >= ?\n            HAVING anomaly_type IS NOT NULL\n            ORDER BY timestamp DESC\n            LIMIT ?\n        "
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        cursor = conn.execute(query, [cutoff, limit])
        rows = cursor.fetchall()
        conn.close()
        anomalies = []
        for row in rows:
            anomalies.append({'timestamp': row['timestamp'], 'type': row['anomaly_type'], 'value': row.get(row['anomaly_type'], 0), 'provider': row['provider'], 'model': row['routed_model']})
        return {'count': len(anomalies), 'anomalies': anomalies, 'period': 'last 7 days'}
    except Exception as e:
        logger.error(f'Anomaly history failed: {e}')
        raise HTTPException(status_code=500, detail=str(e))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/api/websocket_live.py
**Path**: `/home/cheta/code/claude-code-proxy/src/api/websocket_live.py`

**Module Overview**: 
```text
WebSocket Live Metrics & Real-time Monitoring

Provides real-time updates for:
- Live metrics (requests/second, cost, tokens)
- Request feed (streaming requests)
- Alert notifications
- Crosstalk session progress

Author: AI Architect
Date: 2026-01-04
```

## Global Presets & Variables
- `router` = `APIRouter()`
- `metrics_cache` = `{'requests_per_second': 0, 'tokens_per_second': 0, 'cost_per_second': 0.0, 'active_requests': 0, 'error_rate': 0.0, 'model_distribution': {}, 'timestamp': datetime.utcnow().isoformat()}`
- `metrics_manager` = `LiveMetricsManager()`
- `__all__` = `['router', 'metrics_manager', 'start_live_metrics', 'stop_live_metrics', 'broadcast_request_event', 'update_crosstalk_session']`

## Dependencies & Imports
asyncio, json, sqlite3, datetime.datetime, typing.Dict, typing.List, typing.Set, fastapi.WebSocket, fastapi.WebSocketDisconnect, fastapi.APIRouter, pathlib.Path, src.core.logging.logger, src.services.usage.usage_tracker.usage_tracker

## Feature Class: `LiveMetricsManager`
**Description:**
```text
Manages real-time metrics calculation and broadcasting
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self._running = False
    self._task = None
```

### Method: `start`
**Logic & Purpose:**
```text
Start the metrics calculation loop
```

**Parameters:** `self`
**Implementation:**
```python
async def start(self):
    """Start the metrics calculation loop"""
    if self._running:
        return
    self._running = True
    self._task = asyncio.create_task(self._metrics_loop())
    logger.info('Live metrics manager started')
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop the metrics calculation loop
```

**Parameters:** `self`
**Implementation:**
```python
async def stop(self):
    """Stop the metrics calculation loop"""
    self._running = False
    if self._task:
        await self._task
    logger.info('Live metrics manager stopped')
```

### Method: `_metrics_loop`
**Logic & Purpose:**
```text
Calculate and update live metrics every second
```

**Parameters:** `self`
**Variables Used:** `metrics`
**Implementation:**
```python
async def _metrics_loop(self):
    """Calculate and update live metrics every second"""
    while self._running:
        try:
            if usage_tracker.enabled:
                metrics = await self._calculate_metrics()
                metrics_cache.update(metrics)
                await self._broadcast_metrics()
                await self._check_alerts()
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f'Metrics loop error: {e}')
            await asyncio.sleep(5)
```

### Method: `_calculate_metrics`
**Logic & Purpose:**
```text
Calculate real-time metrics from database
```

**Parameters:** `self`
**Variables Used:** `tps, cursor, result, requests_60s, rps, model_dist, error_rate, errors, active, since, total, cost_60s, cps, tokens_60s, conn`
**Implementation:**
```python
async def _calculate_metrics(self) -> Dict:
    """Calculate real-time metrics from database"""
    try:
        import sqlite3
        import time
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()
        since = datetime.utcnow().timestamp() - 60
        cursor.execute("\n                SELECT COUNT(*) FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n            ", (since,))
        requests_60s = cursor.fetchone()[0]
        rps = requests_60s / 60.0
        cursor.execute("\n                SELECT SUM(total_tokens) FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n            ", (since,))
        tokens_60s = cursor.fetchone()[0] or 0
        tps = tokens_60s / 60.0
        cursor.execute("\n                SELECT SUM(estimated_cost) FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n            ", (since,))
        cost_60s = cursor.fetchone()[0] or 0
        cps = cost_60s / 60.0
        cursor.execute("\n                SELECT COUNT(*) FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n                AND status = 'active'\n            ", (time.time() - 5,))
        active = cursor.fetchone()[0]
        cursor.execute("\n                SELECT\n                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,\n                    COUNT(*) as total\n                FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n            ", (since,))
        result = cursor.fetchone()
        errors = result[0] or 0
        total = result[1] or 1
        error_rate = errors / total * 100
        cursor.execute("\n                SELECT routed_model, COUNT(*) as count\n                FROM api_requests\n                WHERE timestamp >= datetime(?, 'unixepoch')\n                GROUP BY routed_model\n                ORDER BY count DESC\n                LIMIT 10\n            ", (since,))
        model_dist = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return {'requests_per_second': round(rps, 2), 'tokens_per_second': round(tps, 2), 'cost_per_second': round(cps, 4), 'active_requests': active, 'error_rate': round(error_rate, 2), 'model_distribution': model_dist, 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f'Error calculating metrics: {e}')
        return metrics_cache
```

### Method: `_broadcast_metrics`
**Logic & Purpose:**
```text
Broadcast metrics to all connected clients
```

**Parameters:** `self`
**Variables Used:** `message, disconnected`
**Implementation:**
```python
async def _broadcast_metrics(self):
    """Broadcast metrics to all connected clients"""
    if not active_connections:
        return
    message = {'type': 'metrics', 'data': metrics_cache, 'timestamp': datetime.utcnow().isoformat()}
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as _e:
            disconnected.add(connection)
    for conn in disconnected:
        active_connections.discard(conn)
```

### Method: `_check_alerts`
**Logic & Purpose:**
```text
Check alert rules and trigger notifications
```

**Parameters:** `self`
**Variables Used:** `condition, cursor, current_value, metric, window, conn, operator, threshold`
**Implementation:**
```python
async def _check_alerts(self):
    """Check alert rules and trigger notifications"""
    if not usage_tracker.enabled:
        return
    try:
        import sqlite3
        conn = sqlite3.connect(usage_tracker.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("\n                SELECT * FROM alert_rules\n                WHERE is_active = 1\n                AND (muted_until IS NULL OR muted_until < datetime('now'))\n            ")
        for rule in cursor.fetchall():
            condition = json.loads(rule['condition_json'])
            metric = condition['metric']
            operator = condition['operator']
            threshold = condition['threshold']
            window = condition.get('window_minutes', 5)
            current_value = self._get_metric_value(metric, window)
            if self._evaluate_condition(current_value, operator, threshold):
                if self._in_cooldown(rule, cursor):
                    continue
                await self._trigger_alert(rule, current_value, cursor)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f'Alert check error: {e}')
```

### Method: `_get_metric_value`
**Logic & Purpose:**
```text
Get current value for a metric
```

**Parameters:** `self, metric, window_minutes`
**Variables Used:** `conn, cursor, since`
**Implementation:**
```python
def _get_metric_value(self, metric: str, window_minutes: int) -> float:
    """Get current value for a metric"""
    since = datetime.utcnow().timestamp() - window_minutes * 60
    try:
        import sqlite3
        conn = sqlite3.connect(usage_tracker.db_path)
        cursor = conn.cursor()
        if metric == 'cost':
            cursor.execute("\n                    SELECT SUM(estimated_cost) FROM api_requests\n                    WHERE timestamp >= datetime(?, 'unixepoch')\n                ", (since,))
            return (cursor.fetchone()[0] or 0) * (1440 / window_minutes)
        elif metric == 'latency':
            cursor.execute("\n                    SELECT AVG(duration_ms) FROM api_requests\n                    WHERE timestamp >= datetime(?, 'unixepoch')\n                ", (since,))
            return cursor.fetchone()[0] or 0
        elif metric == 'error_rate':
            cursor.execute("\n                    SELECT\n                        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)\n                    FROM api_requests\n                    WHERE timestamp >= datetime(?, 'unixepoch')\n                ", (since,))
            return cursor.fetchone()[0] or 0
        elif metric == 'token_count':
            cursor.execute("\n                    SELECT SUM(total_tokens) FROM api_requests\n                    WHERE timestamp >= datetime(?, 'unixepoch')\n                ", (since,))
            return cursor.fetchone()[0] or 0
        elif metric == 'request_count':
            cursor.execute("\n                    SELECT COUNT(*) FROM api_requests\n                    WHERE timestamp >= datetime(?, 'unixepoch')\n                ", (since,))
            return cursor.fetchone()[0] or 0
        conn.close()
    except Exception as _e:
        pass
    return 0
```

### Method: `_evaluate_condition`
**Logic & Purpose:**
```text
Evaluate alert condition
```

**Parameters:** `self, value, operator, threshold`
**Implementation:**
```python
def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
    """Evaluate alert condition"""
    if operator == '>':
        return value > threshold
    elif operator == '<':
        return value < threshold
    elif operator == '>=':
        return value >= threshold
    elif operator == '<=':
        return value <= threshold
    elif operator == '=':
        return abs(value - threshold) < 0.01
    return False
```

### Method: `_in_cooldown`
**Logic & Purpose:**
```text
Check if rule is in cooldown period
```

**Parameters:** `self, rule, cursor`
**Variables Used:** `cooldown_until, last_trigger, cooldown_minutes`
**Implementation:**
```python
def _in_cooldown(self, rule: sqlite3.Row, cursor) -> bool:
    """Check if rule is in cooldown period"""
    if not rule['last_triggered']:
        return False
    cooldown_minutes = rule['cooldown_minutes'] or 5
    last_trigger = datetime.fromisoformat(rule['last_triggered'])
    cooldown_until = last_trigger.timestamp() + cooldown_minutes * 60
    return datetime.utcnow().timestamp() < cooldown_until
```

### Method: `_trigger_alert`
**Logic & Purpose:**
```text
Trigger alert and send notifications
```

**Parameters:** `self, rule, value, cursor`
**Variables Used:** `alert_id, actions, alert_data`
**Implementation:**
```python
async def _trigger_alert(self, rule: sqlite3.Row, value: float, cursor):
    """Trigger alert and send notifications"""
    alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{rule['id']}"
    cursor.execute('\n            UPDATE alert_rules\n            SET last_triggered = ?, trigger_count = trigger_count + 1\n            WHERE id = ?\n        ', (datetime.utcnow().isoformat(), rule['id']))
    alert_data = {'metric_value': value, 'threshold': json.loads(rule['condition_json'])['threshold'], 'window_minutes': json.loads(rule['condition_json']).get('window_minutes', 5)}
    cursor.execute('\n            INSERT INTO alert_history\n            (id, rule_id, rule_name, triggered_at, alert_data_json, severity)\n            VALUES (?, ?, ?, ?, ?, ?)\n        ', (alert_id, rule['id'], rule['name'], datetime.utcnow().isoformat(), json.dumps(alert_data), rule['priority']))
    actions = json.loads(rule['actions_json'])
    if actions.get('in_app'):
        await self._broadcast_alert({'type': 'alert', 'alert_id': alert_id, 'rule_name': rule['name'], 'severity': rule['priority'], 'message': f"{rule['name']}: {value} (threshold: {alert_data['threshold']})", 'timestamp': datetime.utcnow().isoformat()})
    if actions.get('webhook'):
        asyncio.create_task(self._send_webhook(actions['webhook'], {'alert_id': alert_id, 'rule': rule['name'], 'value': value, 'timestamp': datetime.utcnow().isoformat()}))
    logger.info(f"Alert triggered: {rule['name']} - {value}")
```

### Method: `_broadcast_alert`
**Logic & Purpose:**
```text
Broadcast alert to all connected clients
```

**Parameters:** `self, alert`
**Variables Used:** `disconnected`
**Implementation:**
```python
async def _broadcast_alert(self, alert: Dict):
    """Broadcast alert to all connected clients"""
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(alert)
        except Exception as _e:
            disconnected.add(connection)
    for conn in disconnected:
        active_connections.discard(conn)
```

### Method: `_send_webhook`
**Logic & Purpose:**
```text
Send webhook notification
```

**Parameters:** `self, url, payload`
**Implementation:**
```python
async def _send_webhook(self, url: str, payload: Dict):
    """Send webhook notification"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f'Webhook failed: {response.status}')
    except Exception as e:
        logger.error(f'Webhook error: {e}')
```

---

## Feature Function: `websocket_live_metrics`
**Logic & Purpose:**
```text
WebSocket endpoint for live metrics

Client receives:
- metrics: Real-time system metrics (1Hz)
- alerts: Alert notifications when triggered
- request_feed: Streaming request events

Client can send:
- subscribe: Subscribe to specific feeds
- ping: Connection health check
```

**Parameters:** `websocket`
**Variables Used:** `feeds, data`
**Implementation:**
```python
@router.websocket('/ws/live')
async def websocket_live_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for live metrics

    Client receives:
    - metrics: Real-time system metrics (1Hz)
    - alerts: Alert notifications when triggered
    - request_feed: Streaming request events

    Client can send:
    - subscribe: Subscribe to specific feeds
    - ping: Connection health check
    """
    await websocket.accept()
    active_connections.add(websocket)
    try:
        await websocket.send_json({'type': 'metrics', 'data': metrics_cache, 'timestamp': datetime.utcnow().isoformat()})
        if request_feed_buffer:
            await websocket.send_json({'type': 'request_feed', 'data': request_feed_buffer[-10:], 'timestamp': datetime.utcnow().isoformat()})
        while True:
            try:
                data = await websocket.receive_json()
                if data.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong', 'timestamp': datetime.utcnow().isoformat()})
                elif data.get('type') == 'subscribe':
                    feeds = data.get('feeds', ['metrics'])
                    await websocket.send_json({'type': 'subscribed', 'feeds': feeds, 'timestamp': datetime.utcnow().isoformat()})
            except TimeoutError:
                continue
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info('WebSocket client disconnected')
    except Exception as e:
        active_connections.discard(websocket)
        logger.error(f'WebSocket error: {e}')
        try:
            await websocket.close()
        except Exception as _e:
            pass
```

---

## Feature Function: `websocket_crosstalk_session`
**Logic & Purpose:**
```text
WebSocket endpoint for real-time Crosstalk session monitoring

Client receives:
- session_status: Current session state
- round_update: Progress on each round
- cost_update: Running cost totals

Path params:
    session_id: Crosstalk session ID
```

**Parameters:** `websocket, session_id`
**Variables Used:** `session_data, data`
**Implementation:**
```python
@router.websocket('/ws/crosstalk/{session_id}')
async def websocket_crosstalk_session(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time Crosstalk session monitoring

    Client receives:
    - session_status: Current session state
    - round_update: Progress on each round
    - cost_update: Running cost totals

    Path params:
        session_id: Crosstalk session ID
    """
    await websocket.accept()
    if session_id not in crosstalk_sessions:
        crosstalk_sessions[session_id] = {'connections': set(), 'last_update': None, 'cost': 0, 'tokens': 0, 'round': 0}
    crosstalk_sessions[session_id]['connections'].add(websocket)
    try:
        session_data = crosstalk_sessions.get(session_id)
        if session_data:
            await websocket.send_json({'type': 'session_status', 'data': session_data, 'timestamp': datetime.utcnow().isoformat()})
        while True:
            data = await websocket.receive_json()
            if data.get('type') == 'ping':
                await websocket.send_json({'type': 'pong'})
    except WebSocketDisconnect:
        if session_id in crosstalk_sessions:
            crosstalk_sessions[session_id]['connections'].discard(websocket)
    except Exception as e:
        logger.error(f'Crosstalk WebSocket error: {e}')
        try:
            await websocket.close()
        except Exception as _e:
            pass
```

---

## Feature Function: `broadcast_request_event`
**Logic & Purpose:**
```text
Broadcast new request event to all live feed subscribers
```

**Parameters:** `request_data`
**Variables Used:** `message, disconnected`
**Implementation:**
```python
async def broadcast_request_event(request_data: Dict):
    """Broadcast new request event to all live feed subscribers"""
    request_feed_buffer.append({**request_data, 'timestamp': datetime.utcnow().isoformat()})
    if len(request_feed_buffer) > 100:
        request_feed_buffer.pop(0)
    message = {'type': 'request_event', 'data': request_data, 'timestamp': datetime.utcnow().isoformat()}
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as _e:
            disconnected.add(connection)
    for conn in disconnected:
        active_connections.discard(conn)
```

---

## Feature Function: `update_crosstalk_session`
**Logic & Purpose:**
```text
Update crosstalk session with new round data
```

**Parameters:** `session_id, round_data`
**Variables Used:** `message, session, disconnected`
**Implementation:**
```python
async def update_crosstalk_session(session_id: str, round_data: Dict):
    """Update crosstalk session with new round data"""
    if session_id not in crosstalk_sessions:
        crosstalk_sessions[session_id] = {'connections': set(), 'last_update': None, 'cost': 0, 'tokens': 0, 'round': 0}
    session = crosstalk_sessions[session_id]
    session['last_update'] = datetime.utcnow().isoformat()
    session['round'] = round_data.get('round', session['round'] + 1)
    session['cost'] += round_data.get('cost', 0)
    session['tokens'] += round_data.get('tokens', 0)
    message = {'type': 'round_update', 'data': round_data, 'session_summary': {'round': session['round'], 'total_cost': session['cost'], 'total_tokens': session['tokens']}, 'timestamp': datetime.utcnow().isoformat()}
    disconnected = set()
    for connection in session['connections']:
        try:
            await connection.send_json(message)
        except Exception as _e:
            disconnected.add(connection)
    for conn in disconnected:
        session['connections'].discard(conn)
```

---

## Feature Function: `start_live_metrics`
**Logic & Purpose:**
```text
Initialize live metrics system
```

**Parameters:** ``
**Implementation:**
```python
async def start_live_metrics():
    """Initialize live metrics system"""
    await metrics_manager.start()
```

---

## Feature Function: `stop_live_metrics`
**Logic & Purpose:**
```text
Stop live metrics system
```

**Parameters:** ``
**Implementation:**
```python
async def stop_live_metrics():
    """Stop live metrics system"""
    await metrics_manager.stop()
```

---


