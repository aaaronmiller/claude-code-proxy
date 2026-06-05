# Proxy Rewrite — Scratch / Idea Dump

## Core Concept

A clean-slate proxy that decouples model identity from provider routing. Instead of
`provider/model` strings where the provider is embedded in the model name, everything
is a reference: models point to providers, profiles point to models, configs are
JSON files passed as CLI arguments.

## Usage Scenario (Driving Design)

User launches:
```bash
proxy --config my-config.json
```
This starts a proxy with config A. Meanwhile, another terminal:
```bash
proxy --config other-config.json
```
This starts a DIFFERENT proxy instance with config B on a different port. Both run
concurrently. Each CLI gets aliased to its config's port:

```bash
alias pi-a='pi --base-url http://127.0.0.1:9100'
alias hermes-b='hermes --base-url http://127.0.0.1:9101'
alias codex-a='codex --base-url http://127.0.0.1:9100'
```

Config A and B are self-contained JSON files with everything: port, providers, models,
profiles, proxy chain, headroom settings, RTK settings, cliproxyapi settings.

## Key Problems Solved

1. **Model/provider coupling** - Never parse `provider/model` strings. Models and
   providers are separate registries.
2. **No `_enabled` flags** - Null model = disabled. Setting model = enabled.
3. **No post-hoc profile overrides** - Profile context established BEFORE routing.
4. **Single config per instance** - One JSON file = one running proxy. Different JSON
   = different proxy on different port. Clear separation.
5. **No legacy config** - No .env, no proxy_chain.json, no surprise inheritance.

## Architecture

### Config File Shape

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 9100,
    "log_level": "info"
  },
  "providers": {
    "openrouter": {
      "base_url": "https://openrouter.ai/api/v1",
      "api_key": "${OPENROUTER_API_KEY}",
      "models_endpoint": "/models"
    },
    "anthropic": {
      "base_url": "https://api.anthropic.com/v1",
      "api_key": "${ANTHROPIC_API_KEY}"
    },
    "opencode_go": {
      "base_url": "https://opencode.ai/zen/go/v1",
      "api_key": "${OPENCODE_GO_API_KEY}"
    }
  },
  "models": {
    "deepseek-v4": {
      "provider": "openrouter",
      "model_id": "deepseek/deepseek-v4-flash:free"
    },
    "gpt-oss": {
      "provider": "openrouter",
      "model_id": "openai/gpt-oss-120b:free"
    },
    "claude-sonnet": {
      "provider": "anthropic",
      "model_id": "claude-sonnet-4-20250514"
    },
    "claude-sonnet-via-or": {
      "provider": "openrouter",
      "model_id": "anthropic/claude-sonnet-4"
    }
  },
  "profiles": {
    "default": {
      "routes": {
        "default": "deepseek-v4",
        "toolcall": "gpt-oss",
        "web_search": "deepseek-v4",
        "think": "deepseek-v4"
      }
    },
    "pi": {
      "routes": {
        "toolcall": "deepseek-v4"
      }
    }
  },
  "compression": {
    "headroom": {
      "enabled": true,
      "port": 9200
    }
  },
  "rtk": {
    "enabled": true,
    "port": 9300
  },
  "cliproxyapi": {
    "enabled": false,
    "port": 9400
  }
}
```

### Resolution Flow

1. Request arrives at `/p/{profile}/v1/...`
2. Profile name → route table (with default inheritance)
3. Route `default` → model name `deepseek-v4`
4. Model `deepseek-v4` → provider `openrouter`, model_id `deepseek/deepseek-v4-flash:free`
5. Provider `openrouter` → base_url, api_key
6. Client dispatches to `POST {base_url}/chat/completions` with `model=deepseek/deepseek-v4-flash:free`

### Key Differences From Current Codebase

- **No `provider/model` parsing** - Two-field lookup, never string splitting
- **No `force_main`** - Just set `routes.default`
- **No `tier_overrides`** - Tiers are route keys. Route `big`, `middle`, `small` if wanted
- **No `spoof_response_model`** - Response model IS the model_id. Nothing to spoof
- **No `_enabled` flags** - Null route is disabled
- **No `_profile_toolcall_models` stash hack** - Contextvar passes state cleanly
- **No duplicate web-search detection** - One function, one call per request
- **No legacy env-var profile system** - One config format, one schema
- **Compression/headroom/RTK/cliproxyapi in config** - Everything in one file

## Questions to Resolve

1. Port allocation strategy? Auto-increment from base port? Default +1 per service?
2. How does the compression layer chain? Does each proxy instance start its own headroom?
3. Does the config file support shared services (one headroom for all proxy instances)?
4. What about docker? Each config = one container?
5. Watch mode (reload config on file change) or restart-only?
6. Should config support env var expansion from shell AND .env?

## Prior Art

- claude-code-proxy (current): full-featured but legacy architecture
- LiteLLM proxy: config-file-driven, but uses provider/model naming convention
- claude-code-router: task-category routing, multi-provider
- CCS (kaitranntt/ccs): profile:model selectors

## User Stories (for formal spec)

**US1**: User starts two proxy instances with different config files on different ports.
Both run concurrently. CLI aliases target different proxies.

**US2**: User edits config file, restarts proxy. New config takes effect. No migration
needed from old config format because there is no old config format.

**US3**: User defines a model served by OpenRouter, another model served by Anthropic,
and a third that is the same Anthropic model but served through OpenRouter. Each is a
separate model entry with its own provider.

**US4**: User runs pi through a profile that uses cheap models for tool calls and
expensive models for reasoning. Switching a profile's route is editing one line in JSON.

**US5**: User wants compression between their CLI and the upstream. Config includes
headroom settings. No separate headroom start command needed.
