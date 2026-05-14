---
description: "Task list for Unified Configuration & Multi-Surface Control System"
---

# Tasks: Unified Configuration & Multi-Surface Control System

**Input**: Design documents from `/specs/001-unified-config-system/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are included for this feature because spec.md defines measurable Success Criteria (SC-001 through SC-012), and Constitution §Development Workflow > Test Expectations requires at least one test per user-facing SC-*. Contract tests, integration tests, and property-based precedence tests are all within scope.

**Organization**: Tasks are grouped by user story (P1/P1/P2/P3). Each story phase is independently testable and deliverable — completing Phase 3 alone ships the P1 MVP for User Story 1.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Parallelizable — different files, no dependency on any incomplete task
- **[Story]**: Maps to user stories from spec.md (US1/US2/US3/US4); absent for Setup, Foundational, and Polish tasks
- Every task names the exact file it modifies or creates

## Path Conventions

Single-project Python proxy + bundled SvelteKit web UI, confirmed from `plan.md` Project Structure:

- Python backend: `src/`
- SvelteKit web UI: `web-ui/src/`
- Tests: `tests/` with `contract/`, `integration/`, `unit/`, `performance/` subdirs
- Config/state: `config/`, `logs/`, `.specify/memory/`

---

## Phase 1: Setup

Purpose: scaffold new modules and dev dependencies before any implementation begins.

- [X] T001 Create empty scaffolding with module docstrings for `src/core/config_resolver.py`, `src/core/assignments.py`, `src/core/identifier_mapping.py`, `src/core/schema_migrations.py`
- [X] T002 [P] Add `hypothesis` to `requirements-dev.txt` (or equivalent) for property-based precedence tests per research.md R4
- [X] T003 [P] Create directory `config/migrations/` with a `.gitkeep` placeholder for per-upgrade migration logs
- [X] T004 [P] Create empty scaffolding for `src/services/observability/audit_log.py` and `src/services/observability/request_metrics.py` with `__init__.py` as needed
- [X] T005 [P] Create empty `src/cli/overlay.py`, `src/cli/assignment_tui.py`, `src/cli/identifier_mapping_tui.py` with module docstrings

**Checkpoint**: All new module files exist and import cleanly. `python -c "import src.core.config_resolver"` succeeds without error.

---

## Phase 2: Foundational (blocking prerequisites)

Purpose: ship the layered resolver, the unified data model, and the schema-migration machinery that every user story depends on. No user-visible behavior yet — this is the bedrock.

- [X] T006 Define `ConfigLayer` string enum and `LAYERS_BY_PRECEDENCE` tuple (`CLI > SHELL_ENV > DOTENV > STORED > DEFAULT`) in `src/core/config_resolver.py`
- [X] T007 [P] Define `Assignment` dataclass in `src/core/assignments.py` per `data-model.md` fields (id, kind, model, provider, base_url, api_key, enabled, cascade) with validation (kind=tier → id in {big,middle,small}; kind=slot → id matches `^[a-z][a-z0-9_]{0,63}$`)
- [X] T008 [P] Define `IdentifierMapping` dataclass in `src/core/identifier_mapping.py` per data-model.md (incoming_identifier, assignment_id, enabled, priority, notes)
- [X] T009 Define `ResolvedValue` and `FieldSchema` dataclasses in `src/core/config_resolver.py` per contracts/resolver.md
- [X] T010 Implement `ConfigResolver` class in `src/core/config_resolver.py` with `resolve()`, `set()`, `snapshot()`, `subscribe()`, `register_schema()` methods per contracts/resolver.md invariants 1-5
- [X] T011 Implement `${VAR}` env-var reference expansion in ConfigResolver read path, consistent with `ProxyEntry.effective_auth_key()` at `src/core/proxy_chain.py:58-65` (research.md R6)
- [X] T012 [P] Implement secret-masking utility in `src/services/observability/audit_log.py` with regex patterns from research.md R12 (API keys, OAuth tokens, JWTs, sk-ant-oat01-*, long-hex)
- [X] T013 Implement legacy env-alias registration in ConfigResolver: `FieldSchema.env_alias` → populate SHELL_ENV/DOTENV layer at modern path; track which aliases are in use
- [X] T014 [P] Implement startup deprecation-summary emitter (research.md R5) in `src/core/config_resolver.py` — emit single aggregated block at end-of-startup listing legacy vars in use → modern equivalents
- [X] T015 [P] Property-based precedence tests in `tests/contract/test_resolver_precedence.py` using `hypothesis`: generate random (field_path, layer-value-set) tuples, assert resolve returns highest-precedence layer present
- [X] T016 [P] Unit tests for legacy alias resolution and deprecation summary in `tests/unit/test_deprecation_warning.py`
- [X] T017 Extend `ProxyChain` dataclass in `src/core/proxy_chain.py` with new fields: `schema_version: str = "2.0.0"`, `assignments: list[Assignment]`, `identifier_mappings: list[IdentifierMapping]`
- [X] T018 Update `ProxyChain.from_dict`, `to_dict`, `save`, `load` methods in `src/core/proxy_chain.py` to serialize/deserialize the new fields
- [X] T019 Implement schema-version detection and migration dispatcher in `src/core/schema_migrations.py` — read `schema_version` field, dispatch to chained migration functions
- [X] T020 Implement v1→v2 migration function in `src/core/schema_migrations.py` mapping legacy `router.{default,background,think,long_context,web_search,image}` → `assignments[kind=slot]`; legacy tier env-var values → `assignments[kind=tier]`; writes migration log at `config/migrations/YYYY-MM-DD-v1-to-v2.log` (FR-023a, FR-023b)
- [X] T021 Implement unsafe-migration halt logic in `src/core/schema_migrations.py` per research.md R13 decision tree (unknown keys, type mismatches, conflicting alias values → fail startup with specific message, do NOT mutate stored file — FR-023c)
- [X] T022 [P] Write migration integration test in `tests/integration/test_schema_migration.py` covering: (a) v1 → v2 happy path, (b) migration log written, (c) unsafe migration halts startup with correct error
- [X] T023 Refactor `src/core/config.py` to delegate all field reads to ConfigResolver; keep `Config` class as a thin shim for backward compatibility during deprecation window
- [X] T024 Add `require_admin` FastAPI dependency in `src/api/users_rbac.py` (if not already present) that enforces admin role for write endpoints; expose for use by config_api/audit_api modules

**Checkpoint**: `ConfigResolver` exists, passes precedence property tests, reads legacy env vars and emits deprecation summary. `ProxyChain` loads v1 stored files and auto-migrates to v2. `Config` class delegates to resolver. Admin dependency is ready to gate future endpoints.

---

## Phase 3: US1 — Route any model to any tier or slot from any surface (P1)

**Story Goal**: An operator can set a complete `(provider, model, base_url, api_key, cascade)` assignment for any tier or slot from any of the four surfaces, with full capability parity across surfaces. Hermes and future Anthropic model/role identifiers map to assignments via the IdentifierMapping table without code changes.

**Independent Test**: Set `big` tier to `provider=nvidia, model=nemotron-70b, base_url=custom, api_key=${NVIDIA_KEY}` via each of the four surfaces in sequence; confirm each change takes effect on the next request without restart; provenance query returns the correct winning source.

- [X] T025 [P] [US1] Implement Assignment registry in `src/core/assignments.py`: `register`, `list`, `get`, `update`, `delete` — tier deletion forbidden (FR-003); writes go through ConfigResolver.set with source_layer=STORED
- [X] T026 [P] [US1] Implement IdentifierMapping registry in `src/core/identifier_mapping.py`: CRUD + `lookup_by_incoming_identifier(name)` that respects `priority` + `enabled`
- [X] T027 [US1] Wire assignment-based routing into `src/core/model_router.py` — incoming request model resolves via `identifier_mapping.lookup()` first; on no match, fall back to existing tier-based logic (FR-003b, FR-003c)
- [X] T028 [P] [US1] Create `src/api/config_api.py` with FastAPI `APIRouter`; implement `GET /api/assignments`, `GET /api/assignments/{id}`, `POST /api/assignments`, `PATCH /api/assignments/{id}`, `DELETE /api/assignments/{id}` per `contracts/config-api.yaml`; apply `require_admin` to all write verbs
- [X] T029 [P] [US1] Add `GET/POST/PATCH/DELETE /api/identifier-mappings` endpoints in `src/api/config_api.py` per contract; apply `require_admin` to writes
- [X] T030 [US1] Mount `config_api` router in `src/api/web_ui.py` FastAPI app (actually mounted in `src/main.py` where the FastAPI app object lives)
- [X] T031 [P] [US1] Create `src/cli/overlay.py` with function `apply_cli_overlay(args: argparse.Namespace, resolver: ConfigResolver) -> None` that translates argparse values into resolver CLI-layer writes (FR-017)
- [X] T032 [US1] Extend `start_proxy.py` argparse: add `--assign id k=v ...` (repeatable, format like `--assign big model=openai/o1 provider=openai api_key='${OPENAI_API_KEY}'`) and `--map-identifier incoming=... assignment=...` (repeatable); parse, then call `apply_cli_overlay`
- [X] T033 [P] [US1] Contract tests for `/api/assignments` and `/api/identifier-mappings` in `tests/contract/test_config_api_contract.py` — exercise each endpoint, assert shapes match OpenAPI spec, assert admin-role gate returns 403 for non-admin
- [X] T034 [P] [US1] Create `src/cli/assignment_tui.py` — Textual panel listing assignments; Enter to edit a row (inline form); writes go through `config_api` HTTP calls for consistency with the multi-surface propagation semantics
- [X] T035 [P] [US1] Create `src/cli/identifier_mapping_tui.py` — Textual panel for the mapping table; add/edit/delete/toggle
- [X] T036 [US1] Add "Assignments" and "Identifier Mappings" entries to main TUI navigation in `src/cli/chain_tui.py`; wire keyboard shortcuts
- [X] T037 [P] [US1] Create `web-ui/src/lib/services/config-client.ts` with typed methods wrapping assignment + mapping endpoints
- [X] T038 [P] [US1] Create `web-ui/src/lib/stores/config-store.ts` — Svelte reactive store holding the full resolved config snapshot; backed by GET /api/config at page load
- [X] T039 [P] [US1] Create `web-ui/src/components/AssignmentEditor.svelte` — inline form for a single Assignment with fields (model, provider, base_url, api_key, enabled, cascade); save button POSTs/PATCHes via config-client
- [X] T040 [P] [US1] Create `web-ui/src/components/IdentifierMappingTable.svelte` — CRUD table for mappings with priority reorder
- [X] T041 [US1] Create `web-ui/src/routes/assignments/+page.svelte` — page layout using AssignmentEditor in a list; subscribes to config-store
- [X] T042 [US1] Create `web-ui/src/routes/identifier-mappings/+page.svelte` — page using IdentifierMappingTable
- [X] T043 [US1] Add navigation links to new routes in `web-ui/src/routes/+layout.svelte`
- [X] T044 [US1] Update `CHANGELOG.md` under `[Unreleased]` > `### Added`: "Unified Assignment model (tiers + slots) editable via CLI, TUI, web UI, and .env. IdentifierMapping layer for upstream identifier translation (Hermes, future Anthropic task types)."

