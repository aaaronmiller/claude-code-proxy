# Claude Code Proxy Session Findings
**Date:** 2025-12-29
**Session Focus:** Multi-provider test runner + 4KB truncation issue analysis

---

## 1. Tests Created

### 1.1 Direct Proxy Test (`tests/integration/direct_proxy_test.py`)

**Purpose:** Test proxy without Claude Code overhead, with rotating providers.

**Provider Configurations:**
```python
PROVIDER_CONFIGS = {
    "vibeproxy-gemini-claude-sonnet-thinking": {
        "big": "gemini-claude-sonnet-4-5-thinking",
        "small": "gemini-3-flash",
        "timeout": 15,
        "base_url": "http://127.0.0.1:8082",
        "api_key": "pass",
    },
    "vibeproxy-gemini-claude-opus-thinking": {
        "big": "gemini-claude-opus-4-5-thinking",
        "small": "gemini-3-flash",
        "timeout": 20,
    },
    "vibeproxy-gemini-claude-sonnet": {
        "big": "gemini-claude-sonnet-4-5",
        "small": "gemini-3-flash",
        "timeout": 15,
    },
    "vibeproxy-gemini-flash": {
        "big": "gemini-3-flash",
        "small": "gemini-3-flash",
        "timeout": 15,
    },
    "vibeproxy-gemini-pro": {
        "big": "gemini-3-pro-preview",
        "small": "gemini-3-flash",
        "timeout": 15,
    },
    "openrouter-oss120": {
        "big": "openai/gpt-oss-120b:free",
        "small": "openai/gpt-oss-120b:free",
        "timeout": 30,
        "base_url": "https://openrouter.ai/api/v1",
        "skip_reason": "Requires OpenRouter privacy settings",
    },
    "hybrid-sonnet-flash": {
        "big": "gemini-claude-sonnet-4-5-thinking",
        "small": "gemini-3-flash",
        "timeout": 15,
    },
}
```

**Test Functions:**
- `test_simple_request()` - Basic API request
- `test_tool_use()` - Single tool call
- `test_multi_turn_tool_use()` - Full tool cycle (request → tool_use → tool_result → response)
- `test_bash_tool_use()` - 3-step Bash tool cycle with loop detection
- `test_poem_file_creation()` - Write tool simulation

**Results (All VibeProxy providers):**
```
SUMMARY: 25/25 passed
  PASS: vibeproxy-gemini-claude-sonnet-thinking/Simple
  PASS: vibeproxy-gemini-claude-sonnet-thinking/ToolUse
  PASS: vibeproxy-gemini-claude-sonnet-thinking/MultiTurn
  PASS: vibeproxy-gemini-claude-sonnet-thinking/Bash
  ... (all 6 providers × 4 tests = 24 tests + DB logging = 25)
```

**OpenRouter Issue:**
- Error: "No endpoints found matching your data policy (Free model publication)"
- Fix: Configure privacy at https://openrouter.ai/settings/privacy

### 1.2 Quick Headless Test (`tests/integration/quick_headless_test.py`)

**Purpose:** Simple headless Claude Code test with minimal overhead.

**Key Feature - CLAUDE.md Override:**
```python
# Create empty CLAUDE.md to override global one
(claude_dir / "CLAUDE.md").write_text("# Minimal test config\nNo skills or complex instructions.")
```

This is why tests PASSED while real usage FAILED - tests use a tiny CLAUDE.md (~50 bytes).

---

## 2. 4KB Truncation Issue - CONFIRMED

### 2.1 Evidence

**User's CLAUDE.md Analysis:**
| Metric | Value |
|--------|-------|
| File size | 6,107 bytes |
| First "superpowers" mention | byte 4,178 |
| 4KB boundary | byte 4,096 |
| **Overflow** | **82 bytes past 4KB** |

**Observed Behavior:**
1. Claude Code + Antigravity + gemini-claude models
2. Model gets stuck in "Thinking about superpowers" loop
3. Never executes the actual simple task
4. Repetitive skill invocation reasoning

### 2.2 Root Cause

The Gemini-Anthropic conversion endpoint likely has a **~4KB system prompt limit**. When exceeded:
1. System prompt truncated mid-instruction
2. Model sees "superpowers" mentioned but instructions incomplete
3. Gets stuck trying to invoke incomplete skill definitions
4. Never reaches task execution

### 2.3 Supporting Research

**YouTube (Softreviewed, Dec 2025):**
> "Agent terminated due to another error" happens when "too many MCP tools are enabled"
> Fix: Disable all MCPs, refresh, test again

**Self-Service BI Blog:**
> "MCP tools alone consume 16.3% of context window before conversation starts"
> "CLAUDE.md should be under 5,000 tokens"

**GitHub Issues:**
- #2638: MCP responses truncated to ~700 chars (Node.js maxBuffer)
- #14490: `--strict-mcp-config` doesn't override disabledMcpServers
- #3524, #7718: MCP crashes during long tasks

