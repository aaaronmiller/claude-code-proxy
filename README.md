<div align="center">

<img src="web-ui/static/logo.png" alt="The Ultimate Proxy" width="120">

# ⚡ The Ultimate Proxy

**The only proxy you need for Claude Code CLI**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![2025 Ready](https://img.shields.io/badge/2025-Ready-06ffd4.svg)](#)

[Quick Start](#-quick-start) • [Features](#-features) • [Web Dashboard](#-web-dashboard) • [Crosstalk](docs/crosstalk.md)

<br>

<img src="web-ui/static/hero-banner.png" alt="The Ultimate Proxy Dashboard" width="800">

**Route Claude Code to any provider. Save 90% on API costs. Run locally for free.**

</div>

---

## 🌟 What Is It?

The Ultimate Proxy sits between Claude Code CLI and your chosen API provider. It translates Anthropic's API format to OpenAI-compatible format, letting you use **any model** with Claude Code:

```
Claude Code CLI  →  The Ultimate Proxy  →  Any Provider
                                           ├─ OpenRouter
                                           ├─ Gemini / VibeProxy
                                           ├─ OpenAI
                                           ├─ Azure
                                           ├─ Ollama (local)
                                           └─ LM Studio (local)
```

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/holegots/claude-code-proxy.git
cd claude-code-proxy

# Run the automated setup
python quickstart.py
```

This will:
- ✅ Check Python version (3.9+ required)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Configure environment variables
- ✅ Initialize the database
- ✅ Launch the proxy

### Option 2: Manual Setup

```bash
# Clone & install
git clone https://github.com/holegots/claude-code-proxy.git
cd claude-code-proxy

# Install dependencies (choose one)
uv sync                    # Recommended (faster)
# OR
pip install -r requirements.txt

# Interactive setup wizard
python start_proxy.py --setup

# Start the proxy
python start_proxy.py
```

### Using with Claude Code

In a **new terminal**, run:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY=pass
claude
```

> 💡 **Pro Tip**: Add aliases to your `~/.zshrc` for easier access (see [Setup Guide](docs/setup.md))

---

## 🌌 VibeProxy + Antigravity (Free Premium Models)

The easiest way to use Claude Code with premium models for **free**:

1. **Install VibeProxy**: [Download](https://github.com/automazeio/vibeproxy/releases)
2. **Authenticate**: Sign in with Google (Antigravity OAuth)
3. **Setup**: `python start_proxy.py --setup` → Select "VibeProxy/Antigravity"

**What you get:**
- 🧠 Claude Opus 4.5 with 128k thinking tokens
- ⚡ Gemini 3 Pro/Flash
- 📊 BIG/MIDDLE/SMALL model routing
- 📈 Usage tracking & analytics
- 💸 No API keys or billing required

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider** | OpenRouter, Gemini, OpenAI, Azure, Ollama, LM Studio |
| **Model Routing** | BIG/MIDDLE/SMALL tiers with intelligent routing |
| **Web Dashboard** | Real-time monitoring with 2025 glassmorphism UI |
| **Crosstalk** | Model-to-model conversations (up to 8 models) |
| **Usage Tracking** | Cost analytics and token metrics |
| **Extended Thinking** | Up to 128k thinking tokens for reasoning models |
| **Prompt Injection** | Add custom prompts showing routing info |
| **Model Cascade** | Automatic fallback on provider errors |

---

## 🎨 Web Dashboard

Access at `http://localhost:8082` when running.

- **2025 Glassmorphism UI** with aurora gradients
- Real-time request monitoring
- Provider configuration
- Model selection with hybrid routing
- WebSocket live log streaming
- Profile management

---

## 🗣️ Crosstalk

Multi-model conversations where AI models talk to each other:

```bash
# Launch visual TUI
python start_proxy.py --crosstalk-studio

# Quick setup
python start_proxy.py --crosstalk "claude-opus,gemini-pro" --topic "Explore consciousness"
```

**Features:**
- Up to 8 models in a conversation
- Multiple paradigms: relay, debate, memory, report
- Jinja templates for message formatting
- Backrooms-compatible import/export
- MCP integration for programmatic access

[Read the Crosstalk Guide →](CROSSTALK.md)

---

## 🛠️ CLI Commands

```bash
# Configuration
python start_proxy.py --setup           # First-time wizard
python start_proxy.py --settings        # Unified settings TUI
python start_proxy.py --doctor          # Health check + auto-fix

# Model management
python start_proxy.py --select-models   # Interactive model selector
python start_proxy.py --set-big MODEL   # Quick set BIG model
python start_proxy.py --show-models     # List available models

# Diagnostics
python start_proxy.py --config          # Show configuration
python start_proxy.py --dry-run         # Validate without starting
python start_proxy.py --analytics       # View usage stats
```

---

## 📁 Project Structure

```
the-ultimate-proxy/
├── start_proxy.py          # Main entry point
├── .env                    # Configuration
├── CROSSTALK.md           # Multi-model chat docs
│
├── src/
│   ├── core/              # Proxy core logic
│   ├── api/               # FastAPI routes + WebSocket
│   ├── services/          # Providers, models, prompts
│   └── cli/               # CLI tools and TUIs
│
├── configs/crosstalk/     # Crosstalk presets & templates
├── web-ui/                # Svelte + bits-ui dashboard
└── docs/                  # Extended documentation
```

---

## 🐛 Troubleshooting

**401 Unauthorized**
```bash
python start_proxy.py --doctor  # Auto-fix API keys
```

**Model Not Found**
```bash
python start_proxy.py --show-models  # List available models
```

**Connection Refused**
- Ensure proxy is running: `python start_proxy.py`
- Check port 8082 is not in use

---

## 🔮 Roadmap

- [ ] Desktop GUI (Tauri)
- [ ] Multi-instance analytics
- [ ] MCP Server integration
- [ ] Multi-agent orchestration ("Swarm Mode")

---

<div align="center">

**The Ultimate Proxy** • Made with ❤️ for the Claude Code community

[Report Bug](https://github.com/aaaronmiller/the-ultimate-proxy/issues) • [Request Feature](https://github.com/aaaronmiller/the-ultimate-proxy/issues)

</div>
