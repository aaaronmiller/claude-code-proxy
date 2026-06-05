---
date: 2026-05-14 PHASE-LOCK PT
ver: 1.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, routing, multi-cli, requirements]
---

# Profile Routing for claude-code-proxy — Requirements Specification v1.0

## 1. Purpose

The claude-code-proxy currently routes requests through a single global configuration. When multiple command-line tools run against the proxy simultaneously, they share that single configuration, which prevents each tool from using its own model selection for tool calls, web search, background tasks, and other slot-based roles. Forcing each tool to use the same model bundle wastes capability on tools that need cheap fast models and wastes cost on tools that need expensive thoughtful models.

This project adds per-request profile selection to the proxy. A profile is a named bundle of slot overrides that activates when a request arrives at a profile-specific path. The mechanism allows a single proxy instance, a single compression layer, and a single command-rewriting layer to serve every connected tool with its own independent slot configuration, with no process restarts and no environment-variable contention between tools.

The capability is essential for users running pi, opencode, hermes, claude-code, and codex side by side, each with distinct model preferences, and for users who want to route specific tool-call patterns such as web search to different models than the main reasoning chain uses.

## 2. Glossary

| Term | Definition |
|------|-----------|
| **Profile** | A named bundle of slot overrides stored in a profile registry file and applied to matching requests at runtime. |
| **Slot** | A named role in the existing model router, such as `default`, `background`, `think`, `long_context`, `image`, `web_search`. |
| **Overlay** | The merge operation that applies a profile's slot values on top of the global default values for the duration of a single request. |
| **Profile path** | A URL prefix of the form `/p/{profile-name}/v1/...` that selects which profile applies to a request. |
| **Web-search interception** | The runtime pattern in which the proxy inspects a request's tool-call payload, detects a web-search tool invocation, and substitutes the dispatched model with the profile's `web_search` slot value before forwarding the request. |
| **CLI under management** | Any command-line tool that targets the proxy as its upstream provider, including but not limited to pi, opencode, hermes, claude-code, codex. |

## 3. User Scenarios

### 3.1 Primary User Story

As a power user running multiple AI coding assistants in parallel terminal sessions, I want each tool to use its own bundle of model configurations so that pi can use a fast tool-caller while claude-code uses a slower thoughtful main model, all sharing one proxy instance, one compression layer, and one command-rewriting layer.

### 3.2 Acceptance Scenarios

**Scenario 1: Five tools, five profiles, one proxy**
- Given: The proxy is running with five profiles defined and aliases configured for each tool.
- When: The user opens five terminals and launches pi, opencode, hermes, claude-code, and codex concurrently, each via its profile-specific alias.
- Then: Each tool's requests are routed through its own slot configuration. The proxy logs show the correct profile name and the correct dispatched model per request. No tool's configuration affects any other tool's behavior.

**Scenario 2: Web-search interception swaps the model**
- Given: A profile defines a `web_search` slot value distinct from its `default` slot value.
- When: A request from that profile contains a web-search tool invocation as the only tool call in the turn.
- Then: The proxy substitutes the request's model field with the profile's `web_search` slot value before dispatching upstream. Non-search turns from the same profile dispatch to the `default` slot value unchanged.

**Scenario 3: Unknown profile is rejected**
- Given: A client targets a profile path whose name is not defined in the profile registry.
- When: The request arrives at the proxy.
- Then: The proxy returns a structured error response naming the unknown profile and listing all valid profile names. The request does not reach any upstream provider.

**Scenario 4: Backward compatibility for legacy clients**
- Given: A client is configured with the proxy's pre-existing base URL that contains no profile prefix.
- When: The client sends a request to that URL.
- Then: The proxy treats the request as if it targets the `default` profile. The request succeeds with the proxy's existing global routing behavior. No client reconfiguration is required for tools that do not need profile-specific routing.

**Scenario 5: Profile registry edited without restart**
- Given: The proxy is running and serving requests.
- When: A user edits the profile registry file to add a new profile or modify an existing one.
- Then: The next request that resolves a profile reads the updated file content. No proxy restart is required. Concurrent in-flight requests are unaffected by the edit.

## 4. Functional Requirements

### 4.1 Profile Registry

**FR-001**: The system SHALL maintain a profile registry file that contains a top-level mapping of profile names to flat slot-override dictionaries.
- Acceptance: A valid registry file with at least the `default` profile loads successfully at proxy startup and is queryable through the resolver interface.

**FR-002**: The system SHALL reject startup if the registry file is missing, malformed, or lacks a `default` profile.
- Acceptance: Each of the three failure conditions produces a distinct startup error message that names the specific defect and the registry file path.

