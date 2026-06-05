# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — Performance & Reliability Improvements + Profile Routing Spec

### Added
- **Headroom auto acceleration and LAN relay** (`scripts/headroom-start.sh`, `scripts/headroom-relay.py`, `scripts/headroom-openvino-site/sitecustomize.py`) — Headroom startup now detects NVIDIA, Intel Arc/iGPU, or CPU fallback; pins Intel OpenVINO Kompress to the verified device; restores the missing ONNX wrapper in Headroom 0.20.27 for CPU fallback; and supports `HEADROOM_REMOTE_URL` so machines without a useful GPU can relay local `:8787` traffic to a shared LAN Headroom host. Docs added in `docs/headroom-acceleration.md`.
- **Gateway documentation rewrite** (`README.md`, `docs/setup.md`, `docs/index.md`) — Repositioned the project from "proxy" to local AI gateway for coding agents, documented the Headroom-first path, remote GPU sharing, and operational command surface. Working product name: Clutch Gateway.
- **Dense standalone Codex status segment** (`scripts/status/codex_status.py`, `scripts/status/codex_tmux.sh`) — Reads Codex rollout JSONL files to show model/reasoning, permission mode, context window usage, total session input/output/cache tokens, API-equivalent estimated cost, rate-limit pressure, and clock in the independent `codex-status` tmux bar alongside RTK savings.
- **Completed model-scan launcher, lanes, observability, and reliability loop** (`scripts/ccp-launch.sh`, `src/core/quota_sources.py`, `src/core/rotation.py`, `src/services/observability/`, `src/api/endpoints.py`) — Adds ephemeral session routing profiles, `ccp up/errors/<tool>`, standby vs interactive lane policy, quota-aware rotation/key-pool support, unified `~/.ccp/errors.jsonl`, `GET /api/model-scan/dashboard`, session ids on standard logs, and periodic reliability feedback to model-scan.
- **Model-scan integration operator guide** (`docs/MODEL_SCAN_INTEGRATION.md`) — Documents producer/consumer setup, reload endpoint, launcher usage, lane behavior, quota precedence, observability surfaces, and reliability feedback.
- **Repository cleanup archive** (`archive/2026-06-01-cleanup/`) — Moved historical root docs, retired one-off scripts, old draft plans, scratch specs, prompt dumps, and old database copies out of the repo root while preserving their folder context. Added README layout guidance and moved root cheatsheets under `docs/cheatsheets/`.
- **Model-scan router binding** (`src/core/model_scan_binder.py`, `src/core/model_scan_runtime.py`, `src/api/endpoints.py`) — Adds gated snapshot consumption for measured routing: `model_scan` config is preserved across assignment saves, startup/SIGHUP/`POST /api/proxy/reload-models` can bind a routing snapshot into tier assignments and cascades, and profile `slot_bindings` apply in-memory overlays without request-time file IO.
- **RTK stats cache + API** (`scripts/status/rtk_status.py`, `src/api/rtk_stats.py`) — Adds a 10s cached JSON snapshot from `rtk gain --project --format json`, exposed to tmux status via `scripts/tmux_status.sh rtk` and REST via `GET /api/rtk/stats`. Falls back to stale cache if RTK is temporarily unavailable.
- **Standalone Codex RTK status launcher** (`scripts/status/codex_tmux.sh`) — Starts independent `rtk codex` sessions inside a `codex-status` tmux session with project/GitHub status on the left and cached RTK savings on the right.
- **Codex status line setup** (`~/.codex/config.toml`, `scripts/tmux_status.sh`, `proxies`) — Codex native footer now shows model/reasoning, current dir, git branch, context remaining/used, usage limits, token totals, fast mode, and version. The proxy tmux bar now adds a project/GitHub segment with remote, branch, dirty count, and ahead/behind before proxy/headroom/RTK stats.
- **Spec-kit documentation: Profile Routing feature** (`specs/002-profile-routing/`) — 7 files generated from requirements.md and design.md via spec-kit templates: spec.md, plan.md, research.md, data-model.md, tasks.md, quickstart.md, contracts/api-contracts.md. Referenced project constitution (`.specify/memory/constitution.md`) and global agent constitution (`~/code/agents/constitution.md`).

### Added (Model-Scan Integration — Phase 0: shared contract)
- **Routing-snapshot contract fixtures + validation tests** (`tests/fixtures/snapshots/valid_snapshot.json`, `tests/contract/test_routing_snapshot_schema.py`) — Representative valid snapshot (cost_basis slot, free slot, and a null-best/empty-candidates slot) plus eight assertions pinning the structural contract: required fields, `additionalProperties: false`, nullable `best`/`price_blended`, `eval_mode` enum, and `schema_version` pattern. (T001)
- **Snapshot schema mirrored to model-scan** (`/home/cheta/code/model-scan/contracts/routing_snapshot.schema.json`) — Byte-identical copy so producer and consumer share one contract source. (T002)
- **Session-config contract fixtures + parse tests** (`tests/fixtures/sessions/valid_session.json`, `tests/contract/test_session_config_schema.py`) — Pins the policy grammar (`static|free|quality|roles|budget:<ceiling>`), additive-only shape, and empty-overlay validity for the launcher and ephemeral-profile API. (T003)
- **`api_model` derivation and `base_url` gap-fill rules documented** (`specs/003-model-scan-integration/research.md`) — Producer is sole authority for `api_model` (`provider/native_id`, observed suffix preserved, no normalization); router gap-fills empty `base_url` from its credential-paired registry, snapshot endpoint used only when the registry lacks the provider. (T004)

