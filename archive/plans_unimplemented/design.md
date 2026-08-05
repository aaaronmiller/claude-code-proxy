---
date: 2026-05-14 PHASE-LOCK PT
ver: 2.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, routing, bun, hono, svelte, ink, design]
---

# Universal LLM Proxy with Profile Routing — Technical Design v2.0

## 1. Architecture Overview

The system is a single Bun-built artifact that operates as a long-running process exposing four service surfaces from one codebase: an HTTP API serving the OpenAI Chat Completions and Anthropic Messages protocols, a real-time event stream over WebSocket, a static web bundle for the Svelte-based browser dashboard, and an Ink-based terminal user interface that the same binary launches as a subcommand. All four surfaces consume a shared service layer that owns the profile registry, the cascade router, the circuit breaker, the upstream provider abstraction, the request handler, the analytics store, and the configuration persistence.

The product is fully standalone: it does not depend on LiteLLM, claude-code-router, the fuergaosi233 fork, or any external gateway. It speaks the same protocols those tools speak but implements them natively. Adding the product to a workflow requires only running its binary; existing CLI tools target it by setting their base URL to a profile-prefixed path on the proxy.

```
                              Universal LLM Proxy (single binary)
   +------------------------------------------------------------------------------+
   |                                                                              |
   |   +----------+      +-----------+      +-------------------+                 |
   |   | CLI mode |      | TUI mode  |      | Server mode       |                 |
   |   | (args)   |      | (Ink/    |      | (default; HTTP +  |                 |
   |   |          |      |  React)   |      | WebSocket + Web)  |                 |
   |   +----+-----+      +-----+-----+      +---------+---------+                 |
   |        |                  |                      |                           |
   |        +--------+---------+----------+-----------+                           |
   |                 |                    |                                       |
   |          +------v-------+    +-------v--------+                              |
   |          | Config Layer |    | Request Layer  |                              |
   |          | (validate,   |    | (resolve, swap |                              |
   |          |  persist,    |    | , dispatch,    |                              |
   |          |  broadcast)  |    | record)        |                              |
   |          +------+-------+    +-------+--------+                              |
   |                 |                    |                                       |
   |          +------v--------------------v-------+                               |
   |          |   Shared Service Layer            |                               |
   |          |   - Profile Registry              |                               |
   |          |   - Cascade Router                |                               |
   |          |   - Circuit Breaker               |                               |
   |          |   - Provider Abstraction          |                               |
   |          |   - Format Translator            |                                |
   |          |   - Web-Search Interceptor       |                                |
   |          |   - Analytics Store              |                                |
   |          |   - Pricing Table                |                                |
   |          |   - Event Bus                    |                                |
   |          +------------------+-----------------+                              |
   |                             |                                                |
   |                  +----------v-----------+                                    |
   |                  |   Persistence        |                                    |
   |                  |   - profiles.json    |                                    |
   |                  |   - providers.json   |                                    |
   |                  |   - analytics.db     |                                    |
   |                  |   - pricing.json     |                                    |
   |                  +----------+-----------+                                    |
   |                             |                                                |
   +-----------------------------|------------------------------------------------+
                                 |
                       +---------v---------+
                       | Upstream Providers|
                       | (OpenRouter,      |
                       |  Anthropic,       |
                       |  OpenAI, Ollama,  |
                       |  llama.cpp, etc.) |
                       +-------------------+
```

### 1.1 What This System Does NOT Do

- Cache LLM responses (correctness risks exceed value at this scope)
- Authenticate distinct users beyond a shared secret (single-operator design)
- Distribute across multiple processes or machines (single-process design)
- Detect prompt injection or moderate content (scope contains routing only)
- Provide a plugin or extension API for third-party developers (only the upstream provider abstraction is extensible, in-code)
- Bundle a hosted dashboard or cloud service (local-only)
- Mobile applications (browser-responsive WebUI is the mobile experience)

## 2. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Runtime | Bun 1.2+ | Single-binary distribution, fast startup, native TypeScript, built-in SQLite, built-in HTTP server with strong WebSocket support, fast bundler for the web frontend |
| HTTP framework | Hono | Lightweight, type-safe, native Bun fit, mature middleware ecosystem, runs identically in development and production |
| TUI library | Ink 6.6 + React 19 | Production-proven (OpenCode TUI rewrite uses this exact stack); JSX-based; rich ecosystem (`ink-text-input`, `@inkjs/ui`, `ink-spinner`); composes naturally with the rest of the React-based frontend stack |
| Web frontend | Svelte 5 (Runes) + SvelteKit | Operator's preferred stack; small bundle size; runes provide ergonomic reactive state; excellent WebSocket and SSE integration |
| Web UI library | shadcn-svelte | Operator's preferred design system; high-quality components; accessible; copy-in source (no opaque vendor dependency); customizable via Tailwind v4 |
| Charts | Layerchart (Svelte-native) + custom SVG | Charts that read native Svelte reactivity; avoids React-only chart libraries |
| Real-time push | WebSocket (primary), SSE (fallback) | Bun's native WebSocket is high-performance; SSE provides degraded path for restricted environments |
| Persistence (config) | JSON files | Direct human editing supported; consistent with simple operator-owned data |
| Persistence (analytics) | SQLite (Bun built-in) | Zero-config; strong analytical query support; embeds easily; survives restarts |
| Token encryption | Node `crypto` with OS keychain integration where available, file-key fallback | Encrypted at rest with minimal operator friction |
| Format translation | Custom implementation | The translation surface is small enough to own; avoids LiteLLM dependency |
| Validation | Zod | Type-safe runtime validation; aligns with TypeScript-first stack; integrates with Hono for request validation |
| Process manager | Single Bun binary | No external supervisor; the binary is self-contained |
| Distribution | Compiled Bun executable plus npm package | `bun build --compile` produces a single binary; npm package supports `bun x proxy` and `npm i -g` workflows |

