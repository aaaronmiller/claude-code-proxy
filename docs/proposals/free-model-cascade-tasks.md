# Implementation Task List: Free-Model Smart Selection + Quota-Aware Cascade

## 1. Wire cascade into runtime
- [ ] 1.1 Route non-streaming Claude endpoint through `create_chat_completion_with_cascade`
- [ ] 1.2 Route streaming path through cascade-capable wrapper (or explicit fallback policy)
- [ ] 1.3 Add tier inference helper (`big|middle|small`) for all request flows
- [ ] 1.4 Add tests proving `MODEL_CASCADE=true` changes behavior on 429/5xx

## 2. Add quota/error classification and cooldown
- [ ] 2.1 Implement centralized error classifier for free-limit/rate-limit/transient failures
- [ ] 2.2 Add per-model cooldown state and hop budget (`CASCADE_MAX_HOPS`)
- [ ] 2.3 Persist cascade events with reason codes for analytics/dashboard
- [ ] 2.4 Add tests for cooldown and exhaustion behavior

## 3. Build deterministic free-model ranking pipeline
- [ ] 3.1 Create `FreeModelScorer` module using OpenRouter cached metadata
- [ ] 3.2 Implement stealth vs evergreen classification (`STEALTH_WINDOW_DAYS`)
- [ ] 3.3 Add health-informed ranking using usage/error telemetry
- [ ] 3.4 Save ranked catalog artifact in `data/` with generation timestamp
- [ ] 3.5 Add unit tests for scoring weights and tie-break rules

## 4. Integrate optional LLM+Exa reranking
- [ ] 4.1 Add strict structured-output schema for reranker output
- [ ] 4.2 Rerank top-K candidates and blend with deterministic scores
- [ ] 4.3 Add resilient fallback to deterministic-only mode on rerank failure
- [ ] 4.4 Add tests for schema validation and blend logic

## 5. Extend data persistence for daily UTC tracking
- [ ] 5.1 Add table(s) for per-model daily request/error counters keyed by UTC date
- [ ] 5.2 Add ingestion hooks in request-completion paths
- [ ] 5.3 Add query helpers for quota warning thresholds and reset display
- [ ] 5.4 Add migration and DB-level tests

## 6. Expose API surfaces for ranked free models and quota status
- [ ] 6.1 Add `GET /api/models/free/recommended`
- [ ] 6.2 Add `GET /api/models/free/quota-status`
- [ ] 6.3 Add `POST /api/models/free/rebuild-rankings`
- [ ] 6.4 Add endpoint tests and response schema checks

## 7. Upgrade TUI model selector for free-tier workflow
- [ ] 7.1 Add view mode `recommended-free` and keep `all` as explicit toggle
- [ ] 7.2 Add model badges (`STEALTH`, `EVERGREEN`, `COOLDOWN`, `HOT`)
- [ ] 7.3 Add quota status strip with UTC reset note
- [ ] 7.4 Add keyboard command help updates and snapshot tests

## 8. Configuration and docs
- [ ] 8.1 Add new env vars to `config/env.example` with safe defaults
- [ ] 8.2 Add troubleshooting guide for 429 free-limit cascades
- [ ] 8.3 Add operator docs for ranking refresh cadence and override knobs
- [ ] 8.4 Add release notes describing behavior changes and migration path

## 9. Hardening and rollout
- [ ] 9.1 Add feature flags for staged rollout (`ENABLE_SMART_FREE_RANKING`, `CASCADE_ON_FREE_LIMIT`)
- [ ] 9.2 Add observability dashboard cards for cascade success rate and quota pressure
- [ ] 9.3 Perform load/regression test pass on high-concurrency retry scenarios
- [ ] 9.4 Define rollback switch and runbook

## Suggested Execution Order
1. Task group 1 (runtime wiring)
2. Task group 2 (error classifier + cooldown)
3. Task group 5 (daily UTC persistence)
4. Task groups 3 + 4 (ranking + reranking)
5. Task groups 6 + 7 (API + TUI)
6. Task groups 8 + 9 (docs + rollout)

