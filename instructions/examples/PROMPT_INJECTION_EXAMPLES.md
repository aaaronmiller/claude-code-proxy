

# Prompt Injection Examples

This document shows example outputs from the prompt injection system in all three formats.

## Format: EXPANDED (Multi-line Detailed)

```
════════════════════════════════════════════════════════════
PROXY STATUS INFORMATION
(This information is from the Claude Code Proxy layer)
════════════════════════════════════════════════════════════

╔═══════════════════════════════════════════════════════════╗
║ PROXY STATUS & ROUTING                                    ║
╠═══════════════════════════════════════════════════════════╣
║ Mode: Proxy (server key)                                  ║
║ Provider: OpenRouter                                       ║
║ Base URL: https://openrouter.ai/api/v1                    ║
║ Routing:                                                  ║
║   • BIG (Opus)      → openai/gpt-4o                       ║
║   • MIDDLE (Sonnet) → openai/gpt-4o                       ║
║   • SMALL (Haiku)   → gpt-4o-mini                         ║
║ Reasoning: high, 8000 max tokens                          ║
║ Features: Usage tracking ✓ | Compact logger ✗            ║
╚═══════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════╗
║ PERFORMANCE METRICS (Last 10 Requests)                    ║
╠═══════════════════════════════════════════════════════════╣
║ Requests: 847 total (94 today)                            ║
║ Latency:  3,421ms avg | 1,234ms min | 8,765ms max        ║
║ Speed:    78 tok/s avg | 234 tok/s max                    ║
║ Tokens:                                                   ║
║   • Input:    2,145,678 (avg: 2,534/req)                 ║
║   • Output:     456,789 (avg: 539/req)                   ║
║   • Thinking:    12,345 (avg: 15/req)                    ║
║ Context: 43.7k/200k avg (22% utilization)                ║
║ Cost: $12.34 total | $2.47 today | $0.015 avg/req        ║
╚═══════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════╗
║ ERROR TRACKING (Last 24 Hours)                            ║
╠═══════════════════════════════════════════════════════════╣
║ Success Rate: 98.7% (847/859 requests)                    ║
║ Errors: 12 total                                          ║
║   • Rate Limit:     7 (58%)                               ║
║   • Invalid Key:    3 (25%)                               ║
║   • Model Not Found: 2 (17%)                              ║
║                                                           ║
║ Recent Errors:                                            ║
║   [14:23] Rate limit exceeded (openai/gpt-4o)             ║
║   [14:18] Invalid API key (anthropic/claude-3.5-sonnet)   ║
║   [14:05] Model not found (fake/model-123)                ║
╚═══════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════╗
║ MODEL USAGE PATTERNS (Last 7 Days)                        ║
╠═══════════════════════════════════════════════════════════╣
║ Top Models by Request Count:                              ║
║   #1  openai/gpt-4o           245 req  125.3k tok  $1.45  ║
║   #2  anthropic/claude-3.5... 89 req   52.1k tok   $0.89  ║
║   #3  ollama/qwen2.5:72b       34 req   18.9k tok   FREE  ║
║                                                           ║
║ Usage by Type:                                            ║
║   • Text-only:  312 req (82%)                             ║
║   • With tools:  45 req (12%)                             ║
║   • With images: 23 req (6%)                              ║
║                                                           ║
║ Recommendations:                                          ║
║   💡 34 requests to FREE model (saved $0.45)              ║
║   💡 Consider: qwen/qwen-2.5-thinking for reasoning tasks ║
╚═══════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════
```

**Use case**: Complex tasks, debugging sessions, when Claude needs full context

---

## Format: SINGLE (One-line Compact)

```
════════════════════════════════════════════════════════════
PROXY STATUS INFORMATION
(This information is from the Claude Code Proxy layer)
════════════════════════════════════════════════════════════

[Proxy] OpenRouter: O→gpt-4o M→gpt-4o S→gpt-4o-mini | R:high/8k | Track✓ Log✗

Perf: 847req 3.4s⌀ 78t/s | Tok: 2.1M→456k💭12k | Ctx:44k/200k(22%) | Cost:$12.34

Errors: 12/859 (98.7% OK) | RateLimit:7 InvalidKey:3 NotFound:2 | Last:[14:23]RateLimit

Models: gpt-4o:245 claude:89 qwen:34 | Text:82% Tools:12% Img:6% | 34→FREE saved $0.45

════════════════════════════════════════════════════════════
```

**Use case**: Standard tasks, moderate visibility, balanced info/noise ratio

---

## Format: MINI (Ultra-compact Partial Line)

```
════════════════════════════════════════════════════════════
PROXY STATUS INFORMATION
(This information is from the Claude Code Proxy layer)
════════════════════════════════════════════════════════════

P|OR|gpt4o|h | 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free

════════════════════════════════════════════════════════════
```

**Use case**: Every request, minimal overhead, compact header

