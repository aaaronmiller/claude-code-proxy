---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, recon, quota, rotation, allocator, s1-06, s1-08, read-only]
---

# Recon 02: Quota / rotation / capability substrate (S1-06 + S1-08 prep, read-only)

Read-only inspection of `/home/cheta/code/claude-code-proxy`. Key result: the F06 quota and F18
allocator substrate ALREADY EXISTS in the proxy. The new work is EXTEND, not build-new. This
re-scopes F06/F18 downward.

## What already exists

### Quota (F06 substrate) - `src/core/quota_sources.py`
- `QuotaSample` dataclass (`:16`), `QuotaSource` Protocol with `samples()` (`:25`).
- Adapters present: `TokscaleSQLiteSource` (`:42`), `CcusageSource` (`:67`), `StaticQuotaSource`
  (`:89`); `merge_quota_samples()` with precedence (`:108`).
- GAP vs plan: `QuotaSample` is single-dimensional (provider, remaining, source). The
  multi-meter model (per-window + per-model + unit: calls/tokens/credits/dollars/search) from
  `04-DATA-CONTRACTS.md` is NOT there yet.
- S1-06 = EXTEND: generalize `QuotaSample` -> `QuotaMeter` (multi-dimensional), add the
  header/poll/scrape provider adapters implementing the existing `QuotaSource` Protocol, reuse
  `merge_quota_samples`. Do not introduce a parallel system.

### Rotation (F18 runtime executor) - `src/core/rotation.py`
- `RotationState` (`:14`), `provider_drained(quotas, threshold)` (`:28`), `choose_binding(...)`
  (`:33`), `record_rate_limit(cooldown_s)` (`:62`).
- This is the per-request, greedy, quota-aware rotation (drain threshold + cooldown) already
  matching specs/003. It is NOT a global optimizer.
- F18 = NEW LAYER ABOVE this: the LP produces per-session-role cascades; `choose_binding` becomes
  the runtime executor of that plan (token-bucket semantics). Do not rebuild rotation; the
  allocator feeds it better candidate orderings + caps.

### Snapshot binding (S1-08 target) - `src/core/model_scan_runtime.py`
- `_load_snapshot()` (`:64`), `_binding_to_assignment_updates()` (`:80`),
  `reload_model_scan()` (`:110`), profile bindings + lanes (`:41-60`),
  `resolve_profile_binding()` (`:32`). Plus `src/core/assignments.py` (AssignmentRegistry) and
  `src/services/models/model_scan_snapshot.py`.
- S1-08 = the allocator emits an augmented snapshot; this path already loads + binds it. Wire the
  allocator output as a snapshot post-processor before `reload_model_scan`.

### Capability registry (F03) - `src/services/usage/model_limits.py`
- models.dev-backed: `get_model_limits`, `get_model_info`, `supports_tool_call`,
  `supports_vision`, `supports_reasoning`, `supports_pdf`, `supports_audio_*`, `get_pricing`,
  `get_context_limit`, `get_output_limit`. Loads models.dev (`_load_models_dev`) + OpenRouter
  cache + legacy fallback.
- This IS the capability registry F03 wants. RECON-01 fix is now trivial: replace
  `model_router.py:170` name-prefix tool check with `model_limits.supports_tool_call(model)`.

### Also present
- `src/core/proxy_chain.py`, `src/core/assignments.py`, `src/services/usage/{usage_tracker,
  rate_limiter,cost_calculator,model_limits}.py`, `src/services/billing/billing_integrations.py`,
  `src/api/billing.py`.

## Re-scoped sprint-1 implications
- S1-03 fix: one-line swap to `model_limits.supports_tool_call()` (registry exists).
- S1-06: extend `quota_sources.py` (QuotaSample -> multi-meter QuotaMeter + provider adapters),
  not a new `src/services/quota/` package as the ticket assumed. Update the ticket file path.
- S1-07/F18: the LP is the only genuinely new piece; it sits above `rotation.choose_binding` and
  emits through `model_scan_runtime`. Existing `provider_drained`/`record_rate_limit` give the
  enforcement primitives.
- Net: F06 and F18 are smaller than `01-CURRENT-STATE` rated them. F06 PARTIAL -> mostly-present
  substrate + adapters; F18 NEW but thin (LP layer only).

No files changed. Edits gated on DECISIONS.md O2 (repo strategy).
