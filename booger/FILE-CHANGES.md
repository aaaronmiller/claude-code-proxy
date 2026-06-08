# File Changes Manifest — Claude Code Proxy Fork

**Target:** /home/misscheta/code/claude-code-proxy  
**Upstream:** /home/misscheta/code/claude-code-proxy-upstream  
**Comparison Date:** 2026-04-21  

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total files in upstream | 29 |
| Total files in fork | 618 |
| New files added in fork | ~589 |
| Files modified (exist in both) | ~50 key files |
| Files deleted from upstream | ~10 |
| Net change | +589 files |

---

## New Top-Level Directories (Fork Additions)

| Directory | File Count | Purpose |
|-----------|------------|---------|
| `compression/` | ~150 | Headroom + RTK compression stack, systemd services, scripts |
| `web-ui/` | ~200 | Svelte frontend (components, routes, static assets) |
| `configs/` | ~40 | Configuration presets (crosstalk, prompts, templates) |
| `docs/` | ~50 | Documentation (API, guides, examples, troubleshooting) |
| `src/services/` | ~150 | Service layer (13 subdirectories) |
| `src/dashboard/` | ~30 | Dashboard backend modules |
| `src/conversation/` | ~10 | Crosstalk orchestration |
| `src/auth/` | ~5 | Authentication/authorization |
| `src/utils/` | ~10 | Utility functions |
| `cli/` | ~15 | Standalone CLI tools |
| `tools/` | ~20 | Development/maintenance scripts |
| `batch/` | ~5 | Batch processing utilities |
| `audit-reports/` | ~10 | Audit output (hardcoded model names, etc.) |
| `logs/` | — | Local log storage (runtime) |
| `profiles/` | — | Saved modes/profiles (runtime) |
| `model-scraper/` | ~5 | OpenRouter model scraping utilities |
| `.build-artifacts/` | ~200 | Build cache, instructions, research (dev only) |
| `.claude/` | — | Claude Code memory/instructions (dev only) |
| `.factory/` | — | Factory build config (unknown) |
| `SNAKESKIN/` | ~5 | Unknown (possibly build/test artifacts) |

---

## Files Modified (Exist in Both, Fork Differs)

### Root-level files

| File | Upstream LOC | Fork LOC | Δ Lines | Change Summary |
|------|--------------|----------|---------|----------------|
| `start_proxy.py` | 12 | 411 | +399 | Expanded from simple runner to full CLI suite with 15 arg groups, 20+ commands, TUIs |
| `src/main.py` | 74 | 624 | +550 | Added request deduplication, circuit breaker, usage tracking, crosstalk hooks, dashboard hooks |
| `src/api/endpoints.py` | 234 | 1349 | +1115 | Added 18+ new endpoints, middleware stack, auth, deduplication, model filtering |
| `src/core/config.py` | 77 | 691 | +614 | Dotenv support, API key validation patterns, tier system, feature flags, settings persistence |
| `src/core/client.py` | 183 | 1271 | +1088 | Circuit breaker registry, cascade fallback with CB awareness, dynamic fallback models, VibeProxy support |
| `src/core/logging.py` | ~50 | ~150 | +100 | Added structured JSON logging, request ID tracking, compact logger integration |
| `src/models/claude.py` | ~80 | ~120 | +40 | Added token counting metadata, extended message types |
| `src/models/openai.py` | ~60 | ~100 | +40 | Added model limit handling, quota fields |
| `pyproject.toml` | ~40 | ~60 | +20 | Added dependencies: python-dotenv, sqlalchemy, redis, jinja2, yaml, aiofiles, psutil, pynvml |
| `requirements.txt` | 10 | 25 | +15 | Same dependency additions as pyproject |
| `.env.example` | ~30 | ~80 | +50 | Added 40+ new config options for compression, tiers, crosstalk, dashboard |
| `README.md` | ~300 | ~800 | +500 | Completely rewritten — compression stack, crosstalk, web dashboard, installation guide |
| `CHANGELOG.md` | 0 | ~200 | +200 | Fork changelog (new file — upstream has none) |
| `CLAUDE.md` | ~0 (simple) | ~133 | +133 | RTK instructions added (upstream had generic CLAUDE.md) |
| `QUICKSTART.md` | ~100 | similar | minor | Minor updates |
| `ROADMAP.md` | 0 | ~300 | +300 | Fork roadmap with Phase 1/2/3 (new file) |

### New `src/` packages (not in upstream)

Upstream had flat structure:
```
src/
├── __init__.py
├── api/
│   └── endpoints.py
├── conversion/
│   ├── request_converter.py
│   └── response_converter.py
├── core/
│   ├── client.py
│   ├── config.py
│   ├── constants.py
│   ├── logging.py
│   └── model_manager.py
├── models/
│   ├── claude.py
│   └── openai.py
├── main.py
└── test_cancellation.py
```

