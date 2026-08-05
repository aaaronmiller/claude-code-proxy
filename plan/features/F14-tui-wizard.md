---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, tui, wizard, textual, status-bar-builder, parity]
---

# F14: TUI Wizard

> STATUS v1.1: PARTIAL. `start_proxy.py --configure-advanced` (19 categories, all 63 settings)
> BUILT. TO BUILD: the Textual live-monitoring TUI + BIOS-style chain reorder + status-bar builder.
> "(PROPOSED)" tags below superseded by 01-CURRENT-STATE.

Scope: a terminal wizard to assign settings and make choices, with full feature parity to the
CLI/.env layer. Includes a live monitoring view and a status-bar builder.

## Design

- Textual TUI as a primary interface: live view + drill-downs (cohort / key ledger / chain /
  quota discriminator). (`PRD- MAUG.md:604-622,1759-1775`)
- Arrow-key navigation for ALL settings (proxies / models / providers / roles), parity with CLI.
  (`unified_project_idea_record.md:222-230`) (HARD)
- Status-bar builder with real-time preview (this replaces the old "prompt injection" feature);
  writes the .claude statusline file and supports other CLIs in the same format. (`:182-194`)
- Chain management with drag/reorder concept (mirrors Web UX drag-drop). (`Proxy update
  plan.md:26,30,32,38`)
- Daily-mode scannable output redesign (5-second scan: header / incumbent panel / top-3 per slot
  / --appendix opt-in). (`Structural Assessment of the Hermes Model Selection System.md:112-134`)

## Hard requirements

- Feature parity with CLI/.env (F12): every configurable setting is reachable in the TUI.
- Status-bar output format is shared with the CLI statusline and Web UX so all three render the
  same modules.

## Dependencies

- Reads/writes config via F12; live data from F11; renders with F16 color system; edits chain
  (F02), roles (F04), providers/keys (F06).

## Open questions

- Is the TUI a thin client over the same config/API the Web UX uses, or a separate code path? A
  shared API keeps parity cheap; confirm.