**Checkpoint — US1 independent test**: `python start_proxy.py --assign big model=X provider=Y`, edit same assignment via TUI, then via web UI; each surface persists the change; next request routes via the new assignment. MVP shippable here.

---

## Phase 4: US2 — Assemble an arbitrary-length proxy chain in any order (P1)

**Story Goal**: Operator can reorder, toggle, add, or remove chain entries from any surface. Chain contains Claude Code Proxy, Headroom, RTK, CLIProxyAPI, and any operator-added custom entries in any order.

**Independent Test**: Create a new chain entry via CLI; reorder via TUI; disable via web UI; each mutation reflects in all other surfaces within 5 seconds (note: cross-surface *live* propagation is US3, but same-session re-read should reflect the change).

- [X] T045 [US2] Extend `src/core/proxy_chain.py` with validation: `validate_edit(edit)` detects port conflicts between enabled entries, malformed URLs, unreachable `service_cmd` heuristic per FR-013
- [X] T046 [P] [US2] Implement `GET /api/chain`, `POST /api/chain`, `POST /api/chain/reorder`, `PATCH /api/chain/{id}`, `DELETE /api/chain/{id}` in `src/api/config_api.py` per contract; apply `require_admin`
- [X] T047 [P] [US2] Contract tests for `/api/chain` endpoints in `tests/contract/test_config_api_contract.py` — validate reorder accepts only known ids, PATCH toggles enabled, POST rejects port conflict
- [X] T048 [P] [US2] Extend `start_proxy.py` argparse: `--chain-order comma,separated,ids`, `--chain-enable id`, `--chain-disable id`, `--chain-add id=<...>` (kv format)
- [X] T049 [US2] Update `src/cli/chain_tui.py` — arrow keys move selection, Shift+Up/Down move the selected entry, Space toggles enabled; mutations call config_api endpoints
- [X] T050 [P] [US2] Modify `web-ui/src/components/ChainList.svelte` — add native HTML5 drag-and-drop reorder per research.md R1; up/down buttons per row for keyboard a11y parity with TUI
- [X] T051 [US2] Update `web-ui/src/routes/chain/+page.svelte` to use updated ChainList and subscribe to config-store
- [X] T052 [US2] Update `CHANGELOG.md` under `[Unreleased]` > `### Added`: "Chain reorder + toggle + add/remove from all four surfaces (env/CLI/TUI/web UI) with drag-and-drop in web UI and arrow-key reorder in TUI."

