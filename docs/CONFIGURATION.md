# Configuration Guide

Complete reference for all environment variables and configuration options.

## Table of Contents

- [Core Configuration](#core-configuration)
- [Provider Setup](#provider-setup)
- [Model Configuration](#model-configuration)
- [Reasoning & Extended Thinking](#reasoning--extended-thinking)
- [Hybrid Mode (Multi-Provider)](#hybrid-mode-multi-provider)
- [Terminal Output](#terminal-output)
- [Usage Tracking & Analytics](#usage-tracking--analytics)
- [Advanced Options](#advanced-options)

---

## Core Configuration

### Required Variables

```bash
# Your provider's API key
PROVIDER_API_KEY="your-api-key-here"

# Provider base URL
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
```

### Legacy Names (Deprecated)

These still work but show deprecation warnings:

```bash
OPENAI_API_KEY="..."       # Use PROVIDER_API_KEY instead
OPENAI_BASE_URL="..."      # Use PROVIDER_BASE_URL instead
ANTHROPIC_API_KEY="..."    # Use PROXY_AUTH_KEY instead
```

### Optional Security

```bash
# Require clients to provide this key to access the proxy
PROXY_AUTH_KEY="your-secret-key"
```

---

## Provider Setup

### OpenRouter

352+ models, generous free tier, best for experimentation.

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
```

Get your key: https://openrouter.ai/keys

### Google Gemini

Free with API key, excellent for development.

```bash
PROVIDER_API_KEY="AIza..."
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
```

Get your key: https://makersuite.google.com/app/apikey

### OpenAI

Official OpenAI API.

```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"
```

### Azure OpenAI

Enterprise-grade OpenAI via Azure.

```bash
PROVIDER_API_KEY="your-azure-key"
PROVIDER_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
AZURE_API_VERSION="2024-03-01-preview"
```

### Local Models (Ollama)

100% free, runs on your machine.

```bash
PROVIDER_API_KEY="dummy"  # Any value works
PROVIDER_BASE_URL="http://localhost:11434/v1"
```

Install Ollama: https://ollama.ai

### LM Studio

Local models with a GUI.

```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://127.0.0.1:1234/v1"
```

---

## Model Configuration

### Basic Setup

```bash
BIG_MODEL="gpt-4o"           # Used for Claude Opus requests
MIDDLE_MODEL="gpt-4o"        # Used for Claude Sonnet requests
SMALL_MODEL="gpt-4o-mini"    # Used for Claude Haiku requests
```

### Model Mapping

When Claude Code requests `claude-opus-4`, the proxy routes to your `BIG_MODEL`.
When Claude Code requests `claude-sonnet-4`, the proxy routes to your `MIDDLE_MODEL`.
When Claude Code requests `claude-haiku-4`, the proxy routes to your `SMALL_MODEL`.

### Model Name Formats

Different providers use different naming conventions:

```bash
# OpenRouter (provider/model format)
BIG_MODEL="anthropic/claude-sonnet-4"
BIG_MODEL="openai/gpt-4o"
BIG_MODEL="google/gemini-pro-1.5"

# Ollama (simple names)
BIG_MODEL="qwen2.5:72b"
BIG_MODEL="llama3.1:70b"

# Direct OpenAI (model names)
BIG_MODEL="gpt-4o"
BIG_MODEL="o1-preview"
```

---

## Reasoning & Extended Thinking

Enable extended thinking for models that support it (GPT-5, o1/o3, Claude 4+, Gemini 2+).

### OpenAI Reasoning Effort

For GPT-5 and o-series models:

```bash
REASONING_EFFORT="high"  # Options: low, medium, high
```

- **low**: ~20% of max tokens for thinking
- **medium**: ~50% of max tokens for thinking
- **high**: ~80% of max tokens for thinking

### Anthropic/Gemini Token Budget

For Claude and Gemini models:

```bash
REASONING_MAX_TOKENS="16000"  # Exact token count
```

Ranges:
- **Anthropic Claude**: 1024-16000 tokens
- **Google Gemini**: 0-24576 tokens

### Verbosity

```bash
VERBOSITY="high"  # Options: default, high
```

Affects response detail level (provider-specific).

### Exclude Reasoning from Response

```bash
REASONING_EXCLUDE="true"  # Default: false
```

Use reasoning internally but don't include it in the response (OpenAI only).

### Per-Model Overrides

Override reasoning settings for specific model tiers:

```bash
BIG_MODEL_REASONING="high"
MIDDLE_MODEL_REASONING="medium"
SMALL_MODEL_REASONING="low"
```

### Model Name Suffix Notation

Specify reasoning directly in model names:

```bash
# OpenAI (effort levels or token budgets)
BIG_MODEL="o4-mini:high"          # High effort
BIG_MODEL="o4-mini:50000"         # 50k thinking tokens
BIG_MODEL="gpt-5:100k"            # 102,400 tokens

# Anthropic
BIG_MODEL="claude-opus-4-20250514:8k"     # 8192 tokens

# Gemini
BIG_MODEL="gemini-2.5-flash:16000"        # 16000 tokens
```

Suffix notation overrides environment variables.

---

## Hybrid Mode (Multi-Provider)

Route different model tiers to different providers simultaneously!

### Example: Local BIG, Cloud MIDDLE/SMALL

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
SMALL_MODEL="google/gemini-flash-1.5"
```

### Full Hybrid Setup

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

---

## Terminal Output

### Display Mode

```bash
TERMINAL_DISPLAY_MODE="detailed"  # Options: minimal, normal, detailed, debug
```

### Feature Toggles

```bash
TERMINAL_SHOW_WORKSPACE="true"          # Show project/workspace name
TERMINAL_SHOW_CONTEXT_PCT="true"        # Show context window percentage
TERMINAL_SHOW_TASK_TYPE="true"          # Show task icons (🧠 🔧 📝)
TERMINAL_SHOW_SPEED="true"              # Show tokens/sec
TERMINAL_SHOW_COST="true"               # Show cost estimates
TERMINAL_SHOW_DURATION_COLORS="true"    # Color-code request duration
```

### Color Scheme

```bash
TERMINAL_COLOR_SCHEME="auto"  # Options: auto, vibrant, subtle, mono
```

### Session Colors

```bash
TERMINAL_SESSION_COLORS="true"  # Different color per session
```

---

## Usage Tracking & Analytics

### Enable Tracking

```bash
TRACK_USAGE="true"  # Default: false
```

Stores metadata in SQLite database:
- Model used
- Token counts (input/output/thinking)
- Duration
- Cost estimates
- Request counts

**Privacy**: All tracking is local, no data sent anywhere. Message content is never stored.

### Database Location

```bash
USAGE_DB_PATH="usage_tracking.db"  # Default location
```

### Dashboard

```bash
ENABLE_DASHBOARD="true"             # Enable live dashboard
DASHBOARD_LAYOUT="default"          # Options: default, compact, detailed
DASHBOARD_REFRESH="0.5"             # Refresh interval in seconds
DASHBOARD_WATERFALL_SIZE="20"       # Number of requests to show
```

### Compact Logger

```bash
COMPACT_LOGGER="true"  # Single-line logs with emojis
```

---

## Advanced Options

### Server Settings

```bash
HOST="0.0.0.0"         # Listen on all interfaces
PORT="8082"            # Port number
LOG_LEVEL="INFO"       # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Performance

```bash
REQUEST_TIMEOUT="90"        # Request timeout in seconds
MAX_RETRIES="2"             # Number of retries for failed requests
MAX_TOKENS_LIMIT="4096"     # Max tokens per request
MIN_TOKENS_LIMIT="100"      # Min tokens per request
```

### Model Selection

```bash
ENABLE_OPENROUTER_SELECTION="true"  # Show OpenRouter models in selector
```

Set to `false` to hide OpenRouter marketplace (show only local models).

### Custom Headers

Inject custom headers into API requests:

```bash
CUSTOM_HEADER_USER_AGENT="my-app/1.0"
CUSTOM_HEADER_X_API_KEY="..."
CUSTOM_HEADER_AUTHORIZATION="Bearer ..."
```

Headers are automatically converted:
- `CUSTOM_HEADER_USER_AGENT` → `User-Agent: my-app/1.0`
- `CUSTOM_HEADER_X_API_KEY` → `X-API-KEY: ...`

### Custom System Prompts

Override system prompts per model:

```bash
# Enable custom prompts
ENABLE_CUSTOM_BIG_PROMPT="true"
ENABLE_CUSTOM_MIDDLE_PROMPT="true"
ENABLE_CUSTOM_SMALL_PROMPT="true"

# From files
BIG_SYSTEM_PROMPT_FILE="/path/to/prompt.txt"
MIDDLE_SYSTEM_PROMPT_FILE="/path/to/prompt.txt"
SMALL_SYSTEM_PROMPT_FILE="/path/to/prompt.txt"

# Or inline
BIG_SYSTEM_PROMPT="You are a helpful assistant..."
MIDDLE_SYSTEM_PROMPT="..."
SMALL_SYSTEM_PROMPT="..."
```

---

## Quick Reference

### Minimal Config

```bash
PROVIDER_API_KEY="your-key"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
```

### Recommended Config

```bash
# Provider
PROVIDER_API_KEY="your-key"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

# Models
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5"

# Reasoning
REASONING_EFFORT="high"
REASONING_MAX_TOKENS="16000"

# Features
TRACK_USAGE="true"
TERMINAL_DISPLAY_MODE="detailed"
```

### Full Config Example

See `.env.example` in the project root for a complete configuration template with all options.

---

## Need Help?

- [Troubleshooting Guide](TROUBLESHOOTING_401.md)
- [Examples](EXAMPLES.md)
- [API Reference](API.md)
- [GitHub Issues](https://github.com/aaaronmiller/claude-code-proxy/issues)
