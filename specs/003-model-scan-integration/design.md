---
date: 2026-05-30 16:08:12 PDT
ver: 1.0.0
author: claude-code-proxy-worker
model: claude-opus-4-8
tags: [model-scan, routing, design, binder, selection-policy, cascade, ante]
---

# Model-Scan Integration -- Technical Design v1.0

## 1. Architecture Overview

The diagnostic engine (model-scan) and the router (claude-code-proxy) are coupled by exactly
one artifact, a versioned `routing_snapshot.json`. model-scan projects its existing per-role
gold-standard data into the snapshot and writes it atomically after every scan, and also
serves it from its local gateway. The router loads the snapshot into an immutable in-memory
object at startup and on reload, applies a selection policy to resolve each tier and role to
a concrete model and a fallback cascade, and writes those into the existing AssignmentRegistry.
Request handling is unchanged downstream: the existing ModelRouter, profile overlays, cascade,
and circuit breaker operate on registry values, now populated from measured data instead of
hardcoded defaults.

```
 model-scan (separate project)                  claude-code-proxy (this project)
 ┌───────────────────────────┐                  ┌─────────────────────────────────────┐
 │ scan 10 providers         │                  │ start_proxy.py / SIGHUP / TTL / API  │
 │ score 4 axes + calculus   │                  │            │ trigger                 │
 │ gate per slot_definitions │                  │            v                         │
 │ filter blocklist.yaml     │   routing_       │  ModelScanSnapshot.load(path)        │
 │            │              │   snapshot.json  │            │ (validate schema)        │
 │            v              │ ───────────────► │            v                         │
 │ gold_standard projector   │   (file, the     │  ModelScanBinder.bind(snapshot,      │
 │  emit_snapshot()          │    only coupling) │     policy, profiles)               │
 │            │              │ ◄─ GET /routing- │            │                         │
 │  gateway :8124            │     snapshot     │            v                         │
 │  GET /routing-snapshot    │   (admin pull)   │  AssignmentRegistry (tiers+cascade)  │
 └───────────────────────────┘                  │            │                         │
                                                 │            v                         │
 launcher: ccp <tool> --policy --profile         │  ModelRouter.route() -> Assignment   │
   claude codex qwen pi hermes opencode          │   -> profile slot_bindings overlay   │
   antigravity ante                              │   -> client.py cascade + breaker     │
        │ ANTHROPIC_BASE_URL / OPENAI_BASE_URL    │            │                         │
        └─────────────► proxy :8082 ──► headroom :8787 ──► provider (+ rtk terminal wrap)│
                                                 └─────────────────────────────────────┘
```

### 1.1 What This System Does NOT Do

- It does not call the diagnostic engine on the request hot path.
- It does not merge the two projects or share code beyond the snapshot schema.
- It does not change how models are scored or gated; that stays in model-scan.
- It does not store or transit credentials inside the snapshot.
- It does not replace the compression stage or the terminal compression wrapper.
- It does not introduce per-request policy selection in this version.
- It does not hardcode model-name allowlists in the router.

## 2. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Router language | Python 3.12 (existing) | Matches the existing claude-code-proxy codebase; no new runtime |
| Router web layer | FastAPI + Uvicorn (existing) | Reuses the current endpoint and lifecycle machinery |
| Snapshot format | JSON with JSON Schema validation | Language neutral, already model-scan's output medium, easy to version |
| Diagnostic engine | Python 3.12 + FastAPI gateway (existing) | model-scan already emits gold-standard JSON and serves a gateway |
| Config store | proxy_chain.json + profiles.json (existing) | Reuses AssignmentRegistry persistence and profile overlays |
| Launcher | POSIX shell, installed by existing install-aliases.sh | Matches the current alias and proxy lifecycle tooling |
| Schema validation | jsonschema (Python) | Lightweight, standard, validates the shared contract on load |
| Testing | pytest (router), existing model-scan test harness | Matches each project's current test approach |

### 2.1 Technology Decision Records

**Decision: File contract as primary coupling, gateway pull as secondary**
- Context: the router must use measured data without depending on the engine at request time.
- Options considered: request-time gateway calls; shared database; published file artifact.
- Chosen because: a versioned file decouples lifecycles, survives the engine being offline,
  and is trivially cacheable in memory.
- Trade-offs accepted: the router may bind to data a few hours stale until the next scan,
  mitigated by cascades and on-demand refresh.

**Decision: Write resolved models into the existing AssignmentRegistry**
- Context: the router already resolves requests through Assignments with cascades.
- Options considered: a parallel resolution layer; mutating env vars; updating Assignments.
- Chosen because: Assignments already feed ModelRouter, persist, and notify the resolver;
  binding becomes a registry update with no new request-path code.
- Trade-offs accepted: binding mutates shared state, so the swap must be atomic and guarded.

**Decision: Selection policy resolved at bind time, not per request**
- Context: a dozen concurrent clients must stay cheap.
- Options considered: per-request policy evaluation; per-launch and per-reload binding.
- Chosen because: binding once per launch or reload keeps the hot path free of selection
  work and file IO.
