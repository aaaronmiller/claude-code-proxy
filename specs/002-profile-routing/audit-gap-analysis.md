# Profile Routing — Implementation Audit & Feature Gap Analysis

**Date**: 2026-05-28
**Source**: Codebase audit of `~/code/claude-code-proxy`
**Specs referenced**: `requirements.md` (v1.0.0), `design.md` (v1.0.0), `specs/002-profile-routing/`

---

## PART 1: ACTUAL IMPLEMENTATION STATE

### Verified Complete (Present + Functional)

| Component | Location | Status | Evidence |
|-----------|----------|--------|----------|
| Profile resolver with mtime cache | `src/core/profiles.py` lines 117-144 | ✅ DONE | `_load_from_disk()`, `_refresh_cache()` with mtime check |
| ProfileContext frozen dataclass | `src/core/profiles.py` lines 76-88 | ✅ DONE | `ProfileContext` with `get()`, `has()` methods |
| ACTIVE_PROFILE contextvar | `src/core/profiles.py` lines 95-97 | ✅ DONE | `contextvars.ContextVar` for per-request isolation |
| extract_profile_from_path | `src/core/profiles.py` lines 176-193 | ✅ DONE | Strips `/p/{name}` prefix |
| validate_startup | `src/core/profiles.py` lines 196-216 | ✅ DONE | Startup validation, missing default=hard error |
| Profiles registry file | `profiles/profiles.json` | ✅ DONE | 8 profiles: default, pi, opencode, hermes, hermes-bypass, pi-bypass, claude, codex |
| `/p/{profile}/v1/chat/completions` route | `src/api/openai_endpoints.py` line 327 | ✅ DONE | Registered on OpenAI router |
| `/p/{profile}/v1/messages` route | `src/api/endpoints.py` line 393 | ✅ DONE | Registered on Anthropic router |
| Web-search interception | `src/core/profiles.py` lines 222-285 + `src/api/endpoints.py` lines 574-585 | ✅ DONE | Detects web-search tools, swaps model field before cascade |
| force_main override | `src/api/endpoints.py` lines 587-594 | ✅ DONE | Replaces request.model for non-tool turns |
| toolcall_models override | `src/api/endpoints.py` lines 598-601 + `src/core/client.py` lines 948-977 | ✅ DONE | Prepend tool-capable models to cascade chain |
| tier_overrides | `src/api/endpoints.py` lines 602-617 | ✅ DONE | Per-tier model swap after use-case router resolution |
| spoof_response_model | `src/api/openai_endpoints.py` lines 514-562, 693-696 | ✅ DONE | Rewrites response model field back to client's original; works in streaming + non-streaming |
| provider_override | `src/api/endpoints.py` lines 618-646 | ✅ DONE | Forces specific provider entry from PROVIDERS_* registry |
| Usage tracking profile column | `src/services/usage/usage_tracker.py` lines 155, 270, 274-277 | ✅ DONE | Auto-migration adds profile TEXT column |
| Read-only profile API | `src/api/routing_profiles_api.py` | ✅ DONE | `/api/routing-profiles` endpoints with per-profile request counts |
| Profile tests | `tests/test_profiles.py` (302 lines, 25 tests) | ✅ DONE | Tests resolver, path extraction, web-search detection, startup validation |
| install-aliases.sh profile path | `scripts/install-aliases.sh` line 238 | ✅ DONE | cldo routes through `/p/claude/v1` |

### Partially Verified (Present, Functional Status Unknown)

| Component | Location | Notes |
|-----------|----------|-------|
| Dashboard profile surface | `src/api/web_ui.py` lines 503-522 | Lists legacy env-var profiles. Routing profile surface status unclear |
| `proxies profile` CLI subcommands | Not found in `./proxies` script | May not exist — CLI profile management is through `profile_manager.py` which manages env-var profiles, not routing profiles |

---

## PART 2: FEATURES IN CODE NOT IN ORIGINAL SPECS

The following features are **implemented in the codebase** but were **not mentioned** in the original `requirements.md` or `design.md` specs. These represent scope expansion during implementation.

