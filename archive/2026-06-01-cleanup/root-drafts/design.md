---
date: 2026-05-14 PHASE-LOCK PT
ver: 1.0.0
author: Sliither
model: claude-opus-4-7
tags: [proxy, profiles, routing, architecture, design]
---

# Profile Routing for claude-code-proxy — Technical Design v1.0

## 1. Architecture Overview

The profile system is a thin overlay on the proxy's existing model router. A new resolver module loads a JSON registry file, exposes a function that extracts a profile name from a request path prefix, and returns a per-request context object whose slot dictionary is the union of the named profile's overrides and the `default` profile's values. The request handlers inject this context into the existing model router, which consults the context before falling back to its global slot configuration. A separate interceptor inspects each request's tool-call payload after profile resolution and, when both a web-search tool invocation and a profile-defined `web_search` slot are present, rewrites the request's model field before dispatch.

No global state mutates per request. No environment variables are touched at runtime. The legacy routes and their handlers remain unchanged in behavior; the new routes delegate to the same handler functions with a non-null profile context. Profiles are an additive capability, never a replacement for any existing pathway.

```
                          claude-code-proxy
        +---------------------------------------------------+
        |                                                   |
   CLI ---> /p/{profile}/v1/...  --+                        |
        |                          v                        |
        |              [ Profile Resolver ]                 |
        |                  |        |                       |
        |                  |        +-- profiles.json       |
        |                  v                                |
        |        [ Per-Request Profile Context ]            |
        |                  |                                |
        |                  v                                |
        |        [ Web-Search Interceptor ]                 |
        |                  |                                |
        |                  v                                |
        |        [ Existing Model Router ]                  |
        |                  |                                |
        |          (slot lookup checks context first,       |
        |           falls back to global config)            |
        |                  |                                |
        |                  v                                |
        |        [ Cascade + Circuit Breaker ]              |
        |                  |                                |
        +------------------|--------------------------------+
                           v
                  [ Upstream Provider ]
```

### 1.1 What This System Does NOT Do

- Replaces or rebuilds the existing model router or cascade logic
- Mutates environment variables, global configuration, or any process-level state per request
- Introduces filesystem watching, inotify hooks, or background polling threads
- Implements profile inheritance via explicit `_inherits` chains
- Provides header-based or model-name-prefix profile selection
- Manages OAuth tokens, virtual keys, or multi-account routing
- Edits profile content from the dashboard or CLI; profile authoring is filesystem-direct
- Synthesizes default profile content when the registry exists but is missing the `default` profile (this is a hard startup error)

## 2. Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.9+ | Matches the existing proxy codebase |
| Web framework | FastAPI | Already in use for route registration; supports request-scoped dependency injection via `Depends`, which is the safe primitive for per-request profile context |
| Configuration format | JSON | Matches the existing `config/proxy_chain.json` precedent; easy to hand-edit; trivial to validate |
| Caching primitive | In-process mtime-keyed cache | Avoids filesystem watcher dependency, gives near-zero-cost reload check |
| Logging | Existing proxy logger | Profile-aware fields slot into existing log records |
| Storage | Existing SQLite usage-tracking DB | One additive column; no schema redesign |
| Testing | Existing test framework (pytest, per repo convention) | Integration test layered onto existing infrastructure |

### 2.1 Technology Decision Records

**Decision: JSON registry over YAML or TOML**
- Context: The registry must be machine-parsable, hand-editable, and consistent with other proxy configuration files.
- Options considered: JSON, YAML, TOML.
- Chosen because: JSON matches the existing `config/proxy_chain.json` convention; the proxy already has JSON parsing infrastructure; the registry shape is shallow enough that YAML's quality-of-life features add no real benefit.
- Trade-offs accepted: No comments inside the registry file. Mitigated by the `notes` field on each profile.

