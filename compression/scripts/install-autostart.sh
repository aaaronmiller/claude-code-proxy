#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESSION STACK - AUTO-START INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
#
# Sets up systemd services to auto-start compression stack on boot
# Aliases become instant after installation
#
# Usage: ./install-autostart.sh
# ═══════════════════════════════════════════════════════════════════════════════

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

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     COMPRESSION STACK - AUTO-START INSTALLER                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check systemd
if ! command -v systemctl &>/dev/null; then
    log_error "systemctl not found. This script only works with systemd."
    log_info "For non-systemd systems, add cs-start to your shell rc file."
    exit 1
fi

# Create service directory
log_info "Creating service directory..."
mkdir -p ~/.config/systemd/user

# Install Headroom service
log_info "Installing Headroom service..."
cat > ~/.config/systemd/user/headroom.service << 'EOF'
[Unit]
Description=Headroom Compression Proxy
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
log_success "Headroom service installed"

# Install Claude Proxy service (optional)
log_info "Installing Claude Proxy service..."
cat > ~/.config/systemd/user/claude-proxy.service << 'EOF'
[Unit]
Description=Claude Code Proxy
After=network.target headroom.service

[Service]
Type=simple
WorkingDirectory=%h/code/claude-code-proxy
Environment="OPENAI_BASE_URL=http://127.0.0.1:8787/v1"
ExecStart=%h/code/claude-code-proxy/.venv/bin/python start_proxy.py --skip-validation
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
log_success "Claude Proxy service installed"

# Enable linger (start services even when user not logged in)
log_info "Enabling user linger..."
if sudo loginctl show-user "$USER" | grep -q "Linger=no"; then
    sudo loginctl enable-linger "$USER"
    log_success "User linger enabled"
else
    log_info "User linger already enabled"
fi

# Reload systemd
log_info "Reloading systemd daemon..."
systemctl --user daemon-reload
log_success "Daemon reloaded"

# Enable services
log_info "Enabling services..."
systemctl --user enable headroom
systemctl --user enable claude-proxy
log_success "Services enabled"

# Start services
log_info "Starting services..."
systemctl --user start headroom
systemctl --user start claude-proxy
log_success "Services started"

# Verify
echo ""
log_info "Verifying installation..."
sleep 2

if systemctl --user is-active headroom &>/dev/null; then
    log_success "Headroom is running"
else
    log_error "Headroom failed to start"
fi

if systemctl --user is-active claude-proxy &>/dev/null; then
    log_success "Claude Proxy is running"
else
    log_warn "Claude Proxy failed to start (optional)"
fi

# Test aliases
echo ""
log_info "Testing aliases..."
if command -v csi &>/dev/null; then
    log_success "Aliases available"
else
    log_warn "Aliases not installed. Run install-aliases.sh first."
fi

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Services:"
echo "  ✅ Headroom (compression) - auto-starts on boot"
echo "  ✅ Claude Proxy - auto-starts on boot"
echo ""
echo "Usage:"
echo "  csi          - Instant Claude with compression"
echo "  csr          - Instant Claude resume"
echo "  qsi          - Instant Qwen with compression"
echo "  cs-status    - Check compression status"
echo ""
echo "Manual control:"
echo "  cs-start     - Start compression"
echo "  cs-stop      - Stop compression"
echo "  cproxy-start - Start proxy + compression"
echo ""
echo "Service management:"
echo "  systemctl --user status headroom"
echo "  systemctl --user status claude-proxy"
echo "  journalctl --user -u headroom -f"
echo ""
echo "Aliases are now INSTANT! 🚀"
echo ""
