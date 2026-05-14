# File Audit: /home/cheta/code/claude-code-proxy/src/core/json_detector.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/json_detector.py`

**Module Overview**: 
```text
JSON detection utility for TOON conversion analysis.

Detects JSON in request/response content to analyze if TOON format
would provide token savings.
```

## Global Presets & Variables
- `json_detector` = `JSONDetector()`

## Dependencies & Imports
json, re, typing.Tuple, typing.List, typing.Dict, typing.Any

## Feature Class: `JSONDetector`
**Description:**
```text
Detect and analyze JSON content in requests/responses.

Used for session-level TOON conversion analysis, not per-request.
```

### Method: `detect_json_in_text`
**Logic & Purpose:**
```text
Detect JSON structures in text content.

Args:
    text: Text to analyze

Returns:
    (has_json, total_bytes, json_objects)
```

**Parameters:** `text`
**Variables Used:** `json_str, has_json, json_objects, total_bytes, size, obj, matches`
**Implementation:**
```python
@staticmethod
def detect_json_in_text(text: str) -> Tuple[bool, int, List[Dict[str, Any]]]:
    """
        Detect JSON structures in text content.

        Args:
            text: Text to analyze

        Returns:
            (has_json, total_bytes, json_objects)
        """
    if not text or len(text) < JSONDetector.MIN_JSON_SIZE:
        return (False, 0, [])
    json_objects = []
    total_bytes = 0
    matches = JSONDetector.JSON_PATTERN.finditer(text)
    for match in matches:
        json_str = match.group(0)
        try:
            obj = json.loads(json_str)
            size = len(json_str)
            if size >= JSONDetector.MIN_JSON_SIZE:
                json_objects.append({'size': size, 'type': 'object' if isinstance(obj, dict) else 'array', 'depth': JSONDetector._get_depth(obj)})
                total_bytes += size
        except (json.JSONDecodeError, ValueError):
            continue
    has_json = len(json_objects) > 0
    return (has_json, total_bytes, json_objects)
```

### Method: `_get_depth`
**Logic & Purpose:**
```text
Calculate nesting depth of JSON object.
```

**Parameters:** `obj, current_depth`
**Implementation:**
```python
@staticmethod
def _get_depth(obj: Any, current_depth: int=0) -> int:
    """Calculate nesting depth of JSON object."""
    if not isinstance(obj, (dict, list)):
        return current_depth
    if not obj:
        return current_depth
    if isinstance(obj, dict):
        return max((JSONDetector._get_depth(v, current_depth + 1) for v in obj.values()), default=current_depth)
    else:
        return max((JSONDetector._get_depth(item, current_depth + 1) for item in obj), default=current_depth)
```

### Method: `analyze_tool_calls`
**Logic & Purpose:**
```text
Analyze tool calls for JSON content.

Args:
    tool_calls: List of tool call dicts

Returns:
    (has_json, total_bytes)
```

**Parameters:** `tool_calls`
**Variables Used:** `args, total_bytes, has_json`
**Implementation:**
```python
@staticmethod
def analyze_tool_calls(tool_calls: List[Dict[str, Any]]) -> Tuple[bool, int]:
    """
        Analyze tool calls for JSON content.

        Args:
            tool_calls: List of tool call dicts

        Returns:
            (has_json, total_bytes)
        """
    if not tool_calls:
        return (False, 0)
    total_bytes = 0
    for tool_call in tool_calls:
        if 'function' in tool_call:
            args = tool_call['function'].get('arguments', '')
            if args:
                try:
                    json.loads(args)
                    total_bytes += len(args)
                except (json.JSONDecodeError, ValueError):
                    pass
    has_json = total_bytes > 0
    return (has_json, total_bytes)
```

### Method: `estimate_toon_savings`
**Logic & Purpose:**
```text
Estimate token savings with TOON format.

TOON typically saves 20-40% for structured JSON.

Args:
    json_bytes: Total JSON bytes

Returns:
    Estimated bytes saved
```

**Parameters:** `json_bytes`
**Implementation:**
```python
@staticmethod
def estimate_toon_savings(json_bytes: int) -> int:
    """
        Estimate token savings with TOON format.

        TOON typically saves 20-40% for structured JSON.

        Args:
            json_bytes: Total JSON bytes

        Returns:
            Estimated bytes saved
        """
    return int(json_bytes * 0.25)
```

### Method: `should_recommend_toon`
**Logic & Purpose:**
```text
Determine if TOON conversion is recommended.

Args:
    total_requests: Total API requests in session
    json_requests: Requests with JSON content
    total_json_bytes: Total JSON bytes

Returns:
    True if TOON recommended
```

**Parameters:** `total_requests, json_requests, total_json_bytes`
**Variables Used:** `avg_json_size, json_percentage`
**Implementation:**
```python
@staticmethod
def should_recommend_toon(total_requests: int, json_requests: int, total_json_bytes: int) -> bool:
    """
        Determine if TOON conversion is recommended.

        Args:
            total_requests: Total API requests in session
            json_requests: Requests with JSON content
            total_json_bytes: Total JSON bytes

        Returns:
            True if TOON recommended
        """
    if total_requests < 10:
        return False
    json_percentage = json_requests / total_requests * 100
    avg_json_size = total_json_bytes / json_requests if json_requests > 0 else 0
    return json_percentage > 30 and avg_json_size > 500 and (total_json_bytes > 10000)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/circuit_breaker.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/circuit_breaker.py`

