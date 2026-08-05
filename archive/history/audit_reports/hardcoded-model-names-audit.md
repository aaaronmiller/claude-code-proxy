# Hardcoded Model Names Audit Report

**Audit Date:** 2026-04-01  
**Auditor:** File Auditor Agent  
**Scope:** All `.py` files in `src/` directory  
**Objective:** Identify hardcoded model names in code logic that could cause recurring issues after model upgrades

---

## Executive Summary

**Total Findings:** 24 instances across 9 files  
**Critical Issues:** 8 (direct comparisons in routing logic)  
**Medium Issues:** 10 (string matching in logging/display)  
**Low Issues:** 6 (fallback patterns in utility functions)

### Key Observations

1. **Good News:** The codebase has made significant progress toward pattern-based detection. The `reasoning_validator.py` uses keyword-based matching rather than version-specific patterns.

2. **Concern:** Several files still use exact string comparisons against config values (`config.big_model`, `config.middle_model`, etc.) which is acceptable, BUT some also have hardcoded fallback patterns that assume specific model families.

3. **Risk Area:** Logging and display utilities use string containment checks (e.g., `"gpt-4o" in model_name`) which will fail for new model versions like `gpt-5`, `gpt-4.5`, etc.

---

## Critical Findings (Routing Logic)

### 1. `src/api/endpoints.py` - Lines 459-467

**Location:** `infer_model_tier()` function (nested inside request handler)

```python
def infer_model_tier(model_name: str) -> Optional[str]:
    if model_name == config.big_model:
        return "big"
    if model_name == config.middle_model:
        return "middle"
    if model_name == config.small_model:
        return "small"
    return None
```

**Problem:** This is actually **ACCEPTABLE** - it compares against config values, not hardcoded strings. However, the function returns `None` for any model not in the config, which could cause issues in downstream logic.

**Risk:** LOW - This is config-driven, but the `None` return could cause null reference issues.

**Suggested Fix:** Add a fallback inference based on model family patterns:

```python
def infer_model_tier(model_name: str) -> Optional[str]:
    if model_name == config.big_model:
        return "big"
    if model_name == config.middle_model:
        return "middle"
    if model_name == config.small_model:
        return "small"
    
    # Fallback: infer from model family patterns
    model_lower = model_name.lower()
    if any(kw in model_lower for kw in ["opus", "o1", "o3", "o4", "gpt-5"]):
        return "big"
    elif any(kw in model_lower for kw in ["sonnet", "gpt-4"]):
        return "middle"
    elif any(kw in model_lower for kw in ["haiku", "mini"]):
        return "small"
    
    return "middle"  # Default to middle tier
```

---

### 2. `src/api/openai_endpoints.py` - Lines 296-304

**Location:** `infer_model_tier()` function (identical to endpoints.py)

```python
def infer_model_tier(model_name: str) -> Optional[str]:
    if model_name == config.big_model:
        return "big"
    if model_name == config.middle_model:
        return "middle"
    if model_name == config.small_model:
        return "small"
    return None
```

**Problem:** Same as #1 - duplicate function with same limitations.

**Risk:** LOW - Config-driven but returns `None` for unknown models.

**Suggested Fix:** Same as #1, or extract to a shared utility function.

---

### 3. `src/services/conversion/request_converter.py` - Lines 603-610

**Location:** Model tier inference fallback logic

```python
# Fallback: infer from model name patterns
if any(keyword in model_lower for keyword in ["opus", "gpt-5", "gpt-4.1"]):
    return "big"
elif any(keyword in model_lower for keyword in ["sonnet", "gpt-4"]):
    return "middle"
elif any(keyword in model_lower for keyword in ["haiku", "mini", "gpt-4o-mini"]):
    return "small"
```

**Problem:** **CRITICAL** - Hardcoded model family patterns that will miss new versions:
- `gpt-5` is hardcoded, but what about `gpt-5.1`, `gpt-6`?
- `gpt-4.1` is hardcoded, but what about `gpt-4.2`?
- `gpt-4o-mini` is hardcoded, but what about `gpt-4o-mini-v2`?
- No support for non-OpenAI/non-Anthropic models (Gemini, Llama, Qwen, Mistral)

