# Implementation Plan: Unified Configuration & Multi-Surface Control System

**Branch**: `001-unified-config-system` | **Date**: 2026-04-23 | **Spec**: [./spec.md](./spec.md)
**Input**: Feature specification from `specs/001-unified-config-system/spec.md`

## Summary

Collapse the parallel tier-vs-slot configuration models into a single `Assignment` record, introduce a layered `ConfigResolver` with documented precedence (CLI > shell env > .env > stored config > defaults), expose the resolver through a write-path API shared by the CLI, TUI, and web UI, and extend the existing `ProxyChain` structure to surface reordering/toggling through all four surfaces. The `.envrc` pattern has already been removed; `.env` is the sole file-based environment source. Legacy tier env vars (`BIG_MODEL`, `ENABLE_BIG_ENDPOINT`, etc.) remain functional via alias mapping during a deprecation window.

## Technical Context

**Language/Version**: Python 3.11 (proxy core); TypeScript 5.x / Svelte 4 (web UI)
**Primary Dependencies**:
- Backend: `fastapi`, `pydantic`, `python-dotenv`, `textual>=0.47.0` (existing TUI), `rich`, `httpx`, `uvicorn`
- Frontend: SvelteKit, `svelte-dnd-action` for drag-and-drop chain reorder (TBD vs native HTML5 DnD)
- CLI: stdlib `argparse` (already used in `start_proxy.py`)
**Storage**:
- Structured config persisted at `config/proxy_chain.json` (existing file, extended schema).
- Secrets in `.env` only; stored config references them via `${VAR}` syntax.
- No database schema changes.
**Testing**:
- `pytest` for Python (existing `tests/` tree).
- `vitest` for web UI components.
- Property-based precedence tests using `hypothesis` for the resolver.
**Target Platform**: Linux (WSL2 Ubuntu, primary dev); macOS/Linux servers for deployment. Python 3.11+, Node 20+.
**Project Type**: Web-service with bundled TUI and SvelteKit web UI — existing layout keeps `src/` for Python, `web-ui/` for Svelte.
**Performance Goals**:
- Resolver lookup p95 < 1 ms per field (in-memory dict walk, no IO on hot path).
- Live-reload propagation < 5 s from persist to next request.
- TUI/WebUI edit persist < 200 ms end-to-end.
**Constraints**:
- Must not break the public HTTP surface consumed by Claude Code, Qwen Code, and other clients (Anthropic Messages API + OpenAI Chat Completions API compatibility).
- In-flight streaming requests must not be interrupted by concurrent config changes.
- Single-process proxy; no multi-node config sync required.
- Legacy env vars (`BIG_MODEL`, `ENABLE_BIG_ENDPOINT`, `BIG_ENDPOINT`, `BIG_API_KEY`, equivalents for middle/small) MUST continue to resolve during deprecation window.
**Scale/Scope**:
- Chain: ≤ 10 entries typical, no hard cap.
- Assignments: ≤ 20 typical (3 tiers + 6 default slots + custom).
- Concurrent config readers: the live request path (~100s/sec) plus 1–2 UI sessions.
- Config writers: one writer at a time (the operator); concurrent writes are rare and last-write-wins is acceptable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No project constitution file exists at `.specify/memory/constitution.md`. Applying de-facto repo conventions drawn from `CLAUDE.md` and existing code:

| Gate | Status | Notes |
|---|---|---|
| No dependency additions unless justified | ✅ | Adds at most `svelte-dnd-action` (frontend); all backend deps already present. |
| Preserve existing public HTTP surface | ✅ | Resolver is a read-path replacement. No endpoint shapes change. |
| Backward compatibility for legacy env vars | ✅ | Addressed by FR-023/FR-024 via alias layer. |
| Secrets not persisted to git-tracked files | ✅ | FR-014/FR-015 require `${VAR}` references, not literals. |
| Single source of truth | ✅ | Resolver is the only read path; all UIs route writes through one API. |
| No destructive ops without confirmation | ✅ | Config edits are write-validated and preserve prior state on error. |

**Complexity justification**: None required at Phase 0. Re-check after Phase 1.

## Project Structure

### Documentation (this feature)

```text
specs/001-unified-config-system/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (resolves NEEDS CLARIFICATION)
├── data-model.md        # Phase 1 output — Assignment, ProxyEntry, ConfigLayer types
├── quickstart.md        # Phase 1 output — operator-facing "how to use" walkthrough
├── contracts/           # Phase 1 output
│   ├── config-api.yaml  # OpenAPI for /api/config, /api/assignments, /api/chain
│   └── resolver.md      # Internal contract for ConfigResolver class
└── tasks.md             # Phase 2 output (from /speckit.tasks — not part of this plan)
```

