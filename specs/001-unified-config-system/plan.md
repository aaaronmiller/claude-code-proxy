# Implementation Plan: Unified Configuration & Multi-Surface Control System

**Branch**: `001-unified-config-system` | **Date**: 2026-04-23 | **Spec**: [./spec.md](./spec.md)
**Input**: Feature specification from `specs/001-unified-config-system/spec.md`
**Constitution**: [/.specify/memory/constitution.md](../../.specify/memory/constitution.md) v1.0.0 (ratified 2026-04-23)

## Summary

Collapse the parallel tier-vs-slot configuration models into a single `Assignment` record, introduce a layered `ConfigResolver` with documented precedence (CLI > shell env > .env > stored config > defaults), expose the resolver through a write-path API shared by the CLI, TUI, and web UI, and extend `ProxyChain` to surface reordering/toggling and identifier-mapping through all four surfaces. The stored config gains a versioned schema with auto-migration. A configuration audit log and per-assignment/per-model request analytics make config changes and their routing consequences auditable and pivotable. Admin-only RBAC gates the network-reachable write endpoints; the CLI/TUI inherit host-level trust.

Legacy tier env vars (`BIG_MODEL`, `ENABLE_BIG_ENDPOINT`, etc.) remain functional during a deprecation window with warnings naming modern equivalents. `.envrc` is already removed; `.env` is the sole file-based environment source.

## Technical Context

**Language/Version**: Python 3.11 (proxy core); TypeScript 5.x / Svelte 4 (web UI)

**Primary Dependencies**:
- Backend: `fastapi`, `pydantic`, `python-dotenv`, `textual>=0.47.0` (existing TUI), `rich`, `httpx`, `uvicorn`. No new backend dependencies required; audit log is append-only plain-text file I/O; analytics extends the existing `usage_tracking.db` SQLite schema.
- Frontend: SvelteKit (existing). Candidate new dependency: `svelte-dnd-action` for chain reorder — decision deferred to Phase 0 research.
- CLI: stdlib `argparse` (already used in `start_proxy.py`).

**Storage**:
- Structured config persisted at `config/proxy_chain.json` (existing file, extended schema with `schema_version`, `assignments[]`, `identifier_mappings[]`).
- Secrets in `.env` only; stored config references them via `${VAR}` syntax.
- Config audit log: `logs/config-audit.log` (new, append-only).
- Request metrics: extended `usage_tracking.db` — add `assignment_id`, `incoming_identifier`, `attempt_index` columns to the existing request-level table (or a companion table if schema evolution is preferred).
- Schema migration log: `config/migrations/YYYY-MM-DD-<slug>.log` (new, written on auto-migrate).

**Testing**:
- `pytest` for Python (existing `tests/` tree).
- `vitest` for web UI components.
- Property-based precedence tests using `hypothesis` for the resolver — decision deferred to Phase 0 research.
- Adversarial audit-log completeness test (concurrent writes) required by SC-011.

**Target Platform**: Linux (WSL2 Ubuntu primary dev); macOS/Linux servers for deployment. Python 3.11+, Node 20+.

**Project Type**: Web-service with bundled TUI and SvelteKit web UI — existing layout keeps `src/` for Python, `web-ui/` for Svelte.

**Performance Goals**:
- Resolver lookup p95 < 1 ms per field (in-memory dict walk, no IO on hot path).
- Live-reload propagation < 5 s from persist to next request (SC-002, SC-008).
- TUI/WebUI edit persist < 200 ms end-to-end.
- Analytics query (per-assignment or per-model success rate, 24h window) < 10 s per query (SC-009).
- Audit log append < 10 ms per write (fsync tradeoff per Phase 0 research).

**Constraints**:
- Must not break public HTTP surfaces consumed by Claude Code, Qwen Code, Hermes agent runtime (Anthropic Messages API + OpenAI Chat Completions API compatibility). *Per Constitution §Engineering Constraints: Stable Public API.*
- In-flight streaming requests MUST NOT be interrupted by concurrent config changes (FR-008, SC-006).
- Single-process proxy; no multi-node config sync required.
- Legacy env vars MUST continue to resolve during deprecation window with warnings (FR-023, FR-024). *Per Constitution §Engineering Constraints: Deprecation Over Hard-Cut.*
- Secrets MUST NOT be stored as literals in any git-tracked file (FR-014, FR-015, FR-035). *Per Constitution §Engineering Constraints: No Secrets in Git-Tracked Files.*
- Web UI write endpoints MUST require admin role in existing RBAC (FR-026 through FR-029).
- Tier identifiers are fixed at `big`/`middle`/`small`; slot identifiers are free-form (FR-003, FR-003a).

