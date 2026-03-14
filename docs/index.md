# ⚡ The Ultimate Proxy - Documentation

> **Complete reference for The Ultimate Proxy**

---

## 🚀 Quick Start (New Users)

**Fastest way to get started:**

```bash
# Clone the repository
git clone https://github.com/holegots/claude-code-proxy.git
cd claude-code-proxy

# Run automated setup (handles everything!)
python quickstart.py
```

This single command will:
- ✅ Check Python version (3.9+ required)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Configure environment variables
- ✅ Initialize the database
- ✅ Launch the proxy

📖 **See [QUICKSTART.md](../QUICKSTART.md) for the complete guide**

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Setup Guide](setup.md) | Installation, configuration, and first run |
| [Crosstalk](crosstalk.md) | Multi-model conversation orchestration |

### Guides

| Topic | Description |
|-------|-------------|
| [Configuration](guides/configuration.md) | All environment variables and options |
| [Model Selection](guides/model-selection.md) | Choosing and configuring models |
| [Free Cascade](guides/free-cascade.md) | Ranked free models, fallback chains, and history |
| [Reasoning](guides/reasoning.md) | Extended thinking and reasoning tokens |
| [Prompt Injection](guides/prompt-injection.md) | Custom system prompts |

### API Reference

| Endpoint | Description |
|----------|-------------|
| [API Overview](api/api-reference.md) | REST API endpoints |

### Troubleshooting

| Issue | Solution |
|-------|----------|
| [Common Issues](troubleshooting/common-issues.md) | Fixes for frequent problems |
| [Error Codes](troubleshooting/error-codes.md) | API error reference |

---

## 🚀 Quick Start

```bash
# Clone & install
git clone https://github.com/aaaronmiller/the-ultimate-proxy.git
cd the-ultimate-proxy
uv sync

# Interactive setup wizard
python start_proxy.py --setup

# Start the proxy
python start_proxy.py
```

Then in another terminal:
```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude
```

---

## 🛠️ CLI Commands

### Configuration
```bash
python start_proxy.py --setup           # First-time wizard
python start_proxy.py --settings        # Unified settings TUI
python start_proxy.py --doctor          # Health check + auto-fix
```

### Model Management
```bash
python start_proxy.py --select-models   # Interactive model selector
python start_proxy.py --set-big MODEL   # Quick set BIG model
python start_proxy.py --show-models     # List available models
```

### Crosstalk
```bash
python start_proxy.py --crosstalk-studio  # Visual TUI
python start_proxy.py --crosstalk-init    # Setup wizard
```

### Diagnostics
```bash
python start_proxy.py --config          # Show configuration
python start_proxy.py --dry-run         # Validate without starting
python start_proxy.py --analytics       # View usage stats
```

---

## 🌐 Web Dashboard

Access at `http://localhost:8082` when running.

Features:
- Real-time request monitoring
- Model configuration
- Crosstalk session management
- Theme selector (Aurora 2025 / Cyberpunk)
- Live log streaming
- Analytics dashboard

---

## 📁 Project Structure

```
the-ultimate-proxy/
├── start_proxy.py          # Main entry point
├── .env                    # Configuration
├── docs/                   # Documentation (you are here)
│   ├── index.md           # This file
│   ├── setup.md           # Setup guide
│   ├── crosstalk.md       # Multi-model conversations
│   ├── guides/            # Topic guides
│   ├── api/               # API reference
│   └── troubleshooting/   # Problem solving
├── src/                   # Source code
│   ├── api/               # FastAPI routes
│   ├── cli/               # CLI tools
│   ├── core/              # Proxy logic
│   └── services/          # Providers, models
├── configs/               # Runtime configuration
│   └── crosstalk/         # Crosstalk presets/templates
├── web-ui/                # Svelte dashboard
└── tests/                 # Test suite
```

---

## 🔗 Links

- [GitHub Repository](https://github.com/aaaronmiller/the-ultimate-proxy)
- [Report an Issue](https://github.com/aaaronmiller/the-ultimate-proxy/issues)
