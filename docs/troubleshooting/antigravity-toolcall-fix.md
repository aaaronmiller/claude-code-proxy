# Case Study: Cascading Failure Resolution in AI Proxy Architectures
## Interfacing Claude Code CLI with Google Antigravity via VibeProxy

**Date:** December 24, 2025
**Subject:** Debugging and Rectification of "Superpowers" Tool Call Loops and Protocol Mismatches
**System:** Claude Code CLI → Custom Proxy (Python) → VibeProxy (Localhost) → Google Antigravity API

---

### Abstract

This paper documents the diagnostic process and resolution of a complex, multi-layered failure in a custom AI proxy infrastructure designed to interface Anthropic's Claude Code CLI with Google's internal "Antigravity" (Gemini) models. The system exhibited persistent 500 Internal Server Errors, authentication failures, and endless retry loops during tool execution (specifically involving the "superpowers" skill). The root cause was identified as a protocol mismatch in model identification, exacerbated by a secondary logging crash, stream integrity issues ("ghost calls"), artificial context limitations, and streaming parameter transformation defects. This study details the fault progression and the engineering interventions required to restore stability across five distinct failure modes.

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

The failure was not a single bug but a dependency chain of five distinct faults:

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

#### 3.5. Quinary Fault: Streaming Parameter Transformation Defect
Following the aforementioned repairs, an additional failure mode was discovered during production use: **Bash tool execution failures in streaming mode**.
*   **The Bug:** Streaming functions in `src/services/conversion/response_converter.py` performed on-the-fly JSON string replacement to transform Gemini's `"prompt"` parameter to Claude's `"command"` parameter, but this transformation was incomplete. While the non-streaming path correctly applied the centralized `normalize_tool_arguments()` function, streaming functions only applied partial string replacement on JSON deltas without complete semantic transformation.
*   **The Failure:** Claude Code CLI rejected Bash toolcalls in streaming mode with validation error: `"Invalid value for 'command': Expected a string or array, got undefined"`. Non-streaming requests succeeded, revealing an asymmetry in parameter normalization logic.

### 4. Resolution & Implementation

A five-phase rectification plan was executed:

#### Phase 1: Dynamic Protocol Translation (Fixing Auth)
We modified `src/services/models/provider_detector.py` to implement **dynamic model mapping**:
*   **Logic:** Intercept any model name containing "haiku".
*   **Routing:** Check the `SMALL_MODEL` environment variable.
    *   If set to a valid VibeProxy ID (e.g., `gemini-3-flash`), use it.
    *   **Fallback:** If unset or invalid, hard-map to `gemini-3-flash`.
*   **Result:** VibeProxy now receives a valid, authorized model ID for all tool-use requests.

```python
# provider_detector.py - Model name mapping
def get_backend_model(incoming_model: str) -> str:
    model_lower = incoming_model.lower()
    
    # Haiku → SMALL_MODEL (fast tool orchestration)
    if "haiku" in model_lower:
        return os.getenv("SMALL_MODEL", "gemini-3-flash")
    
    # Sonnet → MIDDLE_MODEL
    if "sonnet" in model_lower:
        return os.getenv("MIDDLE_MODEL", "gemini-3-pro")
    
    # Opus → BIG_MODEL
    if "opus" in model_lower:
        return os.getenv("BIG_MODEL", "gemini-claude-opus-4-5-thinking")
    
    return incoming_model  # Pass through unknown models
```

#### Phase 2: Dependency Repair (Fixing 500s)
We corrected the import path in `src/services/logging/request_logger.py`:
*   **Change:** `from src.utils.model_limits` → `from src.services.usage.model_limits`.
*   **Result:** Logging now succeeds, allowing the proxy to run without crashing on completion.

```python
# request_logger.py - Fixed import path
# BEFORE (broken):
# from src.utils.model_limits import get_model_limits

# AFTER (fixed):
from src.services.usage.model_limits import get_model_limits
```

#### Phase 3: Stream Deduplication (Fixing Ghost Calls)
We patched `src/services/conversion/response_converter.py` with robust filtering:
*   **Mechanism:** Tracking active tool call IDs and their primary stream indices.
*   **Logic:** `if active_tool_ids[id]["primary_index"] != current_index: ignore_ghost_stream()`.
*   **Result:** Only a single, coherent stream is forwarded to the client, preventing parse errors.

```python
# response_converter.py - Ghost stream filtering
active_tool_ids = {}  # Map: tc_id -> {primary_index, claude_index}

for tc_delta in delta["tool_calls"]:
    tc_id = tc_delta.get("id")
    tc_index = tc_delta.get("index", 0)
    
    if tc_id in active_tool_ids:
        # Known ID - check if this is a ghost stream (different index)
        if active_tool_ids[tc_id]["primary_index"] != tc_index:
            logger.debug(f"Ignoring ghost stream for ID {tc_id}")
            continue  # Skip duplicate stream
    else:
        # New unique ID - register it
        active_tool_ids[tc_id] = {
            "primary_index": tc_index,
            "claude_index": current_block_index
        }
```

#### Phase 4: Capacity Expansion
We updated `src/services/usage/model_limits.py`:
*   **Change:** Explicitly defined `gemini-3-flash` and `gemini-3-pro` with a **1,000,000 token** context window.
*   **Result:** The proxy no longer throttles the "superpowers" context injection.

