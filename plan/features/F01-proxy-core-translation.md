---
date: 2026-06-16 00:00:00 PT
ver: 1.0.0
author: claude-code-worker
model: claude-opus-4-8
tags: [ai-gateway, proxy-core, translation, tool-calls, streaming, canonical-schema]
---

# F01: Proxy Core and Translation Layer

> STATUS v1.1: BUILT. Hand-built Anthropic<->OpenAI converter (`request_converter.py` 993L,
> `response_converter.py` 1675L), no LiteLLM. GAPS to build (per transformation-matrix): prompt
> caching, server tools, structured outputs, thinking signature_delta, authoritative
> count_tokens, capability discovery. "(PROPOSED)" tags below are superseded by 01-CURRENT-STATE.

Scope: the provider/model/harness-agnostic heart. Accept any supported wire format in,
translate through a canonical schema, dispatch to any provider, translate the response back.
This is the layer that lets a Claude Code session drive an OpenRouter model, or route all
tool calls to a free model.

## Design

- Transport in: OpenAI, Anthropic Messages, Gemini, Bedrock-Converse endpoints; Cohere as a
  legacy 5th. Base-URL re-target so a harness just points at MAUG. (`PRD- MAUG.md:129-141`)
- Canonical internal schema: OpenAI tool shape + JSON-Schema Draft 2020-12 + Pydantic v2
  `strict=True`. Translate A -> Canonical -> B, never A -> B pairwise. (`PRD- MAUG.md:147-164`)
- Per-provider bidirectional adapters (strategy pipeline), with contract symmetry tests.
  (`PRD- MAUG.md:166-179`)
- Streaming tool-call reassembly state machine: idle -> collecting_name -> collecting_args ->
  validating -> complete, using ijson; per-provider quirks. (`PRD- MAUG.md:180-195`)
- Turn-scoped tool-call ID registry mapping provider_id <-> canonical_id <-> reply_id.
  (`Proxy update plan.md:404,431`)
- Schema simplification heuristics for weak providers: flatten nested objects, enum -> string,
  drop format/pattern. (`PRD- MAUG.md:1416-1419`)
- Reasoning/thinking transforms carried from current system: REASONING_MAX_TOKENS,
  REASONING_EFFORT, REASONING_EXCLUDE, VERBOSITY, per-model overrides. (`claude cody proxy .env.md:639-667`) (CURRENT)
- Per-CLI route prefixes /p/{profile}/v1 with Anthropic passthrough. (`new proxy commands.md:36-38`) (CURRENT)
- Capability-aware weighted routing hand-off: score = capability_match * latency * error_penalty
  (selection itself lives in F04). (`Proxy update plan.md:233-240`)

## Hard requirements

- Lossless round-trip: unknown provider fields preserved in `_meta` / x_provider_extensions.
  (`Proxy update plan.md:169`)
- Canonicalize all schemas to Draft 2020-12; strip unsupported fields per target. (`PRD- MAUG.md:406`)
- Translate before dispatch to Antigravity (rejects Anthropic format, needs Gemini contents[],
  rejects $ref/const). (`PRD- MAUG.md:178,1387`)
- 100% tool-call parity across the 4 wire formats, 0 silent format drops (Phase A metric).
- Capability-boundary check post-translation pre-dispatch (reject scope drift vs role allowed_tools).
  (`PRD- MAUG.md:824`; `Proxy update plan.md:504-515`)

## Advanced Anthropic tool primitives (currently zero coverage, must translate or strip)

PTC (programmatic tool calling), Tool Search, defer_loading, server_tool_use, input_examples,
effort, adaptive thinking. Changelog and field-level spec at
`Claude Code Backend Middleware - Project Assessment.md:255-518,437-503`. PTC decomposition is
the hardest item (sandbox stubs) and slots latest. (`:897-917`)

## Dependencies

- Consumes provider capability registry (F03) to know what each target supports.
- Feeds routing/selection (F04) and fallback field-stripping cascade (F05).
- Wrapped by the proxy chain (F02); emits structured translation_delta to observability (F11).

## Open questions

- Confirm the exact wire-format set for v1 (4 vs 5 with Cohere).
- behavior-driven normalization: detect tool-call shape and streaming format from the response
  itself and cache it, per the user's normalization principle, rather than hardcoding provider
  exceptions.