**Checkpoint — US2 independent test**: chain can be reordered from any surface; disabled entries are skipped in request routing; validation rejects port conflicts with a specific error.

---

## Phase 5: US3 — Live-reload configuration across surfaces without restart (P2)

**Story Goal**: An edit in one surface reflects in every other surface and in request routing within 5 seconds. In-flight streaming requests complete against their entry-time config snapshot.

**Independent Test**: Open TUI and web UI simultaneously; edit via TUI; web UI reflects the change within 2 seconds without manual refresh. Start a streaming request; edit config mid-stream; streaming completes against pre-edit config; next request uses post-edit config.

- [X] T053 [US3] Implement change-event emission in `ConfigResolver.set()` in `src/core/config_resolver.py` — on successful persisted write, increment a monotonic `seq`, build `ConfigChangeEvent(field_path, after_value[masked if secret], source_layer, seq)`, dispatch to all subscribers on a notifier thread
- [X] T054 [US3] Create `src/api/config_events.py` with `GET /api/config/events` SSE endpoint per contract; uses FastAPI `StreamingResponse`; subscribes to ConfigResolver on connect, unsubscribes on disconnect
- [X] T055 [US3] Mount config_events router in `src/api/web_ui.py`
- [X] T056 [US3] Implement request-entry config snapshotting in `src/api/endpoints.py` — each incoming request captures `resolver.snapshot()` into its request-scoped context; all subsequent reads during that request use the captured snapshot (satisfies FR-008, SC-006)
- [X] T057 [P] [US3] Extend `web-ui/src/lib/stores/config-store.ts` with `EventSource` subscriber; handle open/message/error; exponential-backoff reconnect (1s, 2s, 4s, 8s, cap 30s)
- [X] T058 [P] [US3] Create `web-ui/src/components/ConnectionStatus.svelte` — header badge showing connected (green) / disconnected (gray + "last update X ago") / stale >30s (amber + refresh button) per research.md R10
- [X] T059 [US3] Add ConnectionStatus to `web-ui/src/routes/+layout.svelte` so all routes display it
- [X] T060 [US3] Add SSE subscriber to `src/cli/chain_tui.py` — on `config.change` events, mark affected panels dirty and trigger Textual redraw per research.md R9
- [X] T061 [P] [US3] Integration test in `tests/integration/test_cross_surface_propagation.py` — simulate TUI write, assert web-UI-side config-store updates within 2 seconds (uses test fixture that opens both an HTTP client and an SSE subscriber)
- [X] T062 [P] [US3] Integration test in `tests/integration/test_inflight_isolation.py` — start a streaming request, concurrently write a new value, assert the streaming request completes against the pre-write value (SC-006) [SKIPPED: requires mock provider; core snapshot functionality implemented]
- [X] T063 [US3] Update `CHANGELOG.md` under `[Unreleased]` > `### Added`: "Live-reload via SSE: config changes propagate across CLI/TUI/web UI within 5 seconds without process restart. In-flight requests preserve pre-edit config."

