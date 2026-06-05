# Implementation Plan: Model-Scan Integration

**Branch**: `003-model-scan-integration` | **Date**: 2026-05-30 | **Spec**: `./spec.md`
**Input**: Feature specification from `specs/003-model-scan-integration/spec.md`

## Summary

Connect the diagnostic engine (model-scan) to the router (claude-code-proxy) through a single
versioned `routing_snapshot.json` contract. The router binds each tier and role to a measured
model and a live cascade under a selection policy, degrades to static config when the snapshot
is absent, and never depends on the engine at request time. Layered on top: session-scoped
ephemeral profiles (preset, file, and argument composition), consumption lanes (free standby vs
quota-aware S-tier interactive rotation built on the existing `rate_limiter` / `usage_tracker` /
`billing_integrations` substrate, fed by a pluggable QuotaSource adapter with tokscale primary
and ccusage secondary), a one-command visible chain bring-up, and a unified error sink keyed by
session correlation id. Full technical detail is in `design.md`.

## Technical Context

**Language/Version**: Python 3.12 (router, existing); Python 3.12 (model-scan, existing)
**Primary Dependencies**: FastAPI + Uvicorn (existing); jsonschema (new, schema validation);
tokscale and ccusage as external quota data sources (optional, behind adapters)
**Storage**: `proxy_chain.json`, `profiles.json` (existing config); `routing_snapshot.json`
(new shared artifact); SQLite via existing `usage_tracker`; tokscale local SQLite (read-only)
**Testing**: pytest (router); existing model-scan harness
**Target Platform**: Local processes on the worker (router 8082, compression 8787, upstream
proxy 8317, diagnostic gateway 8124)
**Project Type**: Single project (service + CLI launcher); two complementary repos, contract-only
coupling
**Performance Goals**: No synchronous file or network read on the request path attributable to
this feature; rebind atomic and non-disruptive to in-flight requests; a dozen concurrent clients
**Constraints**: Router never hard-depends on the engine; snapshot carries no credentials;
credential loading order unchanged; with the feature disabled, behavior identical to baseline
**Scale/Scope**: Up to a dozen concurrent tools through one chain; fifteen roles; ten-plus
providers

## Constitution Check

*GATE: must pass before research and after design. Enumerates every `### ` principle heading in
`.specify/memory/constitution.md` v1.0.0 (six core principles + three engineering constraints).*

Core principles:

- **I. Existing Research Before Building** (NON-NEGOTIABLE): PASS. Prior art surveyed (Claude Code
  Router, Portkey, LiteLLM, RouteLLM, Not Diamond, Unify, tokscale, ccusage, gpt-load) with an
  explicit gap statement; see `research.md` and `requirements.md` section 8.
- **II. Synthesis Verification**: PASS. Comparison claims in `research.md` grounded in source
  review; the consequential claims (tokscale schema, absence of a key pool) are confirmed by the
  two front-loaded spikes (T050, T055) rather than asserted.
- **III. Safe Destructive Operations** (NON-NEGOTIABLE): PASS. The feature performs no `rm -rf`,
  force-push, or `reset --hard`. Snapshot and assignment writes use atomic temp-file-plus-rename
  (T011, T023). Alias installation (T046) is additive and preserves existing aliases. Ephemeral
  profile teardown (T040) is in-memory only. No destructive shell op enters the request or build
  path.
- **IV. Changelog Discipline**: PASS. T086 updates `CHANGELOG.md` `[Unreleased]` and `docs/` for
  the launcher, policies, lanes, and the model-scan contract.
- **V. Progressive Disclosure**: PASS. The project `CLAUDE.md` stays under 300 lines (185); the
  constitution is referenced with its principle names inlined plus a re-read trigger, deep spec
  artifacts live under `specs/003-model-scan-integration/` by pointer; no auto-generated context
  files are committed.
