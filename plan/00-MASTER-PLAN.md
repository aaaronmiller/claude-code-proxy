---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, maug, clutch, master-plan, architecture, greenfield, roadmap]
---

# AI Gateway: Master Plan (v1)

Greenfield rebuild that unifies 21 design docs into one coherent system. This is the
top-level plan. Each feature module has its own file in `plan/features/`. The pointer
index in `plan/SCRATCHPAD.md` traces every concept back to verbatim source text.

Status: v1.1. IMPORTANT REFRAME (see `01-CURRENT-STATE-AND-GAPS.md`): after reading the live
repos, this is a PIVOT and extension of a mature working system (`claude-code-proxy`, branded
"Clutch Gateway"), not a build-from-zero. Most core modules already exist (translation, routing,
chain, config-parity, circuit breaker, model-scan, web-ui). Read `01-CURRENT-STATE-AND-GAPS.md`
for the built-vs-gap map; it overrides any "(PROPOSED)" tag in the feature files where the thing
already exists. The only pre-approved future item is "take the Web UX out of the browser".

---

## 1. What this is

One process that sits between any agent/CLI harness (Claude Code, Codex, OpenCode, Qwen
Code, Hermes Agent, OpenClaw, Factory Droid, Pi, and future tools) and any model provider
(OpenRouter, OpenCode Zen/Go, Ollama Cloud, NVIDIA NIM, Groq, Cerebras, Anthropic OAuth,
Antigravity/Vertex, and more). It:

- translates request/response/tool-call formats bidirectionally so any harness can talk to
  any provider (use an OpenRouter model from Claude Code; route all tool calls to a free model),
- tracks every subscription, API key, usage quota, and provider availability,
- scans and benchmarks available models (models.dev + Artificial Analysis + PinchBench +
  llm-stats) and correlates that with live latency, tokens/s, and historical failures,
- selects optimal models per role under cost constraints (each role can be pinned free or paid),
- generates and live-updates client config files (for example Hermes `config.yaml`), rotating
  to the next-best model as a role approaches its quota,
- runs an arrangeable proxy chain (compression, OAuth, translation) in any order,
- orchestrates multiple concurrent sessions without resource conflict,
- and exposes all of it through three interfaces with full feature parity: CLI/.env, a TUI
  wizard, and a Web UX with a live dashboard plus Prometheus and Grafana.

Working name: MAUG (Model-Agnostic Unified Gateway), also called Clutch. The current
implementation lives at `/code/claude-code-proxy`; this plan rebuilds it greenfield.

## 2. Naming and current baseline

- The same system is referred to in the docs as MAUG, Clutch, and "Claude Code Proxy". Treat
  them as one. This plan uses MAUG for the gateway, Clutch for the quota subsystem heritage.
- Hermes = a routed client CLI whose `config.yaml` MAUG generates; not part of MAUG itself.
- Antigravity = a Google VSC harness reached via OAuth through VibeProxy/CLIProxyAPI.

Current system (verified from `claude cody proxy .env.md:558-991` and `new proxy commands.md`):
Python, `src/` layout, port 8082, Anthropic Messages API in -> OpenAI/Gemini out, SQLite usage
DB, tier model map (BIG/MIDDLE/SMALL), per-tier endpoint overrides, per-model reasoning and
prompt overrides, custom headers, terminal color/metrics output, crosstalk, and a recently
merged per-CLI Routing Profiles system (`profiles.json` + `provider_override` + use-case
routers + REST API). Every current capability is mapped into a feature module below and must
survive the rebuild (hard requirement from the user: at minimum, all current features present).

## 3. Target architecture (layered)

Authoritative layering from PRD-MAUG v3.1 (`PRD- MAUG.md:41-125`), extended with the user's
proxy-chain and three-interface requirements:

```
            +-------------------------------------------------------------+
 Interfaces |  CLI / .env (base)   |   TUI wizard   |   Web UX + dashboard |   F12 F13 F14 F15 F16
            +-------------------------------------------------------------+
                                   | single config source of truth (parity)
            +-------------------------------------------------------------+
 Control    |  Control MCP server  |  hooks emulation  |  memory injection |   F09
            +-------------------------------------------------------------+
 Chain      |  Proxy Chain Orchestrator: [Headroom -> RTK -> CLIProxyAPI -> MAUG] (any order) |  F02 F08
            +-------------------------------------------------------------+
 Intelligence | intent classifier | role-constraint resolver | fitness scoring | rotation |  F04 F05
            +-------------------------------------------------------------+
 Translation | canonical schema (OpenAI tools, JSON-Schema 2020-12) <-> per-provider adapters |  F01
            +-------------------------------------------------------------+
 Transport  | wire-format endpoints in (OpenAI/Anthropic/Gemini/Bedrock) ; dispatch out      |  F01
            +-------------------------------------------------------------+
 Data       | provider+model registry | ORMS scanner | key ledger | quota | reliability.db   |  F03 F06 F05
            +-------------------------------------------------------------+
 Cross-cut  | Observability (JSONL + OTel + Prometheus) | Host Sentinel | Cost engine        |  F11 F10 F07
            +-------------------------------------------------------------+
```

Process topology (PRD-MAUG:792-803): single-process asyncio gateway + sidecars
(LiteLLM container, ORMS, Headroom, RTK, Redis, CLIProxyAPI, TUI), each independently
restartable. Concurrency is for many harnesses/sessions, not many users.

## 4. Module map

Each links to its feature file. Full concept lists with source pointers live there and in
SCRATCHPAD.md.

| ID | Module | One-line scope |
|----|--------|----------------|
| F01 | Proxy Core and Translation | provider/model/harness-agnostic bidirectional translation via canonical schema, streaming tool-call reassembly, ID mapping |
| F02 | Proxy Chain Orchestrator | arrangeable any-order chain (Headroom/RTK/CLIProxyAPI/MAUG), validation, run with/without |
| F03 | Provider+Model Registry and Scanning (ORMS) | capability registry, model discovery, models.dev/AA/PinchBench/llm-stats scrape, leaderboards, tiers.yaml floor, scoring axes |
| F04 | Routing and Model Selection | intent classifier, role-constraint resolver, fitness scoring, profiles, no hardcoded model rules |
| F05 | Rotation, Reliability and Fallback | rotation triggers, demotion/promotion, circuit breaker, 5-stage fallback cascade, reliability.db |
| F06 | Quota, Key and Subscription Mgmt | 11-provider quota adapters, key ledger, quota discriminator, budget ceilings, rotation logic |
| F07 | Cost Management | per-role free/paid constraint, budgets, token-economics ($/M quality-adjusted), value scoring |
| F08 | Compression and Caching | Headroom + RTK + hermes-lcm, request-path ordering, cache-aware strategy, cross-model cache caveats |
| F09 | Memory Integration and Hooks Emulation | wiki-memory content injection/storage hooks, hook emulation for non-hook CLIs, Control MCP |
| F10 | Multi-Session Orchestration and Host Sentinel | concurrent harness serving, resource arbitration, global rate limiter, workers.yaml |
| F11 | Observability, Metrics and Logging | structured JSONL, OpenTelemetry, Prometheus, failure ingestion feeding selection |
| F12 | Configuration and Interface Parity | single config source, dynamic client-config generation (Hermes config.yaml), schema validation, human-gated apply |
| F13 | CLI and Launch Aliases | maug CLI, Ordered Compositor `cc` grammar, installer/bootstrap |
| F14 | TUI Wizard | Textual TUI, status-bar builder, full config parity |
| F15 | Web UX and Dashboard | live fail dashboard, Prometheus + Grafana, drag-drop chain reorder, (future: standalone) |
| F16 | Terminal Color and Status System | TUIDS-LLM color scheme, status bars, statusline injection, content sanctity |
| F17 | Web Browser Multi-Model Aggregator | browser fan-out to LLM web UIs + aggregator synthesis (lowest maturity, in-scope) |
| F18 | Capacity Planner / Quota-Aware Global Allocator | THE optimization core: satisfice-then-maximize allocation of finite multi-dimensional quota across all concurrent sessions (LP + bandit), session profiles, live preemption, weekly utilization/regret audit |

## 5. Cross-cutting hard requirements (must hold across all modules)

From `unified_project_idea_record.md` and PRD-MAUG, these are non-negotiable:

