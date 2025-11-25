# Examples & Use Cases

Practical examples for common Claude Code Proxy setups.

---

## Table of Contents

- [Quick Starts](#quick-starts)
- [Cost Optimization](#cost-optimization)
- [Privacy & Security](#privacy--security)
- [Reasoning & Extended Thinking](#reasoning--extended-thinking)
- [Multi-Provider Hybrid](#multi-provider-hybrid)
- [Development Workflows](#development-workflows)
- [Advanced Configurations](#advanced-configurations)

---

## Quick Starts

### Fastest Setup (Google Gemini - Free)

```bash
# Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# Run setup wizard
python setup_wizard.py
# Select: Google Gemini → Enter API key → Done

# Start proxy
python start_proxy.py
```

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "write a fibonacci function"
```

Get Gemini key: https://makersuite.google.com/app/apikey

---

### Local-Only (100% Free, Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull qwen2.5:72b

# Configure proxy
cat > .env << 'EOF'
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:72b"
SMALL_MODEL="qwen2.5:14b"
EOF

# Start proxy
python start_proxy.py
```

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "analyze this code"
```

---

### OpenRouter (352+ Models, Free Tier)

```bash
# Run setup wizard
python setup_wizard.py
# Select: OpenRouter → Enter API key → Choose models

# Or manual .env:
cat > .env << 'EOF'
PROVIDER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-flash-1.5"
SMALL_MODEL="x-ai/grok-beta:free"
EOF

# Start proxy
python start_proxy.py
```

Get OpenRouter key: https://openrouter.ai/keys

---

## Cost Optimization

### Free Models Only

Use 100% free models from OpenRouter:

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# All free models
BIG_MODEL="google/gemini-flash-1.5:free"
MIDDLE_MODEL="x-ai/grok-beta:free"
SMALL_MODEL="google/gemini-flash-1.5:free"

# Track usage
TRACK_USAGE="true"
USAGE_DB_PATH="usage.db"
```

**Free models on OpenRouter:**
- `google/gemini-flash-1.5:free`
- `x-ai/grok-beta:free`
- `meta-llama/llama-3.1-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`
- `nousresearch/hermes-3-llama-3.1-405b:free`

### Tiered Cost Strategy

Expensive models for hard tasks, cheap for easy:

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Expensive for BIG (complex reasoning)
BIG_MODEL="anthropic/claude-sonnet-4"  # ~$3/M tokens

# Medium for MIDDLE (general tasks)
MIDDLE_MODEL="google/gemini-pro-1.5"   # ~$1.25/M tokens

# Free for SMALL (simple tasks)
SMALL_MODEL="google/gemini-flash-1.5:free"  # $0

# Show cost estimates
TERMINAL_SHOW_COST="true"
TRACK_USAGE="true"
```

**Savings:** ~70% reduction vs. using Claude Sonnet for everything.

### Local for Expensive, Cloud for Fast

```bash
# Default: Local Ollama (free)
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"

# Override SMALL to cloud (faster)
ENABLE_SMALL_ENDPOINT="true"
SMALL_ENDPOINT="https://openrouter.ai/api/v1"
SMALL_API_KEY="sk-or-v1-..."
SMALL_MODEL="google/gemini-flash-1.5:free"

# Local for BIG/MIDDLE
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
```

**Why?** Big tasks use free local model (save money), small tasks use fast cloud (save time).

---

## Privacy & Security

### Air-Gapped (No Internet)

```bash
# Everything local
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"

BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
SMALL_MODEL="llama3.1:8b"

# Local tracking only
TRACK_USAGE="true"
USAGE_DB_PATH="usage.db"

# No external connections
ENABLE_OPENROUTER_SELECTION="false"
```

**Privacy:** No data leaves your machine. Messages never sent to cloud providers.

### Proxy Authentication

Secure your proxy with authentication:

```bash
# .env
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"

# Require auth from clients
PROXY_AUTH_KEY="your-super-secret-key-here-min-32-chars"
```

Client configuration:

```bash
export ANTHROPIC_API_KEY="your-super-secret-key-here-min-32-chars"
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "secure request"
```

### Custom Guardrails

Add custom system prompts with safety guidelines:

```bash
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT_FILE="/path/to/guardrails.txt"
```

**guardrails.txt:**
```
You are a helpful AI assistant for code development.

STRICT RULES:
1. Never generate code that could harm systems or users
2. Always validate user input in code examples
3. Include error handling in all code samples
4. Flag potential security issues in user code
5. Refuse requests for malicious code

Follow these rules without exception.
```

---

## Reasoning & Extended Thinking

### Maximum Reasoning (GPT-5 / o-series)

```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"

# Use reasoning models
BIG_MODEL="gpt-5:high"           # High reasoning effort
MIDDLE_MODEL="o4-mini:50000"     # 50k thinking tokens
SMALL_MODEL="o1-mini:medium"     # Medium reasoning

# Global reasoning config
REASONING_EFFORT="high"          # ~80% tokens for thinking
VERBOSITY="high"                 # Detailed responses
REASONING_EXCLUDE="false"        # Show thinking process
```

**Use cases:** Complex debugging, architectural decisions, mathematical proofs, deep analysis.

### Claude 4 Extended Thinking

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Claude 4 with 16k thinking tokens
BIG_MODEL="anthropic/claude-opus-4-20250514:16000"
MIDDLE_MODEL="anthropic/claude-sonnet-4-20250514:8k"
SMALL_MODEL="anthropic/claude-sonnet-4-20250514"

# Per-model reasoning overrides
BIG_MODEL_REASONING="16000"
MIDDLE_MODEL_REASONING="8192"
```

### Gemini 2/3 Extended Thinking

```bash
PROVIDER_API_KEY="your-gemini-key"
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"

# Gemini 3 with thinking
BIG_MODEL="gemini-3-pro-preview-11-2025-thinking:24000"
MIDDLE_MODEL="gemini-2.5-flash-preview:16000"

REASONING_MAX_TOKENS="24000"  # Max thinking tokens
```

**Note:** Gemini supports up to 24,576 thinking tokens.

### Mixed Reasoning Strategy

Different reasoning levels per model tier:

```bash
# High reasoning for complex tasks
BIG_MODEL="gpt-5:high"
BIG_MODEL_REASONING="high"

# Medium for general tasks
MIDDLE_MODEL="o4-mini:30000"
MIDDLE_MODEL_REASONING="medium"

# No reasoning for simple tasks (faster)
SMALL_MODEL="gpt-4o"
# SMALL_MODEL_REASONING not set (disabled)

# Show performance
TERMINAL_SHOW_SPEED="true"
TERMINAL_SHOW_COST="true"
```

---

## Multi-Provider Hybrid

### Local + Cloud Hybrid

```bash
# Default: OpenRouter
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# BIG: Local Ollama (privacy + free)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# MIDDLE: Gemini (free + fast)
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/openai/"
MIDDLE_API_KEY="your-gemini-key"
MIDDLE_MODEL="gemini-3-pro-preview-11-2025"

# SMALL: OpenRouter free tier
SMALL_MODEL="x-ai/grok-beta:free"
```

**Benefits:**
- Privacy for sensitive tasks (BIG → local)
- Fast free models for common tasks (MIDDLE → Gemini)
- Fallback free tier (SMALL → OpenRouter)

### Multi-Region Redundancy

```bash
# Primary: US region
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# BIG: Azure EU (compliance)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="https://eu-resource.openai.azure.com/openai/deployments/gpt-4"
BIG_API_KEY="azure-key"
BIG_MODEL="gpt-4"

# MIDDLE: OpenAI US
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://api.openai.com/v1"
MIDDLE_API_KEY="sk-..."
MIDDLE_MODEL="gpt-4o"

# SMALL: Default OpenRouter
SMALL_MODEL="google/gemini-flash-1.5"
```

### Development vs. Production

Use profiles to switch between dev and prod configs:

**profiles/development.env:**
```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
SMALL_MODEL="llama3.1:8b"
TERMINAL_DISPLAY_MODE="debug"
ENABLE_DASHBOARD="true"
```

**profiles/production.env:**
```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
TERMINAL_DISPLAY_MODE="normal"
TRACK_USAGE="true"
```

Switch profiles:

```bash
# Development
cp profiles/development.env .env
python start_proxy.py

# Production
cp profiles/production.env .env
python start_proxy.py
```

---

## Development Workflows

### Code Review Assistant

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

BIG_MODEL="anthropic/claude-sonnet-4"
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT="You are a senior code reviewer. Focus on:
- Security vulnerabilities (XSS, SQL injection, auth issues)
- Performance bottlenecks
- Code maintainability and readability
- Best practices for the language/framework
- Edge cases and error handling

Provide specific, actionable feedback with examples."

# Show detailed output
TERMINAL_DISPLAY_MODE="detailed"
TERMINAL_SHOW_COST="true"
```

### Documentation Writer

```bash
ENABLE_CUSTOM_MIDDLE_PROMPT="true"
MIDDLE_SYSTEM_PROMPT="You are a technical documentation specialist.

When writing docs:
- Use clear, concise language
- Include practical examples
- Add code blocks with syntax highlighting
- Organize with headers and lists
- Anticipate common questions
- Provide troubleshooting tips"

MIDDLE_MODEL="google/gemini-pro-1.5"
```

### Debugging Assistant

```bash
ENABLE_CUSTOM_BIG_PROMPT="true"
BIG_SYSTEM_PROMPT="You are a debugging expert.

When analyzing errors:
1. Identify the root cause (not just symptoms)
2. Explain WHY the error occurs
3. Provide step-by-step fix instructions
4. Suggest preventive measures
5. Include relevant documentation links

Use detailed reasoning to trace the issue."

BIG_MODEL="gpt-5:high"
REASONING_EFFORT="high"
TERMINAL_SHOW_SPEED="true"
```

---

## Advanced Configurations

### Performance Tuning

```bash
# Increase timeouts for large requests
REQUEST_TIMEOUT="180"  # 3 minutes

# Retry failed requests
MAX_RETRIES="3"

# Token limits
MAX_TOKENS_LIMIT="8192"
MIN_TOKENS_LIMIT="100"

# Show performance metrics
SHOW_TOKEN_COUNTS="true"
SHOW_PERFORMANCE="true"
TERMINAL_SHOW_SPEED="true"
```

### Custom Headers

Add custom headers for provider-specific features:

```bash
# OpenRouter specific
CUSTOM_HEADER_HTTP_REFERER="https://your-site.com"
CUSTOM_HEADER_X_TITLE="Claude Code Proxy"

# Custom auth
CUSTOM_HEADER_X_API_KEY="custom-key"
CUSTOM_HEADER_AUTHORIZATION="Bearer custom-token"

# User agent
CUSTOM_HEADER_USER_AGENT="ClaudeCodeProxy/1.0"
```

### Rich Terminal Dashboard

```bash
# Enable all visual features
ENABLE_DASHBOARD="true"
DASHBOARD_LAYOUT="detailed"
DASHBOARD_REFRESH="0.5"
DASHBOARD_WATERFALL_SIZE="30"

TERMINAL_DISPLAY_MODE="detailed"
TERMINAL_COLOR_SCHEME="vibrant"
TERMINAL_SESSION_COLORS="true"
TERMINAL_SHOW_WORKSPACE="true"
TERMINAL_SHOW_CONTEXT_PCT="true"
TERMINAL_SHOW_TASK_TYPE="true"
TERMINAL_SHOW_SPEED="true"
TERMINAL_SHOW_COST="true"
TERMINAL_SHOW_DURATION_COLORS="true"

LOG_STYLE="rich"
SHOW_TOKEN_COUNTS="true"
SHOW_PERFORMANCE="true"
```

### Minimal Terminal Output

```bash
# Minimal logs
TERMINAL_DISPLAY_MODE="minimal"
TERMINAL_COLOR_SCHEME="mono"
LOG_STYLE="plain"
COMPACT_LOGGER="true"

# Disable dashboard
ENABLE_DASHBOARD="false"

# Essential info only
TERMINAL_SHOW_COST="true"
TERMINAL_SHOW_SPEED="false"
TERMINAL_SHOW_WORKSPACE="false"
```

---

## Complete Workflow Examples

### First-Time Setup to First Request

```bash
# 1. Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# 2. Run setup wizard
python setup_wizard.py
# Follow prompts...

# 3. Start proxy
python start_proxy.py &

# 4. Configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082

# 5. Use Claude Code
claude "write a function to reverse a string"
```

### Switching Between Providers

```bash
# Use Gemini
cp profiles/gemini.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with Gemini"

# Switch to OpenRouter
cp profiles/openrouter.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with OpenRouter"

# Switch to local Ollama
cp profiles/ollama.env .env
pkill -f start_proxy.py
python start_proxy.py &
claude "test with Ollama"
```

### Testing Different Models

```bash
# Test model selector
python -m src.cli.model_selector
# Search for models, copy names

# Update .env with selected models
nano .env

# Restart proxy
pkill -f start_proxy.py
python start_proxy.py &

# Test new models
claude "hello, which model are you?"
```

---

## Troubleshooting Examples

### Debug 401 Errors

```bash
# Enable debug logging
LOG_LEVEL="DEBUG"
TERMINAL_DISPLAY_MODE="debug"

# Check API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'API Key: {os.getenv(\"PROVIDER_API_KEY\")[:10]}...')"

# Test provider directly
curl -H "Authorization: Bearer $PROVIDER_API_KEY" "$PROVIDER_BASE_URL/models"

# Restart proxy with verbose output
python start_proxy.py
```

### Verify Configuration

```bash
# Check all environment variables
python -c "
from dotenv import load_dotenv
import os
load_dotenv()

print('PROVIDER_API_KEY:', os.getenv('PROVIDER_API_KEY')[:10] + '...' if os.getenv('PROVIDER_API_KEY') else 'NOT SET')
print('PROVIDER_BASE_URL:', os.getenv('PROVIDER_BASE_URL'))
print('BIG_MODEL:', os.getenv('BIG_MODEL'))
print('MIDDLE_MODEL:', os.getenv('MIDDLE_MODEL'))
print('SMALL_MODEL:', os.getenv('SMALL_MODEL'))
"

# Test proxy endpoint
curl http://localhost:8082/v1/models

# Test with Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "test connection"
```

---

## More Resources

- [Configuration Guide](CONFIGURATION.md) - Complete environment variable reference
- [Troubleshooting](TROUBLESHOOTING_401.md) - Fix common issues
- [API Reference](API.md) - HTTP API endpoints
