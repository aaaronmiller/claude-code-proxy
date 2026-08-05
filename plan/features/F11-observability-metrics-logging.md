---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, observability, metrics, logging, prometheus, opentelemetry, jsonl]
---

# F11: Observability, Metrics and Logging

> STATUS v1.1: PARTIAL. 33-col usage SQLite, ~12 /api/analytics endpoints, prometheus_client,
> terminal dashboard suite (waterfall/routing-visualizer/perf-monitor) all BUILT. GAP: web-ui
> analytics surfacing, Grafana dashboards, the failure-by-model/role/provider -> selection
> feedback loop wiring (feeds F04/F18). "(PROPOSED)" tags below are superseded by 01-CURRENT-STATE.

Scope: log every request with full classification, expose metrics for Prometheus/Grafana, and
feed historical failure data back into model selection. This is the data backbone that makes
selections improve over time.

## Structured logging

- JSONL logs, full schema: request_id, routing_decision, costs, translation_delta,
  quota_discriminator result, chain manifest. (`PRD- MAUG.md:545-585`)
- translation_delta attributes truncation: compare canonical vs translated max_tokens to decide
  provider issue vs settings issue. (`:570-576`)
- Role-based logging and analytics, sortable by model OR task: tokens in/out per model/date,
  tool-call success, web-route speed, role failures, compression % and tokens saved.
  (`unified_project_idea_record.md:133-160`)

## Tracing and metrics

- OpenTelemetry spans: schema.transform, tool.reassembly, fallback.triggered; fields_dropped /
  coerced. (`Proxy update plan.md:243-250`)
- Prometheus metrics clutch_quota_* gauges/counters, labels provider/model/key_id. (`Clutch-
  Gateway-Quota-Monitoring-Technical-Spec.md:437-468`)
- Performance telemetry time-series per provider-model-role, with ORMS-change annotations and
  cohort drift view. (`PRD- MAUG.md:593-602`)

## Failure ingestion (closes the loop)

- Parse agent.log + proxy logs nightly into historical_failures.json; failure rate by class
  (auth/rate-limit/empty/timeout/4xx/5xx) feeds F04 fitness and F05 demotion. The current scan
  ignores this data, which is a known defect. (`Structural Assessment of the Hermes Model
  Selection System.md:27-34,92-98`)

## Current terminal metrics (carry forward)

- workspace / context_pct / task_type / speed / cost / duration colors; LOG_STYLE rich/plain/
  compact; SHOW_TOKEN_COUNTS / SHOW_PERFORMANCE. (`claude cody proxy .env.md:719-751`) (CURRENT)

## Hard requirements

- Never use JSONL token counts for quota (undercounts); headers only. (`Clutch...:493`)
- Persist counters across restart; loose scrape selectors; re-scan Antigravity /proc every 30s.
  (`Clutch...:482-516`)

## Dependencies

- Receives events from every module; powers F15 (Grafana + live fail dashboard) and F16 (status
  bars). The fail-by-model/role/provider data is the user's explicit dashboard requirement.

## Open questions

- Retention windows for JSONL vs Prometheus vs reliability.db (F05 says 90d).
