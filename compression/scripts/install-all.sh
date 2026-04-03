#!/usr/bin/env bash
# install-all.sh - Unified Installation Script
# Installs claude-code-proxy, headroom, RTK, and configures them to work together
#
# Usage: curl -fsSL https://raw.githubusercontent.com/.../install-all.sh | bash
# Or: ./install-all.sh

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
echo "║         COMPRESSION STACK - UNIFIED INSTALLER                       ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Detect OS
OS="$(uname -s)"
log_info "Detected OS: $OS"

# Check prerequisites
check_prereqs() {
    log_info "Checking prerequisites..."
    
    local missing=()
    
    # Python
    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    fi
    
    # Git
    if ! command -v git &>/dev/null; then
        missing+=("git")
    fi
    
    # Node.js (for claude-code-proxy web UI)
    if ! command -v node &>/dev/null; then
        log_warn "Node.js not found - web UI may not work"
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing: ${missing[*]}"
        log_info "Install with: sudo apt install ${missing[*]}  # Debian/Ubuntu"
        return 1
    fi
    
    log_success "Prerequisites met"
}

# Install headroom
install_headroom() {
    log_info "Installing Headroom..."
    
    if command -v headroom &>/dev/null; then
        log_warn "Headroom already installed"
    else
        pip install --user "headroom-ai[ml]" && log_success "Headroom installed" || {
            log_error "Headroom installation failed"
            return 1
        }
    fi
}

# Install RTK
install_rtk() {
    log_info "Installing RTK..."
    
    if command -v rtk &>/dev/null; then
        log_warn "RTK already installed"
    else
        # Check if rtk is available
        if command -v cargo &>/dev/null; then
            cargo install rtk 2>/dev/null && log_success "RTK installed" || {
                log_warn "RTK installation via cargo failed, trying pip..."
                pip install --user rtk 2>/dev/null && log_success "RTK installed" || {
                    log_warn "RTK not available - skipping"
                }
            }
        else
            log_warn "Cargo not found - skipping RTK installation"
        fi
    fi
}

# Install claude-code-proxy
install_claude_proxy() {
    log_info "Installing Claude Code Proxy..."

    local proxy_dir="$HOME/code/claude-code-proxy"

    if [[ -d "$proxy_dir" ]]; then
        log_info "✅ Claude Code Proxy already exists at $proxy_dir"
        log_info "Checking for compression layer..."

        if [[ -d "$proxy_dir/compression" ]]; then
            log_warn "Compression layer already installed"
            read -p "Update compression layer? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cd "$proxy_dir" && git pull && log_success "Compression layer updated"
            fi
        else
            log_info "Adding compression layer to existing installation..."
            # The compression/ directory should already exist if running this script from the repo
            if [[ -d "compression" ]]; then
                log_success "✅ Compression layer found in current directory"
            else
                log_warn "Compression layer not found - skipping"
            fi
        fi
    else
        log_info "Fresh installation..."
        git clone https://github.com/aaaronmiller/claude-code-proxy.git "$proxy_dir" && \
            log_success "Claude Code Proxy installed" || {
            log_error "Claude Code Proxy installation failed"
            return 1
        }
    fi
}

# Install input-compression
install_input_compression() {
    log_info "Installing Input Compression..."
    
    local comp_dir="$HOME/code/input-compression"
    
    if [[ -d "$comp_dir" ]]; then
        log_warn "Input Compression already exists at $comp_dir"
    else
        git clone https://github.com/aaaronmiller/input-compression.git "$comp_dir" && \
            log_success "Input Compression installed" || {
            log_error "Input Compression installation failed"
            return 1
        }
    fi
}

