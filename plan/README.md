# AI Gateway (MAUG / Clutch) - Master Plan v1

Greenfield rebuild of /code/claude-code-proxy, unifying 21 source docs into one plan.

## Read in this order

1. `00-MASTER-PLAN.md` - vision, layered architecture, module map, cross-cutting hard
   requirements, build-vs-buy, delivery phases, coverage matrix, open decisions.
2. `01-CURRENT-STATE-AND-GAPS.md` - what the live repos already do vs gaps; resolved decisions
   (LiteLLM, model-scan, config parity); the real model-scan scoring engine; ranked user intent.
   OVERRIDES any "(PROPOSED)" tag in the feature files where the thing already exists.
3. `02-SOURCE-COVERAGE-AND-ARCHIVE.md` - verification that all 21 source docs are incorporated.
4. `03-IMPLEMENTATION-ROADMAP.md` - dependency-ordered workstreams W0-W12 + sprint-1 tasks.
5. `04-DATA-CONTRACTS.md` - codeable schemas for the new core (F06 quota meters, F18 allocator
   LP/inputs/outputs), aligned additively to routing_snapshot.json and specs/001 Assignment.
6. `05-CONFIG-SCHEMA.md` - additive config extension over specs/001 proxy_chain.json (roles/
   profiles, quota, allocator, memory, compression), with parity + migration rules.
7. `06-SPRINT-1-TICKETS.md` - concrete starting tickets (real claude-code-proxy files, steps,
   runnable acceptance tests) for roadmap W0/W1/W4/W5.
8. `SCRATCHPAD.md` - pointer index: every concept mapped to a module with `file:line`
   pointers back to verbatim source text (now in archive/source-docs/), plus contradictions.
9. `features/F01..F18` - one file per feature module (scope, concepts + pointers,
   current-vs-proposed, hard requirements, dependencies, open questions). Each carries a
   STATUS v1.1 banner reflecting current-code reality.

## Modules

- F01 Proxy Core and Translation
- F02 Proxy Chain Orchestrator
- F03 Provider+Model Registry and Scanning (ORMS)
- F04 Routing and Model Selection
- F05 Rotation, Reliability and Fallback
- F06 Quota, Key and Subscription Management
- F07 Cost Management
- F08 Compression and Caching
- F09 Memory Integration and Hooks Emulation
- F10 Multi-Session Orchestration and Host Sentinel
- F11 Observability, Metrics and Logging
- F12 Configuration and Interface Parity
- F13 CLI and Launch Aliases (Ordered Compositor)
- F14 TUI Wizard
- F15 Web UX and Dashboard
- F16 Terminal Color and Status System
- F17 Web Browser Multi-Model Aggregator
- F18 Capacity Planner / Quota-Aware Global Allocator (the optimization core)

## Status

Implementation-ready. Plan reconciled against the live repos (claude-code-proxy, model-scan,
input-compression, wiki-memory). Sources archived in `archive/source-docs/` and verified
incorporated (`02-SOURCE-COVERAGE-AND-ARCHIVE.md`).

Sign-off needed: see `DECISIONS.md` (8 resolved + 8 open, each with a recommendation). Only the
open decisions gate the larger pieces; the decision-independent sprint-1 recon can start now.
No feature deferred without approval; only pre-approved future item = Web UX out of browser (F15).
