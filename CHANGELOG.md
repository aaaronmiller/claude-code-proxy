# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **`proxies statusline` / `proxies sl`** — Visual TUI for building the Claude Code
  status line. Toggle 23 available segments (CC stdin-JSON fields, system metrics,
  proxy/headroom/RTK metrics), assign each to line 1 or 2 with left/right alignment,
  reorder within groups. Live preview updates on every keystroke. Saves to
  `~/.claude/statusline-config.json` and patches `settings.json` to wire up the
  universal renderer. Keybindings: space=toggle, l/r=align, 1/2=line, j/k=reorder,
  s=save, q=quit.
- **`scripts/statusline_segments.sh`** — Library of 23 reusable segment renderers
  (`seg_<id>`): model, cwd, cwd_full, git_branch, session_cost, transcript_lines,
  clock, cpu, memory, disk, proxy_health, headroom_health, routing_mode,
  proxy_requests, proxy_cost, proxy_latency, cascade_events, tokens_per_sec,
  session_tokens, tool_stats, headroom_savings, rtk_savings, last_proxy_error.
  Self-describes via `seg_list` (id|label|category|sample) for TUI consumption.
- **`scripts/statusline_render.sh`** — Universal statusline renderer. Reads stdin
  JSON from Claude Code + config from `~/.claude/statusline-config.json`, emits
  two lines with left-flowing + right-anchored segments using ANSI cursor
  positioning (`\033[<col>G`) to pin right items regardless of left content width.
- **`proxies config` subcommand** — Full proxy chain management from CLI without the TUI.
  Subcommands: `show`, `set <id> <key> <value>`, `toggle <id>`, `order <id> up|down`,
  `add <id> <name> <url>`, `rm <id>`, `env`. Edits `config/proxy_chain.json` directly.
  Example: `proxies config toggle cliproxyapi` to enable/disable an entry.
- **`proxies router` subcommand** — Task-based model substitution management.
  Subcommands: `show`, `set <slot> <model>`, `clear <slot>`, `disable`, `enable`,
  `passthrough`. The `passthrough` mode disables ALL routing AND cascade fallback
  (for Anthropic Pro subscription direct mode). `disable` keeps tier models but
  skips all per-use-case routing. Changes persist to both `proxy_chain.json` and `.env`.
- **`proxies metrics` subcommand** — Detailed usage metrics: `summary` (tokens/cost/latency
  + cascade events + RTK savings), `models` (per-model token breakdown with success/fail),
  `tools` (24h tool call analytics), `daily` (7-day usage history). Pulls from existing
  `/api/stats`, `/api/metrics/aggregate`, `/api/metrics/tool-analytics`, `/api/metrics/history`.
- **Router disabled/passthrough runtime enforcement** — `RouterConfig.disabled` and
  `RouterConfig.passthrough` now short-circuit `ModelRouter.route()` to return `None`
  (tier fallback). `passthrough` additionally disables cascade in `openai_endpoints.py`
  by gating on `not chain.router.passthrough`.
- **Tmux pane status bars** — `proxies up` now configures a bottom status bar across
  the session showing live proxy stats (left) and Headroom + RTK compression stats (right).
  Refreshed every 5 seconds. Powered by `scripts/tmux_status.sh`.
- **`scripts/cc_statusline_metrics.sh`** — Claude Code status line integration module.
  Exposes sourceable functions (`get_proxy_health`, `get_session_tokens`, `get_tool_stats`,
  `get_headroom_savings`, `get_rtk_savings`, `get_last_proxy_error`, `get_routing_mode`,
  `get_fixed_width_model`) plus a standalone `all` mode that prints a one-line joined
  status. Caches API responses for 5s in a PID-scoped tmpdir. See `docs/STATUS_BARS.md`.
- **`docs/STATUS_BARS.md`** — Integration guide for tmux status bars and Claude Code
  status line, including a fix for variable-width layout jitter (fixed-column positioning).
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

### Fixed
- **OpenRouter native fallback overflow** — `src/core/client.py` now caps the injected
  OpenRouter `models` array at 3 total entries (primary + fallbacks), matching OpenRouter's
  request limit and preventing `400 "'models' array must have 3 items or fewer"` failures.
- **`.envrc` / `.env` fallback split-brain** — trimmed `.envrc`
  `OPENROUTER_FALLBACK_MODELS` to 2 entries so shell-started proxy sessions match `.env`
  and stop overriding the safe native fallback count.
- **Proxy chain self-loop on auto-derived upstreams** — `src/core/proxy_chain.py`
  now skips the local Claude Code Proxy entry when deriving `PROVIDER_BASE_URL`, so
  chain-managed launches resolve to Headroom/upstream instead of routing `:8082` back into itself.
- **Dead model `stepfun/step-3.5-flash:free` removed** — Model no longer exists on OpenRouter (404).
  Replaced with `nvidia/nemotron-nano-9b-v2:free` across all configs: `proxy_chain.json`, `.env`,
  `.envrc`, `proxy_chain.py` defaults, `model_catalog.py`, `chain_tui.py` placeholder.
- **Model limits missing for all active free models** — Added correct context/output limits for
  `nvidia/nemotron-3-super-120b-a12b:free`, `minimax/minimax-m2.5:free`, `openai/gpt-oss-120b:free`,
  `nvidia/nemotron-nano-9b-v2:free`, `qwen/qwen3-235b-a22b:free`, `qwen/qwen3-30b-a3b:free` to both
  static fallback in `model_limits.py` and `data/model_limits.json`.
- **Fixed 114 models with `output: None`** — Set reasonable output defaults (16384 for ≥64K ctx, 8192
  for smaller) so proxy doesn't fall back to 4096 for every free model.
- **Context overflow on minimax-m2.5** — Added `max_tokens` capping in `request_converter.py` that
  caps output tokens to the model's actual output limit (e.g. 16384 for minimax-m2.5) instead of
  sending 128K output that blows past the 196K context window.
- **`.envrc` model overrides** — BIG_MODEL/MIDDLE_MODEL/SMALL_MODEL were set to CLIProxyAPI-only models
  (gemini-3.1-pro-high) but CLIProxyAPI is disabled. Changed to OpenRouter free models as defaults.
- **Streaming duplicate `stream` parameter** — `openai_endpoints.py` passed `stream=True` as both a
  dict key and keyword arg to `create()`, causing `got multiple values for keyword argument 'stream'`.
  Fixed by popping `stream` from dict before passing as kwarg.
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

### Added
- **`proxies stats` command** — Pulls usage statistics from proxy API: requests today, total tokens,
  avg latency, recent requests, cascade events. Also shows RTK token savings if installed.
- **Installer Headroom configuration** — `install-all.sh` now passes `--openai-api-url` and
  `--backend` args to Headroom, configurable via `HEADROOM_BACKEND` and `HEADROOM_API_URL` env vars.
  Also configures `proxy_chain.json` and sets up RTK in CLAUDE.md during install.
- **Centralized Headroom config** — Added `HEADROOM_BACKEND`, `HEADROOM_API_URL`, `HEADROOM_MODE`
  env vars so all proxy configuration lives in `.envrc`.

### Changed
- **Starship `scan_timeout`** raised from 30ms → 500ms in `~/.config/starship.toml` to stop timeout
  warnings when the shell prompt scans the proxy directory (large `node_modules`/`.venv`).
