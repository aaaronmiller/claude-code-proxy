# Feature Specification: Model-Scan Integration

**Feature Branch**: `003-model-scan-integration`
**Created**: 2026-05-30
**Status**: Draft
**Input**: `specs/003-model-scan-integration/requirements.md` and `design.md` (this repository)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Measured role binding with live cascades (Priority: P1)

An operator launches a coding tool and every model role binds to a measured winner from a fresh
diagnostic snapshot, each with a real, availability-ranked fallback cascade, under one stated
preference (best free, best under a price ceiling, best overall, explicit per role, or keep
static). When the primary model for a role fails, requests recover via the cascade without a
human editing config.

**Why this priority**: This is the core value and the MVP. Today all three tiers are pinned to
one hardcoded model with empty cascades; this story alone removes the single point of failure
and makes selection measured.

**Independent Test**: With a fixture snapshot and the engine offline, launch under the best-free
preference and confirm every bound role has a non-empty model and cascade; kill the primary
provider and confirm recovery via the cascade.

**Acceptance Scenarios**:

1. **Given** a recent snapshot and the engine not running, **When** the operator launches under
   best-free, **Then** every role and tier binds to the top zero-price candidate with a free
   cascade tail.
2. **Given** a price-ceiling preference, **When** binding runs, **Then** no bound model exceeds
   the ceiling and unknown-price candidates are excluded.
3. **Given** the primary model for a role begins failing, **When** requests arrive, **Then** the
   router advances through the role cascade and no blocklisted model is ever selected.
4. **Given** no snapshot is present, **When** the router starts, **Then** it serves on static
   config, logs a warning, and never empties a binding.

---

### User Story 2 - One-command chain and quicklaunch presets (Priority: P1)

An operator brings the whole chain up with one command (router, the OAuth upstream proxy when
indicated, and the compression stage with its local model) shown in a visible monitor, then
launches any of the supported tools through it with a second command wrapped by the terminal
compression tool.

**Why this priority**: Without a working launch path and chain bring-up, the binding work is not
usable. Required for an end-to-end MVP.

**Independent Test**: Run the chain-up command with OAuth providers configured and confirm all
required services report healthy in a visible monitor; launch each named tool and confirm its
traffic routes through the router.

**Acceptance Scenarios**:

1. **Given** nothing running and OAuth providers configured, **When** the operator runs chain-up,
   **Then** the router, the upstream proxy, and the compression stage with its local model all
   come up healthy in a visible monitor window.
2. **Given** the chain is up, **When** the operator launches any of Claude, Codex, Hermes, Pi,
   Ante, or OpenCode from its preset, **Then** the tool runs through the router with sensible
   per-role defaults.
3. **Given** the chain is down, **When** the operator launches a tool, **Then** the chain is
   brought up before the tool starts.

---

### User Story 3 - Session-scoped configuration and concurrent sessions (Priority: P2)

An operator defines a session's routing by preset, a config file, or inline arguments, and runs
two or more sessions of the same tool with different configurations at the same time, each
routing independently through the one chain.

**Why this priority**: Enables the real multi-tool, multi-config workflow. Builds on P1 launch
but is not required for a single-session MVP.

**Independent Test**: Launch one tool twice with two different session files; confirm each runs on
its own ephemeral profile at a distinct address with independent routing, and ending one does not
affect the other.

**Acceptance Scenarios**:

1. **Given** two session files for one tool, **When** the operator launches the tool twice,
   **Then** each session gets its own ephemeral profile and routes independently.
2. **Given** a preset, a session file, and inline args, **When** they conflict, **Then** the
   inline arg wins over the file, which wins over the preset.
3. **Given** an official-provider session with a per-role override, **When** a tool call is made,
   **Then** the main model passes through to the official provider while the tool call routes to
   the override model.

---

### User Story 4 - Lanes and quota-aware tiered rotation (Priority: P2)

An operator runs always-on agents on free models only, while interactive CLI tools keep the
primary on the best S-tier model with remaining weekly quota, rotating across the paid pool plus
a free S-tier source, with tool calling forced to free models, and falling to a free floor rather
than a paid reserve when paid quota is spent.

**Why this priority**: Delivers maximum weekly quota utilization and protects premium quota, the
operator's stated goal, but layers on top of the binding and rotation substrate.

**Independent Test**: With a fixture quota ledger, confirm the interactive primary picks an S-tier
model with quota and toolcalling picks free; drain the paid pool and confirm the primary falls to
the best free model; confirm standby-lane traffic never decrements paid quota.

