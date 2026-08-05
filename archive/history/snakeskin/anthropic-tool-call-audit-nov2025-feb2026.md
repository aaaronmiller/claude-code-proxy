---
date: 2025-02-19 15:15:00 PST
ver: 1.0.0
author: Sliither
model: claude-opus-4-6
tags: [anthropic, tool-calls, changelog, proxy-audit, api, claude-code, timeline, gemini-routing]
---
# Anthropic Tool Call Changes: Nov 2025 - Feb 2026 Proxy Audit

## Summary

Sonnet 4.6 (Feb 17, 2026) did NOT introduce new tool call types. Instead, it promoted
several beta features to GA and added dynamic web search filtering. The major tool call
primitives all shipped with Opus 4.5 on Nov 24, 2025. Below is the complete chronological
record from the official Anthropic Developer Platform release notes, cross-referenced with
the Claude Code CHANGELOG and the "What's New in Claude 4.6" docs page.

---

## Chronological Tool Call Changes (Nov 2025 - Feb 2026)

### November 14, 2025
**Structured Outputs (beta)**
- Beta header: `structured-outputs-2025-11-13`
- New parameter: `output_format` with `json_schema` type
- Models: Sonnet 4.5, Opus 4.1
- Proxy impact: Gemini has its own JSON mode; translate or strip

### November 18, 2025
**Claude in Microsoft Foundry**
- New platform: Azure endpoint for Claude via Foundry
- Proxy impact: New `azure_ai/` provider prefix in LiteLLM

### November 24, 2025 (Opus 4.5 launch -- MAJOR TOOL RELEASE)
**Programmatic Tool Calling (beta)**
- Beta header: `advanced-tool-use-2025-11-20`
- New tool field: `allowed_callers: ["code_execution_20250825"]`
- New built-in tool: (reused) `code_execution_20250825`
- New response types: `server_tool_use`, `code_execution_tool_result`
- New response field: `caller` on `tool_use` blocks
- New response field: `container` (id, expires_at) on messages
- Proxy impact: HIGH -- requires PTC decomposition sandbox

**Tool Search Tool (beta)**
- Beta header: `advanced-tool-use-2025-11-20`
- New tool field: `defer_loading: true` on tool definitions
- New built-in tools: `tool_search_tool_regex_20251119`, `tool_search_tool_bm25_20251119`
- New response type: `tool_reference` blocks
- MCP toolset config: `default_config.defer_loading`, per-tool `configs` override
- Proxy impact: HIGH -- requires local tool registry + search

**Tool Use Examples (beta)**
- Beta header: `advanced-tool-use-2025-11-20`
- New tool field: `input_examples` (array of example input objects)
- Proxy impact: LOW -- inject into description string or strip

**Effort Parameter (beta)**
- Beta header: `effort-2025-11-18`
- New parameter: `effort` ("low", "medium", "high")
- Proxy impact: MEDIUM -- map to Gemini `reasoning_effort` or strip

**Client-Side Compaction (SDK)**
- Python/TypeScript SDK: auto context summarization via `tool_runner`
- Proxy impact: NONE -- client-side only

### December 4, 2025
**Structured Outputs: Haiku 4.5 support**
- Extended `output_format` support to Haiku 4.5
- Proxy impact: Same as Nov 14 entry

### December 19, 2025
**No tool changes** (Haiku 3.5 deprecation announced)

### January 29, 2026
**Structured Outputs (GA)**
- Beta header no longer required for Sonnet 4.5, Opus 4.5, Haiku 4.5
- Parameter moved: `output_format` -> `output_config.format`
- Proxy impact: Update parameter name in translation layer

### February 5, 2026 (Opus 4.6 launch)
**Adaptive Thinking (new)**
- New parameter: `thinking: {type: "adaptive"}`
- Replaces `thinking: {type: "enabled", budget_tokens: N}` (deprecated)
- Proxy impact: MEDIUM -- Gemini uses `reasoning_effort`; strip or translate

**Effort Parameter (GA)**
- No longer requires beta header
- New level: `"max"` (Opus 4.6 only)
- Proxy impact: Same as Nov 24, now without beta header requirement

**Fine-Grained Tool Streaming (GA)**
- Previously: beta header `fine-grained-tool-streaming-2025-05-14`
- Now: GA on all models, no header needed
- Streams partial JSON tool parameters without buffering
- Proxy impact: LOW -- LiteLLM buffers streaming; partial JSON handled

**Compaction API (beta)**
- Server-side context summarization
- New parameter: auto-summarizes when approaching context limits
- Proxy impact: LOW -- strip for Gemini, manage context client-side

**128K Output Tokens**
- Opus 4.6: doubled from 64K to 128K max output
- Proxy impact: Gemini has its own output limits; cap accordingly

**Data Residency Controls**
- New parameter: `inference_geo` ("global" or "us")
- Proxy impact: NONE for Gemini routing; strip

