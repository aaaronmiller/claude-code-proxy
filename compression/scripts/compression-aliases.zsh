# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES
# Source this file from your shell config (~/.zshrc or ~/.bashrc)
#
# Usage: echo 'source /path/to/compression-aliases.zsh' >> ~/.zshrc
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
