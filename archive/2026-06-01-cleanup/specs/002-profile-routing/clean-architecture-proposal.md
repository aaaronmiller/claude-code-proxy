# Clean Architecture Proposal — Proxy Rewrite

**Context**: Audit of legacy architecture constraints in claude-code-proxy
**Goal**: Resolve provider/model disconnect, enable/disable flag redundancy, and profile overlay ordering problems

---

## ROOT CAUSES IDENTIFIED

### 1. Model Name Encodes Provider (Fragile Convention)

The entire system uses `provider/model` strings (e.g., `openai/gpt-4`, `anthropic/claude-sonnet`). Then the code has to parse this string back apart to figure out which provider to use:

- `_get_tier_provider_from_model()` splits on `/` and takes the first part
- `tier_provider_overrides` exists because parsing from model name doesn't always work
- `provider_override` on profiles exists for the same reason
- That's **three separate mechanisms** for "which provider serves this model"

**Broken case you described**: If Gemini hosts Anthropic models, your model string would be something weird like `gemini/claude-sonnet` but the actual routing needs to go through the Gemini endpoint. Or with OpenRouter hosting everything, every model string starts with `openrouter/` which makes the provider prefix meaningless.

### 2. `_enabled` Flags Are Redundant With Model Presence

`big_enabled`, `middle_enabled`, `small_enabled`, `local_enabled` exist because the original config system needed explicit on/off switches. But they duplicate information: if `big_model` is set, that tier is enabled. If it's empty/null, it's disabled. The `_enabled` flag is a band-aid for config parser limitations that couldn't distinguish "not configured" from "configured to empty string."

### 3. Profile Overlays Fire After Routing (Wrong Order)

The execution order is:
1. model_router.route() — makes routing decision using global config
2. Profile overlay fires — may override the decision

This means the model_router's own web-search detection fires with global config values, then profiles.py's web-search detection fires again with profile values. Two different functions, potentially different results, same request. The profile "overlay" should be the FIRST thing applied, not the last.

### 4. Two Competing "Profile" Systems

- `profiles/profiles.json` → routing profiles (per-CLI model routing)
- `configs/profiles/*.json` → legacy env-var config saves (wizard snapshots)
- `src/cli/profile_manager.py` manages the latter
- `src/core/profiles.py` manages the former
- Both write to disk, different schemas, same concept name

### 5. No Unified UI Surface for Routing

Web UI (`/settings`) manages env vars and tier prompts. TUI has `advanced_config.py` for settings categories. Neither shows routing profiles. The only routing profile UI is the read-only API at `/api/routing-profiles`. Editing requires hand-editing `profiles/profiles.json`.

---

## PROPOSED ARCHITECTURE

### Core Concept: Decouple Model from Provider

```
[ Model Registry ]          [ Provider Registry ]
  gpt-4                       openrouter: { url, key }
  claude-sonnet               anthropic:  { url, key }
  claude-sonnet-via-or        gemini:     { url, key }
  qwen-3-next                 local:      { url }
  
          ↓                    ↓
    [ Route Table ]
    use_case → { model, provider }
    (default, toolcall, web_search, think, long_context, image, subagent)

          ↓
    [ Profile ]
    name: "pi"
    routes: { default: gpt-4, toolcall: claude-sonnet-via-or }
    (inherits unspecified routes from "default" profile)
```

Key changes:

**No `provider/model` strings**. A model is just an identifier. The provider that serves it is a separate configuration. This means:
- `gpt-4` → looked up in model registry → served by `openrouter` provider
- `claude-sonnet` → served by `anthropic` provider  
- `claude-sonnet-via-or` → served by `openrouter` provider (same model, different pipe)
- Provider is NEVER inferred from model name

**No `force_main`, no `tier_overrides`, no `spoof_response_model`**:
- `force_main` = setting the `default` route in a profile. No separate mechanism needed.
- `tier_overrides` = tier is just another routing dimension. If you want "haiku→owl-alpha" you set the `small` use_case to owl-alpha. No separate swap mechanism.
- `spoof_response_model` = if the model is defined as `claude-sonnet` and OpenRouter delivers it, the response says `claude-sonnet`. Nothing to spoof. The model identifier IS what the client expects.

**No `_enabled` flags**. A route with a null/empty model is disabled. Setting a model IS the act of enabling it.

### Single Resolution Order

```
1. Resolve profile name from URL path (/p/{name}/v1/...)
2. Load profile → get route table with defaults merged
3. Load model definitions for each route
4. Load provider config for each model
5. Route request: use profile + use_case → model + provider
```

No "fire routing twice" problem. The profile context is established BEFORE any routing decision, not patched in after.

### Unified Config Schema

```yaml
# Single config file, no split between legacy env-var profiles and routing profiles

providers:
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
  anthropic:
    base_url: https://api.anthropic.com/v1  
    api_key: ${ANTHROPIC_API_KEY}
  gemini:
    base_url: https://generativelanguage.googleapis.com/v1
    api_key: ${GEMINI_API_KEY}

models:
  gpt-4:
    provider: openrouter
    model_id: openai/gpt-4           # what to send in the API request
  claude-sonnet:
    provider: anthropic
    model_id: claude-sonnet-4-20250514
  claude-sonnet-via-or:
    provider: openrouter
    model_id: anthropic/claude-sonnet-4  # OpenRouter needs the prefix
  qwen-3-next:
    provider: openrouter
    model_id: qwen/qwen3-next-80b-a3b-thinking

profiles:
  default:
    routes:
      default: gpt-4
      toolcall: claude-sonnet-via-or
      web_search: claude-sonnet-via-or
      think: qwen-3-next
      image: gpt-4
      
  pi:
    routes:
      default: gpt-4
      toolcall: qwen-3-next    # only overrides toolcall, inherits rest
      
  hermes-bypass:
    routes:
      toolcall: qwen-3-next    # main model passes through (null = inherit)
      web_search: claude-sonnet-via-or

  claude:
    routes:
      default: claude-sonnet
      toolcall: claude-sonnet-via-or
    tier_routes:               # tier is explicit, not a separate mechanism
      small: gpt-4
```

### What This Resolves

| Problem | Resolution |
|---------|-----------|
| `openai/gpt-4` has provider in model name | Provider is a separate field. Model name is just an ID |
| Gemini hosting Anthropic models | Define `claude-sonnet-via-gemini` with `provider: gemini`, `model_id: anthropic/claude-sonnet` |
| `_enabled` flags are redundant | Null model = disabled. Setting model = enabled |
| `force_main` is a hack | Just set the `default` route in the profile |
| `tier_overrides` is a second overlay dimension | Tier is just another route key. Same mechanism, same schema |
| `spoof_response_model` needed because model was swapped | No swap needed. Model IS what the client expects |
| Web-search detected twice (global + profile) | Profile context established BEFORE routing. One resolution pass |
| Two profile systems | One system: `profiles.yaml` |
| Routing profiles invisible in UI | Profiles are just route tables. UI edits `routes:` entries directly |

### UI Surface for the Clean Version

A single page that shows:
- **Providers list**: name, endpoint, key status (masked)
- **Models list**: name, provider, model_id
- **Profiles**: name, route table (with inheritance visible)
- **Live view**: current active profile per request, per-profile request counts

TUI mirrors this: `profiles list`, `profiles show <name>`, `profiles set <profile> <use_case> <model>`.
