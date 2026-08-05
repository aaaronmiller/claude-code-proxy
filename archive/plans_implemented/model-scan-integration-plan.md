---
date: 2026-05-30 16:08:12 PDT
ver: 1.2.0
author: claude-code-proxy-worker
model: claude-opus-4-8
tags: [model-scan, routing, integration, cascade, selection-policy, quicklaunch, ante, quota-rotation, lanes, observability]
---

# Model-Scan Integration Plan (claude-code-proxy <- model-scan)

## Conclusions First

1. **Use a published file contract, not a request-time API.** model-scan writes a
   versioned `routing_snapshot.json`. The proxy reads it at startup, on SIGHUP, and on
   a TTL. The proxy never hard-depends on model-scan being up. A live gateway pull is a
   bonus for the dashboard and manual refresh only, never on the request hot path.
2. **One mapping file, layered like the existing overlays.** A global default
   `slot_bindings` plus per-profile overrides, stored in `profiles.json` next to the
   `tier_overrides` it mirrors. No new top-level config concept.
3. **Cascade from the snapshot is the single highest-value win.** Every cascade in
   `proxy_chain.json` is currently empty. model-scan already ranks candidates per slot.
   Populating cascades from the snapshot makes fallback dynamic and availability-aware
   for the first time.
4. **Ship the shared contract first, then export, then consumer, then quicklaunch.**
   Order is contract -> model-scan export -> proxy binder -> aliases/launcher -> ante.
5. **"Best free / best under $X / best for role" is one selection policy knob.** It
   resolves against the snapshot at bind time using slot `eval_mode` and `price_blended`
   that model-scan already produces. Policies: `static`, `free`, `budget:<ceiling>`,
   `quality`, `roles`.
7. **Quota-aware rotation is built native in the proxy on the existing substrate.** The
   proxy already has `rate_limiter` (per-model quota-scored fallback), `usage_tracker`
   (per-provider usage with JSON export), and `billing_integrations` (provider balances).
   Rotation consumes these rather than reinventing them. External subscription quota the
   proxy cannot see is ingested through a pluggable `QuotaSource` adapter layer: tokscale
   primary (broadest coverage of the actual tool set), ccusage secondary (stable `--json`).
   We adopt the rotate-on-429 pattern natively and reject gpt-load and LiteLLM as components
   (they would duplicate the proxy and add a hop).
8. **Lanes express the free-vs-S-tier split.** A `standby` lane (free only) serves the
   24/7 agents and never touches premium quota; an `interactive` lane (quota-aware S-tier
   rotation) serves the CLI tools, keeps the primary on S-tier within remaining weekly
   quota, and forces toolcalling to free models.
9. **One command, with a visible monitor.** `ccp up` spawns a terminal window running the
   tmux panes (Headroom ratios, proxy, clip), then `ccp <tool>` launches sessions. Every
   session, log, error, and metric is tagged with the session id for one-place tracing.

6. **The two projects stay separate and complementary.** model-scan owns scoring and
   the snapshot. The proxy owns routing and consumption. The only coupling is the
   `routing_snapshot.json` schema, which is versioned and validated on both sides.

---

## Audit Findings

### claude-code-proxy (the consumer)

Request resolution chain (verified in source):
`/p/{profile}/v1/messages` (endpoints.py:393) -> `convert_claude_to_openai` ->
`ModelRouter.route()` (model_router.py:283) -> profile overlay block
(endpoints.py:567 to 648) -> cascade in client.py.

Key structures that already fit:

- `Assignment` (core/assignments.py): `(id, kind, model, provider, base_url, api_key,
  enabled, cascade)`. `kind` is `tier` (big/middle/small) or `slot` (operator-defined,
  regex `^[a-z][a-z0-9_]{0,63}$`). `AssignmentRegistry` is a live-mutable CRUD facade that
  persists to `proxy_chain.json` and pushes updates into `config_resolver` so readers see
  changes immediately. This is the natural write target for model-scan-resolved models.
- `ModelRouter.route()` resolves use cases in priority order: IdentifierMapping, custom
  router, image, toolcall, web_search, long_context, think, background, default. Each
  returns a `RouteTarget(model, base_url, api_key, assignment_id)`.
- Profile overlays (profiles/profiles.json): `toolcall_models` (cascade list),
  `web_search`, `force_main`, `tier_overrides` (per-tier model swap), `provider_override`.
  Applied as pure overlays after the router runs. `tier_overrides` is the exact pattern to
  copy for slot bindings.