### Source Code (repository root)

```text
src/                                # Existing Python proxy core
├── core/
│   ├── config.py                   # MODIFIED: delegate to ConfigResolver
│   ├── config_resolver.py          # NEW: layered resolver + Assignment model
│   ├── proxy_chain.py              # MODIFIED: extend ProxyChain with assignments[]
│   └── assignments.py              # NEW: Assignment dataclass + registry
├── cli/
│   ├── chain_tui.py                # MODIFIED: route writes through resolver API
│   ├── assignment_tui.py           # NEW: per-assignment editor panel
│   └── overlay.py                  # NEW: CLI-args → resolver CLI layer adapter
├── api/
│   ├── config_api.py               # NEW: /api/config, /api/assignments, /api/chain CRUD
│   └── web_ui.py                   # MODIFIED: wire new endpoints
start_proxy.py                      # MODIFIED: argparse expanded, feeds overlay layer
config/
└── proxy_chain.json                # MODIFIED: assignments[] added to schema
tests/
├── contract/                       # Resolver precedence property tests
├── integration/                    # Multi-surface edit-propagation tests
└── unit/
web-ui/                             # Existing SvelteKit app
├── src/
│   ├── routes/
│   │   ├── chain/                  # MODIFIED: drag-and-drop reorder
│   │   └── assignments/            # NEW: slot + tier editor page
│   ├── lib/
│   │   ├── services/
│   │   │   └── config-client.ts    # NEW: calls /api/config endpoints
│   │   └── stores/
│   │       └── config-store.ts     # NEW: reactive store + SSE subscriber
│   └── components/
│       ├── AssignmentEditor.svelte # NEW
│       └── ChainList.svelte        # MODIFIED: drag-and-drop
```

**Structure Decision**: Existing layout already splits Python backend (`src/`) from SvelteKit frontend (`web-ui/`). Extend this; no restructure needed. New modules land alongside existing peers (`src/core/config_resolver.py` next to `src/core/config.py`, `web-ui/src/routes/assignments/` next to `web-ui/src/routes/chain/`).

## Phase Breakdown

### Phase 0 — Research (resolves open questions before design)

**Research tasks:**

1. **svelte-dnd-action vs HTML5 native DnD** — which is a better fit given chain size ≤ 10 entries and the existing SvelteKit setup? Decision criteria: bundle-size impact, a11y support, keyboard-reorder equivalence for parity with TUI.
2. **Live-reload propagation mechanism** — SSE (Server-Sent Events), polling, or WebSocket? The existing web UI already has `websocket_live.py` and `websocket_logs.py`; evaluate reuse vs adding SSE for config change events specifically.
3. **File-watcher for external edits** — should the resolver react to `.env` or `proxy_chain.json` being edited outside the UIs (e.g., by hand in a text editor)? Options: `watchdog` dependency (adds a library), polling every N seconds (simpler), no watcher (require explicit `reload` command). Decision criteria: dev-loop ergonomics vs new dependency.
4. **Property-based precedence test coverage** — is `hypothesis` worth adding for the resolver, or are enumerated table-driven tests sufficient? Decision criteria: failure-mode-discovery yield vs test-suite runtime.
5. **Deprecation-warning UX** — inline console warning per resolution, or single-shot summary at startup? Avoid log spam when legacy env vars resolve many times per request.
6. **Env-var reference expansion boundary** — resolve `${VAR}` at persistence time (store resolved value) or at read time (store literal `${VAR}`)? FR-014 implies read-time; confirm and document.

**Output**: `research.md` with Decision / Rationale / Alternatives-Considered for each of the six items.

### Phase 1 — Design & Contracts

**Prerequisites**: `research.md` complete.

**Entity work → `data-model.md`:**

- `Assignment` — `id: str`, `kind: Literal["tier", "slot"]`, `model: str`, `provider: str`, `base_url: str`, `api_key: str`, `enabled: bool`. Validation rules: `id` unique within kind; `api_key` either empty, `${VAR}` reference, or literal (literal → warning).
- `ProxyEntry` — existing shape preserved (`id`, `name`, `url`, `auth_key`, `enabled`, `order`, `service_cmd`, `service_stop_cmd`, `health_path`, `port`, `timeout`, `extra_headers`, `type`, `model_prefixes`). No breaking changes.
- `ProxyChain` — extended to include `assignments: list[Assignment]` alongside `entries: list[ProxyEntry]` and `router: RouterConfig`. `RouterConfig` becomes a thin projection over `assignments` of `kind="slot"`.
- `ConfigLayer` — enum / literal: `"cli"`, `"shell_env"`, `"dotenv"`, `"stored"`, `"default"`. Precedence ordering defined on this type.
- `ResolvedValue` — `field_path: str`, `value: Any`, `source_layer: ConfigLayer`.
- State transitions: `ProxyChain.apply_edit(edit, source_layer)` → validates → persists if `source_layer == "stored"` → emits change event → resolver recomputes affected fields.

