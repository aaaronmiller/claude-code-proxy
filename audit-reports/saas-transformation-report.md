# Clutch Gateway — SaaS Transformation Architecture Report

> **Date**: 2026-06-06
> **Repo**: `claude-code-proxy` (Clutch Gateway)
> **Focus**: Current-state audit + cloud-hosted SaaS vision covering proxy, compression, proxy chain, transformations, analytics, and operational stack.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Architecture Overview](#2-current-architecture-overview)
3. [Layer-by-Layer Audit & SaaS Mapping](#3-layer-by-layer-audit--saas-mapping)
   - 3.1 [Gateway Core (Proxy & Router)](#31-gateway-core-proxy--router)
   - 3.2 [Model Routing & Cascading Fallback](#32-model-routing--cascading-fallback)
   - 3.3 [Compression Layer (Headroom + RTK)](#33-compression-layer-headroom--rtk)
   - 3.4 [Protocol Conversion Layer](#34-protocol-conversion-layer)
   - 3.5 [Proxy Chain & Pipeline System](#35-proxy-chain--pipeline-system)
   - 3.6 [Usage Tracking & Analytics](#36-usage-tracking--analytics)
   - 3.7 [Alerting & Observability](#37-alerting--observability)
   - 3.8 [Web Dashboard & Terminal Dashboard](#38-web-dashboard--terminal-dashboard)
   - 3.9 [User Management & RBAC](#39-user-management--rbac)
   - 3.10 [Launcher & CLI Layer](#310-launcher--cli-layer)
   - 3.11 [Crosstalk (Multi-Agent Orchestration)](#311-crosstalk-multi-agent-orchestration)
   - 3.12 [Model-Scan Integration](#312-model-scan-integration)
3. [Project Health Assessment](#3-project-health-assessment)
4. [SaaS Deployment Topology](#4-saas-deployment-topology)
5. [Stale / Deprecated Assets](#5-stale--deprecated-assets)
6. [Recommended SaaS Architecture Roadmap](#6-recommended-saas-architecture-roadmap)

---

## 1. Executive Summary

**Clutch Gateway** (formerly `claude-code-proxy`) is a **local AI gateway** that unifies 8+ coding agents (Claude Code, Codex, Hermes, Pi, Qwen, Antigravity, Ante, OpenCode) behind a single HTTP gateway providing model routing, context compression, protocol translation, free-model cascading, and usage analytics — all running on consumer hardware.

### What Exists Today (Local-First)

| Layer | Status | Notes |
|-------|--------|-------|
| FastAPI Gateway (`:8082`) | **Production-ready** | 27 API route modules, 92K `client.py` |
| Headroom Compression (`:8787`) | **Production-ready** | GPU-accelerated, 40-70% context savings |
| RTK Terminal Compression | **Production-ready** | 60-90% shell output reduction |
| Protocol Conversion | **Production-ready** | Anthropic ↔ OpenAI ↔ Gemini |
| Model Cascading Fallback | **Production-ready** | 3-tier (BIG/MIDDLE/SMALL) with circuit breakers |
| Usage Tracking (SQLite) | **Production-ready** | 60K `usage_tracker.py`, full analytics API |
| SvelteKit Web Dashboard | **Beta** | 14 routes, 3 themes (Aurora/Ember/Frost) |
| Terminal Dashboard (Rich TUI) | **Beta** | Edge modules, live waterfall |
| Alert Engine | **Beta** | Rule-based + predictive alerting |
| User Management / RBAC | **Beta** | Role-based access control |
| Model-Scan Integration | **Beta** | Live model health diagnostics |
| xx Launcher | **Stable** | 3-char agent encoding (25 aliases → 1 command) |

### SaaS Opportunity

All of this is **local-first** today but architected in a way that maps 1:1 to a cloud-hosted SaaS:

> **Local Deployment** → **Multi-Tenant Cloud Service**
> single-user FastAPI → horizontally-scalable gateway fleet
> SQLite → PostgreSQL + TimescaleDB
> local headroom GPU → shared GPU pool / serverless inference
> xx launcher → API keys + SDK clients
> tmux-based lifecycle → Kubernetes + Helm

---

## 2. Current Architecture Overview

### Logical Data Flow

```
                         ┌──────────────────────────────────────┐
                         │         Agent Fleet (Customer)         │
                         │  Claude Code · Codex · Hermes · Pi   │
                         │  Qwen · Antigravity · Ante · OpenCode │
                         └──────────────┬───────────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │   RTK Compression    │
                              │  (terminal output)   │
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  Headroom Compressor │
                              │  :8787 · GPU: 787MB  │
                              │  40-70% ctx savings  │
                              └─────────┬──────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│                        Clutch Gateway Router :8082                          │
│                                                                             │
│  ┌─────────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────────┐      │
│  │ Request Conv │→│ Model    │→│ Circuit   │→│ Response Conv     │      │
│  │ (Anthropic→  │ │ Router   │  │ Breaker   │  │ (OpenAI→Anthropic) │      │
│  │  OpenAI)     │  │ (Roles)  │  │ (3-fail)  │  └───────────────────┘      │
│  └─────────────┘  └──────────┘  └───────────┘                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     Cascade Fallback Engine                      │       │
│  │  BIG: Kimi K2.6 → Nemotron → DeepSeek → GPT-OSS                 │       │
│  │  MIDDLE: Nemotron → GLM-4.5 → GPT-OSS                           │       │
│  │  SMALL: Nemotron-Nano → Ling → Nemotron-Super                   │       │
│  └─────────────────────────────────────────────────────────────────┘       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
              ┌─────────────────────────┼──────────────┬──────────────────┐
              ▼                         ▼              ▼                  ▼
        OpenRouter              Anthropic          OpenAI            Gemini
     (free + paid)                (Pro)            (API)             (API)
```

### Source Tree (Active Subsystems)

```
src/
├── api/          (27 files)  — FastAPI endpoints
│   ├── endpoints.py         (89K)  — Core proxy: /v1/messages, streaming, health
│   ├── openai_endpoints.py  (34K)  — OpenAI-compatible API surface
│   ├── analytics.py         (16K)  — Timeseries, cost breakdowns
│   ├── analytics_api.py     (6K)   — Analytics query API
│   ├── alerts.py            (24K)  — Alert rule CRUD + history
│   ├── config_api.py        (18K)  — Full settings API (62 settings)
│   ├── metrics_api.py       (7K)   — Performance metrics
│   ├── web_ui.py            (80K)  — Static web UI server
│   ├── websocket_dashboard.py (6K) — Live dashboard WebSocket
│   ├── websocket_logs.py   (15K)  — Streaming WebSocket logs
│   ├── websocket_live.py   (22K)  — Live metrics WebSocket
│   ├── users.py / users_rbac.py (20K) — Auth + RBAC
│   ├── billing.py / reports.py — Billing & reports
│   └── system_monitor.py   (41K)  — Full system health
│
├── core/         (16 files) — Core engine
│   ├── client.py           (92K)  — OpenAI SDK client, cascade, circuit breakers
│   ├── config.py           (24K)  — Configuration model
│   ├── config_manifest.py  (25K)  — 62-setting manifest (SSOT)
│   ├── config_resolver.py  (20K)  — Precedence resolver (env→file→CLI)
│   ├── model_router.py     (20K)  — Role-based routing engine
│   ├── proxy_chain.py      (23K)  — Service chain topology
│   ├── profiles.py         (14K)  — Agent routing profiles
│   ├── model_scan_binder.py (9K)  — Model-scan snapshot consumption
│   ├── model_scan_runtime.py (5K) — Runtime reload
│   ├── assignments.py      (9K)   — Tier/slot assignments
│   ├── circuit_breaker.py  (17K)  — Circuit breaker state machine
│   └── pipeline.py         (9K)   — Pipeline orchestration
│
├── services/               — Business logic
│   ├── conversion/         — Anthropic↔OpenAI↔Gemini conversion
│   ├── logging/            — 7 loggers (proxy, request, event, structured, etc.)
│   ├── models/             — Model parsing, ranking, filtering, catalog
│   ├── observability/      — Error sink, audit log, reliability feedback
│   ├── usage/              — Rate limiter, cost calculator, usage tracker
│   ├── prompts/            — Prompt injection and system prompt management
│   └── ...                 — Benchmarking, billing, scheduler, IDE detection
│
├── dashboard/    (8 files) — Terminal dashboard / TUI
├── cli/          (15 files) — CLI configuration tools
├── models/       (5 files)  — Data models
└── auth/         (1 file)   — User manager
```

---

## 3. Layer-by-Layer Audit & SaaS Mapping

### 3.1 Gateway Core (Proxy & Router)

**Current State (Local):**
- FastAPI server on `:8082` with 27 route modules
- 92K `client.py` handles all LLM provider communication via OpenAI SDK
- Config is resolved from `.env` → `config/proxy_chain.json` → CLI flags (62 settings in manifest)
- Request snapshot isolation via `config_resolver.py` for in-flight config changes
- Mid-stream budget detection + tier downgrade

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Server | Single uvicorn process | Horizontally-scaled FastAPI on Kubernetes |
| Config | `.env` + JSON file + CLI flags | Central Config DB (PostgreSQL) + Admin API |
| Session State | In-memory per-process | Redis cluster + distributed session store |
| API Surface | 27 route modules → 1 HTTP port | Same API as gateway endpoint per tenant |
| Client SDK | `OpenAI SDK` → `:8082/v1` | SDK per language + REST API key auth |
| Circuit Breakers | In-process dict | Distributed circuit breaker (Redis + pub/sub) |

**Key Interfaces to Expose as SaaS API:**

```
POST /v1/chat/completions     — OpenAI-compatible chat (primary agent traffic)
POST /v1/messages             — Anthropic-compatible messages
POST /v1/audio/transcriptions — Whisper pipeline input
POST /v1/pipeline/{name}      — Multi-step pipeline (voice → LLM → TTS)
GET  /v1/models               — Available models with role annotations
```

### 3.2 Model Routing & Cascading Fallback

**Current State:**
- 3-tier role system: BIG (primary), MIDDLE (tool calls), SMALL (background)
- Signal-based router: `think`, `web_search`, `image`, `long_context`, `background` slots
- Cascade fallback: each tier has 3-5 models, tries sequentially on failure
- Circuit breakers: 3 failures → 60s cooldown → half-open probe
- Quota-aware rotation: per-model RPM limits, cooldown tracking
- Model-scan integration: live provider health → auto tier reassignment
- Profile system: per-agent routing profiles with `slot_bindings`
- Identifier mapping: incoming model names rerouted to tiers (e.g. `haiku` → SMALL)

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Tier assignments | `config/proxy_chain.json` | Multi-tenant assignment table in PostgreSQL |
| Cascade models | Static JSON list | Per-tenant prefs + global health-weighted pool |
| Model-scan data | Local file snapshot | Shared provider health dashboard shared across tenants |
| Identifier mappings | Local config | Per-tenant mapping rules (tenant override → global default) |
| Circuit breaker | In-process per model | Distributed breaker per (tenant, model, provider) |
| Quotas | Hardcoded in JSON | Rate limit service (Redis sliding window) |
| Profile store | `profiles/profiles.json` | PostgreSQL + cached in Redis |

### 3.3 Compression Layer (Headroom + RTK)

**Current State:**

**Headroom** (`:8787`):
- GPU-accelerated context compression (NVIDIA CUDA / Intel OpenVINO / CPU fallback)
- Kompress model (ONNX, ~787 MB GPU memory)
- 40-70% prompt context window savings
- Auto-detects GPU type at startup
- Supports LAN relay (one machine with GPU serves the LAN)
- Sits as an inline proxy in the chain

**RTK** (Terminal Compression):
- 60-90% token reduction on shell output
- Per-command filters: `rtk git status`, `rtk cargo build`, `rtk vitest run`
- Meta commands: `rtk gain` (savings stats), `rtk discover` (missed opportunities)
- Custom per-project RTK filters in `CLAUDE.md`

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Headroom | Local ONNX model, GPU-bound | Serverless GPU inference / dedicated GPU pool |
| Headroom model | Single model, local load | Shared model serving (vLLM / Triton) across tenants |
| RTK | Local CLI tool | Client-side SDK module, server-side preprocessing optional |
| Compression config | `.env` + chain config | Per-tenant compression policy (on/off/aggressive/balanced) |
| Compression metrics | Local logs only | Aggregated savings dashboard per tenant |

```
SaaS Compression Architecture:

                    ┌──────────────────────┐
     Agent ────────→│  Gateway Ingress      │
                    │  (per-tenant routing) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Compression Service   │
                    │  (K8s with GPU node    │
                    │   pool + CPU fallback) │
                    │  ┌─────────────────┐  │
                    │  │ Headroom Pod    │  │
                    │  │ (GPU: 1-4 cards)│  │
                    │  └─────────────────┘  │
                    │  Or: Serverless GPU   │
                    │  (per-request billing) │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Router Node          │
                    │  (model selection +   │
                    │   cascade + circuit   │
                    │   breakers)           │
                    └──────────────────────┘
```

### 3.4 Protocol Conversion Layer

**Current State:**
- `request_converter.py` (38K): Anthropic Messages → OpenAI Chat Completions
  - System prompt → role-based conversion (`role:system` → `role:user` for OpenRouter compat)
  - Tool schema stripping (dedup, remove `additionalProperties: false`, truncate descriptions)
  - Tool output truncation (disabled by default for modern 1M-token models)
  - Reasoning config injection (`thinking` → `reasoning_effort`)
  - Model prefix stripping for provider-specific APIs
- `response_converter.py` (87K): OpenAI → Anthropic streaming + non-streaming response
  - Chunk reassembly, tool call fusion across multiple stream chunks
  - Content block restructuring (OpenAI flat → Anthropic content blocks)
  - Streaming with cancellation support
  - Error mapping between provider error models

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Conversion engine | In-process Python | Edge proxy service + SDK-side option |
| Tool schema stripping | Per-request transform | Configurable rules per tenant |
| Model prefix stripping | Hardcoded provider list | Plugin system for custom providers |
| Streaming | Direct `httpx` streaming | WebSocket relay + buffered reconnect |

The conversion layer is critical IP — it's what makes the gateway provider-agnostic. In SaaS, it becomes a **protocol translation service** that tenants can opt into or handle in their own SDK.

### 3.5 Proxy Chain & Pipeline System

**Current State:**

**Proxy Chain** (`config/proxy_chain.json`):
- Ordered service topology: `claude_code_proxy(:8082)` → `headroom(:8787)` → `cliproxyapi(:8317)` (disabled)
- Each entry has: id, name, type (http/cli), port, health_path, service_cmd, enabled
- Lifecycle management via `proxies` command (up/down/status/logs/config/restart)
- JSON Schema migrations for backward compatibility

**Pipeline System** (`pipeline.py`):
- Multi-step API chains: e.g. Transcribe (Whisper) → LLM (Proxy) → TTS (Piper)
- Steps defined in `proxy_chain.json` under `"pipelines"`
- Each step: url, method, input_field, output_field, headers
- Context passing between steps via dot-notation field extraction
- Use case: voice input → AI processing → voice output

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Chain config | Local JSON file | DB-backed per-tenant + global chain templates |
| Service lifecycle | tmux + shell scripts | Kubernetes deployments + Helm charts |
| Health checks | HTTP `/health` per port | K8s readiness/liveness probes |
| Pipelines | Sequential HTTP steps per request | Workflow engine (Temporal / Airflow) |
| Pipeline steps | Local services | Microservice mesh (Istio) |
| `proxies` command | Shell + tmux | kubectl + SaaS Admin Dashboard |

### 3.6 Usage Tracking & Analytics

**Current State:**
- **Backend**: SQLite database (`usage_tracking.db`) with 8 tables
  - `api_requests` — per-request metrics (model, provider, tokens, latency, cost)
  - `daily_usage` — daily rollups per (provider, model)
  - `model_limits`, `rate_limits`, `alert_rules`, `usage_reports`, `billing_plans`, `session_assignments`
- **Analytics API**: Timeseries queries (minute/hour/day/week), cost breakdowns, provider/model filters
- **Cost calculator**: `cost_calculator.py` with per-model lookup via `cost_lookup.py`
- **Usage tracker**: 60K `usage_tracker.py` — full request logging, sanitization, session tracking
- **Logging subsystem**: 7 loggers with structured JSONL (`logs/events.jsonl`)

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Database | SQLite file | PostgreSQL + TimescaleDB (time-series) |
| Request volume | Single user | 1000s of tenants × 1000s of requests |
| Cost tracking | Per-model pricing JSON | Real-time billing + invoicing |
| Analytics | `GET /api/analytics/timeseries` | Pre-computed rollups + OLAP cube |
| Log storage | Local files | ClickHouse / Loki for structured logs |
| Export | Local SQLite query | API-driven CSV/JSON/Parquet export |
| Retention | Manual cleanup | Tiered: hot (7d) / warm (90d) / cold (1y+) in S3 |

**SaaS Schema Extension:**

```sql
-- Multi-tenant additions to existing schema
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    api_key_hash TEXT NOT NULL,
    tier TEXT CHECK(tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMP DEFAULT NOW(),
    settings_json JSONB
);

ALTER TABLE api_requests ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE api_requests ADD COLUMN billed_amount DECIMAL(10,6);
CREATE INDEX idx_api_requests_tenant ON api_requests(tenant_id, created_at);
```

### 3.7 Alerting & Observability

**Current State:**
- **Alert Engine** (`alert_engine.py`): Rule-based alerts (cost spikes, error rate, token usage)
  - Conditions: metric + operator + threshold
  - Actions: webhook, log, local notification
  - Cooldown: configurable per rule
  - Severity: info → warning → critical
- **Predictive Alerting** (`predictive_alerting.py`): ML-based anomaly detection
  - Cost forecasting, usage trend analysis
  - Proactive budget breach warnings
- **Error Sink** (`error_sink.py`): Unified JSONL error logging
- **Reliability Score** (`reliability_feedback.py`): `R` score with S/A/B/C/F grading
  - Per-component breakdown: cascade health, circuit breaker status, latency
  - `GET /api/reliability?hours=24` — live dashboard endpoint
- **Structured Logger**: `events.jsonl` with per-request structured events
- **WebSocket Logs**: Real-time log streaming to web UI

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Alert rules | SQLite config | Multi-tenant alert rules + global system alerts |
| Notifications | Webhook only | Email, Slack, PagerDuty, Discord, webhook |
| Predictive | Local model | Tenant-specific + cross-tenant models |
| Reliability score | Per-instance | Fleet-wide + per-tenant |
| Error sink | Local JSONL | Centralized error service (Sentry) |
| Incident management | None | Integrated with alert escalation |
| Uptime monitoring | Self-check | External monitoring (Better Uptime / Checkly) |

### 3.8 Web Dashboard & Terminal Dashboard

**Current State:**

**Web Dashboard** (SvelteKit):
- 14 routes: Dashboard, Analytics, Chain, Alerts, Assignments, Crosstalk, Identifier Mappings, Real-time, Audit, Settings, Reports, Billing, Integrations, Dashboards
- 3 themes: Midnight Aurora (default dark), Ember Console (warm orange), Frost Spectrum (light)
- Component library: shadcn-svelte cards, dialogs, Lucide icons
- Particles background, animated transitions
- Pages: Analytics query builder, chain visualization, alerts management, config editor, real-time waterfall

**Terminal Dashboard** (Rich TUI):
- Edge modules (performance, requests, circuits, latency)
- Central waterfall for live request flow
- Moveable module positioning
- Interactive controls

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Auth | None / single-user | OAuth2 (Google, GitHub) + API keys |
| Dashboard routes | Same for all | Tenant-aware: Pro features gated |
| Themes | 3 dark + light | Per-tenant branding/theming |
| Data source | Local SQLite | PostgreSQL + real-time WebSocket from services |
| Chain editor | Config file | Drag-drop UI with save-to-infra |
| Sharing | None | Shareable dashboard links, export to PDF |
| Multi-user | RBAC model exists | Full team management + audit log |

### 3.9 User Management & RBAC

**Current State:**
- `user_manager.py`: Basic login/password auth
- `users_rbac.py` (15K): Role-based access control
  - Roles: admin, operator, viewer
  - Endpoint-level permissions
  - Per-api-key role assignment
- `api/users` + `api/users_rbac`: User CRUD, role assignment
- `billing.py`: Basic billing plan framework

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Auth | Local password | OAuth2 + SAML + API keys |
| RBAC | admin/operator/viewer | Custom roles + permission sets per tenant |
| SSO | N/A | Google Workspace, Microsoft Entra, Okta |
| API Keys | Single key | Scoped keys (read-only, specific models, time-bound) |
| Teams | N/A | Team management, org hierarchy |
| Audit log | Local | Immutable audit trail, SIEM export |
| Billing | Skeleton | Metered billing (tokens, requests, compression) |

### 3.10 Launcher & CLI Layer

**Current State:**
- **`xx` encoding**: 3-character agent launcher (`xx cip` = Claude Code Init Proxy)
  - Position 1: Agent (c=Claude, h=Hermes, x=Codex, q=Qwen, p=Pi, g=Antigravity, a=Ante, o=OpenCode)
  - Position 2: Mode (i=init, c=continue, n=non-interactive, s=session)
  - Position 3: Route (p=proxy, b=bypass, d=debug)
  - Position 4 (optional): Tier (d=DeepSeek, n=Nemotron, k=Kimi, m=model-scan best, f=model-scan free)
- **`cg_run` crash guard**: tmux-based session recovery wrapper
- **`proxies` lifecycle manager**: up/down/status/logs/watch/config/restart
- **Scripts**: `install-aliases.sh`, `headroom-start.sh`, `ccp-launch.sh`
- **Per-tool correct flags baked in**: No more wrong `--dangerously-skip-permissions` flags

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Launcher | Local `xx` shell function | SDK client library (pip/npm/cargo) |
| Agent config | Shell aliases → JSON config | `clutch configure` CLI → SaaS API |
| Crash guard | tmux | Cloud session persistence + auto-reconnect |
| Lifecycle | `proxies` script → tmux | Health-checked K8s + auto-scaling |
| Install | git clone + bash script | `pip install clutch-gateway` / one-click deploy |

### 3.11 Crosstalk (Multi-Agent Orchestration)

**Current State:**
- **Crosstalk Engine** (`crosstalk_engine.py`, `crosstalk_cli.py`, `crosstalk_studio.py`):
  - Multi-agent conversation orchestration
  - Agents: brainstormer, devil-advocate, scientist, dreamer-ai, philosopher, backrooms-explorer
  - Each agent has its own system prompt loaded from `configs/crosstalk/prompts/`
  - Full turn-based conversation between agents with a chair/moderator
  - API endpoints: setup, run, status, list, delete
  - CLI mode + Studio mode (interactive)

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Orchestrator | In-process Python | Distributed agent runtime (Temporal/Durable) |
| Agent prompts | Local JSON files | Prompt registry per tenant + global library |
| Conversations | In-memory | Persistent + searchable per tenant |
| Collaboration | Single session | Team-shared crosstalk sessions |
| Agent registry | Fixed set of agents | Plugin marketplace for custom agents |

### 3.12 Model-Scan Integration

**Current State:**
- **model-scan** as external tool (separate repo)
- Shared contract: `routing_snapshot.schema.json`
- Producer: model-scan scrapes OpenRouter → scores models → writes snapshot
- Consumer: Clutch Gateway loads snapshot → binds to tier assignments
- Runtime reload: SIGHUP / `POST /api/proxy/reload-models`
- Staleness detection: cache TTL + data age wall clock
- Profile `slot_bindings`: per-profile overlay on default tier assignments
- Selection policies: `static`, `free`, `quality`, `roles`, `budget:<ceiling>`

**SaaS Transformation:**

| Component | Local | SaaS |
|-----------|-------|------|
| Model data | Local snapshot file | Shared model intelligence service |
| Scanning | Separate cron job | Continuous provider monitoring service |
| Scoring | Local-only | Fleet-wide score aggregation |
| Selection | Per-instance | Global + per-tenant override |
| Provider health | Single machine | Geo-distributed probes across all providers |

---

## 4. SaaS Deployment Topology

```
                         ┌─────────────────────────────────────────┐
                         │            CDN / Global Load Balancer     │
                         │         (Cloudflare / AWS CloudFront)     │
                         └──────────────────┬──────────────────────┘
                                            │
                      ┌─────────────────────┼─────────────────────┐
                      ▼                     ▼                     ▼
              ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
              │  API Gateway  │    │  API Gateway  │    │  API Gateway  │
              │  (us-east-1)  │    │  (eu-west-1)  │    │  (ap-southeast-1)│
              └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
                     │                   │                   │
              ┌──────▼───────────────────▼───────────────────▼──────┐
              │              Proxy Fleet (Kubernetes)                │
              │                                                      │
              │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
              │  │ Router   │  │ Router   │  │ Router   │           │
              │  │ Pod      │  │ Pod      │  │ Pod      │           │
              │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
              │       │              │              │                 │
              │  ┌────▼──────────────▼──────────────▼────┐           │
              │  │         Redis Cluster                   │           │
              │  │  (Sessions / Circuit Breakers / Cache)  │           │
              │  └───────────────────┬───────────────────┘           │
              │                      │                                │
              │  ┌───────────────────▼───────────────────┐           │
              │  │         PostgreSQL + TimescaleDB        │           │
              │  │  (Tenants / Usage / Analytics / Config)  │           │
              │  └───────────────────┬───────────────────┘           │
              └──────────────────────┼────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                            │
         ▼                           ▼                            ▼
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│  Compression GPU  │   │  Model Intelligence   │   │  Observability   │
│  Pool (K8s GPU    │   │   Service             │   │  Stack            │
│   node group)     │   │  (Provider health +   │   │                  │
│   Serverless or   │   │   model scoring)      │   │  Grafana         │
│   Dedicated       │   │                       │   │  Loki            │
└──────────────────┘   └──────────────────────┘   │  Tempo           │
                                                   │  Sentry          │
                                                   └──────────────────┘
```

### Service Decomposition

| Service | Replicas | Dependencies | Scaling Basis |
|---------|----------|-------------|---------------|
| **Router API** | 5-20 | Redis, PG | Request volume / tenant count |
| **Compression** | 2-10 (GPU) | (standalone) | Context size × request rate |
| **Model Intel** | 2-5 | PG | Provider count + scan frequency |
| **Usage Aggregator** | 2-3 | PG, Redis | Write volume |
| **Alert Engine** | 2-3 | PG, Redis | Alert rule count |
| **Web UI** | 2-5 | Router API | Active users |
| **WebSocket** | 3-5 | Redis pub/sub | Concurrent dashboard users |

### Data Stores

| Store | Technology | Purpose |
|-------|-----------|---------|
| **Primary DB** | PostgreSQL 16 | Tenants, configs, users, billable usage |
| **Time-series** | TimescaleDB | Per-request metrics, rollups |
| **Cache** | Redis 7 | Sessions, circuit breakers, rate-limit buckets |
| **Object Storage** | S3-compatible | Log archives, compressed session history |
| **Search** | OpenSearch (optional) | Log search, full-text analytics |
| **Queue** | RabbitMQ / Redis Streams | Async usage aggregation, alert dispatch |

### API Key → Tenant Resolution

```
1. Client sends request with `Authorization: Bearer ccp_sk_...`
2. Gateway extracts prefix (`ccp_sk_`) → identifies it's a Clutch key
3. Redis cache: `hash("ccp_sk_...")` → `{tenant_id, tier, permissions}`
4. Cache miss → PostgreSQL lookup
5. All downstream services receive tenant_id in context headers:
   `X-Clutch-Tenant-Id`, `X-Clutch-Tier`
```

---

## 5. Project Health Assessment

### File Freshness (Last Modified)

| Layer | Files | Avg Age | Health |
|-------|-------|---------|--------|
| **Core** (api, core/) | 43 files | ~30 days | ✅ Active development |
| **Services** | 60+ files | ~45 days | ✅ Active |
| **Compression** (rtk/) | 20+ files | ~60 days | ✅ Stable |
| **Web UI** (web-ui/src/) | 40+ files | ~25 days | ✅ Active |
| **Dashboard** (dashboard/) | 12 files | ~45 days | ✅ Stable |
| **Infrastructure** | 10+ scripts | ~30 days | ✅ Active |
| **Docs** | 50+ files | 30-90 days | ⚠️ Some stale |
| **Archive** (archive/) | 15 files | June 1 cleanup | ✅ Archived |
| **SNAKESKIN/** | 14 files | 60+ days | ⚠️ Research notes |
| **Configs** (configs/) | 10 files | 30+ days | ⚠️ Needs audit |

### Test Coverage

- Tests in `tests/` directory exist but coverage is patchy
- Recent work (Jun 2-5) added contract tests for model-scan snapshot schema
- Hypothesis-based property tests for config resolver precedence
- Regression test for cascade-exhausted error (test_cascade_exhausted_error.py)
- **Gap**: No comprehensive test suite for core proxy path

### Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite not suitable for multi-tenant SaaS | Blocking | Replace with PostgreSQL + TimescaleDB |
| 92K `client.py` is a monolith | Maintainability | Split into provider-specific handlers |
| No CI/CD pipeline in repo | Engineering velocity | Add GitHub Actions + deployment pipeline |
| No Docker Compose for full stack | Onboarding friction | Add compose for gateway + headroom + DB |
| Single-process in-memory state | HA failure | Add Redis for distributed state |
| Hardcoded user config paths | Portability | Env-var all paths, cloud-config compatible |

---

## 6. Recommended SaaS Architecture Roadmap

### Phase 0: Containerization (Week 1-2)
- [ ] Dockerfile for gateway (multi-stage Python build)
- [ ] Docker Compose: gateway, headroom, postgres, redis, web-ui
- [ ] Environment parity: local dev = production container config
- [ ] Health check standardization for K8s

### Phase 1: Database Migration (Week 2-4)
- [ ] SQLite → PostgreSQL migration tooling
- [ ] Usage tracker: PostgreSQL adapter with TimescaleDB hypertables
- [ ] Multi-tenant schema migration
- [ ] Connection pooling (PgBouncer)
- [ ] Alembic migrations for schema versioning

### Phase 2: Auth & Multi-Tenancy (Week 3-5)
- [ ] API key management service (key generation, hashing, rotation)
- [ ] Tenant isolation in all queries
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Rate limiting per tenant (Redis sliding window)
- [ ] Team management API

### Phase 3: Horizontal Scaling (Week 4-8)
- [ ] Redis-backed distributed circuit breaker
- [ ] Redis session store (replace in-process state)
- [ ] Stateless router nodes (no local file dependencies)
- [ ] Kubernetes manifests + Helm chart
- [ ] Horizontal pod autoscaling (HPA) based on request volume

### Phase 4: SaaS Commercial Features (Week 6-10)
- [ ] Metered billing (token-based + request-based + compression usage)
- [ ] Per-tenant compression policies (off/balanced/aggressive)
- [ ] Usage dashboards with cost forecasting
- [ ] Alert notifications via email/Slack/webhook
- [ ] Model intelligence service: cross-tenant provider health aggregation
- [ ] Published API documentation (Swagger/Redoc)

### Phase 5: Enterprise (Week 8-12)
- [ ] SSO (SAML, Microsoft Entra, Okta)
- [ ] Audit logging to SIEM
- [ ] Custom model provider plugins
- [ ] SLA monitoring and uptime dashboards
- [ ] On-prem deployment option (Docker + license key)

---

## Appendix: Key Source File Index

| File | Lines | Purpose | Freshness |
|------|-------|---------|-----------|
| `src/core/client.py` | 92K | LLM client, cascade engine, circuit breakers | Jun 2 ✅ |
| `src/api/endpoints.py` | 89K | Core proxy endpoints | Jun 2 ✅ |
| `src/api/web_ui.py` | 80K | Web UI static server | May 14 ⚠️ |
| `src/services/conversion/response_converter.py` | 87K | OpenAI → Anthropic response conversion | May 14 ⚠️ |
| `src/services/usage/usage_tracker.py` | 60K | SQLite-based usage tracking | May 19 ✅ |
| `src/api/system_monitor.py` | 41K | Full system health monitoring | Apr 1 ⚠️ |
| `src/services/conversion/request_converter.py` | 38K | Anthropic → OpenAI request conversion | Jun 2 ✅ |
| `src/main.py` | 34K | FastAPI app assembly | Jun 2 ✅ |
| `src/api/openai_endpoints.py` | 34K | OpenAI-compatible API | Jun 2 ✅ |
| `src/services/logging/proxy_logger.py` | 32K | Proxy-specific logging | Jun 2 ✅ |
| `config/proxy_chain.json` | — | Service topology + assignments | Jun 2 ✅ |
| `compression/headroom/` | 200+ | GPU context compression library | ~Apr 2 ⚠️ |
| `compression/rtk/` | 200+ | Terminal compression filters | ~Apr 2 ⚠️ |
| `web-ui/src/` | 40 files | SvelteKit dashboard | May 14 ⚠️ |

**Legend**: ✅ Recently updated / ⚠️ Could use refresh / ❌ Stale

---

## Appendix: Stale / Archived Assets

These were moved to `archive/2026-06-01-cleanup/` during the June 1 cleanup:

| Path | Content | Action |
|------|---------|--------|
| `archive/root-docs/` | Old USERPROMPTS, session notes, handoff docs | Archived |
| `archive/root-drafts/` | Pre-June design drafts, requirements | Archived |
| `archive/plans/old/` | Superseded implementation plans | Archived |
| `SNAKESKIN/` | 14 research notes (401 errors, tool call fixes, etc.) | ⚠️ Needs triage |
| `compression/docs/` (legacy) | 20+ guide files pre-unified compression stack | ⚠️ May be stale |

---

*Report generated 2026-06-06 — based on source tree audit of `claude-code-proxy` (commit ~Jun 2-6 2026)*
