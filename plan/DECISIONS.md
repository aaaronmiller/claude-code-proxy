---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, decisions, sign-off, register]
---

# Decisions Register

One place to see what is settled and what needs your sign-off. RESOLVED items are baked into the
plan with rationale. OPEN items have a recommendation, the impact, and what they block, so you can
approve in one pass.

## RESOLVED (baked in; rationale in 01-CURRENT-STATE)

| # | Decision | Rationale |
|---|----------|-----------|
| R1 | LiteLLM: build our own, do not adopt | No litellm in code; specs/000 rejects it; the in-house converter is the asset; nothing it does is undup-able for this use |
| R2 | Extend `claude-code-proxy`, not greenfield | It already holds translation, routing, config-parity, circuit breaker, model-scan, web-ui; all current features preserved |
| R3 | Model-scan: fold in as a module, keep snapshot producer/consumer boundary | Sophisticated engine (~3600L); scoring must never run on the hot path (specs/003 NFR) |
| R4 | Scoring = model-scan's real 4-axis + slot-fitness engine | Supersedes the conflicting brainstorming formulas (gpt-oss "any-one-of" vs 30.2 are dead) |
| R5 | Config + interface parity = specs/001, extend via config_manifest | Already complete (84/84); single resolver, 4-surface parity, CI-enforced |
| R6 | Compression: Headroom + RTK always-on; Kompressor = Headroom's weight compression (real); context engine optional; never stack lcm+pi-prune | Cache-transparent layers; losslessness constraint |
| R7 | Memory backend = wiki-memory, in-process `import mem` | Its MCP is spec'd but disabled; JSON store is source of truth |
| R8 | Allocator objective = satisfice-then-maximize, user-defined per-role floor + value-sensitivity | Not all sessions need optimal; preserves scarce smart capacity for roles that benefit |

## OPEN (need your sign-off)

| # | Decision | Recommendation | Impact | Blocks |
|---|----------|----------------|--------|--------|
| O1 | Project name | Keep "Clutch" | Branding only | nothing |
| O2 | Repo strategy | Monorepo (model-scan/headroom/wiki-memory as packages, preserve process boundaries) | How the three repos are vendored | S1-05 |
| O3 | Launch UX | Keep minimal `proxies` + 3 aliases; add `cc` only if you want it (then 3-slot) | F13 scope | F13 only |
| O4 | Allocator online mode | Token-bucket + Thompson bandit + periodic LP | F18 complexity (dry-run unaffected) | S1-07 refinement |
| O5 | Memory persistence policy | Explicit "remember" always + opt-in per session/role; not auto-store-everything | F09 store hook | F09 store path |
| O6 | Rotation governance | model-scan reliability loop as engine; Hermes human-gated `apply` only for generated client config | F05/F12 scope | client-config generation |
| O7 | Importance weights source | Per-profile table (overridable at launch) | F18 preemption input | preemption tuning |
| O8 | Allocator default at launch | Off by default until validated (baseline preserved); enable per session-type when proven | rollout safety | nothing (gated) |

## Notes
- None of O1-O8 block the decision-independent sprint-1 recon (S1-01 run tests, S1-03 hardcoded-
  model audit, S1-04 dead-model test). Those can start now.
- O2 is the only one that meaningfully shapes early structure (where vendored code lives).
- Approve, override, or annotate any row; I will fold approvals into the plan and unblock the
  dependent tickets.
