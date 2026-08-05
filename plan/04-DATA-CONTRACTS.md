---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, data-contracts, quota-meter, allocator, lp, schema, f06, f18]
---

# Data Contracts: Quota Meters and the Global Allocator

Concrete, codeable schemas for the new core (F06 quota meters + F18 allocator). Designed to be
ADDITIVE to what exists: the existing `routing_snapshot.json` (model-scan) and the specs/001
`Assignment` record. Types shown as Python dataclass-style; equivalent Pydantic v2 in code.

## 1. Existing shapes we align to (do not break)

- routing_snapshot.json (model-scan producer): `{schema_version, generated_at, provider_health,
  blocklist[], provider_quota{prov:{remaining_fraction, reset_at, unit, source}},
  slots{slot_id:{label, eval_mode, best, candidates[{model_id, provider, api_model, base_url,
  fitness, price_blended, tier, has_tools, has_vision}]}}}`.
- specs/001 Assignment: `{id, kind: tier|slot, model, provider, base_url, api_key, enabled,
  cascade[]}`.
- model-scan QuotaSample: `{provider, remaining_fraction, reset_at, unit, source}`.

F06 generalizes QuotaSample to multi-meter. F18 output maps onto snapshot `candidates` /
Assignment `cascade`.

## 2. F06 quota-meter contract

```
QuotaMeter:                      # one constraint; a provider/model may have several
  id: str                        # "groq:calls:24h:per_model:<model>", "antigravity:tokens:5h"
  scope: "provider" | "provider_model" | "key"
  provider: str
  model: str | None              # set when scope=provider_model
  key_id: str | None             # set when scope=key
  unit: "calls" | "tokens" | "credits" | "dollars" | "search_calls"
  window_seconds: int            # 18000=5h, 86400=day, 604800=week, 2592000=month
  limit: float
  remaining: float               # live
  reset_at: iso8601 | None
  source: "header" | "poll" | "scrape" | "ledger" | "estimate"

QuotaAdapter (ABC, one per provider):
  get_meters() -> list[QuotaMeter]                 # current live meters
  cost(model, est_tokens) -> dict[meter_id, float] # debit per meter for one call
  on_request(model, est_tokens) -> None            # reserve in local ledger
  on_response(model, usage) -> None                # reconcile actual
  get_health() -> "ok" | "degraded" | "down"
```

Adapter implementations map to the F06 provider table (Tier-1 header: Claude/Codex/Cerebras/Groq;
poll: OpenRouter `/api/v1/auth/key`; scrape: Ollama/Antigravity). Local ledger persists across
restart (counters, not just live reads). Token-bucket per meter enforces in real time.

Normalization for the LP: window < 1 day -> rate constraint (budget per window). window > 1 day ->
daily slice = limit * 86400 / window_seconds, but the true-window ledger still hard-caps so a
month cannot be exhausted in week 1.

## 3. F18 allocator input contract

```
RoleSpec:
  session_id: str
  role_id: str                   # "primary","delegation","toolcall","aux:title", ...
  floor:                         # hard gates; candidate excluded if any fail
    min_tier: "S"|"A"|"B"|"C"|None
    needs_tools: bool
    needs_vision: bool
    min_ctx: int
    min_value: float             # e.g. "must beat gpt-oss-120b" -> its fitness
  value_sensitivity: float       # w_r; 0=satisfice (flat above floor), high=maximize
  diversity_cap: float           # max share from one provider (e.g. 0.6)
  fallback_depth: int            # cascade length target (4-6)
  expected_calls_per_day: float  # from logs; demand
  token_profile: {in: int, out: int}
  importance: float              # session priority for preemption
  activity_state: "active"|"idle"|"paused"

SessionProfile (template, "character sheet"):
  name: str                      # "pi-economy","pi-premium","hermes-full","cc-standard"
  roles: list[RoleSpec defaults]
  start_mode: "rollup" | "precomputed" | "hybrid"

CandidateValue:                  # from routing_snapshot per role
  model_id, provider, api_model, base_url, tier, price_blended,
  has_tools, has_vision, ctx, fitness   # fitness = value(m) from model-scan engine

AllocationInput:
  roles: list[RoleSpec]
  candidates_by_role: dict[role_id, list[CandidateValue]]
  meters: list[QuotaMeter]
  horizon_seconds: int           # planning horizon (default 86400)
```

## 4. The LP (formulation, codeable with OR-Tools/PuLP)

```
maximize  sum over (role r, model m):  calls[r] * x[r,m] * U(r,m)

U(r,m) = BASE if m clears r.floor
         + r.value_sensitivity * max(0, fitness(m) - r.floor.min_value)
       = -inf (excluded) if m fails r.floor gates

subject to:
  for each role r:            sum_m x[r,m] == 1            # fully served
  for each role r, provider p: sum_{m in p} x[r,m] <= r.diversity_cap
  for each meter q:
      sum over (r,m using q):  calls[r] * x[r,m] * cost(m, q) <= budget(q, horizon)
  0 <= x[r,m] <= 1
```

- x[r,m] = fraction of role r's daily calls to model m. Cascade = models with x>0 sorted by
  fitness desc; primary = top, fallbacks = next (respecting diversity_cap and fallback_depth).
- Satisficing roles (w_r~0): all floor-clearing models tie -> LP routes to the most ABUNDANT
  (loosest binding meter) -> scarce smart capacity preserved for maximizing roles.
- Solve per model-scan cycle and on fleet/quota change. Problem size = roles x candidates, small.

## 5. F18 allocator output contract

```
RoleAllocation:
  session_id, role_id
  primary: api_model
  cascade: list[api_model]       # ordered fallbacks, diversity-capped
  provider_caps: dict[provider, float]   # share ceiling honored at runtime

AllocationResult:
  generated_at: iso8601
  allocations: list[RoleAllocation]
  shadow_prices: dict[meter_id, float]   # marginal value-per-unit of each quota (bottleneck/buy signal)
  report:
    bench_time: dict[model, float]       # value-weighted unused fraction
    regret: float                        # intelligence left on the table
    over_provisioning: float
```

Mapping out:
- Each RoleAllocation -> snapshot slot entry (best=primary, candidates=cascade) AND/OR a specs/001
  Assignment (`model`=primary, `cascade`=fallbacks). The allocator becomes a snapshot
  POST-PROCESSOR: model-scan emits raw per-slot candidates+fitness; F18 re-ranks them across the
  whole fleet under quota and writes the session-aware result.
- report -> the weekly utilization retrospective (F18 section 7).

## 6. Runtime enforcement contract

```
TokenBucket(meter_id, capacity, refill_rate):
  try_consume(amount) -> bool    # false => meter exhausted, trigger rotation (F05)
RotationDecision: pick next cascade entry whose meters all have headroom (drain_threshold),
  else free-floor model; per-provider cooldown to prevent flapping.
BanditState(role_id): Thompson posterior per candidate, updated from measured
  {latency, tool_success, error_class}; explores within the LP-chosen set; feeds next solve.
```

## 7. Where this plugs in (existing files)

- F06 adapters: new `src/services/quota/adapters/*.py`, ledger in SQLite (reuse usage DB).
- F18 allocator: new `src/services/allocator/` (lp.py, profiles.py, preemption.py, report.py),
  consuming `routing_snapshot.json`, emitting an augmented snapshot the existing
  `model_scan_binder` already knows how to load into `AssignmentRegistry`.
- Enforcement: extend `src/core/client.py` rotation + `circuit_breaker.py`.
- Config: RoleSpec/SessionProfile under the specs/001 manifest so all surfaces edit them.
