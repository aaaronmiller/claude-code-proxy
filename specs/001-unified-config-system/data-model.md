# Data Model — Unified Configuration & Multi-Surface Control System

**Feature**: 001-unified-config-system | **Phase**: 1 | **Date**: 2026-04-23

Entity definitions, validation rules (sourced from spec FRs), and state transitions. Python-first (dataclass sketches); OpenAPI schemas in `contracts/config-api.yaml` are generated from these.

---

## Assignment

A unit of routing configuration identifying a `(provider, model, base_url, api_key, enabled)` target. Replaces the split between per-tier env vars and per-slot `RouteTarget`.

| Field | Type | Rule |
|---|---|---|
| `id` | `str` (slug) | Unique across all assignments. For tiers: fixed `"big"`/`"middle"`/`"small"`. For slots: free-form, lowercase with underscores, ≤ 64 chars. |
| `kind` | `Literal["tier", "slot"]` | Immutable after creation. Tiers are the fixed three; slots are operator-defined. |
| `model` | `str` | Provider-qualified model name (e.g., `nvidia/nemotron-nano-9b-v2:free`). Empty string means "inherit from higher layer or use cascade." |
| `provider` | `str` | Provider slug (e.g., `openrouter`, `anthropic`, `openai`). Empty means auto-detect from model prefix. |
| `base_url` | `str` | Provider base URL. Empty means "lookup in provider_registry by `provider`." |
| `api_key` | `str` | Either `"${VAR_NAME}"` reference, empty (inherit from provider registry), or (warned) literal. |
| `enabled` | `bool` | Disabled assignments are skipped by the router; incoming requests targeting them fall back to tier-default. |
| `cascade` | `list[str]` | Ordered list of fallback models to try on primary failure. Applies when `MODEL_CASCADE=true` or cascade is implied by role. |

**Validation**:
- `kind == "tier"` → `id ∈ {"big", "middle", "small"}` (FR-003).
- `kind == "slot"` → `id` matches `[a-z][a-z0-9_]{0,63}` (FR-003a).
- `api_key` matching a known secret pattern AND not wrapped in `${...}` → emit warning (FR-015).
- `model` and `cascade` entries must be non-empty strings when present.

**State transitions**:
- Created via `POST /api/assignments` (slot only) or seeded at first-run (tier defaults).
- Modified via `PATCH /api/assignments/{id}`; emits change event through live-reload transport.
- Disabled via `PATCH` with `enabled=false`; requests still resolve but router skips.
- Deleted via `DELETE /api/assignments/{id}` (slot only; tiers cannot be deleted).

---

## IdentifierMapping

Maps an incoming identifier (upstream model/role/task name) to an assignment. Enables Hermes, Anthropic model names, and future task types to route without code changes.

| Field | Type | Rule |
|---|---|---|
| `incoming_identifier` | `str` | The string to match against request `model` field or equivalent. Exact match. |
| `assignment_id` | `str` | Must reference an existing `Assignment.id`. |
| `enabled` | `bool` | Disabled mappings are ignored (falls through to next rule or tier default). |
| `priority` | `int` | Tie-breaker if multiple mappings match same identifier; higher wins. Defaults to 0. |
| `notes` | `str` | Free-form operator note. |

**Validation**:
- `incoming_identifier` unique per (enabled) mapping.
- `assignment_id` must exist at write time (FK-style check, not strongly enforced on read).

**Lookup semantics**: When a request arrives with model `X`, the router consults mappings in descending `priority` order for the first enabled match. On no match, fall back to legacy tier-based resolution (current behavior).

---

## ProxyChain

Ordered list of chain entries + associated router config + schema version. Extends the existing structure at `src/core/proxy_chain.py`.

