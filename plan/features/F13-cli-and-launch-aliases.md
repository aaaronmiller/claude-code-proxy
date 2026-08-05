---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, cli, launch-aliases, ordered-compositor, installer, bootstrap]
---

# F13: CLI Interface and Launch Aliases (Ordered Compositor)

> STATUS v1.1: PARTIAL. `proxies` lifecycle command + 3 zshrc aliases (cc/qw point at :8787; mode
> chosen at start time) are BUILT and deliberately minimal (repo rejected alias explosion).
> The Ordered Compositor `cc [R][M][S][C][O]` grammar is PROPOSED ONLY, not implemented, and is
> pending your launch-UX decision (keep minimal vs add cc 3-slot/5-slot). "(PROPOSED)" tags below
> are superseded by 01-CURRENT-STATE.

Scope: the maug CLI (the base configuration layer) plus the Ordered Compositor `cc` launcher
that starts coding CLIs against the gateway with a terse positional grammar, plus a one-command
installer/bootstrap.

## maug CLI

- Commands: start/stop/status/logs/rotate-keys/roles/chains; orms run [--force]; probe.
  (`PRD- MAUG.md:624-637`)
- Current: crosstalk CLI `python -m src.cli.crosstalk_cli`; `proxies profile list|show|validate`.
  (`claude cody proxy .env.md:847`; `new proxy commands.md:8-29`) (CURRENT)

## Ordered Compositor `cc`

- Positional single-char grammar `cc [R][M][S][C][O]`: position encodes Route, Model, Session,
  Context, Output. Trailing omission = defaults. (`Ordered Compositor Design Validation.md:165-235`)
- Route slot binds the gateway path: f=full-stack (Headroom+RTK), h=Headroom, d=direct, p=proxy,
  b=bypass. This is the launch-to-gateway-config mapping. (`:217,247-254`)
- Auto-route probing: localhost:8787 (Headroom) + localhost:8082 (proxy), 1s timeout, fallback to
  direct with stderr warning; idempotent proxy-stack auto-start via lock file. Defines the port
  topology. (`:247-260,522-535`) (HARD)
- Cross-tool consistency: cc/qw/cdx/oc share the grammar, only the model alphabet differs.
  (`:284-287`)
- Session reuse cc + / cc - / --repeat (XDG state); context auto-detect CLAUDE.md/AGENTS.md/.ccrc;
  extended mode ccx with named flags. (`:316,584-595,95-105,277-283`)
- DECISION pending: 5-slot "A+" grammar vs 3-slot "lean" revision. (`:637-804`)

## Installer / bootstrap

- Single-command alias installer: proxy on/off, with/without compression, dual continue-modes
  (cproxy-continue via OpenRouter, claude-continue via Anthropic). (`unified_project_idea_
  record.md:256-300`)
- Installer sets up all proxies on a new machine: Headroom + RTK default-on, CLIProxyAPI opt-in.
  (`:279-289,514`)

## Hard requirements

- Auto-route probe + auto-start must be idempotent and non-blocking (1s timeout, graceful direct
  fallback).
- CLI is the base config layer; parity contract with TUI/Web UX (F12).

## Dependencies

- Reads/writes config via F12; route slot selects chain (F02); status reflects F16 colors.

## Open questions

- 5-slot vs 3-slot grammar (the single biggest UX decision in this module).
