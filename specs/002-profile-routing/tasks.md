---
description: "Task list for Profile Routing feature implementation"
---

# Tasks: Profile Routing for claude-code-proxy

**Input**: Design documents from `specs/002-profile-routing/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by implementation phase to enable independent implementation and testing.

---

## Phase 1: Setup — Resolver, Routes, and Aliases

**Purpose**: Core profile infrastructure — resolver, routes, and CLI aliases. Delivers User Story 1 (multi-CLI isolation).

### Foundational (Blocking)

- [ ] T001 Create `profiles/profiles.json` at repo root with six seed profiles (default, pi, opencode, hermes, claude, codex) per data-model.md schema
- [ ] T002 Implement `src/core/profiles.py` with:
  - `ProfileResolver` class (load, cache, validate registry)
  - `ProfileContext` frozen dataclass
  - `extract_profile_from_path()` function
  - Error types: `RegistryParseError`, `RegistryMissingDefaultError`, `ProfileNotFoundError`
- [ ] T003 Implement FastAPI `get_profile_context` dependency that resolves profile name into `ProfileContext` via `ProfileResolver`, raises HTTPException(404) for unknown profiles
- [ ] T004 Register new routes in `src/api/routes.py`:
  - `POST /p/{profile}/v1/chat/completions`
  - `POST /p/{profile}/v1/messages`
  - Both delegate to existing handler functions with non-null ProfileContext
- [ ] T005 Modify model router slot-lookup function signature to accept optional `ProfileContext` parameter; consult `profile_context.slots[slot_name]` before falling back to global config
- [ ] T006 Update `scripts/install-aliases.sh` to set each CLI's base URL to its profile-prefixed path
- [ ] T007 Write unit tests in `tests/unit/test_profile_resolver.py`:
  - Resolves known profile; raises on unknown
  - Merges profile over default correctly
  - Returns frozen context
  - Mtime change triggers reparse
  - Corrupt file retains last-good state
- [ ] T008 Write integration test in `tests/integration/test_profile_routing.py`:
  - Five concurrent requests through five profile paths
  - Assert dispatched model matches profile's `default` slot
  - Legacy `/v1/...` route still works

**Checkpoint**: Phase 1 complete — multi-CLI isolation functional. Validates FR-001–FR-004, FR-010–FR-012, FR-020–FR-022, FR-040–FR-041; NFR-001–NFR-002, NFR-010–NFR-011, NFR-030–NFR-031.

---

## Phase 2: Web-Search Interception

**Purpose**: Tool-call inspection and model rewrite for web-search invocations. Delivers User Story 2.

### Implementation

- [ ] T009 Implement `src/api/web_search_interceptor.py` with `maybe_rewrite_for_web_search()` function that:
  - Inspects request body for web-search tool invocations
  - Checks profile context for `web_search_intercept` flag and `web_search` slot
  - Rewrites model field when conditions met
  - Returns request body unchanged when conditions not met
- [ ] T010 Extend `ProfileContext` with `web_search_intercept` and `web_search_pattern` fields; implement system-wide default pattern for web-search tool name matching
- [ ] T011 Wire interceptor into request handler stack after profile resolution and before cascade routing
- [ ] T020 Extend usage-tracking logging to record web-search substitution events (original model, new model, profile name)
- [ ] T012 Write unit tests in `tests/unit/test_web_search.py`:
  - Rewrites when conditions met
  - No-ops when interception disabled
  - No-ops when no web_search slot defined
  - No-ops when multi-tool turn without forced choice
  - Custom pattern matching
- [ ] T013 Write integration test: web-search tool-call through `pi` profile asserts dispatched model matches `web_search` slot

**Checkpoint**: Phase 2 complete — web-search interception working. Validates FR-030–FR-033; NFR-020.

---

## Phase 3: Observability Surface

**Purpose**: Profile name persistence in analytics, CLI management commands, and dashboard display. Delivers remaining success criteria.

### Implementation

- [ ] T014 Add `profile TEXT NOT NULL DEFAULT 'default'` column to usage-tracking SQLite schema
- [ ] T015 Update request-write path to populate profile column
- [ ] T016 Extend `proxies` CLI with `proxies profile list`, `proxies profile show <name>`, and `proxies profile validate` subcommands
- [ ] T017 Extend web dashboard to display each profile's resolved overlay and 24-hour request count
- [ ] T018 Update CHANGELOG.md with `[Unreleased]` entries for all phases

**Checkpoint**: Phase 3 complete — full observability. Validates NFR-021; SC-001 through SC-005.

---

## Phase 4: Forward-Compatible Carrier Slot

**Purpose**: Reserve `provider_override` slot for future per-profile upstream account routing. No behavioral changes.

### Implementation

- [ ] T019 Extend profile schema with optional `provider_override` field; document intended use
- [ ] T020 Implement runtime check in request handler that passes `provider_override` to provider selector when present
- [ ] T021 Document `provider_override` usage in `profiles/profiles.json` via `notes` field examples

**Checkpoint**: Phase 4 complete — forward compatibility reserved.