- Existing model-data consumer: `services/models/free_model_rankings.py` plus a large
  `services/models/*` suite (model_ranker, recommender, cost_lookup, provider_models).
  The proxy already builds and caches a `data/free_model_rankings.json`. model-scan is a
  superior replacement source for this data.
- Current `proxy_chain.json`: all three tiers hardcoded to
  `nvidia/nemotron-nano-9b-v2:free`, all cascades empty. This is the gap.
- Launch surface: `scripts/install-aliases.sh` builds an idempotent alias block. Invariant
  is that every alias routes through proxy:8082 then headroom:8787 then provider, wrapped
  by rtk. Profiles are selected by URL prefix `http://127.0.0.1:8082/p/{profile}/v1`.
  Existing aliases cover claude (cc/ccc/cldo), qwen (qw), codex (codex-run), opencode
  (oc/ocl), hermes (hsi/hsi-bp), pi (psi/psi-bp). No ante alias yet.

### model-scan (the producer)

- Output today: `~/.config/model-scan/gold_standard/gold_standard_{scan_id}.json`. Shape
  per slot: `requirements`, `candidates_count`, `top_3`, `primary`, `fallback_1`,
  `fallback_2`, each entry carrying `model_id`, `provider`, `composite`, 4-axis `scores`,
  `gates_passed/failed`, `qualified`. This is 90 percent of the contract already.
- Slot definitions: `~/.config/model-scan/slot_definitions.yaml`. Slots R1_primary,
  R6_compression, R7_vision, R8_web_extract, R9_session_search, R10_approval,
  R11_flush_memories, R12_delegation, R_mcp, R_skills_hub (10 slots total). Each has
  `eval_mode: cost_basis|free`, gates (`min_tier`, `min_iq`, `min_tc`, `needs_tools`,
  `needs_vision`, `min_ai`, `min_tps`, `max_latency_s`, `min_ctx_k`) and axis weights.
- Gateway (FastAPI, gateway.py): already exposes `GET /route?slot=R1_primary` returning
  `{slot, label, eval_mode, best, candidates[]}` where each candidate carries `model_id`,
  `provider`, `api_model`, `tier`, `fitness`, `tps`, `latency_s`, `has_tools`,
  `has_vision`, `arch`, `price_blended`, `iq`, `tc`. Also `/health`, `/models`, `/quota`,
  `/configs`, `/swap`. The request-time data the proxy needs is already a one-line query.
- Cost data: `price_blended` per model in the DB and in `/route` candidates. This is the
  field that powers `budget:<ceiling>`. `blocklist.yaml` and `tiers.yaml` already encode
  quality gates (satisfies the D-tier rule without new code in the proxy).
- Scheduling: `cron_manager.py` exists. Scans run daily or on demand and write the
  gold_standard artifacts.

### ante-spec (new launch target)

Ante is a ~15MB Rust agent runtime, local-first, low-RAM, with its own rule-based
"Dynamic Model Router" (complexity classifier picking cheapest-adequate vs most-capable),
MCP client, hooks, and `ante -p` headless mode plus `ante serve` / `ante gateway`. It
brings-your-own-key and supports 12+ providers. For our stack it becomes another OpenAI
or Anthropic style client pointed at the proxy, with a low-RAM-biased profile that
prefers fast free models and leans on headroom compression.

---

## The Four Decisions, Answered

### Q1. File-read snapshot vs live API at request time

**Decision: published file contract is primary; live gateway pull is admin-only.**

Reasons: request-time HTTP to model-scan would add latency and a hard runtime dependency
to the hot path, and the two projects must stay independently runnable. A versioned
`routing_snapshot.json` decouples them by data, not by socket. The proxy loads it into an
immutable in-memory snapshot object at startup, swaps atomically on reload, and degrades
gracefully to the static `proxy_chain.json` values if the file is missing or stale. The
gateway `GET /route` and a new `GET /routing-snapshot` remain available for the dashboard
and for `POST /api/proxy/reload-models` to pull fresh without a filesystem hop.

Restructure note: rather than the proxy reaching into model-scan's private
`~/.config/model-scan/gold_standard/` directory (cross-project filesystem coupling),
model-scan publishes a single stable, documented artifact to a configurable path
(default `~/.config/model-scan/routing_snapshot.json`). The gold_standard files remain
model-scan's internal detail.