- Trade-offs accepted: changing policy requires a reload or relaunch, acceptable for the use
  case.

## 3. Data Model

### 3.1 Snapshot Schema (the shared contract)

Published by model-scan, consumed by the router. Stored at a configurable path, default
`~/.config/model-scan/routing_snapshot.json`. Full JSON Schema in
`contracts/routing_snapshot.schema.json`.

```typescript
interface RoutingSnapshot {
  schema_version: string;          // semver, e.g. "1.0.0"; major gates compatibility
  generated_at: string;            // ISO 8601 UTC
  scan_id: number;
  slots: Record<string, RoleSelection>;   // keyed by role id, e.g. "R1_primary"
  provider_health: Record<string, "ok" | "degraded" | "down">;
  blocklist: string[];             // model identifiers excluded everywhere
  provider_quota?: Record<string, QuotaState>;   // optional; drives rotation
}

interface QuotaState {
  remaining_fraction: number;      // 0..1 of the quota window left
  reset_at?: string;               // ISO 8601 UTC
  unit?: string;                   // requests | tokens | credits | messages
  best_tier_available?: string;    // e.g. "S"
  source?: "ccusage" | "model-scan" | "live" | "merged";
}

interface RoleSelection {
  label: string;                   // human role name, e.g. "primary"
  eval_mode: "cost_basis" | "free";
  best: Candidate | null;          // null when no candidate qualified
  candidates: Candidate[];         // ranked best-first; includes best
}

interface Candidate {
  model_id: string;                // provider-native id, e.g. "qwen3.6-plus"
  provider: string;                // e.g. "opencode-go"
  api_model: string;               // router-ready id, e.g. "opencode_go/qwen3.6-plus"
  base_url: string;                // may be empty; router fills from its provider registry
  fitness: number;                 // 0..100 composite for this role
  price_blended: number | null;    // per million tokens; null means unknown
  tier: string;                    // quality tier label, e.g. "A"
  has_tools: boolean;
  has_vision: boolean;
}
```

### 3.2 Router In-Memory Model

```python
# src/services/models/model_scan_snapshot.py (new)
@dataclass(frozen=True)
class Candidate:
    model_id: str
    provider: str
    api_model: str
    base_url: str
    fitness: float
    price_blended: float | None
    tier: str
    has_tools: bool
    has_vision: bool

@dataclass(frozen=True)
class RoleSelection:
    label: str
    eval_mode: str
    best: Candidate | None
    candidates: tuple[Candidate, ...]

@dataclass(frozen=True)
class RoutingSnapshot:
    schema_version: str
    generated_at: str
    scan_id: int
    slots: dict[str, RoleSelection]
    provider_health: dict[str, str]
    blocklist: frozenset[str]
    loaded_at: float           # monotonic load time for TTL and staleness
```

Frozen dataclasses make the active snapshot immutable, so a rebind is a single atomic
reference swap and concurrent readers never see a half-updated structure.

### 3.3 Binding Output and Access Patterns

| Query Pattern | Frequency | Implementation |
|---------------|-----------|----------------|
| Resolve a request to a tier model and cascade | Per request, very high | Read AssignmentRegistry (already in memory); no snapshot access |
| Apply a non-default profile binding | Per request on a non-default profile | Dictionary lookup in the in-memory overlay map; no selection work, no file IO |
| Rebind all tiers and roles | Per launch and per reload | Apply policy over the in-memory snapshot, update registry and overlay under a lock, swap references |
| Inspect provenance | On demand, low | Read a binding-provenance map maintained by the binder |
| Pull fresh snapshot | On operator refresh | Read file or call gateway, validate, rebind |

### 3.4 Migration Strategy

The new `model_scan` section in `proxy_chain.json` is additive and defaults to disabled with
the static policy, so existing configs load unchanged. The snapshot schema is versioned;
the consumer accepts any matching major version and refuses a newer major, retaining the last
good binding. No database migration is required on either side.

## 4. Component Specifications

### 4.1 Snapshot projector (`model-scan: gold_standard.py emit_snapshot`)

- Responsibility: project existing per-slot gold-standard data into the snapshot schema,
  derive `api_model`, attach `price_blended`, `provider_health`, and `blocklist`, write
  atomically.
- Interface: `emit_snapshot(path: Path) -> Path`; CLI flag `--emit-snapshot[=PATH]`; called
  from `cron_manager` after each scan.
- Dependencies: the model-scan DB, `slot_definitions.yaml`, `blocklist.yaml`.
- Error handling: on missing scan data, write nothing and exit non-zero with a clear message;
  never write a partial file (temp file plus atomic rename).

### 4.2 Snapshot loader (`src/services/models/model_scan_snapshot.py`, new)

- Responsibility: load, validate, and cache the snapshot; expose query helpers.
- Interface:
  ```python
  def load(path: str) -> RoutingSnapshot | None
  def from_gateway(url: str, timeout_s: float = 2.0) -> RoutingSnapshot | None
  def is_stale(snap: RoutingSnapshot, ttl_s: int) -> bool
  ```
