# Feature Specification: Unified Configuration & Multi-Surface Control System

**Feature Branch**: `001-unified-config-system`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "Route any provider+model to any tier or purpose slot (big/middle/small + default/background/think/long_context/web_search/image). All values settable via .env, CLI arguments, TUI, and web UI. Arbitrary-length proxy chain reorderable and toggleable from every surface."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Route any model to any tier or slot from any surface (Priority: P1)

An operator configuring the proxy wants to say "use `openai/o1-preview` for `think`, `nvidia/nemotron-nano-9b-v2:free` for `background`, and a custom NVIDIA endpoint+key for the `big` tier" — and have that work whether they express it via `.env`, a CLI flag at startup, the interactive TUI, or the web dashboard. Today the tier and slot configuration surfaces are asymmetric (tiers expose `model` only; slots expose `model+base_url+api_key`), and the three editing surfaces (env, TUI, web) each write to different stores without sharing a resolution path. This forces operators to remember which surface "wins," restart the server to apply changes, and accept that some capabilities only work from one surface.

**Why this priority**: Without symmetric capability across tiers and slots, and without all four surfaces feeding the same resolver, every other feature in the system (cascade fallback, routing, compression) inherits the inconsistency. This is the foundation on which the rest is built.

**Independent Test**: Set a `big` tier to `provider=nvidia, model=nemotron-70b, base_url=custom, api_key=custom` via each of the four surfaces in sequence; confirm each change takes effect in the next request without restart and that the resolver reports the correct provenance (which surface supplied the value).

**Acceptance Scenarios**:

1. **Given** a running proxy with `big` tier configured via `.env`, **When** the operator changes the `big` tier model via the TUI, **Then** the next incoming request uses the new model without a proxy restart.
2. **Given** conflicting values for the same field across surfaces, **When** a request arrives, **Then** the resolver selects the value according to documented precedence (CLI > shell env > .env file > stored config > defaults) and can report which source won.
3. **Given** a router slot (`think`, `background`, `long_context`, etc.), **When** the operator sets a full `(provider, model, base_url, api_key)` assignment for it, **Then** that slot is handled with the same capability as a tier (no capability gap).
4. **Given** a purpose slot with no explicit assignment, **When** a matching request arrives, **Then** the system falls back to the tier model appropriate for the request (`big`/`middle`/`small`) without error.

---

### User Story 2 — Assemble an arbitrary-length proxy chain in any order (Priority: P1)

An operator wants to define the chain as `[proxy1, proxy2, proxy3, …]` where each slot is filled by a named proxy entry (Claude Code Proxy, Headroom, RTK, CLIProxyAPI, or a user-added custom entry), with the option to omit any entry entirely. They need to express this across every surface: env declarations, CLI flags, TUI drag/arrow-key reorder, and web-UI drag-and-drop.

**Why this priority**: The chain topology is what determines whether compression applies, whether OAuth tokens pass through, and which upstream receives the final request. Operators need to experiment with chain order without hand-editing JSON.

**Independent Test**: Create a new chain entry via the CLI; reorder it via the TUI; disable it via the web UI; confirm each surface's mutation is reflected in the other surfaces immediately and in the next request's routing.

**Acceptance Scenarios**:

1. **Given** a chain with entries `[claude_code_proxy, headroom, rtk]`, **When** the operator reorders them via any surface to `[rtk, headroom, claude_code_proxy]`, **Then** the new order is used for the next request and is visible in all other surfaces.
2. **Given** an operator-defined custom chain entry, **When** it is added via one surface, **Then** it appears as editable in every other surface.
3. **Given** any chain entry, **When** it is toggled off from any surface, **Then** it is skipped in request flow while remaining in the configuration for re-enabling.

---

### User Story 3 — Live-reload configuration across surfaces without restart (Priority: P2)

An operator iterating on routing choices wants changes made in one surface to be reflected in every other surface and in the running proxy within seconds, without restarting the process or losing in-flight requests.

**Why this priority**: Eliminates the restart-tax that today dominates the config-edit loop. Enables rapid experimentation and real-time monitoring-driven tuning.

**Independent Test**: Make an edit in the TUI while the web UI is open in a browser; confirm the web UI reflects the change within 2 seconds. Make an edit in the web UI while a request is in flight; confirm the in-flight request completes against the old config and the next request uses the new config.

**Acceptance Scenarios**:

1. **Given** a request is currently streaming, **When** the configuration changes, **Then** the in-flight request completes under the configuration it started with.
2. **Given** two surfaces are open simultaneously, **When** one makes a change, **Then** the other surface reflects the change without manual refresh.
3. **Given** a malformed edit from any surface, **When** the change would produce an invalid configuration, **Then** the edit is rejected with a specific error and the running configuration is preserved.