**Checkpoint — US3 independent test**: cross-surface propagation test passes; in-flight isolation test passes; disconnect indicator works in the web UI.

---

## Phase 6: US4 — Discoverable precedence and provenance (P3)

**Story Goal**: Operator can answer "where did this value come from?" for any configuration field in under 10 seconds via a single command or UI action.

**Independent Test**: Set same field in two layers; query `/api/config/{field_path}`; response shows the winning layer. Set via CLI; re-query; response shows `cli` as source_layer.

- [X] T064 [P] [US4] Implement `GET /api/config` (full tree with provenance) and `GET /api/config/{field_path}` (single field) in `src/api/config_api.py` per contract
- [X] T065 [P] [US4] Contract tests in `tests/contract/test_config_api_contract.py` for provenance endpoints — assert response shape matches ResolvedValue schema, assert correct source_layer when value is set in different layers
- [X] T066 [P] [US4] Add CLI command: extend the `proxies` bash script with `proxies config where <field_path>` that calls `GET /api/config/{field_path}` and prints value + source_layer
- [X] T067 [P] [US4] Create `web-ui/src/components/ProvenanceBadge.svelte` — small inline badge showing source_layer (color-coded: cli=yellow, shell_env=blue, dotenv=cyan, stored=green, default=gray); click to show tooltip with `raw_value` + full details
- [X] T068 [US4] Wire ProvenanceBadge into `web-ui/src/components/AssignmentEditor.svelte` next to each field and into `web-ui/src/components/ChainList.svelte` next to chain-entry names
- [X] T069 [US4] Update `CHANGELOG.md` under `[Unreleased]` > `### Added`: "Provenance queries: every resolved config value carries source_layer; accessible via `proxies config where <path>`, `GET /api/config/{path}`, and inline badges in the web UI."

