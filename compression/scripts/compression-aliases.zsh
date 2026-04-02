# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════════════════
# Add these to ~/.zshrc for quick access to compression stack features
#
# Quick start: Run this to auto-add aliases:
#   cat ~/code/input-compression/scripts/compression-aliases.zsh >> ~/.zshrc && source ~/.zshrc
# ═══════════════════════════════════════════════════════════════════════════════

# Compression stack location
export COMPRESSION_DIR="$HOME/code/input-compression"
export PATH="$COMPRESSION_DIR/scripts:$PATH"

# ═══════════════════════════════════════════════════════════════════════════════
# CORE COMPRESSION ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

# Stack control
alias cs-start='systemctl --user start gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; echo "✅ Compression stack started"'
alias cs-stop='systemctl --user stop gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; echo "⏹️  Compression stack stopped"'
alias cs-restart='systemctl --user restart gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null; echo "🔄 Compression stack restarted"'
alias cs-status='systemctl --user status gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null'
alias cs-health='$COMPRESSION_DIR/scripts/compression-stack.sh health'

# Unified control script
alias cs='$COMPRESSION_DIR/scripts/compression-stack.sh'

# ═══════════════════════════════════════════════════════════════════════════════
# MODE ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

# Quick mode switching
alias cs-max='$COMPRESSION_DIR/scripts/compression-stack.sh mode set max-compression && $COMPRESSION_DIR/scripts/compression-stack.sh apply-mode && echo "📊 Mode: MAX COMPRESSION (98%, 80ms)"'
alias cs-balanced='$COMPRESSION_DIR/scripts/compression-stack.sh mode set balanced && $COMPRESSION_DIR/scripts/compression-stack.sh apply-mode && echo "⚖️  Mode: BALANCED (97%, 50ms)"'
alias cs-speed='$COMPRESSION_DIR/scripts/compression-stack.sh mode set speed && $COMPRESSION_DIR/scripts/compression-stack.sh apply-mode && echo "⚡ Mode: SPEED (90%, 20ms)"'
alias cs-free='$COMPRESSION_DIR/scripts/compression-stack.sh mode set free-tier && $COMPRESSION_DIR/scripts/compression-stack.sh apply-mode && echo "🆓 Mode: FREE-TIER (99%, 50ms)"'

# Mode info
alias cs-mode='$COMPRESSION_DIR/scripts/compression-stack.sh mode'

# ═══════════════════════════════════════════════════════════════════════════════
# STATS & DASHBOARD ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

