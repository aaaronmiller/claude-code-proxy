# File Audit: /home/cheta/code/claude-code-proxy/src/services/logging/compact_logger.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/logging/compact_logger.py`

**Module Overview**: 
```text
Ultra-compact single-line request logger with sophisticated color scheme.

Design principles:
- Everything on ONE line
- Use emojis to save tokens
- Subtle colors for normal ops, bright for warnings/errors
- Color shades to differentiate request types
- Session-based color consistency
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `compact_logger` = `CompactLogger()`

## Dependencies & Imports
hashlib, logging, typing.Optional, typing.Dict, typing.Any, datetime.datetime

## Feature Class: `CompactLogger`
**Description:**
```text
Single-line, color-coded, emoji-rich request logger.
```

### Method: `_get_session_color`
**Logic & Purpose:**
```text
Get consistent color and style for session.
```

**Parameters:** `session_id`
**Variables Used:** `color_idx, session_hash`
**Implementation:**
```python
@staticmethod
def _get_session_color(session_id: str) -> tuple[str, str]:
    """Get consistent color and style for session."""
    if not session_id:
        return ('white', 'dim')
    session_hash = int(hashlib.md5(session_id[:8].encode()).hexdigest()[:8], 16)
    color_idx = session_hash % len(CompactLogger.SESSION_COLORS)
    return CompactLogger.SESSION_COLORS[color_idx]
```

### Method: `_get_request_type`
**Logic & Purpose:**
```text
Determine request type for color coding.
```

**Parameters:** `has_tools, has_images, reasoning_config, stream`
**Implementation:**
```python
@staticmethod
def _get_request_type(has_tools: bool=False, has_images: bool=False, reasoning_config: Any=None, stream: bool=False) -> str:
    """Determine request type for color coding."""
    if reasoning_config:
        return 'reasoning'
    if has_images:
        return 'images'
    if has_tools:
        return 'tools'
    if stream:
        return 'streaming'
    return 'text'
```

### Method: `_fmt_tokens`
**Logic & Purpose:**
```text
Format token count compactly.
```

**Parameters:** `count`
**Implementation:**
```python
@staticmethod
def _fmt_tokens(count: int) -> str:
    """Format token count compactly."""
    if count >= 1000000:
        return f'{count / 1000000:.1f}M'
    elif count >= 1000:
        return f'{count / 1000:.1f}k'
    else:
        return str(count)
```

### Method: `_fmt_duration`
**Logic & Purpose:**
```text
Format duration compactly.
```

**Parameters:** `ms`
**Implementation:**
```python
@staticmethod
def _fmt_duration(ms: float) -> str:
    """Format duration compactly."""
    if ms >= 60000:
        return f'{ms / 60000:.1f}m'
    elif ms >= 1000:
        return f'{ms / 1000:.1f}s'
    else:
        return f'{ms:.0f}ms'
```

### Method: `_get_model_short`
**Logic & Purpose:**
```text
Get short model name.
```

**Parameters:** `model`
**Variables Used:** `size, model_part, provider, parts, family`
**Implementation:**
```python
@staticmethod
def _get_model_short(model: str) -> str:
    """Get short model name."""
    if '/' in model:
        parts = model.split('/')
        provider = parts[0][:3]
        model_part = parts[1]
        if 'gpt-5' in model_part:
            family = 'gpt5'
        elif 'gpt-4o' in model_part:
            family = '4o'
        elif 'o1' in model_part or 'o3' in model_part:
            family = model_part.split('-')[0]
        elif 'claude-3.5' in model_part or 'claude-sonnet-4' in model_part:
            family = 'c3.5' if '3.5' in model_part else 'c4'
        elif 'claude' in model_part:
            family = 'c3'
        else:
            family = model_part[:6]
        size = ''
        if 'mini' in model_part:
            size = '-m'
        elif 'haiku' in model_part:
            size = '-h'
        elif 'sonnet' in model_part:
            size = '-s'
        elif 'opus' in model_part:
            size = '-o'
        return f'{provider}/{family}{size}'
    else:
        return model[:12]
```

### Method: `log_request_start`
**Logic & Purpose:**
```text
Log request start - SINGLE LINE.

Format:
🔵abc12│ant/c3.5-s→ope/gpt5│6.2k/200k(3%)→16k│⚡8k│📨3│🔧│127.0.0.1
```

**Parameters:** `request_id, original_model, routed_model, endpoint, reasoning_config, stream, input_tokens, context_limit, output_limit, message_count, has_system, has_tools, has_images, client_info, workspace_name`
**Variables Used:** `routed, ctx_str, meta, line, parts, text, style, parts_str, orig, ctx_pct, think_str, icon_map, ctx_color, req_type, rid, type_icon`
**Implementation:**
```python
@staticmethod
def log_request_start(request_id: str, original_model: str, routed_model: str, endpoint: str, reasoning_config: Optional[Any]=None, stream: bool=False, input_tokens: int=0, context_limit: int=0, output_limit: int=0, message_count: int=0, has_system: bool=False, has_tools: bool=False, has_images: bool=False, client_info: Optional[str]=None, workspace_name: Optional[str]=None, **kwargs) -> None:
    """
        Log request start - SINGLE LINE.

        Format:
        🔵abc12│ant/c3.5-s→ope/gpt5│6.2k/200k(3%)→16k│⚡8k│📨3│🔧│127.0.0.1
        """
    req_type = CompactLogger._get_request_type(has_tools, has_images, reasoning_config, stream)
    session_color, session_style = CompactLogger._get_session_color(request_id)
    icon_map = {'reasoning': '🧠', 'tools': '🔧', 'images': '🖼️', 'streaming': '🌊', 'text': '📝'}
    type_icon = icon_map.get(req_type, '📝')
    rid = request_id[:5]
    orig = CompactLogger._get_model_short(original_model)
    routed = CompactLogger._get_model_short(routed_model)
    parts = []
    if context_limit > 0 and input_tokens > 0:
        ctx_pct = int(input_tokens / context_limit * 100)
        ctx_color = 'green' if ctx_pct < 50 else 'yellow' if ctx_pct < 80 else 'red'
        ctx_str = f'{CompactLogger._fmt_tokens(input_tokens)}/{CompactLogger._fmt_tokens(context_limit)}({ctx_pct}%)'
        parts.append(('ctx', ctx_str, ctx_color))
    elif input_tokens > 0:
        parts.append(('ctx', CompactLogger._fmt_tokens(input_tokens), 'cyan'))
    if output_limit > 0:
        parts.append(('out', CompactLogger._fmt_tokens(output_limit), 'blue'))
    if reasoning_config:
        from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
        if isinstance(reasoning_config, OpenAIReasoningConfig):
            think_str = CompactLogger._fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
        elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
            think_str = CompactLogger._fmt_tokens(reasoning_config.budget)
        else:
            think_str = '?'
        parts.append(('think', think_str, 'magenta'))
    if RICH_AVAILABLE and console:
        text = Text()
        style = f'{session_style} {session_color}' if session_style else session_color
        text.append('🔵', style=f'bold {session_color}')
        text.append(f'{rid}', style=style)
        text.append('│', style='dim')
        text.append(f'{orig}', style='yellow')
        text.append('→', style='dim')
        text.append(f'{routed}', style='green')
        text.append('│', style='dim')
        for i, (label, value, color) in enumerate(parts):
            if i > 0:
                text.append('→', style='dim')
            text.append(value, style=color)
        text.append('│', style='dim')
        text.append(type_icon)
        if message_count > 0:
            text.append(f'{message_count}', style='dim')
        if has_system:
            text.append('🖥️', style='dim')
        if stream:
            text.append('🌊', style='dim')
        if client_info:
            text.append(f'│{client_info[:9]}', style='dim')
        console.print(text)
    else:
        parts_str = '→'.join([f'{v}' for _, v, _ in parts])
        meta = f"{type_icon}{(message_count if message_count > 0 else '')}"
        if has_system:
            meta += '🖥️'
        if stream:
            meta += '🌊'
        line = f'🔵{rid}│{orig}→{routed}│{parts_str}│{meta}'
        if client_info:
            line += f'│{client_info[:9]}'
        logger.info(line)
```

### Method: `log_request_complete`
**Logic & Purpose:**
```text
Log request completion - SINGLE LINE.

Format:
🟢abc12│15.2s│43.7k→1.3k💭920│82t/s│$0.023
```

**Parameters:** `request_id, usage, duration_ms, status, model_name, stream, has_reasoning`
**Variables Used:** `output_tokens, tps, details, input_tokens, cost, parts, text, tokens_str, icon, cost_map, tps_color, cost_color, thinking_tokens, rid, color, style`
**Implementation:**
```python
@staticmethod
def log_request_complete(request_id: str, usage: Optional[Dict[str, Any]]=None, duration_ms: Optional[float]=None, status: str='OK', model_name: Optional[str]=None, stream: bool=False, has_reasoning: bool=False) -> None:
    """
        Log request completion - SINGLE LINE.

        Format:
        🟢abc12│15.2s│43.7k→1.3k💭920│82t/s│$0.023
        """
    session_color, session_style = CompactLogger._get_session_color(request_id)
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0)) if usage else 0
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0)) if usage else 0
    thinking_tokens = 0
    if usage:
        if 'thinking_tokens' in usage:
            thinking_tokens = usage['thinking_tokens']
        elif 'reasoning_tokens' in usage:
            thinking_tokens = usage['reasoning_tokens']
        elif 'completion_tokens_details' in usage:
            details = usage['completion_tokens_details']
            if isinstance(details, dict):
                thinking_tokens = details.get('reasoning_tokens', 0)
    cost = 0.0
    if model_name:
        cost_map = {'gpt-5': (0.015, 0.06), 'gpt-4o': (0.005, 0.015), 'gpt-4': (0.03, 0.06), 'claude-3.5': (0.003, 0.015), 'claude-3': (0.003, 0.015)}
        for key, (in_cost, out_cost) in cost_map.items():
            if key in model_name.lower():
                cost = input_tokens / 1000000 * in_cost + output_tokens / 1000000 * out_cost
                break
    if RICH_AVAILABLE and console:
        text = Text()
        icon = '🟢' if status == 'OK' else '🔴'
        color = 'green' if status == 'OK' else 'red'
        style = f'{session_style} {session_color}' if session_style else session_color
        text.append(icon, style=f'bold {color}')
        text.append(f'{request_id[:5]}', style=style)
        text.append('│', style='dim')
        if duration_ms:
            text.append(CompactLogger._fmt_duration(duration_ms), style='yellow')
            text.append('│', style='dim')
        text.append(CompactLogger._fmt_tokens(input_tokens), style='cyan')
        text.append('→', style='dim')
        text.append(CompactLogger._fmt_tokens(output_tokens), style='blue')
        if thinking_tokens > 0:
            text.append('💭', style='dim')
            text.append(CompactLogger._fmt_tokens(thinking_tokens), style='magenta')
        text.append('│', style='dim')
        if duration_ms and output_tokens > 0:
            tps = output_tokens / (duration_ms / 1000)
            tps_color = 'green' if tps > 50 else 'yellow' if tps > 20 else 'red'
            text.append(f'{tps:.0f}t/s', style=tps_color)
            text.append('│', style='dim')
        if cost > 0:
            cost_color = 'green' if cost < 0.01 else 'yellow' if cost < 0.1 else 'red'
            text.append(f'${cost:.4f}', style=cost_color)
        console.print(text)
    else:
        rid = request_id[:5]
        icon = '🟢' if status == 'OK' else '🔴'
        parts = [f'{icon}{rid}']
        if duration_ms:
            parts.append(CompactLogger._fmt_duration(duration_ms))
        tokens_str = f'{CompactLogger._fmt_tokens(input_tokens)}→{CompactLogger._fmt_tokens(output_tokens)}'
        if thinking_tokens > 0:
            tokens_str += f'💭{CompactLogger._fmt_tokens(thinking_tokens)}'
        parts.append(tokens_str)
        if duration_ms and output_tokens > 0:
            tps = output_tokens / (duration_ms / 1000)
            parts.append(f'{tps:.0f}t/s')
        if cost > 0:
            parts.append(f'${cost:.4f}')
        logger.info('│'.join(parts))
```

### Method: `log_request_error`
**Logic & Purpose:**
```text
Log error - SINGLE LINE.

Format:
🔴abc12│0.5s│Rate limit exceeded
```

**Parameters:** `request_id, error, duration_ms`
**Variables Used:** `text, error_msg, parts, style`
**Implementation:**
```python
@staticmethod
def log_request_error(request_id: str, error: str, duration_ms: Optional[float]=None) -> None:
    """
        Log error - SINGLE LINE.

        Format:
        🔴abc12│0.5s│Rate limit exceeded
        """
    session_color, session_style = CompactLogger._get_session_color(request_id)
    error_msg = error[:60] + '...' if len(error) > 60 else error
    if RICH_AVAILABLE and console:
        text = Text()
        style = f'{session_style} {session_color}' if session_style else session_color
        text.append('🔴', style='bold red')
        text.append(f'{request_id[:5]}', style=style)
        text.append('│', style='dim')
        if duration_ms:
            text.append(CompactLogger._fmt_duration(duration_ms), style='yellow')
            text.append('│', style='dim')
        text.append(error_msg, style='red')
        console.print(text)
    else:
        parts = [f'🔴{request_id[:5]}']
        if duration_ms:
            parts.append(CompactLogger._fmt_duration(duration_ms))
        parts.append(error_msg)
        logger.error('│'.join(parts))
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/logging/request_logger.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/logging/request_logger.py`

**Module Overview**: 
```text
Compact request logging utility for terminal output.

