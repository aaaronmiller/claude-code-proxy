# Claude Code Proxy — Status & TODO (2026-04-16)

> 🧹 **MAINTENANCE REMINDER**: Periodically move all completed `DONE` items from this TODO document directly into the `CHANGELOG.md` to keep both files current and keep this task list free of clutter and debris.
> **Working tree**: Clean (all changes committed in `23fbe86`)
> **Branch**: `main`, up to date with `origin/main`
> **Proxy status**: Running on `:8082` (healthy), Headroom on `:8787` (healthy)

---

## What Just Got Done (commit `23fbe86` — "compression proxies")

This was a massive 32-file, 4,513-insertion commit covering four major areas:

### 1. Option C Reasoning Handling (`src/services/conversion/response_converter.py`)
**Problem**: Upstream models (Qwen, DeepSeek, etc.) emit `reasoning_content` / `thinking` tokens in their responses, but Claude Code clients may not have requested extended thinking. Previously, this caused silent stream stalls — the client waited for text content while the proxy buffered unrequested reasoning.

**Solution** (implemented in both `convert_openai_streaming_to_claude` and `convert_openai_streaming_to_claude_v2`):
- If client **requested** thinking (`original_request.thinking is not None`): emit reasoning as native thinking blocks (unchanged behavior)
- If client **did NOT** request thinking ("Option C"):
  - Tee full reasoning text to a log file at `~/.cache/claude-code-proxy/reasoning/<message_id>.log`
  - Emit a liveness heartbeat into the text stream: first `"💭 thinking"`, then a dot `.` every 1.5s or 400 chars
  - When real text content arrives, emit `\n\n` to break away from the heartbeat line
- Also added: **upstream error detection in stream chunks** — OpenRouter forwards 429/500 errors as chunks with an `"error"` field. Now detected and surfaced as `event: error` SSE instead of silently stalling.
- Added `on_complete` async callback parameter for stream lifecycle metrics (duration_ms, usage, stop_reason, error).

### 2. Proxies CLI Expansion (`proxies` script — +965 lines)
New subcommands added to the `proxies` bash CLI:

| Command | What it does |
|---------|-------------|
| `proxies stats` | Usage summary from `/api/stats`: requests, tokens, cost, latency, RTK savings |
| `proxies config show\|set\|toggle\|order\|add\|rm\|env` | Full proxy chain management without TUI |
| `proxies router show\|set\|clear\|disable\|enable\|passthrough` | Model routing management |
| `proxies metrics summary\|models\|tools\|daily` | Detailed usage metrics from API endpoints |
| `proxies statusline` / `proxies sl` | TUI for building Claude Code status line segments |
| `proxies watch` | Rich-based watch dashboard (from `a2eb3fa`) |

Tmux status bars now configured by `proxies up` — per-pane labels + bottom status showing live proxy/headroom/RTK metrics via `scripts/tmux_status.sh`.

### 3. Status Line System (new files)
| File | Purpose |
|------|---------|
| `scripts/statusline_segments.sh` | 23 reusable segment renderers (`seg_<id>`) with self-describing `seg_list` |
| `scripts/statusline_render.sh` | Universal renderer: reads CC stdin JSON + config, emits ANSI 2-line output |
| `scripts/cc_statusline_metrics.sh` | Sourceable functions for proxy metrics, 5s cached API calls |
| `scripts/tmux_status.sh` | Tmux status bar integration |
| `src/cli/statusline_tui.py` | Textual TUI: toggle/align/reorder 23 segments, live preview, saves config |
| `docs/STATUS_BARS.md` | Integration guide + jitter fix documentation |

### 4. Core Fixes (committed in same batch)
- **OpenRouter `models` array capped to 3** (`src/core/client.py:52`) — OR rejects longer arrays
- **Router disabled/passthrough flags** (`src/core/proxy_chain.py`, `src/core/model_router.py`) — `RouterConfig.disabled` and `RouterConfig.passthrough` short-circuit `ModelRouter.route()` to return `None`. `passthrough` also disables cascade in `openai_endpoints.py`.
- **Self-loop prevention** (`src/core/proxy_chain.py:331-347`) — `_is_local_proxy_entry()` skips the local proxy when deriving upstream URL, preventing `:8082 → :8082` infinite loop.
- **Dead model cleanup** — `stepfun/step-3.5-flash:free` (404 on OpenRouter) replaced with `nvidia/nemotron-nano-9b-v2:free` across all configs.
- **Model limits fixed** — Added correct context/output limits for 6 active free models + set reasonable defaults for 114 models that had `output: None`.
- **`max_tokens` capping** (`src/services/conversion/request_converter.py`) — caps output tokens to model's actual output limit instead of blindly passing through.