**Output Config Migration**
- `output_format` -> `output_config.format` (deprecated, still works)
- Proxy impact: Update translation layer

**Prefill Removal (BREAKING)**
- Opus 4.6 returns 400 on prefilled assistant messages
- Proxy impact: If routing TO Opus 4.6, strip prefills; Gemini still supports

**Interleaved Thinking Deprecation**
- `interleaved-thinking-2025-05-14` header deprecated on Opus 4.6
- Adaptive thinking auto-enables interleaved thinking
- Proxy impact: Stop sending this header for Opus 4.6 requests

### February 17, 2026 (Sonnet 4.6 launch)
**Programmatic Tool Calling (GA)**
- Moved from beta to GA -- no longer requires `advanced-tool-use-2025-11-20` header
- Proxy impact: CRITICAL -- this is now the default path, not optional

**Tool Search Tool (GA)**
- Moved from beta to GA
- Proxy impact: CRITICAL -- same as above

**Tool Use Examples (GA)**
- Moved from beta to GA
- Proxy impact: Same approach, now default behavior

**Memory Tool (GA)**
- Previously beta (since Sep 29, 2025)
- Proxy impact: LOW -- memory is Anthropic-specific; strip or implement locally

**Code Execution Tool (GA)**
- Previously beta since May 22, 2025; v2 since Sep 2, 2025
- Proxy impact: Already handled; confirm GA behavior matches beta

**Dynamic Web Search Filtering (NEW with Sonnet 4.6)**
- New tool versions: `web_search_20260209`, `web_fetch_20260209`
- Claude writes and executes code to filter search results before context
- Uses PTC sandbox internally for post-processing
- 24% input token reduction, BrowserComp accuracy 33% -> 46.6%
- Proxy impact: MEDIUM -- Gemini has grounding/search; these specific tool
  versions won't exist. Strip version suffixes or implement equivalent filtering.

**Effort Parameter for Sonnet**
- Sonnet 4.6 introduces effort parameter to Sonnet family
- Recommended: `medium` for most Sonnet 4.6 use cases
- Proxy impact: Same translation as Opus effort

**1M Context Window (beta)**
- Now available for Opus 4.6 (previously Sonnet 4/4.5 only)
- Proxy impact: Gemini 2.5 Pro has 1M+ context natively

**Agent Teams (Claude Code -- experimental)**
- Shipped with Opus 4.6, enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
- 13 TeammateTool operations (see previous document)
- Proxy impact: Process-level, not API-level (see previous analysis)

---

## Tool Call Inventory: Proxy Coverage Checklist

### Built-in Tool Types (versioned identifiers)

| Tool Type ID | Introduced | Status | Proxy Support Needed |
|---|---|---|---|
| `code_execution_20250825` | May 22, 2025 (v1); Sep 2, 2025 (v2) | GA (Feb 2026) | YES -- sandbox or Gemini code exec |
| `tool_search_tool_regex_20251119` | Nov 24, 2025 | GA (Feb 2026) | YES -- local regex search impl |
| `tool_search_tool_bm25_20251119` | Nov 24, 2025 | GA (Feb 2026) | YES -- local BM25 search impl |
| `web_search_20250305` | May 7, 2025 | GA | YES -- map to Gemini grounding |
| `web_search_20260209` | Feb 17, 2026 | GA (Sonnet 4.6+) | YES -- dynamic filtering variant |
| `web_fetch_20250305` | Sep 10, 2025 | GA | YES -- HTTP fetch impl |
| `web_fetch_20260209` | Feb 17, 2026 | GA (Sonnet 4.6+) | YES -- dynamic filtering variant |
| `computer_20250124` | Feb 24, 2025 | GA | OPTIONAL -- computer use |
| `text_editor_20250124` | Feb 24, 2025 | GA | OPTIONAL -- text editor |
| `text_editor_20250728` | Jul 28, 2025 | GA | OPTIONAL -- text editor v2 |
| `bash_20250124` | Feb 24, 2025 | GA | OPTIONAL -- bash tool |
| `memory_20250929` | Sep 29, 2025 | GA (Feb 2026) | LOW -- Anthropic-specific |
| `clear_tool_uses_20250919` | Sep 29, 2025 | Beta | LOW -- context editing |
| `clear_thinking_20251015` | Oct 28, 2025 | Beta | LOW -- thinking clearing |

### Tool Definition Fields to Translate/Strip

| Field | Introduced | Status | Gemini Action |
|---|---|---|---|
| `defer_loading` | Nov 24, 2025 | GA | Strip; handle in local registry |
| `allowed_callers` | Nov 24, 2025 | GA | Strip; decompose PTC locally |
| `input_examples` | Nov 24, 2025 | GA | Inject into `description` or strip |

### Response Block Types to Translate

