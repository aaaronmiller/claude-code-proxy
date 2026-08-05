---
date: 2025-02-19 14:30:00 PST
ver: 1.0.0
author: Sliither
model: claude-opus-4-6
tags: [anthropic, claude-code, orchestration, tool-calls, gemini, routing, multi-agent, antigravity, litellm, proxy]
---
# Anthropic Orchestration Tool Calls: Identification and Gemini Backend Routing

## Executive Summary

Anthropic has shipped two distinct layers of new orchestration primitives alongside the Opus 4.6 release:

1. **API-Level Advanced Tool Use** (beta: `advanced-tool-use-2025-11-20`) -- three new tool features for programmatic orchestration, deferred tool discovery, and usage examples
2. **Claude Code Agent Teams** (experimental: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) -- a native multi-agent coordination system using `TeammateTool` with 13 operations

Both layers present different challenges for Gemini backend routing. This document catalogs every new call signature and proposes an interception/translation architecture.

---

## Layer 1: API-Level Advanced Tool Use (Beta)

These are API message endpoint features activated via the `advanced-tool-use-2025-11-20` beta header.

### 1.1 Tool Search Tool (Deferred Discovery)

**Purpose:** Load tool definitions on-demand instead of upfront, reducing context consumption by ~85%.

**New API surface:**

```json
// Tool definition -- new field
{
  "name": "my_tool",
  "description": "...",
  "input_schema": {...},
  "defer_loading": true    // NEW FIELD -- tool excluded from initial context
}

// Built-in search tool types (pick one)
{"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"}
{"type": "tool_search_tool_bm25_20251119", "name": "tool_search_tool_bm25"}

// MCP toolset-level deferred loading
{
  "type": "mcp_toolset",
  "mcp_server_name": "google-drive",
  "default_config": {"defer_loading": true},
  "configs": {
    "search_files": {"defer_loading": false}  // keep critical tools loaded
  }
}
```

**Response blocks to intercept:**

```json
// Claude returns tool_reference blocks when searching
{
  "type": "tool_reference",
  "tool_name": "github.createPullRequest"
}
```

**Gemini routing impact:** Gemini has no equivalent to `defer_loading` or `tool_search_tool_*`. The proxy must maintain a local tool registry and handle search requests entirely within the routing layer, injecting matching tool definitions into subsequent Gemini requests.

### 1.2 Programmatic Tool Calling (PTC)

**Purpose:** Claude writes Python code that orchestrates multiple tool calls within a sandboxed Code Execution container. Intermediate results stay in the sandbox; only final output enters context.

**New API surface:**

```json
// Tool definition -- new field
{
  "name": "get_expenses",
  "input_schema": {...},
  "allowed_callers": ["code_execution_20250825"]  // NEW FIELD -- enables PTC
}

// Required companion tool
{
  "type": "code_execution_20250825",
  "name": "code_execution"
}
```

**New response block types:**

```json
// Claude emits server_tool_use for code execution
{
  "type": "server_tool_use",
  "id": "srvtoolu_abc123",
  "name": "code_execution",
  "input": {
    "code": "results = await get_expenses('emp_123', 'Q3')\n..."
  }
}

// Tool calls FROM code execution have a `caller` field
{
  "type": "tool_use",
  "id": "toolu_xyz789",
  "name": "get_expenses",
  "input": {"user_id": "emp_123", "quarter": "Q3"},
  "caller": {                                          // NEW FIELD
    "type": "code_execution_20250825",
    "tool_id": "srvtoolu_abc123"
  }
}

// Final result type
{
  "type": "code_execution_tool_result",
  "tool_use_id": "srvtoolu_abc123",
  "content": {
    "stdout": "[{\"name\": \"Alice\", \"spent\": 12500}]"
  }
}

// Container management (response-level)
{
  "container": {
    "id": "container_xyz789",
    "expires_at": "2025-01-15T14:30:00Z"
  }
}
```

**Gemini routing impact:** This is the hardest feature to route. Gemini 2.0+ has code execution, but the execution-within-tool-calling loop (where code calls tools mid-execution, pausing for results) is Anthropic-specific. The `caller` field and `server_tool_use` / `code_execution_tool_result` block types have no Gemini equivalents.

