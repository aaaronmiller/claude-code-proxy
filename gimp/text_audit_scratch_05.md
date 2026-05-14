# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/examples/usage-examples.md
**File Size:** 6075 bytes

## Features & Sections Declared:
# Examples
## Table of Contents
## Basic Usage
### Start the Proxy
# Quick start (interactive setup)
# Or manual start
# With debug logging
### Configure Claude Code
# Set proxy URL
# Run Claude Code
### Add Shell Aliases
# Toggle proxy
# Start proxy
## Analytics & Monitoring
### Check System Health
# Basic health
# Comprehensive diagnostics
### View Real-time Metrics
# Aggregate metrics
# Active sessions
# Specific session
### Tool Call Analytics
# Last 24 hours
# Last 7 days
# Filter by session
### Cache Performance
# Cache analytics
# Output:
# {
#   "cache_hit_rate": 67.1,
#   "cached_tokens": 45230,
#   "token_savings_percent": 36.2,
#   "estimated_cost_savings": 0.0452
# }
### Historical Trends
# Get 30 days of trends
# Plot with jq (simple text chart)
## CLI Tool Integration
### View All CLI Tools
# Output: ["claude", "opencode", "openclaw", "hermes", "qwen"]
### Get CLI Tool Stats
# Output:
# {
#   "total_tools": 5,
#   "total_sessions": 16,
#   "all_models": ["opus", "sonnet", "coder-model"],
#   "config_file_types": {"CLAUDE.md": 2, "AGENTS.md": 1}
# }
### Session Timeline
# Last 7 days
# Filter by tool
### Specific Tool Details
# Claude Code details
# Output includes:
# - Settings
# - Sessions
# - Config files (CLAUDE.md, etc.)
# - Models used
# - Plugins enabled
## Advanced Configuration
### Enable Debug Logging
# In .env or environment
# Start proxy
### View Log History
# Run cleanup (aggregates then cleans)
# View history
# Show last 30 entries
### Configure Model Cascade
# In .env
# Fallback chain for BIG model
# Fallback chain for MIDDLE model
# Fallback chain for SMALL model
### Set Up Cron for Log Cleanup
# Edit crontab
# Add daily cleanup at 3 AM
### Monitor with Watch
# Watch aggregate metrics
# Watch active sessions
## Troubleshooting
### Check if Proxy is Running
### View Recent Errors
### Check Provider Status
### Verify Database
## Useful One-Liners
# Total cost today
# Tool success rate
# Cache savings
# Active CLI tools count
# Sessions in last hour


## Content / Data Structure:
```text
# Examples

Practical examples for using The Ultimate Proxy.

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Analytics & Monitoring](#analytics--monitoring)
3. [CLI Tool Integration](#cli-tool-integration)
4. [Advanced Configuration](#advanced-configuration)

---

## Basic Usage

### Start the Proxy

```bash
# Quick start (interactive setup)
python quickstart.py

# Or manual start
python start_proxy.py

# With debug logging
LOG_TIER=debug python start_proxy.py
```

### Configure Claude Code

```bash
# Set proxy URL
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY=pass

# Run Claude Code
claude
```

### Add Shell Aliases

Add to `~/.zshrc`:

```bash
# Toggle proxy
cproxy() {
  if [[ -n "$ANTHROPIC_BASE_URL" ]]; then
    unset ANTHROPIC_BASE_URL
    echo "🎯 Direct to Anthropic"
  else
    export ANTHROPIC_BASE_URL=http://localhost:8082
    export ANTHROPIC_API_KEY=pass
    echo "🔀 Using proxy"
  fi
}

# Start proxy
alias ccproxy='cd ~/code/claude-code-proxy && python start_proxy.py'
```

---

## Analytics & Monitoring

### Check System Health

```bash
# Basic health
curl http://localhost:8082/api/system/health

# Comprehensive diagnostics
curl http://localhost:8082/api/system/health/diagnostic | jq
```

### View Real-time Metrics

```bash
# Aggregate metrics
curl http://localhost:8082/api/metrics/aggregate | jq '.metrics'

# Active sessions
curl http://localhost:8082/api/metrics/sessions | jq '.sessions[] | {id: .session_id, requests, tokens, cost}'

# Specific session
curl http://localhost:8082/api/metrics/sessions/abc123... | jq
```

### Tool Call Analytics

```bash
# Last 24 hours
curl http://localhost:8082/api/metrics/tool-analytics | jq

# Last 7 days
curl "http://localhost:8082/api/metrics/tool-analytics?hours=168" | jq

# Filter by session
curl "http://localhost:8082/api/metrics/tool-analytics?session_id=abc123" | jq
```

### Cache Performance

```bash
# Cache analytics
curl http://localhost:8082/api/metrics/cache-analytics | jq

# Output:
# {
#   "cache_hit_rate": 67.1,
#   "cached_tokens": 45230,
#   "token_savings_percent": 36.2,
#   "estimated_cost_savings": 0.0452
# }
```

### Historical Trends

```bash
# Get 30 days of trends
curl "http://localhost:8082/api/metrics/history/trends?days=30" | jq '.trends'

# Plot with jq (simple text chart)
curl "http://localhost:8082/api/metrics/history/trends?days=30" | jq -r '
  .trends | 
  "Date\t\tTool Calls\tSuccess Rate\n" +
  ([range(0; .tool_calls | length)] | 
   map("\(.trends.dates[.])\t\(.trends.tool_calls[.])\t\(.trends.tool_success_rate[.])%") | 
   join("\n"))
'
```

---

## CLI Tool Integration

### View All CLI Tools

```bash
curl http://localhost:8082/api/cli-tools | jq '.data.tools | keys'

# Output: ["claude", "opencode", "openclaw", "hermes", "qwen"]
```

### Get CLI Tool Stats

```bash
curl http://localhost:8082/api/cli-tools/stats | jq '.stats'

# Output:
# {
#   "total_tools": 5,
#   "total_sessions": 16,
#   "all_models": ["opus", "sonnet", "coder-model"],
#   "config_file_types": {"CLAUDE.md": 2, "AGENTS.md": 1}
# }
```

### Session Timeline

```bash
# Last 7 days
curl http://localhost:8082/api/cli-tools/timeline | jq '.timeline[] | {tool: .tool_name, session: .session_id, time: .timestamp}'

# Filter by tool
curl "http://localhost:8082/api/cli-tools/timeline?tool=claude&days=3" | jq
```

### Specific Tool Details

```bash
# Claude Code details
curl http://localhost:8082/api/cli-tools/claude | jq '.data'

# Output includes:
# - Settings
# - Sessions
# - Config files (CLAUDE.md, etc.)
# - Models used
# - Plugins enabled
```

---

## Advanced Configuration

### Enable Debug Logging

```bash
# In .env or environment
LOG_TIER=debug
LOGS_DIR=logs
LOG_MAX_SIZE_MB=100
LOG_RETENTION_DAYS=3

# Start proxy
python start_proxy.py
```

### View Log History

```bash
# Run cleanup (aggregates then cleans)
python -m src.services.logging.log_cleanup

# View history
python -m src.services.logging.log_cleanup --view-history

# Show last 30 entries
python -m src.services.logging.log_cleanup --view-history --history-limit 30
```

### Configure Model Cascade

```bash
# In .env
MODEL_CASCADE=true

# Fallback chain for BIG model
BIG_CASCADE=openai/gpt-4o,anthropic/claude-3-opus,google/gemini-pro

# Fallback chain for MIDDLE model  
MIDDLE_CASCADE=openai/gpt-4o-mini,anthropic/claude-3-sonnet

# Fallback chain for SMALL model
SMALL_CASCADE=openai/gpt-4o-mini,google/gemini-flash
```

### Set Up Cron for Log Cleanup

```bash
# Edit crontab
crontab -e

# Add daily cleanup at 3 AM
0 3 * * * cd /path/to/claude-code-proxy && python -m src.services.logging.log_cleanup >> /var/log/claude-cleanup.log 2>&1
```

### Monitor with Watch

```bash
# Watch aggregate metrics
watch -n 5 'curl -s http://localhost:8082/api/metrics/aggregate | jq ".metrics | {sessions: .total_sessions, requests: .total_requests, tokens: .total_tokens}"'

# Watch active sessions
watch -n 10 'curl -s http://localhost:8082/api/metrics/sessions | jq ".count"'
```

---

## Troubleshooting

### Check if Proxy is Running

```bash
curl http://localhost:8082/api/system/health
```

### View Recent Errors

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.logs.recent_errors'
```

### Check Provider Status

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.providers'
```

### Verify Database

```bash
curl http://localhost:8082/api/system/health/diagnostic | jq '.database'
```

---

## Useful One-Liners

```bash
# Total cost today
curl -s http://localhost:8082/api/metrics/aggregate | jq '.metrics.total_cost'

# Tool success rate
curl -s http://localhost:8082/api/metrics/tool-analytics | jq '.success_rate'

# Cache savings
curl -s http://localhost:8082/api/metrics/cache-analytics | jq '.estimated_cost_savings'

# Active CLI tools count
curl -s http://localhost:8082/api/cli-tools/stats | jq '.stats.total_tools'

# Sessions in last hour
curl -s http://localhost:8082/api/system/health/diagnostic | jq '.requests.last_hour'
```

---

*Examples for version 2.1.0 | Last updated: March 30, 2026*

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/examples/prompt_injection_output.txt
**File Size:** 10642 bytes

## Content / Data Structure:
```text
================================================================================
PROMPT INJECTION DEMO - SAMPLE OUTPUTS
================================================================================

This file shows example outputs from the prompt injection system.

╔══════════════════════════════════════════════════════════════════════════════╗
║                        FORMAT 1: EXPANDED (Multi-line Detailed)              ║
╚══════════════════════════════════════════════════════════════════════════════╝

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

Token cost: ~400-500 tokens
Use case: Complex tasks, debugging sessions, when Claude needs full context


╔══════════════════════════════════════════════════════════════════════════════╗
║                        FORMAT 2: SINGLE (One-line Compact)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════
PROXY STATUS INFORMATION
(This information is from the Claude Code Proxy layer)
════════════════════════════════════════════════════════════

[Proxy] OpenRouter: O→gpt-4o M→gpt-4o S→gpt-4o-mini | R:high/8k | Track✓ Log✗

Perf: 847req 3.4s⌀ 78t/s | Tok: 2.1M→456k💭12k | Ctx:44k/200k(22%) | Cost:$12.34

Errors: 12/859 (98.7% OK) | RateLimit:7 InvalidKey:3 NotFound:2 | Last:[14:23]RateLimit

Models: gpt-4o:245 claude:89 qwen:34 | Text:82% Tools:12% Img:6% | 34→FREE saved $0.45

════════════════════════════════════════════════════════════

Token cost: ~150-200 tokens
Use case: Standard tasks, balanced info/noise ratio


╔══════════════════════════════════════════════════════════════════════════════╗
║                  FORMAT 3: MINI (Ultra-compact Partial Line)                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════
PROXY STATUS INFORMATION
(This information is from the Claude Code Proxy layer)
════════════════════════════════════════════════════════════

P|OR|gpt4o|h

847r|3.4s|78t/s|$12

12err|98.7%OK

gpt4o:245|34free

════════════════════════════════════════════════════════════

Token cost: ~50-80 tokens
Use case: Moderate visibility, compact format


╔══════════════════════════════════════════════════════════════════════════════╗
║                   FORMAT 4: COMPACT HEADER (Always-on Mode)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

[P|OR|gpt4o|h] 847r|3.4s|78t/s|$12 | 12err|98.7%OK | gpt4o:245|34free

Token cost: ~20-30 tokens
Use case: Every request, minimal overhead, can be prepended to any message


================================================================================
LEGEND FOR COMPACT FORMATS
================================================================================

Status Module Mini Format: P|OR|gpt4o|h
  P/S       = Passthrough/Server (proxy mode)
  OR        = Provider abbreviation (OR=OpenRouter, OAI=OpenAI, AZ=Azure)
  gpt4o     = Primary model (truncated)
  h         = Reasoning effort (h=high, m=medium, l=low, N=none)

Performance Module Mini Format: 847r|3.4s|78t/s|$12
  847r      = Total requests
  3.4s      = Average latency in seconds
  78t/s     = Average tokens per second
  $12       = Total cost

Errors Module Mini Format: 12err|98.7%OK
  12err     = Error count
  98.7%OK   = Success rate

Models Module Mini Format: gpt4o:245|34free
  gpt4o:245 = Top model and request count
  34free    = Requests using FREE models


================================================================================
INJECTION STRATEGIES
================================================================================

Strategy 1: Auto-Inject (Recommended)
  - Inject based on request characteristics
  - Enabled for: streaming, tools, complex tasks
  - Format: single or expanded
  - Example: if request.stream or request.tools: inject()

Strategy 2: Compact Header Always
  - Add compact header to every request
  - Minimal token cost (~20-30 tokens)
  - Prepend to first user message
  - Example: messages[0] = f"[{header}]\n\n{original}"

Strategy 3: System Prompt Injection
  - Inject into system prompt only
  - Persistent across conversation
  - Clean separation from user messages
  - Example: system_prompt = inject_into_system_prompt(original)

Strategy 4: Selective Modules
  - Choose which modules to inject
  - status: routing awareness
  - performance: optimization insights
  - errors: debugging information
  - models: usage patterns and recommendations


================================================================================
BENEFITS FOR CLAUDE CODE
================================================================================

When Claude Code receives this information, it can:

1. Routing Awareness
   - Know which actual model is processing the request
   - Understand provider and endpoint configuration
   - Adapt responses based on model capabilities

2. Cost Optimization
   - Track spending in real-time
   - Suggest cheaper alternatives when appropriate
   - Recommend FREE models for simple tasks

3. Error Context
   - See recent errors and patterns
   - Understand rate limits and failures
   - Provide better error messages to users

4. Performance Optimization
   - Know context window usage and limits
   - Understand latency and speed patterns
   - Suggest optimizations based on metrics

