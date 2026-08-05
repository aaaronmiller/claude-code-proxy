# Proxy/Gateway, Adaptive Model Selector & Orchestration Audit Report

**Date:** 2026-07-04  
**Scope:** claude-code-proxy (src/) + MAUG PRD (PRD-MAUG.md)  
**Files Examined:** ~45 source files, 6 docs, test suite  
**Report Format:** Evidence-backed findings with paths and line numbers

---

## Executive Summary

The claude-code-proxy codebase implements a working multi-provider proxy with a layered routing engine, profile-based model selection, cascade fallback, circuit breakers, and model-scan integration. The MAUG PRD doc defines a convergent specification for a separate "Model-Agnostic Unified Gateway" that resolves gaps in the current proxy but is not yet implemented as code. The existing proxy has significant architecture debt in provider/model identity coupling, streaming tool-call normalization, and verification coverage.

---

## 1. Proxy & Gateway Architecture

### 1.1 Core Proxy Chain

**File:** `src/core/proxy_chain.py` (589 lines)

The proxy chain is a linear ordered list of `ProxyEntry` objects defining the topology:
```
Client → :8082 (this proxy) → chain[0] → chain[1] → ... → AI provider
```

**Architecture:**
- `ProxyChain.from_dict()` (line 212) parses from `config/proxy_chain.json` with schema migrations
- `upstream_url()` (line 414) returns first enabled non-local HTTP entry's URL
- `start_services()` (line 454) starts services in reverse order using `subprocess.Popen` (line 468–473)

**Finding: Service lifecycle management is fragile.** `subprocess.Popen` with `stdout=subprocess.DEVNULL` means service failures are invisible until the health endpoint is checked. There is no PID tracking (no `Popen` object storage) — the process reference is discarded immediately. No graceful shutdown; `service_stop_cmd` exists in the `ProxyEntry` dataclass (line 56) but is never invoked anywhere in the codebase.

### 1.2 Configuration Resolver

**File:** `src/core/config_resolver.py` (545 lines)

Layered precedence: `CLI > SHELL_ENV > DOTENV > STORED > DEFAULT`.

**Risk (line 116):** `_initialized` flag is set *before* `_register_legacy_aliases()` completes — if legacy alias registration throws, subsequent `resolve()` calls silently skip alias bridging because `_ensure_initialized` returns immediately.

**Finding (lines 297–321):** Generic provider-key fallback aliases (OPENROUTER_API_KEY → assignments.big.api_key) are gated by `explicit_owned` check — but this check only considers `LEGACY_ALIAS_MAP` entries not in `GENERIC_FALLBACK_ALIASES`. If BIG_API_KEY is set via STORED layer (not SHELL_ENV/DOTENV), the generic fallback aliases will NOT be skipped, potentially causing double-write or conflicting key resolution.

### 1.3 Current Config State (proxy_chain.json)

```json
{
  "entries": [
    {"id": "claude_code_proxy", "port": 8082, "enabled": true},
    {"id": "headroom", "port": 8787, "enabled": true},
    {"id": "cliproxyapi", "port": 8317, "enabled": false}
  ],
  "router": {
    "default": {"model": ""},
    "background": {"model": "deepseek-v4-flash-free"},
    "think": {"model": ""},
    "long_context": {"model": "deepseek-v4-flash-free", "threshold": 60000},
    "web_search": {"model": ""},
    "image": {"model": "deepseek-v4-flash-free"}
  },
  "assignments": [
    {"id": "big", "model": "deepseek-v4-flash-free", "cascade": []},
    {"id": "middle", "model": "deepseek-v4-flash-free", "cascade": []},
    {"id": "small", "model": "deepseek-v4-flash-free", "cascade": []}
  ]
}
```

**Finding:** All three tiers use the same model (`deepseek-v4-flash-free`), no cascade fallbacks configured for any tier, no `provider` field populated for any assignment. The routing system is effectively single-model in its current deployed state.

---

## 2. Adaptive Model Selector

### 2.1 ModelRouter (`src/core/model_router.py`, 527 lines)

Priority-based routing decision tree (lines 289–473):

