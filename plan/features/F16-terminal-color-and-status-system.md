---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, terminal, color, status-bar, tuids-llm, statusline, accessibility]
---

# F16: Terminal Color and Status System

> STATUS v1.1: BUILT (mostly). tmux status bars, statusline scripts (Claude Code + Codex), RTK
> stats cache, jitter-fix layout all present in `scripts/`. TO DO: formalize the TUIDS-LLM color
> scheme + surface RTK tokens-saved stats. "(PROPOSED)" tags below superseded by 01-CURRENT-STATE.

Scope: the operator-facing terminal output styling for the gateway (routing logs, status,
metrics, streaming liveness) and the static status bars. This governs operator readability, NOT
model content. Spec name: TUIDS-LLM v1.0.

## Design

- Semantic color role map (9 roles: error/warn/success/info/metrics/debug/accent/primary/
  secondary) + luminance tiers (hue = category, luminance = hierarchy) + 4-hue ceiling per cycle
  + 60-30-10 surface ratio. (`Terminal Color System.md:1-35,204-279`)
- Motion layer (spinner/pulse/progress/stream-indicator), --no-motion strips it. (`:50-58,432-476`)
- Output map for request/response/content/error/concurrent blocks, with a request-id hex prefix
  for concurrency. (`:59-91,226-258`)
- Palette progressive enhancement ANSI-16 -> 256 -> truecolor (Nord-derived, dark + light).
  (`:92-113,562-572`)
- Config precedence CLI > env > file > defaults (NO_COLOR / CLICOLOR / PROXY_COLOR / COLORTERM);
  proxy-color.yml; --format=json bypass. (`:122-131,281-306`)

## Status bars (operator-facing)

- Static color status bars: Headroom top, proxy bottom, RTK third; no layout shift; left/right
  align; tokens-saved, tokens/s, last error. (`unified_project_idea_record.md:107-130,162-180`)
- Claude Code statusline integration: pipe proxy stats, working/fault indicator per layer.
  (`:166-171,504`)
- Current terminal color env: TERMINAL_COLOR_SCHEME / SESSION_COLORS / DISPLAY_MODE. (`claude cody
  proxy .env.md:713-737`) (CURRENT)

## Hard requirements

- Content sanctity: zero ANSI on model output tokens; content buffer is read-only and throws on
  escape. (`Terminal Color System.md:38,174,799`)
- Color is never the sole signal: glyph-per-color redundancy (cross/triangle/check/arrow/diamond).
  (`:42,363-368`)
- ANSI injection sanitization on untrusted headers/URLs/body before colorize (security). (`:47,588-621`)
- NO_COLOR and pipe (isatty) parity: full function without color. (`:116-131`)
- Belt-and-suspenders dim: pair SGR2 with an explicit darker color (terminals drop SGR2). (`:166,415-428`)

## Dependencies

- Shared status-bar format with F14 and F15; consumes F11 metrics and F08 compression stats (RTK
  stats currently missing, add them).

## Open questions

- Consolidate the 3 overlapping palette tables in the source before implementation. (`:189-202,376-384,816-826`)