Provides information-dense, color-coded logging for reasoning requests,
model routing, and token usage in 3-5 lines maximum.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `LOG_STYLE` = `os.environ.get('LOG_STYLE', 'rich').lower()`
- `SHOW_TOKEN_COUNTS` = `os.environ.get('SHOW_TOKEN_COUNTS', 'true').lower() == 'true'`
- `SHOW_PERFORMANCE` = `os.environ.get('SHOW_PERFORMANCE', 'true').lower() == 'true'`
- `COLOR_SCHEME` = `os.environ.get('COLOR_SCHEME', 'auto').lower()`
- `USE_RICH` = `RICH_AVAILABLE and LOG_STYLE == 'rich' and (COLOR_SCHEME != 'none')`
- `request_logger` = `RequestLogger()`

## Dependencies & Imports
logging, os, hashlib, typing.Optional, typing.Dict, typing.Any, datetime.datetime

## Feature Class: `RequestLogger`
**Description:**
```text
Compact request logger for terminal output with color support.
```

### Method: `_get_session_color`
**Logic & Purpose:**
```text
Get a consistent color for a session based on request ID prefix.
```

**Parameters:** `request_id`
**Variables Used:** `color_idx, session_hash`
**Implementation:**
```python
@staticmethod
def _get_session_color(request_id: str) -> str:
    """Get a consistent color for a session based on request ID prefix."""
    session_hash = int(hashlib.md5(request_id[:8].encode()).hexdigest()[:8], 16)
    color_idx = session_hash % len(RequestLogger.SESSION_COLORS)
    return RequestLogger.SESSION_COLORS[color_idx]
```

### Method: `_estimate_tokens`
**Logic & Purpose:**
```text
Estimate token count from text (rough approximation).
```

**Parameters:** `text`
**Implementation:**
```python
@staticmethod
def _estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough approximation)."""
    return max(1, len(text) // 4)
```

### Method: `_count_tokens_precise`
**Logic & Purpose:**
```text
Count tokens precisely using tiktoken if available.
```

**Parameters:** `text, model`
**Variables Used:** `encoding`
**Implementation:**
```python
@staticmethod
def _count_tokens_precise(text: str, model: str='gpt-4') -> int:
    """Count tokens precisely using tiktoken if available."""
    if not TIKTOKEN_AVAILABLE:
        return RequestLogger._estimate_tokens(text)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding('cl100k_base')
    return len(encoding.encode(text))
```

### Method: `log_request_start`
**Logic & Purpose:**
```text
Log request start with ALL comprehensive info on ONE line.

Format (enhanced with all metrics):
[PROJECT] ▶ abc123 | claude-3.5→gpt-4o | CTX:1.2k/200k(1%) OUT:16k THINK:8k | 🧠REASON | STREAM 3msg | 127.0.0.1
```

**Parameters:** `request_id, original_model, routed_model, endpoint, reasoning_config, stream, input_text, context_limit, output_limit, input_tokens, message_count, has_system, has_tools, has_images, client_info, workspace_name`
**Variables Used:** `session_color, think_str, think, task_icon, parts, text, task_color, endpoint_provider, orig_model_str, task_type, routed_model_str, size, ctx_pct, provider, ctx_color, endpoint_name, family`
**Implementation:**
```python
@staticmethod
def log_request_start(request_id: str, original_model: str, routed_model: str, endpoint: str, reasoning_config: Optional[Any]=None, stream: bool=False, input_text: Optional[str]=None, context_limit: int=0, output_limit: int=0, input_tokens: int=0, message_count: int=0, has_system: bool=False, has_tools: bool=False, has_images: bool=False, client_info: Optional[str]=None, workspace_name: Optional[str]=None) -> None:
    """
        Log request start with ALL comprehensive info on ONE line.

        Format (enhanced with all metrics):
        [PROJECT] ▶ abc123 | claude-3.5→gpt-4o | CTX:1.2k/200k(1%) OUT:16k THINK:8k | 🧠REASON | STREAM 3msg | 127.0.0.1
        """

    def get_provider_info(model_name: str) -> tuple[str, str, str]:
        """Extract provider, model family, and size from model name."""
        if 'claude' in model_name.lower():
            provider = 'anthropic'
            if '3.5' in model_name:
                family = 'claude-3.5'
                size = 'sonnet' if 'sonnet' in model_name else 'haiku' if 'haiku' in model_name else 'opus' if 'opus' in model_name else 'unknown'
            elif '3' in model_name:
                family = 'claude-3'
                size = 'sonnet' if 'sonnet' in model_name else 'haiku' if 'haiku' in model_name else 'opus' if 'opus' in model_name else 'unknown'
            else:
                family = 'claude'
                size = 'unknown'
        elif 'gpt' in model_name.lower() or 'o1' in model_name.lower():
            provider = 'openai'
            if 'gpt-4o' in model_name:
                family = 'gpt-4o'
                size = 'mini' if 'mini' in model_name else 'standard'
            elif 'gpt-4' in model_name:
                family = 'gpt-4'
                size = 'turbo' if 'turbo' in model_name else 'standard'
            elif 'o1' in model_name:
                family = 'o1'
                size = 'mini' if 'mini' in model_name else 'preview' if 'preview' in model_name else 'standard'
            else:
                family = 'gpt'
                size = 'unknown'
        elif 'gemini' in model_name.lower():
            provider = 'google'
            family = 'gemini'
            size = 'pro' if 'pro' in model_name else 'flash' if 'flash' in model_name else 'unknown'
        else:
            provider = 'unknown'
            family = model_name.split('/')[-1] if '/' in model_name else model_name
            size = 'unknown'
        return (provider, family, size)
    endpoint_name = endpoint.replace('https://', '').replace('http://', '').split('/')[0]
    endpoint_provider = 'openrouter' if 'openrouter' in endpoint_name else 'openai' if 'openai' in endpoint_name else 'anthropic' if 'anthropic' in endpoint_name else endpoint_name
    orig_provider, orig_family, orig_size = get_provider_info(original_model)
    routed_provider, routed_family, routed_size = get_provider_info(routed_model)

    def fmt_tokens(count):
        return f'{count / 1000:.1f}k' if count >= 1000 else str(count)
    task_type = 'TEXT'
    task_icon = '📝'
    task_color = 'white'
    if reasoning_config:
        task_type = 'REASON'
        task_icon = '🧠'
        task_color = 'magenta'
    elif has_images:
        task_type = 'IMAGE'
        task_icon = '🖼️ '
        task_color = 'cyan'
    elif has_tools:
        task_type = 'TOOLS'
        task_icon = '🔧'
        task_color = 'yellow'
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        text = Text()
        if workspace_name:
            text.append(f' {workspace_name} ', style=f'bold white on {session_color}')
            text.append('  ', style='')
        text.append('▶ ', style=f'bold {session_color}')
        text.append(f'{request_id[:8]} ', style=f'bold {session_color}')
        text.append('| ', style=f'dim')
        text.append(f'{orig_family}', style=f'dim {session_color}')
        if orig_size != 'unknown':
            text.append(f'-{orig_size}', style=f'dim {session_color}')
        text.append('→', style=f'dim')
        text.append(f'{routed_family}', style=f'bold {session_color}')
        if routed_size != 'unknown':
            text.append(f'-{routed_size}', style=f'bold {session_color}')
        text.append(' | ', style=f'dim')
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = input_tokens / context_limit * 100
            ctx_color = 'green' if ctx_pct < 50 else 'yellow' if ctx_pct < 80 else 'red'
            text.append('CTX:', style='dim')
            text.append(f'{fmt_tokens(input_tokens)}', style=ctx_color)
            text.append(f'/{fmt_tokens(context_limit)}', style='dim')
            text.append(f'({ctx_pct:.0f}%) ', style=ctx_color)
        elif input_tokens > 0:
            text.append(f'IN:{fmt_tokens(input_tokens)} ', style=f'cyan')
        if output_limit > 0:
            text.append('OUT:', style='dim')
            text.append(f'{fmt_tokens(output_limit)} ', style='blue')
        if reasoning_config:
            from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
            if isinstance(reasoning_config, OpenAIReasoningConfig):
                think_str = fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
            elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                think_str = fmt_tokens(reasoning_config.budget)
            else:
                think_str = '?'
            text.append('THINK:', style='dim')
            text.append(f'{think_str} ', style='magenta bold')
        text.append('| ', style='dim')
        text.append(f'{task_icon} ', style=task_color)
        text.append(f'{task_type} ', style=f'bold {task_color}')
        if stream:
            text.append('STREAM ', style=f'bold {session_color}')
        if message_count > 0:
            text.append(f'{message_count}msg ', style=f'dim')
        if has_system:
            text.append('SYS ', style='dim')
        console.print(text)
    else:
        parts = [f'🔵 {request_id[:6]}']
        orig_model_str = f'{orig_provider}/{orig_family}'
        if orig_size != 'unknown':
            orig_model_str += f'-{orig_size}'
        routed_model_str = f'{routed_provider}/{routed_family}'
        if routed_size != 'unknown':
            routed_model_str += f'-{routed_size}'
        parts.append(f'{orig_model_str}→{routed_model_str}')
        parts.append(f'@{endpoint_provider}')
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = input_tokens / context_limit * 100
            parts.append(f'CTX:{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ({ctx_pct:.0f}%)')
        elif input_tokens > 0:
            parts.append(f'CTX:{fmt_tokens(input_tokens)}')
        if output_limit > 0:
            parts.append(f'OUT:{fmt_tokens(output_limit)}')
        if reasoning_config:
            from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
            if isinstance(reasoning_config, OpenAIReasoningConfig):
                think = fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
                parts.append(f'THINK:{think}')
            elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                parts.append(f'THINK:{fmt_tokens(reasoning_config.budget)}')
        if stream:
            parts.append('STREAM')
        if message_count > 0:
            parts.append(f'{message_count}msg')
        if has_system:
            parts.append('SYS')
        if client_info:
            parts.append(client_info)
        logger.info(' | '.join(parts))
```

### Method: `log_request_complete`
**Logic & Purpose:**
```text
Log request completion with ALL available info on ONE comprehensive line.

Format (1 line with colors):
🟢 abc123 15.8s | CTX:43.7k/1840.0k (2%) | OUT:1.3k/64.0k | THINK:920 | 81t/s | 📤 OUTPUT: [░░░░░░░░░░░░░░░░░░░░] 1.3k/64.0k (2%) 🟣 THINKING: [░░░░░░░░░░░░░░░░░░░░] 920/64.0k (1%) | STREAM | 3msg | SYS | 127.0.0.1
```

**Parameters:** `request_id, usage, duration_ms, status, model_name, stream, message_count, has_system, has_reasoning, client_info`
**Variables Used:** `output_tokens, ctx_color, icon_color, out_pct, text, cost_map, context_limit, ctx_pct, session_color, details, input_tokens, cost, tok_s, icon, duration_color, thinking_tokens, out_color, output_limit, speed_color, cost_color, parts`
**Implementation:**
```python
@staticmethod
def log_request_complete(request_id: str, usage: Optional[Dict[str, Any]]=None, duration_ms: Optional[float]=None, status: str='OK', model_name: Optional[str]=None, stream: bool=False, message_count: int=0, has_system: bool=False, has_reasoning: bool=False, client_info: Optional[str]=None) -> None:
    """
        Log request completion with ALL available info on ONE comprehensive line.
        
        Format (1 line with colors):
        🟢 abc123 15.8s | CTX:43.7k/1840.0k (2%) | OUT:1.3k/64.0k | THINK:920 | 81t/s | 📤 OUTPUT: [░░░░░░░░░░░░░░░░░░░░] 1.3k/64.0k (2%) 🟣 THINKING: [░░░░░░░░░░░░░░░░░░░░] 920/64.0k (1%) | STREAM | 3msg | SYS | 127.0.0.1
        """

    def format_tokens(count):
        """Format token count compactly."""
        if count >= 1000:
            return f'{count / 1000:.1f}k'
        else:
            return str(count)
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0)) if usage else 0
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0)) if usage else 0
    thinking_tokens = 0
    if usage:
        if 'thinking_tokens' in usage:
            thinking_tokens = usage['thinking_tokens']
        elif 'reasoning_tokens' in usage:
            thinking_tokens = usage['reasoning_tokens']
        elif 'completion_tokens_details' in usage:
            details = usage['completion_tokens_details']
            if isinstance(details, dict):
                thinking_tokens = details.get('reasoning_tokens', 0)
    from src.services.usage.model_limits import get_model_limits
    context_limit = 0
    output_limit = 0
    if model_name:
        context_limit, output_limit = get_model_limits(model_name)
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        text = Text()
        icon = '✓' if status == 'OK' else '✗'
        icon_color = 'green' if status == 'OK' else 'red'
        text.append(f'  {icon} ', style=f'bold {icon_color}')
        text.append(f'{request_id[:8]} ', style=f'bold {session_color}')
        text.append('| ', style=f'dim')
        if duration_ms:
            duration_color = 'green' if duration_ms < 3000 else 'yellow' if duration_ms < 10000 else 'red'
            text.append(f'{duration_ms / 1000:.1f}s ', style=duration_color)
            text.append('| ', style='dim')
        if usage:
            text.append('IN:', style='dim')
            text.append(f'{format_tokens(input_tokens)} ', style='cyan')
            if context_limit > 0:
                ctx_pct = input_tokens / context_limit * 100
                ctx_color = 'green' if ctx_pct < 50 else 'yellow' if ctx_pct < 80 else 'red'
                text.append(f'({ctx_pct:.0f}%) ', style=ctx_color)
            text.append('OUT:', style='dim')
            text.append(f'{format_tokens(output_tokens)} ', style='bold blue')
            if output_limit > 0 and output_tokens > 0:
                out_pct = output_tokens / output_limit * 100
                out_color = 'green' if out_pct < 50 else 'yellow' if out_pct < 80 else 'red'
                text.append(f'({out_pct:.0f}%) ', style=out_color)
            if thinking_tokens > 0:
                text.append('THINK:', style='dim')
                text.append(f'{format_tokens(thinking_tokens)} ', style='bold magenta')
            text.append('| ', style='dim')
        if output_tokens > 0 and duration_ms:
            tok_s = output_tokens / (duration_ms / 1000)
            speed_color = 'green' if tok_s > 50 else 'yellow' if tok_s > 20 else 'red'
            text.append('⚡', style=speed_color)
            text.append(f'{tok_s:.0f}t/s ', style=f'bold {speed_color}')
        if usage and model_name:
            cost = 0.0
            cost_map = {'gpt-4o': (0.005, 0.015), 'gpt-4': (0.03, 0.06), 'claude-3.5': (0.003, 0.015), 'claude-3': (0.003, 0.015)}
            for key, (in_cost, out_cost) in cost_map.items():
                if key in model_name.lower():
                    cost = input_tokens / 1000000 * in_cost + output_tokens / 1000000 * out_cost
                    break
            if cost > 0:
                cost_color = 'green' if cost < 0.01 else 'yellow' if cost < 0.1 else 'red'
                text.append('$', style='dim')
                text.append(f'{cost:.4f}', style=cost_color)
        console.print(text)
    else:
        icon = '🟢' if status == 'OK' else '🔴'
        parts = [f'{icon} {request_id[:6]}']
        if duration_ms:
            parts.append(f'{duration_ms / 1000:.1f}s')
        if usage:
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = input_tokens / context_limit * 100
                parts.append(f'CTX:{format_tokens(input_tokens)}/{format_tokens(context_limit)} ({ctx_pct:.0f}%)')
            else:
                parts.append(f'CTX:{format_tokens(input_tokens)}')
            if output_limit > 0:
                out_pct = output_tokens / output_limit * 100 if output_tokens > 0 else 0
                parts.append(f'OUT:{format_tokens(output_tokens)}/{format_tokens(output_limit)}')
            else:
                parts.append(f'OUT:{format_tokens(output_tokens)}')
            if thinking_tokens > 0:
                parts.append(f'THINK:{format_tokens(thinking_tokens)}')
        if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
            tok_s = output_tokens / (duration_ms / 1000)
            parts.append(f'{tok_s:.0f}t/s')
        if stream:
            parts.append('STREAM')
        if message_count > 0:
            parts.append(f'{message_count}msg')
        if has_system:
            parts.append('SYS')
        if client_info:
            parts.append(client_info)
        logger.info(' | '.join(parts))
```

