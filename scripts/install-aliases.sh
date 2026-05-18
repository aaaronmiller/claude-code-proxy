#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════════════════
# install-aliases.sh — Install Claude / proxy / compression aliases
#
# Single command to bootstrap a new machine. Installs:
#   proxies         — the proxy chain lifecycle manager
#   cld*            — Claude variants (direct / via proxy / with compression)
#   cldo*           — Claude with OAuth token via passthrough
#   qw / qsi*       — Qwen variants
#   csi-codex*      — Codex variants
#   osi* / ocl* / hsi* — OpenCode / OpenClaw / Hermes variants
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

# Marker wrapping alias block (for idempotent install/uninstall)
MARKER_START="# ═══ claude-code-proxy aliases START (v2) ═══"
MARKER_END="# ═══ claude-code-proxy aliases END (v2) ═══"

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
            sed -n '3,20p' "$0"
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
        *) echo "zsh" ;;  # default
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
echo -e "${BOLD}${CYAN}Claude / Proxy / Compression Alias Installer${NC}"
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
# Collapse double blank lines
content = re.sub(r'\n{3,}', '\n\n', content)
with open(path, 'w') as f:
    f.write(content)
print(f"  removed {n} alias block(s)")
PYEOF

    # Remove proxies symlink
    if [ -L "$LOCAL_BIN/proxies" ]; then
        rm -f "$LOCAL_BIN/proxies"
        ok "removed $LOCAL_BIN/proxies symlink"
    fi

    ok "Uninstalled. Reload your shell: source $RC_FILE"
    exit 0
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Install
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. Ensure proxies binary is symlinked into PATH ──────────────────────────
if [ ! -x "$PROXIES_BIN" ]; then
    fail "proxies script not executable at $PROXIES_BIN"
    exit 1
fi

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

# ── 2. Build the alias block ─────────────────────────────────────────────────
ALIAS_BLOCK=$(cat <<EOF
$MARKER_START
# Managed by: $PROXY_DIR/scripts/install-aliases.sh
# To update aliases, re-run the installer. To remove, run with --uninstall.
#
# INVARIANT: every alias routes through:
#   proxy :8082  → routing, cascade, logging, budget gates
#   headroom :8787 → context compression (GPU-accelerated via proxy chain)
#   RTK → terminal output compression
#
# "Passthrough" aliases (cldo, cc-mini) still go through the proxy — the proxy
# preserves all logging/features, just doesn't reroute the upstream endpoint.

# Ensure ~/.local/bin (where proxies symlink lives) is in PATH
case ":\$PATH:" in *":$LOCAL_BIN:"*) ;; *) export PATH="$LOCAL_BIN:\$PATH" ;; esac

# ─── Proxy stack helper ──────────────────────────────────────────────────────
# Auto-starts the full chain (proxy + headroom) if either service is down.
_proxy_stack_auto_start() {
  if curl -sf --max-time 1 http://127.0.0.1:8082/health >/dev/null 2>&1 \
    && curl -sf --max-time 1 http://127.0.0.1:8787/health >/dev/null 2>&1; then
    return 0
  fi
  NO_ATTACH=1 proxies up >/dev/null 2>&1
}

# ─── Claude CLI ──────────────────────────────────────────────────────────────
# All aliases: proxy:8082 (routing+logs) → headroom:8787 (compression) → provider + RTK
# Suffix -c = --continue (resume prior session)

# DEFAULT: proxy routing → free OpenRouter cascade + headroom + RTK
alias cc='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --dangerously-skip-permissions'
alias ccc='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --continue --dangerously-skip-permissions'