**Module Overview**: 
```text
Circuit Breaker Pattern for Provider Resilience

Inspired by Lynkr's implementation, this module provides:
- Per-provider circuit breakers to prevent cascading failures
- Automatic recovery after timeout period
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `_CB_STATE_FILE` = `Path(os.environ.get('CB_STATE_FILE', 'data/circuit_breaker_state.json'))`

## Dependencies & Imports
asyncio, json, os, time, logging, enum.Enum, pathlib.Path, typing.Dict, typing.Optional, typing.Callable, typing.Any, dataclasses.dataclass, dataclasses.field

## Feature Function: `_load_persisted_state`
**Logic & Purpose:**
```text
Load previously saved circuit breaker states from disk.
```

**Parameters:** ``
**Implementation:**
```python
def _load_persisted_state() -> Dict[str, dict]:
    """Load previously saved circuit breaker states from disk."""
    try:
        if _CB_STATE_FILE.exists():
            return json.loads(_CB_STATE_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning(f'[CB] Could not load persisted state: {e}')
    return {}
```

---

## Feature Function: `_save_persisted_state`
**Logic & Purpose:**
```text
Persist current circuit breaker states to disk.
```

**Parameters:** `states`
**Implementation:**
```python
def _save_persisted_state(states: Dict[str, dict]) -> None:
    """Persist current circuit breaker states to disk."""
    try:
        _CB_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CB_STATE_FILE.write_text(json.dumps(states, indent=2), encoding='utf-8')
    except Exception as e:
        logger.warning(f'[CB] Could not save state: {e}')
```

---

## Feature Class: `CircuitState`
**Description:**
```text
Circuit breaker states.
```

---

## Feature Class: `CircuitBreakerConfig`
**Description:**
```text
Configuration for a circuit breaker.
```

---

## Feature Class: `CircuitBreakerStats`
**Description:**
```text
Runtime statistics for a circuit breaker.
```

---

## Feature Class: `CircuitBreaker`
**Description:**
```text
Circuit breaker implementation for a single provider.

Usage:
    breaker = CircuitBreaker("openrouter")
    try:
        result = await breaker.execute(async_fn, arg1, arg2)
    except CircuitOpenError:
        # Handle circuit open (fail fast)
        pass
```

### Method: `__init__`
**Parameters:** `self, name, failure_threshold, success_threshold, timeout`
**Implementation:**
```python
def __init__(self, name: str, failure_threshold: int=5, success_threshold: int=2, timeout: float=60.0):
    self.name = name
    self.config = CircuitBreakerConfig(failure_threshold=failure_threshold, success_threshold=success_threshold, timeout=timeout)
    self.stats = CircuitBreakerStats()
    self._lock = asyncio.Lock()
```

### Method: `state`
**Parameters:** `self`
**Implementation:**
```python
@property
def state(self) -> CircuitState:
    return self.stats.state
```

### Method: `is_closed`
**Parameters:** `self`
**Implementation:**
```python
@property
def is_closed(self) -> bool:
    return self.stats.state == CircuitState.CLOSED
```

### Method: `is_open`
**Parameters:** `self`
**Implementation:**
```python
@property
def is_open(self) -> bool:
    return self.stats.state == CircuitState.OPEN
```

### Method: `_should_attempt`
**Logic & Purpose:**
```text
Check if request should be attempted based on circuit state.
```

**Parameters:** `self`
**Variables Used:** `elapsed`
**Implementation:**
```python
def _should_attempt(self) -> bool:
    """Check if request should be attempted based on circuit state."""
    if self.stats.state == CircuitState.CLOSED:
        return True
    if self.stats.state == CircuitState.OPEN:
        if self.stats.last_failure_time:
            elapsed = time.time() - self.stats.last_failure_time
            if elapsed >= self.config.timeout:
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN after {elapsed:.1f}s")
                return True
        return False
    return True
```

### Method: `_record_success`
**Logic & Purpose:**
```text
Record a successful request.
```

**Parameters:** `self`
**Implementation:**
```python
def _record_success(self):
    """Record a successful request."""
    self.stats.total_successes += 1
    if self.stats.state == CircuitState.HALF_OPEN:
        self.stats.success_count += 1
        if self.stats.success_count >= self.config.success_threshold:
            self.stats.state = CircuitState.CLOSED
            self.stats.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' CLOSED after {self.stats.success_count} successes")
    else:
        self.stats.failure_count = 0
```

### Method: `_record_failure`
**Logic & Purpose:**
```text
Record a failed request.
```

**Parameters:** `self, error`
**Implementation:**
```python
def _record_failure(self, error: Exception):
    """Record a failed request."""
    self.stats.total_failures += 1
    self.stats.failure_count += 1
    self.stats.last_failure_time = time.time()
    if self.stats.state == CircuitState.HALF_OPEN:
        self.stats.state = CircuitState.OPEN
        logger.warning(f"Circuit breaker '{self.name}' OPEN (failed in half-open): {error}")
    elif self.stats.state == CircuitState.CLOSED:
        if self.stats.failure_count >= self.config.failure_threshold:
            self.stats.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker '{self.name}' OPEN after {self.stats.failure_count} failures: {error}")
```

### Method: `execute`
**Logic & Purpose:**
```text
Execute a function with circuit breaker protection.

Args:
    fn: Async function to execute
    *args, **kwargs: Arguments to pass to fn
    
Returns:
    Result of fn
    
Raises:
    CircuitOpenError: If circuit is open
    Exception: Any exception from fn (after recording failure)
```

**Parameters:** `self, fn`
**Variables Used:** `result`
**Implementation:**
```python
async def execute(self, fn: Callable, *args, **kwargs) -> Any:
    """
        Execute a function with circuit breaker protection.
        
        Args:
            fn: Async function to execute
            *args, **kwargs: Arguments to pass to fn
            
        Returns:
            Result of fn
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from fn (after recording failure)
        """
    async with self._lock:
        if not self._should_attempt():
            self.stats.total_rejections += 1
            raise CircuitOpenError(f"Circuit breaker '{self.name}' is OPEN - failing fast")
    try:
        result = await fn(*args, **kwargs)
        async with self._lock:
            self._record_success()
        return result
    except Exception as e:
        async with self._lock:
            self._record_failure(e)
        raise
```

### Method: `get_stats`
**Logic & Purpose:**
```text
Get circuit breaker statistics.
```

**Parameters:** `self`
**Implementation:**
```python
def get_stats(self) -> Dict[str, Any]:
    """Get circuit breaker statistics."""
    return {'name': self.name, 'state': self.stats.state.value, 'failure_count': self.stats.failure_count, 'success_count': self.stats.success_count, 'total_failures': self.stats.total_failures, 'total_successes': self.stats.total_successes, 'total_rejections': self.stats.total_rejections, 'config': {'failure_threshold': self.config.failure_threshold, 'success_threshold': self.config.success_threshold, 'timeout': self.config.timeout}}
```

### Method: `record_soft_failure`
**Logic & Purpose:**
```text
Record a structural response failure (HTTP 200 but unusable output).

Two soft failures accumulate to one hard-failure equivalent toward the
circuit-open threshold, so a consistently-broken-but-not-404 model
still gets penalized without tripping the breaker as aggressively.
```

**Parameters:** `self`
**Implementation:**
```python
def record_soft_failure(self) -> None:
    """
        Record a structural response failure (HTTP 200 but unusable output).

        Two soft failures accumulate to one hard-failure equivalent toward the
        circuit-open threshold, so a consistently-broken-but-not-404 model
        still gets penalized without tripping the breaker as aggressively.
        """
    self.stats.soft_failure_count += 1
    if self.stats.soft_failure_count % 2 == 0:

        class _SoftError(Exception):
            pass
        self._record_failure(_SoftError('soft failure accumulation'))
        logger.debug(f'[CB] {self.name}: soft failure #{self.stats.soft_failure_count} → equivalent hard failure triggered')
```

### Method: `record_parse_ok`
**Logic & Purpose:**
```text
Check structural validity of a non-streaming response and record the
result in the circuit breaker.

A response is 'ok' when:
  - choices list is non-empty
  - finish_reason is not 'length' (truncated output is unreliable)
  - at least one of: tool_calls populated OR non-empty message content

Returns True if the response is structurally valid.
```

**Parameters:** `self, response`
**Variables Used:** `has_tool_calls, has_content, finish_reason, msg, c, choices`
**Implementation:**
```python
def record_parse_ok(self, response: dict) -> bool:
    """
        Check structural validity of a non-streaming response and record the
        result in the circuit breaker.

        A response is 'ok' when:
          - choices list is non-empty
          - finish_reason is not 'length' (truncated output is unreliable)
          - at least one of: tool_calls populated OR non-empty message content

        Returns True if the response is structurally valid.
        """
    choices = response.get('choices', [])
    if not choices:
        self.record_soft_failure()
        logger.debug(f'[CB] {self.name}: parse_ok=False (empty choices)')
        return False
    c = choices[0]
    finish_reason = c.get('finish_reason', '')
    msg = c.get('message', {}) or {}
    has_tool_calls = bool(msg.get('tool_calls'))
    has_content = bool((msg.get('content') or '').strip())
    if finish_reason == 'length' and (not has_tool_calls):
        self.record_soft_failure()
        logger.debug(f'[CB] {self.name}: parse_ok=False (finish_reason=length, no tool_calls)')
        return False
    if not has_tool_calls and (not has_content):
        self.record_soft_failure()
        logger.debug(f'[CB] {self.name}: parse_ok=False (empty content and no tool_calls)')
        return False
    return True
```

### Method: `record_stream_finish`
**Logic & Purpose:**
```text
Record parse result for a completed streaming response.

Call this at stream end (after the last SSE chunk).
Returns True if the stream output is structurally valid.
```

**Parameters:** `self, finish_reason, had_tool_calls, had_content`
**Implementation:**
```python
def record_stream_finish(self, finish_reason: Optional[str], had_tool_calls: bool, had_content: bool) -> bool:
    """
        Record parse result for a completed streaming response.

        Call this at stream end (after the last SSE chunk).
        Returns True if the stream output is structurally valid.
        """
    if finish_reason == 'length' and (not had_tool_calls):
        self.record_soft_failure()
        logger.debug(f'[CB] {self.name}: stream parse_ok=False (finish_reason=length)')
        return False
    if not had_tool_calls and (not had_content):
        self.record_soft_failure()
        logger.debug(f'[CB] {self.name}: stream parse_ok=False (empty stream)')
        return False
    return True
```

### Method: `to_persist_dict`
**Logic & Purpose:**
```text
Serialise current state for disk persistence.
```

**Parameters:** `self`
**Implementation:**
```python
def to_persist_dict(self) -> dict:
    """Serialise current state for disk persistence."""
    return {'state': self.stats.state.value, 'failure_count': self.stats.failure_count, 'last_failure_time': self.stats.last_failure_time, 'soft_failure_count': self.stats.soft_failure_count, 'total_failures': self.stats.total_failures, 'total_successes': self.stats.total_successes}
```

### Method: `from_persist_dict`
**Logic & Purpose:**
```text
Restore a circuit breaker from a persisted dict.
```

**Parameters:** `cls, name, d`
**Variables Used:** `state_str, elapsed, cb`
**Implementation:**
```python
@classmethod
def from_persist_dict(cls, name: str, d: dict, **kwargs) -> 'CircuitBreaker':
    """Restore a circuit breaker from a persisted dict."""
    cb = cls(name=name, **kwargs)
    state_str = d.get('state', CircuitState.CLOSED.value)
    try:
        cb.stats.state = CircuitState(state_str)
    except ValueError:
        cb.stats.state = CircuitState.CLOSED
    cb.stats.failure_count = d.get('failure_count', 0)
    cb.stats.last_failure_time = d.get('last_failure_time')
    cb.stats.soft_failure_count = d.get('soft_failure_count', 0)
    cb.stats.total_failures = d.get('total_failures', 0)
    cb.stats.total_successes = d.get('total_successes', 0)
    if cb.stats.state == CircuitState.OPEN and cb.stats.last_failure_time:
        elapsed = time.time() - cb.stats.last_failure_time
        if elapsed >= cb.config.timeout:
            cb.stats.state = CircuitState.HALF_OPEN
            logger.info(f"[CB] Restored '{name}' to HALF_OPEN (timeout elapsed during restart)")
        else:
            logger.info(f"[CB] Restored '{name}' as OPEN ({elapsed:.0f}s into {cb.config.timeout:.0f}s cooldown)")
    return cb
```

### Method: `reset`
**Logic & Purpose:**
```text
Manually reset the circuit breaker to closed state.
```

**Parameters:** `self`
**Implementation:**
```python
def reset(self):
    """Manually reset the circuit breaker to closed state."""
    self.stats = CircuitBreakerStats()
    logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
```

---

## Feature Class: `CircuitOpenError`
**Description:**
```text
Raised when circuit breaker is open and rejecting requests.
```

---

## Feature Class: `CircuitBreakerRegistry`
**Description:**
```text
Registry for managing multiple circuit breakers.

Usage:
    registry = CircuitBreakerRegistry()
    breaker = registry.get("openrouter")
    await breaker.execute(fn)
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self._breakers: Dict[str, CircuitBreaker] = {}
    self._lock = asyncio.Lock()
    self._persisted = _load_persisted_state()
```

### Method: `get_instance`
**Logic & Purpose:**
```text
Get or create the singleton registry instance.
```

**Parameters:** `cls`
**Implementation:**
```python
@classmethod
def get_instance(cls) -> 'CircuitBreakerRegistry':
    """Get or create the singleton registry instance."""
    if cls._instance is None:
        cls._instance = cls()
    return cls._instance
```

### Method: `get`
**Logic & Purpose:**
```text
Get or create a circuit breaker by name.
```

**Parameters:** `self, name, failure_threshold, success_threshold, timeout`
**Implementation:**
```python
async def get(self, name: str, failure_threshold: int=5, success_threshold: int=2, timeout: float=60.0) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    async with self._lock:
        if name not in self._breakers:
            self._breakers[name] = self._make_breaker(name, failure_threshold, success_threshold, timeout)
        return self._breakers[name]
```

### Method: `get_sync`
**Logic & Purpose:**
```text
Synchronous version for non-async contexts.
```

**Parameters:** `self, name, failure_threshold, success_threshold, timeout`
**Implementation:**
```python
def get_sync(self, name: str, failure_threshold: int=5, success_threshold: int=2, timeout: float=60.0) -> CircuitBreaker:
    """Synchronous version for non-async contexts."""
    if name not in self._breakers:
        self._breakers[name] = self._make_breaker(name, failure_threshold, success_threshold, timeout)
    return self._breakers[name]
```

### Method: `_make_breaker`
**Logic & Purpose:**
```text
Create a new breaker, restoring persisted state if available.
```

**Parameters:** `self, name, failure_threshold, success_threshold, timeout`
**Variables Used:** `kwargs, cb`
**Implementation:**
```python
def _make_breaker(self, name: str, failure_threshold: int, success_threshold: int, timeout: float) -> CircuitBreaker:
    """Create a new breaker, restoring persisted state if available."""
    kwargs = dict(failure_threshold=failure_threshold, success_threshold=success_threshold, timeout=timeout)
    if name in self._persisted:
        cb = CircuitBreaker.from_persist_dict(name, self._persisted[name], **kwargs)
        logger.debug(f"[CB] Restored '{name}' from disk (state={cb.stats.state.value})")
    else:
        cb = CircuitBreaker(name=name, **kwargs)
        logger.debug(f"[CB] Created new breaker for '{name}'")
    return cb
```

### Method: `save_all`
**Logic & Purpose:**
```text
Persist all circuit breaker states to disk.
```

**Parameters:** `self`
**Variables Used:** `states`
**Implementation:**
```python
def save_all(self) -> None:
    """Persist all circuit breaker states to disk."""
    states = {name: cb.to_persist_dict() for name, cb in self._breakers.items()}
    _save_persisted_state(states)
```

### Method: `get_all_stats`
**Logic & Purpose:**
```text
Get statistics for all registered circuit breakers.
```

**Parameters:** `self`
**Implementation:**
```python
def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
    """Get statistics for all registered circuit breakers."""
    return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
```

### Method: `reset_all`
**Logic & Purpose:**
```text
Reset all circuit breakers.
```

**Parameters:** `self`
**Implementation:**
```python
def reset_all(self):
    """Reset all circuit breakers."""
    for breaker in self._breakers.values():
        breaker.reset()
```

---

## Feature Function: `get_circuit_breaker_registry`
**Logic & Purpose:**
```text
Get the global circuit breaker registry.
```

**Parameters:** ``
**Implementation:**
```python
def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return CircuitBreakerRegistry.get_instance()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/reasoning_validator.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/reasoning_validator.py`

**Module Overview**: 
```text
Reasoning parameter validator for OpenAI, Anthropic, and Gemini models.

Validates and adjusts reasoning parameters to provider-specific constraints:
- OpenAI o-series: effort levels (low, medium, high)
- Anthropic Claude: thinking token budget (1024-128000)
- Google Gemini: thinking budget (0-24576)

Capability detection uses keyword-based matching rather than version-specific
regex patterns, so new model versions are automatically supported.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `VALID_EFFORT_LEVELS` = `{'low', 'medium', 'high'}`
- `ANTHROPIC_MIN_TOKENS` = `1024`
- `ANTHROPIC_MAX_TOKENS` = `128000`
- `GEMINI_MIN_BUDGET` = `0`
- `GEMINI_MAX_BUDGET` = `24576`
- `OPENAI_O_SERIES_KEYWORDS` = `['o1-', 'o1mini', 'o3-', 'o3mini', 'o4-', 'o4mini', 'gpt-5', 'gpt5']`
- `ANTHROPIC_THINKING_KEYWORDS` = `['opus', 'sonnet', 'claude-3-7', 'claude-3.7']`
- `GEMINI_THINKING_KEYWORDS` = `['thinking', 'gemini-2', 'gemini-2.5', 'gemini-pro', 'gemini-flash']`

## Dependencies & Imports
logging, typing.Tuple

## Feature Function: `_is_openai_reasoning_model`
**Logic & Purpose:**
```text
Detect OpenAI o-series / GPT-5+ reasoning models by keyword.
```

**Parameters:** `model_lower`
**Implementation:**
```python
def _is_openai_reasoning_model(model_lower: str) -> bool:
    """Detect OpenAI o-series / GPT-5+ reasoning models by keyword."""
    return any((kw in model_lower for kw in OPENAI_O_SERIES_KEYWORDS))
```

---

## Feature Function: `_is_anthropic_thinking_model`
**Logic & Purpose:**
```text
Detect Anthropic Claude thinking-capable models by keyword.
```

**Parameters:** `model_lower`
**Implementation:**
```python
def _is_anthropic_thinking_model(model_lower: str) -> bool:
    """Detect Anthropic Claude thinking-capable models by keyword."""
    return 'claude' in model_lower and any((kw in model_lower for kw in ANTHROPIC_THINKING_KEYWORDS))
```

---

## Feature Function: `_is_gemini_thinking_model`
**Logic & Purpose:**
```text
Detect Gemini thinking-capable models by keyword.
```

**Parameters:** `model_lower`
**Implementation:**
```python
def _is_gemini_thinking_model(model_lower: str) -> bool:
    """Detect Gemini thinking-capable models by keyword."""
    return 'gemini' in model_lower and any((kw in model_lower for kw in GEMINI_THINKING_KEYWORDS))
```

---

## Feature Function: `validate_openai_reasoning`
**Logic & Purpose:**
```text
Validate OpenAI reasoning effort level.

Args:
    effort: Reasoning effort level (low, medium, high)

Returns:
    Validated effort level (lowercase)

Raises:
    ValueError: If effort level is not valid
```

**Parameters:** `effort`
**Variables Used:** `effort_lower`
**Implementation:**
```python
def validate_openai_reasoning(effort: str) -> str:
    """
    Validate OpenAI reasoning effort level.

    Args:
        effort: Reasoning effort level (low, medium, high)

    Returns:
        Validated effort level (lowercase)

    Raises:
        ValueError: If effort level is not valid
    """
    effort_lower = effort.lower()
    if effort_lower not in VALID_EFFORT_LEVELS:
        raise ValueError(f"Invalid reasoning effort '{effort}'. Valid options: {', '.join(sorted(VALID_EFFORT_LEVELS))}")
    logger.debug(f'Validated OpenAI reasoning effort: {effort_lower}')
    return effort_lower
```

---

## Feature Function: `validate_anthropic_thinking`
**Logic & Purpose:**
```text
Validate and adjust Anthropic thinking token budget to valid range (1024-16000).

Args:
    budget: Thinking token budget

Returns:
    Adjusted budget within valid range
```

**Parameters:** `budget`
**Variables Used:** `original_budget, budget`
**Implementation:**
```python
def validate_anthropic_thinking(budget: int) -> int:
    """
    Validate and adjust Anthropic thinking token budget to valid range (1024-16000).

    Args:
        budget: Thinking token budget

    Returns:
        Adjusted budget within valid range
    """
    original_budget = budget
    if budget < ANTHROPIC_MIN_TOKENS:
        budget = ANTHROPIC_MIN_TOKENS
        logger.warning(f'Anthropic thinking token budget {original_budget} is below minimum. Adjusted to {budget}. Valid range: {ANTHROPIC_MIN_TOKENS}-{ANTHROPIC_MAX_TOKENS}')
    elif budget > ANTHROPIC_MAX_TOKENS:
        budget = ANTHROPIC_MAX_TOKENS
        logger.warning(f'Anthropic thinking token budget {original_budget} exceeds maximum. Adjusted to {budget}. Valid range: {ANTHROPIC_MIN_TOKENS}-{ANTHROPIC_MAX_TOKENS}')
    else:
        logger.debug(f'Validated Anthropic thinking budget: {budget}')
    return budget
```

---

## Feature Function: `validate_gemini_thinking`
**Logic & Purpose:**
```text
Validate and adjust Gemini thinking budget to valid range (0-24576).

Args:
    budget: Thinking budget

Returns:
    Adjusted budget within valid range
```

**Parameters:** `budget`
**Variables Used:** `original_budget, budget`
**Implementation:**
```python
def validate_gemini_thinking(budget: int) -> int:
    """
    Validate and adjust Gemini thinking budget to valid range (0-24576).

    Args:
        budget: Thinking budget

    Returns:
        Adjusted budget within valid range
    """
    original_budget = budget
    if budget < GEMINI_MIN_BUDGET:
        budget = GEMINI_MIN_BUDGET
        logger.warning(f'Gemini thinking budget {original_budget} is below minimum. Adjusted to {budget}. Valid range: {GEMINI_MIN_BUDGET}-{GEMINI_MAX_BUDGET}')
    elif budget > GEMINI_MAX_BUDGET:
        budget = GEMINI_MAX_BUDGET
        logger.warning(f'Gemini thinking budget {original_budget} exceeds maximum. Adjusted to {budget}. Valid range: {GEMINI_MIN_BUDGET}-{GEMINI_MAX_BUDGET}')
    else:
        logger.debug(f'Validated Gemini thinking budget: {budget}')
    return budget
```

---

## Feature Function: `is_reasoning_capable_model`
**Logic & Purpose:**
```text
Check if model supports reasoning capabilities.

Uses keyword-based detection so new model versions are automatically supported.
For example, 'gemini-claude-opus-4-6-thinking' matches because it contains
both 'claude' and 'opus' keywords.

Args:
    model_name: Model name to check

Returns:
    Tuple of (is_capable, reasoning_type)
    - is_capable: True if model supports reasoning
    - reasoning_type: 'effort', 'thinking_tokens', 'thinking_budget', or empty string
```

**Parameters:** `model_name`
**Variables Used:** `model_lower`
**Implementation:**
```python
def is_reasoning_capable_model(model_name: str) -> Tuple[bool, str]:
    """
    Check if model supports reasoning capabilities.

    Uses keyword-based detection so new model versions are automatically supported.
    For example, 'gemini-claude-opus-4-6-thinking' matches because it contains
    both 'claude' and 'opus' keywords.

    Args:
        model_name: Model name to check

    Returns:
        Tuple of (is_capable, reasoning_type)
        - is_capable: True if model supports reasoning
        - reasoning_type: 'effort', 'thinking_tokens', 'thinking_budget', or empty string
    """
    model_lower = model_name.lower()
    if '/' in model_lower:
        model_lower = model_lower.split('/', 1)[1]
    if _is_gemini_thinking_model(model_lower):
        logger.debug(f'Model {model_name} supports Gemini thinking budget')
        return (True, 'thinking_budget')
    if _is_openai_reasoning_model(model_lower):
        logger.debug(f'Model {model_name} supports OpenAI reasoning effort')
        return (True, 'effort')
    if _is_anthropic_thinking_model(model_lower):
        logger.debug(f'Model {model_name} supports Anthropic thinking tokens')
        return (True, 'thinking_tokens')
    logger.debug(f'Model {model_name} does not support reasoning capabilities')
    return (False, '')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/core/logging.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/logging.py`

## Global Presets & Variables
- `log_level` = `config.log_level.split()[0].upper()`
- `valid_levels` = `['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']`
- `logger` = `logging.getLogger(__name__)`

## Dependencies & Imports
logging, src.core.config.config


# File Audit: /home/cheta/code/claude-code-proxy/src/core/constants.py
**Path**: `/home/cheta/code/claude-code-proxy/src/core/constants.py`

## Feature Class: `Constants`
---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/model_display_utils.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/model_display_utils.py`

**Module Overview**: 
```text
Shared utilities for formatting model names in dashboard displays.

These functions use dynamic model family detection to create consistent
shortened display names without hardcoding specific model versions.
```

## Dependencies & Imports
src.services.models.model_family.detect_model_family, src.services.models.model_family.ModelFamily

## Feature Function: `format_model_name`
**Logic & Purpose:**
```text
Format model name for display using dynamic family detection.

Returns shortened names like "claude-opus", "claude-sonnet", "gpt4o", "o1", "gemini"
instead of full version strings.

Args:
    model_name: Full model identifier

Returns:
    Shortened display name
```

**Parameters:** `model_name`
**Variables Used:** `model_lower, family_info`
**Implementation:**
```python
def format_model_name(model_name: str) -> str:
    """
    Format model name for display using dynamic family detection.

    Returns shortened names like "claude-opus", "claude-sonnet", "gpt4o", "o1", "gemini"
    instead of full version strings.

    Args:
        model_name: Full model identifier

    Returns:
        Shortened display name
    """
    if not model_name:
        return 'unknown'
    model_lower = model_name.lower()
    try:
        family_info = detect_model_family(model_name)
        if family_info.family == ModelFamily.ANTHROPIC_CLAUDE:
            if family_info.tier:
                return f'claude-{family_info.tier}'
            return 'claude'
        elif family_info.family == ModelFamily.OPENAI_GPT:
            if 'mini' in model_lower or family_info.tier == 'mini':
                return 'gpt4o-mini'
            return 'gpt4o'
        elif family_info.family == ModelFamily.OPENAI_O_SERIES:
            if family_info.tier == 'mini':
                return 'o1-mini'
            return 'o1'
        elif family_info.family in (ModelFamily.GEMINI_FLASH, ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_OTHER):
            if family_info.tier:
                return f'gemini-{family_info.tier}'
            return 'gemini'
    except Exception:
        pass
    if 'claude' in model_lower:
        if 'opus' in model_lower:
            return 'claude-opus'
        elif 'sonnet' in model_lower:
            return 'claude-sonnet'
        elif 'haiku' in model_lower:
            return 'claude-haiku'
        return 'claude'
    elif 'gpt-4o' in model_lower:
        return 'gpt4o' + ('-mini' if 'mini' in model_lower else '')
    elif 'gpt-4' in model_lower:
        return 'gpt4'
    elif 'o1' in model_lower:
        return 'o1' + ('-mini' if 'mini' in model_lower else '')
    elif 'o3' in model_lower:
        return 'o3' + ('-mini' if 'mini' in model_lower else '')
    elif 'gemini' in model_lower:
        return 'gemini'
    return model_name.split('/')[-1][:10] if '/' in model_name else model_name[:10]
```

---

## Feature Function: `is_reasoning_model`
**Logic & Purpose:**
```text
Check if model supports reasoning/thinking (for cost estimation).
```

**Parameters:** `model_name`
**Variables Used:** `model_lower, family_info`
**Implementation:**
```python
def is_reasoning_model(model_name: str) -> bool:
    """Check if model supports reasoning/thinking (for cost estimation)."""
    if not model_name:
        return False
    model_lower = model_name.lower()
    if any((p in model_lower for p in ['o1', 'o3', 'o4', 'claude', 'gemini'])):
        return True
    try:
        family_info = detect_model_family(model_name)
        return family_info.family in (ModelFamily.OPENAI_O_SERIES, ModelFamily.ANTHROPIC_CLAUDE, ModelFamily.GEMINI_PRO, ModelFamily.GEMINI_FLASH)
    except Exception:
        return False
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/prompt_modules.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/prompt_modules.py`

**Module Overview**: 
```text
Prompt Dashboard Modules

Renders dashboard data for injection into Claude Code prompts.
Supports multiple size variants (large, medium, small) with Nerd Fonts.
```

## Global Presets & Variables
- `prompt_dashboard_renderer` = `PromptDashboardRenderer()`

## Dependencies & Imports
typing.Dict, typing.Any, typing.List, typing.Optional, datetime.datetime, src.dashboard.dashboard_hooks.dashboard_hooks

## Feature Class: `PromptDashboardModule`
**Description:**
```text
Base class for prompt-injectable dashboard modules
```

### Method: `__init__`
**Parameters:** `self, name`
**Implementation:**
```python
def __init__(self, name: str):
    self.name = name
```

### Method: `render_large`
**Logic & Purpose:**
```text
Multi-line detailed format (~200-300 chars)
```

**Parameters:** `self, stats`
**Implementation:**
```python
def render_large(self, stats: Dict[str, Any]) -> str:
    """Multi-line detailed format (~200-300 chars)"""
    raise NotImplementedError
```

### Method: `render_medium`
**Logic & Purpose:**
```text
Single-line compact format (~80-120 chars)
```

**Parameters:** `self, stats`
**Implementation:**
```python
def render_medium(self, stats: Dict[str, Any]) -> str:
    """Single-line compact format (~80-120 chars)"""
    raise NotImplementedError
```

### Method: `render_small`
**Logic & Purpose:**
```text
Ultra-compact inline format (~30-50 chars)
```

**Parameters:** `self, stats`
**Implementation:**
```python
def render_small(self, stats: Dict[str, Any]) -> str:
    """Ultra-compact inline format (~30-50 chars)"""
    raise NotImplementedError
```

---

## Feature Class: `ProxyStatusPromptModule`
**Description:**
```text
Proxy status and configuration for prompts
```

### Method: `render_large`
**Parameters:** `self, stats`
**Variables Used:** `provider`
**Implementation:**
```python
def render_large(self, stats: Dict[str, Any]) -> str:
    from src.core.config import config
    provider = self._get_provider_name(config.openai_base_url)
    return f"┌─ 🔧 Proxy Status ─────────────────────────────────────┐\n│ Provider: {provider:12} │ Mode: {('Passthrough' if config.passthrough_mode else 'Proxy')}              │\n│ BIG:    {config.big_model[:28]:28} │\n│ MIDDLE: {config.middle_model[:28]:28} │\n│ SMALL:  {config.small_model[:28]:28} │\n│ Reasoning: {(config.reasoning_effort or 'none')[:10]:10} │ Max Tokens: {str(config.reasoning_max_tokens or 'auto')[:8]:8} │\n└────────────────────────────────────────────────────────┘"
```

### Method: `render_medium`
**Parameters:** `self, stats`
**Variables Used:** `big_short, reasoning, provider`
**Implementation:**
```python
def render_medium(self, stats: Dict[str, Any]) -> str:
    from src.core.config import config
    provider = self._get_provider_name(config.openai_base_url)
    big_short = config.big_model.split('/')[-1][:12]
    reasoning = config.reasoning_effort or 'none'
    return f"🔧 {provider} | 🤖 {big_short} | 🧠 {reasoning} | {('🔓' if config.passthrough_mode else '🔒')}"
```

### Method: `render_small`
**Parameters:** `self, stats`
**Variables Used:** `provider_icon, reasoning_icon`
**Implementation:**
```python
def render_small(self, stats: Dict[str, Any]) -> str:
    from src.core.config import config
    provider_icon = '🌐' if 'openrouter' in config.openai_base_url.lower() else '🔧'
    reasoning_icon = '🧠' if config.reasoning_effort else '💭'
    return f'{provider_icon}{reasoning_icon}'
```

### Method: `_get_provider_name`
**Parameters:** `self, url`
**Implementation:**
```python
def _get_provider_name(self, url: str) -> str:
    if 'openrouter' in url.lower():
        return 'OpenRouter'
    elif 'openai' in url.lower():
        return 'OpenAI'
    elif 'anthropic' in url.lower():
        return 'Anthropic'
    return 'Custom'
```

---

## Feature Class: `PerformancePromptModule`
**Description:**
```text
Performance metrics for prompts
```

### Method: `render_large`
**Parameters:** `self, stats`
**Variables Used:** `tps, cost, success_rate, total_req, avg_lat`
**Implementation:**
```python
def render_large(self, stats: Dict[str, Any]) -> str:
    total_req = stats.get('total_requests', 0)
    avg_lat = stats.get('avg_latency_ms', 0)
    tps = stats.get('avg_tokens_per_sec', 0)
    cost = stats.get('total_cost', 0.0)
    success_rate = stats.get('success_count', 0) / max(total_req, 1) * 100
    return f"┌─ ⚡ Performance ──────────────────────────────────────┐\n│ Requests: {total_req:5} │ Success: {success_rate:5.1f}%             │\n│ Latency:  {avg_lat:5.0f}ms │ Speed: {tps:5.0f} tok/s          │\n│ Cost:     ${cost:7.3f} │ Avg/req: ${cost / max(total_req, 1):6.4f}     │\n│ Tokens: ↑{stats.get('total_input_tokens', 0):7,} ↓{stats.get('total_output_tokens', 0):7,}           │\n└────────────────────────────────────────────────────────┘"
```

### Method: `render_medium`
**Parameters:** `self, stats`
**Variables Used:** `tps, total_req, cost, avg_lat`
**Implementation:**
```python
def render_medium(self, stats: Dict[str, Any]) -> str:
    total_req = stats.get('total_requests', 0)
    avg_lat = stats.get('avg_latency_ms', 0)
    tps = stats.get('avg_tokens_per_sec', 0)
    cost = stats.get('total_cost', 0.0)
    return f'⚡ {total_req}req | {avg_lat:.0f}ms | {tps:.0f}t/s | ${cost:.3f}'
```

### Method: `render_small`
**Parameters:** `self, stats`
**Variables Used:** `tps, total_req`
**Implementation:**
```python
def render_small(self, stats: Dict[str, Any]) -> str:
    total_req = stats.get('total_requests', 0)
    tps = stats.get('avg_tokens_per_sec', 0)
    return f'⚡{total_req}r·{tps:.0f}t/s'
```

---

## Feature Class: `ErrorTrackingPromptModule`
**Description:**
```text
Error tracking and reliability for prompts
```

### Method: `render_large`
**Parameters:** `self, stats`
**Variables Used:** `error_display, error_types, top_errors, success, total, errors, error_lines, success_rate`
**Implementation:**
```python
def render_large(self, stats: Dict[str, Any]) -> str:
    success = stats.get('success_count', 0)
    errors = stats.get('error_count', 0)
    total = success + errors
    success_rate = success / max(total, 1) * 100
    error_types = stats.get('error_types', {})
    top_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]
    error_lines = []
    for err_type, count in top_errors:
        error_lines.append(f'  • {err_type[:20]:20} {count:3}x')
    error_display = '\n'.join(error_lines) if error_lines else '  • No errors yet! ✓'
    return f'┌─ ⚠️  Error Tracking ──────────────────────────────────┐\n│ Success: {success:5} ({success_rate:5.1f}%) │ Errors: {errors:5}       │\n│ {error_display:50} │\n└────────────────────────────────────────────────────────┘'
