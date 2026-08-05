---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, rotation, reliability, fallback, circuit-breaker, reliability-db]
---

# F05: Rotation, Reliability and Fallback

> STATUS v1.1: BUILT. `circuit_breaker.py` full CLOSED/OPEN/HALF-OPEN FSM + disk persistence;
> `client.py` cascade, OpenRouter native fallback, cross-provider, mid-stream tier override, error
> classification; model-scan reliability_feedback + bad_models. GAP: client-config rotation
> (recommendations.json + human-gated apply) for generated Hermes configs. "(PROPOSED)" tags below
> are superseded by 01-CURRENT-STATE.

Scope: keep selections healthy over time. Track per-model reliability, rotate models on
triggers, demote/promote based on measured behavior, break circuits on failing providers, and
cascade fallbacks so a request still completes when a provider fails.

## Reliability tracking

- SQLite reliability.db at ~/.hermes/ : model_calls + model_health tables, 90-day retention,
  JSONL fallback, 15-minute materialized health views, 8+ fields per call. (`HERMES_REFINEMENT_
  SPECIFICATION.md:155-213`)
- Minimum sample sizes gate every action: 30/50/100/200 calls depending on metric.
  (`Hermes Model Rotation & Reliability Specification.md:232-241`)
- Historical failures also ingested from agent.log + proxy logs nightly into
  historical_failures.json and fed back to F04 scoring. (`Structural Assessment...md:92-98`)

## Rotation, demotion, promotion

- Rotation triggers (DECISION: HERMES_REFINEMENT 7-type calendar/new-model/error/latency/
  availability/quality/credit, priority ordered, vs Hermes-Rotation 5-type). (`HERMES_REFINEMENT_
  SPECIFICATION.md:26-39`; `Hermes Model Rotation...md:116-125`)
- Demote on >5% err over 7d with n>=50 or p95 latency breach; promote needs <1-2% err with
  n>=100; 3 demotions in 7d -> boneyard. (`HERMES_REFINEMENT_SPECIFICATION.md:41-69`)
- Pre-insertion test protocol (MUST PASS ALL): curl + tool-call + baseline + speed + diversity;
  reject if below gpt-oss-120b composite. (`:82-152`)

## Circuit breaker and fallback

- Circuit breaker CLOSED/OPEN/HALF-OPEN, trip at 5 fails/10min, cooldown 10 -> 120min exp
  backoff, per provider-model pair. (`HERMES_REFINEMENT_SPECIFICATION.md:324-385`)
- Note: LiteLLM allowed_fails is a failure-budget, not a true half-open breaker; needs a custom
  wrapper. (`PRD- MAUG.md:1827,1914-1920`)
- 5-stage fallback cascade: retry/backoff -> strip fields -> reduce tools -> next provider ->
  degrade text-only. (`PRD- MAUG.md:256-262,1405-1421`)
- Per-role fallback chains 3-4 deep (same-model-diff-provider as F1, end on the 15-entry global
  main). (`MODEL_ARCHITECTURE.md:481-611`) (CURRENT)
- Provider-wide fast-skip on 429/503; malformed tool_call skip. (`Hermes Model Rotation...md:283-288`)
- Emergency override: `hermes config emergency-mode` sets all roles to gpt-oss-120b.
  (`HERMES_REFINEMENT_SPECIFICATION.md:1096-1151`)

## Known current bug to fix

- hermes-3-405b:free returns provider errors as a fallback; replace with nemotron-3-super.
  (`Hermes Optimal Model Settings - Audit Report.md:51-59`) (CURRENT bug)

## Hard requirements

- No promotion at n<100. (`HERMES_REFINEMENT_SPECIFICATION.md:68`)
- Rotation feeds recommendations.json; config.yaml is NEVER auto-mutated (human-gated apply,
  see F12). (`:237-269`)

## Dependencies

- Uses F03 eligibility/tiers and F06 quota signals; dispatches via LiteLLM Router (Invoke);
  writes telemetry to F11; produces recommendations consumed by F12.

## Open questions

- 7-type vs 5-type trigger set; reconcile circuit-breaker thresholds across the two specs.