### 2.1 Technology Decision Records

**Decision: Bun + Hono over Node + Express, Python + FastAPI, or Go + chi**
- Context: The product needs a fast single-binary deliverable that bundles TUI, HTTP server, and WebSocket support with low operational overhead.
- Options considered: Node + Express + Ink (mature but slow startup, fragmented build chain); Python + FastAPI + Textual (mature for proxies but no single-binary story; mixed-language repo if WebUI is JS); Go + chi + Bubble Tea (single-binary excellent but reimplements format translation and JS frontend toolchain).
- Chosen because: Bun gives single-binary out of the box; TypeScript is the operator's preferred frontend language and the TUI library (Ink) is React-based, so one language across the stack; native SQLite, WebSocket, and bundler avoid 5+ dependencies; format translation is straightforward in TypeScript.
- Trade-offs accepted: Bun is newer than Node and Python; some niche libraries may have rough Bun support. Mitigated by using mainstream libraries throughout.

**Decision: Ink + React 19 over Textual, Bubble Tea, or Charm libs**
- Context: TUI must be modern, keyboard-driven, multi-panel, integrating real-time updates.
- Options considered: Textual (Python, would force two-language repo); Bubble Tea (Go, same problem); Ink (TypeScript, aligns with rest of stack).
- Chosen because: Single-language stack; React paradigm is well-understood and supported by the OpenCode TUI rewrite precedent; ecosystem libraries (`@inkjs/ui`, `ink-text-input`, `ink-table`) cover all needed widget primitives.
- Trade-offs accepted: Ink renders less smoothly than Textual for very dense dashboards. Mitigated by careful component design and bounded update rates.

**Decision: Svelte 5 + shadcn-svelte over React + shadcn or Vue + PrimeVue**
- Context: Web UI must be production-quality with extensive dashboard surfaces.
- Options considered: React + shadcn-ui (largest ecosystem but heavier bundles, two React versions if Ink ships React 19); Svelte 5 + shadcn-svelte (operator preference, smaller bundles, runes provide better dashboard ergonomics); Vue + PrimeVue (operator does not prefer).
- Chosen because: Operator preference combined with Svelte 5's runes being a natural fit for real-time-streaming dashboard state.
- Trade-offs accepted: Slightly smaller ecosystem than React. Mitigated by shadcn-svelte covering all needed primitives.

**Decision: SQLite for analytics over Postgres or DuckDB**
- Context: Analytics must survive restarts, support time-window queries, and handle 90 days of records.
- Options considered: Postgres (heavyweight for single-machine personal use); DuckDB (excellent analytical performance but less mature embed story in Bun); SQLite (zero-config embed, comfortably handles personal-scale workloads, comes bundled with Bun).
- Chosen because: Bundled with Bun; zero deployment friction; performance comfortably exceeds NFR-001 / NFR-002 / SC-005 budgets at expected scale.
- Trade-offs accepted: Single-writer constraint; mitigated by the proxy being the only writer.

**Decision: WebSocket for real-time over polling or SSE-only**
- Context: Dashboard must receive sub-second updates.
- Options considered: Polling (high overhead, lag); SSE (simpler but one-directional); WebSocket (full-duplex, native Bun support).
- Chosen because: Bun's WebSocket implementation is fast and stable; SSE retained as fallback for restricted-network browsers.
- Trade-offs accepted: Slightly more complex client implementation than SSE. Mitigated by using a small client library to abstract reconnection.

## 3. Data Model

### 3.1 Profile Registry Schema

File: `profiles/profiles.json` at the proxy's data directory.

```typescript
// Top-level shape
type ProfileRegistry = Record<string, Profile>;

interface Profile {
    // Slot overrides
    default?: string;
    background?: string;
    think?: string;
    long_context?: string;
    image?: string;
    web_search?: string;

    // Per-slot cascade chain overrides
    cascade?: {
        default?: string[];
        background?: string[];
        think?: string[];
        long_context?: string[];
        image?: string[];
        web_search?: string[];
    };

    // Upstream provider override
    provider_override?: string;        // Name of an entry in providers.json

    // Request parameter overrides
    parameters?: {
        temperature?: number;
        max_tokens?: number;
        top_p?: number;
        frequency_penalty?: number;
        presence_penalty?: number;
    };

    // Web-search interception controls
    web_search_intercept?: boolean;    // default true
    web_search_pattern?: string;       // regex; defaults to system pattern

    // Documentation
    notes?: string;
}
```

The reserved profile name `default` is mandatory and is the source for inherited slot values when other profiles omit a slot.

### 3.2 Provider Configuration Schema

File: `providers.json` at the proxy's data directory.

```typescript
interface ProviderConfig {
    providers: Provider[];
    default_order: string[];   // Names of providers in preferred order
}

interface Provider {
    name: string;              // Unique identifier
    base_url: string;
    wire_format: "openai" | "anthropic" | "ollama" | "custom";
    token_encrypted: string;   // Encrypted at rest
    model_prefix?: string;     // e.g., "openrouter/" for OpenRouter
    models_endpoint?: string;  // Optional override for model list endpoint
    health_check_path?: string;
    timeout_ms?: number;
    max_retries?: number;
    notes?: string;
}
```

### 3.3 Analytics Store Schema

File: `analytics.db` (SQLite) at the proxy's data directory.