---

## 3. MCP Server Configuration Findings

### 3.1 Where MCP Servers Are Defined

**Active MCP Servers (from `claude mcp list`):**
```
context7: /opt/homebrew/bin/npx -y @upstash/context7-mcp
sentry: /opt/homebrew/bin/uvx mcp-server-sentry
playwright: /opt/homebrew/bin/npx -y @playwright/mcp@latest
mem0-memory-mcp: /opt/homebrew/bin/uvx mem0-mcp-server
chrome-devtools-mcp: /opt/homebrew/bin/npx -y chrome-devtools-mcp@latest
exa: /opt/homebrew/bin/npx -y exa-mcp-server
brightdata-mcp: /opt/homebrew/bin/npx -y @brightdata/mcp
sequential-thinking: /opt/homebrew/bin/npx -y @modelcontextprotocol/server-sequential-thinking
```

### 3.2 Settings That DON'T Fully Disable MCP

In `~/.claude/settings.json`:
```json
{
  "enableAllProjectMcpServers": false,
  "disabledMcpjsonServers": ["*"],
  "autoAllowMcpTools": true
}
```

**Problem:** These settings only affect project-level `.mcp.json` files, NOT globally installed MCP servers.

### 3.3 Current Workaround

**Rename/remove the main MCP config:**
```bash
# The global MCP config location is unclear
# MCP servers seem to persist in Claude's internal state
# --strict-mcp-config flag has a bug (issue #14490)
```

**No definitive solution found** for completely disabling global MCP servers without modifying the installation.

---

## 4. Solutions Implemented

### 4.1 Trimmed CLAUDE.md

**Created:** `~/.claude/CLAUDE.md.slim` (1,696 bytes = 41% of 4KB limit)

```bash
# To use:
mv ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.full
cp ~/.claude/CLAUDE.md.slim ~/.claude/CLAUDE.md
```

**Content (condensed from 6KB original):**
- Removed verbose superpowers skill listings
- Kept core identity/stack/execution rules
- Compressed multi-line sections to single lines

### 4.2 Test Workspace Pattern

For isolated testing:
```bash
mkdir -p /tmp/claude-test/.claude
echo '{"mcpServers":{}}' > /tmp/claude-test/.claude/settings.local.json
echo '# Minimal' > /tmp/claude-test/.claude/CLAUDE.md
cd /tmp/claude-test && claude
```

---

## 5. Key Files Modified This Session

1. **`tests/integration/direct_proxy_test.py`**
   - Added multi-provider support
   - Added OpenAI format support for OpenRouter
   - Added `is_openai_format()` helper
   - Updated all test functions with `config` parameter

2. **`~/.claude/CLAUDE.md.slim`** (new)
   - Trimmed version under 4KB

3. **`~/.claude/CLAUDE.md.backup`** (new)
   - Backup of original

---

## 6. Proxy Chain Architecture

```
Claude Code (headless)
    ↓ Anthropic API format
claude-code-proxy (8082)
    ↓ Converts to OpenAI format
VibeProxy/Antigravity (8317)
    ↓ Routes to backend
Gemini API (gemini-claude-* models)
```

**API Key Flow:**
- Claude Code sends `ANTHROPIC_API_KEY=pass`
- Proxy detects provider from model name
- Proxy injects real API key based on provider

---

## 7. Outstanding Issues

### 7.1 No Way to Fully Disable Global MCP

- `disabledMcpjsonServers: ["*"]` only affects project `.mcp.json`
- `--strict-mcp-config` flag has bug (issue #14490)
- Global MCP servers persist in internal state

### 7.2 OpenRouter Free Tier Requires Privacy Settings

- Error: "No endpoints found matching your data policy"
- Fix: https://openrouter.ai/settings/privacy
- Enable "Allow free model publication"

### 7.3 4KB Truncation in Gemini-Anthropic Endpoint

- Confirmed via byte offset analysis
- "superpowers" at byte 4178 (82 past 4KB)
- Causes model confusion/loops
- Fix: Keep CLAUDE.md under 4KB

---

## 8. Commands Reference

```bash
# Run all provider tests
uv run python tests/integration/direct_proxy_test.py --all

# Run single provider test
uv run python tests/integration/direct_proxy_test.py -p vibeproxy-gemini-flash

# Check MCP servers
claude mcp list

# Start proxy with debug logging
DEBUG_TRAFFIC_LOG=true TRACK_USAGE=true uv run python start_proxy.py

# Check VibeProxy models
curl http://127.0.0.1:8317/v1/models | jq '.data[].id'
```

---

## 9. Next Steps for New Session

1. **Investigate MCP disabling** - Find where global MCP servers are stored
2. **Test with slim CLAUDE.md** - Verify 4KB theory fixes the issue
3. **Add OpenRouter tests** - After configuring privacy settings
4. **Consider proxy-level system prompt compression** - If endpoint limit is confirmed