### Method: `log_request_error`
**Logic & Purpose:**
```text
Log request error.

Format (1 line with color):
🔴 REQ abc123 | ERROR | 0.5s | Rate limit exceeded
```

**Parameters:** `request_id, error, duration_ms`
**Variables Used:** `error_text, session_color, error_msg, error_info`
**Implementation:**
```python
@staticmethod
def log_request_error(request_id: str, error: str, duration_ms: Optional[float]=None) -> None:
    """
        Log request error.
        
        Format (1 line with color):
        🔴 REQ abc123 | ERROR | 0.5s | Rate limit exceeded
        """
    error_msg = str(error)
    if len(error_msg) > 80:
        error_msg = error_msg[:77] + '...'
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        error_text = Text()
        error_text.append('  ✗ ', style='bold red')
        error_text.append(f'{request_id[:8]} ', style=f'bold {session_color}')
        error_text.append('| ', style='dim')
        if duration_ms:
            error_text.append(f'{duration_ms / 1000:.1f}s ', style='yellow')
            error_text.append('| ', style='dim')
        error_text.append(error_msg, style='red')
        console.print(error_text)
    else:
        error_info = f'  ✗ {request_id[:8]} | ERROR'
        if duration_ms:
            error_info += f' | {duration_ms / 1000:.1f}s'
        error_info += f' | {error_msg}'
        logger.error(error_info)
```

### Method: `_create_progress_bar`
**Logic & Purpose:**
```text
Create an ASCII progress bar.

Args:
    used: Used amount
    total: Total capacity
    width: Width of the bar in characters
    filled_char: Character for filled portion
    empty_char: Character for empty portion
    
Returns:
    ASCII progress bar string
```

**Parameters:** `used, total, width, filled_char, empty_char`
**Variables Used:** `empty_width, filled_width, percentage`
**Implementation:**
```python
@staticmethod
def _create_progress_bar(used: int, total: int, width: int=20, filled_char: str='█', empty_char: str='░') -> str:
    """
        Create an ASCII progress bar.
        
        Args:
            used: Used amount
            total: Total capacity
            width: Width of the bar in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            ASCII progress bar string
        """
    if total == 0:
        return empty_char * width
    percentage = min(used / total, 1.0)
    filled_width = int(width * percentage)
    empty_width = width - filled_width
    return filled_char * filled_width + empty_char * empty_width
```

### Method: `_get_bar_color`
**Logic & Purpose:**
```text
Get color style based on usage percentage.
```

**Parameters:** `percentage`
**Implementation:**
```python
@staticmethod
def _get_bar_color(percentage: float) -> str:
    """Get color style based on usage percentage."""
    if percentage < 0.5:
        return 'green'
    elif percentage < 0.8:
        return 'yellow'
    else:
        return 'red'
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/logging/log_cleanup.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/logging/log_cleanup.py`

**Module Overview**: 
```text
Automatic log cleanup for Claude Code Proxy.

Removes log files older than retention period and enforces size limits.
Before cleanup, aggregates analytics data into compact summary format.

Usage:
    python -m src.services.logging.log_cleanup
    # Or with custom settings:
    LOG_RETENTION_DAYS=3 LOG_MAX_SIZE_MB=200 python -m src.services.logging.log_cleanup

Cron example (daily at 3 AM):
    0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup
```

## Dependencies & Imports
os, sys, json, time, datetime.datetime, datetime.timedelta, pathlib.Path, typing.Tuple, typing.Dict, typing.Any, typing.List, collections.defaultdict

## Feature Function: `aggregate_analytics_data`
**Logic & Purpose:**
```text
Aggregate analytics data from JSONL files before cleanup.

Reads tool_analytics.jsonl and cache_analytics.jsonl,
computes summary statistics, and returns compact metadata.

Returns a dictionary with:
- timestamp: When aggregation was performed
- period_start: Start of aggregation period
- period_end: End of aggregation period
- tool_calls: Aggregated tool call statistics
- cache_usage: Aggregated cache statistics
- sessions: Unique session count
- summary: One-line human-readable summary
```

**Parameters:** `logs_dir`
**Variables Used:** `tool_file, data, timestamp, cache_file, session_count, summary`
**Implementation:**
```python
def aggregate_analytics_data(logs_dir: Path) -> Dict[str, Any]:
    """
    Aggregate analytics data from JSONL files before cleanup.
    
    Reads tool_analytics.jsonl and cache_analytics.jsonl,
    computes summary statistics, and returns compact metadata.
    
    Returns a dictionary with:
    - timestamp: When aggregation was performed
    - period_start: Start of aggregation period
    - period_end: End of aggregation period
    - tool_calls: Aggregated tool call statistics
    - cache_usage: Aggregated cache statistics
    - sessions: Unique session count
    - summary: One-line human-readable summary
    """
    summary = {'timestamp': datetime.utcnow().isoformat() + 'Z', 'period_start': None, 'period_end': None, 'tool_calls': {'total': 0, 'success': 0, 'failure': 0, 'by_tool': defaultdict(lambda: {'success': 0, 'failure': 0}), 'success_rate': 0}, 'cache_usage': {'total_requests': 0, 'hits': 0, 'misses': 0, 'cached_tokens': 0, 'total_tokens': 0, 'hit_rate': 0, 'token_savings_percent': 0}, 'sessions': set(), 'summary': ''}
    tool_file = logs_dir / 'tool_analytics.jsonl'
    if tool_file.exists():
        try:
            with open(tool_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        timestamp = data.get('timestamp', '')
                        if summary['period_start'] is None or timestamp < summary['period_start']:
                            summary['period_start'] = timestamp
                        if summary['period_end'] is None or timestamp > summary['period_end']:
                            summary['period_end'] = timestamp
                        summary['tool_calls']['total'] += 1
                        if data.get('success', True):
                            summary['tool_calls']['success'] += 1
                            summary['tool_calls']['by_tool'][data.get('tool_name', 'unknown')]['success'] += 1
                        else:
                            summary['tool_calls']['failure'] += 1
                            summary['tool_calls']['by_tool'][data.get('tool_name', 'unknown')]['failure'] += 1
                        if data.get('session_id'):
                            summary['sessions'].add(data['session_id'])
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f'   ⚠️  Error reading tool analytics: {e}')
    if summary['tool_calls']['total'] > 0:
        summary['tool_calls']['success_rate'] = round(summary['tool_calls']['success'] / summary['tool_calls']['total'] * 100, 1)
    cache_file = logs_dir / 'cache_analytics.jsonl'
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        timestamp = data.get('timestamp', '')
                        if summary['period_start'] is None or timestamp < summary['period_start']:
                            summary['period_start'] = timestamp
                        if summary['period_end'] is None or timestamp > summary['period_end']:
                            summary['period_end'] = timestamp
                        summary['cache_usage']['total_requests'] += 1
                        if data.get('cache_hit', False):
                            summary['cache_usage']['hits'] += 1
                            summary['cache_usage']['cached_tokens'] += data.get('cached_tokens', 0)
                        else:
                            summary['cache_usage']['misses'] += 1
                        summary['cache_usage']['total_tokens'] += data.get('total_tokens', 0)
                        if data.get('session_id'):
                            summary['sessions'].add(data['session_id'])
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f'   ⚠️  Error reading cache analytics: {e}')
    if summary['cache_usage']['total_requests'] > 0:
        summary['cache_usage']['hit_rate'] = round(summary['cache_usage']['hits'] / summary['cache_usage']['total_requests'] * 100, 1)
    if summary['cache_usage']['total_tokens'] > 0:
        summary['cache_usage']['token_savings_percent'] = round(summary['cache_usage']['cached_tokens'] / summary['cache_usage']['total_tokens'] * 100, 1)
    session_count = len(summary['sessions'])
    summary['sessions'] = session_count
    summary['tool_calls']['by_tool'] = dict(summary['tool_calls']['by_tool'])
    summary['summary'] = f"Period: {summary['period_start'] or 'N/A'} to {summary['period_end'] or 'N/A'} | Tools: {summary['tool_calls']['total']} calls ({summary['tool_calls']['success_rate']}% success) | Cache: {summary['cache_usage']['hit_rate']}% hit rate ({summary['cache_usage']['cached_tokens']:,} tokens) | Sessions: {session_count}"
    return summary
```

---

## Feature Function: `save_aggregated_summary`
**Logic & Purpose:**
```text
Save aggregated summary to metrics_history.jsonl.

This file contains one line per cleanup cycle with compact statistics.
Raw analytics files can then be safely deleted.

Args:
    logs_dir: Directory containing log files
    summary: Aggregated summary dictionary
    dry_run: If True, don't actually write

Returns:
    True if successful, False otherwise
```

**Parameters:** `logs_dir, summary, dry_run`
**Variables Used:** `history_file`
**Implementation:**
```python
def save_aggregated_summary(logs_dir: Path, summary: Dict[str, Any], dry_run: bool=False) -> bool:
    """
    Save aggregated summary to metrics_history.jsonl.
    
    This file contains one line per cleanup cycle with compact statistics.
    Raw analytics files can then be safely deleted.
    
    Args:
        logs_dir: Directory containing log files
        summary: Aggregated summary dictionary
        dry_run: If True, don't actually write
    
    Returns:
        True if successful, False otherwise
    """
    history_file = logs_dir / 'metrics_history.jsonl'
    if dry_run:
        print(f'   Would save summary to: {history_file}')
        print(f"   Summary: {summary['summary']}")
        return True
    try:
        with open(history_file, 'a') as f:
            f.write(json.dumps(summary) + '\n')
        print(f'   ✅ Saved aggregated metrics to: {history_file.name}')
        return True
    except Exception as e:
        print(f'   ❌ Failed to save summary: {e}')
        return False
```

---

## Feature Function: `get_file_age_days`
**Logic & Purpose:**
```text
Get file age in days based on modification time.
```

**Parameters:** `file_path`
**Variables Used:** `mtime`
**Implementation:**
```python
def get_file_age_days(file_path: Path) -> int:
    """Get file age in days based on modification time."""
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return (datetime.now() - mtime).days
```

---

## Feature Function: `get_file_size_mb`
**Logic & Purpose:**
```text
Get file size in MB.
```

**Parameters:** `file_path`
**Implementation:**
```python
def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)
```

---

## Feature Function: `cleanup_logs`
**Logic & Purpose:**
```text
Clean up old log files and enforce size limits.

Before cleanup, aggregates analytics data into compact summary format.

Args:
    logs_dir: Directory containing log files. Defaults to 'logs/' in project root.
    retention_days: Remove files older than this. Defaults to LOG_RETENTION_DAYS or 7.
    max_size_mb: Maximum total log size in MB. Defaults to LOG_MAX_SIZE_MB or 500.
    dry_run: If True, only report what would be removed.
    aggregate_before_cleanup: If True, aggregate analytics before deleting (default: True).

Returns:
    Tuple of (files_removed, total_size_freed_mb)
```