**Acceptance Scenarios**:

1. **Given** quota available, **When** an interactive session runs, **Then** the primary binds to
   an S-tier model and toolcalling binds to a free model.
2. **Given** a paid provider crosses the drain threshold, **When** the next request arrives,
   **Then** the primary rotates to the next paid provider, with a cooldown preventing flapping.
3. **Given** the paid pool is exhausted, **When** a request arrives, **Then** the primary binds to
   the best free model (preferred default unless the engine ranks a better free model higher) and
   never forces a paid call.
4. **Given** only standby-lane traffic, **When** it runs, **Then** no paid provider quota is
   decremented.

---

### User Story 5 - Unified observability across many tools (Priority: P3)

An operator running many tools traces a cascading error to its origin by filtering one log on a
session id or provider, and watches compression ratios and routing live.

**Why this priority**: High operational value but not required to deliver routing or rotation.

**Independent Test**: Run several sessions, inject an error in one, and confirm it appears in the
single error log tagged with that session's correlation id and is filterable.

**Acceptance Scenarios**:

1. **Given** a dozen tools running, **When** an error occurs in one, **Then** it appears in the
   single error log with source, session id, provider, model, and timestamp.
2. **Given** the unified error log, **When** the operator filters by session or provider, **Then**
   only the matching activity is returned.

---

### User Story 6 - Full role coverage and reliability feedback (Priority: P3)

Every role used by a supported client maps to a measured diagnostic role (the full fifteen Hermes
roles), and the router exports observed reliability back to the engine to weight future scans.

**Why this priority**: Completeness and a learning loop; valuable but the system functions without
it for the common tiers and use cases.

**Independent Test**: Run a coverage check and confirm zero unmapped Hermes roles; after a period
of traffic, confirm the engine receives reliability data keyed by provider and model.

**Acceptance Scenarios**:

1. **Given** the Hermes role set, **When** the coverage check runs, **Then** all fifteen roles
   resolve to a diagnostic role with zero unmapped.
2. **Given** a period of traffic, **When** the export interval elapses, **Then** the engine
   receives per-provider and per-model latency, error rate, and rate-limit frequency.

---

### Edge Cases

- Snapshot missing, empty, stale, or schema-incompatible: degrade to static, retain last good
  binding, surface staleness, never fail a request.
- Binding yields no eligible candidate for a role: keep that role's static value.
- Concurrent rebind under load: atomic immutable swap; in-flight requests keep their resolved
  target.
- Unknown provider in the snapshot: skip with a warning; the router resolves base_url and key
  from its own registry and never dials an untrusted endpoint.
- Budget policy without a ceiling: resolve as static rather than binding an unbounded price.
- All external quota sources absent: the ledger still functions from internal components.
- Missing exit trap on a session: a TTL sweep reclaims idle ephemeral profiles.

## Requirements *(mandatory)*

Functional and non-functional requirements are maintained in full in
`specs/003-model-scan-integration/requirements.md` (FR-001 through FR-064, NFR-001 through
NFR-031), each with acceptance criteria. They map to the user stories as follows:

- US1: FR-001 to FR-025, FR-033 (binding, policies, cascade, degradation, role coverage)
- US2: FR-040 to FR-049 (launch, presets, chain lifecycle)
- US3: FR-030 to FR-039 (profile bindings, session config, ephemeral profiles)
- US4: FR-051 to FR-059, NFR-003 (lanes, quota ledger, rotation, free floor)
- US5: FR-060 to FR-063 (observability, unified errors)
- US6: FR-033, FR-034, FR-064 (full role coverage, reliability feedback)

### Key Entities

Snapshot, Role Selection, Candidate, Selection Policy, Tier Assignment, Profile Binding, Cascade,
Launch Configuration, Preset, Session Config, Ephemeral Profile, Chain, Lane, Quota Ledger,
Rotation State. Defined in `data-model.md`.

## Success Criteria *(mandatory)*

SC-001 to SC-011 are maintained in `requirements.md`. Headline measures:

- SC-001: Launch any supported tool and bind every role to a measured model with a non-empty
  cascade in one command, no manual config edit.
- SC-002: Primary failure recovers via cascade without operator intervention.
- SC-004: With the engine never started, every tool still launches and serves.
- SC-007: Two sessions of one tool with different files route independently through one chain.
- SC-010: Over a week, the interactive lane keeps the primary on S-tier and consumes available
  premium quota substantially before falling to the free floor; standby agents stay on free.
- SC-011: A cascading error across many tools is traceable by one session id or provider.