- Dependencies: jsonschema, the contract schema.
- Error handling: invalid or truncated input returns None; the caller keeps the last good
  snapshot. A newer major schema version is rejected with a logged alert.

### 4.3 Selection policy (`src/core/model_scan_binder.py`, new)

- Responsibility: choose a primary and an ordered cascade from a role's candidates.
- Interface:
  ```python
  class SelectionPolicy:
      kind: Literal["static", "free", "budget", "quality", "roles"]
      price_ceiling: float | None = None
      @classmethod
      def parse(cls, spec: str) -> "SelectionPolicy"   # "budget:0.50" -> kind=budget
      def choose(self, role: RoleSelection, blocklist: frozenset[str]
                 ) -> tuple[Candidate | None, list[Candidate]]
  ```
- Dependencies: snapshot dataclasses.
- Error handling: returns `(None, [])` when nothing qualifies; the binder then keeps static.

### 4.4 Binder (`src/core/model_scan_binder.py`, new)

- Responsibility: apply the active policy across all bound tiers and roles for every profile,
  and produce two outputs: (1) global tier assignments written into the AssignmentRegistry,
  sourced from the `default` profile mapping, used by plain `/v1` and `/p/default` traffic;
  (2) a per-profile resolved-binding overlay map, `resolved[profile][tier_or_use_case] =
  (api_model, cascade)`, for profiles whose bindings differ from default. This split is
  required because the registry holds one global model per tier, while profiles may bind the
  same tier to different roles. Non-default profiles are served at request time from the
  overlay map by the existing profile overlay block, never by a second global registry value.
- Interface:
  ```python
  @dataclass(frozen=True)
  class ResolvedBinding:
      api_model: str
      base_url: str
      cascade: tuple[str, ...]
      source: str              # "snapshot" | "static"

  @dataclass(frozen=True)
  class BindResult:
      global_tiers: dict[str, ResolvedBinding]                 # big/middle/small
      overlay: dict[str, dict[str, ResolvedBinding]]           # profile -> tier/use_case -> binding
      scan_id: int
      schema_version: str

  def bind(snapshot: RoutingSnapshot, policy: SelectionPolicy,
           profile_bindings: dict[str, dict[str, str]]) -> BindResult
  def provenance() -> dict[str, str]   # "<profile>.<tier-or-role>" -> "snapshot" | "static"
  ```
- Dependencies: AssignmentRegistry (for the default/global write), the in-memory overlay map
  (read by the endpoints overlay), profiles role bindings, snapshot loader, the provider
  registry for base_url and key resolution.
- Error handling: per-role failures fall back to static for that role and profile only; a
  whole-snapshot failure leaves both the registry and the overlay untouched. The overlay map
  is swapped atomically as one immutable object alongside the snapshot.

### 4.5 Profile role bindings (`src/core/profiles.py` + endpoints overlay)

- Responsibility: map per-profile tiers and use cases to roles; at request time, swap the
  served model and cascade from the binder overlay map for the active profile, applied after
  tier resolution and alongside the existing `tier_overrides`. The overlay carries already
  resolved models, so this step is a dictionary lookup with no selection work and no file IO
  on the hot path.
- Interface: a `slot_bindings` key per profile; a global `default` profile mapping. The
  endpoints overlay reads `BindResult.overlay[profile][assignment_id]` when present.
- Dependencies: existing profile overlay block in `endpoints.py`, the binder overlay map.
- Error handling: a profile with no overlay entry for the resolved tier falls through to the
  global registry value; an unknown role name is logged and skipped, leaving the prior model.

### 4.6 Gateway endpoint (`model-scan: gateway.py`)

- Responsibility: serve the current snapshot for admin pulls.
- Interface: `GET /routing-snapshot` returns the snapshot JSON.
- Error handling: 404 with guidance when no snapshot has been generated.

### 4.7 Launcher (`scripts/ccp-launch.sh`, new; `scripts/install-aliases.sh`, extended)

- Responsibility: start a chosen tool wired through the router with policy, profile, and
  compression arguments.
- Interface: `ccp <tool> [--policy ...] [--profile ...] [--no-compress] [--continue]
  [-- <tool args>]`.
- Dependencies: the proxy lifecycle helper, the existing alias block.
- Error handling: unknown tool or unhealthy proxy exits with a clear message and a hint to
  start the stack.

### 4.8 Session resolver and ephemeral profiles (`scripts/ccp-launch.sh` + router API)

- Responsibility: compose a session's effective routing from base, preset, session file, and
  inline args; register it as an ephemeral profile on the running router; point the tool at
  its unique address; deregister on exit.
- Layering precedence (low to high): base chain config, preset (named profile), session
  config file, inline arguments. The launcher merges these into one overlay object.
- Registration: the launcher calls `POST /api/routing-profiles` with the merged overlay and a
  desired prefix (for example `claude`); the router returns a unique id and URL prefix (for
  example `claude-7f3a` served at `/p/claude-7f3a/v1`). The launcher exports that base URL and
  execs the tool under rtk. A shell exit trap calls `DELETE /api/routing-profiles/{id}`.
