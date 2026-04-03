#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES - AUTO-INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════
#
# Usage: curl -fsSL <url> | bash
# Or: ./install-aliases.sh
#
# This script adds compression stack aliases to your shell configuration.
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

# Detect shell
SHELL_NAME="${SHELL##*/}"
if [[ "$SHELL_NAME" == "zsh" ]]; then
    RC_FILE="$HOME/.zshrc"
elif [[ "$SHELL_NAME" == "bash" ]]; then
    RC_FILE="$HOME/.bashrc"
else
    log_warn "Unsupported shell: $SHELL_NAME (trying .zshrc anyway)"
    RC_FILE="$HOME/.zshrc"
fi

# Aliases source URL
ALIASES_URL="https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/compression/scripts/compression-aliases.zsh"
ALIASES_LOCAL="$HOME/.compression-aliases.zsh"
ALIASES_REPO="$HOME/code/claude-code-proxy/compression/scripts/compression-aliases.zsh"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     COMPRESSION STACK ALIASES - INSTALLER                           ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if already installed
if grep -q "compression-aliases" "$RC_FILE" 2>/dev/null; then
    log_warn "Compression aliases already installed in $RC_FILE"
    read -p "Reinstall? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Backup existing rc file
if [[ -f "$RC_FILE" ]]; then
    BACKUP_FILE="$RC_FILE.backup.$(date +%Y%m%d%H%M%S)"
    cp "$RC_FILE" "$BACKUP_FILE"
    log_success "Backed up $RC_FILE to $BACKUP_FILE"
fi

# Try to get aliases from repo first, then URL
if [[ -f "$ALIASES_REPO" ]]; then
    log_info "Installing from local repository..."
    cp "$ALIASES_REPO" "$ALIASES_LOCAL"
    log_success "Copied aliases to $ALIASES_LOCAL"
elif command -v curl > /dev/null 2>&1; then
    log_info "Downloading aliases..."
    if curl -fsSL "$ALIASES_URL" -o "$ALIASES_LOCAL" 2>/dev/null; then
        log_success "Downloaded aliases to $ALIASES_LOCAL"
    else
        log_error "Failed to download aliases"
        exit 1
    fi
else
    log_error "curl not found and no local repo. Please install manually."
    exit 1
fi

# Add to rc file
echo "" >> "$RC_FILE"
echo "# ═══════════════════════════════════════════════════════════════════" >> "$RC_FILE"
echo "# Compression Stack Aliases (installed $(date +%Y-%m-%d))" >> "$RC_FILE"
echo "# ═══════════════════════════════════════════════════════════════════" >> "$RC_FILE"
echo "source $ALIASES_LOCAL" >> "$RC_FILE"
log_success "Added aliases to $RC_FILE"

# Reload shell config
if [[ -n "${ZSH_VERSION:-}" ]]; then
    source "$RC_FILE" 2>/dev/null || true
    log_success "Reloaded $RC_FILE"
elif [[ -n "${BASH_VERSION:-}" ]]; then
    source "$RC_FILE" 2>/dev/null || true
    log_success "Reloaded $RC_FILE"
else
    log_info "Please reload your shell: source $RC_FILE"
fi

# Verify installation
echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Available aliases:"
echo "  csi          - Start Claude with compression"
echo "  csr          - Resume Claude session"
echo "  qsi          - Start Qwen with compression"
echo "  qsr          - Resume Qwen session"
echo "  csi-codex    - Start Codex with compression"
echo "  csr-codex    - Resume Codex session"
echo "  osi          - Start OpenCode with compression"
echo "  ocl          - Start OpenClaw with compression"
echo "  hsi          - Start Hermes with compression"
echo "  cs-start     - Start compression stack"
echo "  cs-status    - Check status"
echo ""
echo "Test it:"
echo "  csi          # Start Claude with auto-compression"
echo "  cs-status    # Check if compression is running"
echo ""
echo "Documentation:"
echo "  ~/code/claude-code-proxy/compression/docs/COMPREHENSIVE-ALIASES.md"
echo ""
