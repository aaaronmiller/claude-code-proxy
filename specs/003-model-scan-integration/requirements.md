---
date: 2026-05-30 16:08:12 PDT
ver: 1.0.0
author: claude-code-proxy-worker
model: claude-opus-4-8
tags: [model-scan, routing, requirements, selection-policy, cascade, quicklaunch]
---

# Model-Scan Integration -- Requirements Specification v1.0

## 1. Purpose

The router that fronts every coding agent in this stack currently pins all three model
tiers to a single hardcoded model and ships empty fallback chains. When that model is
slow, rate limited, or withdrawn, every connected tool degrades at once and a human has
to hand edit configuration to recover. Separately, a diagnostic engine already probes ten
providers daily and scores every reachable model on intelligence, speed, agentic ability,
and coding, gated per role and per price. The two systems have never been connected.

This project connects them. It lets the router pick the best model for each role at launch
or on demand, drawn from fresh measured data, under a stated preference: best free model,
best model under a price ceiling, best model regardless of price, or an explicit per-role
choice. It makes fallback chains real and availability aware. It does this without making
the router depend on the diagnostic engine being online, and without merging the two
projects, so each remains independently useful.

The value is concrete. A user can launch any of a dozen coding tools through one router and
say "use the best free models right now" or "stay under this cost," and the router binds
every role to a measured winner with a measured fallback list, recovering automatically
when a provider fails.

## 2. Glossary

| Term | Definition |
|------|-----------|
| **Router** | The single entry point every coding tool connects to. It decides which model serves each request and chains to a compression stage and provider. |
| **Diagnostic engine** | The separate, pre-existing system that probes providers and scores models per role on measured performance, capability, and price. |
| **Role** (slot) | A named job a model performs, for example primary reasoning, tool calling, compression, vision, delegation, web extraction. Each role has its own quality and price gates. |
| **Snapshot** | A versioned, self-contained file the diagnostic engine publishes, listing the best model and a ranked candidate list for each role, with price and capability flags. The only thing the two projects share. |
| **Selection policy** | A user-chosen rule for picking a model from a role's candidates: best free, best under a price ceiling, best overall, explicit per role, or keep the static configured value. |
| **Tier** | One of three fixed router slots (big, middle, small) that incoming requests map to before role resolution. |
| **Profile** | A per-tool overlay on the router that adjusts model choices for a specific client without affecting others. Selected by the connection address the tool uses. |
| **Cascade** | The ordered list of fallback models the router tries when the primary model for a request fails. |
| **Binding** | The act of resolving each role and tier to a concrete model plus its fallback cascade by applying a selection policy to a snapshot. |
| **Blocklist** | A published set of model identifiers judged below the quality bar, excluded from every selection regardless of score. |
| **Launcher** | A command that starts a chosen coding tool already wired through the router, with arguments to choose policy, profile, and compression. |

## 3. User Scenarios

### 3.1 Primary User Story

As an operator running many coding agents through one router, I want to launch any tool and
declare a single preference for model cost and quality, so that every role is bound to the
best currently measured model with an automatic fallback list, without editing config by
hand.

### 3.2 Acceptance Scenarios

**Scenario 1: Launch with best free models**
- Given: a recent snapshot exists and the diagnostic engine is not running.
- When: the operator launches a coding tool with the best-free preference.
- Then: every role and tier binds to the highest scoring model whose price is zero, each
  role gets a fallback cascade of the remaining free candidates, and the tool starts.

**Scenario 2: Launch under a price ceiling**
- Given: a recent snapshot with mixed free and paid candidates.
- When: the operator launches with a price ceiling preference set to a value.
- Then: each role binds to the highest scoring model whose blended price is at or below the
  ceiling, and candidates above the ceiling are excluded from both the primary choice and
  the cascade.

**Scenario 3: Role-specific selection for tool calling**
- Given: a profile that binds the tool-calling role to a capable measured model.
- When: a request arrives that requires tool calling.
- Then: the router serves it with the role-bound tool-capable model, and on failure falls
  through the role cascade, never selecting a blocklisted model.