```sql
CREATE TABLE request_records (
    id              TEXT PRIMARY KEY,            -- UUID
    timestamp       INTEGER NOT NULL,            -- Unix epoch milliseconds
    profile         TEXT NOT NULL,
    slot            TEXT NOT NULL,
    model_requested TEXT NOT NULL,
    model_dispatched TEXT NOT NULL,
    provider        TEXT NOT NULL,
    prompt_tokens   INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    cost_usd        REAL NOT NULL DEFAULT 0.0,
    latency_ms      INTEGER NOT NULL,
    status          TEXT NOT NULL,               -- "success" | "error"
    error_class     TEXT,                        -- nullable: transient, auth, validation, internal, upstream_5xx, rate_limit, timeout
    error_message   TEXT,
    tool_count      INTEGER NOT NULL DEFAULT 0,
    tool_names      TEXT,                        -- JSON array as string
    swap_event      TEXT,                        -- JSON {original, new} when web-search swap occurred
    fallback_event  TEXT,                        -- JSON {attempted: [], succeeded_at_index} when cascade fallback occurred
    request_body_hash TEXT,                      -- For deduplication / linking
    response_size_bytes INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_records_timestamp ON request_records(timestamp);
CREATE INDEX idx_records_profile ON request_records(profile, timestamp);
CREATE INDEX idx_records_model ON request_records(model_dispatched, timestamp);
CREATE INDEX idx_records_provider ON request_records(provider, timestamp);
CREATE INDEX idx_records_status ON request_records(status, timestamp);

CREATE TABLE daily_aggregates (
    day             TEXT NOT NULL,               -- YYYY-MM-DD
    profile         TEXT NOT NULL,
    slot            TEXT NOT NULL,
    model           TEXT NOT NULL,
    provider        TEXT NOT NULL,
    request_count   INTEGER NOT NULL DEFAULT 0,
    success_count   INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    prompt_tokens   INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd        REAL NOT NULL DEFAULT 0.0,
    latency_p50     INTEGER,
    latency_p95     INTEGER,
    latency_p99     INTEGER,
    PRIMARY KEY (day, profile, slot, model, provider)
);

CREATE INDEX idx_daily_day ON daily_aggregates(day);
CREATE INDEX idx_daily_profile ON daily_aggregates(profile, day);

CREATE TABLE circuit_breaker_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       INTEGER NOT NULL,
    model           TEXT NOT NULL,
    event_type      TEXT NOT NULL,                -- "opened" | "half_open" | "closed"
    failure_count   INTEGER,
    reason          TEXT
);

CREATE INDEX idx_breaker_timestamp ON circuit_breaker_events(timestamp);
CREATE INDEX idx_breaker_model ON circuit_breaker_events(model, timestamp);

CREATE TABLE provider_health_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       INTEGER NOT NULL,
    provider        TEXT NOT NULL,
    healthy         INTEGER NOT NULL,             -- 0 or 1
    latency_ms      INTEGER,
    error_message   TEXT
);

CREATE INDEX idx_health_timestamp ON provider_health_events(timestamp);
CREATE INDEX idx_health_provider ON provider_health_events(provider, timestamp);
```

A scheduled job (running every hour) rolls request records older than the configured detail retention window into `daily_aggregates` and deletes the detailed records. Default detail window is 90 days; aggregate retention is unlimited until manually pruned.

### 3.4 Pricing Table

File: `pricing.json` at the proxy's data directory.

```typescript
interface PricingTable {
    rates: Record<string, ModelRate>;   // Keyed by model identifier
    last_updated: number;                // Unix epoch milliseconds
    overrides: Record<string, ModelRate>; // Operator-set overrides
}

interface ModelRate {
    input_per_million: number;    // USD per million input tokens
    output_per_million: number;   // USD per million output tokens
    source: "default" | "override" | "fetched";
}
```

The proxy ships with a built-in default rate set covering common models from OpenAI, Anthropic, OpenRouter top models, and major open-weight providers. Operators can override per model via the configurator. A periodic background job (off by default; opt-in) can fetch fresh rates from a configurable rates endpoint.

### 3.5 Per-Request Profile Context

In-memory only, constructed at request entry, never persisted:

```typescript
interface ProfileContext {
    name: string;                      // Resolved profile name
    slots: Readonly<Record<string, string>>;
    cascade: Readonly<Record<string, readonly string[]>>;
    provider: Provider;
    parameters: Readonly<Partial<RequestParameters>>;
    webSearch: Readonly<{
        intercept: boolean;
        pattern: RegExp;
    }>;
}
```

The context is frozen (immutable) and passed by reference through the request handling stack. No mutation occurs after construction.

## 4. Component Specifications

### 4.1 Profile Resolver (`src/core/profiles.ts`)

**Responsibility**: Load and cache the profile registry; produce a `ProfileContext` on demand.

**Interface**:
```typescript
class ProfileResolver {
    constructor(registryPath: string, providerRegistry: ProviderRegistry);
    resolve(profileName: string): ProfileContext;
    list(): string[];
    reloadIfChanged(): void;
}

function extractProfileFromPath(path: string): { profile: string | null; rewrittenPath: string };
```

**Dependencies**: Provider Registry (to resolve `provider_override`), filesystem.

**Error handling**: Missing registry → fail-fast at startup. Missing `default` profile → fail-fast at startup. Malformed JSON after startup → retain last-good state, log error. Unknown profile name → throw `ProfileNotFoundError` (caught by route handler as 404).

### 4.2 Provider Registry (`src/core/providers.ts`)

**Responsibility**: Manage upstream provider definitions; decrypt tokens on demand; track health.

**Interface**:
```typescript
class ProviderRegistry {
    constructor(configPath: string, keyStore: KeyStore);
    get(name: string): Provider;
    list(): Provider[];
    add(provider: Provider): void;
    update(name: string, patch: Partial<Provider>): void;
    remove(name: string): void;
    healthOf(name: string): ProviderHealth;
}
```

**Dependencies**: Key store (for encryption/decryption), filesystem.

### 4.3 Format Translator (`src/core/translator.ts`)

**Responsibility**: Convert request bodies and response shapes between OpenAI and Anthropic formats, preserving tool calls and streaming.

**Interface**:
```typescript
function translateRequest(body: unknown, from: WireFormat, to: WireFormat): unknown;
function translateResponse(body: unknown, from: WireFormat, to: WireFormat): unknown;
function translateStreamChunk(chunk: unknown, from: WireFormat, to: WireFormat): unknown;
```