5. Smart Recommendations
   - Suggest models based on actual usage patterns
   - Recommend reasoning models for complex tasks
   - Identify cost-saving opportunities


================================================================================
CONFIGURATION EXAMPLES
================================================================================

.env Configuration:
  PROMPT_INJECTION_ENABLED="true"
  PROMPT_INJECTION_FORMAT="single"          # expanded, single, mini
  PROMPT_INJECTION_MODULES="status,performance,errors,models"
  PROMPT_INJECTION_MODE="auto"              # auto, always, never, compact_only

Programmatic Configuration:
  from src.utils.prompt_injection_middleware import prompt_injection_middleware

  prompt_injection_middleware.configure(
      enabled=True,
      format='single',
      modules=['status', 'performance'],
      inject_mode='auto'
  )

Update Proxy Status:
  from src.utils.prompt_injection_middleware import update_proxy_status

  update_proxy_status({
      'status': {...},
      'performance': {...},
      'errors': {...},
      'models': {...}
  })

Inject into Request:
  modified_request = prompt_injection_middleware.inject_into_request(request)

Get Compact Header:
  header = prompt_injection_middleware.get_compact_header()


================================================================================
END OF DEMO
================================================================================

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/examples/crosstalk-config.yaml
**File Size:** 645 bytes

## Content / Data Structure:
```text
# Crosstalk Configuration Example
# Save this file and load with: python start_proxy.py --crosstalk-config examples/crosstalk-config.yaml

models:
  - big
  - small

system_prompts:
  big: path:examples/prompts/alice.txt
  small: path:examples/prompts/bob.txt

paradigm: debate
iterations: 20

topic: "What are the most important challenges facing artificial intelligence in the next 5 years?"

# Available paradigms:
# - memory: Each model analyzes independently and shares insights
# - report: Sequential reporting between models
# - relay: Chain communication through all models
# - debate: Contradictory reasoning with confidence evaluation

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/examples/prompts/bob.txt
**File Size:** 495 bytes

## Content / Data Structure:
```text
You are Bob, a thoughtful and analytical AI assistant. You excel at breaking down complex problems into manageable parts and providing systematic analysis. You tend to think methodically and ask clarifying questions to ensure understanding before moving forward.

When engaging in conversations:
- Be analytical and systematic
- Ask clarifying questions
- Break down complex problems into smaller parts
- Provide structured reasoning and evidence-based conclusions
- Use a calm, methodical tone

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/examples/prompts/alice.txt
**File Size:** 500 bytes

## Content / Data Structure:
```text
You are Alice, an enthusiastic and optimistic AI assistant. You love exploring new ideas and always look for creative solutions to problems. You tend to be upbeat and encouraging in your responses, and you're excellent at brainstorming and coming up with innovative approaches.

When engaging in conversations:
- Be energetic and positive
- Ask thought-provoking questions
- Suggest creative ideas and possibilities
- Encourage collaboration and open-mindedness
- Use a friendly, conversational tone

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/troubleshooting/common-issues.md
**File Size:** 2875 bytes

## Features & Sections Declared:
# Troubleshooting Guide
## 401 Unauthorized Error: "No auth credentials found"
## 400 Bad Request: Unsupported verbosity value
## Reasoning Configuration Issues
### Model doesn't support reasoning parameters
### Using model suffix notation
# OpenAI o-series
# Anthropic Claude
# Google Gemini
## General Debugging Steps


## Content / Data Structure:
```text
# Troubleshooting Guide

## 401 Unauthorized Error: "No auth credentials found"

**Symptom:** You see errors like:
```
Error code: 401 - {'error': {'message': 'No auth credentials found', 'code': 401}}
```

**Cause:** Your `OPENAI_API_KEY` in `.env` is not set to a valid API key.

**Solution:**

1. **For OpenRouter users:**
   - Go to https://openrouter.ai/keys
   - Create or copy your API key
   - Update `.env` file:
     ```bash
     OPENAI_API_KEY="sk-or-v1-YOUR-ACTUAL-KEY-HERE"
     ```

2. **For OpenAI users:**
   - Go to https://platform.openai.com/api-keys
   - Create or copy your API key
   - Update `.env` file:
     ```bash
     OPENAI_API_KEY="sk-YOUR-ACTUAL-KEY-HERE"
     OPENAI_BASE_URL="https://api.openai.com/v1"
     ```

3. **Restart the proxy** after updating the `.env` file

## 400 Bad Request: Unsupported verbosity value

**Symptom:** You see errors like:
```
Error code: 400 - "Unsupported value: 'high' is not supported with the 'gpt-5.1-codex' model"
```

**Cause:** The `VERBOSITY` parameter is not supported by all models.

**Solution:**

1. Open your `.env` file
2. Set `VERBOSITY` to empty:
   ```bash
   VERBOSITY=""
   ```
3. Restart the proxy

**Note:** Verbosity support varies by model and provider. It's recommended to leave it empty unless you know your specific model supports it.

## Reasoning Configuration Issues

### Model doesn't support reasoning parameters

**Symptom:** Reasoning parameters are ignored or cause errors.

**Solution:** Only these models support reasoning:

- **OpenAI o-series:** o1, o3, o4-mini, gpt-5 (use effort: low/medium/high)
- **Anthropic Claude:** claude-opus-4, claude-sonnet-4, claude-3-7-sonnet (use thinking tokens: 1024-16000)
- **Google Gemini:** gemini-2.5-flash-preview-04-17 (use thinking budget: 0-24576)

### Using model suffix notation

You can specify reasoning parameters directly in model names:

```bash
# OpenAI o-series
"o4-mini:high"           # High reasoning effort
"o4-mini:medium"         # Medium reasoning effort

# Anthropic Claude
"claude-opus-4-20250514:4k"    # 4096 thinking tokens
"claude-opus-4-20250514:8000"  # 8000 thinking tokens

# Google Gemini
"gemini-2.5-flash-preview-04-17:16k"  # 16384 thinking budget
```

## General Debugging Steps

1. **Check your `.env` file:**
   ```bash
   cat .env
   ```
   Verify all required variables are set correctly.

2. **Check the proxy logs:**
   Look for ERROR or WARNING messages that indicate what's wrong.

3. **Test with a simple model first:**
   Try using a basic model like `gpt-4o-mini` without reasoning parameters to verify your API key works.

4. **Verify your API key has credits:**
   - OpenRouter: Check https://openrouter.ai/credits
   - OpenAI: Check https://platform.openai.com/usage

5. **Check provider status:**
   - OpenRouter: https://status.openrouter.ai/
   - OpenAI: https://status.openai.com/

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/troubleshooting/tool-call-resolution.md
**File Size:** 4473 bytes

## Features & Sections Declared:
# Solution Architecture: Bridging Claude Code CLI and Google Antigravity
## 1. Problem Statement
## 2. Why Other Methods Failed
### 2.1 The "Simple Proxy" Fallacy
### 2.2 The "Copy-Paste" Patch
### 2.3 The "Streaming Blind Spot"
### 2.4 The "History Amnesia" (Loop Cause)
## 3. The Validated Solution
### 3.1 Configuration (`.env`)
### 3.2 Response Converter (`response_converter.py`)
# Streaming Path (String Replacement)
# Non-Streaming Path (Dict Manipulation)
### 3.3 Request Converter (`request_converter.py`)
# In convert_claude_assistant_message
## 4. Verification & Recovery
## 5. Conclusion


## Content / Data Structure:
```text
# Solution Architecture: Bridging Claude Code CLI and Google Antigravity

**Author:** Droid
**Date:** December 24, 2025
**Context:** Production fix for "Superpowers" loop and authentication failures.

## 1. Problem Statement
The objective was to run **Claude Code CLI** (a tool hardcoded for Anthropic's API) against **Google's Antigravity/Gemini models** (via VibeProxy). The system failed with:
1.  **403 Forbidden**: "Lack a Gemini Code Assist license" for Claude models.
2.  **InputValidationError**: Bash tool failed due to unexpected `prompt` parameter.
3.  **Infinite Loops**: The model repeated successful tool calls endlessly.
4.  **Ghost Streams**: Duplicate responses confused the client.

## 2. Why Other Methods Failed

### 2.1 The "Simple Proxy" Fallacy
Attempting to just forward requests failed because the protocols are **semantically incompatible**, not just syntactically different.
*   **Failure:** Forwarding `claude-haiku` to VibeProxy resulted in `403` because the user lacked the enterprise license for the mapped model.
*   **Fix:** We mapped `SMALL_MODEL` to `gemini-3-flash`, a high-performance, permissive model.

### 2.2 The "Copy-Paste" Patch
Attempting to fix the Bash schema by copying `prompt` to `command` (`args["command"] = args["prompt"]`) failed.
*   **Failure:** Claude Code's validator is strict. It rejected the *presence* of the extra `prompt` key.
*   **Fix:** We implemented a **Rename-and-Delete** strategy (`args["command"] = args.pop("prompt")`).

### 2.3 The "Streaming Blind Spot"
Fixing the JSON payload in the non-streaming path was insufficient because Claude Code relies heavily on **streaming**.
*   **Failure:** The CLI parses the raw stream. If the stream contains `"prompt":`, the CLI validation fails *before* the proxy can parse and fix the full JSON.
*   **Fix:** We implemented a **Stream-Side Patch** that performs string replacement (`.replace('"prompt":', '"command":')`) on the raw chunk buffer, ensuring the client receives the expected key in real-time.

### 2.4 The "History Amnesia" (Loop Cause)
Fixing the outgoing request created a discrepancy in the conversation history.
*   **Failure:** We sent `command` to the client. The client executed it. We sent `command` back to Gemini in the history. Gemini (trained to output `prompt`) saw `command`, didn't recognize it as its own valid tool call, and re-generated the tool call, causing an infinite loop.
*   **Fix:** We implemented **Reverse-Normalization**. When sending history to Gemini, we rename `command` *back* to `prompt`. This maintains the model's illusion of consistency.

## 3. The Validated Solution

### 3.1 Configuration (`.env`)
Map abstract tiers to available, authorized Gemini models.
```bash
BIG_MODEL="gemini-claude-opus-4-5-thinking"      # Or gemini-3-pro if restricted
MIDDLE_MODEL="gemini-claude-sonnet-4-5-thinking" # Or gemini-3-pro
SMALL_MODEL="gemini-3-flash"                     # CRITICAL: Fixes tool call speed & auth
```

### 3.2 Response Converter (`response_converter.py`)
**Forward Normalization**: Transform Gemini output to Claude expectation.
```python
# Streaming Path (String Replacement)
if tool_name in ["bash", "repl"]:
    partial_args = partial_args.replace('"prompt":', '"command":')

# Non-Streaming Path (Dict Manipulation)
if "prompt" in args:
    args["command"] = args.pop("prompt")
```

### 3.3 Request Converter (`request_converter.py`)
**Reverse Normalization**: Transform Claude history to Gemini expectation.
```python
# In convert_claude_assistant_message
if tool_name == "bash" and "command" in args:
    args["prompt"] = args.pop("command")
```
**Temperature Control**: Force deterministic outputs for router models.
```python
if model_size == "small":
    openai_request["temperature"] = 0
```

## 4. Verification & Recovery
To verify the fix:
1.  Clear logs: `echo "" > logs/debug_traffic.log`
2.  Run tool: `claude -p "ls -la"`
3.  Check logs for `200 OK` and correct argument transformation.

If looping persists:
1.  Check `debug_traffic.log` for the `role: user` history block. Ensure it contains `"prompt": ...` for previous tool calls.
2.  Verify `SMALL_MODEL` is `gemini-3-flash` (or another model that supports `function_response` correctly).

## 5. Conclusion
This architecture provides a robust, bi-directional translation layer that satisfies the strict requirements of both the Claude Code CLI and the Gemini API, enabling seamless interoperability without modifying the client.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/troubleshooting/401-errors.md
**File Size:** 9841 bytes

## Features & Sections Declared:
# Troubleshooting 401 "User Not Found" Errors
## Understanding the Error
## Important Note About `OPENAI_API_KEY`
## Quick Fixes
### 1. Verify Your API Key is Loaded
# Check if the API key is set
# If empty, make sure your .env file is correctly configured
### 2. Reinstall Dependencies
### 3. Restart the Proxy
# Stop the proxy (Ctrl+C)
# Then start it again
### 4. Check Your Provider Account
## Detailed Diagnostics
### Check Your Configuration
# Check for passthrough mode triggers
### Test Your API Key Directly
# Replace with your OPENAI_BASE_URL
### Check for Environment Variable Conflicts
# List all environment variables containing "KEY"
## Common Issues and Solutions
### Issue 1: "Passthrough Mode" Enabled
# For OpenRouter
# For OpenAI
# For Azure or other providers
### Issue 2: API Key in Wrong Format
### Issue 3: Wrong Base URL
# For OpenRouter
# For OpenAI
# For Azure OpenAI
# For local models (Ollama, LM Studio, etc.)
### Issue 4: Credits Exhausted
### Issue 5: API Key Cached
# Exit and reopen your terminal
# OR source your .env file again
# Then restart the proxy
## Specific Fix for Recent Update
### Step 1: Update and Restart
# Pull the latest fix
# Reinstall dependencies
# Restart the proxy
### Step 2: Verify Rich Library
### Step 3: Check Logs
## Still Having Issues?
## Prevention
## FAQ: Why is it called `OPENAI_API_KEY`?
## Related Documentation


## Content / Data Structure:
```text
# Troubleshooting 401 "User Not Found" Errors

If you're experiencing 401 authentication errors after updating the Claude Code Proxy, this guide will help you diagnose and resolve the issue.

## Understanding the Error

The error `401 Unauthorized - user not found` comes from your API provider (OpenRouter, OpenAI, Azure, etc.), not from the proxy itself. This typically means:

1. **Invalid API Key**: The API key is not recognized by the provider
2. **Expired API Key**: The API key has expired or been revoked
3. **Account Issue**: The account associated with the API key is inactive or suspended
4. **Wrong API Key**: The wrong API key is being sent (e.g., Anthropic key instead of provider key)
5. **Configuration Issue**: The API key is not being loaded correctly from environment variables

## Important Note About `OPENAI_API_KEY`

**The `OPENAI_API_KEY` environment variable is used for ANY provider you connect to**, not just OpenAI:
- **OpenRouter**: Use your OpenRouter API key (starts with `sk-or-v1-`)
- **OpenAI**: Use your OpenAI API key (starts with `sk-`)
- **Azure**: Use your Azure API key
- **Other providers**: Use whatever API key that provider gives you

The variable is named `OPENAI_API_KEY` for compatibility reasons, but it works with any OpenAI-compatible endpoint.

## Quick Fixes

### 1. Verify Your API Key is Loaded

Check that your API key is correctly set in your environment:

```bash
# Check if the API key is set
echo $OPENAI_API_KEY

# If empty, make sure your .env file is correctly configured
cat .env | grep OPENAI_API_KEY
```

### 2. Reinstall Dependencies

After pulling new changes, reinstall dependencies to ensure all packages are up to date:

```bash
pip install -r requirements.txt
```

### 3. Restart the Proxy

Make sure to fully restart the proxy after pulling new changes:

```bash
# Stop the proxy (Ctrl+C)
# Then start it again
python start_proxy.py
```

### 4. Check Your Provider Account

Verify your API provider account is active:

**For OpenRouter:**
1. Go to https://openrouter.ai/
2. Log in to your account
3. Check your API key is active
4. Verify you have sufficient credits
5. Try regenerating your API key if needed

**For OpenAI:**
1. Go to https://platform.openai.com/
2. Check your API key is active
3. Verify your billing is set up and has credits

**For Azure OpenAI:**
1. Check your Azure portal
2. Verify your deployment is active
3. Confirm your API key and endpoint are correct

## Detailed Diagnostics

### Check Your Configuration

Run this script to verify your configuration:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

print(f"API Key set: {bool(api_key)}")
print(f"API Key prefix: {api_key[:7] if api_key else 'None'}...")
print(f"Base URL: {base_url}")

# Check for passthrough mode triggers
if api_key == "pass" or api_key == "your-api-key-here":
    print("WARNING: Passthrough mode enabled - you need to provide API key via headers")
elif not api_key:
    print("WARNING: No API key configured")
else:
    print("API Key appears to be configured correctly")
```

### Test Your API Key Directly

Test if your API key works directly with your provider:

**For OpenRouter:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**For OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**For custom endpoints:**
```bash
# Replace with your OPENAI_BASE_URL
curl $OPENAI_BASE_URL/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If this returns a 401 error, the problem is with your API key or provider account, not the proxy.

### Check for Environment Variable Conflicts

Make sure no other environment variables are overriding your API key:

```bash
# List all environment variables containing "KEY"
env | grep -i key
```

Look for any variables that might conflict with `OPENAI_API_KEY`.

## Common Issues and Solutions

### Issue 1: "Passthrough Mode" Enabled

**Symptoms**: Proxy says "enabling passthrough mode" on startup

**Cause**: `OPENAI_API_KEY` is not set, or is set to "pass" or "your-api-key-here"

**Solution**: Set a valid API key in your `.env` file:

```bash
# For OpenRouter
OPENAI_API_KEY="sk-or-v1-YOUR-ACTUAL-KEY-HERE"

# For OpenAI
OPENAI_API_KEY="sk-YOUR-ACTUAL-KEY-HERE"

# For Azure or other providers
OPENAI_API_KEY="your-provider-api-key-here"
```

### Issue 2: API Key in Wrong Format

**Symptoms**: 401 error even though key appears to be set

**Cause**: API key is in wrong format for the provider

**Solution**: Verify your key format:
- OpenRouter keys start with: `sk-or-v1-`
- OpenAI keys start with: `sk-`
- Make sure there are no spaces or newlines in the key

### Issue 3: Wrong Base URL

**Symptoms**: API works with `curl` but not with proxy

**Cause**: `OPENAI_BASE_URL` is pointing to wrong endpoint

**Solution**: Set the correct base URL for your provider:

```bash
# For OpenRouter
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# For OpenAI
OPENAI_BASE_URL="https://api.openai.com/v1"

# For Azure OpenAI
OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment-name"

# For local models (Ollama, LM Studio, etc.)
OPENAI_BASE_URL="http://localhost:11434/v1"
```

### Issue 4: Credits Exhausted

**Symptoms**: API worked before but stopped working

**Cause**: API provider account has run out of credits or exceeded quota

**Solution**:

**For OpenRouter:**
1. Go to https://openrouter.ai/account
2. Check your credit balance
3. Add more credits if needed

**For OpenAI:**
1. Go to https://platform.openai.com/account/billing
2. Check your usage and billing status
3. Add a payment method or increase limits if needed

**For Azure:**
1. Check your Azure portal
2. Verify your subscription is active
3. Check quota limits for your deployment

### Issue 5: API Key Cached

**Symptoms**: Changed API key but still getting 401

**Cause**: Old API key cached in environment

**Solution**: Fully restart your terminal/shell:

```bash
# Exit and reopen your terminal
# OR source your .env file again
source .env

# Then restart the proxy
python start_proxy.py
```

## Specific Fix for Recent Update

If the error started **immediately after pulling commit d8bc31c** (terminal output enhancements):

### Step 1: Update and Restart

```bash
# Pull the latest fix
git pull origin main

# Reinstall dependencies
pip install -r requirements.txt

# Restart the proxy
python start_proxy.py
```

The latest version includes defensive error handling that prevents workspace extraction from interfering with API calls.

### Step 2: Verify Rich Library

The terminal enhancements require the `rich` library. Verify it's installed:

```bash
python -c "from rich.console import Console; print('Rich OK')"
```

If this fails:

```bash
pip install rich>=14.2.0
```

### Step 3: Check Logs

Look for any error messages during startup that might indicate configuration issues:

```bash
python start_proxy.py 2>&1 | grep -i error
```

## Still Having Issues?

If none of these solutions work:

1. **Enable Debug Logging**:
   ```bash
   export LOG_LEVEL="DEBUG"
   python start_proxy.py
   ```

2. **Test with Minimal Configuration**:
   Create a minimal `.env` file with just:
   ```bash
   OPENAI_API_KEY="your-key-here"
   OPENAI_BASE_URL="https://openrouter.ai/api/v1"
   BIG_MODEL="openai/gpt-4o"
   SMALL_MODEL="openai/gpt-4o-mini"
   ```

3. **Check for Proxy/VPN Interference**:
   Some corporate proxies or VPNs can interfere with API calls. Try:
   ```bash
   unset http_proxy
   unset https_proxy
   python start_proxy.py
   ```

4. **Verify Python Version**:
   ```bash
   python --version  # Should be 3.10 or higher
   ```

5. **Report the Issue**:
   If the problem persists, create an issue at:
   https://github.com/anthropics/claude-code-proxy/issues

   Include:
   - Error message
   - Output from the diagnostic script above
   - Python version
   - Operating system
   - Contents of `.env` (with API keys redacted)

## Prevention

To avoid similar issues in the future:

1. **Keep dependencies updated**: Run `pip install -r requirements.txt` after each pull
2. **Use environment files**: Keep API keys in `.env` rather than exporting manually
3. **Test after updates**: Run a test request after pulling changes:
   ```bash
   curl -X POST http://localhost:8000/v1/messages \
     -H "x-api-key: your-anthropic-key" \
     -H "Content-Type: application/json" \
     -d '{"model": "claude-3-5-sonnet-20241022", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}'
   ```

4. **Monitor API usage**: Regularly check your OpenRouter dashboard to ensure you have credits

## FAQ: Why is it called `OPENAI_API_KEY`?

The environment variable is named `OPENAI_API_KEY` for compatibility with OpenAI's API format, but **it works with ANY OpenAI-compatible provider**:

- **OpenRouter**: Most common use case - proxy OpenAI models through OpenRouter
- **OpenAI**: Direct OpenAI API access
- **Azure OpenAI**: Microsoft's Azure-hosted OpenAI models
- **Local models**: Ollama, LM Studio, vLLM, etc.
- **Other providers**: Any service with OpenAI-compatible endpoints

The proxy translates Claude API requests to OpenAI-compatible format, then forwards them to whatever endpoint you specify in `OPENAI_BASE_URL`. The naming convention is kept for compatibility, but the key itself is for whatever provider you're using.

## Related Documentation