- Storage: ephemeral profiles live in an in-memory overlay store layered above the file-backed
  profiles, so no global file is edited and teardown is clean. Two sessions of one tool get
  two ids and route independently. The model-scan binder overlay (4.4) is computed for an
  ephemeral profile at registration using the active policy and snapshot.
- Error handling: a registration failure falls back to launching on the static named preset
  with a warning; a missing exit trap is backstopped by a TTL sweep of idle ephemeral
  profiles.

### 4.9 Chain manager (`proxies` lifecycle script + `ccp up`)

- Responsibility: bring up the full chain with one command: the router on 8082, the OAuth
  upstream proxy (CLIProxyAPIPlus) on 8317 when indicated, and the compression stage
  (Headroom) on 8787 together with its local model.
- Interface: `ccp up` wraps `proxies up`, which reads `proxy_chain.json` chain entries and
  starts each enabled service in tmux. New entries are added for the upstream proxy and a
  populated compression entry whose `service_cmd` also launches the local model.
- Conditionality: the upstream proxy entry is enabled only when OAuth-hosted providers are
  configured (FR-047); otherwise it is skipped.
- Error handling: `ccp up` waits on each `health_path` and reports which services came up;
  `ccp <tool>` calls the same readiness check and brings the chain up if absent (FR-049).

### 4.10 Lanes (`src/core/model_scan_binder.py` + profiles)

- Responsibility: classify each preset and session into a consumption lane that fixes its
  policy and quota pool. `standby` uses the free pool only; `interactive` uses the quota-aware
  `rotate` policy over the paid pool plus the free S-tier source.
- Interface: a `lane` key on presets and an optional `--lane` launcher argument; the binder
  selects the lane's policy and pool when resolving that profile.
- Error handling: an unknown lane name falls back to `standby` (the safe, free lane) with a
  warning, so a misconfiguration never spends paid quota.

### 4.11 Quota ledger and rotation engine (`src/core/rotation.py`, new; model-scan ledger)

- Responsibility: maintain per-provider remaining quota and choose the interactive primary by
  highest-capability tier within quota, rotating on drain and on rate-limit responses.
- Built on the existing substrate, not a parallel system. The router already has
  `src/services/usage/rate_limiter.py` (per-model sliding-window tracking, quota-scored fallback
  ordering, x-ratelimit-reset parsing), `src/services/usage/usage_tracker.py` (per-provider
  request and cost logging with JSON and CSV export), and
  `src/services/billing/billing_integrations.py` (remaining balance from OpenRouter, OpenAI,
  Anthropic). The rotation engine consumes these rather than reimplementing them.
- Data sources are pluggable behind a `QuotaSource` adapter interface, so the ledger is never
  bound to one external tool. Out of band, never per request:
  - tokscale (primary external): broadest coverage of the subscription coding tools the router
    cannot see by itself (Claude, Codex, OpenCode, Antigravity, Gemini, Qwen, Kiro, and more),
    read directly from its local SQLite.
  - ccusage (secondary external): stable `--json` contract for the providers it covers, used as
    a redundant cross-check.
  - internal adapters: `usage_tracker` per-provider stats, `billing_integrations` balances,
    `rate_limiter` quota scores, model-scan `/quota`, and live 429 observation.
  Each adapter normalizes to a common `QuotaSample(provider, remaining_fraction, reset_at,
  unit, source)`; the ledger merges by provider with a source-precedence and freshness rule.
- Interface:
  ```python
  @dataclass
  class RotationState:
      active_provider: dict[str, str]      # role -> provider currently selected
      cooldown_until: dict[str, float]     # provider -> monotonic time

  def choose_primary(role: RoleSelection, ledger: QuotaLedger,
                     state: RotationState, drain_threshold: float) -> Candidate
  def on_rate_limit(provider: str, key_id: str) -> None   # advance key/account pool
  ```
- Behavior: prefer the highest-tier candidate whose provider quota fraction exceeds the drain
  threshold; below threshold, rotate to the next paid provider or account; apply a per-provider
  cooldown after rotating away to prevent flapping. The free S-tier source (Ollama Cloud, 3hr
  refill) participates in the pool.
- Free floor (not a paid reserve): when the paid pool is drained, the primary falls to the best
  free model rather than holding a paid provider back. The floor model is the snapshot's top
  free candidate for the role, with deepseek-v4-flash (available across several free providers)
  as the preferred default unless model-scan ranks a better free S-tier (for example an
  OpenRouter stealth model) above it. This means the interactive primary never blocks and never
  forces a paid call once paid quota is spent.
- Key and account pool rotation adopts the rotate-on-429 pattern natively: each provider holds
  a pool of keys or accounts; a 429 advances to the next with remaining quota, transparently.
- Error handling: when the paid pool is drained, serve the free floor (the `standby` behavior
  for that role) rather than failing.

### 4.12 Observability: monitor and unified error sink

- Visible monitor: `ccp up` starts the tmux session and, unless `--background`, spawns a
  terminal window (command configurable, auto-detects wezterm) attached to panes for Headroom,
  the proxy, and clip.