**Scenario 4: Diagnostic engine offline or snapshot missing**
- Given: no snapshot file is present, or it is older than the staleness limit.
- When: the router starts or reloads.
- Then: the router keeps its static configured models, logs a warning, surfaces the stale
  or missing state, and serves requests normally.

**Scenario 5: Provider failure during concurrent use**
- Given: a dozen tools are connected and the primary model for a role begins failing.
- When: requests for that role arrive.
- Then: the router advances through the role cascade per its existing failure handling, and
  in-flight requests already resolved to a target are not disrupted by a concurrent rebind.

**Scenario 6: Manual refresh after a new scan**
- Given: the operator has just run a fresh scan that produced a new snapshot.
- When: the operator triggers a model refresh on the running router.
- Then: the router rebinds all roles and tiers from the new snapshot and reports which
  models changed and which were sourced from the snapshot versus static config.

**Scenario 7: Low-RAM agent launch**
- Given: the low-RAM agent is a supported launch target.
- When: the operator launches it through the router.
- Then: its profile biases every role to fast, low-cost measured models, compression is
  enabled by default, and it runs through the same router as every other tool.

**Scenario 8: Two sessions of one tool with different configs**
- Given: the chain is up and the operator has two different session files for the same tool.
- When: the operator launches the tool twice, once with each file.
- Then: each session runs on its own ephemeral profile at a distinct address with independent
  routing, both through the one chain, and ending one leaves the other unaffected.

**Scenario 9: One-command chain bring-up**
- Given: nothing in the chain is running and OAuth-hosted providers are configured.
- When: the operator runs the chain bring-up command.
- Then: the router, the OAuth upstream proxy, and the compression stage with its local model
  all come up healthy from the single command.

## 4. Functional Requirements

### 4.1 Snapshot Production

**FR-001**: The diagnostic engine SHALL publish a snapshot artifact that lists, for each
defined role, the selected best model and a ranked list of candidate models.
- Acceptance: After a scan, the artifact exists at the configured location and contains at
  least one role with a non-empty candidate list.

**FR-002**: Each candidate in the snapshot SHALL carry a router-ready model identifier, the
provider, a fitness score, a blended price, and capability flags for tool calling and
vision.
- Acceptance: Every candidate entry contains all listed fields; missing price is
  represented explicitly rather than omitted.

**FR-003**: The snapshot SHALL declare a schema version and a generation timestamp.
- Acceptance: Both fields are present and the version follows a documented scheme.

**FR-004**: The snapshot SHALL include the published blocklist and per-provider health at
generation time.
- Acceptance: A reader can determine, from the snapshot alone, which models are blocked and
  which providers were healthy.

**FR-005**: The diagnostic engine SHALL write the snapshot atomically so a reader never
observes a partially written file.
- Acceptance: Concurrent reads during a write either see the previous complete snapshot or
  the new complete snapshot, never a truncated one.

**FR-006**: The diagnostic engine SHALL also serve the current snapshot over its existing
local interface for on-demand retrieval.
- Acceptance: A request to the snapshot endpoint returns the same content as the file.

### 4.2 Snapshot Consumption and Binding

**FR-010**: The router SHALL load the snapshot at startup, on reload signal, on cache
expiry, and on explicit operator refresh.
- Acceptance: Each of the four triggers results in a re-read and rebind, observable in logs.

**FR-011**: The router SHALL validate a snapshot against the declared schema before binding
and SHALL refuse to bind from an incompatible major schema version.
- Acceptance: A snapshot with an unsupported major version is rejected and the last good
  binding is retained.

**FR-012**: The router SHALL resolve each tier and each bound role to a concrete model and a
fallback cascade by applying the active selection policy to the snapshot.
- Acceptance: After binding, each bound tier and role has a non-empty model and a cascade
  derived from the snapshot candidates.

**FR-013**: The router SHALL construct each cascade from the role's ranked candidates with
blocklisted and gate-failing entries removed and the chosen primary excluded.
- Acceptance: No cascade contains a blocklisted model or the primary itself; order matches
  candidate ranking.

**FR-014**: The router SHALL never select or place in a cascade any model present on the
snapshot blocklist.
- Acceptance: A blocklisted model never appears as a bound primary or in any cascade.

