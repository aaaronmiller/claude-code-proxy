# Profile Routing — Operator Quickstart

**Feature**: 002-profile-routing
**Date**: 2026-05-28

---

## What This Feature Does

Adds per-CLI model profiles to the proxy. Each CLI (pi, opencode, hermes, claude-code, codex) gets its own model configuration without needing multiple proxy instances.

## How to Use

### 1. Verify the Registry

The profile registry lives at `profiles/profiles.json`. You should see entries for each CLI you run:

```bash
cat profiles/profiles.json
```

### 2. Check Your Alias Configuration

After installing aliases, each CLI points to its profile path:

| CLI | Base URL |
|-----|----------|
| pi | `http://127.0.0.1:8082/p/pi/v1` |
| opencode | `http://127.0.0.1:8082/p/opencode/v1` |
| hermes | `http://127.0.0.1:8082/p/hermes/v1` |
| claude-code | `http://127.0.0.1:8082/p/claude/v1` (via `ANTHROPIC_BASE_URL`) |
| codex | `http://127.0.0.1:8082/p/codex/v1` |

If you have existing aliases without profile paths, they still work — they're treated as the `default` profile.

### 3. Customize a Profile

Edit `profiles/profiles.json` and change any slot value:

```json
"pi": {
    "default": "your/preferred-model:free",
    "web_search": "your/cheap-search-model:free",
    "notes": "Pi profile"
}
```

Changes take effect on the next matching request — no restart needed.

### 4. Add a New Profile

Add a new entry to `profiles/profiles.json`:

```json
"new-tool": {
    "default": "some/model",
    "background": "another/model",
    "notes": "My new tool"
}
```

Point the new CLI's base URL at `http://127.0.0.1:8082/p/new-tool/v1`.

### 5. Web-Search Interception

If a profile defines a `web_search` slot, web-search tool calls from that CLI automatically use that model instead of the `default` model. To disable this for a specific profile:

```json
"pi": {
    "web_search_intercept": false,
    "notes": "Don't intercept web search calls"
}
```

## Management Commands

```bash
proxies profile list              # List all profiles
proxies profile show pi           # Show pi profile's resolved overlay
proxies profile validate          # Validate registry syntax
```

## Troubleshooting

- **"Profile 'X' not defined"**: The profile name in the URL path doesn't match any entry in `profiles/profiles.json`. Check your alias configuration.
- **Changes not taking effect**: Verify the JSON syntax is valid. Check the proxy logs for parse errors.
- **Legacy URLs still work**: Yes — `/v1/chat/completions` uses the `default` profile. No reconfiguration needed for existing tools.