### Q2. Per-profile mapping granularity

**Decision: global default plus per-profile overrides, stored in profiles.json.**

A new `slot_bindings` key per profile mirrors `tier_overrides`. A `default` profile holds
the global mapping; other profiles override only what they need. This keeps profile
concerns in the profile file and reuses the existing overlay precedence. It avoids a large
new block in `proxy_chain.json`.

### Q3. Cascade from snapshot

**Decision: yes. The snapshot drives cascades.**

Each slot's ranked `candidates` (minus the chosen primary, minus blocklisted) become the
Assignment `cascade`. This is the largest single improvement because every cascade is
empty today. The proxy's existing circuit breaker and reliability scoring then operate on
a real, availability-ranked fallback chain. Live reliability can feed back into model-scan
later (Phase 5, optional) but is not required for v1.

### Q4. Implementation order

**Decision: contract -> export -> consumer -> launcher -> ante.**

1. Agree the `routing_snapshot.json` schema (shared, versioned, validated both sides).
2. model-scan writes it after every scan (`--emit-snapshot`, and from `cron_manager`).
3. Proxy `ModelScanBinder` consumes it and writes resolved models plus cascades into the
   AssignmentRegistry at startup and reload.
4. Quicklaunch: unified `ccp` launcher plus policy flags, keep existing short aliases.
5. Ante profile and alias.

---

## Target Architecture

```
 model-scan (dink.py / cron_manager)
   |  scan -> score (4 axes + calculus) -> gate (slot_definitions.yaml, blocklist.yaml)
   |  emit -> routing_snapshot.json  (versioned, atomic write)
   |
   |  gateway :8124  GET /route?slot=  GET /routing-snapshot  GET /health   (admin only)
   v
 routing_snapshot.json  (the ONLY coupling between the two projects)
   ^
   |  read at: startup, SIGHUP, TTL expiry, POST /api/proxy/reload-models
 claude-code-proxy
   ModelScanBinder
     - apply SelectionPolicy (static|free|budget:<x>|quality|roles)
     - resolve each tier + slot -> model + provider + base_url + api_key
     - resolve cascade from ranked candidates (blocklist filtered)
     - write into AssignmentRegistry (live), persist to proxy_chain.json optionally
   ModelRouter.route() -> Assignment -> profile overlay (slot_bindings) -> client cascade
```

