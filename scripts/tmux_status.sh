#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# tmux_status.sh — Generate status bar content for proxy tmux panes
#
# Usage:
#   tmux_status.sh project [dir] → GitHub/project + branch status
#   tmux_status.sh proxy     → Claude Code Proxy status line
#   tmux_status.sh headroom  → Headroom compression status line
#   tmux_status.sh rtk       → RTK terminal compression status line
#   tmux_status.sh codex_right [dir] → Codex session stats status line
#
# Called by tmux pane-border-status or set-option status-right.
# Output is a single line with tmux color codes.
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROXY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROXY_URL="http://127.0.0.1:8082"
HEADROOM_URL="http://127.0.0.1:8787"

# ── Python helper (use venv if available) ──
_python() {
    local venv="/home/cheta/code/claude-code-proxy/.venv/bin/python"
    if [ -f "$venv" ]; then
        "$venv" "$@"
    else
        python3 "$@"
    fi
}

# ── Project / GitHub status line ──
status_project() {
    local dir="${1:-$PWD}"
    local root
    root=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || {
        echo "#[fg=yellow]● NO GIT#[default]"
        return
    }

    local repo branch remote remote_short porcelain dirty staged unstaged untracked
    repo=$(basename "$root")
    branch=$(git -C "$root" symbolic-ref --quiet --short HEAD 2>/dev/null || git -C "$root" rev-parse --short HEAD 2>/dev/null || echo "detached")
    remote=$(git -C "$root" remote get-url origin 2>/dev/null || true)
    remote_short="$repo"
    if [ -n "$remote" ]; then
        remote_short=$(printf "%s" "$remote" | sed -E \
            -e 's#^git@github.com:##' \
            -e 's#^https://github.com/##' \
            -e 's#\.git$##')
    fi

    porcelain=$(git -C "$root" status --porcelain=v1 2>/dev/null || true)
    dirty=$(printf "%s\n" "$porcelain" | sed '/^$/d' | wc -l | tr -d ' ')
    staged=$(printf "%s\n" "$porcelain" | awk '$1 !~ /^\\?/ && substr($0,1,1) != " " {c++} END {print c+0}')
    unstaged=$(printf "%s\n" "$porcelain" | awk 'substr($0,2,1) != " " && $1 !~ /^\\?/ {c++} END {print c+0}')
    untracked=$(printf "%s\n" "$porcelain" | awk '$1 == "??" {c++} END {print c+0}')

    local upstream_counts ahead behind sync_part dirty_part
    upstream_counts=$(git -C "$root" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null || true)
    sync_part=""
    if [ -n "$upstream_counts" ]; then
        behind="${upstream_counts%%[[:space:]]*}"
        ahead="${upstream_counts##*[[:space:]]}"
        if [ "${ahead:-0}" != "0" ] || [ "${behind:-0}" != "0" ]; then
            sync_part=" #[fg=yellow]↑${ahead:-0}↓${behind:-0}#[default]"
        fi
    fi

    dirty_part=""
    if [ "${dirty:-0}" != "0" ]; then
        dirty_part=" #[fg=yellow]±${dirty}#[default]"
        [ "${staged:-0}" != "0" ] && dirty_part="${dirty_part} +${staged}"
        [ "${unstaged:-0}" != "0" ] && dirty_part="${dirty_part} ~${unstaged}"
        [ "${untracked:-0}" != "0" ] && dirty_part="${dirty_part} ?${untracked}"
    fi

    printf "#[fg=magenta]● %s#[default] #[fg=cyan]%s#[default] │ #[fg=green]%s#[default]%s%s" \
        "$repo" "$remote_short" "$branch" "$sync_part" "$dirty_part"
}

