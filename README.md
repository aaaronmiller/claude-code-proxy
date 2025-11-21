<div align="center">

# 🔄 Claude Code Proxy

**Use Claude Code CLI with any OpenAI-compatible provider**

Stop being locked into Anthropic. Use OpenRouter, Gemini, local models, or any provider you want.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Quick Start](#quick-start) • [Configuration](docs/CONFIGURATION.md) • [Examples](docs/EXAMPLES.md)

</div>

## What It Does

Sits between Claude Code CLI and your chosen API provider. Claude Code thinks it's talking to Anthropic, but you're actually using whatever provider you want (OpenRouter, Gemini, OpenAI, local models, etc.).

**Why?** Save money, use free models, run locally, or use any provider that works for you.

## Quick Start

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
cp .env.example .env
nano .env  # Add your PROVIDER_API_KEY and PROVIDER_BASE_URL
python start_proxy.py
```

In another terminal:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "write a fibonacci function"
```

Done. Claude Code now uses your provider.

## Provider Examples

### Google Gemini (Free)

```bash
PROVIDER_API_KEY="your-gemini-key"
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
BIG_MODEL="gemini-3-pro-preview-11-2025"
```

Get key: https://makersuite.google.com/app/apikey

### OpenRouter (352+ models, free tier)

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
```

Get key: https://openrouter.ai/keys

### Local Models (100% free, runs on your machine)

```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
```

Install: https://ollama.ai

## How It Works

Claude Code sends requests to `ANTHROPIC_BASE_URL`. The proxy:
1. Converts Claude API format → OpenAI API format
2. Routes to your configured provider
3. Converts response back to Claude format
4. Returns to Claude Code

Claude Code can't tell the difference.

## Model Mapping

When Claude Code asks for:
- `claude-opus` → Uses your `BIG_MODEL`
- `claude-sonnet` → Uses your `MIDDLE_MODEL`
- `claude-haiku` → Uses your `SMALL_MODEL`

You can set each to a different model, or different providers:

```bash
# Use local model for expensive tasks, cloud for cheap tasks
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"                          # Local Ollama

MIDDLE_ENDPOINT="https://openrouter.ai/api/v1"
MIDDLE_MODEL="google/gemini-flash"               # OpenRouter free model
```

Why? **Flexibility.** Route models however saves you the most money.

## Features

- Works with any OpenAI-compatible API
- Extended thinking tokens for reasoning models (GPT-5, Claude 4+, Gemini 2+)
- Rich terminal output with metrics
- Web UI at `http://localhost:8082` for configuration
- 100% local tracking (no data sent anywhere)

## Built-in Tools

### Interactive Model Selector

Browse 352+ models with search and filtering:

```bash
python -m src.cli.model_selector
```

### Crosstalk Mode

Multi-agent collaboration:

```bash
python -m src.cli.crosstalk_cli
```

### Configuration Tools

Interactive setup wizards:

```bash
python configure_terminal_output.py  # Terminal display settings
python configure_prompt_injection.py # Custom prompt injection
```

### Web UI

Visual configuration editor and monitoring dashboard:

```
http://localhost:8082
```

## Documentation

- **[Configuration Guide](docs/CONFIGURATION.md)** - All options explained
- **[Examples](docs/EXAMPLES.md)** - Common setups
- **[Troubleshooting](docs/TROUBLESHOOTING_401.md)** - Fix common issues

## License

MIT - do whatever you want with it.

---

<div align="center">

[Report Bug](https://github.com/aaaronmiller/claude-code-proxy/issues) • [Request Feature](https://github.com/aaaronmiller/claude-code-proxy/issues)

</div>
