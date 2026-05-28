# Feature Specification: Profile Routing for claude-code-proxy

**Feature Branch**: `002-profile-routing`

**Created**: 2026-05-28

**Status**: Draft

**Input**: Requirements specification at `requirements.md` and technical design at `design.md` (both v1.0.0, 2026-05-14)

---

## Constitution Check Reference

This specification has been validated against the following governing documents:
- **Project Constitution** (`.specify/memory/constitution.md` v1.0.0) — Six core principles checked: Existing Research Before Building (I), Synthesis Verification (II), Safe Destructive Ops (III), Changelog Discipline (IV), Progressive Disclosure (V), Single Source of Truth for Configuration (VI).
- **Global Agent Constitution** (`~/code/agents/constitution.md`) — Global rules for agent operations, terminal specification, user preferences, research mandate, and synthesis verification.

Gates: All pass. Profile routing is additive, uses zero new dependencies, and introduces no destructive operations.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Five tools, five profiles, one proxy (Priority: P1)

A power user running pi, opencode, hermes, claude-code, and codex in parallel terminal sessions wants each tool to use its own bundle of model configurations. Pi should use a fast tool-caller while claude-code uses a slower thoughtful main model, all sharing one proxy instance, one compression layer, and one command-rewriting layer.

**Why this priority**: Without per-CLI profile isolation, every tool sharing the proxy is forced into the same model bundle. This wastes capability on tools that need cheap fast models and wastes cost on tools that need expensive thoughtful models. This is the primary value proposition of the entire feature.

**Independent Test**: Configure five profiles in `profiles/profiles.json`, launch five concurrent requests through each profile's path, and verify each request dispatches to the model specified by that profile's `default` slot — observable in the proxy logs.

**Acceptance Scenarios**:

1. **Given** a running proxy with profiles defined for pi, opencode, hermes, claude, and codex, **When** five concurrent requests arrive each targeting a different profile path, **Then** each request's dispatched model matches its profile's `default` slot and no request's configuration affects another's behavior.
2. **Given** a client with a legacy base URL (no profile prefix), **When** it sends a request, **Then** the proxy treats it as targeting the `default` profile and behavior is identical to pre-profile-system operation.
3. **Given** a profile registry that has been edited while the proxy is running, **When** the next request arrives targeting that profile, **Then** the new profile values take effect without a proxy restart.

---

### User Story 2 — Web-search tool-call interception (Priority: P1)

A user wants web-search tool invocations from pi to dispatch to a cheap/fast model while the same tool invocations from claude-code dispatch to a more capable model. The proxy should inspect each request's tool-call payload, detect web-search invocations, and substitute the model field before upstream dispatch.

**Why this priority**: Web-search tool calls are the highest-volume slot-swap use case. They consume disproportionate token budgets when routed through expensive reasoning models. Interception at the proxy layer is the only mechanism that works without modifying any CLI under management.

**Independent Test**: Send a web-search tool-call request through the `pi` profile; confirm the dispatched model is the profile's `web_search` slot value, not its `default` slot value. Send the same request through a profile without a `web_search` slot; confirm no swap occurs.

**Acceptance Scenarios**:

1. **Given** a profile defining a `web_search` slot value distinct from its `default`, **When** a request from that profile contains a web-search tool invocation as the only tool call, **Then** the dispatched model is the `web_search` slot value.
2. **Given** a profile with `web_search_intercept: false`, **When** a request contains a web-search tool invocation, **Then** no model substitution occurs.
3. **Given** a profile with a custom `web_search_pattern`, **When** a tool name matching that pattern is invoked, **Then** model substitution occurs; non-matching tool names are ignored.

---

### User Story 3 — Live profile editing without restart (Priority: P2)

An operator wants to add a new profile or tweak an existing profile's slot values by editing a JSON file on disk, with the change reflected in the very next matching request. No proxy restart, no process signal, no CLI invocation should be required.

**Why this priority**: Profile editing cadence is unpredictable — operators add CLIs as they install them, tweak slot values when models change availability, and experiment with routing strategies. A restart barrier turns every tweak into a disruption.

**Independent Test**: Edit `profiles/profiles.json` to add a new profile while the proxy is serving requests; send a request to the new profile's path; confirm the profile resolves and dispatches correctly.

**Acceptance Scenarios**:

1. **Given** a running proxy with a loaded registry, **When** the operator edits the registry file to add a new profile, **Then** the next request targeting that new profile resolves it correctly.
2. **Given** a running proxy, **When** the operator edits the registry file with malformed JSON, **Then** the proxy logs a parse error, retains the last-good registry state, and continues serving without interruption.

---

### Edge Cases

