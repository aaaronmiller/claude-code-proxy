---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, capacity-planner, allocator, quota-optimization, lp, bandit, preemption, profiles]
---

# F18: Capacity Planner and Quota-Aware Global Allocator

The critical synthesis layer. F03 scores each model per role in isolation; F06 tracks quota; F04
selects per request. NONE of them solve the real problem: many concurrent sessions drawing from
the same finite, multi-dimensional quota pools, where the goal is the most EFFECTIVE use of
scarce smart capacity, not just the most usage. F18 is that allocator. It decides, across the
whole fleet, which models each session-role gets, subject to every quota meter, to maximize
agentic intelligence delivered per day where it actually matters.

## 1. Core principle: satisfice then optimize (not "everything optimal")

Not every session needs the best model. Each session-role carries:
- a REQUIREMENT FLOOR: hard gates it must clear (min capability, needs_tools, needs_vision,
  min_ctx, and a per-role minimum value, e.g. "primary must beat gpt-oss-120b", "toolcall must
  beat gpt-oss-120b"). A model below floor is never a candidate.
- a VALUE-SENSITIVITY weight `w_r`: how much the role benefits from quality ABOVE the floor.
  - Satisficing role (w_r ~ 0): flat utility above floor. Example: an economy Pi primary is happy
    with deepseek-v4-flash; a smarter model there is wasted. The allocator will give it the most
    ABUNDANT floor-clearing model and save scarce smart capacity for others.
  - Maximizing role (w_r high): steep utility. Example: a Hermes reasoning primary or delegation
    role. The allocator fights to give it the highest-value affordable model.

Utility curve per role r, model m:
`U_r(m) = base_if_meets_floor + w_r * max(0, value(m) - floor_value_r)`
where `value(m)` = model-scan slot-fitness (F03). Satisficing => w_r small => all floor-clearing
models tie => pick cheapest/most-abundant. Maximizing => w_r large => pull toward the top.

This is exactly your point: the user sets `floor` and `w_r` per session-role, which gives the
optimizer the freedom to route the best models to where they count.

## 2. The allocation as a linear program

Decision: `x[s,r,m]` in [0,1] = fraction of role r's daily calls in session s routed to model m.
Sorting a role's chosen models by value yields primary + ordered fallback cascade for free.

Objective: maximize  Σ_{s,r,m}  `calls[s,r] · x[s,r,m] · U_{role(r)}(m)`
- calls[s,r] = expected daily call volume (from logs / profile).
- Maximizing total U under fixed demand and quota supply = maximizing average effective
  intelligence per call. The LP automatically pushes scarce smart models to high-w_r roles and
  abundant free models to satisficing roles.

Subject to (section 3). Small problem (models x roles x sessions, a few hundred to low-thousands
of vars); solve in milliseconds with OR-Tools / PuLP / scipy.linprog. Re-solve each model-scan
cycle and on fleet changes.

## 3. Constraints

### 3.1 Quota meters (multi-dimensional; see F06 for the normalization table)
Every request debits one or more meters. One LP constraint row per meter:
- call-count meters: OpenRouter free 1k/24h per model; Groq/Cerebras 10k/day per model;
  OpenCode Go free 10k/day per model; OpenCode Zen per-model daily.
- token-window meters: Claude Code 5h + weekly; Ollama 3h + daily + weekly + monthly; Antigravity
  5h + week + month. A single Antigravity call debits all three of its rows at once.
- credit pools: Kiro 50/month; NVIDIA NIM credits.
- dollar pools: OpenCode Go $50/mo effective.
- specialized: Perplexity good-search-calls/week.
Windows shorter than a day are rate constraints (budget per window, enforced by the token-bucket
in 6.1). Windows longer than a day are pro-rated to a daily slice but the ledger tracks the true
window so week-1 cannot exhaust the month.

### 3.2 Per-role floors and gates
`x[s,r,m] = 0` if m fails role r's hard gates or floor_value. Guarantees capability correctness
(never assign a no-tools model to a tool role), independent of the optimization.

### 3.3 Diversity / fallback depth
No role draws more than a configured share from one provider, so the cascade has real
cross-provider fallbacks (mirrors model-scan diversity + F05 cascade).

### 3.4 Coverage
Σ_m x[s,r,m] = 1 per active role (every role must be fully served by something that clears floor;
if nothing clears floor, surface an explicit error, never silently downgrade below floor).

## 4. Session profiles ("character sheets") and the 3 start modes

A library of profile TEMPLATES, each = a set of role specs (floor + w_r + diversity + fallback
depth + activity priority). Examples:
- `pi-economy`: primary floor=deepseek-v4-flash-class w_r low; toolcall floor=beat gpt-oss-120b
  (nemotron-nano-class) w_r low; cheap, abundant, never touches scarce pool.
- `pi-premium`: primary w_r high; toolcall w_r medium.
- `hermes-full`: primary + delegation w_r high; 10 aux roles w_r low/satisficing; vision +
  compression roles with their own floors.
- `cc-standard`: big/middle/small tiers with per-tier floors + fallbacks.

On session start, per-session-type policy picks one of:
1. ROLL-UP FRESH: solve the LP from scratch against live quota + active-fleet state. Best fit,
   slightly slower. ("Roll a new D&D character" against today's conditions.)
2. PRECOMPUTED PROFILE: load a snapshot the offline planner computed earlier. Instant, may be
   slightly stale.
3. HYBRID (recommended default): load the template, then run a fast local re-solve against
   CURRENT quota and idle state to adjust the cascades. Premade config, recomputed optimal.

## 5. Live allocation: preemption and borrowing

Sessions have activity state: active / idle(>T min) / paused. The allocator runs a live
reallocation loop (priority scheduler over model-quota as the scarce resource):
- Effective priority `P[s,r] = importance[s] * activity_factor` (active=1, idle decays toward 0).
- When a high-priority maximizing role needs scarce capacity and a lower-priority/idle session
  holds a reservation on a scarce smart model it is not using, BORROW it: reassign that model to
  the high-need role and DEMOTE the idle session's config to a lower-tier (still floor-clearing)
  primary. Example: a Pi session idle 45 min lends its primary to a busy Hermes; the idle Pi drops
  to a lower-tier primary, restored on wake if capacity allows.
- Hysteresis + cooldown so allocations do not flap (mirror F05 circuit-breaker cooldowns).
- WAKE RE-EVALUATION: a returning session is re-allocated against current state, not given back a
  stale reservation. This is OS-style preemptive scheduling, resource = model-quota, weight =
  importance x activity x role value-sensitivity.

## 6. Online refinement (the production loop)

Recommended: token-bucket enforcement + Thompson-sampling bandit + periodic LP re-solve.

### 6.1 Enforcement
A token-bucket per meter (per provider/model/window) enforces quota in real time. This is the
runtime executor of the LP plan and is what model-scan's quota-aware rotation (drain_threshold,
free-floor) already approximates; F18 makes it the explicit allocator output.

### 6.2 Exploration / self-correction
Within each role's LP-chosen candidate set, a per-role bandit (Thompson sampling) rebalances using
MEASURED outcomes (real latency, tool-call success, error rate), refining `value(m, role)` from
production reality, not just published benchmarks. Improved values feed the next LP solve.

### 6.3 Re-solve cadence
LP re-solves each model-scan cycle and on fleet/quota events. LP handles global scarcity
allocation; bandit handles uncertainty; token-bucket handles hard enforcement.

## 7. Weekly utilization retrospective (did smart models sit on the bench?)

The audit you described, quantified:
- BENCH-TIME(m) = unused_quota_fraction(m), weighted by value(m). High value x high bench-time =
  wasted smart capacity (Kimi 2.6 idle all week).
- REGRET = Σ over calls served by m_actual on a maximizing role where a higher-value model m' was
  available (had quota and/or sat idle): `U_r(m') - U_r(m_actual)`. This is intelligence left on
  the table (gpt-oss serving a Hermes primary while Kimi was free).
- OVER-PROVISIONING = scarce model spent on a satisficing role while a maximizing role was starved.
- SHADOW PRICES (LP duals) = marginal intelligence value of one more unit of each quota meter:
  tells you which subscription to buy more of and which bucket is the binding bottleneck.
Outputs feed back: re-tune floors/w_r, adjust profiles, flag miscalibrated requirements, inform
purchase decisions. Extends model-scan weekly mode + reliability feedback.

## 8. Analytics contract (inputs F18 needs)

- Per (model, provider), measured by the proxy and logged (F11 + model-scan reliability feed):
  TTFT, tokens/s, e2e latency p50/p95, error rate by class, availability by hour-of-day, actual
  tokens in/out per call by role.
- Per (session, role): calls/day, token in/out profile, task mix, tool-call frequency, retry rate,
  activity state. (Mine agent.log + usage DB.)
- Quota telemetry per meter: remaining/limit/reset (F06 adapters).
- Value inputs: AA IQ/coding/agentic, models.dev specs (ctx, max_out, modality), PinchBench,
  benchmarks.json (SWE/BFCL/ELO), own programmatic speed/availability probes (F03).

## 9. Outputs

- Per-session-role cascades (primary + ordered fallbacks) and provider caps.
- These become the model-scan routing snapshot entries and the generated client configs (Hermes
  config.yaml via F12 human-gated apply; Claude Code / Pi profiles).
- The bottleneck/regret/bench report (section 7) for the operator and for purchase decisions.

## 10. Dependencies

- value(m, role) from F03 (model-scan engine). Quota meters from F06. Enforcement + fallback from
  F05/F10. Profiles + generated configs via F12. Telemetry from F11. Per-session lanes from F10.

## 11. Hard requirements

- Never assign below a role's floor; if nothing clears the floor, error explicitly (no silent
  downgrade).
