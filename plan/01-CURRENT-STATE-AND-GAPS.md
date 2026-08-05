---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, current-state, gap-analysis, pivot, litellm-decision, model-scan, reconciliation]
---

# Current State and Gap Analysis (reconciliation with real code)

This doc reconciles the v1 plan (built from 21 brainstorming docs) with the ACTUAL state of
the three live repos. Read it before the feature files: it overrides any "(PROPOSED)" tag in
F01-F17 where the thing already exists.

Evidence: deep read of `/home/cheta/code/claude-code-proxy` (specs 000-003 + docs + src),
`/home/cheta/code/model-scan` (scoring engine), and intent-mining of USERPROMPTS-v2.md (6464
lines of verbatim prompts) + CASS (873 conversations).

## 0. The big reframe: this is a PIVOT, not a greenfield rebuild

`claude-code-proxy` (branded "Clutch Gateway", pkg v1.0.0, Python + FastAPI) is a mature,
hand-built Anthropic<->OpenAI gateway. The authoritative "going forward" PRD is
`specs/000-claude-code-middleware-gateway`: it pivots the repo to a FOCUSED Anthropic-compatible
middleware gateway and sheds platform weight (billing/dashboards/RBAC/GraphQL as non-core). The
greenfield framing in `00-MASTER-PLAN.md` should be read as "unify and extend this base", not
"build from zero". Most core modules already exist and must be preserved, not rebuilt.

The three repos to unify:
- `/home/cheta/code/claude-code-proxy` - the gateway (translation, routing, chain, config, web-ui)
- `/home/cheta/code/model-scan` - the model scanner + scoring engine (`dink.py` ~3600 lines)
- `/home/cheta/code/input-compression` - Headroom (compression), with RTK as a CLI-side wrapper
- `/home/cheta/code/wiki-memory` - the memory backend (audit summaries already exist)

## 1. RESOLVED DECISIONS

### 1.1 LiteLLM: BUILD OUR OWN (do not adopt). RESOLVED.
- Current code uses NO LiteLLM (absent from src, pyproject, lockfile). Translation is hand-built:
  `request_converter.py` (993 L) + `response_converter.py` (1675 L).
- `specs/000` final-report explicitly rejects it: "Do not fully replace the gateway with LiteLLM",
  "not the right center of gravity". The in-house converter is the differentiated asset to keep.
- Answer to "what does LiteLLM do that we could not duplicate": nothing decisive. Its one real
  edge is breadth of provider adapters, but providers here are OpenAI-compatible or hand-added,
  and our tool-call fidelity + behavior-driven normalization already exceeds LiteLLM's. Adopting
  it also reintroduces the pip supply-chain risk for zero net gain.
- Note: old logs show `litellm.NotFoundError`, so an earlier build may have used it; the current
  build does not. Decision is final: extend the in-house converter; treat CCR/Mux as reference
  benchmarks only.
- Iterative-improvement hook: keep an eval harness that diffs our converter output against a
  reference (e.g. CCR) on a fixture set, so we catch fidelity regressions.

### 1.2 Model-scan: FOLD IN AS A MODULE, KEEP THE SNAPSHOT BOUNDARY. RESOLVED.
- model-scan is a complete working program with a sophisticated scoring engine (see section 3).
  It produces `~/.config/model-scan/routing_snapshot.json`; the proxy consumes it (no import, no
  scoring on the hot path). specs/003 marks the integration built.
- "Fold in fully" = bring model-scan into the unified project as a first-class module (shared
  repo, shared config, shared docs), but PRESERVE the producer/consumer snapshot boundary. Scoring
  must never run on the request hot path (specs/003 NFR-001/031). This is correct architecture,
  not a deferral.
- The brainstorming-doc scoring conflicts (gpt-oss-120b "any-one-of" vs composite-30.2) are
  SUPERSEDED by model-scan's real engine (section 3). Drop those open questions.