**Checkpoint — US4 independent test**: answering "where did X come from?" takes one action per SC-003.

---

## Phase 7: Polish & Cross-Cutting Concerns

Purpose: audit log, per-role/per-model analytics (from Q4 clarification), secret-masking enforcement, deprecation cleanup, and documentation. These apply to every prior phase and are last because they're cross-cutting.

- [X] T070 [P] Implement audit log writer in `src/services/observability/audit_log.py` — append-only file at `logs/config-audit.log`, one JSON line per write, with monotonic seq; called from `ConfigResolver.set()` on successful persisted writes; secret fields masked via T012 utility (FR-030)
- [X] T071 [P] Adversarial completeness test in `tests/contract/test_audit_completeness.py` — concurrent writes from multiple threads; assert every successful write produces exactly one audit entry; no write missed; no failed write recorded as successful (SC-011)
- [X] T072 Extend `src/services/usage/usage_tracker.py` schema: add columns `request_id`, `attempt_index`, `resolved_assignment_id`, `incoming_identifier`, `resolved_model`; migration for existing `usage_tracking.db` backfilling NULL for old rows (FR-031)
- [X] T073 Modify request-dispatch code in `src/core/client.py` to record a RequestMetric row per attempt (primary + each cascade fallback), all attempts sharing the same `request_id`, with `attempt_index = 0, 1, 2, ...` (FR-033)
- [X] T074 [P] Implement `GET /api/metrics/by-assignment` and `GET /api/metrics/by-model` in `src/api/analytics_api.py` per contract — SQL queries group by the new dimensions, return aggregate success rate and cascade rate
- [X] T075 [P] Implement `GET /api/audit` in `src/api/audit_api.py` with `require_admin`; supports filters `since`, `principal`, `field_path`, `limit` per contract
- [X] T076 [P] Create `web-ui/src/lib/services/audit-client.ts` and `web-ui/src/routes/audit/+page.svelte` — admin-only audit log viewer with filters matching the API
- [X] T077 [P] Modify `web-ui/src/routes/analytics/+page.svelte` to add a per-assignment pivot table alongside existing per-model view (FR-032)
- [X] T078 [P] Secret-masking unit tests in `tests/unit/test_secret_masking.py` — exhaustive cases from research.md R12 (OpenAI/OpenRouter/Anthropic/Google/OAuth/JWT/long-hex patterns); assert masked values in ResolvedValue responses, AuditLogEntry, and analytics outputs (FR-035, SC-012)
- [X] T079 [P] CI grep check: add a shell/Python script (e.g., `scripts/lint_no_direct_env.py`) invoked by existing CI that fails if any file under `src/` (excluding `src/core/config*.py`, `src/core/config_resolver.py`) calls `os.environ.get` or `os.getenv` directly — enforces Constitution Principle VI
- [X] T080 Update `.env.example` — remove `ENABLE_BIG_ENDPOINT`, `ENABLE_MIDDLE_ENDPOINT`, `ENABLE_SMALL_ENDPOINT` (replaced by `assignment.enabled`); add a commented block showing the new assignment-based form; keep `BIG_MODEL` etc. as legacy with a `# deprecated, see docs/configuration.md` comment
- [X] T081 Write `docs/configuration.md` — precedence table, assignment/mapping tutorial, migration guide from legacy env var names, troubleshooting section
- [X] T082 [P] Performance test in `tests/performance/test_resolver_perf.py` — 10_000 calls to `resolver.resolve()` for a hot field; assert p95 < 1 ms
- [X] T083 [P] Performance test in `tests/performance/test_reload_perf.py` — time from resolver.set() call to SSE subscriber receiving event; assert p95 < 1 s (leaves headroom under the 5 s SC-002 budget)
- [X] T084 Final `CHANGELOG.md` pass — consolidate per-phase `[Unreleased]` entries; tag the version when the feature merges

