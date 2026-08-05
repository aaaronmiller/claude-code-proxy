# Feature Inventory — Claude Code Proxy Fork Analysis

## Methodology
- Compared TARGET (aaaronmiller fork) against UPSTREAM (fuergaosi233 v1.0.0)
- Files examined: src/**, start_proxy.py, config/, compression/, cli/, web-ui/, docs/
- Date: 2026-04-21

## NEW TOP-LEVEL DIRECTORIES (Fork Additions)

| Directory | Purpose | Status |
|-----------|---------|--------|
| `compression/` | Compression stack (Headroom + RTK integration) | COMPLETE |
| `cli/` | Standalone CLI tools | COMPLETE |
| `web-ui/` | Svelte + bits-ui web dashboard | COMPLETE |
| `configs/` | Configuration presets (crosstalk, prompts) | COMPLETE |
| `docs/` | Extended documentation (API, guides, examples) | COMPLETE |
| `tools/` | Utility scripts | COMPLETE |
| `batch/` | Batch processing scripts | COMPLETE |
| `audit-reports/` | Audit output files | COMPLETE |
| `profiles/` | User profiles/modes | COMPLETE |
| `logs/` | Local log storage | COMPLETE |
| `model-scraper/` | OpenRouter model scraper | COMPLETE |
| `SNAKESKIN/` | Unknown (possibly build artifacts) | UNKNOWN |

## NEW Python PACKAGES in src/ (Service Layer Architecture)

The fork completely refactored src/ from a flat structure to a layered service architecture:

### src/services/ (NEW - comprehensive service layer)
- `services/usage/` - Usage tracking, token counting, cost analytics
- `services/models/` - Model filtering, rankings, limits enforcement
- `services/conversion/` - Request/response conversion (moved from src/conversion/)
- `services/logging/` - Structured logging, request logging, compact logger
- `services/providers/` - Provider-specific implementations
- `services/cli/` - CLI command implementations
- `services/prompts/` - Prompt injection middleware, templates
- `services/tools/` - Tool handling and routing
- `services/metrics/` - Metrics collection and exposition
- `services/billing/` - Billing and quota management
- `services/benchmarking/` - Model benchmarking suite
- `services/openrouter_model_scout/` - OpenRouter model discovery
- `services/ide/` - IDE integrations

### src/dashboard/ (NEW - web dashboard backend)
- Dashboard module system
- Real-time data hooks
- Widget infrastructure

### src/conversation/ (NEW - conversation orchestration)
- Crosstalk orchestrator
- Multi-model conversation state
- Session management

### src/auth/ (NEW - authentication/authorization)
- API key validation
- Request authentication
- Rate limiting per key

### src/utils/ (NEW - utility functions)
- Common helpers
- Data validation

### src/static/ (NEW - static web assets)
- CSS stylesheets
- JavaScript bundles
- Images/icons

### src/models/scout/ (NEW - model scouting)
- Model discovery
- Capability detection

## KEY NEW/CHANGED FILES WITH FUNCTIONAL CHANGES

### 1. start_proxy.py — MASSIVE expansion
UPSTREAM: 74 lines, simple uvicorn runner
FORK: 412 lines, full CLI suite with 15 argument groups

**New CLI Commands Added:**
- `--setup` - First-time wizard
- `--settings` - Unified settings TUI
- `--doctor` - Health check + auto-fix
- `--select-models` - Interactive model selector
- `--set-big`, `--set-middle`, `--set-small` - Quick model config
- `--show-models` - List available models
- `--check-endpoints` - Connectivity check
- `--update-models` - Scrape model stats
- `--rank-models` - AI-rank free models
- `--config` - Show configuration
- `--validate-config` - Validate config
- `--dry-run` - Validate without starting
- `--analytics` - View usage stats
- `--crosstalk-studio` - Launch Crosstalk TUI
- `--crosstalk-init` - Crosstalk setup wizard
- `--crosstalk` - Quick crosstalk setup
- `--configure-prompts` - Prompt injection configurator
- `--configure-terminal` - Terminal output configurator
- `--configure-dashboard` - Dashboard module configurator
- `--configure-advanced` - Advanced config TUI
- `--list-modes`, `--save-mode`, `--load-mode`, `--delete-mode` - Mode management
- `--reasoning-effort`, `--verbosity`, `reasoning-exclude` - Reasoning controls
- `--model-cascade` - Enable cascade fallback
- `--system-prompt-big/middle/small` - Custom system prompts

**New Configuration Groups:**
- Model tier configuration (BIG/MIDDLE/SMALL)
- Reasoning parameters
- Mode/profile management
- Crosstalk orchestration
- Interactive configuration wizards

**Status:** COMPLETE

### 2. src/api/endpoints.py — EXPLOSION of endpoints
UPSTREAM: ~85 lines, 2 endpoints (chat completions, token count)
FORK: ~700 lines, 20+ endpoints

**New API Endpoints:**
- `POST /api/v1/chat/completions` — enhanced with deduplication
- `POST /api/v1/token/count` — enhanced with model limits
- `GET /api/v1/models` — with filtering, sorting, caching
- `GET /api/v1/models/provider` — provider-specific models
- `GET /api/v1/models/free` — free model rankings
- `GET /api/v1/models/limits` — model quota limits
- `GET /api/v1/models/scout` — OpenRouter model scouting
- `POST /api/v1/crosstalk/setup` — configure crosstalk
- `POST /api/v1/crosstalk/run` — start crosstalk session
- `GET /api/v1/crosstalk/status` — crosstalk status
- `GET /api/v1/crosstalk/list` — list sessions
- `DELETE /api/v1/crosstalk/delete` — delete session
- `GET /api/v1/analytics/usage` — usage analytics
- `GET /api/v1/analytics/cost` — cost breakdown
- `POST /api/v1/dashboard/register-module` — dashboard module registration
- `GET /api/v1/dashboard/modules` — list dashboard modules
- `GET /api/v1/health` — health check with dependencies
- `POST /api/v1/validate-key` — API key validation
- `GET /api/v1/config` — current configuration (sanitized)
- `POST /api/v1/billing/check` — billing/quota check

**New Middleware:**
- Request deduplication (hash-based, time-windowed)
- Circuit breaker per model
- Usage tracking middleware
- Prompt injection middleware
- Request/response logging
- Model limits enforcement
- Authentication

**Status:** COMPLETE

### 3. src/core/config.py — Drastically expanded
UPSTREAM: ~70 lines, simple env var loading
FORK: ~207 lines, full config management system

**New Features:**
- Dotenv support (loads .env file)
- API key format validation by provider (regex patterns)
- Per-provider configuration objects
- Model tier definitions (BIG/MIDDLE/SMALL/SCOUT)
- Model limits database integration
- Feature flags
- Settings persistence
- Configuration validation
- Custom router module support
- Proxy chain configuration
- Multi-provider endpoint management

**New Config Options:**
```python
API_KEY_PATTERNS = {openai, openrouter, anthropic, google, gemini, azure}
MODEL_TIERS = {big, middle, small, scout}
ENABLE_CIRCUIT_BREAKER
ENABLE_REQUEST_DEDUPLICATION
ENABLE_PROMPT_INJECTION
CASCADE_FALLBACK_ENABLED
MAX_CONCURRENT_REQUESTS
REQUEST_TIMEOUT
LOG_LEVEL
```

**Status:** COMPLETE

### 4. src/core/client.py — Circuit breakers + cascade
UPSTREAM: Simple OpenAIClient wrapper
FORK: Added circuit breaker registry, dynamic fallback, VibeProxy support

**New Features:**
- Circuit breaker registry (module-level shared state)
- `_get_circuit_breaker()` factory with failure thresholds
- `_is_cb_open()` circuit breaker state check
- `_build_or_models_list()` - filters models with open breakers, caps at 3 for OR
- `_get_dynamic_fallback_models()` - loads free model rankings cache
- `VibeProxyUnavailableError` exception
- Cascade fallback logic with circuit breaker awareness

**Circuit Breaker Settings:**
- failure_threshold: 3
- success_threshold: 1  
- timeout: 300s (5 min)

**Status:** COMPLETE

### 5. New files: src/request_deduplicator.py
Request deduplication system to prevent duplicate terminal output from client retries.

**Features:**
- Content hash generation
- Time-windowed deduplication (configurable window)
- In-memory cache with LRU eviction
- Per-request tracking with timestamps
- Thread-safe with Lock

**Status:** COMPLETE

### 6. New directory: compression/ — Compression Stack (MAJOR NEW FEATURE)
 Entire compression layer with Headroom + RTK integration.

**Key Files:**
- `compression/lib/stack_manager.py` - Orchestrates both layers
- `compression/lib/headroom_adapter.py` - Headroom proxy integration  
- `compression/lib/rtk_adapter.py` - RTK command compression
- `compression/bin/compressctl` - Control binary
- `compression/scripts/compression-stack.sh` - Start all services
- `compression/scripts/install-all.sh` - Unified installer
- `compression/scripts/compression-dashboard.py` - Web dashboard
- `compression/systemd/*.service` - systemd units (5 services)

**Services:**
1. `headroom-proxy.service` - Headroom compression proxy (:8787)
2. `compression-tracker.service` - Token usage tracker
3. `compression-dashboard.service` - Web dashboard (:8899)
4. `gpu-resident-manager.service` - GPU memory manager
5. `surface-audit.service` - System audit (Surface-specific)

**Features:**
- 97% compression rate claim
- GPU acceleration (CUDA/ROCm/Level Zero)
- Multi-CLI support (Claude, Qwen, Codex, OpenCode, OpenClaw, Hermes)
- Real-time dashboard (web + terminal)
- Multi-tier compression (default + small model)
- Semantic caching
- RTK command compression (60-90% savings)

**Status:** COMPLETE, integrated, auto-start enabled

---

[CONTINUING ANALYSIS IN NEXT SCRATCH FILE DUE TO LENGTH...]