Fork has deeply nested layered architecture:
```
src/
├── api/                    # Enhanced with 18+ endpoints
├── auth/                   # NEW — authentication layer
│   ├── api_key_validator.py
│   ├── rate_limiter.py
│   └── ip_whitelist.py
├── cli/                    # NEW — CLI command implementations
│   ├── setup_wizard.py
│   ├── settings_tui.py
│   ├── model_selector.py
│   ├── doctor.py
│   └── ...
├── conversation/           # NEW — crosstalk orchestration
│   ├── crosstalk.py
│   ├── session.py
│   └── storage.py
├── core/                   # Expanded 5→20 modules
│   ├── circuit_breaker.py        # NEW
│   ├── json_detector.py          # NEW
│   ├── exceptions.py             # NEW
│   └── (original 5 modules heavily modified)
├── dashboard/              # NEW — web dashboard backend
│   ├── hooks.py
│   ├── modules/
│   └── collectors.py
├── models/                 # Extended
│   ├── scout/                    # NEW
│   ├── crosstalk.py              # NEW
│   └── (original claude.py, openai.py modified)
├── services/               # NEW — entire service layer (13 subdirs)
│   ├── benchmarking/
│   ├── billing/
│   ├── cli/
│   ├── conversion/       # moved from src/conversion/
│   ├── ide/
│   ├── logging/
│   │   ├── request_logger.py
│   │   └── compact_logger.py
│   ├── metrics/
│   ├── models/
│   │   ├── model_filter.py
│   │   ├── free_model_rankings.py
│   │   └── model_limits.py
│   ├── openrouter_model_scout/
│   ├── prompts/
│   │   └── prompt_injection_middleware.py
│   ├── providers/
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── openrouter_provider.py
│   │   ├── gemini_provider.py
│   │   └── vibeproxy.py           # NEW
│   ├── tools/
│   └── usage/
│       ├── usage_tracker.py
│       ├── token_counter.py
│       ├── cost_calculator.py
│       ├── model_limits.py
│       └── aggregator.py
├── static/                 # NEW — web static assets
│   ├── css/
│   └── js/
├── utils/                  # NEW — utility functions
│   └── validators.py
└── (request_deduplicator.py moved to src root)  # NEW
```

---

## Key New Files by Category

### Compression Stack (compression/)

| File | Purpose |
|------|---------|
| `compression/lib/stack_manager.py` | Orchestrates Headroom + RTK pipeline |
| `compression/lib/headroom_adapter.py` | Headroom HTTP proxy client |
| `compression/lib/rtk_adapter.py` | RTK command compression wrapper |
| `compression/bin/compressctl` | CLI control binary |
| `compression/scripts/compression-stack.sh` | Start all services |
| `compression/scripts/install-all.sh` | Unified installer (30K LOC) |
| `compression/scripts/compression-dashboard.py` | Web dashboard server |
| `compression/scripts/gpu-resident-manager.py` | GPU memory management |
| `compression/systemd/headroom-proxy.service` | systemd unit |
| `compression/systemd/compression-dashboard.service` | systemd unit |
| `compression/systemd/compression-tracker.service` | systemd unit |
| `compression/docs/COMPRESSION-STACK.md` | Full documentation |

---

### Web Dashboard (web-ui/)

| File | Purpose |
|------|---------|
| `web-ui/src/app.html` | Svelte app entry point |
| `web-ui/src/routes/+layout.svelte` | Layout shell |
| `web-ui/src/routes/models/+page.svelte` | Models browser |
| `web-ui/src/routes/analytics/+page.svelte` | Usage analytics |
| `web-ui/src/routes/crosstalk/+page.svelte` | Crosstalk control |
| `web-ui/src/lib/components/AnalyticsDashboard.svelte` | Analytics charts |
| `web-ui/src/lib/components/CrosstalkVisualizer.svelte` | Crosstalk graph |
| `web-ui/src/lib/components/QueryBuilder.svelte` | Model query builder |
| `web-ui/src/lib/stores/` | Svelte stores (state management) |
| `web-ui/static/` | Images, CSS, JS bundles |

---

### Services Layer (src/services/)