**Parameters:** `logs_dir, retention_days, max_size_mb, dry_run, aggregate_before_cleanup`
**Variables Used:** `action, log_files, age_days, freed_mb, total_size_mb, size_mb, removed_count, size_freed, max_size_mb, logs_dir, has_analytics, history_size, history_lines, history_file, analytics_files, summary, log_files_sorted, retention_days`
**Implementation:**
```python
def cleanup_logs(logs_dir: str=None, retention_days: int=None, max_size_mb: int=None, dry_run: bool=False, aggregate_before_cleanup: bool=True) -> Tuple[int, float]:
    """
    Clean up old log files and enforce size limits.
    
    Before cleanup, aggregates analytics data into compact summary format.
    
    Args:
        logs_dir: Directory containing log files. Defaults to 'logs/' in project root.
        retention_days: Remove files older than this. Defaults to LOG_RETENTION_DAYS or 7.
        max_size_mb: Maximum total log size in MB. Defaults to LOG_MAX_SIZE_MB or 500.
        dry_run: If True, only report what would be removed.
        aggregate_before_cleanup: If True, aggregate analytics before deleting (default: True).
    
    Returns:
        Tuple of (files_removed, total_size_freed_mb)
    """
    logs_dir = Path(logs_dir or os.getenv('LOGS_DIR', 'logs'))
    retention_days = int(retention_days or os.getenv('LOG_RETENTION_DAYS', '7'))
    max_size_mb = int(max_size_mb or os.getenv('LOG_MAX_SIZE_MB', '500'))
    if not logs_dir.exists():
        print(f'ℹ️  Logs directory does not exist: {logs_dir}')
        return (0, 0.0)
    print(f'🧹 Starting log cleanup')
    print(f'   Directory: {logs_dir.absolute()}')
    print(f'   Retention: {retention_days} days')
    print(f'   Max size: {max_size_mb} MB')
    print()
    if aggregate_before_cleanup:
        print(f'📊 Step 1: Aggregating analytics data...')
        analytics_files = ['tool_analytics.jsonl', 'cache_analytics.jsonl']
        has_analytics = any(((logs_dir / f).exists() for f in analytics_files))
        if has_analytics:
            summary = aggregate_analytics_data(logs_dir)
            if summary['period_start']:
                save_aggregated_summary(logs_dir, summary, dry_run)
            else:
                print(f'   ℹ️  No analytics data to aggregate')
        else:
            print(f'   ℹ️  No analytics files found')
        print()
    log_files = list(logs_dir.glob('*.log')) + list(logs_dir.glob('*.jsonl'))
    log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
    if not log_files:
        print('✅ No log files to clean up')
        return (0, 0.0)
    total_size_mb = sum((get_file_size_mb(f) for f in log_files))
    print(f'📊 Current state:')
    print(f'   Files: {len(log_files)}')
    print(f'   Total size: {total_size_mb:.1f} MB')
    print()
    print(f'📅 Phase 1: Removing files older than {retention_days} days...')
    removed_count = 0
    freed_mb = 0.0
    for log_file in sorted(log_files):
        age_days = get_file_age_days(log_file)
        if age_days > retention_days:
            size_mb = get_file_size_mb(log_file)
            action = 'Would remove' if dry_run else 'Removing'
            print(f'   {action}: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)')
            if not dry_run:
                log_file.unlink()
            removed_count += 1
            freed_mb += size_mb
    if removed_count == 0:
        print(f'   ✅ No files exceeded retention period')
    else:
        action = 'Would remove' if dry_run else 'Removed'
        print(f'   ✅ {action} {removed_count} files ({freed_mb:.1f} MB)')
    print()
    if removed_count > 0 and (not dry_run):
        log_files = list(logs_dir.glob('*.log')) + list(logs_dir.glob('*.jsonl'))
        log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
        total_size_mb = sum((get_file_size_mb(f) for f in log_files))
    print(f'💾 Phase 2: Enforcing {max_size_mb} MB size limit...')
    if total_size_mb <= max_size_mb:
        print(f'   ✅ Total size ({total_size_mb:.1f} MB) is within limit')
    else:
        print(f'   ⚠️  Total size ({total_size_mb:.1f} MB) exceeds limit')
        print(f'   Removing oldest files until under {max_size_mb} MB...')
        log_files_sorted = sorted(log_files, key=lambda f: f.stat().st_mtime)
        size_freed = 0.0
        for log_file in log_files_sorted:
            if total_size_mb - size_freed <= max_size_mb:
                break
            size_mb = get_file_size_mb(log_file)
            age_days = get_file_age_days(log_file)
            action = 'Would remove' if dry_run else 'Removing'
            print(f'   {action}: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)')
            if not dry_run:
                log_file.unlink()
            removed_count += 1
            size_freed += size_mb
        print(f'   ✅ Freed {size_freed:.1f} MB')
        freed_mb += size_freed
    print()
    if not dry_run:
        log_files = list(logs_dir.glob('*.log')) + list(logs_dir.glob('*.jsonl'))
        log_files = [f for f in log_files if f.name != 'metrics_history.jsonl']
        total_size_mb = sum((get_file_size_mb(f) for f in log_files))
    print(f'📊 Final state:')
    print(f'   Files: {len(log_files)}')
    print(f'   Total size: {total_size_mb:.1f} MB')
    history_file = logs_dir / 'metrics_history.jsonl'
    if history_file.exists():
        history_size = get_file_size_mb(history_file)
        history_lines = sum((1 for _ in open(history_file)))
        print(f'   Metrics history: {history_lines} snapshots ({history_size:.2f} MB)')
    print()
    if dry_run:
        print(f'🔍 DRY RUN - No files actually removed')
        print(f'   Would remove {removed_count} files')
        print(f'   Would free {freed_mb:.1f} MB')
    else:
        print(f'✅ Cleanup complete')
        print(f'   Removed {removed_count} files')
        print(f'   Freed {freed_mb:.1f} MB')
    return (removed_count, freed_mb)
```

---

## Feature Function: `cleanup_old_forensic_logs`
**Logic & Purpose:**
```text
Clean up forensic log files older than specified days.

Forensic logs are named like: forensic_YYYYMMDD_HHMMSS.log

Args:
    logs_dir: Directory containing log files
    max_age_days: Remove forensic logs older than this
```

**Parameters:** `logs_dir, max_age_days`
**Variables Used:** `removed, age_days, logs_dir, size_mb`
**Implementation:**
```python
def cleanup_old_forensic_logs(logs_dir: str=None, max_age_days: int=3):
    """
    Clean up forensic log files older than specified days.
    
    Forensic logs are named like: forensic_YYYYMMDD_HHMMSS.log
    
    Args:
        logs_dir: Directory containing log files
        max_age_days: Remove forensic logs older than this
    """
    logs_dir = Path(logs_dir or os.getenv('LOGS_DIR', 'logs'))
    if not logs_dir.exists():
        return 0
    print(f'🧹 Cleaning up forensic logs older than {max_age_days} days...')
    removed = 0
    for log_file in logs_dir.glob('forensic_*.log'):
        age_days = get_file_age_days(log_file)
        if age_days > max_age_days:
            size_mb = get_file_size_mb(log_file)
            print(f'   Removing: {log_file.name} (age: {age_days}d, size: {size_mb:.1f}MB)')
            log_file.unlink()
            removed += 1
    if removed == 0:
        print(f'   ✅ No old forensic logs found')
    else:
        print(f'   ✅ Removed {removed} forensic log(s)')
    return removed
```

---

## Feature Function: `view_metrics_history`
**Logic & Purpose:**
```text
View recent entries from metrics history.

Args:
    logs_dir: Directory containing log files
    limit: Number of entries to show
```

**Parameters:** `logs_dir, limit`
**Variables Used:** `data, tool_calls, lines, cache, logs_dir, history_file`
**Implementation:**
```python
def view_metrics_history(logs_dir: str=None, limit: int=10):
    """
    View recent entries from metrics history.
    
    Args:
        logs_dir: Directory containing log files
        limit: Number of entries to show
    """
    logs_dir = Path(logs_dir or os.getenv('LOGS_DIR', 'logs'))
    history_file = logs_dir / 'metrics_history.jsonl'
    if not history_file.exists():
        print('ℹ️  No metrics history available yet')
        return
    print(f'📊 Recent Metrics History (last {limit} entries):')
    print('=' * 80)
    try:
        with open(history_file, 'r') as f:
            lines = f.readlines()
        for line in lines[-limit:]:
            data = json.loads(line.strip())
            print(f"\n📅 {data.get('timestamp', 'Unknown')[:10]}")
            print(f"   Period: {data.get('period_start', 'N/A')[:10]} to {data.get('period_end', 'N/A')[:10]}")
            print(f"   {data.get('summary', 'No summary')}")
            tool_calls = data.get('tool_calls', {})
            cache = data.get('cache_usage', {})
            print(f"   Tools: {tool_calls.get('total', 0)} calls, {tool_calls.get('success_rate', 0)}% success")
            print(f"   Cache: {cache.get('hit_rate', 0)}% hit rate, {cache.get('cached_tokens', 0):,} tokens saved")
            print(f"   Sessions: {data.get('sessions', 0)} unique")
    except Exception as e:
        print(f'❌ Error reading history: {e}')
```

---

## Feature Function: `main`
**Logic & Purpose:**
```text
Main entry point for CLI usage.
```

**Parameters:** ``
**Variables Used:** `args, parser`
**Implementation:**
```python
def main():
    """Main entry point for CLI usage."""
    import argparse
    parser = argparse.ArgumentParser(description='Clean up old log files and enforce size limits', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  # Run cleanup with default settings\n  python -m src.services.logging.log_cleanup\n  \n  # Dry run (see what would be removed)\n  python -m src.services.logging.log_cleanup --dry-run\n  \n  # Custom retention (3 days)\n  LOG_RETENTION_DAYS=3 python -m src.services.logging.log_cleanup\n  \n  # Custom size limit (200 MB)\n  LOG_MAX_SIZE_MB=200 python -m src.services.logging.log_cleanup\n  \n  # Custom logs directory\n  LOGS_DIR=/var/log/claude-proxy python -m src.services.logging.log_cleanup\n  \n  # View metrics history\n  python -m src.services.logging.log_cleanup --view-history\n\nCron setup (daily at 3 AM):\n  0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup\n        ')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without actually removing')
    parser.add_argument('--retention-days', type=int, default=None, help='Override retention period (days)')
    parser.add_argument('--max-size-mb', type=int, default=None, help='Override maximum total size (MB)')
    parser.add_argument('--logs-dir', type=str, default=None, help='Override logs directory path')
    parser.add_argument('--clean-forensic', action='store_true', help='Also clean up old forensic logs')
    parser.add_argument('--no-aggregate', action='store_true', help='Skip aggregation step (faster, but loses analytics data)')
    parser.add_argument('--view-history', action='store_true', help='View recent metrics history instead of cleaning')
    parser.add_argument('--history-limit', type=int, default=10, help='Number of history entries to show (default: 10)')
    args = parser.parse_args()
    if args.view_history:
        view_metrics_history(logs_dir=args.logs_dir, limit=args.history_limit)
        sys.exit(0)
    removed, freed = cleanup_logs(logs_dir=args.logs_dir, retention_days=args.retention_days, max_size_mb=args.max_size_mb, dry_run=args.dry_run, aggregate_before_cleanup=not args.no_aggregate)
    if args.clean_forensic:
        print()
        cleanup_old_forensic_logs(logs_dir=args.logs_dir)
    sys.exit(0)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/logging/structured_logger.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/logging/structured_logger.py`

**Module Overview**: 
```text
Structured logging system for Claude Code Proxy.

Provides tiered logging with automatic rotation, structured JSON output,
and sensitive data redaction.

Tiers:
- production: Errors only, 10MB files, 7-day retention (~5MB/day)
- debug: All requests, 50MB files, 3-day retention (~20MB/day)
- forensic: Full payloads, manual cleanup (~100MB/day)

Usage:
    from src.services.logging.structured_logger import get_logger
    logger = get_logger()
    logger.log_request(request_id, {...})
```

## Dependencies & Imports
json, logging, os, sys, datetime.datetime, datetime.timedelta, logging.handlers.RotatingFileHandler, logging.handlers.TimedRotatingFileHandler, pathlib.Path, typing.Any, typing.Dict, typing.Optional

## Feature Class: `JsonFormatter`
**Description:**
```text
JSON formatter for structured logging.
```

### Method: `format`
**Parameters:** `self, record`
**Variables Used:** `value, log_data, extra_fields`
**Implementation:**
```python
def format(self, record: logging.LogRecord) -> str:
    log_data = {'timestamp': datetime.utcnow().isoformat() + 'Z', 'level': record.levelname, 'logger': record.name, 'message': record.getMessage()}
    extra_fields = ['request_id', 'model', 'endpoint', 'duration_ms', 'input_tokens', 'output_tokens', 'tool_calls', 'status', 'error_type', 'session_id', 'provider']
    for field in extra_fields:
        if hasattr(record, field):
            value = getattr(record, field)
            if isinstance(value, (set, frozenset)):
                value = list(value)
            elif hasattr(value, '__dict__'):
                value = str(value)
            log_data[field] = value
    return json.dumps(log_data, default=str)
```

---

## Feature Class: `DetailedFormatter`
**Description:**
```text
Detailed human-readable formatter for forensic mode.
```

