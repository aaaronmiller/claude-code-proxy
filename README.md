# Clutch Gateway

Local AI gateway for coding agents that need cheaper context, better model routing, and reliable fallback.

Working name: **Clutch Gateway**. The old repo name says "proxy", but the product is now a local agent gateway: it accepts Claude/OpenAI-compatible traffic, compresses context through Headroom, routes work by role, and falls back across providers when models fail.

## What It Does

```
Claude Code / Codex / Qwen / OpenCode
        |
        v
RTK terminal compression
        |
        v
Headroom context compression (:8787)
        |
        v
Clutch Gateway router (:8082)
        |
        +-- model tiers: big / middle / small
        +-- role slots: background / think / long_context / web_search / image
        +-- cascade fallback + circuit breakers
        +-- usage, reliability, and model-scan telemetry
        |
        v
OpenRouter / OpenAI / Gemini / Anthropic / Ollama / local gateways
```

## Why It Exists

Coding agents burn tokens differently from chat apps. They replay files, tool logs, terminal output, and long histories. A generic LLM gateway helps with provider access, but it does not optimize the agent loop.

Clutch is built for that loop:

- **Context compression first**: Headroom compresses prompt payloads before provider billing.
- **Terminal compression before context**: RTK keeps shell output from poisoning future turns.
- **Role-aware routing**: background, long-context, web-search, image, and reasoning work can use different models.
- **Failure-aware cascades**: circuit breakers and fallbacks keep sessions moving when free or hosted endpoints fail.
- **Local-first operation**: run on a laptop, a workstation with the best GPU, or a LAN gateway shared by multiple machines.

## Quick Start

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
cp .env.example .env
./proxies up
```

Use the compression entrypoint:

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
export ANTHROPIC_API_KEY=pass
claude
```

Use the router directly when you want routing without Headroom:

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8082
export ANTHROPIC_API_KEY=pass
claude
```

## Headroom Acceleration

The Headroom launcher detects acceleration automatically:

| Mode | Detection | Behavior |
|------|-----------|----------|
| Intel Arc / Intel iGPU | `clinfo`, `lspci`, or WSL `/dev/dxg` | OpenVINO Kompress on `GPU.0` by default |
| NVIDIA | `nvidia-smi` | CUDA/PyTorch path, OpenVINO disabled |
| No GPU | none | CPU/ONNX fallback |
| Remote GPU host | `HEADROOM_REMOTE_URL` | local relay to LAN Headroom |

Current verified local setup:

- Headroom `0.20.27`
- Kompress model `chopratejas/kompress-base`
- OpenVINO backend on Intel `GPU.0`
- OpenVINO IR size: about `286M`
- Headroom process RSS after preload: about `603 MiB`

Details: [docs/headroom-acceleration.md](docs/headroom-acceleration.md)

## LAN GPU Sharing

Run Headroom once on the best GPU machine, then point other machines at it:

```bash
HEADROOM_REMOTE_URL=http://gpu-box.local:8787 ./proxies restart headroom
```

The local machine keeps a local `:8787` endpoint, but requests relay to the remote Headroom instance. The remote Headroom server must be configured so its upstream gateway is reachable from that GPU host.

## Core Commands

```bash
./proxies up                         # start gateway + Headroom in tmux
./proxies down                       # stop managed services
./proxies restart headroom           # restart compression layer
./proxies status                     # health for chain entries
./proxies config show                # inspect chain config
./proxies router show                # inspect role routing
./proxies metrics summary            # usage summary
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | environment overrides and credentials |
| `config/proxy_chain.json` | service chain, assignments, cascades, model-scan settings |
| `profiles/profiles.json` | per-tool routing profiles |
| `logs/proxy.log` | gateway request log |
| `~/.headroom/logs/proxy.jsonl` | Headroom savings log |

Never commit real provider keys. `ANTHROPIC_API_KEY=pass` and `x-api-key: pass` are local client compatibility values, not real credentials.

## Documentation

| Guide | Use |
|-------|-----|
| [Setup](docs/setup.md) | install, local mode, remote Headroom mode |
| [Headroom Acceleration](docs/headroom-acceleration.md) | GPU/CPU/remote compression setup |
| [Configuration](docs/configuration.md) | env vars and settings surfaces |
| [Model Scan Integration](docs/MODEL_SCAN_INTEGRATION.md) | measured routing snapshot binding |
| [Status Bars](docs/STATUS_BARS.md) | tmux/RTK/Codex status surfaces |
| [Troubleshooting 401s](docs/troubleshooting/401-errors.md) | auth and provider failures |

## Category Positioning

This project competes less with "proxies" and more with **agent gateways**:

- LiteLLM-style unified provider access
- Portkey/Bifrost-style routing and resilience
- Helicone-style usage visibility
- Headroom/RTK-style context reduction for coding agents

The differentiator is the combination: local gateway + context compression + coding-agent routing profiles.

## Repository Layout

| Path | Purpose |
|------|---------|
| `src/` | gateway API, routing, conversion, logging |
| `scripts/` | launchers, status tools, Headroom relay |
| `config/` | chain and assignment configuration |
| `profiles/` | per-agent profile config |
| `docs/` | operator docs |
| `tests/` | unit and integration tests |
| `compression/` | vendored compression projects and references |
| `archive/` | historical cleanup snapshot |

## Current Caveats

- The repo is still named `claude-code-proxy`; docs now use the product direction `Clutch Gateway`.
- Remote Headroom works as a relay, but the remote GPU host must have network reachability to its configured upstream gateway.
- Exact Intel VRAM counters are not exposed in this WSL environment; verify with native i915 tooling on bare metal Linux.
