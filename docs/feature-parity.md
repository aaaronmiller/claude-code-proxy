# Configuration Feature Parity

Auto-generated from `src/core/config_manifest.py` — 63 settings.

Every setting on every surface. All four surfaces (CLI flag, TUI menu, Web UI, .env)
are listed per setting. ✅ = supported, — = N/A on that surface.

## Coverage Summary

| Surface | Coverage |
|---|---|
| .env file | 63/63 (100%) — every setting has an env var by definition |
| CLI flags | 63/63 (100%) |
| TUI widgets | 63/63 (100%) |
| Web components | 63/63 (100%) |

## Authentication & API Keys

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `PROXY_AUTH_KEY` | ✅ | `--proxy-auth-key` | `input` | `input` | Client access key (clients must present this to use the proxy; empty=no auth) |
| `OPENROUTER_API_KEY` | ✅ | `--openrouter-key` | `input` | `input` | OpenRouter API key |
| `AA_API_KEY` | ✅ | `--aa-key` | `input` | `input` | Artificial Analysis API key (for intelligence benchmark scores) |

## Budget & Cost Controls

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `DAILY_TOKEN_BUDGET` | ✅ | `--daily-token-budget` | `number` | `number` | Max tokens per UTC day across all requests (0=disabled) |
| `PER_REQUEST_TOKEN_BUDGET` | ✅ | `--per-request-token-budget` | `number` | `number` | Max input tokens per single request (0=disabled) |
| `DAILY_COST_BUDGET` | ✅ | `--daily-cost-budget` | `number` | `number` | Max USD spend per UTC day (0=disabled) |
| `MID_STREAM_OUTPUT_BUDGET` | ✅ | `--mid-stream-budget` | `number` | `slider` | Stop expensive model after N output tokens, route next turn cheaper (0=disabled) |

## Circuit Breaker

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `CB_FAILURE_THRESHOLD` | ✅ | `--cb-failure-threshold` | `number` | `number` | Failures before circuit opens (trips model as 'dead') |
| `CB_SUCCESS_THRESHOLD` | ✅ | `--cb-success-threshold` | `number` | `number` | Successes in half-open state before circuit closes |
| `CB_TIMEOUT_SECONDS` | ✅ | `--cb-timeout` | `number` | `slider` | Cooldown seconds before half-open probe (default: 5 min) |

## Compression & Cache

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `HEADROOM_BYPASS_THRESHOLD` | ✅ | `--headroom-bypass` | `number` | `slider` | Skip headroom compression for requests below this token count (0=disabled) |
| `TOOL_SCHEMA_STRIP` | ✅ | `--tool-schema-strip` | `toggle` | `switch` | Strip redundant fields from tool schemas to reduce token burn |
| `TOOL_DESC_MAX` | ✅ | `--tool-desc-max` | `number` | `number` | Max characters for tool-level description |
| `TOOL_PARAM_DESC_MAX` | ✅ | `--tool-param-desc-max` | `number` | `number` | Max characters for per-property description |
| `SEMANTIC_CACHE_ENABLED` | ✅ | `--semantic-cache` | `toggle` | `switch` | Enable semantic dedup cache (skips provider call for near-duplicate prompts) |
| `SEMANTIC_CACHE_THRESHOLD` | ✅ | `--semantic-cache-threshold` | `number` | `slider` | Similarity threshold for semantic cache hits (0.0-1.0) |
| `SEMANTIC_CACHE_SIZE` | ✅ | `--semantic-cache-size` | `number` | `number` | Max entries in semantic cache (LRU) |
| `SEMANTIC_CACHE_TTL` | ✅ | `--semantic-cache-ttl` | `number` | `number` | Seconds before semantic cache entry expires |
| `TOKEN_COUNT_CACHE_SIZE` | ✅ | `--token-cache-size` | `number` | `number` | LRU cache slots for tiktoken encoding results |

## Local GPU Inference

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `LOCAL_ENABLED` | ✅ | `--local-enabled` | `toggle` | `switch` | Enable local GPU inference (ollama/llamafile) as 4th cascade tier |
| `LOCAL_MODEL` | ✅ | `--local-model` | `input` | `input` | Local model name (e.g. llama3.2, mistral, phi3) |
| `LOCAL_ENDPOINT` | ✅ | `--local-endpoint` | `input` | `input` | Local inference endpoint (ollama default: :11434/v1) |

## Logging

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `LOG_FILE` | ✅ | `--log-file` | `input` | `input` | Proxy log file path |
| `LOG_MAX_SIZE_MB` | ✅ | `--log-max-mb` | `number` | `number` | Max log file size before rotation |
| `LOG_RETENTION_DAYS` | ✅ | `--log-retention` | `number` | `number` | Days to keep rotated logs |
| `DEBUG_TRAFFIC_LOG` | ✅ | `--debug-traffic` | `toggle` | `switch` | Force full traffic logging (logs/debug_traffic.log). Automatic when LOG_LEVEL=de |
| `DEBUG_TRAFFIC_QUIET` | ✅ | `--debug-traffic-quiet` | `toggle` | `switch` | Suppress full traffic logging even at LOG_LEVEL=debug. For debug Python logs WIT |