---

## Remaining TODO / Known Issues

### Audit Pass — 2026-04-16 (post-commit `23fbe86`)

Functional audit of the CHANGELOG entries vs. actual code state. Findings + fixes applied in this pass:

**Verified working (no action needed):**
- `on_complete` streaming callback wired in `endpoints.py:693-762` → `response_converter.py:1608-1614`
- `_extract_session_fingerprint` replaces `request_id[:8]` for session grouping (`endpoints.py:664`)
- `_QuietPollFilter.addFilter()` replaces the broken `dictConfig` path (`main.py:624-625`)
- Circuit breaker registry delegation in `client.py:20-38` (`_get_circuit_breaker`, `_is_cb_open`)
- RBAC auth bypass fix: `users_rbac.py:81` now calls `user_service.authenticate()`
- `admin123` removal + `PROXY_DEFAULT_ADMIN_PASSWORD` / `secrets.token_urlsafe(16)` fallback (`user_management.py:656-658`)
- `validate_safe_filename` applied across 6 profile/crosstalk endpoints in `web_ui.py`
- `CrosstalkOrchestrator._get_or_create_client()` lazy init (`crosstalk.py:68-79`)
- Reasoning heartbeat + tee-to-disk + upstream-error detection in both `convert_openai_streaming_to_claude` and `..._with_cancellation`
- Model rankings cron **is** installed (prior audit gave a false negative — `grep` is aliased to `rg` which handled `\|` differently; the entry `0 */6 * * * cd /home/cheta/code/claude-code-proxy && .venv/bin/python tools/refresh_model_rankings.py --force ...` was already present)

**Fixed in this pass:**
- **API key slice leak** — CHANGELOG claimed `client.py` was reduced to `[:8]`, but 4 debug logs still exposed `[:20]` or `[:10]` of live tokens (lines 131, 157, 163, 351, 491). All reduced to `[:8]`.
- **Claude Code system-prompt match too broad** — `request_converter.py:305` previously fired on `"claude" in system_text.lower()`, which triggers on any unrelated mention of "claude" (URLs, doc references, model names in other system prompts). Tightened to three disjoint strong markers: `"You are Claude Code"`, `"claude-code"`, or `"Anthropic's official CLI"`.
- **Reasoning log unbounded growth** — Added a non-blocking startup prune in `main.py` that removes `~/.cache/claude-code-proxy/reasoning/*.log` files older than 7 days. Runs once per server start; silently skips on any OSError.

**Still outstanding (not fixed here):**
- **API key slice leak (broader scope)** — The same `[:20]` / `[:15]` / `[:10]` pattern exists in `src/services/antigravity.py` (3 sites), `src/services/logging/startup_display.py` (2 sites), `src/cli/advanced_config.py` (2 sites), `src/core/validator.py` (3 sites), `src/api/endpoints.py` (5 sites). Not part of the `23fbe86` commit scope; flag for a follow-up security pass.
- **Option C heartbeat runtime test (item C below)** — still needs live proxy restart + a reasoning-model request to confirm the heartbeat dots actually surface to the client. Code path is correct; runtime behavior unverified.
- **Duplicated reasoning logic** in `convert_openai_streaming_to_claude` and `..._with_cancellation` — still listed under LOW PRIORITY below.

---

### HIGH PRIORITY

#### C. Test the Option C Reasoning Heartbeat
After proxy restart, test with a model that emits `reasoning_content` (e.g., `qwen/qwen3-235b-a22b:free`). Verify:
1. When CC client does NOT request thinking: heartbeat dots appear, reasoning logged to `~/.cache/claude-code-proxy/reasoning/`
2. When CC client requests thinking: native thinking blocks still work
3. Stream error detection: force a 429 and verify the error event is surfaced