| Field | Type | Rule |
|---|---|---|
| `schema_version` | `str` (semver) | Current: `"2.0.0"`. Prior: `"1.0.0"` (pre-assignments). |
| `entries` | `list[ProxyEntry]` | Ordered; order reflects request-flow position. |
| `assignments` | `list[Assignment]` | NEW in v2. Unordered by routing; indexed by `id`. |
| `identifier_mappings` | `list[IdentifierMapping]` | NEW in v2. |
| `router` | `RouterConfig` | MODIFIED in v2: becomes thin projection over `assignments[kind="slot"]`. Kept in schema for backward compatibility during deprecation window. |

**State transitions**: any mutation goes through `ConfigResolver.set()` or `ProxyChain.apply_edit()`; invalid edits raise before persisting (FR-013).

**Persistence**: JSON file at `config/proxy_chain.json`. On load, if `schema_version` < current, `schema_migrations.migrate()` runs and rewrites the file (FR-023a) with migration-log entry (FR-023b).

---

## ProxyEntry

Unchanged from existing. Preserved shape to avoid breaking TUI/web-UI code already reading `proxy_chain.json`:

```python
@dataclass
class ProxyEntry:
    id: str
    name: str
    url: str
    auth_key: str = ""
    enabled: bool = True
    order: int = 0
    service_cmd: str = ""
    service_stop_cmd: str = ""
    health_path: str = "/health"
    port: int = 0
    timeout: int = 90
    extra_headers: dict = field(default_factory=dict)
    type: str = "http"
    model_prefixes: list = field(default_factory=list)
```

---

## RouterConfig

Legacy shape; v2 derives this dynamically from `ProxyChain.assignments[kind="slot"]` for backward compat during deprecation. Field shape unchanged.

---

## ConfigLayer

Enum of resolution layers, ordered by precedence (highest first):

```python
class ConfigLayer(str, Enum):
    CLI        = "cli"          # Highest precedence
    SHELL_ENV  = "shell_env"
    DOTENV     = "dotenv"
    STORED     = "stored"       # proxy_chain.json
    DEFAULT    = "default"      # Hardcoded fallbacks (lowest)
```

Precedence is data, not code — defined as a tuple at module scope so test-time reorder is trivial (Phase 2 test helper).

---

## ResolvedValue

| Field | Type | Rule |
|---|---|---|
| `field_path` | `str` | Dot-notation path, e.g., `"assignments.big.model"`. |
| `value` | `Any` | The resolved value after env-var expansion. |
| `source_layer` | `ConfigLayer` | Which layer supplied the value. |
| `raw_value` | `Any` | Pre-expansion value (shows `${VAR}` references as literals). |

Returned by every resolver read; the `source_layer` field is what makes provenance queryable (FR-006, SC-003).

---

## AuditLogEntry

Append-only record of a successful configuration write (FR-030).

| Field | Type | Rule |
|---|---|---|
| `seq` | `int` | Monotonic sequence number, unique per log file. |
| `timestamp` | `str` (ISO-8601 UTC) | When the write succeeded. |
| `principal` | `str` | Authenticated user identity (username or user-id). |
| `surface` | `ConfigLayer` | Which surface initiated the write (typically `cli` or `stored`). |
| `endpoint` | `str` | Endpoint invoked (for HTTP writes) or CLI verb (for CLI writes). |
| `field_path` | `str` | Dot-notation path that was written. |
| `before_value` | `Any` | Prior resolved value (secrets masked per FR-035). |
| `after_value` | `Any` | New resolved value (secrets masked). |
| `client_ip` | `str` (optional) | Origin IP for HTTP-initiated writes. |

Serialized as one JSON line per entry. File: `logs/config-audit.log`. Append-only; rotate with existing log-rotation tooling.

---

## RequestMetric

One row per request attempt. Primary attempt is `attempt_index = 0`; cascade fallbacks are `1, 2, ...` — all sharing the same `request_id`. Enables independent per-assignment and per-model success-rate queries (FR-033, SC-009, SC-010).