### 1.3 Config + interface parity: ALREADY BUILT, EXTEND IT. RESOLVED.
- `specs/001-unified-config-system` is COMPLETE (84/84 tasks): single `Assignment` record, layered
  `ConfigResolver` (precedence CLI > shell env > .env > stored > defaults), one write-path API
  shared by CLI/TUI/WebUI, proxy-chain reorder across all surfaces, audit log, schema migration.
  CI greps to forbid direct `os.environ.get` outside config modules (mechanical single-source).
- 63 settings claimed at 100% parity across .env/CLI/TUI/WebUI (`docs/feature-parity.md`,
  auto-generated from `src/core/config_manifest.py`).
- This satisfies the user's #1 structural demand (CLI as source of truth, TUI/Web as wrappers).
  v2 work = extend the manifest to new settings, finish web-UI analytics surfacing, verify the
  one skipped test (T062 in-flight isolation).

## 2. WHAT IS ALREADY BUILT vs GAP (by feature module)

Status: WORKS = implemented and documented. PARTIAL = present but incomplete. MISSING = not built.

| Module | Status | Evidence / gap |
|--------|--------|----------------|
| F01 Proxy core / translation | WORKS | Hand-built Anthropic<->OpenAI; tools/tool_use/tool_result/tool_choice, SSE input_json_delta, text-tool-call recovery, per-provider arg normalization + behavior cache. GAPS: prompt caching (MISSING), server tools web_search/web_fetch/memory/code-exec (MISSING), structured outputs (modeled only), thinking signature_delta (MISSING), count_tokens accuracy (PARTIAL, char/4), capability discovery GET /v1/models (MISSING), subagent model control (MISSING) |
| F02 Proxy chain | WORKS | `config/proxy_chain.json`, proxy is itself a chain entry, reorder via all surfaces (specs/001 FR-009..013). Modes comp/proxy/full. GAP: BIOS-style reorder TUI polish |
| F03 Registry + scanning | WORKS | model-scan full engine + 10 providers + snapshot. GAP: unify into repo; surface model characteristics in web-ui |
| F04 Routing / selection | WORKS | `model_router.py` precedence (passthrough > assignment > custom py/js router > tier); slot detectors; snapshot policies static/free/budget/quality/roles/rotate (specs/003) |
| F05 Rotation / reliability / fallback | WORKS | `circuit_breaker.py` full FSM + disk persistence; `client.py` cascade, OpenRouter native fallback, cross-provider, mid-stream tier override, error classification. model-scan reliability_feedback + bad_models. GAP: the Hermes-spec rotation cadence/recommendations.json apply-flow |
| F06 Quota / key / subscription | PARTIAL (substrate exists) | budgets WORK; `src/core/quota_sources.py` has QuotaSample + QuotaSource Protocol + Tokscale/Ccusage/Static adapters + merge; `src/core/rotation.py` has drain-threshold rotation + cooldown. GAP: generalize QuotaSample -> multi-meter QuotaMeter + add header/poll/scrape provider adapters (RECON-02). Smaller than first rated |
| F07 Cost management | PARTIAL | budgets + free/paid eval_mode per slot WORK; OC Go budget blended into fitness. GAP: consumer-plan $/M token-economics report |
| F08 Compression + caching | WORKS | Headroom always-on base :8787 (15 settings), semantic + token cache, RTK CLI wrapper. Kompressor = Headroom's model-weight compression (corrected). GAP: surface RTK stats; cache-state signal exposure |
| F09 Memory + hooks emulation | SPEC'D (new build) | F09 v2 specifies the real contract: in-process `import mem` (wiki-memory `memory/mem.py` JSON store), recall->render_injection->prepend pre-request, store.add post-response, hooks-emulation bus. MCP is only spec'd/disabled in wiki-memory so not relied on. Genuinely new gateway-side build |
| F10 Multi-session orch + host sentinel | PARTIAL | crosstalk WORKS; lanes (standby/interactive) in model-scan; concurrency pain noted (429s, dup-request). GAP: host sentinel, workers.yaml, global rate limiter across sessions |
| F11 Observability | PARTIAL | 33-col usage SQLite, ~12 /api/analytics endpoints, prometheus_client, terminal dashboard suite. GAP: web-ui analytics surfacing, Grafana, failure->selection feedback loop wiring |
| F12 Config + parity | WORKS | specs/001 complete. GAP: extend manifest; finish web analytics; verify T062 |
| F13 CLI + launch aliases | PARTIAL | `proxies` lifecycle command + 3 zshrc aliases (deliberately minimal). Ordered Compositor `cc` grammar is PROPOSED ONLY, not built |
| F14 TUI wizard | PARTIAL | `start_proxy.py --configure-advanced` (19 categories) WORKS; Textual live TUI noted "not yet built" |
| F15 Web UX + dashboard | PARTIAL | built SvelteKit app exists; user calls it "totally broken"; analytics under-surfaced. Needs frontend-design pass + Grafana |
| F16 Terminal color + status | WORKS | tmux status bars, statusline scripts, RTK stats cache, jitter-fix. GAP: TUIDS-LLM formalization |
| F17 Browser aggregator | MISSING | idea sketch only |