```

### Method: `render_medium`
**Parameters:** `self, stats`
**Variables Used:** `success, total, status_icon, errors, success_rate`
**Implementation:**
```python
def render_medium(self, stats: Dict[str, Any]) -> str:
    success = stats.get('success_count', 0)
    errors = stats.get('error_count', 0)
    total = success + errors
    success_rate = success / max(total, 1) * 100
    status_icon = '✓' if success_rate >= 95 else '⚠️' if success_rate >= 80 else '❌'
    return f'{status_icon} {success}/{total} OK ({success_rate:.1f}%) | {errors} ERR'
```

### Method: `render_small`
**Parameters:** `self, stats`
**Variables Used:** `success, errors, success_rate, total`
**Implementation:**
```python
def render_small(self, stats: Dict[str, Any]) -> str:
    success = stats.get('success_count', 0)
    errors = stats.get('error_count', 0)
    total = success + errors
    success_rate = success / max(total, 1) * 100
    return f"{('✓' if success_rate >= 95 else '⚠️')}{success_rate:.0f}%"
```

---

## Feature Class: `ModelUsagePromptModule`
**Description:**
```text
Model usage statistics for prompts
```

### Method: `render_large`
**Parameters:** `self, stats`
**Variables Used:** `model_display, cost, requests, model_lines, top_models, name`
**Implementation:**
```python
def render_large(self, stats: Dict[str, Any]) -> str:
    top_models = stats.get('top_models', [])[:5]
    model_lines = []
    for i, model in enumerate(top_models, 1):
        name = model['name'].split('/')[-1][:24]
        requests = model['requests']
        cost = model.get('cost', 0.0)
        model_lines.append(f'  {i}. {name:24} {requests:3}req ${cost:6.3f}')
    model_display = '\n'.join(model_lines) if model_lines else '  No data yet'
    return f'┌─ 🤖 Model Usage ──────────────────────────────────────┐\n│ {model_display:50} │\n└────────────────────────────────────────────────────────┘'