### 1.3 Tool Use Examples

**Purpose:** Provide concrete usage examples alongside JSON schemas for improved parameter accuracy (72% to 90% in internal testing).

**New API surface:**

```json
{
  "name": "create_ticket",
  "input_schema": {...},
  "input_examples": [                    // NEW FIELD
    {
      "title": "Login page returns 500",
      "priority": "critical",
      "labels": ["bug", "auth"]
    },
    {
      "title": "Add dark mode",
      "labels": ["feature-request"]
    }
  ]
}
```

**Gemini routing impact:** Gemini function calling does not support `input_examples`. The proxy should strip this field before forwarding, or inject example content into the tool description string as formatted text.

### 1.4 Context Management (Related)

**Beta:** `context-management-2025-06-27`

```json
// Automatic tool result clearing
{
  "type": "clear_tool_uses_20250919",
  "strategy": "auto"
}
```

**Gemini routing impact:** Gemini has its own context window management. Strip this field entirely.

---

## Layer 2: Claude Code Agent Teams (TeammateTool)

These operate at the Claude Code CLI level, not the raw API. They are activated by the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` feature flag (or environment variable).

### 2.1 TeammateTool Operations (13 Total)

| Operation | Direction | Parameters | Purpose |
|-----------|-----------|------------|---------|
| `spawnTeam` | Leader -> System | `name`, `description` | Create team, initialize directories |
| `discoverTeams` | Any -> System | (none) | List available teams |
| `requestJoin` | Agent -> Leader | `team_id`, `proposed_name` | Request team membership |
| `approveJoin` | Leader -> Agent | `agent_id` | Accept join request |
| `rejectJoin` | Leader -> Agent | `agent_id` | Deny join request |
| `spawn` | Leader -> System | `name`, `prompt`, `plan_mode_required?` | Create and start a teammate |
| `write` | Any -> Any | `agent_id`, `message` | Send targeted message |
| `broadcast` | Any -> All | `message` | Message all team members |
| `requestShutdown` | Leader -> Agent | `reason` | Initiate graceful shutdown |
| `approveShutdown` | Agent -> Leader | (none) | Confirm ready to exit |
| `rejectShutdown` | Agent -> Leader | `reason` | Refuse shutdown with explanation |
| `cleanup` | Leader -> System | `team_id` | Remove team directories and resources |
| `approvePlan` | Leader -> Agent | `agent_id`, `request_id` | Approve agent's plan |

### 2.2 Task System Operations

These pre-date Agent Teams but are integral to coordination:

| Operation | Parameters | Purpose |
|-----------|------------|---------|
| `TaskCreate` | `subject`, `description`, `blocks?`, `blockedBy?`, `team_name?` | Create a task |
| `TaskUpdate` | `taskId`, `status?`, `addBlockedBy?`, `removeBlockedBy?` | Update task state |
| `TaskList` | `team_name?` | List all tasks |
| `TaskGet` | `taskId` | Get task details |

### 2.3 Agent Spawn Backends

Controlled via `CLAUDE_CODE_SPAWN_BACKEND`:

| Value | Behavior |
|-------|----------|
| `tmux` | Visible tmux panes, persistent |
| `iterm2` | iTerm2 tabs via it2 CLI |
| `in-process` | Fastest, no visibility (headless) |
| (unset) | Auto-detect |

### 2.4 File System Structure

```
~/.claude/
  teams/{team-name}/
    config.json           # Team metadata, leader, members
    messages/{session-id}/ # Per-agent inbox (JSON files)
  tasks/{team-name}/
    1.json                # Task with status, blocks, blockedBy, owner
    2.json
```

### 2.5 Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_TEAM_NAME` | Current team context |
| `CLAUDE_CODE_AGENT_ID` | This agent's identifier |
| `CLAUDE_CODE_AGENT_TYPE` | Agent role (leader/worker) |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Feature flag |
| `CLAUDE_CODE_SPAWN_BACKEND` | tmux/iterm2/in-process |

### 2.6 Hooks for Team Events

| Hook | Fires When | Exit Code 2 Behavior |
|------|-----------|---------------------|
| `TeammateIdle` | Teammate about to go idle | Send feedback, keep working |
| `TaskCompleted` | Task being marked complete | Prevent completion, send feedback |

