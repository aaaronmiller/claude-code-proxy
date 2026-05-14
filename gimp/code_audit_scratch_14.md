# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/token_utils.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/token_utils.py`

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
    request_size: Size of request payload in characters
    response_size: Size of response body in characters
    request_body: Optional actual request body for more accurate token estimation

Returns:
    dict with prompt_tokens, completion_tokens, total_tokens
```

**Parameters:** `request_size, response_size, request_body`
**Variables Used:** `prompt_tokens, completion_tokens`
**Implementation:**
```python
def track_api_call(request_size: int, response_size: int, request_body: str=None) -> dict:
    """
    Create a token usage record for an API call.

    Args:
        request_size: Size of request payload in characters
        response_size: Size of response body in characters
        request_body: Optional actual request body for more accurate token estimation

    Returns:
        dict with prompt_tokens, completion_tokens, total_tokens
    """
    if request_body:
        prompt_tokens = estimate_prompt_tokens(request_body)
    else:
        prompt_tokens = estimate_tokens('a' * request_size)
    completion_tokens = estimate_response_tokens('a' * response_size)
    return {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'total_tokens': prompt_tokens + completion_tokens}
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/leaderboard.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/leaderboard.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/cost.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/openrouter_model_scout/cost.py`

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


# File Audit: /home/cheta/code/claude-code-proxy/src/services/conversion/request_converter.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/conversion/request_converter.py`

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `TOOL_OUTPUT_MAX_CHARS` = `int(os.getenv('TOOL_OUTPUT_MAX_CHARS', '50000'))`
- `TOOL_OUTPUT_TRUNCATION_ENABLED` = `os.getenv('TOOL_OUTPUT_TRUNCATION', 'false').lower() == 'true'`

## Dependencies & Imports
json, os, typing.Dict, typing.Any, typing.List, typing.Tuple, logging, src.services.models.model_parser.parse_model_id, src.services.prompts.templates.apply_template, src.models.claude.ClaudeMessagesRequest, src.models.claude.ClaudeMessage, src.core.config.config, src.models.reasoning.OpenAIReasoningConfig, src.models.reasoning.AnthropicThinkingConfig, src.models.reasoning.GeminiThinkingConfig, src.services.models.model_filter.model_filter, src.core.constants.Constants, src.services.tools.tool_mapper.sanitize_tool_declarations, src.services.conversion.tool_behavior_cache.get_tool_argument_style

## Feature Function: `truncate_tool_output`
**Logic & Purpose:**
```text
Truncate large tool outputs for token efficiency.

Inspired by Lynkr's truncateToolOutput() function.
Large outputs from tools like file reads or command execution
can waste tokens and confuse the model.

Args:
    content: The tool output content
    max_chars: Maximum characters allowed (defaults to TOOL_OUTPUT_MAX_CHARS)

Returns:
    Tuple of (possibly truncated content, was_truncated boolean)
```

**Parameters:** `content, max_chars`
**Variables Used:** `original_len, truncated, max_chars, truncated_chars`
**Implementation:**
```python
def truncate_tool_output(content: str, max_chars: int=None) -> Tuple[str, bool]:
    """
    Truncate large tool outputs for token efficiency.

    Inspired by Lynkr's truncateToolOutput() function.
    Large outputs from tools like file reads or command execution
    can waste tokens and confuse the model.

    Args:
        content: The tool output content
        max_chars: Maximum characters allowed (defaults to TOOL_OUTPUT_MAX_CHARS)

    Returns:
        Tuple of (possibly truncated content, was_truncated boolean)
    """
    if max_chars is None:
        max_chars = TOOL_OUTPUT_MAX_CHARS
    if not TOOL_OUTPUT_TRUNCATION_ENABLED:
        return (content, False)
    if not content or len(content) <= max_chars:
        return (content, False)
    original_len = len(content)
    truncated_chars = original_len - max_chars
    truncated = content[:max_chars]
    truncated += f'\n\n... [OUTPUT TRUNCATED: {truncated_chars:,} chars removed, {original_len:,} total]'
    logger.info(f'Tool output truncated: {original_len:,} -> {max_chars:,} chars (-{truncated_chars:,})')
    return (truncated, True)
```

---

## Feature Function: `validate_tool_message_sequence`
**Logic & Purpose:**
```text
Validate that tool role messages have matching tool_calls in preceding assistant messages.

Inspired by Lynkr's implementation, this prevents errors from orphaned tool messages
that can occur when conversation history is truncated or corrupted.

Args:
    messages: List of OpenAI-format messages
    remove_orphans: If True, remove orphaned tool messages. If False, just log warnings.

Returns:
    Validated (and optionally cleaned) message list
```

**Parameters:** `messages, remove_orphans`
**Variables Used:** `orphan_count, tool_calls, validated, tool_call_id, found_match, prev_msg, role`
**Implementation:**
```python
def validate_tool_message_sequence(messages: List[Dict[str, Any]], remove_orphans: bool=False) -> List[Dict[str, Any]]:
    """
    Validate that tool role messages have matching tool_calls in preceding assistant messages.

    Inspired by Lynkr's implementation, this prevents errors from orphaned tool messages
    that can occur when conversation history is truncated or corrupted.

    Args:
        messages: List of OpenAI-format messages
        remove_orphans: If True, remove orphaned tool messages. If False, just log warnings.

    Returns:
        Validated (and optionally cleaned) message list
    """
    if not messages:
        return messages
    validated = []
    orphan_count = 0
    for i, msg in enumerate(messages):
        role = msg.get('role', '')
        if role == 'tool':
            tool_call_id = msg.get('tool_call_id')
            found_match = False
            for j in range(len(validated) - 1, -1, -1):
                prev_msg = validated[j]
                if prev_msg.get('role') == 'assistant':
                    tool_calls = prev_msg.get('tool_calls', [])
                    if any((tc.get('id') == tool_call_id for tc in tool_calls)):
                        found_match = True
                        break
                if prev_msg.get('role') == 'user':
                    break
            if not found_match:
                orphan_count += 1
                logger.warning(f'Orphaned tool message detected at index {i}: tool_call_id={tool_call_id}, no matching assistant tool_calls found')
        validated.append(msg)
    if orphan_count > 0:
        logger.info(f'Tool message validation complete: {orphan_count} orphan(s) kept for conversation continuity (Issue 18)')
    return validated
```

---

## Feature Function: `_apply_reasoning_config`
**Logic & Purpose:**
```text
Apply reasoning configuration to OpenAI request based on provider type.

Args:
    openai_request: OpenAI request dictionary to modify
    reasoning_config: ReasoningConfig object (OpenAI/Anthropic/Gemini)
    model_name: Model name for logging
    model_manager: ModelManager instance for config access
```

**Parameters:** `openai_request, reasoning_config, model_name, model_manager`
**Variables Used:** `is_using_openrouter, log_msg, reasoning_params`
**Implementation:**
```python
def _apply_reasoning_config(openai_request: Dict[str, Any], reasoning_config: Any, model_name: str, model_manager) -> None:
    """
    Apply reasoning configuration to OpenAI request based on provider type.

    Args:
        openai_request: OpenAI request dictionary to modify
        reasoning_config: ReasoningConfig object (OpenAI/Anthropic/Gemini)
        model_name: Model name for logging
        model_manager: ModelManager instance for config access
    """
    is_using_openrouter = 'openrouter' in model_manager.config.openai_base_url.lower()
    if isinstance(reasoning_config, OpenAIReasoningConfig):
        if is_using_openrouter:
            if 'extra_body' not in openai_request:
                openai_request['extra_body'] = {}
            reasoning_params = {}
            if reasoning_config.effort:
                reasoning_params['effort'] = reasoning_config.effort
            if reasoning_config.max_tokens:
                reasoning_params['max_tokens'] = reasoning_config.max_tokens
            reasoning_params['exclude'] = reasoning_config.exclude
            openai_request['extra_body']['reasoning'] = reasoning_params
            log_msg = f'Applied OpenAI reasoning config for {model_name}: '
            if reasoning_config.effort:
                log_msg += f'effort={reasoning_config.effort}'
            if reasoning_config.max_tokens:
                log_msg += f' max_tokens={reasoning_config.max_tokens}'
            log_msg += f' exclude={reasoning_config.exclude}'
            logger.info(log_msg)
        else:
            if 'extra_body' not in openai_request:
                openai_request['extra_body'] = {}
            reasoning_params = {}
            if reasoning_config.effort:
                reasoning_params['effort'] = reasoning_config.effort
            if reasoning_config.max_tokens:
                reasoning_params['max_tokens'] = reasoning_config.max_tokens
            openai_request['extra_body']['reasoning'] = reasoning_params
            log_msg = f'Applied OpenAI reasoning config for {model_name}: '
            if reasoning_config.effort:
                log_msg += f'effort={reasoning_config.effort}'
            if reasoning_config.max_tokens:
                log_msg += f'max_tokens={reasoning_config.max_tokens}'
            logger.info(log_msg)
    elif isinstance(reasoning_config, AnthropicThinkingConfig):
        if is_using_openrouter:
            if 'extra_body' not in openai_request:
                openai_request['extra_body'] = {}
            openai_request['extra_body']['thinking'] = {'type': reasoning_config.type, 'budget': reasoning_config.budget}
        else:
            openai_request['thinking'] = {'type': reasoning_config.type, 'budget': reasoning_config.budget}
        logger.info(f'Applied Anthropic thinking config for {model_name}: budget={reasoning_config.budget}')
    elif isinstance(reasoning_config, GeminiThinkingConfig):
        if 'generation_config' not in openai_request:
            if 'extra_body' not in openai_request:
                openai_request['extra_body'] = {}
            openai_request['extra_body']['generation_config'] = {}
        if 'extra_body' in openai_request and 'generation_config' in openai_request['extra_body']:
            openai_request['extra_body']['generation_config']['thinking_config'] = {'budget': reasoning_config.budget}
        else:
            if 'generation_config' not in openai_request:
                openai_request['generation_config'] = {}
            openai_request['generation_config']['thinking_config'] = {'budget': reasoning_config.budget}
        logger.info(f'Applied Gemini thinking config for {model_name}: budget={reasoning_config.budget}')
```