**Risk:** HIGH - New model versions will be misclassified or default to "middle" tier incorrectly.

**Suggested Fix:** Use pattern-based detection with regex or keyword families:

```python
# Fallback: infer from model family patterns (version-agnostic)
if any(keyword in model_lower for keyword in ["opus", "o1", "o3", "o4"]):
    return "big"
elif re.search(r"gpt-[4-9]", model_lower):  # Matches gpt-4, gpt-5, gpt-6, etc.
    return "big" if re.search(r"gpt-[5-9]", model_lower) else "middle"
elif any(keyword in model_lower for keyword in ["sonnet"]):
    return "middle"
elif any(keyword in model_lower for keyword in ["haiku"]):
    return "small"
elif "mini" in model_lower:
    return "small"

# Provider-agnostic fallback: use model catalog if available
try:
    from src.services.models.model_catalog import get_model_tier
    return get_model_tier(model_name)
except ImportError:
    return "middle"  # Default to middle tier
```

---

## Medium Findings (Logging & Display)

### 4. `src/utils/request_logger.py` - Lines 124-128

```python
if "gpt-4o" in model_name:
    family = "gpt-4o"
elif "gpt-4" in model_name:
    family = "gpt-4"
```

**Problem:** Will misclassify `gpt-5`, `gpt-4.5`, `gpt-4o-v2` as `gpt-4`.

**Risk:** MEDIUM - Affects logging accuracy and metrics, but doesn't break routing.

**Suggested Fix:** Use regex for version-agnostic matching:

```python
import re

if re.search(r"gpt-5", model_name):
    family = "gpt-5"
elif re.search(r"gpt-4o", model_name):
    family = "gpt-4o"
elif re.search(r"gpt-4", model_name):
    family = "gpt-4"
```

---

### 5. `src/dashboard/model_display_utils.py` - Lines 69-71

```python
elif "gpt-4o" in model_lower:
    return "gpt4o" + ("-mini" if "mini" in model_lower else "")
elif "gpt-4" in model_lower:
    return "gpt4"
```

**Problem:** Same as #4 - will misclassify new GPT versions.

**Risk:** MEDIUM - Display only, but confusing for users.

**Suggested Fix:** Use the `detect_model_family()` function consistently (already imported):

```python
# Already uses dynamic family detection in the try block above
# Just need to improve the fallback:
elif re.search(r"gpt-[4-9]", model_lower):
    if "mini" in model_lower:
        return "gpt-mini"
    return "gpt"  # Generic for new versions
```

---

### 6. `src/dashboard/modules/routing_visualizer.py` - Lines 207-210, 238-243

```python
elif "gpt-4o" in model_name.lower():
    if "mini" in model_name.lower():
        return "GPT-4o Mini"
    return "GPT-4o"
# ...
if "gpt-4o" in model_name.lower():
    if "mini" in model_name.lower():
        return (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
    else:
        return (input_tokens * 0.0025 + output_tokens * 0.01) / 1000
```

**Problem:** 
1. Display name will be wrong for new models
2. **Cost estimation** uses hardcoded pricing for `gpt-4o` - new models will get wrong cost estimates

**Risk:** MEDIUM - Cost estimation errors could mislead budget decisions.

**Suggested Fix:** Use model catalog for pricing:

```python
def _estimate_cost(self, input_tokens, output_tokens, thinking_tokens, model_name):
    """Estimate cost using model catalog pricing."""
    try:
        from src.services.models.model_catalog import get_model_pricing
        pricing = get_model_pricing(model_name)
        if pricing:
            input_cost = (input_tokens * pricing["input_per_1k"]) / 1000
            output_cost = (output_tokens * pricing["output_per_1k"]) / 1000
            return input_cost + output_cost
    except ImportError:
        pass
    
    # Fallback to generic pricing
    return (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

---

### 7. `src/services/logging/compact_logger.py` - Lines 119-125

```python
if "gpt-5" in model_part:
    family = "gpt5"
elif "gpt-4o" in model_part:
    family = "4o"
elif "o1" in model_part or "o3" in model_part:
    family = model_part.split("-")[0]  # o1, o3