**FR-015**: When binding produces no eligible candidate for a role or tier, or the mapped
role is absent from the snapshot, the router SHALL retain the static configured value for
that role or tier rather than leaving it empty.
- Acceptance: A role whose candidates are all excluded, and a tier mapped to a role not
  present in the snapshot, both keep a usable model.

**FR-016**: The router SHALL degrade to static configured models when the snapshot is
missing, unreadable, or older than the configured staleness limit, and SHALL continue
serving requests.
- Acceptance: With no snapshot, requests still succeed using static config and a warning is
  logged.

**FR-017**: The router SHALL record, for each bound tier and role, whether its model came
from the snapshot or from static config, and expose this provenance for inspection.
- Acceptance: An inspection surface lists source per tier and role.

### 4.3 Selection Policies

**FR-020**: The router SHALL support a best-free policy that selects, per role, the highest
ranked candidate whose price is zero.
- Acceptance: Under best-free, every bound model has zero price when at least one free
  candidate exists for that role.

**FR-021**: The router SHALL support a price-ceiling policy parameterized by a numeric
ceiling, selecting the highest ranked candidate at or below the ceiling. A price-ceiling
policy without a ceiling value SHALL be treated as a configuration error and resolved as the
static policy rather than binding an unbounded price.
- Acceptance: Under a ceiling, no bound model exceeds the ceiling; candidates lacking a known
  price are treated as ineligible; a ceiling policy with no value falls back to static and
  logs an error.

**FR-022**: The router SHALL support a quality policy that selects the highest ranked
candidate regardless of price.
- Acceptance: Under quality, the bound model equals the role's top eligible candidate by
  fitness.

**FR-023**: The router SHALL support a roles policy that honors explicit per-role bindings
and resolves each using that role's own free-or-paid gate.
- Acceptance: Each explicitly bound role resolves from its mapped role definition.

**FR-024**: The router SHALL support a static policy that ignores the snapshot and keeps the
configured models, as the safe default.
- Acceptance: Under static, no model differs from configuration regardless of snapshot.

**FR-025**: The active policy SHALL be selectable at launch without editing persisted
configuration.
- Acceptance: A launch-time preference overrides the configured default policy for that run.

### 4.4 Profile Role Bindings

**FR-030**: The system SHALL map, per profile, each tier and use case to a role, with a
global default mapping and per-profile overrides.
- Acceptance: A profile without overrides inherits the default mapping; an override changes
  only the specified role bindings.

**FR-031**: Profile role bindings SHALL apply as overlays after tier resolution, consistent
with existing profile overlay behavior.
- Acceptance: A profile binding changes the served model only for requests on that profile.

**FR-032**: A profile MAY leave selected tiers static while binding others from the
snapshot.
- Acceptance: A profile can pass one tier through unchanged while sourcing another from the
  snapshot in the same request path.

**FR-033**: Every role used by a supported client SHALL map to a defined role in the
diagnostic engine, so that no client role is left without measured candidates. The complete
Hermes role set is the reference inventory and SHALL be fully covered.
- Acceptance: Each of the fifteen Hermes roles (primary, delegation, compression, vision,
  web extract, session search, approval, flush memories, mcp, skills hub, title generation,
  triage, kanban, profile describer, curator) resolves to a diagnostic-engine role; a
  coverage check reports zero unmapped roles.

**FR-034**: The system SHALL bind client-specific auxiliary roles (those beyond the three
tiers and the common use cases) only through the owning client's profile, not the global
default, so that auxiliary roles never affect other clients.
- Acceptance: An auxiliary role binding appears only on its owning profile's requests.

### 4.45 Session-Scoped Configuration

**FR-035**: The system SHALL resolve a session's routing from a layered composition, in order
of increasing precedence: the base chain configuration, a named preset, an optional session
configuration file, and optional inline arguments.
- Acceptance: an inline argument overrides the same setting in the file, which overrides the
  preset, which overrides the base; the effective resolved configuration is inspectable.

**FR-036**: The system SHALL accept a session configuration file that defines the selection
policy, the compression toggle, the main-model provider selection, and per-role and per-tier
model and provider overrides.
- Acceptance: a file specifying these fields produces the corresponding routing for that
  session and nothing leaks to other sessions.