- Correlation id: the ephemeral session profile id is the correlation id. The launcher exports
  it; the proxy stamps it on every log line, metric, and error for that session; chain
  components include it when present.
- Unified error sink: a structured append-only log (`~/.ccp/errors.jsonl`) written by the
  proxy, the launcher, and chain components via a small shared emitter. `ccp errors` tails and
  filters by tool, provider, or session. The dashboard gains an error panel and a compression
  ratio panel.
- Reliability export: the proxy aggregates per provider and model latency, error rate, and
  rate-limit frequency and posts it to model-scan on an interval, closing the loop.

### 4.13 Technology Decision Record: quota and rotation tooling

**Decision: build rotation native in the proxy on the existing quota substrate; ingest external
quota through a pluggable QuotaSource adapter layer with tokscale primary and ccusage secondary;
reject gpt-load and LiteLLM as components.**
- Context: maximum weekly quota utilization with S-tier kept for the primary and free models for
  toolcalling, across many concurrent tools on one chain, with long-term reliability and broad
  coverage of the operator's actual tool set.
- Options considered for rotation: (a) gpt-load key-rotation proxy; (b) LiteLLM proxy for
  rotation, budgets, tracking; (c) native rotation in the proxy. Chosen (c): the proxy is
  already the chokepoint with cascade, circuit breaker, `rate_limiter`, `usage_tracker`, and
  `billing_integrations`; (a) and (b) would duplicate that and add a hop, breaking the single
  chain.
- Options considered for the external quota feed: ccusage (clean `--json`, but covers only
  Claude, Codex, OpenCode, Amp, Droid, Codebuff); tokscale (20+ tools including Antigravity,
  Gemini, Qwen, Kiro, OpenCode, queryable SQLite, active Rust v2); tokenusage and
  coding_agent_usage_tracker (narrower monitors). Chosen tokscale as the primary external source
  for the broadest durable coverage of the operator's stack, with ccusage as a stable-contract
  secondary, both behind a `QuotaSource` adapter so the ledger is never locked to one tool's
  schema.
- Trade-offs accepted: we own the ledger contract and key-pool rotation rather than inheriting
  LiteLLM's, and we adapt to tokscale's SQLite schema in one thin adapter (insulated by the
  interface), in exchange for one chain, full tier-aware control, and provider coverage that
  matches the operator's tools.

## 5. API / Interface Contracts

### 5.1 Diagnostic engine (model-scan)

```
GET /routing-snapshot
  Response: RoutingSnapshot (see contracts/routing_snapshot.schema.json)
  Errors:   404 when no snapshot exists yet

GET /route?slot=<roleId>            (existing, unchanged)
  Response: { slot, label, eval_mode, best, candidates[] }

GET /quota, /quota/ledger           (existing) + ingests `ccusage --json` on a cron

POST /reliability                   (new: router posts observed reliability back)
  Request:  { "samples": [ { "provider": str, "model": str, "latency_p95_ms": number,
              "error_rate": number, "rate_limit_rate": number, "window_s": number } ] }
  Response: { "accepted": int }
```

### 5.2 Router (claude-code-proxy)

```
POST /api/routing-profiles            (new: register an ephemeral session profile)
  Request:  { "prefix": "claude", "overlay": { <profile overlay>: force_main,
              tier_overrides, toolcall_models, web_search, provider_override,
              slot_bindings }, "policy": "<optional>", "ttl_s": 43200 }
  Response: { "id": "claude-7f3a", "url_prefix": "/p/claude-7f3a/v1" }
  Errors:   400 invalid overlay; 409 prefix collision (router assigns a fresh suffix)

DELETE /api/routing-profiles/{id}     (new: deregister an ephemeral session profile)
  Response: { "removed": true }
  Errors:   404 unknown id (idempotent: treated as already removed)

GET /api/routing-profiles             (existing, unchanged: now also lists ephemerals)

POST /api/proxy/reload-models
  Request:  { "source": "file" | "gateway", "policy": "<optional override>" }
  Response: { "bound": { "<tier-or-role>": { "model": str, "source": str,
                          "cascade": [str], "changed": bool } },
             "scan_id": int, "schema_version": str, "stale": bool }
  Errors:   409 when no usable snapshot and feature enabled (keeps last good);
            200 with degraded=true when falling back to static
```

### 5.3 Configuration surface (proxy_chain.json, new section)

```json
"model_scan": {
  "enabled": false,
  "policy": "static",
  "snapshot_path": "~/.config/model-scan/routing_snapshot.json",
  "gateway_url": "http://127.0.0.1:8124",
  "cache_ttl_s": 300,
  "staleness_limit_s": 86400,
  "lanes": {
    "standby":     { "policy": "free",   "pool": "free" },
    "interactive": { "policy": "rotate", "pool": "paid+free_s_tier",
                     "drain_threshold": 0.15, "free_floor": true,
                     "free_floor_preferred": "deepseek-v4-flash", "cooldown_s": 600 }
  },
  "quota": {
    "sources": [
      { "adapter": "tokscale", "db_path": "~/.local/share/tokscale/tokscale.db", "primary": true },
      { "adapter": "ccusage", "cmd": "ccusage --json" },
      { "adapter": "usage_tracker" },
      { "adapter": "billing" },
      { "adapter": "model_scan_quota" }
    ],
    "refresh_s": 900,
    "reliability_export_s": 3600
  }
}
```