---

## Feature Function: `convert_claude_to_openai`
**Logic & Purpose:**
```text
Convert Claude API request format to OpenAI format with enhanced validation.

Args:
    claude_request: The Claude API request
    model_manager: Model manager instance
    target_provider: Target provider name (e.g., 'vibeproxy', 'openrouter', 'gemini')
                    Used to conditionally apply provider-specific transformations
```

**Parameters:** `claude_request, model_manager, target_provider`
**Variables Used:** `model_output_limit, next_msg, msg, openai_tools, tool_results, model_size, system_text, i, effective_max, openai_messages, role, openai_request, token_limit, choice_type, tool_calls, openai_message, is_newer_model, text_parts, content, input_schema`
**Implementation:**
```python
def convert_claude_to_openai(claude_request: ClaudeMessagesRequest, model_manager, target_provider: str=None) -> Dict[str, Any]:
    """Convert Claude API request format to OpenAI format with enhanced validation.

    Args:
        claude_request: The Claude API request
        model_manager: Model manager instance
        target_provider: Target provider name (e.g., 'vibeproxy', 'openrouter', 'gemini')
                        Used to conditionally apply provider-specific transformations
    """
    if not claude_request:
        raise ValueError('Claude request cannot be None')
    if not claude_request.messages:
        raise ValueError('Claude request must contain at least one message')
    if not isinstance(claude_request.messages, list):
        raise ValueError('Claude request messages must be a list')
    if claude_request.max_tokens < 1:
        raise ValueError(f'max_tokens must be at least 1, got {claude_request.max_tokens}')
    openai_model, reasoning_config = model_manager.parse_and_map_model(claude_request.model)
    model_filter.track_model_usage(openai_model)
    openai_messages = []
    if claude_request.system:
        system_text = ''
        if isinstance(claude_request.system, str):
            system_text = claude_request.system
        elif isinstance(claude_request.system, list):
            text_parts = []
            for block in claude_request.system:
                if hasattr(block, 'type') and block.type == Constants.CONTENT_TEXT:
                    text_parts.append(block.text)
                elif isinstance(block, dict) and block.get('type') == Constants.CONTENT_TEXT:
                    text_parts.append(block.get('text', ''))
            system_text = '\n\n'.join(text_parts)
        if 'You are Claude Code' in system_text or 'claude-code' in system_text.lower() or "Anthropic's official CLI" in system_text:
            system_text += "\n\nIMPORTANT RULE: Never use the Bash/Repl tools to execute 'echo' commands or shell scripts solely to output insights, thoughts, or explanations. Always output your insights directly as inline text."
        if system_text.strip():
            openai_messages.append({'role': Constants.ROLE_SYSTEM, 'content': system_text.strip()})
    i = 0
    while i < len(claude_request.messages):
        msg = claude_request.messages[i]
        if msg.role == Constants.ROLE_USER:
            openai_message = convert_claude_user_message(msg)
            openai_messages.append(openai_message)
        elif msg.role == Constants.ROLE_ASSISTANT:
            openai_message = convert_claude_assistant_message(msg, target_provider, openai_model)
            openai_messages.append(openai_message)
            if i + 1 < len(claude_request.messages):
                next_msg = claude_request.messages[i + 1]
                if next_msg.role == Constants.ROLE_USER and isinstance(next_msg.content, list) and any((block.type == Constants.CONTENT_TOOL_RESULT for block in next_msg.content if hasattr(block, 'type'))):
                    i += 1
                    tool_results = convert_claude_tool_results(next_msg)
                    openai_messages.extend(tool_results)
        i += 1
    openai_messages = validate_tool_message_sequence(openai_messages, remove_orphans=False)
    is_newer_model = model_manager.is_newer_openai_model(openai_model)
    from src.services.usage.model_limits import get_output_limit
    model_output_limit = get_output_limit(openai_model)
    if config.max_tokens_limit:
        effective_max = min(config.max_tokens_limit, model_output_limit)
    else:
        effective_max = model_output_limit
    if config.min_tokens_limit:
        token_limit = min(max(claude_request.max_tokens, config.min_tokens_limit), effective_max)
    else:
        token_limit = claude_request.max_tokens
    if token_limit < claude_request.max_tokens:
        logger.debug(f'Capped max_tokens {claude_request.max_tokens} → {token_limit} (model {openai_model} output limit: {model_output_limit})')
    openai_request = {'model': openai_model, 'messages': openai_messages, 'stream': claude_request.stream}
    logger.debug(f'OUTGOING REQUEST: {len(openai_messages)} messages')
    if logger.isEnabledFor(logging.DEBUG):
        for idx, msg in enumerate(openai_messages):
            role = msg.get('role', '?')
            content = str(msg.get('content', ''))[:80]
            tool_calls = 'YES' if msg.get('tool_calls') else 'NO'
            if content.strip() and '(no content)' not in content.lower():
                logger.debug(f'  MSG[{idx}] role={role}, tool_calls={tool_calls}, content={content}...')
            else:
                logger.debug(f'  MSG[{idx}] role={role}, tool_calls={tool_calls}, content=[empty/placeholder]')
    if is_newer_model:
        openai_request['max_completion_tokens'] = token_limit
        openai_request['temperature'] = 1
        logger.debug(f'Converted request (newer model): model={openai_model}, messages={len(openai_messages)}, max_completion_tokens={token_limit}, temperature=1')
    else:
        openai_request['max_tokens'] = token_limit
        openai_request['temperature'] = claude_request.temperature
        logger.debug(f'Converted request: model={openai_model}, messages={len(openai_messages)}, max_tokens={token_limit}, temp={claude_request.temperature}')
    if claude_request.stop_sequences:
        openai_request['stop'] = claude_request.stop_sequences
    if claude_request.top_p is not None:
        openai_request['top_p'] = claude_request.top_p
    if claude_request.tools:
        openai_tools = []
        logger.debug(f'Converting {len(claude_request.tools)} tools to OpenAI format')
        for tool in claude_request.tools:
            if tool.name and tool.name.strip():
                input_schema = tool.input_schema.copy() if tool.input_schema else {}
                if 'defer_loading' in input_schema:
                    del input_schema['defer_loading']
                openai_tools.append({'type': Constants.TOOL_FUNCTION, 'function': {'name': tool.name, 'description': tool.description or '', 'parameters': input_schema}})
        if openai_tools:
            openai_tools = sanitize_tool_declarations(openai_tools)
            openai_request['tools'] = openai_tools
            logger.debug(f"Added {len(openai_tools)} tools to OpenAI request: {[t['function']['name'] for t in openai_tools]}")
    if claude_request.tool_choice:
        choice_type = claude_request.tool_choice.get('type')
        if choice_type == 'auto':
            openai_request['tool_choice'] = 'auto'
        elif choice_type == 'any':
            openai_request['tool_choice'] = 'required'
        elif choice_type == 'none':
            openai_request['tool_choice'] = 'none'
        elif choice_type == 'tool' and 'name' in claude_request.tool_choice:
            openai_request['tool_choice'] = {'type': Constants.TOOL_FUNCTION, Constants.TOOL_FUNCTION: {'name': claude_request.tool_choice['name']}}
        else:
            openai_request['tool_choice'] = 'auto'
        if claude_request.tool_choice.get('disable_parallel_tool_use'):
            openai_request['parallel_tool_calls'] = False
    if reasoning_config:
        _apply_reasoning_config(openai_request, reasoning_config, openai_model, model_manager)
    if model_manager.config.verbosity and _model_supports_reasoning(openai_model, model_manager):
        logger.debug(f'Verbosity configured but skipped for {openai_model} to avoid compatibility issues')
    from src.services.prompts.system_prompt_loader import inject_system_prompt
    model_size = _get_model_size_from_model_id(openai_model)
    openai_messages = inject_system_prompt(openai_messages, model_size, model_manager.config)
    openai_request['messages'] = openai_messages
    return openai_request
```

---

## Feature Function: `_model_supports_reasoning`
**Logic & Purpose:**
```text
Check if a model supports reasoning parameters.

Models known to support reasoning_effort and related parameters:
- OpenAI: GPT-5 family, o1 series, o3 series
- Anthropic: Claude 3.7, Claude 4.x, Claude 4.1 with reasoning
- xAI: Grok models with reasoning
- Qwen: Qwen3, Qwen-2.5 thinking variants
- DeepSeek: DeepSeek V3/V3.1, DeepSeek R1 variants
- MiniMax: M2 thinking models
- Kimi: K2 thinking models
```