### routing_snapshot.json (the shared contract)

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-05-30T16:00:00Z",
  "scan_id": 61,
  "slots": {
    "R1_primary": {
      "label": "primary",
      "eval_mode": "cost_basis",
      "best": {
        "model_id": "qwen3.6-plus",
        "provider": "opencode-go",
        "api_model": "opencode_go/qwen3.6-plus",
        "base_url": "https://opencode-go.example/v1",
        "fitness": 76.9,
        "price_blended": 0.0,
        "tier": "A",
        "has_tools": true,
        "has_vision": false
      },
      "candidates": [ { "...": "ranked, same shape as best" } ]
    }
  },
  "provider_health": { "openrouter": "ok", "opencode-go": "ok" },
  "blocklist": ["llama-3.3-70b", "gpt-oss-120b"]
}
```

Notes:
- `api_model` is the proxy-ready `provider/model` string. model-scan derives it so the
  proxy does no provider-prefix guessing (behavior-driven, not hardcoded).
- `base_url` may be empty when the provider is one the proxy already knows from its
  PROVIDERS_* registry. The binder fills gaps from the proxy provider registry.
- `blocklist` is published so the proxy filters consistently with model-scan and with the
  D-tier rule. No model-name allowlists are hardcoded in the proxy.

### SelectionPolicy

A policy resolves, per tier and per bound slot, which snapshot entry to pick:

- `static`: ignore the snapshot, keep `proxy_chain.json` values. Default. Zero dependency.
- `free`: pick the best candidate whose `price_blended == 0` (or slot `eval_mode: free`).
- `budget:<ceiling>`: pick the best candidate with `price_blended <= ceiling`.
- `quality`: pick the best candidate regardless of price (slot `eval_mode: cost_basis`).
- `roles`: honor explicit per-role slot bindings (for example tool calling -> R_mcp),
  using each slot's own `eval_mode` to decide free vs paid.

Every policy filters out `blocklist` entries before choosing, and skips entries whose
gates did not pass. The cascade is the remaining ranked, filtered candidate list.

### Tier and slot binding

- `slot_bindings` in profiles.json maps a profile use case to a snapshot slot:

```json
{
  "default": {
    "slot_bindings": {
      "big": "R1_primary",
      "middle": "R12_delegation",
      "small": "R6_compression",
      "toolcall": "R_mcp",
      "web_search": "R8_web_extract",
      "image": "R7_vision"
    }
  },
  "ante": {
    "slot_bindings": { "big": "R6_compression", "small": "R6_compression",
                       "toolcall": "R_mcp" },
    "notes": "low-RAM agent: bias all tiers to fast compression-class free models"
  }
}
```

- The binder reads `slot_bindings`, looks up each slot in the snapshot, applies the active
  SelectionPolicy, and updates the AssignmentRegistry. Profiles with no `slot_bindings`
  inherit the `default` mapping.

### Where the policy is selected

- Global default in `proxy_chain.json` (`"model_scan": { "enabled": bool,
  "policy": "static|free|budget:<x>|quality|roles", "snapshot_path": "...",
  "gateway_url": "...", "cache_ttl_s": 300 }`).
- Override at launch via env (`MODEL_SCAN_POLICY=free`) so a quicklaunch command can say
  "run now with best free models" without editing config.
- Override per request is out of scope for v1 (binding is a startup/reload concern, not a
  hot-path concern, to keep a dozen concurrent clients cheap).

---

## Free, Paid, and Price-Point Selection (worked examples)

- "best free models now": `MODEL_SCAN_POLICY=free`. Binder picks `price_blended == 0`
  winners per slot. Cascade is the free candidate tail.
- "best under 0.50 per million": `MODEL_SCAN_POLICY=budget:0.50`. Binder filters
  `price_blended <= 0.50`.
- "best for tool calling regardless": profile uses `roles`, toolcall bound to R_mcp
  (mcp_orchestration, the agentic slot that gates on `needs_tools`/`min_tc`).
- "paid plan passthrough for main, free for menial": this is the existing `claude` profile
  pattern (`tier_overrides.small`), now generalized: leave `big` static (Anthropic Pro
  passthrough) while `small`/`toolcall` resolve from the snapshot under a free policy.

---

## Quicklaunch and Tool Support

Goal: every tool launches through proxy:8082 then headroom:8787 then provider, wrapped by
rtk, with argument support to pick policy, profile, and compression. Up to a dozen
instances run concurrently through the single router (stateless per-request resolution,
read-mostly snapshot, atomic swap on reload, no per-request file IO).

### Two-command UX

- Command 1, bring the chain up: `ccp up` (wraps `proxies up`). Starts the router on 8082,
  CLIProxyAPIPlus on 8317 when OAuth providers are indicated, and Headroom on 8787 together
  with its local model. Driven by `proxy_chain.json` chain entries (a conditional clip entry
  and a populated headroom entry are added). By default it spawns a new terminal window
  running the tmux panes (Headroom compression ratios, proxy routing, clip) so the chain is
  monitored, not silent; `--background` detaches. The terminal command is configurable and
  auto-detects wezterm.
- Command 2, launch a tool: `ccp <tool> [...]` under rtk. Default is `ccp claude`; custom is
  the same command with a session file or arguments. `ccp <tool>` also verifies the chain and
  brings it up if absent.

### Unified launcher

A `ccp` dispatcher (scripts/ccp-launch.sh, exposed on PATH):

```
ccp up
ccp <tool> [--preset <name>] [--config <session.yaml>]
           [--policy free|budget=0.50|quality|roles|static]
           [--role <tier-or-usecase>=<passthrough|provider/model|slot>] ...
           [--provider <name>] [--no-compress] [--continue] [-- <tool args...>]
```

`<tool>` in: claude, codex, qwen, pi, hermes, opencode, openclaw, antigravity, ante.

Resolution is layered, lowest to highest precedence: base chain config, preset, session
config file, inline args. The launcher merges these into one overlay, registers it as an
ephemeral session profile on the running proxy via `POST /api/routing-profiles`, exports the
returned base URL (for example `http://127.0.0.1:8082/p/claude-7f3a/v1`), toggles the headroom
hop, and execs the tool under rtk. A shell exit trap deregisters via
`DELETE /api/routing-profiles/{id}`; a TTL sweep backstops missed traps. Existing short aliases
(cc, qw, psi, hsi, oc, codex-run) are preserved and gain optional policy and config.

### Session-scoped configuration (two sessions, same tool, different config)

