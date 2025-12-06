<div align="center">

# 🔄 Claude Code Proxy

**Use Claude Code CLI with any OpenAI-compatible provider**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Quick Start](#-quick-start) • [Features](#-features) • [Configuration](docs/getting-started/configuration.md) • [Examples](docs/guides/examples.md)

</div>

---

## 📖 What It Does

Claude Code Proxy sits between Claude Code CLI and your chosen API provider. It tricks Claude Code into thinking it's talking to Anthropic, but routes requests to **OpenRouter, Gemini, OpenAI, Azure, Ollama, or LM Studio**.

**Why?** Save money, run locally, or use models like GPT-5/o1/Gemini 2.0.

---

## 🚀 Quick Start

1. **Clone and Install**
   ```bash
   git clone https://github.com/aaaronmiller/claude-code-proxy.git
   cd claude-code-proxy
   uv sync
   ```

2. **Setup**
   Run the interactive setup wizard to configure your provider and models:
   ```bash
   python start_proxy.py --setup
   ```

3. **Start Proxy**
   ```bash
   python start_proxy.py
   ```

4. **Connect Claude Code**
   In a separate terminal:
   ```bash
   export ANTHROPIC_BASE_URL=http://localhost:8082
   claude
   ```

## 📂 Project Structure

The repository is organized for clarity and ease of use:

- **`start_proxy.py`**: The single entry point for the server and all CLI tools.
- **`config/`**: Configuration templates and presets.
- **`data/`**: Runtime data (databases, logs, usage stats).
- **`deploy/`**: Deployment configurations (Docker, etc.).
- **`docs/`**: Comprehensive documentation.
- **`scripts/`**: Developer and maintenance scripts.
- **`src/`**: Source code.

## 🛠️ CLI Tools

All tools are accessible via `start_proxy.py`:

- **Setup Wizard**: `python start_proxy.py --setup`
- **Configure Prompts**: `python start_proxy.py --configure-prompts`
- **Configure Terminal**: `python start_proxy.py --configure-terminal`
- **Configure Dashboard**: `python start_proxy.py --configure-dashboard`
- **View Analytics**: `python start_proxy.py --analytics`
- **Select Models**: `python start_proxy.py --select-models`

---

## 🧩 How It Works

```mermaid
graph LR
    A[Claude Code CLI] -->|Claude API Format| B(Proxy)
    B -->|OpenAI API Format| C{Provider}
    C -->|OpenAI Response| B
    B -->|Claude Response| A
    
    subgraph Providers
    C --> D[OpenRouter]
    C --> E[Gemini]
    C --> F[Local / Ollama]
    end
```

---

## ✨ Features

- **💰 Cost Savings**: Use free models (Gemini Flash, OpenRouter free tier) or cheaper alternatives.
- **🏠 Local Privacy**: Run 100% offline with Ollama or LM Studio.
- **🧠 Extended Thinking**: Enable "thinking tokens" for reasoning models (o1, Gemini 2.0).
- **📊 Terminal Dashboard**: Live request monitoring and metrics.
- **🔀 Hybrid Routing**: Route simple tasks to cheap models and complex tasks to smart models.
- **✏️ Custom Prompts**: Inject custom system prompts for different model tiers.

---

## 📚 Documentation

- **[Configuration Guide](docs/getting-started/configuration.md)** - Full list of environment variables.
- **[Examples](docs/guides/examples.md)** - Recipes for different setups (Free, Local, Power User).
- **[Troubleshooting](docs/troubleshooting/common-issues.md)** - Solutions for common problems.
- **[API Reference](docs/api/reference.md)** - For developers.

---

## 🐛 Common Issues

**401 User Not Found (OpenRouter)**
You likely have a negative balance or $0.00 credit. OpenRouter requires a positive balance even for free models.
[Read more](docs/troubleshooting/401-errors.md)

**Connection Refused**
Make sure `python start_proxy.py` is running in a separate terminal window.

**Model Not Found**
Check your `BIG_MODEL`, `MIDDLE_MODEL`, and `SMALL_MODEL` settings in `.env`.

---

## 🔮 Potential Future Additions

1. **Desktop GUI Client (Electron/Tauri)**
   - System tray integration, global hotkeys, and a native chat experience.
   - *Tech*: Tauri (Rust + React) for lightweight performance.

2. **Advanced Analytics Platform**
   - Aggregate usage data from multiple proxy instances for teams.
   - *Tech*: Postgres, Grafana/Metabase, separate FastAPI service.

3. **Multi-Agent Orchestrator ("Swarm Mode")**
   - Extend Crosstalk to support complex, multi-step workflows where specialist models collaborate autonomously.
   - *Tech*: LangGraph or custom orchestration layer.

4. **MCP Server Integration**
   - Expose the proxy as an MCP Server, allowing Claude Desktop to use it as a tool for routing requests to alternative providers.
   - *Tech*: Model Context Protocol SDK.

---

<div align="center">
Made with ❤️ for the Claude Code community
</div>