# ── Proxy status line ──
status_proxy() {
    local health stats
    health=$(curl -sf --max-time 1 "$PROXY_URL/health" 2>/dev/null) || {
        echo "#[fg=red]● PROXY DOWN#[default]"
        return
    }

    stats=$(curl -sf --max-time 2 "$PROXY_URL/api/stats" 2>/dev/null) || {
        echo "#[fg=green]● PROXY#[default] #[fg=yellow](no stats)#[default]"
        return
    }

    _python -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    reqs = d.get('requests_today', 0)
    tokens = d.get('total_tokens', 0)
    cost = d.get('est_cost', 0)
    latency = d.get('avg_latency', 0)

    # Cascade events count
    cascade = d.get('cascade', {})
    events = cascade.get('events', [])
    c_count = len(events)

    # Last error from recent requests
    last_err = ''
    for r in d.get('recent_requests', []):
        if r.get('status') != 'success':
            last_err = f' err:{r.get(\"model\",\"?\")[:15]}'
            break

    # Format tokens compactly
    if tokens >= 1_000_000:
        tok_str = f'{tokens/1_000_000:.1f}M'
    elif tokens >= 1_000:
        tok_str = f'{tokens/1_000:.1f}K'
    else:
        tok_str = str(tokens)

    parts = [
        '#[fg=green]● PROXY#[default]',
        f'#[fg=cyan]{reqs}req#[default]',
        f'{tok_str}tok',
        f'\${cost:.3f}',
        f'{latency}ms',
    ]
    if c_count > 0:
        parts.append(f'#[fg=yellow]↺{c_count}#[default]')
    if last_err:
        parts.append(f'#[fg=red]{last_err}#[default]')

    print(' │ '.join(parts))
except Exception as e:
    print(f'#[fg=green]● PROXY#[default] #[fg=red]parse error#[default]')
" <<< "$stats"
}

# ── Headroom status line ──
status_headroom() {
    local health
    health=$(curl -sf --max-time 1 "$HEADROOM_URL/health" 2>/dev/null) || {
        echo "#[fg=red]● HEADROOM DOWN#[default]"
        return
    }

    # Headroom may expose stats at /stats or /metrics — try both
    local stats
    stats=$(curl -sf --max-time 2 "$HEADROOM_URL/stats" 2>/dev/null)
    if [ -z "$stats" ]; then
        stats=$(curl -sf --max-time 2 "$HEADROOM_URL/metrics" 2>/dev/null)
    fi

    if [ -z "$stats" ]; then
        # No stats endpoint — show basic health
        local mode="${HEADROOM_MODE:-token_headroom}"
        echo "#[fg=green]● HEADROOM#[default] │ mode:${mode} │ #[fg=cyan]healthy#[default]"
        return
    fi

    _python -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    s = d.get('summary', d)   # Headroom nests under 'summary'
    comp = s.get('compression', {}) if isinstance(s.get('compression'), dict) else {}
    avg_pct = comp.get('avg_compression_pct', 0) or 0
    saved = comp.get('total_tokens_removed', 0) or 0
    reqs = s.get('api_requests', 0) or 0
    reqs_compressed = comp.get('requests_compressed', 0) or 0
    cache_hits = (s.get('cache', {}) or {}).get('ccr_retrievals', 0) or 0

    if saved >= 1_000_000:
        saved_str = f'{saved/1_000_000:.1f}M'
    elif saved >= 1_000:
        saved_str = f'{saved/1_000:.1f}K'
    else:
        saved_str = str(saved)

    parts = [
        '#[fg=green]● HEADROOM#[default]',
        f'#[fg=cyan]{avg_pct:.0f}%#[default] compressed',
        f'saved:{saved_str}tok',
        f'{reqs_compressed}/{reqs}req',
    ]
    if cache_hits:
        parts.append(f'cache:{cache_hits}')

    print(' │ '.join(parts))
except Exception as e:
    print(f'#[fg=green]● HEADROOM#[default] │ #[fg=yellow]parse error: {e}#[default]')
" <<< "$stats"
}

# ── RTK status line ──
status_rtk() {
    local dir="${1:-$PWD}"
    if ! command -v rtk &>/dev/null; then
        echo "#[fg=yellow]● RTK NOT INSTALLED#[default]"
        return
    fi

    _python "$PROXY_DIR/scripts/status/rtk_status.py" \
        --scope project \
        --format tmux \
        --cwd "$dir" \
        --ttl 10 \
        --timeout 1.5 2>/dev/null || {
        echo "#[fg=green]● RTK#[default] │ #[fg=yellow](no data)#[default]"
    }
}

# ── Codex session status line ──
status_codex_right() {
    local dir="${1:-$PWD}"
    _python "$PROXY_DIR/scripts/status/codex_status.py" \
        --side right \
        --cwd "$dir" 2>/dev/null || {
        echo "#[fg=yellow]codex:no-session#[default]"
    }
}

# ── Dispatch ──
case "${1:-proxy}" in
    project)  shift; status_project "$@" ;;
    proxy)    status_proxy ;;
    headroom) status_headroom ;;
    rtk)      shift; status_rtk "$@" ;;
    codex_right) shift; status_codex_right "$@" ;;
    *)
        echo "Usage: tmux_status.sh {project [dir]|proxy|headroom|rtk|codex_right [dir]}"
        exit 1
        ;;
esac