# Quick stats
alias cs-stats='python3 $COMPRESSION_DIR/scripts/compression-dashboard.py --interval 2 2>/dev/null | head -50'
alias cs-stats-quick='python3 -c "
import json
from pathlib import Path
f = Path.home() / \".compression_stats.json\"
if f.exists():
    s = json.load(f)[\"total\"]
    t = s.get(\"tokens_saved\", 0)
    c = s.get(\"cost_without\", 0) - s.get(\"cost_with\", 0)
    r = s.get(\"requests\", 0)
    ts = f\"{t/1e6:.1f}M\" if t > 1e6 else f\"{t/1e3:.0f}K\" if t > 1e3 else str(t)
    print(f\"💰 Saved \${c:.2f} ({ts} tokens, {r} requests)\")
else:
    print(\"💰 No stats yet\")
" 2>/dev/null'

# Web dashboard
alias cs-web='python3 $COMPRESSION_DIR/scripts/compression-dashboard.py --web && echo "📊 Dashboard: file://$HOME/.compression_dashboard.html"'
alias cs-dashboard='python3 $COMPRESSION_DIR/scripts/compression-dashboard.py'

# Tracker
alias cs-tracker='python3 $COMPRESSION_DIR/scripts/compression-tracker.py &'

# ═══════════════════════════════════════════════════════════════════════════════
# COMPRESCTL ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

alias compress-on='compressctl on && echo "✅ Compression ENABLED"'
alias compress-off='compressctl off && echo "⏹️  Compression DISABLED"'
alias compress-status='compressctl status'

# Short versions
alias con='compress-on'
alias coff='compress-off'
alias cstat='compress-status'

# ═══════════════════════════════════════════════════════════════════════════════
# MODIFIED CLI ALIASES (AUTO-ENABLE COMPRESSION)
# ═══════════════════════════════════════════════════════════════════════════════
# These replace the standard cli-init and cli-resume to ALWAYS include compression
# Compression should NEVER be optional - it's always on by default
# ═══════════════════════════════════════════════════════════════════════════════

# Claude Code with compression auto-enabled (REPLACES existing cli-init)
alias cli-init='
  echo "🔧 Initializing compression stack..."
  compressctl on 2>/dev/null
  systemctl --user start gpu-resident-manager compression-tracker 2>/dev/null || true
  echo "✅ Compression enabled"
  echo "🚀 Starting Claude Code..."
  claude
'

# Claude Code resume with compression (REPLACES existing cli-resume)
alias cli-resume='
  echo "🔧 Resuming compression stack..."
  compressctl on 2>/dev/null
  systemctl --user start compression-dashboard 2>/dev/null || true
  echo "✅ Compression enabled"
  echo "🚀 Starting Claude Code..."
  claude
'

# Ultra-short versions (RECOMMENDED for daily use)
alias csi='cli-init'      # Claude with compression init
alias csr='cli-resume'    # Claude with compression resume

# Compression-only start (no Claude)
alias cli-compress='
  compressctl on
  systemctl --user start gpu-resident-manager compression-tracker compression-dashboard 2>/dev/null
  cs-health
'

# ═══════════════════════════════════════════════════════════════════════════════
# HEADROOM ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

alias headroom-start='headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry &'
alias headroom-stop='pkill -f "headroom proxy" && echo "⏹️  Headroom stopped"'
alias headroom-status='curl -s http://127.0.0.1:8787/health | python3 -m json.tool 2>/dev/null || echo "Headroom not running"'

# ═══════════════════════════════════════════════════════════════════════════════
# GPU MONITORING ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

alias gpu-watch='watch -n1 "nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv"'
alias gpu-stats='nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,memory.free --format=csv'
alias gpu-resident='python3 $COMPRESSION_DIR/scripts/gpu-resident-manager.py &'

# ═══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE HELP
# ═══════════════════════════════════════════════════════════════════════════════

cs-help() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║              COMPRESSION STACK - QUICK REFERENCE                     ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📦 STACK CONTROL"
    echo "  cs-start      Start compression stack"
    echo "  cs-stop       Stop compression stack"
    echo "  cs-restart    Restart compression stack"
    echo "  cs-status     Show service status"
    echo "  cs-health     Full health check"
    echo "  cs            Unified control (cs start|stop|restart|status|health)"
    echo ""
    echo "⚙️  MODES"
    echo "  cs-max        MAX COMPRESSION (98%, 80ms)"
    echo "  cs-balanced   BALANCED (97%, 50ms) ← DEFAULT"
    echo "  cs-speed      SPEED (90%, 20ms)"
    echo "  cs-free       FREE-TIER (99%, 50ms)"
    echo "  cs-mode       Show/set current mode"
    echo ""
    echo "📊 STATS"
    echo "  cs-stats      Full dashboard"
    echo "  cs-stats-quick Quick one-liner"
    echo "  cs-web        Web dashboard (HTML)"
    echo "  cs-dashboard  Terminal dashboard"
    echo ""
    echo "🔧 COMPRESSION CONTROL"
    echo "  con / compress-on    Enable compression"
    echo "  coff / compress-off  Disable compression"
    echo "  cstat / compress-status  Show status"
    echo ""
    echo "🚀 CLAUDE CODE (AUTO-ENABLES COMPRESSION)"
    echo "  csi / cli-init    Start Claude with compression"
    echo "  csr / cli-resume  Resume Claude with compression"
    echo ""
    echo "🎮 GPU"
    echo "  gpu-watch       Real-time GPU monitoring"
    echo "  gpu-stats       GPU statistics"
    echo ""
    echo "══════════════════════════════════════════════════════════════════════"
    echo "  RECOMMENDED: Use 'csi' or 'csr' for daily Claude Code work"
    echo "  These ALWAYS enable compression automatically"
    echo "══════════════════════════════════════════════════════════════════════"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-START ON SHELL INIT (OPTIONAL)
# ═══════════════════════════════════════════════════════════════════════════════
# Uncomment the following lines to auto-start compression on shell init:

# if command -v systemctl &>/dev/null; then
#     systemctl --user start gpu-resident-manager compression-tracker 2>/dev/null || true
# fi

# ═══════════════════════════════════════════════════════════════════════════════
# END COMPRESSION STACK ALIASES
# ═══════════════════════════════════════════════════════════════════════════════
