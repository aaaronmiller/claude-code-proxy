# Scratch: Proxy Rewrite — Architecture Reset

## The Real Problem

Legacy proxy has 6 years of incremental hacks. Each feature was bolted onto an architecture that didn't anticipate it. The result:

1. **Model name encodes provider** — `openai/gpt-4` means the code parses model strings to extract provider. Breaks when Gemini hosts Anthropic models or OpenRouter proxies everything.
2. **`_enabled` flags** — `big_enabled`, `middle_enabled`, `small_enabled` exist because config parser couldn't distinguish "not set" from "set to empty." A null model should = disabled automatically.
3. **Profile overlays fire AFTER routing** — Wrong order. Profile context should be established FIRST, then routing uses it. Instead: route → patch → hope nothing broke.
4. **Two profile systems** — `profiles/profiles.json` (routing) vs `configs/profiles/*.json` (legacy env saves). Same name, different schemas, different code paths.
5. **`spoof_response_model` exists because model swaps are a patch** — If routing served the right model first time, nothing to spoof.

## User's Usage Scenario

> "Config files per CLI alias. Run config A on claude-code, codex, and pi simultaneously. Or config A, B, C all at the same time. Config includes proxy chain, headroom, RTK, cli-proxy-api settings."

This means: config is a portable document. You load it by alias. The config specifies:
- Which provider(s) to use (endpoint, key)
- Which models for each use case
- Which proxy chain elements (headroom, compression, etc.)
- Which RTK/CLI settings

Multiple concurrent sessions can share the same config or use different ones. Config is a JSON file passed as argument.

## Proposed Solution

### Core Concept: Config as Document

```
proxy --config my-config.json
```

The config file IS the profile. It contains everything:
- Providers (named entries with endpoint + key source)
- Models (named entries with provider reference + model_id)
- Routes (use_case → model mapping)
- Proxy chain (ordered list of middleware: headroom, compression, etc.)
- CLIs\RTK settings

### Schema

```json
{
  "meta": { "name": "pi-config", "version": 1 },
  "providers": {
    "openrouter": {
      "base_url": "https://openrouter.ai/api/v1",
      "api_key_ref": "OPENROUTER_API_KEY"
    }
  },
  "models": {
    "gpt-4": { "provider": "openrouter", "model_id": "openai/gpt-4" },
    "claude-sonnet": { "provider": "openrouter", "model_id": "anthropic/claude-sonnet-4" }
  },
  "routes": {
    "default": "gpt-4",
    "toolcall": "claude-sonnet",
    "web_search": "claude-sonnet"
  },
  "chain": [
    { "kind": "headroom", "config": { "port": 8787 } },
    { "kind": "rtk", "config": { "mode": "passthrough" } }
  ],
  "cli": {
    "rtk_enabled": true,
    "compression": { "enabled": true, "algorithm": "zstd" }
  }
}
```

### Multiple Configs, Concurrent Sessions

```
# Alias setup
alias pi='proxy --config ~/.config/proxy/pi.json --port 8082'
alias codex='proxy --config ~/.config/proxy/codex.json --port 8083'
alias hermes='proxy --config ~/.config/proxy/hermes.json --port 8084'

# Run all three concurrently
pi & codex & hermes &
```

Each config fully specifies provider, models, chain, and CLI settings. No global state. No env variable contention. Each instance is a self-contained process.

### What This Eliminates

| Legacy Feature | Gone Because |
|---------------|-------------|
| `provider/model` string parsing | Model and provider are separate fields |
| `_enabled` flags | Null model = disabled automatically |
| `force_main` | Just set `routes.default` |
| `tier_overrides` | Tier is just another route key |
| `spoof_response_model` | Model IS what client expects |
| Profile overlay post-routing | Config loaded first, routing uses it |
| Two profile systems | One config file format |
| `PROVIDERS_*` env registry | Providers defined in config |
| Deprecated env var warnings | No env vars at all |

## User Stories

1. As a power user running 5 CLI agents simultaneously, I want each to have its own model config so pi uses cheap models while opus passes through for claude-code, without env variable conflicts.

2. As a user experimenting with providers, I want to define "claude-sonnet via OpenRouter" and "claude-sonnet via Anthropic direct" as two different model entries so I can A/B test latency without changing my alias.

3. As a user with multiple OpenRouter accounts, I want each proxy instance to use a different API key so I can pool free-tier quotas across instances.

4. As a CLI user, I want `proxies up --config my-team-config.json` to load everything—providers, models, routes, chain—from one file so I can version-control my setup.

5. As a user sharing a machine, I want each terminal to run a proxy with completely different provider accounts so my team's API keys don't collide.