### Method: `format`
**Parameters:** `self, record`
**Variables Used:** `timestamp, extra, parts`
**Implementation:**
```python
def format(self, record: logging.LogRecord) -> str:
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    parts = [f'{timestamp} | {record.levelname:<8} | {record.name}']
    if hasattr(record, 'request_id'):
        parts.append(f'| req:{record.request_id[:8]}')
    if hasattr(record, 'model'):
        parts.append(f'| model:{record.model}')
    parts.append(f'| {record.getMessage()}')
    if hasattr(record, 'extra_data') and record.extra_data:
        extra = record.extra_data
        if len(extra) > 500:
            extra = extra[:500] + '...'
        parts.append(f'| {extra}')
    return ' '.join(parts)
```

---

## Feature Class: `StructuredLogger`
**Description:**
```text
Production-ready logger with tiered verbosity and automatic rotation.

Features:
- Automatic file rotation (size + time based)
- Structured JSON logging for easy parsing
- Tiered verbosity (production/debug/forensic)
- Request tracing with correlation IDs
- Sensitive data redaction
- Tool call flow tracking
```

### Method: `__init__`
**Logic & Purpose:**
```text
Initialize structured logger.

Args:
    tier: Logging tier (production, debug, forensic). 
          Defaults to LOG_TIER env var or 'production'.
    logs_dir: Directory for log files. 
             Defaults to LOGS_DIR env var or 'logs/'.
```

**Parameters:** `self, tier, logs_dir`
**Implementation:**
```python
def __init__(self, tier: Optional[str]=None, logs_dir: Optional[str]=None):
    """
        Initialize structured logger.
        
        Args:
            tier: Logging tier (production, debug, forensic). 
                  Defaults to LOG_TIER env var or 'production'.
            logs_dir: Directory for log files. 
                     Defaults to LOGS_DIR env var or 'logs/'.
        """
    self.tier = tier or os.getenv('LOG_TIER', 'production').lower()
    self.logs_dir = Path(logs_dir or os.getenv('LOGS_DIR', 'logs'))
    self.logs_dir.mkdir(parents=True, exist_ok=True)
    self.max_size_mb = int(os.getenv('LOG_MAX_SIZE_MB', '50'))
    self.retention_days = int(os.getenv('LOG_RETENTION_DAYS', '7'))
    self.logger = logging.getLogger('claude_proxy')
    self.logger.setLevel(logging.DEBUG)
    self.logger.handlers = []
    if self.tier == 'production':
        self._setup_production_handlers()
    elif self.tier == 'debug':
        self._setup_debug_handlers()
    elif self.tier == 'forensic':
        self._setup_forensic_handlers()
    else:
        self._setup_production_handlers()
    self.logger.info(f'Structured logger initialized (tier={self.tier})')
```

### Method: `_setup_production_handlers`
**Logic & Purpose:**
```text
Production tier: errors only to file, info to console.
- File: 10MB rotation, 7-day retention
- Console: compact format
```

**Parameters:** `self`
**Variables Used:** `console_handler, error_handler`
**Implementation:**
```python
def _setup_production_handlers(self):
    """
        Production tier: errors only to file, info to console.
        - File: 10MB rotation, 7-day retention
        - Console: compact format
        """
    error_handler = RotatingFileHandler(self.logs_dir / 'proxy_errors.log', maxBytes=10 * 1024 * 1024, backupCount=7)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    self.logger.addHandler(error_handler)
    self.logger.addHandler(console_handler)
```

### Method: `_setup_debug_handlers`
**Logic & Purpose:**
```text
Debug tier: all requests to file.
- File: 50MB rotation, 3-day retention
- Console: debug format
```

**Parameters:** `self`
**Variables Used:** `debug_handler, console_handler`
**Implementation:**
```python
def _setup_debug_handlers(self):
    """
        Debug tier: all requests to file.
        - File: 50MB rotation, 3-day retention
        - Console: debug format
        """
    debug_handler = RotatingFileHandler(self.logs_dir / 'proxy_debug.log', maxBytes=self.max_size_mb * 1024 * 1024, backupCount=3)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(JsonFormatter())
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    self.logger.addHandler(debug_handler)
    self.logger.addHandler(console_handler)
```

### Method: `_setup_forensic_handlers`
**Logic & Purpose:**
```text
Forensic tier: full payloads, manual cleanup.
- File: timestamped, no rotation
- Console: detailed format
```

**Parameters:** `self`
**Variables Used:** `forensic_handler, timestamp, console_handler`
**Implementation:**
```python
def _setup_forensic_handlers(self):
    """
        Forensic tier: full payloads, manual cleanup.
        - File: timestamped, no rotation
        - Console: detailed format
        """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    forensic_handler = logging.FileHandler(self.logs_dir / f'forensic_{timestamp}.log', mode='w', encoding='utf-8')
    forensic_handler.setLevel(logging.DEBUG)
    forensic_handler.setFormatter(DetailedFormatter())
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(DetailedFormatter())
    self.logger.addHandler(forensic_handler)
    self.logger.addHandler(console_handler)
    self.logger.warning('Forensic logging enabled - manual cleanup required')
```

### Method: `_redact_sensitive`
**Logic & Purpose:**
```text
Redact sensitive data from dictionary.

Args:
    data: Dictionary potentially containing sensitive data
    
Returns:
    Dictionary with sensitive values redacted
```

**Parameters:** `self, data`
**Variables Used:** `key_lower`
**Implementation:**
```python
def _redact_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """
        Redact sensitive data from dictionary.
        
        Args:
            data: Dictionary potentially containing sensitive data
            
        Returns:
            Dictionary with sensitive values redacted
        """
    if self.tier == 'forensic':
        return data

    def redact_value(key: str, value: Any) -> Any:
        key_lower = key.lower()
        if any((sens in key_lower for sens in self.SENSITIVE_KEYS)):
            return '***REDACTED***'
        elif isinstance(value, dict):
            return {k: redact_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [redact_value(f'item_{i}', v) for i, v in enumerate(value)]
        return value
    return redact_value('root', data)
```

### Method: `log_request`
**Logic & Purpose:**
```text
Log incoming request.

Args:
    request_id: Unique request identifier
    model: Requested model
    endpoint: Target endpoint
    message_count: Number of messages in conversation
    has_tools: Whether request includes tool definitions
    has_images: Whether request includes images
    has_reasoning: Whether request uses reasoning/thinking
    input_tokens: Input token count
    context_limit: Model context limit
    client_ip: Client IP address
```

**Parameters:** `self, request_id, model, endpoint, message_count, has_tools, has_images, has_reasoning, input_tokens, context_limit, client_ip`
**Variables Used:** `ctx_pct`
**Implementation:**
```python
def log_request(self, request_id: str, model: str, endpoint: str, message_count: int=0, has_tools: bool=False, has_images: bool=False, has_reasoning: bool=False, input_tokens: int=0, context_limit: int=0, client_ip: str='unknown', **kwargs):
    """
        Log incoming request.
        
        Args:
            request_id: Unique request identifier
            model: Requested model
            endpoint: Target endpoint
            message_count: Number of messages in conversation
            has_tools: Whether request includes tool definitions
            has_images: Whether request includes images
            has_reasoning: Whether request uses reasoning/thinking
            input_tokens: Input token count
            context_limit: Model context limit
            client_ip: Client IP address
        """
    ctx_pct = None
    if context_limit > 0 and input_tokens > 0:
        ctx_pct = round(input_tokens / context_limit * 100, 1)
    self.logger.info(f'Request: {model} ({message_count} msgs, tools={has_tools})', extra={'request_id': request_id, 'model': model, 'endpoint': endpoint, 'input_tokens': input_tokens, 'tool_calls': 'yes' if has_tools else 'no', 'status': 'start', 'session_id': client_ip, 'extra_data': json.dumps({'message_count': message_count, 'has_tools': has_tools, 'has_images': has_images, 'has_reasoning': has_reasoning, 'context_pct': ctx_pct})})
```

### Method: `log_response`
**Logic & Purpose:**
```text
Log response.

Args:
    request_id: Unique request identifier
    model: Model that generated response
    output_tokens: Output token count
    input_tokens: Input token count
    thinking_tokens: Reasoning/thinking token count
    duration_ms: Request duration in milliseconds
    cost: Request cost in USD
    tool_calls: List of tool calls made
    status: Response status (success/error/cancelled)
    error: Error message if failed
```

**Parameters:** `self, request_id, model, output_tokens, input_tokens, thinking_tokens, duration_ms, cost, tool_calls, status, error`
**Variables Used:** `tps, log_kwargs, extra_data`
**Implementation:**
```python
def log_response(self, request_id: str, model: str, output_tokens: int=0, input_tokens: int=0, thinking_tokens: int=0, duration_ms: float=0, cost: float=0, tool_calls: Optional[list]=None, status: str='success', error: Optional[str]=None, **kwargs):
    """
        Log response.
        
        Args:
            request_id: Unique request identifier
            model: Model that generated response
            output_tokens: Output token count
            input_tokens: Input token count
            thinking_tokens: Reasoning/thinking token count
            duration_ms: Request duration in milliseconds
            cost: Request cost in USD
            tool_calls: List of tool calls made
            status: Response status (success/error/cancelled)
            error: Error message if failed
        """
    tps = None
    if duration_ms > 0 and output_tokens > 0:
        tps = round(output_tokens / (duration_ms / 1000), 1)
    log_kwargs = {'request_id': request_id, 'model': model, 'duration_ms': round(duration_ms, 1), 'output_tokens': output_tokens, 'input_tokens': input_tokens, 'status': status}
    if thinking_tokens > 0:
        log_kwargs['thinking_tokens'] = thinking_tokens
    if tool_calls:
        log_kwargs['tool_calls'] = len(tool_calls)
    if error:
        log_kwargs['error_type'] = error.split(':')[0] if ':' in error else error
    extra_data = {'tps': tps, 'cost': f'${cost:.4f}' if cost > 0 else None}
    if tool_calls:
        extra_data['tool_names'] = [tc.get('name', 'unknown') for tc in tool_calls[:5]]
    log_kwargs['extra_data'] = json.dumps({k: v for k, v in extra_data.items() if v is not None})
    if status == 'error' and error:
        self.logger.error(f'Error: {error[:100]}', extra=log_kwargs)
    else:
        self.logger.info(f'Response: {output_tokens} tokens in {duration_ms:.0f}ms', extra=log_kwargs)
```

### Method: `log_tool_call_flow`
**Logic & Purpose:**
```text
Track tool call lifecycle for debugging and analytics.

Phases:
- call_start: Tool call detected in model response
- call_transform: Arguments being transformed
- call_sent: Tool call sent to client
- result_received: Tool result received from client
- result_transform: Result being transformed for model
- result_sent: Transformed result sent to model
- success: Tool call completed successfully
- failure: Tool call failed

Args:
    request_id: Request identifier
    tool_name: Name of tool (Bash, Read, Write, etc.)
    phase: Current phase
    tool_id: Tool call ID
    data: Phase-specific data
    session_id: Session identifier for per-session metrics
    success: Whether the tool call succeeded
    error: Error message if failed
```

**Parameters:** `self, request_id, tool_name, phase, tool_id, data, session_id, success, error`
**Variables Used:** `extra, extra_data`
**Implementation:**
```python
def log_tool_call_flow(self, request_id: str, tool_name: str, phase: str, tool_id: Optional[str]=None, data: Optional[Dict[str, Any]]=None, session_id: Optional[str]=None, success: bool=True, error: Optional[str]=None, **kwargs):
    """
        Track tool call lifecycle for debugging and analytics.
        
        Phases:
        - call_start: Tool call detected in model response
        - call_transform: Arguments being transformed
        - call_sent: Tool call sent to client
        - result_received: Tool result received from client
        - result_transform: Result being transformed for model
        - result_sent: Transformed result sent to model
        - success: Tool call completed successfully
        - failure: Tool call failed
        
        Args:
            request_id: Request identifier
            tool_name: Name of tool (Bash, Read, Write, etc.)
            phase: Current phase
            tool_id: Tool call ID
            data: Phase-specific data
            session_id: Session identifier for per-session metrics
            success: Whether the tool call succeeded
            error: Error message if failed
        """
    extra_data = {'phase': phase, 'tool_id': tool_id[:12] + '...' if tool_id and len(tool_id) > 12 else tool_id, 'success': success, 'session_id': session_id, **(data or {})}
    if error:
        extra_data['error'] = error[:200]
    extra = {'request_id': request_id, 'tool_calls': tool_name, 'session_id': session_id, 'extra_data': json.dumps(extra_data)[:500]}
    if phase in ('success', 'failure'):
        self.logger.info(f'Tool {phase}: {tool_name} (success={success})', extra=extra)
        self._log_tool_analytics({'timestamp': datetime.utcnow().isoformat(), 'request_id': request_id, 'session_id': session_id, 'tool_name': tool_name, 'tool_id': tool_id, 'phase': phase, 'success': success, 'error': error})
    else:
        self.logger.info(f'Tool {phase}: {tool_name}', extra=extra)
```

### Method: `_log_tool_analytics`
**Logic & Purpose:**
```text
Log tool call analytics to separate file for analysis.
```

**Parameters:** `self, data`
**Variables Used:** `analytics_file`
**Implementation:**
```python
def _log_tool_analytics(self, data: Dict[str, Any]):
    """Log tool call analytics to separate file for analysis."""
    try:
        analytics_file = self.logs_dir / 'tool_analytics.jsonl'
        with open(analytics_file, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        pass
```

