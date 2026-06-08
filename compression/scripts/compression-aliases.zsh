# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES
# Source this file from your shell config (~/.zshrc or ~/.bashrc)
#
# Usage: echo 'source /path/to/compression-aliases.zsh' >> ~/.zshrc
#
# Prefer running: bash scripts/install-aliases.sh
# That installs the full alias set and keeps things in sync.
#
# This file is the minimal subset for machines without the full repo.
# ═══════════════════════════════════════════════════════════════════

# Proxy chain manager (the script, not a shell alias)
if command -v proxies > /dev/null 2>&1 && [[ "$(command -v proxies)" == *"claude-code-proxy"* ]]; then
    alias proxies="$(command -v proxies)"
else
    alias proxies="$HOME/code/claude-code-proxy/proxies"
fi

# ── Auto-start helper ─────────────────────────────────────────────
_proxy_stack_auto_start() {
  if curl -sf --max-time 1 http://127.0.0.1:8082/health >/dev/null 2>&1 \
    && curl -sf --max-time 1 http://127.0.0.1:8787/health >/dev/null 2>&1; then
    return 0
  fi
  NO_ATTACH=1 proxies up >/dev/null 2>&1
}

# ── FULL STACK: proxy :8082 → headroom :8787 → provider ──────────
# RTK terminal compression + yolo (--dangerously-skip-permissions)
alias cc='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --dangerously-skip-permissions'
alias ccc='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8082 ANTHROPIC_API_KEY=pass rtk claude --continue --dangerously-skip-permissions'

# ── HEADROOM DIRECT: bypass proxy, headroom :8787 only ────────────
alias cldx='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8787 rtk claude --dangerously-skip-permissions'
alias cldx-c='_proxy_stack_auto_start && ANTHROPIC_BASE_URL=http://127.0.0.1:8787 rtk claude --continue --dangerously-skip-permissions'

# ── DIRECT: no proxy, no headroom (straight to Anthropic) ─────────
alias cld='rtk claude --dangerously-skip-permissions'
alias cld-c='rtk claude --continue --dangerously-skip-permissions'

# ── Other CLIs via headroom ────────────────────────────────────────
alias qw='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/v1 OPENAI_API_KEY=pass qwen --auth-type openai'
alias qw-c='_proxy_stack_auto_start && OPENAI_BASE_URL=http://127.0.0.1:8082/v1 OPENAI_API_KEY=pass qwen --auth-type openai --continue'

# Legacy muscle-memory aliases
alias car='cc'
alias carc='ccc'

# ═══════════════════════════════════════════════════════════════════
# END COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════
