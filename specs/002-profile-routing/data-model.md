# Data Model: Profile Routing Registry

**Phase**: Phase 1 output
**Date**: 2026-05-28
**Spec**: `specs/002-profile-routing/spec.md`

---

## 1. Registry File Shape

The registry file lives at `profiles/profiles.json` at the repo root. Its top-level shape is a JSON object whose keys are profile names. The reserved key `default` is mandatory.

### Seed Registry

```json
{
    "default": {
        "default":      "qwen/qwen3-next-80b-a3b-thinking",
        "background":   "minimax/minimax-m2.5:free",
        "think":        "qwen/qwen3-next-80b-a3b-thinking",
        "long_context": "minimax/minimax-m2.5:free",
        "image":        "nvidia/nemotron-nano-12b-v2-vl:free",
        "web_search":   "nvidia/nemotron-nano-12b-v2-vl:free",
        "notes": "Cascade-first conservative defaults"
    },
    "pi": {
        "web_search": "nvidia/nemotron-nano-12b-v2-vl:free",
        "web_search_pattern": "^(web_search|search_web)$",
        "notes": "Pi inherits default reasoning chain; only overrides web-search target"
    },
    "opencode": {
        "default": "openai/gpt-oss-120b:free",
        "notes": "OpenCode prefers GPT-OSS for main reasoning"
    },
    "hermes": {
        "default": "qwen/qwen3-next-80b-a3b-thinking",
        "notes": "Hermes uses thinking-tier qwen for main"
    },
    "claude": {
        "background": "anthropic/claude-haiku-4-5",
        "notes": "Claude-Code uses haiku for background; default for main"
    },
    "codex": {
        "notes": "Codex inherits default entirely"
    }
}
```

## 2. Per-Profile Schema

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `default` | string (model identifier) | No | Override for the `default` slot |
| `background` | string (model identifier) | No | Override for the `background` slot |
| `think` | string (model identifier) | No | Override for the `think` slot |
| `long_context` | string (model identifier) | No | Override for the `long_context` slot |
| `image` | string (model identifier) | No | Override for the `image` slot |
| `web_search` | string (model identifier) | No | Override for the `web_search` slot; also the substitution target for web-search interception |
| `web_search_intercept` | boolean | No (default `true`) | When `false`, disables web-search tool-call interception for this profile |
| `web_search_pattern` | string (regex) | No (default global pattern) | Custom regex for matching web-search tool names |
| `notes` | string | No | Human-readable description; never used for routing |

Unknown fields are ignored without error to allow forward-compatible schema extensions (such as `provider_override`, reserved for Phase 4).

## 3. Per-Request Profile Context

The Profile Context is a Python dataclass constructed once per request and passed by reference through the handler stack. It is never mutated after construction.

```python
@dataclass(frozen=True)
class ProfileContext:
    name: str                          # The resolved profile name (e.g. "pi", "default")
    slots: Mapping[str, str]           # The merged slot dictionary (profile overlaid on default)
    web_search_intercept: bool         # Whether web-search interception is enabled for this profile
    web_search_pattern: re.Pattern     # Compiled regex pattern for matching web-search tool names
```

The `slots` mapping is a frozen overlay: for each recognized slot name, the value is the profile's value if defined and the `default` profile's value otherwise.

## 4. Usage-Tracking Storage Extension

```sql
ALTER TABLE request_records ADD COLUMN profile TEXT NOT NULL DEFAULT 'default';
```

The column is populated at write time with the resolved profile name. Existing records receive the `default` value via the column default, ensuring backward compatibility with historical data and existing query patterns.