```

### Method: `render_medium`
**Parameters:** `self, stats`
**Variables Used:** `models_str, top_models`
**Implementation:**
```python
def render_medium(self, stats: Dict[str, Any]) -> str:
    top_models = stats.get('top_models', [])[:3]
    if not top_models:
        return '🤖 No model data'
    models_str = ' | '.join([f"{m['name'].split('/')[-1][:12]}:{m['requests']}" for m in top_models])
    return f'🤖 {models_str}'
```

### Method: `render_small`
**Parameters:** `self, stats`
**Variables Used:** `top_model, top_models`
**Implementation:**
```python
def render_small(self, stats: Dict[str, Any]) -> str:
    top_models = stats.get('top_models', [])
    if not top_models:
        return '🤖-'
    top_model = top_models[0]['name'].split('/')[-1][:8]
    return f'🤖{top_model}'
```

---

## Feature Class: `PromptDashboardRenderer`
**Description:**
```text
Renders dashboard modules for Claude Code prompt injection
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.modules = {'status': ProxyStatusPromptModule('status'), 'performance': PerformancePromptModule('performance'), 'errors': ErrorTrackingPromptModule('errors'), 'models': ModelUsagePromptModule('models')}
```

### Method: `render`
**Logic & Purpose:**
```text
Render selected modules at specified size.

Args:
    modules: List of module names to render
    size: 'large', 'medium', or 'small'
    stats: Statistics dict (uses live data if None)

Returns:
    Rendered prompt text
```

**Parameters:** `self, modules, size, stats`
**Variables Used:** `module, render_method, stats, output, separator, outputs`
**Implementation:**
```python
def render(self, modules: List[str], size: str='medium', stats: Optional[Dict[str, Any]]=None) -> str:
    """
        Render selected modules at specified size.

        Args:
            modules: List of module names to render
            size: 'large', 'medium', or 'small'
            stats: Statistics dict (uses live data if None)

        Returns:
            Rendered prompt text
        """
    if stats is None:
        stats = dashboard_hooks.get_stats()
    render_method = f'render_{size}'
    outputs = []
    for module_name in modules:
        if module_name not in self.modules:
            continue
        module = self.modules[module_name]
        if not hasattr(module, render_method):
            continue
        try:
            output = getattr(module, render_method)(stats)
            outputs.append(output)
        except Exception as e:
            pass
    if not outputs:
        return ''
    if size == 'large':
        separator = '\n\n'
    elif size == 'medium':
        separator = '\n'
    else:
        separator = ' '
    return separator.join(outputs)
```

### Method: `render_header`
**Logic & Purpose:**
```text
Render as compact header (single line regardless of size).

Uses small rendering for all modules and joins horizontally.
```

**Parameters:** `self, modules, size, stats`
**Variables Used:** `stats, output, module, outputs`
**Implementation:**
```python
def render_header(self, modules: List[str], size: str='medium', stats: Optional[Dict[str, Any]]=None) -> str:
    """
        Render as compact header (single line regardless of size).

        Uses small rendering for all modules and joins horizontally.
        """
    if stats is None:
        stats = dashboard_hooks.get_stats()
    outputs = []
    for module_name in modules:
        if module_name not in self.modules:
            continue
        module = self.modules[module_name]
        try:
            output = module.render_small(stats)
            outputs.append(output)
        except Exception:
            pass
    return ' '.join(outputs) if outputs else ''
```

### Method: `get_available_modules`
**Logic & Purpose:**
```text
Get list of available module names
```

**Parameters:** `self`
**Implementation:**
```python
def get_available_modules(self) -> List[str]:
    """Get list of available module names"""
    return list(self.modules.keys())
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/live_dashboard.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/live_dashboard.py`

**Module Overview**: 
```text
Live Dashboard - Real-time API monitoring interface.

Replaces standard terminal output with a rich dashboard interface.
```

## Dependencies & Imports
os, sys, asyncio, signal, typing.Dict, typing.Any, src.dashboard.dashboard_manager.dashboard_manager, src.utils.request_logger.RequestLogger

## Feature Class: `LiveDashboard`
**Description:**
```text
Live updating dashboard that replaces terminal logging.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.console = Console() if RICH_AVAILABLE else None
    self.running = False
    self.live_display = None
    self._setup_dashboard_integration()