**Scale/Scope**:
- Chain: ≤ 10 entries typical, no hard cap.
- Assignments: ≤ 20 typical (3 fixed tiers + 6 default slots + operator-defined custom slots).
- IdentifierMappings: ≤ 100 typical (upstream model names × Hermes roles × Anthropic task types).
- Concurrent config readers: the live request path (~100s/sec) plus 1–2 UI sessions.
- Config writers: one writer at a time; concurrent writes rare, last-write-wins acceptable with warning surfaced to both UIs.
- Request metrics retention: to be decided in Phase 0.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluating against `.specify/memory/constitution.md` v1.0.0. All six core principles and three engineering constraints enumerated:

| # | Principle / Constraint | Status | Rationale |
|---|---|---|---|
| I | Existing Research Before Building (NON-NEGOTIABLE) | ✅ | Pre-work surveyed `src/core/config.py`, `src/core/proxy_chain.py`, `src/cli/chain_tui.py`, `src/api/web_ui.py`, existing `usage_tracking.db` schema. Resolver is *extension* of existing config, not replacement. External solutions (`dynaconf`, `hydra`, `pydantic-settings`) considered; documented in Phase 0 research item #7. |
| II | Synthesis Verification | ✅ | Audit of existing paradigms cites specific file/line references. Phase 0 research will verify each cited line still reads as described before Phase 1 design commits. |
| III | Safe Destructive Operations (NON-NEGOTIABLE) | ✅ | Auto-migration (FR-023a) rewrites the stored config file — destructive. Mitigation: (a) migration writes preceded by copy-to-backup; (b) FR-023c requires startup refusal when migration would be unsafe; (c) migration log (FR-023b) captures every change. Alias cleanup (Phase 2 step 10) removes `ENABLE_BIG_ENDPOINT` from `.env.example` only — no live env manipulation. |
| IV | Changelog Discipline | ✅ | `CHANGELOG.md` will receive `[Unreleased]` entries for each merged phase. Enforced in Phase 2 sequencing. |
| V | Progressive Disclosure | ✅ | This plan ~280 lines, research.md ~150 lines target, data-model.md ~200 lines target — all under 300-line budget. Operational docs (precedence tables, migration recipes) live in separate files under `docs/` with pointers from here. |
| VI | Single Source of Truth for Configuration | ✅ | This feature *is* the principle's enabling mechanism. Post-migration, direct `os.environ.get` calls in feature code are constitutionally forbidden; grep-based CI check added in Phase 2 step 10. |
| E1 | Stable Public API | ✅ | New endpoints under `/api/config/*`, `/api/assignments/*`, `/api/chain/*`, `/api/identifier-mappings/*`, `/api/audit` are additions. Existing `/v1/messages` and `/v1/chat/completions` shapes unchanged. |
| E2 | No Secrets in Git-Tracked Files | ✅ | FR-014 mandates `${VAR}` references; FR-015 warns on literal secrets in stored config; FR-035 enforces masking in audit log and analytics output. |
| E3 | Deprecation Over Hard-Cut | ✅ | FR-023/FR-024 provide alias + warning for legacy env vars. Removal of `ENABLE_BIG_ENDPOINT`-style toggles documented in Phase 2 but gated on deprecation cycle. |

**Result**: All gates pass. Complexity justifications captured at the bottom for architectural decisions that expand surface area. Re-check after Phase 1 design.

## Project Structure

### Documentation (this feature)

```text
specs/001-unified-config-system/
├── plan.md                     # This file
├── spec.md                     # Feature specification (post-/speckit.clarify)
├── research.md                 # Phase 0 output — resolves unknowns
├── data-model.md               # Phase 1 output — entity schemas + state transitions
├── quickstart.md               # Phase 1 output — operator walkthrough
├── contracts/                  # Phase 1 output
│   ├── config-api.yaml         # OpenAPI 3 for all config HTTP endpoints
│   └── resolver.md             # Internal contract for ConfigResolver class
├── checklists/
│   └── requirements.md         # From /speckit.specify validation
└── tasks.md                    # Phase 2 output (from /speckit.tasks, NOT this plan)
```

### Source code (repository root)