**Decision: Mtime-keyed cache over filesystem watcher**
- Context: Profile edits must be picked up without proxy restart, but the edit cadence is low (single-digit edits per day at most).
- Options considered: `watchfiles` library with async observer, `inotify` direct integration, mtime check on each resolution.
- Chosen because: Mtime check is a single `os.stat` per request, comfortably under the NFR-001 budget; eliminates a runtime dependency; eliminates a thread or task that could deadlock or leak; recovers automatically from any filesystem oddity.
- Trade-offs accepted: A few microseconds of overhead per request that resolves a profile, versus zero overhead with a watcher (but a watcher's complexity tax is paid every day of maintenance).

**Decision: Path-based profile selection over header or model-name-prefix**
- Context: Selection mechanism must work across pi, opencode, hermes, claude-code, codex without requiring upstream changes to any of them.
- Options considered: URL path prefix, `X-Proxy-Profile` header, model-name encoding (`profile::model`).
- Chosen because: Every CLI under management honors `BASE_URL` / `ANTHROPIC_BASE_URL` env vars natively; none expose custom-header injection; model-name encoding requires every alias to dual-purpose its model arg.
- Trade-offs accepted: URL path is the binding mechanism; switching profile mid-session requires changing the alias-set base URL, which matches existing CLI ergonomics anyway since none of these CLIs support live re-routing.

**Decision: Overlay on existing slot vocabulary over a new parallel schema**
- Context: The proxy already has named slots (`default`, `background`, `think`, `long_context`, `image`, `web_search`) consumed by the existing router.
- Options considered: Reuse slot vocabulary as profile keys (chosen); invent a new vocabulary like `toolcall_models` and `cascade`; embed full router configs inside each profile.
- Chosen because: Reuse means profiles ARE the existing slots, just with per-request overrides. Zero schema translation cost. Zero router-rewrite cost. Future router slot additions automatically work in profiles with no code changes.
- Trade-offs accepted: Profile expressiveness is bounded by the slot vocabulary. Any future capability that needs new vocabulary requires a slot addition first, which is the right ordering of concerns.

## 3. Data Model

### 3.1 Registry File Shape

The registry file lives at `profiles/profiles.json` at the repo root. Its top-level shape is a JSON object whose keys are profile names. The reserved key `default` is mandatory.

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

### 3.2 Per-Profile Schema

The recognized fields on a profile entry are:

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

### 3.3 Per-Request Profile Context

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

### 3.4 Usage-Tracking Storage Extension

The existing usage-tracking SQLite database receives one additive column:

```sql
ALTER TABLE request_records ADD COLUMN profile TEXT NOT NULL DEFAULT 'default';
```

The column is populated at write time with the resolved profile name. Existing records receive the `default` value via the column default, ensuring backward compatibility with historical data and existing query patterns.

## 4. Component Specifications

### 4.1 Profile Resolver (`src/core/profiles.py`)

**Responsibility**: Load and cache the profile registry, validate it against the schema, and produce a `ProfileContext` on demand.

**Interface**:

```python
class ProfileResolver:
    def __init__(self, registry_path: Path): ...
    def resolve(self, profile_name: str) -> ProfileContext: ...
    def list_profiles(self) -> List[str]: ...

def extract_profile_from_path(path: str) -> Tuple[Optional[str], str]:
    """
    Returns (profile_name, rewritten_path).
    If path matches /p/{name}/v1/..., returns (name, /v1/...).
    Otherwise returns (None, path) unchanged.
    """
```

**Dependencies**: Standard library only (`json`, `pathlib`, `os`, `re`, `dataclasses`).

**Error handling**:
- Missing registry file at startup: raise `FileNotFoundError` with the path.
- Malformed JSON: raise `RegistryParseError` with the parse error context.
- Missing `default` profile: raise `RegistryMissingDefaultError`.
- Unknown profile name in `resolve()`: raise `ProfileNotFoundError(name, available=[...])`. The route handler catches this and emits the structured 404 per FR-012.
- Malformed registry detected on reload: retain the last good parsed state, log a warning at error level, continue serving.

### 4.2 Profile Context Provider (FastAPI dependency)

**Responsibility**: Provide a request-scoped `ProfileContext` to handler functions via FastAPI's dependency injection.

**Interface**:

```python
async def get_profile_context(
    profile: Optional[str] = None,
    resolver: ProfileResolver = Depends(get_resolver),
) -> ProfileContext:
    """
    FastAPI dependency that resolves the profile name into a ProfileContext.
    When `profile` is None (legacy route), returns the 'default' profile's context.
    Raises HTTPException(404) for unknown profiles.
    """
```

**Dependencies**: `ProfileResolver`.

### 4.3 Model Router Integration

**Responsibility**: Consult the per-request profile context for slot lookups before falling back to global router state.

**Change site**: Whatever function in `src/core/` currently resolves a slot name to a model identifier. The signature gains an optional `profile_context: Optional[ProfileContext] = None` parameter. When non-null, the function checks `profile_context.slots[slot_name]` first and returns that value if present.

**Backward compatibility**: All existing call sites pass `profile_context=None` and observe identical behavior.

### 4.4 Web-Search Interceptor (`src/api/web_search_interceptor.py`)

**Responsibility**: Inspect requests for web-search tool invocations after profile resolution and substitute the model field when conditions are met.

**Interface**:

```python
def maybe_rewrite_for_web_search(
    request_body: dict,
    profile_context: ProfileContext,
) -> dict:
    """
    Returns the request body, possibly with the model field rewritten.
    Conditions for rewrite (all must be true):
      - profile_context.web_search_intercept is True
      - profile_context.slots contains 'web_search'
      - request_body's tool payload contains a web-search invocation
      - the web-search tool is the only tool invoked in this turn,
        OR tool_choice explicitly forces the web-search tool
    """
```

**Dependencies**: `ProfileContext`, a compiled regex pattern.

**Error handling**: When inspection fails (malformed request body, regex error), log a warning and return the request body unchanged. Never block a request because the interceptor failed.

### 4.5 Route Handlers

**Responsibility**: Register the new path-prefixed routes and delegate to the existing handler functions with a non-null profile context.

**Change site**: Wherever routes are registered (likely `src/api/routes.py`). Two new routes are added:

```
POST /p/{profile}/v1/chat/completions
POST /p/{profile}/v1/messages
```

Both routes resolve the profile via `get_profile_context` and delegate to the same handler function the legacy `/v1/chat/completions` and `/v1/messages` routes use, passing the resolved `ProfileContext`. The legacy routes are unchanged; their handlers call `get_profile_context(profile=None)`, which resolves to the `default` profile context.

## 5. API / Interface Contracts

### 5.1 Profiled Chat Completions

```
POST /p/{profile}/v1/chat/completions
  Path params:
    profile  (string)  Name of the profile to apply.
  Request body:
    Same shape as POST /v1/chat/completions (OpenAI-compatible).
  Response:
    Same shape as POST /v1/chat/completions.
  Errors:
    404 if profile is not defined in the registry. Body:
        {
            "profile_requested": "<name>",
            "profiles_available": ["default", "pi", "opencode", ...],
            "message": "Profile '<name>' is not defined. Edit profiles/profiles.json to add it."
        }
```

### 5.2 Profiled Messages

```
POST /p/{profile}/v1/messages
  Path params:
    profile  (string)  Name of the profile to apply.
  Request body:
    Same shape as POST /v1/messages (Anthropic-compatible).
  Response:
    Same shape as POST /v1/messages.
  Errors:
    404 if profile is not defined in the registry. Body: same shape as above.
```

### 5.3 Legacy Routes

```
POST /v1/chat/completions
POST /v1/messages
  Behavior: Identical to pre-existing behavior. Internally resolves the 'default' profile.
```

## 6. Hosting and Deployment

### 6.1 Infrastructure

The profile system runs entirely within the existing proxy process. No new services, no new containers, no new dependencies are introduced. Deployment changes are limited to ensuring the `profiles/profiles.json` file is present in the container or on the host filesystem alongside the existing configuration files.

### 6.2 Configuration

A single new file: `profiles/profiles.json`. The proxy's startup sequence reads this file once and caches the parsed content. The `profiles/` directory is created and seeded by the installer (`install-all.sh`) on initial install. Upgrades from a pre-profile-system version detect the absence of the file and synthesize a `default`-only registry from the existing global slot configuration, ensuring zero-friction upgrade.

### 6.3 Alias Updates

`scripts/install-aliases.sh` is updated to set each CLI's base URL to its profile-prefixed path:

| CLI | Updated base URL |
|-----|-------------------|
| pi | `http://127.0.0.1:8082/p/pi/v1` |
| opencode | `http://127.0.0.1:8082/p/opencode/v1` |
| hermes | `http://127.0.0.1:8082/p/hermes/v1` |
| claude-code | `http://127.0.0.1:8082/p/claude/v1` (set via `ANTHROPIC_BASE_URL`) |
| codex | `http://127.0.0.1:8082/p/codex/v1` |

Users with existing aliases pointing at legacy paths continue to work via FR-040 / FR-041; no action is required from those users.

## 7. Security Considerations

### 7.1 Threat Model

The profile system runs within the existing proxy's trust boundary. The same threat model applies: the proxy listens on localhost by default, and profile selection via URL path is no more or less authenticated than the proxy's existing endpoints. Profile names are not secrets and are not used as authorization tokens.

### 7.2 Authentication and Authorization

The existing `PROXY_AUTH_KEY` mechanism (per the proxy's README) continues to gate access to all routes including the new profile-prefixed routes. Profile selection does not introduce a new authentication surface.

### 7.3 Input Validation

Profile names extracted from request paths are validated against the registry; unknown names produce a 404 per FR-012. The validation prevents path-traversal-style attacks that might attempt to access non-profile data through the `{profile}` segment. The regex pattern in `web_search_pattern` is compiled at registry load time; a malformed pattern is detected and reported at load rather than at request time, with the affected profile falling back to the system-wide default pattern.

### 7.4 Supply Chain

No new third-party dependencies are introduced. All profile-system logic uses Python standard library only.

## 8. Implementation Phases

Phases are sized to ship independently. Each phase produces a working, deployable proxy. Phase boundaries align with test gates.

### Phase 1: Resolver, Routes, and Aliases

- Create `profiles/profiles.json` at the repo root with the five seed profiles (`default`, `pi`, `opencode`, `hermes`, `claude`, `codex`).
- Implement `src/core/profiles.py` with `ProfileResolver`, `ProfileContext`, and `extract_profile_from_path`.
- Implement the FastAPI `get_profile_context` dependency.
- Register the new `/p/{profile}/v1/chat/completions` and `/p/{profile}/v1/messages` routes.
- Modify the existing model router's slot-lookup function signature to accept an optional `ProfileContext` and consult it first.
- Update `scripts/install-aliases.sh` to point each CLI at its profile path.
- Write an integration test that launches a request through each profile path and asserts the dispatched model matches the profile's `default` slot.
- Validates: FR-001, FR-002, FR-003, FR-004, FR-010, FR-011, FR-012, FR-020, FR-021, FR-022, FR-040, FR-041; NFR-001, NFR-002, NFR-010, NFR-011, NFR-030, NFR-031.

### Phase 2: Web-Search Interception

- Implement `src/api/web_search_interceptor.py` with `maybe_rewrite_for_web_search`.
- Wire the interceptor into the request handler stack after profile resolution and before cascade routing.
- Extend `ProfileContext` with `web_search_intercept` and `web_search_pattern` fields, including a system-wide default pattern.
- Extend usage-tracking logging to record the substitution event with both original and rewritten model names.
- Write an integration test that sends a web-search tool-call request through the `pi` profile and asserts the dispatched model matches the profile's `web_search` slot.
- Validates: FR-030, FR-031, FR-032, FR-033; NFR-020.

### Phase 3: Observability Surface

- Add the `profile` column to the usage-tracking SQLite schema via the additive migration.
- Update the request-write path to populate the column.
- Extend the existing `proxies` CLI with `proxies profile list`, `proxies profile show <name>`, and `proxies profile validate` subcommands.
- Extend the dashboard's Profile management surface to display each profile's resolved overlay and 24-hour request count.
- Validates: NFR-021; remaining acceptance criteria for SC-001 through SC-005.

### Phase 4: Forward-Compatible Carrier Slot

- Extend the profile schema with an optional `provider_override` field (reserved for future per-profile upstream account routing).
- Implement the runtime check in the request handler that passes `provider_override` to the existing provider selector when present.
- Document the field's intended use in `profiles/profiles.json` comments via `notes` field examples.
- Validates: forward-compatibility commitment.

## 9. Testing Strategy

### 9.1 Unit Tests

| Module | Key Test Cases |
|--------|---------------|
| `ProfileResolver.resolve` | Resolves known profile; raises on unknown; merges profile over default correctly; returns frozen context |
| `extract_profile_from_path` | Extracts name from `/p/pi/v1/...`; returns None for `/v1/...`; handles malformed paths gracefully |
| `maybe_rewrite_for_web_search` | Rewrites when conditions met; no-ops when interception disabled; no-ops when no web-search slot; no-ops when multi-tool turn without forced choice |
| Registry reload | Mtime change triggers reparse; corrupt file retains last-good state |

### 9.2 Integration Tests

| Scenario | Validates |
|----------|----------|
| Five concurrent requests through five profile paths, each asserting the correct dispatched model | FR-010, FR-020, FR-021, FR-022, SC-001 |
| Web-search tool-call request through a profile defining `web_search` swaps the model | FR-030, FR-031, SC-002 |
| Live edit of `profiles.json` reflected on the next request without restart | FR-004, NFR-031, SC-003 |
| Legacy `/v1/...` route still works with no profile prefix | FR-011, FR-040, FR-041, SC-004 |
| Unknown profile path returns structured 404 | FR-012, NFR-011 |

### 9.3 Performance Benchmarks

| Benchmark | Target | Method |
|-----------|--------|--------|
| Per-request profile resolution overhead at P99 | < 1 millisecond | Compare pre- and post-profile-system latency against mock upstream over 10,000 requests |
| Concurrent profile resolution under load | No errors at 50 concurrent clients | Run 50-client parallel test cycling five profile paths for 60 seconds; assert no error responses and P99 within 2x single-client baseline |

## 10. Project Structure

```
claude-code-proxy/
├── profiles/
│   └── profiles.json                  # NEW: profile registry (Phase 1)
├── src/
│   ├── core/
│   │   ├── profiles.py                # NEW: ProfileResolver and ProfileContext (Phase 1)
│   │   └── model_router.py            # MODIFIED: signature change to accept optional context (Phase 1)
│   ├── api/
│   │   ├── routes.py                  # MODIFIED: register profile-prefixed routes (Phase 1)
│   │   └── web_search_interceptor.py  # NEW: tool-call inspection and rewrite (Phase 2)
│   └── services/
│       └── usage_tracking.py          # MODIFIED: add profile column and write path (Phase 3)
├── scripts/
│   ├── install-aliases.sh             # MODIFIED: point CLIs at profile paths (Phase 1)
│   └── proxies                        # MODIFIED: add `proxies profile` subcommands (Phase 3)
├── web-ui/
│   └── (profile management surface)   # MODIFIED: display overlay and counts (Phase 3)
└── tests/
    ├── integration/
    │   └── test_profile_routing.py    # NEW: full integration coverage (Phase 1+)
    └── unit/
        ├── test_profile_resolver.py   # NEW: resolver unit tests (Phase 1)
        └── test_web_search.py         # NEW: interceptor unit tests (Phase 2)
```

The directory layout follows the existing proxy's convention: feature logic in `src/core/`, request handlers in `src/api/`, persistent storage and analytics in `src/services/`. The `profiles/` directory is sibling to `config/` to keep registry semantics distinct from proxy chain configuration.

## 11. References

1. The aaaronmiller/claude-code-proxy README, which documents the existing model router slots and the `proxies` CLI surface.
2. The transcript and Option C+ assessment that motivated this design, refined by 10-agent council deliberation into Option C-slim.
3. The CCS (`kaitranntt/ccs`) project's `profile:model` selector pattern, which informed the path-based selection approach.
4. The claude-code-router (`musistudio/claude-code-router`) project's task-category routing vocabulary, which informed the choice to reuse existing slot names rather than invent parallel vocabulary.