### 1. toolcall_models (list of models for tool-call routing)
- **Not in spec**: Spec described simple per-slot model override. This is a list priority system.
- **What it does**: Profile defines `toolcall_models: ["model-a", "model-b"]`. When a request has tool calls and the current model doesn't support tools, the proxy cascades through this list.
- **Code**: `profiles/profiles.json` in 7 of 8 profiles. Routed through `src/core/client.py` lines 948-977.
- **Design implication**: A list, not a single value. Changes cascade behavior.

### 2. force_main (full model override per-CLI)
- **Not in spec**: Spec described slot overlays only. This is a different mechanism entirely.
- **What it does**: Forces a specific model as the main reasoning model for ALL non-tool-call requests from that profile's CLI. Overrides whatever model the client requested.
- **Code**: `src/api/endpoints.py` lines 587-594.
- **Design implication**: This is a blunt instrument — it replaces the client's model choice entirely, not just slot-defaulting.

### 3. tier_overrides (per-tier model swap)
- **Not in spec**: Tier routing is a separate concern from slot routing, not covered in the spec.
- **What it does**: After the use-case router resolves a request to a tier (big/middle/small), the profile can swap that tier's model. The claude profile uses this: `small → owl-alpha` to save Anthropic Pro quota on menial tasks.
- **Code**: `src/api/endpoints.py` lines 602-617. Used in `profiles/profiles.json` claude profile.
- **Design implication**: Requires understanding the proxy's tier router to use effectively. Adds a second overlay dimension orthogonal to slots.

### 4. spoof_response_model (invisible model swaps)
- **Not in spec**: Completely absent from requirements and design docs.
- **What it does**: When force_main or tier_overrides swaps the model, the proxy rewrites the upstream response's `model` field back to what the client originally requested. Defaults to True — swaps are invisible to the CLI. Set False to surface the real model.
- **Code**: `src/api/openai_endpoints.py` lines 514-562 (streaming) and 693-696 (non-streaming). Also documented in `src/core/profiles.py` lines 22-31.
- **Design implication**: This is critical UX — without it, every profile model swap would cause the CLI to display a different model than expected. It's also a potential confusion source if debugging.

### 5. subagent_model (reserved)
- **Not in spec**: Not mentioned.
- **What it does**: A reserved slot in the profile schema for future subagent routing. No runtime code consumes it yet.
- **Code**: `src/core/profiles.py` line 36 (docstring only).
- **Design implication**: Forward-compatibility slot. Schema is already locked in.

### 6. provider_override (per-profile provider selection)
- **Not in spec**: Not mentioned in requirements or design.
- **What it does**: Forces a specific provider entry from the PROVIDERS_* registry for that profile's requests. Enables per-profile OAuth account selection, region selection, etc. Creates a new `OpenAIClient` with the override provider's base_url and api_key.
- **Code**: `src/api/endpoints.py` lines 618-646.
- **Design implication**: This is a significant feature — it effectively allows different CLIs to use different upstream accounts through the same proxy. The original spec said "out of scope" for OAuth account selection.

### 7. web_search_intercept opt-out (per-profile flag)
- **Not in spec**: Not mentioned.
- **What it does**: Per-profile `web_search_intercept: false` disables web-search tool-call model swapping for that profile. Prevents future pi version conflicts without code changes.
- **Code**: `src/core/profiles.py` lines 242-243.
- **Design implication**: The spec described web-search interception as always-on. The opt-out handles edge cases the spec didn't anticipate.

### 8. Custom web_search_pattern regex
- **Not in spec**: Not mentioned.
- **What it does**: Per-profile regex to match tool names for web-search detection. Allows profiles to recognize non-standard web-search tool names.
- **Code**: `src/core/profiles.py` lines 249-268.
- **Design implication**: The spec assumed tool names were standardized. Real CLIs use different names.

### 9. contextvars-based per-request isolation
- **Not in spec**: Spec described passing ProfileContext as a function parameter.
- **What it does**: Uses Python `contextvars.ContextVar` for per-request profile state. Each FastAPI async task gets its own immutable profile context. No parameter plumbing needed through the entire handler stack.
- **Code**: `src/core/profiles.py` lines 95-97, consumed in `src/api/endpoints.py` lines 572-573.
- **Design implication**: Much cleaner than parameter passing for a deeply nested call stack. But it's invisible — you won't find profile context in function signatures.

