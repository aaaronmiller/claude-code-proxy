# What "Start Everything" Includes

**Version:** 1.0.0  
**Date:** April 2, 2026

---

## Components Started by `cs-start`

When you run `cs-start` (or any `cs*` / `*si` / `*sr` alias), the following services are started:

### 1. Headroom Proxy (:8787) ✅

**Purpose:** Token compression layer

**What it does:**
- Compresses tokens before sending to upstream (97% reduction)
- GPU-accelerated inference (92% VRAM utilization)
- Routes to OpenRouter or other providers
- Maintains compression cache

**Process:** `headroom proxy --port 8787 ...`

**Memory:** ~200 MB

**Port:** 8787

---

### 2. RTK (Command Compression) ✅

**Purpose:** Command output compression

**What it does:**
- Compresses shell command outputs (88.9% reduction)
- Pre-processes before Headroom
- Integrated via shell hooks

**Process:** Shell integration (no daemon)

**Memory:** ~50 MB (when active)

---

### 3. Compression Dashboard (Optional) ⚙️

**Purpose:** Real-time stats tracking

**What it does:**
- Tracks token savings
- Displays cost savings
- Shows GPU utilization
- Web UI at `file://~/.compression_dashboard.html`

**Process:** `compression-dashboard.py` (if started)

**Memory:** ~100 MB

---

### 4. GPU Resident Manager (Optional) ⚙️

**Purpose:** Keep compression models in VRAM

**What it does:**
- Loads multiple models resident
- Maintains 92% VRAM utilization
- Prevents cold start latency

**Process:** `gpu-resident-manager.py` (if started via systemd)

**Memory:** ~5.3 GB VRAM

---

## What's NOT Started by Default

### Claude Code Proxy (:8082) ❌

**NOT started by `cs-start`** - this is compression-only.

To start Claude Code Proxy:
```bash
# Manual start
cd ~/code/claude-code-proxy
source .venv/bin/activate
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
python start_proxy.py &
```

**Note:** The `csi` / `csr` aliases use compression directly, not through Claude Code Proxy.

---

## Architecture

### Compression-Only (cs-start)
```
User → Headroom (:8787) → OpenRouter
       [Compression]
```

### Full Stack (cs-start + Claude Proxy)
```
User → Claude Proxy (:8082) → Headroom (:8787) → OpenRouter
       [API Translation]     [Compression]
```

---

## Quick Commands

```bash
# Start compression only
cs-start

# Start Claude with compression (direct to Headroom)
csi

# Start Claude Proxy + compression (manual)
cd ~/code/claude-code-proxy && python start_proxy.py &
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
claude

# Check what's running
cs-status

# Stop compression
cs-stop
```

---

## Service Details

| Service | Port | Memory | Auto-Start | Purpose |
|---------|------|--------|------------|---------|
| Headroom | 8787 | ~200 MB | ✅ Yes | Token compression |
| RTK | N/A | ~50 MB | ✅ Yes | Command compression |
| Dashboard | N/A | ~100 MB | ⚙️ Optional | Stats tracking |
| GPU Manager | N/A | ~5.3 GB VRAM | ⚙️ Optional | Model residency |
| Claude Proxy | 8082 | ~150 MB | ❌ No | API translation |

---

## Systemd Services (Optional)

For auto-start on boot:

```bash
# Enable services
systemctl --user enable gpu-resident-manager compression-tracker compression-dashboard

# Start services
systemctl --user start gpu-resident-manager compression-tracker compression-dashboard

# Check status
systemctl --user status gpu-resident-manager
```

---

## Manual Start Commands

### Headroom Only
```bash
headroom proxy --port 8787 --mode token_headroom \
  --openai-api-url https://openrouter.ai/api/v1 \
  --backend openrouter --no-telemetry &
```

### GPU Resident Manager
```bash
python3 ~/code/claude-code-proxy/compression/scripts/gpu-resident-manager.py &
```

### Compression Dashboard
```bash
python3 ~/code/claude-code-proxy/compression/scripts/compression-dashboard.py &
```

### Claude Code Proxy
```bash
cd ~/code/claude-code-proxy
source .venv/bin/activate
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
python start_proxy.py &
```

---

## Troubleshooting

### Check What's Running
```bash
# Compression
pgrep -f "headroom proxy" && echo "Headroom: Running" || echo "Headroom: Stopped"

# GPU Manager
pgrep -f "gpu-resident-manager" && echo "GPU Manager: Running" || echo "GPU Manager: Stopped"

# Dashboard
pgrep -f "compression-dashboard" && echo "Dashboard: Running" || echo "Dashboard: Stopped"

# Claude Proxy
pgrep -f "start_proxy.py" && echo "Claude Proxy: Running" || echo "Claude Proxy: Stopped"
```

### Health Checks
```bash
# Headroom health
curl http://127.0.0.1:8787/health

# Claude Proxy health
curl http://127.0.0.1:8082/health

# GPU status
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

---

*What "Start Everything" Includes v1.0.0 - April 2, 2026*
