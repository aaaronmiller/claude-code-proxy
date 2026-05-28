# Research: Prior Art for Profile Routing

**Phase**: Phase 0 (pre-implementation research)
**Date**: 2026-05-28
**Spec**: `specs/002-profile-routing/spec.md`

---

## 1. Existing Solutions Analysis

### 1.1 claude-code-router (musistudio/claude-code-router)

| Aspect | Assessment |
|--------|-----------|
| Approach | Mature task-category routing with multi-provider support and dynamic `/model` switching |
| Profile isolation | Single global config per running instance; no per-client profile isolation |
| Tool-call interception | No mechanism to inspect tool-call payloads for per-role model switching |
| Overlap with this feature | Task-category routing vocabulary informed the choice to reuse existing slot names |
| Gap | Cannot isolate multiple CLIs running concurrently against the same router instance |

### 1.2 LiteLLM Proxy

| Aspect | Assessment |
|--------|-----------|
| Approach | Hierarchical Keys > Teams > Global resolution with virtual keys and model_group_alias |
| Profile isolation | Team-level config separation, but designed for upstream gateway concerns, not per-CLI tool-role routing |
| Tool-call interception | Cannot inspect tool-call payloads to rewrite model field mid-request |
| Overlap with this feature | Hierarchical resolution pattern informed the overlay model (profile over default) |
| Gap | Adding a new "CLI" means adding a new team, which brings OAuth, rate limits, and spend management — overkill for localhost multi-CLI isolation |

### 1.3 CCS (kaitranntt/ccs)

| Aspect | Assessment |
|--------|-----------|
| Approach | Request-time `profile:model` selectors with scenario-based routing and multi-runtime bridges |
| Profile isolation | Profile semantics are coarser than per-slot overlays; centered on OAuth/account switching |
| Overlap with this feature | Path-based profile selection (convergent pattern) |
| Gap | Slot-granular overlay model is fundamentally different from CCS's account-switching centered approach |

### 1.4 Multiple Proxy Instances

| Aspect | Assessment |
|--------|-----------|
| Approach | Run one proxy instance per CLI, each with its own configuration |
| Profile isolation | Trivial — total process-level isolation |
| Overlap with this feature | None — this is the anti-pattern the feature replaces |
| Gap | Multiplies compression-layer and command-rewriting-layer memory cost; configuration sprawl across N instances; no shared analytics |

## 2. Patterns Adopted

- **Path-based addressing** (from CCS and general URL-routing convention): `/p/{profile-name}/v1/...` as the profile selection mechanism.
- **Slot vocabulary** (from existing proxy router): `default`, `background`, `think`, `long_context`, `image`, `web_search` — adopted unchanged so profiles are overlays on existing semantics.
- **Mtime-keyed cache** (from prior proxy patterns): Use `os.stat` to check registry freshness instead of a filesystem watcher.
- **FastAPI Depends injection** (from existing proxy pattern): Request-scoped dependency injection for per-request `ProfileContext`.

## 3. Patterns Avoided

- **Filesystem-watcher hot-reload**: Mtime check is sufficient for single-digit-edits-per-day cadence; eliminates a runtime dependency and a thread that could deadlock.
- **Profile inheritance via `_inherits` keys**: The implicit `default`-profile overlay handles every observed case. Explicit inheritance adds schema complexity with no current use case.
- **Header-based profile selection (`X-Proxy-Profile`)**: No CLI under management exposes a clean header injection mechanism, making path-based the only universally compatible primary mechanism.
- **Model-name-prefix selection (`profile::model`)**: Requires every alias to dual-purpose its model arg; pollutes the model namespace.

## 4. Recommendations

1. **Phase 1 delivers immediate value** — the resolver + routes + aliases alone enable multi-CLI isolation, which is the primary use case.
2. **Web-search interceptor in Phase 2** — the highest-volume slot-swap use case; the inspection logic is isolated in a single module that can be tested independently.
3. **Dashboard surface deferred to Phase 3** — required for SC-001 completeness but not a dependency for the core value proposition.
4. **Forward-compatible provider_override slot in Phase 4** — reserved for future per-profile upstream account routing; not needed now.