**Parameters:** `model_id, model_manager`
**Variables Used:** `model_lower`
**Implementation:**
```python
def _model_supports_reasoning(model_id: str, model_manager=None) -> bool:
    """
    Check if a model supports reasoning parameters.

    Models known to support reasoning_effort and related parameters:
    - OpenAI: GPT-5 family, o1 series, o3 series
    - Anthropic: Claude 3.7, Claude 4.x, Claude 4.1 with reasoning
    - xAI: Grok models with reasoning
    - Qwen: Qwen3, Qwen-2.5 thinking variants
    - DeepSeek: DeepSeek V3/V3.1, DeepSeek R1 variants
    - MiniMax: M2 thinking models
    - Kimi: K2 thinking models
    """
    model_lower = model_id.lower()
    if any((keyword in model_lower for keyword in ['openai/gpt-5', 'gpt-5', 'openai/o1', 'o1', 'openai/o3', 'o3'])):
        return True
    if any((pattern in model_lower for pattern in ['anthropic/claude-3.7', 'anthropic/claude-4', 'anthropic/claude-4.1', 'anthropic/claude-sonnet', 'anthropic/claude-opus', 'anthropic/claude-haiku'])):
        return True
    if 'xai/' in model_lower and any((keyword in model_lower for keyword in ['reason', 'thinking'])):
        return True
    if any((keyword in model_lower for keyword in ['qwen3', 'qwen2.5-thinking', 'qwen-2.5-thinking', 'qwen-thinking', 'qwen-reasoning'])):
        return True
    if any((keyword in model_lower for keyword in ['deepseek-v3', 'deepseek-v3.1', 'deepseek-r1', 'deepseek-reasoning'])):
        return True
    if any((keyword in model_lower for keyword in ['minimax/m2', 'minimax-thinking', 'kimi-k2', 'kimi-thinking'])):
        return True
    if any((keyword in model_lower for keyword in ['thinking', '-reasoning', '-r1', '-deepseek-r1', 'cognition', 'chain-of-thought'])):
        return True
    if model_manager and hasattr(model_manager, 'models_data'):
        for category in ['reasoning_models', 'verbosity_models']:
            if category in model_manager.models_data:
                for model in model_manager.models_data[category]:
                    if model.get('id', '').lower() == model_lower:
                        return True
    return False
```

---

## Feature Function: `_get_model_size_from_model_id`
**Logic & Purpose:**
```text
Determine model size from model ID.

Args:
    model_id: The OpenAI model ID

Returns:
    "big", "middle", or "small"
```

**Parameters:** `model_id`
**Variables Used:** `model_lower`
**Implementation:**
```python
def _get_model_size_from_model_id(model_id: str) -> str:
    """
    Determine model size from model ID.

    Args:
        model_id: The OpenAI model ID

    Returns:
        "big", "middle", or "small"
    """
    model_lower = model_id.lower()
    if model_lower == config.big_model.lower():
        return 'big'
    elif model_lower == config.middle_model.lower():
        return 'middle'
    elif model_lower == config.small_model.lower():
        return 'small'
    if any((keyword in model_lower for keyword in ['opus', 'gpt-5', 'gpt-4.1'])):
        return 'big'
    elif any((keyword in model_lower for keyword in ['sonnet', 'gpt-4'])):
        return 'middle'
    elif any((keyword in model_lower for keyword in ['haiku', 'mini', 'gpt-4o-mini'])):
        return 'small'
    return 'middle'
```

---

## Feature Function: `convert_claude_user_message`
**Logic & Purpose:**
```text
Convert Claude user message to OpenAI format.
```

**Parameters:** `msg`
**Variables Used:** `openai_content`
**Implementation:**
```python
def convert_claude_user_message(msg: ClaudeMessage) -> Dict[str, Any]:
    """Convert Claude user message to OpenAI format."""
    if msg.content is None:
        return {'role': Constants.ROLE_USER, 'content': ''}
    if isinstance(msg.content, str):
        return {'role': Constants.ROLE_USER, 'content': msg.content}
    openai_content = []
    for block in msg.content:
        if block.type == Constants.CONTENT_TEXT:
            openai_content.append({'type': 'text', 'text': block.text})
        elif block.type == Constants.CONTENT_IMAGE:
            if isinstance(block.source, dict) and block.source.get('type') == 'base64' and ('media_type' in block.source) and ('data' in block.source):
                openai_content.append({'type': 'image_url', 'image_url': {'url': f"data:{block.source['media_type']};base64,{block.source['data']}"}})
    if len(openai_content) == 1 and openai_content[0]['type'] == 'text':
        return {'role': Constants.ROLE_USER, 'content': openai_content[0]['text']}
    else:
        return {'role': Constants.ROLE_USER, 'content': openai_content}
```

---

## Feature Function: `convert_claude_assistant_message`
**Logic & Purpose:**
```text
Convert Claude assistant message to OpenAI format.

Args:
    msg: Claude message object
    target_provider: Target provider name (e.g., 'vibeproxy', 'gemini', 'openrouter')
                    Used to conditionally apply provider-specific transformations
    target_model: Target model name (provider-specific, optional)
```

**Parameters:** `msg, target_provider, target_model`
**Variables Used:** `tool_name, target_provider_lower, tool_calls, text_parts, arguments, openai_message, observed_style, should_reverse_rename`
**Implementation:**
```python
def convert_claude_assistant_message(msg: ClaudeMessage, target_provider: str=None, target_model: str=None) -> Dict[str, Any]:
    """
    Convert Claude assistant message to OpenAI format.

    Args:
        msg: Claude message object
        target_provider: Target provider name (e.g., 'vibeproxy', 'gemini', 'openrouter')
                        Used to conditionally apply provider-specific transformations
        target_model: Target model name (provider-specific, optional)
    """
    text_parts = []
    tool_calls = []
    if msg.content is None:
        return {'role': Constants.ROLE_ASSISTANT, 'content': None}
    if isinstance(msg.content, str):
        return {'role': Constants.ROLE_ASSISTANT, 'content': msg.content}
    for block in msg.content:
        if block.type == Constants.CONTENT_TEXT:
            text_parts.append(block.text)
        elif block.type == Constants.CONTENT_TOOL_USE:
            tool_name = block.name
            arguments = block.input
            target_provider_lower = target_provider.lower() if target_provider else ''
            observed_style = get_tool_argument_style(target_provider_lower, tool_name)
            should_reverse_rename = observed_style == 'prompt'
            if target_provider:
                logger.debug(f'Tool call: target_provider={target_provider}, should_reverse_rename={should_reverse_rename}')
            if should_reverse_rename and tool_name.lower() in ['bash', 'repl'] and isinstance(arguments, dict):
                arguments = arguments.copy()
                if 'command' in arguments and 'prompt' not in arguments:
                    arguments['prompt'] = arguments.pop('command')
                    logger.debug(f"Reverse renamed Bash 'command' → 'prompt' for {target_provider} (Issue 18 fix)")
            tool_calls.append({'id': block.id, 'type': Constants.TOOL_FUNCTION, Constants.TOOL_FUNCTION: {'name': tool_name, 'arguments': json.dumps(arguments, ensure_ascii=False)}})
        elif block.type == 'thinking' or block.type == 'redacted_thinking':
            continue
    openai_message = {'role': Constants.ROLE_ASSISTANT}
    if text_parts:
        openai_message['content'] = ''.join(text_parts)
    elif tool_calls:
        openai_message['content'] = None
    else:
        openai_message['content'] = '(thinking)'
    if tool_calls:
        openai_message['tool_calls'] = tool_calls
    return openai_message
```

---

## Feature Function: `convert_claude_tool_results`
**Logic & Purpose:**
```text
Convert Claude tool results to OpenAI format with deduplication.
```

**Parameters:** `msg`
**Variables Used:** `content, seen_tool_ids, tool_id, tool_messages`
**Implementation:**
```python
def convert_claude_tool_results(msg: ClaudeMessage) -> List[Dict[str, Any]]:
    """Convert Claude tool results to OpenAI format with deduplication."""
    tool_messages = []
    seen_tool_ids = set()
    if isinstance(msg.content, list):
        for block in msg.content:
            if block.type == Constants.CONTENT_TOOL_RESULT:
                tool_id = block.tool_use_id
                if tool_id in seen_tool_ids:
                    logger.debug(f'DEDUP: Skipping duplicate tool_result for tool_use_id={tool_id}')
                    continue
                seen_tool_ids.add(tool_id)
                content = parse_tool_result_content(block.content)
                tool_messages.append({'role': Constants.ROLE_TOOL, 'tool_call_id': tool_id, 'content': content})
    return tool_messages
```

---

## Feature Function: `parse_tool_result_content`
**Logic & Purpose:**
```text
Parse and normalize tool result content into a string format.

Applies truncation for large outputs to save tokens.
```

**Parameters:** `content`
**Variables Used:** `result_parts, result`
**Implementation:**
```python
def parse_tool_result_content(content):
    """Parse and normalize tool result content into a string format.

    Applies truncation for large outputs to save tokens.
    """
    if content is None:
        return 'No content provided'
    result = None
    if isinstance(content, str):
        result = content
    elif isinstance(content, list):
        result_parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == Constants.CONTENT_TEXT:
                result_parts.append(item.get('text', ''))
            elif isinstance(item, str):
                result_parts.append(item)
            elif isinstance(item, dict):
                if 'text' in item:
                    result_parts.append(item.get('text', ''))
                else:
                    try:
                        result_parts.append(json.dumps(item, ensure_ascii=False))
                    except (TypeError, ValueError):
                        result_parts.append(str(item))
        result = '\n'.join(result_parts).strip()
    elif isinstance(content, dict):
        if content.get('type') == Constants.CONTENT_TEXT:
            result = content.get('text', '')
        else:
            try:
                result = json.dumps(content, ensure_ascii=False)
            except (TypeError, ValueError):
                result = str(content)
    else:
        try:
            result = str(content)
        except Exception:
            result = 'Unparseable content'
    if result:
        result, was_truncated = truncate_tool_output(result)
    return result
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/conversion/tool_behavior_cache.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/conversion/tool_behavior_cache.py`

## Global Presets & Variables
- `_lock` = `threading.Lock()`

## Dependencies & Imports
threading, typing.Dict, typing.Optional, typing.Tuple

## Feature Function: `record_tool_argument_style`
**Logic & Purpose:**
```text
Record observed argument style for a tool (prompt vs command).
```

**Parameters:** `provider, tool_name, arguments`
**Variables Used:** `provider_key, tool_key, style`
**Implementation:**
```python
def record_tool_argument_style(provider: Optional[str], tool_name: Optional[str], arguments: object) -> None:
    """Record observed argument style for a tool (prompt vs command)."""
    if not provider or not tool_name or (not isinstance(arguments, dict)):
        return
    provider_key = provider.lower()
    tool_key = tool_name.lower()
    style = None
    if 'prompt' in arguments and 'command' not in arguments:
        style = 'prompt'
    elif 'command' in arguments and 'prompt' not in arguments:
        style = 'command'
    if style:
        with _lock:
            _preferences[provider_key, tool_key] = style
```

