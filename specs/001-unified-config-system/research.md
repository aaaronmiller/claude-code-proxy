# Research — Unified Configuration & Multi-Surface Control System

**Feature**: 001-unified-config-system | **Phase**: 0 | **Date**: 2026-04-23

Each item below resolves a Technical-Context unknown or dependency choice called out in `plan.md`. Format per `/speckit.plan` contract: Decision / Rationale / Alternatives Considered.

---

## R1 — `svelte-dnd-action` vs HTML5 native DnD

**Decision**: Start with HTML5 native DnD + keyboard-reorder fallback; add `svelte-dnd-action` only if native DnD proves insufficient for the a11y/keyboard parity required by FR-018 (TUI arrow-key reorder ↔ web-UI equivalent).

**Rationale**: Chain has ≤ 10 entries. Native HTML5 DnD is zero-dependency, well-documented, and adequate for short lists. A11y/keyboard-equivalence is better served by an explicit move-up/move-down button pair next to each row than by trying to make drag-and-drop screen-reader-friendly — that pattern matches the TUI's arrow-key model and satisfies Principle V (progressive disclosure: fewer new deps).

**Alternatives considered**:
- `svelte-dnd-action` (well-maintained, ~8KB): adds a dep; delivers polish for lists 20+; overkill for ≤ 10 items.
- `sortablejs` via wrapper: larger footprint; not idiomatic Svelte.

---

## R2 — Live-reload transport (SSE vs WebSocket vs polling)

**Decision**: **SSE** (Server-Sent Events) for config-change notifications; keep existing WebSocket surfaces (`websocket_live.py`, `websocket_logs.py`) for their current purposes.

**Rationale**: Config changes are unidirectional server→client. SSE has no handshake complexity, automatic reconnect, and plays well with FastAPI's `StreamingResponse`. Existing WS code in this repo is bidirectional (dashboard interactions) — different problem shape. Reusing WS here would force multiplexing over one channel or spinning up a third WS endpoint, both of which complicate the live-reload path that needs to be trivially correct. Polling fails SC-002's 5-second budget under heavy request load.

**Alternatives considered**:
- WebSocket: needed only if clients ever push over the channel; they don't — all config writes go through the REST API.
- Long-polling: wastes connections; behaves worse behind HTTP/1.1 reverse proxies.
- Client polling at 5-second intervals: meets SC-002 only at worst case; wastes CPU across multiple tabs.

---

## R3 — File-watcher for external edits to `.env` or `proxy_chain.json`

**Decision**: Ship without a file-watcher in v1. Provide an explicit `proxies reload-config` CLI verb and a `POST /api/config/reload` endpoint. Document that manual edits require explicit reload.

**Rationale**: `watchdog` adds a dep; polling at 1-second intervals for a rarely-edited file is wasteful. Power users who hand-edit JSON can run one command; the common path is edit-via-UI which already triggers live-reload. Revisit if operator feedback shows manual-edit friction.

**Alternatives considered**:
- `watchdog` auto-reload: good UX, but adds native-compile dep; failure modes (symlink resolution, WSL inotify quirks) add maintenance cost.
- Polling every N seconds: simple but wasteful.
- SIGHUP handler: Unix-only and less discoverable than an explicit command.

---

## R4 — `hypothesis` property-based tests for precedence

**Decision**: Use `hypothesis` for the precedence walker only. Rest of the resolver uses enumerated table-driven tests.

**Rationale**: Precedence walking is a pure function over 5 ordered layers with arbitrary string keys — exactly the shape property-based testing shines on. Generating random (key, layer-set, value-per-layer) tuples and asserting `resolve(key).source_layer ∈ set and value == expected_for_highest_layer_present` catches the off-by-one and empty-layer bugs enumerated tests miss. Non-precedence logic (field validation, secret masking) is better covered by handcrafted cases.

**Alternatives considered**:
- Pure enumerated tests: fine for the 32 combinations of 5-layer presence, but brittle if layer semantics evolve.
- Skip property tests entirely: acceptable but leaves a known-tricky invariant weakly defended.

