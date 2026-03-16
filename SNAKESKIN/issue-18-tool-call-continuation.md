# Issue 18: Tool Call Continuation - Sessions Stop After Each Tool Use

**Date:** March 16, 2026  
**Severity:** High - Blocks autonomous multi-turn tool execution

## Symptom

Claude Code sessions stop after each tool use execution, requiring manual intervention to continue:
1. User asks model to perform a task
2. Model makes ONE tool call
3. Tool executes successfully
4. Session stops - model doesn't continue autonomously
5. User must instruct "continue working"
6. Model makes ONE more tool call, then stops again

This breaks the autonomous flow that Claude Code is designed for.

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

**Original Fix Attempt:** The reverse normalization was disabled because it caused `InputValidationError` - but this was likely due to applying the transformation at the wrong layer or to the wrong messages.

### 2. Tool Result Message Validation

**Location:** `src/services/conversion/request_converter.py` (lines 90-120)

**Problem:** The `validate_tool_message_sequence()` function may be too strict, removing or skipping tool results that don't have perfect ID matches.

**Impact:** If tool results are removed or skipped, the model doesn't see the execution results and can't continue.

### 3. Missing "Continue" Signal in Response

**Location:** `src/services/conversion/response_converter.py`

**Problem:** After tool calls complete, the response may not include proper continuation signals that tell Claude Code the model is ready for more turns.

## Solution

### Fix 1: Smart Reverse Normalization

**File:** `src/services/conversion/request_converter.py`

**Change:** Apply reverse normalization ONLY to messages being sent to Gemini, NOT to messages being sent to Claude Code CLI.

```python
def convert_claude_assistant_message(msg: ClaudeMessage, target_provider: str = None) -> Dict[str, Any]:
    # ... existing code ...
    
    if should_reverse_rename and tool_name.lower() in ["bash", "repl"] and isinstance(arguments, dict):
        # CRITICAL FIX: Only apply when sending to Gemini, not when sending to Claude Code
        # Check if this is a HISTORY message (being sent back to provider)
        # vs a LIVE message (being sent to CLI)
        if target_provider and target_provider.lower() in ['vibeproxy', 'gemini', 'antigravity', 'google']:
            # This is being sent TO Gemini - use 'prompt'
            arguments = arguments.copy()
            if "command" in arguments and "prompt" not in arguments:
                arguments["prompt"] = arguments.pop("command")
                logger.debug(f"Reverse renamed Bash 'command' → 'prompt' for {target_provider}")
```

**Key Insight:** The transformation must be applied based on the TARGET of the message:
- Claude Code CLI → expects `command`
- Gemini API → expects `prompt`

### Fix 2: Relaxed Tool Result Validation

**File:** `src/services/conversion/request_converter.py`

**Change:** Make tool result validation more lenient - log warnings but don't remove tool results.

```python
def validate_tool_message_sequence(messages: List[Dict[str, Any]], remove_orphans: bool = False) -> List[Dict[str, Any]]:
    # ... existing code ...
    
    # Instead of removing orphans, just add a warning and keep them
    # The model can handle some inconsistency better than missing data
    if not found_match:
        orphan_count += 1
        logger.warning(f"Tool result {tool_call_id} has no matching tool_call in history")
        # DON'T remove - keep the message anyway
        validated.append(msg)
```

### Fix 3: Add Continuation Hint

**File:** `src/services/conversion/response_converter.py`

**Change:** After tool calls complete, ensure the response includes proper signals.

```python
# After processing tool calls, add implicit continuation hint
if finish_reason in ["tool_calls", "function_call"]:
    # Model has called tools - ensure Claude Code knows to execute and continue
    final_stop_reason = Constants.STOP_TOOL_USE
    # No additional hint needed - Claude Code will automatically continue
    # after receiving tool results
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

- `src/services/conversion/request_converter.py` - Smart reverse normalization
- `src/services/conversion/request_converter.py` - Relaxed tool validation
- `src/services/conversion/response_converter.py` - Continuation signals

## Related Issues

- **Issue 14:** Overly Aggressive Tool Call Deduplication
- **Cascading Failure Phase 5:** Parameter Schema (Streaming Failures)
- **Tool Call Resolution:** History Amnesia problem

## Verification

After fix, check logs for:
1. ✅ "Reverse renamed Bash 'command' → 'prompt'" when sending to Gemini
2. ✅ No "Skipping duplicate tool_result" messages for unique tool calls
3. ✅ Continuous conversation flow in Claude Code without manual prompts

---

*This document should be updated once the fix is verified in production.*
