# Configuration Guide

Complete reference for all environment variables, CLI tools, and configuration options.

## Table of Contents

- [Interactive CLI Tools](#interactive-cli-tools)
- [Core Configuration](#core-configuration)
- [Provider Setup](#provider-setup)
- [Model Configuration](#model-configuration)
- [Reasoning & Extended Thinking](#reasoning--extended-thinking)
- [Terminal Output](#terminal-output)
- [Dashboards & Analytics](#dashboards--analytics)
- [Hybrid Mode](#hybrid-mode-multi-provider)

---

## Interactive CLI Tools

The easiest way to configure the proxy is using the built-in interactive tools. All tools are accessed via `start_proxy.py`.

### 🛠️ Configuration Wizards

| Command | Description |
|---------|-------------|
| `python start_proxy.py --setup` | **First-time setup**. Guided wizard to set provider, API keys, and basic preferences. |
| `python start_proxy.py --configure-dashboard` | **Dashboard Design**. Interactive TUI to arrange your 10-slot terminal dashboard. |
| `python start_proxy.py --configure-terminal` | **Output Styling**. Customize colors, metrics, and display modes (minimal/detailed). |
| `python start_proxy.py --configure-prompts` | **Prompt Injection**. Configure stats injected into Claude's context. |
| `python start_proxy.py --select-models` | **Model Selector**. Interactive menu to choose specific models for Big/Middle/Small tiers. |
| `python start_proxy.py --fix-keys` | **Auto-Healing**. Repair broken API keys or switch providers. |

### 📊 Analytics & Diagnostics

| Command | Description |
|---------|-------------|
| `python start_proxy.py --analytics` | View top models, cost summary, and JSON/TOON analysis. |
| `python start_proxy.py --validate-config` | Run a health check on your current configuration. |
| `python start_proxy.py --config` | specific configuration dump (sanitized tokens). |

---

## Core Configuration

Environment variables can be set in your `.env` file or exported in your shell.

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

### VibeProxy / Antigravity (Recommended)
Free access to Claude and Gemini models via Google's Antigravity service. No API keys needed.
```bash
PROVIDER_API_KEY="dummy"  # Not used - OAuth handled by VibeProxy
PROVIDER_BASE_URL="http://127.0.0.1:8317/v1"

# Recommended models
BIG_MODEL="gemini-claude-opus-4-5-thinking"     # Claude Opus with 128k thinking
MIDDLE_MODEL="gemini-3-pro-preview"             # Gemini 3 Pro
SMALL_MODEL="gemini-3-flash"                    # Fast Gemini 3
REASONING_MAX_TOKENS="128000"
```
**Setup**: Install [VibeProxy](https://github.com/automazeio/vibeproxy/releases), authenticate with Google, then run `python start_proxy.py --setup`.

### OpenRouter (Recommended)
352+ models, generous free tier, best for experimentation.
```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
```

### Google Gemini
Free with API key, excellent for development.
```bash
PROVIDER_API_KEY="AIza..."
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
```

### OpenAI
Official OpenAI API.
```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"
```

### Local Models (Ollama)
100% free, runs on your machine.
```bash
PROVIDER_API_KEY="dummy"  # Any value works
PROVIDER_BASE_URL="http://localhost:11434/v1"
```

---

## Model Configuration

### Basic Setup
```bash
BIG_MODEL="gpt-4o"           # for Claude Opus requests (Complex tasks)
MIDDLE_MODEL="gpt-4o"        # for Claude Sonnet requests (General coding)
SMALL_MODEL="gpt-4o-mini"    # for Claude Haiku requests (Fast/Routine)
```

### Interactive Selector
Use `python start_proxy.py --select-models` to browse and select models from your provider including benchmarks and pricing.

---

## Reasoning & Extended Thinking

Enable extended thinking for compatible models (o1, Claude 3.7+, Gemini 2+).

### OpenAI Reasoning Effort
For o-series models:
```bash
REASONING_EFFORT="high"  # Options: low, medium, high
```

### Token Budgets (Anthropic/Gemini)
For models with explicit thinking budgets:
```bash
REASONING_MAX_TOKENS="128000"  # Range: 1024-128000 for Claude, 0-24576 for Gemini
```

### Suffix Notation (Power User)
Override settings per-model using suffix notation:
```bash
BIG_MODEL="o3-mini:high"              # Force High effort
BIG_MODEL="claude-opus-4:128k"        # Force 128k thinking tokens
BIG_MODEL="gemini-2.5-flash:16k"      # Force 16k thinking budget
```

---

## Terminal Output

The proxy provides a rich, color-coded terminal interface.

```bash
# Display mode: minimal, normal, detailed, debug
TERMINAL_DISPLAY_MODE="detailed"

# Metrics toggles
TERMINAL_SHOW_COST="true"
TERMINAL_SHOW_SPEED="true"
TERMINAL_SHOW_WORKSPACE="true"

# Visuals
TERMINAL_COLOR_SCHEME="auto"    # auto, vibrant, subtle, mono
TERMINAL_SESSION_COLORS="true"  # Unique color per session
```

Use `python start_proxy.py --configure-terminal` to preview these settings live.

---

## Dashboards & Analytics

### Terminal Dashboard
A TUI dashboard that runs alongside your code.
```bash
ENABLE_DASHBOARD="true"         # Enable live dashboard
DASHBOARD_LAYOUT="default"      # Options: default, compact, detailed
DASHBOARD_REFRESH="0.5"         # Refresh interval in seconds
```
Use `python start_proxy.py --configure-dashboard` to design your layout.

### Usage Tracking
Stores metadata in a local SQLite database (`usage_tracking.db`).
```bash
TRACK_USAGE="true"  # Default: false
```
**Privacy**: All tracking is local. Message content is NEVER stored.

---

## Hybrid Mode (Multi-Provider)

Route different model tiers to different providers simultaneously.

```bash
# 1. Enable per-model routing
ENABLE_BIG_ENDPOINT="true"

# 2. Configure the specific endpoint
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="qwen2.5:72b"

# Other models use the main PROVIDER details
MIDDLE_MODEL="anthropic/claude-sonnet-4"
```