#### A. Architecture Overhaul (Migrating from Proxy Chain JSON to Declarative YAML)
The core proxy lacks structured fingerprint routing, relying on string-checks that couple code directly to provider naming conventions. 
This is being addressed in the `implementation_plan.md` artifact via a 6-step incremental rollout.
**Status**: Plan approved by user (`env > yaml`, `permissive` matching). Development has begun. 
**Execution Tracking**: All progress and specific sub-tasks are actively tracked in `task.md`.

*Note: The `CrosstalkOrchestrator` startup crash (`OpenAIError` due to eager client instantiation) has been fixed and documented in the CHANGELOG. All prior Phase 1 logging, duplication, security, and path traversal bug fixes have also been completed and officially patched.*

---

## 🏛️ EXPANDED ARCHITECTURAL IMPLEMENTATION PLAN: PROXY V2 MIGRATION
*Generated via meticulous source code analysis to outline the structural ramifications of the V2 migration.*

The `claude-code-proxy` is shifting from a state where logic is organically spread across environment variables, JSON arrays, and deeply nested string-matching heuristics into a state driven entirely by declarative YAML schemas, HTTP headers, and dynamic plugin resolution. This requires touching the very core of how requests are marshaled, translated, and dispatched within the server architecture.

### OVERVIEW: THE WHY & THE HOW
Currently, if a user queries the proxy using Claude Code, the request traverses `src/api/openai_endpoints.py`. The endpoint attempts to infer the target provider by applying `.split("/")` and literal string matches (e.g., `if "gemini" in model_name`). Downstream, `request_converter.py` applies hardcoded "IF provider == X" gates to modify JSON schema representations of Tool usages. This coupling means adding a single new backend provider (like DeepSeek or Kiro) requires modifying 6+ core proxy files. 

This migration decouples **Request Characteristics** (the IDE calling the proxy) from **Upstream Capabilities** (what the target model supports), linking them via an agnostic `config/proxy.yaml` definitions file and a Plugin Engine.

Below is the exhaustive file-by-file action plan, ordered sequentially by intended implementation milestones.

---

### Step 1: Consolidate Configuration (The YAML Source of Truth)
**Current Method**:
The proxy bootloads in `src/core/config.py` by scanning `os.environ` for over 50 permutations of legacy variables (e.g., `OPENAI_API_KEY`, `BIG_CASCADE`, `ROUTER_LONG_CONTEXT_THRESHOLD`), interspersed with a legacy `proxy_chain.json` loader `src/core/proxy_chain.py` that handles CLI wrapper configurations. These two sources often fight for precedence, causing confusion over whether the `.envrc` or the `proxy_chain.json` holds the ultimate authority.

**The Ramification / Reason for Change**:
Config validation is duplicated. Type coercion is handled via manual `int()` and `.lower() == 'true'` checks, prone to parsing crashes. A unified YAML file (`proxy.yaml`) eliminates this entirely, allowing complex nesting (like arrays of model cascades or nested Router profiles) while maintaining `ENV > YAML` precedence via the standard `pydantic-settings` or `deepmerge` pattern.

**Files Regulated & Actions:**
1. **`config/proxy.yaml`** `[NEW]`
   - **Action**: Create the root schema defining `ingress` (host/port), `chain` (the proxy wrappers), `clients` (API keys & fingerprint matching rules), `profiles` (model tiering), and `transforms` (plugins).
2. **`requirements.txt` / `pyproject.toml`** `[MODIFY]`
   - **Action**: Inject `pyyaml` and `deepmerge` bindings.
3. **`src/core/config.py`** `[MODIFY]`
   - **Action**: Gut out lines 105-650 (the manual `os.environ.get` spaghetti). Implement a `load_yaml` pipeline that merges against `os.environ` keys starting with `PROXY__*`. Re-map properties (e.g., `self.big_model` becomes `self.get_profile('default').big_model`).
4. **`src/core/proxy_chain.py`** `[MODIFY]`
   - **Action**: Gut the JSON parser `ProxyChain.load()`. Refactor `ProxyChain` to instantiate directly from the `chain:` block passed heavily loaded from `src/core/config.py`.

---

### Step 2: Client Fingerprinting & Context Awareness
**Current Method**:
Any incoming HTTP payload to `/v1/chat/completions` is treated equally. If Claude Code hits the endpoint, it gets the exact same middleware pipeline as if Cursor or a raw `curl` script hits it. The only way the proxy knows it's Claude Code is via `detect_ide()` mapping user-agents, but the proxy currently hardcodes behaviors based on this detection instead of allowing configurable profiles.

