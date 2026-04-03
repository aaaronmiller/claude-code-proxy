# Alias & Command Design — Proxy Chain

## Problem

Running a 3-proxy chain with multiple usage patterns creates a combinatorial explosion of commands. The naive approach produces **8+ aliases** just for start/stop + tool launch combos — a maintenance nightmare that clutters `.zshrc`, creates inconsistent behavior, and makes it impossible to remember which command does what.

---

## The Architecture

### Three modes, one base port

| Mode | What runs | Chain |
|------|-----------|-------|
| **comp** | Headroom only | tools → :8787 → Anthropic direct (compression, no proxy) |
| **proxy** | Headroom + ClaudeProxy | tools → :8787 → :8082 → OpenRouter (compression + model routing) |
| **full** | Headroom + ClaudeProxy + CLIProxyAPI | tools → :8787 → :8082 → :8317 → Antigravity (everything) |

**CLIProxyAPI is NEVER started alone.** It only runs in `full` mode, when both Headroom and ClaudeProxy are also running. It's the top-tier provider, not a base layer.

**ClaudeProxy is only started with Headroom.** No solo mode.

**Headroom is the constant base** — always running in every mode. All tools point at :8787. The difference is what Headroom's upstream is, set at start time.

### Compression-Only Mode (comp)

When only Headroom is running, it forwards directly to Anthropic's API:

```
Client → Headroom(:8787) → api.anthropic.com
```

Headroom compresses the context but uses the normal Anthropic endpoint — no Claude Code Proxy or CLIProxyAPI involved.

### RTK (Not a Proxy)

`rtk` is a Rust CLI wrapper (`rtk <command>`) that compresses terminal command output **before** it reaches the LLM. It has no daemon, no port, no startup. It runs as a foreground wrapper. Not part of the proxy chain.

---

## The Combinatorial Explosion (Naive Approach)

### What you might think you need

For each tool (claude, qwen), each mode (full chain, compression only), each session type (init, continue), plus proxy management:

```
# Proxy management (2)
proxies-up
proxies-down

# Claude, full chain (2)
cc-init
cc-con

# Claude, compression only (2)
cc-init-comp
cc-con-comp

# Qwen, full chain (2)
qw-init
qw-con

# Qwen, compression only (2)
qw-init-comp
qw-con-comp
```

**That's 10 aliases.** And it scales linearly — add another tool, add 4 more. Add another mode, add 4 more per tool.

### Why this approach fails

| Problem | Detail |
|---------|--------|
| **Memory tax** | You can't remember which alias does what. `cc-con-comp`? `qw-init-comp`? You'll forget. |
| **`.zshrc` bloat** | 10+ lines of nearly-identical aliases that do one thing: set `ANTHROPIC_BASE_URL` |
| **Stale config risk** | If a port changes, every alias is wrong. If you add a mode, you edit every alias. |
| **False specificity** | `--continue` is a tool flag, not a proxy concern. Baking it into the alias name conflates two orthogonal dimensions. |
| **Tool lock-in** | The aliases assume you only use claude and qwen. Cursor? Open WebUI? curl? Each gets its own alias. |
| **No status** | None of these tell you what's actually running. You need a separate status command anyway. |

---

## The proxy-stack Alternative (What Actually Existed)

### What it proposes

A more elaborate supervisor script (`proxy-stack`) with 3 modes:

```
proxy-stack start comp    → Headroom only (:8787 → Anthropic direct)
proxy-stack start proxy   → Headroom + ClaudeProxy (:8787 → :8082 → OpenRouter)
proxy-stack start full    → Headroom + ClaudeProxy + CLIProxyAPI (:8787 → :8082 → :8317 → Antigravity)
```

