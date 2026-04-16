#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# statusline_segments.sh — All available status-line segment renderers
#
# Each segment is a bash function named `seg_<id>()` that prints exactly
# one formatted chunk of output (with ANSI color codes) or empty string
# if the segment should be skipped.
#
# Two input sources:
#   1. Stdin JSON from Claude Code (set in $CC_JSON env before dispatch)
#   2. Live APIs (proxy, headroom, rtk) — cached 5s in /tmp
#
# Listing: seg_list        — prints `id|label|sample_output` for TUI
# Dispatch: seg_render <id> — prints rendered segment
# ═══════════════════════════════════════════════════════════════════

# Source shared proxy metric functions (provides get_* helpers + palette)
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$_SCRIPT_DIR/cc_statusline_metrics.sh"

# Additional palette entries not in cc_statusline_metrics.sh
_CC_BLUE_DIM='\033[38;2;96;165;250m'
_CC_BLUE_PRI='\033[38;2;59;130;246m'
_CC_AMBER_HOT='\033[38;2;252;211;77m'
_CC_BOLD='\033[1m'

# CC_JSON is populated by the renderer from stdin (avoid re-reading stdin)
CC_JSON="${CC_JSON:-}"

_json_field() {
    local path="$1"
    [ -z "$CC_JSON" ] && return
    echo "$CC_JSON" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for k in '$path'.split('.'):
        if d is None: break
        d = d.get(k) if isinstance(d, dict) else None
    print(d if d is not None else '')
except Exception:
    pass
" 2>/dev/null
}

# ── CC stdin-JSON segments ───────────────────────────────────────────
seg_model() {
    local m; m=$(_json_field "model.display_name")
    [ -z "$m" ] && m=$(_json_field "model.id")
    [ -z "$m" ] && return
    # Normalize to 10-char padded short form — prevents layout jitter
    local short
    short=$(get_fixed_width_model "$m")
    echo -e "${_CC_VIOLET}󰚩 ${short}${_CC_RESET}"
}

seg_cwd() {
    local p; p=$(_json_field "workspace.current_dir")
    [ -z "$p" ] && p="$PWD"
    # Collapse $HOME -> ~ and show only basename (stable width)
    p="${p/#$HOME/~}"
    local base="${p##*/}"
    [ -z "$base" ] && base="$p"
    echo -e "${_CC_BLUE_DIM}󰉋 ${base}${_CC_RESET}"
}

seg_cwd_full() {
    local p; p=$(_json_field "workspace.current_dir")
    [ -z "$p" ] && p="$PWD"
    p="${p/#$HOME/~}"
    echo -e "${_CC_BLUE_DIM}󰉋 ${p}${_CC_RESET}"
}

seg_git_branch() {
    local dir; dir=$(_json_field "workspace.current_dir")
    [ -z "$dir" ] && dir="$PWD"
    local branch
    branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null) || return
    [ "$branch" = "HEAD" ] && branch=$(git -C "$dir" rev-parse --short HEAD 2>/dev/null)
    [ -z "$branch" ] && return
    # Show dirty indicator
    local dirty=""
    if ! git -C "$dir" diff --quiet 2>/dev/null || ! git -C "$dir" diff --cached --quiet 2>/dev/null; then
        dirty="${_CC_AMBER}*${_CC_RESET}"
    fi
    echo -e "${_CC_EMERALD_DIM} ${branch}${dirty}${_CC_RESET}"
}

seg_session_cost() {
    local c; c=$(_json_field "cost.total_cost_usd")
    [ -z "$c" ] || [ "$c" = "0" ] && return
    local formatted
    formatted=$(python3 -c "print(f'\${float(\"$c\"):.3f}')" 2>/dev/null)
    echo -e "${_CC_AMBER}${formatted}${_CC_RESET}"
}

seg_transcript_lines() {
    local path; path=$(_json_field "transcript_path")
    [ -z "$path" ] || [ ! -f "$path" ] && return
    local lines
    lines=$(command wc -l < "$path" 2>/dev/null)
    [ -z "$lines" ] && return
    echo -e "${_CC_GRAY}󰆓 ${lines}L${_CC_RESET}"
}

seg_clock() {
    echo -e "${_CC_GRAY}󰔚 $(date +%H:%M)${_CC_RESET}"
}

# ── System segments ──────────────────────────────────────────────────
seg_cpu() {
    local pct
    pct=$(command cat /proc/loadavg 2>/dev/null | awk '{printf "%.0f", $1*100/'"$(command nproc)"'}')
    [ -z "$pct" ] && return
    local color="$_CC_EMERALD_DIM"
    [ "$pct" -gt 70 ] && color="$_CC_AMBER"
    [ "$pct" -gt 90 ] && color="$_CC_ROSE"
    echo -e "${color}⚡ ${pct}%${_CC_RESET}"
}

seg_memory() {
    local pct
    pct=$(command free 2>/dev/null | awk '/^Mem:/ {printf "%.0f", $3/$2*100}')
    [ -z "$pct" ] && return
    local color="$_CC_EMERALD_DIM"
    [ "$pct" -gt 75 ] && color="$_CC_AMBER"
    [ "$pct" -gt 90 ] && color="$_CC_ROSE"
    echo -e "${color}󰍛 ${pct}%${_CC_RESET}"
}