**The Ramification / Reason for Change**:
We want different clients to experience different model logic natively. Claude Code should ride the `headroom` token compressor natively, while Cursor should bypass it to preserve full file representations. By implementing YAML-based fingerprinting, the proxy natively links a Client's identifying Header (`User-Agent: claude-code*`) to a `profile_id`.

**Files Regulated & Actions:**
1. **`src/api/openai_endpoints.py`** `[MODIFY]`
   - **Action**: Modify `openai_chat_completions` signature. Extract `request.headers`. Create a `ClientContext` object by passing the headers to a new `ContextResolver` service. 
2. **`src/core/client_matcher.py`** `[NEW]`
   - **Action**: Implement permissive matching loop: iterate over `config.clients[]`. If `headers['User-Agent']` regex matches a defined client's `fingerprint`, return that client's `profile`. If no matches exist, safely fallback to the `default` profile.

---

### Step 3: Per-Request Profile Chains (Dynamic Sub-chains)
**Current Method**:
The `proxy_chain.py` evaluates the `proxy_chain.json` at boot time and establishes a rigid topology (`:8082 -> :8787 -> openrouter`). If a request hits the system, it traverses the full chain regardless of the task, unless manually aborted by a global `--passthrough` CLI flag.

**The Ramification / Reason for Change**:
Hard static chains waste compute. If the matched Client Profile explicitly demands a direct connection to OpenRouter (e.g., a massive context upload via Qwen), forcing it through the `headroom` intermediate proxy bottlenecks performance and tokenizes data unnecessarily. Profile Chains enable dynamic hop skipping.

**Files Regulated & Actions:**
1. **`src/core/proxy_chain.py`** `[MODIFY]`
   - **Action**: Alter `get_chain().upstream_url()`. Instead of returning the first active entry statically, accept the `ClientContext.profile`. Filter the active chain hops by `if profile.name in hop.allowed_profiles`. If the hop is bypassed, return the secondary upstream destination.

---

### Step 4: Dialect-Agnostic Ingress Routing
**Current Method**:
The system maps APIs purely by explicit matching endpoints: `/v1/messages` exclusively handles Anthropic syntax, while `/v1/chat/completions` exclusively handles OpenAI syntax. 

**The Ramification / Reason for Change**:
This is brittle. Many modern tools (like Google SDKs) send Anthropic-shaped blobs to OpenAI-branded router paths, or vice-versa. Endpoints should act organically as data ingests, determining their routing trajectory by examining the structural taxonomy of the body payload (`messages[]` roles, `contents` vectors) rather than trusting the arbitrary URL suffix utilized by the IDE.

**Files Regulated & Actions:**
1. **`src/api/dispatcher.py`** `[NEW]`
   - **Action**: Create a universal `/v1/dispatch` POST receiver. Read the raw stream. If `.get('contents')` exists, flag it internally as Anthropic-dialect. If `.get('messages')` exists, flag as OpenAI-dialect.
2. **`src/api/openai_endpoints.py` & `src/api/anthropic_endpoints.py`** `[MODIFY]`
   - **Action**: Deprecate strict path routing validation. Instead of exploding with HTTP 400 when an OpenAI-shaped body hits `/v1/messages`, transparently hand the body to the internal cross-compiler and proceed with generation.

---

### Step 5: Plugin Transform Registry (The Engine)
**Current Method**:
`src/services/conversion/request_converter.py` is an 800+ line monolith. It features huge procedural blocks containing logic for completely segregated paradigms:
- `if provider == "gemini"` -> Modify tool schemas to replace `type: object`
- `if effort == "high"` -> Inject `extra_body` thinking nodes
- `if option_c_active` -> Splice `event: heartbeat` SSE ticks.

**The Ramification / Reason for Change**:
Procedural conversion functions create "God Classes" that explode tracking states. A Plugin Engine isolates these modifications into single-responsibility objects (`JSONCoercePlugin`, `HeartbeatPlugin`), which are dynamically loaded strictly based on the capabilities advertised by the upstream provider.

**Files Regulated & Actions:**
1. **`src/plugins/transforms/`** `[NEW FOLDER]`
   - **Action**: Scaffold `plugin_base.py` containing an `AbstractTransform`. Create `reasoning_heartbeat.py`, `tool_name_normalize.py`, and `json_type_coerce.py` executing isolated `transform_request()` and `transform_response_chunk()` capabilities.
