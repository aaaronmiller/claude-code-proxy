# Claude Code Proxy - Project Intent Map (A+ Verified)

This map defines the **Useful Intent** and **Information Flow** of the project, reasoned from a file-by-file audit.

## 1. The Resilience Loop (Heart)
- **Primary Goal**: Ensure the AI agent (Claude Code) never sees a "dead" endpoint.
- **Flow**: `endpoints.py` (Entry) → `client.py` (Cascader) ↔ `circuit_breaker.py` (Health State).
- **Key Intent**: The `CircuitBreaker` persists "dead" models to JSON so that the `client.py` can surgically skip them in the next session. It even detects "soft failures" (broken JSON) to prevent the agent from getting confused by hallucinated formatting.

## 2. The Context-Optimization Chain (The Filters)
- **Primary Goal**: Shrink the prompt to save money and stay under context limits.
- **Flow**: `proxy_chain.py` (Topology) → `Headroom` (HTTP Filter) → `RTK` (CLI Output Filter).
- **Key Intent**: `RTK` is a "Rule Engine" (`.toml` based) that understands specific developer tools (Docker, Terraform). It strips the "noise" out of terminal output *before* it becomes expensive input tokens.

## 3. The Self-Awareness System (The Metrics)
- **Primary Goal**: Let the AI agent see its own performance.
- **Flow**: `usage_tracker.py` (Collection) → `prompt_injector.py` (Formatting) → `endpoints.py` (Injection).
- **Key Intent**: By injecting a "Dashboard" into the system prompt, the AI understands its own "Token Speed" and "Remaining Budget." This turns the AI into a partner in cost-optimization.

## 4. The Orchestration Lab (Crosstalk)
- **Primary Goal**: Multi-agent collaboration research.
- **Flow**: `crosstalk_studio.py` (TUI) → `crosstalk.py` (Orchestrator) ↔ `crosstalk/sessions/` (Persistence).
- **Key Intent**: Uses 4 paradigms (Debate, Memory, Relay, Report) to simulate model-to-model dialogue. It’s designed to explore "Infinite Backrooms" scenarios where AIs build upon each other's reasoning.

## 5. The Operational Pulse (Lifecycle)
- **Primary Goal**: Self-healing and persistent monitoring.
- **Flow**: `main.py` (Lifespan) → `alert_engine.py` + `scheduler.py` + `migrations`.
- **Key Intent**: Every startup performs a health check and DB migration to ensure the environment is pristine. The `Alert Engine` monitors for cost spikes or latency drops in the background.