**FR-003**: The system SHALL recognize a fixed set of slot names that match the proxy's existing model router slots, plus an optional `notes` field per profile.
- Acceptance: The recognized slot names are `default`, `background`, `think`, `long_context`, `image`, and `web_search`. Any other top-level key in a profile entry is ignored without error. The `notes` field is preserved but never used for routing.

**FR-004**: The system SHALL re-read the registry file when its modification time has changed since the last load.
- Acceptance: An mtime check runs on every profile resolution. When the mtime differs from the cached value, the file is reloaded before resolution proceeds. The reload cost is bounded by a single `os.stat` call plus a JSON parse when the mtime has changed.

### 4.2 Path-Based Profile Selection

**FR-010**: The system SHALL accept requests at path prefix `/p/{profile-name}/v1/chat/completions` and `/p/{profile-name}/v1/messages` and treat the path-segment `{profile-name}` as the requested profile for that request.
- Acceptance: A request to `/p/pi/v1/chat/completions` is processed identically to a request to `/v1/chat/completions` except that the resolved profile is `pi` rather than `default`.

**FR-011**: The system SHALL continue accepting requests at the legacy paths `/v1/chat/completions` and `/v1/messages` and SHALL treat such requests as targeting the `default` profile.
- Acceptance: A request to a legacy path produces identical behavior to a request that explicitly targets `/p/default/v1/...`. No existing client requires reconfiguration.

**FR-012**: The system SHALL reject a request to a profile path whose `{profile-name}` is not defined in the registry, returning a 404-class error with a structured body that names the missing profile and lists the valid alternatives.
- Acceptance: The error body is JSON. It contains a `profile_requested` field, a `profiles_available` field (array), and a human-readable `message` field. The request never reaches any upstream provider.

### 4.3 Profile Overlay on Slot Routing

**FR-020**: The system SHALL build a per-request profile context at request entry containing the resolved profile name and the profile's merged slot dictionary, where the merge is the profile's slot values overlaid onto the `default` profile's slot values.
- Acceptance: For every slot key, the resolved value is the profile's value if defined and the default profile's value otherwise. The context is created once per request and passed down the request handling stack as a parameter, not stored in any global or module-level state.

**FR-021**: The system SHALL consult the per-request profile context for slot resolution before falling back to the proxy's global slot configuration.
- Acceptance: When the model router selects a model for a slot, it checks the profile context first; if the profile context defines that slot, the profile's value is used; otherwise the global slot value is used.

**FR-022**: The system SHALL ensure that no request's profile context leaks into another request's processing.
- Acceptance: Concurrent requests targeting different profiles each see only their own profile context. Concurrent requests targeting the same profile each see independent context objects. No mutation of one context affects another.

### 4.4 Web-Search Tool-Call Interception

**FR-030**: The system SHALL inspect every request's tool-call payload after profile resolution and before upstream dispatch, identifying whether the request constitutes a web-search invocation.
- Acceptance: The inspection recognizes web-search invocations in both OpenAI-style requests (via `tool_choice` referencing a tool whose name matches the web-search pattern) and Anthropic-style requests (via a `tools` array entry of type `web_search_20250305` or matching the web-search pattern).

**FR-031**: The system SHALL substitute the request's model field with the active profile's `web_search` slot value when (a) a web-search invocation is detected, (b) the profile defines a `web_search` slot value, and (c) the web-search tool is the only tool invoked in that turn.
- Acceptance: The substitution happens before the cascade router runs, so cascade and circuit-breaker logic operate on the swapped model. The substitution event is logged with both the original and new model names plus the active profile name.

**FR-032**: The system SHALL allow per-profile opt-out of web-search interception via an optional `web_search_intercept` boolean field that defaults to `true` when absent.
- Acceptance: A profile with `web_search_intercept: false` skips the inspection entirely for that profile's requests. Other profiles' behavior is unaffected.

**FR-033**: The system SHALL allow per-profile customization of the web-search detection pattern via an optional `web_search_pattern` regex field.
- Acceptance: The pattern is used to match tool names during inspection. When absent, the system uses a default pattern matching the common web-search tool naming conventions: `web_search`, `search_web`, `brave_search`, and `exa_search`.

### 4.5 Backward Compatibility

**FR-040**: The system SHALL preserve the behavior of every existing route, endpoint, CLI command, configuration file, and integration that does not opt into the profile system.
- Acceptance: The existing test suite passes unchanged after the profile system is added. Legacy aliases continue to work without modification. The web dashboard's existing surfaces are unaffected. The existing `proxies` CLI commands continue to function identically.

