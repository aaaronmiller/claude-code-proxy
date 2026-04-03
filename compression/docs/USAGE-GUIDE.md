# Compression Stack - Usage Guide

**Version:** 1.0.0  
**Date:** April 2, 2026

---

## Quick Start

### Start Everything (Recommended)

```bash
# Start compression stack + claude-code-proxy
cs-start

# Start Claude with compression
csi

# That's it! Compression is active.
```

---

## Scenario 1: Full Stack (Claude Proxy + Compression)

### Start All Services

```bash
# Option A: Using aliases (after running install-all.sh)
source ~/.zshrc  # Load aliases
cs-start         # Start everything

# Option B: Using unified script
cd ~/code/claude-code-proxy
./compression/scripts/unified-start.sh start

# Option C: Manual start
# 1. Start Headroom
headroom proxy --port 8787 --mode token_headroom \
  --openai-api-url https://openrouter.ai/api/v1 \
  --backend openrouter --no-telemetry &

# 2. Start Claude Code Proxy
cd ~/code/claude-code-proxy
source .venv/bin/activate
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
python start_proxy.py --skip-validation &
```

### Verify Services

```bash
# Check health
cs-health

# Expected output:
# ✓ Headroom (:8787)
# ✓ Claude Code Proxy (:8082)
# ✓ GPU VRAM: 5311 MiB
```

### Use with Different CLIs

#### Claude Code
```bash
# With compression (recommended)
csi  # or cli-init

# Or manually
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
export ANTHROPIC_API_KEY="pass"
claude
```

#### Qwen Code
```bash
# With compression
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
qwen

# Or use shim
~/.config/input-compression/shims/qwen
```

#### Codex CLI
```bash
# With compression
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
codex

# Or use shim
~/.config/input-compression/shims/codex
```

#### OpenCode
```bash
# With compression
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
opencode

# Or use shim
~/.config/input-compression/shims/opencode
```

#### OpenClaw
```bash
# With compression
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
openclaw

# Or use shim
~/.config/input-compression/shims/openclaw
```

#### Hermes
```bash
# With compression
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
hermes

# Or use shim
~/.config/input-compression/shims/hermes
```

---

## Scenario 2: Compression Proxies ONLY (No Claude Proxy)

### Start Only Headroom + RTK

```bash
# Option A: Using compression-stack script
cd ~/code/claude-code-proxy/compression
./scripts/unified-start.sh start

# Option B: Manual start
# 1. Start Headroom
headroom proxy --port 8787 --mode token_headroom \
  --openai-api-url https://openrouter.ai/api/v1 \
  --backend openrouter --no-telemetry &

# 2. Initialize RTK (optional, for command compression)
rtk init --global

# 3. Verify
curl http://127.0.0.1:8787/health
# Expected: {"status":"healthy",...}
```

### Use with CLIs (Direct to Headroom)

```bash
# All CLIs point directly to Headroom (:8787)
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"

# Then use any CLI
claude  # Will connect directly to Headroom
qwen
codex
opencode
openclaw
hermes
```

### Architecture (Compression Only)

```
CLI → Headroom (:8787) → OpenRouter
      [Compression]
```

**Note:** Without claude-code-proxy, you lose:
- ❌ Claude API format translation
- ❌ Model routing (BIG/MIDDLE/SMALL)
- ❌ Web dashboard
- ✅ Token compression (97% rate)
- ✅ Command compression (RTK)

---

## Scenario 3: Claude Proxy ONLY (No Compression)

### Start Only Claude Proxy

```bash
# Option A: Manual start
cd ~/code/claude-code-proxy
source .venv/bin/activate

# Point directly to OpenRouter (skip Headroom)
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export PROVIDER_BASE_URL="https://openrouter.ai/api/v1"

python start_proxy.py --skip-validation &

# Option B: Using compression-stack (stop compression)
cs-stop   # Stop everything
# Then start proxy without compression
```

### Use with CLIs

```bash
# Point to proxy (no compression)
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
export ANTHROPIC_API_KEY="pass"
claude
```

### Architecture (Proxy Only)

```
CLI → Claude Proxy (:8082) → OpenRouter
      [API Translation]
```

