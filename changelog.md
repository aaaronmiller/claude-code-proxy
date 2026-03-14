# Claude Code Proxy - Changelog

> This document serves as a comprehensive knowledge base for future agents to understand the construction of the program, recurring issues, and solutions. It documents issues that arise from Claude Code and backend architecture upgrades.

---

## Table of Contents

1. [Current Session Fixes (March 2026)](#current-session-fixes-march-2026)
   - Issue 1: 64000 Token Output Limit
   - Issue 2: NoneType Error in endpoints.py
   - Issue 3: Stream Parameter None Handling
   - Issue 4: API Key None Handling
   - Issue 5: Request Deduplication Blocking Different Sessions
   - Issue 6: Alert Rule Conditions Parsing Error
   - Issue 7: Missing Model Limits
   - Issue 8: Invalid ModelManager Parameter
   - Issue 9: DB Migration Duplicate Column
   - Issue 10: Syntax Error - Duplicate Docstring
   - Issue 11: Concurrent Sessions Still Blocking
   - Issue 12: Database Migrations Failing on Fresh Install
   - Issue 13: Model Catalog Service
2. [Dynamic Model Discovery (February 2026)](#dynamic-model-discovery-february-2026)
3. [Anthropic Tool Call Changes (Nov 2025 - Feb 2026)](#anthropic-tool-call-changes-nov-2025---feb-2026)
4. [GIMP Debugging Session (February 2026)](#gimp-debugging-session-february-2026)
5. [Cascading Failure Resolution (December 2025)](#cascading-failure-resolution-december-2025)
6. [Tool Call Resolution (December 2025)](#tool-call-resolution-december-2025)
7. [401 Error Troubleshooting](#401-error-troubleshooting)
8. [Common Issues Reference](#common-issues-reference)
9. [Multi-Provider Architecture](#multi-provider-architecture)
10. [Known Issues / Technical Debt](#known-issues--technical-debt)

---

## Current Session Fixes (March 2026)

### Issue 1: 64000 Token Output Limit

**Symptom:** Claude Code was capped at 64000 output tokens despite supporting up to 128000.

**Root Cause:** The `CLAUDE_CODE_MAX_OUTPUT_TOKENS` environment variable was only set in shell aliases (`cproxy-init`, `cproxy-continue`), not globally in the shell profile.

**Solution:** Added `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000` to `~/.zshrc`.

**Files Modified:**
- `/home/cheta/.zshrc`

---

### Issue 2: NoneType Error in endpoints.py (Line 687)

**Symptom:** `'NoneType' object has no attribute 'get'` error when processing responses.

**Root Cause:** The `usage` field in the response could be `None`, and the code attempted to call `.get()` on it without a guard.

**Solution:** Added `usage = usage or {}` guard before accessing usage fields.

**Files Modified:**
- `src/api/endpoints.py` (line ~687)

---

### Issue 3: Stream Parameter None Handling

**Symptom:** Stream parameter was being passed as `None` instead of a boolean.

**Root Cause:** The `request.stream` attribute could be `None`, which caused downstream issues.

**Solution:** Fixed with explicit default: `request.stream if request.stream is not None else False`

**Files Modified:**
- `src/api/endpoints.py`

---

### Issue 4: API Key None Handling

**Symptom:** API key validation failures when key was not provided.

**Root Cause:** `api_key` could be `None` and was used without proper fallback.

**Solution:** Added `or ""` fallback for api_key handling.

**Files Modified:**
- `src/api/endpoints.py`

---

### Issue 5: Request Deduplication Blocking Different Sessions

**Symptom:** Concurrent Claude Code sessions were blocking each other; requests from one session were incorrectly flagged as duplicates of another.

**Root Cause:** The deduplication logic was not session-aware - it only checked request content hash without considering the session ID.

**Solution:** Modified deduplication to include session identifier in the deduplication key, ensuring different sessions don't block each other.

**Files Modified:**
- `src/api/endpoints.py`

---

### Issue 6: Alert Rule Conditions Parsing Error

**Symptom:** Alert rules failing with `'str' object has no attribute 'get'`.

**Root Cause:** Alert rule conditions were being stored as JSON strings but parsed as dictionaries.

**Solution:** Added JSON parsing for conditions that arrive as strings.

**Files Modified:**
- `src/services/alert_engine.py`

---

### Issue 7: Missing Model Limits

**Symptom:** New models without defined limits causing errors.

**Root Cause:** Missing entries for `pony-alpha`, `gpt-oss-120b-medium`, `hunter-alpha` in model limits.

**Solution:** Added these models to the model limits configuration.

**Files Modified:**
- `src/services/usage/model_limits.py`

---

### Issue 8: Invalid ModelManager Parameter

**Symptom:** ModelManager initialization errors.

**Root Cause:** Invalid `enabled=True` parameter passed to ModelManager.

**Solution:** Removed invalid parameter from model_manager.py.

**Files Modified:**
- `src/core/model_manager.py`

---

### Issue 9: DB Migration Duplicate Column

**Symptom:** Database migration failures with duplicate column errors.

**Root Cause:** Column already exists during migration.

**Solution:** Added handling in main.py for duplicate column scenarios.

**Files Modified:**
- `src/main.py`

---

### Issue 10: Syntax Error - Duplicate Docstring

**Symptom:** `SyntaxError: unterminated triple-quoted string literal` at line 1249 in endpoints.py.

**Root Cause:** Duplicate docstring content in `check_duplicate` method - the docstring text was repeated twice, leaving an unclosed triple-quote.

**Solution:** Removed duplicate docstring content.

**Files Modified:**
- `src/api/endpoints.py`

---

### Issue 11: Concurrent Sessions Still Blocking Each Other

**Symptom:** Multiple concurrent Claude Code sessions (3+) would stop after a single operation without completing.

**Root Cause:** While session ID was added to deduplication hash, Claude Code doesn't reliably send `metadata.user_id` in the expected format. All requests ended up with `session_id="none"`, making them appear as duplicates.

**Solution:** 
- Extract client IP address before deduplication check
- Include client IP in hash computation alongside session ID
- Different sessions from same or different IPs are now properly distinguished

**Files Modified:**
- `src/api/endpoints.py`

**Tested:** 3 concurrent sessions - all completed successfully with unique outputs.

---

### Issue 12: Database Migrations Failing on Fresh Install

**Symptom:** 
- `Failed to run DB migrations: no such table: alert_rules`
- `Alert check error: no such column: enabled` (repeating every second)

**Root Cause:** 
1. `main.py` tried to ADD COLUMNS to `alert_rules` and `scheduled_reports` tables BEFORE creating them
2. `websocket_live.py` used `WHERE enabled = 1` but table has `is_active`, not `enabled`

**Solution:**
- Added `create_table_if_not_exists()` helper in main.py to create core tables BEFORE adding columns
- Created tables: `api_requests`, `alert_rules` (with `muted_until` column), `alert_history`, `scheduled_reports`
- Fixed `websocket_live.py` to use `WHERE is_active = 1` instead of `WHERE enabled = 1`

**Files Modified:**
- `src/main.py`
- `src/api/websocket_live.py`

---

### Issue 13: Model Catalog Service

**Symptom:** Users had to choose from 400+ OpenRouter models without curated recommendations.

**Solution:** Created comprehensive model catalog system:
- **Model Catalog Service** (`src/services/models/model_catalog.py`): Core service with:
  - Curated model lists (free, smartest, coding, value) - 5 models each
  - Recent models from selection history
  - Daily usage tracking for cascade fallback
  - Model specs (context length, throughput, pricing)
  
- **Catalog Sync Script** (`src/services/models/catalog_sync.py`): 
  - Syncs model-scraper output into main proxy
  - Run with: `python -m src.services.models.catalog_sync --run-scraper`
  
- **Web UI Endpoints**:
  - `GET /api/models/catalog` - Returns curated lists + recent models
  - `GET /api/models/specs/{model_id}` - Get specific model specs
  - `POST /api/models/refresh-catalog` - Force refresh from scraper

**Files Modified:**
- `src/services/models/model_catalog.py` (NEW)
- `src/services/models/catalog_sync.py` (NEW)
- `src/api/web_ui.py`

---

## Dynamic Model Discovery (February 2026)

### The Problem

The Claude Code proxy experienced critical recurring failures (502 Gateway errors) indicating "unknown provider for model X". This occurred when Antigravity updated its models (e.g., introducing the `gemini-3.1` series) or changed backend taxonomy.

### Root Causes

1. **Hardcoded Model Lists**: The proxy maintained hardcoded lists of models (`ANTIGRAVITY_MODELS`) and aliases in provider modules.
2. **Stale Mappings**: Whenever the upstream CLIProxyAPI changed available models, the proxy sent outdated names.
3. **Rigid Passthrough**: The `ModelManager` blindly passed unknown non-Claude models without validation.

### The Solution: Dynamic ModelResolver

A new singleton class (`src/services/models/dynamic_model_resolver.py`) was implemented:

1. **Live Synchronization**: Queries upstream `/v1/models` endpoint at startup
2. **Periodic Refresh**: Polls every 5 minutes to discover new/removed models
3. **Model Families & Smart Aliasing**: Groups variants (e.g., `gemini-3.1-pro-high` and `gemini-3.1-pro-low` under family `gemini-3.1-pro`)
4. **Fuzzy Fallback**: Maps stale names to closest available live family members

### Files Modified

- `src/services/models/dynamic_model_resolver.py` (NEW)
- `src/core/model_manager.py` - Routes non-Claude models through resolver
- Provider modules (antigravity.py, antigravity_optimized.py) - Use dynamic list as primary

---

## Anthropic Tool Call Changes (Nov 2025 - Feb 2026)

### Major Releases

#### November 24, 2025 (Opus 4.5 Launch - MAJOR)
- **Programmatic Tool Calling (PTC)**: `allowed_callers`, `server_tool_use`, `code_execution_tool_result`
- **Tool Search Tool**: `defer_loading`, `tool_search_tool_regex`, `tool_search_tool_bm25`
- **Tool Use Examples**: `input_examples` field
- **Effort Parameter**: "low", "medium", "high"

#### January 29, 2026
- **Structured Outputs (GA)**: `output_format` -> `output_config.format`

#### February 5, 2026 (Opus 4.6 Launch)
- **Adaptive Thinking**: `thinking: {type: "adaptive"}`
- **Effort Parameter (GA)**: No beta header required
- **Fine-Grained Tool Streaming (GA)**
- **128K Output Tokens**: Doubled from 64K
- **Compaction API (beta)**

#### February 17, 2026 (Sonnet 4.6 Launch)
- **PTC (GA)**: No beta header required
- **Tool Search Tool (GA)**
- **Dynamic Web Search**: `web_search_20260209`, `web_fetch_20260209`

### Beta Headers Timeline

| Header | Introduced | Current Status |
|--------|-----------|----------------|
| `advanced-tool-use-2025-11-20` | Nov 24, 2025 | GA Feb 17, 2026 |
| `fine-grained-tool-streaming-2025-05-14` | Jun 11, 2025 | GA Feb 5, 2026 |
| `structured-outputs-2025-11-13` | Nov 14, 2025 | GA Jan 29, 2026 |
| `effort-2025-11-18` | Nov 24, 2025 | GA Feb 5, 2026 |
| `computer-use-2025-01-24` | Feb 24, 2025 | Still required |

### Proxy Impact: Translation Required

**Handled by LiteLLM:**
- Basic tool_use/tool_result translation
- Streaming translation
- Effort mapping to reasoning_effort

**Requires Custom Middleware (Layer 2):**
- `defer_loading` + tool search (local registry)
- `allowed_callers` + PTC execution loop
- `server_tool_use` decomposition
- `caller` field routing
- `input_examples` -> description injection

---

## GIMP Debugging Session (February 2026)

### Issue: 502 Bad Gateway / Unknown Provider

**Root Causes Identified:**
1. Missing model alias in CLIProxyAPI config (`gemini-claude-opus-4-6-thinking`)
2. `.envrc` override causing API key to not be loaded
3. Relative paths in startup scripts causing "file not found"

### Corrective Actions

1. **Config Fix**: Added Opus 4.6 mapping to `config.yaml`
2. **Auth Fix**: Added `PROVIDER_API_KEY="dummy"` fallback in `.env`
3. **Startup Script**: Created `start_all_services.sh` with absolute paths

### Code Patches

1. **Tool Choice Mapping**: Fixed `tool_choice: {type: "any"}` -> `"required"` conversion
2. **Thinking Budget**: Renamed `thinking.budget` to `thinking.budget_tokens`
3. **Stop Reason Handling**: Added `stop_sequence`, `pause_turn`, `refusal`, `tool_use`

---

## Cascading Failure Resolution (December 2025)

### The "Perfect Storm" - Six Distinct Faults

#### Phase 1: Protocol Mismatch (Auth Failure)
**Symptom:** `403 Forbidden` - "Lack a Gemini Code Assist license"
**Root Cause:** Claude Code uses `claude-haiku-4-5-20251001` for tool execution; VibeProxy rejected unrecognized model ID
**Solution:** Dynamic model mapping - intercept "haiku", route to `SMALL_MODEL` env var (default: `gemini-3-flash`)

#### Phase 2: Infrastructure Crash (500 Errors)
**Symptom:** `ModuleNotFoundError: src.utils.model_limits`
**Root Cause:** Wrong import path in `request_logger.py`
**Solution:** Changed `from src.utils.model_limits` to `from src.services.usage.model_limits`

#### Phase 3: Ghost Streams (Duplicate Responses)
**Symptom:** Duplicate SSE for same tool call (ID-based)
**Root Cause:** Upstream emitted duplicate streams with same ID, different indices
**Solution:** Track active tool call IDs; ignore streams with mismatched primary_index

#### Phase 4: Artificial Capacity Limits
**Symptom:** Large context (~170KB+) rejected
**Root Cause:** `model_limits.py` enforced 128k default; Gemini supports 1M+
**Solution:** Explicitly defined 1,000,000 token context for Gemini models

#### Phase 5: Parameter Schema (Streaming Failures)
**Symptom:** Bash tool fails in streaming: "Invalid value for 'command': got undefined"
**Root Cause:** Streaming path only did partial string replacement; non-streaming used full normalization
**Solution:** Dual-tier transformation - both streaming string replacement AND centralized normalize_tool_arguments()

#### Phase 6: Duplicate Operations (Content-Based)
**Symptom:** Duplicate tool outputs with DIFFERENT IDs
**Root Cause:** Gemini emits same operation twice with unique IDs (ID-based filter missed this)
**Solution:** Content-based fingerprinting - `f"{tool_name}:{first_args[:50]}"` before ID registration

---

## Tool Call Resolution (December 2025)

### Why Simple Fixes Failed

1. **"Simple Proxy" Fallacy**: Forwarding requests failed due to semantic incompatibility, not just syntax
2. **"Copy-Paste" Patch**: Copying `prompt` to `command` failed - CLI rejected extra key presence
3. **"Streaming Blind Spot":** Non-streaming fix insufficient - CLI parses raw stream
4. **"History Amnesia"**: Sending `command` to Gemini caused it to re-generate tool calls (loop)

### Validated Solution Architecture

**Forward Normalization (Response Converter):**
```python
# Streaming
partial_args = partial_args.replace('"prompt":', '"command":')
# Non-streaming  
args["command"] = args.pop("prompt")
```

**Reverse Normalization (Request Converter):**
```python
# When sending history to Gemini
args["prompt"] = args.pop("command")
```

**Temperature Control:**
```python
if model_size == "small":
    openai_request["temperature"] = 0
```

---

## 401 Error Troubleshooting

### Common Causes

1. **Invalid API Key**: Key not recognized by provider
2. **Expired API Key**: Key revoked or expired
3. **Wrong API Key**: Anthropic key sent to OpenAI-compatible endpoint
4. **Passthrough Mode**: `OPENAI_API_KEY="pass"` or unset

### The OPENAI_API_KEY Misconception

**Important:** `OPENAI_API_KEY` is used for ANY provider, not just OpenAI:
- **OpenRouter**: Use OpenRouter key (`sk-or-v1-`)
- **OpenAI**: Use OpenAI key (`sk-`)
- **Azure**: Use Azure key

### Quick Diagnostics

```bash
# Check API key
echo $OPENAI_API_KEY

# Test directly
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Common Issues Reference

### 401 Unauthorized: "No auth credentials found"
- **Fix:** Set valid `OPENAI_API_KEY` in `.env`

### 400 Bad Request: Unsupported verbosity value
- **Fix:** Set `VERBOSITY=""` in `.env`

### Reasoning Configuration Issues
- Only specific models support reasoning (o-series, Claude with thinking, Gemini with budget)
- Use suffix notation: `o4-mini:high`, `claude-opus-4:4k`, `gemini-2.5:16k`

---

## Multi-Provider Architecture

### Provider-Specific Quirks

| Provider | Tool Schema | Unique Issues |
|----------|-------------|---------------|
| Gemini/VibeProxy | Transformed | OAuth auth, ghost streams, duplicate history |
| OpenRouter | Normalized | `tools` required every request |
| OpenAI | Native | Strict schema mode |
| Anthropic | Different | `input_schema`, `tool_use` blocks |
| Azure | Native | API version header |

### Parameter Name Divergence

| Claude CLI Expects | Gemini May Output | OpenRouter May Output |
|--------------------|-------------------|----------------------|
| `command` | `prompt`, `code` | `command` |
| `file_path` | `path`, `filename` | `file_path` |
| `old_text` | `original`, `before` | `old_text` |

### Normalization Intensity Levels

| Provider | Level |
|----------|-------|
| Gemini | FULL (18+ transformations) |
| OpenRouter | LIGHT |
| OpenAI | NONE |
| Azure | NONE |

---

## Known Issues / Technical Debt

### High Priority

1. **PTC Decomposition Sandbox**: Programmatic Tool Calling requires local Python sandbox for Gemini routing
2. **Tool Search Registry**: `defer_loading` requires local tool registry implementation
3. **CLI Interceptor for Agent Teams**: Agent Teams spawn subprocesses; need wrapper script

### Medium Priority

4. **Provider-Specific Auth**: Currently hardcoded for VibeProxy; needs provider-aware auth handlers
5. **Model Listing Per Provider**: Dynamic model catalog per endpoint

### Low Priority

6. **Rate Limit Handling**: Provider-specific rate limit headers
7. **Cost Estimation**: Per-provider cost calculation

---

## Configuration Reference

### Model Environment Variables

```bash
# Required for Gemini/VibeProxy
BIG_MODEL="gemini-claude-opus-4-5-thinking"
SMALL_MODEL="gemini-3-flash"

# Required for OpenRouter
OPENAI_API_KEY="sk-or-v1-YOUR-KEY"
OPENBASE_URL="https://openrouter.ai/api/v1"

# Token limits
CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000
```

### Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Claude Code Proxy | 8000 | Main proxy |
| CLIProxyAPI/VibeProxy | 8317 | Upstream provider |

---

*Last Updated: March 13, 2026*
*This document should be updated whenever new issues are discovered and resolved to serve as institutional knowledge for future debugging sessions.*
