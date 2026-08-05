# Proxy Observability Overhaul — Build Plan

> Scope: comprehensive request logging (dual-level + codec), Prometheus metrics for
> everything, Grafana dashboards, and two web-UI surfaces (frontpage + analytics with
> 30+ graphs by topic), cross-referencing headroom + RTK + Claude/Hermes session data.
> Status: PLAN ONLY. Execute in phases; honor repo constitution (research-first,
> changelog, single-source config, safe destructive ops, progressive disclosure).

## What already exists (verified — extend, don't rebuild)
- **DB**: `usage_tracking.db` (`api_requests`) now has: original_model, routed_model,
  resolved_model, provider, endpoint, input/output/thinking/total tokens, **cached_tokens,
  transformed, transform_type** (just added), duration_ms, tokens_per_second,
  estimated_cost, stream, message_count, has_system/tools/images, status, session_id,
  profile, request/response_content. Plus `model_usage_summary`, `daily_model_stats`,
  `session_summary` tables.
- **Prometheus**: 14 metric defs across `src/main.py`, `src/api/metrics_api.py`,
  `src/api/analytics_api.py`, `src/api/system_monitor.py`. `metrics_api.py` already has
  a single fan-out point (`update all relevant series` from `usage_tracker.log_request`).
- **Grafana**: `deploy/observability/` has `prometheus.yml`, grafana provisioning
  (datasources + dashboards), and `dashboards/clutch-gateway.json`. docker-compose present.
- **Web UI** (SvelteKit): `routes/analytics`, `routes/dashboards`, `routes/realtime`,
  `AnalyticsDashboard.svelte`, `components/charts`, websocket live feeds.
  ⚠ `web-ui/src/lib/services/mockAnalytics.ts` exists — **must be replaced with real data**
  (NO-PLACEHOLDERS mandate).
- **Logging**: `services/logging/structured_logger.py` (prod/debug/forensic handlers,
  redaction), `utils/request_logger.py`. Log dir under proxy CWD.

## Phase 0 — Spec + gate (constitution)
- Write `specs/NNN-observability/` (requirements.md, design.md) per spec-driven flow.
- `plan.md` Constitution Check enumerating all 6 principles. Gate before code.

## Phase 1 — Logging layer: dual-level + codec
**Goal:** `default` = compact (each field 5–20 chars, mostly numbers/enum codes);
`debug` = EVERYTHING (full request/response, headers, timings, chain decisions).
- Add `LOG_LEVEL` (default|debug) resolved through `config_resolver` (single-source; no
  stray `os.environ.get`). Map: default→compact JSONL line; debug→forensic handler (exists).
- **Codec** (`src/services/logging/codec.py`): bidirectional enum maps persisted as a
  versioned `codec.json` so historical logs stay decodable:
  - provider: 1=openrouter 2=deepseek 3=nvidia 4=anthropic 5=kimi 6=qwen 7=opencode_go …
  - model: small int per resolved_model (auto-assigned, append-only)
  - transform: 0=none 1=claude->openai 2=openai->claude 3=both
  - status: 0=ok 1=err 2=timeout 3=ratelimit 4=cascade
  - endpoint: 0=/v1/messages 1=/chat/completions …
- **Compact line schema** (CSV or packed JSON, ~80–120 bytes/req):
  `ts,reqid8,prof#,inID#,actID#,prov#,tx#,st#,in,out,cache,think,ms,tps,cost_milli`
  (cost in integer milli-dollars to avoid float bloat). Write via a new `compact_logger`.
- Keep the SQLite `log_request` as the structured source of truth (already wired);
  the compact file is the cheap append-only stream for tailing/replay.
- Tests: round-trip encode/decode; size assertion (<128 B/line default); debug captures
  full body. SC: default line ≤128B, debug line lossless.

## Phase 2 — Prometheus: meter everything
Expand `metrics_api.py` fan-out (the existing single call point) to emit, labeled by
{provider, resolved_model, profile, transformed, status}:
- counters: requests_total, errors_total, cascade_switches_total (already), tokens_total{kind=in|out|cache|think}
- histograms: request_duration_ms, ttft_ms (add — needs client timing), tokens_per_second
- gauges: active_requests, circuit_breaker_state (already), weekly/session quota_remaining
- cost: estimated_cost_total, original_cost_total, savings_total (headroom+RTK)
- **headroom**: pull from `~/.headroom/logs/proxy.jsonl` + headroom `/metrics` if exposed →
  compression_ratio, tokens_saved_total, kompress_device, cache_hit_total.
