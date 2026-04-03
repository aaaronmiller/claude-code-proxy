# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE PROXY - COMPREHENSIVE ALIASES v2.3
# ═══════════════════════════════════════════════════════════════════════════════
# 
# SINGLE INSTANCE ARCHITECTURE:
#   - ONE Headroom instance serves ALL terminals and ALL CLI tools
#   - Start once per day: cs-start
#   - All terminals share the same compression proxy
#   - Aliases just USE the service, don't START it
#   - If not running, aliases warn but don't block
#
# TWO PATHS:
#   1. Direct to Headroom (compression only) - csi, qsi, etc.
#   2. Through Proxy (compression + proxy) - csi-proxy, qsi-proxy, etc.
#
# INSTALLATION:
#   cat ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh >> ~/.zshrc
#   source ~/.zshrc
# ═══════════════════════════════════════════════════════════════════════════════

# Compression stack location
if [[ -z "$COMPRESSION_DIR" ]]; then
    export COMPRESSION_DIR="$HOME/code/claude-code-proxy/compression"
fi
export PATH="$COMPRESSION_DIR/scripts:$PATH"

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - CHECK ONLY, DON'T START
# ═══════════════════════════════════════════════════════════════════════════════

# Check if compression is running (don't start)
_check_compression() {
    if ! pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo -e "⚠️  \033[0;33mCompression not running. Run 'cs-start' first.\033[0m"
        return 1
    fi
    return 0
}

# Check if proxy is running (don't start)
_check_proxy() {
    if ! pgrep -f "start_proxy.py" > /dev/null 2>&1; then
        echo -e "⚠️  \033[0;33mProxy not running. Run 'cproxy-start' first.\033[0m"
        return 1
    fi
    return 0
}

# Quick non-blocking check
_check_quick() {
    pgrep -f "headroom proxy" > /dev/null 2>&1
}

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL COMMANDS - Manual Start/Stop
# ═══════════════════════════════════════════════════════════════════════════════

# Compression only
cs-start() {
    if pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo "✅ Compression already running"
        return 0
    fi
    echo -n "🔧 Starting compression... "
    headroom proxy --port 8787 --mode token_headroom \
        --openai-api-url https://openrouter.ai/api/v1 \
        --backend openrouter --no-telemetry > /dev/null 2>&1 &
    sleep 2
    if pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌ Failed"
        return 1
    fi
}

cs-stop() {
    pkill -f "headroom proxy" 2>/dev/null
    echo "⏹️  Compression stopped"
}

cs-restart() {
    cs-stop
    sleep 2
    cs-start
}

cs-status() {
    if pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo -e "✅ Compression: \033[0;32mRunning\033[0m"
        curl -s http://127.0.0.1:8787/health 2>/dev/null | python3 -m json.tool 2>/dev/null | head -3
    else
        echo -e "❌ Compression: \033[0;31mNot Running\033[0m"
    fi
}

cs-health() {
    curl -s http://127.0.0.1:8787/health > /dev/null 2>&1 && echo "✅ Headroom: Healthy" || echo "❌ Headroom: Unhealthy"
}

cs-stats-quick() {
    python3 -c "
import json
from pathlib import Path
f = Path.home() / '.compression_stats.json'
s = json.load(f)['total'] if f.exists() else {'tokens_saved':0,'requests':0}
t = s.get('tokens_saved', 0)
r = s.get('requests', 0)
ts = f'{t/1e6:.1f}M' if t > 1e6 else f'{t/1e3:.0f}K' if t > 1e3 else str(t)
print(f'💰 Saved {ts} tokens ({r} requests)')
" 2>/dev/null || echo "💰 No stats yet"
}

# Proxy + Compression
cproxy-start() {
    cs-start
    if pgrep -f "start_proxy.py" > /dev/null 2>&1; then
        echo "✅ Proxy already running"
        return 0
    fi
    echo -n "🔧 Starting proxy... "
    cd ~/code/claude-code-proxy
    source .venv/bin/activate 2>/dev/null || true
    export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
    nohup python start_proxy.py --skip-validation > /dev/null 2>&1 &
    sleep 2
    if pgrep -f "start_proxy.py" > /dev/null 2>&1; then
        echo "✅"
    else
        echo "❌ Failed"
        return 1
    fi
}

cproxy-stop() {
    pkill -f "start_proxy.py" 2>/dev/null
    cs-stop
    echo "⏹️  Proxy + Compression stopped"
}

cproxy-restart() {
    cproxy-stop
    sleep 2
    cproxy-start
}

