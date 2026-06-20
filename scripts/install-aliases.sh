#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════════════════
# install-aliases.sh — Install the unified xx launcher + proxy aliases
#
# Installs:
#   xx        — the unified agent launcher (3-char positional encoding)
#   proxies   — proxy chain lifecycle manager (up/down/status/logs)
#   legacy muscle-memory aliases that map to xx commands
#
# What's new in v3:
#   - One launcher to rule them all: xx <AGENT><MODE><ROUTE>[<TIER>]
#   - Replaces 25+ broken aliases with a single 3-char encoding
#   - Each tool gets the CORRECT flags (no more --dangerously-bypass-approvals on codex)
#   - --session <id> works across all tools
#   - --model <name> overrides the main model for any tool
#   - Built-in proxy health check + auto-start (no _proxy_stack_auto_start needed)
#
# Usage:
#   bash scripts/install-aliases.sh                 # install
#   bash scripts/install-aliases.sh --uninstall     # remove
#   bash scripts/install-aliases.sh --dry-run       # preview without writing
#   bash scripts/install-aliases.sh --shell zsh     # force shell (else auto-detect)
# ═════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'
YELLOW='\033[0;33m'; BOLD='\033[1m'; NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }
info() { echo -e "  ${CYAN}→${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $*"; }

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROXIES_BIN="$PROXY_DIR/proxies"
LOCAL_BIN="$HOME/.local/bin"
XX_BIN="$LOCAL_BIN/xx"
XX_CONFIG_DIR="$HOME/.xx"
XX_CONFIG="$XX_CONFIG_DIR/config.json"

# Marker wrapping alias block (for idempotent install/uninstall)
MARKER_START="# ═══ claude-code-proxy aliases START (v3) ═══"
MARKER_END="# ═══ claude-code-proxy aliases END (v3) ═══"

# ── CLI parsing ───────────────────────────────────────────────────────────────
MODE="install"
DRY_RUN=false
FORCE_SHELL=""

while [ $# -gt 0 ]; do
    case "$1" in
        --uninstall) MODE="uninstall" ;;
        --dry-run)   DRY_RUN=true ;;
        --shell)     FORCE_SHELL="$2"; shift ;;
        --help|-h)
            sed -n '3,22p' "$0"
            exit 0
            ;;
        *) fail "Unknown argument: $1"; exit 1 ;;
    esac
    shift
done

# ── Shell detection ───────────────────────────────────────────────────────────
detect_shell() {
    if [ -n "$FORCE_SHELL" ]; then
        echo "$FORCE_SHELL"; return
    fi
    local name="${SHELL##*/}"
    case "$name" in
        zsh|bash|fish) echo "$name" ;;
        *) echo "zsh" ;;
    esac
}

shell_rc_path() {
    case "$1" in
        zsh)  echo "$HOME/.zshrc" ;;
        bash) echo "$HOME/.bashrc" ;;
        fish) echo "$HOME/.config/fish/config.fish" ;;
        *) echo "$HOME/.zshrc" ;;
    esac
}

SHELL_NAME="$(detect_shell)"
RC_FILE="$(shell_rc_path "$SHELL_NAME")"

echo ""
echo -e "${BOLD}${CYAN}Unified Agent Launcher Installer (v3)${NC}"
echo -e "  Shell: ${BOLD}$SHELL_NAME${NC}"
echo -e "  RC file: ${BOLD}$RC_FILE${NC}"
echo -e "  Proxy dir: ${BOLD}$PROXY_DIR${NC}"
echo -e "  Mode: ${BOLD}$MODE${NC}$([ "$DRY_RUN" = true ] && echo ' (dry-run)')"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# Uninstall
# ═══════════════════════════════════════════════════════════════════════════════

if [ "$MODE" = "uninstall" ]; then
    if [ ! -f "$RC_FILE" ]; then
        warn "$RC_FILE not found — nothing to uninstall"
        exit 0
    fi
    if ! command grep -qF "$MARKER_START" "$RC_FILE"; then
        warn "No alias block found in $RC_FILE — nothing to uninstall"
        exit 0
    fi

    if [ "$DRY_RUN" = true ]; then
        info "would remove the alias block between markers in $RC_FILE"
        exit 0
    fi

    # Remove the block between markers (inclusive)
    python3 - "$RC_FILE" "$MARKER_START" "$MARKER_END" <<'PYEOF'
import sys, re
path, start_marker, end_marker = sys.argv[1:4]
with open(path, 'r') as f:
    content = f.read()
pattern = re.compile(
    re.escape(start_marker) + r'.*?' + re.escape(end_marker) + r'\n?',
    re.DOTALL,
)
content, n = pattern.subn('', content)
content = re.sub(r'\n{3,}', '\n\n', content)
with open(path, 'w') as f:
    f.write(content)