**FR-037**: The router SHALL support ephemeral, session-scoped profiles created at launch and
removed at session end, each served at a unique address, so that two or more sessions of the
same tool can run different configurations concurrently through the one chain.
- Acceptance: two sessions of one tool started with different files route independently;
  ending one does not change the other.

**FR-038**: Creating or removing a session profile SHALL NOT require restarting the router or
editing persisted global configuration.
- Acceptance: sessions begin and end against a running router with no edit to the global
  profile or chain files.

**FR-039**: The system SHALL provide curated presets for the Claude, Codex, Hermes, Pi, Ante,
and OpenCode tools, each usable directly as a default launch or as the base layer for a
session file or inline arguments.
- Acceptance: each named tool launches from its preset with sensible per-role defaults and
  accepts further overrides without editing the preset.

### 4.5 Launch and Tool Support

**FR-040**: The system SHALL provide a launcher that starts any supported coding tool wired
through the router, the compression stage, and the terminal compression wrapper.
- Acceptance: Launching any supported tool routes its traffic through the router on the
  expected address.

**FR-041**: The launcher SHALL accept arguments to choose the selection policy, the profile,
whether compression is enabled, and a continue or resume mode where the tool supports it.
- Acceptance: Each argument changes the launched environment accordingly and is documented
  in launcher help.

**FR-042**: The system SHALL support all of the following launch targets through the router:
the Claude coding tool, the Codex tool, the Qwen tool, the Pi agent, the Hermes agent, the
OpenCode tool, the Antigravity tool, and the low-RAM Ante agent.
- Acceptance: Each target has a working launch path and profile.

**FR-043**: The system SHALL provide a low-RAM profile for the Ante agent that biases all
tiers to fast, low-cost measured models and enables compression by default.
- Acceptance: Launching the low-RAM agent binds its tiers to compression-class models.

**FR-044**: The router SHALL serve at least a dozen concurrently connected tools in any
combination without per-request snapshot file reads.
- Acceptance: Under concurrent load, request handling reads an in-memory snapshot, not the
  file, and no client interferes with another.

**FR-045**: Existing short launch aliases SHALL continue to work and SHALL accept an optional
policy preference.
- Acceptance: Prior aliases launch as before and honor a policy preference when supplied.

### 4.55 Chain Lifecycle

**FR-046**: The system SHALL bring up the entire proxy chain with a single command: the
router, the OAuth upstream proxy when indicated, and the compression stage including its local
model.
- Acceptance: one command results in every required chain service reporting healthy.

**FR-047**: The chain bring-up SHALL start the OAuth upstream proxy only when configuration
indicates OAuth-hosted providers are in use.
- Acceptance: with no OAuth providers configured the upstream proxy is not started; with them
  configured it is started and healthy.

**FR-048**: The chain bring-up SHALL start the compression stage together with the local model
it depends on.
- Acceptance: after bring-up both the compression stage and its local model are reachable.

**FR-049**: Launching a tool SHALL verify the chain is up and SHALL bring it up if absent.
- Acceptance: launching with the chain down brings the chain up before the tool starts.

### 4.6 Refresh Interface

**FR-050**: The router SHALL expose an operator action to refresh models from the snapshot or
the diagnostic engine interface without a restart.
- Acceptance: Invoking the action rebinds and returns the updated assignments and which
  models changed.

### 4.7 Lanes and Quota-Aware Rotation

**FR-051**: The system SHALL define consumption lanes, each with a selection policy and a quota
pool. At minimum a `standby` lane (free pool only) and an `interactive` lane (quota-aware
S-tier rotation) SHALL exist.
- Acceptance: a request is served under exactly one lane, observable in its provenance.

**FR-052**: Each preset SHALL declare a lane, and a session MAY override it.
- Acceptance: the 24/7 agents default to `standby`, the CLI tools default to `interactive`,
  and a session argument can change the lane for that session only.

**FR-053**: The `standby` lane SHALL NOT consume premium (paid) quota under any policy.
- Acceptance: with only standby-lane traffic, no paid provider quota is decremented.

