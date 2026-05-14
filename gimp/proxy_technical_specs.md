# Claude Code Proxy - Technical Specifications (A+ Verified)

## 1. Multi-Agent Orchestration (Crosstalk)
- **Class: `CrosstalkOrchestrator`**: Manages model-to-model conversation sessions.
  - **Source**: `src/conversation/crosstalk.py` (~Line 60)
  - **Paradigm Logic**: Implements `MEMORY`, `REPORT`, `RELAY`, and `DEBATE` enums and their associated prompt-flow logic.
- **Method: `setup_crosstalk()`**: Validates model tiers (Big, Middle, Small) and initializes session state.
  - **Source**: `src/conversation/crosstalk.py` (~Line 85)
- **State Storage**: Session history and memory are stored in `configs/crosstalk/sessions/`.

## 2. Advanced Compression Logic
- **RTK Filters**: Rust-based TOML filters used to strip redundant CLI data.
  - **Location**: `/home/cheta/code/claude-code-proxy/compression/rtk/src/filters/`
  - **Examples**: `docker.toml`, `terraform-plan.toml`, `shellcheck.toml`.
- **Headroom Hooks**: Python-based interceptors for specific client adapters.
  - **Source**: `compression/headroom/headroom/hooks.py`
  - **Integrations**: Agno (`headroom/integrations/agno/hooks.py`) and Strands.

## 3. Resilience: Circuit Breaker & Persistence
- **Method: `record_parse_ok()`**: Inspects responses for structural integrity (missing tool_calls or empty content).
  - **Source**: `src/core/circuit_breaker.py` (~Line 120)
- **Persistence**: `_load_persisted_state()` ensures model health data survives restarts.
  - **Source**: `src/core/circuit_breaker.py` (~Line 215)

## 4. Resilience: Intelligent Cascading
- **Method: `_build_or_models_list()`**: Dynamically filters out "OPEN" (failed) models from the OpenRouter fallback array before sending the request.
  - **Source**: `src/core/client.py` (~Line 380)
- **Logic: Alibaba Ramp-Up Check**: Immediate skip on "rate increased too quickly" message.
  - **Source**: `src/core/client.py` (~Line 512)

## 5. UI & TUI Entry Points
- **Crosstalk Studio**: Terminal interface for orchestrating agent debates.
  - **Source**: `src/cli/crosstalk_studio.py`
- **Proxy TUI**: Bash-based TUI for chain management.
  - **Source**: `/home/cheta/code/claude-code-proxy/proxies` (functions `cmd_config` and `cmd_router`)
- **Web UI**: Svelte 5 components for metrics display.
  - **Location**: `web-ui/src/routes/realtime/`
