# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES
# Source this file from your shell config (~/.zshrc or ~/.bashrc)
#
# Usage: echo 'source /path/to/compression-aliases.zsh' >> ~/.zshrc
#
# Design: 3 aliases only. Not 20. Not 10. Three.
#   proxies → manage the proxy chain lifecycle
#   cc      → launch Claude via Headroom (:8787)
#   qw      → launch Qwen via Headroom (:8787)
#
# Ad-hoc overrides use inline env vars, not baked-in aliases.
# ═══════════════════════════════════════════════════════════════════

# Proxy chain manager (the script, not a shell alias)
# If not in PATH, use the full path
if command -v proxies > /dev/null 2>&1 && [[ "$(command -v proxies)" == *"claude-code-proxy"* ]]; then
    alias proxies="$(command -v proxies)"
else
    alias proxies='/home/cheta/code/claude-code-proxy/proxies'
fi

# Tool launch — all point at Headroom (:8787)
# The chain topology (comp/full) is decided by `proxies up` at start time.
alias cc='ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude'
alias qw='OPENAI_BASE_URL=http://127.0.0.1:8787/v1 qwen'

# ═══════════════════════════════════════════════════════════════════
# END COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════