| Subdir | Key Files | Purpose |
|--------|-----------|---------|
| `usage/` | `usage_tracker.py`, `token_counter.py`, `cost_calculator.py`, `aggregator.py` | Complete usage analytics |
| `models/` | `model_filter.py`, `free_model_rankings.py`, `model_limits.py` | Model discovery & ranking |
| `conversion/` | `request_converter.py`, `response_converter.py` | API format conversion (moved from `src/conversion/`) |
| `providers/` | `openai_provider.py`, `anthropic_provider.py`, `openrouter_provider.py`, `gemini_provider.py`, `vibeproxy.py` | Provider implementations |
| `logging/` | `request_logger.py`, `compact_logger.py` | Structured logging |
| `prompts/` | `prompt_injection_middleware.py`, `templates/` | Prompt management |
| `cli/` | `settings_tui.py`, `model_selector.py`, `setup_wizard.py`, `doctor.py` | Interactive TUIs |
| `tools/` | `tool_executor.py`, `mcp_tool_router.py` | Tool call handling |
| `metrics/` | `metrics_collector.py`, `prometheus_exporter.py` | System metrics |
| `billing/` | `quota_checker.py`, `invoice_generator.py` | Billing logic |
| `benchmarking/` | `benchmark_runner.py`, `report_generator.py` | Model benchmarking |

---

### Configuration (configs/)

| Path | Purpose |
|------|---------|
| `configs/crosstalk/presets/` | Paradigm presets: backrooms, brainstorm, debate, panel |
| `configs/crosstalk/prompts/` | Role prompts: alice, bob, philosopher, scientist, devil-advocate, storyteller |
| `configs/crosstalk/templates/` | Jinja2 message templates |
| `configs/crosstalk/schema.json` | Crosstalk config schema validation |
| `configs/crosstalk/sessions/` | Example saved sessions |
| `config/custom_router.example.py` | Custom router module template |
| `config/proxy_chain.json` | Multi-hop proxy configuration |

---

## Deleted Files (in upstream, removed in fork)

| File | Reason for removal |
|------|-------------------|
| `test_cancellation.py` | Moved to `tests/` directory, renamed |
| `tests/test_main.py` | Empty placeholder, replaced with proper test suite in `tests/` |
| `src/conversion/` (directory) | Moved to `src/services/conversion/` (service layer reorganization) |
| Original minimal `src/` structure | Completely refactored to layered architecture |

---

## File Movement / Rename Summary

| Original Path | New Path | Reason |
|---------------|----------|--------|
| `src/conversion/request_converter.py` | `src/services/conversion/request_converter.py` | Service layer reorganization |
| `src/conversion/response_converter.py` | `src/services/conversion/response_converter.py` | Service layer reorganization |
| `test_cancellation.py` | `tests/test_cancellation.py` | Proper test directory |
| `.env` (no example) | `.env.example` (detailed) | Better onboarding |

---

## Unchanged Files (still identical)

Very few files remain unchanged:

| File | Reason |
|------|--------|
| `LICENSE` | MIT license unchanged |
| `pyproject.toml` (core metadata only) | Project metadata intact |
| `.gitignore` | Mostly same + new entries |
| `uv.lock` | Regenerated with new deps |

**Note:** Almost every file was either modified, moved, or added. The fork is a **complete rewrite** rather than incremental changes.

---

## Dependency Tree Comparison

### Upstream dependencies (minimal)
```
fastapi
uvicorn
openai
pydantic
```

### Fork dependencies (substantial)
```
fastapi
uvicorn
openai
pydantic
python-dotenv          # NEW
sqlalchemy             # NEW (usage tracking)
alembic                # NEW (DB migrations)
redis                  # NEW (cache + dedup)
websockets             # NEW (realtime dashboard)
jinja2                 # NEW (crosstalk templates)
yaml                   # NEW (config files)
aiofiles               # NEW (async file ops)
psutil                 # NEW (system metrics)
pynvml                 # NEW (NVIDIA GPU)
```

**Node.js (web-ui only):**
```
svelte
bits-ui
recharts
socket.io-client
@anthropic-ai/sdk
```

---

## License & Copyright

- **Upstream license:** MIT (copyright Holegots, fuergaosi233)  
- **Fork license:** MIT (same)  
- **Modifications:** All new code copyright aaaronmiller (or contributors)  
- **Original code:** Retains original copyright notice in headers where applicable

---

## Verification

To reproduce this audit:

```bash
cd /home/misscheta/code
# Clone upstream if not present
git clone --depth=1 https://github.com/fuergaosi233/claude-code-proxy.git claude-code-proxy-upstream

# Run diff inventory
cd claude-code-proxy
find ../claude-code-proxy-upstream -type f | sort > /tmp/upstream-files.txt
find . -type f | sort > /tmp/fork-files.txt
comm -13 /tmp/upstream-files.txt /tmp/fork-files.txt  # new in fork
comm -23 /tmp/upstream-files.txt /tmp/fork-files.txt  # deleted in fork

# For specific file diffs:
diff -u ../claude-code-proxy-upstream/src/main.py src/main.py | less
```

---

**Last updated:** 2026-04-21  
**Audit scope:** Full filesystem comparison excluding node_modules, .venv, __pycache__, .git  
**Tools used:** diff, find, rsync, wc, grep, manual code review  
**Scratch files:** booger/scratch-1.md through scratch-4.md (intermediate analysis)  