Profiles today are keyed by URL prefix and shared across sessions of one tool. To let two
sessions of the same tool diverge, the launcher creates an ephemeral session profile per
launch with a unique id and address, so each session routes independently through the one
chain. A session is defined by any mix of preset, a `--config` file, and inline `--role`/
`--policy` arguments. The session config file is a profile overlay plus a policy and a
compression toggle; see specs/003 contracts/session_config.schema.json. This requires
extending the currently read-only routing-profiles API with ephemeral register and deregister
endpoints backed by an in-memory overlay store layered above the file-backed profiles.

### Curated presets for the named tools

`profiles.json` ships a curated preset per tool, usable directly or as a session base layer:
claude (official Anthropic passthrough; menial and toolcall to free), codex (budget policy;
toolcall to a free tool-capable model), hermes (full fifteen-role slot_bindings; toolcall to
R_mcp), pi (caller passthrough; toolcall forced fast; own web_search), ante (compression-class
free across all tiers; compress on), opencode (minimax-class main; free toolcall cascade).

### New profiles to add to profiles.json

- `antigravity`: maps to the OAuth-hosted Antigravity path via CLIProxyAPIPlus
  (provider_override), Gemini-class main, free toolcall slot.
- `ante`: low-RAM agent. All tiers biased to R6_compression-class free models, toolcall to
  R_mcp, aggressive headroom compression on by default.

### New aliases

```
alias agi='ccp antigravity'        # Antigravity CLI via /p/antigravity/v1
alias ante-si='ccp ante --profile ante'
alias ante-srv='ccp ante --profile ante -- serve'
```

Ante is configured to point its OpenAI/Anthropic base URL at
`http://127.0.0.1:8082/p/ante/v1`, BYO placeholder key `pass`. Ante's own dynamic router
still runs locally; the proxy supplies the actual model targets per role, so the two
routers compose rather than conflict (ante decides complexity class, proxy decides which
concrete model serves that class under the active policy).

---

## Quota-Aware Tiered Rotation and Lanes

### Lanes

A lane is a consumption class with its own selection policy and quota pool. Presets declare a
lane; a session may override it.

- `standby` lane: the 24/7 agents (hermes coordinator, ante). `policy: free`. Draws only from
  the free pool and never consumes premium quota. This protects the paid quota that the
  interactive lane needs.
- `interactive` lane: the CLI tools (claude, codex, pi, opencode). `policy: rotate`. The
  primary and reasoning roles get the highest-IQ S-tier model with remaining weekly quota; the
  toolcalling and menial roles are forced to free models to preserve premium quota for
  reasoning.

### Quota ledger and data sources (builds on what exists)

The proxy is already the rotation chokepoint and already has a quota substrate: `rate_limiter`
(per-model sliding window, quota-scored fallback, x-ratelimit-reset parsing), `usage_tracker`
(per-provider request and cost logging with JSON and CSV export), and `billing_integrations`
(remaining balance from OpenRouter, OpenAI, Anthropic). The rotation engine consumes these. The
genuinely new piece is a ledger that also ingests what the proxy cannot see, behind a pluggable
`QuotaSource` adapter interface:

1. tokscale (primary external): subscription consumption for 20+ coding tools read from its
   local SQLite, covering Antigravity, Gemini, Qwen, Kiro, OpenCode and more that ccusage does
   not. This is data model-scan cannot get by probing.
2. ccusage (secondary external): stable `--json` contract for the providers it covers, used as
   a redundant cross-check.
3. internal adapters: `usage_tracker`, `billing_integrations`, `rate_limiter`, and model-scan
   `/quota`.
4. live observation: decrement the ledger on observed usage and 429s between refreshes.

model-scan publishes the merged per-provider quota and reset times in the snapshot
`provider_quota` section.

### Decision on the quota tools (researched options)

Build native on the existing substrate; ingest external quota through the adapter layer with
tokscale primary and ccusage secondary; adopt gpt-load's rotate-on-429 pattern natively
(per-provider key and account pool). Do not add gpt-load or LiteLLM as proxy components: each
duplicates the proxy's existing routing and 429 handling and adds a hop, breaking the
single-chain design. tokscale is chosen over ccusage as the primary external feed for long-term
reliability because it covers the operator's actual tool set far more completely (20+ tools to
ccusage's six), with a queryable SQLite and an active Rust v2; the adapter interface insulates
the ledger from tokscale's internal schema. tokenusage and coding_agent_usage_tracker are
narrower monitors; the dashboard covers visualization.