---

## R5 — Deprecation-warning emission strategy

**Decision**: **Single-shot at startup, aggregated summary.** On first resolution that hits a legacy env var, cache the fact; at end-of-startup print one block listing every legacy var in use and its modern equivalent. Per-resolution suppression for the remainder of the process.

**Rationale**: Legacy env vars can be consulted hundreds of times per request path. Inline warnings are log-spam — violates Principle V (progressive disclosure). Single-shot aggregation is discoverable (operators scanning startup logs see it once), actionable (every legacy var in one place), and silent thereafter.

**Alternatives considered**:
- Inline per resolution: log-spam at production request rates.
- Startup-only with suppression: proposed decision.
- Metrics counter only (no log): invisible to operators who don't check metrics.

---

## R6 — Env-var reference expansion point (read-time vs persist-time)

**Decision**: **Read-time.** Preserve `${VAR_NAME}` as a literal string in stored config; expand on every read.

**Rationale**: Consistent with existing `ProxyEntry.effective_auth_key()` at `proxy_chain.py:58-65`. Persist-time expansion would leak resolved secret values into the stored config file — violates Principle E2 (no secrets in git-tracked files) and undermines the entire FR-014 contract. Read-time cost is negligible (string lookup); encapsulated in resolver.

**Alternatives considered**:
- Persist-time: faster reads but leaks secrets; non-starter.
- Hybrid (expand on first read, cache): cache invalidation across config edits is the classic hard problem. Not worth the complexity.

---

## R7 — Existing-solution survey (Principle I)

**Decision**: **Build `ConfigResolver` in-tree.** Do not adopt `dynaconf`, `hydra`, `pydantic-settings`, or `configobj`.

**Rationale**: The existing codebase (`config.py` + `proxy_chain.py`) is already ~80% of the way to the target design. External solutions would require wrapping our existing `ProxyChain`/`RouterConfig`/provider-registry model or rewriting around their primitives — either path costs more than writing a 50–100-line resolver that fits our exact precedence semantics. Specifically:

- `dynaconf`: excellent for layered config but opinionated about layers (Vault, secrets managers) we don't need; adds a dep for capability we'd use 20% of.
- `hydra`: designed for ML experiment sweeps; overkill for server config; confusing CLI syntax for operators.
- `pydantic-settings`: would actually be a fine fit, but existing `Config` class is plain Python — migrating the class is more churn than writing the resolver.
- `configobj`: outdated; not type-safe; no provenance tracking (Principle VI requires provenance).

Documented decision: use in-tree. If the resolver grows past ~200 lines, revisit `pydantic-settings`.

**Alternatives considered**: see above — each rejected with specific reason.

---

## R8 — Cascade trigger semantics