---

## Feature Function: `get_tool_argument_style`
**Logic & Purpose:**
```text
Get observed argument style for a tool, if available.
```

**Parameters:** `provider, tool_name`
**Variables Used:** `provider_key, tool_key`
**Implementation:**
```python
def get_tool_argument_style(provider: Optional[str], tool_name: Optional[str]) -> Optional[str]:
    """Get observed argument style for a tool, if available."""
    if not provider or not tool_name:
        return None
    provider_key = provider.lower()
    tool_key = tool_name.lower()
    with _lock:
        return _preferences.get((provider_key, tool_key))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/conversion/response_converter.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/conversion/response_converter.py`

## Global Presets & Variables
- `DEBUG_SSE` = `os.getenv('DEBUG_SSE', 'false').lower() == 'true'`
- `sse_logger` = `logging.getLogger('sse_debug')`
- `_NUMERIC_PARAM_RE` = `re.compile('"(timeout|offset|limit|cell_number)"\\s*:\\s*"(\\d+)"')`
- `_TOOL_CALL_BLOCK_RE` = `re.compile('<tool_call>(.*?)</tool_call>', re.IGNORECASE | re.DOTALL)`

## Dependencies & Imports
json, re, time, uuid, logging, os, fastapi.HTTPException, fastapi.Request, src.core.constants.Constants, src.models.claude.ClaudeMessagesRequest, src.services.providers.provider_detector.NormalizationLevel, src.services.providers.provider_detector.get_normalization_level, src.services.conversion.tool_behavior_cache.record_tool_argument_style

## Feature Function: `_coerce_int_fields`
**Logic & Purpose:**
```text
Coerce string values to int for specified fields.

Gemini sometimes returns integer-typed parameters as strings
(e.g., "120" instead of 120). Claude Code CLI's strict validator
rejects these with InputValidationError.
```

**Parameters:** `arguments, fields`
**Implementation:**
```python
def _coerce_int_fields(arguments: dict, fields: list) -> dict:
    """Coerce string values to int for specified fields.

    Gemini sometimes returns integer-typed parameters as strings
    (e.g., "120" instead of 120). Claude Code CLI's strict validator
    rejects these with InputValidationError.
    """
    for field in fields:
        if field in arguments and isinstance(arguments[field], str):
            try:
                arguments[field] = int(arguments[field])
            except (ValueError, TypeError):
                pass
    return arguments
```

---

## Feature Function: `_normalize_tool_name`
**Logic & Purpose:**
```text
Normalize tool names that models may call with different names than expected.

For example, some models call "write_file" instead of "Write".
```

**Parameters:** `tool_name, provider`
**Variables Used:** `tool_name_lower, name_mappings`
**Implementation:**
```python
def _normalize_tool_name(tool_name: str, provider: str='gemini') -> str:
    """
    Normalize tool names that models may call with different names than expected.

    For example, some models call "write_file" instead of "Write".
    """
    tool_name_lower = tool_name.lower().replace('_', '')
    name_mappings = {'bash': 'Bash', 'repl': 'Repl', 'read': 'Read', 'write': 'Write', 'edit': 'Edit', 'multiedit': 'MultiEdit', 'glob': 'Glob', 'grep': 'Grep', 'ls': 'LS', 'task': 'Task', 'agentdispatch': 'AgentDispatch', 'todowrite': 'TodoWrite', 'todoread': 'TodoRead', 'webfetch': 'WebFetch', 'websearch': 'WebSearch', 'browser': 'Browser', 'notebookedit': 'NotebookEdit', 'notebookread': 'NotebookRead', 'readfile': 'Read', 'writefile': 'Write', 'runcommand': 'Bash', 'runbash': 'Bash', 'listfiles': 'LS', 'searchfiles': 'Grep', 'search': 'Grep', 'findfiles': 'Glob', 'createtask': 'Task', 'runtask': 'Task', 'todolist': 'TodoRead', 'browse': 'Browser'}
    return name_mappings.get(tool_name_lower, tool_name)
```

---

## Feature Function: `_extract_tool_calls_from_text`
**Logic & Purpose:**
```text
Extract tool calls from text-based tool_call markup.

Returns:
    (remaining_text, tool_calls)
    tool_calls: list of {name: str, arguments: dict}
```

**Parameters:** `buffer`
**Variables Used:** `args_text, name_match, tool_calls, block, arguments, params_match, remaining, name, json_match`
**Implementation:**
```python
def _extract_tool_calls_from_text(buffer: str) -> tuple[str, list[dict]]:
    """
    Extract tool calls from text-based tool_call markup.

    Returns:
        (remaining_text, tool_calls)
        tool_calls: list of {name: str, arguments: dict}
    """
    tool_calls = []
    remaining = buffer
    for match in _TOOL_CALL_BLOCK_RE.finditer(buffer):
        block = match.group(1)
        name = None
        name_match = re.search('<function\\s*=\\s*"?([A-Za-z0-9_ -]+)"?\\s*>', block, re.IGNORECASE)
        if not name_match:
            name_match = re.search('<function\\s+name=\\"([^\\"]+)\\"\\s*>', block, re.IGNORECASE)
        if not name_match:
            name_match = re.search('<function>\\s*([^<]+)\\s*</function>', block, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
        if not name:
            continue
        args_text = None
        params_match = re.search('<parameters>\\s*(.*?)\\s*</parameters>', block, re.IGNORECASE | re.DOTALL)
        if params_match:
            args_text = params_match.group(1)
        else:
            json_match = re.search('({.*})', block, re.DOTALL)
            if json_match:
                args_text = json_match.group(1)
        if not args_text:
            continue
        try:
            arguments = json.loads(args_text)
        except json.JSONDecodeError:
            continue
        tool_calls.append({'name': name, 'arguments': arguments})
    if tool_calls:
        remaining = _TOOL_CALL_BLOCK_RE.sub('', buffer)
    return (remaining, tool_calls)
```

---

## Feature Function: `_build_tool_use_delta_event`
**Logic & Purpose:**
```text
Build a Claude input_json_delta SSE event for a parsed tool call.
```

**Parameters:** `index, arguments`
**Variables Used:** `payload`
**Implementation:**
```python
def _build_tool_use_delta_event(index: int, arguments: dict) -> str:
    """Build a Claude input_json_delta SSE event for a parsed tool call."""
    payload = {'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': index, 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': json.dumps(arguments, ensure_ascii=False)}}
    return f'event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
```

---

## Feature Function: `normalize_tool_arguments`
**Logic & Purpose:**
```text
Normalize tool arguments to match Claude Code CLI's expected schemas.

This function transforms parameter names that may differ between providers
(e.g., Gemini's "prompt" → Claude's "command" for Bash tools).

Normalization intensity varies by provider:
- NONE (openai, azure): Pass through unchanged
- LIGHT (openrouter, openai_compatible): Common mismatches only
- FULL (gemini): All 18+ tool transformations

Handles ALL Claude Code CLI tools:
- Tier 1: Bash, Repl, Read, Write, Edit, MultiEdit
- Tier 2: Glob, Grep, LS
- Tier 3: Task, AgentDispatch
- Tier 4: TodoWrite, TodoRead
- Tier 5: WebFetch, WebSearch, Browser
- Tier 6: NotebookEdit, NotebookRead

Args:
    tool_name: The name of the tool being called
    arguments: The raw arguments dict from the provider
    provider: The provider type (gemini, openrouter, openai, etc.)

Returns:
    Normalized arguments dict matching Claude CLI schema
```

**Parameters:** `tool_name, arguments, provider`
**Variables Used:** `tool_name, normalization_level`
**Implementation:**
```python
def normalize_tool_arguments(tool_name: str, arguments: dict, provider: str='gemini') -> dict:
    """
    Normalize tool arguments to match Claude Code CLI's expected schemas.

    This function transforms parameter names that may differ between providers
    (e.g., Gemini's "prompt" → Claude's "command" for Bash tools).

    Normalization intensity varies by provider:
    - NONE (openai, azure): Pass through unchanged
    - LIGHT (openrouter, openai_compatible): Common mismatches only
    - FULL (gemini): All 18+ tool transformations

    Handles ALL Claude Code CLI tools:
    - Tier 1: Bash, Repl, Read, Write, Edit, MultiEdit
    - Tier 2: Glob, Grep, LS
    - Tier 3: Task, AgentDispatch
    - Tier 4: TodoWrite, TodoRead
    - Tier 5: WebFetch, WebSearch, Browser
    - Tier 6: NotebookEdit, NotebookRead

    Args:
        tool_name: The name of the tool being called
        arguments: The raw arguments dict from the provider
        provider: The provider type (gemini, openrouter, openai, etc.)

    Returns:
        Normalized arguments dict matching Claude CLI schema
    """
    tool_name = _normalize_tool_name(tool_name, provider)
    normalization_level = get_normalization_level(provider)
    if normalization_level == NormalizationLevel.NONE.value:
        return arguments
    if normalization_level == NormalizationLevel.LIGHT.value:
        return _light_normalize(tool_name, arguments)
    return _full_normalize(tool_name, arguments)
```

---

## Feature Function: `_light_normalize`
**Logic & Purpose:**
```text
Light normalization for OpenRouter and OpenAI-compatible providers.

Handles common parameter mismatches that occur with non-Gemini providers.
```