| Priority | Trigger | Mechanism |
|----------|---------|-----------|
| 0 | Passthrough/disabled | Short-circuit return None |
| 0b | IdentifierMapping match | Lookup by `_original_model` → assignment |
| 1 | Custom router (Python/JS) | External script loaded at runtime |
| 2 | Image detection | `_has_image()` scans message content |
| 2b | Tool-call auto-route | `_model_supports_tools()` check → TOOLCALL_MODELS |
| 3 | Web search | Tool name heuristic |
| 4 | Long context | Token estimation > threshold |
| 5 | Think/Plan mode | System prompt keywords |
| 6 | Background | Original model = haiku or max_tokens ≤ 256 |
| 7 | Default | Fallback if set (otherwise None → caller keeps original) |

**Finding (line 46–58):** Token estimation uses a crude `total_chars // 4` heuristic with no tiktoken integration. This is potentially inaccurate for code-heavy or non-English content, causing false-positive/negative long-context routing decisions.

**Finding (lines 73–82):** Web search detection uses a hardcoded keyword list (`web_search`, `search_web`, `brave`, `exa`, `perplexity`). This is not configurable and misses tools like `web_fetch`, `duckduckgo`, etc. that various harnesses may use.

**Finding (lines 406–417, tool-call auto-route):** `toolcall_auto_route` picks `toolcall_models_list[0]` when the current model lacks tool support. This always picks the first model in the list regardless of actual capability differences — no capability-ranking logic, no fallback ordering, no loading awareness.

### 2.2 Identifier Mapping + Assignment Registry

**File:** `src/core/identifier_mapping.py` (171 lines)  
**File:** `src/core/assignments.py` (222 lines)

The IdentifierMapping system maps upstream model names (Anthropic model IDs, Gemini model IDs) to Assignment targets. Current config has 11 identifier mappings, all routing Claude haiku variants to the "small" assignment.

**Finding (identifier_mapping.py lines 137–154):** `lookup_by_incoming_identifier` sorts candidates by priority (descending) but returns the first match only — priority-based selection works, but there's no fallback chain if the top-priority assignment is disabled. The lookup just returns None, cascading to tier-based routing.

**Finding (assignments.py line 33–52):** Validation ensures `kind="tier"` has id in {big, middle, small}. `kind="slot"` validates regex. But there is no cross-validation that slot cascades reference only other valid assignments — cascade entries are opaque strings.

### 2.3 Model-Scan Binder (`src/core/model_scan_binder.py`, 231 lines)

Five policy kinds for automatic model selection: `static`, `free`, `budget`, `quality`, `roles`.

**Finding (lines 42–55):** `SelectionPolicy.parse("budget:0.5")` parses a per-Mtok ceiling. The `budget` policy is the only one with a numeric parameter. The `roles` policy (line 73–77) defers to each role's `eval_mode` — but the codebase has no runtime for evaluating eval_mode from the snapshot, meaning this policy is effectively unimplemented in practice.

**Finding (line 188):** When profile lane is "standby", forces `free` policy — but `price_blended == 0.0` eligibility excludes price-blended models with unknown prices (`None`). A model with unknown price will always be excluded by the free policy, even if it's actually free.

### 2.4 ModelScan Runtime (`src/core/model_scan_runtime.py`, 250 lines)

**Finding (lines 189–250):** `reload_model_scan()` performs the full binder pipeline on each reload. The allocator (F18, line 242) runs inside the same lock. If the allocator takes >1s (iterating ~300 snapshot candidates with per-candidate plan generation), it blocks the reload, which blocks all model-scan profile resolution until completion.

---

## 3. Orchestration & Tool Flow

### 3.1 Request Lifecycle (`src/api/openai_endpoints.py`, 851 lines)

The orchestration flow for a `/v1/chat/completions` request:

1. **Line 377:** Instantiate `Config()` — singleton, reads all env vars + proxy_chain.json
2. **Line 419–422:** Detect source IDE from headers/path/body
3. **Line 429:** `model_manager.parse_and_map_model(body.model)` — parses model name + reasoning config
4. **Line 432:** `openai_client.get_client_for_model(routed_model, config)` — resolves provider endpoint
5. **Line 443–446:** Normalize system role messages
6. **Line 461–464:** Normalize tools for provider
7. **Line 466–481:** Apply OpenRouter Fusion (if enabled)
8. **Line 483–606:** Profile overrides (web-search intercept, force_main, toolcall_models, provider_override, tier_overrides, model_scan bindings)
9. **Line 613–739:** Streaming path → cascade (line 664) or direct (line 685)
10. **Line 740–751:** Non-streaming path → cascade (line 743) or direct