print(f"  removed {n} alias block(s)")
PYEOF

    # Remove proxies symlink (keep xx — it's a separate tool)
    if [ -L "$LOCAL_BIN/proxies" ]; then
        rm -f "$LOCAL_BIN/proxies"
        ok "removed $LOCAL_BIN/proxies symlink"
    fi

    # Remove old v2 marker block if present (cleanup from prior version)
    V2_MARKER_START="# ═══ claude-code-proxy aliases START (v2) ═══"
    V2_MARKER_END="# ═══ claude-code-proxy aliases END (v2) ═══"
    if command grep -qF "$V2_MARKER_START" "$RC_FILE"; then
        python3 - "$RC_FILE" "$V2_MARKER_START" "$V2_MARKER_END" <<'PYEOF'
import sys, re
path, start_marker, end_marker = sys.argv[1:4]
with open(path, 'r') as f:
    content = f.read()
pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker) + r'\n?', re.DOTALL)
content = pattern.sub('', content)
content = re.sub(r'\n{3,}', '\n\n', content)
with open(path, 'w') as f:
    f.write(content)
PYEOF
        ok "also removed legacy v2 alias block"
    fi

    ok "Uninstalled. Reload your shell: source $RC_FILE"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Install
# ═══════════════════════════════════════════════════════════════════════════════

# ── 0. Ensure xx launcher exists ─────────────────────────────────────────────
XX_SOURCE="$PROXY_DIR/scripts/xx"
if [ ! -f "$XX_SOURCE" ]; then
    # xx may not live in this repo — check ~/.local/bin directly
    if [ ! -x "$XX_BIN" ]; then
        warn "xx launcher not found at $XX_BIN or $XX_SOURCE"
        info "Run the xx installer separately, or copy xx to ~/.local/bin/ first."
        info "Continuing with proxy aliases only..."
    else
        ok "xx launcher found at $XX_BIN"
    fi
else
    if [ "$DRY_RUN" = true ]; then
        info "would copy $XX_SOURCE → $XX_BIN"
    else
        mkdir -p "$LOCAL_BIN"
        cp "$XX_SOURCE" "$XX_BIN"
        chmod +x "$XX_BIN"
        ok "installed xx launcher at $XX_BIN"
    fi
fi

# ── 1. Symlink proxies lifecycle command ──────────────────────────────────────
mkdir -p "$LOCAL_BIN"

if [ "$DRY_RUN" = true ]; then
    info "would symlink $PROXIES_BIN → $LOCAL_BIN/proxies"
else
    if [ -L "$LOCAL_BIN/proxies" ]; then
        current=$(readlink -f "$LOCAL_BIN/proxies" 2>/dev/null || echo "")
        if [ "$current" = "$PROXIES_BIN" ]; then
            ok "proxies symlink already points to this repo"
        else
            ln -sf "$PROXIES_BIN" "$LOCAL_BIN/proxies"
            ok "updated proxies symlink (was: $current)"
        fi
    elif [ -e "$LOCAL_BIN/proxies" ]; then
        warn "$LOCAL_BIN/proxies exists as a non-symlink — leaving alone"
    else
        ln -sf "$PROXIES_BIN" "$LOCAL_BIN/proxies"
        ok "created proxies symlink at $LOCAL_BIN/proxies"
    fi
fi

# ── 2. Build the alias block (v3 — xx-based + crash-guard) ───────────────────
ALIAS_BLOCK=$(cat <<EOF
$MARKER_START
# Managed by: $PROXY_DIR/scripts/install-aliases.sh
# Re-run the installer to refresh. Run with --uninstall to remove.
#
# xx handles cg_run (crash-guard) internally by default.
# Use --no-cg to disable crash-guard if needed.
#
# ENCODING: xx <AGENT><MODE><ROUTE>[<TIER>]
#   AGENT: c=claude  h=hermes  x=codex  o=opencode
#          q=qwen    p=pi      a=ante   g=antigravity
#   MODE:  i=init    c=continue  n=non-interactive  s=session  r=resume
#   ROUTE: p=proxy   b=bypass  d=debug (direct)
#   TIER:  d=deepseek  n=nemotron  k=kimi  q=qwen-next
#          m=best (ms)  f=free (ms)  0-9=profile

# Ensure ~/.local/bin is in PATH
case ":\$PATH:" in *":$LOCAL_BIN:"*) ;; *) export PATH="$LOCAL_BIN:\$PATH" ;; esac

# ─── Proxy lifecycle (standalone, not wrapped in cg_run) ───────────────────
alias proxies-up='proxies up'
alias proxies-down='proxies down'
alias proxies-status='proxies status'

# ─── Claude ──────────────────────────────────────────────────────────────
alias cc='xx cip'                  # Claude init, proxy
alias ccc='xx ccf'                 # Claude continue, proxy, free tier
alias cc-debug='xx cid'            # Claude init, direct (no proxy)

alias hsi='xx hip'                 # Hermes init, proxy
alias hsr='xx hcf'                 # Hermes continue, proxy, free tier

alias pi='xx pip'                  # Pi init, proxy
alias pic='xx pcp'                 # Pi continue, proxy, free tier

alias qw='xx qip'                  # Qwen init, proxy
alias qw-c='xx qcp'                # Qwen continue, proxy, free tier

alias codex-run='xx xip'           # Codex init, proxy
alias codex-res='xx xcp'           # Codex continue, proxy, free tier

