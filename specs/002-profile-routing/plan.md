# Implementation Plan: Profile Routing for claude-code-proxy

**Branch**: `002-profile-routing` | **Date**: 2026-05-28 | **Spec**: `specs/002-profile-routing/spec.md`

**Input**: Feature specification from `specs/002-profile-routing/spec.md`, design from `design.md` (v1.0.0)

---

## Summary

Add per-request profile selection to the claude-code-proxy. A profile is a named bundle of slot overrides that activates when a request arrives at a profile-specific path (`/p/{profile-name}/v1/...`). The mechanism allows a single proxy instance, a single compression layer, and a single command-rewriting layer to serve every connected CLI with its own independent model slot configuration, with no process restarts and no environment-variable contention between tools. A web-search tool-call interceptor inspects request payloads and conditionally rewrites the model field when a profile defines a distinct `web_search` slot.

The capability is essential for users running pi, opencode, hermes, claude-code, and codex side by side, each with distinct model preferences, and for users who want to route specific tool-call patterns (e.g., web search) to different models than the main reasoning chain.

---

## Technical Context

**Language/Version**: Python 3.9+ (matching existing proxy codebase)

**Primary Dependencies**: Standard library only (`json`, `pathlib`, `os`, `re`, `dataclasses`). FastAPI already in use; no new framework dependencies.

**Storage**: Existing SQLite usage-tracking DB gets one additive column (`profile TEXT NOT NULL DEFAULT 'default'`). Profile registry stored as JSON file at `profiles/profiles.json`.

**Testing**: pytest (per repo convention). New unit tests for ProfileResolver, extract_profile_from_path, maybe_rewrite_for_web_search. New integration test for multi-profile concurrent routing.

**Target Platform**: Linux server (same as existing proxy deployment).

**Project Type**: Feature extension to existing Python web service.

**Performance Goals**: Profile resolution <1ms P99 overhead. 50+ concurrent profiled requests without contention.

**Constraints**: Zero new third-party dependencies. Zero backward-incompatible changes to existing routes, configuration, or CLI surface. All profile logic uses Python standard library only.

**Scale/Scope**: Single-instance proxy serving up to ~10 concurrent CLI tools, each with its own named profile (5-10 profiles typical).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Existing Research Before Building** | ✅ PASS | Design.md section 8 contains comprehensive prior art analysis: claude-code-router, LiteLLM proxy, CCS, multi-instance approach. All evaluated with explicit strengths/weaknesses/gaps. |
| **II. Synthesis Verification** | ✅ PASS | Spec derived from two existing high-quality artifacts (requirements.md, design.md). Claims back-referenced to source. |
| **III. Safe Destructive Operations** | ✅ PASS (N/A) | No destructive filesystem or git operations in this feature. Profile registry is a new additive file. |
| **IV. Changelog Discipline** | ✅ PASS | CHANGELOG.md in repo root; [Unreleased] section will be updated on merge. |
| **V. Progressive Disclosure** | ✅ PASS | This plan is a single focused document. Implementation will keep changes confined to minimal surface area. |
| **VI. Single Source of Truth for Configuration** | ✅ PASS | Profile registry is the sole source for profile definitions. No overlapping env-var configuration for profiles. Existing config surfaces remain authoritative for non-profile global settings. |
| **Engineering: Stable Public API** | ✅ PASS | New routes are additive; legacy routes unchanged. |
| **Engineering: No Secrets in Git** | ✅ PASS (N/A) | Profile registry contains model identifiers, not secrets. |
| **Engineering: Deprecation Over Hard-Cut** | ✅ PASS (N/A) | No capabilities are removed. |

Referenced constitution: `.specify/memory/constitution.md` (project, v1.0.0) and `~/code/agents/constitution.md` (global agent rules).

---

## Project Structure

### Documentation (this feature)

```text
specs/002-profile-routing/
├── spec.md             # This feature specification
├── plan.md             # This implementation plan
├── research.md         # Prior art analysis (Phase 0)
├── data-model.md       # Registry schema and profile context (Phase 1)
├── contracts/          # API contracts for profiled endpoints
├── quickstart.md       # Operator setup guide (Phase 1)
└── tasks.md            # Atomic implementation units (Phase 2)
```

### Source Code (repository root)

```text
claude-code-proxy/
├── profiles/
│   └── profiles.json                  # NEW: profile registry
├── src/
│   ├── core/
│   │   ├── profiles.py                # NEW: ProfileResolver and ProfileContext
│   │   └── model_router.py            # MODIFIED: slot-lookup accepts optional profile context
│   ├── api/
│   │   ├── routes.py                  # MODIFIED: register /p/{profile}/v1/... routes
│   │   └── web_search_interceptor.py  # NEW: tool-call inspection and model rewrite
│   └── services/
│       └── usage_tracking.py          # MODIFIED: add profile column
├── scripts/
│   ├── install-aliases.sh             # MODIFIED: point CLIs at profile paths
│   └── proxies                        # MODIFIED: add `proxies profile` subcommands
├── web-ui/
│   └── (profile management surface)   # MODIFIED: display overlay and request counts
└── tests/
    ├── integration/
    │   └── test_profile_routing.py    # NEW: full integration coverage
    └── unit/
        ├── test_profile_resolver.py   # NEW: resolver unit tests
        └── test_web_search.py         # NEW: interceptor unit tests
```

**Structure Decision**: Follows existing proxy convention — feature logic in `src/core/`, request handlers in `src/api/`, persistent storage in `src/services/`. The `profiles/` directory is sibling to `config/` to keep registry semantics distinct from proxy chain configuration.

---

## Complexity Tracking

No constitution violations to justify. This feature is:
- Additive (no existing code removed or modified behaviorally)
- Single-module core (ProfileResolver confines all new logic)
- Uses only standard library and existing FastAPI injection patterns
- Maps exactly to existing slot vocabulary and router architecture