**Decision**: Match existing `MODEL_CASCADE` logic in `src/core/model_manager.py` and `src/core/circuit_breaker.py`. Cascade triggers on: (a) HTTP 4xx other than 401/403 (auth errors don't benefit from retrying), (b) HTTP 5xx, (c) request timeout, (d) explicit provider "unavailable" signals. Document this in `research.md` so FR-003d's semantics are pinned.

**Rationale**: Reuse not reinvention (Principle I). Current behavior is proven in production. `attempt_index` in `RequestMetric` records every cascade step, preserving the distinction between "primary target failed" (role-config issue) and "every target failed" (model or network issue) that SC-010 requires.

**Alternatives considered**:
- Cascade on any non-2xx: over-aggressive; would retry on 400s that will always fail.
- Cascade only on 5xx: misses timeout cases.
- Model-emitted "I don't know" text: not machine-detectable reliably; out of scope.

---

## R9 — TUI auto-refresh on external edit

**Decision**: **TUI subscribes to the same SSE stream as the web UI.** On change event, affected TUI panels redraw. `textual` reactive bindings + a small SSE consumer.

**Rationale**: Parity with FR-022 (web UI auto-reflects). Without this, TUI users see stale state when operator edits via web UI mid-session — silent divergence. SSE consumer in TUI is ~30 lines; cost is low.

**Alternatives considered**:
- Manual refresh key in TUI: cheap but leaves a known divergence.
- Polling every N seconds from TUI: wasteful and laggier than SSE.

---

## R10 — Web UI stale-cache indicator UX

**Decision**: Visual indicator in the page header: a small badge showing **connected** (green dot), **disconnected** (gray dot with "last update X ago" tooltip), or **stale > 30s** (amber badge + "refresh" button). On disconnect, the client tries SSE reconnect with exponential backoff; failure to reconnect after 30 s surfaces the amber state.

**Rationale**: Silent staleness is the dangerous case. Explicit indicator matches operator mental model. Amber + manual refresh button lets operators decide whether to refresh or wait.

**Alternatives considered**:
- No indicator, rely on backend timestamps: invisible.
- Full-page modal on disconnect: over-aggressive, interrupts work.

---

## R11 — Analytics data retention policy

**Decision**: Per-attempt `RequestMetric` rows retained **30 days** by default (configurable via `ANALYTICS_RETENTION_DAYS` env). Daily aggregates (per assignment, per model) retained **365 days** by default. A background task prunes old rows.

**Rationale**: 30 days covers typical debugging windows; daily aggregates cover annual trend analysis. Matches existing `usage_tracking.db` retention behavior (to be verified during implementation). Configurable for ops that want longer retention.

**Alternatives considered**:
- Indefinite retention: disk growth unbounded.
- 7 days: too short for quarterly reporting.
- Daily aggregate only, discard per-attempt: loses the dimension SC-010 needs.

---

## R12 — Secret-masking regex coverage (FR-035)

**Decision**: Extend `API_KEY_PATTERNS` in `src/core/config.py:25-34` with: OAuth tokens (`Bearer [A-Za-z0-9+/=._-]+`), JWTs (`eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+`), generic long-hex (`[0-9a-f]{40,}`), and Anthropic OAuth (`sk-ant-oat01-[A-Za-z0-9_-]+`). Masking strategy: show first 4 and last 4 chars separated by `...` for values ≥ 12 chars; fully mask shorter values.

**Rationale**: Comprehensive coverage of formats actually seen in this codebase's `.env` files and OAuth flows (see `litellm-gateway.yaml` and `compression-aliases.zsh`). Partial masking (first-4/last-4) lets operators recognize their own keys without exposing them in audit logs.

**Alternatives considered**:
- Full mask always: destroys operator ability to recognize values.
- Allowlist (only mask known formats): dangerous — misses new formats.
- Denylist specific values: brittle; can't catch dynamic secrets.

---

## R13 — Migration safety heuristic (FR-023c)

**Decision**: Auto-migration halts and fails startup when any of the following holds:

1. A field exists in the stored config whose key is unknown to the current schema AND the key does not match a known rename mapping.
2. A field's stored type does not match the expected type and no documented coercion exists.
3. A required field is missing AND no safe default exists (e.g., a user-defined slot with no fallback model).
4. Two or more legacy fields map to the same new field with conflicting values.

All other cases (missing optional fields, known renames, additive defaults) auto-migrate.

**Rationale**: Bias toward halting — Principle III says the cost of silent data loss (wrong routing decision) is higher than the cost of an explicit fix. Startup failure is loud and recoverable; silent mismigration is the worst outcome.

**Alternatives considered**:
- Always auto-migrate with "best guess": violates Principle III.
- Always refuse and require manual migration tool: regresses UX from the auto-migration promise (FR-023a).
- Auto-migrate with warning but proceed: operator may miss the warning and ship misconfigured.

---

## Summary

All 13 unknowns resolved. Technical Context in plan.md has no remaining "NEEDS CLARIFICATION" markers. Phase 1 (Design & Contracts) is unblocked.

Three decisions above have **deferred revisits**: R1 (add dnd lib if native DnD proves insufficient), R3 (add file-watcher if manual-edit friction is reported), R7 (migrate to `pydantic-settings` if resolver grows past ~200 lines).