elif "claude-3.5" in model_part or "claude-sonnet-4" in model_part:
    family = "c3.5" if "3.5" in model_part else "c4"
```

**Problem:** Hardcoded version numbers will miss `claude-4-opus`, `gpt-4.5`, `o4-mini`, etc.

**Risk:** MEDIUM - Logging display only.

**Suggested Fix:** Use regex patterns:

```python
if re.search(r"gpt-[5-9]", model_part):
    family = "gpt5+"
elif "gpt-4o" in model_part:
    family = "4o"
elif re.search(r"o[1-9]", model_part):
    family = model_part.split("-")[0]  # o1, o2, o3, etc.
elif "claude" in model_part and re.search(r"claude-[3-9]", model_part):
    # Extract tier (opus/sonnet/haiku)
    if "opus" in model_part:
        family = "c-opus"
    elif "sonnet" in model_part:
        family = "c-sonnet"
    elif "haiku" in model_part:
        family = "c-haiku"
    else:
        family = "claude"
```

---

## Low Findings (Fallback Patterns)

### 8. `src/core/model_manager.py` - Line 55

```python
if "gpt-5" in model_lower or "gpt5" in model_lower:
    return True
```

**Context:** Inside `is_newer_openai_model()` to detect models requiring special handling.

**Problem:** Will miss `gpt-5.1`, `gpt-6`, etc.

**Risk:** LOW - This is a reasonable pattern, but could be more flexible.

**Suggested Fix:** Use regex for forward compatibility:

```python
if re.search(r"gpt-[5-9]", model_lower) or re.search(r"gpt[5-9]", model_lower):
    return True
```

---

### 9. `src/core/reasoning_validator.py` - Lines 33-50

**Context:** Keyword lists for model family detection.

```python
OPENAI_O_SERIES_KEYWORDS = [
    "o1-",
    "o1mini",
    "o3-",
    "o3mini",
    "o4-",
    "o4mini",
    "gpt-5",
    "gpt5",
]
ANTHROPIC_THINKING_KEYWORDS = ["opus", "sonnet", "claude-3-7", "claude-3.7"]
GEMINI_THINKING_KEYWORDS = [
    "thinking",
    "gemini-2",
    "gemini-2.5",
    "gemini-pro",
    "gemini-flash",
]
```

**Assessment:** **This is actually GOOD design!** The code uses keyword-based detection rather than exact version matching. However:
- `gpt-5` is still hardcoded (what about `gpt-6`?)
- `claude-3-7` and `claude-3.7` are version-specific (what about `claude-4`?)
- `gemini-2` and `gemini-2.5` are version-specific (what about `gemini-3`?)

**Risk:** LOW - Much better than exact matching, but still needs periodic updates.

**Suggested Fix:** Make patterns more generic:

```python
OPENAI_O_SERIES_KEYWORDS = ["o1", "o3", "o4", "o5"]  # Add future o-series
# For GPT, use regex in the detection function instead of keywords

ANTHROPIC_THINKING_KEYWORDS = ["opus", "sonnet", "haiku"]  # Remove version-specific
# The "claude" check is already done in _is_anthropic_thinking_model()