Net: F01-F05, F08, F12, F16 are largely built. F06, F07, F10, F11, F13, F14, F15 are partial.
F09, F17 are genuinely new. The plan's effort should concentrate on the partial/missing rows.

## 3. THE REAL MODEL-SCAN SCORING ENGINE (supersedes brainstorming formulas)

From `/home/cheta/code/model-scan`. Two paths: v5 multi-axis engine (`scoring/`) and a legacy
heuristic in `dink.py`. Slot fitness is the selection score.

- 4 axes, each calibrated-base + bounded modifiers, clamped 0-100 (`scoring/engine.py:88-142`):
  - Intelligence: base = calibrate(AA intelligence index); modifiers kc_age, recency, reasoning, ctx, multimodal
  - Speed: base = tps_score*0.55 + lat_score*0.45, provider mult {groq 1.3, cerebras 1.25}; penalties reasoning/free-tier
  - Agentic: base = calibrate(BFCL) else has_tools?60:30; modifiers struct_output, max_output, ctx, kc
  - Coding: aa_coding*0.6 + (swe_verified*0.4 or arena_elo*0.3 or 30*0.4) + tps*0.15
- Calibration constants (`scoring/calibration.py:7-49`): aa_index (raw/60*100)-10; tps 50*log2(1+tps/60);
  latency 80-log1p(s)*30; bfcl raw/92.5*100; arena_elo elo/1482*100; swe score/80*100
- Composite weights: default intel .50/speed .15/agentic .15/coding .20; gold_standard .40/.20/.20/.20
- Slot fitness (`dink.py:2278-2510`): hard GATES first (accessible, free-whitelist, needs_tools,
  needs_vision, min_tps, max_latency, min_ai, min_ctx_k, min_tier, min_iq, min_tc) then weighted
  score with weight_speed HARD-CAPPED at 0.50, times multiplicative modifiers: aa-freshness
  (fresh 1.0, 7d-cache 0.3), latency-consistency, arch bonus, OC Go budget blend, historical-issue
  (logfile mining, persistence .8 -> mult .2), capability probe (<=0 disqualifies), provider
  hour-window availability (0-1)
- Tiers: static `tiers.yaml` (S/A/B+/B/C/D/NOT_CHAT, curated) + computed thresholds S>=65/A>=55/B>=40/C>=15
- Slots: `slot_definitions.yaml` (config dir), 16 roles (R1_primary, R6_compression, R7_vision, ...)
  each with gates + weights + eval_mode (free vs cost_basis)
- Blocklist (`blocklist.yaml`): d_tier_chat, not_chat_models, overpriced_for_quality,
  conditionally_allowed, misleadingly_free, provider_exhausted; glob + regex match
