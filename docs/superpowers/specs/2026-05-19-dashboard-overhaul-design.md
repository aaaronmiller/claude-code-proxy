# Dashboard Overhaul — Design Spec
**Date:** 2026-05-19
**Status:** Approved end-to-end; ship Phases 1+2+3 in one session

## Problem
80% of the analytics backend already exists but isn't surfaced in the web UI:
- 12+ `/api/analytics/*` endpoints (savings, time-series, model-comparison, token-breakdown)
- `usage_tracker` schema has 33 columns including `profile`, `cost`, `tokens`, `duration_ms`, `tokens_per_second`, `has_tools`, `error_message`
- `prometheus_client` already installed
- model-scan tool at `/code/model-scan` has its own data + UI

What's missing: web UI consumption, Prometheus exposition, cost-vs-paid comparison, drag-drop chain editor, model-scan integration, themes.

## Goals
1. Surface existing data via 4 dashboard cards
2. Expose Prometheus `/metrics` endpoint
3. Cost-vs-paid with selectable baseline (default: same model paid via OpenRouter)
4. Drag-drop visual proxy chain editor
5. Dark-mode default + theme system
6. Micro-animations on state changes
7. model-scan link in nav
8. Feature parity doc (CLI/TUI/Web/.env coverage)

## Non-Goals
- Grafana docker-compose (user has Grafana — bring-your-own)
- A/B benchmark harness (deferred until model-scan integration is closer)
- Image generation (not needed; beauty via typography + motion)

## Architecture

### Phase 1A — Analytics cards
New section in `settings.html` titled "Analytics" with 5 cards in a 2-column grid:
| Card | Source endpoint | Visualization |
|---|---|---|
| Token usage by model (24h) | `/api/analytics/token-breakdown` | horizontal bars |
| Tool-call success/failure | `/api/analytics/model-comparison` | green/red stacked bars |
| Latency p50/p95 + tokens/s | `/api/analytics/model-comparison` | dual-bar |
| Cost savings vs paid | NEW `/api/analytics/savings-vs-paid` | $ total + per-model |
| Per-profile traffic | `/api/routing-profiles` | doughnut |
| Error type distribution | `/api/analytics/queries` | horizontal bars |

Color coding: cyan = primary metric, green = success, red = failure, amber = warning, magenta = rate-limit. Same palette as existing settings.html.

### Phase 1B — Prometheus `/metrics`
New module `src/api/metrics_api.py`:
- `proxy_requests_total{profile, model, status}` — counter
- `proxy_request_duration_seconds{model, profile}` — histogram (default buckets)
- `proxy_tokens_total{direction, model, profile}` — counter (in/out)
- `proxy_cost_usd_total{model, profile}` — counter
- `proxy_circuit_breaker_state{model}` — gauge (0/1/2)
- `proxy_cascade_depth` — histogram
- `proxy_profile_active` — gauge per profile
Mounted at `/metrics`. Hook: usage_tracker.log_request() also increments matching counters.

### Phase 1C — Cost-vs-paid
New endpoint `/api/analytics/savings-vs-paid?hours=24&baseline=auto|same|tier|<model>`:
- `auto` (default) = same model's paid version on OpenRouter (look up at openrouter.ai/api/v1/models)
- `same` = compare against `<provider>/<model>` (strip `:free`)
- `tier` = compare small→haiku, middle→sonnet, big→opus pricing
- `<model_id>` = compare to that specific model's pricing
- Backend reads `usage_tracker` for window, multiplies `total_tokens × paid_price_per_token`, returns: `{total_saved_usd, per_model: [{free, baseline, tokens, would_have_cost}], baseline_name}`
- Pricing data: `models/scout/models.json` (already exists, 344 models) + cache from `/code/model-scan/data/`

UI control: dropdown in the Cost card lets user pick baseline. Tier-organized: `── Auto (same model, paid) ──`, `── By tier ──`, `── Premium ──`, `── Mid-tier ──`, `── Budget ──` groups.