1. No hardcoded model-name routing rules. New models/CLIs route via config, not code edits.
   (`unified_project_idea_record.md:46,468`)
2. Full feature parity across .env/CLI, TUI, and Web UX. CLI/.env is the base layer the other
   two wrap. Any setting configurable in one is configurable in all. (`:199-242,441-465`)
3. Each model role independently constrained free or paid; an all-free preset must exist.
   (`:37-48`; user prompt)
4. Proxy chain adjustable to any count and any order; system runs with or without it. (`:9-35`)
5. Secrets from env at runtime only, never persisted to disk; preserve existing credential
   loading order and never modify ANTHROPIC_API_KEY=pass / x-api-key:pass. (`PRD- MAUG.md:1129,1737`)
6. LiteLLM is used as a Docker container only (never pip-imported into the gateway), per the
   March 2026 supply-chain compromise. (`PRD- MAUG.md:234-238`)
7. Config changes that affect a client (for example Hermes config.yaml) are written via a
   human-gated apply step, never auto-mutated, with .bak retention and schema validation.
   (`HERMES_REFINEMENT_SPECIFICATION.md:237-269`)
8. Lossless round-trip translation: unknown provider fields preserved, tool-call IDs mapped per
   turn. (`Proxy update plan.md:169,404`)
9. All current-system features (Section 2) are reimplemented. Nothing dropped silently.

## 6. Build-vs-buy strategy

Taxonomy (PRD-MAUG:30-39): Embed (use as library), Invoke (run as sidecar, call over
HTTP/MCP), Build (write ourselves), Fork (copy and modify). Glue-architecture principle:
orchestrate a small number of strong external projects rather than reimplement them
(`Proxy update plan.md:2454-2468`).

| Component | Decision | Note |
|-----------|----------|------|
| LiteLLM | Drop (build our own) | RESOLVED: current code uses none; specs/000 rejects it; the in-house converter is the asset. See 01-CURRENT-STATE 1.1 |
| Headroom | Invoke (chain stage, port 8787) | input/prompt compression, already in user stack |
| RTK | Invoke (chain stage) | shell/output compression via CLI hooks |
| hermes-lcm | Embed or Invoke | context engine; do not stack with pi-context-prune |
| CLIProxyAPI | Invoke (sidecar, opt-in) | OAuth for Antigravity/Anthropic |
| ORMS / model-scan | Fold in (extend) | EXISTS at /home/cheta/code/model-scan (dink.py + scoring engine); not build-from-scratch. Vendor into repo, keep snapshot boundary |
| wiki-memory | Invoke (hooks) | user's bespoke memory at /code/wiki-memory |
| Translation, routing, quota, registry | Build | the core differentiators |
| resillm | drop | no library; replaced by LiteLLM Router |

## 7. Delivery phases (notation: phases, not weeks)

> Note: this section is the conceptual grouping, written before the code recon. For the
> reconciled, dependency-ordered BUILD sequence (which accounts for what already exists), use
> `03-IMPLEMENTATION-ROADMAP.md` (W0-W12) and `06-SPRINT-1-TICKETS.md`. Where the two differ
> (e.g. ORMS and circuit breaker are listed as Phase C work below but already exist), the roadmap
> wins.

Phase A - Foundation: transport endpoints + canonical schema + bidirectional translation for
the 4 wire formats + streaming tool-call reassembly + provider/model registry + .env/CLI base.
Target: 100% tool-call parity, 0 format drops. (carries current system forward)

Phase B - Control and routing: intent classifier + role-constraint resolver + Routing Profiles
+ key ledger + quota discriminator + proxy chain orchestrator + Control MCP.

Phase C - Intelligence and reliability: ORMS scanner + scoring/fitness + tiers.yaml floor +
rotation/demotion/promotion + circuit breaker + reliability.db + dynamic config generation for
Hermes with human-gated apply.

Phase D - Extension and observability: compression chain (Headroom/RTK/hermes-lcm) + memory
injection/hooks emulation + multi-session orchestration + Host Sentinel + full observability
(JSONL/OTel/Prometheus/Grafana) + cost engine + token-economics.