cproxy-status() {
    if pgrep -f "start_proxy.py" > /dev/null 2>&1; then
        echo -e "✅ Proxy: \033[0;32mRunning\033[0m"
    else
        echo -e "❌ Proxy: \033[0;31mNot Running\033[0m"
    fi
    cs-status
}

cproxy-health() {
    curl -s http://127.0.0.1:8082/health > /dev/null 2>&1 && echo "✅ Proxy: Healthy" || echo "❌ Proxy: Unhealthy"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE - DIRECT TO HEADROOM (Compression Only)
# ═══════════════════════════════════════════════════════════════════════════════

csi() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude "$@"
}

csr() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --resume "$@"
}

csi-yolo() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --dangerously-skip-permissions "$@"
}

csi-safe() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --permission-mode=read "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE - THROUGH PROXY (Compression + Proxy)
# ═══════════════════════════════════════════════════════════════════════════════

csi-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude "$@"
}

csr-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --resume "$@"
}

csi-proxy-yolo() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --dangerously-skip-permissions "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# QWEN CODE - DIRECT TO HEADROOM
# ═══════════════════════════════════════════════════════════════════════════════

qsi() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen "$@"
}

qsr() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen --resume "$@"
}

qsi-yolo() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen --dangerously-skip-permissions "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# QWEN CODE - THROUGH PROXY
# ═══════════════════════════════════════════════════════════════════════════════

qsi-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" qwen "$@"
}

qsr-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" qwen --resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CODEX - DIRECT TO HEADROOM
# ═══════════════════════════════════════════════════════════════════════════════

csi-codex() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex "$@"
}

csr-codex() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex resume "$@"
}

csi-codex-yolo() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex --dangerously-skip-permissions "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CODEX - THROUGH PROXY
# ═══════════════════════════════════════════════════════════════════════════════

csi-codex-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" codex "$@"
}

csr-codex-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" codex resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# OPENCODE - DIRECT TO HEADROOM
# ═══════════════════════════════════════════════════════════════════════════════
# Note: OpenCode YOLO mode is set in settings.json, not via CLI flag

osi() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" opencode "$@"
}

osr() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" opencode --resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# OPENCODE - THROUGH PROXY
# ═══════════════════════════════════════════════════════════════════════════════

osi-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" opencode "$@"
}

osr-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" opencode --resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# OPENCLAW - DIRECT TO HEADROOM
# ═══════════════════════════════════════════════════════════════════════════════

ocl() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw "$@"
}

ocr() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw --resume "$@"
}

ocl-yolo() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw --dangerously-skip-permissions "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# OPENCLAW - THROUGH PROXY
# ═══════════════════════════════════════════════════════════════════════════════

ocl-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" openclaw "$@"
}

ocr-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" openclaw --resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# HERMES - DIRECT TO HEADROOM
# ═══════════════════════════════════════════════════════════════════════════════

hsi() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes "$@"
}

hsr() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes --resume "$@"
}

hsi-yolo() {
    _check_compression || return 1
    OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes --dangerously-skip-permissions "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# HERMES - THROUGH PROXY
# ═══════════════════════════════════════════════════════════════════════════════

hsi-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" hermes "$@"
}

hsr-proxy() {
    _check_proxy || return 1
    ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" hermes --resume "$@"
}

# ═══════════════════════════════════════════════════════════════════════════════
# QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════════════════════
#
# PATTERN: <prefix><action>[-modifier]
#
# PREFIXES:
#   c   = Claude Code          osi/osr = OpenCode
#   q   = Qwen Code            ocl/ocr = OpenClaw
#   codex = Codex CLI          hsi/hsr = Hermes
#   Add -proxy for through proxy path
#
# ACTIONS:
#   si  = Start/Init
#   sr  = Start/Resume (or just 'r' for resume)
#   yolo = dangerously-skip-permissions
#   safe = read-only mode
#
# EXAMPLES:
#   csi          = Claude start (direct to Headroom)
#   csr          = Claude resume (direct)
#   csi-yolo     = Claude YOLO (direct)
#   csi-proxy    = Claude start (through proxy)
#   csr-proxy  = Claude resume (through proxy)
#
# GLOBAL:
#   cs-start     = Start compression (manual)
#   cs-stop      = Stop compression
#   cproxy-start = Start proxy + compression (manual)
#   cproxy-stop  = Stop both
#
# ═══════════════════════════════════════════════════════════════════════════════
# END OF COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════════════════