**Note:** Without Headroom, you lose:
- ❌ Token compression (97% savings)
- ❌ Command compression (RTK)
- ✅ Claude API format translation
- ✅ Model routing
- ✅ Web dashboard

---

## Scenario 4: Quick Temporary Sessions

### One-Time Compression Session

```bash
# Start compression, use it, stop it
cs-start
claude  # Use with compression
# ... session done ...
cs-stop
```

### Test Compression

```bash
# Quick test
cs-start
cs-stats-quick
# Output: 💰 Saved $X.XX today (X.XM tokens, X requests)
cs-stop
```

### Check What's Running

```bash
# Full status
cs-status

# Quick health
cs-health

# Manual check
pgrep -f "headroom proxy" && echo "Headroom: Running" || echo "Headroom: Stopped"
pgrep -f "start_proxy.py" && echo "Proxy: Running" || echo "Proxy: Stopped"
```

---

## Configuration Modes

### Switch Compression Modes

```bash
# Maximum compression (98%, 80ms latency)
cs-max

# Balanced (97%, 50ms) ← DEFAULT
cs-balanced

# Speed mode (90%, 20ms)
cs-speed

# Free tier optimization (99%, 50ms)
cs-free
```

### Low-VRAM Mode (5GB GPU)

```bash
# Edit GPU config
nano ~/code/claude-code-proxy/compression/scripts/gpu-resident-manager.py

# Set:
# - batch_size: 4 (instead of 16)
# - preload_models: ["kompress-small"]
# - gpu_cache_mb: 500 (instead of 1500)

# Restart
cs-restart
```

### CPU-Only Mode (No GPU)

```bash
# Set environment variable
export HEADROOM_DEVICE=cpu

# Or edit config
nano ~/.headroom/config.json
# Set: "device": "cpu"

# Restart
cs-restart
```

---

## Network Access (Remote Machines)

### SSH Tunneling

```bash
# From remote machine to proxy host
ssh -L 8787:localhost:8787 -L 8082:localhost:8082 user@proxy-host

# Then on remote machine
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
claude
```

### LAN Cleartext Access

```bash
# On proxy server (allow LAN access)
headroom proxy --port 8787 --host 0.0.0.0 ...

# On client machine
export OPENAI_BASE_URL="http://192.168.1.100:8787/v1"
claude
```

**⚠️ Warning:** LAN access is unencrypted. Use SSH tunneling for security.

---

## Troubleshooting

### Services Won't Start

```bash
# Check what's running
cs-status

# Kill stuck processes
pkill -f "headroom proxy"
pkill -f "start_proxy.py"

# Restart
cs-restart
```

### Compression Not Working

```bash
# Verify Headroom is running
curl http://127.0.0.1:8787/health

# Check compression stats
cs-stats-quick

# Check Headroom logs
tail -f ~/.local/share/headroom/headroom-default.out | grep -E "compress|saved"
```

### High Latency

```bash
# Check GPU status
nvidia-smi

# Check queue depth
cs-health

# Try speed mode
cs-speed
```

### RTK Not Working

```bash
# Check installation
rtk --version

# Reinitialize
rtk init --global

# Check stats
rtk gain
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `cs-start` | Start all compression services |
| `cs-stop` | Stop all services |
| `cs-restart` | Restart all services |
| `cs-status` | Show service status |
| `cs-health` | Full health check |
| `csi` | Start Claude with compression |
| `csr` | Resume Claude with compression |
| `cs-stats-quick` | Quick stats one-liner |
| `cs-max` | Maximum compression mode |
| `cs-balanced` | Balanced mode (default) |
| `cs-speed` | Speed mode |
| `cs-free` | Free tier mode |

---

## Architecture Diagrams

### Full Stack (Recommended)
```
User → Claude Proxy (:8082) → Headroom (:8787) → OpenRouter
       [API Translation]     [Compression]
```

### Compression Only
```
User → Headroom (:8787) → OpenRouter
       [Compression]
```

### Proxy Only
```
User → Claude Proxy (:8082) → OpenRouter
       [API Translation]
```

---

*Usage Guide v1.0.0 - April 2, 2026*