**Gemini routing impact:** Agent Teams operate at the process orchestration level (tmux panes, file system, CLI sessions). These are NOT API calls that pass through the messages endpoint. They are internal to Claude Code's runtime. Routing to Gemini requires intercepting the headless CLI invocation, not the API.

---

## Routing Architecture for Gemini Backend

### Problem Statement

When using antigravity models like `gemini-claude-opus-4.6-thinking` through a Gemini-based backend, these Anthropic-specific primitives will fail because:

1. Gemini's `/v1/generateContent` has no concept of `defer_loading`, `allowed_callers`, `caller`, `server_tool_use`, or `code_execution_tool_result`
2. Agent Teams use local filesystem coordination, not API calls
3. The `advanced-tool-use-2025-11-20` beta header is Anthropic-specific

### Proposed Architecture: Three-Layer Proxy

```
Claude Code CLI
      |
      v
[Layer 1: CLI Interceptor]     -- Handles Agent Teams (process-level)
      |
      v
[Layer 2: API Translator]      -- Handles Advanced Tool Use (API-level)
      |
      v
[Layer 3: LiteLLM Proxy]       -- Handles model routing + format translation
      |
      +-- Anthropic API (native)
      +-- Gemini API (translated)
      +-- Vertex AI (translated)
```

### Layer 1: CLI Interceptor (Agent Teams)

Agent Teams spawn Claude Code instances via subprocess. The interceptor sits between the leader and spawned processes.

**Strategy:** Replace the Claude Code binary path with a wrapper that:

```bash
#!/bin/bash
# antigravity-claude-wrapper.sh
# Intercepts claude CLI calls and routes model selection

REQUESTED_MODEL="${CLAUDE_MODEL:-claude-opus-4-6}"

case "$REQUESTED_MODEL" in
  gemini-claude-opus-4.6-thinking|antigravity/*)
    # Route through LiteLLM proxy
    export ANTHROPIC_BASE_URL="http://localhost:4000"
    export ANTHROPIC_API_KEY="$LITELLM_PROXY_KEY"
    ;;
esac

# Forward to real claude binary
exec /usr/local/bin/claude.real "$@"
```

**Key consideration:** Each spawned teammate is an independent Claude Code session making its own API calls. The wrapper ensures ALL sessions route through the proxy, not just the leader.

### Layer 2: API Translator

A middleware that transforms Anthropic API-specific fields before they reach Gemini.

**Translation rules:**

| Anthropic Feature | Gemini Translation |
|---|---|
| `defer_loading: true` | Strip field; maintain local tool registry; inject tool defs on demand |
| `tool_search_tool_regex_*` | Implement search locally; return tool definitions directly |
| `allowed_callers` | Strip field; decompose PTC into sequential Gemini tool calls |
| `server_tool_use` (code_execution) | Use Gemini's native code execution OR run local sandbox |
| `caller` field on tool_use | Strip; map tool results back to correct execution context |
| `code_execution_tool_result` | Convert to standard tool result format |
| `input_examples` | Append examples to tool `description` as formatted text |
| `container` (request/response) | Manage local container state; strip from Gemini requests |
| `context-management-*` beta | Strip entirely |

**PTC decomposition (the hard part):**

When Claude emits a `server_tool_use` with code that calls tools, the translator must:

1. Parse the Python code to extract tool call sequences
2. Execute tool calls sequentially or in parallel against your actual backends
3. Feed results back into a local Python sandbox
4. Return only the final stdout/stderr to Gemini as a standard tool result

```python
# Pseudocode for PTC decomposition
class PTCDecomposer:
    def handle_server_tool_use(self, code_block):
        sandbox = PythonSandbox()
        
        # Register tool stubs that call real backends
        for tool in self.registered_tools:
            sandbox.register_async_function(
                tool.name,
                lambda **kwargs: self.execute_tool(tool.name, kwargs)
            )
        
        # Run the code; tool calls happen via registered stubs
        result = sandbox.execute(code_block.input.code)
        
        return {
            "type": "tool_result",
            "content": result.stdout
        }
```

### Layer 3: LiteLLM Proxy Configuration

LiteLLM already supports Anthropic-to-Gemini translation for basic operations. Configure it as the base routing layer:

```yaml
# litellm_config.yaml
model_list:
  # Native Anthropic routing
  - model_name: claude-opus-4-6
    litellm_params:
      model: anthropic/claude-opus-4-6
      api_key: os.environ/ANTHROPIC_API_KEY

  # Gemini backend for antigravity models
  - model_name: gemini-claude-opus-4.6-thinking
    litellm_params:
      model: gemini/gemini-2.5-pro-preview
      api_key: os.environ/GEMINI_API_KEY

  # Fallback chain
  - model_name: antigravity-default
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GEMINI_API_KEY

router_settings:
  model_group_alias:
    "claude-opus-4-6": "gemini-claude-opus-4.6-thinking"
  
  # Enable Anthropic message format on proxy
  enable_anthropic_messages_endpoint: true

litellm_settings:
  # Forward beta headers for native Anthropic calls
  forward_anthropic_beta_headers: true
  
  # Strip unsupported fields for Gemini
  drop_params: true
```

**LiteLLM already handles:**

- `anthropic/v1/messages` endpoint translation to Gemini format
- Tool call format conversion (Anthropic `tool_use` to Gemini `function_call`)
- Streaming translation
- Thought signatures (Gemini) preservation

**LiteLLM does NOT yet handle (requires Layer 2):**

- `defer_loading` / tool search
- `allowed_callers` / PTC loop
- `caller` field routing
- `server_tool_use` / `code_execution_tool_result` block types
- `input_examples` injection

### Implementation Priority

| Phase | Component | Complexity | Impact |
|-------|-----------|------------|--------|
| 1 | LiteLLM proxy with basic routing | Low | Gets basic Gemini calls working |
| 2 | CLI wrapper for Agent Teams | Low | Enables multi-agent with Gemini |
| 3 | `input_examples` to description injection | Low | Improves tool call accuracy |
| 4 | `defer_loading` local registry | Medium | Reduces context overhead |
| 5 | PTC decomposition sandbox | High | Enables programmatic tool orchestration |

### Critical Gaps and Risks

1. **PTC is fundamentally Anthropic-specific.** The execution-pauses-for-tool-results loop is tightly coupled to Anthropic's container infrastructure. Full fidelity requires building an equivalent sandbox locally.

2. **Agent Teams file coordination assumes Claude Code runtime.** If teammates are running through a Gemini backend, the filesystem-based inbox/task system still works because it is process-level, not API-level. The critical question is whether the Gemini-backed model can correctly USE the TeammateTool operations, since those instructions come from Claude Code's system prompt, not the API spec.

3. **Token-efficient tool use** (`token-efficient-tools-2025-02-19`) is automatic on Claude 4+ models. Gemini has its own token optimization. LiteLLM handles this transparently.

4. **Fine-grained tool streaming** (`fine-grained-tool-streaming-2025-05-14`) allows streaming partial JSON tool parameters. Gemini streams differently. LiteLLM buffers and translates.

---

## Quick Reference: All New Types and Fields

### New Beta Headers
- `advanced-tool-use-2025-11-20`
- `context-management-2025-06-27`
- `token-efficient-tools-2025-02-19`
- `fine-grained-tool-streaming-2025-05-14`
- `tool-search-tool-2025-10-19` (Bedrock-specific)

### New Tool Definition Fields
- `defer_loading` (boolean)
- `allowed_callers` (string array)
- `input_examples` (array of objects)

### New Built-in Tool Types
- `tool_search_tool_regex_20251119`
- `tool_search_tool_bm25_20251119`
- `code_execution_20250825`
- `clear_tool_uses_20250919`

### New Response Block Types
- `server_tool_use` (code execution invocation)
- `code_execution_tool_result` (sandbox output)
- `tool_reference` (deferred tool discovery result)

### New Response Fields
- `caller` on `tool_use` blocks (indicates PTC origin)
- `container` on message response (sandbox lifecycle)

### Agent Teams Operations (Claude Code CLI)
- `spawnTeam`, `discoverTeams`, `requestJoin`, `approveJoin`, `rejectJoin`
- `spawn`, `write`, `broadcast`
- `requestShutdown`, `approveShutdown`, `rejectShutdown`
- `cleanup`, `approvePlan`
- `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`
