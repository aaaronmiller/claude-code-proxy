# Solution Architecture: Bridging Claude Code CLI and Google Antigravity

**Author:** Droid
**Date:** December 24, 2025
**Context:** Production fix for "Superpowers" loop and authentication failures.

## 1. Problem Statement
The objective was to run **Claude Code CLI** (a tool hardcoded for Anthropic's API) against **Google's Antigravity/Gemini models** (via VibeProxy). The system failed with:
1.  **403 Forbidden**: "Lack a Gemini Code Assist license" for Claude models.
2.  **InputValidationError**: Bash tool failed due to unexpected `prompt` parameter.
3.  **Infinite Loops**: The model repeated successful tool calls endlessly.
4.  **Ghost Streams**: Duplicate responses confused the client.

## 2. Why Other Methods Failed

### 2.1 The "Simple Proxy" Fallacy
Attempting to just forward requests failed because the protocols are **semantically incompatible**, not just syntactically different.
*   **Failure:** Forwarding `claude-haiku` to VibeProxy resulted in `403` because the user lacked the enterprise license for the mapped model.
*   **Fix:** We mapped `SMALL_MODEL` to `gemini-3-flash`, a high-performance, permissive model.

### 2.2 The "Copy-Paste" Patch
Attempting to fix the Bash schema by copying `prompt` to `command` (`args["command"] = args["prompt"]`) failed.
*   **Failure:** Claude Code's validator is strict. It rejected the *presence* of the extra `prompt` key.
*   **Fix:** We implemented a **Rename-and-Delete** strategy (`args["command"] = args.pop("prompt")`).

### 2.3 The "Streaming Blind Spot"
Fixing the JSON payload in the non-streaming path was insufficient because Claude Code relies heavily on **streaming**.
*   **Failure:** The CLI parses the raw stream. If the stream contains `"prompt":`, the CLI validation fails *before* the proxy can parse and fix the full JSON.
*   **Fix:** We implemented a **Stream-Side Patch** that performs string replacement (`.replace('"prompt":', '"command":')`) on the raw chunk buffer, ensuring the client receives the expected key in real-time.

### 2.4 The "History Amnesia" (Loop Cause)
Fixing the outgoing request created a discrepancy in the conversation history.
*   **Failure:** We sent `command` to the client. The client executed it. We sent `command` back to Gemini in the history. Gemini (trained to output `prompt`) saw `command`, didn't recognize it as its own valid tool call, and re-generated the tool call, causing an infinite loop.
*   **Fix:** We implemented **Reverse-Normalization**. When sending history to Gemini, we rename `command` *back* to `prompt`. This maintains the model's illusion of consistency.

## 3. The Validated Solution

### 3.1 Configuration (`.env`)
Map abstract tiers to available, authorized Gemini models.
```bash
BIG_MODEL="gemini-claude-opus-4-5-thinking"      # Or gemini-3-pro if restricted
MIDDLE_MODEL="gemini-claude-sonnet-4-5-thinking" # Or gemini-3-pro
SMALL_MODEL="gemini-3-flash"                     # CRITICAL: Fixes tool call speed & auth
```

### 3.2 Response Converter (`response_converter.py`)
**Forward Normalization**: Transform Gemini output to Claude expectation.
```python
# Streaming Path (String Replacement)
if tool_name in ["bash", "repl"]:
    partial_args = partial_args.replace('"prompt":', '"command":')

# Non-Streaming Path (Dict Manipulation)
if "prompt" in args:
    args["command"] = args.pop("prompt")
```

### 3.3 Request Converter (`request_converter.py`)
**Reverse Normalization**: Transform Claude history to Gemini expectation.
```python
# In convert_claude_assistant_message
if tool_name == "bash" and "command" in args:
    args["prompt"] = args.pop("command")
```
**Temperature Control**: Force deterministic outputs for router models.
```python
if model_size == "small":
    openai_request["temperature"] = 0
```

## 4. Verification & Recovery
To verify the fix:
1.  Clear logs: `echo "" > logs/debug_traffic.log`
2.  Run tool: `claude -p "ls -la"`
3.  Check logs for `200 OK` and correct argument transformation.

If looping persists:
1.  Check `debug_traffic.log` for the `role: user` history block. Ensure it contains `"prompt": ...` for previous tool calls.
2.  Verify `SMALL_MODEL` is `gemini-3-flash` (or another model that supports `function_response` correctly).

## 5. Conclusion
This architecture provides a robust, bi-directional translation layer that satisfies the strict requirements of both the Claude Code CLI and the Gemini API, enabling seamless interoperability without modifying the client.
