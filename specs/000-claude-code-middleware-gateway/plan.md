# Implementation Plan: Claude Code Middleware Gateway

**Branch**: `001-claude-code-middleware-gateway` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-claude-code-middleware-gateway/spec.md`

## Summary

This plan transforms the current repository into a focused Claude Code middleware gateway paired with Claude Code Swap / CC Switch. The gateway keeps Anthropic API compatibility at the edge, adds a capability registry and transformation matrix as sources of truth, hardens adapter-based request/response/streaming translation, and pushes non-core platform features into optional addons or separate subprojects.

## Primary Planning Inputs

- [requirements.md](./requirements.md)
- [design.md](./design.md)
- [transformation-matrix.md](./transformation-matrix.md)
- [research.md](./research.md)

## Planned Phases

### Phase 0: Freeze Scope

- confirm middleware core boundaries
- classify current modules as core vs addon vs separate subproject

### Phase 1: Introduce Capability Registry

- define machine-readable Anthropic capability inventory
- encode provider adapter support states
- use the registry to drive the transformation matrix

### Phase 2: Harden Anthropic Edge

- normalize `/v1/messages` and `/v1/messages/count_tokens`
- formalize streaming event support
- formalize stop reason mapping

### Phase 3: Close Protocol Gaps

- structured outputs via `output_config.format`
- automatic / block-level caching
- thinking signatures and omitted-display behavior
- server tools and tool-family classification
- accurate token counting strategy

### Phase 4: Split Non-Core Features

- move dashboard / analytics / alerts / RBAC / GraphQL / crosstalk into addon or subproject boundaries

### Phase 5: Compatibility Test Harness

- fixture-test every supported Anthropic surface
- require coverage before support claims are upgraded

### Phase 6: Release-Driven Maintenance

- document update workflow from Anthropic release notes + Claude Code changelog
- regenerate docs and compatibility matrix on every protocol change

## Immediate Next Command

Use the next spec workflow step to generate the definitive task list from these documents.