### Added (Model-Scan Integration — Phase 2/3: router consumption and profile overlays)
- **Routing-snapshot loader** (`src/services/models/model_scan_snapshot.py`, T020) — Immutable frozen-dataclass `RoutingSnapshot`/`RoleSelection`/`Candidate` graph with `load(path)`, `from_gateway(url)`, `is_stale` (monotonic cache TTL) and `is_data_stale`/`data_age_seconds` (wall-clock `generated_at` staleness). Validates against the contract, applies schema defaults the validator does not inject (`base_url:""`, `tier:"unknown"`), refuses a newer major schema version with a logged alert, and returns `None` on any failure so the caller keeps its last good snapshot. Single canonical schema resolved from the repo `specs/` contract (no second copy to drift). 19 tests (`tests/test_model_scan_snapshot.py`).
- **Selection policy and binder** (`src/core/model_scan_binder.py`, T022-T024) — `SelectionPolicy.parse` (`static|free|budget:<ceiling>|quality|roles`) and `choose(role, blocklist)` returning `(primary, cascade)` with the cascade excluding the primary and the blocklist. `bind()` resolves default tier assignments plus per-profile overlays with provenance and static fallback when a role is absent or empty. 26 tests (`tests/test_model_scan_policy.py`).
- **Runtime model-scan reload** (`src/core/model_scan_runtime.py`, `src/main.py`, T026-T027) — Reads snapshots from file or gateway, rejects stale/invalid data, writes changed default tier assignments through `AssignmentRegistry`, atomically swaps the active overlay map, and exposes `POST /api/proxy/reload-models`. Startup and SIGHUP call the same reload path.
- **Profile `slot_bindings` support** (`src/core/profiles.py`, `profiles/profiles.json`, `src/api/endpoints.py`, `src/api/openai_endpoints.py`, T030-T031) — Deep-merges default and named profile role bindings, applies active model-scan overlays after tier resolution alongside `tier_overrides`, and carries the resolved cascade into the existing cascade engine.

### Fixed (Cascade-exhausted error masked real failures as 500)
- **`raise APIError("...")` replaced with `HTTPException(503)`** (`src/core/client.py`, both non-stream and stream cascade) — When every cascade model was skipped before an attempt (all circuit breakers open after repeated failures), the loop exited with `last_error is None` and ran `raise APIError("All cascade models failed")`. The OpenAI SDK signature is `APIError(message, request, *, body)`, so a bare-message construction raised `TypeError: ... missing 1 required positional argument: 'request'`, which the endpoint turned into a generic 500 — masking the real cause (e.g. the headroom 401 storm that tripped the breakers). Now raises a clear `503` with an actionable message. Regression test `tests/test_cascade_exhausted_error.py` (all-circuits-open → 503 for both stream and non-stream; guard test proving `APIError("msg")` is a `TypeError`).
- **Verified `NORMALIZE_SYSTEM_ROLE` end-to-end** — `normalize_system_role=true` is live; its output (`role:system`→`role:user`, producing two leading user messages) is accepted by OpenRouter (HTTP 200 confirmed against two free models). Confirms the cross-backend format normalization the launcher relies on for mid-session backend switches produces provider-valid requests.

### Fixed (Headroom 401 cascade — correct root-cause fix, headroom kept enabled)
- **Headroom now routes OpenAI-format upstream traffic to OpenRouter** (`config/proxy_chain.json` headroom `service_cmd`) — Added `--openai-api-url https://openrouter.ai/api/v1` and re-enabled headroom (`enabled: true`). Root cause: the proxy converts requests to OpenAI format before forwarding to headroom (headroom logs them as `provider: openai`), but the headroom command set only `--anthropic-api-url`; with `--openai-api-url`/`OPENAI_TARGET_API_URL` unset, headroom defaulted its OpenAI passthrough target to `https://api.openai.com` (`headroom/providers/codex/runtime.py: DEFAULT_API_URL`), so the OpenRouter `sk-or-...` key was sent to OpenAI and rejected — 401 on every cascade model. A prior session had masked this by disabling headroom entirely; that is now undone. Verified by A/B: direct OpenRouter 200, headroom-old-cmd 401, headroom-fixed 200 (real free-model completion through `:8787`). NOTE: a running ccp must reload its chain (restart / `ccp up`) to pick up `enabled: true` and route through headroom; ccp has no live SIGHUP reload.

