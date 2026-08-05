---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, maug, clutch, pointer-index, audit, scratchpad, traceability]
---

# AI Gateway: Source Pointer Index (Scratchpad)

Purpose: single index mapping every concept found in the 21 source docs to a feature
module, with `file:line` pointers back to verbatim text. Built from a 7-agent parallel
audit of 15,485 lines. Use this to retrieve exact source via `Read <file> offset:N`.
Nothing is summarized away here that the master plan or feature files depend on.

Legend: (CUR) = current system already has it. (PROP) = proposed/new. (EXT) = external
fact or third-party tool. F## = feature module file in plan/features/.

## 0. Source-file map (what each doc is)

| Doc | Lines | Role | Authority |
|-----|-------|------|-----------|
| unified_project_idea_record.md | 535 | Umbrella vision, ~80-item feature checklist | PRIMARY vision |
| PRD- MAUG.md | 1969 | Model-Agnostic Unified Gateway PRD (4 stacked drafts; v3.1 L11-906 + v3.0 L929-1207 authoritative; C/D-drafts superseded) | PRIMARY arch |
| Proxy update plan.md | 3092 | Stream-of-consciousness gateway design + research dumps (heavy duplication L735-1231 ~= L1814-2309) | rationale, noisy |
| Hermes Model Rotation & Reliability Specification.md | 1525 | Rotation/reliability hardening (embeds MODEL_ARCHITECTURE verbatim L583-1457) | model layer |
| HERMES_REFINEMENT_SPECIFICATION.md | 1268 | Production thresholds for role->model->provider routing | model layer |
| Claude Code Backend Middleware - Project Assessment.md | 1036 | Competitive landscape + Anthropic tool-call changelog + 3-layer proxy proposal | reference |
| claude cody proxy .env.md | 991 | CURRENT config surface (L558-991; L1-557 is irrelevant ghostty transcript) | CUR truth |
| Terminal Color System.md | 885 | Operator-log color scheme "TUIDS-LLM v1.0" | UX spec |
| MODEL_ARCHITECTURE.md | 874 | Canonical free-tier model selection (providers, tiers, roles, fallbacks) | CUR baseline |
| Ordered Compositor Design Validation.md | 804 | `cc` launch-alias grammar (RMSCO positional) | CLI UX spec |
| Clutch-Gateway-Quota-Monitoring-Technical-Spec.md | 572 | 11-provider quota monitoring + Prometheus/Grafana (architecture only) | quota spec |
| unified_project_idea_record.md | (above) | | |
| PRD- proxy model scraper helper.md | 479 | ORMS (OpenRouter Model Scout) daemon PRD | scan spec |
| Optimal compression for hermes agent.md | 338 | Compression stack analysis (Headroom/RTK/hermes-lcm/pi-prune) | compression spec |
| AAA model-scan algorithm construction.md | 301 | Multi-axis model scoring algorithm + model/pricing universe | scoring spec |
| Structural Assessment of the Hermes Model Selection System.md | 196 | Critique of current scan v4 + ideal continuous-selection design | scan redesign |
| How to use context compression tools and provider prompt caching correctly.md | 171 | Subset-duplicate of Optimal-compression (keep that as canonical) | dup |
| Hermes Optimal Model Settings - Audit Report.md | 149 | $0.05 free-only role-model audit + 4 fixes | model layer |
| Model-scan features.md | 139 | Token-economics ranking spec ($/M quality-adjusted) | cost spec |
| Query for best model plan.md | 84 | Prompt form of Model-scan features.md (dup pair) | cost spec |
| new proxy commands.md | 57 | NEWEST current feature: per-CLI Routing Profiles (merged main) | CUR truth |
| web browser plugin - multi model question distributor and aggregator.md | 20 | Browser fan-out/aggregate idea sketch | idea |

Naming: project = MAUG / Clutch / "Claude Code Proxy" (all the same system). Hermes =
a routed client CLI whose config.yaml the gateway generates. Antigravity = Google VSC
harness reached via VibeProxy/CLIProxyAPI OAuth.

---

## F01. PROXY CORE & TRANSLATION LAYER