### Method: `log_cache_usage`
**Logic & Purpose:**
```text
Log cache usage for analytics.

Args:
    request_id: Request identifier
    session_id: Session identifier
    cache_hit: Whether cache was hit
    cache_miss: Whether cache was missed
    cached_tokens: Number of tokens from cache
    total_tokens: Total tokens in request
    cache_type: Type of cache (prompt, response, tool)
```

**Parameters:** `self, request_id, session_id, cache_hit, cache_miss, cached_tokens, total_tokens, cache_type`
**Variables Used:** `extra, analytics_file, cache_ratio`
**Implementation:**
```python
def log_cache_usage(self, request_id: str, session_id: Optional[str]=None, cache_hit: bool=False, cache_miss: bool=False, cached_tokens: int=0, total_tokens: int=0, cache_type: str='prompt', **kwargs):
    """
        Log cache usage for analytics.
        
        Args:
            request_id: Request identifier
            session_id: Session identifier
            cache_hit: Whether cache was hit
            cache_miss: Whether cache was missed
            cached_tokens: Number of tokens from cache
            total_tokens: Total tokens in request
            cache_type: Type of cache (prompt, response, tool)
        """
    cache_ratio = round(cached_tokens / total_tokens * 100, 1) if total_tokens > 0 else 0
    extra = {'request_id': request_id, 'session_id': session_id, 'extra_data': json.dumps({'cache_hit': cache_hit, 'cache_miss': cache_miss, 'cached_tokens': cached_tokens, 'total_tokens': total_tokens, 'cache_ratio': cache_ratio, 'cache_type': cache_type})}
    self.logger.info(f"Cache {('hit' if cache_hit else 'miss')}: {cached_tokens}/{total_tokens} ({cache_ratio}%)", extra=extra)
    try:
        analytics_file = self.logs_dir / 'cache_analytics.jsonl'
        with open(analytics_file, 'a') as f:
            f.write(json.dumps({'timestamp': datetime.utcnow().isoformat(), 'request_id': request_id, 'session_id': session_id, 'cache_hit': cache_hit, 'cached_tokens': cached_tokens, 'total_tokens': total_tokens, 'cache_type': cache_type}) + '\n')
    except Exception:
        pass
```

### Method: `log_error`
**Logic & Purpose:**
```text
Log error with context.

Args:
    error: Exception object
    context: Where error occurred
    request_id: Request identifier if applicable
```

**Parameters:** `self, error, context, request_id`
**Variables Used:** `extra`
**Implementation:**
```python
def log_error(self, error: Exception, context: str='unknown', request_id: Optional[str]=None, **kwargs):
    """
        Log error with context.
        
        Args:
            error: Exception object
            context: Where error occurred
            request_id: Request identifier if applicable
        """
    extra = {'error_type': type(error).__name__, 'extra_data': json.dumps({'context': context, 'error_message': str(error), **(kwargs or {})})}
    if request_id:
        extra['request_id'] = request_id
    self.logger.error(f'{context}: {type(error).__name__}: {error}', extra=extra)
```

### Method: `log_provider_fallback`
**Logic & Purpose:**
```text
Log provider fallback event.

Args:
    request_id: Request identifier
    from_provider: Original provider
    to_provider: Fallback provider
    reason: Reason for fallback
```

**Parameters:** `self, request_id, from_provider, to_provider, reason`
**Implementation:**
```python
def log_provider_fallback(self, request_id: str, from_provider: str, to_provider: str, reason: str, **kwargs):
    """
        Log provider fallback event.
        
        Args:
            request_id: Request identifier
            from_provider: Original provider
            to_provider: Fallback provider
            reason: Reason for fallback
        """
    self.logger.warning(f'Provider fallback: {from_provider} → {to_provider} ({reason})', extra={'request_id': request_id, 'provider': to_provider, 'extra_data': json.dumps({'from': from_provider, 'to': to_provider, 'reason': reason})})
```

### Method: `log_startup_info`
**Logic & Purpose:**
```text
Log startup configuration summary.

Args:
    config_summary: Configuration summary dictionary
```

**Parameters:** `self, config_summary`
**Variables Used:** `redacted`
**Implementation:**
```python
def log_startup_info(self, config_summary: Dict[str, Any]):
    """
        Log startup configuration summary.
        
        Args:
            config_summary: Configuration summary dictionary
        """
    redacted = self._redact_sensitive(config_summary)
    self.logger.info('Proxy startup', extra={'extra_data': json.dumps(redacted, default=str, indent=2)})
```

---

## Feature Function: `get_logger`
**Logic & Purpose:**
```text
Get or create global logger instance.

Args:
    tier: Optional tier override
    
Returns:
    StructuredLogger instance
```

**Parameters:** `tier`
**Variables Used:** `_logger`
**Implementation:**
```python
def get_logger(tier: Optional[str]=None) -> StructuredLogger:
    """
    Get or create global logger instance.
    
    Args:
        tier: Optional tier override
        
    Returns:
        StructuredLogger instance
    """
    global _logger
    if _logger is None or tier:
        _logger = StructuredLogger(tier=tier)
    return _logger
```

---

## Feature Function: `log_request`
**Logic & Purpose:**
```text
Convenience function for logging requests.
```

**Parameters:** ``
**Implementation:**
```python
def log_request(**kwargs):
    """Convenience function for logging requests."""
    get_logger().log_request(**kwargs)
```

---

## Feature Function: `log_response`
**Logic & Purpose:**
```text
Convenience function for logging responses.
```

**Parameters:** ``
**Implementation:**
```python
def log_response(**kwargs):
    """Convenience function for logging responses."""
    get_logger().log_response(**kwargs)
```

---

## Feature Function: `log_tool_call_flow`
**Logic & Purpose:**
```text
Convenience function for logging tool call flow.
```

**Parameters:** ``
**Implementation:**
```python
def log_tool_call_flow(**kwargs):
    """Convenience function for logging tool call flow."""
    get_logger().log_tool_call_flow(**kwargs)
```

---

## Feature Function: `log_error`
**Logic & Purpose:**
```text
Convenience function for logging errors.
```

**Parameters:** `error`
**Implementation:**
```python
def log_error(error: Exception, **kwargs):
    """Convenience function for logging errors."""
    get_logger().log_error(error, **kwargs)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/services/logging/startup_display.py
**Path**: `/home/cheta/code/claude-code-proxy/src/services/logging/startup_display.py`

**Module Overview**: 
```text
Colorful startup configuration display.
```

## Global Presets & Variables
- `print_startup_banner` = `display_startup_config`

## Dependencies & Imports
src.services.usage.model_limits.get_model_limits

## Feature Function: `display_startup_config`
**Logic & Purpose:**
```text
Display comprehensive startup configuration with colors.

Color scheme:
- Cyan/Blue: Primary info (calm, professional)
- Magenta/Purple: Highlights and important values
- Green: Success/enabled features
- Yellow: Warnings
- Dim: Secondary info
```

**Parameters:** `config`
**Variables Used:** `provider_name, provider_table, server_table, tips_table, provider, prov_table, model_display, model_table, key_preview, out_str, auth_status, ctx_str, reasoning_table, console`
**Implementation:**
```python
def display_startup_config(config):
    """
    Display comprehensive startup configuration with colors.

    Color scheme:
    - Cyan/Blue: Primary info (calm, professional)
    - Magenta/Purple: Highlights and important values
    - Green: Success/enabled features
    - Yellow: Warnings
    - Dim: Secondary info
    """
    if not RICH_AVAILABLE:
        _display_plain(config)
        return
    console = Console()
    console.print()
    console.print('🚀 [bold bright_cyan]The Ultimate Proxy[/bold bright_cyan] [dim]v2.1.0[/dim]')
    console.print()
    provider_table = Table(show_header=False, box=None, padding=(0, 2))
    provider_table.add_column('Key', style='dim')
    provider_table.add_column('Value', style='bright_cyan')
    provider_name = _extract_provider_name(config.openai_base_url)
    provider_table.add_row('Provider', f'[bold]{provider_name}[/bold]')
    provider_table.add_row('Endpoint', config.openai_base_url)
    if config.openai_api_key:
        key_preview = config.openai_api_key[:15] + '...' if len(config.openai_api_key) > 15 else config.openai_api_key
        provider_table.add_row('Provider Key', f'[green]{key_preview}[/green]')
    else:
        provider_table.add_row('Provider Key', '[yellow]NOT SET (passthrough mode)[/yellow]')
    console.print(Panel(provider_table, title='[bold magenta]Provider[/bold magenta]', border_style='cyan'))
    model_table = Table(show_header=True, box=None, padding=(0, 1))
    model_table.add_column('Tier', style='dim', width=8)
    model_table.add_column('Provider', style='yellow', width=12)
    model_table.add_column('Model', style='bright_cyan', width=35)
    model_table.add_column('Context', style='green', justify='right', width=10)
    model_table.add_column('Output', style='blue', justify='right', width=10)
    for tier, model in [('BIG', config.big_model), ('MIDDLE', config.middle_model), ('SMALL', config.small_model)]:
        context, output = get_model_limits(model)
        ctx_str = _format_tokens(context) if context > 0 else 'unknown'
        out_str = _format_tokens(output) if output > 0 else 'unknown'
        provider = _extract_model_provider(model, config.openai_base_url)
        model_display = model.split('/', 1)[-1] if '/' in model else model
        model_table.add_row(tier, provider, model_display, ctx_str, out_str)
    console.print(Panel(model_table, title='[bold magenta]Models[/bold magenta]', border_style='cyan'))
    if config.reasoning_effort or config.reasoning_max_tokens or config.verbosity:
        reasoning_table = Table(show_header=False, box=None, padding=(0, 2))
        reasoning_table.add_column('Setting', style='dim')
        reasoning_table.add_column('Value', style='bright_magenta')
        if config.reasoning_effort:
            reasoning_table.add_row('Effort', config.reasoning_effort.upper())
        if config.reasoning_max_tokens:
            reasoning_table.add_row('Max Tokens', _format_tokens(config.reasoning_max_tokens))
        if config.verbosity:
            reasoning_table.add_row('Verbosity', config.verbosity)
        reasoning_table.add_row('Exclude', 'Yes' if config.reasoning_exclude else 'No')
        console.print(Panel(reasoning_table, title='[bold magenta]Reasoning[/bold magenta]', border_style='cyan'))
    if config.provider_registry:
        prov_table = Table(show_header=True, box=None, padding=(0, 1))
        prov_table.add_column('Provider', style='dim', width=30)
        prov_table.add_column('Endpoint', style='bright_cyan', width=50)
        for name, entry in config.provider_registry.items():
            prov_table.add_row(name.upper(), entry.get('url', ''))
        console.print(Panel(prov_table, title='[bold magenta]Provider Registry[/bold magenta]', border_style='cyan'))
    server_table = Table(show_header=False, box=None, padding=(0, 2))
    server_table.add_column('Setting', style='dim')
    server_table.add_column('Value', style='bright_cyan')
    server_table.add_row('Host', config.host)
    server_table.add_row('Port', str(config.port))
    server_table.add_row('Log Level', config.log_level.split()[0].upper())
    server_table.add_row('Timeout', f'{config.request_timeout}s')
    server_table.add_row('Max Tokens', _format_tokens(config.max_tokens_limit))
    auth_status = '[green]Enabled[/green]' if config.anthropic_api_key else '[dim]Disabled[/dim]'
    server_table.add_row('Proxy Auth', auth_status)
    console.print(Panel(server_table, title='[bold magenta]Server[/bold magenta]', border_style='cyan'))
    tips_table = Table(show_header=True, box=None, padding=(0, 2))
    tips_table.add_column('Category', style='dim', width=14)
    tips_table.add_column('Command', style='yellow', width=45)
    tips_table.add_row('Settings', '--settings (unified TUI)')
    tips_table.add_row('Models', '--select-models  |  --set-big MODEL')
    tips_table.add_row('Diagnostics', '--doctor  |  --config  |  --analytics')
    tips_table.add_row('Crosstalk', '--crosstalk-studio  |  --crosstalk MODEL1,MODEL2')
    tips_table.add_row('Help', '-h  |  --help')
    console.print(Panel(tips_table, title='[bold green]CLI Arguments[/bold green]', border_style='cyan'))
    console.print()
    console.print(f'[dim]→ API Endpoint[/dim]  [bold bright_cyan]http://{config.host}:{config.port}/v1[/bold bright_cyan]')
    console.print(f'[dim]→ Web Dashboard[/dim] [bold bright_cyan]http://{config.host}:{config.port}/[/bold bright_cyan]')
    console.print(f'[dim]→ Full help[/dim]     [yellow]python start_proxy.py --help[/yellow]')
    console.print()
```

---

## Feature Function: `_display_plain`
**Logic & Purpose:**
```text
Plain text fallback without Rich.
```

**Parameters:** `config`
**Variables Used:** `ctx_str, out_str, key_preview`
**Implementation:**
```python
def _display_plain(config):
    """Plain text fallback without Rich."""
    print()
    print('🚀 Claude Code Proxy v1.0.0')
    print()
    print('Provider:')
    print(f'  {_extract_provider_name(config.openai_base_url)}')
    print(f'  {config.openai_base_url}')
    if config.openai_api_key:
        key_preview = config.openai_api_key[:15] + '...' if len(config.openai_api_key) > 15 else config.openai_api_key
        print(f'  Provider Key: {key_preview}')
    else:
        print(f'  Provider Key: NOT SET (passthrough mode)')
    print()
    print('Models:')
    for tier, model in [('BIG', config.big_model), ('MIDDLE', config.middle_model), ('SMALL', config.small_model)]:
        context, output = get_model_limits(model)
        ctx_str = _format_tokens(context) if context > 0 else 'unknown'
        out_str = _format_tokens(output) if output > 0 else 'unknown'
        print(f'  {tier:8} {model:40} CTX:{ctx_str:>8} OUT:{out_str:>8}')
    print()
    if config.reasoning_effort or config.reasoning_max_tokens:
        print('Reasoning:')
        if config.reasoning_effort:
            print(f'  Effort: {config.reasoning_effort.upper()}')
        if config.reasoning_max_tokens:
            print(f'  Max Tokens: {_format_tokens(config.reasoning_max_tokens)}')
        print()
    print(f'Server: http://{config.host}:{config.port}')
    print()