```text
src/                                          # Existing Python proxy core
├── core/
│   ├── config.py                             # MODIFIED: thin alias shim over ConfigResolver
│   ├── config_resolver.py                    # NEW: layered resolver + precedence walker
│   ├── assignments.py                        # NEW: Assignment dataclass + registry
│   ├── identifier_mapping.py                 # NEW: incoming-identifier → assignment lookup
│   ├── proxy_chain.py                        # MODIFIED: extended schema
│   └── schema_migrations.py                  # NEW: versioned auto-migration + log writer
├── services/
│   ├── observability/
│   │   ├── audit_log.py                      # NEW: append-only audit writer, secret masking
│   │   └── request_metrics.py                # MODIFIED/NEW: adds assignment_id, attempt_index
│   └── usage/
│       └── usage_tracker.py                  # MODIFIED: records new dimensions
├── cli/
│   ├── chain_tui.py                          # MODIFIED: writes via resolver API
│   ├── assignment_tui.py                     # NEW: assignment editor panel
│   ├── identifier_mapping_tui.py             # NEW: mapping table editor panel
│   └── overlay.py                            # NEW: argparse → resolver CLI-layer adapter
├── api/
│   ├── config_api.py                         # NEW: config/assignments/chain/identifier-mappings CRUD
│   ├── config_events.py                      # NEW: SSE or WS stream for live-reload
│   ├── audit_api.py                          # NEW: /api/audit — admin-only query
│   ├── analytics_api.py                      # MODIFIED: adds per-assignment group-by
│   ├── users_rbac.py                         # EXISTING, REUSED: admin-role gate
│   └── web_ui.py                             # MODIFIED: mounts new routers
start_proxy.py                                # MODIFIED: expanded argparse; feeds overlay layer
config/
├── proxy_chain.json                          # MODIFIED: assignments, identifier_mappings, schema_version
└── migrations/                               # NEW: per-upgrade migration logs
logs/
└── config-audit.log                          # NEW: append-only audit of successful config writes
tests/
├── contract/
│   ├── test_resolver_precedence.py
│   ├── test_config_api_contract.py
│   └── test_audit_completeness.py
├── integration/
│   ├── test_cross_surface_propagation.py
│   ├── test_inflight_isolation.py
│   └── test_schema_migration.py
└── unit/
    ├── test_identifier_mapping.py
    ├── test_secret_masking.py
    └── test_deprecation_warning.py
web-ui/
├── src/
│   ├── routes/
│   │   ├── chain/                            # MODIFIED: drag-and-drop reorder
│   │   ├── assignments/                      # NEW: tier + slot editor page
│   │   ├── identifier-mappings/              # NEW: mapping-table editor page
│   │   ├── audit/                            # NEW: config audit log viewer (admin)
│   │   └── analytics/                        # MODIFIED: per-assignment pivot
│   ├── lib/
│   │   ├── services/
│   │   │   ├── config-client.ts              # NEW
│   │   │   └── audit-client.ts               # NEW
│   │   └── stores/
│   │       └── config-store.ts               # NEW: reactive + SSE/WS subscriber
│   └── components/
│       ├── AssignmentEditor.svelte           # NEW
│       ├── IdentifierMappingTable.svelte     # NEW
│       ├── ChainList.svelte                  # MODIFIED: drag-and-drop
│       └── ProvenanceBadge.svelte            # NEW
```

**Structure Decision**: Existing layout splits Python backend (`src/`) from SvelteKit frontend (`web-ui/`). Extend in place — no restructure. New Python modules land alongside existing peers (`config_resolver.py` next to `config.py`, observability under existing `src/services/`). New Svelte routes next to existing `routes/chain/` and `routes/analytics/`.

## Phase 0 — Research

### Research tasks