| Field | Type | Rule |
|---|---|---|
| `request_id` | `str` | Shared across all attempts for one incoming request. |
| `attempt_index` | `int` | 0 = primary target, 1+ = cascade fallbacks. |
| `timestamp` | `str` (ISO-8601 UTC) | When the attempt was dispatched. |
| `incoming_identifier` | `str` | The model/role name as received in the request. |
| `resolved_assignment_id` | `str` | Which assignment handled this attempt. |
| `resolved_model` | `str` | The actual model dispatched (after provider prefix resolution). |
| `resolved_provider` | `str` | Which provider served (OpenRouter, Anthropic, etc.). |
| `status` | `Literal["success", "failure", "cascaded"]` | `cascaded` = attempt failed AND a subsequent attempt was made. |
| `http_status` | `int` (optional) | Upstream HTTP status if applicable. |
| `latency_ms` | `int` | Wall-clock duration. |
| `tool_calls_attempted` | `int` | Count of tool-call attempts. |
| `tool_calls_succeeded` | `int` | Count of successful tool-calls. |
| `tokens_in`, `tokens_out` | `int` | Usage tokens if available. |

**Derived queries**:
- Per-assignment success rate (24h) = count(status="success" AND attempt_index=0) / count(attempt_index=0) grouped by resolved_assignment_id.
- Per-model success rate (24h) = count(status="success") / count(*) grouped by resolved_model, across all attempt_index values.
- Cascade rate per assignment = count(status="cascaded") / count(attempt_index=0) grouped by resolved_assignment_id.

Schema evolution strategy: extend existing `usage_tracking.db` table with new columns; backfill with NULL for old rows; migration path documented in `schema_migrations.py`.

---

## Entity relationships

```
ProxyChain (1)
    ├── entries: (N) ProxyEntry
    ├── assignments: (N) Assignment
    └── identifier_mappings: (N) IdentifierMapping
                                      │
                                      └── assignment_id → Assignment.id (FK)

ConfigResolver (singleton)
    ├── layers: (5) ConfigLayer (ordered)
    └── resolve(field_path) → ResolvedValue

AuditLogEntry (append-only stream)
    └── field_path ↔ ResolvedValue.field_path (audit references resolver paths)

RequestMetric (append-only rows)
    ├── resolved_assignment_id → Assignment.id (FK at write time)
    └── request_id clusters all attempts for one request
```

---

## State transition: config edit lifecycle

```text
Operator edits via (CLI | TUI | WebUI)
            │
            ▼
    validate(edit)  ──── invalid ───→ reject with specific error (FR-013)
            │
            ▼ valid
    apply to STORED layer ── fsync
            │
            ▼
    audit_log.append(AuditLogEntry)  (FR-030)
            │
            ▼
    emit change event to SSE subscribers
            │
            ├──→ WebUI updates view (FR-022)
            └──→ TUI redraws affected panels (R9)
            │
            ▼
    next incoming request resolves via the new value  (FR-007, SC-002)
    in-flight requests complete against the old value (FR-008, SC-006)
```

---

## State transition: request routing with cascade

```text
Incoming request with model = X
            │
            ▼
    IdentifierMapping.lookup(X) ── no match ──→ tier-based fallback
            │
            ▼ match
    Assignment A = mapped_assignment
            │
            ▼ attempt_index = 0
    dispatch to Provider(A)  ──→ success → RequestMetric(success, idx=0); done
            │
            ▼ failure (R8 triggers)
    RequestMetric(cascaded, idx=0)
            │
            ▼
    for each fallback in A.cascade:
        attempt_index += 1
        dispatch to Provider(fallback)  ──→ success → RequestMetric(success, idx=N); done
                                       ──→ failure → RequestMetric(cascaded, idx=N); continue
            │
            ▼ all fallbacks exhausted
    RequestMetric(failure, idx=final)
    return error to client
```

Per-assignment success rate counts row where `attempt_index=0`. Per-model success rate counts all rows. This is the mechanical enforcement of SC-010.
