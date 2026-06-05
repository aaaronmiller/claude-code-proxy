# Clutch Gateway Documentation

Local AI gateway for coding agents: routing, compression, fallback, and telemetry.

---

## Quick Start

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
cp .env.example .env
./proxies up
```

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
export ANTHROPIC_API_KEY=pass
claude
```

## Primary Guides

| Guide | Description |
|-------|-------------|
| [Setup](setup.md) | Install, start, and choose local/remote Headroom |
| [Headroom Acceleration](headroom-acceleration.md) | GPU, CPU, and LAN compression setup |
| [Configuration](configuration.md) | Settings surfaces and env reference |
| [Model Scan Integration](MODEL_SCAN_INTEGRATION.md) | measured routing snapshot binding |
| [Status Bars](STATUS_BARS.md) | tmux, RTK, and Codex status segments |
| [Crosstalk](crosstalk.md) | Multi-model conversation orchestration |

## API and Operations

| Guide | Description |
|-------|-------------|
| [API Reference](api/api-reference.md) | REST endpoints |
| [Production](guides/production.md) | deployment notes |
| [Free Cascade](guides/free-cascade.md) | free model fallback chains |
| [Common Issues](troubleshooting/common-issues.md) | frequent runtime failures |
| [401 Errors](troubleshooting/401-errors.md) | credential and upstream auth failures |

## Commands

```bash
./proxies up
./proxies down
./proxies restart headroom
./proxies status
./proxies router show
```

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