```python
# model_limits.py - Gemini capacity definitions
MODEL_LIMITS = {
    # Gemini models with 1M+ context
    "gemini-3-flash": {"context_window": 1_000_000, "max_output": 8192},
    "gemini-3-pro": {"context_window": 1_000_000, "max_output": 8192},
    "gemini-3-pro-preview": {"context_window": 1_000_000, "max_output": 8192},
    
    # Thinking models (default limits for unrecognized)
    "gemini-claude-opus-4-5-thinking": {"context_window": 128_000, "max_output": 4096},
}

def get_model_limits(model_name: str) -> dict:
    return MODEL_LIMITS.get(model_name, {"context_window": 128_000, "max_output": 4096})
```

#### Phase 5: Dual-Layer Parameter Normalization (Fixing Bash Tool Streaming)
Following the aforementioned repairs, Bash tool execution failures in streaming mode revealed the fifth fault.

**Root Cause:** Forensic investigation of [`src/services/conversion/response_converter.py`](src/services/conversion/response_converter.py:1) revealed an asymmetry in parameter transformation:
*   **Non-Streaming Path:** Correctly applied `normalize_tool_arguments()` function to transform Gemini's `"prompt"` parameter to Claude's `"command"` parameter.
*   **Streaming Path:** Only performed partial JSON string replacement on streaming deltas without complete semantic transformation.

**The Engineering Solution:** Implemented a two-tier transformation strategy:

*   **Tier 1 - Streaming JSON Transformation (Real-time):** Preserved existing string replacement for immediate streaming compatibility:
```python
# Lines 309-312, 564-567
transformed_partial = partial_args
if tool_call["name"].lower() in ["bash", "repl"]:
    transformed_partial = transformed_partial.replace('"prompt":', '"command":')
```

*   **Tier 2 - Centralized Normalization Function (Systemic):** Created `normalize_tool_arguments()` (lines 8-74) to handle:
    *   **Bash/Repl tools:** `"prompt"` → `"command"` transformation
    *   **Task tools:** Bidirectional mapping between `"prompt"` and `"description"`; default `"subagent_type": "Explore"`
    *   **Read tools:** `"path"` → `"file_path"` transformation
    *   **Glob/Grep tools:** Multiple parameter name variants normalized to expected schema
    *   **TodoWrite tools:** `"tasks"` → `"todos"` transformation with status enumeration validation

**Result:** Bash toolcalls execute successfully in both streaming and non-streaming modes.

**Architectural Implication:** This fault underscores a common pitfall in streaming protocol implementations—the assumption that real-time transformations are sufficient for end-to-end compatibility. The dual nature of Server-Sent Events processing requires both streaming-time transformations (for client display) and accumulated-buffer normalization (for final validation).

---

## Phase 6: Content-Based Duplicate Tool Call Filtering (December 2025)

**Symptom:** Claude Code CLI displays duplicate tool outputs:
```
⏺ Bash(ls -la)
  ⎿  PreToolUse:Bash hook succeeded:
  ⎿  PreToolUse:Bash hook succeeded:   ← DUPLICATE
  ⎿     rwxr-xr-x...
  ⎿  PreToolUse:Bash hook succeeded:   ← THIRD HOOK
  ⎿     rwxr-xr-x...                   ← DUPLICATE OUTPUT
```

**Root Cause Discovery:** This is a **NEW Gemini API behavior** distinct from Phase 3 "Ghost Streams":

| Phase 3: Ghost Streams | Phase 6: Duplicate Operations |
|------------------------|-------------------------------|
| Same `tc_id`, different `tc_index` | **Different `tc_id`**, same operation |
| ID-based filtering sufficient | Content-based fingerprinting required |

Gemini's OpenAI compatibility layer occasionally emits the **same tool call twice with unique IDs**:
```
tool_call_1: id="call_abc", name="Bash", args='{"command":"ls -la"}'  
tool_call_2: id="call_xyz", name="Bash", args='{"command":"ls -la"}'  ← DUPLICATE
```

**Why Phase 3 Fix Didn't Catch This:** The ghost stream filter checks if `tc_id in active_tool_ids`. Since each duplicate has a **unique ID**, both pass through as "new" blocks.

**The Engineering Solution:** Content-based fingerprint deduplication in [`response_converter.py`](src/services/conversion/response_converter.py):

1. **Fingerprint Generation:** `f"{tool_name}:{first_args[:50]}"` creates unique signature per operation
2. **Early Detection:** Check fingerprint **BEFORE** registering block (critical timing fix)
3. **Skip Tracking:** `skipped_tool_ids` set prevents processing future chunks for duplicate IDs

```python
# Lines 539-563: Early fingerprint check
if tool_name:
    fingerprint = f"{tool_name}:{first_args[:50]}"
    if fingerprint in content_fingerprints:
        logger.info(f"DEDUP: Blocking duplicate tool call '{tool_name}' (id={tc_id})")
        skipped_tool_ids.add(tc_id)
        continue
    content_fingerprints[fingerprint] = tc_id

# Lines 518-520: Early skip for marked duplicates
if tc_id and tc_id in skipped_tool_ids:
    continue
```

**Result:** Only one tool call per unique operation is forwarded to Claude Code CLI.

---

### 6. Conclusion

The complete cascade resolution now covers **six distinct faults**:

| Phase | Fault | Solution |
|-------|-------|----------|
| 1 | Protocol Mismatch | Token refresh per request |
| 2 | Infrastructure Crash | `ModelLimits` import guard |
| 3 | Ghost Streams | ID-based stream deduplication |
| 4 | Capacity Limits | Dynamic context sizing |
| 5 | Parameter Schema | Dual-tier streaming transformation |
| 6 | Duplicate Operations | Content-based fingerprinting |

Claude Code can now transparently utilize Google's Gemini 3 infrastructure with complete tool execution support, handling both streaming protocol edge cases and Gemini API behavioral quirks.
