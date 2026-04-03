# Compression Stack - Comprehensive Aliases

**Version:** 2.0.0  
**Date:** April 2, 2026

---

## What "Start Everything" Includes

When you run `cs-start`, it starts:

1. **Headroom Proxy** (:8787)
   - Token compression (97% rate)
   - GPU-accelerated (92% VRAM utilization)
   - Routes to OpenRouter

2. **RTK** (Command Layer)
   - Command output compression (88.9% rate)
   - Pre-processing before Headroom

3. **Claude Code Proxy** (:8082)
   - API format translation
   - Model routing (BIG/MIDDLE/SMALL)
   - Web dashboard

4. **Compression Dashboard** (optional)
   - Real-time stats tracking
   - Web UI at `file://~/.compression_dashboard.html`

---

## Auto-Start Compression Aliases

**All aliases below automatically start compression in background if not running.**

### Global Start/Stop

```bash
# Start compression stack (background)
cs-start

# Stop compression stack
cs-stop

# Restart compression stack
cs-restart

# Check status
cs-status

# Health check
cs-health
```

---

## Claude Code Aliases

### Start New Session (with compression)
```bash
csi              # Start fresh Claude session
csi-yolo         # Start with --dangerously-skip-permissions
csi-safe         # Start with read-only mode
```

### Resume Session (with compression)
```bash
csr              # Resume most recent session
csr-last         # Resume last session
csr-<id>         # Resume specific session ID (e.g., csr-abc123)
```

### Implementation
```bash
# ~/.zshrc aliases
alias csi='_compression_auto_start && claude'
alias csi-yolo='_compression_auto_start && claude --dangerously-skip-permissions'
alias csi-safe='_compression_auto_start && claude --permission-mode=read'
alias csr='_compression_auto_start && claude --resume'
alias csr-last='_compression_auto_start && claude --resume'
```

---

## Qwen Code Aliases

### Start New Session
```bash
qsi              # Start fresh Qwen session
qsi-yolo         # Start with --dangerously-skip-permissions
qsi-prompt="<x>" # Start with initial prompt
```

### Resume Session
```bash
qsr              # Resume most recent session
qsr-<id>         # Resume specific session
```

### Implementation
```bash
alias qsi='_compression_auto_start && qwen'
alias qsi-yolo='_compression_auto_start && qwen --dangerously-skip-permissions'
alias qsi-prompt='_compression_auto_start && qwen --prompt'
alias qsr='_compression_auto_start && qwen --resume'
alias qsr-alias='_compression_auto_start && qwen -r'
```

---

## Codex CLI Aliases

### Start New Session
```bash
csi-codex        # Start fresh Codex session
csi-codex-yolo   # Start with --dangerously-skip-permissions
```

### Resume Session
```bash
csr-codex        # Resume most recent session
csr-codex-<id>   # Resume specific session
```

### Implementation
```bash
alias csi-codex='_compression_auto_start && codex'
alias csi-codex-yolo='_compression_auto_start && codex --dangerously-skip-permissions'
alias csr-codex='_compression_auto_start && codex resume'
```

---

## OpenCode Aliases

### Start New Session
```bash
osi              # Start fresh OpenCode session
osi-yolo         # Start with --dangerously-skip-permissions
```

### Resume Session
```bash
osr              # Resume most recent session
```

### Implementation
```bash
alias osi='_compression_auto_start && opencode'
alias osi-yolo='_compression_auto_start && opencode --dangerously-skip-permissions'
alias osr='_compression_auto_start && opencode --resume'
```

---

## OpenClaw Aliases

### Start New Session
```bash
ocl              # Start fresh OpenClaw session
ocl-yolo         # Start with --dangerously-skip-permissions
```

### Resume Session
```bash
ocr              # Resume most recent session
```

### Implementation
```bash
alias ocl='_compression_auto_start && openclaw'
alias ocl-yolo='_compression_auto_start && openclaw --dangerously-skip-permissions'
alias ocr='_compression_auto_start && openclaw --resume'
```

---

## Hermes Aliases

### Start New Session
```bash
hsi              # Start fresh Hermes session
hsi-yolo         # Start with --dangerously-skip-permissions
```

### Resume Session
```bash
hsr              # Resume most recent session
```

### Implementation
```bash
alias hsi='_compression_auto_start && hermes'
alias hsi-yolo='_compression_auto_start && hermes --dangerously-skip-permissions'
alias hsr='_compression_auto_start && hermes --resume'
```

---

## Helper Functions

Add these to `~/.zshrc`:

```bash
# Auto-start compression if not running
_compression_auto_start() {
    if ! pgrep -f "headroom proxy" > /dev/null; then
        echo "🔧 Starting compression stack..."
        cs-start > /dev/null 2>&1
        sleep 2
        if pgrep -f "headroom proxy" > /dev/null; then
            echo "✅ Compression ready"
        else
            echo "⚠️  Compression failed to start"
        fi
    fi
}

# Quick status check
_compression_status() {
    if pgrep -f "headroom proxy" > /dev/null; then
        echo -e "✅ Compression: \033[0;32mRunning\033[0m"
    else
        echo -e "❌ Compression: \033[0;31mNot Running\033[0m"
    fi
}
```

---

## Quick Reference Table

