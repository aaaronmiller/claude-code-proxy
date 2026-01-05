# Case Study: Cascading Failure Resolution in AI Proxy Architectures
## Interfacing Claude Code CLI with Google Antigravity via VibeProxy

**Date:** December 24, 2025
**Subject:** Debugging and Rectification of "Superpowers" Tool Call Loops and Protocol Mismatches
**System:** Claude Code CLI → Custom Proxy (Python) → VibeProxy (Localhost) → Google Antigravity API

---

### Abstract

This paper documents the diagnostic process and resolution of a complex, multi-layered failure in a custom AI proxy infrastructure designed to interface Anthropic's Claude Code CLI with Google's internal "Antigravity" (Gemini) models. The system exhibited persistent 500 Internal Server Errors, authentication failures, and endless retry loops during tool execution (specifically involving the "superpowers" skill). The root cause was identified as a protocol mismatch in model identification, exacerbated by a secondary logging crash, stream integrity issues ("ghost calls"), and artificial context limitations. This study details the fault progression and the engineering interventions required to restore stability.

### 1. Introduction

The objective was to enable the **Claude Code CLI** (a terminal-based AI coding agent) to utilize **Anthropic Opus 4.5** models provided by Google via its Antigravity IDE during the initial product release period (December 2925), during which token limits were virtually unlimited. The prohibitive price and restrictive token limits on this model via the default Anthropic configuration for users under the $20 "pro" plan made this a very attractive opportunity to users if it could be made functional. However various bugs in the routing software used to enable this needed to be resolved related to the specific differences in how Anthropic and Google process tool calls respectively. Since Claude Code is hardcoded to expect Anthropic models (Sonnet, Haiku, Opus), a middleware layer was required to:
1.  Intercept requests from Claude Code.
2.  Translate model names and protocols.
3.  Forward requests to **VibeProxy**, a local service wrapping Google's internal "Antigravity" API, utiizing code from **CLIProxyAPI**.

The system failed catastrophically when Claude Code attempted to execute tools (e.g., `Bash`, `Task`), entering a loop where an enabled skill, **superpowers**, was repeatedly reloaded without successful execution - related to an addtional configuration setting due to token output limit discrepancies between thosse permitted by Anthropic (128k) and Google(1m).

### 2. Diagnostic Methodology

Forensic analysis of the `debug_traffic.log` and codebase revealed a "snowballing" failure chain:

*   **Symptom 1:** `500 Internal Server Error` returned to the client.
*   **Symptom 2:** `auth_unavailable: no auth available` logged by the proxy.
*   **Symptom 3:** `ModuleNotFoundError: src.utils.model_limits` in the traceback.
*   **Symptom 4:** Massive payloads (~170KB) observed during retries.

### 3. Fault Analysis: The "Perfect Storm"

The failure was not a single bug but a dependency chain of four distinct faults:

#### 3.1. Primary Fault: Protocol Mismatch (The Trigger)
Claude Code uses a specific model, `claude-haiku-4-5-20251001`, for fast tool execution/orchestration.
*   **The Bug:** The middleware forwarded this model ID directly to VibeProxy.
*   **The Failure:** VibeProxy (Antigravity wrapper) operates on a strictly allowlisted set of model IDs (e.g., `gemini-3-flash`, `gemini-claude-sonnet-4-5`). It did not recognize `claude-haiku...` and rejected the request with `auth_unavailable` (interpreting the invalid ID as a permission scope error).

#### 3.2. Secondary Fault: Infrastructure Crash (The Mask)
When the proxy attempted to log the failure (or any completed request), it triggered a fatal crash.
*   **The Bug:** `src/services/logging/request_logger.py` attempted to import `get_model_limits` from a non-existent path `src.utils.model_limits`.
*   **The Failure:** This raised an unhandled `ModuleNotFoundError`, causing the proxy to return HTTP 500 to the client, effectively masking the upstream "auth" error and preventing graceful error handling.

#### 3.3. Tertiary Fault: Stream Integrity ("Ghost Streams")
Upon fixing the crash, a race condition in the VibeProxy/Gemini streaming protocol emerged.
*   **The Bug:** The upstream provider occasionally emitted duplicate Server-Sent Events (SSE) for the same tool call—one containing the ID and another containing arguments but no ID ("ghost stream").
*   **The Failure:** The proxy interleaved these streams, sending conflicting data to Claude Code. The CLI interpreted this as "two different model outputs" for a single session, failed to parse the JSON, and initiated a retry.

#### 3.4. Quaternary Fault: Artificial Capacity Limits
*   **The Bug:** The proxy's `model_limits.py` enforced a default context window of 128k tokens for unrecognized models.
*   **The Failure:** The "superpowers" system prompt injection involved massive context (~170KB+). While Gemini supports 1M+ tokens, the proxy risked truncating or rejecting these requests before they even reached the upstream provider.

### 4. Resolution & Implementation

A four-phase rectification plan was executed:

#### Phase 1: Dynamic Protocol Translation (Fixing Auth)
We modified `src/services/models/provider_detector.py` to implement **dynamic model mapping**:
*   **Logic:** Intercept any model name containing "haiku".
*   **Routing:** Check the `SMALL_MODEL` environment variable.
    *   If set to a valid VibeProxy ID (e.g., `gemini-3-flash`), use it.
    *   **Fallback:** If unset or invalid, hard-map to `gemini-3-flash`.
*   **Result:** VibeProxy now receives a valid, authorized model ID for all tool-use requests.

#### Phase 2: Dependency Repair (Fixing 500s)
We corrected the import path in `src/services/logging/request_logger.py`:
*   **Change:** `from src.utils.model_limits` → `from src.services.usage.model_limits`.
*   **Result:** Logging now succeeds, allowing the proxy to run without crashing on completion.

#### Phase 3: Stream Deduplication (Fixing Ghost Calls)
We patched `src/services/conversion/response_converter.py` with robust filtering:
*   **Mechanism:** Tracking active tool call IDs and their primary stream indices.
*   **Logic:** `if active_tool_ids[id]["primary_index"] != current_index: ignore_ghost_stream()`.
*   **Result:** Only a single, coherent stream is forwarded to the client, preventing parse errors.

#### Phase 4: Capacity Expansion
We updated `src/services/usage/model_limits.py`:
*   **Change:** Explicitly defined `gemini-3-flash` and `gemini-3-pro` with a **1,000,000 token** context window.
*   **Result:** The proxy no longer throttles the "superpowers" context injection.

### 5. Conclusion

The "looping" behavior was a classic symptom of a **retry storm** caused by downstream protocol rejections (`auth_unavailable`) and middleware crashes (`ModuleNotFoundError`). By aligning the model identification protocol with the upstream VibeProxy requirements and hardening the stream processing logic, we restored full functionality. Claude Code can now transparently utilize Google's Gemini 3 infrastructure for high-context, tool-heavy development tasks.
