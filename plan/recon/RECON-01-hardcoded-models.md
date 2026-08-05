---
date: 2026-06-17 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, recon, hardcoded-models, s1-03, read-only]
---

# Recon 01: Hardcoded-model audit (ticket S1-03, read-only)

Read-only grep over `/home/cheta/code/claude-code-proxy`. No files changed. Verdict: routing is
largely config/snapshot-driven already; only two genuine name-keyed spots need fixing for W1.

## Good news (already dynamic)
- Fallbacks come from config, not literals: `openrouter_fallback_models` ConfigField
  (`src/core/config.py:117`), `{TIER}_CASCADE` env vars (`config.py:483-495`),
  `_get_dynamic_fallback_models()` (`client.py:112`), `_build_or_models_list()` (`client.py:93`).
- The model-id literals in `model_router.py` / `client.py` are docstring/example strings
  ("provider/model", "qwen/foo", "nvidia/...") - not routing decisions.
- Tier branching in `request_converter.py:759-763` keys on `config.big_model/middle_model/
  small_model` (config values), which is acceptable, not hardcoding.

## Two genuine anti-pattern spots to fix (W1)
1. `src/core/model_router.py:170` -
   `if model_id.startswith(("claude-", "gpt-", "gemini", "llama", "mistral")):`
   Tool-capability inferred from a hardcoded name-prefix list. This is exactly the brittle pattern
   the user wants gone (new model families silently misclassified). FIX: derive tool capability
   from the capability registry / models.dev specs / snapshot `has_tools`, not name prefixes.
2. `src/services/conversion/request_converter.py:662-717` - a reasoning-format lookup table keyed
   on model families ("openai/gpt-5", "openai/o1|o3", "anthropic/claude-*", "minimax/m2"). SOFT
   hardcoding: acceptable as capability detection but fragile for new models. FIX (lower priority):
   drive reasoning-format selection from models.dev `reasoning` capability + behavior-driven
   detection, with the table as a documented fallback.

## Test suite (S1-01 prep)
22 test files + subdirs (unit, contract, integration, performance, legacy). Relevant: test_profiles,
test_model_scan_{runtime,policy,snapshot}, test_quota_rotation, test_routing_profiles_ephemeral,
test_cascade_{daily_limit,exhausted_error}, test_observability_reliability, test_normalize_tool_
arguments, test_tool_text_recovery. `conftest.py` present. S1-01 (`pytest tests/`) is viable next.

## Action for S1-03
- Replace `model_router.py:170` name-prefix tool check with capability-registry/snapshot lookup.
- Add a test: an unknown model family with `has_tools=true` in the snapshot is treated as
  tool-capable (proves no name-prefix dependence).
- Track the `request_converter.py` reasoning table as a follow-up (models.dev-driven) under F01/W11.

No destructive change made. Code edits await DECISIONS.md O2 (repo strategy) sign-off.