alias oc='xx oip'                  # OpenCode init, proxy
alias ante='xx aip'                # Ante init, proxy
alias antigravity='xx gip'         # Antigravity init, proxy

# ─── Direct (no proxy) ────────────────────────────────────────────────────
alias cc-direct='xx cid'
alias pi-direct='xx pid'
alias hsi-direct='xx hid'
alias qw-direct='xx qid'
alias ante-direct='xx aid'

# ─── Bypass (proxy features on, model reroute off) ────────────────────────
alias hsi-bp='xx hib'
alias pi-bp='xx pib'

$MARKER_END
EOF
)

# ── 3. Install / update the alias block ──────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    echo ""
    info "would append/replace alias block in $RC_FILE:"
    echo "$ALIAS_BLOCK" | sed 's/^/      /'
    echo ""
    info "dry-run complete — no changes made"
    exit 0
fi

# Remove any old v2 block before installing v3
V2_MARKER_START="# ═══ claude-code-proxy aliases START (v2) ═══"
V2_MARKER_END="# ═══ claude-code-proxy aliases END (v2) ═══"
if command grep -qF "$V2_MARKER_START" "$RC_FILE" 2>/dev/null; then
    python3 - "$RC_FILE" "$V2_MARKER_START" "$V2_MARKER_END" <<'PYEOF'
import sys, re
path, start_marker, end_marker = sys.argv[1:4]
with open(path, 'r') as f:
    content = f.read()
pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker) + r'\n?', re.DOTALL)
content = pattern.sub('', content)
content = re.sub(r'\n{3,}', '\n\n', content)
with open(path, 'w') as f:
    f.write(content)
PYEOF
    info "purged old v2 alias block before installing v3"
fi

touch "$RC_FILE"

if command grep -qF "$MARKER_START" "$RC_FILE"; then
    # Replace existing v3 block
    python3 - "$RC_FILE" "$MARKER_START" "$MARKER_END" <<PYEOF
import sys, re
path, start_marker, end_marker = sys.argv[1:4]
new_block = '''$ALIAS_BLOCK'''
with open(path, 'r') as f:
    content = f.read()
pattern = re.compile(
    re.escape(start_marker) + r'.*?' + re.escape(end_marker),
    re.DOTALL,
)
content = pattern.sub(new_block, content)
with open(path, 'w') as f:
    f.write(content)
PYEOF
    ok "replaced existing alias block in $RC_FILE"
else
    {
        echo ""
        echo "$ALIAS_BLOCK"
    } >> "$RC_FILE"
    ok "appended alias block to $RC_FILE"
fi

# ── 4. Report ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}Installed.${NC} Reload your shell or run:  ${CYAN}source $RC_FILE${NC}"
echo ""
echo -e "${BOLD}The xx encoding system${NC}"
echo ""
echo "  xx <AGENT><MODE><ROUTE>[<TIER>]"
echo ""
echo "  AGENT  MODE          ROUTE          TIER"
echo "  ─────  ────────────  ─────────────  ─────────────────"
echo "  c      i = init      p = proxy      m = best (ms)"
echo "  h      n = non-int.  b = bypass     f = free (ms)"
echo "  x      c = continue  d = debug      d = deepseek"
echo "  o      s = session                  n = nemotron"
echo "  q      r = resume                   k = kimi"
echo "  p                                   0-9 = profile"
echo "  a"
echo "  g"
echo ""
echo -e "${BOLD}Quick reference:${NC}"
cat <<'EOFQR'
  ── Claude ─────────────────────────────────────────────────────
  cc                     xx cip            Init, proxy
  ccc                    xx ccf            Continue, free tier
  cc-debug               xx cid            Init, direct

  ── Hermes ─────────────────────────────────────────────────────
  hsi                    xx hip            Init, proxy
  hsr                    xx hcf            Continue, free tier

  ── Pi ─────────────────────────────────────────────────────────
  pi                     xx pip            Init, proxy
  pic                    xx pcp            Continue, free tier

  ── Others ─────────────────────────────────────────────────────
  qw                     xx qip            Qwen init, proxy
  codex-run              xx xip            Codex init, proxy
  antigravity            xx gip            Antigravity init, proxy
  ante                   xx aip            Ante init, proxy
  oc                     xx oip            OpenCode init, proxy

  ── Any tool, any mode, raw ────────────────────────────────────
  xx cip                 Claude init proxy         (cg_run on by default)
  xx --no-cg cip         Claude init proxy         (no crash-guard)
  xx hif                 Hermes init free tier
  xx xcd                 Codex continue debug
  xx qcpd                Qwen continue proxy deepseek

  ── Proxy lifecycle ────────────────────────────────────────────
  proxies up / down / status

  ── Learn the encoding ────────────────────────────────────────
  xx -h
EOFQR
echo ""
echo -e "  ${YELLOW}Tip:${NC} xx handles crash-guard internally. Use ${CYAN}--no-cg${NC} to disable."
echo -e "  ${YELLOW}Tip:${NC} Run ${CYAN}xx${NC} or ${CYAN}xx -h${NC} for the full encoding reference."
echo ""
