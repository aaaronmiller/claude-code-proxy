#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESSION STACK - ALIAS INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
#
# Portable script to install compression aliases on any machine.
# Adapts to any user - no hardcoded paths or usernames.
#
# Usage:
#   Option 1: Run directly from repo
#     ./compression/scripts/install-aliases.sh
#
#   Option 2: Pipe from repo URL
#     curl -fsSL https://raw.githubusercontent.com/USER/REPO/main/compression/scripts/install-aliases.sh | bash
#
#   Option 3: Add to existing ~/.zshrc manually
#     echo 'source /path/to/compression/scripts/compression-aliases.zsh' >> ~/.zshrc
#
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

# Detect shell config file
detect_shell_rc() {
    local shell_name="${SHELL##*/}"
    case "$shell_name" in
        zsh)  echo "$HOME/.zshrc" ;;
        bash) echo "$HOME/.bashrc" ;;
        *)    echo "$HOME/.zshrc" ;;  # Default to zsh
    esac
}

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIAS_FILE="${SCRIPT_DIR}/compression-aliases.zsh"
RC_FILE="$(detect_shell_rc)"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         COMPRESSION STACK - ALIAS INSTALLER                         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Shell: ${SHELL##*/}"
log_info "Config file: $RC_FILE"
log_info "Alias file: $ALIAS_FILE"
echo ""

# Check if alias file exists
if [[ ! -f "$ALIAS_FILE" ]]; then
    log_error "Alias file not found: $ALIAS_FILE"
    log_info "Make sure you're running this from the repository"
    exit 1
fi

# Check if already installed
if [[ -f "$RC_FILE" ]] && grep -q "COMPRESSION STACK ALIASES" "$RC_FILE" 2>/dev/null; then
    log_warn "Compression aliases already installed in $RC_FILE"
    echo ""
    read -p "Reinstall? This will replace existing aliases. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    # Remove existing aliases
    log_info "Removing existing compression aliases..."
    python3 -c "
import re
with open('$RC_FILE', 'r') as f:
    content = f.read()
content = re.sub(r'\n# ═*COMPRESSION.*?END COMPRESSION.*?\n', '\n', content, flags=re.DOTALL)
content = re.sub(r'\n{3,}', '\n\n', content)
with open('$RC_FILE', 'w') as f:
    f.write(content)
" 2>/dev/null || true
    log_success "Removed existing aliases"
fi

# Create rc file if it doesn't exist
if [[ ! -f "$RC_FILE" ]]; then
    log_info "Creating $RC_FILE..."
    touch "$RC_FILE"
fi

# Add aliases to shell config
log_info "Installing compression aliases to $RC_FILE..."

cat >> "$RC_FILE" << 'ALIASES'

# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════

# Global compression control
alias cs-start='headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry > /dev/null 2>&1 & sleep 2; pgrep -f "headroom proxy" > /dev/null 2>&1 && echo "✅ Compression started" || echo "❌ Failed"'
alias cs-stop='pkill -f "headroom proxy" 2>/dev/null; echo "⏹️  Compression stopped"'
alias cs-restart='cs-stop && sleep 2 && cs-start'
alias cs-status='pgrep -f "headroom proxy" > /dev/null 2>&1 && echo "✅ Compression: Running" || echo "❌ Compression: Not running"'
alias cs-health='curl -s http://127.0.0.1:8787/health > /dev/null 2>&1 && echo "✅ Headroom: Healthy" || echo "❌ Headroom: Unhealthy"'

# Claude Code
alias csi='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude'
alias csr='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --resume'
alias csi-yolo='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude --dangerously-skip-permissions'
alias csi-proxy='ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude'
alias csr-proxy='ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --resume'
alias csi-proxy-yolo='ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" claude --dangerously-skip-permissions'

# Qwen Code
alias qsi='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen'
alias qsr='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen --resume'
alias qsi-yolo='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" qwen --dangerously-skip-permissions'
alias qsi-proxy='ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" qwen'
alias qsr-proxy='ANTHROPIC_BASE_URL="http://127.0.0.1:8082" ANTHROPIC_API_KEY="pass" qwen --resume'

# Codex
alias csi-codex='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex'
alias csr-codex='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex resume'
alias csi-codex-yolo='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" codex --dangerously-skip-permissions'

# OpenCode
alias osi='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" opencode'
alias osr='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" opencode --resume'

# OpenClaw
alias ocl='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw'
alias ocr='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw --resume'
alias ocl-yolo='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" openclaw --dangerously-skip-permissions'

# Hermes
alias hsi='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes'
alias hsr='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes --resume'
alias hsi-yolo='OPENAI_BASE_URL="http://127.0.0.1:8787/v1" hermes --dangerously-skip-permissions'

# ═══════════════════════════════════════════════════════════════════
# END COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════
ALIASES

log_success "Aliases installed to $RC_FILE"

# Check if we can source the file (only if running interactively)
if [[ -n "${ZSH_VERSION:-}" ]]; then
    log_info "Detected Zsh - reloading config..."
    source "$RC_FILE" 2>/dev/null || true
    log_success "Config reloaded"
elif [[ -n "${BASH_VERSION:-}" ]]; then
    log_info "Detected Bash - reloading config..."
    source "$RC_FILE" 2>/dev/null || true
    log_success "Config reloaded"
else
    log_info "Please reload your shell: source $RC_FILE"
fi

# Show quick reference
echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Global:"
echo "  cs-start     - Start compression"
echo "  cs-stop      - Stop compression"
echo "  cs-status    - Check status"
echo ""
echo "Claude Code:"
echo "  csi          - Start (direct to Headroom)"
echo "  csr          - Resume"
echo "  csi-yolo     - Start (YOLO mode)"
echo ""
echo "Qwen Code:"
echo "  qsi          - Start"
echo "  qsr          - Resume"
echo "  qsi-yolo     - YOLO mode"
echo ""
echo "Other CLIs:"
echo "  csi-codex    - Codex"
echo "  osi          - OpenCode"
echo "  ocl          - OpenClaw"
echo "  hsi          - Hermes"
echo ""
