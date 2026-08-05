---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, web-ux, dashboard, prometheus, grafana, drag-drop, standalone-future]
---

# F15: Web UX and Dashboard

> STATUS v1.1: PARTIAL / NEEDS REBUILD. A SvelteKit app exists but the user reports it "totally
> broken" (lucide-svelte import breakages); analytics endpoints exist but are under-surfaced.
> TO DO: frontend-design rebuild (3 themes, microanimations), full config parity, live fail
> dashboard, Grafana. "(PROPOSED)" tags below superseded by 01-CURRENT-STATE.

Scope: a browser UI that does everything the CLI and TUI do (full parity), plus a live dashboard
of API-call failures by model/role/provider, with Prometheus and Grafana as prominent
inclusions. The only pre-approved future change is taking this UX out of the browser into a
standalone app.

## Design

- Web UI: configuration dashboard + analytics + drag-drop proxy-chain reorder (ref
  claude-code-swap). (`unified_project_idea_record.md:232-242`) (HARD parity)
- Live fail dashboard: API-call failures associated with model/role/provider, so the data
  improves future selections. (user prompt; `unified_project_idea_record.md:133-160`) (HARD)
- Prometheus + Grafana prominent: quota bars, key health, request rate, 429 alerts, rotation log,
  color-coded green<70 / yellow / red>90. (`Clutch-Gateway-Quota-Monitoring-Technical-Spec.md:437-478`)
- Optional admin analytics can reuse the LiteLLM admin container rather than reimplementing
  historical views. (`PRD- MAUG.md:639-641`)
- Current: Web UI /settings Routing Profiles section + REST /api/routing-profiles + per-profile
  usage endpoint. (`new proxy commands.md:5-6,14-15`) (CURRENT)
- Current terminal dashboard (ENABLE_DASHBOARD / layout / refresh / modules) is the in-terminal
  precursor. (`claude cody proxy .env.md:791-803`) (CURRENT)

## Hard requirements

- Full feature parity with CLI/.env and TUI (F12): all configurable features present.
- The fail dashboard must tag every failure with model + role + provider for selection feedback.

## Future (pre-approved deferral, not v1)

- Take the Web UX out of the browser into a standalone desktop app. This is the ONLY item allowed
  to be deferred. (user prompt)

## Dependencies

- Backed by the same config/API as F14 (parity); data from F11; Prometheus/Grafana from F11 + F06;
  chain reorder writes F02; tech stack default Svelte 5 + Hono + Cloudflare per user stack rules.

## Open questions

- v1 web stack: ship a minimal dashboard over the shared API first, expand to full config parity
  in Phase E? Confirm scope split.