2. **`src/services/conversion/request_converter.py`** `[MODIFY]`
   - **Action**: Delete the hardcoded behavior logic. Replace it with `PluginEngine.apply_transformers(request, capability_matrix)`.
3. **`src/services/conversion/response_converter.py`** `[MODIFY]`
   - **Action**: Delete the manual `. (dot)` heartbeat threading block inside the chunk loop. Yield execution exclusively to `PluginEngine.apply_stream_transformers()`.

---

### Step 6: Upstream Dispatcher & Dynamic Probing
**Current Method**:
When a client asks for `google/gemini-pro`, the proxy relies on `src/services/providers/provider_detector.py` calling `.lower().startswith('google/')` to string-match and blindly assume the endpoint has Google-specific schema capabilities.

**The Ramification / Reason for Change**:
New models release daily. A user attaching `meta-llama/llama-3.4` via an unfamiliar proxy host shouldn't fail simply because the literal string `"llama"` wasn't written into our source code `if` checks. The proxy must implement Upstream Probing—caching a lightweight OPTIONS/GET request against the upstream URL to detect `supported_features` (e.g., tool_use, streaming, option_c_native) at boot/first-run.

**Files Regulated & Actions:**
1. **`src/services/providers/capability_cache.py`** `[NEW]`
   - **Action**: Build an async SQLite/JSON store tracking model capability maps.
2. **`src/services/providers/provider_detector.py`** `[MODIFY]`
   - **Action**: Delete the name-matching array dictionary. Replace with dynamic network probes fetching `GET /v1/models` against the designated OpenRouter/VibeProxy backend to extract capability definitions. If a probe fails, fallback safely to standard OpenAI formatting equivalents.

### CONCLUSION
This implementation plan serves as the definitive roadmap for the agent orchestration. Once strictly executed, the system will support indefinite new providers and local models purely via YAML updates, without requiring systemic Python source modification ever again.
### MEDIUM PRIORITY

#### E. Web UI Chain Management Page
- **File**: `web-ui/src/routes/chain/` (if it exists, or needs creation)
- The CHANGELOG mentions a chain management UI at `/chain` but verify it's functional
- API endpoints `GET/PUT /api/proxy-chain` and `GET/PUT /api/router-config` should already exist in `src/api/web_ui.py`

#### F. Statusline TUI Polish
- `src/cli/statusline_tui.py` — verify it launches cleanly: `proxies sl`
- Check that `~/.claude/statusline-config.json` is created correctly after saving
- Verify the renderer `scripts/statusline_render.sh` works with CC's actual stdin JSON format

#### G. Model Rankings Refresh Cron — SCRIPT EXISTS, NO CRON
- **File**: `tools/refresh_model_rankings.py` — EXISTS, verified
- Should run every 6h to refresh `data/free_model_rankings.json`
- **No crontab entry** — confirmed via `crontab -l`. Need to add:
  `0 */6 * * * cd /home/cheta/code/claude-code-proxy && .venv/bin/python tools/refresh_model_rankings.py`

#### H. Tmux Status Bar Testing
- After `proxies up`, verify tmux status bars render correctly
- `scripts/tmux_status.sh` should show proxy health (left) + headroom/RTK stats (right)
- Check for issues with `pane-border-status` on the current tmux version

#### I. Web UI Overhaul + Feature Parity (Prompt 7-8, 40)
**Original request** (2026-03-29, Session `8fba7926`): "update and fix the fucking web/ux —
use the frontend design masterclass, restyle with 3 color themes, microanimations, metrics
for usage, feature parity with the TUI esp. model selection + showing available model
characteristics from OpenRouter."

**Later expanded** (Prompt 40, 2026-04-14): ALL features should be configurable via CLI args,
TUI, AND web UI. CLI args are the base layer; TUI and web UI act as wrappers. Web UI should
have setup section + analytics dashboard. Referenced "claude code swap" and "claude code mux"
as examples.

**Status**: Partially done. Web UI has `/chain` page (API endpoints exist), but:
- 3 themes were added (Midnight Aurora, Ember Console, Synthwave Minimal) — verify functional
- Model selection from web UI — unclear if complete
- Analytics dashboard in web UI — needs verification
- Feature parity audit: CLI `proxies config/router/metrics` vs web UI equivalents
- **File**: `web-ui/src/routes/` — check what pages exist and which are functional

