# Dynamic Model Discovery: Solving 502 Gateway Errors

> **Date:** 2026-02-28  
> **Status:** Implemented in Production

## 1. The Problem

The Claude Code proxy experienced critical recurring failures (502 Gateway errors) indicating "unknown provider for model X". This was specifically seen when Antigravity updated its models (e.g., introducing the `gemini-3.1` series) or changed backend taxonomy (e.g., adding `-high` and `-low` variants).

### Root Causes
1. **Hardcoded Model Lists**: The proxy maintained hardcoded lists of models (`ANTIGRAVITY_MODELS`) and aliases (`ANTIGRAVITY_ALIASES`) in `antigravity.py` and `antigravity_optimized.py`.
2. **Stale Mappings**: Whenever the upstream CLIProxyAPI changed available models, the proxy sent outdated names (e.g., `gemini-3.1-pro` instead of `gemini-3.1-pro-high`), causing the upstream router to reject the request.
3. **Rigid Passthrough**: The `ModelManager` blindly passed unknown non-Claude models through without any validation or normalization against live capabilities.

## 2. The Solution: Dynamic Model Discovery

We completely redesigned the model mapping architecture to be **dynamic, upstream-aware, and model-name agnostic**, eliminating the need to manually update lists when new models drop.

### 2.1 The `DynamicModelResolver`

A new singleton class (`src/services/models/dynamic_model_resolver.py`) acts as the brains of the proxy's model routing:

1. **Live Synchronization**: At proxy startup (in `main.py`), the resolver queries the upstream `CLIProxyAPI /v1/models` endpoint to fetch the exact, live list of supported models.
2. **Periodic Refresh**: Polling occurs every 5 minutes to gracefully discover models added or removed during proxy runtime.

### 2.2 Model Families & Smart Aliasing

The resolver no longer relies on explicit 1:1 mapping. Instead, it dynamically groups the live models into **Families**:

* `gemini-3.1-pro-high` & `gemini-3.1-pro-low` → grouped under family **`gemini-3.1-pro`**
* `tab_flash_lite_preview` → grouped under family **`tab_flash_lite`**

**Smart Aliasing:**
For each family, the resolver automatically creates a short-name alias that points to the most capable/preferred variant (prioritizing `-high`, then `-preview`, `-latest`, `-image`, `-low`). 
* User asks for `gemini-3.1-pro` → Proxy automatically resolves to `gemini-3.1-pro-high`.

### 2.3 Fuzzy Fallback for Stale Names

When the proxy encounters a model name that doesn't exactly match the live list or an alias, it utilizes a Fuzzy Fallback algorithm:
* If the user requests `gemini-3-pro-preview` but upstream only has `gemini-3-pro-high`, the resolver identifies they share the `gemini-3-pro` family.
* It safely upgrades the request to the best available live member of that family (`gemini-3-pro-high`).

### 2.4 Integration Points

* **`model_manager.py`**: Intercepts non-Claude models (which were previously passed through blindly) and routes them through the `DynamicModelResolver`.
* **`antigravity_optimized.py` / `antigravity.py`**: Now prefer the live dynamic list from the resolver, only using the hardcoded static lists as an offline fallback if CLIProxyAPI is completely unreachable.

## 3. Production Readiness

✅ **Architecture is Model-Agnostic**: The proxy no longer cares what the model names are. It adapts to whatever upstream provides.
✅ **Graceful Upgrades/Downgrades**: Stale model names instantly map to the closest available live family members.
✅ **Safe Fallbacks**: If the upstream model API goes down, the last known static models act as a safety net.
✅ **Eliminated Hardcoded Sprawl**: No more modifying dictionaries in three different files whenever `claude-sonnet-4.6` drops.

The system is now robust against provider taxonomy changes and ready for production. 