**Implementation notes**: The translator handles system message extraction (Anthropic top-level field vs OpenAI message-role), tool block translation (Anthropic `tool_use` and `tool_result` blocks vs OpenAI `tool_calls` and `tool` role messages), stop reason mapping, and streaming event shape conversion. Translation tables are maintained as constants; the test corpus exercises every documented conversion path.

### 4.4 Cascade Router (`src/core/router.ts`)

**Responsibility**: Resolve a request to a dispatched model by applying profile overlay, cascade chain, and circuit-breaker state.

**Interface**:
```typescript
class CascadeRouter {
    constructor(
        breaker: CircuitBreaker,
        defaultCascade: Record<Slot, string[]>
    );
    selectModel(
        slot: Slot,
        context: ProfileContext,
        excluded: Set<string>
    ): string | null;   // null when chain is exhausted
}
```

The selector consults the profile's slot value first, then the profile's cascade chain for that slot (if defined), then the global cascade chain for that slot. Each candidate is filtered through the circuit breaker.

### 4.5 Circuit Breaker (`src/core/circuit_breaker.ts`)

**Responsibility**: Track per-model failure history; expose availability state; record state transitions.

**Interface**:
```typescript
class CircuitBreaker {
    constructor(
        failureThreshold: number,         // Default 5
        windowMs: number,                  // Default 60_000
        cooldownMs: number                 // Default 300_000
    );
    isAvailable(modelId: string): boolean;
    recordSuccess(modelId: string): void;
    recordFailure(modelId: string, errorClass: ErrorClass): void;
    stateOf(modelId: string): CircuitState;
    eventBus: EventEmitter;
}
```

State transitions emit events to the system Event Bus (consumed by the analytics persister and the real-time push surface).

### 4.6 Web-Search Interceptor (`src/core/web_search.ts`)

**Responsibility**: Inspect a request body for web-search tool invocations; rewrite the model field when conditions are met.

**Interface**:
```typescript
function maybeRewriteForWebSearch(
    body: unknown,
    context: ProfileContext
): {
    rewritten: unknown;
    swap: { from: string; to: string } | null;
};
```

The function returns the (possibly rewritten) body and a swap record (when rewriting occurred) for logging and analytics.

### 4.7 Request Handler (`src/api/handler.ts`)

**Responsibility**: Orchestrate the full request lifecycle: profile resolution, format detection, translation, web-search interception, cascade dispatch, response translation, record persistence, event emission.

The handler is invoked from the Hono route registrations. Both legacy and profile-prefixed routes use the same handler with different `ProfileContext` resolution paths.

### 4.8 Analytics Store (`src/services/analytics.ts`)

**Responsibility**: Write request records and aggregate events; serve analytics queries; manage retention rollup.

**Interface**:
```typescript
class AnalyticsStore {
    constructor(dbPath: string);
    record(record: RequestRecord): void;
    recordCircuitEvent(event: CircuitBreakerEvent): void;
    recordHealthEvent(event: ProviderHealthEvent): void;
    queryTimeSeries(spec: QuerySpec): Promise<TimeSeriesResult>;
    queryDistribution(spec: QuerySpec): Promise<DistributionResult>;
    queryCostRollup(spec: QuerySpec): Promise<CostRollupResult>;
    queryEfficiencyScatter(spec: QuerySpec): Promise<ScatterResult>;
    queryRecords(filter: RecordFilter, page: Pagination): Promise<RecordPage>;
    runRetentionRollup(): Promise<RolloverStats>;
}
```

Writes are async-batched (write-behind) with a flush every 100 milliseconds or every 50 records, whichever comes first, to avoid serialization bottlenecks under load.

### 4.9 Event Bus (`src/core/event_bus.ts`)

**Responsibility**: In-process pub-sub for cross-cutting events (request completed, circuit changed, configuration changed, provider health changed). Consumed by the analytics store, the real-time push surface, and (optionally) the TUI.

**Interface**:
```typescript
class EventBus {
    on<K extends EventKey>(key: K, handler: (event: EventOf<K>) => void): Unsubscribe;
    emit<K extends EventKey>(key: K, event: EventOf<K>): void;
}
```

### 4.10 Real-Time Push Surface (`src/api/realtime.ts`)

**Responsibility**: Maintain WebSocket and SSE connections from web clients; coalesce and push events from the Event Bus.

The surface coalesces high-frequency events (per-request) on a per-connection basis with a configurable push interval (default 250 ms) to bound bandwidth and rendering load on busy dashboards. Low-frequency events (circuit transitions, configuration changes, provider health changes) are pushed immediately.

### 4.11 CLI Entry Point (`src/cli/index.ts`)

**Responsibility**: Parse arguments, dispatch to subcommand handlers, return structured exit codes.

The CLI uses `commander` (or equivalent) for argument parsing. Each subcommand consumes the shared service layer through a thin adapter that handles JSON-vs-table output formatting.

### 4.12 TUI Entry Point (`src/tui/index.tsx`)

**Responsibility**: Bootstrap the Ink + React 19 application and provide service-layer access to all TUI views.

The TUI uses a top-level `<App />` component with a router that swaps between views based on keyboard navigation. Views subscribe to the Event Bus for real-time updates.

### 4.13 Web Frontend (`web/`)

**Responsibility**: Render the dashboard. Built with SvelteKit + Svelte 5 + shadcn-svelte. Bundled into static assets served by Hono.

The frontend connects to the proxy's WebSocket endpoint at `/ws` for real-time updates and to the REST API at `/api/*` for analytics queries, profile and provider management, and settings.

## 5. API / Interface Contracts

### 5.1 Proxy Endpoints

