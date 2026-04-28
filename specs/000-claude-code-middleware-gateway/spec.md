# Feature Specification: Claude Code Middleware Gateway

**Feature Branch**: `001-claude-code-middleware-gateway`
**Created**: 2026-03-18
**Status**: Draft
**Input**: User description requesting a pivot of the current project into a focused Claude Code middleware gateway operating in conjunction with Claude Code Swap / CC Switch, backed by an authoritative Anthropic transformation matrix, competitive ecosystem research, and spec-driven planning documents.

---

## Summary

Refactor the current repository away from a broad "ultimate proxy" platform and toward a narrowly-scoped Anthropic-compatible middleware gateway whose primary job is protocol fidelity between Claude Code and non-Anthropic backend providers.

The gateway must:

1. preserve Claude Code and Agent SDK compatibility,
2. transform Anthropic Messages API semantics to alternative providers,
3. track protocol support through a maintained transformation matrix,
4. integrate cleanly with Claude Code Swap / CC Switch,
5. separate non-core platform features into addons or subprojects.

---

## Canonical Documents

- [requirements.md](./requirements.md)
- [design.md](./design.md)
- [transformation-matrix.md](./transformation-matrix.md)
- [research.md](./research.md)

These documents are the authoritative basis for later planning and task generation.

---

## Core Decision

Preferred architecture:

`Claude Code -> Claude Code Swap / CC Switch -> this middleware gateway -> provider adapter -> upstream model provider`

The gateway remains responsible for Anthropic protocol fidelity. CC Switch remains responsible for switching and user-facing profile control.

---

## Success Criteria

- Anthropic surface area is explicitly classified as implemented, partial, passthrough-only, or missing.
- Latest late-2025 and early-2026 Anthropic protocol changes are represented in the matrix.
- Non-core project features are separated from the middleware core in the design.
- The spec bundle is sufficient input for a follow-on planning/tasks phase.

