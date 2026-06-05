#!/usr/bin/env bash
# Launch Codex inside a tmux session with project + RTK status segments.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
STATUS_SCRIPT="$PROXY_DIR/scripts/tmux_status.sh"
SESSION="${CODEX_STATUS_SESSION:-codex-status}"
START_DIR="${CODEX_STATUS_CWD:-$PWD}"
ATTACH=1

if [ "${1:-}" = "--no-attach" ]; then
    ATTACH=0
    shift
fi

if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux is required for the external RTK status bar" >&2
    exit 1
fi

_apply_status() {
    local target="$1"
    tmux set-option -t "$target" -g status on
    tmux set-option -t "$target" -g status-interval 5
    tmux set-option -t "$target" -g status-left-length 300
    tmux set-option -t "$target" -g status-right-length 420
    tmux set-option -t "$target" -g status-bg "colour235"
    tmux set-option -t "$target" -g status-fg "white"
    tmux set-option -t "$target" -g status-left "#($STATUS_SCRIPT project #{pane_current_path}) "
    tmux set-option -t "$target" -g status-right "#($STATUS_SCRIPT codex_right #{pane_current_path}) │ #($STATUS_SCRIPT rtk #{pane_current_path})"
    tmux set-option -t "$target" -g pane-border-status top
    tmux set-option -t "$target" -g pane-border-format " Codex #{pane_current_path} "
}

if tmux has-session -t "$SESSION" 2>/dev/null; then
    _apply_status "$SESSION"
    if [ "$ATTACH" -eq 1 ]; then
        exec tmux attach -t "$SESSION"
    fi
    echo "codex status session already running: tmux attach -t $SESSION"
    exit 0
fi

if [ "$#" -gt 0 ]; then
    CMD=(rtk codex "$@")
else
    CMD=(rtk codex --dangerously-bypass-approvals-and-sandbox)
fi

tmux new-session -d -s "$SESSION" -c "$START_DIR" -n codex
_apply_status "$SESSION"
tmux send-keys -t "$SESSION:0.0" "cd \"$START_DIR\" && $(printf '%q ' "${CMD[@]}")" C-m

if [ "$ATTACH" -eq 1 ]; then
    exec tmux attach -t "$SESSION"
fi

echo "started: tmux attach -t $SESSION"
