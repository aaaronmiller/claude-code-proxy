# Feature Specification: Unified Configuration & Multi-Surface Control System

**Feature Branch**: `001-unified-config-system`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "Route any provider+model to any tier or purpose slot (big/middle/small + default/background/think/long_context/web_search/image). All values settable via .env, CLI arguments, TUI, and web UI. Arbitrary-length proxy chain reorderable and toggleable from every surface."

## Clarifications

### Session 2026-04-23

- Q: What authentication/authorization posture do the new config-write endpoints require? → A: Admin-only via existing RBAC — write endpoints require an administrator role in the existing role-based access control system; read endpoints require an authenticated user but no elevated role.
- Q: What scope of "add without code changes" does FR-003 promise? → A: Slot-only expansion for internal purpose slots, **plus** a configurable incoming-identifier mapping layer. Tiers remain fixed at big/middle/small. New purpose slots may be added via config. Separately, incoming model/role identifiers from upstream systems (Anthropic model names, Hermes agent role names, future Anthropic task types) map to any assignment via a configurable translation table, so new upstream identifiers are accepted without middleware reassignment. Fallback chains work across any assignment kind, including cases where upstream systems (e.g., Hermes `config.yaml`) do not natively support fallbacks for the field.
- Q: How does the system handle a stored config file whose schema predates the running proxy version? → A: Auto-migrate with a migration log. The stored config carries a `schema_version`. On load, missing fields receive defaults, legacy shapes are translated into the current schema, and the file is rewritten at the current version. A human-readable migration log (e.g., `config/migrations/YYYY-MM-DD-<description>.log`) records what changed and why, so operators have an audit trail across upgrades.
- Q: Where and in what form are successful configuration changes recorded, and what per-role/per-model analytics must the system provide? → A: Dedicated append-only audit file (`logs/config-audit.log`) captures each successful write with timestamp, principal, endpoint, field path, and before/after values (secrets masked). **Additionally**, request-level analytics MUST track the resolved assignment (role/tier/slot) *and* the actual model that served each request as separate, pivotable dimensions. Tool-call success/failure MUST be tallied per assignment and per model so operators can determine whether a failure trend is attributable to the role configuration or to the underlying model. When a cascade fallback occurs, each attempt (primary and each fallback) MUST be recorded individually with a shared request identifier so per-assignment and per-model success rates are computable independently.

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
- What happens when a non-admin authenticated user attempts a config-write endpoint? → The request is rejected with a permission-denied response; the stored configuration is unchanged and the attempt is logged.
- What happens when an unauthenticated request reaches any configuration endpoint (read or write)? → The request is rejected with an authentication-required response; no configuration data is disclosed.
- What happens when a proxy upgrade encounters a stored config file of a prior schema version? → The proxy auto-migrates the file to the current schema, writes a migration log entry describing each transformation, and proceeds to serve requests without manual operator intervention.
- What happens when an auto-migration cannot be performed safely (field semantics changed in a way that can't be inferred)? → The proxy refuses to mutate the file, fails startup with a message naming the problematic fields, and preserves the stored config untouched for the operator to fix by hand.

## Requirements *(mandatory)*

### Functional Requirements

#### Unified assignment model

- **FR-001**: System MUST represent every model assignment — whether a tier (big/middle/small) or a purpose slot (default/background/think/long_context/web_search/image) — using a single record type containing at minimum: identifier, model, provider, base URL, API key reference, and enabled flag.
- **FR-002**: System MUST allow any assignment (tier or slot) to specify a complete `(provider, model, base_url, api_key)` tuple so that tiers and slots have symmetric capability.
- **FR-003**: Tier identifiers are fixed at `big`, `middle`, and `small`, reflecting the upstream Anthropic model-size taxonomy. Adding a new tier requires code changes and is out of scope for configuration.
- **FR-003a**: Purpose-slot identifiers MAY be added purely via configuration. Routing code MUST NOT hardcode the set of slot identifiers; slot lookup MUST be dynamic, so a new slot `my_custom_purpose` declared in configuration is reachable by the custom-router hook without a code change.
- **FR-003b**: System MUST support a configurable incoming-identifier mapping table that maps upstream model or role identifiers (e.g., Anthropic model names like `claude-opus-4-7`, Hermes agent role names from their `config.yaml`, future Anthropic task-type identifiers) to assignments. An incoming identifier present in the table resolves via the mapped assignment; an incoming identifier not present falls back to the existing tier-based mapping.
- **FR-003c**: The incoming-identifier mapping table MUST be editable from all four surfaces (`.env`, CLI, TUI, web UI), on equal footing with assignments and chain entries.
- **FR-003d**: Fallback chains MUST be expressible for any assignment, independent of whether the upstream system that produced the originating identifier (e.g., Hermes `config.yaml` for a given role) natively supports fallbacks for that field. When an upstream system's configuration forbids fallback, this proxy MAY still provide fallback behavior on that path.

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

#### Security and access control

- **FR-026**: All configuration-write endpoints exposed by the web UI (create, update, delete, reorder for assignments and for chain entries) MUST require the caller to be an authenticated user holding an administrator role in the project's existing role-based access control system.
- **FR-027**: All configuration-read endpoints exposed by the web UI MUST require the caller to be an authenticated user; non-administrator roles are acceptable for read access.
- **FR-028**: The CLI and TUI surfaces, which are invoked from the same host as the proxy process, inherit host-level trust and are not required to enforce the RBAC admin check. Network-reachable surfaces (web UI) MUST enforce it.
- **FR-029**: Rejected write attempts (non-admin or unauthenticated) MUST be logged with the attempted endpoint, the attempting principal (if known), and the timestamp.

#### Observability and analytics

- **FR-030**: Successful configuration writes MUST be appended to a dedicated, append-only audit log file (e.g., `logs/config-audit.log`). Each entry MUST include: ISO-8601 timestamp, principal (authenticated user identity), endpoint invoked, field path(s) affected, and the before/after values with any secret-shaped fields (API keys, tokens) masked.
- **FR-031**: For every request routed by the proxy, telemetry MUST record at minimum: request identifier, timestamp, incoming identifier (upstream model/role name as received), resolved assignment identifier (which tier or slot handled the request), resolved model (the actual model dispatched to), status (success/failure), latency, and tool-call outcome counts (attempted, succeeded, failed).
- **FR-032**: The resolved assignment identifier and the resolved model MUST be separate, independently-queryable dimensions in the analytics data. This enables operators to ask distinct questions: "What is the success rate of the `think` slot over the last 24 hours?" and "What is the success rate of model X over the last 24 hours?" without conflating the two.
- **FR-033**: When cascade/fallback occurs for a single incoming request, each attempt (the primary target and each subsequent fallback) MUST be recorded as a distinct telemetry row, all sharing the same request identifier. Per-assignment success rate counts the primary-target outcome; per-model success rate counts each model's own outcome. This makes it possible to distinguish role-configuration failures (assignment consistently fails before fallback) from model-capability failures (a specific model consistently fails regardless of which role invoked it).
- **FR-034**: An analytics query surface MUST expose aggregate statistics filterable by time range and groupable by at least the following dimensions: resolved assignment, resolved model, incoming identifier, and tool name. This surface MAY reuse the existing metrics endpoints if they are extended with the required dimensions.
- **FR-035**: Secret-shaped field values (matching known API-key or token patterns) MUST NEVER appear in the audit log, analytics records, or any query response in unmasked form. Field paths referencing secret fields MUST remain visible; the *value* side MUST be redacted (e.g., `"***masked***"` or `"sk-...1234"`).

#### Backward compatibility and migration

- **FR-023**: System MUST continue to honor legacy env-var names (`BIG_MODEL`, `ENABLE_BIG_ENDPOINT`, `BIG_ENDPOINT`, `BIG_API_KEY`, and the equivalents for middle/small) for a deprecation window, mapping them onto the unified assignment model.
- **FR-023a**: The stored configuration file MUST carry an explicit schema version identifier. When the running proxy loads a stored file whose schema version is older than the current expected version, the proxy MUST auto-migrate the file: missing fields are populated with documented defaults, legacy shapes are translated into the current schema, and the file is rewritten at the current version.
- **FR-023b**: Auto-migration MUST produce a human-readable migration log at a predictable location (e.g., `config/migrations/YYYY-MM-DD-<slug>.log`) describing each transformation applied, so operators have an audit trail across proxy upgrades.
- **FR-023c**: If auto-migration would be destructive (e.g., a field's semantics changed in a way that cannot be inferred automatically), the proxy MUST refuse to mutate the stored file and MUST fail startup with a specific error naming the fields that require operator attention, rather than silently dropping or guessing values.
- **FR-024**: System MUST emit a deprecation warning when a legacy env-var is the source of a resolved value, naming the modern equivalent.
- **FR-025**: System MUST operate with a single environment-variable source file: `.env`. The `.envrc` pattern is not supported.

### Key Entities

- **Assignment**: A unit of routing configuration identifying a `(provider, model, base_url, api_key, enabled)` target. Exists in two kinds: *tier* (capacity class — big/middle/small) and *slot* (purpose — default/background/think/long_context/web_search/image). Future kinds may be added without schema change.
- **ProxyEntry**: A node in the request chain. Carries an identifier, display name, order index, enabled flag, optional upstream URL, optional service-lifecycle command, optional health-check path, and metadata. The proxy itself is representable as a ProxyEntry.
- **ProxyChain**: An ordered list of ProxyEntry records plus the associated RouterConfig.
- **RouterConfig**: The collection of slot Assignments plus threshold/behavior settings (e.g., long-context threshold, routing-disabled flag, passthrough flag).
- **ConfigLayer**: A source of values in the precedence stack. Five layers exist: CLI-overrides, shell env, .env file, stored config file, hard defaults.
- **ResolvedValue**: The result of consulting the layers for a field — carries the field path, the resolved value, and the winning layer name.
- **IdentifierMapping**: A rule mapping an incoming identifier (an upstream model name, agent role name, or task-type identifier) to an assignment. Absence of a mapping for a given identifier triggers the tier-based default resolution. Fallback chains attached to the mapped assignment apply when the primary target fails.
- **AuditLogEntry**: An append-only record of a successful configuration write. Carries: timestamp, principal, endpoint, field-path(s), before-value, after-value (secrets masked), and a monotonic sequence number.
- **RequestMetric**: One row per attempt for an incoming request. Carries: request identifier (shared across fallback attempts), timestamp, incoming identifier, resolved assignment, resolved model, attempt index (0 = primary, 1+ = cascade fallback), status, latency, and tool-call outcome counts. The per-assignment success rate is computed from rows where `attempt_index = 0`; the per-model success rate is computed across all rows regardless of `attempt_index`.

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
- **SC-009**: For any 24-hour period, an operator can obtain the success rate of any single assignment (tier or slot) and the success rate of any single model independently, in under 10 seconds per query, via a single command or web-UI action.
- **SC-010**: When analyzing a failure trend, an operator can determine within one analytics session whether the trend correlates with the assignment, with the model, with both, or with neither — by pivoting the same telemetry data along two independent dimensions.
- **SC-011**: The configuration audit log contains one entry for every successful write in 100% of trials across an adversarial test (concurrent writes, rapid successive edits, interleaved failed writes). No successful write is missing; no failed write is recorded as successful.
- **SC-012**: No secret-shaped value appears unmasked in any analytics record, audit-log entry, or query response in 100% of trials across a test suite that enumerates every field in the configuration schema.

## Assumptions

- `.envrc` has been removed as of 2026-04-23; `.env` is the sole file-based environment source going forward.
- The existing structured configuration file used by the proxy is acceptable as the persistent store; secrets are not required to live there.
- All four configuration surfaces (env, CLI, TUI, web UI) operate on the same host or network-local; no multi-node configuration sync is required in this feature.
- Operators are technically proficient enough to edit JSON/env files directly if a UI is unavailable; the UI surfaces are convenience layers, not hard requirements for operation.
- Existing chain-entry behaviors — env-var reference expansion (`${VAR}`), service lifecycle commands, health-check paths — remain the contract and are preserved.
- The established behavior where shell environment values win over file-based environment values is retained; this defines two adjacent layers of the precedence stack.
- The existing tier-to-provider auto-detection (prefix-based) is retained as a last-resort fallback when no explicit provider is supplied for an assignment.
- OAuth-based Claude authentication remains a supported flow and must continue to work when the chain is configured in a `passthrough` topology (proxy does no model rewriting).
- Breaking changes to the public API of the proxy (the Anthropic/OpenAI-compatible HTTP surface consumed by Claude Code and other clients) are out of scope for this feature.
- Drag-and-drop in the web UI targets modern evergreen browsers; no IE/legacy support required.
- Upstream systems that feed requests into this proxy (e.g., Claude Code, Hermes agent runtime, Qwen Code) may each define their own identifier schemes for models, roles, or task types. This feature accepts those identifiers via the IdentifierMapping table and does not require upstream systems to conform to a shared taxonomy.
- Tier stability (big/middle/small fixed) is assumed; if Anthropic introduces a new model-size tier, treating it will require a follow-up feature that extends the tier set. The IdentifierMapping layer, however, can absorb new *model names* within the existing tiers without any code change.