**Parameters:** `tool_name, arguments`
**Variables Used:** `tool_name_lower`
**Implementation:**
```python
def _light_normalize(tool_name: str, arguments: dict) -> dict:
    """
    Light normalization for OpenRouter and OpenAI-compatible providers.

    Handles common parameter mismatches that occur with non-Gemini providers.
    """
    tool_name_lower = tool_name.lower() if tool_name else ''
    if tool_name_lower in ['bash', 'repl']:
        if 'prompt' in arguments and 'command' not in arguments:
            arguments['command'] = arguments.pop('prompt')
            import logging
            logging.getLogger('response_converter').warning(f'⚠️ NORMALIZED {tool_name}: prompt -> command')
        _coerce_int_fields(arguments, ['timeout'])
    if tool_name_lower == 'read':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'filePath' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filePath')
        _coerce_int_fields(arguments, ['offset', 'limit'])
    if tool_name_lower == 'write':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'filePath' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filePath')
        elif 'filename' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filename')
        elif 'file' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('file')
        if 'text' in arguments and 'content' not in arguments:
            arguments['content'] = arguments.pop('text')
        elif 'contents' in arguments and 'content' not in arguments:
            arguments['content'] = arguments.pop('contents')
        elif 'data' in arguments and 'content' not in arguments:
            arguments['content'] = arguments.pop('data')
    if tool_name_lower == 'edit':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'filePath' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filePath')
    return arguments
```

---

## Feature Function: `_full_normalize`
**Logic & Purpose:**
```text
Full normalization for Gemini provider.

Handles all 18+ Claude Code CLI tools with comprehensive parameter mapping.
```

**Parameters:** `tool_name, arguments`
**Variables Used:** `valid_statuses, tool_name_lower, status`
**Implementation:**
```python
def _full_normalize(tool_name: str, arguments: dict) -> dict:
    """
    Full normalization for Gemini provider.

    Handles all 18+ Claude Code CLI tools with comprehensive parameter mapping.
    """
    tool_name_lower = tool_name.lower() if tool_name else ''
    if tool_name_lower in ['bash', 'repl']:
        if 'prompt' in arguments and 'command' not in arguments:
            arguments['command'] = arguments.pop('prompt')
        elif 'code' in arguments and 'command' not in arguments:
            arguments['command'] = arguments.pop('code')
        _coerce_int_fields(arguments, ['timeout'])
    if tool_name_lower == 'read':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'filename' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filename')
        elif 'file' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('file')
        _coerce_int_fields(arguments, ['offset', 'limit'])
    if tool_name_lower == 'write':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'filename' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('filename')
        elif 'file' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('file')
        if 'text' in arguments and 'content' not in arguments:
            arguments['content'] = arguments.pop('text')
        elif 'data' in arguments and 'content' not in arguments:
            arguments['content'] = arguments.pop('data')
    if tool_name_lower == 'edit':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'file' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('file')
        if 'original' in arguments and 'old_text' not in arguments:
            arguments['old_text'] = arguments.pop('original')
        elif 'before' in arguments and 'old_text' not in arguments:
            arguments['old_text'] = arguments.pop('before')
        if 'replacement' in arguments and 'new_text' not in arguments:
            arguments['new_text'] = arguments.pop('replacement')
        elif 'after' in arguments and 'new_text' not in arguments:
            arguments['new_text'] = arguments.pop('after')
    if tool_name_lower == 'multiedit':
        if 'path' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('path')
        elif 'file' in arguments and 'file_path' not in arguments:
            arguments['file_path'] = arguments.pop('file')
        if 'changes' in arguments and 'edits' not in arguments:
            arguments['edits'] = arguments.pop('changes')
        elif 'modifications' in arguments and 'edits' not in arguments:
            arguments['edits'] = arguments.pop('modifications')
    if tool_name_lower == 'glob':
        if 'glob' in arguments and 'pattern' not in arguments:
            arguments['pattern'] = arguments.pop('glob')
        elif 'glob_pattern' in arguments and 'pattern' not in arguments:
            arguments['pattern'] = arguments.pop('glob_pattern')
    if tool_name_lower == 'grep':
        if 'query' in arguments and 'pattern' not in arguments:
            arguments['pattern'] = arguments.pop('query')
        elif 'search' in arguments and 'pattern' not in arguments:
            arguments['pattern'] = arguments.pop('search')
        elif 'regex' in arguments and 'pattern' not in arguments:
            arguments['pattern'] = arguments.pop('regex')
        if 'directory' in arguments and 'path' not in arguments:
            arguments['path'] = arguments.pop('directory')
        elif 'dir' in arguments and 'path' not in arguments:
            arguments['path'] = arguments.pop('dir')
    if tool_name_lower == 'ls':
        if 'directory' in arguments and 'path' not in arguments:
            arguments['path'] = arguments.pop('directory')
        elif 'dir' in arguments and 'path' not in arguments:
            arguments['path'] = arguments.pop('dir')
        elif 'folder' in arguments and 'path' not in arguments:
            arguments['path'] = arguments.pop('folder')
    if tool_name_lower == 'task':
        if 'description' in arguments and 'prompt' not in arguments:
            arguments['prompt'] = arguments['description']
        elif 'prompt' in arguments and 'description' not in arguments:
            arguments['description'] = arguments['prompt']
        if 'agent_type' in arguments and 'subagent_type' not in arguments:
            arguments['subagent_type'] = arguments.pop('agent_type')
        elif 'type' in arguments and 'subagent_type' not in arguments:
            arguments['subagent_type'] = arguments.pop('type')
        if 'subagent_type' not in arguments:
            arguments['subagent_type'] = 'Explore'
    if tool_name_lower == 'agentdispatch':
        if 'id' in arguments and 'agent_id' not in arguments:
            arguments['agent_id'] = arguments.pop('id')
        if 'prompt' in arguments and 'task' not in arguments:
            arguments['task'] = arguments.pop('prompt')
        elif 'instruction' in arguments and 'task' not in arguments:
            arguments['task'] = arguments.pop('instruction')
    if tool_name_lower == 'todowrite':
        if 'tasks' in arguments and 'todos' not in arguments:
            arguments['todos'] = arguments['tasks']
        if 'tasks' in arguments:
            del arguments['tasks']
        if 'items' in arguments and 'todos' not in arguments:
            arguments['todos'] = arguments.pop('items')
        if 'todos' in arguments and isinstance(arguments['todos'], list):
            valid_statuses = {'pending', 'in_progress', 'completed'}
            for todo in arguments['todos']:
                if isinstance(todo, dict) and 'status' in todo:
                    status = todo['status']
                    if status not in valid_statuses:
                        if 'complete' in status.lower():
                            todo['status'] = 'completed'
                        elif 'progress' in status.lower():
                            todo['status'] = 'in_progress'
                        else:
                            todo['status'] = 'pending'
    if tool_name_lower == 'todoread':
        pass
    if tool_name_lower == 'webfetch':
        if 'link' in arguments and 'url' not in arguments:
            arguments['url'] = arguments.pop('link')
        elif 'href' in arguments and 'url' not in arguments:
            arguments['url'] = arguments.pop('href')
        elif 'address' in arguments and 'url' not in arguments:
            arguments['url'] = arguments.pop('address')
    if tool_name_lower == 'websearch':
        if 'search' in arguments and 'query' not in arguments:
            arguments['query'] = arguments.pop('search')
        elif 'q' in arguments and 'query' not in arguments:
            arguments['query'] = arguments.pop('q')
        elif 'term' in arguments and 'query' not in arguments:
            arguments['query'] = arguments.pop('term')
    if tool_name_lower == 'browser':
        if 'link' in arguments and 'url' not in arguments:
            arguments['url'] = arguments.pop('link')
        elif 'address' in arguments and 'url' not in arguments:
            arguments['url'] = arguments.pop('address')
        if 'command' in arguments and 'action' not in arguments:
            arguments['action'] = arguments.pop('command')
        elif 'operation' in arguments and 'action' not in arguments:
            arguments['action'] = arguments.pop('operation')
    if tool_name_lower == 'notebookedit':
        if 'path' in arguments and 'notebook_path' not in arguments:
            arguments['notebook_path'] = arguments.pop('path')
        elif 'file' in arguments and 'notebook_path' not in arguments:
            arguments['notebook_path'] = arguments.pop('file')
        if 'cell' in arguments and 'cell_id' not in arguments:
            arguments['cell_id'] = arguments.pop('cell')
        elif 'index' in arguments and 'cell_id' not in arguments:
            arguments['cell_id'] = arguments.pop('index')
        _coerce_int_fields(arguments, ['cell_number'])
    if tool_name_lower == 'notebookread':
        if 'path' in arguments and 'notebook_path' not in arguments:
            arguments['notebook_path'] = arguments.pop('path')
        elif 'file' in arguments and 'notebook_path' not in arguments:
            arguments['notebook_path'] = arguments.pop('file')
    return arguments
```

---

## Feature Function: `streaming_transform_partial`
**Logic & Purpose:**
```text
Apply partial-arg schema formatting for Claude Code CLI to prevent
real-time streaming validation failures on the client side.

The client strictly validates streaming chunks against its tool schemas.
These operations were specifically put here to ensure Claude Code doesn't 
throw exceptions during the token-by-token stream.

FIXED: We now use strict regex for 'prompt' to ensure we only replace
keys and not random user content inside values.
```

**Parameters:** `partial_args, tool_name, provider`
**Variables Used:** `result`
**Implementation:**
```python
def streaming_transform_partial(partial_args: str, tool_name: str, provider: str='gemini') -> str:
    """
    Apply partial-arg schema formatting for Claude Code CLI to prevent
    real-time streaming validation failures on the client side.

    The client strictly validates streaming chunks against its tool schemas.
    These operations were specifically put here to ensure Claude Code doesn't 
    throw exceptions during the token-by-token stream.

    FIXED: We now use strict regex for 'prompt' to ensure we only replace
    keys and not random user content inside values.
    """
    if tool_name.lower() in ['bash', 'repl', 'runcommand', 'runbash']:
        import re
        result = re.sub('"prompt"\\s*:', '"command":', partial_args)
        result = _NUMERIC_PARAM_RE.sub('"\\1":\\2', result)
        return result
    if tool_name.lower() in ['read', 'readfile', 'notebookedit']:
        return _NUMERIC_PARAM_RE.sub('"\\1":\\2', partial_args)
    return partial_args
```

