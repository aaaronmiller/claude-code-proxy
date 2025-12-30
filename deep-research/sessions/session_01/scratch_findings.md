# Scratch Findings: Claude Code -> Gemini Tool Call Transformation
**Session ID:** session_01

## Phase 2: Breadth - Search Findings

### Search 1: Schemas & Specs
- **Claude Code CLI**: Uses `bash` tool (persistent session), `repl`, `grep`, `glob`. Expects strict JSON schema.
- **Gemini**: Has "Function Calling" and native "Code Execution" (often termed "Bash Tool" in Gemini 3).
- **Mismatch**: Claude expects `command` for bash. Gemini often outputs `prompt` or `code`.
- **Validation**: Anthropic enforces `strict: true` validation. Gemini is looser, sometimes emitting `prompt` instead of defined schema if not carefully prompted or if using "Thinking" models that reference internal tool definitions.


### Search 2: Proxy Patterns
- **LiteLLM**: Gold standard. Handles "thought signatures" injection/extraction for Gemini 3+. Converts parameters to unified `thinkingLevel`.
- **Streaming Algo**: "In-memory mutation" is key. Buffering partial JSON, applying repairs (`json_repair`), or using event-driven parsing (jsonriver) are common strategies.
- **Claude Compatibility**: Proxies often need to "fake" the Anthropic format completely, including "interleaved thinking" structure if using Gemini 3.

### Search 3: Gemini Quirks
- **Ghost Streams**: Known issue where `functionCall` event is followed by text chunks *in the same stream*. Clients (like Claude Code?) might stop reading after the function call, missing the text.
- **Duplicate History**: `chat_session` history growing with duplicates after function calls.
- **Loops**: Repetitive tool calling (infinite loops) is a common failure mode, often due to context loss or unavailable endpoints.
- **SSE Format**: Gemini's OpenAI compat mode sometimes omits `index` in tool_calls, breaking parsers.


### Search 4: Community Solutions
*Pending...*

### Search 5: Edge Cases
*Pending...*

## Grounding (GitHub/Social)
*Pending...*