```

### Method: `_setup_dashboard_integration`
**Logic & Purpose:**
```text
Integrate dashboard with request logging.
```

**Parameters:** `self`
**Variables Used:** `original_log_complete, request_data, original_log_start, original_log_error`
**Implementation:**
```python
def _setup_dashboard_integration(self):
    """Integrate dashboard with request logging."""
    original_log_complete = RequestLogger.log_request_complete
    original_log_start = RequestLogger.log_request_start
    original_log_error = RequestLogger.log_request_error

    def dashboard_log_start(*args, **kwargs):
        """Enhanced log_request_start that feeds dashboard."""
        original_log_start(*args, **kwargs)
        request_data = {'type': 'start', 'request_id': kwargs.get('request_id', args[0] if args else 'unknown'), 'original_model': kwargs.get('original_model', args[1] if len(args) > 1 else 'unknown'), 'routed_model': kwargs.get('routed_model', args[2] if len(args) > 2 else 'unknown'), 'endpoint': kwargs.get('endpoint', args[3] if len(args) > 3 else 'unknown'), 'reasoning_config': kwargs.get('reasoning_config'), 'stream': kwargs.get('stream', False), 'context_limit': kwargs.get('context_limit', 0), 'output_limit': kwargs.get('output_limit', 0), 'input_tokens': kwargs.get('input_tokens', 0), 'message_count': kwargs.get('message_count', 0), 'has_system': kwargs.get('has_system', False), 'client_info': kwargs.get('client_info', 'unknown')}
        dashboard_manager.log_request_data(request_data)

    def dashboard_log_complete(*args, **kwargs):
        """Enhanced log_request_complete that feeds dashboard."""
        original_log_complete(*args, **kwargs)
        request_data = {'type': 'complete', 'request_id': kwargs.get('request_id', args[0] if args else 'unknown'), 'usage': kwargs.get('usage', {}), 'duration_ms': kwargs.get('duration_ms', 0), 'status': kwargs.get('status', 'OK'), 'model_name': kwargs.get('model_name', 'unknown'), 'stream': kwargs.get('stream', False), 'message_count': kwargs.get('message_count', 0), 'has_system': kwargs.get('has_system', False), 'client_info': kwargs.get('client_info', 'unknown')}
        dashboard_manager.log_request_data(request_data)

    def dashboard_log_error(*args, **kwargs):
        """Enhanced log_request_error that feeds dashboard."""
        original_log_error(*args, **kwargs)
        request_data = {'type': 'error', 'request_id': kwargs.get('request_id', args[0] if args else 'unknown'), 'error': kwargs.get('error', args[1] if len(args) > 1 else 'unknown'), 'duration_ms': kwargs.get('duration_ms', 0)}
        dashboard_manager.log_request_data(request_data)
    RequestLogger.log_request_start = staticmethod(dashboard_log_start)
    RequestLogger.log_request_complete = staticmethod(dashboard_log_complete)
    RequestLogger.log_request_error = staticmethod(dashboard_log_error)
```

### Method: `create_header`
**Logic & Purpose:**
```text
Create dashboard header.
```

**Parameters:** `self`
**Variables Used:** `header_text`
**Implementation:**
```python
def create_header(self) -> Panel:
    """Create dashboard header."""
    header_text = Text()
    header_text.append('🚀 API Dashboard', style='bold cyan')
    header_text.append(' | ', style='dim')
    header_text.append('Live Monitoring', style='green')
    header_text.append(' | ', style='dim')
    header_text.append('Press Ctrl+C to exit', style='dim')
    return Panel(header_text, style='cyan')
```

### Method: `create_layout`
**Logic & Purpose:**
```text
Create the main dashboard layout.
```

**Parameters:** `self`
**Variables Used:** `layout, dashboard_content`
**Implementation:**
```python
def create_layout(self) -> Layout:
    """Create the main dashboard layout."""
    layout = Layout(name='root')
    layout.split_column(Layout(self.create_header(), name='header', size=3), Layout(name='main'))
    dashboard_content = dashboard_manager.render_dashboard()
    layout['main'].update(dashboard_content)
    return layout
```

### Method: `start`
**Logic & Purpose:**
```text
Start the live dashboard.
```

**Parameters:** `self, refresh_rate`
**Variables Used:** `layout`
**Implementation:**
```python
async def start(self, refresh_rate: float=2.0):
    """Start the live dashboard."""
    if not RICH_AVAILABLE:
        print('Rich library not available. Falling back to standard logging.')
        return
    self.running = True

    def signal_handler(signum, frame):
        self.running = False
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        with Live(self.create_layout(), console=self.console, refresh_per_second=refresh_rate, screen=True) as live:
            self.live_display = live
            while self.running:
                try:
                    layout = self.create_layout()
                    live.update(layout)
                    await asyncio.sleep(1.0 / refresh_rate)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    if self.console:
                        self.console.print(f'[red]Dashboard error: {e}[/red]')
                    await asyncio.sleep(1.0)
    except Exception as e:
        if self.console:
            self.console.print(f'[red]Failed to start dashboard: {e}[/red]')
        print(f'Failed to start dashboard: {e}')
    finally:
        self.running = False
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop the dashboard.
```

**Parameters:** `self`
**Implementation:**
```python
def stop(self):
    """Stop the dashboard."""
    self.running = False
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main entry point for live dashboard.
```

**Parameters:** ``
**Variables Used:** `dashboard, config`
**Implementation:**
```python
def main():
    """Main entry point for live dashboard."""
    config = os.environ.get('DASHBOARD_MODULES')
    if not config:
        print('No dashboard configuration found.')
        print("Run 'python configure_dashboard.py' to set up your dashboard.")
        return
    print(f'Starting dashboard with modules: {config}')
    dashboard = LiveDashboard()
    try:
        asyncio.run(dashboard.start())
    except KeyboardInterrupt:
        print('\nDashboard stopped.')
    except Exception as e:
        print(f'Dashboard error: {e}')
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/dashboard_hooks.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/dashboard_hooks.py`

**Module Overview**: 
```text
Dashboard Integration Hooks

Provides hooks for integrating proxy request/response flow with the terminal dashboard.
```

## Global Presets & Variables
- `dashboard_hooks` = `DashboardHooks()`

## Dependencies & Imports
typing.Dict, typing.Any, typing.Optional, src.core.config.config, time, asyncio

## Feature Class: `DashboardHooks`
**Description:**
```text
Hooks for feeding data to dashboard and prompt injection system
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.enabled = False
    self.terminal_dashboard = None
    self.websocket_enabled = False
    self.request_stats = {'total_requests': 0, 'today_requests': 0, 'total_cost': 0.0, 'today_cost': 0.0, 'avg_latency_ms': 0, 'min_latency_ms': 0, 'max_latency_ms': 0, 'avg_tokens_per_sec': 0, 'max_tokens_per_sec': 0, 'total_input_tokens': 0, 'total_output_tokens': 0, 'total_thinking_tokens': 0, 'avg_input_tokens': 0, 'avg_output_tokens': 0, 'avg_thinking_tokens': 0, 'avg_context_tokens': 0, 'avg_context_limit': 0, 'avg_cost_per_request': 0.0, 'success_count': 0, 'error_count': 0, 'error_types': {}, 'recent_errors': [], 'top_models': [], 'usage_by_type': {'text_only': 0, 'with_tools': 0, 'with_images': 0}, 'free_savings': 0.0}
    self.latency_samples = []
    self.tokens_per_sec_samples = []
    self.model_usage = {}
```

### Method: `enable`
**Logic & Purpose:**
```text
Enable dashboard hooks
```

**Parameters:** `self`
**Implementation:**
```python
def enable(self):
    """Enable dashboard hooks"""
    if config.enable_dashboard:
        try:
            from src.dashboard.terminal_dashboard import terminal_dashboard
            self.terminal_dashboard = terminal_dashboard
            self.enabled = True
        except ImportError:
            pass
    try:
        from src.api.websocket_dashboard import dashboard_broadcaster
        self.websocket_enabled = True
    except ImportError:
        pass
```

### Method: `_broadcast_websocket`
**Logic & Purpose:**
```text
Broadcast message via WebSocket if enabled
```

**Parameters:** `self, message_type, data`
**Variables Used:** `loop`
**Implementation:**
```python
def _broadcast_websocket(self, message_type: str, data: Dict[str, Any]):
    """Broadcast message via WebSocket if enabled"""
    if not self.websocket_enabled:
        return
    try:
        from src.api.websocket_dashboard import broadcast_dashboard_update
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_dashboard_update(message_type, data))
    except Exception:
        pass
```

### Method: `on_request_start`
**Logic & Purpose:**
```text
Called when a request starts
```

**Parameters:** `self, request_id, request_data`
**Implementation:**
```python
def on_request_start(self, request_id: str, request_data: Dict[str, Any]):
    """Called when a request starts"""
    if self.enabled and self.terminal_dashboard:
        try:
            self.terminal_dashboard.waterfall.add_request(request_id, request_data)
            self.terminal_dashboard.update()
        except Exception:
            pass
    self._broadcast_websocket('request_start', {'request_id': request_id, **request_data})
```

### Method: `on_request_phase`
**Logic & Purpose:**
```text
Called when a request enters a new phase
```

**Parameters:** `self, request_id, phase`
**Implementation:**
```python
def on_request_phase(self, request_id: str, phase: str):
    """Called when a request enters a new phase"""
    if not self.enabled or not self.terminal_dashboard:
        return
    try:
        self.terminal_dashboard.waterfall.update_phase(request_id, phase)
        self.terminal_dashboard.update()
    except Exception:
        pass
