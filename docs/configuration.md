# Configuration Guide

Claude Code Proxy supports four equally-capable configuration surfaces. All 62 settings are reachable from every surface.

## The Four Surfaces

| Surface | How | Scope |
|---------|-----|-------|
| **`.env` file** | Edit `.env` in project root | Persists across restarts |
| **CLI flags** | `python start_proxy.py --flag value` | Current run only (use `--save-config` to persist) |
| **TUI** | `python start_proxy.py --configure-advanced` | Writes to `.env` |
| **Web UI** | `http://localhost:8082/settings` | Writes to `.env` via POST `/api/settings` |

### Precedence Order (highest → lowest)

```
CLI flags  >  shell env  >  .env file  >  stored config  >  defaults
```

### Bulk Configuration via JSON

Pass any number of settings via a JSON file:

```bash
python start_proxy.py --config-file ~/my-proxy.json
```

Format: `{ "ENV_VAR": "value", ... }` — uses the same env-var names as `.env`.

Save current settings to a file:

```bash
python start_proxy.py --save-config ~/my-proxy.json
```

---

## All 62 Settings

### Server (5 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `HOST` | `--host` | `0.0.0.0` | Bind address |
| `PORT` | `--port` | `8082` | Listen port |
| `LOG_LEVEL` | `--log-level` | `info` | Verbosity: debug/info/warning/error |
| `REQUEST_TIMEOUT` | `--request-timeout` | `120` | Upstream timeout (seconds) |
| `MAX_RETRIES` | `--max-retries` | `2` | Retries before cascade |

### Models (9 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `BIG_MODEL` | `--big-model` | — | Opus-class model |
| `MIDDLE_MODEL` | `--middle-model` | — | Sonnet-class model |
| `SMALL_MODEL` | `--small-model` | — | Haiku-class model |
| `BIG_CASCADE` | `--big-cascade` | — | Fallback models (comma-separated) |
| `MIDDLE_CASCADE` | `--middle-cascade` | — | Fallback models |
| `SMALL_CASCADE` | `--small-cascade` | — | Fallback models |
| `MODEL_CASCADE` | `--model-cascade` | `true` | Enable cascade fallback |
| `MODEL_CASCADE_DAILY_LIMIT` | `--cascade-daily-limit` | `0` | Max cascade per model/day (0=∞) |
| `OPENROUTER_FALLBACK_MODELS` | `--or-fallbacks` | — | Dynamic OR fallback pool |

### Reasoning (5 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `REASONING_EFFORT` | `--reasoning-effort` | `low` | Default effort: low/medium/high |
| `REASONING_MAX_TOKENS` | `--reasoning-max-tokens` | `32000` | Max thinking tokens |
| `REASONING_EXCLUDE` | `--reasoning-exclude` | `false` | Strip thinking from response |
| `BIG_MODEL_REASONING` | `--big-reasoning` | — | BIG tier reasoning override |
| `MIDDLE_MODEL_REASONING` | `--middle-reasoning` | — | MIDDLE tier reasoning override |

### Router Slots (6 settings)

| Setting | CLI Flag | Description |
|---------|----------|-------------|
| `ROUTER_BACKGROUND` | `--router-background` | Model for background tasks |
| `ROUTER_THINK` | `--router-think` | Model for reasoning requests |
| `ROUTER_LONG_CONTEXT` | `--router-long-context` | Model for long-context |
| `ROUTER_LONG_CONTEXT_THRESHOLD` | `--router-long-context-threshold` | Token threshold (default: 60000) |
| `ROUTER_WEB_SEARCH` | `--router-web-search` | Model for web search tools |
| `ROUTER_IMAGE` | `--router-image` | Model for vision requests |

### Budget & Cost (4 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `DAILY_TOKEN_BUDGET` | `--daily-token-budget` | `0` | Daily token cap (0=off) |
| `PER_REQUEST_TOKEN_BUDGET` | `--per-request-token-budget` | `0` | Per-request input cap (0=off) |
| `DAILY_COST_BUDGET` | `--daily-cost-budget` | `0.0` | Daily USD cap (0=off) |
| `MID_STREAM_OUTPUT_BUDGET` | `--mid-stream-budget` | `0` | Mid-stream tier switch threshold |

### Circuit Breaker (3 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `CB_FAILURE_THRESHOLD` | `--cb-failure-threshold` | `3` | Failures to open circuit |
| `CB_SUCCESS_THRESHOLD` | `--cb-success-threshold` | `1` | Successes to close from half-open |
| `CB_TIMEOUT_SECONDS` | `--cb-timeout` | `300` | Cooldown before half-open probe |

### Compression and Headroom (15 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `HEADROOM_BYPASS_THRESHOLD` | `--headroom-bypass` | `0` | Skip compression below N tokens |
| `HEADROOM_ACCELERATOR` | — | `auto` | `auto`, `intel`, `nvidia`, or `cpu` for Headroom Kompress |
| `HEADROOM_KOMPRESS_DEVICE` | — | auto-detected | OpenVINO device, usually `GPU.0` on Intel Arc |
| `HEADROOM_REMOTE_URL` | — | — | Relay local Headroom port to a remote LAN Headroom instance |
| `HEADROOM_UPSTREAM_URL` | — | `http://127.0.0.1:8082` | Upstream gateway URL used by local Headroom |
| `HEADROOM_ALLOW_CPU_FALLBACK` | — | `1` | Retry CPU/ONNX when GPU preload fails |
| `HEADROOM_PRELOAD_TIMEOUT` | — | `90s` | Timeout for Kompress preload |
| `TOOL_SCHEMA_STRIP` | `--tool-schema-strip` | `true` | Strip redundant tool schema fields |
| `TOOL_DESC_MAX` | `--tool-desc-max` | `200` | Max tool description chars |
| `TOOL_PARAM_DESC_MAX` | `--tool-param-desc-max` | `120` | Max property description chars |
| `SEMANTIC_CACHE_ENABLED` | `--semantic-cache` | `true` | Enable near-duplicate cache |
| `SEMANTIC_CACHE_THRESHOLD` | `--semantic-cache-threshold` | `0.97` | Similarity threshold (0–1) |
| `SEMANTIC_CACHE_SIZE` | `--semantic-cache-size` | `256` | Max LRU cache entries |
| `SEMANTIC_CACHE_TTL` | `--semantic-cache-ttl` | `3600` | Cache TTL (seconds) |
| `TOKEN_COUNT_CACHE_SIZE` | `--token-cache-size` | `512` | tiktoken LRU cache slots |