```
POST /v1/chat/completions
POST /v1/messages
POST /p/{profile}/v1/chat/completions
POST /p/{profile}/v1/messages
    Request:  OpenAI Chat Completions or Anthropic Messages shape
    Response: Same shape as requested
    Auth:     Bearer token (PROXY_AUTH_KEY) in Authorization header
    Errors:   401 (no auth), 404 (unknown profile), 422 (validation), 502 (upstream),
              503 (cascade exhausted), 504 (timeout)
```

### 5.2 Configuration API

```
GET    /api/profiles                       List all profiles
GET    /api/profiles/{name}                Get profile (with resolved overlay)
POST   /api/profiles                       Create profile
PUT    /api/profiles/{name}                Update profile
DELETE /api/profiles/{name}                Delete profile
POST   /api/profiles/{name}/validate       Validate without persisting
GET    /api/profile-templates              List built-in templates

GET    /api/providers                      List providers
POST   /api/providers                      Add provider
PUT    /api/providers/{name}               Update provider
DELETE /api/providers/{name}               Delete provider
POST   /api/providers/{name}/test          Test provider connectivity

GET    /api/settings                       Get proxy settings
PUT    /api/settings                       Update settings (some require restart)
```

### 5.3 Analytics API

```
GET /api/analytics/timeseries?window={range}&group_by={dim}&metric={metric}
GET /api/analytics/distribution?window={range}&group_by={dim}&metric=latency
GET /api/analytics/cost?window={range}&group_by={dim}
GET /api/analytics/efficiency?window={range}&group_by={dim}
GET /api/analytics/circuit-state                    Current circuit breaker state per model
GET /api/analytics/provider-health                  Current and recent provider health
GET /api/analytics/records?filter={query}&page={n}  Paginated request records
GET /api/analytics/export?format={csv|json}&...     Stream export of filtered records
GET /api/reports/{type}?window={range}&format={pdf|html}   Generated reports
```

### 5.4 Real-Time Endpoint

```
WebSocket  /ws
    Subscribe topics: requests, circuit, health, config
    Receive:  Server-pushed events with type field
    Send:     Subscribe/unsubscribe messages

GET /sse                                            Fallback SSE stream of same events
```

### 5.5 System Endpoints

```
GET /healthz                  Health check (readiness state)
GET /metrics                  Prometheus exposition format
GET /openapi.json             Live OpenAPI 3.1 specification
GET /version                  Build info
```

### 5.6 CLI Commands

```
proxy serve [--port N] [--host H] [--data-dir D] [--allow-noauth]
proxy tui [--data-dir D]
proxy web [--port N]                                                      Opens dashboard URL in browser

proxy profile list [--json]
proxy profile show <name> [--json]
proxy profile create <name> [--template T] [--slot key=value]... [--from-file F]
proxy profile edit <name> [--slot key=value]... [--cascade slot=models]... [--param key=value]...
proxy profile duplicate <source> <destination>
proxy profile delete <name>
proxy profile validate [<name>]

proxy provider list [--json]
proxy provider add <name> --base-url U --wire-format F --token T
proxy provider edit <name> [--base-url U] [--token T]
proxy provider test <name>
proxy provider remove <name>

proxy stats [--window 24h|7d|30d] [--profile P] [--group-by dim] [--metric m] [--json]
proxy logs [--follow] [--profile P] [--model M] [--status S] [--since DURATION] [--json]
proxy report <daily|weekly|custom> [--window R] [--out FILE] [--format pdf|html]

proxy settings show [--json]
proxy settings set <key> <value>

proxy version
proxy help [<subcommand>]
```

## 6. UX Architecture

### 6.1 TUI Layout and Navigation

The TUI presents a fixed-position header bar with the proxy version, current view name, and a global status indicator (proxy serving / paused, registry valid / invalid, last error timestamp). Below the header, the active view occupies the rest of the viewport. A persistent footer shows context-sensitive keyboard shortcuts.

**Views**:

- **Dashboard** (default): Three-pane layout. Left pane: profile activity (per-profile request count over last 5 minutes, current rate, error rate). Middle pane: scrolling request stream (most recent 50 requests, color-coded by status, with profile, slot, model, latency). Right pane: circuit breaker state (each known model with its current state and last transition).
- **Profile Manager**: Master-detail. Left list of profiles, navigated with arrow keys. Right pane shows resolved overlay (read-only) with key bindings for new (`n`), edit (`e`), duplicate (`d`), delete (`x`), validate (`v`). Edit and new modes open a form modal with field-by-field navigation.
- **Provider Manager**: Mirror of Profile Manager structure for upstream providers. Token field is masked. Test connectivity action available.
- **Analytics**: Two-pane layout. Top pane: configurable chart selection (request volume, latency distribution, cost over time, error rate, token consumption). Bottom pane: drill-down filter chips. ASCII/Unicode rendering of charts. Time-window selector at the top with quick options (1h, 24h, 7d, 30d, 90d) and custom range entry.
- **Logs**: Real-time scrolling log viewer with filter chips at the top (profile, model, status), free-text search, and pause/resume control. Pressing Enter on a record opens a detail modal with full request and response bodies.
- **Settings**: Form view for proxy-level settings (port, auth key visibility, default provider order, circuit-breaker thresholds, retention policy). Validation runs on field exit.
- **Help**: Always accessible via `?`. Shows shortcuts and a short description for the current view plus global shortcuts.

**Global shortcuts**:
- `1-7`: jump to views (1=Dashboard, 2=Profiles, 3=Providers, 4=Analytics, 5=Logs, 6=Settings, 7=Help)
- `?`: open help for the current view
- `q`: quit
- `r`: refresh current view
- `:`: command palette (free-text command entry)

### 6.2 Web Dashboard Layout and Navigation

The web dashboard uses a left-sidebar navigation with the same set of views as the TUI, expanded for browser ergonomics. Top bar shows proxy status, current user identity (operator), connection status (WebSocket up/down), and a global search.

**Pages**:

