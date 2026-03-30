# Dynamic Model Detection

> **IMPORTANT:** This codebase uses **dynamic model family detection** instead of hardcoded model names. This ensures the proxy remains functional when providers update model versions without requiring code changes.

## The Problem

Old proxy code looked like this:
```python
if model_name == "claude-opus-4-20250514":
    # do something
elif model_name == "gemini-1.5-flash":
    # do something else
```

This breaks when:
- Providers release new versions (claude-opus-4-20250515, gemini-1.6-flash)
- Models are deprecated or renamed
- OpenRouter adds new model variants

## The Solution: Model Family Detection

The proxy now uses **pattern-based family detection**:

```python
from src.services.models.model_family import detect_model_family, ModelFamily

family_info = detect_model_family("claude-opus-4-20250514")
# → ModelFamilyInfo(family=ModelFamily.ANTHROPIC_CLAUDE, tier="opus", ...)

family_info = detect_model_family("gemini-2.5-flash-preview-04-17")
# → ModelFamilyInfo(family=ModelFamily.GEMINI_FLASH, tier="flash", ...)
```

### Supported Families

| Family | Detects | Examples |
|--------|---------|----------|
| `OPENAI_O_SERIES` | o1, o3, o4 + variants | o1-mini, o3, o4-mini |
| `OPENAI_GPT` | GPT-4, GPT-5 | gpt-4, gpt-4o, gpt-5 |
| `ANTHROPIC_CLAUDE` | Claude models | claude-opus, claude-sonnet, claude-haiku |
| `GEMINI_FLASH` | Gemini Flash | gemini-flash, gemini-2.0-flash |
| `GEMINI_PRO` | Gemini Pro | gemini-pro, gemini-2.0-pro |
| `GEMINI_OTHER` | Other Gemini | gemini-1.5-pro |

### Helper Functions

```python
# Check reasoning support
is_reasoning_model("o1-mini")  # True
is_reasoning_model("claude-sonnet-4")  # True

# Check parameter requirements
requires_effort_level("o3-mini")  # True (OpenAI)
requires_thinking_tokens("claude-opus-4")  # True (Anthropic)
requires_thinking_budget("gemini-2.0-flash")  # True (Google)
```

## Adding New Model Families

Edit `src/services/models/model_family.py` - add a regex pattern:

```python
MODEL_FAMILY_PATTERNS = [
    # Add new patterns here
    (r'^(?:provider/)?new-model-\d+', ModelFamily.OPENAI_GPT),
    # ...
]
```

No other code changes needed!

## Migration Guide

### Before (Bad)
```python
if "claude-opus-4" in model_name:
    do_opus_stuff()
elif "claude-sonnet-4" in model_name:
    do_sonnet_stuff()
```

### After (Good)
```python
from src.services.models.model_family import detect_model_family

family = detect_model_family(model_name)
if family.tier == "opus":
    do_opus_stuff()
elif family.tier == "sonnet":
    do_sonnet_stuff()
```

Or even better - write logic based on capabilities:
```python
if requires_thinking_tokens(model_name):
    # Handle any Claude model
elif requires_effort_level(model_name):
    # Handle any OpenAI o-series
```

## Files Using This Pattern

- `src/services/models/model_family.py` - Core detection
- `src/core/reasoning_validator.py` - Reasoning parameter validation
- `src/services/models/model_parser.py` - Suffix parsing
- `src/core/model_manager.py` - Routing logic

## Anti-Patterns to Avoid

❌ **Don't do this:**
```python
if model_name in ["claude-opus-4-20250514", "claude-opus-4-20250515"]:
    # version-specific logic
```

✅ **Do this instead:**
```python
if family_info.family == ModelFamily.ANTHROPIC_CLAUDE and family_info.tier == "opus":
    # family-level logic (works for ALL opus versions)
```