- **RTK**: parse `rtk gain --history` (JSON) → rtk_tokens_saved_total{command}.
Add a `/metrics` scrape endpoint if not already complete; point `deploy/observability/prometheus.yml` at it.

## Phase 3 — Cross-reference session data (Claude/Hermes)
- Ingestor that reads `~/.claude/projects/**/*.jsonl` (Anthropic Pro usage) and Hermes
  logs → a `session_facts` table keyed by session_id/time bucket: cost-weighted tokens,
  5-hour-window + Thursday-02:00 quota-week rollups (reuse the cost weighting:
  in×1 + out×5 + cache_write×1.25 + cache_read×0.1).
- Join proxy `api_requests.session_id` ↔ transcript sessions to attribute proxy-routed
  (non-Anthropic) vs Anthropic-quota spend per session. This is the "what's eating my
  quota vs what's offloaded" view.
- Multi-machine: optional SSH pull from `spectre-16` (192.168.0.137:2222, user cheta) to
  union both machines' session_facts (account quota is shared).

## Phase 4 — Grafana
- Extend `clutch-gateway.json` + add `dashboards/usage-deep.json`:
  rows by topic: Traffic, Latency, Tokens, Cost & Savings, Routing/Transforms,
  Providers, Quota (5h + weekly Thu reset), Headroom, RTK, Errors/Cascade, Sessions.
- Provisioning already wired; just drop JSON + reference datasource.

## Phase 5 — Web UI surface 1: frontpage dashboard
- `routes/dashboards` (or `+page`): at-a-glance cards + ~6 hero charts
  (req/min, p50/p95 latency, tokens today, cost vs savings, top providers, quota gauges:
  5-hour window % + weekly Thu-reset %). Real data via analytics API; kill mock usage here.

## Phase 6 — Web UI surface 2: analytics (30+ graphs by topic)
Replace `mockAnalytics.ts` with real endpoints (`analytics_api.py`). Organize into tabs:
1. **Traffic** (4): req/min, by endpoint, by profile, stream vs non-stream
2. **Latency** (4): p50/p95/p99 over time, by provider, by model, TTFT
3. **Tokens** (5): in/out/cache/thinking stacked, per-req dist, cache-hit %, tokens/sec, ctx-util %
4. **Cost & Savings** (5): est cost/day, original vs effective, headroom savings, RTK savings, $/provider
5. **Routing & Transforms** (4): requested→actual sankey, transform mix, cascade switches, fallback rate
6. **Providers** (4): share, error rate by provider, latency by provider, key-pool rotation
7. **Quota** (4): 5-hour window burn, weekly (Thu 02:00) burn, projected exhaustion, per-machine split
8. **Sessions** (4): cost-weighted per session, Claude vs proxy split, top sessions, session timeline
9. **Headroom** (3): compression ratio, tokens saved, device/mode
10. **RTK** (3): savings by command, calls, % reduction
Each: tables + graphs; export buttons; time-range picker. Target ≥40 panels total.

## Phase 7 — Verify & ship
- `rtk vitest run` / backend tests; `rtk next build` for web-ui.
- Live-verify in browser (load each tab, confirm real numbers, no mock).
- CHANGELOG `[Unreleased]`; update docs by pointer (progressive disclosure).

## Risks / decisions to confirm
- Codec versioning: append-only, never renumber (old logs must decode).
- `request_content`/`response_content` only in debug (redaction + size).
- Anthropic Pro usage is NOT in the proxy DB (direct traffic) — Phase 3 ingestor is the
  only way to unify it; without it, "quota" graphs cover proxy-routed traffic only.
- Cost-weighting constants live in ONE module (single source) reused by web + Grafana + ingestor.

## Suggested execution order for a fresh session
P0 gate → P1 (codec+dual log, testable in isolation) → P2 (prometheus) →
P3 (session ingest) → P4 (grafana) → P5 (frontpage) → P6 (analytics tabs) → P7.
Each phase is independently shippable; stop/checkpoint between.

---

## PROMPT A — existing-config analysis (run this FIRST in the next session)
Paste verbatim:

> You are working in `~/code/claude-code-proxy` (FastAPI proxy + SvelteKit web-ui,
> spec-driven, see CLAUDE.md constitution). Before writing ANY code, produce a grounded
> inventory of the existing observability/config stack. Do NOT assume — read the files.
> Deliver a markdown report covering:
> 1. **Config resolution**: how `LOG_LEVEL`/`TRACK_USAGE`/`USAGE_DB_PATH` and provider/
>    model routing are resolved. Find the single-source resolver (`src/core/config_resolver.py`,
>    `config.py`, `config_manifest.py`); list every `os.environ.get` that bypasses it (constitution #6).
> 2. **Logging**: enumerate handlers in `src/services/logging/structured_logger.py` +
>    `utils/request_logger.py` — what each writes, where, at what level, redaction rules.
> 3. **DB**: full `PRAGMA table_info(api_requests)` + the other tables in `usage_tracking.db`;
>    which columns are populated vs always-null in the last 500 rows; row counts + date ranges
>    of the live DB and the archived copies under `archive/2026-06-01-cleanup/root-data/`.
> 4. **Prometheus**: list all 14 metric defs (file:line, name, type, labels) and the
>    single fan-out point in `metrics_api.py`; what `/metrics` currently exposes; what
>    `deploy/observability/prometheus.yml` scrapes.
> 5. **Grafana**: panels in `deploy/observability/grafana/dashboards/clutch-gateway.json`
>    (titles + queries); provisioning wiring.
> 6. **Web-UI**: routes under `web-ui/src/routes/{analytics,dashboards,realtime}`; every
>    component that imports `mockAnalytics.ts` (these must become real); the analytics API
>    client + which `analytics_api.py` endpoints exist vs are stubbed.
> 7. **External data**: headroom log schema (`~/.headroom/logs/proxy.jsonl`) and whether
>    headroom exposes `/metrics`; `rtk gain --history` output shape; Claude transcript
>    usage schema (`~/.claude/projects/**/*.jsonl` — `message.usage` fields).
> Output a gap table: [data field the plan needs] × [exists? where? populated?]. Save to
> `plans/observability-existing-config-report.md`. This satisfies constitution principle #1
> (Existing Research Before Building) and de-risks every later phase.

## PROMPT B — handoff (start a build session after Prompt A)
Paste verbatim:

> Continue the Proxy Observability Overhaul. Read these first, in order:
> 1. `~/code/claude-code-proxy/plans/observability-overhaul-plan.md` (the build plan)
> 2. `~/code/claude-code-proxy/plans/observability-existing-config-report.md` (recon from Prompt A)
> 3. `~/code/claude-code-proxy/CLAUDE.md` (constitution — research-first, changelog, single-
>    source config, safe destructive ops, progressive disclosure) and run its mandatory
>    `.specify/memory/constitution.md` read before any `/speckit.*`.
> Context already done in a prior session: `usage_tracking.db.api_requests` gained
> `cached_tokens`, `transformed`, `transform_type`; all 4 `log_request` call sites in
> `src/api/endpoints.py` pass them; `TRACK_USAGE=true` in `.env`. headroom-start.sh fixed
> (`--openai-api-url`, anthropic redirect via `ANTHROPIC_TARGET_API_URL`).
> Execute phases IN ORDER (P0 gate → P1 codec+dual-log → P2 prometheus → P3 session
> ingest → P4 grafana → P5 frontpage → P6 analytics tabs → P7 verify). Stop and checkpoint
> after each phase; update `CHANGELOG.md [Unreleased]` per phase. Hard rule: NO mock/
> placeholder data anywhere — replace `web-ui/src/lib/services/mockAnalytics.ts` with real
> endpoints; if data isn't available yet, surface "no data" not fake numbers. Cost-weighting
> constants (in×1, out×5, cache_write×1.25, cache_read×0.1) live in ONE module reused
> everywhere. Multi-machine union: `ssh spectre-16` (192.168.0.137:2222, user cheta).
> Begin with P0: write `specs/NNN-observability/{requirements,design,plan}.md` and the
> Constitution Check gate; do not implement until the gate passes.

## FILE LOCATIONS
- Plan: `~/code/claude-code-proxy/plans/observability-overhaul-plan.md` (this file)
- Recon report (Prompt A will create): `~/code/claude-code-proxy/plans/observability-existing-config-report.md`
- Note: `plans/` is local scratch (excluded from sync per CLAUDE.md).
