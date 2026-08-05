---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, config, parity, dynamic-config-gen, hermes-config, schema-validation]
---

# F12: Configuration System and Interface Parity + Dynamic Config Generation

> STATUS v1.1: COMPLETE (specs/001, 84/84 tasks). Single `ConfigResolver` (CLI > shell env > .env
> > stored > defaults), 63 settings x 4 surfaces, CI grep forbids stray os.environ. Extend via
> `config_manifest.py` (see 05-CONFIG-SCHEMA.md). TO BUILD: dynamic client-config generation
> (recommendations.json + `apply-recommendations` human gate) for Hermes config.yaml. "(PROPOSED)"
> tags below are superseded by 01-CURRENT-STATE.

Scope: one config source of truth that all three interfaces share with full parity, plus the
ability to GENERATE optimal config files for client CLIs (the Hermes config.yaml use case) and
live-update them as quotas approach limits.

## Single source, full parity (core user ask)

- CLI/.env is the base layer; TUI and Web UX wrap it identically. Any setting in one is in all.
  (`unified_project_idea_record.md:199-242,441-465`) (HARD)
- One .env (not .envrc); CLI args override env temporarily. (`:201,382-388`)
- gateway.yaml schema covers gateway/routing/providers/roles/compression/observability/orms/
  host_sentinel/control_mcp. (`PRD- MAUG.md:685-762`)
- Config file set: tiers.yaml (canonical weights), slot_definitions (min_tier/needs_tools/
  needs_vision/min_ctx; remove min_ai), blocklist.yaml, workers.yaml, provider_windows.yaml.
  (`Structural Assessment of the Hermes Model Selection System.md:136-145`)
- Namespaced provider registry PROVIDERS_<name>_URL / _API_KEY migrating from flat keys; Phase A
  lands on the namespaced shape. (`new proxy commands.md:47`) (CURRENT, in progress)
- Per-model system-prompt override files and custom-header pattern CUSTOM_HEADER_<NAME>.
  (`claude cody proxy .env.md:923-967`) (CURRENT)

## Dynamic config generation (core user ask)

- Generate optimal role -> model selections for a client CLI (Hermes config.yaml), and as a role
  approaches its quota, switch it to the next-best available model. (`unified_project_idea_
  record.md:64-89`; `HERMES_REFINEMENT_SPECIFICATION.md:819-912`)
- Output goes to recommendations.json; `hermes config apply-recommendations` applies it with a
  HUMAN GATE, preserving comments, keeping the last 5 .bak files, validating against
  config.schema.yaml with a config_version field. (`HERMES_REFINEMENT_SPECIFICATION.md:237-269`;
  `Hermes Model Rotation...md:253-266,522-523`)

## Hard requirements

- Full feature parity across .env/CLI, TUI, Web UX. (`unified_project_idea_record.md:25,463-465`)
- Client config files (Hermes config.yaml) are NEVER auto-mutated; human-gated apply only.
- Secrets resolved from env at startup by name, never persisted to disk; preserve loading order.
  (`PRD- MAUG.md:764-786`)

## Dependencies

- Consumes F04/F05 recommendations; read/written by F13 (CLI), F14 (TUI), F15 (Web UX); schema
  validated before any apply.

## Open questions

- Single config format: gateway.yaml + .env, or unify? Source uses both; confirm the split (env =
  secrets, yaml = structure is the working assumption).