# ANTHROPIC PRO: proxy passthrough with OAuth → Anthropic API + headroom + RTK
# Small/toolcall requests still cascade to free OR via proxy routing
# cldo guards against the silent-empty-OAuth-token failure mode:
# if \$CLAUDE_CODE_OAUTH_TOKEN is unset/empty, warn the user explicitly
# instead of passing an empty string to the proxy (which would silently
# fall back to a server key and produce confusing 401s).
_cldo_guard() {
  if [ -z "\${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
    echo "  \033[33m⚠  CLAUDE_CODE_OAUTH_TOKEN is not set in your shell.\033[0m" >&2
    echo "  Get a token from claude.ai/code (Settings → Developer → OAuth Token)," >&2
    echo "  then export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-... in ~/.zshrc" >&2
    echo "  Falling back to proxy's PROVIDERS_anthropic_API_KEY (server-side key)." >&2
    return 0
  fi
  return 0
}
alias cldo='_proxy_stack_auto_start && _cldo_guard && CLAUDE_CODE_OAUTH_TOKEN=\$CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_BASE_URL=http://127.0.0.1:8082/p/claude rtk claude --dangerously-skip-permissions'
alias cldo-c='_proxy_stack_auto_start && _cldo_guard && CLAUDE_CODE_OAUTH_TOKEN=\$CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_BASE_URL=http://127.0.0.1:8082/p/claude rtk claude --continue --dangerously-skip-permissions'

# OPENCODE GO: proxy routes BIG tier to opencode_go/minimax-m2.7, small→free OR + headroom + RTK
alias cc-mini='_proxy_stack_auto_start && BIG_MODEL=opencode_go/minimax-m2.7 ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --dangerously-skip-permissions'
alias cc-mini-c='_proxy_stack_auto_start && BIG_MODEL=opencode_go/minimax-m2.7 ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --continue --dangerously-skip-permissions'

# ─── Other CLIs ──────────────────────────────────────────────────────────────
# All route through proxy:8082 (which chains to headroom for compression).
# RTK wraps where it helps (Claude Code tool output); for other CLIs it's a no-op pass-through.

alias qw='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/codex/v1 OPENAI_API_KEY=pass rtk qwen --auth-type openai'
alias qw-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/codex/v1 OPENAI_API_KEY=pass rtk qwen --auth-type openai --continue'

alias codex-run='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/codex/v1 OPENAI_API_KEY=pass rtk codex --dangerously-bypass-approvals-and-sandbox'
alias codex-res='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/codex/v1 OPENAI_API_KEY=pass rtk codex resume'

alias oc='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/opencode/v1 OPENAI_API_KEY=pass rtk opencode'
alias oc-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/opencode/v1 OPENAI_API_KEY=pass rtk opencode --resume'

alias ocl='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/opencode/v1 OPENAI_API_KEY=pass rtk openclaw'
alias ocl-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/opencode/v1 OPENAI_API_KEY=pass rtk openclaw --resume'

# Hermes: routes through proxy → headroom for context compression.
# RTK wraps the launch so hermes output is also compressed if used inside Claude Code.
alias hsi='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/hermes/v1 OPENAI_API_KEY=pass rtk hermes --dangerously-skip-permissions'
alias hsr='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/hermes/v1 OPENAI_API_KEY=pass rtk hermes --resume --dangerously-skip-permissions'

# Hermes bypass: main model unchanged (caller decides), tool calls → owl-alpha cascade.
# Use when you want hermes to keep its own model choice but still benefit from the
# proxy's tool-call routing + headroom compression + RTK output filtering.
alias hsi-bp='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/hermes-bypass/v1 OPENAI_API_KEY=pass rtk hermes --dangerously-skip-permissions'
alias hsr-bp='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/hermes-bypass/v1 OPENAI_API_KEY=pass rtk hermes --resume --dangerously-skip-permissions'

# Pi: AI coding assistant. Routes through proxy → headroom + RTK.
# Main model: NOT pinned — pass --model at runtime to choose per-session.
# Tool calls: auto-routed by the proxy to TOOLCALL_MODELS (.env) regardless of main.
# Usage examples:
#   psi --model qwen/qwen3-next-80b "build an http server"
#   psi --model anthropic/claude-opus-4-20250514 "complex refactor"
#   psi --tools read,grep -p "review the code in src/"
alias psi='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/pi/v1 OPENAI_API_KEY=pass rtk pi --provider openai'
alias psi-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/pi/v1 OPENAI_API_KEY=pass rtk pi --provider openai --continue'

# Pi bypass: main model unchanged (pi/agent decides), tool calls → owl-alpha cascade.
# Use when you want pi to keep its default model choice but still benefit from the
# proxy's tool-call routing + headroom compression + RTK output filtering.
alias psi-bp='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/pi-bypass/v1 OPENAI_API_KEY=pass rtk pi --provider openai'
alias psi-bp-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/p/pi-bypass/v1 OPENAI_API_KEY=pass rtk pi --provider openai --continue'

# ─── Legacy muscle-memory ────────────────────────────────────────────────────
alias car='cc'
alias carc='ccc'
alias cproxy-init='cc'
alias cproxy-continue='ccc'
alias oc-direct='opencode'

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

touch "$RC_FILE"

if command grep -qF "$MARKER_START" "$RC_FILE"; then
    # Replace existing block
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
    # Append
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
echo -e "${BOLD}Quick reference:${NC}"
cat <<'EOFQR'
  proxies up / down / status   — proxy chain lifecycle (starts headroom+proxy in tmux)

  ALL aliases: proxy:8082 (routing+logs) → headroom:8787 (compression) → provider + RTK

  ── Claude CLI ────────────────────────────────────────────────────
  cc / ccc             — default: OR cascade, new/continue
  cldo / cldo-c        — Anthropic Pro OAuth passthrough, new/continue
  cc-mini / cc-mini-c  — opencode_go/minimax-m2.7 big tier, new/continue

  ── Other CLIs (all via proxy→headroom) ──────────────────────────
  qw / qw-c            — Qwen (rtk)
  codex-run / codex-res — Codex (rtk)
  oc / oc-c            — OpenCode (rtk)
  ocl / ocl-c          — OpenClaw (rtk)
  hsi / hsr            — Hermes (rtk, proxy cascade for aux roles)
  psi / psi-c          — pi (no main pinned, toolcalls via TOOLCALL_MODELS, rtk)
                         use: psi --model X "prompt"  to pick main per session

  ── Legacy muscle-memory ──────────────────────────────────────────
  car / carc           → cc / ccc
  cproxy-init / cproxy-continue → cc / ccc
EOFQR
echo ""
