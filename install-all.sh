#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE PROXY - UNIFIED INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
# Installs Claude Code Proxy with full compression stack integration
# Includes: claude-code-proxy, Headroom, RTK, and all compression tools
#
# Usage: curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/install-all.sh | bash
# Or: ./install-all.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Configuration
PROXY_DIR="${HOME}/code/claude-code-proxy"
COMPRESSION_DIR="${PROXY_DIR}/compression"
HEADROOM_PORT="${HEADROOM_PORT:-8787}"
PROXY_PORT="${PROXY_PORT:-8082}"

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
log_header() { echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}\n"; }

# Check prerequisites
check_prereqs() {
    log_header "CHECKING PREREQUISITES"
    
    local missing=()
    
    # Python 3.9+
    if command -v python3 &>/dev/null; then
        local pyver=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
            log_success "Python 3.9+ detected ($pyver)"
        else
            log_error "Python 3.9+ required (found $pyver)"
            missing+=("python3.9+")
        fi
    else
        missing+=("python3")
    fi
    
    # Git
    if command -v git &>/dev/null; then
        log_success "Git detected"
    else
        missing+=("git")
    fi
    
    # pip
    if command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
        log_success "pip detected"
    else
        missing+=("pip")
    fi
    
    # Check OS
    local os="$(uname -s)"
    log_info "Detected OS: $os"
    
    # Optional dependencies
    if command -v node &>/dev/null; then
        log_success "Node.js detected (web UI support)"
    else
        log_warn "Node.js not found - web UI may not work"
    fi
    
    if command -v cargo &>/dev/null; then
        log_success "Cargo detected (RTK installation)"
    else
        log_warn "Cargo not found - will use pip for RTK"
    fi
    
    if command -v nvidia-smi &>/dev/null; then
        log_success "NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | while read -r line; do
            echo -e "  ${GREEN}✓${NC} GPU: $line"
        done
    else
        log_warn "No NVIDIA GPU detected - will use CPU mode"
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing prerequisites: ${missing[*]}"
        if [[ "$os" == "Linux" ]]; then
            log_info "Install with: sudo apt install ${missing[*]}"
        elif [[ "$os" == "Darwin" ]]; then
            log_info "Install with: brew install ${missing[*]}"
        fi
        return 1
    fi
    
    log_success "All prerequisites met"
}

# Clone claude-code-proxy
clone_proxy() {
    log_header "CLONING CLAUDE CODE PROXY"
    
    if [[ -d "$PROXY_DIR" ]]; then
        log_warn "Claude Code Proxy already exists at $PROXY_DIR"
        read -p "Update existing installation? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$PROXY_DIR" && git pull && log_success "Claude Code Proxy updated"
        fi
    else
        log_info "Cloning claude-code-proxy..."
        git clone https://github.com/aaaronmiller/claude-code-proxy.git "$PROXY_DIR" && \
            log_success "Claude Code Proxy installed" || {
            log_error "Failed to clone claude-code-proxy"
            return 1
        }
    fi
}

# Install Headroom (as git submodule or pip)
install_headroom() {
    log_header "INSTALLING HEADROOM"
    
    # Try git clone first (for development)
    local headroom_dir="${COMPRESSION_DIR}/headroom"
    if [[ ! -d "$headroom_dir" ]]; then
        log_info "Cloning headroom..."
        if git clone https://github.com/chopratejas/headroom.git "$headroom_dir" 2>/dev/null; then
            log_success "Headroom cloned"
        else
            log_warn "Headroom clone failed - will install via pip"
        fi
    fi
    
    # Install via pip
    if command -v headroom &>/dev/null; then
        log_warn "Headroom already installed"
    else
        log_info "Installing headroom-ai[ml]..."
        pip install --user "headroom-ai[ml]" && log_success "Headroom installed" || {
            log_error "Headroom installation failed"
            return 1
        }
    fi
}

# Install RTK (as git submodule or cargo/pip)
install_rtk() {
    log_header "INSTALLING RTK"
    
    # Try git clone first
    local rtk_dir="${COMPRESSION_DIR}/rtk"
    if [[ ! -d "$rtk_dir" ]]; then
        log_info "Cloning rtk..."
        if git clone https://github.com/rtk-ai/rtk.git "$rtk_dir" 2>/dev/null; then
            log_success "RTK cloned"
        else
            log_warn "RTK clone failed - will install via package manager"
        fi
    fi
    
    # Install via cargo or pip
    if command -v rtk &>/dev/null; then
        log_warn "RTK already installed"
    elif command -v cargo &>/dev/null; then
        log_info "Installing RTK via cargo..."
        cargo install rtk 2>/dev/null && log_success "RTK installed" || {
            log_warn "Cargo installation failed - trying pip"
            pip install --user rtk 2>/dev/null && log_success "RTK installed" || {
                log_warn "RTK not available - skipping"
            }
        }
    else
        log_info "Installing RTK via pip..."
        pip install --user rtk 2>/dev/null && log_success "RTK installed" || log_warn "RTK installation failed"
    fi
}

# Install Python dependencies
install_dependencies() {
    log_header "INSTALLING DEPENDENCIES"
    
    cd "$PROXY_DIR"
    
    # Create virtual environment
    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv && log_success "Virtual environment created"
    else
        log_warn "Virtual environment already exists"
    fi
    
    # Activate and install
    source .venv/bin/activate
    log_info "Installing Python dependencies..."
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt && log_success "Dependencies installed" || {
            log_error "Dependency installation failed"
            return 1
        }
    else
        log_warn "requirements.txt not found"
    fi
}

