# ⚡ Product Requirements Document: Claude Code Proxy (v2.1.0)

## 1. Project Mission
To provide a high-fidelity **Stability and Optimization Layer** between agentic CLI tools (Claude Code) and LLM providers. The system must ensure that the AI agent never sees an error, operates at 90%+ token efficiency, and gains self-awareness of its own performance.

---

## 2. Core Architecture: The "Resilience Loop"
The heart of the project is the **Cascade Fallback** system. It must be built as a state-aware retry loop.

### R1: Sequential Cascade with Preemptive Skipping
*   **Logic**: Instead of a blind retry, the system must build a list of models: `Primary -> Cascade Tier -> Dynamic Rankings`.
*   **Circuit Breaker Integration**: Before attempting a model, the system MUST check the `CircuitBreaker` state. If the circuit is `OPEN` (due to recent failures), the model is skipped without an API call.
*   **Soft Failure Detection**: The system must track "Soft Failures"—responses that are HTTP 200 but contain malformed JSON or empty content. These penalize a model’s health just like a 500 error.
*   **Alibaba Edge Case**: If the error string contains `"rate increased too quickly"`, the system MUST perform a "Surgical Skip"—moving to a different provider immediately because the current provider’s window will not reset on a retry.
*   **Source Reference**: `src/core/client.py` (`create_chat_completion_with_cascade`)

### R2: Request Consistency (Deduplication)
*   **Logic**: To prevent "Ghost Output" (duplicate text in the terminal during retries), the proxy must implement a `RequestDeduplicator`.
*   **Implementation**: Extract a **Session Fingerprint** from the Claude Code metadata (billing markers or system blocks). Cache successful responses for 5 seconds. If a duplicate hash arrives, return the cache.
*   **Source Reference**: `src/api/endpoints.py` (`RequestDeduplicator`)

---

## 3. The Compression Stack: "Rule-Based Efficiency"
The proxy is useless without its multi-stage compression logic.

### F1: RTK (Rust Token Killer)
*   **Requirement**: Must implement a rule-engine that uses `.toml` filter manifests.
*   **Logic**: Each tool (Docker, `ps`, `terraform`) has a specific filter that strips headers and redundant columns.
*   **Scale**: Rebuilding requires porting the 50+ tool filters found in `compression/rtk/src/filters/`.

### F2: Headroom (Context Squeezing)
*   **Requirement**: Programmatic prompt shrinking via client-specific "Hooks."
*   **Logic**: Adapts the context window based on the calling agent (e.g., stripping specific system-prompt noise for OpenClaw or Agno).
*   **Source Reference**: `compression/headroom/headroom/hooks.py`

---

## 4. Intelligence & Self-Awareness

### F3: Intent-Based Routing
*   **Slots**: `default`, `background`, `think`, `long_context`, `web_search`, `image`.
*   **Logic**: Dynamically swap the `model_id` based on the request content. If `max_tokens <= 256`, route to `background` (free tier). If intent is planning, route to `think` (reasoning tier).
*   **Source Reference**: `src/core/model_router.py`

### F4: Agent Awareness (Prompt Injection)
*   **Logic**: The proxy must be "Visible" to the AI. It injects a status dashboard (Tokens/s, Cost, Health) into the system prompt.
*   **Implementation**: Supports `EXPANDED` (ASCII box), `SINGLE` (one line), and `MINI` (compact string) formats.
*   **Source Reference**: `src/services/prompts/prompt_injector.py`

### F5: Crosstalk (Agentic Lab)
*   **Logic**: A standalone multi-agent orchestration lab. Implements 4 paradigms: `Debate`, `Memory`, `Relay`, and `Report`.
*   **Visualization**: Circular ASCII representation of up to 8 models in a "Backrooms" style simulation.
*   **Source Reference**: `src/conversation/crosstalk.py`

---

## 5. Lifecycle & Management

### R3: Reverse-Dependency Orchestration
*   **Logic**: Services MUST start in reverse order of the chain (`Provider -> Headroom -> RTK -> Proxy`). This ensures that when the Proxy starts, its upstream dependencies already pass health checks.
*   **Source Reference**: `proxies` bash script (`_chain_services_reversed`)

### R4: Defensive Migrations
*   **Logic**: On every startup, the system must check the SQLite schema (`usage_tracking.db`) and add missing columns (`muted_until`, `actions_json`) to ensure the DB survives version upgrades.
*   **Source Reference**: `src/main.py` (`lifespan` manager)

### Management Tools:
*   **ChainTUI**: Textual-based UI for hot-reloading the proxy stack and routing slots.
*   **Web UI**: Glassmorphism dashboard for real-time monitoring and log streaming.