### Rotation policy (`rotate`)

For the interactive primary role: pick the highest-IQ S-tier candidate whose provider has
remaining weekly quota; as a provider crosses a drain threshold, rotate to the next-best
paid provider or account; when the paid pool is exhausted, fall to a free floor (the best free
model, deepseek-v4-flash preferred across its several free providers, unless model-scan ranks a
better free S-tier such as an OpenRouter stealth model) rather than holding a paid provider in
reserve. Ollama Cloud free S-tier (3hr refill) is part of the rotation pool, filling gaps
between paid quota windows. Hysteresis and a per-provider cooldown prevent flapping at quota
edges. The aim is to maximize weekly S-tier utilization across the paid pool (Claude, Gemini,
OpenAI, OpenCode Go) while keeping toolcalling free and never forcing a paid call once paid
quota is spent. Perplexity binds to the web_search and web_extract roles, not the primary.

### Closing the loop (reliability feedback)

Promoted from optional to a real phase. The proxy exports observed reliability (latency, error
rate, 429 frequency) per provider and model back to model-scan, which weights future scans and
quota estimates. Rotation makes this valuable: the system learns which providers actually
deliver under load, not just which score well in a probe.

## Observability and the Chain Monitor

- Visible monitor: `ccp up` spawns a terminal window with tmux panes for Headroom (compression
  ratios), the proxy (routing and errors), and clip when running. Default on; `--background`
  detaches.
- Correlation by session id: every session already gets an ephemeral profile id. That id is
  stamped on every log line, error, and metric across the chain, so a problem in one tool is
  traceable to its origin even with a dozen tools running.
- Unified error sink: all chain components and the launcher write structured errors to a single
  append-only log (`~/.ccp/errors.jsonl`) with source, session id, provider, model, error
  class, and timestamp. `ccp errors` tails and filters it (by tool, provider, or session), and
  the dashboard gains an error panel. This addresses error cascades across tools: filter by
  correlation id or provider to see the whole cascade in one place.

## Role Coverage (Hermes config.yaml v39)

The reference role universe is the Hermes `config.yaml` role table, fifteen roles. The
diagnostic engine defines ten slots today, so five auxiliary roles are unbacked and are added
in Phase 1 (model-scan side). The proxy binds tiers and common use cases through the `default`
profile and binds Hermes auxiliary roles only through the `hermes` profile.

| Hermes role | model-scan slot | Proxy binding | Status |
|-------------|-----------------|---------------|--------|
| Primary | R1_primary | default.big | exists |
| Delegation | R12_delegation | default.middle | exists |
| Compression | R6_compression | default.small, default.background | exists |
| Vision | R7_vision | default.image | exists |
| Web Extract | R8_web_extract | default.web_search | exists |
| Session Search | R9_session_search | hermes.session_search | exists |
| Approval | R10_approval | hermes.approval | exists |
| Flush Memories | R11_flush_memories | hermes.flush_memories | exists |
| MCP | R_mcp | default.toolcall, hermes.mcp | exists |
| Skills Hub | R_skills_hub | hermes.skills_hub | exists |
| Title Generation | R_title_gen | hermes.title_gen | add (Phase 1) |
| Triage | R_triage | hermes.triage | add (Phase 1) |
| Kanban | R_kanban | hermes.kanban | add (Phase 1) |
| Profile Describer | R_profile_desc | hermes.profile_desc | add (Phase 1) |
| Curator | R_curator | hermes.curator | add (Phase 1) |

The five new slots are 1:1 (one per role) for fidelity. Their gates come from a per-role needs
analysis in Phase 1 (title generation is short and cheap; triage and profile describing need
moderate reasoning; kanban and curation benefit from higher quality), informed by the v39 model
choices. Their `eval_mode` is `cost_basis` so paid candidates are scored and available, with
free as the operational default via the `standby` lane and a per-session opt-in to paid. Tool
calling stays a gate (`needs_tools`, `min_tc`) on slots, not a separate slot, which is why the
corrected agentic binding is `R_mcp` and there is no `R5_tool`.

## Project Boundary (kept separate, complementary)