### 5.4 Profile bindings (profiles.json, new key)

```json
{
  "default": {
    "slot_bindings": {
      "big": "R1_primary", "middle": "R12_delegation", "small": "R6_compression",
      "toolcall": "R_mcp", "web_search": "R8_web_extract", "image": "R7_vision"
    }
  },
  "ante": {
    "notes": "low-RAM agent: bias all tiers to fast compression-class free models",
    "slot_bindings": { "big": "R6_compression", "middle": "R6_compression",
                       "small": "R6_compression", "toolcall": "R_mcp" }
  }
}
```

### 5.5 Role Inventory and Coverage

The reference role universe is the Hermes `config.yaml` v39 role table (fifteen roles). The
diagnostic engine defines ten slots today; five Hermes auxiliary roles have no backing slot
and are added in Phase 1 (model-scan side). Tiers and common use cases bind via the `default`
profile; Hermes auxiliary roles bind only via the `hermes` profile (FR-034).

| Hermes role | model-scan slot | eval_mode | Proxy binding (profile.use_case) | Status |
|-------------|-----------------|-----------|----------------------------------|--------|
| Primary | R1_primary | cost_basis | default.big | exists |
| Delegation | R12_delegation | cost_basis | default.middle | exists |
| Compression | R6_compression | free | default.small, default.background | exists |
| Vision | R7_vision | free | default.image | exists |
| Web Extract | R8_web_extract | free | default.web_search | exists |
| Session Search | R9_session_search | free | hermes.session_search | exists |
| Approval | R10_approval | free | hermes.approval | exists |
| Flush Memories | R11_flush_memories | free | hermes.flush_memories | exists |
| MCP | R_mcp | free | default.toolcall, hermes.mcp | exists |
| Skills Hub | R_skills_hub | free | hermes.skills_hub | exists |
| Title Generation | R_title_gen | cost_basis | hermes.title_gen | add in Phase 1 |
| Triage | R_triage | cost_basis | hermes.triage | add in Phase 1 |
| Kanban | R_kanban | cost_basis | hermes.kanban | add in Phase 1 |
| Profile Describer | R_profile_desc | cost_basis | hermes.profile_desc | add in Phase 1 |
| Curator | R_curator | cost_basis | hermes.curator | add in Phase 1 |

The five new slots are defined 1:1 (one slot per role) for fidelity. Their gates are set by a
per-role needs analysis in Phase 1, not copied blindly: each role's intelligence, tool-calling,
latency, and context needs are derived from what the role does (title generation is a short
cheap summarization; triage and profile describing need moderate reasoning; kanban and curation
benefit from higher quality), informed by the model choices already recorded in the v39 role
table. Their `eval_mode` is `cost_basis` so paid candidates are scored and available, while the
operational default stays free because these roles run in the `standby` lane; a session can opt
into a paid policy when desired. Tool calling is expressed as the `needs_tools` and `min_tc`
gates on these slots, not as a separate slot. This keeps role definitions single-sourced in the
diagnostic engine; the proxy never invents a role.

### 5.6 Session config file

A session file is a profile overlay plus a policy and a compression toggle. Full schema in
`contracts/session_config.schema.json`. Each `roles` entry maps to existing overlay keys:
`passthrough` to leave the caller model intact (force_main suppressed), `model`/`provider` to
a per-tier override, `slot` to bind from the snapshot via `slot_bindings`.

```yaml
preset: claude                 # optional base preset
policy: free                   # static | free | budget:<x> | quality | roles
compress: true
provider_override: anthropic   # official main provider
roles:
  big:        { passthrough: true }
  toolcall:   { model: qwen/qwen3-next-80b-a3b-thinking, provider: openrouter }
  small:      { model: openrouter/owl-alpha }
  web_search: { slot: R8_web_extract }
```

Inline arguments mirror the file keys: `--policy free`, `--compress/--no-compress`,
`--provider anthropic`, `--role big=passthrough`, `--role toolcall=openrouter/qwen3-next`.

### 5.7 Presets

Presets are named profiles in `profiles.json`, curated per tool and usable as a launch default
or as the base layer for a session file or arguments.

| Preset | Main model | Per-role defaults |
|--------|------------|-------------------|
| claude | official Anthropic passthrough (Opus/Sonnet) | small and toolcall to free measured models; Haiku-class swapped to free |
| codex | caller model or budget policy | toolcall to a tool-capable free model; compression on |
| hermes | qwen3-next aux main | full fifteen-role `slot_bindings`; toolcall to R_mcp |
| pi | caller model passthrough | toolcall forced to a fast tool-capable model; web_search own model |
| ante | compression-class free main | all tiers biased to R6_compression; toolcall to R_mcp; compress on |
| opencode | minimax-class main | toolcall cascade of free tool-capable models |

## 6. UX Architecture

The user surface is the command line and the existing admin dashboard.