```

---

## Feature Function: `_extract_provider_name`
**Logic & Purpose:**
```text
Extract provider name from base URL.
```

**Parameters:** `base_url`
**Implementation:**
```python
def _extract_provider_name(base_url: str) -> str:
    """Extract provider name from base URL."""
    if 'openrouter' in base_url:
        return 'OpenRouter'
    elif 'openai.com' in base_url:
        return 'OpenAI'
    elif 'azure' in base_url:
        return 'Azure OpenAI'
    elif 'googleapis.com' in base_url:
        return 'Google Gemini'
    elif 'localhost' in base_url or '127.0.0.1' in base_url:
        if '8317' in base_url:
            return 'VibeProxy/Gemini (Local)'
        elif '11434' in base_url:
            return 'Ollama (Local)'
        elif '1234' in base_url:
            return 'LMStudio (Local)'
        return 'Local'
    return 'Custom'
```

---

## Feature Function: `_extract_model_provider`
**Logic & Purpose:**
```text
Extract provider from model name prefix or detect from default endpoint.

Args:
    model_name: Model name, possibly with provider prefix (e.g., "vibeproxy/gemini-2.5-pro")
    default_base_url: Default API endpoint URL

Returns:
    Provider name (e.g., "VibeProxy", "OpenRouter", "OpenAI")
```

**Parameters:** `model_name, default_base_url`
**Variables Used:** `prefix, provider_map`
**Implementation:**
```python
def _extract_model_provider(model_name: str, default_base_url: str) -> str:
    """Extract provider from model name prefix or detect from default endpoint.

    Args:
        model_name: Model name, possibly with provider prefix (e.g., "vibeproxy/gemini-2.5-pro")
        default_base_url: Default API endpoint URL

    Returns:
        Provider name (e.g., "VibeProxy", "OpenRouter", "OpenAI")
    """
    if '/' in model_name:
        prefix = model_name.split('/', 1)[0].lower()
        provider_map = {'vibeproxy': 'VibeProxy', 'antigravity': 'VibeProxy', 'openrouter': 'OpenRouter', 'openai': 'OpenAI', 'anthropic': 'Anthropic', 'google': 'Google', 'meta-llama': 'Meta', 'mistral': 'Mistral', 'cohere': 'Cohere', 'qwen': 'Qwen'}
        return provider_map.get(prefix, prefix.title())
    if 'openrouter' in default_base_url:
        return 'OpenRouter'
    elif '8317' in default_base_url:
        return 'VibeProxy'
    elif 'openai.com' in default_base_url:
        return 'OpenAI'
    elif 'googleapis' in default_base_url:
        return 'Google'
    elif '11434' in default_base_url:
        return 'Ollama'
    else:
        return 'Default'
```

---

## Feature Function: `_format_tokens`
**Logic & Purpose:**
```text
Format token count compactly.
```

**Parameters:** `count`
**Variables Used:** `count`
**Implementation:**
```python
def _format_tokens(count) -> str:
    """Format token count compactly."""
    if count is None:
        return 'No limit'
    count = int(count)
    if count >= 1000000:
        return f'{count / 1000000:.1f}M'
    elif count >= 1000:
        return f'{count / 1000:.0f}k'
    return str(count)
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/utils/key_reloader.py
**Path**: `/home/cheta/code/claude-code-proxy/src/utils/key_reloader.py`

## Global Presets & Variables
- `key_reloader` = `KeyReloader()`

## Dependencies & Imports
os, re, time, pathlib.Path, typing.Optional, typing.Tuple, typing.Dict, src.core.logging.logger, src.core.config.config

## Feature Class: `KeyReloader`
**Description:**
```text
Handles reloading API keys from the user's shell profile.
Used for seamless key rotation when 401 errors occur.
```

### Method: `__init__`
**Parameters:** `self`
**Implementation:**
```python
def __init__(self):
    self.profile_path = self._find_shell_profile()
    self.last_check_time = 0
    self.cached_keys: Dict[str, str] = {}
```

### Method: `_find_shell_profile`
**Logic & Purpose:**
```text
Detect the config file.
```

**Parameters:** `self`
**Variables Used:** `path, project_root`
**Implementation:**
```python
def _find_shell_profile(self) -> Optional[Path]:
    """Detect the config file."""
    project_root = Path(__file__).parent.parent.parent
    path = project_root / '.env'
    if path.exists():
        logger.debug(f'KeyReloader: Watching config at {path}')
        return path
    logger.debug(f'KeyReloader: Config file {path} does not exist yet')
    return path
```

### Method: `extract_key_from_profile`
**Logic & Purpose:**
```text
Read the profile and extract the value of an exported variable.
```

**Parameters:** `self, var_name`
**Variables Used:** `pattern, content, matches`
**Implementation:**
```python
def extract_key_from_profile(self, var_name: str) -> Optional[str]:
    """
        Read the profile and extract the value of an exported variable.
        """
    if not self.profile_path:
        return None
    try:
        content = self.profile_path.read_text()
        pattern = f"""export\\s+{var_name}=['"]?([^'"\\n]+)['"]?"""
        matches = list(re.finditer(pattern, content))
        if matches:
            return matches[-1].group(1).strip()
        return None
    except Exception as e:
        logger.error(f'KeyReloader: Error reading profile: {e}')
        return None
```

### Method: `check_for_updates`
**Logic & Purpose:**
```text
Check if any relevant keys have changed in the profile.
Returns True if updates were found and applied.
```

**Parameters:** `self`
**Variables Used:** `keys_to_check, mtime, new_value, current_value, updated`
**Implementation:**
```python
def check_for_updates(self) -> bool:
    """
        Check if any relevant keys have changed in the profile.
        Returns True if updates were found and applied.
        """
    if not self.profile_path:
        return False
    try:
        mtime = self.profile_path.stat().st_mtime
        if mtime <= self.last_check_time:
            return False
        self.last_check_time = mtime
    except OSError:
        return False
    logger.info('KeyReloader: Profile modification detected, checking for key updates...')
    keys_to_check = ['ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'GOOGLE_API_KEY', 'PERPLEXITY_API_KEY']
    updated = False
    for var_name in keys_to_check:
        new_value = self.extract_key_from_profile(var_name)
        if new_value:
            current_value = os.environ.get(var_name)
            if new_value != current_value:
                logger.info(f'KeyReloader: Found new value for {var_name}')
                os.environ[var_name] = new_value
                if var_name == 'OPENROUTER_API_KEY':
                    pass
                if var_name == 'ANTHROPIC_API_KEY':
                    config.anthropic_api_key = new_value
                elif var_name in ['OPENAI_API_KEY', 'OPENROUTER_API_KEY']:
                    if 'openrouter' in config.openai_base_url:
                        if var_name == 'OPENROUTER_API_KEY':
                            config.openai_api_key = new_value
                            os.environ['OPENAI_API_KEY'] = new_value
                    elif 'openai' in config.openai_base_url:
                        if var_name == 'OPENAI_API_KEY':
                            config.openai_api_key = new_value
                updated = True
    return updated
```

---


# File Audit: /home/cheta/code/claude-code-proxy/src/utils/request_logger.py
**Path**: `/home/cheta/code/claude-code-proxy/src/utils/request_logger.py`

**Module Overview**: 
```text
Compact request logging utility for terminal output.

Provides information-dense, color-coded logging for reasoning requests,
model routing, and token usage in 3-5 lines maximum.
```

## Global Presets & Variables
- `logger` = `logging.getLogger(__name__)`
- `LOG_STYLE` = `os.environ.get('LOG_STYLE', 'rich').lower()`
- `SHOW_TOKEN_COUNTS` = `os.environ.get('SHOW_TOKEN_COUNTS', 'true').lower() == 'true'`
- `SHOW_PERFORMANCE` = `os.environ.get('SHOW_PERFORMANCE', 'true').lower() == 'true'`
- `COLOR_SCHEME` = `os.environ.get('COLOR_SCHEME', 'auto').lower()`
- `USE_RICH` = `RICH_AVAILABLE and LOG_STYLE == 'rich' and (COLOR_SCHEME != 'none')`
- `request_logger` = `RequestLogger()`

## Dependencies & Imports
logging, os, hashlib, typing.Optional, typing.Dict, typing.Any, datetime.datetime

## Feature Class: `RequestLogger`
**Description:**
```text
Compact request logger for terminal output with color support.
```

### Method: `_get_session_color`
**Logic & Purpose:**
```text
Get a consistent color for a session based on request ID prefix.
```

**Parameters:** `request_id`
**Variables Used:** `color_idx, session_hash`
**Implementation:**
```python
@staticmethod
def _get_session_color(request_id: str) -> str:
    """Get a consistent color for a session based on request ID prefix."""
    session_hash = int(hashlib.md5(request_id[:8].encode()).hexdigest()[:8], 16)
    color_idx = session_hash % len(RequestLogger.SESSION_COLORS)
    return RequestLogger.SESSION_COLORS[color_idx]
```

### Method: `_estimate_tokens`
**Logic & Purpose:**
```text
Estimate token count from text (rough approximation).
```

**Parameters:** `text`
**Implementation:**
```python
@staticmethod
def _estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough approximation)."""
    return max(1, len(text) // 4)
```

### Method: `_count_tokens_precise`
**Logic & Purpose:**
```text
Count tokens precisely using tiktoken if available.
```

**Parameters:** `text, model`
**Variables Used:** `encoding`
**Implementation:**
```python
@staticmethod
def _count_tokens_precise(text: str, model: str='gpt-4') -> int:
    """Count tokens precisely using tiktoken if available."""
    if not TIKTOKEN_AVAILABLE:
        return RequestLogger._estimate_tokens(text)
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding('cl100k_base')
    return len(encoding.encode(text))
```

### Method: `log_request_start`
**Logic & Purpose:**
```text
Log request start with ALL comprehensive info on ONE line.

Format (1 line with colors):
🔵 abc123 | anthropic/claude-3.5-sonnet→openai/gpt-4o-mini | openrouter.ai | CTX:1.2k/200k (1%) | OUT:16k | THINK:8k | STREAM | 3msg | SYS | 127.0.0.1
```