**FR-041**: The system SHALL treat the profile registry as additive: a deployment without a registry file SHALL function as if a registry containing only a synthesized `default` profile (derived from the proxy's current global configuration) were present.
- Acceptance: The proxy starts and serves requests on legacy paths even when no `profiles.json` exists, behaving exactly as the pre-profile-system proxy did.

## 5. Non-Functional Requirements

### 5.1 Performance

**NFR-001**: Profile resolution SHALL add no more than 1 millisecond to request latency at the 99th percentile under normal load.
- Verified by benchmark comparing pre-profile and post-profile request latencies against a mock upstream, with the registry file present and mtime-cached.

**NFR-002**: The system SHALL support at least 50 concurrent profiled requests without contention on the profile registry cache.
- Verified by load test running 50 parallel clients each cycling through five profile paths for 60 seconds without errors or measurable latency degradation versus a single-client baseline.

### 5.2 Reliability

**NFR-010**: A malformed registry file modification SHALL NOT crash the proxy or affect in-flight requests.
- Verified by writing a corrupted registry file while requests are in flight. The proxy logs a parse error, retains the last good registry state, and continues serving requests using that cached state until the file is corrected.

**NFR-011**: An unknown-profile request SHALL fail closed, never falling through to an unintended profile or to the global configuration as a silent fallback.
- Verified by sending requests to invalid profile paths and confirming each receives the structured 404-class error per FR-012.

### 5.3 Observability

**NFR-020**: Every request that resolves a profile SHALL emit a log record containing the resolved profile name, the dispatched model, and (when applicable) any web-search interception event.
- Verified by parsing proxy logs after a controlled test session and confirming the profile name appears in every relevant record.

**NFR-021**: The proxy's existing usage-tracking storage SHALL persist the profile name for every recorded request to enable per-profile analytics.
- Verified by querying the usage-tracking storage after a multi-profile test session and confirming the profile name is queryable as a column or field on each request record.

### 5.4 Maintainability

**NFR-030**: The profile resolver and overlay logic SHALL live in a single dedicated module to confine the surface area of future changes.
- Verified by code review: all profile-aware logic outside of route registration and one router signature change lives in the dedicated module.

**NFR-031**: Adding a new profile SHALL require only an edit to the registry file, with no source-code change, no rebuild, and no proxy restart.
- Verified by adding a new profile entry to the registry file while the proxy is running and confirming requests to its profile path are served correctly without intervention.

## 6. Key Entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Profile Registry | A persistent mapping of profile names to slot-override dictionaries | File path, last-loaded mtime, cached parsed content | Contains many Profile entries; consulted by the Resolver |
| Profile | A named bundle of slot overrides plus optional metadata | Name, slot dictionary, web-search interception flag, web-search pattern, notes | Belongs to the Registry; consumed by Profile Context |
| Profile Context | A per-request object carrying the resolved profile state | Profile name, merged slot dictionary | Created at request entry; consumed by the model router and the web-search interceptor; discarded after response is sent |
| Slot | A named role in the model router | Slot name, model identifier | Referenced by Profile entries and by the global router; the unit of override |
| Web-Search Match Pattern | The regex pattern used to identify web-search tool invocations | Pattern string, scope (per-profile or default) | Belongs to a Profile or to the system-wide default; consulted by the interceptor |

## 7. Success Criteria

SC-001: A user can run pi, opencode, hermes, claude-code, and codex concurrently against a single proxy instance, each with independent slot configurations, without restarting the proxy and without any tool's configuration affecting any other tool's behavior.

SC-002: Web-search invocations from a profile that defines a distinct `web_search` slot value dispatch to that slot's model rather than the profile's `default` slot model, in 100% of qualifying turns.

SC-003: Adding a new profile or modifying an existing profile requires only a registry file edit, with the change observable on the next matching request and no proxy restart.

SC-004: The proxy's existing test suite passes unchanged after the profile system is integrated, demonstrating that no legacy behavior has regressed.

SC-005: Profile resolution adds no more than 1 millisecond of P99 latency to request handling, demonstrating that the overlay mechanism is not a hot-path cost.

## 8. Prior Art Analysis

### 8.1 Existing Solutions

| Solution | Strengths | Weaknesses | Gap This Project Fills |
|----------|-----------|------------|----------------------|
| claude-code-router | Mature task-category routing, multi-provider support, dynamic `/model` switching | Single global config per running instance; no per-client profile isolation; no tool-call interception | Multi-CLI concurrent isolation, web-search-specific model swap |
| LiteLLM proxy | Hierarchical Keys > Teams > Global resolution, virtual keys, model_group_alias | Cannot inspect tool-call payloads to rewrite model field mid-request; designed for upstream gateway concerns, not per-CLI tool-role routing | In-request tool-call inspection and model rewrite for web-search role |
| ccs (CCS) | Request-time `profile:model` selectors, scenario-based routing, multi-runtime bridges | Centered on OAuth/account switching; profile semantics are coarser than per-slot overlays | Slot-granular overlay model aligned with the existing internal router |
| Multiple proxy instances per CLI | Trivial isolation, zero code changes | Multiplies compression-layer and command-rewriting-layer memory cost; configuration sprawl | Single-instance solution preserving the existing single-compression-layer architecture |

### 8.2 Patterns Adopted

The path-based addressing of profiles is the convergent pattern across CCS's `profile:model` selectors and the typical practice of placing per-tenant routes at distinct URL prefixes. The slot vocabulary (`default`, `background`, `think`, `long_context`, `image`, `web_search`) is adopted unchanged from the proxy's existing model router so that profiles are overlays on the existing semantics rather than a parallel taxonomy.

### 8.3 Patterns Avoided

Filesystem-watcher hot-reload, profile inheritance via explicit `_inherits` keys, and triple-hop resolution via header and model-name-prefix mechanisms were considered and rejected for this version. The rationale and conditions for their later inclusion are documented in `future-plans.md`. Header-based profile selection in particular was rejected because no CLI under management exposes a clean header injection mechanism, which makes the path-based route the only universally compatible primary mechanism.

## 9. Assumptions and Dependencies

### Assumptions
- Users targeting profile-specific behavior will configure their CLI's base URL to point at a profile-prefixed path, typically through the proxy's alias-installation script.
- The profile registry file is owned and edited by the same user who runs the proxy; no multi-user write coordination is required.
- The proxy continues to expose its model router slot vocabulary; profiles are valid only insofar as that vocabulary remains stable.
- Web-search tool naming conventions across the CLIs under management remain dominated by the default pattern; per-profile pattern overrides handle outliers.

### Dependencies
- Requires the proxy's existing model router and slot-based routing to remain in place; this project layers atop that subsystem rather than replacing it.
- Requires the proxy's existing FastAPI routing infrastructure for new route registration.
- Requires the existing usage-tracking storage to gain a single new column or field for profile name (a minor migration).

## 10. Identified Risks

| # | Risk | Severity | Mitigation | Related Req |
|---|------|----------|-----------|-------------|
| 1 | Profile context leaks across concurrent requests via shared mutable state | High | Use per-request dependency injection (FastAPI `Depends` or equivalent), avoid module-level mutable caches except the immutable mtime-keyed registry cache | FR-022 |
| 2 | Registry file corruption during a live edit produces a hard failure | Medium | Retain the last-good parsed registry in memory; surface parse errors via logs without affecting in-flight requests | NFR-010 |
| 3 | Upstream fork divergence from `fuergaosi233/claude-code-proxy` widens, complicating future merges | Medium | Land the profile system on a long-lived feature branch with a tagged release; document the schema in the fork's `CHANGELOG.md` | (architectural) |
| 4 | Web-search interception conflicts with a future pi version that exposes its own web-search model parameter | Low | The per-profile `web_search_intercept: false` opt-out gives a single-line fix when the conflict emerges | FR-032 |
| 5 | A tool sends a request with both a web-search tool and other tools, and the interceptor incorrectly swaps the model for a non-search-dominant turn | Medium | Constrain swap logic to the case where the web-search tool is the only tool invoked in the turn or is explicitly forced via `tool_choice` | FR-031 |

## 11. Scope Boundaries

### In Scope
- Profile registry file with flat per-profile slot-override dictionaries
- Path-based profile selection at `/p/{profile-name}/v1/...`
- Per-request profile context plumbing through the request handler stack
- Slot-resolution overlay logic that consults the profile context before the global router
- Web-search tool-call interception with per-profile opt-out and per-profile pattern customization
- Backward compatibility for all legacy routes, configurations, and integrations
- Mtime-based registry reload (no filesystem watcher required)
- Per-request profile-name emission to logs and usage-tracking storage

### Out of Scope
- Filesystem-watcher-based hot-reload (mtime check is sufficient for this version)
- Explicit profile inheritance via `_inherits` keys (the implicit `default` overlay handles every observed case)
- Header-based profile selection (`X-Proxy-Profile`) and model-name-prefix profile selection (no managed CLI supports the former; the latter introduces model-name pollution)
- A dedicated profile-management binary or interactive TUI (the existing `proxies` CLI is the natural home for any management subcommands)
- Generation of starter profile templates from a CLI command (registry edits are simple enough to be hand-authored)
- Per-profile provider-override that routes to a specific upstream provider entry rather than a model (deferred for Phase 4 forward compatibility but not implemented now)
- OAuth account selection per profile (a separate concern that the schema must remain forward-compatible with)
- Per-profile cascade chain overrides distinct from slot overlays (the existing cascade applies uniformly within a slot's resolution)
- Dashboard UI for editing profiles (registry file edits are sufficient; only read-only display is in scope for the dashboard surface)

### Future Considerations
- Provider-override slot enabling per-profile upstream account routing
- Dashboard read-only surface showing the resolved overlay and per-profile request counts
- Per-profile cascade chain customization if a concrete need emerges
- Web-search interception extensions to handle multi-tool turns intelligently

