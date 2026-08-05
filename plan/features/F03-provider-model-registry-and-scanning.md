---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, registry, orms, model-scan, benchmarks, models-dev, artificial-analysis, tiers]
---

# F03: Provider and Model Registry + Scanning/Benchmarking (ORMS)

> STATUS v1.1: model-scan already EXISTS and is a complete working program at
> `/home/cheta/code/model-scan` (`dink.py`, ~3600 lines). Its real scoring engine (4-axis +
> slot-fitness + calibration constants + tiers.yaml + blocklist.yaml) SUPERSEDES the
> brainstorming-doc formulas below. See `01-CURRENT-STATE-AND-GAPS.md` section 3 for the
> authoritative algorithm. The notes below remain as design/source context only.

Scope: know every provider, every model, what each can do, and how good/fast/reliable/cheap it
is. Two halves: (a) a live capability registry the request path queries, and (b) ORMS, an
offline scanner that enriches a local model DB from external benchmark sources. This is the
model-scan program the user plans to fold in fully.

## Capability registry (live)

- Per-model capabilities: max_tools, parallel_calls, strict_schema, streaming format, health,
  TTL. Three sources: provider /v1/models, curated JSON, live probe. Redis-cached, invalidated
  on 4xx/5xx. (`PRD- MAUG.md:196-228`)
- Live capability probing via dry-run (max_tokens:1) on cache miss or error.
  (`Proxy update plan.md:147`)
- Provider inventory (endpoints/keys/models): OpenRouter, OpenCode Zen, OpenCode Go, Ollama
  Cloud, NVIDIA NIM, Groq, Cerebras. (`MODEL_ARCHITECTURE.md:112-247`) (CURRENT)

## ORMS scanner (offline, Build)

- Hybrid acquisition: Tier-1 fast API sync (daily, <30s, ~300 models) + Tier-2 conditional deep
  scrape (camoufox + crawl4ai). (`PRD- proxy model scraper helper.md:67-85`)
- Smart change detection: SHA-256 checksum, >10% pricing delta re-scrape, new-model queue,
  30-day full audit. (`:86-92`)
- SUPERSEDED: the brainstorming doc said ORMS does not exist, but model-scan DOES exist at
  /home/cheta/code/model-scan (complete program). Fold in / extend, not build from scratch.
  (`Proxy update plan.md:2800-2855`; see STATUS banner above + 01-CURRENT-STATE)
- Graceful degradation: scrape failure falls back to API-only so the gateway never blocks.
  (`PRD- proxy model scraper helper.md:240-241`)

## External data sources and fields

- Artificial Analysis (IQ/coding/agentic/reasoning/speed; free endpoint /v2/language/models/free),
  models.dev (ctx/maxout/toolcall/reasoning/cache/multimodal/pricing/dates), PinchBench (agentic
  %), llm-stats.com coding arena (TrueSkill over SWE-Bench/LiveCodeBench/Terminal-Bench/Aider),
  LMArena ELO. (`MODEL_ARCHITECTURE.md:74-99`; `AAA model-scan algorithm construction.md:1-17,151-301`)
- Detailed benchmark fields: gpqa_diamond, hle, ifbench, aa_lcr, gdpval, critpt, scicode,
  terminal_bench, omniscience. (`PRD- proxy model scraper helper.md:139-163`)
- Performance fields: throughput_tps, latency_seconds, e2e_latency, tool_error_rate,
  uptime_percent. (`:130-138`)

## Scoring axes (the inputs; the formula lives in F04)

Multi-axis spatial evaluation, top-model calibrated to 100, speed<->agentic quadratic
equivalence. (`AAA model-scan algorithm construction.md:1-17`) Inputs: AA indices, PinchBench,
models.dev specs, live latency/tps, historical failure rate by class, time-of-day availability.
Full input list with pointers in SCRATCHPAD.md F03/F04.

## Static quality floor

- tiers.yaml (S/A/B/C/D/Ungraded, monthly human review) is the ultimate gate; below-floor models
  are never suggested. Plus blocklist.yaml (safety classifiers, non-chat, sub-D). (`Structural
  Assessment of the Hermes Model Selection System.md:65,85,136-143`)
- 5-tier runtime system (T1 Reasoning / T2 -Claw / T3 Workhorse / T4 Specialist / T5 Baseline +
  Boneyard); gpt-oss-120b baseline filter; -claw class IQ40+ AND speed85+.
  (`MODEL_ARCHITECTURE.md:297-407`) (CURRENT)

## Model onboarding pipeline

Startup key-scan -> LLM structured-output classification -> provisional role assignment ->
telemetry reconcile/downgrade + similar-models heuristic. (`PRD- MAUG.md:460-471`)

## Hard requirements

- Leaderboards smartest/coding/free/value; value_score = intelligence/price, free excluded
  (div-by-zero). (`PRD- proxy model scraper helper.md:165-186`)
- Freshness <=24h, >=95% benchmark completeness, <1% scrape block rate, deep scan <60min/300
  models, token cost accuracy +-10%, atomic writes, no persisted credentials. (`:210-241`)
- camoufox isolated to ORMS, never in the live request path; holds only OpenRouter public creds.
  (`PRD- MAUG.md:818,1055`)

## Dependencies

- Feeds F04 (selection), F05 (rotation eligibility), F07 (cost/value), F11 (ORMS-change
  annotations on telemetry).

## Open questions

- Fold ORMS in fully (in-process or sub-package) vs Invoke as sidecar? User leans fully.
- Reconcile detailed-benchmark field set vs what AA free endpoint actually exposes.