seg_disk() {
    local pct
    pct=$(command df -h / 2>/dev/null | awk 'NR==2 {gsub("%",""); print $5}')
    [ -z "$pct" ] && return
    local color="$_CC_EMERALD_DIM"
    [ "$pct" -gt 80 ] && color="$_CC_AMBER"
    [ "$pct" -gt 95 ] && color="$_CC_ROSE"
    echo -e "${color}󰋊 ${pct}%${_CC_RESET}"
}

# ── Proxy segments (re-exported from cc_statusline_metrics.sh) ───────
seg_proxy_health()     { get_proxy_health; }
seg_headroom_health()  { get_headroom_health; }
seg_tokens_per_sec()   { get_tokens_per_sec; }
seg_session_tokens()   { get_session_tokens; }
seg_tool_stats()       { get_tool_stats; }
seg_headroom_savings() { get_headroom_savings; }
seg_rtk_savings()      { get_rtk_savings; }
seg_last_proxy_error() { get_last_proxy_error; }
seg_routing_mode()     { get_routing_mode; }

# Extra proxy-derived segments not in cc_statusline_metrics.sh
seg_proxy_requests() {
    local stats; stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local r; r=$(echo "$stats" | python3 -c "
import json, sys
try: print(json.load(sys.stdin).get('requests_today', 0))
except: print('')
" 2>/dev/null)
    [ -z "$r" ] || [ "$r" = "0" ] && return
    echo -e "${_CC_BLUE_PRI}󰁨 ${r}req${_CC_RESET}"
}

seg_proxy_cost() {
    local stats; stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local c; c=$(echo "$stats" | python3 -c "
import json, sys
try:
    v = json.load(sys.stdin).get('est_cost', 0)
    print(f'{float(v):.3f}' if v else '')
except: print('')
" 2>/dev/null)
    [ -z "$c" ] || [ "$c" = "0.000" ] && return
    echo -e "${_CC_AMBER}\$${c}${_CC_RESET}"
}

seg_proxy_latency() {
    local stats; stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local l; l=$(echo "$stats" | python3 -c "
import json, sys
try: print(int(json.load(sys.stdin).get('avg_latency', 0)))
except: print('')
" 2>/dev/null)
    [ -z "$l" ] || [ "$l" = "0" ] && return
    local color="$_CC_EMERALD_DIM"
    [ "$l" -gt 2000 ] && color="$_CC_AMBER"
    [ "$l" -gt 5000 ] && color="$_CC_ROSE"
    echo -e "${color}󱎫 ${l}ms${_CC_RESET}"
}

seg_cascade_events() {
    local stats; stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local c; c=$(echo "$stats" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    events = d.get('cascade', {}).get('events', [])
    print(len(events) if events else '')
except: print('')
" 2>/dev/null)
    [ -z "$c" ] || [ "$c" = "0" ] && return
    echo -e "${_CC_AMBER_HOT}↺${c}${_CC_RESET}"
}

# ── Segment registry (id|label|category|sample) ──────────────────────
# Used by the TUI to show options + sample output for preview.
seg_list() {
    cat <<'EOF'
model|Model name|CC|󰚩 Opus
cwd|Working dir (basename)|CC|󰉋 project
cwd_full|Working dir (full)|CC|󰉋 ~/code/project
git_branch|Git branch|CC| main*
session_cost|Session cost (from CC)|CC|$0.023
transcript_lines|Transcript lines|CC|󰆓 342L
clock|Clock (HH:MM)|CC|󰔚 14:32
cpu|CPU load %|System|⚡ 45%
memory|Memory %|System|󰍛 67%
disk|Disk %|System|󰋊 38%
proxy_health|Proxy up/down|Proxy|● Proxy
headroom_health|Headroom up/down|Proxy|● HR
routing_mode|Routing mode|Proxy|⇒ routed
proxy_requests|Proxy requests today|Proxy|󰁨 45req
proxy_cost|Proxy cost today|Proxy|$0.023
proxy_latency|Proxy avg latency|Proxy|󱎫 340ms
cascade_events|Cascade fallback count|Proxy|↺2
tokens_per_sec|Tokens/sec|Proxy|󱐋 240tok/s
session_tokens|Session tokens|Proxy|󰊢 182.3K
tool_stats|Tool success/fail|Proxy|󰠗 45✓/2✗
headroom_savings|Headroom compression|Compression|󱐋 HR:67% (12.4K)
rtk_savings|RTK compression|Compression|󰚩 RTK:78% (45.2K)
last_proxy_error|Last error|Proxy|⚠ gpt-oss-120b
EOF
}

# Dispatch by id
seg_render() {
    local id="$1"
    local fn="seg_$id"
    if declare -F "$fn" >/dev/null 2>&1; then
        "$fn"
    fi
}

# Standalone testing
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    case "${1:-list}" in
        list)   seg_list ;;
        render) shift; seg_render "$@" ;;
        all)
            while IFS='|' read -r id label cat sample; do
                printf "%-20s %-25s " "$id" "[$cat]"
                out=$(seg_render "$id")
                if [ -n "$out" ]; then
                    printf "%b\n" "$out"
                else
                    printf "(empty)\n"
                fi
            done < <(seg_list)
            ;;
        *) echo "Usage: $0 {list|render <id>|all}" ;;
    esac
fi
