# Clutch Gateway — Master Feature Specification & Recreation Guide

This document lists all currently implemented features of the Clutch Gateway (formerly `claude-code-proxy`) with pointers to the exact implementation files. It serves as a comprehensive reference to recreate the project from scratch.

---

## 1. Gateway Core & Protocol Translator
The gateway accepts Anthropic Messages and OpenAI Chat Completions requests, translates payload structures on-the-fly (including tool definitions, message roles, and system messages), and routes them to upstream providers.
- **API Entrypoint and FastAPI Setup**: [main.py](file:///home/cheta/code/claude-code-proxy/src/main.py)
- **Protocol Endpoints and Request Processing**: [endpoints.py](file:///home/cheta/code/claude-code-proxy/src/api/endpoints.py) and [openai_endpoints.py](file:///home/cheta/code/claude-code-proxy/src/api/openai_endpoints.py)
- **Anthropic-to-OpenAI Translation Logic**: [request_converter.py](file:///home/cheta/code/claude-code-proxy/src/services/conversion/request_converter.py) and [response_converter.py](file:///home/cheta/code/claude-code-proxy/src/services/conversion/response_converter.py)

## 2. Dynamic Model Router & Assignment Engine
The router maps incoming requests to static tiers (`big`, `middle`, `small`, `xbig`) or functional slots (`background`, `think`, `long_context`, `image`, `web_search`) using configured assignments and model identifier mappings.
- **Router Logic**: [model_router.py](file:///home/cheta/code/claude-code-proxy/src/core/model_router.py)
- **Assignment Definitions**: [assignments.py](file:///home/cheta/code/claude-code-proxy/src/core/assignments.py)
- **Unified Config Resolver**: [config_resolver.py](file:///home/cheta/code/claude-code-proxy/src/core/config_resolver.py) and [config_manifest.py](file:///home/cheta/code/claude-code-proxy/src/core/config_manifest.py)
- **Model Family Regex Detection**: [model_family.py](file:///home/cheta/code/claude-code-proxy/src/services/models/model_family.py)

## 3. Quota-Aware Cascade & Rotation Engine
When a request fails, the proxy runs a 4-layer fallback cascade (e.g. primary model -> toolcall fallback -> tier cascade -> dynamic rankings), rotating API keys and falling back to free models.
- **Cascade Completion Loop**: [client.py](file:///home/cheta/code/claude-code-proxy/src/core/client.py#L647-L800)
- **Fallback, Key Rotation, and Standby Lane Logic**: [rotation.py](file:///home/cheta/code/claude-code-proxy/src/core/rotation.py)
- **Quota Adapters and Metering**: [quota_adapters.py](file:///home/cheta/code/claude-code-proxy/src/core/quota_adapters.py) and [quota_live.py](file:///home/cheta/code/claude-code-proxy/src/core/quota_live.py)

## 4. Circuit Breaker System
Tracks failures (timeouts, 5xx, 429s) per model/provider and temporarily isolates ("opens") them from cascade selection during a cooldown window.
- **State and Tripping Logic**: [circuit_breaker.py](file:///home/cheta/code/claude-code-proxy/src/core/circuit_breaker.py)
- **Breaker REST Endpoints**: [config_api.py](file:///home/cheta/code/claude-code-proxy/src/api/config_api.py#L141-L150)

## 5. Usage & Cost Tracking Database
Tracks token consumption (input, output, cached, thinking) and estimated cost in real-time. Logs requests to a local SQLite database for analytics.
- **Database Schema and Logging**: [usage_tracker.py](file:///home/cheta/code/claude-code-proxy/src/services/usage/usage_tracker.py)
- **SQLite Migrations & DB Path**: `usage_tracking.db`

## 6. SvelteKit Web UI
Provides a modern, dark-mode configuration editor for all 64 manifest settings, real-time log viewer, and analytics cards.
- **Frontend Source**: Located under [web-ui/](file:///home/cheta/code/claude-code-proxy/web-ui/)
- **API Settings Sync**: [web_ui.py](file:///home/cheta/code/claude-code-proxy/src/api/web_ui.py) and [config_api.py](file:///home/cheta/code/claude-code-proxy/src/api/config_api.py)

## 7. Python-Textual TUI
Interactive terminal interface to review settings, monitor provider health, and modify router configurations via forms.
- **TUI Settings Entrypoint**: [settings_tui.py](file:///home/cheta/code/claude-code-proxy/src/cli/settings_tui.py)
- **Statusline TUI**: [statusline_tui.py](file:///home/cheta/code/claude-code-proxy/src/cli/statusline_tui.py)

## 8. Context Compression (RTK & Headroom)
Context compression stack to shrink input tokens before dispatching to upstream providers.
- **RTK (Rust Token Killer) Wrapper CLI**: Compresses terminal output. Source: `compression/rtk/`
- **Headroom Patcher**: Enforces environment overrides on headroom checkpoints. [patch-headroom-kompress.py](file:///home/cheta/code/claude-code-proxy/compression/scripts/patch-headroom-kompress.py)
- **Relay Mechanism**: Relays traffic to LAN Headroom hosts. [headroom-relay.py](file:///home/cheta/code/claude-code-proxy/scripts/headroom-relay.py)
- **GPU Device Detector**: Auto-detects NVIDIA/Intel GPUs and handles CPU fallbacks. [headroom-start.sh](file:///home/cheta/code/claude-code-proxy/scripts/headroom-start.sh)

## 9. Prometheus Metrics & Observability
Exposes gauges and counters for Prometheus scraping to construct real-time Grafana dashboards.
- **Exposed Metrics**: [metrics_api.py](file:///home/cheta/code/claude-code-proxy/src/api/metrics_api.py) and [system_monitor.py](file:///home/cheta/code/claude-code-proxy/src/api/system_monitor.py)
- **JSONL Event Log**: [event_logger.py](file:///home/cheta/code/claude-code-proxy/src/services/logging/event_logger.py)

## 10. `xx` CLI Launcher
A case-encoded command-line launcher replacing multiple shell aliases (e.g. `xx cip` runs Claude Code in interactive mode through the proxy).
- **Launcher Script**: [xx](file:///home/cheta/code/claude-code-proxy/scripts/xx)
- **Alias Patcher**: [install-aliases.sh](file:///home/cheta/code/claude-code-proxy/scripts/install-aliases.sh)

## 11. Crosstalk V1 Orchestrator
A multi-agent model-to-model conversation system implementing Exchange-of-Thought (EoT) research.
- **Communication Paradigms (Memory, Debate, Relay, Report)**: [crosstalk.py](file:///home/cheta/code/claude-code-proxy/src/conversation/crosstalk.py)

## 12. OpenRouter Fusion
Parallel panel routing that queries multiple models simultaneously, compares outputs via a judge model, and returns the response.
- **Fusion Routing**: [fusion.py](file:///home/cheta/code/claude-code-proxy/src/core/fusion.py)

## 13. F18 Quota-Aware Allocator (Satisfice-then-Maximize)
Global allocator that re-ranks routing profiles under finite Groq/Cerebras/OpenRouter quota constraints.
- **Allocator Logic**: [allocator.py](file:///home/cheta/code/claude-code-proxy/src/services/allocator.py)
- **Quota Ledger Integration**: [quota_runtime.py](file:///home/cheta/code/claude-code-proxy/src/core/quota_runtime.py)

## 14. Model-Scan Integration
Consumes the dynamically generated `routing_snapshot.json` schema to update defaults and overlays based on model capabilities.
- **Snapshot Parser**: [model_scan_snapshot.py](file:///home/cheta/code/claude-code-proxy/src/services/models/model_scan_snapshot.py)
- **Model Selection & Binding**: [model_scan_binder.py](file:///home/cheta/code/claude-code-proxy/src/core/model_scan_binder.py) and [model_scan_runtime.py](file:///home/cheta/code/claude-code-proxy/src/core/model_scan_runtime.py)

## 15. Fractal Council / Synthetic Cortex Isolation
Headless spawning helper for recursive agent swarms.
- **Headless Spawning CLI**: [spawn_mission.sh](file:///home/cheta/code/claude-code-proxy/tools/spawn_mission.sh)
- **Autonomic Governors**: `post_error_logger.sh` and `budget_governor.js` under `.claude/hooks/`
- **Agent Roles**: strategists, analysts, and scouts under `.claude/agents/`