**FR-054**: Under the `interactive` lane, the primary and reasoning roles SHALL bind to the
highest-capability tier model with remaining quota, while toolcalling and menial roles SHALL
bind to free models.
- Acceptance: with quota available, the primary resolves to an S-tier model and toolcalling
  resolves to a free model in the same session.

**FR-055**: The `rotate` policy SHALL move the primary role to the next-best paid provider or
account when the current provider crosses a configurable quota-drain threshold, and when the
paid pool is exhausted SHALL fall to the best free model (a free floor) rather than holding a
paid provider in reserve. The free floor SHALL prefer a configurable default free model and
SHALL defer to the diagnostic engine when it ranks a better free model higher.
- Acceptance: draining a paid provider past the threshold rebinds the primary to the next paid
  provider; with all paid providers drained the primary binds to the best free model and never
  forces a paid call; the configured preferred free model is used unless a higher-ranked free
  model exists.

**FR-056**: The system SHALL maintain a per-provider quota ledger sourced from a subscription
usage feed, the diagnostic engine quota interface, the router's existing usage and billing
components, and live observation of usage and rate-limit responses.
- Acceptance: the ledger reflects subscription consumption, API-credit and balance state, the
  router's own routed usage, and live 429s; the snapshot carries per-provider quota and reset
  times.

**FR-059**: Quota sources SHALL be pluggable behind a common adapter interface, and the ledger
SHALL reuse the router's existing usage, rate-limit, and billing components rather than
duplicating them. No single external tool SHALL be a hard dependency.
- Acceptance: an external quota source can be added or removed by configuration; with all
  external sources absent, the ledger still functions from the router's internal components.

**FR-057**: The router SHALL rotate among a per-provider pool of keys or accounts on rate-limit
responses, transparently to the client.
- Acceptance: a 429 on one key advances to the next key in the pool without surfacing an error
  to the client when another key has quota.

**FR-058**: Rotation SHALL apply hysteresis and a per-provider cooldown to avoid rapid flapping
between providers at quota boundaries.
- Acceptance: a provider just rotated away from is not reselected until its cooldown elapses.

### 4.8 Observability

**FR-060**: The chain bring-up SHALL, by default, present a visible monitor showing the
compression stage output and the router output, with an option to run detached.
- Acceptance: the default bring-up shows live compression ratios and routing; a flag detaches.

**FR-061**: Every log line, error, and metric across the chain SHALL be tagged with the session
correlation id of the originating session.
- Acceptance: filtering by a session id returns only that session's activity across components.

**FR-062**: The system SHALL write structured errors from all chain components and the launcher
to a single append-only error log with source, session id, provider, model, error class, and
timestamp.
- Acceptance: an error in any component appears in the single log with those fields.

**FR-063**: The system SHALL provide a command to tail and filter the unified error log by
tool, provider, or session.
- Acceptance: the command returns matching errors for each filter.

**FR-064**: The system SHALL export observed reliability per provider and model (latency, error
rate, rate-limit frequency) back to the diagnostic engine for use in future scans.
- Acceptance: after a period of traffic, the diagnostic engine receives reliability data keyed
  by provider and model.

## 5. Non-Functional Requirements

### 5.1 Performance

**NFR-001**: Request-path model resolution SHALL add no synchronous file or network read
attributable to this feature.
- Acceptance: Profiling a served request shows snapshot access served from memory.

**NFR-002**: A rebind SHALL complete fast enough to avoid disrupting in-flight requests and
SHALL swap the active snapshot atomically.
- Acceptance: In-flight requests during a rebind complete on their already-resolved target.

**NFR-003**: Rotation and quota-ledger reads on the request path SHALL use in-memory state
only; the subscription usage feed and the diagnostic engine quota interface SHALL be consulted
out of band, never synchronously per request.
- Acceptance: a served request performs no synchronous quota network call attributable to this
  feature.

### 5.2 Reliability

**NFR-010**: The router SHALL remain fully operational when the diagnostic engine is absent
for an arbitrary duration.
- Acceptance: With the engine never started, the router serves requests indefinitely on
  static or last-good bindings.