```

### Method: `on_request_complete`
**Logic & Purpose:**
```text
Called when a request completes (success or error)
```

**Parameters:** `self, request_id, status, data`
**Variables Used:** `tps, total_count, success_count, error_type, model, top_models, duration`
**Implementation:**
```python
def on_request_complete(self, request_id: str, status: str, data: Dict[str, Any]):
    """Called when a request completes (success or error)"""
    if not self.enabled:
        return
    self.request_stats['total_requests'] += 1
    if status == 'completed':
        self.request_stats['success_count'] += 1
    else:
        self.request_stats['error_count'] += 1
        error_type = data.get('error_type', 'Unknown')
        self.request_stats['error_types'][error_type] = self.request_stats['error_types'].get(error_type, 0) + 1
        self.request_stats['recent_errors'].append({'time': time.strftime('%H:%M'), 'type': error_type, 'message': data.get('error', '')[:50], 'model': data.get('model', '')})
        if len(self.request_stats['recent_errors']) > 10:
            self.request_stats['recent_errors'].pop(0)
    if 'duration_ms' in data:
        duration = data['duration_ms']
        self.latency_samples.append(duration)
        if len(self.latency_samples) > 100:
            self.latency_samples.pop(0)
        self.request_stats['avg_latency_ms'] = int(sum(self.latency_samples) / len(self.latency_samples))
        self.request_stats['min_latency_ms'] = min(self.latency_samples)
        self.request_stats['max_latency_ms'] = max(self.latency_samples)
    if 'input_tokens' in data:
        self.request_stats['total_input_tokens'] += data['input_tokens']
    if 'output_tokens' in data:
        self.request_stats['total_output_tokens'] += data['output_tokens']
    if 'thinking_tokens' in data:
        self.request_stats['total_thinking_tokens'] += data['thinking_tokens']
    if 'cost' in data:
        self.request_stats['total_cost'] += data['cost']
    if 'tokens_per_sec' in data:
        tps = data['tokens_per_sec']
        self.tokens_per_sec_samples.append(tps)
        if len(self.tokens_per_sec_samples) > 100:
            self.tokens_per_sec_samples.pop(0)
        self.request_stats['avg_tokens_per_sec'] = int(sum(self.tokens_per_sec_samples) / len(self.tokens_per_sec_samples))
        self.request_stats['max_tokens_per_sec'] = max(self.tokens_per_sec_samples)
    model = data.get('model', 'unknown')
    if model not in self.model_usage:
        self.model_usage[model] = {'requests': 0, 'tokens': 0, 'cost': 0.0}
    self.model_usage[model]['requests'] += 1
    if 'input_tokens' in data and 'output_tokens' in data:
        self.model_usage[model]['tokens'] += data['input_tokens'] + data['output_tokens']
    if 'cost' in data:
        self.model_usage[model]['cost'] += data['cost']
    top_models = sorted(self.model_usage.items(), key=lambda x: x[1]['requests'], reverse=True)[:5]
    self.request_stats['top_models'] = [{'name': model, 'requests': stats['requests'], 'tokens': stats['tokens'], 'cost': stats['cost']} for model, stats in top_models]
    if data.get('has_tools'):
        self.request_stats['usage_by_type']['with_tools'] += 1
    elif data.get('has_images'):
        self.request_stats['usage_by_type']['with_images'] += 1
    else:
        self.request_stats['usage_by_type']['text_only'] += 1
    if self.request_stats['total_requests'] > 0:
        self.request_stats['avg_input_tokens'] = int(self.request_stats['total_input_tokens'] / self.request_stats['total_requests'])
        self.request_stats['avg_output_tokens'] = int(self.request_stats['total_output_tokens'] / self.request_stats['total_requests'])
        self.request_stats['avg_thinking_tokens'] = int(self.request_stats['total_thinking_tokens'] / self.request_stats['total_requests'])
        self.request_stats['avg_cost_per_request'] = self.request_stats['total_cost'] / self.request_stats['total_requests']
    if self.terminal_dashboard:
        try:
            self.terminal_dashboard.waterfall.complete_request(request_id, status, data)
            self.terminal_dashboard.update_module('performance', {'total_requests': self.request_stats['total_requests'], 'today_requests': self.request_stats['today_requests'], 'avg_latency_ms': self.request_stats['avg_latency_ms'], 'min_latency_ms': self.request_stats['min_latency_ms'], 'max_latency_ms': self.request_stats['max_latency_ms'], 'avg_tokens_per_sec': self.request_stats['avg_tokens_per_sec'], 'max_tokens_per_sec': self.request_stats['max_tokens_per_sec'], 'total_input_tokens': self.request_stats['total_input_tokens'], 'total_output_tokens': self.request_stats['total_output_tokens'], 'total_thinking_tokens': self.request_stats['total_thinking_tokens'], 'avg_input_tokens': self.request_stats['avg_input_tokens'], 'avg_output_tokens': self.request_stats['avg_output_tokens'], 'avg_thinking_tokens': self.request_stats['avg_thinking_tokens'], 'avg_context_tokens': data.get('context_tokens', 0), 'avg_context_limit': data.get('context_limit', 0), 'total_cost': self.request_stats['total_cost'], 'today_cost': self.request_stats['today_cost'], 'avg_cost_per_request': self.request_stats['avg_cost_per_request'], 'success_rate': self.request_stats['success_count'] / self.request_stats['total_requests'] * 100 if self.request_stats['total_requests'] > 0 else 100})
            self.terminal_dashboard.update_module('routing', {'provider': self._get_provider_name(config.openai_base_url), 'base_url': config.openai_base_url, 'big_model': config.big_model, 'middle_model': config.middle_model, 'small_model': config.small_model, 'passthrough_mode': config.passthrough_mode, 'reasoning_effort': config.reasoning_effort or 'none', 'reasoning_max_tokens': config.reasoning_max_tokens})
            self.terminal_dashboard.update_module('activity', {'request': {'status': status, 'model': data.get('model', ''), 'duration_ms': data.get('duration_ms', 0)}})
            self.terminal_dashboard.update_module('models', {'top_models': self.request_stats['top_models'], 'usage_by_type': self.request_stats['usage_by_type']})
            self.terminal_dashboard.update()
        except Exception:
            pass
    self._broadcast_websocket('request_complete' if status == 'completed' else 'request_error', {'request_id': request_id, 'status': status, **data})
    self._broadcast_websocket('stats_update', self.request_stats)
    try:
        from src.utils.prompt_injection_middleware import update_proxy_status
        total_count = self.request_stats['success_count'] + self.request_stats['error_count']
        success_count = self.request_stats['success_count']
        update_proxy_status({'status': {'passthrough_mode': config.passthrough_mode, 'provider': self._get_provider_name(config.openai_base_url), 'base_url': config.openai_base_url, 'big_model': config.big_model, 'middle_model': config.middle_model, 'small_model': config.small_model, 'reasoning_effort': config.reasoning_effort or 'none', 'reasoning_max_tokens': config.reasoning_max_tokens, 'track_usage': config.track_usage, 'compact_logger': config.compact_logger}, 'performance': self.request_stats, 'errors': {'success_count': success_count, 'total_count': total_count, 'error_types': self.request_stats['error_types'], 'recent_errors': self.request_stats['recent_errors']}, 'models': {'top_models': self.request_stats['top_models'], 'usage_by_type': self.request_stats['usage_by_type'], 'recommendations': [], 'free_savings': self.request_stats['free_savings']}})
    except ImportError:
        pass
```

### Method: `_get_provider_name`
**Logic & Purpose:**
```text
Extract provider name from base URL
```

**Parameters:** `self, base_url`
**Implementation:**
```python
def _get_provider_name(self, base_url: str) -> str:
    """Extract provider name from base URL"""
    if 'openrouter' in base_url.lower():
        return 'OpenRouter'
    elif 'azure' in base_url.lower():
        return 'Azure'
    elif 'anthropic' in base_url.lower():
        return 'Anthropic'
    elif 'openai' in base_url.lower():
        return 'OpenAI'
    else:
        return 'Custom'
```

### Method: `get_stats`
**Logic & Purpose:**
```text
Get current stats snapshot
```

**Parameters:** `self`
**Implementation:**
```python
def get_stats(self) -> Dict[str, Any]:
    """Get current stats snapshot"""
    return self.request_stats.copy()
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/__init__.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/__init__.py`

**Module Overview**: 
```text
Dashboard package for terminal and web-based monitoring.
```

## Global Presets & Variables
- `__all__` = `['terminal_dashboard', 'dashboard_hooks']`

## Dependencies & Imports
src.dashboard.terminal_dashboard.terminal_dashboard, src.dashboard.dashboard_hooks.dashboard_hooks


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/dashboard_manager.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/dashboard_manager.py`

**Module Overview**: 
```text
Dashboard Manager - Orchestrates multiple dashboard modules.
```

## Global Presets & Variables
- `dashboard_manager` = `DashboardManager()`

## Dependencies & Imports
os, time, asyncio, typing.List, typing.Dict, typing.Any, typing.Optional, enum.Enum, dataclasses.dataclass, modules.performance_monitor.PerformanceMonitor, modules.activity_feed.ActivityFeed, modules.routing_visualizer.RoutingVisualizer, modules.analytics_panel.AnalyticsPanel, modules.request_waterfall.RequestWaterfall

## Feature Class: `DisplayMode`
---

## Feature Class: `ModuleType`
---

## Feature Class: `ModuleConfig`
---

## Feature Class: `DashboardManager`
**Description:**
```text
Manages multiple dashboard modules with user-configurable layouts.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.console = Console() if RICH_AVAILABLE else None
    self.modules = {}
    self.active_configs: List[ModuleConfig] = []
    self.live_display: Optional[Live] = None
    self.running = False
    self._init_modules()
    self._load_config()
```

### Method: `_init_modules`
**Logic & Purpose:**
```text
Initialize all dashboard modules.
```

**Parameters:** `self`
**Implementation:**
```python
def _init_modules(self):
    """Initialize all dashboard modules."""
    self.modules = {ModuleType.PERFORMANCE: PerformanceMonitor(), ModuleType.ACTIVITY: ActivityFeed(), ModuleType.ROUTING: RoutingVisualizer(), ModuleType.ANALYTICS: AnalyticsPanel(), ModuleType.WATERFALL: RequestWaterfall()}
```

### Method: `_load_config`
**Logic & Purpose:**
```text
Load dashboard configuration from environment variables.
```

**Parameters:** `self`
**Variables Used:** `dashboard_config, default_modules`
**Implementation:**
```python
def _load_config(self):
    """Load dashboard configuration from environment variables."""
    default_modules = [ModuleConfig(ModuleType.PERFORMANCE, DisplayMode.DENSE, 0), ModuleConfig(ModuleType.ACTIVITY, DisplayMode.SPARSE, 1)]
    dashboard_config = os.environ.get('DASHBOARD_MODULES', 'performance:dense,activity:sparse')
    if dashboard_config:
        self.active_configs = self._parse_config_string(dashboard_config)
    else:
        self.active_configs = default_modules
```

### Method: `_parse_config_string`
**Logic & Purpose:**
```text
Parse dashboard configuration string.
```

**Parameters:** `self, config_str`
**Variables Used:** `configs, module_type, display_mode`
**Implementation:**
```python
def _parse_config_string(self, config_str: str) -> List[ModuleConfig]:
    """Parse dashboard configuration string."""
    configs = []
    for i, module_config in enumerate(config_str.split(',')):
        if ':' in module_config:
            module_name, mode = module_config.strip().split(':')
            try:
                module_type = ModuleType(module_name.lower())
                display_mode = DisplayMode(mode.lower())
                configs.append(ModuleConfig(module_type, display_mode, i))
            except ValueError:
                continue
    return configs
```

### Method: `configure_modules`
**Logic & Purpose:**
```text
Configure active dashboard modules.
```

**Parameters:** `self, configs`
**Implementation:**
```python
def configure_modules(self, configs: List[ModuleConfig]):
    """Configure active dashboard modules."""
    self.active_configs = sorted(configs, key=lambda x: x.position)
```

### Method: `add_module`
**Logic & Purpose:**
```text
Add a module to the dashboard.
```

**Parameters:** `self, module_type, display_mode`
**Variables Used:** `config`
**Implementation:**
```python
def add_module(self, module_type: ModuleType, display_mode: DisplayMode=DisplayMode.DENSE):
    """Add a module to the dashboard."""
    config = ModuleConfig(module_type, display_mode, len(self.active_configs))
    self.active_configs.append(config)
```

### Method: `remove_module`
**Logic & Purpose:**
```text
Remove a module from the dashboard.
```

**Parameters:** `self, module_type`
**Implementation:**
```python
def remove_module(self, module_type: ModuleType):
    """Remove a module from the dashboard."""
    self.active_configs = [c for c in self.active_configs if c.module_type != module_type]
```

### Method: `log_request_data`
**Logic & Purpose:**
```text
Log request data to all active modules.
```

**Parameters:** `self, request_data`
**Variables Used:** `module`
**Implementation:**
```python
def log_request_data(self, request_data: Dict[str, Any]):
    """Log request data to all active modules."""
    for config in self.active_configs:
        if config.enabled and config.module_type in self.modules:
            module = self.modules[config.module_type]
            module.add_request_data(request_data)
```

### Method: `render_dashboard`
**Logic & Purpose:**
```text
Render the complete dashboard.
```

**Parameters:** `self`
**Variables Used:** `section_name, layout, module, content`
**Implementation:**
```python
def render_dashboard(self) -> str:
    """Render the complete dashboard."""
    if not RICH_AVAILABLE:
        return self._render_plain_dashboard()
    if not self.active_configs:
        return 'No dashboard modules configured.'
    layout = self._create_layout()
    for i, config in enumerate(self.active_configs):
        if config.enabled and config.module_type in self.modules:
            module = self.modules[config.module_type]
            content = module.render(config.display_mode)
            section_name = f'module_{i}'
            if hasattr(layout, section_name):
                layout[section_name].update(Panel(content, title=module.get_title()))
    return layout
```

### Method: `_create_layout`
**Logic & Purpose:**
```text
Create Rich layout based on active modules.
```

**Parameters:** `self`
**Variables Used:** `layout, num_modules`
**Implementation:**
```python
def _create_layout(self) -> Layout:
    """Create Rich layout based on active modules."""
    num_modules = len([c for c in self.active_configs if c.enabled])
    if num_modules == 1:
        layout = Layout(name='root')
        layout.add_split(Layout(name='module_0'))
    elif num_modules == 2:
        layout = Layout(name='root')
        layout.split_row(Layout(name='module_0'), Layout(name='module_1'))
    elif num_modules == 3:
        layout = Layout(name='root')
        layout.split_column(Layout(name='module_0'), Layout(name='bottom'))
        layout['bottom'].split_row(Layout(name='module_1'), Layout(name='module_2'))
    elif num_modules == 4:
        layout = Layout(name='root')
        layout.split_column(Layout(name='top'), Layout(name='bottom'))
        layout['top'].split_row(Layout(name='module_0'), Layout(name='module_1'))
        layout['bottom'].split_row(Layout(name='module_2'), Layout(name='module_3'))
    else:
        layout = Layout(name='root')
        for i in range(min(num_modules, 6)):
            layout.add_split(Layout(name=f'module_{i}'))
    return layout
```