- Data sources: Artificial Analysis API (v2 intelligence/coding/math index), models.dev,
  PinchBench, local benchmarks.json (swe_verified, bfcl_v3, arena_elo), OpenRouter API
  (free whitelist), live per-provider probes. No llm-stats in code.
- Snapshot schema (`routing_snapshot.py`): schema_version, provider_health, blocklist,
  provider_quota, slots{slot:{best, candidates[ {model_id, provider, api_model, fitness,
  price_blended, tier, has_tools, has_vision} ] }}. Cascade = ordered candidates by fitness.
- 10 providers: openrouter, nvidia, groq, cerebras, opencode-go, ollama-cloud, opencode-zen,
  kilo, ollama-local, venice.

This is the authoritative selection algorithm. F03/F04 should reference THIS, not the
brainstorming-doc formulas.

## 4. USER INTENT (from prompt mining, ranked)

True-intent one-liner: a free-tier-only, provider-agnostic local AI gateway with a fully
reorderable proxy+compression chain, task-based model routing, and total CLI/TUI/Web parity,
that never hardcodes a model, never wastes budget, gracefully passes through anything new, and
surfaces deep token/cost metrics everywhere, evolving toward a self-tuning multi-session
agent-fleet controller.

Non-negotiables (hard):
- Free models only; never burn budget (test with free OpenRouter models).
- No hardcoded model IDs or settings; unknown models/features pass through, never break (this is
  the root cause of the 404/500 storms he keeps hitting).
- Three-way interface parity via CLI-as-source-of-truth; TUI/Web are thin wrappers (no dup logic).
- All config in one `.env` (he dislikes the env + envrc split).
- Proxy chain fully arbitrary and reorderable (BIOS-boot-order-style TUI, Bubble Tea/Textual).
- Must run as pure passthrough (compression-only) with Anthropic Pro keys when substitutions off.
- Tooling: TUI Bubble Tea/Textual; Web SvelteKit 5 + his frontend-design skill; metrics
  Prometheus + Grafana.

Core/urgent (build first): free-only operation without 404/500 storms; reorderable chain owned by
`proxies`; Headroom+RTK with exposed knobs + tokens-saved benchmarks; task-substitution with full
bypass / Pro passthrough; centralized .env + new-machine installer; functional parity + a
not-broken web UX; accurate metrics (tokens in/out per model/date, tool success, status bars).

Nice-to-have: polished themeable web UX (3 themes, microanimations); full Grafana deep analytics;
fitness leaderboard with OpenRouter scraping; multi-session orchestration (20+) + quota ledger +
preemption; logfile-mining -> fitness -> dynamic Hermes config generation; wiki-memory hooks.

Pet peeves to design against: broken/ugly web UX; dead hardcoded models causing 404/500 storms;
OpenRouter free-tier tool-use/data-policy narrowing; stale config silently breaking routing;
concurrent-session breakage (429s, dup-request, lossy single pending message); status-bar jitter;
half-built features left lingering.

## 5. REMAINING OPEN DECISIONS (genuinely unresolved)

1. Project name: "Clutch" / "Clutch Gateway" is the working name; MAUG was a brainstorming name.
   Naming not locked. RECOMMEND: keep Clutch.
2. Ordered Compositor `cc`: still proposed-only. 5-slot vs 3-slot, OR keep the current minimal
   `proxies` + 3-alias scheme (which the repo doc deliberately chose to avoid alias explosion).
   RECOMMEND: keep minimal launch UX; add cc 3-slot only if you want it. Your call.
3. Repo strategy for the unify: monorepo (gateway + model-scan + headroom as packages) vs linked
   repos with shared config. RECOMMEND: monorepo, preserve snapshot/compression process
   boundaries.
4. Rotation governance: model-scan already does reliability_feedback + bad_models + provider
   windows. The Hermes-spec recommendations.json + human-gated `apply` flow is additional. Adopt
   the Hermes apply-flow on top, or rely on model-scan's existing loop? RECOMMEND: model-scan's
   loop is the engine; add the human-gated apply only for client-config (Hermes config.yaml)
   generation.