- Free-floor: satisficing roles must not consume scarce paid quota when an abundant free model
  clears their floor.
- Quota enforcement is hard (token-bucket); the LP plan is a target, the bucket is the ceiling.
- Per-session/per-role floor + value-sensitivity are USER-DEFINED (the flexibility you require).
- Borrowing/preemption must be reversible with hysteresis; a woken session is re-allocated, never
  handed a stale reservation.

## 12. Open questions

- Importance weights: a fixed per-session-type table, or a priority the user sets at launch?
- Offline planner cadence (nightly full sim) vs purely on-demand at session start.
- How aggressively to preempt idle sessions (idle threshold T, demotion depth).

## 13. Worked example: the real fleet (numbers illustrative)

Fleet:
- 3 Hermes systems, each = 1 primary + 1 delegation + 10 aux + 4-6 fallbacks per role.
- 1 Claude Code session = big / middle / small + fallbacks.
- 5 Pi sessions = primary + toolcall + fallbacks. Of these, per your example, 2 are `pi-economy`
  (satisficing) and 3 are `pi-premium` (maximizing).

Step 1 - classify roles by utility curve:
- MAXIMIZING (high w_r, want best affordable): 3 Hermes primaries, 3 Hermes delegation, Claude
  Code big, 3 Pi-premium primaries. ~10 high-value seats competing for scarce smart capacity.