---

## Feature Function: `convert_openai_to_claude_response`
**Logic & Purpose:**
```text
Convert OpenAI response to Claude format with enhanced error handling.
```

**Parameters:** `openai_response, original_request, provider`
**Variables Used:** `arguments, detail, original_tool_name, cache_read_input_tokens, claude_response, function_data, finish_reason, usage_data, prompt_tokens_details, message, tool_calls, usage, content_blocks, tool_name, error_msg, stop_reason, text_content, choice, choices`
**Implementation:**
```python
def convert_openai_to_claude_response(openai_response: dict, original_request: ClaudeMessagesRequest, provider: str='gemini') -> dict:
    """Convert OpenAI response to Claude format with enhanced error handling."""
    if not isinstance(openai_response, dict):
        raise HTTPException(status_code=500, detail='Invalid OpenAI response format: expected dictionary')
    choices = openai_response.get('choices', [])
    if not choices:
        error_msg = openai_response.get('error', {})
        if error_msg:
            detail = error_msg.get('message', 'No choices in OpenAI response')
            raise HTTPException(status_code=500, detail=f'OpenAI error: {detail}')
        import logging
        logging.getLogger('response_converter').warning(f"Empty choices in OpenAI response: {openai_response.get('id', 'unknown')}")
        raise HTTPException(status_code=500, detail='No choices in OpenAI response - possible rate limiting. Try again.')
    if not isinstance(choices, list):
        raise HTTPException(status_code=500, detail='Invalid choices format in OpenAI response')
    choice = choices[0]
    if not isinstance(choice, dict):
        raise HTTPException(status_code=500, detail='Invalid choice format in OpenAI response')
    message = choice.get('message', {})
    content_blocks = []
    text_content = message.get('content')
    if text_content is not None:
        content_blocks.append({'type': Constants.CONTENT_TEXT, 'text': text_content})
    tool_calls = message.get('tool_calls', []) or []
    for tool_call in tool_calls:
        if tool_call.get('type') == Constants.TOOL_FUNCTION:
            function_data = tool_call.get(Constants.TOOL_FUNCTION, {})
            try:
                arguments = json.loads(function_data.get('arguments', '{}'))
            except json.JSONDecodeError:
                arguments = {'raw_arguments': function_data.get('arguments', '')}
            original_tool_name = function_data.get('name', '')
            tool_name = _normalize_tool_name(original_tool_name, provider)
            record_tool_argument_style(provider, tool_name, arguments)
            arguments = normalize_tool_arguments(tool_name, arguments, provider)
            content_blocks.append({'type': Constants.CONTENT_TOOL_USE, 'id': tool_call.get('id', f'tool_{uuid.uuid4()}'), 'name': tool_name, 'input': arguments})
    if not content_blocks:
        content_blocks.append({'type': Constants.CONTENT_TEXT, 'text': ''})
    finish_reason = choice.get('finish_reason', 'stop')
    stop_reason = {'stop': Constants.STOP_END_TURN, 'length': Constants.STOP_MAX_TOKENS, 'tool_calls': Constants.STOP_TOOL_USE, 'function_call': Constants.STOP_TOOL_USE}.get(finish_reason, Constants.STOP_END_TURN)
    usage = openai_response.get('usage', {})
    usage_data = {'input_tokens': usage.get('prompt_tokens', 0), 'output_tokens': usage.get('completion_tokens', 0)}
    prompt_tokens_details = usage.get('prompt_tokens_details', {})
    if prompt_tokens_details:
        cache_read_input_tokens = prompt_tokens_details.get('cached_tokens', 0)
        if cache_read_input_tokens > 0:
            usage_data['cache_read_input_tokens'] = cache_read_input_tokens
    claude_response = {'id': openai_response.get('id', f'msg_{uuid.uuid4()}'), 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': content_blocks, 'stop_reason': stop_reason, 'stop_sequence': None, 'usage': usage_data}
    return claude_response
```

---

## Feature Function: `convert_openai_streaming_to_claude`
**Logic & Purpose:**
```text
Convert OpenAI streaming response to Claude streaming format with provider-aware normalization.
```

**Parameters:** `openai_stream, original_request, logger, provider`
**Variables Used:** `partial_args, tool_call, delta, current_tool_calls, tool_text_buffer, chunk, reasoning_log_path, function_data, thinking_requested, final_stop_reason, reasoning_placeholder_emitted, normalized_args, transformed_partial, finish_reason, choices, reasoning_last_beat, reasoning_chars_since_heartbeat, usage_data, reasoning_log_file, reasoning_active, complete_args, chunk_data, err_code, tc_index, err, tool_call_id, tool_text_parsed_any, error_event, log_dir, now, current_block_index, tool_name, current_block_type, choice, text_content, reasoning_content, tool_text_mode, message_id, err_msg`
**Implementation:**
```python
async def convert_openai_streaming_to_claude(openai_stream, original_request: ClaudeMessagesRequest, logger, provider: str='gemini'):
    """Convert OpenAI streaming response to Claude streaming format with provider-aware normalization."""
    message_id = f'msg_{uuid.uuid4().hex[:24]}'
    yield f"event: {Constants.EVENT_MESSAGE_START}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n"
    current_block_type = 'text'
    current_block_index = 0
    current_tool_calls = {}
    final_stop_reason = Constants.STOP_END_TURN
    usage_data = {'input_tokens': 0, 'output_tokens': 0}
    tool_text_buffer = ''
    tool_text_mode = False
    tool_text_parsed_any = False
    thinking_requested = original_request.thinking is not None
    reasoning_active = False
    reasoning_placeholder_emitted = False
    reasoning_chars_since_heartbeat = 0
    reasoning_last_beat = time.monotonic()
    reasoning_log_file = None
    reasoning_log_path = None
    try:
        async for line in openai_stream:
            if line.strip():
                if line.startswith('data: '):
                    chunk_data = line[6:]
                    if chunk_data.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(chunk_data)
                        choices = chunk.get('choices', [])
                        if not choices:
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(f'Failed to parse chunk: {chunk_data}, error: {e}')
                        continue
                    choice = choices[0]
                    delta = choice.get('delta', {})
                    finish_reason = choice.get('finish_reason')
                    if chunk.get('error'):
                        err = chunk['error']
                        if isinstance(err, dict):
                            err_msg = err.get('message', 'Upstream error')
                            err_code = err.get('code', 'upstream_error')
                        else:
                            err_msg = str(err)
                            err_code = 'upstream_error'
                        logger.error(f'Upstream error in stream: {err_code} - {err_msg}')
                        yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': f'Upstream error ({err_code}): {err_msg}'}}, ensure_ascii=False)}\n\n"
                        return
                    reasoning_content = delta.get('reasoning_content') or delta.get('thinking')
                    if reasoning_content:
                        if thinking_requested:
                            if current_block_type != 'thinking':
                                if current_block_index >= 0:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                current_block_index += 1
                                current_block_type = 'thinking'
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_THINKING, 'thinking': ''}}, ensure_ascii=False)}\n\n"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_THINKING, 'thinking': reasoning_content}}, ensure_ascii=False)}\n\n"
                        else:
                            if reasoning_log_file is None:
                                try:
                                    log_dir = os.path.expanduser('~/.cache/claude-code-proxy/reasoning')
                                    os.makedirs(log_dir, exist_ok=True)
                                    reasoning_log_path = os.path.join(log_dir, f'{message_id}.log')
                                    reasoning_log_file = open(reasoning_log_path, 'w', encoding='utf-8')
                                except Exception as _log_err:
                                    logger.warning(f'Could not open reasoning log: {_log_err}')
                                    reasoning_log_file = False
                            if reasoning_log_file:
                                try:
                                    reasoning_log_file.write(reasoning_content)
                                    reasoning_log_file.flush()
                                except Exception:
                                    pass
                            reasoning_active = True
                            reasoning_chars_since_heartbeat += len(reasoning_content)
                            if not reasoning_placeholder_emitted:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '💭 thinking'}}, ensure_ascii=False)}\n\n"
                                reasoning_placeholder_emitted = True
                                reasoning_last_beat = time.monotonic()
                                reasoning_chars_since_heartbeat = 0
                            else:
                                now = time.monotonic()
                                if now - reasoning_last_beat >= 1.5 or reasoning_chars_since_heartbeat >= 400:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '.'}}, ensure_ascii=False)}\n\n"
                                    reasoning_last_beat = now
                                    reasoning_chars_since_heartbeat = 0
                    text_content = delta.get('content')
                    if text_content is not None:
                        if reasoning_active and text_content.strip():
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '\n\n'}}, ensure_ascii=False)}\n\n"
                            reasoning_active = False
                        if tool_text_mode or '<tool_call>' in text_content:
                            tool_text_mode = True
                            tool_text_buffer += text_content
                            tool_text_buffer, extracted_calls = _extract_tool_calls_from_text(tool_text_buffer)
                            if extracted_calls:
                                tool_text_parsed_any = True
                                if current_block_type in ['thinking', 'text']:
                                    if current_block_index >= 0:
                                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                    current_block_index = -1
                                    current_block_type = None
                                for call in extracted_calls:
                                    tool_name = _normalize_tool_name(call['name'], provider)
                                    record_tool_argument_style(provider, tool_name, call['arguments'])
                                    normalized_args = normalize_tool_arguments(tool_name, call['arguments'], provider)
                                    current_block_index += 1
                                    tool_call_id = f'tool_{uuid.uuid4().hex[:24]}'
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call_id, 'name': tool_name}}, ensure_ascii=False)}\n\n"
                                    yield _build_tool_use_delta_event(current_block_index, normalized_args)
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                    current_block_index = -1
                                    current_block_type = None
                                final_stop_reason = Constants.STOP_TOOL_USE
                        else:
                            if current_block_type != 'text':
                                if current_block_index >= 0:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                current_block_index += 1
                                current_block_type = 'text'
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': text_content}}, ensure_ascii=False)}\n\n"
                    if 'tool_calls' in delta and delta['tool_calls']:
                        if current_block_type in ['thinking', 'text']:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_type = 'tool'
                        for tc_delta in delta['tool_calls']:
                            tc_index = tc_delta.get('index', 0)
                            if tc_index not in current_tool_calls:
                                current_tool_calls[tc_index] = {'id': None, 'name': None, 'args_buffer': '', 'json_sent': False, 'claude_index': None, 'started': False}
                            tool_call = current_tool_calls[tc_index]
                            if tc_delta.get('id'):
                                tool_call['id'] = tc_delta['id']
                            function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                            if function_data.get('name'):
                                tool_call['name'] = function_data['name']
                            if tool_call['id'] and tool_call['name'] and (not tool_call['started']):
                                current_block_index += 1
                                tool_call['claude_index'] = current_block_index
                                tool_call['started'] = True
                                if DEBUG_SSE:
                                    sse_logger.info(f"SSE: content_block_start tool_use index={current_block_index} name={tool_call['name']} id={tool_call['id'][:12]}...")
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': tool_call['claude_index'], 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call['id'], 'name': tool_call['name']}}, ensure_ascii=False)}\n\n"
                            if 'arguments' in function_data and tool_call['started'] and (function_data['arguments'] is not None):
                                partial_args = function_data['arguments']
                                tool_call['args_buffer'] += partial_args
                                transformed_partial = streaming_transform_partial(partial_args, tool_call['name'], provider)
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': tool_call['claude_index'], 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': transformed_partial}}, ensure_ascii=False)}\n\n"
                    if finish_reason:
                        if DEBUG_SSE:
                            sse_logger.info(f'SSE: finish_reason={finish_reason} current_block_index={current_block_index} current_block_type={current_block_type}')
                        if tool_text_parsed_any:
                            final_stop_reason = Constants.STOP_TOOL_USE
                        elif finish_reason == 'length':
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ['tool_calls', 'function_call']:
                            final_stop_reason = Constants.STOP_TOOL_USE
                            if DEBUG_SSE:
                                sse_logger.info(f'Processing {len(current_tool_calls)} completed tool calls')
                            for tc_index, tool_call in current_tool_calls.items():
                                if tool_call['started'] and tool_call['name']:
                                    try:
                                        if not tool_call['args_buffer']:
                                            continue
                                        complete_args = json.loads(tool_call['args_buffer'])
                                        tool_name = _normalize_tool_name(tool_call['name'], provider)
                                        record_tool_argument_style(provider, tool_name, complete_args)
                                        normalized_args = normalize_tool_arguments(tool_name, complete_args, provider)
                                        if DEBUG_SSE:
                                            sse_logger.info(f"Normalized args for '{tool_name}': {normalized_args}")
                                        tool_call['normalized_args'] = normalized_args
                                    except json.JSONDecodeError as e:
                                        if DEBUG_SSE:
                                            sse_logger.warning(f"Failed to parse args_buffer for '{tool_call['name']}': {e}")
                        elif finish_reason == 'stop':
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN
                        if DEBUG_SSE:
                            sse_logger.info(f'SSE: final_stop_reason={final_stop_reason}')
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_index = -1
                            current_block_type = None
                        break
    except Exception as e:
        logger.error(f'Streaming error: {e}')
        error_event = {'type': 'error', 'error': {'type': 'api_error', 'message': f'Streaming error: {str(e)}'}}
        yield f'event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n'
        return
    if tool_text_mode and (not tool_text_parsed_any) and tool_text_buffer.strip():
        if current_block_type != 'text':
            if current_block_index >= 0:
                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
            current_block_index += 1
            current_block_type = 'text'
            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': tool_text_buffer}}, ensure_ascii=False)}\n\n"
    if current_block_index >= 0 and current_block_type is not None:
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
    if DEBUG_SSE:
        sse_logger.info(f'SSE: Stream ended normally. stop_reason={final_stop_reason} usage={usage_data}')
    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n"
```