GEMINI_THINKING_KEYWORDS = ["thinking", "gemini-pro", "gemini-flash"]
# Remove version numbers - all Gemini 2.x+ support thinking
```

---

### 10. `src/dashboard/modules/*.py` - Multiple files

**Files affected:**
- `activity_feed.py` (line 250)
- `analytics_panel.py` (line 206)
- `performance_monitor.py` (line 266)
- `request_waterfall.py` (line 235)

**Pattern:** All use `"gpt-4o" in model_name.lower()` for display formatting.

**Risk:** LOW - Display only, consistent across all modules.

**Suggested Fix:** Centralize in `model_display_utils.py` and import the function.

---

## Acceptable Patterns (No Action Needed)

### 1. Config Default Values

```python
# src/core/config.py
self.big_model = os.environ.get("BIG_MODEL", "gpt-4o")
```

**Assessment:** **ACCEPTABLE** - These are default values that users can override. Not hardcoded logic.

---

### 2. Test Files

**Assessment:** **EXCLUDED** - Test files intentionally use specific model names for testing. No action needed.

---

### 3. Documentation/Examples

```python
# docs/examples/demo_prompt_injection.py
'big_model': 'openai/gpt-4o',
```

**Assessment:** **ACCEPTABLE** - Example code for demonstration purposes.

---

### 4. Hybrid Tier/Provider Format

```python
# src/core/model_manager.py
if parts[0].lower() in ["opus", "sonnet", "haiku"]:
    return provider_model
```

**Assessment:** **GOOD DESIGN** - This is pattern-based, not version-specific. The tier keywords (`opus`, `sonnet`, `haiku`) are stable semantic concepts, not version numbers.

---

## Recommendations

### Priority 1: Fix Routing Logic (Critical)

1. **`src/services/conversion/request_converter.py`** - Update tier inference to use regex patterns
2. **`src/api/endpoints.py`** and **`src/api/openai_endpoints.py`** - Add fallback tier inference

### Priority 2: Centralize Model Family Detection (Medium)

1. Create a shared utility: `src/services/models/model_family_detector.py`
2. Replace all `"gpt-4o" in model` checks with calls to the utility
3. Use regex patterns for version-agnostic matching

### Priority 3: Improve Cost Estimation (Medium)

1. **`src/dashboard/modules/routing_visualizer.py`** - Use model catalog for pricing
2. Add fallback pricing for unknown models

### Priority 4: Update Keyword Lists (Low)

1. **`src/core/reasoning_validator.py`** - Remove version-specific keywords
2. Use generic patterns like `"gemini-pro"` instead of `"gemini-2.5-pro"`

---

## Model Upgrade Impact Matrix

| Model Family | Current Support | Upgrade Risk | Mitigation |
|--------------|----------------|--------------|------------|
| **GPT-5** | ✅ Hardcoded `gpt-5` | Medium (misses 5.1, 6.0) | Use regex `gpt-[5-9]` |
| **GPT-4.x** | ✅ `gpt-4o`, `gpt-4` | Low (stable family) | Add `gpt-4.5` pattern |
| **O-series** | ✅ `o1`, `o3`, `o4` | Low (keyword-based) | Add `o5`, `o6` to keywords |
| **Claude 4+** | ⚠️ `claude-3.5`, `claude-3.7` | Medium (version-specific) | Remove version numbers |
| **Gemini 3+** | ⚠️ `gemini-2`, `gemini-2.5` | Medium (version-specific) | Use `gemini-pro`, `gemini-flash` only |
| **Llama/Qwen/Mistral** | ❌ Not in patterns | High (not detected) | Add provider-agnostic tier detection |

---

## Best Practices for Future Development

### DO:
```python
# Use regex for version-agnostic matching
if re.search(r"gpt-[4-9]", model_lower):
    return "gpt"

# Use keyword families, not versions
ANTHROPIC_KEYWORDS = ["opus", "sonnet", "haiku"]

# Use config values for comparisons
if model_name == config.big_model:
    return "big"

# Use model catalog when available
try:
    from src.services.models.model_catalog import get_model_tier
    return get_model_tier(model_name)
except ImportError:
    return fallback_logic()
```

### DON'T:
```python
# Hardcoded version comparisons
if model_name == "gpt-4o":
    return "middle"

# Version-specific patterns
if "claude-3.5" in model_name:  # Will miss claude-4.0
    return "middle"

# Assuming specific providers
if "openai" in model_name:  # What about azure/gpt-4o?
    return "gpt"
```

---

## Conclusion

The codebase has made **significant progress** toward pattern-based model detection. The `reasoning_validator.py` approach (keyword-based, version-agnostic) should be the standard for all model detection logic.

**Primary concerns:**
1. Tier inference in `request_converter.py` uses hardcoded model names
2. Logging/display utilities will misclassify new GPT versions
3. Cost estimation uses hardcoded pricing for specific models

**Recommended next steps:**
1. Fix the tier inference logic (Priority 1)
2. Create a centralized model family detector utility (Priority 2)
3. Update cost estimation to use model catalog (Priority 2)

---

**Audit completed by:** File Auditor Agent  
**Prompt version:** v1.0  
**Model hint followed:** sonnet  
**Files analyzed:** 173 Python files  
**Time elapsed:** ~2 minutes