**Finding (lines 466–481):** Fusion interception creates a separate `AsyncOpenAI` client inline (line 476) bypassing the OpenAIClient's provider pool. Fusion does not use the per-model client resolution, so Fusion requests cannot benefit from circuit breaker state or cascade fallback.

**Finding (lines 515–536):** `provider_override` profile setting creates another inline `AsyncOpenAI` client (line 528) — third client creation pattern in this endpoint alone. The codebase has three distinct client construction strategies (OpenAIClient, Fusion inline, provider_override inline) with no shared abstraction.

### 3.2 Cascade Fallback (`src/core/client.py`, lines 927–1314+)

**Finding (line 965):** Cascade models come from `request.get("_model_scan_cascade") or config.get_cascade_for_tier(tier)`. The `_model_scan_cascade` is set on the request dict by openai_endpoints.py (line 593) from the model-scan binding. But this only cascades within the `_model_scan_cascade` list — if model-scan hasn't been loaded, it falls back to config's cascade, which is **empty** in the current proxy_chain.json (all assignments have `"cascade": []`).

**Finding (lines 996–999):** Model deduplication uses an ordered `seen` set to build `raw_models_to_try`. Priority: `primary → toolcall_models → tier_cascade → dynamic_models`. If primary model is also in toolcall_models, it appears first. However, `_get_dynamic_fallback_models()` (lines 112–128) loads free model rankings from disk — if the rankings file is stale/missing, dynamic fallback is an empty list.

**Finding (lines 1009–1013):** Context-limit filtering uses `ctx_limit * 0.9` as the effective limit with a hardcoded `required_output=4096`. This means requests with `max_tokens > 4096` may be incorrectly rejected even when the model can handle them.

### 3.3 Circuit Breaker (`src/core/client.py`, lines 65–109)

Per-model circuit breaker state:
- `CB_FAILURE_THRESHOLD`: default 3 failures
- `CB_SUCCESS_THRESHOLD`: default 1 success
- `CB_TIMEOUT_SECONDS`: default 300s (5 min)

**Finding (line 73):** Circuit breakers are keyed by `model` string only — not `(model, provider, endpoint)` tuple. If two different endpoints serve the same model name, they share a breaker state incorrectly.

**Finding (lines 86–90):** `_is_cb_open()` checks `_circuit_breakers[model].is_open`. If the breaker doesn't exist (model never seen), returns `False`. This means models that are perpetually failing on first try are never circuit-broken — the breaker activates only after `failure_threshold` failures are recorded.

### 3.4 Request/Response Conversion

**File:** `src/services/conversion/request_converter.py` (1025 lines)  
**File:** `src/services/conversion/response_converter.py` (1675 lines)

**Finding (request_converter.py lines 39–109):** Tool schema stripping (`_strip_tool_schemas`) is enabled by default (`TOOL_SCHEMA_STRIP_ENABLED` = True). This deduplicates tools, removes `additionalProperties: false`, truncates descriptions to 200/120 chars. While marked as "semantics-preserving" (line 43), removing `additionalProperties: false` changes the JSON Schema validation behavior for providers like OpenAI v2 that enforce it.

**Finding (response_converter.py lines 30–36):** `_coerce_int_fields` hardcodes field names `timeout, offset, limit, cell_number`. If a model returns a different integer field as a string, it passes through uncoerced and causes `InputValidationError` downstream in Claude Code.

**Finding (response_converter.py lines 46–92):** `_normalize_tool_name` has a hardcoded mapping table (23 entries) mapping lowercased names to PascalCase. Any tool name not in this map passes through unchanged, which will fail in Claude Code CLI's strict validator.

---

## 4. Provider Detection & Identity

### 4.1 Provider Detector (`src/services/providers/provider_detector.py`, 282 lines)

**Finding (lines 48–93):** Provider detection is URL-substring based:
- `"127.0.0.1:8317"` → GEMINI
- `"openrouter.ai"` → OPENROUTER
- `"anthropic.com"` → ANTHROPIC
- `"azure"` or `".openai.azure.com"` → AZURE
- `"api.openai.com"` → OPENAI
- `"kiro"` or `"127.0.0.1:8083"` → KIRO
- Anything else → OPENAI_COMPATIBLE

