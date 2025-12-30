# Claude Code Proxy - Documentation Index

> **One-stop reference for all proxy features**

---

## Quick Links

| Doc | Description |
|-----|-------------|
| [README.md](README.md) | Project overview, features, installation |
| [SETUP.md](SETUP.md) | Detailed setup with aliases and auto-healing |
| [CROSSTALK.md](CROSSTALK.md) | Multi-model conversation orchestration |

---

## Getting Started

### 1. Install (30 seconds)

```bash
git clone https://github.com/youruser/claude-code-proxy.git
cd claude-code-proxy
uv sync  # or: pip install -r requirements.txt
```

### 2. Configure (30 seconds)

```bash
cp .env.example .env
nano .env  # Add your API key
```

**Minimum config:**
```bash
OPENAI_API_KEY="sk-your-key"
```

### 3. Start

```bash
python start_proxy.py
```

### 4. Use with Claude Code

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "Write a Python hello world"
```

---

## CLI Commands Reference

### Server & Configuration

```bash
python start_proxy.py              # Start the proxy server
python start_proxy.py --settings   # Launch unified settings TUI
python start_proxy.py --doctor     # Run health check + auto-fix
python start_proxy.py --config     # Show current configuration
python start_proxy.py --dry-run    # Validate without starting
```

### Model Configuration

```bash
python start_proxy.py --set-big MODEL       # Set BIG model (e.g., claude-3-opus)
python start_proxy.py --set-middle MODEL    # Set MIDDLE model
python start_proxy.py --set-small MODEL     # Set SMALL model
python start_proxy.py --show-models         # Show available models
python start_proxy.py --check-endpoints     # Verify API keys
python start_proxy.py --update-models       # Scrape latest model stats
python start_proxy.py --rank-models         # AI-rank coding models
```

### Crosstalk (Multi-Model Chat)

```bash
python start_proxy.py --crosstalk-studio    # Launch visual TUI
python start_proxy.py --crosstalk "m1,m2"   # Quick 2-model setup
python start_proxy.py --crosstalk-paradigm relay   # Set paradigm
python start_proxy.py --crosstalk-iterations 20    # Set rounds
```

### Prompt Configuration

```bash
python start_proxy.py --configure-prompts  # Prompt injection wizard
python start_proxy.py --configure-terminal # Terminal display config
python start_proxy.py --setup              # First-time setup wizard
```

---

## Features Overview

### Core Features
- **Multi-Provider Support**: OpenRouter, OpenAI, Anthropic, Azure, Gemini/VibeProxy
- **Model Mapping**: BIG/MIDDLE/SMALL model tiers with auto-routing
- **Streaming**: Full streaming support with token counting
- **Tool Normalization**: Provider-aware parameter transformation

### Advanced Features
- **Crosstalk**: Model-to-model conversations (1-8 models)
- **Prompt Injection**: Add system prompts to all requests
- **Usage Tracking**: Cost and token analytics
- **Live Dashboard**: Real-time request monitoring

### Configuration
- **Settings TUI**: Visual configuration editor
- **Doctor Mode**: Auto-heal configuration issues
- **Hybrid Mode**: Route model tiers to different providers

---

## Provider Configuration

### OpenRouter (Recommended)

```bash
OPENAI_API_KEY="sk-or-v1-..."
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-3-opus"
MIDDLE_MODEL="anthropic/claude-3-sonnet"
SMALL_MODEL="anthropic/claude-3-haiku"
```

### OpenAI Direct

```bash
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4-turbo"
MIDDLE_MODEL="gpt-4"
SMALL_MODEL="gpt-3.5-turbo"
```

### Local Models (Ollama)

```bash
OPENAI_API_KEY="dummy"
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/qwen2.5:32b"
SMALL_MODEL="ollama/qwen2.5:7b"
```

### Hybrid Mode (Different Providers per Tier)

```bash
# Big: VibeProxy (Gemini)
ENABLE_BIG_ENDPOINT=true
BIG_ENDPOINT=http://127.0.0.1:8317/v1
BIG_API_KEY=oauth_auto
BIG_MODEL=gemini-2.5-pro

# Middle: OpenRouter
ENABLE_MIDDLE_ENDPOINT=true
MIDDLE_ENDPOINT=https://openrouter.ai/api/v1
MIDDLE_API_KEY=sk-or-xxx
MIDDLE_MODEL=anthropic/claude-sonnet-4

# Small: OpenAI
ENABLE_SMALL_ENDPOINT=true
SMALL_ENDPOINT=https://api.openai.com/v1
SMALL_API_KEY=sk-xxx
SMALL_MODEL=gpt-4o-mini
```

---

## Detailed Guides

### In `instructions/` folder:

| Path | Content |
|------|---------|
| `api/reference.md` | API endpoint documentation |
| `development/` | Feature guides and enhancement docs |
| `examples/` | Usage examples and prompt snippets |
| `getting-started/` | Installation, configuration, quickstart |
| `guides/` | Crosstalk, production, troubleshooting |
| `operations/` | API keys, binary packaging |
| `troubleshooting/` | 401 errors, common issues |

---

## Architecture & Development

| Doc | Description |
|-----|-------------|
| `instructions/development/multi-provider-architecture.md` | Provider adapters, tool normalization |
| `instructions/development/changelog.md` | Recent changes and updates |
| `instructions/troubleshooting/tool-call-resolution.md` | Tool call issue fixes |
| `instructions/troubleshooting/antigravity-toolcall-fix.md` | VibeProxy-specific fixes |

---

## Troubleshooting

### Common Issues

**401 Unauthorized**
```bash
python start_proxy.py --doctor  # Auto-fix API keys
```

**Model not found**
```bash
python start_proxy.py --show-models  # List available models
```

**Tool call failures**
- Check `Proxy.md` for provider-specific tool normalization
- Run with `--log-level debug` for detailed logs

---

## File Structure

```
claude-code-proxy/
├── start_proxy.py          # Main entry point
├── .env                    # Configuration (create from .env.example)
├── CROSSTALK.md           # Multi-model chat documentation
├── SETUP.md               # Detailed setup guide
├── README.md              # Project overview
│
├── src/
│   ├── core/              # Core proxy logic
│   ├── services/          # Providers, models, prompts
│   └── cli/               # CLI tools and TUIs
│
├── configs/
│   └── crosstalk/         # Crosstalk templates and presets
│
└── instructions/          # Extended documentation
    ├── api/
    ├── development/
    ├── examples/
    ├── getting-started/
    ├── guides/
    ├── operations/
    └── troubleshooting/
```