- SATISFICING (floor only, route to abundant): 30 Hermes aux (10 x 3), 5 Pi toolcall, 2 Pi-economy
  primaries, Claude Code middle/small. Floors: aux/toolcall must beat gpt-oss-120b; Pi-economy
  primary floor = deepseek-v4-flash-class.

Step 2 - lanes (F10):
- INTERACTIVE lane = the 10 maximizing seats. Latency-sensitive, get the smart scarce pool.
- STANDBY lane = the ~40 satisficing seats. Get free-abundant models, never touch scarce paid
  quota (free-floor rule).

Step 3 - allocate the scarce smart pool to maximizing seats (LP, with diversity cap so each seat
has cross-provider fallbacks). Illustrative result:

| Seat (maximizing) | Primary | Fallback 1 | Fallback 2 | Drawn from |
|-------------------|---------|------------|------------|------------|
| Hermes-1 primary | Cerebras top-IQ | Antigravity premium | Groq high-IQ | distinct providers |
| Hermes-2 primary | Antigravity premium | Groq high-IQ | OpenRouter free S-tier | diversity enforced |
| Hermes-3 primary | Groq high-IQ | Cerebras top-IQ | OpenRouter free S-tier | |
| Hermes-1/2/3 delegation | next-best smart per provider, spread | ... | ... | shares buckets below caps |
| Claude Code big | Antigravity premium (5h window) | Cerebras | Groq | window-metered |
| Pi-premium x3 primary | remaining smart capacity by w_r | free S-tier | free A-tier | |

The LP spreads the three Hermes primaries across Cerebras / Antigravity / Groq so no single
10k/day-per-model bucket starves, and every seat still has 2-3 cross-provider fallbacks.

Step 4 - satisficing seats go to abundant free pools:
- 30 Hermes aux + 5 Pi toolcall: OpenRouter free (1k/day per model, spread across many models) +
  OpenCode free (10k/day per model) + nemotron-nano-class for toolcall. Floor = beat gpt-oss-120b.
- 2 Pi-economy primaries: deepseek-v4-flash. No scarce quota consumed.

Step 5 - live preemption: Pi-premium-3 goes idle 45 min. Its Cerebras reservation is borrowed by
Hermes-1 (busy, maximizing); Pi-premium-3 is demoted to a free S-tier primary. On wake, Pi-3 is
re-allocated against current quota; if Cerebras headroom returned, it gets a smart model back.

Step 6 - weekly audit: report shows Kimi-2.6 sat at 70% bench-time while a Hermes primary ran
gpt-oss 30% of the week -> regret flag -> either raise that primary's w_r/floor or the LP was
quota-starved (check the Groq/Cerebras shadow price; if high, that bucket is the bottleneck to
buy up). Pi-economy primaries show ~0 regret (correctly satisficed on deepseek-v4-flash).

Outcome: scarce intelligence concentrated on the ~10 seats that benefit, ~40 seats correctly
served by free-abundant models, every seat has real fallbacks, idle capacity recycled live, and a
weekly signal that tunes floors/weights and informs what to buy.