**NFR-011**: A malformed or truncated snapshot SHALL never crash the router or empty a
binding.
- Acceptance: Feeding corrupt snapshots leaves the last good binding intact.

### 5.3 Security

**NFR-020**: The snapshot SHALL contain no credentials. Provider keys SHALL be resolved only
from the router's existing secret sources.
- Acceptance: Inspection of any snapshot shows no secret material; bound models still
  authenticate using existing keys.

**NFR-021**: The integration SHALL NOT alter the existing credential loading order or the
placeholder key convention.
- Acceptance: Credential resolution behavior is unchanged by enabling the feature.

### 5.4 Compatibility

**NFR-030**: With the feature disabled or under the static policy, observable routing
behavior SHALL be identical to the pre-integration baseline.
- Acceptance: A regression comparison under static shows no behavioral difference.

**NFR-031**: The two projects SHALL share only the snapshot contract and SHALL NOT import one
another.
- Acceptance: Neither codebase references the other as a code dependency.

## 6. Key Entities

| Entity | Description | Key Attributes | Relationships |
|--------|-------------|----------------|---------------|
| Snapshot | Published measured selection data for all roles | schema version, generation time, blocklist, provider health | contains many Role Selections |
| Role Selection | Per-role best model and ranked candidates | role name, free-or-paid gate, best candidate, candidate list | belongs to Snapshot; bound to a Tier or use case |
| Candidate | One scored model option for a role | model identifier, provider, fitness, price, tool flag, vision flag | listed within a Role Selection; may enter a Cascade |
| Selection Policy | Rule for choosing among candidates | kind, optional price ceiling | applied during Binding |
| Tier Assignment | A fixed router slot resolved to a model | tier name, model, provider, cascade, source | produced by Binding from a Role Selection |
| Profile Binding | Per-tool mapping of tiers and use cases to roles | profile name, tier-to-role map, overrides | overlays Tier Assignment for one tool |
| Cascade | Ordered fallback models for a role | ordered model list | derived from a Role Selection minus blocklist and primary |
| Launch Configuration | A way to start a tool through the router | tool, policy, profile, compression flag | selects a Profile and Selection Policy |
| Preset | A curated named profile for one tool | tool, default policy, per-role defaults | base layer for a Session |
| Session Config | The effective routing for one running tool instance | layered from base, preset, file, args | produces an Ephemeral Profile |
| Ephemeral Profile | A session-scoped profile served at a unique address | id, url prefix, overlay, ttl | created and removed per Session |
| Chain | The set of services a launch depends on | router, optional upstream proxy, compression stage and local model | brought up by one command |
| Lane | A consumption class with a policy and quota pool | name, policy, pool, free floor | assigned to a Preset or Session |
| Quota Ledger | Per-provider remaining quota and reset state | provider, remaining, reset time, source | feeds the Rotation decision |
| Rotation State | Live selection state for the interactive primary | active provider, cooldowns, free floor | derived from Quota Ledger and Snapshot |

## 7. Success Criteria

- SC-001: An operator can launch any supported tool and bind every role to a measured model
  with a non-empty cascade in a single command, with no manual config edit.
- SC-002: When the primary model for a role fails, requests recover via the cascade without
  operator intervention.
- SC-003: Switching from best-free to a price ceiling to quality changes the bound models
  appropriately and is verifiable from the provenance surface.
- SC-004: With the diagnostic engine never started, every supported tool still launches and
  serves requests.
- SC-005: At least a dozen tools run concurrently through the router with no per-request
  snapshot file access.
- SC-006: No blocklisted model is ever bound or placed in a cascade across all policies.
- SC-007: An operator can run two sessions of the same tool with different session files
  concurrently, each routing independently, through one chain.
- SC-008: A single command brings up the router, the OAuth upstream proxy when indicated, and
  the compression stage with its local model.
- SC-009: Each of the six named tools (Claude, Codex, Hermes, Pi, Ante, OpenCode) launches
  from a curated preset and accepts file or argument overrides without editing the preset.
- SC-010: Over a week, the interactive lane keeps the primary on S-tier models and rotates
  across the paid pool and free S-tier source so that available premium quota is substantially
  consumed before falling back, while 24/7 agents run on free models only.