1. **`svelte-dnd-action` vs HTML5 native DnD** — bundle-size, a11y, keyboard-reorder parity with TUI.
2. **Live-reload transport: SSE, WebSocket, or polling** — existing `websocket_live.py`/`websocket_logs.py` establish WS precedent; evaluate reuse vs SSE simplicity.
3. **File-watcher for external edits** to `.env` / `proxy_chain.json` — `watchdog` dep, polling, or explicit reload command.
4. **`hypothesis` property-based tests for precedence** — worth a dev dep given only 5 layers?
5. **Deprecation-warning emission strategy** — inline per resolution vs single-shot startup summary.
6. **Env-var reference expansion point** — read-time vs persist-time; stay consistent with `ProxyEntry.effective_auth_key()` at `proxy_chain.py:58-65`.
7. **Existing-solution survey (Principle I)** — `dynaconf`, `hydra`, `pydantic-settings`, `configobj`. Document why ConfigResolver instead.
8. **Cascade trigger semantics** — what constitutes "model failure" for fallback? HTTP 4xx/5xx, timeouts, response patterns? Audit existing `model_manager.py`.
9. **TUI auto-refresh on external edit** — `textual` reactive binding capability; parity with FR-022 web-UI-side.
10. **Web UI stale-cache indicator UX** — visual indicator when SSE/WS disconnects.
11. **Analytics data retention policy** — audit existing `usage_tracking.db` pattern.
12. **Secret-masking regex coverage (FR-035)** — extend `API_KEY_PATTERNS` in `config.py:25-34` to OAuth/JWT.
13. **Migration safety heuristic (FR-023c)** — decision tree for when auto-migration halts.

**Output**: `specs/001-unified-config-system/research.md`.

## Phase 1 — Design & Contracts

**Prerequisites**: `research.md` complete.

- **Entity work** → `data-model.md`: `Assignment`, `ProxyEntry`, `ProxyChain`, `RouterConfig`, `IdentifierMapping`, `ConfigLayer`, `ResolvedValue`, `AuditLogEntry`, `RequestMetric`. Fields, validation rules, state transitions.
- **API contracts** → `contracts/config-api.yaml` (OpenAPI 3, all HTTP endpoints, admin-role security scheme), `contracts/resolver.md` (internal ConfigResolver contract).
- **Quickstart** → `quickstart.md`: four-user-story walkthrough end-to-end.
- **Agent context update** — run `.specify/scripts/bash/update-agent-context.sh claude` after Phase 1 artifacts land.
- **Post-design re-check** — re-evaluate Constitution Check; add Complexity Tracking rows if new violations introduced.

## Phase 2 — Implementation (tracked in tasks.md, out of scope here)

1. **Foundation** — resolver, Assignment, IdentifierMapping, ConfigLayer; unit + property tests.
2. **Schema + migrations** — versioned `proxy_chain.json`; legacy-to-current migrator with log.
3. **Integration** — `Config` delegates; ProxyChain extended; legacy alias layer with warnings.
4. **CLI** — argparse expanded; `overlay.py` feeds resolver CLI layer.
5. **Observability** — audit log writer; request metrics dimensions; adversarial completeness test.
6. **HTTP API** — CRUD endpoints; admin-role gate from `users_rbac.py`.
7. **Live-reload transport** — SSE or WS per Phase 0.
8. **TUI** — new assignment + identifier-mapping panels; writes via API.
9. **Web UI** — drag-and-drop chain, assignment editor, identifier-mapping table, audit viewer, analytics pivot.
10. **Cleanup** — remove legacy toggles from `.env.example`; docs under `docs/`; CI grep check for direct `os.environ.get`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| New `src/core/config_resolver.py` module (fourth config-adjacent file) | Single-responsibility layered resolver with provenance; keeps `config.py` viable as alias shim during deprecation | Merging into `config.py` would entangle resolver with legacy flat-env-var reader and complicate deprecation cutover |
| Stored config extended (not replaced) rather than new format | Preserves forward compat with existing TUI/web-UI code reading `proxy_chain.json` | New `config/assignments.json` would force two-file sync and break existing tooling (`proxies config show`) |
| Change-event transport (SSE or WS) added for live-reload | Required by FR-007 and User Story 3 | Polling adds latency and wastes CPU; explicit reload commands regress UX back to restart-tax |
| Separate audit-log file (not reusing telemetry DB) | Per Q4 clarification; audit needs distinct retention, access control, survives DB corruption | Coupling audit to telemetry entangles unrelated concerns and complicates SIEM export |
| `RequestMetric.attempt_index` dimension beyond existing `usage_tracker` schema | Required by FR-033 — only way to distinguish role-config failures from model-capability failures when cascade is active | Collapsing to one row per request loses fallback-attempt trail and fails SC-010 |
| New `IdentifierMapping` entity (beyond Assignment) | Per Q2 clarification — upstream identifiers (Anthropic names, Hermes roles) map dynamically to assignments without code changes | Embedding mapping rules directly in Assignment would force identifier namespace to be per-assignment; mapping table is the shared lookup |