**Risk (line 81):** `"azure" in url_lower` catches *any* URL containing "azure", including team names, subdomain patterns, or routing identifiers. A URL like `https://my-azure-proxy.example.com/v1` would be misidentified as Azure provider, triggering wrong auth and normalization.

**Finding (line 52):** When `base_url` is None/empty, returns `OPENAI_COMPATIBLE`. The default normalization for `OPENAI_COMPATIBLE` is `LIGHT`. This means a misconfigured proxy with no base_url will silently apply light normalization instead of failing fast.

### 4.2 Provider/Model Identity Coupling

The codebase uses three overlapping identity models:
1. **Tier model names** (config points `big_model`, `middle_model`, `small_model` to model strings)
2. **Provider-prefixed models** (`openrouter/deepseek-v4`, `google/gemini-3-flash`)
3. **Assignment identities** (unified `Assignment.id` + `Assignment.model` + `Assignment.provider`)

**Finding (client.py lines 349–364, `_resolve_provider_for_tier`):** Provider inference works by splitting the model name on "/" and looking up the prefix in `config.provider_registry`. If the model name doesn't have a "/" prefix (e.g., bare `"deepseek-v4-flash-free"`), the provider is `"default"`, which resolves to OpenRouter via env vars.

**Finding (client.py lines 366–399, `get_client_for_model`):** Tier matching uses string comparison against `config.big_model`, `config.middle_model`, `config.small_model`, with a `norm()` function that strips the provider prefix. This means if big_model="openrouter/model-x" and the request model="model-x" (without prefix), the tier is still correctly identified — but the provider prefix in the config model is the only way to infer which endpoint to use.

---

## 5. MAUG PRD Gap Analysis

**File:** `/home/cheta/code/ai-gateway/archive/source-docs/PRD- MAUG.md` (1969 lines)

The MAUG PRD identifies several requirements the current proxy doesn't implement:

### 5.1 Built (not in current proxy)
| Feature | MAUG Section | Current Status |
|---------|-------------|----------------|
| Quota Discriminator (quota vs overload vs invalid key) | §6.4 | Not implemented |
| Role-Constraint Resolver with hard/soft constraints | §6.3 | Not implemented |
| Model Onboarding Pipeline (auto-classify new models) | §7.2 | Not implemented |
| Host Sentinel (resource monitoring) | §9.7 | Not implemented |
| Control MCP Server (self-management) | §8.5 | Not implemented |
| Capability Registry (live provider metadata) | §5.4 | Partial (model_scan binder exists but no registry) |
| Performance Telemetry Surface (time-series) | §9.3 | Not implemented |

### 5.2 Invoke (external, documented)
| Feature | MAUG Section | Current Status |
|---------|-------------|----------------|
| LiteLLM as Docker container | §6.1 | Current proxy has no LiteLLM docker integration; uses direct provider calls |
| Headroom as integrated compression proxy | §8.1 | `headroom` entry in proxy_chain.json but client bypasses it for many paths |
| Redis-backed Key Ledger | §6.5 | Not implemented (current proxy uses SQLite for usage tracking) |
| Structured JSONL logging | §9.1 | Current proxy has `logging/` directory with text-based logging; not the full structured schema |

### 5.3 Key Architectural Differences

| Dimension | Current Proxy | MAUG (PRD) |
|-----------|--------------|------------|
| Provider dispatch | Direct via OpenAI SDK client pool | LiteLLM Docker container |
| Model selection | Tier-based (big/middle/small) + router profiles + model-scan | Role-constraint resolver + ranked candidates |
| Failure classification | Circuit breaker (binary open/closed) | Quota discriminator (3 failure classes + probe) |
| Configuration | env vars + proxy_chain.json + profiles.json | gateway.yaml + Redis + MCP |
| Model state | SQLite usage_tracking.db | Redis Key Ledger |
| Fallback | Ordered model list with context filtering | Five-stage fallback chain with schema downgrade |
| Streaming tool reassembly | `streaming_transform_partial()` in response_converter.py | Dedicated state machine (`idle → collecting_name → collecting_args → validating → complete`) |

---

## 6. Verification Gaps

### 6.1 Test Coverage

Tests exist for: allocator, cascade, circuit breaker, config parity, fusion, model_scan policy, model_scan snapshot, tool normalization, profiles, quota, reasoning.