- **Overview** (default): Grid layout. Top row: four KPI tiles (current RPS, current error rate, P95 latency over 5 minutes, cost-per-hour by sum across all profiles). Second row: real-time request stream (virtualized scroll, last 100 requests, click any row for detail drawer). Third row: per-profile activity sparklines (request volume over last hour). Bottom row: circuit-breaker health board (grid of model cards showing state, last transition, failure samples).
- **Profile Manager**: Two-column layout. Left: profile list with search and template-filter. Right: profile detail with tabs (Overlay, Edit, JSON Preview, Activity). Activity tab shows the profile's request history and aggregate stats.
- **Provider Manager**: Mirror structure for providers, plus a connectivity test button on each provider.
- **Analytics**: Multi-section page with collapsible sections for each chart type. Top of page: time-window control, group-by selector, profile/model/provider filter chips. Sections: Request Volume (time series), Latency Distribution (P50/P95/P99 ribbons), Cost Rollup (bar chart and table), Error Rate (stacked area by error class), Token Consumption (stacked area by slot), Efficiency Scatter (latency vs tokens, colored by model). Each section has a "View as Table" toggle and a "Download CSV/JSON" action.
- **Logs / Request Explorer**: Search-first design. Top: query input with chip-based filters (profile, model, status, tool name, free-text). Body: virtualized table of records with columns for timestamp, profile, model, slot, latency, status, cost. Click any row for full-detail drawer showing request body, response body, dispatched model, swap event, fallback event.
- **Reports**: Pre-built report templates (Daily, Weekly, Monthly, Custom). Each template generates an HTML or PDF document with embedded charts and tables. Reports can be downloaded or sent to a configured webhook.
- **Settings**: Multi-tab settings page (General, Authentication, Routing, Circuit Breaker, Retention, Pricing Overrides).

### 6.3 CLI Ergonomics

The CLI is designed for two audiences: interactive operators who want quick edits, and scripts that want machine-parseable output. Every read command supports `--json` for piping to `jq`. Every write command validates before persisting and prints a single-line confirmation with the affected entity's identifier.

Error output goes to stderr; data output goes to stdout. Exit codes follow standard Unix conventions (0 = success, 1 = generic error, 2 = usage error, 3 = configuration error, 4 = upstream error).

## 7. Hosting and Deployment

### 7.1 Distribution

The proxy ships as:
1. A compiled single-file Bun executable per platform (Linux x64, Linux ARM64, macOS x64, macOS ARM64, Windows x64), produced via `bun build --compile`.
2. An npm package installable via `npm i -g universal-llm-proxy` or `bun x universal-llm-proxy`.
3. A Docker image for users who prefer containerized deployment.
4. (Optional) A Homebrew formula for macOS, an Arch User Repository package for Arch Linux.

### 7.2 Data Directory

By default, the proxy stores its data in:
- macOS: `~/Library/Application Support/universal-llm-proxy/`
- Linux: `~/.local/share/universal-llm-proxy/`
- Windows: `%APPDATA%/universal-llm-proxy/`

Overridable via `--data-dir` flag or `PROXY_DATA_DIR` environment variable.

Contents:
```
${DATA_DIR}/
├── profiles.json
├── providers.json
├── pricing.json
├── settings.json
├── analytics.db
├── analytics.db-wal
├── analytics.db-shm
└── logs/
    ├── proxy-YYYY-MM-DD.log
    └── ...
```

### 7.3 Configuration

The proxy reads configuration from (in priority order):
1. Command-line arguments
2. Environment variables (`PROXY_*`)
3. `settings.json` in the data directory
4. Built-in defaults

### 7.4 Process Management

The proxy runs as a foreground process by default. Operators wanting background execution use OS-native mechanisms: `systemd` on Linux, `launchd` on macOS, or simply `tmux` / `screen`. Sample unit files for `systemd` and `launchd` are shipped in `examples/`.

## 8. Security Considerations

### 8.1 Threat Model

The proxy holds upstream provider credentials and serves LLM requests on localhost. Primary attack vectors:
- **Local credential theft**: Another process or user on the same machine reading provider tokens.
- **Network exfiltration**: Misconfiguration binding to a non-loopback interface exposing the proxy to LAN.
- **Authentication bypass**: A client without the shared secret using the proxy's credentials.

### 8.2 Mitigations

- **Encryption at rest**: Upstream tokens are encrypted using a machine-bound key. On macOS, the key is stored in the Keychain. On Linux, the key is stored in a file with `0600` permissions in the data directory; the file is generated on first launch using `crypto.randomBytes`. Decryption only happens in-process at request dispatch time.
- **Bind warnings**: The proxy binds to `127.0.0.1` by default. Any other bind address requires `--allow-public` to be passed explicitly, with a banner in logs and the dashboard.
- **Shared secret**: `PROXY_AUTH_KEY` gates every endpoint. Refusal to start without a key set, except with explicit `--allow-noauth` (intended for local testing only).
- **No plaintext logs**: Tokens never appear in any log record. Request bodies in the logs view are redacted via a configurable patterns list.

### 8.3 Supply Chain

- All production dependencies pinned to exact versions in `bun.lockb`.
- Automated dependency audit via `bun audit` (or equivalent) on every CI run.
- The proxy avoids the LiteLLM March 2026 supply-chain compromise scenario by not including LiteLLM as a runtime dependency.

## 9. Implementation Phases

Phases are sized to ship a usable artifact at each boundary. Each phase produces a working binary that strictly supersedes the prior phase.

### Phase 1: Core Proxy Foundation

- Bun project scaffolding; TypeScript configuration; package.json with dependency pins.
- Hono server skeleton with health and version endpoints.
- Format translator with comprehensive test corpus.
- Provider abstraction with one provider implementation (OpenAI-compatible) and provider configuration persistence (`providers.json`).
- Token encryption (OS keychain integration with file-key fallback).
- Authentication middleware (`PROXY_AUTH_KEY`).
- Single-binary build via `bun build --compile`.
- Validates: FR-001 through FR-004, FR-010 through FR-012, FR-130 through FR-132, NFR-002, NFR-021.

