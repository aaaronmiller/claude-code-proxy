# Prompt Injection Examples

This document shows different configurations and their outputs for Claude Code prompt injection.

## Quick Start

```bash
# 1. Run the interactive configurator
python configure_prompt_injection.py

# 2. Or set manually
export PROMPT_INJECTION_ENABLED="true"
export PROMPT_INJECTION_MODULES="status,performance"
export PROMPT_INJECTION_SIZE="medium"
export PROMPT_INJECTION_MODE="auto"
```

## Size Variants

### Large (Multi-line, ~200-300 tokens)

**Use case:** When you need comprehensive context about proxy state.

**Configuration:**
```bash
export PROMPT_INJECTION_SIZE="large"
export PROMPT_INJECTION_MODULES="status,performance,errors"
```

**Output injected into prompt:**
```
┌─ 🔧 Proxy Status ─────────────────────────────────────┐
│ Provider: OpenRouter   │ Mode: Proxy                  │
│ BIG:    openai/gpt-5                                  │
│ MIDDLE: openai/gpt-5                                  │
│ SMALL:  gpt-4o-mini                                   │
│ Reasoning: high        │ Max Tokens: 8000             │
└────────────────────────────────────────────────────────┘

┌─ ⚡ Performance ──────────────────────────────────────┐
│ Requests:   847 │ Success:  98.6%                     │
│ Latency:  1234ms │ Speed:    78 tok/s                │
│ Cost:    $12.450 │ Avg/req: $0.0147                  │
│ Tokens: ↑ 45,000 ↓ 12,000                            │
└────────────────────────────────────────────────────────┘

┌─ ⚠️  Error Tracking ──────────────────────────────────┐
│ Success:   835 (98.6%) │ Errors:    12                │
│   • Rate Limit              8x                         │
│   • Timeout                 4x                         │
└────────────────────────────────────────────────────────┘
```

**Token cost:** ~250-300 tokens per request

---

### Medium (Single-line, ~50-100 tokens) **[RECOMMENDED]**

**Use case:** Balanced approach for most scenarios.

**Configuration:**
```bash
export PROMPT_INJECTION_SIZE="medium"
export PROMPT_INJECTION_MODULES="status,performance,errors,models"
```

**Output injected into prompt:**
```
🔧 OpenRouter | 🤖 gpt-5 | 🧠 high | 🔒
⚡ 847req | 1234ms | 78t/s | $12.450
✓ 835/847 OK (98.6%) | 12 ERR
🤖 gpt-4o:420 | claude-3.5-sonnet:312 | gpt-4o-mini:115
```

**Token cost:** ~60-80 tokens per request

---

### Small (Inline, ~20-40 tokens)

**Use case:** Minimal token usage, status bar style.

**Configuration:**
```bash
export PROMPT_INJECTION_SIZE="small"
export PROMPT_INJECTION_MODULES="status,performance,errors"
```

**Output injected into prompt:**
```
🌐🧠 ⚡847r·78t/s ✓99%
```

**Token cost:** ~20-30 tokens per request

---

## Module Combinations

### 1. Status Only (Quick Provider Check)

```bash
export PROMPT_INJECTION_MODULES="status"
export PROMPT_INJECTION_SIZE="medium"
```

**Output:**
```
🔧 OpenRouter | 🤖 gpt-5 | 🧠 high | 🔒
```

---

### 2. Performance Monitoring

```bash
export PROMPT_INJECTION_MODULES="performance"
export PROMPT_INJECTION_SIZE="large"
```

**Output:**
```
┌─ ⚡ Performance ──────────────────────────────────────┐
│ Requests:   847 │ Success:  98.6%                     │
│ Latency:  1234ms │ Speed:    78 tok/s                │
│ Cost:    $12.450 │ Avg/req: $0.0147                  │
│ Tokens: ↑ 45,000 ↓ 12,000                            │
└────────────────────────────────────────────────────────┘
```

---

### 3. Error Tracking Focus

```bash
export PROMPT_INJECTION_MODULES="errors"
export PROMPT_INJECTION_SIZE="medium"
```

**Output:**
```
✓ 835/847 OK (98.6%) | 12 ERR
```

---

### 4. Complete Dashboard (All Modules)

```bash
export PROMPT_INJECTION_MODULES="status,performance,errors,models"
export PROMPT_INJECTION_SIZE="medium"
```

**Output:**
```
🔧 OpenRouter | 🤖 gpt-5 | 🧠 high | 🔒
⚡ 847req | 1234ms | 78t/s | $12.450
✓ 835/847 OK (98.6%) | 12 ERR
🤖 gpt-4o:420 | claude-3.5-sonnet:312 | gpt-4o-mini:115
```

---

## Injection Modes

### Auto Mode (Smart Injection) **[RECOMMENDED]**

Injects only when beneficial (tool calls, streaming, complex prompts).

```bash
export PROMPT_INJECTION_MODE="auto"
```

**Injects when:**
- Request has system message
- Request includes tools/functions
- Request is streaming

**Skips when:**
- Simple text completion
- No system message needed

---

### Always Mode (Every Request)

Injects on all requests.

```bash
export PROMPT_INJECTION_MODE="always"
```

**Use case:** When you want consistent context in all interactions.

---

### Header Mode (Compact Header Only)

Injects ultra-compact header but not full content.

