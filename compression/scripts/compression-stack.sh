#!/usr/bin/env bash
# compression-stack - Unified Control Script
# Usage: compression-stack {start|stop|restart|status|health|mode}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODES_FILE="$SCRIPT_DIR/compression-modes.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Service names
SERVICES=("gpu-resident-manager" "compression-tracker" "compression-dashboard")

cmd_start() {
    log_info "Starting compression stack..."
    
    for service in "${SERVICES[@]}"; do
        systemctl --user start "$service" 2>/dev/null || log_warn "Service $service not available"
    done
    
    # Start headroom if not running
    if ! pgrep -f "headroom proxy" > /dev/null; then
        log_info "Starting headroom proxy..."
        headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry &
        sleep 3
    fi
    
    log_success "Compression stack started"
    cmd_status
}

cmd_stop() {
    log_info "Stopping compression stack..."
    
    for service in "${SERVICES[@]}"; do
        systemctl --user stop "$service" 2>/dev/null || true
    done
    
    log_success "Compression stack stopped"
}

cmd_restart() {
    log_info "Restarting compression stack..."
    
    for service in "${SERVICES[@]}"; do
        systemctl --user restart "$service" 2>/dev/null || true
    done
    
    log_success "Compression stack restarted"
    sleep 2
    cmd_status
}

cmd_status() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║        COMPRESSION STACK - STATUS                     ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if systemctl --user is-active "$service" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $service: Running"
        else
            echo -e "  ${YELLOW}○${NC} $service: Stopped"
        fi
    done
    
    echo ""
    echo -n "  Headroom Proxy: "
    if pgrep -f "headroom proxy" > /dev/null; then
        echo -e "${GREEN}✓${NC} Running"
    else
        echo -e "${YELLOW}○${NC} Stopped"
    fi
    
    echo ""
}

cmd_health() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║        COMPRESSION STACK - HEALTH CHECK               ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    
    # Service health
    echo "📊 Services:"
    for service in "${SERVICES[@]}"; do
        if systemctl --user is-active "$service" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $service"
        else
            echo -e "  ${YELLOW}○${NC} $service (not critical)"
        fi
    done
    
    echo ""
    echo "🔧 Headroom Proxy:"
    if pgrep -f "headroom proxy" > /dev/null; then
        echo -e "  ${GREEN}✓${NC} Running"
        curl -s http://127.0.0.1:8787/health > /dev/null 2>&1 && echo -e "  ${GREEN}✓${NC} Healthy" || echo -e "  ${RED}✗${NC} Unhealthy"
    else
        echo -e "  ${RED}✗${NC} Not running"
    fi
    
    echo ""
    echo "🎮 GPU Status:"
    if command -v nvidia-smi > /dev/null; then
        nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader | while read -r line; do
            echo "  $line"
        done
    else
        echo "  NVIDIA GPU not detected"
    fi
    
    echo ""
    echo "💾 Compression Stats:"
    if [[ -f "$HOME/.compression_stats.json" ]]; then
        python3 -c "
import json
with open('$HOME/.compression_stats.json') as f:
    stats = json.load(f)
total = stats.get('total', {})
print(f\"  Requests: {total.get('requests', 0):,}\")
print(f\"  Tokens Saved: {total.get('tokens_saved', 0):,}\")
print(f\"  Cost Saved: \${total.get('cost_without', 0) - total.get('cost_with', 0):.4f}\")
" 2>/dev/null || echo "  Stats unavailable"
    else
        echo "  No stats yet"
    fi
    
    echo ""
}

cmd_mode() {
    local subcmd="${1:-get}"
    
    case "$subcmd" in
        get)
            if [[ -f "$HOME/.compression-mode" ]]; then
                mode=$(cat "$HOME/.compression-mode")
                echo -e "${CYAN}Current mode:${NC} $mode"
            else
                echo -e "${CYAN}Current mode:${NC} balanced (default)"
            fi
            ;;
        set)
            local new_mode="${2:-balanced}"
            echo "$new_mode" > "$HOME/.compression-mode"
            log_success "Mode set to: $new_mode"
            echo ""
            echo "Apply with: compression-stack apply-mode"
            ;;
        list)
            echo "Available modes:"
            echo "  max-compression  - Maximum savings (98%, 80ms)"
            echo "  balanced         - Best balance (97%, 50ms)"
            echo "  speed            - Minimum latency (90%, 20ms)"
            echo "  free-tier        - Maximize free quota (99%, 50ms)"
            ;;
        *)
            echo "Usage: compression-stack mode {get|set|list}"
            ;;
    esac
}