**API contracts → `contracts/config-api.yaml` (OpenAPI 3):**

- `GET /api/config` — full resolved config tree with per-field provenance.
- `GET /api/config/{field_path}` — single field with provenance.
- `GET /api/assignments` — list assignments with resolved values.
- `PATCH /api/assignments/{id}` — edit an assignment; body validated; returns new resolved state.
- `POST /api/assignments` — create a new assignment.
- `DELETE /api/assignments/{id}` — remove (if not a built-in tier).
- `GET /api/chain` — list chain entries in order.
- `POST /api/chain/reorder` — body: `{"order": ["id1", "id2", ...]}`.
- `PATCH /api/chain/{id}` — edit an entry.
- `POST /api/chain` — add an entry.
- `DELETE /api/chain/{id}` — remove an entry.
- `GET /api/config/events` — SSE stream of change events (or equivalent WebSocket per Phase 0 decision).

**Internal contract → `contracts/resolver.md`:**

- `ConfigResolver.resolve(field_path: str) → ResolvedValue`
- `ConfigResolver.set(field_path: str, value: Any, layer: ConfigLayer) → None`
- `ConfigResolver.snapshot() → dict` — full tree with provenance
- `ConfigResolver.subscribe(callback) → unsubscribe_fn` — change notifications
- Layer ordering is data, not code: defined as a list in `config_resolver.py` so test-time reorder is trivial.

**Agent context update:**

Run `.specify/scripts/bash/update-agent-context.sh claude` once `.specify/` scaffolding is present, to append the new tech (FastAPI resolver endpoints, Svelte assignment editor) to the agent context file while preserving manual additions.

**Quickstart → `quickstart.md`:**

Step-by-step walkthrough for an operator:
1. Edit an assignment via TUI (arrow keys + enter).
2. Observe the change in the web UI within 5 seconds.
3. Confirm the change took effect on the next request via `/api/config/{field_path}` provenance query.
4. Add a custom chain entry via CLI (`python start_proxy.py --add-chain-entry id=custom …`).
5. Reorder it via web UI drag-and-drop.
6. Revert a change by deleting the stored value and watching the lower layer take over.

### Phase 2 — Implementation (tracked separately in tasks.md)

Out of scope for `/speckit.plan`. High-level sequencing:

1. **Foundation**: `config_resolver.py`, `Assignment`, `ConfigLayer`; precedence walker; property tests.
2. **Integration**: `Config.__init__` delegates to resolver; `ProxyChain` extended; legacy env-var alias layer emits deprecation warnings.
3. **CLI**: `start_proxy.py` argparse expanded; `overlay.py` writes into resolver CLI layer.
4. **HTTP API**: `config_api.py` with endpoints from `contracts/config-api.yaml`; wired into existing FastAPI app in `web_ui.py` / `main.py`.
5. **TUI**: `chain_tui.py` mutations routed through HTTP API or direct resolver call; `assignment_tui.py` new panel.
6. **Web UI**: `config-client.ts`, `config-store.ts`, `AssignmentEditor.svelte`, `ChainList.svelte` drag-and-drop; subscribe to change-event stream.
7. **Cleanup**: Remove `ENABLE_BIG_ENDPOINT` / `ENABLE_MIDDLE_ENDPOINT` / `ENABLE_SMALL_ENDPOINT` from `.env.example`; update `docs/` with precedence table.

## Complexity Tracking

> Fill only if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| New `src/core/config_resolver.py` module (fourth config-adjacent file alongside `config.py`, `proxy_chain.py`, `model_router.py`) | Single-responsibility class for layered resolution with provenance; keeps `config.py` viable during the alias/deprecation window | Merging into `config.py` would entangle the resolver with the legacy flat-env-var reader and make the deprecation cutover harder. Separation enables `config.py` to become a thin alias shim. |
| Stored config extended (not replaced) rather than a ground-up new format | Preserves forward compat with TUI/web-UI code already reading `proxy_chain.json` | Writing a new `config/assignments.json` would force two-file synchronization and break existing tooling (e.g., `proxies config show`) without benefit. |
| Change-event transport (SSE/WS) added for live-reload | Required by FR-007 (5-second propagation without restart) and User Story 3 | Polling would add latency and waste CPU; explicit reload commands regress the UX back to the restart-tax this feature aims to eliminate. |