### Method: `_render_plain_dashboard`
**Logic & Purpose:**
```text
Render dashboard without Rich formatting.
```

**Parameters:** `self`
**Variables Used:** `lines, module, content`
**Implementation:**
```python
def _render_plain_dashboard(self) -> str:
    """Render dashboard without Rich formatting."""
    lines = []
    lines.append('=' * 80)
    lines.append('API DASHBOARD')
    lines.append('=' * 80)
    for config in self.active_configs:
        if config.enabled and config.module_type in self.modules:
            module = self.modules[config.module_type]
            content = module.render_plain(config.display_mode)
            lines.append(f'\n--- {module.get_title()} ---')
            lines.append(content)
    lines.append('=' * 80)
    return '\n'.join(lines)
```

### Method: `start_live_dashboard`
**Logic & Purpose:**
```text
Start live updating dashboard.
```

**Parameters:** `self, refresh_rate`
**Implementation:**
```python
async def start_live_dashboard(self, refresh_rate: float=1.0):
    """Start live updating dashboard."""
    if not RICH_AVAILABLE:
        print('Rich library not available. Live dashboard disabled.')
        return
    self.running = True
    with Live(self.render_dashboard(), console=self.console, refresh_per_second=refresh_rate) as live:
        self.live_display = live
        while self.running:
            try:
                live.update(self.render_dashboard())
                await asyncio.sleep(1.0 / refresh_rate)
            except KeyboardInterrupt:
                break
    self.running = False
```

### Method: `stop_live_dashboard`
**Logic & Purpose:**
```text
Stop live dashboard.
```

**Parameters:** `self`
**Implementation:**
```python
def stop_live_dashboard(self):
    """Stop live dashboard."""
    self.running = False
```

### Method: `print_dashboard`
**Logic & Purpose:**
```text
Print current dashboard state.
```

**Parameters:** `self`
**Implementation:**
```python
def print_dashboard(self):
    """Print current dashboard state."""
    if RICH_AVAILABLE and self.console:
        self.console.print(self.render_dashboard())
    else:
        print(self._render_plain_dashboard())
```

### Method: `get_available_modules`
**Logic & Purpose:**
```text
Get list of available module types.
```

**Parameters:** `self`
**Implementation:**
```python
def get_available_modules(self) -> List[str]:
    """Get list of available module types."""
    return [module.value for module in ModuleType]
```

### Method: `get_module_info`
**Logic & Purpose:**
```text
Get information about each module.
```

**Parameters:** `self`
**Variables Used:** `info`
**Implementation:**
```python
def get_module_info(self) -> Dict[str, str]:
    """Get information about each module."""
    info = {}
    for module_type, module in self.modules.items():
        info[module_type.value] = module.get_description()
    return info
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/terminal_dashboard.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/terminal_dashboard.py`

**Module Overview**: 
```text
Terminal Dashboard with Edge Modules and Central Waterfall

This replaces the standard proxy terminal output with a Rich-based TUI that shows:
- Modules on edges (top, bottom, left, right)
- Central waterfall area for live request flow
- Moveable module positioning
- Interactive controls
```

## Global Presets & Variables
- `terminal_dashboard` = `TerminalDashboard()`

## Dependencies & Imports
rich.console.Console, rich.layout.Layout, rich.live.Live, rich.panel.Panel, rich.table.Table, rich.text.Text, rich.progress.Progress, rich.progress.SpinnerColumn, rich.progress.BarColumn, rich.progress.TextColumn, datetime.datetime, time, typing.Dict, typing.List, typing.Optional, typing.Any, collections.deque, threading

## Feature Class: `EdgeModule`
**Description:**
```text
Base class for edge modules
```

### Method: `__init__`
**Parameters:** `self, name, position`
**Implementation:**
```python
def __init__(self, name: str, position: str='top'):
    self.name = name
    self.position = position
    self.data = {}
    self.visible = True
    self.size = 'normal'
```

### Method: `update`
**Logic & Purpose:**
```text
Update module data
```

**Parameters:** `self, data`
**Implementation:**
```python
def update(self, data: Dict[str, Any]):
    """Update module data"""
    self.data = data
```

### Method: `render`
**Logic & Purpose:**
```text
Render module as Rich Panel
```

**Parameters:** `self`
**Implementation:**
```python
def render(self) -> Panel:
    """Render module as Rich Panel"""
    raise NotImplementedError
```

---

## Feature Class: `PerformanceEdgeModule`
**Description:**
```text
Performance metrics module
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='top'):
    super().__init__('Performance', position)
```

### Method: `render`
**Parameters:** `self`
**Variables Used:** `total_cost, table, req_count, tokens_sec, avg_lat`
**Implementation:**
```python
def render(self) -> Panel:
    if not self.visible:
        return Panel('', title='', border_style='dim')
    table = Table(show_header=False, box=None, padding=0)
    table.add_column('Label', style='cyan')
    table.add_column('Value', style='white bold')
    req_count = self.data.get('total_requests', 0)
    avg_lat = self.data.get('avg_latency_ms', 0)
    tokens_sec = self.data.get('avg_tokens_per_sec', 0)
    total_cost = self.data.get('total_cost', 0)
    if self.size == 'compact':
        table.add_row('Req', f'{req_count}')
        table.add_row('Lat', f'{avg_lat}ms')
        table.add_row('$/h', f'${total_cost:.2f}')
    elif self.size == 'expanded':
        table.add_row('Requests', f'{req_count:,}')
        table.add_row('Latency', f'{avg_lat:,}ms avg')
        table.add_row('Speed', f'{tokens_sec} tok/s')
        table.add_row('Cost', f'${total_cost:.2f}')
        table.add_row('Success', f"{self.data.get('success_rate', 100):.1f}%")
    else:
        table.add_row('Req', f'{req_count:,}')
        table.add_row('Lat', f'{avg_lat}ms')
        table.add_row('Speed', f'{tokens_sec}t/s')
        table.add_row('Cost', f'${total_cost:.2f}')
    return Panel(table, title=f'[bold cyan]⚡ {self.name}[/]', border_style='cyan')
```

---

## Feature Class: `RoutingEdgeModule`
**Description:**
```text
Routing configuration module
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='right'):
    super().__init__('Routing', position)
```

### Method: `render`
**Parameters:** `self`
**Variables Used:** `big, middle, mode, content, provider, small`
**Implementation:**
```python
def render(self) -> Panel:
    if not self.visible:
        return Panel('', title='', border_style='dim')
    provider = self.data.get('provider', 'Unknown')
    big = self.data.get('big_model', '')[:20]
    middle = self.data.get('middle_model', '')[:20]
    small = self.data.get('small_model', '')[:20]
    mode = 'Passthrough' if self.data.get('passthrough_mode') else 'Proxy'
    content = Text()
    content.append(f'Mode: ', style='dim')
    content.append(f'{mode}\n', style='yellow bold' if mode == 'Passthrough' else 'green bold')
    content.append(f'Provider: ', style='dim')
    content.append(f'{provider}\n\n', style='cyan')
    if self.size != 'compact':
        content.append('Routes:\n', style='bold')
        content.append(f'  O → ', style='dim')
        content.append(f'{big}\n', style='white')
        content.append(f'  M → ', style='dim')
        content.append(f'{middle}\n', style='white')
        content.append(f'  S → ', style='dim')
        content.append(f'{small}', style='white')
    return Panel(content, title=f'[bold yellow]🎯 {self.name}[/]', border_style='yellow')
```

---

## Feature Class: `ActivityEdgeModule`
**Description:**
```text
Activity feed module
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='left'):
    super().__init__('Activity', position)
    self.recent_requests = deque(maxlen=10)
```

### Method: `update`
**Parameters:** `self, data`
**Implementation:**
```python
def update(self, data: Dict[str, Any]):
    super().update(data)
    if 'request' in data:
        self.recent_requests.append(data['request'])
```

### Method: `render`
**Parameters:** `self`
**Variables Used:** `status, icon, model, content, duration, style`
**Implementation:**
```python
def render(self) -> Panel:
    if not self.visible:
        return Panel('', title='', border_style='dim')
    content = Text()
    for req in list(self.recent_requests)[-5:]:
        status = req.get('status', 'pending')
        model = req.get('model', '')[:15]
        duration = req.get('duration_ms', 0)
        if status == 'completed':
            icon = '🟢'
            style = 'green'
        elif status == 'error':
            icon = '🔴'
            style = 'red'
        else:
            icon = '🔵'
            style = 'blue'
        content.append(f'{icon} ', style=style)
        content.append(f'{model}', style='white')
        if duration:
            content.append(f' {duration}ms', style='dim')
        content.append('\n')
    return Panel(content if content.plain else 'No recent activity', title=f'[bold green]📊 {self.name}[/]', border_style='green')
```

---

## Feature Class: `ModelUsageEdgeModule`
**Description:**
```text
Model usage stats module
```

### Method: `__init__`
**Parameters:** `self, position`
**Implementation:**
```python
def __init__(self, position: str='bottom'):
    super().__init__('Model Usage', position)
```

### Method: `render`
**Parameters:** `self`
**Variables Used:** `top_models, cost, count, content, name`
**Implementation:**
```python
def render(self) -> Panel:
    if not self.visible:
        return Panel('', title='', border_style='dim')
    top_models = self.data.get('top_models', [])
    content = Text()
    for i, model in enumerate(top_models[:3], 1):
        name = model.get('name', '')[:20]
        count = model.get('requests', 0)
        cost = model.get('cost', 0)
        content.append(f'#{i} ', style='dim')
        content.append(f'{name}', style='white')
        content.append(f' ({count})', style='cyan')
        if cost == 0:
            content.append(' FREE', style='green bold')
        content.append('\n')
    return Panel(content if content.plain else 'No usage data', title=f'[bold magenta]🤖 {self.name}[/]', border_style='magenta')
```

---

## Feature Class: `WaterfallDisplay`
**Description:**
```text
Central waterfall display for live request flow
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.active_requests = {}
    self.completed_requests = deque(maxlen=20)
    self.lock = threading.Lock()
```

### Method: `add_request`
**Logic & Purpose:**
```text
Add new request to waterfall
```

**Parameters:** `self, request_id, request_data`
**Implementation:**
```python
def add_request(self, request_id: str, request_data: Dict[str, Any]):
    """Add new request to waterfall"""
    with self.lock:
        self.active_requests[request_id] = {**request_data, 'phase': 'parse', 'start_time': time.time(), 'phases': []}
```

### Method: `update_phase`
**Logic & Purpose:**
```text
Update request phase
```

**Parameters:** `self, request_id, phase`
**Variables Used:** `req`
**Implementation:**
```python
def update_phase(self, request_id: str, phase: str):
    """Update request phase"""
    with self.lock:
        if request_id in self.active_requests:
            req = self.active_requests[request_id]
            req['phase'] = phase
            req['phases'].append({'phase': phase, 'timestamp': time.time()})
```

### Method: `complete_request`
**Logic & Purpose:**
```text
Complete a request
```

**Parameters:** `self, request_id, status, data`
**Variables Used:** `req`
**Implementation:**
```python
def complete_request(self, request_id: str, status: str, data: Dict[str, Any]=None):
    """Complete a request"""
    with self.lock:
        if request_id in self.active_requests:
            req = self.active_requests.pop(request_id)
            req['status'] = status
            req['end_time'] = time.time()
            req['duration_ms'] = int((req['end_time'] - req['start_time']) * 1000)
            if data:
                req.update(data)
            self.completed_requests.append(req)
```

### Method: `render`
**Logic & Purpose:**
```text
Render waterfall display
```