---

## Feature Function: `convert_openai_streaming_to_claude_with_cancellation`
**Logic & Purpose:**
```text
Convert OpenAI streaming response to Claude streaming format with cancellation support and provider-aware normalization.

Args:
    on_complete: Optional async callback invoked when the stream finishes.
        Signature: async (usage_data: dict, stop_reason: str, error: str | None) -> None
```

**Parameters:** `openai_stream, original_request, logger, http_request, openai_client, request_id, config, provider, on_complete`
**Variables Used:** `active_tool_ids, partial_args, original_tool_name, stream_error, delta, current_tool_calls, tool_text_buffer, chunk, cache_read_input_tokens, reasoning_log_path, function_data, thinking_requested, final_stop_reason, reasoning_placeholder_emitted, duration_ms, known_id, transformed_partial, normalized_args, first_args, finish_reason, choices, reasoning_last_beat, reasoning_chars_since_heartbeat, stream_start_time, usage_data, is_new_block, tc_id, reasoning_log_file, reasoning_active, complete_args, prompt_tokens_details, chunk_data, err_code, tc_index, err, usage, tool_call_id, tool_text_parsed_any, target_claude_index, error_event, log_dir, now, current_block_index, stream_index_to_id, tool_name, current_block_type, choice, text_content, reasoning_content, tool_text_mode, message_id, tool_call_state, err_msg`
**Implementation:**
```python
async def convert_openai_streaming_to_claude_with_cancellation(openai_stream, original_request: ClaudeMessagesRequest, logger, http_request: Request, openai_client, request_id: str, config=None, provider: str='gemini', on_complete=None):
    """Convert OpenAI streaming response to Claude streaming format with cancellation support and provider-aware normalization.

    Args:
        on_complete: Optional async callback invoked when the stream finishes.
            Signature: async (usage_data: dict, stop_reason: str, error: str | None) -> None
    """
    stream_start_time = time.monotonic()
    message_id = f'msg_{uuid.uuid4().hex[:24]}'
    yield f"event: {Constants.EVENT_MESSAGE_START}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n"
    current_block_type = 'text'
    current_block_index = 0
    current_tool_calls = {}
    active_tool_ids = {}
    stream_index_to_id = {}
    final_stop_reason = Constants.STOP_END_TURN
    usage_data = {'input_tokens': 0, 'output_tokens': 0}
    tool_text_buffer = ''
    tool_text_mode = False
    tool_text_parsed_any = False
    thinking_requested = original_request.thinking is not None
    reasoning_active = False
    reasoning_placeholder_emitted = False
    reasoning_chars_since_heartbeat = 0
    reasoning_last_beat = time.monotonic()
    reasoning_log_file = None
    reasoning_log_path = None
    try:
        async for line in openai_stream:
            if await http_request.is_disconnected():
                logger.info(f'Client disconnected, cancelling request {request_id}')
                openai_client.cancel_request(request_id)
                break
            if line.strip():
                if line.startswith('data: '):
                    chunk_data = line[6:]
                    if chunk_data.strip() == '[DONE]':
                        if DEBUG_SSE:
                            sse_logger.info('SSE: Received [DONE] signal, stream ending normally')
                        break
                    try:
                        chunk = json.loads(chunk_data)
                        usage = chunk.get('usage', None)
                        if usage:
                            cache_read_input_tokens = 0
                            prompt_tokens_details = usage.get('prompt_tokens_details', {})
                            if prompt_tokens_details:
                                cache_read_input_tokens = prompt_tokens_details.get('cached_tokens', 0)
                            usage_data = {'input_tokens': usage.get('prompt_tokens', 0), 'output_tokens': usage.get('completion_tokens', 0), 'cache_read_input_tokens': cache_read_input_tokens}
                        choices = chunk.get('choices', [])
                        if not choices:
                            continue
                    except json.JSONDecodeError as e:
                        logger.warning(f'Failed to parse chunk: {chunk_data}, error: {e}')
                        continue
                    choice = choices[0]
                    delta = choice.get('delta', {})
                    finish_reason = choice.get('finish_reason')
                    if chunk.get('error'):
                        err = chunk['error']
                        if isinstance(err, dict):
                            err_msg = err.get('message', 'Upstream error')
                            err_code = err.get('code', 'upstream_error')
                        else:
                            err_msg = str(err)
                            err_code = 'upstream_error'
                        logger.error(f'Upstream error in stream: {err_code} - {err_msg}')
                        yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'type': 'api_error', 'message': f'Upstream error ({err_code}): {err_msg}'}}, ensure_ascii=False)}\n\n"
                        return
                    reasoning_content = delta.get('reasoning_content') or delta.get('thinking')
                    if reasoning_content:
                        if thinking_requested:
                            if current_block_type != 'thinking':
                                if current_block_index >= 0:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                current_block_index += 1
                                current_block_type = 'thinking'
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_THINKING, 'thinking': ''}}, ensure_ascii=False)}\n\n"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_THINKING, 'thinking': reasoning_content}}, ensure_ascii=False)}\n\n"
                        else:
                            if reasoning_log_file is None:
                                try:
                                    log_dir = os.path.expanduser('~/.cache/claude-code-proxy/reasoning')
                                    os.makedirs(log_dir, exist_ok=True)
                                    reasoning_log_path = os.path.join(log_dir, f'{message_id}.log')
                                    reasoning_log_file = open(reasoning_log_path, 'w', encoding='utf-8')
                                except Exception as _log_err:
                                    logger.warning(f'Could not open reasoning log: {_log_err}')
                                    reasoning_log_file = False
                            if reasoning_log_file:
                                try:
                                    reasoning_log_file.write(reasoning_content)
                                    reasoning_log_file.flush()
                                except Exception:
                                    pass
                            reasoning_active = True
                            reasoning_chars_since_heartbeat += len(reasoning_content)
                            if not reasoning_placeholder_emitted:
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '💭 thinking'}}, ensure_ascii=False)}\n\n"
                                reasoning_placeholder_emitted = True
                                reasoning_last_beat = time.monotonic()
                                reasoning_chars_since_heartbeat = 0
                            else:
                                now = time.monotonic()
                                if now - reasoning_last_beat >= 1.5 or reasoning_chars_since_heartbeat >= 400:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '.'}}, ensure_ascii=False)}\n\n"
                                    reasoning_last_beat = now
                                    reasoning_chars_since_heartbeat = 0
                    text_content = delta.get('content')
                    if text_content:
                        if reasoning_active and text_content.strip():
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': '\n\n'}}, ensure_ascii=False)}\n\n"
                            reasoning_active = False
                        if tool_text_mode or '<tool_call>' in text_content:
                            tool_text_mode = True
                            tool_text_buffer += text_content
                            tool_text_buffer, extracted_calls = _extract_tool_calls_from_text(tool_text_buffer)
                            if extracted_calls:
                                tool_text_parsed_any = True
                                if current_block_type in ['thinking', 'text']:
                                    if current_block_index >= 0:
                                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                    current_block_index = -1
                                    current_block_type = None
                                for call in extracted_calls:
                                    tool_name = _normalize_tool_name(call['name'], provider)
                                    record_tool_argument_style(provider, tool_name, call['arguments'])
                                    normalized_args = normalize_tool_arguments(tool_name, call['arguments'], provider)
                                    current_block_index += 1
                                    tool_call_id = f'tool_{uuid.uuid4().hex[:24]}'
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call_id, 'name': tool_name}}, ensure_ascii=False)}\n\n"
                                    yield _build_tool_use_delta_event(current_block_index, normalized_args)
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                    current_block_index = -1
                                    current_block_type = None
                                final_stop_reason = Constants.STOP_TOOL_USE
                        else:
                            if current_block_type != 'text':
                                if current_block_index >= 0:
                                    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                                current_block_index += 1
                                current_block_type = 'text'
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': text_content}}, ensure_ascii=False)}\n\n"
                            if text_content.strip():
                                logger.debug(f"STREAM: text delta idx={current_block_index}, text='{text_content[:30]}'")
                    if 'tool_calls' in delta and delta['tool_calls']:
                        if current_block_type in ['thinking', 'text']:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_type = 'tool'
                        for tc_delta in delta['tool_calls']:
                            tc_index = tc_delta.get('index', 0)
                            tc_id = tc_delta.get('id')
                            target_claude_index = None
                            is_new_block = False
                            if tc_id:
                                stream_index_to_id[tc_index] = tc_id
                                if tc_id in active_tool_ids:
                                    target_claude_index = active_tool_ids[tc_id]['claude_index']
                                    if active_tool_ids[tc_id]['primary_index'] != tc_index:
                                        logger.debug(f"Ignoring ghost stream for ID {tc_id} (index {tc_index} vs primary {active_tool_ids[tc_id]['primary_index']})")
                                        continue
                                else:
                                    function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                                    original_tool_name = function_data.get('name', '')
                                    tool_name = _normalize_tool_name(original_tool_name, provider)
                                    first_args = function_data.get('arguments', '')
                                    if tool_name:
                                        pass
                                    current_block_index += 1
                                    target_claude_index = current_block_index
                                    is_new_block = True
                                    active_tool_ids[tc_id] = {'primary_index': tc_index, 'claude_index': current_block_index}
                                    logger.debug(f'New tool call detected: index={tc_index}, id={tc_id} -> claude_index={current_block_index}')
                            else:
                                known_id = stream_index_to_id.get(tc_index)
                                if known_id and known_id in active_tool_ids:
                                    target_claude_index = active_tool_ids[known_id]['claude_index']
                                else:
                                    if tc_index > 0:
                                        logger.debug(f'Ignoring unmapped tool delta at index {tc_index}')
                                        continue
                                    if current_tool_calls.get(0, {}).get('claude_index') is not None:
                                        target_claude_index = current_tool_calls[0]['claude_index']
                                        logger.debug(f'Fallback: mapping index 0 to existing claude_index {target_claude_index}')
                            if target_claude_index is None:
                                continue
                            if is_new_block or tc_index not in current_tool_calls:
                                if tc_index not in current_tool_calls:
                                    current_tool_calls[tc_index] = {'id': tc_id, 'name': None, 'args_buffer': '', 'claude_index': target_claude_index}
                                tool_call_state = current_tool_calls[tc_index]
                            else:
                                tool_call_state = current_tool_calls.get(tc_index)
                                if not tool_call_state:
                                    continue
                            function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                            if function_data.get('name'):
                                tool_call_state['name'] = _normalize_tool_name(function_data['name'], provider)
                            if is_new_block and tc_id and tool_call_state.get('name'):
                                if DEBUG_SSE:
                                    sse_logger.info(f"SSE[cancel]: content_block_start tool_use index={target_claude_index} name={tool_call_state['name']} id={tc_id[:12]}...")
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': target_claude_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tc_id, 'name': tool_call_state['name']}}, ensure_ascii=False)}\n\n"
                            if 'arguments' in function_data and function_data['arguments'] is not None:
                                partial_args = function_data['arguments']
                                tool_call_state['args_buffer'] += partial_args
                                transformed_partial = streaming_transform_partial(partial_args, tool_call_state.get('name', ''), provider)
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': target_claude_index, 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': transformed_partial}}, ensure_ascii=False)}\n\n"
                    if finish_reason:
                        if DEBUG_SSE:
                            sse_logger.info(f'SSE[cancel]: finish_reason={finish_reason} current_block_index={current_block_index}')
                        if tool_text_parsed_any:
                            final_stop_reason = Constants.STOP_TOOL_USE
                        elif finish_reason == 'length':
                            final_stop_reason = Constants.STOP_MAX_TOKENS
                        elif finish_reason in ['tool_calls', 'function_call']:
                            final_stop_reason = Constants.STOP_TOOL_USE
                            if DEBUG_SSE:
                                sse_logger.info(f'Processing {len(current_tool_calls)} completed tool calls (cancel version)')
                            for tc_index, tool_call in current_tool_calls.items():
                                if tool_call.get('name'):
                                    try:
                                        if not tool_call['args_buffer']:
                                            continue
                                        complete_args = json.loads(tool_call['args_buffer'])
                                        tool_name = _normalize_tool_name(tool_call['name'], provider)
                                        record_tool_argument_style(provider, tool_name, complete_args)
                                        normalized_args = normalize_tool_arguments(tool_name, complete_args, provider)
                                        if DEBUG_SSE:
                                            sse_logger.info(f"Normalized args for '{tool_name}': {normalized_args}")
                                        tool_call['normalized_args'] = normalized_args
                                    except json.JSONDecodeError as e:
                                        if DEBUG_SSE:
                                            sse_logger.warning(f"Failed to parse args_buffer for '{tool_call['name']}': {e}")
                        elif finish_reason == 'stop':
                            final_stop_reason = Constants.STOP_END_TURN
                        else:
                            final_stop_reason = Constants.STOP_END_TURN
                        if DEBUG_SSE:
                            sse_logger.info(f'SSE[cancel]: final_stop_reason={final_stop_reason}')
                        if current_block_index >= 0:
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
                            current_block_index = -1
                            current_block_type = None
                        break
    except HTTPException as e:
        if e.status_code == 499:
            logger.info(f'Request {request_id} was cancelled')
            error_event = {'type': 'error', 'error': {'type': 'cancelled', 'message': 'Request was cancelled by client'}}
        else:
            logger.error(f'HTTPException during streaming: {e.status_code} - {e.detail}')
            error_event = {'type': 'error', 'error': {'type': 'api_error', 'message': f'API error ({e.status_code}): {e.detail}'}}
        yield f'event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n'
        if on_complete:
            try:
                duration_ms = (time.monotonic() - stream_start_time) * 1000
                import asyncio
                asyncio.ensure_future(on_complete(usage_data, final_stop_reason, duration_ms, str(e)))
            except Exception:
                pass
        return
    except Exception as e:
        logger.error(f'Streaming error: {e}')
        import traceback
        logger.error(traceback.format_exc())
        error_event = {'type': 'error', 'error': {'type': 'api_error', 'message': f'Streaming error: {str(e)}'}}
        yield f'event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n'
        if on_complete:
            try:
                duration_ms = (time.monotonic() - stream_start_time) * 1000
                import asyncio
                asyncio.ensure_future(on_complete(usage_data, final_stop_reason, duration_ms, str(e)))
            except Exception:
                pass
        return
    stream_error = None
    if tool_text_mode and (not tool_text_parsed_any) and tool_text_buffer.strip():
        if current_block_type != 'text':
            if current_block_index >= 0:
                yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
            current_block_index += 1
            current_block_type = 'text'
            yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': current_block_index, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': current_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': tool_text_buffer}}, ensure_ascii=False)}\n\n"
    if current_block_index >= 0:
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': current_block_index}, ensure_ascii=False)}\n\n"
    if DEBUG_SSE:
        sse_logger.info(f'SSE[cancel]: Stream ended normally. stop_reason={final_stop_reason} usage={usage_data}')
    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n"
    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n"
    if on_complete:
        try:
            duration_ms = (time.monotonic() - stream_start_time) * 1000
            import asyncio
            asyncio.ensure_future(on_complete(usage_data, final_stop_reason, duration_ms, stream_error))
        except Exception as cb_err:
            logger.warning(f'on_complete callback failed: {cb_err}')
```

---


