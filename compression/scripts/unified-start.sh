#!/usr/bin/env bash
# unified-start.sh - Unified Start/Stop Script
# Starts/stops all compression stack services in correct order
#
# Usage: ./unified-start.sh {start|stop|restart|status}

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Service order matters!
SERVICES=("gpu-resident-manager" "compression-tracker" "compression-dashboard")
HEADROOM_PORT="${HEADROOM_PORT:-8787}"
PROXY_PORT="${PROXY_PORT:-8082}"

cmd_start() {
    log_info "Starting compression stack..."
    
    # 1. Start headroom first (compression layer)
    if ! pgrep -f "headroom proxy" &>/dev/null; then
        log_info "Starting headroom proxy..."
        headroom proxy --port "$HEADROOM_PORT" --mode token_headroom \
            --openai-api-url https://openrouter.ai/api/v1 \
            --backend openrouter --no-telemetry &
        sleep 3
        
        if pgrep -f "headroom proxy" &>/dev/null; then
            log_success "Headroom started on :$HEADROOM_PORT"
        else
            log_error "Failed to start headroom"
            return 1
        fi
    else
        log_warn "Headroom already running"
    fi
    
    # 2. Start systemd services (if available)
    if command -v systemctl &>/dev/null; then
        for service in "${SERVICES[@]}"; do
            if systemctl --user is-enabled "$service" &>/dev/null; then
                systemctl --user start "$service" 2>/dev/null && \
                    log_success "$service started" || \
                    log_warn "$service not available"
            fi
        done
    fi
    
    # 3. Start claude-code-proxy
    local proxy_dir="$HOME/code/claude-code-proxy"
    if [[ -d "$proxy_dir" ]] && ! pgrep -f "start_proxy.py" &>/dev/null; then
        log_info "Starting claude-code-proxy..."
        cd "$proxy_dir"
        
        # Activate venv if exists
        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
        fi
        
        # Set compression env
        export OPENAI_BASE_URL="http://127.0.0.1:$HEADROOM_PORT/v1"
        export PROVIDER_BASE_URL="http://127.0.0.1:$HEADROOM_PORT/v1"
        
        nohup python -u start_proxy.py --skip-validation > proxy.log 2>&1 &
        sleep 3
        
        if pgrep -f "start_proxy.py" &>/dev/null; then
            log_success "Claude Code Proxy started on :$PROXY_PORT"
        else
            log_error "Failed to start claude-code-proxy"
            return 1
        fi
    elif pgrep -f "start_proxy.py" &>/dev/null; then
        log_warn "Claude Code Proxy already running"
    fi
    
    # 4. Health check
    echo ""
    log_info "Health Check:"
    
    # Headroom
    if curl -s "http://127.0.0.1:$HEADROOM_PORT/health" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Headroom (: $HEADROOM_PORT)"
    else
        echo -e "  ${RED}✗${NC} Headroom (: $HEADROOM_PORT)"
    fi
    
    # Proxy
    if curl -s "http://127.0.0.1:$PROXY_PORT/health" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Claude Code Proxy (: $PROXY_PORT)"
    else
        echo -e "  ${RED}✗${NC} Claude Code Proxy (: $PROXY_PORT)"
    fi
    
    # GPU
    if command -v nvidia-smi &>/dev/null; then
        local vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null | head -1)
        echo -e "  ${GREEN}✓${NC} GPU VRAM: $vram"
    fi
    
    echo ""
    log_success "Compression stack started"
    echo ""
    echo "Quick Commands:"
    echo "  cs-health  - Check health status"
    echo "  cs-stats   - View compression stats"
    echo "  csi        - Start Claude with compression"
    echo ""
}

cmd_stop() {
    log_info "Stopping compression stack..."
    
    # 1. Stop claude-code-proxy first
    pkill -f "start_proxy.py" 2>/dev/null && log_success "Claude Code Proxy stopped" || log_warn "Claude Code Proxy not running"
    
    # 2. Stop systemd services
    if command -v systemctl &>/dev/null; then
        for service in "${SERVICES[@]}"; do
            systemctl --user stop "$service" 2>/dev/null || true
        done
        log_success "Systemd services stopped"
    fi
    
    # 3. Stop headroom last
    pkill -f "headroom proxy" 2>/dev/null && log_success "Headroom stopped" || log_warn "Headroom not running"
    
    echo ""
    log_success "Compression stack stopped"
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║        COMPRESSION STACK - STATUS                     ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    # Headroom
    echo -n "Headroom (: $HEADROOM_PORT): "
    if pgrep -f "headroom proxy" &>/dev/null; then
        echo -e "${GREEN}Running${NC}"
        curl -s "http://127.0.0.1:$HEADROOM_PORT/health" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -5 || true
    else
        echo -e "${RED}Not running${NC}"
    fi
    
    echo ""
    
    # Proxy
    echo -n "Claude Code Proxy (: $PROXY_PORT): "
    if pgrep -f "start_proxy.py" &>/dev/null; then
        echo -e "${GREEN}Running${NC}"
        curl -s "http://127.0.0.1:$PROXY_PORT/health" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -3 || true
    else
        echo -e "${RED}Not running${NC}"
    fi
    
    echo ""
    
    # GPU
    echo "GPU Status:"
    if command -v nvidia-smi &>/dev/null; then
        nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "  NVIDIA GPU not detected"
    else
        echo "  nvidia-smi not available"
    fi
    
    echo ""
    
    # Systemd services
    echo "Systemd Services:"
    if command -v systemctl &>/dev/null; then
        for service in "${SERVICES[@]}"; do
            if systemctl --user is-active "$service" &>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $service"
            else
                echo -e "  ${YELLOW}○${NC} $service"
            fi
        done
    else
        echo "  systemctl not available"
    fi
    
    echo ""
}

cmd_health() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║        COMPRESSION STACK - HEALTH CHECK               ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    local healthy=true
    
    # Headroom health
    echo -n "Headroom: "
    if curl -s "http://127.0.0.1:$HEADROOM_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi
    
    # Proxy health
    echo -n "Claude Code Proxy: "
    if curl -s "http://127.0.0.1:$PROXY_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi
    
    # GPU health
    echo -n "GPU: "
    if command -v nvidia-smi &>/dev/null; then
        local vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null | head -1 | tr -d ' MiB')
        if [[ "$vram_used" -gt 100 ]]; then
            echo -e "${GREEN}✓ Active ($vram_used MiB)${NC}"
        else
            echo -e "${YELLOW}○ Idle${NC}"
        fi
    else
        echo -e "${YELLOW}○ Not available${NC}"
    fi
    
    # Compression stats
    echo ""
    echo "Compression Stats:"
    if [[ -f "$HOME/.compression_stats.json" ]]; then
        python3 -c "
import json
with open('$HOME/.compression_stats.json') as f:
    s = json.load(f)['total']
print(f\"  Requests: {s.get('requests', 0):,}\")
print(f\"  Tokens Saved: {s.get('tokens_saved', 0):,}\")
print(f\"  Cost Saved: \${s.get('cost_without', 0) - s.get('cost_with', 0):.4f}\")
" 2>/dev/null || echo "  Stats unavailable"
    else
        echo "  No stats yet"
    fi
    
    echo ""
    
    if $healthy; then
        log_success "All systems healthy"
    else
        log_error "Some systems unhealthy"
        return 1
    fi
}

# Main
case "${1:-status}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|health}"
        exit 1
        ;;
esac