- Model/provider/harness-agnostic thesis (PROP) -> Proxy update plan.md:4-8,51-54; unified_project_idea_record.md:37-61
- Bidirectional format translation, A->Canonical->B not A->B (PROP) -> PRD- MAUG.md:147-179,1007,1372-1387; Proxy update plan.md:87-117,576-613
- Canonical schema = OpenAI tools + JSON-Schema 2020-12 + Pydantic v2 strict (PROP/HARD) -> PRD- MAUG.md:148,1007,1312-1336
- 4 wire formats (OpenAI/Anthropic/Gemini/Bedrock-Converse), Cohere 5th legacy (PROP) -> PRD- MAUG.md:129-141,999-1003
- Partial tool-call streaming reassembly state machine (idle->collecting->validating->complete, ijson) (PROP) -> PRD- MAUG.md:180-195,1389-1403; Proxy update plan.md:179-199
- `_meta`/x_provider_extensions unknown-field preservation, lossless round-trip (HARD) -> Proxy update plan.md:169; PRD- MAUG.md:166-179
- Turn-scoped tool-call ID registry {provider_id<->canonical_id<->reply_id} (HARD) -> Proxy update plan.md:404,431; PRD- MAUG.md
- Schema simplification heuristics (flatten objects, enum->string, drop format/pattern) (PROP) -> PRD- MAUG.md:1416-1419
- Reasoning/thinking transforms: REASONING_MAX_TOKENS / REASONING_EFFORT / REASONING_EXCLUDE / VERBOSITY, per-model overrides (CUR) -> claude cody proxy .env.md:639-667
- Antigravity needs Gemini contents[], rejects $ref/const; translate before dispatch (HARD/EXT) -> PRD- MAUG.md:178,1387; Proxy update plan.md:458-470,727
- Advanced Anthropic tool primitives to translate/strip: PTC, Tool Search, defer_loading, server_tool_use, input_examples, effort, adaptive thinking (PROP; zero current coverage) -> Claude Code Backend Middleware...md:255-518,437-503,897-917
- Current server: HOST 0.0.0.0 / PORT 8082 / timeouts / token limits (CUR) -> claude cody proxy .env.md:679-699
- Per-CLI route prefixes /p/pi/v1, /p/opencode/v1, /p/claude/v1 (Anthropic passthrough) (CUR) -> new proxy commands.md:36-38
- Capability-aware weighted routing score = capability*latency*error_penalty (PROP) -> Proxy update plan.md:233-240

## F02. PROXY CHAIN ORCHESTRATOR

- Adjustable any-number/any-order chain; default Headroom(0)->RTK(1)->CLIProxyAPI(2,off)->Proxy (CUR+PROP/HARD) -> unified_project_idea_record.md:9-35
- Proxy Chain first-class; default [maug], extended [headroom,maug,litellm,provider] (PROP) -> PRD- MAUG.md:661-679,1119-1123
- Chain config via 3 surfaces (YAML/TUI/MCP set_active_chain) (PROP) -> PRD- MAUG.md:669-673
- Chain validation: reject loops / incompatible mid-flight mutation / format mismatch; manifest in every log (HARD) -> PRD- MAUG.md:674-679
- Run with OR without chain; passthrough tunnel; both continue-modes at once (HARD) -> unified_project_idea_record.md:33-35,265-273
- Provider diversity filter (no provider >2 consecutive) (CUR) -> MODEL_ARCHITECTURE.md:332-341
- 3-layer proxy alt: CLI-Interceptor -> API-Translator -> LiteLLM (PROP) -> Claude Code Backend Middleware...md:824-841
- starbased-co/ccproxy hook system as foundation (PROP/EXT) -> Claude Code Backend Middleware...md:213-229

## F03. PROVIDER & MODEL REGISTRY + SCANNING/BENCHMARKING (ORMS)

- Provider capability registry: max_tools/parallel/strict_schema/streaming-format/health/TTL; 3 sources (/v1/models + curated json + live probe), Redis-cached (PROP) -> PRD- MAUG.md:196-228,1338-1370; Proxy update plan.md:121-152
- Live capability probing (dry-run max_tokens:1 on cache miss/error) (PROP) -> Proxy update plan.md:147,1261
- ORMS daemon: hybrid API sync (<30s/300 models) + conditional deep scrape (camoufox+crawl4ai, <1% block) + checksum change detect + leaderboards (PROP) -> PRD- proxy model scraper helper.md:21-216; PRD- MAUG.md:352-458,1520-1672; Proxy update plan.md:735-877
- ORMS: the brainstorming doc claimed it does not exist, but the model-scan program DOES exist at
  /home/cheta/code/model-scan (dink.py). SUPERSEDED: fold in / extend, not build from scratch.
  See 01-CURRENT-STATE. -> Proxy update plan.md:2800,2817