### 10. _profile_toolcall_models request stashing
- **Not in spec**: Not mentioned.
- **What it does**: The profile's toolcall_models list is stashed on the request dict as `_profile_toolcall_models` so the cascade/client layer can prepend them to the cascade chain. Clean separation of concerns between profile module and cascade logic.
- **Code**: `src/api/endpoints.py` lines 598-601, consumed in `src/core/client.py` lines 952-954.
- **Design implication**: Uses the request dict as a communication channel between middleware layers. Fragile but pragmatic.

### 11. Response model spoofing in streaming chunks
- **Not in spec**: Not mentioned.
- **What it does**: In streaming mode, rewrites `model` in each SSE chunk, not just the final response. Ensures the CLI never sees the swapped model even at the chunk level.
- **Code**: `src/api/openai_endpoints.py` lines 558-562.
- **Design implication**: Streaming SSE chunk manipulation is more complex than response-level rewrites. This was a significant implementation effort not captured in any spec.

---

## PART 3: DESIGN IRREGULARITIES / TECHNICAL DEBT

### 1. Duplicate web-search detection logic
`src/core/model_router.py` lines 72-? has its own `_is_web_search_request()`. `src/core/profiles.py` lines 222-285 has a more sophisticated version `is_web_search_request()`. These are NOT the same function — model_router's version is simpler and checks against config, while profiles.py's version checks against profile context and supports patterns. The model_router's version runs during use-case routing (step before profile overrides). The profiles.py version runs during profile overlay (step after). This means web-search requests get detected TWICE with potentially different logic.

### 2. Legacy env-var profile system vs routing profiles
There are TWO "profile" systems in the codebase:
- **Legacy env-var profiles** managed by `src/cli/profile_manager.py` and `src/api/web_ui.py` — save/load .env configs
- **Routing profiles** managed by `src/core/profiles.py` and `profiles/profiles.json` — per-CLI model routing

These share the `profiles/` directory but serve different purposes and have different APIs. The dashboard and CLI tooling for routing profiles are incomplete because the legacy system's surface area was reused.

### 3. Profile integration is in endpoints.py, not modular
The entire profile overlay logic (web-search intercept, force_main, toolcall_models, tier_overrides, provider_override) lives inline in `src/api/endpoints.py` (lines 567-648) rather than in a dedicated module. This is a ~80-line conditional block that duplicates some logic from `src/core/profiles.py`. A cleaner architecture would have a single `apply_profile_overlays()` function.

### 4. No Anthropic endpoint profile spoofing
The `spoof_response_model` feature is only implemented for OpenAI `/v1/chat/completions` in `openai_endpoints.py`. The Anthropic `/v1/messages` endpoint in `endpoints.py` applies profile overrides but does NOT have response model spoofing. This is documented in `src/core/profiles.py` lines 28-31: "Anthropic /v1/messages path is already invisible by construction (response converter uses request.model)." Worth verifying.

### 5. model_router does not use profile context directly
The model_router's `route()` method has its own toolcall_models and web-search logic that reads from config, not from `ACTIVE_PROFILE`. Profile overrides are applied AFTER the model_router runs (in endpoints.py). This means the model_router's own web-search detection fires first with global config, then the profile overlay may swap again. The order-of-operations matters and is fragile.

---

## PART 4: REMAINING WORK

### Minor / Verification
- Verify Anthropic endpoint response spoofing is indeed handled correctly by the response converter
- Check if dashboard routing profile display works (web_ui.py may need updates for routing_profiles)
- Verify `proxies profile` CLI subcommands exist or need creation

### Refactoring Opportunities (if building clean version)
1. Unify web-search detection into a single function
2. Extract profile overlay logic from endpoints.py into profiles.py as `apply_profile_overlays()`
3. Consolidate the two profile systems (legacy env-var + routing profiles) or at least clarify their boundaries
4. Add streaming response spoofing to the Anthropic endpoint for parity
5. Make model_router profile-aware directly instead of applying overrides after routing