#### J. Unified Config Architecture (Prompt 54, 56)
**Request** (2026-04-15): env/arg-based config as base layer, TUI + web UI as wrappers.
User decided: YAML format, env > file precedence, permissive model handling (new models
should pass through without breaking, new API features get passthrough, breaking changes
well-logged for diagnosis).

**Status**: Partially implemented. `.envrc` + `config/proxy_chain.json` exist but:
- No YAML config file yet (user requested YAML over JSON)
- Passthrough for unknown model features — verify this works
- New API features (e.g., new Anthropic fields) — check if unknown fields pass through
  or get stripped by request/response converters

#### K. Realtime Page Completion (Prompt 56)
**Request** (2026-04-15): "finish the realtime page" — this was the last instruction before
the session ended. Lucide-Svelte icon imports were broken (Tool → Wrench, Cache → HardDrive
fix applied in prompt 41 context).

**Status**: Fix was committed (`web-ui/package-lock.json` change in `23fbe86`). Verify:
- `web-ui/src/routes/realtime/+page.svelte` renders without errors
- Build the web UI: `cd web-ui && npm run build`
- Icons display correctly

#### L. Infinite Lag / Stream Stall Issue (Prompts 45-51)
**Symptom** (2026-04-15): User started proxy via `proxies up`, ran `cproxy-continue`, sent
"hello" — response took 3m15s+ (cancelled). minimax model, first request of day, quota fine.
Proxy logged a 200 OK for the POST but client saw nothing.

**Root cause**: This is the exact problem Option C reasoning handling was built to fix — the
upstream model was emitting `reasoning_content` that the proxy wasn't forwarding to the client,
causing an apparent hang. Option C (heartbeat dots during thinking) is now committed but
**needs proxy restart to activate**.

**Verification**: After proxy restart, repeat the test — send a simple message through minimax
and confirm heartbeat appears if the model reasons.

#### M. Dependabot Security Fixes (Prompt 6, Session `486a2843`)
**Request** (2026-03-30): "address all of https://github.com/aaaronmiller/claude-code-proxy/security/dependabot"
**Status**: Commits `3cbb35a` and `a30dadd` addressed Dependabot alerts, plus PR #13 for lodash-es.
Verify: `gh api repos/aaaronmiller/claude-code-proxy/vulnerability-alerts --jq length` or check
GitHub security tab for any remaining alerts.

#### N. Circuit Breaker Persistence + Soft Failures — LOST IN CRASH
**Designed in session** (Prompt 17 context, 2026-04-08) but **NEVER COMMITTED** — confirmed
by grep: zero matches for `record_soft_failure`, `record_parse_ok`, `_load_persisted_state`
in `src/core/circuit_breaker.py`. Also `data/circuit_breaker_state.json` does not exist.

**What needs implementing** (from session summary):
- `_load_persisted_state()` / `_save_persisted_state()` → `data/circuit_breaker_state.json`
- `soft_failure_count` field on `CircuitBreakerStats`
- `record_soft_failure()` — every 2 soft failures triggers 1 hard failure recording
- `record_parse_ok(response: dict)` — checks non-empty choices, valid finish_reason, content present
- `record_stream_finish(finish_reason, had_tool_calls, had_content)` — streaming equivalent
- `to_persist_dict()` / `from_persist_dict()` for serialization
- Load state on startup, `save_all()` method for periodic persistence
- **File**: `src/core/circuit_breaker.py`
- **Reference**: Full spec in USERPROMPTS-v2.md lines 3421-3431

#### O. Macdrive Script (Prompt 38)
**Request** (2026-04-14): Check `/code/scripts` macdrive script, make it mount any external
drive regardless of partition type (currently handles APFS, goal: hands-free auto-mount of
any drive on WSL2).
**Status**: Unknown — this was a side request during the proxy session. Likely not done.
Not proxy-related but was requested in this project's session.

### LOW PRIORITY / FUTURE

#### I. Response Converter Duplication
The Option C reasoning logic is duplicated between two functions:
- `convert_openai_streaming_to_claude()` (line ~696+)
- `convert_openai_streaming_to_claude_v2()` (line ~1097+)

