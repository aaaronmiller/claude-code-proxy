---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, multi-session, orchestration, host-sentinel, rate-limit, workers]
---

# F10: Multi-Session Orchestration and Host Sentinel

> STATUS v1.1: PARTIAL. crosstalk BUILT; lanes (standby/interactive) in model-scan. NEW to build:
> host sentinel (cpu/ram/thermal), workers.yaml, global cross-session rate limiter, idle detection
> that feeds F18 preemption. "(PROPOSED)" tags below are superseded by 01-CURRENT-STATE.

Scope: serve many concurrent harness sessions (multiple Hermes runs, multiple Claude Code
sessions) without resource conflict, and watch host resources so runaway sessions are caught.

## Concurrent serving

- Single-process asyncio gateway handling many harnesses/sessions concurrently (not many users).
  (`PRD- MAUG.md:790-804,907`)
- Deployment topology / process table: gateway + LiteLLM container + ORMS + Headroom + RTK +
  Redis + TUI + CLIProxyAPI, each independently restartable. (`:792-803`)
- Global rate limiter across child processes (file or Redis): for example 6 concurrent Hermes
  children against OpenRouter 20 RPM. (`Hermes Model Rotation & Reliability Specification.md:524`)
- Multi-machine awareness via workers.yaml: per-worker model availability, route delegation.
  (`Structural Assessment of the Hermes Model Selection System.md:87`)
- Hybrid routing architectures per usage profile (light 5M / moderate 15M / power 50M / heavy
  500M tokens-month). (`Model-scan features.md:100-107`)

## Host Sentinel

- Monitor cpu/ram/swap/thermal with baselining; graduated responses log -> alert -> notify ->
  kill the offending process, with per-category opt-in and attribution vs baseline. (`PRD-
  MAUG.md:643-657`; `Proxy update plan.md:56`)

## Crosstalk (current)

- Model-to-model exchange paradigms memory/report/relay/debate, iterations, model list (currently
  commented). (`claude cody proxy .env.md:853-871`) (CURRENT)

## Reference (external)

- Claude Code Agent Teams TeammateTool / Task system / spawn backends (tmux/iterm2/in-process).
  (`Claude Code Backend Middleware - Project Assessment.md:741-810`)

## Hard requirements

- Concurrency must not exceed provider RPM limits; the global rate limiter is authoritative across
  sessions.
- Host Sentinel kill action is opt-in per category and must log attribution before acting.

## Dependencies

- Rate limiter consumes F06 quota windows; Sentinel emits to F11; workers.yaml read by F04 for
  route delegation; Control MCP (F09) can pause providers/sessions.

## Open questions

- Is multi-machine (workers.yaml) in v1 scope or a later phase? Source lists it as a late phase.
