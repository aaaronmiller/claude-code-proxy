# Compression Stack - Alias Matrix

**Version:** 2.1.0  
**Date:** April 2, 2026

---

## Current Alias Structure

### What Each Alias Does

| Alias | Starts Compression | Starts Proxy | CLI Used |
|-------|-------------------|--------------|----------|
| `csi` | ✅ Yes | ❌ No | `claude` (direct to Headroom) |
| `csr` | ✅ Yes | ❌ No | `claude --resume` (direct to Headroom) |
| `qsi` | ✅ Yes | ❌ No | `qwen` (direct to Headroom) |
| `osi` | ✅ Yes | ❌ No | `opencode` (direct to Headroom) |

**Current behavior:** ALL aliases start compression ONLY, then launch CLI directly to Headroom (:8787).

---

## What You Asked For

You want **TWO paths** for each CLI:

### Path 1: Compression Only (Direct to Headroom)
```
User → Headroom (:8787) → OpenRouter
```

### Path 2: Compression + Proxy
```
User → Claude Proxy (:8082) → Headroom (:8787) → OpenRouter
```

---

## Updated Alias Matrix

### Claude Code

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `csi` | ✅ | ❌ | `claude` | Direct to Headroom (faster) |
| `csi-proxy` | ✅ | ✅ | `claude` | Through proxy (API translation) |
| `csr` | ✅ | ❌ | `claude --resume` | Resume direct |
| `csr-proxy` | ✅ | ✅ | `claude --resume` | Resume through proxy |
| `csi-yolo` | ✅ | ❌ | `claude --dangerously-skip-permissions` | YOLO direct |
| `csi-proxy-yolo` | ✅ | ✅ | `claude --dangerously-skip-permissions` | YOLO through proxy |

### Qwen Code

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `qsi` | ✅ | ❌ | `qwen` | Direct to Headroom |
| `qsi-proxy` | ✅ | ✅ | `qwen` | Through proxy (if proxy adds value) |
| `qsr` | ✅ | ❌ | `qwen --resume` | Resume direct |
| `qsr-proxy` | ✅ | ✅ | `qwen --resume` | Resume through proxy |
| `qsi-yolo` | ✅ | ❌ | `qwen --dangerously-skip-permissions` | YOLO direct |

### Codex

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `csi-codex` | ✅ | ❌ | `codex` | Direct to Headroom |
| `csr-codex` | ✅ | ❌ | `codex resume` | Resume direct |
| `csi-codex-yolo` | ✅ | ❌ | `codex --dangerously-skip-permissions` | YOLO direct |

### OpenCode

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `osi` | ✅ | ❌ | `opencode` | Direct to Headroom |
| `osr` | ✅ | ❌ | `opencode --resume` | Resume direct |
| `osi-yolo` | ✅ | ❌ | `opencode --dangerously-skip-permissions` | YOLO direct |

### OpenClaw

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `ocl` | ✅ | ❌ | `openclaw` | Direct to Headroom |
| `ocr` | ✅ | ❌ | `openclaw --resume` | Resume direct |
| `ocl-yolo` | ✅ | ❌ | `openclaw --dangerously-skip-permissions` | YOLO direct |

### Hermes

| Alias | Compression | Proxy | Command | Use Case |
|-------|-------------|-------|---------|----------|
| `hsi` | ✅ | ❌ | `hermes` | Direct to Headroom |
| `hsr` | ✅ | ❌ | `hermes --resume` | Resume direct |
| `hsi-yolo` | ✅ | ❌ | `hermes --dangerously-skip-permissions` | YOLO direct |

---

## Global Commands

| Alias | Starts | Purpose |
|-------|--------|---------|
| `cs-start` | Compression only | Start Headroom proxy |
| `cs-stop` | Compression only | Stop Headroom proxy |
| `cs-restart` | Compression only | Restart Headroom proxy |
| `cs-status` | N/A | Check compression status |
| `cs-health` | N/A | Health check |
| `cs-stats-quick` | N/A | Quick stats |
| `cproxy-start` | Proxy + Compression | Start both layers |
| `cproxy-stop` | Proxy + Compression | Stop both layers |
| `cproxy-status` | N/A | Check both status |

---

## Environment Variables Set

### Direct to Headroom (csi, qsi, etc.)
```bash
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
```

### Through Proxy (csi-proxy, etc.)
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
export ANTHROPIC_API_KEY="pass"
```

---

## Quick Reference

### Use Direct (csi, qsi, etc.) When:
- ✅ You want minimum latency
- ✅ CLI supports OpenAI format natively
- ✅ You don't need Claude API translation
- ✅ Personal use, single user

### Use Proxy (csi-proxy, etc.) When:
- ✅ You need Claude API format translation
- ✅ You want model routing (BIG/MIDDLE/SMALL)
- ✅ You want web dashboard
- ✅ Multi-user setup

---

## Implementation

```bash
# Helper functions
_compression_auto_start() {
    if ! pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo -n "🔧 Starting compression... "
        headroom proxy --port 8787 --mode token_headroom \
            --openai-api-url https://openrouter.ai/api/v1 \
            --backend openrouter --no-telemetry > /dev/null 2>&1 &
        sleep 3
        pgrep -f "headroom proxy" > /dev/null 2>&1 && echo "✅" || echo "⚠️ Failed"
    fi
}

_proxy_auto_start() {
    _compression_auto_start
    if ! pgrep -f "start_proxy.py" > /dev/null 2>&1; then
        echo -n "🔧 Starting proxy... "
        cd ~/code/claude-code-proxy
        source .venv/bin/activate 2>/dev/null || true
        export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
        nohup python start_proxy.py --skip-validation > /dev/null 2>&1 &
        sleep 3
        pgrep -f "start_proxy.py" > /dev/null 2>&1 && echo "✅" || echo "⚠️ Failed"
    fi
}

# Direct to Headroom (compression only)
alias csi='_compression_auto_start && OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude'
alias csr='_compression_auto_start && OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --resume'
alias csi-yolo='_compression_auto_start && OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --dangerously-skip-permissions'

# Through Proxy (compression + proxy)
alias csi-proxy='_proxy_auto_start && ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude'
alias csr-proxy='_proxy_auto_start && ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --resume'
alias csi-proxy-yolo='_proxy_auto_start && ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --dangerously-skip-permissions'

# Global commands
alias cs-start='_compression_auto_start'
alias cproxy-start='_proxy_auto_start'
```

---

## OpenRouter Exception

OpenRouter CLI (if it exists) would be:

| Alias | Compression | Direct to OpenRouter |
|-------|-------------|---------------------|
| `osi-or` | ❌ | ✅ |
| `osi-or-yolo` | ❌ | ✅ |

Since OpenRouter is already the upstream, no compression layer needed for direct OpenRouter CLI.

---

*Alias Matrix v2.1.0 - April 2, 2026*
