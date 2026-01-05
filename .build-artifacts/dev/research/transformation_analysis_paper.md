# Transformation Analysis: Protocol Mismatches in Claude Code <> Gemini Bridge

**Date:** December 24, 2025
**Scope:** Architecture Analysis of Custom Proxy Middleware (Claude Code CLI -> VibeProxy -> Google Antigravity)

## 1. Executive Summary
This paper documents the structural incompatibilities identified between the **Claude Code CLI** (Client) and the **Google Antigravity/Gemini API** (Provider), and the architectural interventions required to bridge them. The system exhibited critical failures including persistent 403 License errors, `InputValidationError` on tool calls, and infinite execution loops. The root causes were traced to three distinct protocol layers: **Authentication Scope**, **Tool Schema Dialects**, and **Conversation History State**.

## 2. Failure Modes & Root Cause Analysis

### 2.1 The "License Lock" (403 Forbidden)
**Symptom:** API requests for `claude-opus-4-5-thinking` and `claude-sonnet-4-5` failed with `403 Forbidden` and "lack a Gemini Code Assist license".
**Root Cause:**
*   Google's "Antigravity" service exposes Claude models but restricts them to specific enterprise licenses ("Gemini Code Assist Standard/Enterprise").
*   The default `.env` configuration mapped `SMALL_MODEL`, `MIDDLE_MODEL`, and `BIG_MODEL` all to these restricted Claude IDs.
*   The user's account lacked the required entitlement, causing immediate rejection for all requests, including the "router" (Small) requests used for tool selection.

**Resolution:**
*   **Operational Workaround**: Remapped `SMALL_MODEL` to `gemini-3-flash` and `MIDDLE/BIG` models to `gemini-3-pro-preview`. These first-party Google models have more permissive access controls and function correctly without the enterprise license.

### 2.2 The "Bash Dialect" Mismatch (InputValidationError)
**Symptom:** Claude Code CLI crashed with `InputValidationError: Bash failed... unexpected parameter 'prompt'`.
**Root Cause:**
*   **Claude Code CLI** enforces a strict schema for its `Bash` tool, requiring the argument name `command`.
*   **Gemini Models** (specifically Flash/Pro) were trained on datasets where bash tools often use the argument name `prompt` or `code`.
*   When acting as the router, Gemini "hallucinated" the `prompt` parameter.
*   The proxy originally *copied* `prompt` to `command` but left `prompt` in place. The strict Pydantic validator in the CLI rejected the payload due to the presence of the unknown `prompt` key.

**Resolution (Response Path):**
*   Implemented a **Rename-and-Delete** strategy in `response_converter.py`.
*   **Logic:** `if "prompt" in args: args["command"] = args.pop("prompt")`.
*   **Streaming Fix:** Applied a real-time string replacement (`.replace('"prompt":', '"command":')`) in the streaming buffer to ensuring the CLI's incremental parser receives the expected key.

### 2.3 The "Amnesic Loop" (Infinite Tool Repetition)
**Symptom:** The model successfully executed `ls -la`, received the output, but immediately executed `ls -la` again, looping indefinitely.
**Root Cause:**
*   **History Mismatch**: The proxy modified the *outgoing* tool call to satisfy the client (`prompt` -> `command`).
*   However, when sending the *conversation history* back to Gemini for the next turn, the proxy sent the *modified* history (`command`).
*   Gemini, having originally generated `prompt`, did not recognize the `command`-based tool call in its history as its own valid action. It likely treated it as a "failed" or "foreign" tool call and attempted to regenerate the action, leading to an infinite loop.

**Resolution (Request Path):**
*   Implemented **Reverse-Rename** in `request_converter.py`.
*   **Logic:** When reconstructing the `assistant` message for the history array, if the tool is `Bash` and the argument is `command`, rename it *back* to `prompt`.
*   **Effect:** Gemini sees a history that is consistent with its own training/output (`prompt`), accepts the tool result, and proceeds to the next step.

## 3. Comparative Architecture
Research into similar projects (`litellm`, `gemini-openai-proxy`) confirms these findings are consistent with the state of the art in LLM interoperability.

| Feature | OpenAI / Claude Protocol | Gemini Protocol | Proxy Intervention |
| :--- | :--- | :--- | :--- |
| **Tool Args** | Strict Schema (`command`) | Flexible/Hallucinated (`prompt`) | **Bi-Directional Normalization** |
| **Streaming** | `delta` objects | `candidates` chunks | **Stream Buffering / String Patching** |
| **History** | `tool_use` + `tool_result` | `function_call` + `function_response` | **Role Mapping & ID Preservation** |

## 4. Recommendations
1.  **Maintain the Mappings**: The `.env` mapping to `gemini-3-flash` is critical for stability until license issues are resolved.
2.  **Monitor Stream Patching**: The regex/string replacement for streaming is fragile. If Gemini changes its output format (e.g., adds whitespace), this regex might fail. A proper streaming JSON parser (like `json-repair`) is the long-term fix.
3.  **Temperature Control**: Forcing `temperature=0` for the router model (Small) significantly reduces the likelihood of schema hallucinations.

## 5. Conclusion
The "Superpowers" failure was a symptom of a brittle bridge between two highly opinionated systems. By implementing a symmetrical translation layer—normalizing downstream for the client and denormalizing upstream for the model—we have established a stable protocol tunnel that allows Claude Code to operate on Google's infrastructure.