---

### User Story 4 — Discoverable precedence and provenance (Priority: P3)

An operator debugging why a request went to the wrong model wants to ask "where did this value come from?" and receive a clear answer naming the surface (CLI, shell env, .env file, stored config, default) and the exact key.

**Why this priority**: Enables self-service debugging. Without it, the layered precedence model is opaque and operators resort to re-reading source code.

**Independent Test**: Query the running proxy's config introspection endpoint/command; for any given field, confirm the response reports both the current value and the layer that supplied it.

**Acceptance Scenarios**:

1. **Given** the same field is defined in `.env` and the stored config, **When** the operator queries provenance, **Then** the response shows `.env` as the winning source.
2. **Given** a value was overridden via CLI flag at startup, **When** the operator queries provenance, **Then** the response shows `cli` as the winning source.

---

### Edge Cases

- What happens when the same field is set in `.env` and as a CLI flag with conflicting values? → Documented precedence (CLI wins) must be enforced and queryable.
- What happens when a chain entry's `service_cmd` fails to start? → The entry is marked unhealthy in all surfaces; request routing skips it if configured to do so, or surfaces a clear error if not.
- What happens when an operator sets a slot's `api_key` to a literal string like `${OPENROUTER_API_KEY}`? → The value is resolved as an environment-variable reference, not a literal, consistent with existing chain-entry behavior.
- What happens when a tier has no model and no cascade defined? → Requests to that tier fail fast with a specific error naming the missing configuration, not a generic upstream failure.
- What happens when two concurrent edits are made to the stored config via different surfaces? → The later write wins; a conflict warning surfaces in both UIs within the live-reload window.
- What happens when an operator adds a chain entry whose port conflicts with another? → Validation rejects the edit before persisting; the error identifies both entries.
- What happens when a secret value like `api_key` is set in the stored config vs `.env`? → Secrets in the stored config trigger a warning; the system prefers env-var references (`${VAR_NAME}`) to avoid git-commit footguns.

## Requirements *(mandatory)*

### Functional Requirements

#### Unified assignment model

- **FR-001**: System MUST represent every model assignment — whether a tier (big/middle/small) or a purpose slot (default/background/think/long_context/web_search/image) — using a single record type containing at minimum: identifier, model, provider, base URL, API key reference, and enabled flag.
- **FR-002**: System MUST allow any assignment (tier or slot) to specify a complete `(provider, model, base_url, api_key)` tuple so that tiers and slots have symmetric capability.
- **FR-003**: System MUST support new assignment identifiers being added (beyond the current fixed set) without code changes — purely via configuration.

#### Multi-surface configuration

- **FR-004**: System MUST support reading, writing, and live-reloading every assignment and every chain entry from each of four surfaces: `.env` file, command-line arguments, terminal UI, web UI.
- **FR-005**: System MUST resolve conflicting values from multiple surfaces using a single documented precedence order (CLI > shell env > .env file > stored config > defaults).
- **FR-006**: System MUST expose a query mechanism that, for any given field, reports the current value and the surface that supplied it.
- **FR-007**: System MUST apply configuration changes to subsequent requests within 5 seconds of the change being persisted, without requiring a process restart.
- **FR-008**: System MUST complete any in-flight request against the configuration active when that request began, even if a configuration change is persisted mid-request.

#### Proxy chain

- **FR-009**: System MUST support a proxy chain containing an arbitrary number of entries in an operator-defined order.
- **FR-010**: Every chain entry MUST be independently toggleable between enabled and disabled without removing it from the chain.
- **FR-011**: The order, enabled state, and configuration of chain entries MUST be editable from all four surfaces (env, CLI, TUI, web UI).
- **FR-012**: System MUST treat the proxy itself as a chain entry, so that its position relative to upstream services is configurable like any other entry.
- **FR-013**: System MUST validate chain edits before persisting (e.g., port conflicts, missing required fields, unreachable service commands) and reject invalid edits with a specific error identifying the offending entry and field.

#### Secrets handling

- **FR-014**: System MUST support environment-variable references in configuration values (syntax: `${VAR_NAME}`) so that secrets can live in `.env` or the shell environment rather than the stored config file.
- **FR-015**: System MUST warn when a literal secret value (detected by format heuristics — e.g., a string matching an API-key pattern) is stored in the persisted config file.

#### CLI surface

- **FR-016**: Every field editable via the TUI or web UI MUST also be settable via a documented CLI argument at process startup.
- **FR-017**: CLI-supplied values MUST flow through the same resolver used by every other surface, not a separate code path.