- SC-011: An operator can find the origin of a cascading error across multiple running tools by
  filtering the unified error log on one session correlation id or provider.

## 8. Prior Art Analysis

### 8.1 Existing Solutions

| Solution | Strengths | Weaknesses | Gap This Project Fills |
|----------|-----------|------------|------------------------|
| Claude Code Router | Per-request routing by task type and token count, free-model support, single launch command, multi-provider | Fallback lists are static and quality-blind; selection is hand-written rules, not measured | Supplies measured, availability and price aware selection plus real cascades as a reusable artifact |
| Portkey, LiteLLM gateways | Production fallbacks, cooldowns, priority lists, tracing | Fallback is reactive and quality-blind; availability alone does not recover quality | Adds proactive, benchmark-grounded ranking before failures occur |
| RouteLLM, Not Diamond | Learned or preference-based routing between strong and weak models | Research-grade or hosted; pairwise quality, not per-role price-aware selection across many providers | Provides per-role, multi-provider, price-tiered selection wired into an existing local router |
| Unify | Live benchmarks optimizing cost, speed, quality | Hosted product and routing surface; not a local decoupled file feeding the operator's own proxy | Keeps selection local, versioned, and consumable by an independently owned router |

### 8.2 Patterns Adopted

- Single launch command that starts the tool already wired to the router, borrowed from
  Claude Code Router ergonomics.
- Priority list and cooldown style fallback from production gateways, here populated from
  measured rankings rather than hand maintained lists.
- Per-role evaluation gates so a compression role and a reasoning role are judged
  differently.

### 8.3 Patterns Avoided

- Request-time calls to an external selection service, rejected because it adds latency and
  a hard runtime dependency to the hot path.
- Merging the diagnostic engine into the router, rejected because each is independently
  useful and the coupling surface should stay small.
- Hardcoded model allowlists in the router, rejected in favor of a published blocklist and
  measured rankings.

## 9. Assumptions and Dependencies

### Assumptions
- A snapshot is produced on a schedule or on demand and is usually present, but the router
  must tolerate its absence.
- Role definitions and their price and quality gates are owned by the diagnostic engine.
- Provider credentials already exist in the router's secret sources.

### Dependencies
- The diagnostic engine must emit the agreed snapshot contract.
- The router must retain its existing tier, profile, cascade, and failure-handling
  facilities.

## 10. Identified Risks

| # | Risk | Severity | Mitigation | Related Req |
|---|------|----------|-----------|-------------|
| 1 | Snapshot drift makes the router bind to a withdrawn model | Medium | Cascade fallback and staleness degradation to static | FR-013, FR-016 |
| 2 | Concurrent rebind disrupts in-flight requests | Medium | Atomic immutable snapshot swap; resolved targets are stable | NFR-002, FR-044 |
| 3 | Price data missing for a candidate under a ceiling policy | Low | Treat unknown price as ineligible for ceiling policies | FR-021 |
| 4 | Schema evolution breaks the consumer | Medium | Versioned schema with major-version refusal and last-good retention | FR-011 |
| 5 | A blocklisted but high-scoring model slips into a cascade | High | Centralized blocklist filter applied to every selection and cascade | FR-014 |
| 6 | Ante local router and the proxy router conflict | Low | Define composition: the agent classifies complexity, the router selects the concrete model | FR-043 |

## 11. Scope Boundaries

### In Scope
- The snapshot contract and its production by the diagnostic engine.
- Snapshot consumption, binding, selection policies, and cascade construction in the router.
- Per-profile role bindings with a global default.
- Graceful degradation to static configuration.
- A launcher and profiles for all named tools including the low-RAM agent.
- An operator refresh action.

### Out of Scope
- Per-request live selection calls to the diagnostic engine.
- Merging the two projects or sharing code beyond the contract.
- Changing how the diagnostic engine scores models.
- Changing the compression stage or the terminal compression wrapper internals.

### Future Considerations
- Feeding the router's observed reliability back into the diagnostic engine to weight future
  scans.
- Per-request policy selection if a need emerges beyond launch-time and reload-time binding.