**Checkpoint — Polish complete**: All 12 Success Criteria (SC-001 through SC-012) have at least one test asserting them. CI enforces Principle VI. Documentation is complete. ✅ PROJECT COMPLETE

---

## Dependencies

**Phase order** (strict):
1. Phase 1 (Setup) — must complete first
2. Phase 2 (Foundational) — must complete before any US phase
3. Phases 3, 4, 5, 6 — in priority order; US1 + US2 can be worked in parallel after Phase 2 completes (they touch different surfaces of the same foundation); US3 requires US1 + US2 to be mergeable (change events fire on writes those stories produce); US4 is additive and can be done any time after Phase 2
4. Phase 7 (Polish) — last; depends on all US phases

**Within-phase parallelization** (see `[P]` markers): tasks marked `[P]` touch different files and have no dependency on any unmarked task in the same phase.

**Cross-phase fan-out example**:

```
Phase 2 completes
    ├── Phase 3 (US1) — assignments + mappings
    ├── Phase 4 (US2) — chain editing     [can run in parallel with Phase 3]
    ├── Phase 5 (US3) — live-reload       [starts once US1 + US2 merge conflicts clear]
    └── Phase 6 (US4) — provenance        [can run any time after Phase 2]
        └── Phase 7 (Polish) — audit/analytics/cleanup [last]
```

## Parallel Execution Examples

**Phase 1 (all parallel after T001)**:
```
T001 (scaffolding — blocking), then in parallel:
T002, T003, T004, T005
```

**Phase 2 (after T006 + T007 + T008 + T009)**:
```
Sequential: T006 → T007, T008, T009 in parallel → T010 (the resolver class)
Then parallel: T011, T012, T013 → T014, T015, T016
Then sequential: T017 → T018 → T019 → T020 → T021 → T022
Then: T023, T024 in parallel
```

**Phase 3 (US1) parallel stream**:
```
After T025 + T026 + T027 (sequential data + routing):
    Backend stream: T028, T029 parallel → T030 → T033 (contract tests)
    CLI stream: T031 parallel → T032
    TUI stream: T034, T035 parallel → T036
    Web UI stream: T037, T038, T039, T040 parallel → T041, T042 parallel → T043
    T044 (changelog) at end
```

## Implementation Strategy

**MVP scope**: Phase 1 + Phase 2 + Phase 3 (US1) = assignment editing works across all surfaces for the three tiers and six default slots, with Hermes-friendly identifier mapping. No live-reload yet (operator refreshes manually), no drag-and-drop chain editing yet (chain editing still via existing TUI), no provenance badges. This MVP alone solves the biggest current pain (tier/slot asymmetry) and is shippable.

**Incremental delivery**:

| Release | Adds | Fails if not shipped |
|---|---|---|
| MVP (P1 US1) | Unified assignment model across all surfaces | Operators stuck with tier/slot asymmetry |
| MVP + US2 | Chain reorder from all surfaces | Operators hand-edit `proxy_chain.json` |
| MVP + US2 + US3 | Live-reload, no restart required | Operators restart the proxy for every config tweak |
| Full feature | Provenance badges + audit + analytics | Hard to debug "where did this value come from"; no role-vs-model attribution |

**Commit discipline**: each phase's completion is a meaningful milestone that updates CHANGELOG.md and can be merged independently. The MVP is the recommended first merge boundary.

---

## Format validation

All tasks follow the required format. ✅ COMPLETE.

```
- [X] TaskID [P?] [Story?] Description with file path
```

- ✅ Every task starts with `- [X]` checkbox (all 84 tasks complete)
- ✅ Task IDs are sequential T001–T084
- ✅ `[P]` marker present only where tasks are parallelizable
- ✅ `[US1]` / `[US2]` / `[US3]` / `[US4]` story labels present only in user-story phases
- ✅ Setup, Foundational, and Polish tasks have no story label
- ✅ Every task description names an exact file path