---

## COMPACT HEADER (Always-on Mode)

For minimal overhead, use the compact header in **every** request:

```
[P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free
```

This can be prepended to the first user message or appended to system prompt with minimal token cost (~30 tokens).

---

## Configuration Examples

### Enable in .env

```bash
# Enable prompt injection
PROMPT_INJECTION_ENABLED="true"

# Format: expanded, single, mini
PROMPT_INJECTION_FORMAT="single"

# Modules to include (comma-separated)
PROMPT_INJECTION_MODULES="status,performance,errors,models"

# Injection mode: auto, always, never, compact_only
PROMPT_INJECTION_MODE="auto"
```

### Programmatic Configuration

```python
from src.utils.prompt_injection_middleware import prompt_injection_middleware

# Configure middleware
prompt_injection_middleware.configure(
    enabled=True,
    format='single',
    modules=['status', 'performance'],
    inject_mode='auto'
)

# Update proxy status data
status_data = {
    'status': {
        'passthrough_mode': False,
        'provider': 'OpenRouter',
        'base_url': 'https://openrouter.ai/api/v1',
        'big_model': 'openai/gpt-4o',
        'middle_model': 'openai/gpt-4o',
        'small_model': 'gpt-4o-mini',
        'reasoning_effort': 'high',
        'reasoning_max_tokens': 8000,
        'track_usage': True,
        'compact_logger': False
    },
    'performance': {
        'total_requests': 847,
        'today_requests': 94,
        'avg_latency_ms': 3421,
        'min_latency_ms': 1234,
        'max_latency_ms': 8765,
        'avg_tokens_per_sec': 78,
        'max_tokens_per_sec': 234,
        'total_input_tokens': 2145678,
        'total_output_tokens': 456789,
        'total_thinking_tokens': 12345,
        'avg_input_tokens': 2534,
        'avg_output_tokens': 539,
        'avg_thinking_tokens': 15,
        'avg_context_tokens': 43700,
        'avg_context_limit': 200000,
        'total_cost': 12.34,
        'today_cost': 2.47,
        'avg_cost_per_request': 0.015
    }
}

from src.utils.prompt_injection_middleware import update_proxy_status
update_proxy_status(status_data)

# Inject into request
request = {
    'model': 'claude-3-5-sonnet-20241022',
    'messages': [
        {'role': 'user', 'content': 'Write a Python function...'}
    ],
    'stream': True
}

# Middleware automatically injects
modified_request = prompt_injection_middleware.inject_into_request(request)

# Or get compact header for manual injection
header = prompt_injection_middleware.get_compact_header()
# Output: "[P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free"
```

---

## Integration Strategies

### Strategy 1: Auto-Inject (Recommended)

Automatically inject based on request characteristics:

```python
# In request processing pipeline
if request.get('stream') or request.get('tools'):
    request = prompt_injection_middleware.inject_into_request(request)
```

Benefits:
- ✅ Intelligent injection
- ✅ Only when beneficial
- ✅ Low overhead

### Strategy 2: Compact Header Always

Add compact header to every request:

```python
# Prepend to first user message
header = prompt_injection_middleware.get_compact_header()
messages[0]['content'] = f"[{header}]\n\n{messages[0]['content']}"
```

Benefits:
- ✅ Minimal tokens (~30)
- ✅ Always-on visibility
- ✅ Easy to parse

### Strategy 3: System Prompt Injection

Inject into system prompt only:

```python
system_prompt = "You are a helpful assistant..."
enhanced_prompt = prompt_injection_middleware.inject_into_system_prompt(system_prompt)
```

Benefits:
- ✅ Doesn't pollute user messages
- ✅ Persistent across conversation
- ✅ Clean separation

### Strategy 4: Selective Modules

Inject only specific modules based on task:

```python
# For debugging: include errors
prompt_injection_middleware.configure(modules=['status', 'errors'])

# For optimization: include performance and models
prompt_injection_middleware.configure(modules=['performance', 'models'])

# For overview: all modules
prompt_injection_middleware.configure(modules=['status', 'performance', 'errors', 'models'])
```

---

## Benefits for Claude Code

When Claude Code receives this information, it can:

1. **Understand routing**: Know which actual model is processing the request
2. **Track costs**: Be aware of spending and suggest cheaper alternatives
3. **Debug errors**: See recent errors and patterns
4. **Optimize**: Suggest free models when appropriate
5. **Context awareness**: Know context window usage and limits
6. **Performance insights**: Understand latency and speed patterns

---

## Token Costs

Approximate token costs per format:

- **Expanded**: ~400-500 tokens (full visibility)
- **Single**: ~150-200 tokens (balanced)
- **Mini**: ~50-80 tokens (minimal)
- **Compact Header**: ~20-30 tokens (always-on)

Recommendation: Use **single** for complex tasks, **compact header** for everything else.
