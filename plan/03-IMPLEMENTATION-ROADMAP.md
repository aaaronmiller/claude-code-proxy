---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, roadmap, implementation, workstreams, build-order, sprints]
---

# Implementation Roadmap

Turns the plan into build order. Approach (per `01-CURRENT-STATE-AND-GAPS.md`): EXTEND
`claude-code-proxy` (it already holds translation, routing, config-parity, circuit breaker,
model-scan consumption, web-ui); bring `model-scan`, `input-compression` (Headroom), and
`wiki-memory` in as packages/sidecars (monorepo recommended, preserve process boundaries). Hard
rule: every current feature survives; nothing below a role's floor; free-only by default.

Tags: [EXTEND] builds on existing code. [NEW] genuinely new. [VERIFY] exists, confirm/finish.
Order is dependency-driven; W0/W1 first, W4/W5 are the new differentiator core.

## W0 - Baseline spine [VERIFY]
- Confirm specs/001 unified-config-system is the config spine; run `pytest tests/` to validate
  SC-001..012; close the skipped T062 in-flight isolation test.
- Extend `src/core/config_manifest.py` so new settings (quota meters, allocator, memory) inherit
  4-surface parity automatically.
- DoD: tests green; one new setting added end-to-end (.env/CLI/TUI/web) via the manifest.

## W1 - Free-only, no-404 reliability [EXTEND] (URGENT, user's top pain)
- Audit `src/core/model_router.py` + `src/core/client.py` for any residual hardcoded model lists;
  make routing fully snapshot-driven (model-scan `routing_snapshot.json`).
- Ensure circuit breaker (`src/core/circuit_breaker.py`) + cascade exclude dead/blocklisted models;
  unknown models/features pass through gracefully and are logged (never break).
- DoD: a day of free-only traffic across the fleet with zero 404/500 storms; every drop logged
  with cause.

## W2 - Proxy chain reorder owned by `proxies` [VERIFY/EXTEND]
- Confirm chain-as-config (specs/001 FR-009..013, `config/proxy_chain.json`); proxy is itself a
  chain entry; reorder/toggle from all 4 surfaces.
- Add BIOS-style reorder UX in TUI (F14) and web drag-drop (F15).
- DoD: reorder a chain from CLI, TUI, and web; change reflected with no restart.

## W3 - Compression knobs + RTK stats surfacing [EXTEND] (F08/F16)
- Expose Headroom settings via the manifest; ensure RTK stats reach the status bars (currently
  missing) and a tokens-saved metric is logged.
- Keep RTK+Headroom always-on, cache-transparent; context engine (hermes-lcm) optional.
- DoD: status bar shows live tokens-saved per layer; knobs settable on all surfaces.

## W4 - Quota meters + global allocator [NEW] (F06 + F18, the new core)
- F06: implement per-provider quota adapters to the meter schema (start Tier-1 header-passthrough:
  Claude, Codex, Cerebras, Groq), then poll (OpenRouter) and scrape (Ollama, Antigravity).
- F18: implement the LP allocator (OR-Tools/PuLP) consuming model-scan value + F06 meters +
  session demand; token-bucket enforcement; Thompson bandit refinement; periodic re-solve.
- Session profiles ("character sheets") with satisfice/maximize per role; live preemption of idle
  sessions; weekly utilization/regret report.
- DoD: allocator emits per-session-role cascades honoring every meter; idle-session borrow works;
  weekly report shows bench-time/regret/shadow-prices.

## W5 - Model-scan fold-in [EXTEND/INTEGRATE] (F03/F04)
- Bring `model-scan` into the repo as a package; keep the snapshot producer/consumer boundary (no
  scoring on hot path). Wire its slot-fitness as F18's `value(m, role)`.
- DoD: one repo, shared config; snapshot drives both routing (F04) and allocation (F18).

## W6 - Memory + hooks-emulation [NEW] (F09)
- In-process `import mem` (wiki-memory): pre-request recall->render_injection->prepend;
  post-response `store.add`; file lock around writes; set MEMORY_PROJECT/DB explicitly.
- Hook-emulation bus: session-start/pre-request/post-response/session-end events for all CLIs.
- DoD: a non-hook CLI (e.g. Pi) gets memory injection + storage through the gateway.

## W7 - Multi-session orchestration + host sentinel [EXTEND/NEW] (F10)
- Global rate limiter across sessions (file/Redis); lanes (standby/interactive); idle detection
  feeding F18 preemption; host sentinel (cpu/ram/thermal, graduated response).
- DoD: 3 Hermes + CC + 5 Pi run concurrently within provider RPM caps; idle preemption observed.

## W8 - Observability completion [EXTEND] (F11)
- Wire failure-by-model/role/provider into historical_failures.json feeding F04/F18; finish
  Prometheus exposure + Grafana dashboards.
- DoD: Grafana shows quota/health; selection improves from logged failures.

## W9 - Web UX rebuild [EXTEND] (F15) (user calls it "totally broken")
- frontend-design pass: 3 themes, microanimations; surface the ~12 analytics endpoints; config
  parity with CLI/TUI; live fail dashboard.
- DoD: web UX builds clean (fix lucide-svelte import breakages), full config parity, live data.

## W10 - Interface polish [EXTEND] (F13/F14/F16)
- Textual live TUI; formalize TUIDS-LLM color system; optional Ordered Compositor `cc` (pending
  your launch-UX decision; current minimal `proxies` + 3 aliases otherwise retained).

## W11 - Translation gaps [EXTEND] (F01, per transformation-matrix)
- Build the MISSING rows: prompt caching, server tools (web search/fetch/memory/code-exec),
  structured outputs, thinking signature_delta, authoritative count_tokens, capability discovery
  GET /v1/models, subagent model control.
- DoD: transformation-matrix rows move missing/partial -> implemented with fixture coverage.

## W12 - Browser aggregator [NEW] (F17, lowest priority)
- Slot after the core lands.

## Sprint 1 (concrete first tasks)
1. W0: run test suite; extend config_manifest with a throwaway setting to prove parity path.
2. W1: grep `model_router.py`/`client.py` for hardcoded model ids; route everything via snapshot.
3. W4/F06: define the quota-meter schema (section B of F06) + implement the 4 header-passthrough
   adapters.
4. W4/F18: stub the LP over current roles using the model-scan snapshot as value; emit a dry-run
   allocation + shadow-price report (no enforcement yet).
5. W5: vendor model-scan into the repo; point the proxy at the in-repo snapshot path.

## Cross-cutting guardrails (every workstream)
- No hardcoded model ids; unknown passes through. Free-only default; per-role free/paid honored.
- 4-surface parity via the manifest (no separate code paths). Secrets env-only; loading order
  preserved; never touch ANTHROPIC_API_KEY=pass / x-api-key:pass.
- Every feature change keeps the transformation-matrix + feature-parity docs current.
