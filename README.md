<div align="center">

# 🔄 Claude Code Proxy

**Use Claude Code CLI with any OpenAI-compatible provider**

Stop being locked into Anthropic. Use OpenRouter, Gemini, local models, or any provider you want.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Quick Start](#-quick-start) • [Features](#-features) • [Configuration](docs/CONFIGURATION.md) • [Examples](docs/EXAMPLES.md)

</div>

---

## 📖 What It Does

Claude Code Proxy sits between Claude Code CLI and your chosen API provider. Claude Code thinks it's talking to Anthropic, but you're actually using whatever provider you want—OpenRouter, Gemini, OpenAI, local models, etc.

**Why use this?**
- 💰 **Save money** - Use free or cheaper models instead of paid Anthropic API
- 🏠 **Run locally** - Use Ollama or LM Studio for 100% free, offline operation
- 🌐 **Multi-provider** - Route different model tiers to different providers
- 🧠 **Extended reasoning** - Access thinking tokens for reasoning models (GPT-5, Claude 4+, Gemini 2+)
- 📊 **Rich monitoring** - Terminal dashboards, usage tracking, performance metrics
- 🎛️ **Full control** - Configure everything via .env, Web UI, or interactive wizards

---

## 🚀 Quick Start

### 1. First-Time Setup Wizard (Recommended)

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
python setup_wizard.py
```

The wizard will guide you through:
- Provider selection (OpenRouter, Gemini, OpenAI, Azure, Ollama, LM Studio)
- Model configuration (BIG/MIDDLE/SMALL mapping)
- Optional features (reasoning, dashboard, terminal output, crosstalk, etc.)
- Profile management (save/load different configurations)

### 2. Manual Setup

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
cp .env.example .env
nano .env  # Add your PROVIDER_API_KEY and PROVIDER_BASE_URL
```

### 3. Start the Proxy

```bash
python start_proxy.py
```

### 4. Use Claude Code

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "write a fibonacci function"
```

Done! Claude Code now uses your configured provider.

---

## 📋 Complete Workflow (Copy-Paste Ready)

### One-Time Setup + First Request

```bash
# Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# Run setup wizard (interactive)
python setup_wizard.py

# Start proxy (in background)
python start_proxy.py &

# Configure Claude Code + test
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "write a fibonacci function"
```

### Manual Setup (Without Wizard)

```bash
# Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# Configure .env
cp .env.example .env
cat >> .env << 'EOF'
PROVIDER_API_KEY="your-api-key-here"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
EOF

# Start proxy + use
python start_proxy.py &
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "hello world"
```

### Daily Usage

```bash
# Terminal 1: Start proxy
cd claude-code-proxy
python start_proxy.py

# Terminal 2: Use Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
cd ~/your-project
claude "your prompt here"
```

### Quick Model Switch

```bash
# Browse models
python -m src.cli.model_selector

# Update .env with selected model
nano .env  # Change BIG_MODEL, MIDDLE_MODEL, or SMALL_MODEL

# Restart proxy
pkill -f start_proxy.py && python start_proxy.py &
```

---

## 🧩 Core Concepts

### How It Works

```
Claude Code → Proxy → Your Provider
     ↓                      ↓
  Claude API           OpenAI API
    format              format
```

The proxy transparently converts between API formats:
1. Claude Code sends requests to `ANTHROPIC_BASE_URL` (the proxy)
2. Proxy converts Claude API format → OpenAI API format
3. Proxy routes request to your configured provider
4. Provider responds in OpenAI format
5. Proxy converts response → Claude API format
6. Claude Code receives response and can't tell the difference

### Model Mapping

Claude Code requests models by name. The proxy maps them to your configured models:

| Claude Code Requests | Routes To | Environment Variable |
|---------------------|-----------|---------------------|
| `claude-opus-4` | Your BIG model | `BIG_MODEL` |
| `claude-sonnet-4` | Your MIDDLE model | `MIDDLE_MODEL` |
| `claude-haiku-4` | Your SMALL model | `SMALL_MODEL` |

**Why?** **Flexibility.** You decide what model handles each tier:

```bash
# Example 1: All same model
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o"

# Example 2: Cost optimization
BIG_MODEL="anthropic/claude-sonnet-4"    # Expensive tasks
MIDDLE_MODEL="google/gemini-pro-1.5"     # Medium tasks
SMALL_MODEL="google/gemini-flash-1.5"    # Cheap tasks (free!)

# Example 3: Hybrid local + cloud
BIG_MODEL="qwen2.5:72b"                  # Local Ollama (free!)
MIDDLE_MODEL="openai/gpt-4o"             # Cloud (fast)
SMALL_MODEL="google/gemini-flash-1.5"    # Cloud (free!)
```

See [Hybrid Mode](#-hybrid-mode-multi-provider-routing) for routing different tiers to different providers.

---

## 🌐 Provider Setup

### Google Gemini (Free)

Best for: Development, testing, free tier usage

```bash
PROVIDER_API_KEY="your-gemini-key"
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
BIG_MODEL="gemini-3-pro-preview-11-2025"
```

Get key: https://makersuite.google.com/app/apikey

### OpenRouter (352+ models, free tier)

Best for: Experimentation, model variety, generous free tier

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="x-ai/grok-beta:free"  # Free model!
```

Get key: https://openrouter.ai/keys

### OpenAI (Official API)

Best for: Production, GPT-5/o-series access, reliability

```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o-mini"
```

Get key: https://platform.openai.com/api-keys

### Azure OpenAI

Best for: Enterprise, regional compliance, OpenAI access in restricted regions

```bash
PROVIDER_API_KEY="your-azure-key"
PROVIDER_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
AZURE_API_VERSION="2024-03-01-preview"
BIG_MODEL="gpt-4"
MIDDLE_MODEL="gpt-4"
SMALL_MODEL="gpt-35-turbo"
```

### Ollama (100% free, runs on your machine)

Best for: Privacy, offline work, zero cost, learning

```bash
PROVIDER_API_KEY="dummy"  # Any value works for local models
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:72b"
SMALL_MODEL="qwen2.5:14b"
```

Install Ollama: https://ollama.ai

### LM Studio (Local models with GUI)

Best for: Local models, GUI management, easy setup

```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://127.0.0.1:1234/v1"
BIG_MODEL="local-model"  # Set in LM Studio
```

Install LM Studio: https://lmstudio.ai

---

## ✨ Features

### 🎯 Model Configuration

Control exactly which models handle which requests.

**Basic Setup:**
```bash
BIG_MODEL="gpt-4o"           # Claude Opus requests
MIDDLE_MODEL="gpt-4o"        # Claude Sonnet requests
SMALL_MODEL="gpt-4o-mini"    # Claude Haiku requests
```

**Model Name Formats:**

Different providers use different naming:

```bash
# OpenRouter (provider/model)
BIG_MODEL="anthropic/claude-sonnet-4"
BIG_MODEL="openai/gpt-4o"
BIG_MODEL="google/gemini-pro-1.5"

# Ollama (simple names)
BIG_MODEL="qwen2.5:72b"
BIG_MODEL="llama3.1:70b"

# OpenAI (model IDs)
BIG_MODEL="gpt-4o"
BIG_MODEL="o1-preview"

# Gemini (official names)
BIG_MODEL="gemini-3-pro-preview-11-2025"
```

### 🧠 Reasoning & Extended Thinking

Enable extended thinking for reasoning models (GPT-5, Claude 4+, Gemini 2+, o-series).

**OpenAI Reasoning Effort (GPT-5, o1, o3, o4-mini):**

```bash
REASONING_EFFORT="high"  # Options: low, medium, high
```

- **low**: ~20% of max tokens for thinking
- **medium**: ~50% of max tokens for thinking
- **high**: ~80% of max tokens for thinking

**Anthropic/Gemini Token Budget:**

```bash
REASONING_MAX_TOKENS="16000"  # Exact token count for thinking
```

Ranges:
- **Anthropic Claude**: 1024-16000 tokens
- **Google Gemini**: 0-24576 tokens

**Per-Model Overrides:**

```bash
BIG_MODEL_REASONING="high"      # Override for BIG model
MIDDLE_MODEL_REASONING="medium" # Override for MIDDLE model
SMALL_MODEL_REASONING="low"     # Override for SMALL model
```

**Model Name Suffix Notation:**

Specify reasoning directly in model names:

```bash
# OpenAI (effort levels or arbitrary token budgets)
BIG_MODEL="o4-mini:high"          # High effort
BIG_MODEL="o4-mini:50000"         # 50k thinking tokens
BIG_MODEL="gpt-5:100k"            # 102,400 tokens (k-notation)

# Anthropic
BIG_MODEL="claude-opus-4-20250514:8k"     # 8192 thinking tokens
BIG_MODEL="claude-opus-4-20250514:16000"  # 16000 tokens (exact)

# Gemini
BIG_MODEL="gemini-2.5-flash:16000"        # 16000 thinking tokens
```

Suffix notation overrides environment variables.

**Other Options:**

```bash
REASONING_EXCLUDE="true"  # Hide reasoning tokens in response (OpenAI only)
VERBOSITY="high"          # Response detail level (provider-specific)
```

### 🔀 Hybrid Mode (Multi-Provider Routing)

Route different model tiers to different providers simultaneously!

**Example: Local for BIG, Cloud for MIDDLE/SMALL**

```bash
# Default provider (for MIDDLE/SMALL)
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Override BIG model to use local Ollama
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# MIDDLE and SMALL use default OpenRouter
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5:free"
```

**Full Hybrid Configuration:**

```bash
# Enable per-model routing
ENABLE_BIG_ENDPOINT="true"
ENABLE_MIDDLE_ENDPOINT="true"
ENABLE_SMALL_ENDPOINT="true"

# BIG: Local Ollama
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# MIDDLE: OpenRouter
MIDDLE_ENDPOINT="https://openrouter.ai/api/v1"
MIDDLE_API_KEY="sk-or-v1-..."
MIDDLE_MODEL="anthropic/claude-sonnet-4"

# SMALL: LM Studio
SMALL_ENDPOINT="http://127.0.0.1:1234/v1"
SMALL_API_KEY="dummy"
SMALL_MODEL="llama3.1:8b"
```

**Why?** Cost optimization, privacy, redundancy, experimentation.

### 🛠️ Built-in Tools

#### Setup Wizard

Interactive first-time configuration:

```bash
python setup_wizard.py
```

Features:
- Provider selection (OpenRouter, Gemini, OpenAI, Azure, Ollama, LM Studio, custom)
- Model configuration with suggestions
- Feature-based setup (reasoning, dashboard, terminal, crosstalk, prompts, tracking, hybrid)
- Profile management (save/load/switch configurations)

#### Interactive Model Selector

Browse and search 352+ models:

```bash
python -m src.cli.model_selector
```

Features:
- Real-time search and filtering
- Model metadata (context size, pricing, capabilities)
- Direct .env updates
- OpenRouter integration

#### Crosstalk Mode (Multi-Agent)

Enable multiple agents to collaborate on complex tasks:

```bash
python -m src.cli.crosstalk_cli
```

Or create `crosstalk.yaml` config files for different agent setups.

#### Terminal Output Configurator

Interactive terminal display customization:

```bash
python configure_terminal_output.py
```

Configure:
- Display mode (minimal, normal, detailed, debug)
- Color schemes (auto, vibrant, subtle, mono)
- Toggles (workspace, context%, task type, speed, cost, duration colors)
- Session colors

#### Prompt Injection Configurator

Interactive custom system prompt setup:

```bash
python configure_prompt_injection.py
```

Configure custom prompts for BIG/MIDDLE/SMALL models from files or inline.

#### Web UI

Visual configuration editor and monitoring dashboard:

```
http://localhost:8082
```

Features:
- Real-time configuration editing (no restart required!)
- Profile management (save/load/delete)
- Model browser with search
- Live request monitoring
- Usage analytics (when TRACK_USAGE enabled)
- Performance metrics

### 🎨 Terminal Output Customization

Rich terminal output with extensive customization.

**Display Modes:**

```bash
TERMINAL_DISPLAY_MODE="detailed"  # minimal, normal, detailed, debug
```

**Feature Toggles:**

```bash
TERMINAL_SHOW_WORKSPACE="true"          # Show project/workspace name
TERMINAL_SHOW_CONTEXT_PCT="true"        # Show context window percentage
TERMINAL_SHOW_TASK_TYPE="true"          # Show task icons (🧠 REASON, 🔧 TOOLS, 📝 TEXT)
TERMINAL_SHOW_SPEED="true"              # Show tokens/sec
TERMINAL_SHOW_COST="true"               # Show cost estimates
TERMINAL_SHOW_DURATION_COLORS="true"    # Color-code duration (green/yellow/red)
```

**Color Schemes:**

```bash
TERMINAL_COLOR_SCHEME="auto"  # auto, vibrant, subtle, mono
TERMINAL_SESSION_COLORS="true"  # Different color per Claude Code session
```

**Log Styles:**

```bash
LOG_STYLE="rich"           # rich (colored, progress bars), plain, compact
COMPACT_LOGGER="false"     # Single-line logs with emojis
COLOR_SCHEME="auto"        # auto (detect terminal), dark, light, none
SHOW_TOKEN_COUNTS="true"   # Show input/output/thinking tokens
SHOW_PERFORMANCE="true"    # Show tokens/sec, latency
```

### 📊 Usage Tracking & Analytics

Local SQLite database for usage analytics (privacy-first, no data sent anywhere).

**Enable Tracking:**

```bash
TRACK_USAGE="true"
USAGE_DB_PATH="usage_tracking.db"  # Database location
```

**Data Stored:**
- Model used
- Token counts (input, output, thinking)
- Request duration
- Cost estimates
- Request counts
- Performance metrics

**Privacy:** Message content is **never** stored. Only metadata.

**Access Analytics:**
- Web UI: http://localhost:8082/analytics
- Database queries: SQLite CLI or any SQLite tool

### 📈 Dashboard & Monitoring

Live terminal dashboard with real-time metrics.

**Enable Dashboard:**

```bash
ENABLE_DASHBOARD="true"
DASHBOARD_LAYOUT="default"      # default, compact, detailed
DASHBOARD_REFRESH="0.5"         # Refresh interval (seconds)
DASHBOARD_WATERFALL_SIZE="20"   # Number of recent requests to show
```

**Dashboard Features:**
- Active requests with progress
- Request waterfall (recent activity)
- Performance metrics (tokens/sec, latency)
- Cost tracking
- Model usage distribution

### ✏️ Custom System Prompts

Override system prompts per model tier.

**Enable Custom Prompts:**

```bash
ENABLE_CUSTOM_BIG_PROMPT="true"
ENABLE_CUSTOM_MIDDLE_PROMPT="true"
ENABLE_CUSTOM_SMALL_PROMPT="true"
```

**From Files:**

```bash
BIG_SYSTEM_PROMPT_FILE="/path/to/big_prompt.txt"
MIDDLE_SYSTEM_PROMPT_FILE="/path/to/middle_prompt.txt"
SMALL_SYSTEM_PROMPT_FILE="/path/to/small_prompt.txt"
```

**Inline:**

```bash
BIG_SYSTEM_PROMPT="You are a helpful assistant specialized in..."
MIDDLE_SYSTEM_PROMPT="You are a helpful assistant..."
SMALL_SYSTEM_PROMPT="You are a helpful assistant..."
```

Files take precedence over inline prompts.

**Use Cases:**
- Domain-specific behavior (code review, writing, analysis)
- Different personalities per model tier
- Custom guardrails or constraints
- A/B testing different prompt strategies

### 🔐 Security & Authentication

**Proxy Authentication:**

Require clients to authenticate with the proxy:

```bash
PROXY_AUTH_KEY="your-secret-key"
```

Clients must provide this key:

```bash
export ANTHROPIC_API_KEY="your-secret-key"  # Same as PROXY_AUTH_KEY
export ANTHROPIC_BASE_URL=http://localhost:8082
```

**Note:** This is for securing YOUR proxy, not for Anthropic's API.

### 🔧 Advanced Configuration

**Server Settings:**

```bash
HOST="0.0.0.0"         # Listen on all interfaces
PORT="8082"            # Port number
LOG_LEVEL="INFO"       # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Performance:**

```bash
REQUEST_TIMEOUT="90"        # Request timeout (seconds)
MAX_RETRIES="2"             # Retries for failed requests
MAX_TOKENS_LIMIT="4096"     # Max tokens per request
MIN_TOKENS_LIMIT="100"      # Min tokens per request
```

**Model Selection:**

```bash
ENABLE_OPENROUTER_SELECTION="true"  # Show OpenRouter models in selector
```

Set to `false` to hide OpenRouter marketplace (show only local models).

**Custom Headers:**

Inject custom headers into API requests:

```bash
CUSTOM_HEADER_USER_AGENT="my-app/1.0"
CUSTOM_HEADER_X_API_KEY="..."
CUSTOM_HEADER_AUTHORIZATION="Bearer ..."
CUSTOM_HEADER_X_CUSTOM="value"
```

Headers are automatically formatted:
- `CUSTOM_HEADER_USER_AGENT` → `User-Agent: my-app/1.0`
- `CUSTOM_HEADER_X_API_KEY` → `X-API-KEY: ...`

---

## 📚 Configuration Reference

### Environment Variables (Semantic Names)

**Recommended:** Use semantic names for clarity.

```bash
PROVIDER_API_KEY="..."     # Your backend provider's API key
PROVIDER_BASE_URL="..."    # Your backend provider's base URL
PROXY_AUTH_KEY="..."       # Optional auth key for proxy clients
```

### Legacy Names (Deprecated)

These still work but show deprecation warnings:

```bash
OPENAI_API_KEY="..."       # Use PROVIDER_API_KEY instead
OPENAI_BASE_URL="..."      # Use PROVIDER_BASE_URL instead
ANTHROPIC_API_KEY="..."    # Use PROXY_AUTH_KEY instead
```

**Why deprecated?**
- `OPENAI_API_KEY` works with ANY provider, not just OpenAI
- `ANTHROPIC_API_KEY` is for proxy auth, NOT Anthropic's API (confusing!)

### Complete Configuration

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for comprehensive reference of all 50+ environment variables.

---

## 🎓 Examples

### Cost Optimization

Use free models for cheap tasks, paid for expensive:

```bash
# OpenRouter free models
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

BIG_MODEL="anthropic/claude-sonnet-4"    # Paid, powerful
MIDDLE_MODEL="google/gemini-flash-1.5"   # Free!
SMALL_MODEL="x-ai/grok-beta:free"        # Free!
```

### Privacy & Local-First

Everything runs on your machine:

```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"

BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="qwen2.5:14b"
SMALL_MODEL="llama3.1:8b"

TRACK_USAGE="true"  # Local SQLite, no data sent anywhere
```

### Maximum Reasoning Power

Configure for reasoning-optimized models:

```bash
# Use GPT-5 with high reasoning effort
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"

BIG_MODEL="gpt-5:high"           # High reasoning effort
MIDDLE_MODEL="o4-mini:50000"     # 50k thinking tokens
SMALL_MODEL="gpt-4o"             # Standard model

REASONING_EFFORT="high"
REASONING_MAX_TOKENS="16000"
VERBOSITY="high"
```

### Multi-Provider Hybrid

Different providers for different use cases:

```bash
# Default: OpenRouter
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# BIG: Local Ollama (privacy + free)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# MIDDLE: Gemini (free, fast)
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/openai/"
MIDDLE_API_KEY="your-gemini-key"
MIDDLE_MODEL="gemini-3-pro-preview-11-2025"

# SMALL: OpenRouter free tier
SMALL_MODEL="x-ai/grok-beta:free"
```

More examples: [docs/EXAMPLES.md](docs/EXAMPLES.md)

---

## 🐛 Troubleshooting

### 401 "user not found" Error

**Cause:** Negative balance on OpenRouter (even $-0.01 locks ALL models, including free ones)

**Fix:**
1. Check balance: https://openrouter.ai/settings/credits
2. Add credits or switch to free models:
   ```bash
   BIG_MODEL="x-ai/grok-beta:free"
   MIDDLE_MODEL="google/gemini-flash-1.5:free"
   ```

### API Key Not Working

**Check:**
1. Correct variable name:
   ```bash
   PROVIDER_API_KEY="..."  # NOT OPENAI_API_KEY (deprecated)
   ```
2. API key has no quotes or extra spaces
3. Proxy shows API key status on startup

### Model Not Found

**OpenRouter users:** Use `provider/model` format:
```bash
BIG_MODEL="anthropic/claude-sonnet-4"  # NOT "claude-sonnet-4"
```

**List available models:**
```bash
python -m src.cli.model_selector
```

### Thinking Tokens Not Working

**Requirements:**
1. Model must support extended thinking (GPT-5, Claude 4+, Gemini 2+, o-series)
2. Set `REASONING_EFFORT` or `REASONING_MAX_TOKENS`
3. Or use suffix notation: `o4-mini:high`, `claude-opus-4:8k`

### Connection Refused

**Check:**
1. Proxy is running: `python start_proxy.py`
2. Correct URL: `export ANTHROPIC_BASE_URL=http://localhost:8082`
3. Port not in use: `lsof -i :8082`

More troubleshooting: [docs/TROUBLESHOOTING_401.md](docs/TROUBLESHOOTING_401.md)

---

## 📖 Documentation

- **[Configuration Guide](docs/CONFIGURATION.md)** - Complete reference for all environment variables
- **[Examples](docs/EXAMPLES.md)** - Common setups and use cases
- **[Troubleshooting](docs/TROUBLESHOOTING_401.md)** - Fix common issues
- **[API Reference](docs/API.md)** - HTTP API endpoints and schemas

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - do whatever you want with it.

---

<div align="center">

**Made with ❤️ for the Claude Code community**

[Report Bug](https://github.com/aaaronmiller/claude-code-proxy/issues) • [Request Feature](https://github.com/aaaronmiller/claude-code-proxy/issues) • [Discussions](https://github.com/aaaronmiller/claude-code-proxy/discussions)

</div>