Plus `stop`, `status`, `logs`, `restart` commands, with per-mode stop (only kills what's needed for that mode).

### What it gets right

| Strength | Detail |
|----------|--------|
| **Per-mode stop** | `proxy-stack stop comp` only kills Headroom, not ClaudeProxy |
| **3 routing modes** | `comp` / `proxy` / `full` gives granular control |
| **`proxy-stack logs`** | Quick per-service log access |
| **Sequential startup** | Same ordering as `proxies` — CLIProxyAPI → ClaudeProxy → Headroom |

### What it gets wrong (for our case)

| Flaw | Impact |
|------|--------|
| **Comp routing mismatch** | `proxy-stack comp` routes Headroom → Anthropic direct. But we need Headroom → CLIProxyAPI for the real compression stack. |
| **Over-complexity** | 3 modes × 5 commands = 15 code paths. We only use 2 modes. |
| **Per-mode stop is pointless** | When you stop proxies, you stop *all* of them. Partial stop leaves orphan processes. |
| **PID-pattern matching** | Uses `pgrep -f` on command strings — fragile if multiple instances run. |
| **Duplicate of proxies** | The simpler `proxies` script does the same job with less code. |

### Verdict on proxy-stack

**Better vocabulary than `proxies` but wrong routing for our use case.** The 3-mode design sounds comprehensive but `comp → Anthropic direct` doesn't match our stack (which always goes through CLIProxyAPI). The `proxies` script with `--comp` routing to CLIProxyAPI is what we actually need.

---

## The Current Solution

### Design Principles

1. **Headroom is always the entry point.** Clients point at :8787. The chain topology is decided at start time.
2. **One command to start/stop.** No alias explosion.
3. **`pgrep` over PID files.** Process-based tracking is self-healing.
4. **Health checks via HTTP, not PID.** A process can run without listening.
5. **Sequential startup with waits.** Each proxy must be ready before the next starts.
6. **Two aliases for daily use.** That's it.

### The Command

```
proxies [up|down|status|restart] [--comp|--full]
```

```
proxies up          → Start full chain (all 3 proxies)
proxies up --comp   → Compression only (Headroom → CLIProxyAPI)
proxies down        → Kill all proxy processes
proxies status      → Show running proxies with PIDs
proxies restart     → Stop and restart (defaults to last mode)
```

### The Aliases (3 lines in .zshrc)

```bash
alias proxies='/home/cheta/code/claude-code-proxy/proxies'
alias cc='ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude'
alias qw='OPENAI_BASE_URL=http://127.0.0.1:8787/v1 qwen'
```

**Three aliases.** Not 20. Not 10. Three.

The `proxies` command is also symlinked to `~/.local/bin/proxies` by the installer, so it's available as a bare command in any shell session.

### How It Works

#### Startup Flow

```
proxies up
  ├── 1. Start CLIProxyAPI (:8317) if not running
  │     └── wait for :8317 health (20s timeout)
  ├── 2. Start Claude Code Proxy (:8082) if --full mode
  │     └── wait for :8082 health (20s timeout)
  ├── 3. Start Headroom (:8787) with correct upstream
  │     ├── --full:   ANTHROPIC_TARGET_API_URL=http://127.0.0.1:8082
  │     ├── --comp:   ANTHROPIC_TARGET_API_URL=http://127.0.0.1:8317
  │     └── wait for :8787 health (30s timeout)
  └── done
```

Each step checks if the service is already running. Running `proxies up` twice is safe — it skips what's already there.

#### Shutdown

```
proxies down
  ├── pkill -f "headroom proxy"
  ├── pkill -f "start_proxy.py"
  └── pkill -f "cli-proxy-api-plus"
```

Blunt but effective. No PID files to stale. No state to reconcile.

#### Bypassing Compression

Headroom (:8787) is the default entry point. To skip it:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8082 claude    # via Claude Proxy only
ANTHROPIC_BASE_URL=http://127.0.0.1:8317 claude    # direct to CLIProxyAPI
```

No alias needed — this is an ad-hoc override, not a daily workflow.

---

## Why This Design

### The Separation of Concerns

| Layer | Responsibility | Interface |
|-------|---------------|-----------|
| **Infrastructure** | Proxy lifecycle, startup ordering, health checks | `proxies up/down/status` |
| **Routing** | Which upstream Headroom points to | `--comp` / `--full` flag |
| **Tool launch** | Running claude/qwen/cursor with correct base URL | `cc` / `qw` aliases or manual |

Each layer is independent:
- You can change routing (`--comp` vs `--full`) without changing tool aliases
- You can launch any tool without changing proxy config
- You can add new tools without touching the proxy script

### Why Not Tool-Specific Aliases Per Mode

The dimensionality:

```
Tools: claude, qwen, cursor, open-webui, curl, ...
Modes: full, comp
Sessions: init, continue
```

If you bake all dimensions into aliases: `2 tools × 2 modes × 2 sessions = 8 aliases` and growing.

If you separate them: `1 command + 2 aliases` and tool-specific flags are inline:

```bash
cc                        # default (compression)
cc --continue             # continue session
ANTHROPIC_BASE_URL=http://127.0.0.1:8082 claude  # bypass compression
qw                        # qwen, same pattern
qwen --continue           # qwen continue
```

The **only variable** that changes the proxy topology is `--comp` vs `--full`, and that's a start-time decision. Once the chain is running, all tools point at the same port.

### Why `pgrep` Over PID Files

PID files are a solved problem in the wrong direction. They require:
- Writing on start
- Reading on stop
- Cleanup on crash
- Staleness detection
- Race condition handling

`pgrep -f` just works. If the process exists, it finds it. If it died, it doesn't. No state to manage.

### Why HTTP Health Checks Over Port Listening

A port can be bound but the server not ready (Headroom's Python startup took ~8 seconds to actually serve requests after binding). `curl /health` confirms the service is actually accepting and responding.

### What Happens When You Add a 4th Proxy

With the current design: edit the startup sequence in `proxies`, add one sequential step.

With the naive approach: double your aliases.

With the proxy-stack approach: add a mode, but discover you need routing logic changes and health checks that don't match your actual topology.

---

## Trade-Offs

### What We Don't Have (Yet)

| Missing Feature | Severity | Fix |
|----------------|----------|-----|
| Per-service start/stop | Low | Add `proxies start headroom` subcommand |
| Per-service logs | Low | `tail -f /tmp/headroom.log` |
| `proxy` mode (no CLIProxyAPI) | Medium | Add `proxies up --proxy` (Headroom → ClaudeProxy only) |
| Auto-restart on failure | Medium | systemd user units or a watch loop |
| Web dashboard | None needed | Overkill for 3 processes |

### What We Won't Add (And Why)

| Rejected Feature | Reason |
|-----------------|--------|
| PID files | `pgrep` already solves this |
| Per-tool mode aliases | Inline env var overrides are cleaner |
| Systemd integration | These are user-space dev tools, not daemons |
| Web UI / dashboard | 3 processes don't need a GUI |
| Config file for services | The script is the config, 100 lines is fine |
| Curses / TUI | Terminal output is the UI |

---

## Summary

```
Problem: 20+ aliases for proxy chain management
Solution: 1 command + 2 aliases

proxies up          → start everything in order
proxies up --comp   → compression-only mode
proxies down        → kill everything
proxies status      → check what's running

cc                  → launch claude via Headroom
qw                  → launch qwen via Headroom
```

Total: **one script** (~110 lines), **two aliases** in `.zshrc`, **one symlink** (`~/.local/bin/proxies`), **zero state files**, **zero PID files**, **zero config files**.

The design separates infrastructure (proxy lifecycle) from tool usage (launching claude/qwen) from routing decisions (--comp vs --full). Each dimension is independently variable. Adding tools or modes doesn't multiply aliases.
