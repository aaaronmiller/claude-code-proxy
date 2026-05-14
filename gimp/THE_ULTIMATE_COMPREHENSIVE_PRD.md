# 🌌 THE ULTIMATE COMPREHENSIVE PRD: Claude Code Proxy

## 1. Project Vision
To build a high-fidelity, hardware-aware **Agentic Operating System Layer**. This system serves as a transparent middleware between advanced AI CLI tools (Claude Code, OpenCode, Aider, etc.) and any LLM provider, providing total resilience, maximum token optimization, and autonomous multi-agent orchestration.

---

## Phase 1: Core Connectivity & Protocol Fidelity
*The foundation of the bridge.*

### 1.1 FastAPI Gateway
- **Requirement**: A high-performance async server intercepting `/v1/messages` and `/v1/chat/completions`.
- **Logic**: Must handle both streaming and non-streaming requests with sub-10ms overhead.

### 1.2 Multi-Format Protocol Translation
- **Request Converter**: Meticulously map Anthropic fields (`thinking`, `tools`) to OpenAI-compatible formats.
- **Response Converter**: A 1,600+ line logic block that merges "ghost chunks" from providers and maps tool IDs back to the client's expected state.
- **Null Safety**: Defensive checks for empty content blocks or malformed argument arrays to prevent client crashes.

---

## Phase 2: Resilience & The "Stability Layer"
*Ensuring the AI agent never sees an error.*

### 2.1 Sequential Cascade Fallback
- **Logic**: Primary -> Cascade Tier -> Dynamic Free Tier.
- **Surgical Skip**: Detect specific error strings (e.g., Alibaba `"rate increased too quickly"`) and skip providers immediately instead of retrying.

### 2.2 Circuit Breaker State Machine
- **Hard Failures**: Monitor 429/5xx errors and trip the circuit for a specific model/provider.
- **Soft Failures**: Detect hallucinated JSON or truncated responses and penalize model health.
- **Persistence**: Save breaker state to `circuit_breaker_state.json` to survive proxy restarts.

### 2.3 Request Deduplicator
- **Logic**: Prevent "Ghost Output" by hashing client metadata (Session Fingerprint).
- **Implementation**: Cache responses for 5 seconds; return cache on client retries.

---

## Phase 3: The Optimization Stack (Compression)
*Reducing costs by 90-99%.*

### 3.1 RTK (Rust Token Killer)
- **Requirement**: Rule-engine using 50+ tool-specific `.toml` filters.
- **Logic**: Strip redundant headers and info from terminal outputs (Docker, Terraform, `ps`) *before* conversion to tokens.

### 3.2 Headroom (Context Squeezing)
- **Requirement**: HTTP middleware with client-side "Hooks."
- **Logic**: Programmatic prompt shrinking tailored for specific agents (Agno, OpenClaw).

### 3.3 Hardware-Aware VRAM Management
- **GPU Resident Manager**: Detect hardware (NVIDIA, Intel XPU, AMD) and keep local models warm in VRAM/XPU-RAM.

---

## Phase 4: Advanced Routing & Intelligence
*The "Synthetic Cortex" of the proxy.*

### 4.1 Intent-Based Model Routing
- **Slots**: `default`, `background` (free models), `think` (reasoning models), `long_context`, `web_search`, `image`.
- **Logic**: Dynamically swap `model_id` based on request intent (e.g., small tasks -> free models).

### 4.2 Dynamic Model Ranker
- **Implementation**: `model_ranker.py`.
- **Logic**: Uses LLM scoring + Exa Neural Search to live-benchmark coding models and update `model_rankings.json`.

### 4.3 JSON to TOON Density Analysis
- **Logic**: Predict 20-40% savings by analyzing JSON frequency and recommending the more compact `TOON` format.

---

## Phase 5: Agentic Orchestration (Crosstalk)
*Multi-model collaboration lab.*

### 5.1 EoT (Exchange-of-Thought) Paradigms
- **Modes**: `Memory` (independent analysis), `Report` (structured findings), `Relay` (sequential CoT), and `Debate` (adversarial reasoning).

### 5.2 Circular TUI & Visualization
- **Logic**: Circular ASCII-art representation of up to 8 models interacting in real-time.

### 5.3 MCP Tool Integration
- **Feature**: Expose Crosstalk as a set of "Tools" via the Model Context Protocol, allowing other agents to spawn autonomous debates.

---

## Phase 6: Observability & Multi-User Management
*Self-awareness for the agent and the developer.*

### 6.1 Prompt-Injected Dashboards
- **Logic**: Injects proxy health/cost metrics directly into the AI's system prompt (Expanded/Single/Mini formats).

### 6.2 Svelte 5 Glassmorphism Web UI
- **Features**: Real-time request waterfall, profile visual editor, analytics charts, and WebSocket log streaming.

### 6.3 Multi-User Quotas & Auth
- **Infrastructure**: SQLite-backed `users` table with per-key token/request limits.

### 6.4 CLI Tool Session Collector
- **Logic**: Identify and tag traffic from specific tools (Claude, OpenCode, Aider) for granular attribution.

---

## Phase 7: Operational Excellence
*Making the system self-healing and portable.*

### 7.1 Unified Single-Command Installer
- **Implementation**: `install-all.sh`.
- **Logic**: Auto-detect GPU backends, validate Linux toolchains (GCC-12), and configure shell aliases idempotently.

### 7.2 Process Isolation & Survivability
- **Requirement**: Use `setsid` and `tmux` orchestration to ensure the proxy stack survives even if the launching terminal closes.

### 7.3 Defensive Database Migrations
- **Logic**: Lifespan manager in `main.py` must verify SQLite schemas on every boot and add missing columns/tables automatically.

### 7.4 Automated Self-Updates
- **Logic**: Integrated `proxies self-update` command that pulls from git, runs tests with `pytest-cov`, and restarts the chain.