### Phase 2: Routing, Cascade, and Profiles

- Profile registry resolver with mtime-keyed cache and validation.
- Cascade router with circuit breaker.
- Profile context plumbing through the request handler.
- Profile-prefixed routes (`/p/{profile}/v1/...`).
- Built-in profile templates for pi, opencode, hermes, claude-code, codex, local-ollama, openai-bare, anthropic-bare.
- First-launch starter registry synthesis.
- Web-search interceptor.
- Validates: FR-020 through FR-023, FR-030 through FR-033, FR-040 through FR-042, FR-050 through FR-051, FR-060 through FR-063, FR-070 through FR-072, NFR-001, NFR-010, NFR-011.

### Phase 3: Analytics Foundation

- Analytics SQLite store with schema and migrations.
- Request record persistence with async-batched writes.
- Circuit breaker event persistence.
- Provider health event persistence.
- Pricing table with default rates for known models.
- Cost computation pipeline.
- Time-series, distribution, cost-rollup, efficiency-scatter, records-query handlers in the REST API.
- Retention rollup job.
- Validates: FR-110 through FR-118, NFR-012, SC-005.

### Phase 4: CLI Configurator

- Top-level CLI with `commander`-style argument parsing.
- Subcommands: serve, profile (list/show/create/edit/duplicate/delete/validate), provider (list/add/edit/test/remove), stats, logs, settings, version, help.
- JSON output mode for all read commands.
- Validation of all write operations before persistence.
- Validates: FR-080 through FR-083, NFR-030, SC-003.

### Phase 5: Real-Time Push and Event Bus

- Event Bus implementation.
- WebSocket endpoint at `/ws` with topic subscription.
- SSE fallback endpoint at `/sse`.
- Event coalescing per connection with configurable push interval.
- Real-time emission of request, circuit, health, config events.
- Validates: FR-120 through FR-123, NFR-004, SC-004.

### Phase 6: Web Dashboard

- SvelteKit project scaffolding under `web/`; Svelte 5 with runes.
- Tailwind v4 and shadcn-svelte integration.
- Layerchart integration for time-series and distribution charts.
- WebSocket client with reconnection logic.
- Pages: Overview, Profile Manager, Provider Manager, Analytics, Logs, Reports, Settings.
- Validation forms with shared logic between client and server.
- Static asset bundling and serving from Hono.
- Validates: FR-100 through FR-106, NFR-031 (web-equivalent), NFR-032, SC-001, SC-002, SC-003.

### Phase 7: TUI Configurator

- Ink 6.6 + React 19 application scaffolding under `src/tui/`.
- Top-level App with view router and persistent header/footer.
- Views: Dashboard, Profile Manager, Provider Manager, Analytics, Logs, Settings, Help.
- Event Bus subscription for real-time updates.
- Keyboard navigation conforming to the design spec.
- Validates: FR-090 through FR-096, NFR-031.

### Phase 8: Reports and Polish

- Pre-built report templates (Daily, Weekly, Monthly, Custom).
- HTML and PDF report generation.
- CSV and JSON export endpoints.
- OpenAPI 3.1 generator with dynamic profile path reflection.
- Prometheus metrics endpoint.
- Distribution: Docker image, Homebrew formula, npm publish, AUR package.
- Validates: FR-117, FR-140 through FR-142, FR-150 through FR-151, SC-006, SC-007, SC-008.

## 10. Testing Strategy

### 10.1 Unit Tests

| Module | Key Test Cases |
|--------|---------------|
| Profile Resolver | Resolves known profile; throws on unknown; merges overlay correctly; mtime-triggered reload; corrupt-file recovery |
| Format Translator | Round-trips every documented OpenAI <-> Anthropic case; preserves tool calls; handles streaming chunks; preserves unknown fields |
| Cascade Router | Selects primary on healthy; falls through on transient failure; respects circuit-breaker state; honors profile cascade overrides |
| Circuit Breaker | Opens after threshold; half-opens after cooldown; closes on probe success; reopens on probe failure |
| Web-Search Interceptor | Rewrites when conditions met; no-op when disabled; no-op for multi-tool turns without forced choice; honors per-profile pattern |
| Analytics Store | Batched writes; query correctness; retention rollup integrity; index coverage |
| Token Encryption | Round-trip on each supported platform; key rotation; refuses to start without key access |

### 10.2 Integration Tests

| Scenario | Validates |
|----------|----------|
| Five concurrent CLIs through five profiles | FR-040, FR-042, FR-050, SC-001 |
| Web-search swap end-to-end (real Anthropic web-search shape) | FR-060, FR-061, FR-063, SC-002 |
| Live profile edit reflected next request | FR-032, NFR-031-equivalent, SC-007 |
| Cascade exhaustion returns 503 | FR-020, FR-022 |
| Translation round-trip with tool calls | FR-002 |
| WebSocket reconnect under server restart | FR-120, NFR-004 |
| CLI / TUI / WebUI produce identical state for same operation | NFR-030, SC-003 |
| Unknown profile returns 404 | FR-041 |
| Analytics query over 100K records | FR-111, SC-005 |
| Fresh install to "ready to serve" under 10 seconds | NFR-033, SC-006 |

### 10.3 Performance Benchmarks

| Benchmark | Target | Method |
|-----------|--------|--------|
| Profile resolution overhead at P99 | < 2 ms | 10,000 requests against mock upstream; compare to pass-through baseline |
| Format translation overhead at P99 | < 5 ms | 10,000 representative requests in each direction |
| Sustained throughput on single core | >= 200 RPS | 5-minute load test with mixed-profile traffic |
| Real-time push latency at P95 | < 1 second | 1000 instrumented events end-to-end |
| Analytics query at P95 over 30-day, 100K-record window | < 2 seconds | Synthetic data populated, time-series and distribution queries timed |

