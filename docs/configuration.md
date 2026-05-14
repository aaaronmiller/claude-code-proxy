# Configuration Guide — Unified Config System

The Claude Code Proxy uses a layered configuration system that supports multiple editing surfaces (CLI, TUI, web UI, `.env`) with automatic precedence and live reload.

## Precedence Order

Configuration values are resolved in this order (highest to lowest precedence):

| Layer | Source | Description |
|-------|--------|-------------|
| **CLI** | `--assign` flags at startup | Highest priority, command-line overrides |
| **Shell Env** | Environment variables in current shell | Set via `export VAR=value` |
| **Dotenv** | `.env` file | Project-level environment defaults |
| **Stored** | `proxy_chain.json` assignments + mappings | Persisted configuration |
| **Default** | Built-in proxy defaults | Fallback when no layer provides a value |

When a value is set in multiple layers, the highest-precedence layer wins. Use provenance queries (see below) to debug which layer is providing a value.

## Assignment Model

Assignments define how the proxy routes requests to models. There are two kinds:

- **Tier** — `big`, `middle`, `small` (three fixed tiers for Opus/Sonnet/Haiku class)
- **Slot** — Custom purpose slots like `think`, `background`, `web_search`, etc.

### Creating an Assignment

```bash
# Via API (admin only)
curl -X POST http://127.0.0.1:8082/api/assignments \
  -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "document_summarizer",
    "kind": "slot",
    "model": "anthropic/claude-haiku-4-5",
    "provider": "anthropic",
    "api_key": "${ANTHROPIC_API_KEY}",
    "enabled": true,
    "cascade": ["openai/gpt-4o-mini"]
  }'

# Via web UI — navigate to /assignments
```

### Assignment Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (lowercase, max 63 chars) |
| `kind` | `tier` or `slot` | Tier is fixed; slot is custom |
| `model` | string | Model ID (e.g., `openai/gpt-4o`) |
| `provider` | string | Provider name (`openai`, `anthropic`, etc.) |
| `base_url` | string | Optional custom endpoint |
| `api_key` | string | API key or `${VAR}` env reference |
| `enabled` | boolean | Whether this assignment is active |
| `cascade` | list[string] | Fallback models on failure |

## Identifier Mappings

Map incoming identifiers (from Hermes, Claude Code, or future Anthropic task types) to assignments:

```bash
curl -X POST http://127.0.0.1:8082/api/identifier-mappings \
  -H "Authorization: Bearer $PROXY_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incoming_identifier": "hermes.document_summarizer",
    "assignment_id": "document_summarizer",
    "enabled": true,
    "priority": 0,
    "notes": "Routes Hermes summarizer role"
  }'
```

## Provenance Queries

To answer "where did this value come from?":

```bash
# CLI
proxies config where assignments.big.model

# API
curl http://127.0.0.1:8082/api/config/assignments.big.model

# Response:
# {
#   "field_path": "assignments.big.model",
#   "value": "nvidia/nemotron-70b-instruct",
#   "raw_value": "nvidia/nemotron-70b-instruct",
#   "source_layer": "cli"
# }
```

The `source_layer` field tells you which layer won:
- `cli` — Set via `--assign` at startup
- `shell_env` — Exported in current shell
- `dotenv` — Set in `.env` file
- `stored` — Set via API/web UI/TUI
- `default` — Built-in fallback

## Live Reload

Configuration changes propagate to all surfaces without restart:
- SSE endpoint: `/api/config/events`
- Web UI auto-refreshes within 2 seconds
- TUI shows live updates

The proxy captures a config snapshot at request start, so in-flight streaming requests complete against the old configuration while new requests use the updated values.

## Migration from Legacy Env Vars

The old `BIG_MODEL`, `MIDDLE_MODEL`, `SMALL_MODEL` style is deprecated. The new assignment model replaces them:

| Legacy | New |
|--------|-----|
| `BIG_MODEL` | `assignments.big.model` |
| `BIG_ENDPOINT` | `assignments.big.base_url` |
| `BIG_API_KEY` | `assignments.big.api_key` |
| `ENABLE_BIG_ENDPOINT` | `assignments.big.enabled` |
| `BIG_CASCADE` | `assignments.big.cascade` |

The proxy detects legacy env vars at startup and emits a deprecation summary. Migration steps:

1. Create assignments via API or web UI
2. Set the model/provider/api_key for each tier
3. Remove legacy vars from `.env` (or leave commented)

## Troubleshooting

### Value not propagating

Check provenance:
```bash
proxies config where assignments.think.model
```

If `source_layer` is unexpected (e.g., `dotenv` when you set via CLI), there's a conflicting layer. Remove the lower-precedence value or restart without CLI overrides.

### TUI showing stale value

SSE subscriber may have dropped. Restart the TUI or check `/api/config/events` is reachable.

### Secret literal warning at startup

Someone committed an API key literally (e.g., `api_key: "sk-..."`). Replace with `"${VAR_NAME}"` reference.

### Live-reload indicator goes amber

SSE disconnected. Reconnect is automatic with exponential backoff. Click refresh in web UI header to force reconnect.

### Deprecation warnings on startup

Legacy env vars in use. Migrate to modern names per the startup summary. Point to this doc for equivalents.

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config` | Full config tree with provenance |
| GET | `/api/config/{field_path}` | Single field provenance |
| GET | `/api/assignments` | List all assignments |
| POST | `/api/assignments` | Create assignment (admin) |
| PATCH | `/api/assignments/{id}` | Update assignment (admin) |
| DELETE | `/api/assignments/{id}` | Delete assignment (admin) |
| GET | `/api/identifier-mappings` | List mappings |
| POST | `/api/identifier-mappings` | Create mapping (admin) |
| GET | `/api/chain` | List chain entries |
| POST | `/api/chain/reorder` | Reorder chain (admin) |
| GET | `/api/config/events` | SSE live-reload stream |
| GET | `/api/audit` | Audit log (admin) |

### Authentication

All write endpoints require admin role. Read endpoints require authenticated user. Set `PROXY_ADMIN_TOKEN` environment variable or use session authentication.