### 6.1 Interaction Model

- Launch is one command: `ccp <tool> --policy <p> [--profile <name>]`. Defaults are sensible
  so `ccp claude` works with the configured policy.
- The dashboard gains a model-source panel: per tier and role, the bound model, its source
  (snapshot or static), the snapshot scan id and age, and a refresh button that calls the
  reload endpoint.
- Error, empty, and stale states are explicit: a missing snapshot shows a clear static-mode
  banner; a stale snapshot shows its age.

### 6.2 Design System Alignment

- The model-source panel reuses the existing dashboard component set and theming; no new
  design language is introduced.

### 6.3 Adoption and Onboarding

- The quickstart shows running a scan, launching with best-free, and confirming bindings.
- Existing aliases keep working, so adoption is incremental: users add `--policy` when ready.

## 7. Hosting and Deployment

### 7.1 Infrastructure

| Component | Service | Tier | Rationale |
|-----------|---------|------|-----------|
| Router | Local process on the worker, port 8082 | Self-hosted | Existing deployment, unchanged |
| Compression stage | Local process, port 8787 | Self-hosted | Existing chain element |
| Diagnostic gateway | Local process, port 8124 | Self-hosted | Existing; gains one endpoint |
| Snapshot artifact | Local filesystem | n/a | Single shared file, no service needed |

### 7.2 CI/CD Pipeline

- Router: existing test suite plus new unit and integration tests for loader, policy, binder,
  and overlay. Schema validation runs in CI against sample snapshots.
- model-scan: existing harness plus a test that the projector output validates against the
  shared schema.

### 7.3 Environment Strategy

- The feature is disabled by default. Enabling it and choosing a non-static policy is an
  explicit operator action via config or launch argument, identical across development and
  production.

## 8. Security Considerations

### 8.1 Threat Model

- A tampered snapshot could try to redirect traffic to an attacker model or endpoint.
  Mitigation: the snapshot carries no credentials. The router resolves base_url and key from
  its own provider registry by provider name and prefers those over any snapshot value; a
  snapshot `base_url` is honored only for a provider already present in the registry, and a
  provider absent from the registry is skipped with a warning rather than dialed. Because an
  unknown provider carries no stored key, a malicious endpoint cannot exfiltrate existing
  credentials. The snapshot file lives under the user account that runs both tools.
- `provider_health` is advisory in this version: the binder MAY deprioritize a `down`
  provider but MUST NOT depend on the field for correctness, since cascades already handle
  live failure.

### 8.2 Authentication / Authorization

- Unchanged. The router authenticates to providers using its existing keys. The reload
  endpoint inherits the router's existing admin protections.

### 8.3 Data Protection

- The snapshot contains only model metadata and scores. No secrets, no user content. Provider
  keys remain in the router's existing sources and loading order.

### 8.4 Supply Chain Security

- One new router dependency, jsonschema, pinned in the lockfile and covered by the existing
  dependency audit. No new dependency in model-scan beyond what it already uses.

## 9. Implementation Phases

### Phase 0: Shared contract
- Author `contracts/routing_snapshot.schema.json` and copy it into both repositories.
- Define the `api_model` derivation rule and the base_url gap-fill rule.
- Validates: FR-002, FR-003, NFR-031.

### Phase 1: Snapshot production and role coverage (model-scan)
- Add the five missing auxiliary slots to `slot_definitions.yaml` (R_title_gen, R_triage,
  R_kanban, R_profile_desc, R_curator) as 1:1 slots, with gates set by a per-role needs
  analysis and `eval_mode: cost_basis` (paid permitted, free by default via the standby lane),
  so every Hermes role has a backing slot.
- Implement `emit_snapshot` projector and `--emit-snapshot`; emit from `cron_manager`.
- Add `GET /routing-snapshot` to the gateway.
- Validates: FR-001, FR-004, FR-005, FR-006, FR-033.

### Phase 2: Snapshot consumption and binding (router)
- Implement the loader with validation and TTL, the selection policies, and the binder.
- Add the `model_scan` config section; wire binding into startup, SIGHUP, and TTL.
- Add `POST /api/proxy/reload-models` with provenance.
- Validates: FR-010 through FR-017, FR-020 through FR-025, FR-050, NFR-001, NFR-002,
  NFR-010, NFR-011, NFR-030.

### Phase 3: Profile role bindings (router)
- Add `slot_bindings` to profiles and apply in the overlay block; global default plus
  overrides. Add a `hermes` profile mapping all fifteen Hermes roles to their slots.
- Validates: FR-030, FR-031, FR-032, FR-034.

### Phase 4: Launcher, sessions, and chain lifecycle
- Implement `ccp-launch.sh` with preset, session-config-file, inline role args, policy,
  compression, and continue arguments; compose the layered overlay; register and tear down
  ephemeral session profiles.
- Add `POST /api/routing-profiles` and `DELETE /api/routing-profiles/{id}` with an in-memory
  ephemeral overlay store and a TTL sweep.
- Curate the six presets (claude, codex, hermes, pi, ante, opencode) plus antigravity in
  `profiles.json`; add the full fifteen-role `hermes` profile.
