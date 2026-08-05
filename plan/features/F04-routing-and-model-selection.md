---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, routing, model-selection, classifier, roles, fitness, profiles]
---

# F04: Routing and Model Selection Engine

> STATUS v1.1: BUILT. `model_router.py` precedence (passthrough > assignment > custom py/js router
> > tier) + slot detectors; snapshot policies static/free/budget/quality/roles/rotate (specs/003).
> value(m,role) = model-scan engine (01-CURRENT 3). F18 re-ranks per-fleet under quota.
> "(PROPOSED)" tags below are superseded by 01-CURRENT-STATE.

Scope: decide which model handles each request. Classify intent, resolve the role's
constraints, score eligible models, pick the best. No hardcoded model names anywhere.

## Pipeline

Classifier -> Role-Constraint Resolver -> Key Ledger check (F06) -> dispatch (via LiteLLM Router
in F05). (`PRD- MAUG.md:240-264`)

- Intent classifier, 4 dimensions: complexity, task type, vision need, tool need. Rule-based v1,
  optional ONNX later. Claimed ~80% routing optimization. (`PRD- MAUG.md:250-255`; `Proxy update
  plan.md:478-489`)
- Role-constraint resolver reads YAML hard/soft constraints with overrides. Example: free +
  tool_calling + dense>30B or MoE>60B@8B. Arbitrary user trait tags ("good thinkers").
  (`PRD- MAUG.md:265-287`; `Proxy update plan.md:45-47`)
- Slot eligibility hard gates applied before scoring: min_tier, needs_tools, needs_vision,
  min_ctx, max_latency. Architecture gates are never softly penalized. (`Structural Assessment of
  the Hermes Model Selection System.md:67,140`)
- Fitness score: tier-anchor * AA-multiplier * reliability * latency-consistency *
  hourly-availability + architecture bonus, weights in tiers.yaml. (`:75`)
- Recommendation logic: rank eligible, show delta-vs-incumbent, swap only if +5 fitness. (`:77`)

## Role model

- 14 Hermes roles mapped to tiers, each with rationale. (`MODEL_ARCHITECTURE.md:415-478`) (CURRENT)
- Per-CLI Routing Profiles (profiles.json) with provider_override, toolcall_models, use-case
  routers (for example web-search -> nemotron-nano). (`new proxy commands.md:40-49`) (CURRENT)
- Tier model map BIG/MIDDLE/SMALL (opus/sonnet/haiku -> mapped models). (`claude cody proxy
  .env.md:608-627`) (CURRENT)
- Task-based substitutions toggleable (tool calls, large ctx); new roles addable without
  middleware code. (`unified_project_idea_record.md:64-89`)

## Hard requirements

- No hardcoded model-name routing rules. (`unified_project_idea_record.md:46,468`)
- Each role independently constrained free or paid (cost dimension owned by F07).
- Selection respects the static tiers.yaml floor from F03; never pick below-floor.

## Two scoring systems (decision needed)

Free-tier fitness (this module) vs consumer-plan $/M token-economics (F07) were never unified in
the source. They share inputs but differ in objective. v2 decision: one engine with a mode flag,
or two cooperating engines.

## Dependencies

- Consumes F03 registry/scores and tiers.yaml; hands the chosen model to F05 for dispatch and
  fallback; reads quota/key health from F06; emits routing_decision to F11.

## Open questions

- gpt-oss-120b baseline: any-one-of definition vs composite-30.2 formula.
- Classifier v1 rule set: confirm task taxonomy and thresholds.