Consider extracting shared reasoning handling into a helper to reduce maintenance burden. Both functions have identical heartbeat/tee/error-detection logic.

#### J. Reasoning Log Rotation
Reasoning logs at `~/.cache/claude-code-proxy/reasoning/` will grow indefinitely. Add:
- A cron job or startup task to prune logs older than 7 days
- Or configure `logrotate` for the directory

#### K. CLIProxyAPI Re-evaluation
- `cliproxyapi` entry in `proxy_chain.json` is disabled (Google TOS banning concerns)
- If Antigravity project status changes, re-enable and update model defaults:
  - BIG_MODEL → `gemini-3.1-pro-high`
  - MIDDLE_MODEL → `gemini-3-flash`
  - SMALL_MODEL → `gemini-3.1-flash-lite`

#### L. Install Script GPU Detection
- `install-all.sh` has GPU auto-detection for NVIDIA/Intel Arc/AMD/CPU
- Intel Arc A370M (user's GPU) should be detected — verify with `proxies status`
- Headroom config passes `--backend openrouter` — may want GPU-accelerated local backend in future

---

## Architecture Quick Reference

```
Claude Code Client
    │
    ▼
RTK (cli_wrapper — terminal output compression, not a network proxy)
    │
    ▼
Claude Code Proxy (:8082)  ◄── THIS PROJECT
    │  ├─ Model Router (per-use-case routing: background, think, long_context, image, web_search)
    │  ├─ Cascade fallback (circuit breaker, exponential backoff, dynamic model list)
    │  ├─ OpenRouter native fallback (inject `models` array for OR endpoint selection)
    │  └─ Response conversion (OpenAI SSE → Claude SSE, with Option C reasoning handling)
    │
    ▼
Headroom Compression (:8787)  ◄── context/token compression proxy
    │
    ▼
OpenRouter API (openrouter.ai/api/v1)  ◄── routes to free models
```

### Key Files Map
| Area | Files |
|------|-------|
| **Entry point** | `start_proxy.py` |
| **API endpoints** | `src/api/openai_endpoints.py`, `src/api/web_ui.py` |
| **Request conversion** | `src/services/conversion/request_converter.py` |
| **Response conversion** | `src/services/conversion/response_converter.py` |
| **Proxy chain config** | `src/core/proxy_chain.py`, `config/proxy_chain.json` |
| **Model routing** | `src/core/model_router.py` |
| **HTTP client / cascade** | `src/core/client.py` |
| **Config loading** | `src/core/config.py` |
| **Circuit breaker** | `src/core/circuit_breaker.py` |
| **Model catalog** | `src/services/models/model_catalog.py` |
| **Model limits** | `src/services/usage/model_limits.py`, `data/model_limits.json` |
| **CLI (bash)** | `proxies` (main CLI script) |
| **CLI TUIs** | `src/cli/chain_tui.py`, `src/cli/statusline_tui.py` |
| **Status line scripts** | `scripts/statusline_*.sh`, `scripts/tmux_status.sh`, `scripts/cc_statusline_metrics.sh` |
| **Environment config** | `.envrc` (sourced by direnv) |
| **Installer** | `install-all.sh` |

### Active Free Models (as of 2026-04-16)
| Model | Role | Context | Output |
|-------|------|---------|--------|
| `minimax/minimax-m2.5:free` | BIG_MODEL, long_context | 196K | 16384 |
| `nvidia/nemotron-3-super-120b-a12b:free` | MIDDLE_MODEL | 131K | 16384 |
| `nvidia/nemotron-nano-9b-v2:free` | SMALL_MODEL, background | 131K | 16384 |
| `qwen/qwen3-235b-a22b:free` | Cascade fallback | 131K | 8192 |
| `openai/gpt-oss-120b:free` | Cascade fallback | 131K | 16384 |
| `qwen/qwen2.5-vl-72b-instruct` | Image routing | 131K | 8192 |

### Fallback Order
1. **OpenRouter native**: injects `models` array (max 3 entries) → OR picks fastest healthy endpoint
2. **Cascade**: proxy-level retry with circuit breakers → cycles through `BIG_CASCADE` / `MIDDLE_CASCADE` / `SMALL_CASCADE` + dynamic models from `data/free_model_rankings.json`
3. Both methods enabled by default (`FALLBACK_METHOD=cascade,openrouter_native`)