**Parameters:** `self`
**Variables Used:** `status, error, current_idx, elapsed, duration, icon, progress_bar, short_id, phase, content, phases, tokens, model, style`
**Implementation:**
```python
def render(self) -> Panel:
    """Render waterfall display"""
    content = Text()
    with self.lock:
        if self.active_requests:
            content.append('ACTIVE REQUESTS\n', style='bold cyan')
            content.append('─' * 60 + '\n', style='dim')
            for req_id, req in list(self.active_requests.items())[:5]:
                short_id = req_id[:8]
                model = req.get('model', '')[:20]
                phase = req.get('phase', 'unknown')
                elapsed = int((time.time() - req['start_time']) * 1000)
                content.append('🔵 ', style='blue')
                content.append(f'{short_id}', style='cyan')
                content.append(f' {model}', style='white')
                content.append(f' {phase}', style='yellow')
                content.append(f' {elapsed}ms', style='dim')
                content.append('\n')
                phases = ['parse', 'route', 'think', 'send', 'wait', 'recv', 'done']
                current_idx = phases.index(phase) if phase in phases else 0
                progress_bar = ''
                for i, p in enumerate(phases):
                    if i < current_idx:
                        progress_bar += '━'
                    elif i == current_idx:
                        progress_bar += '╸'
                    else:
                        progress_bar += '┄'
                content.append(f'  {progress_bar}\n', style='blue')
            content.append('\n')
        if self.completed_requests:
            content.append('COMPLETED REQUESTS\n', style='bold green')
            content.append('─' * 60 + '\n', style='dim')
            for req in list(self.completed_requests)[-10:]:
                short_id = req.get('request_id', '')[:8] if isinstance(req.get('request_id'), str) else 'unknown'
                model = req.get('model', '')[:20]
                status = req.get('status', 'unknown')
                duration = req.get('duration_ms', 0)
                if status == 'completed':
                    icon = '🟢'
                    style = 'green'
                else:
                    icon = '🔴'
                    style = 'red'
                content.append(f'{icon} ', style=style)
                content.append(f'{short_id}', style='cyan')
                content.append(f' {model}', style='white')
                content.append(f' {duration}ms', style='dim')
                if status == 'error':
                    error = req.get('error', '')[:30]
                    content.append(f' ✗ {error}', style='red')
                elif 'tokens' in req:
                    tokens = req.get('tokens', 0)
                    content.append(f' {tokens} tokens', style='cyan')
                content.append('\n')
    if not content.plain:
        content.append('Waiting for requests...\n', style='dim italic')
    return Panel(content, title='[bold white]🌊 REQUEST WATERFALL[/]', border_style='white')
```

---

## Feature Class: `TerminalDashboard`
**Description:**
```text
Main terminal dashboard with edge modules and waterfall
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.console = Console()
    self.layout = Layout()
    self.waterfall = WaterfallDisplay()
    self.modules = {'performance': PerformanceEdgeModule('top'), 'routing': RoutingEdgeModule('right'), 'activity': ActivityEdgeModule('left'), 'models': ModelUsageEdgeModule('bottom')}
    self.live = None
    self.running = False
```

### Method: `setup_layout`
**Logic & Purpose:**
```text
Setup the dashboard layout
```

**Parameters:** `self`
**Implementation:**
```python
def setup_layout(self):
    """Setup the dashboard layout"""
    self.layout.split_column(Layout(name='top', size=7), Layout(name='middle'), Layout(name='bottom', size=6))
    self.layout['middle'].split_row(Layout(name='left', size=25), Layout(name='center'), Layout(name='right', size=25))
```

### Method: `update_module`
**Logic & Purpose:**
```text
Update a module with new data
```

**Parameters:** `self, module_name, data`
**Implementation:**
```python
def update_module(self, module_name: str, data: Dict[str, Any]):
    """Update a module with new data"""
    if module_name in self.modules:
        self.modules[module_name].update(data)
```

### Method: `render`
**Logic & Purpose:**
```text
Render the entire dashboard
```

**Parameters:** `self`
**Implementation:**
```python
def render(self):
    """Render the entire dashboard"""
    self.layout['top'].update(self.modules['performance'].render())
    self.layout['bottom'].update(self.modules['models'].render())
    self.layout['left'].update(self.modules['activity'].render())
    self.layout['right'].update(self.modules['routing'].render())
    self.layout['center'].update(self.waterfall.render())
    return self.layout
```

### Method: `start`
**Logic & Purpose:**
```text
Start the live dashboard
```

**Parameters:** `self`
**Implementation:**
```python
def start(self):
    """Start the live dashboard"""
    self.setup_layout()
    self.running = True
    self.live = Live(self.render(), console=self.console, refresh_per_second=2)
    self.live.start()
```

### Method: `stop`
**Logic & Purpose:**
```text
Stop the dashboard
```

**Parameters:** `self`
**Implementation:**
```python
def stop(self):
    """Stop the dashboard"""
    self.running = False
    if self.live:
        self.live.stop()
```

### Method: `update`
**Logic & Purpose:**
```text
Update the dashboard display
```

**Parameters:** `self`
**Implementation:**
```python
def update(self):
    """Update the dashboard display"""
    if self.live:
        self.live.update(self.render())
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/dashboard/modules/routing_visualizer.py
**Path**: `/home/cheta/code/claude-code-proxy/src/dashboard/modules/routing_visualizer.py`

**Module Overview**: 
```text
Routing Visualizer Module - Model routing flow display.
```

## Dependencies & Imports
base_module.BaseModule, src.dashboard.model_display_utils.format_model_name

## Feature Class: `RoutingVisualizer`
**Description:**
```text
Model routing visualization module.
```

### Method: `get_title`
**Parameters:** `self`
**Implementation:**
```python
def get_title(self) -> str:
    return 'Model Routing'
```

### Method: `get_description`
**Parameters:** `self`
**Implementation:**
```python
def get_description(self) -> str:
    return 'Visual display of model routing decisions and flow'
```

### Method: `render_dense`
**Logic & Purpose:**
```text
Render detailed routing visualization.
```

**Parameters:** `self`
**Variables Used:** `output_tokens, routed, input_tokens_actual, input_tokens, recent, cost, complete_req, text, tok_s, duration_ms, efficiency, context_limit, usage, original, thinking_tokens, start_req`
**Implementation:**
```python
def render_dense(self) -> str:
    """Render detailed routing visualization."""
    recent = self.get_recent_requests(1)
    if not recent:
        return 'No routing data available'
    start_req = None
    complete_req = None
    for req in reversed(recent):
        if req.get('type') == 'start':
            start_req = req
            break
    for req in reversed(recent):
        if req.get('type') == 'complete' and req.get('request_id') == start_req.get('request_id'):
            complete_req = req
            break
    if not start_req:
        return 'No routing information'
    if not RICH_AVAILABLE:
        return self._render_dense_plain(start_req, complete_req)
    text = Text()
    original = start_req.get('original_model', 'unknown')
    routed = start_req.get('routed_model', 'unknown')
    text.append(f'[{self._format_model_display(original)}]', style='yellow')
    text.append(' ──routing──> ', style='dim')
    text.append(f'[{self._format_model_display(routed)}]', style='green')
    text.append('\n')
    context_limit = start_req.get('context_limit', 0)
    input_tokens = start_req.get('input_tokens', 0)
    if context_limit > 0:
        text.append(f'     ↓ {self.format_tokens(input_tokens)} ctx', style='cyan')
    if complete_req:
        usage = complete_req.get('usage', {})
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        text.append(f'                  ↓ {self.format_tokens(output_tokens)} out', style='blue')
        text.append('\n')
        thinking_tokens = self._extract_thinking_tokens(usage)
        if thinking_tokens > 0:
            text.append(f'🧠 Thinking: {self.format_tokens(thinking_tokens)} tokens', style='magenta')
        duration_ms = complete_req.get('duration_ms', 0)
        if duration_ms > 0 and output_tokens > 0:
            tok_s = output_tokens / (duration_ms / 1000)
            text.append(f'      ⚡ Speed: {tok_s:.0f} tok/s', style='green')
        text.append('\n')
        input_tokens_actual = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        cost = self._estimate_cost(input_tokens_actual, output_tokens, thinking_tokens, routed)
        text.append(f'💰 Cost: {self.format_cost(cost)}', style='yellow')
        if context_limit > 0 and input_tokens_actual > 0:
            efficiency = min(100, output_tokens / input_tokens_actual * 100)
            text.append(f'            📊 Efficiency: {efficiency:.0f}%', style='cyan')
    return text
```

### Method: `render_sparse`
**Logic & Purpose:**
```text
Render compact routing info.
```

**Parameters:** `self`
**Variables Used:** `output_tokens, routed, input_tokens, recent, cost, complete_req, tok_s, duration_ms, usage, original, thinking_tokens, parts, start_req`
**Implementation:**
```python
def render_sparse(self) -> str:
    """Render compact routing info."""
    recent = self.get_recent_requests(1)
    if not recent:
        return 'No routing data'
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
        return 'No routing info'
    original = self._format_model_name(start_req.get('original_model', 'unknown'))
    routed = self._format_model_name(start_req.get('routed_model', 'unknown'))
    parts = [f'{original}→{routed}']
    input_tokens = start_req.get('input_tokens', 0)
    if input_tokens > 0:
        parts.append(f'{self.format_tokens(input_tokens)}')
    if complete_req:
        usage = complete_req.get('usage', {})
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        thinking_tokens = self._extract_thinking_tokens(usage)
        duration_ms = complete_req.get('duration_ms', 0)
        if output_tokens > 0:
            parts.append(f'→{self.format_tokens(output_tokens)}')
        if thinking_tokens > 0:
            parts.append(f'🧠{self.format_tokens(thinking_tokens)}')
        if duration_ms > 0 and output_tokens > 0:
            tok_s = output_tokens / (duration_ms / 1000)
            parts.append(f'⚡{tok_s:.0f}t/s')
        cost = self._estimate_cost(usage.get('input_tokens', 0), output_tokens, thinking_tokens, routed)
        parts.append(f'💰{self.format_cost(cost)}')
    return ' | '.join(parts)
```

### Method: `_render_dense_plain`
**Logic & Purpose:**
```text
Plain text version.
```

**Parameters:** `self, start_req, complete_req`
**Variables Used:** `output_tokens, routed, lines, usage, original, thinking_tokens`
**Implementation:**
```python
def _render_dense_plain(self, start_req, complete_req):
    """Plain text version."""
    original = start_req.get('original_model', 'unknown')
    routed = start_req.get('routed_model', 'unknown')
    lines = [f'Routing: {original} -> {routed}', f"Context: {self.format_tokens(start_req.get('input_tokens', 0))}"]
    if complete_req:
        usage = complete_req.get('usage', {})
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        lines.append(f'Output: {self.format_tokens(output_tokens)}')
        thinking_tokens = self._extract_thinking_tokens(usage)
        if thinking_tokens > 0:
            lines.append(f'Thinking: {self.format_tokens(thinking_tokens)}')
    return '\n'.join(lines)
```

### Method: `_format_model_display`
**Logic & Purpose:**
```text
Format model name for display.
```

**Parameters:** `self, model_name`
**Implementation:**
```python
def _format_model_display(self, model_name: str) -> str:
    """Format model name for display."""
    if 'claude' in model_name.lower():
        if '3.5' in model_name and 'sonnet' in model_name.lower():
            return 'Claude 3.5 Sonnet'
        elif '3' in model_name and 'opus' in model_name.lower():
            return 'Claude 3 Opus'
        elif '3' in model_name and 'haiku' in model_name.lower():
            return 'Claude 3 Haiku'
        return 'Claude'
    elif 'gpt-4o' in model_name.lower():
        if 'mini' in model_name.lower():
            return 'GPT-4o Mini'
        return 'GPT-4o'
    elif 'o1' in model_name.lower():
        if 'preview' in model_name.lower():
            return 'o1-preview'
        elif 'mini' in model_name.lower():
            return 'o1-mini'
        return 'o1'
    return model_name.split('/')[-1] if '/' in model_name else model_name
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


