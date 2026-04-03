#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK - ALIAS INSTALLER (Simplified)
# ═══════════════════════════════════════════════════════════════════
#
# Installs 3 aliases + the proxies command:
#   proxies → manage the proxy chain lifecycle
#   cc      → launch Claude via Headroom (:8787)
#   qw      → launch Qwen via Headroom (:8787)
#
# Usage:
#   ./install-aliases.sh
#
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROXIES_SCRIPT="$PROXY_DIR/proxies"
ALIAS_FILE="$SCRIPT_DIR/compression-aliases.zsh"

# Detect shell config file
detect_shell_rc() {
    local shell_name="${SHELL##*/}"
    case "$shell_name" in
        zsh)  echo "$HOME/.zshrc" ;;
        bash) echo "$HOME/.bashrc" ;;
        *)    echo "$HOME/.zshrc" ;;
    esac
}

RC_FILE="$(detect_shell_rc)"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         COMPRESSION STACK - ALIAS INSTALLER                         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
log_info "Shell: ${SHELL##*/}"
log_info "Config file: $RC_FILE"
log_info "Proxy dir: $PROXY_DIR"
echo ""

# ── 1. Install proxies script to PATH ──
if [[ ! -f "$PROXIES_SCRIPT" ]]; then
    log_error "proxies script not found at $PROXIES_SCRIPT"
    log_info "Make sure you're running this from the repository"
    exit 1
fi

# Create ~/.local/bin if it doesn't exist
mkdir -p "$HOME/.local/bin"

if [[ -L "$HOME/.local/bin/proxies" ]]; then
    local_target="$(readlink -f "$HOME/.local/bin/proxies" 2>/dev/null || true)"
    if [[ "$local_target" == "$PROXIES_SCRIPT" ]]; then
        log_info "proxies command already linked"
    else
        log_warn "Updating proxies symlink (was: $local_target)"
        ln -sf "$PROXIES_SCRIPT" "$HOME/.local/bin/proxies"
        log_success "proxies command updated"
    fi
elif [[ -f "$HOME/.local/bin/proxies" ]]; then
    log_warn "proxies already exists in ~/.local/bin (file, not symlink)"
    read -p "Replace with symlink to this repo? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$HOME/.local/bin/proxies"
        ln -sf "$PROXIES_SCRIPT" "$HOME/.local/bin/proxies"
        log_success "proxies command installed"
    fi
else
    ln -sf "$PROXIES_SCRIPT" "$HOME/.local/bin/proxies"
    log_success "proxies command installed (symlink → $PROXIES_SCRIPT)"
fi

# ── 2. Add ~/.local/bin to PATH if not already there ──
if ! grep -q "\.local/bin" "$RC_FILE" 2>/dev/null; then
    log_info "Adding ~/.local/bin to PATH..."
    cat >> "$RC_FILE" << 'PATHFIX'

# CLI tools PATH
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.opencode/bin:$PATH"
PATHFIX
    log_success "PATH updated"
else
    log_info "~/.local/bin already in PATH"
fi

# ── 3. Install aliases ──
# Remove old compression aliases if present
if [[ -f "$RC_FILE" ]] && grep -q "COMPRESSION STACK ALIASES" "$RC_FILE" 2>/dev/null; then
    log_warn "Old compression aliases found — replacing..."
    python3 -c "
import re
with open('$RC_FILE', 'r') as f:
    content = f.read()
content = re.sub(r'\n# ═*COMPRESSION.*?END COMPRESSION.*?\n', '\n', content, flags=re.DOTALL)
content = re.sub(r'\n{3,}', '\n\n', content)
with open('$RC_FILE', 'w') as f:
    f.write(content)
" 2>/dev/null || true
    log_success "Old aliases removed"
fi

# Remove any old sprawling aliases individually (csi, csr, qsi, etc.)
if [[ -f "$RC_FILE" ]]; then
    old_aliases=""
    for alias_name in csi csr csi-yolo csi-proxy csr-proxy csi-proxy-yolo \
                      qsi qsr qsi-yolo qsi-proxy qsr-proxy \
                      csi-codex csr-codex csi-codex-yolo \
                      osi osr ocl ocr ocl-yolo hsi hsr hsi-yolo \
                      cs-start cs-stop cs-restart cs-status cs-health; do
        if grep -q "^alias $alias_name=" "$RC_FILE" 2>/dev/null; then
            old_aliases="$old_aliases $alias_name"
        fi
    done
    if [[ -n "$old_aliases" ]]; then
        log_warn "Removing old sprawling aliases:$old_aliases"
        python3 -c "
aliases_to_remove = '''$old_aliases'''.split()
with open('$RC_FILE', 'r') as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith('alias '):
        alias_name = stripped.split('=')[0].replace('alias ', '').strip()
        if alias_name not in aliases_to_remove:
            new_lines.append(line)
    else:
        new_lines.append(line)
with open('$RC_FILE', 'w') as f:
    f.writelines(new_lines)
" 2>/dev/null || true
        log_success "Old aliases removed"
    fi
fi

# Create rc file if it doesn't exist
if [[ ! -f "$RC_FILE" ]]; then
    log_info "Creating $RC_FILE..."
    touch "$RC_FILE"
fi

# Add the new simplified aliases
log_info "Installing simplified aliases to $RC_FILE..."

cat >> "$RC_FILE" << 'ALIASES'

# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES (simplified — 3 only)
# ═══════════════════════════════════════════════════════════════════

alias cc='ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude'
alias qw='OPENAI_BASE_URL=http://127.0.0.1:8787/v1 qwen'
# proxies is installed via symlink in ~/.local/bin/proxies

# ═══════════════════════════════════════════════════════════════════
# END COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════
ALIASES

log_success "Aliases installed to $RC_FILE"

# Reload shell config if possible
if [[ -n "${ZSH_VERSION:-}" ]]; then
    log_info "Detected Zsh — reloading..."
    source "$RC_FILE" 2>/dev/null || true
    log_success "Config reloaded"
elif [[ -n "${BASH_VERSION:-}" ]]; then
    log_info "Detected Bash — reloading..."
    source "$RC_FILE" 2>/dev/null || true
    log_success "Config reloaded"
else
    log_info "Reload your shell: source $RC_FILE"
fi

# Show quick reference
echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    INSTALLATION COMPLETE                             ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Proxy management:"
echo "  proxies up          → Start full chain"
echo "  proxies up --comp   → Compression only"
echo "  proxies down        → Stop all"
echo "  proxies status      → Check running"
echo ""
echo "Tool launch:"
echo "  cc                  → Claude via Headroom (:8787)"
echo "  qw                  → Qwen via Headroom (:8787)"
echo ""
echo "Ad-hoc overrides:"
echo "  ANTHROPIC_BASE_URL=http://127.0.0.1:8082 claude   # bypass compression"
echo "  ANTHROPIC_BASE_URL=http://127.0.0.1:8317 claude   # direct to CLIProxyAPI"
echo ""