| Concern | Owner |
|---|---|
| Probing providers, scoring, gating, blocklist, tiers | model-scan |
| Producing routing_snapshot.json (versioned, validated) | model-scan |
| Scheduling scans (cron_manager) | model-scan |
| Consuming the snapshot, selection policy, binding | claude-code-proxy |
| Cascade construction, circuit breaking, request routing | claude-code-proxy |
| Quicklaunch, profiles, headroom and rtk chaining | claude-code-proxy |
| The schema of routing_snapshot.json | shared, versioned both sides |

Neither project imports the other. The proxy degrades to static config if model-scan never
runs. model-scan runs fully without the proxy.

---

## Phased Implementation

### Phase 0: Shared contract

- Author `routing_snapshot.schema.json` (JSON Schema). Place a copy in both repos under a
  `contracts/` path. Version it `schema_version`.
- Define the proxy-ready `api_model` derivation rule (model-scan side) and the gap-fill
  rule (proxy side, from PROVIDERS_* registry).

### Phase 1: model-scan export and role coverage

- Add the five missing auxiliary slots to `slot_definitions.yaml` (R_title_gen, R_triage,
  R_kanban, R_profile_desc, R_curator) as 1:1 slots with gates from a per-role needs analysis
  (eval_mode cost_basis, free by default via the standby lane), so all fifteen Hermes roles
  have a backing slot. See Role Coverage below.
- Add `--emit-snapshot[=PATH]` to dink.py and a writer in gold_standard.py that projects
  the existing per-slot data into the snapshot shape, including `api_model`,
  `price_blended`, `provider_health`, and `blocklist`.
- Atomic write (temp file plus rename). Emit from `cron_manager` after each scan.
- Add `GET /routing-snapshot` to gateway.py (serves the same artifact for admin pulls).

### Phase 2: proxy consumer

- New `src/services/models/model_scan_snapshot.py`: immutable `RoutingSnapshot` loader
  with `load(path)`, `from_gateway(url)`, validation against the schema, and TTL caching.
- New `src/core/model_scan_binder.py`: `SelectionPolicy` plus `bind(snapshot, policy,
  profiles)` that produces two outputs: global tier assignments (from the `default` profile)
  written into the AssignmentRegistry, and a per-profile resolved-binding overlay map for
  profiles whose bindings differ from default. Records provenance (which models came from the
  snapshot vs static) for the dashboard. See Refinement Notes for why the overlay split is
  required.
- New `proxy_chain.json` `model_scan` section (enabled, policy, snapshot_path,
  gateway_url, cache_ttl_s). Wire the binder into startup (start_proxy.py) and into SIGHUP
  reload alongside `reload_router`.
- `POST /api/proxy/reload-models`: re-read snapshot or pull gateway, rebind, return the new
  assignments and provenance.

### Phase 3: profile slot bindings

- Add `slot_bindings` support to `src/core/profiles.py` and apply in the endpoints.py
  overlay block (a sibling to `tier_overrides`). Global `default` plus per-profile
  overrides.

### Phase 4: quicklaunch, sessions, and chain lifecycle

- `scripts/ccp-launch.sh` dispatcher with `--preset`, `--config`, `--role`, `--policy`,
  `--provider`, `--no-compress`, `--continue`, plus `ccp up`. Layered overlay composition and
  ephemeral session-profile register and teardown.
- Extend the routing-profiles API with `POST /api/routing-profiles` and
  `DELETE /api/routing-profiles/{id}` over an in-memory ephemeral store plus a TTL sweep.
- Curate the six presets plus antigravity and the full fifteen-role hermes profile in
  `profiles.json`.
- Extend `proxy_chain.json` with a conditional CLIProxyAPIPlus entry and a populated Headroom
  entry that also launches the local model; wire `ccp up` through `proxies up`.
- Extend `scripts/install-aliases.sh` to install `ccp`, keep existing aliases, and add
  optional policy and config.

### Phase 5: lanes, quota ledger, and rotation

- Spike first (de-risking): confirm the tokscale SQLite schema, and confirm the proxy has no
  per-provider key pool today (it does not) so pool rotation is scoped as new work.
- Add the `standby` and `interactive` lanes; presets declare a lane.
- Build the `QuotaSource` adapter layer over the existing `rate_limiter`, `usage_tracker`, and
  `billing_integrations`, plus tokscale (primary) and ccusage (secondary) adapters.
- Extend the snapshot with `provider_quota`; model-scan ingests the merged ledger and publishes
  quota and reset times.
- Implement the `rotate` policy in the proxy: quota-aware S-tier rotation for the interactive
  primary, free toolcalling, free floor (best free model, deepseek-v4-flash preferred),
  hysteresis and cooldown, reusing `rate_limiter` scores.
