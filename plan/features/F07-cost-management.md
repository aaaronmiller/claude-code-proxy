---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, cost, free-paid, budgets, token-economics, value-score]
---

# F07: Cost Management and Free/Paid Constraints

> STATUS v1.1: PARTIAL. Budgets (daily/per-request/cost/mid-stream-output) BUILT; per-slot
> free vs cost_basis eval_mode BUILT; OC Go $/mo blended into fitness. TO BUILD: consumer-plan
> $/M quality-adjusted token-economics report. "(PROPOSED)" tags below superseded by 01-CURRENT-STATE.

Scope: cost as a first-class routing parameter. Every role can be pinned free or paid; an
all-free preset must exist (and a "plan model paid, all auxiliary free" preset for Hermes).
Budgets enforced; consumer-plan token-economics available for picking subscriptions.

## Per-role cost constraint (core user ask)

- Each model role independently constrained free or paid. Optimal "free" preset. Hermes preset:
  main model paid/plan, auxiliary roles all free. (`unified_project_idea_record.md:37-48`; user prompt)
- Task-defined routing pushes simple tool calls to high-quota free models. (`Proxy update
  plan.md:15,45`)

## Budgets

- Budget enforcement daily/hourly/per-request; refuse if projected cost > remaining; cost
  projection formula. (`PRD- MAUG.md:342-347`)
- OC Go $/mo spend monitoring -> switch to free past threshold. (`Hermes Model Rotation...md:317-323`)
- Budget constraint of record: user is budget-limited, free models for testing, OpenRouter key
  is global. (`unified_project_idea_record.md:408-413`) (CURRENT constraint)

## Token-economics engine (consumer-plan ranking)

- Rank all plans/APIs by effective $/M quality-adjusted tokens; AA Intelligence Index v4.0
  anchor (GPT-5.5 xhigh = 60 = 100%). (`Model-scan features.md:4-15`; `Query for best model plan.md:2`)
- Subscription multiplier framework: 5x for $20/$100 tiers, 10x only top unlimited tiers; footgun
  "20x tokens != 20x value". (`Model-scan features.md:17-22`)
- Workload blended ratios: conversational 58/42, tool-call 75/25; reasoning 3x output; cache 80%
  hit. (`:23-33`)
- value_score = intelligence / cost (free excluded). (`PRD- proxy model scraper helper.md:183-186`)
- Cost-intelligence: input/output/cached/retry breakdown per team/project, TCO compare.
  (`Proxy update plan.md:517-522`)

## Hard requirements

- Token cost tracking accuracy +-10%. (`PRD- proxy model scraper helper.md:467-479`)
- Free-vs-paid is a hard constraint per role, enforced before selection (works with F04 gates).

## Two scoring systems (decision shared with F04)

The free-tier fitness engine (F04) and this $/M token-economics engine share inputs but optimize
different objectives. Decide in v2 whether to unify or run both as modes.

## Dependencies

- Reads F03 pricing/value and F06 budgets/quota; constrains F04 selection; surfaces cost in F11
  and F15.

## Open questions

- Is the consumer-plan token-economics ranking a runtime feature or a periodic advisory report?
  Source treats it as a 45-minute analysis with monthly re-run.