**Coverage gaps identified from test directory listing:**
- **No end-to-end routing tests** — test_model_scan_policy.py tests the binder in isolation, no integration test that exercises ModelRouter → cascade → circuit breaker → fallback as a complete pipeline
- **No provider detection unit tests** — `provider_detector.py` has 0 dedicated tests; its behavior is exercised only indirectly
- **No test for openai_endpoints.py** — the main API entry point has no dedicated unit/integration tests
- **No test for client.py cascade logic** — the cascade fallback loop (lines 927–1314+) is untested despite being the most complex orchestration code
- **No streaming response converter tests** — response_converter.py (1675 lines) has no test file, despite being the largest single file in the codebase

### 6.2 Test Infrastructure Observations

- `conftest.py` at root provides shared fixtures
- `contract/` directory has schema validation tests (`test_resolver_precedence.py`, `test_routing_snapshot_schema.py`, etc.)
- `fixtures/` directory has test data
- `integration/` directory exists but appears minimal

### 6.3 Cross-Cutting Concern: Error Handling

All errors in cascade (client.py lines 1102–1314) are caught generically as `Exception` and logged. There is no structured distinction between transient errors (retryable), permanent errors (skip model), or critical errors (abort cascade). The cascade treats every exception as a reason to try the next model.

---

## 7. Risks Summary

| Risk | Severity | Location | Description |
|------|----------|----------|-------------|
| Single model all tiers | HIGH | proxy_chain.json | big/middle/small all `deepseek-v4-flash-free`; zero cascade fallbacks configured |
| No dead model detection at startup | HIGH | client.py/startup | Models are never probed at startup; a dead model only discovered at first request |
| Provider identity via URL substring | MEDIUM | provider_detector.py:48-93 | "azure" substring match is fragile; custom endpoints can be misidentified |
| Service lifecycle unmanaged | MEDIUM | proxy_chain.py:468-473 | subprocess.Popen with no PID tracking, no graceful shutdown, no restart |
| Token estimation without tiktoken | MEDIUM | model_router.py:46-58 | char//4 heuristic is crude; long-context routing decisions can be wrong |
| Model-only circuit breaker keys | MEDIUM | client.py:73 | Breaker keyed by model string only, not (model, provider, endpoint) |
| Fusion requests bypass circuit breakers | MEDIUM | openai_endpoints.py:476 | Fusion creates inline client, skips all cascade/breaker protections |
| No streaming response converter tests | HIGH | response_converter.py | 1675 lines — largest file — has zero tests |
| No openai_endpoints tests | HIGH | openai_endpoints.py | 851 lines — main API entry point — has zero dedicated tests |
| MAUG features unimplemented | MEDIUM | PRD- MAUG.md | Quota Discriminator, Role-Constraint, Host Sentinel, MCP server are spec-only |
| Config initialization race | LOW | config_resolver.py:116 | `_initialized` flag set before legacy alias registration completes |

---

## 8. Recommendations

### Immediate (High Impact)
1. **Add tests for openai_endpoints.py and response_converter.py** — these are the two most critical files with zero dedicated test coverage
2. **Configure cascade fallbacks** in proxy_chain.json for all tiers (big/middle/small) to reduce single-model risk
3. **Add startup model probe** — quick health check for configured models before accepting traffic

### Near-Term (Medium Impact)
4. **Decouple provider detection from URL heuristics** — use explicit provider registry with known endpoint patterns
5. **Add provider+model+endpoint tuple to circuit breaker keys** — prevent cross-contamination
6. **Add structured error classification** to cascade fallback (transient vs permanent vs critical)
7. **Replace char-based token estimation** with tiktoken for accurate long-context routing

### Architecture (Strategic)
8. **Unify client construction strategies** — eliminate three separate `AsyncOpenAI` creation patterns (OpenAIClient, Fusion, provider_override)
9. **Implement Quota Discriminator** (MAUG §6.4) — differentiate quota exhaustion, provider overload, invalid key
10. **Add proper service lifecycle management** to ProxyChain — PID tracking, health monitoring, graceful shutdown, auto-restart
11. **Implement model-scan snapshots as the primary model source** — currently model-scan is off in config (`"enabled": false`)
12. **Adopt MAUG's streaming reassembly state machine** — replace the ad-hoc `streaming_transform_partial()` with the formal `idle → collecting_name → collecting_args → validating → complete` state model