- Add per-provider key and account pool rotation in the proxy (the native rotate-on-429
  pattern). Live ledger decrement on usage and 429s.

### Phase 6: observability and the chain monitor

- `ccp up` spawns the visible tmux monitor terminal; `--background` detaches.
- Stamp the session correlation id across logs, errors, and metrics.
- Unified error sink (`~/.ccp/errors.jsonl`), `ccp errors` filter command, dashboard error
  panel.

### Phase 7: reliability feedback loop

- Export proxy observed reliability (latency, error rate, 429 frequency) per provider and
  model back to model-scan to weight future scans and quota estimates.

---

## Spec-Kit Deliverables (specs/003-model-scan-integration)

Following the existing repo convention (specs/000.., 001.., 002..), generate:

- `spec.md`: requirements (FR list), the four decisions, success criteria, scope and
  non-goals (no request-time hard dependency, two projects stay separate).
- `plan.md`: technical context, architecture, the binder and policy design, phases.
- `data-model.md`: RoutingSnapshot, SelectionPolicy, the slot_bindings overlay, the
  AssignmentRegistry write path.
- `contracts/routing_snapshot.schema.json`: the shared schema.
- `contracts/proxy_api.md`: `GET /routing-snapshot`, `POST /api/proxy/reload-models`.
- `research.md`: why file contract over live API, why cascade-from-snapshot, ante
  composition with the proxy router, blocklist reuse.
- `quickstart.md`: run a scan, emit snapshot, launch `ccp claude --policy free`, verify
  bound models via the dashboard and `/api/proxy/reload-models`.
- `tasks.md`: dependency-ordered tasks for Phases 0 to 4.

The spec-kit skill workflow produces these. The deliberative refinement step
(cross-artifact analysis plus clarify) then resolves the edge cases below.

---

## Edge Cases for Refinement

- Snapshot missing, empty, or stale: bind falls back to static `proxy_chain.json`, log a
  warning, expose staleness in the dashboard. Never fail a request.
- Schema version mismatch: refuse to bind from a newer major schema, keep last good
  binding, surface an alert.
- Policy yields no candidate for a slot (everything blocklisted or gated out): keep the
  static value for that slot; do not leave it empty.
- A dozen concurrent clients during a reload: binding swaps an immutable snapshot object
  atomically; in-flight requests keep their already-resolved target.
- Provider in snapshot unknown to the proxy PROVIDERS_* registry: skip with a warning,
  fall through to the next cascade candidate.
- Ante double-routing: document that ante classifies complexity, the proxy selects the
  concrete model; ensure no conflicting force_main in the ante profile.
- Secrets: the snapshot carries no API keys. base_url plus provider name only. Keys come
  from the proxy registry. The `pass` placeholder and credential order are untouched.
- price_blended missing on a candidate under a budget policy: treat as ineligible for
  budget (cannot prove it is under ceiling), eligible for quality.

---

## Refinement Notes (post-review)

Applied during the deliberative refinement pass over this plan and the spec documents:

1. **Per-profile tier binding reconciliation.** The AssignmentRegistry holds one global model
   per tier (big/middle/small), but profiles can bind the same tier to different roles (for
   example default `big` to R1_primary versus ante `big` to R6_compression). The binder
   therefore writes the `default` profile resolution into the global registry and emits a
   per-profile overlay map for the rest; non-default profiles are served from the overlay at
   request time via the existing overlay block, with no second global value and no hot-path
   selection work.
2. **base_url trust.** The router resolves base_url and key from its own provider registry and
   prefers those over any snapshot value. A snapshot base_url is honored only for a provider
   already in the registry; unknown providers are skipped, not dialed. Prevents a tampered
   snapshot from redirecting traffic to an unauthenticated endpoint.
3. **Budget policy without a ceiling, and role absent from the snapshot.** A price-ceiling
   policy with no ceiling resolves as static rather than binding an unbounded price. A tier
   mapped to a role missing from the snapshot keeps its static value rather than emptying.

## Rollback

- All changes are additive and gated by `model_scan.enabled` (default false) and
  `policy: static`. Disabling restores exact current behavior.
- Capture state before edits: `git stash` in claude-code-proxy and model-scan, or tar the
  touched files. Restore path recorded in the work log per repo.
- Snapshot writer in model-scan is a new flag and a new endpoint; it does not alter
  existing scan outputs.
