# PRD: Free-Model Smart Selection + Quota-Aware Cascade

## 1. Problem Statement
The current model-selection and cascade experience is not robust enough for heavy OpenRouter free-tier workflows:
- Free model limits are frequently reached and require manual model switching.
- The recommended list relies heavily on static curated arrays and local usage history, not real-time model metadata quality.
- High-value short-lived "stealth" free models are hard to discover quickly in the TUI.
- Existing cascade logic exists in `OpenAIClient` but is not wired into request handlers.

## 2. Research Findings (External)
### 2.1 Free-model daily window semantics
OpenRouter documents free-model limits as daily quotas and tracks usage counters on the **current UTC day** (`usage_daily`).

Conclusion for planning:
- Treat free-model quotas as **calendar-day UTC windows**, not rolling trailing 24h windows.
- Daily reset behavior should be modeled as next UTC day boundary.

Sources:
- OpenRouter limits docs: https://openrouter.ai/docs/api-reference/limits/
- OpenRouter FAQ: https://openrouter.ai/docs/faq
- OpenRouter support article: https://openrouter.zendesk.com/hc/en-us/articles/39501163636379-OpenRouter-Rate-Limits-What-You-Need-to-Know

### 2.2 Existing fallback/routing patterns to borrow
- OpenRouter model-level fallback supports ordered model lists via `models` parameter.
  Source: https://openrouter.ai/docs/model-routing
- OpenRouter provider routing supports configurable provider order and fallbacks.
  Source: https://openrouter.ai/docs/features/provider-routing
- Claude Code Switch (`claude-code-switch`) emphasizes practical fallback and model-switch ergonomics.
  Source: https://github.com/foreveryh/claude-code-switch

## 3. Current-State Analysis (This Repo)
### 3.1 Cascade implementation gap
- Cascade function exists: `src/core/client.py` (`create_chat_completion_with_cascade`), but request handlers call `create_chat_completion` directly.
- Result: `MODEL_CASCADE=true` does not provide the expected failover behavior in normal Claude endpoint flow.

### 3.2 Model discovery and ranking
- OpenRouter model fetch/enrichment exists and captures useful metadata (`created`, `context_length`, `supports_tools`, `pricing.is_free`, etc.).
- `ModelFilter` currently uses static `TOP_MODELS`, `FREE_MODELS`, `NEW_MODELS` lists.
- LLM+Exa ranker exists (`model_ranker.py`) with tool calls and can return coding-focused ranking output.

### 3.3 TUI discoverability
- TUI already supports recommended vs all toggle and model badges.
- It lacks a first-class free-tier strategy: stealth-vs-evergreen grouping, quota risk indicators, and cascade-preview path.

## 4. Goals
1. Build a hybrid free-model ranking pipeline:
- Programmatic scoring from OpenRouter model metadata.
- Optional LLM+Exa refinement over top candidates.

2. Add quota-aware cascading for OpenRouter free models:
- Automatic model failover on quota/rate/upstream errors.
- Cooldown and health tracking to avoid repeated failing models.

3. Improve operator UX:
- Faster discovery of high-value free coding models.
- Clear "recommended free list" and optional "show all models" path.
- Daily quota telemetry and approaching-limit warnings.

## 5. Non-Goals
- No provider-specific hardcoding for every transient free model.
- No dependency on web scraping for critical runtime path.
- No forced prompt injection for warnings (opt-in only).

## 6. User Personas
- Power user running Claude Code against OpenRouter free tier.
- User who wants best coding output with minimal manual model swaps.
- Operator who wants deterministic fallback behavior under rate limits.

## 7. Functional Requirements
1. Hybrid Ranking
- System SHALL build a candidate set from OpenRouter metadata for free models.
- System SHALL classify free models into:
  - `stealth_free`: recently created and high potential.
  - `evergreen_free`: stable long-available free models.
- System SHALL score candidates programmatically (context, tools, reasoning, recency, provider diversity, usage health).
- System SHALL optionally run Exa+LLM refinement on top-N candidates.

2. Cascade Runtime
- System SHALL detect OpenRouter free-tier failures (429 free-model/day, provider rate-limit, transient 5xx).
- System SHALL route to next model in configured cascade chain.
- System SHALL apply per-model cooldown windows after repeated failures.
- System SHALL log cascade transitions with reason and target model.

3. TUI Integration
- TUI SHALL provide `Recommended Free` mode as default when OpenRouter is active.
- TUI SHALL allow `Show All` models via command/key toggle.
- TUI SHALL display class badges (stealth, evergreen), context, output, tools/reasoning indicators.

4. Quota Telemetry
- System SHALL persist per-model/day request counters and error counters.
- System SHALL expose daily usage state and estimated reset time (UTC).
- System SHALL warn when nearing quota thresholds (configurable).

## 8. Non-Functional Requirements
- Sorting must complete under 500ms from cached metadata, excluding optional LLM refinement.
- Cascade decision must add <20ms overhead in non-failure cases.
- No secret leakage in logs or telemetry payloads.
- Feature must degrade gracefully when Exa key or ranker model is unavailable.

## 9. Success Metrics
- >= 90% reduction in manual model swaps after free-tier 429 events.
- >= 50% faster model selection in TUI for free-tier users.
- >= 80% of sessions remain available after first free-tier quota error via cascade.

## 10. Risks
- Model metadata can be stale between cache refreshes.
- Provider-side behavior for temporary free models can change rapidly.
- Over-aggressive fallback may increase latency if not bounded.

## 11. Rollout Strategy
1. Phase 1: Wire existing cascade into non-streaming path and add telemetry.
2. Phase 2: Add programmatic ranking + TUI "Recommended Free" view.
3. Phase 3: Add optional Exa/LLM reranking and stealth/evergreen classification.
4. Phase 4: Add streaming-path fallback and full quota dashboard indicators.