Phase E - Interfaces and hardening: TUI wizard + Web UX dashboard + Terminal Color system +
Ordered Compositor `cc` + installer + capability-boundary enforcement + security hardening.

Phase F (pre-approved future, not now): take Web UX out of the browser into a standalone app.
F17 (browser aggregator) is in-scope but lowest priority; slot into D or E.

## 8. Coverage matrix (proof that all concepts are captured)

Every CATEGORY from the audit maps to at least one module. No concept is orphaned.

| Audit category | Module(s) |
|----------------|-----------|
| PROXY-CORE | F01 |
| PROXY-CHAIN | F02 |
| PROVIDER-MODEL-REGISTRY | F03 |
| MODEL-SCAN-BENCH | F03 (data) + F04 (use) + F07 ($/M variant) |
| MODEL-ROTATION-FALLBACK | F04 (selection) + F05 (rotation/fallback) |
| QUOTA-USAGE-TRACKING | F06 |
| SUBSCRIPTION-KEY-MGMT | F06 |
| COST-MGMT | F07 |
| COMPRESSION | F08 |
| MEMORY-INTEGRATION | F09 |
| HOOKS-EMULATION | F09 |
| MULTI-SESSION-ORCH | F10 |
| OBSERVABILITY-METRICS | F11 |
| DYNAMIC-CONFIG-GEN | F12 |
| CLI-IFACE | F13 |
| TUI-WIZARD | F14 |
| WEBUX-DASHBOARD | F15 |
| TERMINAL-UX | F16 |
| SECURITY/ROUTING-INTELLIGENCE | F01 (boundary) + F04 (classifier) |
| web browser aggregator | F17 |
| QUOTA-OPTIMIZATION / GLOBAL-ALLOCATION (new) | F18 (uses F03 value + F06 meters + F10 sessions) |

## 9. Open decisions for the v2 conversation

RESOLVED by the code/intent research (see `01-CURRENT-STATE-AND-GAPS.md` sections 1 and 3):
- LiteLLM: build our own, do not adopt.
- Model-scan: fold in as a module, keep the snapshot producer/consumer boundary.
- Scoring: use model-scan's real 4-axis + slot-fitness engine; the brainstorming gpt-oss-120b
  "any-one-of vs 30.2" and "two scoring systems" questions are moot/superseded.
- Config + interface parity: already built (specs/001), extend it.
- Implementation approach: from-scratch vs modify is the user's indifference point. RECOMMEND
  extend `claude-code-proxy` (it already holds the required features), keep the plan
  implementation-agnostic. Hard rule either way: every current-version feature must survive into
  the update, plus the new F06/F18 quota-allocation core.
- Allocator online loop: token-bucket enforcement + Thompson bandit + periodic LP re-solve (F18).

STILL OPEN (your call):
1. Project name: keep "Clutch" (recommended) or another?
2. Launch UX: keep the minimal `proxies` + 3-alias scheme (recommended), or add the Ordered
   Compositor `cc` (and if so, 3-slot or 5-slot)?
3. Unify repo strategy: monorepo (recommended) vs linked repos with shared config.
4. Rotation governance: rely on model-scan's existing reliability loop as the engine and add the
   Hermes human-gated `apply` only for generating client config (recommended), or adopt the full
   Hermes rotation spec on top?
5. RESOLVED: wiki-memory hook contract extracted and specified in F09 v2 (in-process `import mem`,
   recall+render_injection pre-request, store.add post-response, hooks-emulation bus). Remaining
   sub-question = persistence policy (auto-store what vs explicit "remember" only).

## 10. Risks and notes

- Several source docs are multi-draft stacks with internal contradictions (notably PRD-MAUG and
  the Hermes specs). The authoritative drafts are identified in SCRATCHPAD.md section 0; v2 must
  not silently re-import superseded numbers.
- Heavy duplication exists across docs (model-scraper spec appears 2-3x; compression analysis has
  a subset duplicate). Consolidated into single feature files; originals retained as source.
- The current system is mid-migration (flat env keys -> namespaced PROVIDERS_* + profiles.json).
  Phase A must land on the namespaced shape, not the legacy flat keys.
- ORMS <1% scrape-block-rate target is aggressive; API-only graceful fallback is mandatory so the
  gateway never blocks on the scanner.