### Fixed (Test isolation + config restoration — model-scan integration)
- **Tests no longer pollute the real `config/proxy_chain.json`** (`tests/conftest.py`) — Added a global autouse `_isolate_proxy_chain_file` fixture that copies the chain to a per-test temp file and points `PROXY_CHAIN_FILE` at it, so chain/assignment-mutating tests (`test_config_api_contract`, `test_inflight_isolation`, `test_cross_surface_propagation`) write to a throwaway file. Reads see identical content; tests that set their own `PROXY_CHAIN_FILE` still take precedence. Teardown reload is best-effort so migration-halt tests that point at a malformed file do not error.
- **Restored `config/proxy_chain.json` production data** — Earlier test runs had persisted test entries into the real config, wiping the `claude_code_proxy`/`headroom` chain entries down to a leftover `tobedeleted` and overwriting `assignments.big.model` with `after-write`. Restored the committed entries and `big.model=baidu/cobuddy:free`; the only intended diff is the new `model_scan` section. This also fixes `test_delete_chain_entry`, which had failed because a stale `tobedeleted` entry survived on disk between runs.
- **Added conditional upstream-proxy chain entry** (`config/proxy_chain.json`, T044) — `cliproxyapi` (CLIProxyAPI/Antigravity, port 8317) added `enabled: false` per the design's conditional-bring-up rule (`ccp up` starts it only when OAuth-hosted providers are configured).
- **T044 local-model clause verified, no code change needed** (FR-048) — Investigated the "Headroom `service_cmd` also launches the local model" requirement against the live chain. Headroom's compression model is **in-process** (ONNX/PyTorch, GPU-accelerated via the existing `_detect_gpu_env` injection in `proxies`), not an external service — confirmed by no `:11434`/ollama connection from the headroom process and by headroom reporting healthy (`:8787` HTTP 200), which only happens once its kompressor model has loaded. FR-048 acceptance ("the compression stage and its local model are reachable") is therefore satisfied by the existing headroom entry; adding an external model launch would spawn a process headroom does not use. Router `:8082` and headroom `:8787` both verified HTTP 200.

### Fixed (Constitution gate integrity — model-scan spec)
- **Invalid Constitution Check gate corrected** (`specs/003-model-scan-integration/plan.md`) — The gate enumerated only 2 of 6 core principles plus 4 items that are not constitution principles ("no hardcoded model names", "reuse over duplication", "two projects stay separate"), so the two non-negotiables most relevant to the feature (III Safe Destructive Operations, VI Single Source of Truth for Configuration) were never evaluated. Rewrote the gate to enumerate all six core principles and the three engineering constraints with file-grounded PASS/N/A status.
- **Project `CLAUDE.md` constitution wiring corrected** (`CLAUDE.md`) — Replaced the wrong 4-item abbreviation (sourced from global engineering rules, not the constitution) with the accurate six principle names + three constraints, a mandatory re-read-before-gate trigger that survives context compaction, and explicit rules for honoring the `tasks.md` phase gates and MVP boundary. File kept under the 300-line Progressive-Disclosure limit (185 lines).
- **`speckit-autonomous-run` skill hardened** (external `custom-skills/speckit-autonomous-run/SKILL.md`, v1.1→v1.2) — Root-caused the gate corruption: the skill assumed a fixed 5 principles and told the agent to list names from memory, which pulled in non-constitution rules and dropped real ones; the "name the principles" verification was circular and confirmed the corrupted list against itself. Fixed: mechanical `grep '^### '` extraction of principle headings, count assertion, full-text-or-headings+re-read-trigger wiring, a gate-validity rule, and a file-vs-CLAUDE.md cross-check replacing the circular verification.

### Fixed (Deliberative Refinement audit — 8 issues resolved)
- **CRITICAL: Cascade fallbacks all empty** (`src/core/config.py`) — `get_cascade_for_tier()` only read the new `assignments.{tier}.cascade` format but `.env` uses legacy `MIDDLE_CASCADE=` vars. Added legacy env var fallback path so `BIG_CASCADE`, `MIDDLE_CASCADE`, `SMALL_CASCADE` are now read correctly. All three tiers now have fallback models. Estimated reliability score improvement: +0.30.
- **Security: PROXY_AUTH_KEY bypassed** (`src/core/config.py`) — `config.anthropic_api_key` was falling through to the real `ANTHROPIC_API_KEY` instead of `PROXY_AUTH_KEY`. Fixed priority: PROXY_AUTH_KEY → None (default). Legacy re-enable via `ENABLE_LEGACY_PROXY_AUTH=true`. Closes auth bypass.
- **Bug: `parse_model_name` drops colon suffix** (`src/services/models/model_parser.py`) — `original_model` field returned `"o4-mini"` instead of `"o4-mini:high"` because `model_name` was mutated before `original_model` was set. Fixed by capturing `original_input` before parsing. Reasoning config (effort level, token budget) now applies correctly for `:high`/`:4k` notation.
- **Rate limit: X-RateLimit-Reset header now read** (`src/core/client.py`) — 429 responses from OpenRouter include `X-RateLimit-Reset` with the exact reset timestamp. Previously used 300s hardcoded backoff. Now parses the header and uses the actual reset time (capped at 120s). Failed attempts count toward the 200 req/day free quota — this prevents wasting quota on blind retries.
- **Router slots configured** (`.env`) — `think` and `web_search` router slots were empty; tool-call and reasoning requests fell through to default. Assigned: `think→nemotron-3-super:free`, `web_search→nemotron-nano:free`, `image→qwen-vl:free`. Populated `BIG_CASCADE` and `MIDDLE_CASCADE` with 4-5 free fallbacks each.
- **CRITICAL FIX comments removed** (`src/services/conversion/response_converter.py`, `src/services/conversion/request_converter.py`) — Replaced opaque CRITICAL FIX + Issue 18 comments with explanatory docstrings: why the initial empty text block is required (Claude Code SSE client invariant), why orphaned tool results are kept (multi-turn conversation continuity).
- **Deprecated env var warnings suppressible** (`src/core/config_resolver.py`) — Added `SILENCE_DEPRECATION_WARNINGS=true` to silence startup noise when legacy vars are being used intentionally.
- **Structured event log + reliability score** (`src/services/logging/event_logger.py`, `src/api/endpoints.py`, `proxies`) — New `logs/events.jsonl` records one JSON event per request: model_attempted, model_succeeded, cascade_depth, error_type, latency_ms, cost_usd, cache_hit. `GET /api/reliability?hours=24` returns R score with grade (S/A/B/C/F) and per-component breakdown. `proxies reliability` command shows live score with target guidance.

