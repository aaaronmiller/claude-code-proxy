---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, quota, keys, subscriptions, clutch, key-ledger, discriminator]
---

# F06: Quota, Key and Subscription Management

> STATUS v1.1: PARTIAL. Budgets + key-pool rotate-on-429 (PROVIDERS_<n>_API_KEYS) + model-scan
> quota ledger (tokscale primary) BUILT. TO BUILD: the full multi-provider quota-meter adapters
> (see "Quota normalization" below + 04-DATA-CONTRACTS). Feeds F18. "(PROPOSED)" tags below
> superseded by 01-CURRENT-STATE.

Scope: track every subscription, API key, and usage quota across providers; tell real quota
exhaustion apart from transient overload or a bad key; rotate keys to the one with the most
headroom. This is the Clutch quota subsystem.

## Quota acquisition (11 providers, 3 access patterns)

Pattern A response headers, Pattern B REST poll, Pattern C local scrape.
(`Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:44-54`)

| Provider | Method | Pointer |
|----------|--------|---------|
| Claude Code | x-ratelimit-* headers (ignore JSONL, undercounts 100-174x) | :60-86 |
| Codex/OpenAI | response headers + reset ts | :89-111 |
| Antigravity | Connect-RPC GetUserStatus, dynamic port+CSRF from /proc, 5h window | :114-154 |
| OpenCode Go | local SQLite read | :157-179 |
| OpenCode Zen | local file/DB read | :182-198 |
| NVIDIA NIM | sliding-window counter (~40 RPM, 429-only) | :201-231 |
| Cerebras | response headers | :234-255 |
| Groq | per-model RPM/TPM headers | :258-280 |
| Kilo Code | REST poll / headers | :283-300 |
| OpenRouter | GET /api/v1/auth/key (usage/limit, 1000/day funded) | :303-346 |
| Ollama Cloud | HTML scrape /settings (next-auth cookie, weekly) | :349-373 |

- Common adapter interface: get_quota / get_health / on_response / on_request.
  (`:521-528`)
- 4-tier integration priority: Tier-1 header-passthrough (trivial) to Tier-4 complex. (`:530-557`)

## Key ledger and rotation

- Key Ledger: Redis per-key state, dims temporal/token/request, status active/throttled/dead/
  suspended. (`PRD- MAUG.md:308-340`)
- Rotation logic: filter cooldown -> rank by remaining -> tiebreak reset window -> cascade.
  (`Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:559-568`)
- `maug rotate-keys`; key-rotation proxy refs (LLM-API-Key-Proxy/gpt-load/LiteLLM
  credential_balancer). (`PRD- MAUG.md:814`; `Clutch...:398-433`)

## Quota discriminator

- Distinguish real-quota vs overload vs invalid-key via probe pipeline + error matrix
  (429/401/422/503 -> action). Target >95% accuracy. (`PRD- MAUG.md:288-307,1956-1966`)

## Budgets and provider specifics

- Budget ceilings daily/hourly/per-request; refuse if projected cost > remaining. (`PRD-
  MAUG.md:342-347`) (cost policy detailed in F07)
- Provider budget rules (RESOLVE conflicts): NVIDIA NIM credits (100k tokens vs 1000 credits),
  OC Go spend ($0.50 vs $2/$5/$10/$20), Ollama weekly free-tier probe 402 -> boneyard.
  (`HERMES_REFINEMENT_SPECIFICATION.md:391-459`)
- Time-aware quota windows (Groq 00:00 UTC, Ollama 3h, Cerebras off-peak) become an
  availability multiplier for F04. (`Structural Assessment...md:73`)

## Quota normalization (meters) - feeds F18 allocator

Every quota is modeled as a "meter". A single request debits one or more meters at once. Keep
them as separate constraints; do not collapse into one number. Each meter exposes
remaining/limit/reset to the allocator.

| Provider | Meter(s) | Type | Note |
|----------|----------|------|------|
| Claude Code | 5h window + weekly | token | use x-ratelimit headers, not JSONL |
| Codex/OpenAI | rolling | token | headers |
| Antigravity | 5h + week + month | token | one call debits all three |
| Ollama Cloud | 3h + daily + weekly + monthly | token | scrape /settings weekly |
| Groq | per-model 10k/day | call-count | per model, per key |
| Cerebras | per-model 10k/day | call-count | headers |
| OpenRouter free | per-model 1k/24h | call-count | 50/day unfunded |
| OpenCode Go | $50/mo effective + per-free-model 10k/day | dollar pool + call-count | budget blended into fitness |
| OpenCode Zen | per-model daily | call-count | several free models |
| Kiro | 50/month | credit pool | |
| NVIDIA NIM | credits | credit pool | ~40 RPM, 429-only signal |
| Perplexity | good-search-calls/week | specialized call | search route only |

Normalization rule: window shorter than a day -> rate constraint (budget per window, token-bucket
enforced); window longer than a day -> pro-rate to a daily slice but track the true window so a
month is not exhausted early. These meters are the constraint rows in the F18 linear program.

## Hard requirements

- Never rely on JSONL token counts; use response headers exclusively. (`Clutch...:493`)
- Secrets env-only, never persisted; preserve existing credential loading order; never modify
  ANTHROPIC_API_KEY=pass / x-api-key:pass. (`PRD- MAUG.md:1129,1737`)
- Persist counters across restart (NIM/scrape drift); re-scan Antigravity /proc every 30s. (`Clutch...:482-516`)

## Dependencies

- Current usage_tracking.db with profile column extended here. (`new proxy commands.md:31-33`)
- Feeds F04 selection (headroom), F05 (dead-key -> circuit), F11 (Prometheus clutch_quota_*), F15
  (Grafana quota dashboard).

## Open questions

- Resolve the conflicting provider-budget numbers above (need authoritative values).