# Configure integration
configure_integration() {
    log_info "Configuring integration..."
    
    # Add compression aliases
    local aliases_file="$HOME/code/input-compression/scripts/compression-aliases.zsh"
    if [[ -f "$aliases_file" ]]; then
        if ! grep -q "compression-stack.sh" ~/.zshrc 2>/dev/null; then
            cat "$aliases_file" >> ~/.zshrc && \
                log_success "Aliases added to ~/.zshrc" || {
                log_warn "Failed to add aliases - add manually"
            }
        else
            log_warn "Aliases already in ~/.zshrc"
        fi
    fi
    
    # Configure claude-code-proxy to use headroom
    local proxy_envrc="$HOME/code/claude-code-proxy/.envrc"
    if [[ -f "$proxy_envrc" ]]; then
        if ! grep -q "HEADROOM_PORT" "$proxy_envrc" 2>/dev/null; then
            echo "" >> "$proxy_envrc"
            echo "# Compression stack integration" >> "$proxy_envrc"
            echo "export OPENAI_BASE_URL=\"http://127.0.0.1:8787/v1\"" >> "$proxy_envrc"
            log_success "Claude Code Proxy configured for headroom"
        fi
    fi
    
    # Install systemd services
    if command -v systemctl &>/dev/null; then
        log_info "Installing systemd services..."
        
        local services_dir="$HOME/.config/systemd/user"
        mkdir -p "$services_dir"
        
        # Copy service files
        if [[ -f "$HOME/code/input-compression/scripts/gpu-resident-manager.service" ]]; then
            cp "$HOME/code/input-compression/scripts/gpu-resident-manager.service" "$services_dir/" && \
                log_success "GPU resident manager service installed"
        fi
        
        systemctl --user daemon-reload 2>/dev/null || true
    fi
}

# Start all services
start_services() {
    log_info "Starting services..."
    
    # Start headroom
    if command -v headroom &>/dev/null; then
        if ! pgrep -f "headroom proxy" &>/dev/null; then
            headroom proxy --port 8787 --mode token_headroom \
                --openai-api-url https://openrouter.ai/api/v1 \
                --backend openrouter --no-telemetry &
            sleep 3
            log_success "Headroom started on :8787"
        else
            log_warn "Headroom already running"
        fi
    fi
    
    # Start claude-code-proxy
    local proxy_dir="$HOME/code/claude-code-proxy"
    if [[ -d "$proxy_dir" ]]; then
        if ! pgrep -f "start_proxy.py" &>/dev/null; then
            cd "$proxy_dir" && source .venv/bin/activate 2>/dev/null && \
                python start_proxy.py --skip-validation &
            sleep 3
            log_success "Claude Code Proxy started on :8082"
        else
            log_warn "Claude Code Proxy already running"
        fi
    fi
    
    # Show status
    echo ""
    log_info "Service Status:"
    pgrep -f "headroom proxy" &>/dev/null && echo -e "  ${GREEN}✓${NC} Headroom (:8787)" || echo -e "  ${RED}✗${NC} Headroom"
    pgrep -f "start_proxy.py" &>/dev/null && echo -e "  ${GREEN}✓${NC} Claude Code Proxy (:8082)" || echo -e "  ${RED}✗${NC} Claude Code Proxy"
    command -v rtk &>/dev/null && echo -e "  ${GREEN}✓${NC} RTK" || echo -e "  ${YELLOW}○${NC} RTK (not installed)"
}

# Show usage info
show_usage() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                    INSTALLATION COMPLETE                             ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Quick Start:"
    echo "  cs-start     - Start all compression services"
    echo "  cs-stop      - Stop all services"
    echo "  cs-health    - Check health status"
    echo "  csi          - Start Claude with compression"
    echo "  csr          - Resume Claude with compression"
    echo ""
    echo "Documentation:"
    echo "  ~/code/input-compression/README.md"
    echo "  ~/code/claude-code-proxy/README.md"
    echo ""
    echo "Next Steps:"
    echo "  1. Run: source ~/.zshrc"
    echo "  2. Run: cs-start"
    echo "  3. Run: csi  (to start Claude with compression)"
    echo ""
}

# Main
main() {
    check_prereqs || exit 1
    install_headroom
    install_rtk
    install_claude_proxy
    install_input_compression
    configure_integration
    start_services
    show_usage
}

main "$@"