- Pre-made ORMS alternatives surveyed (openrouter-provider-api, openrouter-inspector, or-models, llm_models_spider) (EXT) -> Proxy update plan.md:2804-2855
- Data sources: artificialanalysis.ai (IQ/coding/agentic/reasoning/speed; free endpoint /v2/language/models/free), models.dev (ctx/maxout/toolcall/reasoning/cache/multimodal/pricing/dates), PinchBench (agentic %), llm-stats.com coding arena (TrueSkill, SWE-Bench/LiveCodeBench/Terminal-Bench/Aider), LMArena ELO (EXT) -> MODEL_ARCHITECTURE.md:74-99,840-855; AAA model-scan algorithm construction.md:1-17,151-301
- Detailed benchmark fields: gpqa_diamond/hle/ifbench/aa_lcr/gdpval/critpt/scicode/terminal_bench/omniscience (PROP) -> PRD- proxy model scraper helper.md:139-163
- Performance fields: throughput_tps, latency_seconds, e2e_latency, tool_error_rate, uptime_percent (PROP) -> PRD- proxy model scraper helper.md:130-138
- Leaderboards smartest/coding/free/value; value_score=intelligence/price (free excluded, div-by-zero) (PROP) -> PRD- MAUG.md:409-418; PRD- proxy model scraper helper.md:165-186
- Provider inventory (OpenRouter, OpenCode Zen, OpenCode Go, Ollama Cloud, NVIDIA NIM, Groq, Cerebras): endpoints/keys/models (CUR) -> MODEL_ARCHITECTURE.md:112-247; AAA model-scan algorithm construction.md:28-144
- Static tier registry tiers.yaml (S/A/B/C/D/Ungraded, monthly review) = quality floor + blocklist.yaml (PROP/HARD) -> Structural Assessment...md:65,85,136-143
- Model onboarding pipeline: startup key-scan -> LLM structured-output classify -> provisional role -> telemetry reconcile/downgrade + similar-models heuristic (PROP) -> PRD- MAUG.md:460-471; Proxy update plan.md:27,47
- 5-tier model system (T1 Reasoning/T2 -Claw/T3 Workhorse/T4 Specialist/T5 Baseline + Boneyard) (CUR) -> MODEL_ARCHITECTURE.md:351-407
- gpt-oss-120b baseline filter; -claw class (IQ40+ AND speed85+) (CUR) -> MODEL_ARCHITECTURE.md:297-331
- Rejected-models rationale (15 entries) + reserved candidates (CUR) -> MODEL_ARCHITECTURE.md:659-803
- ORMS HARD reqs: sync<30s, deep<60min/300, >=95% benchmark completeness, <=24h freshness, <1% block, +-10% token accuracy, atomic writes, no persisted creds, API-only graceful fallback -> PRD- proxy model scraper helper.md:210-241; PRD- MAUG.md:817-847
- Scoring algorithm (multi-axis, top-model calibrate=100, speed<->agentic quadratic equivalence) (PROP) -> AAA model-scan algorithm construction.md:1-17
- See F04 for how scores feed selection; F07 for token-economics ($/M) variant.

## F04. ROUTING & MODEL SELECTION ENGINE

- Routing engine built (not embedded): Classifier->Role-Resolver->KeyLedger->LiteLLM-Router dispatch (PROP) -> PRD- MAUG.md:240-264,1017-1021
- Intent classifier 4 dims (complexity/task/vision/tool); rule-based v1, ONNX phase D; ~80% optimization claim (PROP) -> PRD- MAUG.md:250-255,1423-1450; Proxy update plan.md:478-489,615-632
- Role-constraint resolver: YAML hard/soft constraints + overrides (e.g. free + tool_calling + dense>30B / MoE>60B@8B); arbitrary user trait tags ("good thinkers") (PROP/HARD) -> PRD- MAUG.md:265-287,1446-1450; Proxy update plan.md:45-47
- Role->Tier mapping for 14 Hermes roles + per-role rationale (CUR) -> MODEL_ARCHITECTURE.md:415-478
- Task-based substitutions toggleable (tool calls / large ctx) + new roles without middleware code (PROP/HARD) -> unified_project_idea_record.md:64-89
- No hardcoded model-name routing rules (HARD) -> unified_project_idea_record.md:46,468
- Slot eligibility hard gates: min_tier/needs_tools/needs_vision/min_ctx/max_latency (PROP/HARD) -> Structural Assessment...md:67,140
- Fitness scoring formula: tier-anchor * AA * reliability * latency-consistency * hourly-availability + arch bonus (PROP) -> Structural Assessment...md:75
- Recommendation logic: ranked eligible, delta-vs-incumbent, swap only if +5 fitness (PROP) -> Structural Assessment...md:77
- Per-CLI Routing Profiles (profiles.json) + provider_override + toolcall_models + use-case routers (CUR, merged) -> new proxy commands.md:40-49
- Tier model map BIG/MIDDLE/SMALL (opus/sonnet/haiku -> mapped models) (CUR) -> claude cody proxy .env.md:608-627

## F05. ROTATION, RELIABILITY & FALLBACK