- **VI. Single Source of Truth for Configuration**: PASS (the principle this feature most
  implicates). All new fields (`model_scan.*` in `config/proxy_chain.json`, profile
  `slot_bindings`, lanes) resolve through the existing resolver and the `AssignmentRegistry`
  (T023, T025, T030, T031). No feature code reads values via direct `os.environ.get` or mutates
  JSON outside the resolver; request-time overlay lookup performs no file IO (T031). Legacy names,
  if any, alias with a deprecation warning.

Engineering constraints:

- **Stable Public API**: PASS. Anthropic Messages and OpenAI Chat Completions surfaces are
  unchanged; all new endpoints (`/routing-snapshot`, `/api/proxy/reload-models`,
  `/api/routing-profiles`) are additive and gated by `model_scan.enabled` (default off, policy
  static). NFR-030 asserts byte-for-byte baseline behavior when disabled (T085).
- **No Secrets in Git-Tracked Files**: PASS. The snapshot carries no credentials; `${VAR}`
  references and credential loading order are untouched (NFR-020, NFR-021).
- **Deprecation Over Hard-Cut**: N/A. No existing capability is removed; the feature is purely
  additive and gated. Should any field be renamed during implementation, an aliased deprecation
  warning is required.

Re-check after design: no new violations introduced. The ephemeral-profile API and the
QuotaSource adapter are additive and gated by `model_scan.enabled`. The one notable complexity
(session-scoped ephemeral profiles) is recorded in Complexity Tracking below, not a principle
violation.

## Project Structure

### Documentation (this feature)

```text
specs/003-model-scan-integration/
├── spec.md              # feature spec (user stories, requirements pointer)
├── plan.md              # this file
├── research.md          # decisions and rationale (Phase 0)
├── data-model.md        # entities and state (Phase 1)
├── quickstart.md        # end-to-end run (Phase 1)
├── contracts/
│   ├── routing_snapshot.schema.json
│   └── session_config.schema.json
├── requirements.md      # full FR/NFR with acceptance (source input)
├── design.md            # full technical design (source input)
└── tasks.md             # task list (Phase 2, /speckit.tasks)
```

### Source Code (repository root)

```text
claude-code-proxy/
├── src/
│   ├── services/models/model_scan_snapshot.py   # loader, validation, in-memory model (new)
│   ├── core/
│   │   ├── model_scan_binder.py                  # SelectionPolicy + binder + lanes (new)
│   │   ├── rotation.py                           # quota ledger + rotation engine (new)
│   │   ├── profiles.py                           # + slot_bindings, ephemeral profiles
│   │   └── assignments.py                        # write target (existing)
│   ├── services/usage/                           # rate_limiter, usage_tracker (existing, reused)
│   ├── services/billing/                         # billing_integrations (existing, reused)
│   └── api/
│       ├── endpoints.py                          # + overlay binding
│       └── routing_profiles_api.py               # + ephemeral register/deregister
├── config/proxy_chain.json                       # + model_scan section, chain entries
├── profiles/profiles.json                        # + slot_bindings, presets, lanes
└── scripts/
    ├── ccp-launch.sh                             # unified launcher + ccp up (new)
    └── install-aliases.sh                        # + presets, ante, antigravity

model-scan/   (separate project, contract-only)
├── gold_standard.py        # + emit_snapshot projector
├── slot_definitions.yaml   # + 5 aux slots (role-needs analysis)
├── cron_manager.py         # + emit after scan, ingest external quota
└── gateway.py              # + GET /routing-snapshot, POST /reliability
```

## Phasing

Phases 0 through 7 are defined in `design.md` section 9 and drive `tasks.md`:

0. Shared contract. 1. Snapshot production and role coverage (model-scan). 2. Snapshot
consumption and binding (router). 3. Profile role bindings. 4. Launcher, sessions, chain
lifecycle. 5. Lanes, quota ledger, rotation. 6. Observability and the chain monitor. 7.
Reliability feedback loop.

Two spikes are front-loaded for de-risking: the tokscale SQLite schema, and the per-provider
key-pool (confirmed absent today, so it is new work).

## Complexity Tracking

No constitution violations require justification. The one notable complexity, session-scoped
ephemeral profiles, is justified by US3 (two sessions of one tool with different configs), which
the existing profile-scoped model cannot satisfy.