### Phase 1D — model-scan link + parity doc
- Add nav item "Model Scan ↗" in `settings.html` (`navSections` array) → opens `http://localhost:7099/` (model-scan's default UI port) in new tab. If user's model-scan port differs, configurable via `MODEL_SCAN_URL` env var.
- Write `docs/feature-parity.md`: auto-generated table from `config_manifest.py` showing every setting's coverage on each surface (CLI flag, TUI menu/widget, Web component, env var). 100% data already in manifest.

### Phase 2 — Reorganization + themes + micro-animations
- **Theme system**: CSS variables for palette. 3 built-in themes: `dark` (default, current), `dark-warm` (sepia-tinted), `light` (high-contrast). Stored in localStorage. Toggle in top-bar.
- **Smart grouping**: settings groups already exist in `config_manifest.py` (server/models/reasoning/etc). Add collapsible sections — auto-collapse non-"models" groups on first load, expand on click. State persisted in localStorage.
- **Micro-animations** (CSS keyframes + a few JS-driven): card fade-in on load (staggered 60ms), value pulse on save success, smooth height transitions on collapse, hover ring on interactive cards, gsap-style scroll-reveal on cards entering viewport (IntersectionObserver based — no GSAP runtime needed for a settings page).
- **No GSAP dependency**: page is form-heavy; CSS + IntersectionObserver covers what GSAP would do without 200KB of JS.

### Phase 3 — Drag-drop chain editor
- New section in `settings.html` titled "Proxy Chain" → uses **Svelte Flow** loaded via ESM CDN (`https://esm.sh/@xyflow/svelte`). Lighter than React Flow, MIT-licensed, works in single-file HTML via dynamic imports.
- Nodes: one per `proxy_chain.json` entry (currently 2: claude_code_proxy, headroom)
- Edges: implicit chain order — drag to reorder
- Node body: editable form (name, url, port, enabled, model). Model picker dropdown sourced from `/api/routing-profiles` resolved models + model-scan data (if scan data available, show tier badge next to each)
- Save: POST `/api/chain` (already exists at line 244 of `config_api.py`)
- Inline validation: cycle detection (chain must be DAG), port collision check

### Data flow

```
Client request
  → proxy:8082 (FastAPI)
    → usage_tracker.log_request(...)         [SQLite]
    → metrics counters incremented           [Prometheus]
    → events.jsonl append                    [JSONL]
  → upstream
  ← response
Web UI:
  /api/analytics/*  ← settings.html cards (Phase 1A)
  /metrics          ← scraped by user's Grafana (Phase 1B)
  /api/analytics/savings-vs-paid ← Cost card (Phase 1C)
  /api/chain        ← Drag-drop editor (Phase 3)
```

## Components / file map
| New / modified | File | Purpose |
|---|---|---|
| NEW | `src/api/metrics_api.py` | Prometheus exposition |
| MOD | `src/services/usage/usage_tracker.py` | Wire metrics counters |
| MOD | `src/api/analytics_api.py` | Add savings-vs-paid endpoint |
| MOD | `src/services/models/cost_lookup.py` | Add `paid_equivalent_cost()` |
| NEW | `src/static/dashboard.js` | Chart helpers (vanilla, no chart.js — inline SVG bars for tighter control) |
| MOD | `src/static/settings.html` | New sections: Analytics, Proxy Chain. Themes, animations |
| NEW | `docs/feature-parity.md` | Auto-rendered config coverage matrix |
| MOD | `src/main.py` | Mount metrics router |

## Testing
- Unit: extend `tests/test_profiles.py` with savings-vs-paid resolver tests
- Smoke: each endpoint returns 200 with valid JSON shape
- Visual: manual — open `/settings`, verify all 6 cards render with mock data when usage_tracker is empty

## Open questions
**Resolved by user:**
- Q1: comparison baseline = selectable, default = same-model-paid, tier-organized in dropdown
- Q2: all phases approved, skip Grafana docker
- Q4: drag-drop via Svelte Flow CDN; dark default + themes; gsap/micro-animations as appropriate

## Risk register
| Risk | Mitigation |
|---|---|
| Svelte Flow ESM CDN unreliable | Fallback: skip chain editor, list-with-buttons UI (already works via JSON edit) |
| model-scan port not on 7099 | Configurable via `MODEL_SCAN_URL` env, default skip the link if unreachable |
| `models/scout/models.json` pricing stale | Show "data freshness: N days old" badge in Cost card |
| Prometheus counters double-counting on cascade retries | Use `attempt_index=0` as the canonical request boundary |
| 8 cards on one page = slow load | Lazy-render cards 4-6 (defer fetch until scrolled into view via IntersectionObserver) |