# Configure integration
configure_integration() {
    log_header "CONFIGURING INTEGRATION"
    
    # Configure claude-code-proxy to use headroom
    local envrc="${PROXY_DIR}/.envrc"
    if [[ -f "$envrc" ]]; then
        if ! grep -q "HEADROOM_PORT" "$envrc" 2>/dev/null; then
            log_info "Configuring compression integration..."
            cat >> "$envrc" << 'EOF'

# Compression stack integration
export OPENAI_BASE_URL="http://127.0.0.1:8787/v1"
export PROVIDER_BASE_URL="http://127.0.0.1:8787/v1"
export HEADROOM_PORT="8787"
EOF
            log_success "Environment configured"
        else
            log_warn "Environment already configured"
        fi
    fi
    
    # Add compression aliases
    local aliases_file="${COMPRESSION_DIR}/scripts/compression-aliases.zsh"
    if [[ -f "$aliases_file" ]]; then
        if ! grep -q "compression-stack.sh" ~/.zshrc 2>/dev/null; then
            log_info "Adding compression aliases..."
            cat "$aliases_file" >> ~/.zshrc && log_success "Aliases added to ~/.zshrc" || {
                log_warn "Failed to add aliases - add manually"
            }
        else
            log_warn "Aliases already in ~/.zshrc"
        fi
    fi
    
    # Install systemd services
    if command -v systemctl &>/dev/null; then
        log_info "Installing systemd services..."
        
        local services_dir="$HOME/.config/systemd/user"
        mkdir -p "$services_dir"
        
        # Copy service files
        if [[ -d "${COMPRESSION_DIR}/systemd" ]]; then
            for service in "${COMPRESSION_DIR}/systemd/"*.service; do
                if [[ -f "$service" ]]; then
                    cp "$service" "$services_dir/" && \
                        log_success "Installed $(basename "$service")"
                fi
            done
            
            systemctl --user daemon-reload 2>/dev/null && log_success "Systemd reloaded" || true
        fi
    else
        log_warn "systemctl not available - skipping systemd installation"
    fi
}

# Start all services
start_services() {
    log_header "STARTING SERVICES"
    
    # Start headroom
    if command -v headroom &>/dev/null; then
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
    fi
    
    # Start claude-code-proxy
    cd "$PROXY_DIR"
    if ! pgrep -f "start_proxy.py" &>/dev/null; then
        log_info "Starting claude-code-proxy..."
        
        # Activate venv
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
    else
        log_warn "Claude Code Proxy already running"
    fi
}

# Show health status
show_health() {
    log_header "HEALTH CHECK"
    
    local healthy=true
    
    # Headroom
    echo -n "Headroom (: $HEADROOM_PORT): "
    if curl -s "http://127.0.0.1:$HEADROOM_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi
    
    # Proxy
    echo -n "Claude Code Proxy (: $PROXY_PORT): "
    if curl -s "http://127.0.0.1:$PROXY_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi
    
    # GPU
    echo -n "GPU: "
    if command -v nvidia-smi &>/dev/null; then
        local vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null | head -1)
        if [[ -n "$vram" ]]; then
            echo -e "${GREEN}✓ Active ($vram)${NC}"
        else
            echo -e "${YELLOW}○ Idle${NC}"
        fi
    else
        echo -e "${YELLOW}○ Not available${NC}"
    fi
    
    echo ""
    if $healthy; then
        log_success "All systems healthy"
    else
        log_error "Some systems unhealthy"
        return 1
    fi
}

# Show completion message
show_completion() {
    log_header "INSTALLATION COMPLETE"
    
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════╗
║                    INSTALLATION SUCCESSFUL                           ║
╚══════════════════════════════════════════════════════════════════════╝

Quick Start:
  source ~/.zshrc
  cs-start         # Start compression stack
  csi              # Start Claude with compression
  cs-stats-quick   # View quick stats
  cs-health        # Check health status

Documentation:
  ~/code/claude-code-proxy/README.md
  ~/code/claude-code-proxy/compression/PHASE-1-COMPLETE.md

Compression Stack:
  Headroom:  http://127.0.0.1:8787/health
  Proxy:     http://127.0.0.1:8082/health
  Dashboard: python3 ~/code/claude-code-proxy/compression/scripts/compression-dashboard.py --web

Modes:
  cs-max       # Maximum compression (98%, 80ms)
  cs-balanced  # Balanced (97%, 50ms) ← DEFAULT
  cs-speed     # Speed mode (90%, 20ms)
  cs-free      # Free tier mode (99%, 50ms)

Low-VRAM / No-GPU Support:
  Edit ~/code/claude-code-proxy/compression/scripts/gpu-resident-manager.py
  Set: device='cpu' for CPU-only mode
  Set: batch_size=4 for 5GB GPU mode

═══════════════════════════════════════════════════════════════════════
EOF
}

# Main installation function
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║         CLAUDE CODE PROXY - UNIFIED INSTALLER                        ║"
    echo "║         Compression Stack + Headroom + RTK                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prereqs || exit 1
    clone_proxy
    install_headroom
    install_rtk
    install_dependencies
    configure_integration
    start_services
    show_health
    show_completion
}

# Run main function
main "$@"