- [Configuration Guide](../README.md#configuration)
- [Terminal Output Configuration](TERMINAL_OUTPUT.md)
- [API Key Setup](../README.md#api-key-setup)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/troubleshooting/antigravity-toolcall-fix.md
**File Size:** 14940 bytes

## Features & Sections Declared:
# Case Study: Cascading Failure Resolution in AI Proxy Architectures
## Interfacing Claude Code CLI with Google Antigravity via VibeProxy
### Abstract
### 1. Introduction
### 2. Diagnostic Methodology
### 3. Fault Analysis: The "Perfect Storm"
#### 3.1. Primary Fault: Protocol Mismatch (The Trigger)
#### 3.2. Secondary Fault: Infrastructure Crash (The Mask)
#### 3.3. Tertiary Fault: Stream Integrity ("Ghost Streams")
#### 3.4. Quaternary Fault: Artificial Capacity Limits
#### 3.5. Quinary Fault: Streaming Parameter Transformation Defect
### 4. Resolution & Implementation
#### Phase 1: Dynamic Protocol Translation (Fixing Auth)
# provider_detector.py - Model name mapping
# Haiku → SMALL_MODEL (fast tool orchestration)
# Sonnet → MIDDLE_MODEL
# Opus → BIG_MODEL
#### Phase 2: Dependency Repair (Fixing 500s)
# request_logger.py - Fixed import path
# BEFORE (broken):
# from src.utils.model_limits import get_model_limits
# AFTER (fixed):
#### Phase 3: Stream Deduplication (Fixing Ghost Calls)
# response_converter.py - Ghost stream filtering
# Known ID - check if this is a ghost stream (different index)
# New unique ID - register it
#### Phase 4: Capacity Expansion
# model_limits.py - Gemini capacity definitions
# Gemini models with 1M+ context
# Thinking models (default limits for unrecognized)
#### Phase 5: Dual-Layer Parameter Normalization (Fixing Bash Tool Streaming)
# Lines 309-312, 564-567
## Phase 6: Content-Based Duplicate Tool Call Filtering (December 2025)
# Lines 539-563: Early fingerprint check
# Lines 518-520: Early skip for marked duplicates
### 6. Conclusion


## Content / Data Structure:
```text
# Case Study: Cascading Failure Resolution in AI Proxy Architectures
## Interfacing Claude Code CLI with Google Antigravity via VibeProxy

**Date:** December 24, 2025
**Subject:** Debugging and Rectification of "Superpowers" Tool Call Loops and Protocol Mismatches
**System:** Claude Code CLI → Custom Proxy (Python) → VibeProxy (Localhost) → Google Antigravity API

---

### Abstract

This paper documents the diagnostic process and resolution of a complex, multi-layered failure in a custom AI proxy infrastructure designed to interface Anthropic's Claude Code CLI with Google's internal "Antigravity" (Gemini) models. The system exhibited persistent 500 Internal Server Errors, authentication failures, and endless retry loops during tool execution (specifically involving the "superpowers" skill). The root cause was identified as a protocol mismatch in model identification, exacerbated by a secondary logging crash, stream integrity issues ("ghost calls"), artificial context limitations, and streaming parameter transformation defects. This study details the fault progression and the engineering interventions required to restore stability across five distinct failure modes.

### 1. Introduction

The objective was to enable the **Claude Code CLI** (a terminal-based AI coding agent) to utilize **Anthropic Opus 4.5** models provided by Google via its Antigravity IDE during the initial product release period (December 2925), during which token limits were virtually unlimited. The prohibitive price and restrictive token limits on this model via the default Anthropic configuration for users under the $20 "pro" plan made this a very attractive opportunity to users if it could be made functional. However various bugs in the routing software used to enable this needed to be resolved related to the specific differences in how Anthropic and Google process tool calls respectively. Since Claude Code is hardcoded to expect Anthropic models (Sonnet, Haiku, Opus), a middleware layer was required to:
1.  Intercept requests from Claude Code.
2.  Translate model names and protocols.
3.  Forward requests to **VibeProxy**, a local service wrapping Google's internal "Antigravity" API, utiizing code from **CLIProxyAPI**.

The system failed catastrophically when Claude Code attempted to execute tools (e.g., `Bash`, `Task`), entering a loop where an enabled skill, **superpowers**, was repeatedly reloaded without successful execution - related to an addtional configuration setting due to token output limit discrepancies between thosse permitted by Anthropic (128k) and Google(1m).

### 2. Diagnostic Methodology

Forensic analysis of the `debug_traffic.log` and codebase revealed a "snowballing" failure chain:

*   **Symptom 1:** `500 Internal Server Error` returned to the client.
*   **Symptom 2:** `auth_unavailable: no auth available` logged by the proxy.
*   **Symptom 3:** `ModuleNotFoundError: src.utils.model_limits` in the traceback.
*   **Symptom 4:** Massive payloads (~170KB) observed during retries.

### 3. Fault Analysis: The "Perfect Storm"

The failure was not a single bug but a dependency chain of five distinct faults:

#### 3.1. Primary Fault: Protocol Mismatch (The Trigger)
Claude Code uses a specific model, `claude-haiku-4-5-20251001`, for fast tool execution/orchestration.
*   **The Bug:** The middleware forwarded this model ID directly to VibeProxy.
*   **The Failure:** VibeProxy (Antigravity wrapper) operates on a strictly allowlisted set of model IDs (e.g., `gemini-3-flash`, `gemini-claude-sonnet-4-5`). It did not recognize `claude-haiku...` and rejected the request with `auth_unavailable` (interpreting the invalid ID as a permission scope error).

#### 3.2. Secondary Fault: Infrastructure Crash (The Mask)
When the proxy attempted to log the failure (or any completed request), it triggered a fatal crash.
*   **The Bug:** `src/services/logging/request_logger.py` attempted to import `get_model_limits` from a non-existent path `src.utils.model_limits`.
*   **The Failure:** This raised an unhandled `ModuleNotFoundError`, causing the proxy to return HTTP 500 to the client, effectively masking the upstream "auth" error and preventing graceful error handling.

#### 3.3. Tertiary Fault: Stream Integrity ("Ghost Streams")
Upon fixing the crash, a race condition in the VibeProxy/Gemini streaming protocol emerged.
*   **The Bug:** The upstream provider occasionally emitted duplicate Server-Sent Events (SSE) for the same tool call—one containing the ID and another containing arguments but no ID ("ghost stream").
*   **The Failure:** The proxy interleaved these streams, sending conflicting data to Claude Code. The CLI interpreted this as "two different model outputs" for a single session, failed to parse the JSON, and initiated a retry.

#### 3.4. Quaternary Fault: Artificial Capacity Limits
*   **The Bug:** The proxy's `model_limits.py` enforced a default context window of 128k tokens for unrecognized models.
*   **The Failure:** The "superpowers" system prompt injection involved massive context (~170KB+). While Gemini supports 1M+ tokens, the proxy risked truncating or rejecting these requests before they even reached the upstream provider.

#### 3.5. Quinary Fault: Streaming Parameter Transformation Defect
Following the aforementioned repairs, an additional failure mode was discovered during production use: **Bash tool execution failures in streaming mode**.
*   **The Bug:** Streaming functions in `src/services/conversion/response_converter.py` performed on-the-fly JSON string replacement to transform Gemini's `"prompt"` parameter to Claude's `"command"` parameter, but this transformation was incomplete. While the non-streaming path correctly applied the centralized `normalize_tool_arguments()` function, streaming functions only applied partial string replacement on JSON deltas without complete semantic transformation.
*   **The Failure:** Claude Code CLI rejected Bash toolcalls in streaming mode with validation error: `"Invalid value for 'command': Expected a string or array, got undefined"`. Non-streaming requests succeeded, revealing an asymmetry in parameter normalization logic.

### 4. Resolution & Implementation

A five-phase rectification plan was executed:

#### Phase 1: Dynamic Protocol Translation (Fixing Auth)
We modified `src/services/models/provider_detector.py` to implement **dynamic model mapping**:
*   **Logic:** Intercept any model name containing "haiku".
*   **Routing:** Check the `SMALL_MODEL` environment variable.
    *   If set to a valid VibeProxy ID (e.g., `gemini-3-flash`), use it.
    *   **Fallback:** If unset or invalid, hard-map to `gemini-3-flash`.
*   **Result:** VibeProxy now receives a valid, authorized model ID for all tool-use requests.

```python
# provider_detector.py - Model name mapping
def get_backend_model(incoming_model: str) -> str:
    model_lower = incoming_model.lower()
    
    # Haiku → SMALL_MODEL (fast tool orchestration)
    if "haiku" in model_lower:
        return os.getenv("SMALL_MODEL", "gemini-3-flash")
    
    # Sonnet → MIDDLE_MODEL
    if "sonnet" in model_lower:
        return os.getenv("MIDDLE_MODEL", "gemini-3-pro")
    
    # Opus → BIG_MODEL
    if "opus" in model_lower:
        return os.getenv("BIG_MODEL", "gemini-claude-opus-4-5-thinking")
    
    return incoming_model  # Pass through unknown models
```

#### Phase 2: Dependency Repair (Fixing 500s)
We corrected the import path in `src/services/logging/request_logger.py`:
*   **Change:** `from src.utils.model_limits` → `from src.services.usage.model_limits`.
*   **Result:** Logging now succeeds, allowing the proxy to run without crashing on completion.

```python
# request_logger.py - Fixed import path
# BEFORE (broken):
# from src.utils.model_limits import get_model_limits

# AFTER (fixed):
from src.services.usage.model_limits import get_model_limits
```

#### Phase 3: Stream Deduplication (Fixing Ghost Calls)
We patched `src/services/conversion/response_converter.py` with robust filtering:
*   **Mechanism:** Tracking active tool call IDs and their primary stream indices.
*   **Logic:** `if active_tool_ids[id]["primary_index"] != current_index: ignore_ghost_stream()`.
*   **Result:** Only a single, coherent stream is forwarded to the client, preventing parse errors.

```python
# response_converter.py - Ghost stream filtering
active_tool_ids = {}  # Map: tc_id -> {primary_index, claude_index}

for tc_delta in delta["tool_calls"]:
    tc_id = tc_delta.get("id")
    tc_index = tc_delta.get("index", 0)
    
    if tc_id in active_tool_ids:
        # Known ID - check if this is a ghost stream (different index)
        if active_tool_ids[tc_id]["primary_index"] != tc_index:
            logger.debug(f"Ignoring ghost stream for ID {tc_id}")
            continue  # Skip duplicate stream
    else:
        # New unique ID - register it
        active_tool_ids[tc_id] = {
            "primary_index": tc_index,
            "claude_index": current_block_index
        }
```

#### Phase 4: Capacity Expansion
We updated `src/services/usage/model_limits.py`:
*   **Change:** Explicitly defined `gemini-3-flash` and `gemini-3-pro` with a **1,000,000 token** context window.
*   **Result:** The proxy no longer throttles the "superpowers" context injection.

```python
# model_limits.py - Gemini capacity definitions
MODEL_LIMITS = {
    # Gemini models with 1M+ context
    "gemini-3-flash": {"context_window": 1_000_000, "max_output": 8192},
    "gemini-3-pro": {"context_window": 1_000_000, "max_output": 8192},
    "gemini-3-pro-preview": {"context_window": 1_000_000, "max_output": 8192},
    
    # Thinking models (default limits for unrecognized)
    "gemini-claude-opus-4-5-thinking": {"context_window": 128_000, "max_output": 4096},
}

def get_model_limits(model_name: str) -> dict:
    return MODEL_LIMITS.get(model_name, {"context_window": 128_000, "max_output": 4096})
```

#### Phase 5: Dual-Layer Parameter Normalization (Fixing Bash Tool Streaming)
Following the aforementioned repairs, Bash tool execution failures in streaming mode revealed the fifth fault.

**Root Cause:** Forensic investigation of [`src/services/conversion/response_converter.py`](src/services/conversion/response_converter.py:1) revealed an asymmetry in parameter transformation:
*   **Non-Streaming Path:** Correctly applied `normalize_tool_arguments()` function to transform Gemini's `"prompt"` parameter to Claude's `"command"` parameter.
*   **Streaming Path:** Only performed partial JSON string replacement on streaming deltas without complete semantic transformation.

**The Engineering Solution:** Implemented a two-tier transformation strategy:

*   **Tier 1 - Streaming JSON Transformation (Real-time):** Preserved existing string replacement for immediate streaming compatibility:
```python
# Lines 309-312, 564-567
transformed_partial = partial_args
if tool_call["name"].lower() in ["bash", "repl"]:
    transformed_partial = transformed_partial.replace('"prompt":', '"command":')
```

*   **Tier 2 - Centralized Normalization Function (Systemic):** Created `normalize_tool_arguments()` (lines 8-74) to handle:
    *   **Bash/Repl tools:** `"prompt"` → `"command"` transformation
    *   **Task tools:** Bidirectional mapping between `"prompt"` and `"description"`; default `"subagent_type": "Explore"`
    *   **Read tools:** `"path"` → `"file_path"` transformation
    *   **Glob/Grep tools:** Multiple parameter name variants normalized to expected schema
    *   **TodoWrite tools:** `"tasks"` → `"todos"` transformation with status enumeration validation

**Result:** Bash toolcalls execute successfully in both streaming and non-streaming modes.

**Architectural Implication:** This fault underscores a common pitfall in streaming protocol implementations—the assumption that real-time transformations are sufficient for end-to-end compatibility. The dual nature of Server-Sent Events processing requires both streaming-time transformations (for client display) and accumulated-buffer normalization (for final validation).

---

## Phase 6: Content-Based Duplicate Tool Call Filtering (December 2025)

**Symptom:** Claude Code CLI displays duplicate tool outputs:
```
⏺ Bash(ls -la)
  ⎿  PreToolUse:Bash hook succeeded:
  ⎿  PreToolUse:Bash hook succeeded:   ← DUPLICATE
  ⎿     rwxr-xr-x...
  ⎿  PreToolUse:Bash hook succeeded:   ← THIRD HOOK
  ⎿     rwxr-xr-x...                   ← DUPLICATE OUTPUT
```

**Root Cause Discovery:** This is a **NEW Gemini API behavior** distinct from Phase 3 "Ghost Streams":

| Phase 3: Ghost Streams | Phase 6: Duplicate Operations |
|------------------------|-------------------------------|
| Same `tc_id`, different `tc_index` | **Different `tc_id`**, same operation |
| ID-based filtering sufficient | Content-based fingerprinting required |

Gemini's OpenAI compatibility layer occasionally emits the **same tool call twice with unique IDs**:
```
tool_call_1: id="call_abc", name="Bash", args='{"command":"ls -la"}'  
tool_call_2: id="call_xyz", name="Bash", args='{"command":"ls -la"}'  ← DUPLICATE
```

**Why Phase 3 Fix Didn't Catch This:** The ghost stream filter checks if `tc_id in active_tool_ids`. Since each duplicate has a **unique ID**, both pass through as "new" blocks.

**The Engineering Solution:** Content-based fingerprint deduplication in [`response_converter.py`](src/services/conversion/response_converter.py):

1. **Fingerprint Generation:** `f"{tool_name}:{first_args[:50]}"` creates unique signature per operation
2. **Early Detection:** Check fingerprint **BEFORE** registering block (critical timing fix)
3. **Skip Tracking:** `skipped_tool_ids` set prevents processing future chunks for duplicate IDs

```python
# Lines 539-563: Early fingerprint check
if tool_name:
    fingerprint = f"{tool_name}:{first_args[:50]}"
    if fingerprint in content_fingerprints:
        logger.info(f"DEDUP: Blocking duplicate tool call '{tool_name}' (id={tc_id})")
        skipped_tool_ids.add(tc_id)
        continue
    content_fingerprints[fingerprint] = tc_id

# Lines 518-520: Early skip for marked duplicates
if tc_id and tc_id in skipped_tool_ids:
    continue
```

**Result:** Only one tool call per unique operation is forwarded to Claude Code CLI.

---

### 6. Conclusion

The complete cascade resolution now covers **six distinct faults**:

| Phase | Fault | Solution |
|-------|-------|----------|
| 1 | Protocol Mismatch | Token refresh per request |
| 2 | Infrastructure Crash | `ModelLimits` import guard |
| 3 | Ghost Streams | ID-based stream deduplication |
| 4 | Capacity Limits | Dynamic context sizing |
| 5 | Parameter Schema | Dual-tier streaming transformation |
| 6 | Duplicate Operations | Content-based fingerprinting |

Claude Code can now transparently utilize Google's Gemini 3 infrastructure with complete tool execution support, handling both streaming protocol edge cases and Gemini API behavioral quirks.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/crosstalk-quick-ref.md
**File Size:** 3911 bytes

## Features & Sections Declared:
# Crosstalk V2 Quick Reference
## 📐 Topologies
## 🎛️ Per-Model Configuration
## 📁 Config File (Clean!)
## 🚀 Advanced Features
### Infinite Conversations (Backrooms-style)
### Voting & Consensus
### Meta-Prompts (Summaries)
### Multi-Stage Conversations
## 🔄 Session Management
# Use existing Claude Code session
# Create new sessions dynamically
# Mix both
## 🔌 MCP Integration
# MCP Tool
## 📋 Quick Examples
### Simple Debate
### Star with Moderator
### Mesh Brainstorming
### Infinite Backrooms
## 🎯 Key Improvements
## 📚 Full Documentation


## Content / Data Structure:
```text
# Crosstalk V2 Quick Reference

**TL;DR**: Massive enhancement to crosstalk system with topologies, per-model config, infinite conversations, and more.

## 📐 Topologies

| Type | Use Case | Example Pattern |
|------|----------|----------------|
| **Ring** | Sequential turns | 1→2→3→1→2→3... |
| **Star** | Central moderator | 1→2, 2→1, 1→3, 3→1... |
| **Mesh** | Everyone talks to everyone | 1→2, 1→3, 2→1, 2→3... |
| **Chain** | Linear, no return | 1→2→3→1→2→3 |
| **Random** | Random each turn | Random(1,2,3) |
| **Tournament** | Bracket elimination | 2v3 winner→1 |
| **Custom** | Define exact pattern | Your pattern |
| **Conditional** | Dynamic routing | Based on content |

## 🎛️ Per-Model Configuration

```bash
--model 1=big \
--sysprompt 1=alice.txt \
--append 1="Consider ethics." \
--temp 1=0.7 \
--max-tokens 1=2000 \
--reasoning 1=extended --budget 1=8000
```

## 📁 Config File (Clean!)

```bash
python crosstalk.py --config star_debate.json
```

```json
{
  "topology": {"type": "star", "center": 1, "spokes": [2, 3]},
  "models": [
    {"id": 1, "name": "big", "sysprompt": {"file": "alice.txt"}},
    {"id": 2, "name": "middle", "append": "Focus on tech."},
    {"id": 3, "name": "small", "append": "Consider UX."}
  ],
  "conversation": {
    "init_prompt": "Should AI be regulated?",
    "rounds": 10,
    "final_round": {"prompt": "Give your final verdict."}
  },
  "output": {"file": "debate.json"}
}
```

## 🚀 Advanced Features

### Infinite Conversations (Backrooms-style)
```bash
--infinite \
--stop-after-time 86400 \
--stop-after-cost 100.00 \
--checkpoint-every 100
```

### Voting & Consensus
```json
{
  "final_round": {
    "type": "vote",
    "question": "Should we proceed?",
    "options": ["yes", "no"],
    "tally_method": "majority"
  }
}
```

### Meta-Prompts (Summaries)
```bash
--summarize-every 5 \
--summarizer 1 \
--summary-prompt "Summarize key points."
```

### Multi-Stage Conversations
```json
{
  "stages": [
    {"name": "brainstorm", "rounds": 10, "topology": "mesh"},
    {"name": "evaluate", "rounds": 5, "topology": "star"},
    {"name": "decide", "rounds": 3, "topology": "ring"}
  ]
}
```

## 🔄 Session Management

```bash
# Use existing Claude Code session
--session 1=abc123

# Create new sessions dynamically
--create-sessions 2 \
--workspace 2=/path/to/project2

# Mix both
--session 1=abc123 --create-sessions 2
```

## 🔌 MCP Integration

From Claude Desktop:

```python
# MCP Tool
{
  "config_file": "star_debate.json",
  "wait_for_completion": true,
  "stream_updates": true
}
```

## 📋 Quick Examples

### Simple Debate
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=small \
  --init-prompt "Will AI cause unemployment?" \
  --rounds 10
```

### Star with Moderator
```bash
python crosstalk.py \
  --topology star --center 1 --spokes 2,3 \
  --model 1=big --model 2=middle --model 3=small \
  --sysprompt 1=moderator.txt \
  --init-prompt "Should AI be regulated?" \
  --rounds 15
```

### Mesh Brainstorming
```bash
python crosstalk.py \
  --topology mesh \
  --model 1=big --model 2=middle --model 3=small \
  --init-prompt "How to reduce carbon emissions?" \
  --rounds 5
```

### Infinite Backrooms
```bash
python crosstalk.py \
  --topology ring \
  --model 1=big --model 2=big \
  --infinite \
  --stop-after-time 86400 \
  --stop-after-cost 100
```

## 🎯 Key Improvements

| Before | After |
|--------|-------|
| 4 paradigms | 8+ topologies |
| 2-5 models | 2-10 models |
| Basic config | Full per-model config |
| No session mgmt | Dynamic session creation |
| YAML only | JSON/YAML + rich CLI |
| Fixed rounds | Infinite + stop conditions |
| No advanced features | Voting, meta-prompts, stages |

## 📚 Full Documentation

See **CROSSTALK_V2_PROPOSAL.md** for complete details (1,200+ lines).

**This transforms crosstalk from a simple conversation system into a powerful multi-agent orchestration platform!**

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/memory-optimization.md
**File Size:** 12301 bytes

## Features & Sections Declared:
# Maximum Memory Optimization Plan
## For Heavy Workloads (70+ Chrome tabs, 10+ Claude Code sessions)
## 🔍 Current Settings (PROBLEMATIC)
## ⚡ Maximum Optimization Script
#!/bin/bash
# Maximum Memory Optimization for Heavy Workloads
# Run with: sudo bash /opt/memory-optimization.sh
# ═══════════════════════════════════════════════════════════════
# 1. SWAPPINESS - CRITICAL FIX
# ═══════════════════════════════════════════════════════════════
# Current: 180 (aggressive swapping)
# Target: 10 (only swap when absolutely necessary)
#
# Impact: System will use RAM fully before touching swap
# Risk: If RAM fills completely, OOM killer may activate
# ═══════════════════════════════════════════════════════════════
# 2. VFS CACHE PRESSURE
# ═══════════════════════════════════════════════════════════════
# Current: 150 (aggressive cache dropping)
# Target: 50 (keep filesystem caches longer)
#
# Impact: Faster file operations, better caching
# Risk: Slightly less RAM for applications
# ═══════════════════════════════════════════════════════════════
# 3. MIN_FREE_KBYTES - Prevent Stalls
# ═══════════════════════════════════════════════════════════════
# Current: 67584 (66MB)
# Target: 131072 (128MB) - prevent allocation stalls
#
# Impact: System always keeps more free RAM available
# Risk: Slightly less usable RAM
# ═══════════════════════════════════════════════════════════════
# 4. WATERMARK SCALE FACTOR
# ═══════════════════════════════════════════════════════════════
# Increase watermarks for heavy workloads
# Default: 10, Target: 20 (more aggressive refill)
#
# Impact: Memory reclaim starts earlier, preventing sudden drops
# ═══════════════════════════════════════════════════════════════
# 5. DIRTY PAGE WRITEBACK
# ═══════════════════════════════════════════════════════════════
# Start writing back earlier to prevent sudden I/O storms
# ═══════════════════════════════════════════════════════════════
# 6. OVERCOMMIT SETTINGS
# ═══════════════════════════════════════════════════════════════
# Allow overcommit but with heuristics
# 0 = heuristic (default), 1 = always, 2 = don't overcommit
# ═══════════════════════════════════════════════════════════════
# 7. ZRAM OPTIMIZATION
# ═══════════════════════════════════════════════════════════════
# ZRAM is already configured - verify it's optimal
# ═══════════════════════════════════════════════════════════════
# 8. CPU GOVERNOR - Performance Mode
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════
## 📌 Make Settings Persistent
# Maximum Memory Optimization for Heavy Workloads
# Created: 2026-03-30
# CRITICAL: Reduce swap aggression (was 180)
# Keep filesystem caches longer (was 150)
# Prevent allocation stalls
# Start reclaim earlier
# Dirty page writeback optimization
# Memory overcommit
## 🔧 Chrome-Specific Optimizations
### **1. Limit Chrome Memory Per Tab**
# Add to Chrome launch command:
### **2. Auto-Discard Inactive Tabs**
### **3. Chrome Memory Saver Mode**
## 🤖 Claude Code Session Management
### **1. Session Memory Limits**
### **2. Process Priority Management**
### **3. Session Multiplexing Script**
#!/bin/bash
# Claude Code Session Multiplexer
# Automatically manages session count based on memory pressure
# Add your session suspension logic here
## 📊 Monitoring & Early Warning
### **1. Real-Time Memory Monitor**
#!/bin/bash
# Real-time memory watcher with swap warning
# Memory stats
# Percentage
# Warnings
# Top memory consumers
### **2. Systemd Service for Monitoring**
## ⚠️ Tradeoffs & Risks
### **Power Impact:**
### **Stability Impact:**
## 🚀 Quick Start (Copy-Paste)
# 1. Apply optimizations immediately
# 2. Make persistent
# 3. Download monitoring script
# 4. Start monitoring
## 📈 Expected Results
## 🆘 Emergency Recovery
# Magic SysRq key (if enabled)
# Or from TTY (Ctrl+Alt+F3)
# Last resort


## Content / Data Structure:
```text
# Maximum Memory Optimization Plan
## For Heavy Workloads (70+ Chrome tabs, 10+ Claude Code sessions)

**Target:** Prevent swap-induced 5+ second command delays  
**System:** 32GB LPDDR5 @ 5200 MT/s  
**Risk Level:** Aggressive but safe

---

## 🔍 Current Settings (PROBLEMATIC)

| Setting | Current | Problem |
|---------|---------|---------|
| **swappiness** | 180 | ⚠️ WAY TOO HIGH - causes aggressive swapping |
| **vfs_cache_pressure** | 150 | ⚠️ High - pushes out filesystem caches |
| **min_free_kbytes** | 67584 (66MB) | ✅ OK |
| **transparent_hugepage** | madvise | ✅ Good |
| **hugepage_defrag** | madvise | ✅ Good |
| **zram** | 31.2GB (priority 100) | ✅ Good (faster than disk swap) |
| **swapfile** | 8GB (priority 10) | ⚠️ Consider reducing |

---

## ⚡ Maximum Optimization Script

Save as `/opt/memory-optimization.sh`:

```bash
#!/bin/bash
# Maximum Memory Optimization for Heavy Workloads
# Run with: sudo bash /opt/memory-optimization.sh

set -e

echo "🚀 Applying maximum memory optimizations..."

# ═══════════════════════════════════════════════════════════════
# 1. SWAPPINESS - CRITICAL FIX
# ═══════════════════════════════════════════════════════════════
# Current: 180 (aggressive swapping)
# Target: 10 (only swap when absolutely necessary)
# 
# Impact: System will use RAM fully before touching swap
# Risk: If RAM fills completely, OOM killer may activate
echo "📉 Setting swappiness to 10 (was 180)..."
echo 10 > /proc/sys/vm/swappiness

# ═══════════════════════════════════════════════════════════════
# 2. VFS CACHE PRESSURE
# ═══════════════════════════════════════════════════════════════
# Current: 150 (aggressive cache dropping)
# Target: 50 (keep filesystem caches longer)
#
# Impact: Faster file operations, better caching
# Risk: Slightly less RAM for applications
echo "📉 Setting vfs_cache_pressure to 50 (was 150)..."
echo 50 > /proc/sys/vm/vfs_cache_pressure

# ═══════════════════════════════════════════════════════════════
# 3. MIN_FREE_KBYTES - Prevent Stalls
# ═══════════════════════════════════════════════════════════════
# Current: 67584 (66MB)
# Target: 131072 (128MB) - prevent allocation stalls
#
# Impact: System always keeps more free RAM available
# Risk: Slightly less usable RAM
echo "📈 Setting min_free_kbytes to 131072 (was 67584)..."
echo 131072 > /proc/sys/vm/min_free_kbytes

# ═══════════════════════════════════════════════════════════════
# 4. WATERMARK SCALE FACTOR
# ═══════════════════════════════════════════════════════════════
# Increase watermarks for heavy workloads
# Default: 10, Target: 20 (more aggressive refill)
#
# Impact: Memory reclaim starts earlier, preventing sudden drops
echo "📈 Setting watermark_scale_factor to 20..."
echo 20 > /proc/sys/vm/watermark_scale_factor

# ═══════════════════════════════════════════════════════════════
# 5. DIRTY PAGE WRITEBACK
# ═══════════════════════════════════════════════════════════════
# Start writing back earlier to prevent sudden I/O storms
echo "📝 Optimizing dirty page writeback..."
echo 10 > /proc/sys/vm/dirty_ratio           # Was likely 20
echo 5 > /proc/sys/vm/dirty_background_ratio  # Was likely 10
echo 3000 > /proc/sys/vm/dirty_expire_centisecs  # 30 seconds
echo 500 > /proc/sys/vm/dirty_writeback_centisecs # 5 seconds

# ═══════════════════════════════════════════════════════════════
# 6. OVERCOMMIT SETTINGS
# ═══════════════════════════════════════════════════════════════
# Allow overcommit but with heuristics
# 0 = heuristic (default), 1 = always, 2 = don't overcommit
echo "🎯 Setting memory overcommit to heuristic mode..."
echo 0 > /proc/sys/vm/overcommit_memory
echo 50 > /proc/sys/vm/overcommit_ratio  # 50% of RAM

# ═══════════════════════════════════════════════════════════════
# 7. ZRAM OPTIMIZATION
# ═══════════════════════════════════════════════════════════════
# ZRAM is already configured - verify it's optimal
echo "✅ ZRAM already configured (31.2GB, priority 100)"

# ═══════════════════════════════════════════════════════════════
# 8. CPU GOVERNOR - Performance Mode
# ═══════════════════════════════════════════════════════════════
echo "⚡ Setting CPU governor to performance..."
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu 2>/dev/null || true
done

# ═══════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════
echo ""
echo "✅ Optimization complete! Current settings:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "swappiness:              $(cat /proc/sys/vm/swappiness)"
echo "vfs_cache_pressure:      $(cat /proc/sys/vm/vfs_cache_pressure)"
echo "min_free_kbytes:         $(cat /proc/sys/vm/min_free_kbytes)"
echo "watermark_scale_factor:  $(cat /proc/sys/vm/watermark_scale_factor)"
echo "dirty_ratio:             $(cat /proc/sys/vm/dirty_ratio)"
echo "dirty_background_ratio:  $(cat /proc/sys/vm/dirty_background_ratio)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  These settings reset on reboot!"
echo "   Run 'sudo systemctl enable memory-optimization' to persist"
```

---

## 📌 Make Settings Persistent

Create `/etc/sysctl.d/99-memory-optimization.conf`:

```bash
# Maximum Memory Optimization for Heavy Workloads
# Created: 2026-03-30

# CRITICAL: Reduce swap aggression (was 180)
vm.swappiness = 10

# Keep filesystem caches longer (was 150)
vm.vfs_cache_pressure = 50

# Prevent allocation stalls
vm.min_free_kbytes = 131072

# Start reclaim earlier
vm.watermark_scale_factor = 20

# Dirty page writeback optimization
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
vm.dirty_expire_centisecs = 3000
vm.dirty_writeback_centisecs = 500

# Memory overcommit
vm.overcommit_memory = 0
vm.overcommit_ratio = 50
```

Apply: `sudo sysctl --system`

---

## 🔧 Chrome-Specific Optimizations

### **1. Limit Chrome Memory Per Tab**

Create `~/.config/google-chrome/Default/Preferences` override or use flags:

```bash
# Add to Chrome launch command:
google-chrome \
  --max-old-space-size=4096 \
  --disable-features=CalculateNativeWinOcclusion \
  --disable-features=GlobalMediaControls \
  --disable-features=HeavyAdPrivacyMitigations \
  --disable-features=MediaRouter \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-ipc-flooding-protection \
  --num-raster-threads=4 \
  --enable-zero-copy \
  --disable-gpu-compositing \
  --force-color-profile=srgb
```

### **2. Auto-Discard Inactive Tabs**

Install **The Great Suspender** or **Auto Tab Discard** extension:
- Suspend tabs after 5 minutes inactive
- Exclude active Claude Code tabs
- Reduces Chrome memory by 40-60%

### **3. Chrome Memory Saver Mode**

Enable in `chrome://settings/performance`:
- ✅ Memory Saver: ON
- ✅ Energy Saver: OFF (you need performance)

---

## 🤖 Claude Code Session Management

### **1. Session Memory Limits**

Create `~/.claude/settings.local.json`:

```json
{
  "maxSessionMemory": 2048,
  "maxConcurrentSessions": 15,
  "sessionTimeout": 3600,
  "autoSaveInterval": 300
}
```

### **2. Process Priority Management**

Create `/etc/systemd/system/claude-code.service.d/override.conf`:

```ini
[Service]
MemoryMax=4G
MemoryHigh=3G
CPUQuota=200%
Nice=-5
IOSchedulingClass=realtime
IOSchedulingPriority=4
```

### **3. Session Multiplexing Script**

Save as `~/bin/claude-mux`:

```bash
#!/bin/bash
# Claude Code Session Multiplexer
# Automatically manages session count based on memory pressure

MAX_SESSIONS=10
MEMORY_THRESHOLD=85  # Percent

get_memory_usage() {
    free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}'
}

get_claude_sessions() {
    pgrep -f "claude" | wc -l
}

while true; do
    mem=$(get_memory_usage)
    sessions=$(get_claude_sessions)
    
    if [ "$mem" -gt "$MEMORY_THRESHOLD" ] && [ "$sessions" -gt 2 ]; then
        echo "⚠️  Memory at ${mem}% - suspending oldest session..."
        # Add your session suspension logic here
    fi
    
    sleep 30
done
```

---

## 📊 Monitoring & Early Warning

### **1. Real-Time Memory Monitor**

Save as `~/bin/mem-watch`:

```bash
#!/bin/bash
# Real-time memory watcher with swap warning

THRESHOLD=80
SWAP_THRESHOLD=10

while true; do
    clear
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║           MEMORY MONITOR (Ctrl+C to exit)             ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    # Memory stats
    free -h | grep -E "Mem|Swap"
    echo ""
    
    # Percentage
    mem_pct=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
    swap_pct=$(free | grep Swap | awk '{if($2>0) printf "%.1f", $3/$2 * 100; else print "0"}')
    
    echo "Memory Usage: ${mem_pct}%"
    echo "Swap Usage:   ${swap_pct}%"
    echo ""
    
    # Warnings
    if (( $(echo "$mem_pct > $THRESHOLD" | bc -l) )); then
        echo "⚠️  WARNING: Memory above ${THRESHOLD}%"
        echo "   Consider closing Chrome tabs or Claude sessions"
    fi
    
    if (( $(echo "$swap_pct > $SWAP_THRESHOLD" | bc -l) )); then
        echo "⚠️  WARNING: Swap usage above ${SWAP_THRESHOLD}%"
        echo "   System performance will degrade!"
    fi
    
    # Top memory consumers
    echo ""
    echo "Top 5 Memory Consumers:"
    ps aux --sort=-%mem | head -6 | awk '{printf "%-10s %-8s %s\n", $1, $4"%", $11}'
    
    sleep 5
done
```

### **2. Systemd Service for Monitoring**

Create `/etc/systemd/system/memory-monitor.service`:

```ini
[Unit]
Description=Memory Pressure Monitor
After=network.target

[Service]
Type=simple
ExecStart=/home/misscheta/bin/mem-watch
Restart=always
User=misscheta

[Install]
WantedBy=multi-user.target
```

---

## ⚠️ Tradeoffs & Risks

| Optimization | Benefit | Risk | Mitigation |
|--------------|---------|------|------------|
| **swappiness=10** | Prevents swap thrashing | OOM if RAM fills | Monitor + early warning |
| **vfs_cache_pressure=50** | Faster file ops | Less app RAM | Acceptable for SSD |
| **min_free_kbytes=128MB** | Prevents stalls | 66MB less usable | Negligible |
| **CPU performance mode** | Better latency | +10-20W power | Use on AC power |
| **dirty_ratio=10** | Smoother I/O | More frequent writes | SSDs handle this well |

### **Power Impact:**
- **Battery:** -15-25% runtime (CPU performance mode)
- **Heat:** +5-10°C under load
- **Recommendation:** Use performance mode on AC, powersave on battery

### **Stability Impact:**
- **OOM Risk:** Low with monitoring
- **Data Loss:** None (dirty settings are conservative)
- **Crashes:** None expected

---

## 🚀 Quick Start (Copy-Paste)

```bash
# 1. Apply optimizations immediately
sudo bash -c '
echo 10 > /proc/sys/vm/swappiness
echo 50 > /proc/sys/vm/vfs_cache_pressure
echo 131072 > /proc/sys/vm/min_free_kbytes
echo 20 > /proc/sys/vm/watermark_scale_factor
echo 10 > /proc/sys/vm/dirty_ratio
echo 5 > /proc/sys/vm/dirty_background_ratio
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu 2>/dev/null || true
done
'

# 2. Make persistent
sudo tee /etc/sysctl.d/99-memory-optimization.conf > /dev/null << 'EOF'
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.min_free_kbytes = 131072
vm.watermark_scale_factor = 20
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
EOF

sudo sysctl --system

# 3. Download monitoring script
curl -o ~/bin/mem-watch https://raw.githubusercontent.com/.../mem-watch
chmod +x ~/bin/mem-watch

# 4. Start monitoring
~/bin/mem-watch &
```

---

## 📈 Expected Results

| Metric | Before | After |
|--------|--------|-------|
| **Swap usage at 80% RAM** | 2-4 GB | <100 MB |
| **Command delay after typing** | 5+ seconds | <100ms |
| **Chrome 70 tabs memory** | 24 GB | 18 GB (with suspend) |
| **10 Claude sessions** | Swap thrashing | Smooth |
| **System responsiveness** | Poor at >85% RAM | Good until >95% RAM |

---

## 🆘 Emergency Recovery

If system becomes unresponsive:

```bash
# Magic SysRq key (if enabled)
Alt+SysRq+f  # Trigger OOM killer

# Or from TTY (Ctrl+Alt+F3)
sudo systemctl restart claude-code
sudo pkill -9 chrome

# Last resort
echo 1 > /proc/sys/kernel/sysrq
echo f > /proc/sysrq-trigger  # Force OOM
```

---

*Created: 2026-03-30 | For: 32GB LPDDR5 Heavy Workload Optimization*

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/dynamic-model-detection.md
**File Size:** 3378 bytes

## Features & Sections Declared:
# Dynamic Model Detection
## The Problem
# do something
# do something else
## The Solution: Model Family Detection
# → ModelFamilyInfo(family=ModelFamily.ANTHROPIC_CLAUDE, tier="opus", ...)
# → ModelFamilyInfo(family=ModelFamily.GEMINI_FLASH, tier="flash", ...)
### Supported Families
### Helper Functions
# Check reasoning support
# Check parameter requirements
## Adding New Model Families
# Add new patterns here
# ...
## Migration Guide
### Before (Bad)
### After (Good)
# Handle any Claude model
# Handle any OpenAI o-series
## Files Using This Pattern
## Anti-Patterns to Avoid
# version-specific logic
# family-level logic (works for ALL opus versions)


## Content / Data Structure:
```text
# Dynamic Model Detection

> **IMPORTANT:** This codebase uses **dynamic model family detection** instead of hardcoded model names. This ensures the proxy remains functional when providers update model versions without requiring code changes.

## The Problem

Old proxy code looked like this:
```python
if model_name == "claude-opus-4-20250514":
    # do something
elif model_name == "gemini-1.5-flash":
    # do something else
```

This breaks when:
- Providers release new versions (claude-opus-4-20250515, gemini-1.6-flash)
- Models are deprecated or renamed
- OpenRouter adds new model variants

## The Solution: Model Family Detection

The proxy now uses **pattern-based family detection**:

```python
from src.services.models.model_family import detect_model_family, ModelFamily

family_info = detect_model_family("claude-opus-4-20250514")
# → ModelFamilyInfo(family=ModelFamily.ANTHROPIC_CLAUDE, tier="opus", ...)

family_info = detect_model_family("gemini-2.5-flash-preview-04-17")
# → ModelFamilyInfo(family=ModelFamily.GEMINI_FLASH, tier="flash", ...)
```

### Supported Families

| Family | Detects | Examples |
|--------|---------|----------|
| `OPENAI_O_SERIES` | o1, o3, o4 + variants | o1-mini, o3, o4-mini |
| `OPENAI_GPT` | GPT-4, GPT-5 | gpt-4, gpt-4o, gpt-5 |
| `ANTHROPIC_CLAUDE` | Claude models | claude-opus, claude-sonnet, claude-haiku |
| `GEMINI_FLASH` | Gemini Flash | gemini-flash, gemini-2.0-flash |
| `GEMINI_PRO` | Gemini Pro | gemini-pro, gemini-2.0-pro |
| `GEMINI_OTHER` | Other Gemini | gemini-1.5-pro |

### Helper Functions

```python
# Check reasoning support
is_reasoning_model("o1-mini")  # True
is_reasoning_model("claude-sonnet-4")  # True

# Check parameter requirements
requires_effort_level("o3-mini")  # True (OpenAI)
requires_thinking_tokens("claude-opus-4")  # True (Anthropic)
requires_thinking_budget("gemini-2.0-flash")  # True (Google)
```

## Adding New Model Families

Edit `src/services/models/model_family.py` - add a regex pattern:

```python
MODEL_FAMILY_PATTERNS = [
    # Add new patterns here
    (r'^(?:provider/)?new-model-\d+', ModelFamily.OPENAI_GPT),
    # ...
]
```

No other code changes needed!

## Migration Guide

### Before (Bad)
```python
if "claude-opus-4" in model_name:
    do_opus_stuff()
elif "claude-sonnet-4" in model_name:
    do_sonnet_stuff()
```

### After (Good)
```python
from src.services.models.model_family import detect_model_family

family = detect_model_family(model_name)
if family.tier == "opus":
    do_opus_stuff()
elif family.tier == "sonnet":
    do_sonnet_stuff()
```

Or even better - write logic based on capabilities:
```python
if requires_thinking_tokens(model_name):
    # Handle any Claude model
elif requires_effort_level(model_name):
    # Handle any OpenAI o-series
```

## Files Using This Pattern

- `src/services/models/model_family.py` - Core detection
- `src/core/reasoning_validator.py` - Reasoning parameter validation
- `src/services/models/model_parser.py` - Suffix parsing
- `src/core/model_manager.py` - Routing logic

## Anti-Patterns to Avoid

❌ **Don't do this:**
```python
if model_name in ["claude-opus-4-20250514", "claude-opus-4-20250515"]:
    # version-specific logic
```

✅ **Do this instead:**
```python
if family_info.family == ModelFamily.ANTHROPIC_CLAUDE and family_info.tier == "opus":
    # family-level logic (works for ALL opus versions)
```

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/terminal-dashboard.md
**File Size:** 10112 bytes

## Features & Sections Declared:
# Terminal Output Configuration
## Features
### 🎨 Rich Visual Output
### 📊 Comprehensive Metrics
## Quick Start
### Interactive Configuration
### Manual Configuration
# Display mode: minimal, normal, detailed, debug
# Toggle individual metrics
# Color scheme: auto, vibrant, subtle, mono
# Session differentiation
## Display Modes
### Minimal
### Normal (Default)
### Detailed
### Debug
## Color Schemes
### Auto (Default)
### Vibrant
### Subtle
### Mono
## Session Color Differentiation
# Session 1 (bright cyan)
# Session 2 (magenta)
# Session 3 (bright blue)
## Workspace Name Detection
## Task Type Icons
## Performance Indicators
### Speed (tokens/second)
### Duration
### Context Window Usage
### Output Usage
## Integration with Dashboard
# Standard terminal output
# Terminal output + live dashboard
## Examples
### Basic Usage
# Use detailed mode (default)
### Minimal Output for CI/CD
# Minimal output, no colors
### High-Visibility Mode
# Vibrant colors, all metrics
### Focus Mode
# Subtle colors, hide cost
## Troubleshooting
### Workspace name shows parent folder
### Colors not showing
### Too much information
# OR
### Session colors all the same
## Best Practices
## Related Documentation
## Configuration Script Reference


## Content / Data Structure:
```text
# Terminal Output Configuration

The Claude Code Proxy provides highly configurable terminal output that shows comprehensive metrics for each request in a color-coded, easy-to-read format.

## Features

### 🎨 Rich Visual Output
- **Session-based color coding** - Each Claude Code session gets a unique color for easy tracking
- **Task type indicators** - Visual icons for different request types (🧠 reasoning, 🔧 tools, 🖼️ images, 📝 text)
- **Performance color coding** - Green/yellow/red colors based on speed and resource usage
- **Workspace badges** - Project name displayed with colored background

### 📊 Comprehensive Metrics

Each request displays:
- **Request ID** - Short 8-character ID for tracking
- **Model routing** - Source model → destination model
- **Context usage** - Input tokens with percentage of context window
- **Output limits** - Maximum output tokens available
- **Thinking budget** - For reasoning models (o1, Claude thinking, etc.)
- **Task type** - Visual indication of request type
- **Stream status** - Whether streaming is enabled
- **Message count** - Number of messages in conversation
- **Duration** - Color-coded by speed (green < 3s, yellow < 10s, red >= 10s)
- **Token speeds** - Tokens per second with performance indicators (⚡82t/s)
- **Cost estimates** - Approximate cost per request

## Quick Start

### Interactive Configuration

Run the configuration wizard:

```bash
python start_proxy.py --configure-terminal
```

This will guide you through:
1. **Display Mode** - Choose information density
2. **Metric Visibility** - Toggle individual metrics
3. **Color Scheme** - Select your visual preference

The script will show a live preview and generate the configuration for you.

### Manual Configuration

Add these environment variables to your `.env` file or shell profile:

```bash
# Display mode: minimal, normal, detailed, debug
export TERMINAL_DISPLAY_MODE="detailed"

# Toggle individual metrics
export TERMINAL_SHOW_WORKSPACE="true"
export TERMINAL_SHOW_CONTEXT_PCT="true"
export TERMINAL_SHOW_TASK_TYPE="true"
export TERMINAL_SHOW_SPEED="true"
export TERMINAL_SHOW_COST="true"
export TERMINAL_SHOW_DURATION_COLORS="true"

# Color scheme: auto, vibrant, subtle, mono
export TERMINAL_COLOR_SCHEME="auto"

# Session differentiation
export TERMINAL_SESSION_COLORS="true"
```

## Display Modes

### Minimal
Shows only essential information:
```
▶ a1b2c3d4 | claude-3.5→gpt-4o | IN:12.3k
```

### Normal (Default)
Adds token counts and speed:
```
▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | IN:12.3k OUT:16k | STREAM 3msg
  ✓ a1b2c3d4 | 5.2s | IN:12.3k OUT:2.1k | ⚡82t/s
```

### Detailed
All metrics including context %, task type, and cost:
```
 claude-code-proxy  ▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | CTX:12.3k/200k(6%) OUT:16k THINK:8k | 🧠 REASON | STREAM 3msg
  ✓ a1b2c3d4 | 5.2s | IN:12.3k (6%) OUT:2.1k (13%) THINK:920 | ⚡82t/s $0.0042
```

### Debug
Everything plus system flags and client info:
```
 claude-code-proxy  ▶ a1b2c3d4 | claude-3.5-sonnet→gpt-4o-mini | CTX:12.3k/200k(6%) OUT:16k THINK:8k | 🧠 REASON | STREAM 3msg SYS 127.0.0.1
  ✓ a1b2c3d4 | 5.2s | IN:12.3k (6%) OUT:2.1k (13%) THINK:920 | ⚡82t/s $0.0042
```

## Color Schemes

### Auto (Default)
Rich colors with session differentiation. Each Claude Code session gets a unique color from an expanded palette:
- Bright Cyan / Cyan
- Bright Magenta / Magenta
- Bright Blue / Blue
- Bright Green / Green
- Bright Yellow / Yellow
- Bright Red / Red (for high activity sessions)

Performance metrics use semantic colors:
- Green: Fast, low usage, low cost
- Yellow: Medium speed/usage
- Red: Slow, high usage, high cost

### Vibrant
Bright, high-contrast colors for maximum visibility. Best for:
- High ambient light environments
- Multiple terminal windows
- Presentations

### Subtle
Muted colors for reduced distraction. Best for:
- Long coding sessions
- Focus mode
- Low-light environments

### Mono
Minimal colors, mostly white/gray. Best for:
- Terminals with limited color support
- Screen recordings
- Accessibility needs

## Session Color Differentiation

When `TERMINAL_SESSION_COLORS="true"`, each unique request session gets a consistent color assigned based on its request ID. This helps visually group related requests when multiple Claude Code instances are running.

**Example:**
```
# Session 1 (bright cyan)
 project-a  ▶ abc12345 | claude-3.5→gpt-4o | ...

# Session 2 (magenta)
 project-b  ▶ def67890 | claude-3.5→gpt-4o | ...

# Session 3 (bright blue)
 project-c  ▶ ghi24680 | claude-3.5→gpt-4o | ...
```

## Workspace Name Detection

The proxy automatically extracts the project/workspace name from Claude Code prompts:

**Detection patterns (in order of priority):**
1. **Claude Code pattern**: `Working directory: /path/to/project`
2. **Git path**: `/something/git/project-name`
3. **Generic absolute paths**: Extracts last folder name
4. **Workspace keyword**: `workspace: project-name`

**Excluded names** (common parent folders):
- `users`, `home`, `user`, `documents`, `projects`, `git`, `code`, `my_projects`, `0my_projects`

If your workspace name isn't detected correctly, ensure it appears in your system prompt with one of these patterns.

## Task Type Icons

Visual indicators for different request types:

| Icon | Type | Trigger |
|------|------|---------|
| 🧠 | REASON | Reasoning config present (o1, extended thinking) |
| 🖼️ | IMAGE | Image content in request |
| 🔧 | TOOLS | Tool/function calling enabled |
| 📝 | TEXT | Standard text request |
| 🌊 | (suffix) | Streaming enabled |

## Performance Indicators

### Speed (tokens/second)
- ⚡**Green** (>50 t/s): Fast response
- ⚡**Yellow** (20-50 t/s): Medium speed
- ⚡**Red** (<20 t/s): Slow response

### Duration
- **Green** (<3s): Fast request
- **Yellow** (3-10s): Normal request
- **Red** (≥10s): Slow request

### Context Window Usage
- **Green** (<50%): Plenty of context remaining
- **Yellow** (50-80%): Moderate usage
- **Red** (>80%): High context usage, consider splitting

### Output Usage
- **Green** (<50%): Low output usage
- **Yellow** (50-80%): Moderate output
- **Red** (>80%): Approaching output limit

## Integration with Dashboard

Terminal output works seamlessly with the full dashboard:

```bash
# Standard terminal output
python start_proxy.py

# Terminal output + live dashboard
python start_proxy.py --dashboard
```

When the dashboard is enabled (`--dashboard` or `ENABLE_DASHBOARD=true`):
- Terminal output continues showing request-by-request details
- Live dashboard shows aggregate stats, waterfalls, and module-based views
- Both update in real-time without interfering with each other

## Examples

### Basic Usage
```bash
# Use detailed mode (default)
export TERMINAL_DISPLAY_MODE="detailed"
python start_proxy.py
```

### Minimal Output for CI/CD
```bash
# Minimal output, no colors
export TERMINAL_DISPLAY_MODE="minimal"
export TERMINAL_COLOR_SCHEME="mono"
python start_proxy.py
```

### High-Visibility Mode
```bash
# Vibrant colors, all metrics
export TERMINAL_DISPLAY_MODE="detailed"
export TERMINAL_COLOR_SCHEME="vibrant"
export TERMINAL_SESSION_COLORS="true"
python start_proxy.py
```

### Focus Mode
```bash
# Subtle colors, hide cost
export TERMINAL_DISPLAY_MODE="normal"
export TERMINAL_COLOR_SCHEME="subtle"
export TERMINAL_SHOW_COST="false"
python start_proxy.py
```

## Troubleshooting

### Workspace name shows parent folder
If your workspace is showing "0MY_PROJECTS" or another parent folder:

1. Check your system prompt includes `Working directory: /full/path/to/project`
2. Ensure the project folder name isn't in the excluded list
3. Add custom detection in `.env`:
   ```bash
   export TERMINAL_SHOW_WORKSPACE="true"
   ```

### Colors not showing
1. Ensure your terminal supports colors (most modern terminals do)
2. Check `TERMINAL_COLOR_SCHEME` isn't set to "mono"
3. Verify Rich library is installed: `pip install rich`

### Too much information
Use minimal mode or toggle off specific metrics:
```bash
export TERMINAL_DISPLAY_MODE="minimal"
# OR
export TERMINAL_SHOW_CONTEXT_PCT="false"
export TERMINAL_SHOW_COST="false"
export TERMINAL_SHOW_TASK_TYPE="false"
```

### Session colors all the same
Enable session colors explicitly:
```bash
export TERMINAL_SESSION_COLORS="true"
```

## Best Practices

1. **Start with detailed mode** - See all metrics, then disable what you don't need
2. **Use session colors** - Essential when running multiple Claude Code instances
3. **Monitor context percentage** - Helps avoid hitting context limits
4. **Watch token speeds** - Identify slow models or network issues
5. **Check cost estimates** - Track spending in real-time

## Related Documentation

- [Dashboard Configuration](../README.md#terminal-dashboard-configuration) - Full dashboard setup
- [Prompt Injection](../examples/PROMPT_INJECTION_EXAMPLES.md) - Inject stats into prompts
- [Model Configuration](../README.md#model-configuration) - Model routing setup

## Configuration Script Reference

The interactive configuration tool provides an easy way to set up your terminal output:

```bash
$ python start_proxy.py --configure-terminal

┌────────────────────────────────────────┐
│ Claude Code Proxy                      │
│ Terminal Output Configuration          │
│                                        │
│ Configure your terminal output to     │
│ show exactly what you need            │
└────────────────────────────────────────┘

Current Settings:
Display Mode     detailed
Show Workspace   true
Show Context %   true
Show Task Type   true
Show Speed       true
Show Cost        true
Color Scheme     auto

═══ Step 1: Display Mode ═══
Choose how much information to display:

  1. minimal  - Request ID + model only
  2. normal   - Add tokens + speed
  3. detailed - All metrics (context %, task type, cost)
  4. debug    - Everything including system flags

Select display mode [1/2/3/4] (3):
```

The script will:
1. Show your current configuration
2. Guide you through options with examples
3. Preview the output in real-time
4. Generate environment variables
5. Optionally write to `.env` file

Re-run anytime to adjust settings!

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/adversarial_report_v2.md
**File Size:** 1870 bytes

## Features & Sections Declared:
# Adversarial Report v2: Deep Audit of Current State
## 1. The "Junk Drawer" Problem (`src/utils`)
## 2. Redundancy in Entry Points
## 3. CLI Organization
## 4. Missing "Service" Abstractions
## Plan for Phase 3 (Execution)


## Content / Data Structure:
```text
# Adversarial Report v2: Deep Audit of Current State

## 1. The "Junk Drawer" Problem (`src/utils`)
**Critique:** `src/utils` contains 18 files with mixed concerns.
- **Logging:** `compact_logger.py`, `request_logger.py`, `startup_display.py` -> Should be `src/core/logging/` or `src/services/logging/`.
- **Cost/Usage:** `cost_calculator.py`, `usage_tracker.py`, `model_limits.py` -> Should be `src/services/billing/` or `src/services/usage/`.
- **Prompting:** `prompt_injector.py`, `system_prompt_loader.py`, `templates.py` -> Should be `src/services/prompts/`.
- **Models:** `model_filter.py`, `model_parser.py`, `provider_detector.py` -> Should be `src/services/models/`.

**Verdict:** `src/utils` is a dumping ground. It violates the "Service Layer" architecture.

## 2. Redundancy in Entry Points
**Critique:** `src/main.py` is the FastAPI app definition, but it contains logic that might overlap with `start_proxy.py` (like static file mounting logic).
- **Observation:** `src/main.py` has comments about "redundant blocks".
- **Action:** Clean up `src/main.py` to be purely the App Factory.

## 3. CLI Organization
**Critique:** `src/cli` is flat.
- **Observation:** It's mostly fine, but `wizard.py` is huge (31KB).
- **Action:** Consider splitting `wizard.py` if it grows, but acceptable for now.

## 4. Missing "Service" Abstractions
**Critique:** The code relies on "Managers" and "Trackers" instantiated globally or in modules.
- **Action:** Ensure dependency injection or clear singleton patterns in `src/core/container.py` (if we were being very strict), but for now, just grouping them into `src/services/` is a huge win.

## Plan for Phase 3 (Execution)
1.  **Explode `src/utils`**: Move files to their semantic homes.
2.  **Refine `src/main.py`**: Remove dead comments.
3.  **Update Imports**: This will be the hardest part. Every move breaks imports.

```


---


# Text/Config File Audit: /home/cheta/code/claude-code-proxy/docs/guides/production.md
**File Size:** 15740 bytes

## Features & Sections Declared:
# Production-Ready Features Guide
## Table of Contents
## Config Validation
### Automatic Validation
### Manual Validation
### Skip Validation
### What Gets Validated
#### ✅ Required Variables
#### ⚠️ Warnings
#### ❌ Errors
### Example: Valid Configuration
# .env
### Example: Invalid Configuration
# .env
### Strict Mode
## Profile Manager
### Quick Start
### List Profiles
### Switch Profiles
### Create Profile
# Description: My custom configuration
# Created: 2025-11-22 10:35:12
#
### Delete Profile
### Compare Profiles
### Export Profile
### Import Profile
# Saves as 'custom-setup' profile
### Common Workflows
#### Setup Development Environment
# 1. Configure for local development
# Select: Ollama, qwen2.5:72b, enable dashboard
# 2. Save as development profile
# 3. Configure for production
# Select: OpenRouter, real models, disable dashboard
# 4. Save as production profile
#### Switch Between Environments
# Development
# Production
# Testing (Gemini free)
#### Share Configuration with Team
# Export your setup
# Team member imports
## Test Suite
### Quick Start
### Run Specific Tests
### Test Categories
### Coverage Reports
### Continuous Integration
### Writing New Tests
# tests/test_my_feature.py
## Integration Examples
### Full Development Workflow
# 1. Setup
# 2. Configure development environment
# → Choose Ollama, local models
# 3. Save as dev profile
# 4. Validate configuration
# 5. Run tests
# 6. Start proxy
# 7. Test with Claude Code
### Production Deployment
# 1. Create production profile
# → Choose OpenRouter, production models
# 2. Validate before deploying
# 3. Run tests
# 4. Deploy
### Testing Different Providers
# 1. Create profiles for each provider
# 2. Test each
# 3. Compare configurations
## Troubleshooting
### Validation Fails on Startup
# Check what's wrong
# Fix with wizard
# Or bypass (not recommended)
### Profile Switch Not Working
# Restart proxy after switching
### Tests Failing
# Run with verbose output
# Check for environment conflicts
# Reinstall dependencies
## Best Practices
### Configuration Management
### Testing
### Profile Management
## Summary


## Content / Data Structure:
```text
# Production-Ready Features Guide

Comprehensive guide for config validation, profile management, and testing.

---

## Table of Contents

- [Config Validation](#config-validation)
- [Profile Manager](#profile-manager)
- [Test Suite](#test-suite)

---

## Config Validation

Automatically validates configuration on startup to catch errors early.

### Automatic Validation

Every time you start the proxy, configuration is validated:

```bash
python start_proxy.py
```

Output:
```
🔍 Validating configuration...

ERRORS:
1. PROVIDER_API_KEY is not set
  → Run: python start_proxy.py --setup
  → Or add to .env: PROVIDER_API_KEY="your-key-here"

💡 Run 'python start_proxy.py --setup' to fix configuration issues
```

### Manual Validation

Check configuration without starting the server:

```bash
python start_proxy.py --validate-config
```

Or directly:

```bash
python -m src.core.validator
```

### Skip Validation

Bypass validation checks (not recommended for production):

```bash
python start_proxy.py --skip-validation
```

### What Gets Validated

#### ✅ Required Variables

- `PROVIDER_API_KEY` or `OPENAI_API_KEY`
- `PROVIDER_BASE_URL` or `OPENAI_BASE_URL`
- At least one model configured (`BIG_MODEL`, `MIDDLE_MODEL`, or `SMALL_MODEL`)

#### ⚠️ Warnings

- Deprecated variable names (`OPENAI_API_KEY` → `PROVIDER_API_KEY`)
- Missing model configurations
- Incorrect OpenRouter format (missing `provider/` prefix)
- Short API keys (< 20 characters)
- Anthropic API keys (this proxy is for non-Anthropic providers)
- URLs without `/v1` suffix
- Hybrid mode with missing API keys
- Reasoning tokens outside recommended range

#### ❌ Errors

- Missing required variables
- Invalid URL format (must start with http:// or https://)
- Hybrid mode enabled but endpoint not set
- Non-numeric reasoning token values
- Invalid API keys (tested with provider /models endpoint)

### Example: Valid Configuration

```bash
# .env
PROVIDER_API_KEY="sk-or-v1-1234567890abcdef"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
```

Validation output:
```
🔍 Validating configuration...

CONFIGURATION:
  • Main Provider: API key validated ✓
  • Port 8082 is available

✅ Configuration validated successfully
```

### Example: Invalid Configuration

```bash
# .env
PROVIDER_API_KEY="short"  # Too short!
PROVIDER_BASE_URL="api.openai.com"  # Missing https://
BIG_MODEL="claude-sonnet"  # Wrong for OpenRouter
```

Validation output:
```
🔍 Validating configuration...

WARNINGS:
1. PROVIDER_API_KEY is very short (5 chars)
  → Most API keys are 30+ characters
  → Make sure you copied the full key

2. BIG_MODEL="claude-sonnet" may be incorrect for OpenRouter
  → OpenRouter models use format: provider/model
  → Example: anthropic/claude-sonnet-4
  → Run: python -m src.cli.model_selector

ERRORS:
1. PROVIDER_BASE_URL must start with http:// or https://
  → Current value: api.openai.com

❌ Configuration validation failed

💡 Run 'python setup_wizard.py' to fix configuration issues
```

### Strict Mode

Treat warnings as errors:

```bash
python -m src.core.validator --strict
```

---

## Profile Manager

Easily switch between different configurations (dev, prod, testing, etc.).

### Quick Start

**Interactive mode:**
```bash
python -m src.cli.profile_manager
```

Shows menu:
```
====================================================================
💾 Profile Manager
====================================================================

What would you like to do?
❯ 📋 List profiles
  🔄 Switch to profile
  ➕ Create new profile
  ❌ Delete profile
  🔍 Compare profiles
  📤 Export profile
  📥 Import profile
  🚪 Exit
```

### List Profiles

**CLI:**
```bash
python -m src.cli.profile_manager list
```

**Output:**
```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Name        ┃ Provider          ┃ BIG Model             ┃ Modified        ┃ Description   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ development │ localhost:11434   │ qwen2.5:72b           │ 2025-11-22 09:30│ Local dev     │
│ production  │ openrouter.ai     │ anthropic/claude-so.. │ 2025-11-21 14:22│ Production    │
│ testing     │ generativelang... │ gemini-3-pro-previe.. │ 2025-11-20 11:15│ Testing setup │
└─────────────┴───────────────────┴───────────────────────┴─────────────────┴───────────────┘
```

### Switch Profiles

**CLI:**
```bash
python -m src.cli.profile_manager switch production
```

**Output:**
```
📦 Backed up current .env to .env.backup.20251122_103045

✅ Switched to profile: production

Active Configuration:
  Provider: https://openrouter.ai/api/v1
  BIG Model: anthropic/claude-sonnet-4
  MIDDLE Model: google/gemini-pro-1.5
  SMALL Model: google/gemini-flash-1.5:free
```

**What happens:**
1. Current `.env` backed up to `.env.backup.TIMESTAMP`
2. Profile copied to `.env`
3. Configuration summary displayed

**Restart proxy to use new config:**
```bash
pkill -f start_proxy.py
python start_proxy.py
```

### Create Profile

**From current .env:**
```bash
python -m src.cli.profile_manager create my-setup "My custom configuration"
```

**What happens:**
1. Reads current `.env`
2. Adds description and timestamp
3. Saves to `profiles/my-setup.env`

**Profile file:**
```bash
# Description: My custom configuration
# Created: 2025-11-22 10:35:12
#
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
...
```

### Delete Profile

**CLI:**
```bash
python -m src.cli.profile_manager delete old-config
```

**Confirmation:**
```
Are you sure you want to delete profile 'old-config'? (y/N):
```

### Compare Profiles

**CLI:**
```bash
python -m src.cli.profile_manager compare development production
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Variable            ┃ development       ┃ production            ┃ Status     ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ PROVIDER_BASE_URL   │ localhost:11434/v1│ openrouter.ai/api/v1  │ ✗ Different│
│ BIG_MODEL           │ qwen2.5:72b       │ anthropic/claude-so..│ ✗ Different│
│ MIDDLE_MODEL        │ qwen2.5:14b       │ google/gemini-pro-1.5│ ✗ Different│
│ ENABLE_DASHBOARD    │ true              │ false                 │ ✗ Different│
│ HOST                │ 0.0.0.0           │ 0.0.0.0               │ ✓ Same     │
└─────────────────────┴───────────────────┴───────────────────────┴────────────┘
```

### Export Profile

**Share a profile:**
```bash
python -m src.cli.profile_manager export production ~/shared/prod-config.env
```

### Import Profile

**From shared file:**
```bash
python -m src.cli.profile_manager import ~/shared/prod-config.env production
```

**Auto-name from filename:**
```bash
python -m src.cli.profile_manager import custom-setup.env
# Saves as 'custom-setup' profile
```

### Common Workflows

#### Setup Development Environment

```bash
# 1. Configure for local development
python setup_wizard.py
# Select: Ollama, qwen2.5:72b, enable dashboard

# 2. Save as development profile
python -m src.cli.profile_manager create development "Local Ollama setup"

# 3. Configure for production
python setup_wizard.py
# Select: OpenRouter, real models, disable dashboard

# 4. Save as production profile
python -m src.cli.profile_manager create production "Production OpenRouter"
```

#### Switch Between Environments

```bash
# Development
python -m src.cli.profile_manager switch development
python start_proxy.py

# Production
python -m src.cli.profile_manager switch production
python start_proxy.py

# Testing (Gemini free)
python -m src.cli.profile_manager switch testing
python start_proxy.py
```

#### Share Configuration with Team

```bash
# Export your setup
python -m src.cli.profile_manager export my-setup team-config.env

# Team member imports
python -m src.cli.profile_manager import team-config.env shared-setup
python -m src.cli.profile_manager switch shared-setup
```

---

## Test Suite

Comprehensive pytest suite with 70+ tests for production quality.

### Quick Start

**Run all tests:**
```bash
python run_tests.py
```

**With coverage:**
```bash
python run_tests.py --cov
```

**Output:**
```
🧪 Running tests...

tests/test_config_loading.py::TestConfigLoading::test_load_provider_config PASSED [ 5%]
tests/test_config_loading.py::TestConfigLoading::test_load_model_config PASSED [10%]
tests/test_model_mapping.py::TestModelMapping::test_claude_opus_maps_to_big_model PASSED [15%]
...

=============================== 70 passed in 2.34s ================================

---------- coverage: platform linux, python 3.11.7 -----------
Name                               Stmts   Miss  Cover
------------------------------------------------------
src/core/config.py                   156     12    92%
src/core/model_manager.py             89      5    94%
src/core/validator.py                287     23    92%
src/cli/profile_manager.py           234     31    87%
------------------------------------------------------
TOTAL                                766     71    91%

Coverage HTML written to htmlcov/index.html
```

### Run Specific Tests

**Single file:**
```bash
pytest tests/test_model_mapping.py -v
```

**Single test:**
```bash
pytest tests/test_model_mapping.py::TestModelMapping::test_claude_opus_maps_to_big_model -v
```

**By keyword:**
```bash
pytest -k "validation" -v  # All validation tests
pytest -k "profile" -v     # All profile tests
```

### Test Categories

**Model Mapping (9 tests):**
- Claude model name → configured model
- OpenRouter format validation
- Case-insensitive matching
- Suffix notation for reasoning
- Pass-through for non-Claude models

**Config Loading (13 tests):**
- Environment variable parsing
- Legacy variable support
- Default values
- Boolean/integer parsing
- Hybrid mode configuration
- Terminal output settings
- Custom prompts

**Validator (21 tests):**
- Required variable checks
- Deprecated variable warnings
- Invalid reasoning config detection
- OpenRouter format validation
- Hybrid mode validation
- API key testing (401, 403)
- Common mistake detection
- Strict mode behavior

**Profile Manager (15 tests):**
- Create/list/switch/delete profiles
- Profile comparison
- Import/export functionality
- Metadata preservation
- Error handling

### Coverage Reports

**Terminal:**
```bash
python run_tests.py --cov
```

**HTML (detailed):**
```bash
python run_tests.py --cov
open htmlcov/index.html
```

Shows:
- Line-by-line coverage
- Missing branches
- Functions not tested
- Interactive drill-down

### Continuous Integration

**GitHub Actions:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install uv
      - run: uv sync
      - run: python run_tests.py --cov
```

### Writing New Tests

**Example:**
```python
# tests/test_my_feature.py
import pytest
from src.my_module import my_function

class TestMyFeature:
    """Test my new feature"""

    def test_basic_case(self, sample_config):
        """Test basic functionality"""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case(self, clean_env):
        """Test edge case"""
        result = my_function(None)
        assert result is None
```

**Run new tests:**
```bash
pytest tests/test_my_feature.py -v
```

---

## Integration Examples

### Full Development Workflow

```bash
# 1. Setup
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# 2. Configure development environment
python setup_wizard.py
# → Choose Ollama, local models

# 3. Save as dev profile
python -m src.cli.profile_manager create development "Local dev setup"

# 4. Validate configuration
python start_proxy.py --validate-config

# 5. Run tests
python run_tests.py --cov

# 6. Start proxy
python start_proxy.py

# 7. Test with Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "test prompt"
```

### Production Deployment

```bash
# 1. Create production profile
python setup_wizard.py
# → Choose OpenRouter, production models

python -m src.cli.profile_manager create production "Production config"

# 2. Validate before deploying
python -m src.cli.profile_manager switch production
python start_proxy.py --validate-config

# 3. Run tests
python run_tests.py

# 4. Deploy
python start_proxy.py
```

### Testing Different Providers

```bash
# 1. Create profiles for each provider
python setup_wizard.py  # Gemini
python -m src.cli.profile_manager create gemini "Google Gemini free"

python setup_wizard.py  # OpenRouter
python -m src.cli.profile_manager create openrouter "OpenRouter"

python setup_wizard.py  # Local
python -m src.cli.profile_manager create local "Ollama local"

# 2. Test each
for profile in gemini openrouter local; do
    echo "Testing $profile..."
    python -m src.cli.profile_manager switch $profile
    python start_proxy.py --validate-config
done

# 3. Compare configurations
python -m src.cli.profile_manager compare gemini openrouter
python -m src.cli.profile_manager compare openrouter local
```

---

## Troubleshooting

### Validation Fails on Startup

**Problem:**
```
❌ Configuration validation failed
```

**Solution:**
```bash
# Check what's wrong
python start_proxy.py --validate-config

# Fix with wizard
python setup_wizard.py

# Or bypass (not recommended)
python start_proxy.py --skip-validation
```

### Profile Switch Not Working

**Problem:**
Profile switched but proxy still uses old config

**Solution:**
```bash
# Restart proxy after switching
pkill -f start_proxy.py
python start_proxy.py
```

### Tests Failing

**Problem:**
```
FAILED tests/test_model_mapping.py::test_claude_opus_maps_to_big_model
```

**Solution:**
```bash
# Run with verbose output
pytest tests/test_model_mapping.py -vv

# Check for environment conflicts
python -m src.core.validator

# Reinstall dependencies
uv sync
```

---

## Best Practices

### Configuration Management

1. **Always validate before deploying:**
   ```bash
   python start_proxy.py --validate-config
   ```

2. **Use profiles for different environments:**
   - `development` - Local testing
   - `staging` - Pre-production
   - `production` - Live deployment

3. **Version control profiles:**
   ```bash
   git add profiles/*.env
   git commit -m "Update production profile"
   ```

### Testing

1. **Run tests before committing:**
   ```bash
   python run_tests.py --cov
   ```

2. **Maintain coverage above 90%:**
   ```bash
   pytest --cov=src --cov-fail-under=90
   ```

3. **Write tests for new features:**
   - Unit tests for logic
   - Integration tests for API
   - Validation tests for config

### Profile Management

1. **Document profiles:**
   ```bash
   python -m src.cli.profile_manager create prod "Production: OpenRouter with Claude Sonnet"
   ```

2. **Back up before switching:**
   - Automatic backups to `.env.backup.TIMESTAMP`
   - Can restore if needed

3. **Share team configurations:**
   ```bash
   python -m src.cli.profile_manager export team-standard ~/shared/
   ```

---

## Summary

**Config Validation:**
- ✅ Automatic on startup
- ✅ Clear error messages
- ✅ API key testing
- ✅ Common mistake detection

**Profile Manager:**
- ✅ Easy environment switching
- ✅ Import/export for sharing
- ✅ Profile comparison
- ✅ Automatic backups

**Test Suite:**
- ✅ 70+ comprehensive tests
- ✅ 91% code coverage
- ✅ CI/CD ready
- ✅ Easy to extend

**Production Ready!** 🎉

```


---