- What happens when a profile is deleted from the registry file while in-flight requests targeting it are still being processed? In-flight requests complete with their original profile context; new requests receive a 404.
- How does the system handle a profile name that matches a filesystem path segment (e.g., `..`, `.env`)? Profile names are matched by exact string against registry keys; path-traversal patterns simply fail to match and produce a 404 per FR-012.
- What happens when a request arrives at `/p//v1/chat/completions` (empty profile name)? The route pattern does not match; the request falls through to standard 404 handling for the unmatched route.
- How does the system handle a registry file that defines a `web_search_pattern` that is an invalid regex? The profile falls back to the system-wide default pattern; a warning is logged at registry load time identifying the invalid pattern and the affected profile.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system SHALL maintain a profile registry file containing a top-level mapping of profile names to flat slot-override dictionaries.
- **FR-002**: The system SHALL reject startup if the registry file is missing, malformed, or lacks a `default` profile, with a distinct error message for each condition.
- **FR-003**: The system SHALL recognize slot names matching the proxy's existing model router slots: `default`, `background`, `think`, `long_context`, `image`, `web_search`. Unknown keys in a profile entry SHALL be ignored without error.
- **FR-004**: The system SHALL re-read the registry file when its modification time has changed since the last load, using a single `os.stat` call plus JSON parse when the mtime has changed.
- **FR-010**: The system SHALL accept requests at path prefix `/p/{profile-name}/v1/chat/completions` and `/p/{profile-name}/v1/messages` and treat the path-segment `{profile-name}` as the requested profile.
- **FR-011**: The system SHALL continue accepting requests at legacy paths `/v1/chat/completions` and `/v1/messages`, treating them as targeting the `default` profile.
- **FR-012**: The system SHALL reject a request to an unknown profile path with a structured 404 JSON body containing `profile_requested`, `profiles_available` (array), and `message` fields.
- **FR-020**: The system SHALL build a per-request profile context at request entry containing the resolved profile name and the merged slot dictionary (profile values overlaid onto `default`).
- **FR-021**: The system SHALL consult the per-request profile context for slot resolution before falling back to the proxy's global slot configuration.
- **FR-022**: The system SHALL ensure no request's profile context leaks into another request's processing. Concurrent requests each see only their own independent context objects.
- **FR-030**: The system SHALL inspect every request's tool-call payload after profile resolution and before upstream dispatch to identify web-search tool invocations.
- **FR-031**: The system SHALL substitute the request's model field with the active profile's `web_search` slot value when a web-search invocation is detected, the profile defines a `web_search` slot, and the web-search tool is the only tool invoked in that turn.
- **FR-032**: The system SHALL allow per-profile opt-out of web-search interception via an optional `web_search_intercept` boolean field (defaults to `true`).
- **FR-033**: The system SHALL allow per-profile customization of the web-search detection pattern via an optional `web_search_pattern` regex field.
- **FR-040**: The system SHALL preserve the behavior of every existing route, endpoint, CLI command, configuration file, and integration that does not opt into the profile system.
- **FR-041**: The system SHALL treat the profile registry as additive — a deployment without a registry file SHALL function as if a `default`-only registry were present.

### Non-Functional Requirements

- **NFR-001**: Profile resolution SHALL add no more than 1 millisecond to request latency at the 99th percentile.
- **NFR-002**: The system SHALL support at least 50 concurrent profiled requests without contention.
- **NFR-010**: A malformed registry file modification SHALL NOT crash the proxy or affect in-flight requests.
- **NFR-011**: An unknown-profile request SHALL fail closed with a structured 404, never falling through to an unintended profile or global configuration.
- **NFR-020**: Every profiled request SHALL emit a log record containing the resolved profile name, dispatched model, and any web-search interception event.
- **NFR-021**: The proxy's usage-tracking storage SHALL persist the profile name for every recorded request.
- **NFR-030**: The profile resolver and overlay logic SHALL live in a single dedicated module.
- **NFR-031**: Adding a new profile SHALL require only a registry file edit with no source-code change, no rebuild, and no proxy restart.

### Key Entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Profile Registry | Persistent mapping of profile names to slot-override dictionaries | File path, last-loaded mtime, cached parsed content | Contains many Profile entries; consulted by the Resolver |
| Profile | A named bundle of slot overrides plus optional metadata | Name, slot dictionary, web_search_intercept flag, web_search_pattern, notes | Belongs to the Registry; consumed by Profile Context |
| Profile Context | Per-request object carrying the resolved profile state | Profile name, merged slot dictionary | Created at request entry; consumed by model router and web-search interceptor; discarded after response |
| Slot | A named role in the model router | Slot name, model identifier | Referenced by Profile entries and global router; the unit of override |
| Web-Search Match Pattern | Regex pattern used to identify web-search tool invocations | Pattern string, scope (per-profile or default) | Belongs to a Profile or to the system-wide default; consulted by the interceptor |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can run pi, opencode, hermes, claude-code, and codex concurrently against a single proxy instance, each with independent slot configurations, without restarting the proxy and without any tool's configuration affecting another's.
- **SC-002**: Web-search invocations from a profile that defines a distinct `web_search` slot value dispatch to that slot's model rather than the profile's `default` slot model in 100% of qualifying turns.
- **SC-003**: Adding a new profile or modifying an existing profile requires only a registry file edit, with the change observable on the next matching request and no proxy restart.
- **SC-004**: The proxy's existing test suite passes unchanged after the profile system is integrated.
- **SC-005**: Profile resolution adds no more than 1 millisecond of P99 latency to request handling.

---

## Assumptions

- Users targeting profile-specific behavior will configure their CLI's base URL to point at a profile-prefixed path, typically through the proxy's alias-installation script.
- The profile registry file is owned and edited by the same user who runs the proxy; no multi-user write coordination is required.
- The proxy continues to expose its model router slot vocabulary; profiles are valid only insofar as that vocabulary remains stable.
- Web-search tool naming conventions across the CLIs under management remain dominated by the default pattern; per-profile pattern overrides handle outliers.
