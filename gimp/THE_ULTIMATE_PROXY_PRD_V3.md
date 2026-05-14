# ⚡ EXHAUSTIVE Product Requirements Document: Claude Code Proxy (v3.0.0)

## 1. Project Mission
To provide a high-fidelity **Stability and Optimization Layer** between agentic CLI tools (Claude Code) and LLM providers. The system must ensure that the AI agent never sees an error, operates at 90%+ token efficiency, and gains self-awareness of its own performance.

---

## 2. Core Architecture: The "Resilience Loop"
The system functions as a state-aware retry loop.

### R1: Sequential Cascade with Preemptive Skipping
- **Logic**: Primary -> Cascade Tier -> Dynamic Rankings.
- **Circuit Breaker**: Skip models if circuit is `OPEN` (JSON state persisted to disk).
- **Surgical Skip**: Immediate skip on Alibaba error string: `"rate increased too quickly"`.
- **Source**: `src/core/client.py`

### R2: Request Consistency (Deduplication)
- **Logic**: Extract **Session Fingerprint** from client metadata.
- **Implementation**: 5-second cache for successful responses; returns cache for duplicate hashes to prevent ghost terminal output.
- **Source**: `src/api/endpoints.py`

---

## 3. The Compression Stack

### F1: RTK (Rust Token Killer)
- **Requirement**: Rule-engine using 50+ tool-specific `.toml` filters (Docker, Terraform, etc.).
- **Implementation**: Strips headers/columns *before* LLM conversion.
- **Source**: `compression/rtk/src/filters/`

### F2: Headroom (Context Squeezing)
- **Logic**: Client-specific "Hooks" (Agno, OpenClaw) for programmatic prompt shrinking.
- **Source**: `compression/headroom/headroom/hooks.py`

---

## 4. Technical Appendix: Data & Contracts

### A1: SQLite Database Schema (`usage_tracking.db`)
To support **Defensive Migrations**, you MUST implement these tables:
1. `api_requests`: Tracks `request_id`, `timestamp`, `original_model`, `routed_model`, `provider`, `input_tokens`, `output_tokens`, `duration_ms`, `status`.
2. `model_usage_summary`: (Primary: `model`) Tracks totals for tokens, cost, and latency.
3. `daily_model_stats`: Aggregates usage per day for the 7-day history API.
4. `savings_tracking`: Compares `original_cost` vs `actual_cost` to calculate "RTK Gain."

### A2: API Route Registry
| Method | Path | Function |
| :--- | :--- | :--- |
| `GET` | `/api/system/health` | Uptime, CPU, Mem, DB Size. |
| `GET` | `/api/system/stats` | Requests today, Total cost, Error rate. |
| `GET` | `/api/system/request-feed` | Real-time list of the last 20 requests. |
| `GET` | `/api/docs/` | Serves the project's markdown documentation. |
| `WS` | `/api/ws/logs` | Real-time WebSocket log streaming to dashboard. |

### A3: Configuration Schema (`proxy_chain.json`)
```json
{
  "entries": [
    {
      "id": "headroom",
      "name": "Headroom",
      "type": "http",
      "url": "http://127.0.0.1:8787",
      "service_cmd": "headroom proxy --port 8787",
      "enabled": true
    }
  ],
  "router": {
    "background": "nvidia/nemotron-nano-9b-v2:free",
    "think": "anthropic/claude-3-opus",
    "long_context_threshold": 60000
  }
}
```

---

## 5. Lifecycle & Management
- **Startup**: Services MUST start in **Reverse Order** (`_chain_services_reversed`).
- **Management**: `proxies` bash script handles `up`, `down`, `status`, and `logs`.
- **UI**: Glassmorphism Svelte 5 dashboard for analytics.