## Model Tiers

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `BIG_MODEL` | ✅ | `--big-model` | `input` | `input` | BIG tier model (opus-level) |
| `MIDDLE_MODEL` | ✅ | `--middle-model` | `input` | `input` | MIDDLE tier model (sonnet-level) |
| `SMALL_MODEL` | ✅ | `--small-model` | `input` | `input` | SMALL tier model (haiku-level) |
| `BIG_CASCADE` | ✅ | `--big-cascade` | `textarea` | `textarea` | BIG tier fallback models (comma-separated) |
| `MIDDLE_CASCADE` | ✅ | `--middle-cascade` | `textarea` | `textarea` | MIDDLE tier fallback models (comma-separated) |
| `SMALL_CASCADE` | ✅ | `--small-cascade` | `textarea` | `textarea` | SMALL tier fallback models (comma-separated) |
| `MODEL_CASCADE` | ✅ | `--model-cascade` | `toggle` | `switch` | Enable cascade fallback on model failures |
| `MODEL_CASCADE_DAILY_LIMIT` | ✅ | `--cascade-daily-limit` | `number` | `number` | Max cascade requests per model per day (0=unlimited) |
| `OPENROUTER_FALLBACK_MODELS` | ✅ | `--or-fallbacks` | `textarea` | `textarea` | Dynamic OpenRouter fallback pool (comma-separated) |

## Reasoning & Thinking

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `REASONING_EFFORT` | ✅ | `--reasoning-effort` | `select` | `select` | Default reasoning effort level |
| `REASONING_MAX_TOKENS` | ✅ | `--reasoning-max-tokens` | `number` | `slider` | Max thinking tokens for extended reasoning |
| `REASONING_EXCLUDE` | ✅ | `--reasoning-exclude` | `toggle` | `switch` | Strip thinking tokens from response (reduce output size) |
| `BIG_MODEL_REASONING` | ✅ | `--big-reasoning` | `input` | `input` | Per-tier reasoning override for BIG model |
| `MIDDLE_MODEL_REASONING` | ✅ | `--middle-reasoning` | `input` | `input` | Per-tier reasoning override for MIDDLE model |

## Router Slots

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `ROUTER_BACKGROUND` | ✅ | `--router-background` | `input` | `input` | Model for background/async tasks |
| `ROUTER_THINK` | ✅ | `--router-think` | `input` | `input` | Model for reasoning/thinking requests |
| `ROUTER_LONG_CONTEXT` | ✅ | `--router-long-context` | `input` | `input` | Model for long-context requests |
| `ROUTER_LONG_CONTEXT_THRESHOLD` | ✅ | `--router-long-context-threshold` | `number` | `slider` | Token threshold for long-context routing |
| `ROUTER_WEB_SEARCH` | ✅ | `--router-web-search` | `input` | `input` | Model for web search tool requests |
| `ROUTER_IMAGE` | ✅ | `--router-image` | `input` | `input` | Model for image/vision requests |

## Server

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `HOST` | ✅ | `--host` | `input` | `input` | Server bind address |
| `PORT` | ✅ | `--port` | `number` | `number` | Server port |
| `LOG_LEVEL` | ✅ | `--log-level` | `select` | `select` | Logging verbosity |
| `REQUEST_TIMEOUT` | ✅ | `--request-timeout` | `number` | `number` | Upstream request timeout |
| `MAX_RETRIES` | ✅ | `--max-retries` | `number` | `number` | Max upstream retries before cascade |

## Tool Calls

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `TOOLCALL_MODELS` | ✅ | `--toolcall-models` | `textarea` | `textarea` | Tool-call capable models prepended to cascade (comma-separated) |
| `TOOLCALL_AUTO_ROUTE` | ✅ | `--toolcall-auto-route` | `toggle` | `switch` | Auto-detect tool-call requests and use TOOLCALL_MODELS |
| `TOOLCALL_MAX_RETRIES` | ✅ | `--toolcall-max-retries` | `number` | `number` | Max retries per model in tool-call cascade |
| `TOOL_OUTPUT_MAX_CHARS` | ✅ | `--tool-output-max` | `number` | `number` | Max characters per tool output (truncation) |
| `TOOL_OUTPUT_TRUNCATION` | ✅ | `--tool-truncation` | `toggle` | `switch` | Enable tool output truncation (for small-context models) |

## Usage Tracking

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `TRACK_USAGE` | ✅ | `--track-usage` | `toggle` | `switch` | Record request statistics to SQLite database |
| `USAGE_TRACKING_DB_PATH` | ✅ | `--usage-db` | `input` | `input` | SQLite database file path for usage tracking |
| `SILENCE_DEPRECATION_WARNINGS` | ✅ | `--silence-deprecation-warnings` | `toggle` | `switch` | Suppress deprecated env-var warnings on startup |

## Watchdog

| Setting | .env | CLI | TUI | Web | Description |
|---|---|---|---|---|---|
| `PROXY_WATCHDOG` | ✅ | `--proxy-watchdog` | `toggle` | `switch` | Start auto-recovery watchdog pane (checks health, restarts dead services) |
| `WATCHDOG_INTERVAL` | ✅ | `--watchdog-interval` | `number` | `number` | Watchdog health check frequency |
| `WATCHDOG_GRACE` | ✅ | `--watchdog-grace` | `number` | `number` | Seconds to wait before restarting after first failure |

## How to Configure

Pick whichever surface is convenient:

**Via `.env` file** (persistent):
```bash
echo 'BIG_MODEL=anthropic/claude-opus-4-20250514' >> .env
proxies down && proxies up   # picks up new env vars
```

**Via CLI flag** (single run):
```bash
python start_proxy.py --big-model anthropic/claude-opus-4-20250514
```

**Via TUI** (interactive):
```bash
python start_proxy.py --configure-advanced
```

**Via Web UI**:
```
http://localhost:8082/settings
```

**Via `--config-file` JSON** (bulk):
```bash
python start_proxy.py --config-file my-config.json
```
