<div align="center">

# 🔄 Claude Code Proxy

**Use Claude Code with any OpenAI-compatible provider**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Examples](#examples)

</div>

---

## What is Claude Code Proxy?

A drop-in proxy server that lets you use the official **Claude Code CLI** with any OpenAI-compatible API provider—including OpenAI, OpenRouter, Azure OpenAI, Google Gemini, local models (Ollama/LMStudio), and more.

Stop being locked into a single provider. Use the models and providers that work best for you, while keeping the familiar Claude Code CLI experience.

## Features

- 🔌 **Universal Provider Support** - Works with any OpenAI-compatible API (OpenRouter, Azure, Gemini, local models)
- 💰 **Cost Optimization** - Use free models, local models, or cheaper providers
- 🧠 **Advanced Reasoning** - Configure thinking token budgets for GPT-5, Claude, Gemini
- 🎨 **Rich Terminal Output** - Color-coded logs, progress bars, performance metrics
- 📊 **Token Visualization** - Real-time context window and output tracking
- 🌐 **Web UI** - Visual configuration editor with model browser
- 🚀 **Hybrid Routing** - Route different model tiers to different providers simultaneously
- 📦 **Smart Templates** - One-click configs for common setups (free models, local-only, etc.)

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync

# 2. Configure your provider
cp .env.example .env
nano .env  # Set PROVIDER_API_KEY and PROVIDER_BASE_URL

# 3. Start the proxy
python start_proxy.py

# 4. Use Claude Code normally
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "Write a Python function to calculate fibonacci numbers"
```

That's it! Claude Code now uses your configured provider.

## Configuration

### Minimal Setup (Required)

```bash
# .env file
PROVIDER_API_KEY="your-api-key-here"
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
```

### Provider Examples

<details>
<summary><b>OpenRouter (352+ models, generous free tier)</b></summary>

```bash
PROVIDER_API_KEY="sk-or-v1-..."
PROVIDER_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-sonnet-4"
MIDDLE_MODEL="google/gemini-pro-1.5"
SMALL_MODEL="google/gemini-flash-1.5"
```
</details>

<details>
<summary><b>Google Gemini (Free with API key)</b></summary>

```bash
PROVIDER_API_KEY="your-gemini-api-key"
PROVIDER_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
BIG_MODEL="gemini-3-pro-preview-11-2025"
MIDDLE_MODEL="gemini-2.0-flash-exp"
SMALL_MODEL="gemini-2.0-flash-exp"
```
</details>

<details>
<summary><b>Local Models (Ollama - 100% Free)</b></summary>

```bash
PROVIDER_API_KEY="dummy"
PROVIDER_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="qwen2.5:72b"
MIDDLE_MODEL="llama3.1:70b"
SMALL_MODEL="llama3.1:8b"
```
</details>

<details>
<summary><b>OpenAI (Official API)</b></summary>

```bash
PROVIDER_API_KEY="sk-..."
PROVIDER_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o-mini"
```
</details>

<details>
<summary><b>Azure OpenAI</b></summary>

```bash
PROVIDER_API_KEY="your-azure-key"
PROVIDER_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
AZURE_API_VERSION="2024-03-01-preview"
BIG_MODEL="gpt-4"
```
</details>

### Advanced Features

```bash
# Extended thinking for reasoning models
REASONING_EFFORT="high"              # low, medium, high
REASONING_MAX_TOKENS="16000"         # Fine-grained token control

# Hybrid routing (mix local + cloud)
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"  # Use local Ollama for BIG
MIDDLE_ENDPOINT="https://openrouter.ai/api/v1"  # Use OpenRouter for MIDDLE
```

See [CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

## Usage

### With Claude Code CLI

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "Help me debug this Python code"
```

### With Claude Desktop App

Add to your Claude Desktop config (`~/.claude/config.json`):

```json
{
  "api": {
    "baseURL": "http://localhost:8082"
  }
}
```

### Direct API Calls

```bash
curl http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 1024
  }'
```

## Documentation

- 📖 **[Configuration Guide](docs/CONFIGURATION.md)** - Complete environment variable reference
- 🚀 **[Deployment Guide](docs/DEPLOYMENT.md)** - Docker, production setup, scaling
- 🔌 **[API Reference](docs/API.md)** - Endpoint specifications
- 💡 **[Examples](docs/EXAMPLES.md)** - Common use cases and recipes
- 🐛 **[Troubleshooting](docs/TROUBLESHOOTING_401.md)** - Common issues and solutions

## Examples

### Interactive Model Selection

```bash
python -m src.cli.model_selector
```

Browse 352+ models with search, filtering, and one-click selection.

### Web UI

Start the proxy and visit `http://localhost:8082` for:
- Visual configuration editor
- Model browser with specs
- Real-time monitoring
- Usage analytics

### Configuration Templates

```bash
# View available templates
python -m src.utils.templates list

# Apply a template
python -m src.utils.templates apply free-models
```

Pre-built templates:
- `free-models` - Free tier models only
- `local-only` - 100% local with Ollama
- `high-reasoning` - Maximum thinking tokens
- `cost-optimized` - Cheapest reliable setup
- `enterprise` - Azure + high availability

## Project Structure

```
claude-code-proxy/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── conversion/       # Claude ↔ OpenAI conversion
│   ├── core/             # Config, client, model manager
│   ├── cli/              # Interactive tools
│   └── utils/            # Helpers, templates, modes
├── docs/                 # Detailed documentation
├── examples/             # Example configs
├── .env.example          # Configuration template
└── start_proxy.py        # Entry point
```

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ by the community**

[Report Bug](https://github.com/aaaronmiller/claude-code-proxy/issues) • [Request Feature](https://github.com/aaaronmiller/claude-code-proxy/issues)

</div>