```bash
export PROMPT_INJECTION_MODE="header"
```

**Output:** Small icons added to all requests
```
🌐🧠⚡✓
```

---

### Manual Mode (On-Demand)

No automatic injection. Use programmatically.

```bash
export PROMPT_INJECTION_MODE="manual"
```

**Use case:** When you want to control injection via API calls only.

---

## Integration Examples

### 1. Add to .zshrc

```bash
# Claude Code Proxy - Prompt Injection
export PROMPT_INJECTION_ENABLED="true"
export PROMPT_INJECTION_MODULES="status,performance,errors"
export PROMPT_INJECTION_SIZE="medium"
export PROMPT_INJECTION_MODE="auto"

# Start proxy with injection
alias claude-proxy="python ~/claude-code-proxy/src/main.py"
```

### 2. P10k Integration

Add to `~/.p10k.zsh`:

```zsh
# See examples/p10k_integration.zsh for full implementation

function prompt_custom_proxy_status() {
  # Shows: 🔧⚡✓🤖 when proxy is configured
  # ...
}

# Add to right prompt elements
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
  ...
  custom_proxy_status
  ...
)
```

### 3. Project-Specific Configuration

Create `.envrc` in your project:

```bash
# Use direnv to load per-project config

# For this project, use compact injection
export PROMPT_INJECTION_SIZE="small"
export PROMPT_INJECTION_MODULES="performance,errors"
```

---

## Real-World Scenarios

### Scenario 1: Development Mode (High Visibility)

You're debugging performance issues and want full context.

```bash
export PROMPT_INJECTION_SIZE="large"
export PROMPT_INJECTION_MODULES="status,performance,errors"
export PROMPT_INJECTION_MODE="always"
```

### Scenario 2: Production Mode (Low Overhead)

You want minimal token usage but still track critical metrics.

```bash
export PROMPT_INJECTION_SIZE="small"
export PROMPT_INJECTION_MODULES="status,errors"
export PROMPT_INJECTION_MODE="auto"
```

### Scenario 3: Cost Optimization (Track Spending)

Focus on cost and model usage.

```bash
export PROMPT_INJECTION_SIZE="medium"
export PROMPT_INJECTION_MODULES="performance,models"
export PROMPT_INJECTION_MODE="auto"
```

### Scenario 4: Reliability Monitoring (Error Focus)

Track error rates and success.

```bash
export PROMPT_INJECTION_SIZE="medium"
export PROMPT_INJECTION_MODULES="errors,performance"
export PROMPT_INJECTION_MODE="always"
```

---

## Tips & Best Practices

### 1. **Start with Medium Size**
Best balance of information vs token cost.

### 2. **Use Auto Mode**
Smart injection reduces unnecessary token usage.

### 3. **2-3 Modules Maximum**
Avoids prompt bloat while providing useful context.

### 4. **For Long Sessions: Use Small**
Saves tokens over many requests.

### 5. **For Complex Tasks: Use Large**
Gives Claude full visibility into proxy state.

### 6. **Monitor Token Usage**
Check total token cost in analytics to optimize.

---

## Token Cost Comparison

| Configuration | Tokens/Request | Cost Impact* | Use Case |
|--------------|----------------|--------------|----------|
| Small (2 modules) | ~20 | $0.00002 | Status bar |
| Medium (2 modules) | ~60 | $0.00006 | Recommended |
| Medium (4 modules) | ~100 | $0.00010 | Full context |
| Large (2 modules) | ~200 | $0.00020 | Debugging |
| Large (4 modules) | ~350 | $0.00035 | Development |

\* Based on ~$0.001/1K input tokens (varies by model)

---

## Advanced: Conditional Injection

Inject different sizes based on request type:

```python
# In custom middleware
from src.utils.prompt_injection_middleware import prompt_injection_middleware

# Configure based on request
def configure_for_request(request):
    if request.get('tools'):
        # Tool calls = more context needed
        prompt_injection_middleware.configure(
            size='medium',
            modules=['status', 'performance', 'errors']
        )
    else:
        # Simple request = minimal
        prompt_injection_middleware.configure(
            size='small',
            modules=['status']
        )
```

---

## Troubleshooting

### Injection Not Working?

1. Check environment variable:
   ```bash
   echo $PROMPT_INJECTION_ENABLED
   # Should output: true
   ```

2. Verify modules are configured:
   ```bash
   echo $PROMPT_INJECTION_MODULES
   # Should output: status,performance (or similar)
   ```

3. Test mode setting:
   ```bash
   echo $PROMPT_INJECTION_MODE
   # If 'manual', injection won't happen automatically
   ```

### Too Many Tokens?

Reduce size and modules:
```bash
export PROMPT_INJECTION_SIZE="small"
export PROMPT_INJECTION_MODULES="status"
```

### Not Enough Context?

Increase size or add modules:
```bash
export PROMPT_INJECTION_SIZE="large"
export PROMPT_INJECTION_MODULES="status,performance,errors,models"
```

---

## Example Output in Claude Code

When you run Claude Code with injection enabled, your prompts will include context like:

```
User: Help me optimize this function

[System: 🔧 OpenRouter | 🤖 gpt-5 | 🧠 high | 🔒
⚡ 42req | 856ms | 124t/s | $2.34
✓ 41/42 OK (97.6%) | 1 ERR]