| CLI | Start | Start (-yolo) | Resume |
|-----|-------|---------------|--------|
| **Claude Code** | `csi` | `csi-yolo` | `csr` |
| **Qwen Code** | `qsi` | `qsi-yolo` | `qsr` |
| **Codex** | `csi-codex` | `csi-codex-yolo` | `csr-codex` |
| **OpenCode** | `osi` | `osi-yolo` | `osr` |
| **OpenClaw** | `ocl` | `ocl-yolo` | `ocr` |
| **Hermes** | `hsi` | `hsi-yolo` | `hsr` |

---

## Usage Examples

### Typical Workflow

```bash
# Morning: Start compression and begin work
cs-start
csi  # Start Claude session

# Afternoon: Resume session
csr  # Resume Claude

# Switch to Qwen for different task
qsi  # Start Qwen session

# End of day: Check stats, stop compression
cs-stats-quick
cs-stop
```

### YOLO Mode (Use with Caution)

```bash
# Claude with no permission prompts
csi-yolo

# Qwen with no permission prompts
qsi-yolo

# Codex with no permission prompts
csi-codex-yolo
```

### Session Management

```bash
# Resume specific session by ID
csr-abc123  # Claude session abc123
qsr-def456  # Qwen session def456

# List recent sessions (CLI-specific)
claude --list-sessions
qwen --list-sessions
```

---

## Installation

Add to `~/.zshrc`:

```bash
# Compression Stack Aliases
# Auto-start compression for all CLI tools

# Helper function
_compression_auto_start() {
    if ! pgrep -f "headroom proxy" > /dev/null; then
        echo -n "🔧 Starting compression... "
        cs-start > /dev/null 2>&1
        sleep 2
        if pgrep -f "headroom proxy" > /dev/null; then
            echo "✅"
        else
            echo "⚠️  Failed"
        fi
    fi
}

# Claude Code
alias csi='_compression_auto_start && claude'
alias csi-yolo='_compression_auto_start && claude --dangerously-skip-permissions'
alias csi-safe='_compression_auto_start && claude --permission-mode=read'
alias csr='_compression_auto_start && claude --resume'
alias csr-last='_compression_auto_start && claude --resume'

# Qwen Code
alias qsi='_compression_auto_start && qwen'
alias qsi-yolo='_compression_auto_start && qwen --dangerously-skip-permissions'
alias qsi-prompt='_compression_auto_start && qwen --prompt'
alias qsr='_compression_auto_start && qwen --resume'
alias qsr-alias='_compression_auto_start && qwen -r'

# Codex
alias csi-codex='_compression_auto_start && codex'
alias csi-codex-yolo='_compression_auto_start && codex --dangerously-skip-permissions'
alias csr-codex='_compression_auto_start && codex resume'

# OpenCode
alias osi='_compression_auto_start && opencode'
alias osi-yolo='_compression_auto_start && opencode --dangerously-skip-permissions'
alias osr='_compression_auto_start && opencode --resume'

# OpenClaw
alias ocl='_compression_auto_start && openclaw'
alias ocl-yolo='_compression_auto_start && openclaw --dangerously-skip-permissions'
alias ocr='_compression_auto_start && openclaw --resume'

# Hermes
alias hsi='_compression_auto_start && hermes'
alias hsi-yolo='_compression_auto_start && hermes --dangerously-skip-permissions'
alias hsr='_compression_auto_start && hermes --resume'

# Global compression control
alias cs-start='systemctl --user start gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry > /dev/null 2>&1 & sleep 3; echo "✅ Compression started"'
alias cs-stop='pkill -f "headroom proxy" 2>/dev/null; systemctl --user stop gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; echo "⏹️  Compression stopped"'
alias cs-restart='cs-stop && sleep 2 && cs-start'
alias cs-status='systemctl --user status gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; pgrep -f "headroom proxy" > /dev/null && echo -e "Headroom: \033[0;32mRunning\033[0m" || echo -e "Headroom: \033[0;31mNot Running\033[0m"'
alias cs-health='curl -s http://127.0.0.1:8787/health > /dev/null 2>&1 && echo -e "✅ Headroom: Healthy" || echo -e "❌ Headroom: Unhealthy"'
alias cs-stats-quick='python3 -c "import json; from pathlib import Path; f = Path.home() / \".compression_stats.json\"; s = json.load(f)[\"total\"] if f.exists() else {\"tokens_saved\":0,\"requests\":0}; t = s.get(\"tokens_saved\", 0); r = s.get(\"requests\", 0); ts = f\"{t/1e6:.1f}M\" if t > 1e6 else f\"{t/1e3:.0f}K\" if t > 1e3 else str(t); print(f\"💰 Saved {ts} tokens ({r} requests)\")" 2>/dev/null || echo "💰 No stats yet"'
```

Then reload:
```bash
source ~/.zshrc
```

---

## Troubleshooting

### Compression Not Auto-Starting

```bash
# Check if function is loaded
type _compression_auto_start

# Manually start
cs-start

# Check health
cs-health
```

### Alias Not Working

```bash
# Check if alias exists
alias csi

# Reload zshrc
source ~/.zshrc
```

### Session Not Resuming

```bash
# List available sessions
claude --list-sessions

# Resume with explicit ID
claude --resume <session-id>
```

---

*Comprehensive Aliases Guide v2.0.0 - April 2, 2026*