- Add `ccp up`; extend `proxy_chain.json` with a conditional CLIProxyAPIPlus entry and a
  populated Headroom entry that also launches the local model; extend `install-aliases.sh`.
- Validates: FR-035 through FR-039, FR-040 through FR-049.

### Phase 5: Lanes, quota ledger, and rotation
- Add `standby` and `interactive` lanes and the `model_scan.lanes` config; presets declare a
  lane.
- Build the `QuotaSource` adapter layer over the existing `rate_limiter`, `usage_tracker`, and
  `billing_integrations`, plus tokscale (primary external) and ccusage (secondary external)
  adapters. Spike first: confirm the tokscale SQLite schema and the per-provider key-pool gap.
- Extend the snapshot with `provider_quota`; model-scan ingests external quota and publishes
  quota and reset times.
- Implement `src/core/rotation.py`: quota-aware S-tier rotation for the interactive primary,
  free toolcalling, free floor (best free model, deepseek-v4-flash preferred), hysteresis and
  cooldown; native key/account pool rotation on 429; live ledger decrement reusing
  `rate_limiter` scores.
- Validates: FR-051 through FR-059, NFR-003.

### Phase 6: Observability and the chain monitor
- `ccp up` spawns the visible tmux monitor terminal; `--background` detaches.
- Stamp the session correlation id across logs, errors, and metrics; add the unified error sink
  and `ccp errors`; add dashboard error and compression-ratio panels.
- Validates: FR-060 through FR-063.

### Phase 7: Reliability feedback loop
- Export router observed reliability (latency, error rate, rate-limit frequency) per provider
  and model back to model-scan for future scans and quota estimates.
- Validates: FR-064.

## 10. Testing Strategy

### 10.1 Unit Tests
| Module | Key Test Cases |
|--------|----------------|
| Snapshot loader | valid load, truncated file returns None, newer major rejected, TTL and staleness |
| Selection policy | free picks zero price, budget excludes over-ceiling and unknown price, quality picks top, roles honors mapping, static ignores snapshot |
| Binder | cascade excludes blocklist and primary, empty candidates keep static, provenance correct, atomic swap |
| Projector (model-scan) | output validates against the shared schema, api_model derivation, atomic write |

### 10.2 Integration Tests
| Scenario | Validates |
|----------|-----------|
| Launch best-free with a fixture snapshot, inspect bindings | FR-012, FR-020, SC-001 |
| Kill primary provider, observe cascade recovery | FR-013, SC-002 |
| Remove snapshot, confirm static serving | FR-016, SC-004, NFR-010 |
| Switch policy via reload, compare provenance | FR-025, SC-003 |
| Drive a dozen concurrent profiles during a rebind | FR-044, NFR-002, SC-005 |
| Inject a blocklisted top scorer, confirm exclusion | FR-014, SC-006 |

### 10.3 Performance Benchmarks
| Benchmark | Target | Method |
|-----------|--------|--------|
| Per-request resolution overhead | No file or network read from this feature | Trace a served request and assert in-memory access |
| Rebind duration | In-flight requests unaffected | Issue requests during a forced rebind and assert success |

## 11. Project Structure

```
claude-code-proxy/
├── src/
│   ├── services/models/
│   │   └── model_scan_snapshot.py     # loader, validation, in-memory model
│   ├── core/
│   │   ├── model_scan_binder.py       # SelectionPolicy + binder
│   │   ├── profiles.py                # + slot_bindings support
│   │   └── assignments.py             # write target (existing)
│   └── api/
│       └── endpoints.py               # + reload-models, + overlay binding
├── config/proxy_chain.json            # + model_scan section
├── profiles/profiles.json             # + slot_bindings
├── scripts/
│   ├── ccp-launch.sh                  # unified launcher (new)
│   └── install-aliases.sh             # + ante/antigravity, + policy (extended)
├── specs/003-model-scan-integration/
│   └── contracts/routing_snapshot.schema.json
└── tests/                             # loader, policy, binder, overlay, integration

model-scan/   (separate project, contract-only coupling)
├── gold_standard.py                   # + emit_snapshot projector
├── cron_manager.py                    # + emit after scan
├── gateway.py                         # + GET /routing-snapshot
└── contracts/routing_snapshot.schema.json   # copy of the shared schema
```

Organization is layered within the router (services for data, core for logic, api for
surface), matching the existing structure, so the new pieces sit beside their peers.

## 12. References

1. musistudio Claude Code Router, real-time per-task routing and launch ergonomics:
   https://github.com/musistudio/claude-code-router
2. Not-Diamond awesome-ai-model-routing, survey of routing approaches:
   https://github.com/Not-Diamond/awesome-ai-model-routing
3. Production gateway fallback patterns (Portkey, LiteLLM), reactive availability handling:
   https://inworld.ai/resources/best-llm-router-ai-gateway
4. Cost-aware routing benchmarks (RouterBench and related), measured quality and cost:
   https://arxiv.org/pdf/2509.09782
5. Internal: plans/model-scan-integration-plan.md (this repository).
