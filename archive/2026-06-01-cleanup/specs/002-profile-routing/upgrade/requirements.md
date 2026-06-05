# Profile Routing — Upgrade Requirements

**Project**: claude-code-proxy
**Phase**: Upgrade v2.1.x → v2.2.0
**Inputs**: `clean-architecture-proposal.md`, `rewrite-scratch.md`, `audit-gap-analysis.md`
**Date**: 2026-05-28
**Status**: Draft

---

## Constitution Check

This specification has been validated against `~/code/agents/constitution.md`:
- **Safety**: No destructive operations proposed. All changes are additive or refactoring.
- **Terminal**: All operations specified with correct terminal context.
- **Existing Research**: Prior art in `audit-gap-analysis.md` section 4 documents 5 design irregularities.
- **Synthesis Verification**: Claims trace to tested code paths (confirmed via proxy test on 2026-05-28).

---

## Problem Statement

The claude-code-proxy has accumulated five architectural inconsistencies during rapid feature development:

1. **Provider/model name coupling** — Models are named `provider/model` (e.g., `openai/gpt-4`), then the code parses the string back apart to figure out which provider serves it. Three separate override mechanisms exist for the same job.
2. **`_enabled` flags are redundant** — `big_enabled`, `middle_enabled`, `small_enabled`, `local_enabled` duplicate information already carried by the model field being null or set.
3. **Profile overlays fire after routing** — The model_router makes routing decisions using global config, then profile overrides patch the result. Web-search gets detected twice with potentially different logic.
4. **Two competing profile systems** — `profiles/profiles.json` (routing profiles) and `configs/profiles/*.json` (legacy env-var saves) share the concept name but have different schemas and code paths.
5. **`_profile_toolcall_models` request-dict stashing** — Internal state leaks through the request dict into upstream API calls, causing TypeError. Fixed in commit `d63430e` but the pattern is fragile.

Additionally, GPT-5.5 access through ChatGPT Plus requires OAuth proxy integration rather than the current API-key approach.

---

## User Scenarios & Testing

### User Story 1 — Model identity independent of provider (Priority: P1)

An operator wants to define a model once and use it through any provider without changing the model name. Currently `claude-sonnet` served through Anthropic's API and `claude-sonnet` served through OpenRouter require different model strings and different config entries.

**Independent Test**: Define `claude-sonnet` as `{provider: anthropic, model_id: claude-sonnet-4}` and `claude-sonnet-via-or` as `{provider: openrouter, model_id: anthropic/claude-sonnet-4}`. A request using `claude-sonnet-via-or` reaches the OpenRouter endpoint with the correct model string.

### User Story 2 — Remove all `_enabled` flags (Priority: P2)

An operator should not need to set `small_enabled=true` in addition to setting `small_model=...`. A null/empty model IS disabled. Setting a model IS the act of enabling it.

**Independent Test**: Remove `small_enabled` from the config. Set `small_model` to a valid model. The small tier works. Set `small_model` to empty. The small tier is skipped.

### User Story 3 — Profile context before routing (Priority: P1)

Profile overrides should be applied BEFORE the model_router runs, not patched in after. This eliminates duplicate web-search detection and ensures the cascade/circuit-breaker runs against the correct model.

**Independent Test**: A request to `/p/pi/v1/...` with a web-search tool call. The model_router should see the profile's `web_search` model value in its first routing pass, not have it swapped afterward.

### User Story 4 — Single profile system (Priority: P2)

Consolidate `profiles/profiles.json` (routing profiles) and `configs/profiles/` (legacy env-var saves) into one schema under one directory.

**Independent Test**: After migration, both the wizard's "save profile" flow and the routing profiles API serve from the same data store.

### User Story 5 — GPT-5.5 through Plus subscription via OAuth proxy (Priority: P1)

A user with a ChatGPT Plus subscription should be able to use GPT-5.5 in Hermes without an OpenAI API key, by routing through the Codex OAuth proxy.

**Independent Test**: `npx openai-oauth` starts a proxy on port 10531. A request to `http://127.0.0.1:10531/v1/chat/completions` with model `gpt-5.5` returns a valid response without any API key header.

---

## Functional Requirements

### FR-001: Model/Provider Decoupling
The system SHALL define models and providers as separate registry entries. A model entry contains a `provider` reference and a `model_id` string. The provider entry contains `base_url`, `api_key`, and optional metadata. Provider SHALL NEVER be inferred from the model name.

### FR-002: Null-Model-Is-Disabled
Every route slot SHALL treat a null/empty model value as "disabled." The presence of a model value SHALL be the sole act of enabling that slot. No parallel `_enabled` flag SHALL be required.

### FR-003: Profile Context Before Routing
The profile resolution SHALL complete before the model router's first routing decision. The model router SHALL receive the fully resolved profile context (with overlays applied) as input, not as a post-hoc patch.

### FR-004: Single Profile Registry
All profile data SHALL live in `profiles/` with a single schema. The legacy env-var profile system (`configs/profiles/`) SHALL be migrated to the routing profile schema or deprecated.

### FR-005: No Internal State on Request Dict
No subsystem SHALL stash internal state keys (like `_profile_toolcall_models`) on the request dictionary. Inter-module communication SHALL use explicit parameters, contextvars, or a dedicated context object.

### FR-006: OAuth Proxy Integration
The startup sequence SHALL optionally start an OAuth proxy subprocess (`npx openai-oauth`) and route the GPT-5.5 model through it when configured.

---

## Non-Functional Requirements

### NFR-001
Profile resolution SHALL add no more than 1ms P99 latency. (Carried forward.)

### NFR-002
Zero backward-incompatible changes to existing routes (`/v1/chat/completions`, `/v1/messages`).

### NFR-003
All 25 existing profile tests SHALL pass unchanged after refactoring.

---

## Key Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| Provider | An upstream API endpoint with auth | name, base_url, api_key |
| Model | A specific model accessible through a provider | name, provider_ref, model_id |
| Profile | A named bundle of route overrides | name, routes (map of use_case → model_ref) |
| Route | A use-case to model mapping | use_case (default, toolcall, web_search, etc.), model_ref |

---

## Success Criteria

- **SC-001**: The `_profile_toolcall_models` bug fix (d63430e) is confirmed stable under load
- **SC-002**: A user can run `npx openai-oauth` and point Hermes at `http://127.0.0.1:10531/v1` to use GPT-5.5
- **SC-003**: The `_enabled` flags can be removed from .env without breaking any tier
- **SC-004**: Profile overlay logging shows the correct model on the first routing pass, not a swap after
- **SC-005**: All 25 profile tests pass

---

## Assumptions

- The existing proxy codebase remains the foundation; clean-sheet rewrite is a separate project.
- OAuth proxy (`openai-oauth`) runs as a sidecar process managed by the proxy startup.
- Claude Code OAuth (`~/.codex/auth.json`) is already set up by the user.