#### TUI surface

- **FR-018**: The TUI MUST allow reordering chain entries using arrow keys and toggling enabled state with a single key press.
- **FR-019**: The TUI MUST allow editing any assignment's fields using inline forms without leaving the TUI session.

#### Web UI surface

- **FR-020**: The web UI MUST allow reordering chain entries via drag-and-drop.
- **FR-021**: The web UI MUST present assignment editors that mirror the field set exposed by the TUI and CLI.
- **FR-022**: The web UI MUST reflect configuration changes originated from other surfaces without manual page refresh.

#### Backward compatibility and migration

- **FR-023**: System MUST continue to honor legacy env-var names (`BIG_MODEL`, `ENABLE_BIG_ENDPOINT`, `BIG_ENDPOINT`, `BIG_API_KEY`, and the equivalents for middle/small) for a deprecation window, mapping them onto the unified assignment model.
- **FR-024**: System MUST emit a deprecation warning when a legacy env-var is the source of a resolved value, naming the modern equivalent.
- **FR-025**: System MUST operate with a single environment-variable source file: `.env`. The `.envrc` pattern is not supported.

### Key Entities

- **Assignment**: A unit of routing configuration identifying a `(provider, model, base_url, api_key, enabled)` target. Exists in two kinds: *tier* (capacity class — big/middle/small) and *slot* (purpose — default/background/think/long_context/web_search/image). Future kinds may be added without schema change.
- **ProxyEntry**: A node in the request chain. Carries an identifier, display name, order index, enabled flag, optional upstream URL, optional service-lifecycle command, optional health-check path, and metadata. The proxy itself is representable as a ProxyEntry.
- **ProxyChain**: An ordered list of ProxyEntry records plus the associated RouterConfig.
- **RouterConfig**: The collection of slot Assignments plus threshold/behavior settings (e.g., long-context threshold, routing-disabled flag, passthrough flag).
- **ConfigLayer**: A source of values in the precedence stack. Five layers exist: CLI-overrides, shell env, .env file, stored config file, hard defaults.
- **ResolvedValue**: The result of consulting the layers for a field — carries the field path, the resolved value, and the winning layer name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Any field editable via the TUI can also be edited via CLI flag, `.env`, and web UI. Coverage audit reports 100% parity across surfaces.
- **SC-002**: A configuration change persisted via any surface affects the next matching request within 5 seconds, without process restart, in at least 95% of trials across a 100-trial test.
- **SC-003**: An operator asked "where did this value come from?" can obtain a correct answer for any configuration field in under 10 seconds using a single command or UI action.
- **SC-004**: The number of unique environment-variable names relevant to tier/slot/provider configuration is reduced by at least 40% compared to the pre-change baseline, with legacy names still functional for a deprecation window.
- **SC-005**: A new chain entry or new assignment kind can be added and configured without touching Python source code — only by editing the stored configuration or supplying env/CLI values.
- **SC-006**: An in-flight streaming request is never interrupted by a concurrent configuration edit in 100% of trials.
- **SC-007**: An invalid configuration edit (port conflict, missing required field, malformed env-var reference) is rejected with a specific, actionable error in 100% of trials and never corrupts the persisted state.
- **SC-008**: Chain reordering is reflected across all four surfaces within 5 seconds of the persisting edit, in at least 95% of trials.

## Assumptions

- `.envrc` has been removed as of 2026-04-23; `.env` is the sole file-based environment source going forward.
- The existing `proxy_chain.json` (or its successor single-file stored config) is acceptable as the persistent store for structured configuration; secrets are not required to live there.
- All four configuration surfaces (env, CLI, TUI, web UI) operate on the same host or network-local; no multi-node configuration sync is required in this feature.
- Operators are technically proficient enough to edit JSON/env files directly if a UI is unavailable; the UI surfaces are convenience layers, not hard requirements for operation.
- Existing chain-entry behaviors — env-var reference expansion (`${VAR}`), service lifecycle commands, health-check paths — remain the contract and are preserved.
- The current usage of `python-dotenv` with `override=False` (shell env wins over `.env`) is retained; this defines two adjacent layers of the precedence stack.
- The existing tier-to-provider auto-detection (prefix-based) is retained as a last-resort fallback when no explicit provider is supplied for an assignment.
- OAuth-based Claude authentication remains a supported flow and must continue to work when the chain is configured in a `passthrough` topology (proxy does no model rewriting).
- Breaking changes to the public API of the proxy (the Anthropic/OpenAI-compatible HTTP surface consumed by Claude Code and other clients) are out of scope for this feature.
- Drag-and-drop in the web UI targets modern evergreen browsers; no IE/legacy support required.
