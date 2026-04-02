#!/usr/bin/env bash
# Full Stack Debug Script - Monitors entire request pathway
# Usage: ./debug-full-stack.sh

set -euo pipefail

PROXY_DIR="${CLAUDE_CODE_PROXY_DIR:-$HOME/code/claude-code-proxy}"
HEADROOM_LOG_DIR="$HOME/.local/share/headroom"
PROXY_LOG="$PROXY_DIR/debug-proxy.log"
HEADROOM_DEFAULT_LOG="$HEADROOM_LOG_DIR/proxy-default.jsonl"
HEADROOM_SMALL_LOG="$HEADROOM_LOG_DIR/proxy-small.jsonl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "========================================"
echo "  CLAUDE CODE PROXY - FULL STACK DEBUG"
echo "========================================"
echo ""

# Step 1: Kill existing processes
log_info "Step 1: Cleaning up existing processes..."
pkill -f "headroom proxy" 2>/dev/null || true
pkill -f "start_proxy.py" 2>/dev/null || true
sleep 2
log_success "Cleared old processes"

# Step 2: Start headroom with compression ENABLED
log_info "Step 2: Starting headroom proxies (compression ENABLED)..."

# Default tier (BIG/MIDDLE models) - compression ON
nohup headroom proxy \
    --port 8787 \
    --mode token_headroom \
    --openai-api-url https://openrouter.ai/api/v1 \
    --log-file "$HEADROOM_DEFAULT_LOG" \
    --no-telemetry \
    > "$HEADROOM_LOG_DIR/headroom-default.out" 2>&1 &
DEFAULT_PID=$!

# SMALL tier (NVIDIA models) - compression ON
nohup headroom proxy \
    --port 8790 \
    --mode token_headroom \
    --openai-api-url https://integrate.api.nvidia.com/v1 \
    --log-file "$HEADROOM_SMALL_LOG" \
    --no-telemetry \
    > "$HEADROOM_LOG_DIR/headroom-small.out" 2>&1 &
SMALL_PID=$!

sleep 4

# Verify headroom is running
if kill -0 $DEFAULT_PID 2>/dev/null; then
    log_success "Headroom default (8787) started - PID: $DEFAULT_PID"
else
    log_error "Headroom default (8787) FAILED to start!"
    cat "$HEADROOM_LOG_DIR/headroom-default.out"
    exit 1
fi

if kill -0 $SMALL_PID 2>/dev/null; then
    log_success "Headroom small (8790) started - PID: $SMALL_PID"
else
    log_error "Headroom small (8790) FAILED to start!"
    cat "$HEADROOM_LOG_DIR/headroom-small.out"
    exit 1
fi

# Check headroom health
log_info "Checking headroom health..."
sleep 2
DEFAULT_HEALTH=$(curl -s http://127.0.0.1:8787/health 2>/dev/null || echo "FAILED")
SMALL_HEALTH=$(curl -s http://127.0.0.1:8790/health 2>/dev/null || echo "FAILED")

if [[ "$DEFAULT_HEALTH" == *"optimize\":true"* ]]; then
    log_success "Headroom default: Compression ENABLED ✓"
else
    log_warn "Headroom default: $DEFAULT_HEALTH"
fi

if [[ "$SMALL_HEALTH" == *"optimize\":true"* ]]; then
    log_success "Headroom small: Compression ENABLED ✓"
else
    log_warn "Headroom small: $SMALL_HEALTH"
fi

# Step 3: Start claude-code-proxy
log_info "Step 3: Starting claude-code-proxy..."

cd "$PROXY_DIR"
source .venv/bin/activate

OPENAI_BASE_URL="http://127.0.0.1:8787/v1" \
PROVIDER_BASE_URL="http://127.0.0.1:8787/v1" \
nohup python -u start_proxy.py --skip-validation \
    > "$PROXY_LOG" 2>&1 &
PROXY_PID=$!

sleep 5

if kill -0 $PROXY_PID 2>/dev/null; then
    log_success "Claude Code Proxy (8082) started - PID: $PROXY_PID"
else
    log_error "Claude Code Proxy FAILED to start!"
    tail -50 "$PROXY_LOG"
    exit 1
fi

# Check proxy health
PROXY_HEALTH=$(curl -s http://127.0.0.1:8082/health 2>/dev/null || echo "FAILED")
if [[ "$PROXY_HEALTH" == *"healthy"* ]]; then
    log_success "Proxy health check: PASSED ✓"
else
    log_error "Proxy health check: FAILED"
    echo "$PROXY_HEALTH"
    exit 1
fi

# Step 4: Show monitoring dashboard
echo ""
echo "========================================"
echo "  MONITORING DASHBOARD (Live)"
echo "========================================"
echo ""
echo "Process Tree:"
echo "  Claude Code → Proxy :8082 (PID: $PROXY_PID)"
echo "              → Headroom :8787 (PID: $DEFAULT_PID) → OpenRouter"
echo "              → Headroom :8790 (PID: $SMALL_PID) → NVIDIA"
echo ""
echo "Log Files:"
echo "  Proxy:     $PROXY_LOG"
echo "  Headroom:  $HEADROOM_DEFAULT_LOG"
echo "  Small:     $HEADROOM_SMALL_LOG"
echo ""
echo "Quick Commands:"
echo "  tail -f $PROXY_LOG           # Proxy logs"
echo "  tail -f $HEADROOM_DEFAULT_LOG # Headroom logs"
echo "  curl http://127.0.0.1:8082/health"
echo ""
echo "========================================"
echo ""

# Step 5: Start live monitoring
log_info "Starting live request monitoring (Ctrl+C to stop)..."
echo ""

# Create a temp file for the monitoring output
MONITOR_OUTPUT=$(mktemp)

# Function to cleanup on exit
cleanup() {
    echo ""
    log_info "Stopping monitor..."
    rm -f "$MONITOR_OUTPUT"
    exit 0
}
trap cleanup EXIT INT TERM

# Monitor all logs in parallel
{
    echo "=== PROXY LOGS ==="
    tail -n 20 -f "$PROXY_LOG" 2>/dev/null | while read -r line; do
        if [[ "$line" == *"ERROR"* ]]; then
            echo -e "${RED}[PROXY ERROR]${NC} $(date '+%H:%M:%S') $line"
        elif [[ "$line" == *"POST"* ]]; then
            echo -e "${GREEN}[PROXY REQ]${NC} $(date '+%H:%M:%S') $line"
        elif [[ "$line" == *"200 OK"* ]]; then
            echo -e "${BLUE}[PROXY OK]${NC} $(date '+%H:%M:%S') $line"
        fi
    done
} &

{
    echo ""
    echo "=== HEADROOM LOGS ==="
    tail -n 10 -f "$HEADROOM_DEFAULT_LOG" 2>/dev/null | while read -r line; do
        if [[ -n "$line" ]]; then
            echo -e "${YELLOW}[HEADROOM]${NC} $(date '+%H:%M:%S') $line"
        fi
    done
} &

# Wait for background processes
wait