- Rotation triggers (HERMES_REFINEMENT 7-type: calendar/new-model/error/latency/availability/quality/credit, priority T7>T5>...) vs (Hermes Rotation 5-type 14d/new/deprecation/error/manual) -> HERMES_REFINEMENT_SPECIFICATION.md:26-39; Hermes Model Rotation...md:116-125  [RESOLVE: pick one]
- Demotion/promotion criteria (>5% err/n>=50 demote; <1-2% err/n>=100 promote; 3 demotions/7d -> boneyard) -> HERMES_REFINEMENT_SPECIFICATION.md:41-69; Hermes Model Rotation...md:126-149
- Pre-insertion test protocol (curl+toolcall+baseline+speed+diversity, MUST PASS ALL; reject if < gpt-oss-120b composite 30.2) (HARD) -> HERMES_REFINEMENT_SPECIFICATION.md:82-152
- Reliability SQLite schema reliability.db (model_calls + model_health, 90d, JSONL fallback, 15-min views) at ~/.hermes/ (PROP/HARD) -> HERMES_REFINEMENT_SPECIFICATION.md:155-213; Hermes Model Rotation...md:198-241
- Min sample sizes 30/50/100/200 calls gate actions (PROP) -> Hermes Model Rotation...md:232-241
- Circuit breaker CLOSED/OPEN/HALF-OPEN, trip 5 fails/10min, cooldown 10->120min exp backoff (PROP) -> HERMES_REFINEMENT_SPECIFICATION.md:324-385; Hermes Model Rotation...md:289-302
- NOTE: LiteLLM allowed_fails is failure-budget not true half-open; needs custom wrapper (Gap1) -> PRD- MAUG.md:1827,1914-1920
- 5-stage fallback cascade: retry/backoff -> strip fields -> reduce tools -> next provider -> degrade text-only (PROP) -> PRD- MAUG.md:256-262,1405-1421; Proxy update plan.md:203-218
- Per-role fallback chains (3-4 deep, same-model-diff-provider F1, end with main 15-entry global) (CUR) -> MODEL_ARCHITECTURE.md:481-611; HERMES_REFINEMENT_SPECIFICATION.md:914-1092
- Provider-wide fast-skip on 429/503; malformed tool_call skip (PROP) -> Hermes Model Rotation...md:283-288
- CRITICAL broken fallback: hermes-3-405b:free returns provider errors, replace (CUR bug) -> Hermes Optimal Model Settings - Audit Report.md:51-59
- Emergency override `hermes config emergency-mode` -> all roles gpt-oss-120b (PROP) -> HERMES_REFINEMENT_SPECIFICATION.md:1096-1151
- Feedback loop: recommendations.json, human-approved apply, NEVER auto-edit config.yaml (HARD) -> HERMES_REFINEMENT_SPECIFICATION.md:237-269; Hermes Model Rotation...md:253-266

## F06. QUOTA, KEY & SUBSCRIPTION MANAGEMENT