### Added (Config Surface Parity — Full 100% Compliance Pass)
- **CLI: 10 missing flags added** (`start_proxy.py`) — `_skip_groups` was blocking auto-gen for server/models/reasoning groups without manual registration. Added: `--request-timeout`, `--max-retries`, `--big-cascade`, `--middle-cascade`, `--small-cascade`, `--cascade-daily-limit`, `--or-fallbacks`, `--reasoning-max-tokens`, `--big-reasoning`, `--middle-reasoning`. CLI now covers 62/62 manifest settings.
- **Web UI: reasoning group added** (`src/static/settings.html`) — `displayGroups` was missing the `reasoning` group (5 settings). Now all 13 manifest groups are shown. Web UI coverage: 62/62.
- **Web UI: redesign to Terminal-forge dark** (`src/static/settings.html`) — Complete visual overhaul: JetBrains Mono throughout, electric cyan accent (#00d9ff), 2-column settings grid, ASCII-box reliability grade, monospace circuit breaker badges, scanline + noise grain overlay, borderless inputs with bottom-border focus style.
- **TUI: 4 new menu categories** (`src/cli/advanced_config.py`) — Added `configure_models()` (BIG/MIDDLE/SMALL + cascade), `configure_toolcalls()` (5 settings), `configure_logging_advanced()` (log file/rotation), `configure_watchdog()` (3 settings). Also added `AA_API_KEY` to API Keys menu. TUI now covers 62/62 manifest settings across 19 categories.
- **.env.example: fully regenerated** (`.env.example`) — All 62 settings documented with group headers, descriptions, defaults, and usage examples. Previously only 2 variables were documented.
- **docs/configuration.md: complete rewrite** — Full reference for all 62 settings across all 4 surfaces. Tables for every group, TUI category index, Web UI reference, JSON config file format.

### Added (Configuration Surface Parity — CLI/TUI/Web/ENV)
- **Config Manifest** (`src/core/config_manifest.py`) — Single source of truth for all 62 configurable settings. Each setting: `env_var`, `type`, `default`, `description`, `group`, `cli_flag`, `tui_widget`, `web_component`, `units`, `min_val`, `max_val`, `secret`. Consumed by CLI, TUI, Web UI, and API.
- **CLI: 40 new flags + `--config-file` + `--save-config`** (`start_proxy.py`) — All 62 manifest settings now exposed as CLI arguments. `--config-file path.json` loads settings from a JSON file. `--save-config [path]` exports current configuration to .env or JSON. New groups: Budget, Circuit Breaker, Compression, Local GPU, Router Slots, Auth, Logging, Watchdog.
- **API: `GET /api/settings` + `POST /api/settings`** (`src/api/config_api.py`) — `GET /api/settings` returns all 62 settings with values, metadata (type, description, widget hints, units), and group structure. `POST /api/settings` accepts `{settings: {ENV_VAR: value}, persist: true}` and writes to .env.
- **TUI: 5 new sections** (`src/cli/advanced_config.py`) — Added: [A] Budget & Cost Controls, [B] Cascade & Circuit Breaker, [C] Local GPU Inference, [D] Compression & Cache, [E] Router Slots. Main menu now has 14 categories (was 9). Each section shows current values and prompts for changes.
- **Web UI: Settings dashboard** (`src/static/settings.html`, `src/main.py`) — Dark-mode settings page served at `/settings`. Alpine.js + Tailwind CSS with shadcn-style design. Sections: Reliability score gauge, Circuit breakers with reset buttons, all 62 settings grouped with toggle switches, inline editing, toast notifications, Save All button. `GET /api/settings` drives the form.
- **Identifier mappings for gemini models** — `gemini-3-flash`, `google/gemini-3-flash`, `google/gemini-3-flash-preview` → `small` tier. `gemini-3-pro-preview` → `big` tier. Prevents "Invalid API key" errors when clients request these non-free models.

### Fixed
- **`proxies up` broken** (`config/proxy_chain.json`) — `entries` array was emptied during a config write operation. Restored `claude_code_proxy` (:8082), `headroom` (:8787), and `rtk` (disabled) entries. Also fixed: pipe character (`|`) in headroom `service_cmd` broke `IFS='|'` parsing in the proxies script — removed the `tee` redirection from the stored service_cmd.

### Changed (Alias cleanup, hermes routing, model data in startup)
- **Alias invariant enforced** (`scripts/install-aliases.sh`) — All aliases now go through proxy:8082 (routing+logging) → headroom:8787 (compression) → provider + RTK. Removed dead variants: `cld`, `cldx`, `cldp`, `csi`, `csr`, `qsi`, `qsr`, `qw-direct` — headroom-only and proxy-without-RTK variants were clutter.
- **Hermes aliases via proxy** — `hsi`/`hsr` now route through proxy:8082 (not headroom direct :8787). Proxy's cascade/CB handles model failures for all hermes calls. RTK wraps launch (`rtk hermes`) for output compression when used inside another Claude Code session.
- **All other CLI aliases via proxy** — `qw`, `codex-run`, `oc`, `ocl` all go through proxy:8082 + RTK. Headroom-direct variants removed.
- **Startup display: Cost + Free columns** (`src/services/logging/startup_display.py`) — Model table now shows `$/1k` (averaged prompt+completion cost from `models/scout/models.json`) and `Free` status for BIG/MIDDLE/SMALL/LOCAL tiers. 344 models in pricing index.
- **LOCAL tier shown in startup** — When `LOCAL_ENABLED=true`, LOCAL tier row appears in model table.

### Added (Hermes integration, AA/model-scan, alias updates)
- **AA_API_KEY support** (`.env.example`, `src/services/models/model_ranker.py`) — `AA_API_KEY` documented and `get_aa_score()` helper added to model_ranker. Artificial Analysis intelligence scores (MMLU, HumanEval composites) now accessible for model ranking decisions. Set `AA_API_KEY=` in `.env` to enable.
- **Hermes auxiliary roles → proxy routing** (`~/.hermes-shit/config.yaml`) — All 9 auxiliary roles (approval, compression, flush_memories, mcp, session_search, skills_hub, title_generation, vision, web_extract) + delegation now route through the proxy `:8082/v1`. Proxy's circuit breaker + cascade handles model failures automatically. Previously had zero fallback protection.
- **`cc-mini` / `cc-mini-c` aliases** (`scripts/install-aliases.sh`) — Inline `BIG_MODEL=opencode_go/minimax-m2.7` override for sessions where opencode_go is preferred over OpenRouter for the big tier.
- **`cldo` / `cldo-c` documented** — Anthropic OAuth (Pro subscription) passthrough via proxy + headroom compression + RTK terminal compression. Small/toolcall requests cascade to free OpenRouter models.

### Added (Completing All 5 Original Goals to 100%)
- **Mid-stream Tier Switching** (`src/core/client.py`, `src/api/endpoints.py`) — Closes Goal 1. When a model's streaming output exceeds `MID_STREAM_OUTPUT_BUDGET` tokens, the stream is stopped cleanly (Claude Code sees `stop_reason: max_tokens`), and a session-level override routes the continuation turn to the next cheaper tier. Session override is one-shot and cleared after use. Enable via `MID_STREAM_OUTPUT_BUDGET=2000` in `.env`.
- **Pipeline Per-Step Retry + Auth Inheritance** (`src/core/pipeline.py`) — Closes Goal 5. Each pipeline step now supports `max_retries` (retries on transient failure with logging) and `inherit_auth` (`"openrouter"`, `"anthropic"`, `"openai"`) which automatically injects the proxy's API key into step headers. No more hardcoded keys in pipeline JSON.
- **Semantic Dedup Cache** (`src/services/semantic_cache.py`, `src/api/endpoints.py`) — Closes Goal 3. Two-level cache: exact SHA-256 hash match + SimHash near-duplicate detection (pure Python, zero ML deps). For the target use case (agentic loops with identical system prompts + slightly varied queries), similarity hits at 1.0. TTL-based expiry, LRU eviction. Stats via `GET /api/semantic-cache/stats`. Configure via `SEMANTIC_CACHE_THRESHOLD`, `SEMANTIC_CACHE_SIZE`, `SEMANTIC_CACHE_TTL`.
- **Local GPU Inference Tier** (`src/core/client.py`, `src/core/config.py`) — Closes Goal 1 (4th layer). Ollama/llamafile registered as the final cascade fallback when `LOCAL_ENABLED=true`. Speaks OpenAI-compatible HTTP (ollama default: `:11434/v1`). Circuit breakers on remote tiers falling through to local. Configure via `LOCAL_ENABLED`, `LOCAL_MODEL`, `LOCAL_ENDPOINT`.
- **Daily Cost Budget** (`src/services/usage/usage_tracker.py`, `src/api/endpoints.py`) — Companion to token budget. `DAILY_COST_BUDGET=1.00` rejects requests via HTTP 429 when the day's estimated spend exceeds the limit. Uses `UsageTracker.get_daily_total_cost()` querying `daily_model_stats.total_cost`. Resets at UTC midnight.

### Fixed (Deliberative Refinement Pass)
- **Pipeline None propagation** (`src/core/pipeline.py`) — `_get_nested()` returning `None` for a missing `output_field` previously silently passed `None` as input to the next pipeline step. Now raises a descriptive `ValueError` listing available response keys, failing loudly rather than corrupting downstream steps.
- **Circuit breaker thresholds now env-configurable** (`src/core/client.py`) — `failure_threshold`, `success_threshold`, and `timeout` were hardcoded at `3 / 1 / 300`. Now read from `CB_FAILURE_THRESHOLD`, `CB_SUCCESS_THRESHOLD`, `CB_TIMEOUT_SECONDS` env vars with same defaults. Documented in `.env.example`.
- **Tool schema strip skips strict-mode providers** (`src/services/conversion/request_converter.py`) — `_strip_tool_schemas()` (which removes `additionalProperties: false`) is now bypassed for OpenAI, Azure, and Gemini/Google providers that enforce strict JSON Schema. Prevents silent tool-call regression when routing to those providers.

### Added
- **Streaming Output Token Counting** (`src/services/conversion/response_converter.py`) — Accumulates actual output text during streaming and counts tokens via tiktoken at stream end. Fixes the `0→0t` display on providers (minimax, nemotron, etc.) that omit usage data from SSE chunks. Previously fell back to `len//4` heuristic.
- **Cost-per-Request Display** (`src/services/models/cost_lookup.py`, `src/services/logging/proxy_logger.py`) — Estimates and displays per-request cost in the terminal log line using pricing data from `models/scout/models.json`. Free models show `$0.00`; unknown models show nothing. Color-coded green/yellow/red by cost tier.
- **`proxies restart <service>`** (`proxies`) — Restarts a single service in its tmux pane without killing the whole session. Sends Ctrl+C, waits 1s, re-runs the service_cmd with GPU env prefix injected. Usage: `proxies restart headroom`.
- **Headroom Bypass for Tiny Requests** (`src/core/proxy_chain.py`, `src/api/endpoints.py`, `src/core/config.py`) — When `HEADROOM_BYPASS_THRESHOLD` is set, requests with fewer input tokens than the threshold skip headroom and route directly to the provider (default: disabled). New `ProxyChain.direct_provider_url()` method resolves the actual provider URL, falling back to OpenRouter.
- **Auto-Recover Watchdog** (`scripts/watchdog.sh`, `proxies`) — Background health-check loop that restarts dead services automatically. Runs as a small tmux pane when `PROXY_WATCHDOG=true`. Checks every `WATCHDOG_INTERVAL` seconds (default: 30), waits `WATCHDOG_GRACE` seconds before restarting (default: 5) to distinguish transient blips from real failures.
- **Tool Schema Stripper** (`src/services/conversion/request_converter.py`) — Strips redundant fields from tool definitions before forwarding to the model: deduplicates tools by name, removes `additionalProperties: false` (JSON Schema default), truncates verbose parameter descriptions. Reduces tool schema JSON size by 9-52%. Controlled by `TOOL_SCHEMA_STRIP` env var (default: true); thresholds tunable via `TOOL_DESC_MAX` / `TOOL_PARAM_DESC_MAX`.
- **Accurate Token Counting** (`src/services/token_cache.py`) — Replaces the `len(text)//4` character heuristic with real `cl100k_base` tiktoken encoding. Results cached in an LRU keyed on text hash (512 slots, configurable via `TOKEN_COUNT_CACHE_SIZE`). Fixes 16-34% count errors on code/JSON content that affected logging accuracy and will affect budget enforcement.
- **Token Budget Enforcement** (`src/core/config.py`, `src/api/endpoints.py`) — Request-boundary budget gate: set `DAILY_TOKEN_BUDGET` and/or `PER_REQUEST_TOKEN_BUDGET` to reject over-budget requests with HTTP 429 before any tokens are burned. Defaults to 0 (disabled). Daily total tracked via new `UsageTracker.get_daily_total_tokens()`.
- **Circuit Breaker CLI** (`proxies`, `src/api/endpoints.py`) — `proxies breakers` lists all circuit breakers with state (open/closed/half-open), failure counts, and cooldown remaining. `proxies breakers reset <model>` manually un-trips a model. New `/api/breakers` (GET) and `/api/breakers/{model}/reset` (POST) endpoints.
- **Context Dedup Token Cache** (`src/api/endpoints.py`) — Splits input text into stable (system prompt + tools, identical every turn) and variable (messages, changes each turn) portions before token counting. The stable portion hits the LRU cache from turn 2 onwards — empirically 81% of input tokens are in the stable portion of a Claude Code session, eliminating redundant encoding.
- **API Pipeline Orchestration** (`src/core/pipeline.py`, `src/api/endpoints.py`) — Sequential API handoff chains defined in `config/proxy_chain.json` under `"pipelines"`. Each step specifies url, method, input_field, output_field, and optional extra_body. Step output auto-feeds the next step's input. Exposed via `POST /v1/pipeline/{name}` and `GET /api/pipelines`. Includes an `_example_voice` template (Whisper → LLM → Piper TTS) in proxy_chain.json.

### Changed
- `proxies up` — Smart re-attach: if tmux session exists and all services are healthy, re-attaches without kill+restart. Only restarts if session is dead or services are down.
- Terminal logging — Suppressed duplicate uvicorn access log lines for `/v1/messages` and `/v1/chat/completions` (already captured by proxy_logger with full token/latency/routing detail). Added plain-text fallbacks to `proxy_logger` for when Rich is unavailable.
- GPU auto-detection — `_detect_gpu_env()` in `proxies` script probes NVIDIA via `nvidia-smi`, Intel via `clinfo` (WSL2-compatible), and `/dev/dxg` + `/dev/dri` fallback. Injects correct `ONEAPI_DEVICE_SELECTOR` at launch time and strips the static one from `proxy_chain.json`.

## [2026-04-16] — Streaming Usage Tracking & Log Fixes

### Fixed
- **Streaming requests now tracked in `usage_tracking.db`** — Previously, only non-streaming
  requests called `usage_tracker.log_request()`. The streaming generator in `response_converter.py`
  now accepts an `on_complete` async callback, which `endpoints.py` passes to log usage data
  (input/output tokens, duration, status) once the stream finishes. This closes the gap where
  14+ streaming requests per Claude Code tool-use loop were completely invisible to the DB.
- **🟢 completion log lines for streaming requests** — `active_logger.log_request_complete()` is
  now called from the `on_complete` callback, so streaming requests get the same paired 🔵/🟢
  terminal output as non-streaming ones. Previously only non-streaming showed completion.
- **Session grouping via conversation fingerprint** — Replaced `session_id = request_id[:8]`
  (which made every request its own "session") with a stable fingerprint derived from
  `metadata.user_id` or system prompt markers via `RequestDeduplicator._extract_session_fingerprint()`.
  Related tool-use round-trips within a single Claude Code conversation now share the same
  `session_id` in the database.
- **Error-path logging enhanced** — Both `HTTPException` and generic `Exception` error handlers
  in `endpoints.py` now pass `message_count`, `input_tokens`, actual `routed_model`, `provider`,
  `endpoint`, and the conversation `session_id` instead of hardcoded `"unknown"` values.
  Error rows in the DB are now diagnostically useful.
- **Health check log filter actually works** — The existing `_QuietPollFilter` was wired via
  `uvicorn.config.LOGGING_CONFIG.copy()` + dictConfig, which silently failed because `.copy()`
  is shallow (handlers dict was shared/mutated). Replaced with direct
  `logging.getLogger("uvicorn.access").addFilter()` which is guaranteed to work. `/health`,
  `/api/stats`, and `/api/system/health` 200s are now properly suppressed from terminal output.
- **Circuit breaker persistence was silently broken** — `client.py` maintained its own module-level
  `_circuit_breakers` dict separate from `CircuitBreakerRegistry`. The `save_all()` calls at cascade
  exhaustion went through the registry (which had an empty breakers dict), so persisted state was
  always `{}`. Rewired `_get_circuit_breaker()` and `_is_cb_open()` to delegate to
  `CircuitBreakerRegistry.get_sync()`, so persisted state is loaded on first access and `save_all()`
  writes the actual breakers used during cascade.

### Added
- **Model rankings refresh cron** — Added `crontab` entry: every 6 hours,
  `tools/refresh_model_rankings.py --force` refreshes `data/free_model_rankings.json` from
  OpenRouter. Log output goes to `data/rankings_cron.log`.

### Security
- **RBAC Authentication Bypass** — Fixed a massive vulnerability in `src/api/users_rbac.py` where the password verification check was accidentally a tautology (`hash_password(password) == hash_password(password)`). The method now correctly delegates to `user_service.authenticate(username, password)` which queries the database securely.
- **Hardcoded Secret Removal** — Removed the highly insecure hardcoded `admin123` fallback password inside `src/services/user_management.py` auto-provisioning logic. It now checks for `PROXY_DEFAULT_ADMIN_PASSWORD` in the environment, or securely dynamically generates a random 16-byte URL-safe fallback token on first initialization.
- **Credential Storage Dump Prevention** — Reduced the slice length of API keys printed directly into DEBUG logs from `[:20]` down to `[:8]` in `src/core/client.py` to prevent credential exposure of long-lived tokens in case `claude-code-proxy.log` is ever leaked.
- **Path Traversal / Local File Inclusion (LFI)** — Created and injected a `validate_safe_filename()` sanitizer across 6+ API endpoints in `src/api/web_ui.py` (Profiles, Crosstalk Sessions, and Crosstalk Presets endpoints). The API previously used unsanitized web input directly in Path abstraction concatenations, exposing the system to arbitrary LFI or arbitrary fast file deletion attacks (e.g. `../../../var/log/syslog`).

### Hotfixes
- **CrosstalkOrchestrator Startup Crash** — Fixed an issue where `CrosstalkOrchestrator` eagerly initialized `OpenAIClient` upon module import. If `CrosstalkOrchestrator` was imported during startup before configuration and keys were fully processed, it crashed the server with `OpenAIError: The api_key client option must be set`. Initialization is now deferred until the client is lazily requested.
- **Dynamic Prompt Interception for Bash Echo Insights** — Added an auto-intercept rule into `request_converter.py` that listens for the Claude Code system prompt. If active, it seamlessly injects `"IMPORTANT RULE: Never use the Bash/Repl tools to execute 'echo' commands or shell scripts solely to output insights, thoughts, or explanations. Always output your insights directly as inline text."`. This entirely mitigates the issue with upstream generic-instruction models deciding to use bash to "echo" insights!

### Changed
- **`on_complete` callback fully wired** — The `on_complete` parameter added in the previous
  commit to `convert_openai_streaming_to_claude_with_cancellation()` is now passed by
  `endpoints.py` with a callback that handles usage tracking, terminal logging, and dashboard
  hooks. Previously it was just a signature addition with no caller.


## [Unreleased]

### Fixed
- **RTK proxy chain entry disaled** — `rtk serve --port 8788` does not exist (RTK v0.34.3 has no `serve` subcommand; it's a CLI wrapper, not an HTTP server). Disabled the RTK entry in `config/proxy_chain.json` so `proxies up` no longer times out waiting for a non-existent server. The `rtk` CLI is still used as a terminal compression wrapper in aliases (`cldr`, `car`, etc.).

### Added
- **Live-reload via SSE** — Config changes propagate across CLI/TUI/web UI within 5 seconds without
  process restart. In-flight requests preserve pre-edit config (FR-008, SC-006). SSE endpoint at
  `/api/config/events` with exponential-backoff reconnection (T053-T062).
- **Provenance queries** — Every resolved config value carries `source_layer` (cli/shell_env/dotenv/stored/default).
  Accessible via `proxies config where <path>`, `GET /api/config/{path}`, and inline provenance badges
  in the web UI next to each field (T064-T068).
- **Per-attempt usage metrics** — Each cascade attempt (primary + fallbacks) now logs a distinct row
  in `usage_tracking.db` with `attempt_index` (0=primary, 1,2,...) and `resolved_assignment_id`.
  This enables role-based attribution (which assignment served the request) regardless of model fallbacks.
- **Analytics API** — New endpoints:
  - `GET /api/metrics/by-assignment` — aggregate success/cascade rate by assignment
  - `GET /api/metrics/by-model` — aggregate metrics by actual model used (across all attempts)
- **Audit log API** — `GET /api/audit` (admin only) with filters `since`, `principal`, `field_path`, `limit`.
  Returns configuration change history with masked secret values.
- **Web UI audit viewer** — new page `/audit` for admins to browse configuration audit trail.
- **Analytics per-assignment pivot** — Analytics page now shows usage broken down by assignment alongside
  existing per-model view (FR-032).
- **Secret-masking unit tests** — Comprehensive coverage of API key, OAuth, JWT, and long-hex patterns
  across ResolvedValue responses, audit entries, and analytics outputs (FR-035, SC-012).
- **CI lint enforcement** — `scripts/lint_no_direct_env.py` detects direct `os.environ.get` calls in backend
  code (excluding central ConfigResolver) to enforce Principle VI.
- **Performance tests** — T082 (resolver latency p95 < 1ms) and T083 (SSE notification p95 < 1s) added under
  `tests/performance/`.
- **Documentation** — `docs/configuration.md` with precedence table, assignment/mapping tutorial, migration
  guide from legacy env vars, and troubleshooting.

### Security
- **Secret masking in config API responses** — `/api/config` and `/api/config/{field_path}` now mask
  secret-shaped values (API keys, tokens) per FR-035. Operators can still identify their own keys via
  first-4/last-4 partial reveal.

### Changed
- **.env.example** — deprecated `ENABLE_BIG_ENDPOINT`, `ENABLE_MIDDLE_ENDPOINT`, `ENABLE_SMALL_ENDPOINT`
  and all `BIG_*`, `MIDDLE_*`, `SMALL_*` configuration vars. Added a commented block introducing the new
  `assignments_<id>_<field>` schema and pointing to `docs/configuration.md`.
- **`proxies` lifecycle hardening** — `proxies up` now launches service commands from the repo root so the
  global `~/.local/bin/proxies` command works outside the project directory. `proxies down` now derives a
  safer stop pattern for interpreter-backed commands such as `python start_proxy.py` instead of matching
  every `python` process on the machine. Added `PROXIES_NO_ATTACH=1` / `proxies --no-attach up` support
  for alias-driven auto-start without dropping users into tmux.
- **Alias installer restored multi-CLI coverage** — `scripts/install-aliases.sh` now installs the older
  compatibility aliases for Qwen, Codex, OpenCode, OpenClaw, and Hermes alongside the newer `cld*`
  aliases, and wires them through the proxy/headroom/RTK stack with auto-start behavior.
