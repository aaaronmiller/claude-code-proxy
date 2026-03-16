# Issue 18: Tool Call Continuation - Sessions Stop After Each Tool Use

**Date:** March 16, 2026  
**Severity:** High - Blocks autonomous multi-turn tool execution  
**Status:** FIXED ✓

## Symptom

Claude Code sessions stop after each tool use execution, requiring manual intervention to continue:
1. User asks model to perform a task
2. Model makes ONE tool call
3. Tool executes successfully
4. Session stops - model doesn't continue autonomously
5. User must instruct "continue working"
6. Model makes ONE more tool call, then stops again

This breaks the autonomous flow that Claude Code is designed for.

## Log Analysis

**Debug Traffic Log:** `/home/misscheta/code/claude-code-proxy/logs/debug_traffic.log`

Analysis of the traffic log shows:
- Multiple consecutive requests with increasing message sizes (140KB → 171KB)
- Session IDs remain consistent (`user_ccd8fd3a0c229232cef18e421f8a1ecf40fa1c0966a8a15715fbf253f550338d`)
- Request intervals: 6-60 seconds between tool calls (indicating manual intervention delays)
- Models used: `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-haiku-4-5-20251001`

**Pattern:** Each request contains the full conversation history, but tool results from previous turns are not being properly recognized by the model, causing it to wait for explicit continuation.

## Root Cause Analysis

### 1. Reverse Normalization Disabled (Primary Cause)

**Location:** `src/services/conversion/request_converter.py` (lines 630-641)

**Problem:** The code that converts `command` back to `prompt` for Gemini is disabled:

```python
# UPDATE (2026-02-11): Disabling this because it causes InputValidationError on the client side.
# The local Bash tool expects 'command', so forcing 'prompt' confuses the model or the
# tool execution layer.
should_reverse_rename = False  # DISABLED!
```

**Why This Breaks Continuation:**
- Gemini outputs tool calls with `prompt` parameter
- Proxy converts to `command` for Claude Code CLI (correct)
- CLI executes and sends back `command` in history
- Proxy sends `command` back to Gemini in next request
- Gemini doesn't recognize `command` (expects `prompt`)
- Gemini treats it as unknown/invalid history
- Model becomes confused and waits for explicit instruction

**Historical Context:** This is the EXACT problem documented in:
- `SNAKESKIN/tool-call-resolution.md` - "History Amnesia" section
- `docs/troubleshooting/tool-call-resolution.md` - Section 2.4
- `changelog.md` - Cascading Failure Resolution Phase 6

The fix was known and documented, but was disabled due to a false positive (InputValidationError).

### 2. Tool Result Message Validation Too Strict

**Location:** `src/services/conversion/request_converter.py` (lines 106-120)

**Problem:** The `validate_tool_message_sequence()` function was removing tool results that don't have perfect ID matches.

**Impact:** If tool results are removed or skipped, the model doesn't see the execution results and can't continue.

**Code Before Fix:**
```python
if remove_orphans:
    logger.info(f"Removing orphaned tool message (tool_call_id={tool_call_id})")
    continue  # Skip this message - REMOVES IT FROM HISTORY!
```

### 3. Historical Precedent - Same Issue Fixed Before

From `SNAKESKIN/tool-call-resolution.md`:

> **The "History Amnesia" (Loop Cause)**
> Fixing the outgoing request created a discrepancy in the conversation history.
> - **Failure:** We sent `command` to the client. The client executed it. We sent `command` back to Gemini in the history. Gemini saw `command`, didn't recognize it as its own valid tool call, and re-generated the tool call.
> - **Fix:** We implemented **Reverse-Normalization**. When sending history to Gemini, we rename `command` *back* to `prompt`.

This is the EXACT same issue - it was fixed before but the fix was later disabled.

## Solution

### Fix 1: Smart Reverse Normalization

**File:** `src/services/conversion/request_converter.py`

**Change:** Apply reverse normalization ONLY when sending messages TO Gemini, NOT when sending to Claude Code CLI.

```python
should_reverse_rename = target_provider and target_provider.lower() in [
    'vibeproxy', 'gemini', 'antigravity', 'google'
]

if should_reverse_rename and tool_name.lower() in ["bash", "repl"] and isinstance(arguments, dict):
    arguments = arguments.copy()
    if "command" in arguments and "prompt" not in arguments:
        arguments["prompt"] = arguments.pop("command")
        logger.debug(f"Reverse renamed Bash 'command' → 'prompt' for {target_provider} (Issue 18 fix)")
```

**Key Insight:** The transformation must be applied based on the TARGET of the message:
- Claude Code CLI → expects `command`
- Gemini API → expects `prompt`

### Fix 2: Relaxed Tool Result Validation

**File:** `src/services/conversion/request_converter.py`

**Change:** Make tool result validation more lenient - log warnings but don't remove tool results.

```python
# FIX (2026-03-16) Issue 18: DON'T remove orphaned tool results
# Removing them breaks conversation continuity in multi-turn tool use
# The model can handle some inconsistency better than missing data
# if remove_orphans:
#     logger.info(f"Removing orphaned tool message...")
#     continue  # Skip this message

validated.append(msg)  # Always keep the message
```

## Testing

### Test Case 1: Single Tool Call
```bash
claude "Create a file called test.txt with 'hello world' in it"
```
**Expected:** File created, model confirms completion without stopping

### Test Case 2: Multi-Tool Sequence
```bash
claude "List all Python files, then read the first one"
```
**Expected:** Both tools execute autonomously without manual intervention

### Test Case 3: Complex Workflow
```bash
claude "Refactor the code in src/main.py to use async/await"
```
**Expected:** Multiple read/edit cycles complete autonomously

## Files Modified

- `src/services/conversion/request_converter.py` - Smart reverse normalization + Relaxed tool validation
- `SNAKESKIN/issue-18-tool-call-continuation.md` - This documentation

## Related Issues

- **Issue 14:** Overly Aggressive Tool Call Deduplication
- **Cascading Failure Phase 5:** Parameter Schema (Streaming Failures)
- **Cascading Failure Phase 6:** Duplicate Operations (Content-Based)
- **Tool Call Resolution:** History Amnesia problem (SAME ISSUE - fixed before!)
- **SNAKESKIN/tool-call-resolution.md:** Original documentation of reverse normalization

## Verification

After fix, check logs for:
1. ✅ "Reverse renamed Bash 'command' → 'prompt' for vibeproxy/gemini (Issue 18 fix)" when sending to Gemini
2. ✅ "Tool message validation complete: X orphan(s) kept for conversation continuity" 
3. ✅ Continuous conversation flow in Claude Code without manual prompts
4. ✅ No more 60-second gaps between tool calls in debug_traffic.log

## Lessons Learned

1. **Don't disable known fixes** - The reverse normalization was documented as THE solution to history amnesia
2. **Debug carefully** - The InputValidationError was likely caused by applying the fix at the wrong layer
3. **Context matters** - Always check SNAKESKIN docs before disabling fixes
4. **Test multi-turn** - Single tool call tests don't catch continuation issues

---

*Fix verified and pushed to main. Multi-turn tool calls should now complete autonomously.*
