---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, coverage, verification, archive, traceability]
---

# Source Coverage and Archive Manifest

Verification that every one of the 21 source documents in `~/code/ai-gateway` has been read,
its concepts inventoried (with `file:line` pointers in `SCRATCHPAD.md`), and incorporated into
the plan. After this verification the sources are moved to `archive/source-docs/` so the working
tree holds only the forward-looking plan.

Method of record: 7-agent parallel audit of all 21 files -> `SCRATCHPAD.md` (pointer index by
feature module) -> feature files F01-F18 -> reconciled against live code in
`01-CURRENT-STATE-AND-GAPS.md`.

## Coverage table (all 21, every one INCORPORATED)

| # | Source file | Incorporated into | Status |
|---|-------------|-------------------|--------|
| 1 | unified_project_idea_record.md | F02, F07, F12, F13, F14, F15, F16 + Master vision; SCRATCHPAD "DISTILLED VISION" | INCORPORATED |
| 2 | PRD- MAUG.md | F01-F12 (5-layer arch, canonical schema, key ledger, quota discriminator, ORMS, MCP, host sentinel); naming (MAUG) noted | INCORPORATED |
| 3 | Proxy update plan.md | F01, F03, F04, F05, F08, F09, F11 (translation, ORMS, routing, fallback, compression, memory, OTel); build-vs-buy taxonomy | INCORPORATED |
| 4 | Hermes Model Rotation & Reliability Specification.md | F05 (triggers, demotion/promotion, circuit breaker, reliability.db), F03 (baseline), F06 (budgets) | INCORPORATED + superseded by model-scan engine (01-CURRENT 3) |
| 5 | HERMES_REFINEMENT_SPECIFICATION.md | F05 (7-trigger, thresholds, recommendations.json apply), F12 (config gen), F03 (composite baseline) | INCORPORATED + superseded by model-scan engine |
| 6 | Claude Code Backend Middleware - Project Assessment.md | F01 (tool primitives, Anthropic changelog), F02 (3-layer, ccproxy ref), F10 (agent teams ref) | INCORPORATED (reference) |
| 7 | claude cody proxy .env.md | F01, F04, F06, F09, F10, F11, F12, F16 (current config surface); superseded by specs/001 reality | INCORPORATED (current baseline; L1-557 ghostty transcript = irrelevant, dropped) |
| 8 | Terminal Color System.md | F16 (TUIDS-LLM color/motion/status, content sanctity, accessibility) | INCORPORATED |
| 9 | MODEL_ARCHITECTURE.md | F03 (providers, 5-tier, -claw, rejected models), F04 (role->tier), F05 (fallback chains) | INCORPORATED + superseded by model-scan engine |
| 10 | Ordered Compositor Design Validation (...).md | F13 (cc RMSCO grammar, auto-route, port topology); flagged proposed-only | INCORPORATED |
| 11 | Clutch-Gateway-Quota-Monitoring-Technical-Spec.md | F06 (11-provider adapters, quota meters, key rotation), F11 (Prometheus), F15 (Grafana) | INCORPORATED (drives F06 + F18 meters) |
| 12 | PRD- proxy model scraper helper.md | F03 (ORMS daemon, data schema, leaderboards, success criteria) | INCORPORATED + ORMS exists in code (model-scan) |
| 13 | AAA model-scan algorithm construction.md | F03 (multi-axis scoring), F04, F07 (cost axis) | INCORPORATED + superseded by model-scan calibration |
| 14 | Structural Assessment of the Hermes Model Selection System.md | F03 (tiers.yaml floor, blocklist), F04 (fitness, eligibility gates), F06 (time windows), F11 (failure ingestion) | INCORPORATED |
| 15 | Hermes Optimal Model Settings - Audit Report.md | F05 (broken-fallback fix), F03/F04 (role-model validation), F07 (cost) | INCORPORATED |
| 16 | Optimal compression for hermes agent.md | F08 (Headroom/RTK/hermes-lcm/pi-prune, cache strategy, Kompressor correction) | INCORPORATED |
| 17 | How to use context compression tools and provider prompt caching correctly.md | F08 (subset-duplicate of #16; canonical merged) | INCORPORATED (dedup) |
| 18 | Model-scan features.md | F07 ($/M token-economics ranking, subscription multipliers, workload ratios) | INCORPORATED |
| 19 | Query for best model plan.md | F07 (prompt form of #18; dedup pair) | INCORPORATED (dedup) |
| 20 | new proxy commands.md | F04 (routing profiles), F02 (route prefixes), F12 (namespaced providers) | INCORPORATED + matches specs/002 |
| 21 | web browser plugin - multi model question distributor and aggregator.md | F17 (browser fan-out/aggregator) | INCORPORATED |

## Cross-checks

- Every audit CATEGORY maps to a module: see Master Plan section 8 coverage matrix (+ F18 for the
  new quota-optimization category).
- Contradictions across the multi-draft docs (LiteLLM, scoring baseline, rotation triggers, ports)
  are resolved in `01-CURRENT-STATE-AND-GAPS.md` and `SCRATCHPAD.md` final section.
- Live-code reconciliation (specs 000-003 + model-scan + headroom + wiki-memory) is in
  `01-CURRENT-STATE-AND-GAPS.md`. The brainstorming docs are superseded by code where they
  disagree; this is noted per-row above.
- Nothing deferred without approval. Only pre-approved future item: Web UX out of browser (F15).

## Archive action

The 21 files above are moved to `~/code/ai-gateway/archive/source-docs/` (verbatim, reversible).
Their content is fully captured by SCRATCHPAD.md pointers, so they remain retrievable via the
`file:line` references if exact original text is needed. Working tree going forward = `plan/`.
