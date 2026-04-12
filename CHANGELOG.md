# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **RTK visibility** — fixed RTK visibility in `proxies status` output.
- **Hermes proxy routing** — updated `~/.hermes/config.yaml` `base_url` to `127.0.0.1:8082` so it routes through proxy.
- **Web UI Fixes** — fixed Tool and Cache icon imports in `realtime/+page.svelte`.
- **Chain management UI** — built a new web UI page for proxy chain/router management (`/chain`).
- **Use Case Endpoint Overrides** — added configurable provider and endpoint overrides (URL/API Key) for role-based model switching (e.g. background, think, long_context) allowing complete delegation of tool calls or specific contexts to dedicated model platforms (like Nvidia Nemotron API).
- **Dual fallback methods** — `FALLBACK_METHOD` env var selects `cascade`, `openrouter_native`,
  or `cascade,openrouter_native` (both). Default: `cascade,openrouter_native`.
  - `openrouter_native`: injects `"models":[…]` + `"provider":{"require_parameters":true,
    "sort":{"by":"throughput","partition":"none"}}` into every request routed through OpenRouter,
    so OR picks the fastest healthy endpoint — zero extra latency, no wasted quota.
  - `cascade`: proxy-level retry loop with circuit breakers and exponential backoff.
- **Circuit breaker wired into cascade** — `src/core/circuit_breaker.py` (previously unused) is
  now integrated into `create_chat_completion_with_cascade`. SSL errors and 400/401s trip the
  breaker for that model (5-min cooldown). Successes close it. OPEN circuits are skipped during
  cascade, avoiding repeated calls to dead endpoints.
- **Dynamic fallback model list** — cascade now appends tool-capable free models from
  `data/free_model_rankings.json` (the existing rankings cache) after the static `BIG_CASCADE` /
  `SMALL_CASCADE` lists, ensuring the cascade always has fresh candidates even when env lists
  aren't configured.
- **`tools/refresh_model_rankings.py`** — standalone script to refresh the rankings cache from
  OpenRouter `/api/v1/models`. Run every 6 hours via cron.
- **Cascade + OpenRouter native enabled by default** in `.envrc`:
  `MODEL_CASCADE=true`, `FALLBACK_METHOD=cascade,openrouter_native`,
  `BIG_CASCADE`, `MIDDLE_CASCADE`, `SMALL_CASCADE` pre-configured with curated free models.
- **Hermes routed through proxy** — `~/.hermes/config.yaml` `base_url` updated from direct
  OpenRouter to `http://127.0.0.1:8082/v1` for cascade/retry coverage.
- **Qwen CLI routed through proxy** — `qw` alias in `.zshrc` updated to `:8082`; `qw-direct`
  alias added for bypass when proxy is unavailable.
- **OpenCode partial routing** — `oc` alias sets `OPENAI_BASE_URL=http://127.0.0.1:8082/v1` for
  the OpenAI provider; `oc-direct` alias for bypass. Note: OpenCode's `openrouter/` models still
  bypass the proxy (hardcoded URL in binary — no config workaround).
- **Bypass aliases** — every proxied tool now has a `-direct` alias (`qw-direct`, `oc-direct`,
  `cc-direct`, `hermes-direct`) for running without the proxy stack.
- **Alibaba ramp-up cascade** — both non-streaming (`create_chat_completion_with_cascade`) and
  streaming (`create_chat_completion_stream_with_cascade`) now detect Alibaba's "rate increased too
  quickly" / "scale requests more smoothly" 429 and immediately cascade to the next provider instead
  of retrying. Other 429s get exponential backoff: `min(30s, 2^retry * jitter)` instead of flat 1s.
- **Proxy chain config** (`src/core/proxy_chain.py`) — fully configurable ordered list of upstream
  services. Each entry: id, name, url, auth_key, service_cmd, port, health_path, timeout. Chain saved
  to `config/proxy_chain.json`. CLIProxyAPI entry kept but **disabled by default** (Google banning
  TOS violations). `ProxyChain.upstream_url()` auto-derives `PROVIDER_BASE_URL` from first enabled
  HTTP entry — no need to hardcode it in `.env`.
- **Model router** (`src/core/model_router.py`) — per-use-case routing: `default`, `background`,
  `think`, `long_context`, `web_search`, `image`. Custom router scripts supported (Python natively,
  JavaScript via Node.js subprocess). Wired into `endpoints.py` after tier routing so use-case
  overrides win. Env vars `ROUTER_*` override `proxy_chain.json` router section.