| Block Type | Introduced | Status | Gemini Translation |
|---|---|---|---|
| `tool_use` | Original | GA | Map to `function_call` |
| `tool_result` | Original | GA | Map to `function_response` |
| `server_tool_use` | Nov 24, 2025 | GA | Decompose; run code locally |
| `code_execution_tool_result` | Nov 24, 2025 | GA | Convert to standard `tool_result` |
| `tool_reference` | Nov 24, 2025 | GA | Handle in local tool registry |

### Response Fields to Translate

| Field | Location | Introduced | Gemini Action |
|---|---|---|---|
| `caller` | On `tool_use` blocks | Nov 24, 2025 | Strip; handle PTC routing locally |
| `container` | Message-level | Nov 24, 2025 | Strip; manage sandbox state locally |
| `inference_geo` | Request param | Feb 5, 2026 | Strip |
| `output_config.format` | Request param | Jan 29, 2026 | Map to Gemini JSON mode |
| `thinking.type: "adaptive"` | Request param | Feb 5, 2026 | Map to `reasoning_effort` |
| `effort` | Request param | Nov 24, 2025 (GA Feb 2026) | Map to `reasoning_effort` |
| `speed: "fast"` | Request param | Feb 5, 2026 | Strip (Anthropic infra only) |

### Beta Headers Timeline

| Header | Introduced | Current Status |
|---|---|---|
| `advanced-tool-use-2025-11-20` | Nov 24, 2025 | GA as of Feb 17, 2026 (header optional) |
| `fine-grained-tool-streaming-2025-05-14` | Jun 11, 2025 | GA as of Feb 5, 2026 (header optional) |
| `structured-outputs-2025-11-13` | Nov 14, 2025 | GA as of Jan 29, 2026 (header optional) |
| `interleaved-thinking-2025-05-14` | May 22, 2025 | Deprecated on Opus 4.6 (ignored) |
| `effort-2025-11-18` | Nov 24, 2025 | GA as of Feb 5, 2026 (header optional) |
| `computer-use-2025-01-24` | Feb 24, 2025 | Still required for computer tool |
| `skills-2025-10-02` | Oct 16, 2025 | Still beta |
| `context-management-2025-06-27` | Sep 29, 2025 | Still beta |
| `fast-mode-2026-02-01` | Feb 5, 2026 | Beta (Opus 4.6 only) |
| `tool-search-tool-2025-10-19` | ~Oct 2025 | Bedrock-specific variant |

---

## What Sonnet 4.6 Actually Changed (Feb 17, 2026)

To directly answer the question: Sonnet 4.6 did NOT introduce new tool call types or
new tool definition fields. What it did was:

1. **Promoted to GA:** Programmatic Tool Calling, Tool Search Tool, Tool Use Examples,
   Memory Tool, Code Execution Tool (all previously beta since Nov 24, 2025 or earlier)

2. **New tool versions:** `web_search_20260209` and `web_fetch_20260209` with dynamic
   filtering (code execution sandbox post-processes search results)

3. **Model capabilities:** Adaptive thinking for Sonnet, effort parameter for Sonnet,
   1M context window beta, improved computer use (72.5% OSWorld)

4. **No new response block types** beyond what Opus 4.6 (Feb 5) already defined

The practical implication for the proxy: if you already handle the Nov 24, 2025 beta
primitives, you are mostly covered. The GA promotion means the beta header
`advanced-tool-use-2025-11-20` is now optional (features work without it), and the
`web_search_20260209`/`web_fetch_20260209` tool versions need handling.

---

## Gap Analysis: What Your Proxy Likely Needs

### Confirmed covered by LiteLLM (as of Feb 2026):
- Basic `tool_use` / `tool_result` translation (Anthropic <-> Gemini)
- `anthropic/v1/messages` endpoint translation
- Streaming translation
- Thought signature preservation (Gemini 3)
- `effort` / `reasoning_effort` mapping
- Beta header forwarding (native Anthropic calls)
- `drop_params: true` for unsupported fields

### Requires custom middleware (Layer 2):
- `defer_loading` + tool search (local registry + regex/BM25)
- `allowed_callers` + PTC execution loop (local Python sandbox)
- `server_tool_use` decomposition
- `caller` field routing
- `code_execution_tool_result` conversion
- `input_examples` -> description injection
- `container` lifecycle management
- `web_search_20260209` / `web_fetch_20260209` dynamic filtering
- `thinking: {type: "adaptive"}` translation
- `output_config.format` structured output translation

### Not applicable to Gemini routing:
- `inference_geo` (Anthropic infrastructure)
- `speed: "fast"` (Anthropic infrastructure)
- `memory_20250929` (Anthropic-specific persistence)
- Agent Teams TeammateTool (process-level, not API-level)
- `clear_tool_uses_20250919` / `clear_thinking_20251015` (context editing)