### Local GPU (3 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `LOCAL_ENABLED` | `--local-enabled` | `false` | Enable 4th cascade tier (ollama) |
| `LOCAL_MODEL` | `--local-model` | — | Local model name |
| `LOCAL_ENDPOINT` | `--local-endpoint` | `http://localhost:11434/v1` | Inference endpoint |

### Tool Calls (5 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `TOOLCALL_MODELS` | `--toolcall-models` | — | Tool-capable models (prepended to cascade) |
| `TOOLCALL_AUTO_ROUTE` | `--toolcall-auto-route` | `true` | Auto-detect tool requests |
| `TOOLCALL_MAX_RETRIES` | `--toolcall-max-retries` | `2` | Retries per model in tool cascade |
| `TOOL_OUTPUT_MAX_CHARS` | `--tool-output-max` | `50000` | Max tool output chars |
| `TOOL_OUTPUT_TRUNCATION` | `--tool-truncation` | `false` | Enable truncation |

### Auth (3 settings)

| Setting | CLI Flag | Description |
|---------|----------|-------------|
| `PROXY_AUTH_KEY` | `--proxy-auth-key` | Client access key (empty = no auth) |
| `OPENROUTER_API_KEY` | `--openrouter-key` | OpenRouter API key |
| `AA_API_KEY` | `--aa-key` | Artificial Analysis key (benchmark scores) |

### Logging (4 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `LOG_FILE` | `--log-file` | `logs/proxy.log` | Log file path |
| `LOG_MAX_SIZE_MB` | `--log-max-mb` | `50` | Max file size before rotation |
| `LOG_RETENTION_DAYS` | `--log-retention` | `7` | Days to keep rotated logs |
| `DEBUG_TRAFFIC_LOG` | `--debug-traffic` | `false` | Dump full HTTP headers |

### Watchdog (3 settings)

| Setting | Default | Description |
|---------|---------|-------------|
| `PROXY_WATCHDOG` | `false` | Auto-recovery watchdog |
| `WATCHDOG_INTERVAL` | `30` | Health check interval (seconds) |
| `WATCHDOG_GRACE` | `5` | Grace period before restart (seconds) |

### Usage Tracking (3 settings)

| Setting | CLI Flag | Default | Description |
|---------|----------|---------|-------------|
| `TRACK_USAGE` | `--track-usage` | `true` | Record stats to SQLite |
| `USAGE_TRACKING_DB_PATH` | `--usage-db` | `usage_tracking.db` | Database path |
| `SILENCE_DEPRECATION_WARNINGS` | — | `false` | Suppress startup deprecation warnings |

---

## TUI Reference

```bash
python start_proxy.py --configure-advanced
```

Menu categories (19 total):

| Key | Category | Settings Covered |
|-----|----------|-----------------|
| 1 | 🤖 Models & Cascade | BIG/MIDDLE/SMALL model, cascade lists |
| 2 | 🧠 Reasoning | Effort, max tokens, per-tier overrides |
| 3 | 💰 Budget & Cost | Token/USD limits, mid-stream budget |
| 4 | 🗺️ Router Slots | Background, think, web_search, image |
| 5 | 🗜️ Compression | Headroom bypass, semantic cache, schema strip |
| 6 | 🖥️ Local GPU | ollama endpoint, local model |
| 7 | 🔄 Cascade & Circuit Breaker | Fallback lists, CB thresholds |
| 8 | 🔧 Tool Calls | Tool-capable models, truncation |
| 9 | 🔑 API Keys | Provider endpoint, auth keys |
| A | 🌐 Network & Server | Host, port, timeout |
| B | 📋 Logging | File path, rotation, debug traffic |
| C | 📈 Analytics & Tracking | Usage DB, tracking toggle |
| D | 🐕 Watchdog | Enable, interval, grace period |
| E | 📝 Custom Prompts | System prompt overrides |
| F | 🔀 Hybrid Mode | Per-tier endpoint routing |
| G | 📊 Token Limits | Max context, min tokens |
| H | 🚩 Feature Flags | Misc toggles |
| I | 💬 Crosstalk | Multi-model chat config |

---

## Web UI Reference

Open `http://localhost:8082/settings` in a browser.

All 62 settings are rendered dynamically from `/api/settings`. Changes are queued locally and committed on **Save**. The UI shows:

- 15 sections including Reliability Score and Circuit Breaker live state
- Toggle switches for boolean settings
- Dropdowns for enumerated settings
- Number inputs with range validation
- Pending change indicators per-section
- Discard button to revert unsaved changes

---

## Assignment Model (Advanced)

For per-tier provider routing, use assignments rather than the simple `BIG_MODEL` env var:

```bash
# Set big tier to Anthropic directly
python start_proxy.py --assign big anthropic/claude-opus-4-20250514

# List current assignments
python start_proxy.py --list-assignments
```

Assignments are stored in `config/proxy_chain.json` and take precedence over `BIG_MODEL` env var.