- 3 quota access patterns: A headers / B REST poll / C local-scrape, mapped across 11 providers (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:44-54
- Per-provider quota methods: Claude Code x-ratelimit headers (ignore JSONL, undercounts 100-174x), Codex/OpenAI headers, Antigravity Connect-RPC GetUserStatus (dynamic port+CSRF from /proc, 5h window), OpenCode Go SQLite read, OpenCode Zen file read, NVIDIA NIM sliding-window (~40 RPM, 429-only), Cerebras headers, Groq headers, Kilo REST, OpenRouter GET /api/v1/auth/key (1000/day funded), Ollama HTML scrape /settings -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:60-373
- Adapter interface get_quota/get_health/on_response/on_request (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:521-528
- 4-tier integration priority (Tier1 header-passthrough trivial -> Tier4 complex) (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:530-557
- Key Ledger (Redis per-key: temporal/token/request dims; status active/throttled/dead/suspended) (PROP) -> PRD- MAUG.md:308-340,1033-1037
- Quota Discriminator: real-quota vs overload vs invalid-key via probe pipeline + error matrix 429/401/422/503 (PROP/HARD >95% accuracy) -> PRD- MAUG.md:288-307,1956-1966
- Key rotation cadence + `maug rotate-keys`; secrets env-only never disk (HARD) -> PRD- MAUG.md:814,1129,1737
- Rotation logic: filter cooldown -> rank by remaining -> tiebreak reset window -> cascade (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:559-568
- Key rotation proxy refs (LLM-API-Key-Proxy/gpt-load/LiteLLM credential_balancer) (EXT) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:398-433
- Provider budget specifics: NVIDIA NIM credits (100k tokens or 1000 credits CONFLICT, 80% auto-remove), OC Go spend ($0.50 vs $2/$5/$10/$20 CONFLICT), Ollama free-tier-change weekly probe 402->boneyard -> HERMES_REFINEMENT_SPECIFICATION.md:391-459; Hermes Model Rotation...md:308-329  [RESOLVE conflicts]
- Time-aware quota windows (Groq 00:00 UTC, Ollama 3h, Cerebras off-peak) -> availability multiplier (PROP) -> Structural Assessment...md:73; HERMES_REFINEMENT_SPECIFICATION.md:485-520
- OpenRouter free reality: 50/day unfunded, 1000/day funded, 20 RPM, failed attempts count (EXT) -> PRD- MAUG.md:317-322
- Current usage tracking: TRACK_USAGE SQLite usage_tracking.db, profile column (CUR) -> claude cody proxy .env.md:779-785; new proxy commands.md:31-33

## F07. COST MANAGEMENT & FREE/PAID CONSTRAINTS

- Per-role free OR paid constraint (each model role independently constrained); optimal "free" preset; plan-model-paid + aux-all-free preset (PROP/HARD; core user ask) -> unified_project_idea_record.md:37-48,64-89; Proxy update plan.md:15,45
- Budget enforcement daily/hourly/per-request ceilings; refuse if projected > remaining (PROP) -> PRD- MAUG.md:342-347,1043-1045; Proxy update plan.md:686,2543-2546
- Token-economics ranking ($/M quality-adjusted, AA v4.0 anchor GPT-5.5=60=100%) (PROP) -> Model-scan features.md:4-15; Query for best model plan.md:2
- Subscription multiplier framework (5x $20/$100, 10x only top unlimited; "20x tokens != 20x value" footgun) (PROP) -> Model-scan features.md:17-22; Query for best model plan.md:9-18
- Workload blended ratios (conversational 58/42, tool-call 75/25, reasoning 3x output, cache 80% hit) (PROP) -> Model-scan features.md:23-33
- value_score = intelligence/cost (free excluded) (PROP) -> PRD- proxy model scraper helper.md:183-186
- Cost-intelligence: input/output/cached/retry breakdown per team/project, TCO compare (PROP) -> Proxy update plan.md:517-522,660-688
- Token-level cost tracking +-10% accuracy (HARD) -> PRD- proxy model scraper helper.md:467-479
- Budget constraint (user is budget-limited, free models only for testing, OpenRouter key global) (CUR constraint) -> unified_project_idea_record.md:408-413
- OC Go $/mo spend monitoring -> switch to free (CUR intent) -> Hermes Model Rotation...md:317-323

## F08. COMPRESSION & CACHING LAYER

- Headroom = input/prompt compression 70-90% (CUR; at /home/cheta/code/input-compression/, port 8787 authoritative vs 8001 in superseded draft) -> unified_project_idea_record.md:94-101; Optimal compression...md:78-83,250-261; PRD- MAUG.md:477-503
- RTK = shell/terminal-output compression via CLI hooks (CUR; "retk" in user goal == RTK) -> unified_project_idea_record.md:102-106; Optimal compression...md:84-88
- Kompressor = Headroom's model-weight compression (quantization/sparsification), real and
  orthogonal to context compression (user correction) -> Optimal compression...md:78-82
- hermes-lcm = context engine (DAG+SQLite+lineage, lossless originals, 7 recovery tools); primary context layer (PROP) -> Optimal compression...md:52-62,180-208
- pi-context-prune = tool-output pruner (alt; cache-aware batch boundary) (PROP) -> Optimal compression...md:64-71,196-228
- HARD: do NOT layer pi-prune on hermes-lcm (breaks losslessness); use one (HARD) -> Optimal compression...md:233-247,300
- Request-path order: RTK(transport) -> Headroom(input) -> context engine; RTK+Headroom always on, cache-transparent (PROP/HARD) -> Optimal compression...md:239-247,265-296
- Cache tradeoff: write-time selection > post-hoc eviction; reprocess cost linear w/ context; lower threshold 0.35 (PROP) -> Optimal compression...md:14-21,130-138,210-228
- HARD: cross-model prompt caches NOT shared (each model pays own prefill); routing must not assume warm cache across switches -> Optimal compression...md:159 (free-model tool turns caveat)
- HARD: hermes-lcm has no provider/model TTL heuristics / no cache-break tracking; gateway is natural place to expose cache-state signals -> Optimal compression...md:182-190
- Cache-aware pre-tokenization / header-footer detection / semantic+exact match cache (PROP) -> Proxy update plan.md:42-43,2419-2423
- RTK stats currently missing from terminal display (CUR gap) -> unified_project_idea_record.md:102-106,433-439
- hermes-lcm tuning env: LCM_CONTEXT_THRESHOLD=0.35, FRESH_TAIL=64, LEAF_CHUNK=20000, dynamic leaf chunk on, externalize @12000 chars (PROP) -> Optimal compression...md:284-296

## F09. MEMORY INTEGRATION & HOOKS EMULATION

- Bespoke memory system at /code/wiki-memory, integrate via content-injection + storage "hooks" (PROP/HARD; user core ask) -> [user prompt] + Proxy update plan.md:12,2448-2451
- Memory injection pre-routing hook (Mem0/ByteRover/Graphiti via MCP; facts prepended w/ metadata + display marker) (PROP) -> PRD- MAUG.md:505-509,1511-1516; Proxy update plan.md:2448-2451,2660
- Hooks emulation: provide Claude-Code hook features to CLIs lacking them (this is the memory integration method) (PROP/HARD; user core ask) -> [user prompt] + Proxy update plan.md:44-45
- Claude Code hook reference (TeammateIdle/TaskCompleted exit-code-2 pattern) (EXT) -> Claude Code Backend Middleware...md:804-810
- Control MCP server (built, streamable HTTP, mandatory auth): switch_provider/model, set_role, get_routing_stats, open/close_circuit, set_budget_limit, list/set_active_chain, pause_provider (PROP) -> PRD- MAUG.md:519-539,1085-1087
- Memory metadata used for cache hits + compression coordination (PROP) -> Proxy update plan.md:34,2448-2451
- Custom statusline injection as a hook-like content surface (CUR, off) -> claude cody proxy .env.md:817-835
- DAG source-lineage tracking; large-payload externalization at ingest (PROP) -> Optimal compression...md:159,201,291-292

## F10. MULTI-SESSION ORCHESTRATION & HOST SENTINEL

- Concurrent multi-harness serving (many agents/sessions, not many users); single-process asyncio (PROP/HARD; user core ask) -> PRD- MAUG.md:790-804,907,1135; Proxy update plan.md:56
- Host resource monitoring + arbitration (cpu/ram/temp baselining; graduated log/alert/notify/kill offending procs vs baseline) (PROP) -> Proxy update plan.md:56; PRD- MAUG.md:643-657,1115-1117
- Global rate limiter across Hermes child processes (file/Redis; 6 concurrent children vs OR 20 RPM) (PROP) -> Hermes Model Rotation...md:524; HERMES_REFINEMENT_SPECIFICATION.md:485-520
- Multi-machine awareness workers.yaml (per-worker model availability, route delegation) (PROP) -> Structural Assessment...md:87
- Crosstalk model-to-model (memory/report/relay/debate paradigms, iterations, model list) (CUR, commented) -> claude cody proxy .env.md:853-871
- Claude Code Agent Teams TeammateTool / Task / spawn backends (tmux/iterm2/in-process) (EXT) -> Claude Code Backend Middleware...md:741-810
- Deployment topology / process table (gateway, LiteLLM ctr, ORMS, Headroom, Redis, TUI, CLIProxyAPI; independent restart) (PROP) -> PRD- MAUG.md:792-803,1131-1135
- Hybrid routing architectures per usage profile (light 5M/moderate 15M/power 50M/heavy 500M tokens/mo) (PROP) -> Model-scan features.md:100-107

## F11. OBSERVABILITY, METRICS & LOGGING

- Structured JSONL logs full schema (request_id, routing_decision, costs, translation_delta, quota_discriminator, chain manifest) (PROP) -> PRD- MAUG.md:545-585,1462-1492
- translation_delta truncation attribution (canonical-vs-translated max_tokens -> provider vs settings) (PROP) -> PRD- MAUG.md:570-576
- OpenTelemetry spans (schema.transform, tool.reassembly, fallback.triggered; fields_dropped/coerced) (PROP) -> Proxy update plan.md:243-250; PRD- MAUG.md:587-591
- Prometheus metrics clutch_quota_* gauges/counters, labels provider/model/key_id (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:437-468
- Grafana dashboard (quota bars/key health/req rate/429 alert/rotation log, green<70/yellow/red>90) (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:470-478
- Role-based logging + analytics, sort by model OR task (tokens in/out per model/date, tool success, web routing, role failures) (PROP) -> unified_project_idea_record.md:133-160
- Historical-failure ingestion: parse agent.log+proxy logs nightly -> historical_failures.json -> feed selection (PROP; current scan ignores this) -> Structural Assessment...md:27-34,92-98
- Per-model role/task performance tracking time-series w/ ORMS-change annotations + cohort drift (PROP) -> PRD- MAUG.md:593-602
- Current terminal metrics: workspace/context_pct/task_type/speed/cost/duration colors; LOG_STYLE rich/plain/compact (CUR) -> claude cody proxy .env.md:719-751
- Accuracy caveats: JSONL undercount, NIM drift, scrape fragility, Antigravity rediscovery (PROP) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:482-516

## F12. CONFIGURATION SYSTEM & INTERFACE PARITY + DYNAMIC CONFIG GEN

- Single config source-of-truth; CLI/.env base layer wrapped identically by TUI + Web UI; FULL feature parity (HARD; user core ask) -> unified_project_idea_record.md:199-242,441-465
- One .env (not .envrc); CLI args override env temporarily (PROP) -> unified_project_idea_record.md:201,382-388
- gateway.yaml full schema (gateway/routing/providers/roles/compression/observability/orms/host_sentinel/control_mcp) (PROP) -> PRD- MAUG.md:685-762,1677-1735
- Dynamic config GENERATION for client CLIs: produce hermes config.yaml optimal role->model selections, regenerate as quota nears limits -> switch to next-best (PROP/HARD; user core ask) -> unified_project_idea_record.md:64-89; HERMES_REFINEMENT_SPECIFICATION.md:819-912
- recommendations.json + `hermes config apply-recommendations` (human gate), edits config.yaml preserving comments, keep last 5 .bak, config_version + config.schema.yaml validation (HARD) -> HERMES_REFINEMENT_SPECIFICATION.md:237-269; Hermes Model Rotation...md:253-266,522-523
- Config file set: tiers.yaml (canonical weights), slot_definitions (min_tier/needs_tools/needs_vision/min_ctx, remove min_ai), blocklist.yaml, workers.yaml, provider_windows.yaml (PROP) -> Structural Assessment...md:136-145,92-98
- Per-model system prompt override files + custom headers pattern CUSTOM_HEADER_<NAME> (CUR) -> claude cody proxy .env.md:923-967
- Namespaced provider registry PROVIDERS_<name>_URL/_API_KEY migrating from flat keys (CUR, in progress) -> new proxy commands.md:47
- Secrets env-only, resolved at startup by name, never persisted (HARD) -> PRD- MAUG.md:764-786,1737-1755

## F13. CLI INTERFACE & LAUNCH ALIASES (ORDERED COMPOSITOR)

- `cc [R][M][S][C][O]` positional single-char grammar (position encodes route/model/session/context/output) (PROP) -> Ordered Compositor...md:165-235
- Route slot = gateway path (f=full-stack headroom+RTK / h=headroom / d=direct / p=proxy / b=bypass) (PROP/KEY) -> Ordered Compositor...md:217,247-254
- Auto-route probing (localhost:8787 headroom + 8082 proxy, 1s timeout, fallback direct+warn) + idempotent proxy-stack auto-start (PROP/HARD; defines port topology) -> Ordered Compositor...md:247-260,522-535
- Cross-tool consistency cc/qw/cdx/oc (same grammar, model alphabet differs) (PROP) -> Ordered Compositor...md:284-287
- Persistent session reuse cc + / cc - / --repeat (XDG state); context auto-detect CLAUDE.md/AGENTS.md/.ccrc (PROP) -> Ordered Compositor...md:316,584-595,95-105
- Extended mode ccx slash/named flags (PROP) -> Ordered Compositor...md:277-283,681-695
- LEAN revision: collapse to 3 slots, drop fuzzy/cache/counter (DECISION pending) -> Ordered Compositor...md:637-804  [RESOLVE: 5-slot vs 3-slot]
- maug CLI commands: start/stop/status/logs/rotate-keys/roles/chains; orms run[--force]; probe (PROP) -> PRD- MAUG.md:624-637
- Current crosstalk CLI `python -m src.cli.crosstalk_cli` (CUR) -> claude cody proxy .env.md:847
- Current `proxies profile list|show|validate` (CUR) -> new proxy commands.md:8-29
- Single-command alias installer (proxy on/off, +-compression, dual continue cproxy-continue/claude-continue) (PROP) -> unified_project_idea_record.md:256-300
- Installer sets up all proxies on new machine (Headroom/RTK default-on, CLIProxyAPI opt-in) (PROP) -> unified_project_idea_record.md:279-289,514

## F14. TUI WIZARD

- Textual TUI primary interface; live view + drill-downs (cohort/ledger/chain/discriminator) (PROP) -> PRD- MAUG.md:604-622,1759-1775
- Arrow-key TUI for all settings (proxies/models/providers), parity w/ CLI (PROP/HARD) -> unified_project_idea_record.md:222-230
- Status-bar builder TUI w/ real-time preview (renames "prompt injection"); writes .claude statusline file; works for other CLIs same format (PROP) -> unified_project_idea_record.md:182-194
- TUI manages routing/chains/config (drag-drop chain reorder concept) (PROP) -> Proxy update plan.md:26,30,32,38
- Daily-mode terminal output redesign (5-sec scannable: header/incumbent panel/top-3 per slot/--appendix) (PROP) -> Structural Assessment...md:112-134

## F15. WEB UX & DASHBOARD

- Web UI: dashboard + analytics + drag-drop proxy reorder (ref claude-code-swap) (PROP/HARD; user core ask) -> unified_project_idea_record.md:232-242
- Live dashboard for API-call fails associated with model/role/provider (improve future selection) (PROP/HARD; user core ask) -> [user prompt] + unified_project_idea_record.md:133-160
- Prometheus + Grafana prominent inclusion (HARD; user core ask) -> Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:437-478; Proxy update plan.md:26,2438,2675
- Optional Web UI = LiteLLM admin container (historical analytics, not reimplemented) (PROP) -> PRD- MAUG.md:639-641,1767
- Current Web UI /settings Routing Profiles section + REST /api/routing-profiles (CUR) -> new proxy commands.md:5-6,14-15
- Current terminal dashboard ENABLE_DASHBOARD/layout/refresh/modules (CUR, off) -> claude cody proxy .env.md:791-803
- FUTURE (only approved deferral): take web UX out of browser -> standalone -> [user prompt]

## F16. TERMINAL COLOR & STATUS SYSTEM

- TUIDS-LLM v1.0 semantic color role map (9 roles) + luminance tiers + 4-hue ceiling + 60-30-10 ratio (PROP) -> Terminal Color System.md:1-35,204-279
- HARD: content sanctity (zero ANSI on model output), glyph-per-color redundancy, ANSI injection sanitization, NO_COLOR/pipe parity, belt-and-suspenders dim -> Terminal Color System.md:38-47,116-131,166,363-368,588-621
- Motion/animation layer (spinner/pulse/progress/stream-indicator), --no-motion strips (PROP) -> Terminal Color System.md:50-58,432-476
- Output map for request/response/content/error/concurrent blocks (rid hex prefix) (PROP) -> Terminal Color System.md:59-91,226-258
- Palette progressive enhancement ANSI-16->256->truecolor (Nord-derived) (PROP) -> Terminal Color System.md:92-113,562-572
- Config precedence CLI>env>file>defaults (NO_COLOR/CLICOLOR/PROXY_COLOR/COLORTERM); proxy-color.yml; --format=json bypass (PROP) -> Terminal Color System.md:122-131,281-306
- Static color status bars (Headroom top / Proxy bottom / RTK third; no layout shift; tokens-saved/t-s/last-error) (PROP) -> unified_project_idea_record.md:107-130,162-180
- Claude Code statusline integration (pipe proxy stats, working/fault per layer) (PROP) -> unified_project_idea_record.md:166-171,504
- Current terminal color env: TERMINAL_COLOR_SCHEME/SESSION_COLORS/DISPLAY_MODE (CUR) -> claude cody proxy .env.md:713-737
- NOTE possible_dup: 3 overlapping palette tables in Terminal Color System.md (L189-202/376-384/816-826) consolidate

## F17. WEB BROWSER MULTI-MODEL AGGREGATOR (lowest maturity, still in-scope)

- Chrome ext + local site: query distributor (fan to multiple LLM web UIs, auto-submit) (PROP) -> web browser plugin...md:2
- Result scraper (DOM copy per tab) + aggregator step (API to known-good model, structured output) (PROP) -> web browser plugin...md:2
- Workflow primitives loop/branch/sequence/transform/judge; atom/molecule/element composition (PROP) -> web browser plugin...md:4
- Open: difficulty? already-exists? vs n8n/Zapier (research) -> web browser plugin...md:7-21

---

## CROSS-CUTTING DECISIONS & CONTRADICTIONS TO RESOLVE (for the v2 conversation)

1. LiteLLM role: Docker-container-only (security, Mar-2026 supply-chain compromise) is AUTHORITATIVE; ignore embed/pip C-draft. Use as Router/infra, never import. -> PRD- MAUG.md:234-238,947,1019
2. Build-vs-buy taxonomy: Embed / Invoke(Delegate) / Build / Fork. Glue-architecture: orchestrate ~4-5 core projects (LiteLLM, Headroom, ORMS, CLIProxyAPI) via HTTP/MCP/callbacks. -> PRD- MAUG.md:30-39,840-866; Proxy update plan.md:2997-3085
3. resillm = Delegate only (no library); likely replace with LiteLLM Router. -> Proxy update plan.md:3073-3084
4. Two scoring systems NOT unified: free-tier fitness (Hermes) vs $/M token-economics (Model-scan). Decide unify vs keep parallel. -> see F03/F04/F07
5. gpt-oss-120b baseline: any-one-of definition vs composite-30.2 formula CONFLICT. -> Hermes Model Rotation...md:168-192 vs HERMES_REFINEMENT_SPECIFICATION.md:101-152
6. Rotation triggers: 5-type vs 7-type. Provider budget numbers (NVIDIA, OC Go) conflict across docs.
7. Headroom port 8787 (authoritative) vs 8001 (superseded). Placement: proxy-before-MAUG (authoritative) vs inline middleware.
8. Ordered Compositor: 5-slot "A+" vs 3-slot "lean". -> Ordered Compositor...md
9. Memory backend: user's /code/wiki-memory is canonical (not Mem0/ByteRover/Graphiti, which are doc examples). Confirm injection/storage hook contract.
10. Phase notation: use Phases A-E (not week-numbers); some superseded drafts use weeks.
11. Roadmap conflict: PRD-MAUG 12-week vs phase-based; honor phase-based per standing instruction.
12. "retk" (user) == "RTK" (docs). "Kompressor" = Headroom's model-weight compression (real, per
    user correction), not a missing component.