cmd_apply_mode() {
    if [[ ! -f "$HOME/.compression-mode" ]]; then
        log_warn "No mode set. Use: compression-stack mode set <mode>"
        return 1
    fi
    
    mode=$(cat "$HOME/.compression-mode")
    log_info "Applying mode: $mode"
    
    # Update headroom config based on mode
    case "$mode" in
        max-compression)
            python3 << 'PYEOF'
import json
config = {
    "kompress": {"device": "cuda", "batch_size": 16, "preload": True, "resident": True},
    "cache": {"enabled": True, "max_size_mb": 2000}
}
with open("/home/misscheta/.headroom/config.json", "w") as f:
    json.dump(config, f, indent=2)
PYEOF
            log_success "Applied: MAX COMPRESSION mode"
            ;;
        balanced)
            python3 << 'PYEOF'
import json
config = {
    "kompress": {"device": "cuda", "batch_size": 8, "preload": True, "resident": True},
    "cache": {"enabled": True, "max_size_mb": 1500}
}
with open("/home/misscheta/.headroom/config.json", "w") as f:
    json.dump(config, f, indent=2)
PYEOF
            log_success "Applied: BALANCED mode"
            ;;
        speed)
            python3 << 'PYEOF'
import json
config = {
    "kompress": {"device": "cuda", "batch_size": 4, "preload": True, "resident": True},
    "cache": {"enabled": True, "max_size_mb": 500}
}
with open("/home/misscheta/.headroom/config.json", "w") as f:
    json.dump(config, f, indent=2)
PYEOF
            log_success "Applied: SPEED mode"
            ;;
        free-tier)
            python3 << 'PYEOF'
import json
config = {
    "kompress": {"device": "cuda", "batch_size": 8, "preload": True, "resident": True},
            "compression_thresholds": {"min_tokens": 100},
    "cache": {"enabled": True, "max_size_mb": 1500}
}
with open("/home/misscheta/.headroom/config.json", "w") as f:
    json.dump(config, f, indent=2)
PYEOF
            log_success "Applied: FREE-TIER mode"
            ;;
    esac
    
    # Restart services to apply changes
    cmd_restart
}

cmd_stats() {
    local quick="${1:-false}"
    
    if [[ "$quick" == "--quick" || "$quick" == "-q" ]]; then
        # Quick one-liner stats
        if [[ -f "$HOME/.compression_stats.json" ]]; then
            python3 << 'PYEOF'
import json
from datetime import datetime, timedelta

with open("/home/misscheta/.compression_stats.json") as f:
    stats = json.load(f)

total = stats.get('total', {})
today = datetime.now().strftime("%Y-%m-%d")
daily = stats.get('daily', {}).get(today, {})

tokens_saved = total.get('tokens_saved', 0)
cost_saved = total.get('cost_without', 0) - total.get('cost_with', 0)
requests = total.get('requests', 0)

if tokens_saved > 1000000:
    tokens_str = f"{tokens_saved/1000000:.1f}M"
elif tokens_saved > 1000:
    tokens_str = f"{tokens_saved/1000:.0f}K"
else:
    tokens_str = str(tokens_saved)

print(f"💰 Saved \${cost_saved:.2f} today ({tokens_str} tokens, {requests} requests)")
PYEOF
        else
            echo "💰 No stats yet - start using compression!"
        fi
    else
        # Full stats - launch dashboard
        python3 "$SCRIPT_DIR/compression-dashboard.py"
    fi
}

cmd_help() {
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║        COMPRESSION STACK - HELP                       ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo "Usage: compression-stack <command> [options]"
    echo ""
    echo "Commands:"
    echo "  start       Start all compression services"
    echo "  stop        Stop all compression services"
    echo "  restart     Restart all compression services"
    echo "  status      Show service status"
    echo "  health      Full health check with stats"
    echo "  mode        Manage compression modes"
    echo "    get       Show current mode"
    echo "    set       Set mode (max-compression|balanced|speed|free-tier)"
    echo "    list      List available modes"
    echo "  apply-mode  Apply the selected mode"
    echo "  stats       View compression statistics"
    echo "    --quick   Quick one-liner stats"
    echo ""
    echo "Quick Aliases:"
    echo "  cs-start    Start compression stack"
    echo "  cs-stop     Stop compression stack"
    echo "  cs-status   Show status"
    echo "  cs-health   Health check"
    echo "  cs-max      Set max-compression mode"
    echo "  cs-balanced Set balanced mode"
    echo "  cs-speed    Set speed mode"
    echo "  cs-stats    Quick stats"
    echo ""
}

# Main command handler
case "${1:-help}" in
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
    mode)
        shift
        cmd_mode "$@"
        ;;
    apply-mode)
        cmd_apply_mode
        ;;
    stats)
        shift
        cmd_stats "$@"
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