**Parameters:** `request_id, original_model, routed_model, endpoint, reasoning_config, stream, input_text, context_limit, output_limit, input_tokens, message_count, has_system, client_info`
**Variables Used:** `endpoint_name, session_color, think, text, orig_model_str, endpoint_provider, routed_model_str, size, ctx_pct, provider, ctx_color, parts, family`
**Implementation:**
```python
@staticmethod
def log_request_start(request_id: str, original_model: str, routed_model: str, endpoint: str, reasoning_config: Optional[Any]=None, stream: bool=False, input_text: Optional[str]=None, context_limit: int=0, output_limit: int=0, input_tokens: int=0, message_count: int=0, has_system: bool=False, client_info: Optional[str]=None) -> None:
    """
        Log request start with ALL comprehensive info on ONE line.
        
        Format (1 line with colors):
        🔵 abc123 | anthropic/claude-3.5-sonnet→openai/gpt-4o-mini | openrouter.ai | CTX:1.2k/200k (1%) | OUT:16k | THINK:8k | STREAM | 3msg | SYS | 127.0.0.1
        """

    def get_provider_info(model_name: str) -> tuple[str, str, str]:
        """Extract provider, model family, and size from model name."""
        if 'claude' in model_name.lower():
            provider = 'anthropic'
            if '3.5' in model_name:
                family = 'claude-3.5'
                size = 'sonnet' if 'sonnet' in model_name else 'haiku' if 'haiku' in model_name else 'opus' if 'opus' in model_name else 'unknown'
            elif '3' in model_name:
                family = 'claude-3'
                size = 'sonnet' if 'sonnet' in model_name else 'haiku' if 'haiku' in model_name else 'opus' if 'opus' in model_name else 'unknown'
            else:
                family = 'claude'
                size = 'unknown'
        elif 'gpt' in model_name.lower() or 'o1' in model_name.lower():
            provider = 'openai'
            if 'gpt-4o' in model_name:
                family = 'gpt-4o'
                size = 'mini' if 'mini' in model_name else 'standard'
            elif 'gpt-4' in model_name:
                family = 'gpt-4'
                size = 'turbo' if 'turbo' in model_name else 'standard'
            elif 'o1' in model_name:
                family = 'o1'
                size = 'mini' if 'mini' in model_name else 'preview' if 'preview' in model_name else 'standard'
            else:
                family = 'gpt'
                size = 'unknown'
        elif 'gemini' in model_name.lower():
            provider = 'google'
            family = 'gemini'
            size = 'pro' if 'pro' in model_name else 'flash' if 'flash' in model_name else 'unknown'
        else:
            provider = 'unknown'
            family = model_name.split('/')[-1] if '/' in model_name else model_name
            size = 'unknown'
        return (provider, family, size)
    endpoint_name = endpoint.replace('https://', '').replace('http://', '').split('/')[0]
    endpoint_provider = 'openrouter' if 'openrouter' in endpoint_name else 'openai' if 'openai' in endpoint_name else 'anthropic' if 'anthropic' in endpoint_name else endpoint_name
    orig_provider, orig_family, orig_size = get_provider_info(original_model)
    routed_provider, routed_family, routed_size = get_provider_info(routed_model)

    def fmt_tokens(count):
        return f'{count / 1000:.1f}k' if count >= 1000 else str(count)
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        text = Text()
        text.append('🔵 ', style=f'bold {session_color}')
        text.append(f'{request_id[:6]} ', style=session_color)
        text.append(f'{orig_provider}/', style='dim')
        text.append(f'{orig_family}', style='yellow')
        if orig_size != 'unknown':
            text.append(f'-{orig_size}', style='bright_yellow')
        text.append('→', style='dim')
        text.append(f'{routed_provider}/', style='dim')
        text.append(f'{routed_family}', style='green')
        if routed_size != 'unknown':
            text.append(f'-{routed_size}', style='bright_green')
        text.append(f' @{endpoint_provider} ', style='dim')
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = input_tokens / context_limit * 100
            ctx_color = 'green' if ctx_pct < 50 else 'yellow' if ctx_pct < 80 else 'red'
            text.append('| CTX:', style='dim')
            text.append(f'{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ', style=ctx_color)
            text.append(f'({ctx_pct:.0f}%) ', style=ctx_color)
        elif input_tokens > 0:
            text.append('| CTX:', style='dim')
            text.append(f'{fmt_tokens(input_tokens)} ', style='cyan')
        if output_limit > 0:
            text.append('| OUT:', style='dim')
            text.append(f'{fmt_tokens(output_limit)} ', style='blue')
        if reasoning_config:
            from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
            text.append('| THINK:', style='dim')
            if isinstance(reasoning_config, OpenAIReasoningConfig):
                if reasoning_config.max_tokens:
                    text.append(f'{fmt_tokens(reasoning_config.max_tokens)} ', style='bold magenta')
                elif reasoning_config.effort:
                    text.append(f'{reasoning_config.effort} ', style='bold magenta')
            elif isinstance(reasoning_config, AnthropicThinkingConfig):
                text.append(f'{fmt_tokens(reasoning_config.budget)} ', style='bold magenta')
            elif isinstance(reasoning_config, GeminiThinkingConfig):
                text.append(f'{fmt_tokens(reasoning_config.budget)} ', style='bold magenta')
        if stream:
            text.append('| STREAM ', style='bright_blue')
        if message_count > 0:
            text.append(f'| {message_count}msg ', style='dim')
        if has_system:
            text.append('| SYS ', style='green')
        if client_info:
            text.append(f'| {client_info}', style='dim')
        console.print(text)
    else:
        parts = [f'🔵 {request_id[:6]}']
        orig_model_str = f'{orig_provider}/{orig_family}'
        if orig_size != 'unknown':
            orig_model_str += f'-{orig_size}'
        routed_model_str = f'{routed_provider}/{routed_family}'
        if routed_size != 'unknown':
            routed_model_str += f'-{routed_size}'
        parts.append(f'{orig_model_str}→{routed_model_str}')
        parts.append(f'@{endpoint_provider}')
        if context_limit > 0 and input_tokens > 0:
            ctx_pct = input_tokens / context_limit * 100
            parts.append(f'CTX:{fmt_tokens(input_tokens)}/{fmt_tokens(context_limit)} ({ctx_pct:.0f}%)')
        elif input_tokens > 0:
            parts.append(f'CTX:{fmt_tokens(input_tokens)}')
        if output_limit > 0:
            parts.append(f'OUT:{fmt_tokens(output_limit)}')
        if reasoning_config:
            from src.models.reasoning import OpenAIReasoningConfig, AnthropicThinkingConfig, GeminiThinkingConfig
            if isinstance(reasoning_config, OpenAIReasoningConfig):
                think = fmt_tokens(reasoning_config.max_tokens) if reasoning_config.max_tokens else reasoning_config.effort
                parts.append(f'THINK:{think}')
            elif isinstance(reasoning_config, (AnthropicThinkingConfig, GeminiThinkingConfig)):
                parts.append(f'THINK:{fmt_tokens(reasoning_config.budget)}')
        if stream:
            parts.append('STREAM')
        if message_count > 0:
            parts.append(f'{message_count}msg')
        if has_system:
            parts.append('SYS')
        if client_info:
            parts.append(client_info)
        logger.info(' | '.join(parts))
```

### Method: `log_request_complete`
**Logic & Purpose:**
```text
Log request completion with ALL available info on ONE comprehensive line.

Format (1 line with colors):
🟢 abc123 1.7s | CTX:132k/400k (33%) | OUT:56/128k | THINK:8k | 24t/s
```

**Parameters:** `request_id, usage, duration_ms, status, model_name, stream, message_count, has_system, client_info`
**Variables Used:** `output_tokens, think_bar, ctx_color, out_pct, text, context_limit, ctx_pct, session_color, details, input_tokens, tok_s, icon, think_color, out_bar, thinking_tokens, out_color, think_pct, output_limit, parts`
**Implementation:**
```python
@staticmethod
def log_request_complete(request_id: str, usage: Optional[Dict[str, Any]]=None, duration_ms: Optional[float]=None, status: str='OK', model_name: Optional[str]=None, stream: bool=False, message_count: int=0, has_system: bool=False, client_info: Optional[str]=None) -> None:
    """
        Log request completion with ALL available info on ONE comprehensive line.
        
        Format (1 line with colors):
        🟢 abc123 1.7s | CTX:132k/400k (33%) | OUT:56/128k | THINK:8k | 24t/s
        """

    def format_tokens(count):
        """Format token count compactly."""
        if count >= 1000:
            return f'{count / 1000:.1f}k'
        return str(count)

    def format_tokens(count):
        return f'{count / 1000:.1f}k' if count >= 1000 else str(count)
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0)) if usage else 0
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0)) if usage else 0
    thinking_tokens = 0
    if usage:
        if 'thinking_tokens' in usage:
            thinking_tokens = usage['thinking_tokens']
        elif 'reasoning_tokens' in usage:
            thinking_tokens = usage['reasoning_tokens']
        elif 'completion_tokens_details' in usage:
            details = usage['completion_tokens_details']
            if isinstance(details, dict):
                thinking_tokens = details.get('reasoning_tokens', 0)
    from src.utils.model_limits import get_model_limits
    context_limit = 0
    output_limit = 0
    if model_name:
        context_limit, output_limit = get_model_limits(model_name)
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        text = Text()
        icon = '🟢' if status == 'OK' else '🔴'
        text.append(f'{icon} ', style='bold green' if status == 'OK' else 'bold red')
        text.append(f'{request_id[:6]} ', style=session_color)
        if duration_ms:
            text.append(f'{duration_ms / 1000:.1f}s ', style='yellow')
        if usage:
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = input_tokens / context_limit * 100
                ctx_color = 'cyan' if ctx_pct < 50 else 'bright_cyan' if ctx_pct < 80 else 'yellow'
                text.append('| CTX:', style='dim')
                text.append(f'{format_tokens(input_tokens)}/{format_tokens(context_limit)} ', style=ctx_color)
                text.append(f'({ctx_pct:.0f}%) ', style=ctx_color)
            else:
                text.append(f'| CTX:{format_tokens(input_tokens)} ', style='cyan')
            if output_limit > 0:
                out_pct = output_tokens / output_limit * 100 if output_tokens > 0 else 0
                out_color = 'blue' if out_pct < 50 else 'bright_blue' if out_pct < 80 else 'yellow'
                text.append('| OUT:', style='dim')
                text.append(f'{format_tokens(output_tokens)}/{format_tokens(output_limit)} ', style=out_color)
            else:
                text.append(f'| OUT:{format_tokens(output_tokens)} ', style='blue')
            if thinking_tokens > 0:
                text.append('| THINK:', style='dim')
                text.append(f'{format_tokens(thinking_tokens)} ', style='bright_magenta')
        if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
            tok_s = output_tokens / (duration_ms / 1000)
            text.append(f'| {tok_s:.0f}t/s ', style='cyan')
        if output_limit > 0 and output_tokens > 0:
            out_pct = output_tokens / output_limit
            out_bar = RequestLogger._create_progress_bar(output_tokens, output_limit, width=10)
            out_color = RequestLogger._get_bar_color(out_pct)
            text.append('| 📤[', style='dim')
            text.append(out_bar, style=f'bold {out_color}')
            text.append('] ', style='dim')
            if thinking_tokens > 0:
                think_pct = thinking_tokens / output_limit
                think_bar = RequestLogger._create_progress_bar(thinking_tokens, output_limit, width=10)
                think_color = RequestLogger._get_bar_color(think_pct)
                text.append('🟣[', style='dim')
                text.append(think_bar, style=f'bold {think_color}')
                text.append('] ', style='dim')
        if stream:
            text.append('| STREAM ', style='bright_blue')
        if message_count > 0:
            text.append(f'| {message_count}msg ', style='dim')
        if has_system:
            text.append('| SYS ', style='green')
        if client_info:
            text.append(f'| {client_info}', style='dim')
        console.print(text)
    else:
        icon = '🟢' if status == 'OK' else '🔴'
        parts = [f'{icon} {request_id[:6]}']
        if duration_ms:
            parts.append(f'{duration_ms / 1000:.1f}s')
        if usage:
            if context_limit > 0 and input_tokens > 0:
                ctx_pct = input_tokens / context_limit * 100
                parts.append(f'CTX:{format_tokens(input_tokens)}/{format_tokens(context_limit)} ({ctx_pct:.0f}%)')
            else:
                parts.append(f'CTX:{format_tokens(input_tokens)}')
            if output_limit > 0:
                out_pct = output_tokens / output_limit * 100 if output_tokens > 0 else 0
                parts.append(f'OUT:{format_tokens(output_tokens)}/{format_tokens(output_limit)}')
            else:
                parts.append(f'OUT:{format_tokens(output_tokens)}')
            if thinking_tokens > 0:
                parts.append(f'THINK:{format_tokens(thinking_tokens)}')
        if SHOW_PERFORMANCE and output_tokens > 0 and duration_ms:
            tok_s = output_tokens / (duration_ms / 1000)
            parts.append(f'{tok_s:.0f}t/s')
        if stream:
            parts.append('STREAM')
        if message_count > 0:
            parts.append(f'{message_count}msg')
        if has_system:
            parts.append('SYS')
        if client_info:
            parts.append(client_info)
        logger.info(' | '.join(parts))
```

### Method: `log_request_error`
**Logic & Purpose:**
```text
Log request error.

Format (1 line with color):
🔴 REQ abc123 | ERROR | 0.5s | Rate limit exceeded
```

**Parameters:** `request_id, error, duration_ms`
**Variables Used:** `error_text, session_color, error_msg, error_info`
**Implementation:**
```python
@staticmethod
def log_request_error(request_id: str, error: str, duration_ms: Optional[float]=None) -> None:
    """
        Log request error.
        
        Format (1 line with color):
        🔴 REQ abc123 | ERROR | 0.5s | Rate limit exceeded
        """
    error_msg = str(error)
    if len(error_msg) > 80:
        error_msg = error_msg[:77] + '...'
    if USE_RICH and console:
        session_color = RequestLogger._get_session_color(request_id)
        error_text = Text()
        error_text.append('🔴 ', style='bold red')
        error_text.append('REQ ', style='bold red')
        error_text.append(f'{request_id[:8]} ', style=session_color)
        error_text.append('| ', style='dim')
        error_text.append('ERROR', style='bold red')
        if duration_ms:
            error_text.append(' | ', style='dim')
            error_text.append(f'{duration_ms / 1000:.1f}s', style='yellow')
        error_text.append(' | ', style='dim')
        error_text.append(error_msg, style='red')
        console.print(error_text)
    else:
        error_info = f'🔴 REQ {request_id[:8]} | ERROR'
        if duration_ms:
            error_info += f' | {duration_ms / 1000:.1f}s'
        error_info += f' | {error_msg}'
        logger.error(error_info)
```

### Method: `_create_progress_bar`
**Logic & Purpose:**
```text
Create an ASCII progress bar.

Args:
    used: Used amount
    total: Total capacity
    width: Width of the bar in characters
    filled_char: Character for filled portion
    empty_char: Character for empty portion
    
Returns:
    ASCII progress bar string
```

**Parameters:** `used, total, width, filled_char, empty_char`
**Variables Used:** `empty_width, filled_width, percentage`
**Implementation:**
```python
@staticmethod
def _create_progress_bar(used: int, total: int, width: int=20, filled_char: str='█', empty_char: str='░') -> str:
    """
        Create an ASCII progress bar.
        
        Args:
            used: Used amount
            total: Total capacity
            width: Width of the bar in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            
        Returns:
            ASCII progress bar string
        """
    if total == 0:
        return empty_char * width
    percentage = min(used / total, 1.0)
    filled_width = int(width * percentage)
    empty_width = width - filled_width
    return filled_char * filled_width + empty_char * empty_width
```

### Method: `_get_bar_color`
**Logic & Purpose:**
```text
Get color style based on usage percentage.
```

**Parameters:** `percentage`
**Implementation:**
```python
@staticmethod
def _get_bar_color(percentage: float) -> str:
    """Get color style based on usage percentage."""
    if percentage < 0.5:
        return 'green'
    elif percentage < 0.8:
        return 'yellow'
    else:
        return 'red'
```

---