### 10.4 End-to-End Tests

Playwright tests cover the web dashboard: profile create flow, provider add flow, analytics navigation, real-time stream visibility, request explorer search and filter, report generation.

The TUI is tested via `ink-testing-library` for component behavior and via headless terminal automation for navigation flows.

## 11. Project Structure

```
universal-llm-proxy/
├── src/
│   ├── api/
│   │   ├── handler.ts                  # Main request handler
│   │   ├── routes.ts                   # Hono route registration
│   │   ├── realtime.ts                 # WebSocket + SSE endpoints
│   │   ├── analytics_routes.ts         # Analytics REST API
│   │   ├── config_routes.ts            # Profile + provider + settings REST
│   │   └── auth.ts                     # Authentication middleware
│   ├── core/
│   │   ├── profiles.ts                 # Profile resolver
│   │   ├── providers.ts                # Provider registry
│   │   ├── translator.ts               # Format translation
│   │   ├── router.ts                   # Cascade router
│   │   ├── circuit_breaker.ts          # Circuit breaker
│   │   ├── web_search.ts               # Web-search interceptor
│   │   ├── event_bus.ts                # Pub-sub
│   │   ├── pricing.ts                  # Pricing table + cost computation
│   │   └── key_store.ts                # Token encryption
│   ├── services/
│   │   ├── analytics.ts                # Analytics store
│   │   ├── retention.ts                # Rollup job
│   │   ├── healthcheck.ts              # Provider health probing
│   │   └── openapi.ts                  # OpenAPI spec generator
│   ├── cli/
│   │   ├── index.ts                    # CLI entry point
│   │   ├── commands/
│   │   │   ├── serve.ts
│   │   │   ├── tui.ts
│   │   │   ├── profile.ts
│   │   │   ├── provider.ts
│   │   │   ├── stats.ts
│   │   │   ├── logs.ts
│   │   │   ├── settings.ts
│   │   │   └── report.ts
│   │   └── format.ts                   # JSON vs table formatting
│   ├── tui/
│   │   ├── index.tsx                   # TUI entry point
│   │   ├── App.tsx                     # Top-level component
│   │   ├── views/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ProfileManager.tsx
│   │   │   ├── ProviderManager.tsx
│   │   │   ├── Analytics.tsx
│   │   │   ├── Logs.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Help.tsx
│   │   └── components/                 # Shared TUI primitives
│   ├── shared/
│   │   ├── schemas.ts                  # Zod schemas for all entities
│   │   ├── types.ts                    # TypeScript type definitions
│   │   └── constants.ts                # Slot names, defaults
│   └── main.ts                         # Process entry: dispatches to CLI / serve / tui
├── web/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte
│   │   │   ├── +page.svelte                  # Overview
│   │   │   ├── profiles/
│   │   │   ├── providers/
│   │   │   ├── analytics/
│   │   │   ├── logs/
│   │   │   ├── reports/
│   │   │   └── settings/
│   │   ├── lib/
│   │   │   ├── api.ts                  # REST client
│   │   │   ├── ws.ts                   # WebSocket client
│   │   │   ├── stores/                 # Svelte 5 runes-based stores
│   │   │   └── components/             # shadcn-svelte components
│   │   └── app.html
│   ├── svelte.config.js
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── templates/
│   ├── profiles/                       # Built-in profile templates
│   │   ├── pi.json
│   │   ├── opencode.json
│   │   ├── hermes.json
│   │   ├── claude-code.json
│   │   ├── codex.json
│   │   ├── local-ollama.json
│   │   ├── local-llamacpp.json
│   │   ├── openai-bare.json
│   │   └── anthropic-bare.json
│   └── providers/                      # Built-in provider templates
│       ├── openrouter.json
│       ├── anthropic.json
│       ├── openai.json
│       └── ollama.json
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   │   ├── playwright/                 # Web dashboard tests
│   │   └── tui/                        # TUI flow tests
│   └── perf/                           # Performance benchmarks
├── examples/
│   ├── systemd/
│   ├── launchd/
│   └── docker/
├── docs/
│   ├── README.md
│   ├── INSTALL.md
│   ├── CONFIGURATION.md
│   ├── PROFILES.md
│   ├── PROVIDERS.md
│   ├── ANALYTICS.md
│   ├── CLI.md
│   ├── TUI.md
│   ├── API.md
│   └── DEVELOPING.md
├── scripts/
│   ├── build.sh
│   └── release.sh
├── package.json
├── tsconfig.json
├── bun.lockb
└── LICENSE
```

The structure separates the proxy core (`src/core/`), the API surface (`src/api/`), the persistent services (`src/services/`), the configurator UIs (`src/cli/`, `src/tui/`, `web/`), and the shared types and schemas (`src/shared/`). Each configurator is a thin facade over the same service layer; capability parity (NFR-030) is enforced by integration tests in `tests/integration/`.

## 12. References

1. Ink 6.6 documentation and React 19 integration, as used by anomalyco/opencode TUI rewrite.
2. LiteLLM dashboard analytics patterns: Model Activity view, cost tracking per model, latency distributions, efficiency scatter.
3. Hono framework documentation.
4. Svelte 5 Runes documentation; shadcn-svelte component reference.
5. Layerchart documentation for Svelte-native charting.
6. SQLite analytical query patterns, particularly for time-series rollups.
7. Bun documentation for `--compile`, native WebSocket, native SQLite.
8. CCS (`kaitranntt/ccs`) profile selector pattern, adopted as `/p/{name}` path prefix.
9. claude-code-router (`musistudio/claude-code-router`) task-category routing vocabulary, adopted as slot names.
10. Anthropic Messages API specification (current version) and OpenAI Chat Completions API specification (current version) for format translation correctness.

