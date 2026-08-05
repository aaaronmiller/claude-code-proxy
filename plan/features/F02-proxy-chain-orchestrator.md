---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, proxy-chain, orchestrator, headroom, rtk, cliproxyapi]
---

# F02: Proxy Chain Orchestrator

> STATUS v1.1: BUILT. `config/proxy_chain.json`, proxy is itself a chain entry, reorder/toggle
> from all 4 surfaces (specs/001 FR-009..013). GAP: BIOS-style reorder UX polish in TUI/web.
> "(PROPOSED)" tags below are superseded by 01-CURRENT-STATE.

Scope: arrange any number of proxy stages in any order, validate the chain, and run requests
through it. The chain composes compression (Headroom, RTK), OAuth (CLIProxyAPI), and the MAUG
translation core. The system must also run with no chain at all (direct passthrough).

## Design

- Chain is first-class and reorderable. Default order Headroom(0) -> RTK(1) -> CLIProxyAPI(2,
  off) -> MAUG. Any count, any order. (`unified_project_idea_record.md:9-35`)
- PRD-MAUG default chain [maug]; extended [headroom, maug, litellm, provider].
  (`PRD- MAUG.md:661-679`)
- Three config surfaces for the chain: gateway.yaml, TUI editor, Control MCP `set_active_chain`.
  (`PRD- MAUG.md:669-673`)
- Per-CLI prefix routing already exists: /p/pi/v1, /p/opencode/v1, /p/claude/v1 (Anthropic
  passthrough), aliases psi/oc/cldo. (`new proxy commands.md:36-38`) (CURRENT)
- Provider diversity filter at chain level: no provider more than 2 consecutive.
  (`MODEL_ARCHITECTURE.md:332-341`) (CURRENT)
- Reference foundation: starbased-co/ccproxy hook system (rule_evaluator, model_router); the
  3-layer alt CLI-Interceptor -> API-Translator -> LiteLLM is a complementary view.
  (`Claude Code Backend Middleware - Project Assessment.md:213-229,824-841`)

## Hard requirements

- Chain MUST be adjustable to any count and any order. (`unified_project_idea_record.md:21`)
- System MUST run with OR without the chain, and support both continue-modes simultaneously
  (cproxy-continue via OpenRouter and claude-continue via Anthropic). (`:33-35,265-273`)
- Chain validation MUST reject loops, incompatible mid-flight mutation, and format mismatch; the
  resolved chain manifest appears in every request log. (`PRD- MAUG.md:674-679`)

## Dependencies

- Stages: Headroom + RTK (F08), CLIProxyAPI OAuth (F09/F06), MAUG core (F01).
- Reorder UI in TUI (F14) and Web UX drag-drop (F15); manifest to observability (F11).

## Open questions

- Where does the context engine (hermes-lcm) sit relative to the chain vs the client? F08 keeps
  it on assembled context, after RTK/Headroom; confirm it is not a chain stage.
- CLIProxyAPI default off vs on per provider that needs OAuth.