- **`src/cli/chain_tui.py`** — Textual TUI for managing the proxy chain. Numbered list, arrow-key
  reordering (W/S), add/delete/edit entries, toggle enabled/disabled, restart services, edit all
  router config fields. Auto-saves on quit. Launch with `proxies chain` or
  `python -m src.cli.chain_tui`.
- **`proxies` script rebuilt** — now reads `config/proxy_chain.json` dynamically. Spawns one tmux
  pane per enabled service entry (in correct start order). `proxies chain` opens the TUI.
  `proxies status` shows health for all chain entries.
- **Web UI API** — `GET/PUT /api/proxy-chain` and `GET/PUT /api/router-config` endpoints added to
  `src/api/web_ui.py` for managing chain config from the web dashboard.
- **`config/custom_router.example.py`** — contract documentation + working examples for the Python
  custom router API.
- **`config.py` auto-derives `PROVIDER_BASE_URL`** from proxy chain when env var not set.
  `ROUTER_*` env vars loaded into `Config` fields and merged into `ModelRouter` on init.

### Added
- **RTK visibility** — fixed RTK visibility in `proxies status` output.
- **Hermes proxy routing** — updated `~/.hermes/config.yaml` `base_url` to `127.0.0.1:8082` so it routes through proxy.
- **Web UI Fixes** — fixed Tool and Cache icon imports in `realtime/+page.svelte`.
- **Chain management UI** — built a new web UI page for proxy chain/router management (`/chain`).
- **Use Case Endpoint Overrides** — added configurable provider and endpoint overrides (URL/API Key) for role-based model switching (e.g. background, think, long_context) allowing complete delegation of tool calls or specific contexts to dedicated model platforms (like Nvidia Nemotron API).
- **Circuit breaker → OR `models` array feedback** (`client.py`) — `_build_or_models_list()` now
  filters OPEN circuit breakers from the OpenRouter native `models` array before injecting into
  requests. Dead models no longer waste OR's routing budget; if all breakers are OPEN, primary model
  is kept as the only entry so OR still receives a valid request.
- **`parse_ok` structural tracking** (`circuit_breaker.py`) — `record_parse_ok()` and
  `record_stream_finish()` methods on `CircuitBreaker` detect structurally broken HTTP 200 responses
  (empty content, missing `tool_calls`, `finish_reason: length`). Two soft failures accumulate to one
  hard-failure equivalent toward the circuit-open threshold. Wired into both non-streaming and
  streaming cascade success paths.
- **Background routing cascade fallback** (`endpoints.py`) — Use-case-routed requests (background,
  image, long_context, think) now carry a `_use_case_tier` that flows into `infer_model_tier` as a
  fallback. Background/haiku requests fall back to `MIDDLE_CASCADE`; image/long_context/think fall
  back to `BIG_CASCADE`. Previously, a single failure of `ROUTER_BACKGROUND` was a hard client error.
- **Circuit breaker state persistence** (`circuit_breaker.py`) — State is saved to
  `data/circuit_breaker_state.json` when the cascade exhausts all models. On startup, breakers are
  restored from disk: OPEN breakers recalculate their remaining cooldown, breakers whose cooldown
  elapsed during the restart come back as HALF_OPEN. Eliminates quota waste re-discovering dead models
  after every proxy restart.
- **Streaming cascade circuit breaker skip** (`client.py`) — The streaming cascade was missing the
  OPEN circuit breaker skip that existed in the non-streaming path. Fixed: both paths now skip OPEN
  breakers before attempting a model.

### Fixed
- **Crash on manual startup without `PROVIDER_API_KEY`** — `crosstalk.py` line 511 has a module-level
  `CrosstalkOrchestrator(config)` that runs at import time. In passthrough mode (`openai_api_key=None`),
  `AsyncOpenAI(api_key=None)` raised `OpenAIError`. Fixed in `src/core/client.py`: substitute
  `"passthrough-no-server-key"` when `api_key` is None so the client can be constructed; the real
  per-request key is injected later by `endpoints.py`. The systemd service was unaffected (it explicitly
  sets `PROVIDER_API_KEY=passthrough`).
- **Config placeholder list** — added `"dummy"` to the `PROVIDER_API_KEY` placeholder detection in
  `src/core/config.py` so it correctly enables passthrough mode (was treated as a real key before).
  `"pass"` was already in the list. `"passthrough"` intentionally NOT added — the systemd service uses
  that value in proxy mode (not passthrough mode) and CLIProxyAPI replaces it with real auth downstream.

### Changed
- **Starship `scan_timeout`** raised from 30ms → 500ms in `~/.config/starship.toml` to stop timeout
  warnings when the shell prompt scans the proxy directory (large `node_modules`/`.venv`).
