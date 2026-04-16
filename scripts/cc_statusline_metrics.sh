#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# cc_statusline_metrics.sh — Proxy metrics for Claude Code status line
#
# Outputs formatted metric chunks that can be appended to the Claude
# Code status line. Each function outputs a single formatted segment.
#
# Usage in ~/.claude/status-line.sh:
#   source /home/cheta/code/claude-code-proxy/scripts/cc_statusline_metrics.sh
#   local ph; ph=$(get_proxy_health); [ -n "$ph" ] && metrics+=("$ph")
#   local hr; hr=$(get_headroom_compression); [ -n "$hr" ] && metrics+=("$hr")
#   ...
#
# Or standalone:
#   cc_statusline_metrics.sh all    # print all segments joined
#   cc_statusline_metrics.sh health # proxy up/down only
# ═══════════════════════════════════════════════════════════════════

# Palette (matches ~/.claude/status-line.sh)
_CC_EMERALD='\033[38;2;16;185;129m'
_CC_EMERALD_DIM='\033[38;2;52;211;153m'
_CC_AMBER='\033[38;2;245;158;11m'
_CC_ROSE='\033[38;2;244;63;94m'
_CC_BLUE='\033[38;2;96;165;250m'
_CC_GRAY='\033[38;2;100;116;139m'
_CC_VIOLET='\033[38;2;139;92;246m'
_CC_RESET='\033[0m'

PROXY_URL="${PROXY_URL:-http://127.0.0.1:8082}"
HEADROOM_URL="${HEADROOM_URL:-http://127.0.0.1:8787}"

# Cache: refresh API polls every 5s to avoid hammering
_CACHE_DIR="/tmp/.cc_proxy_statusline_$$"
mkdir -p "$_CACHE_DIR" 2>/dev/null

_cached_fetch() {
    local url="$1" cache_key="$2" ttl="${3:-5}"
    local cache_file="$_CACHE_DIR/$cache_key"
    if [ -f "$cache_file" ]; then
        local age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || echo 0) ))
        if [ "$age" -lt "$ttl" ]; then
            cat "$cache_file"
            return
        fi
    fi
    local resp
    resp=$(curl -sf --max-time 1 "$url" 2>/dev/null) || return 1
    echo "$resp" | tee "$cache_file" 2>/dev/null
}

# ── Proxy health indicator (dot with color) ──
get_proxy_health() {
    if curl -sf --max-time 1 "$PROXY_URL/health" >/dev/null 2>&1; then
        echo -e "${_CC_EMERALD}● Proxy${_CC_RESET}"
    else
        echo -e "${_CC_ROSE}○ Proxy${_CC_RESET}"
    fi
}

# ── Headroom health indicator ──
get_headroom_health() {
    if curl -sf --max-time 1 "$HEADROOM_URL/health" >/dev/null 2>&1; then
        echo -e "${_CC_EMERALD}● HR${_CC_RESET}"
    else
        echo -e "${_CC_ROSE}○ HR${_CC_RESET}"
    fi
}

# ── Session tokens per second ──
get_tokens_per_sec() {
    local stats
    stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local tps
    tps=$(echo "$stats" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    tokens = d.get('total_tokens', 0)
    latency = d.get('avg_latency', 0)
    if latency > 0 and tokens > 0:
        # rough estimate: avg tokens/req ÷ avg seconds/req
        reqs = d.get('requests_today', 1) or 1
        avg_tok = tokens / reqs
        avg_sec = latency / 1000
        print(f'{avg_tok/avg_sec:.0f}' if avg_sec > 0 else '0')
    else:
        print('0')
except Exception:
    print('')
" 2>/dev/null)
    [ -z "$tps" ] || [ "$tps" = "0" ] && return
    echo -e "${_CC_VIOLET}󱐋 ${tps}tok/s${_CC_RESET}"
}

# ── Total session tokens ──
get_session_tokens() {
    local stats
    stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local tokens
    tokens=$(echo "$stats" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    t = d.get('total_tokens', 0)
    if t >= 1_000_000:
        print(f'{t/1_000_000:.1f}M')
    elif t >= 1_000:
        print(f'{t/1_000:.1f}K')
    else:
        print(str(t) if t else '')
except Exception:
    print('')
" 2>/dev/null)
    [ -z "$tokens" ] && return
    echo -e "${_CC_BLUE}󰊢 ${tokens}${_CC_RESET}"
}

# ── Tool call success/fail count (24h window) ──
get_tool_stats() {
    local tools
    tools=$(_cached_fetch "$PROXY_URL/api/metrics/tool-analytics?hours=24" tool_stats 10) || return
    local result
    result=$(echo "$tools" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if d.get('status') == 'no_data':
        print('')
        sys.exit(0)
    tstats = d.get('tools', d.get('tool_stats', {}))
    total_s = 0
    total_f = 0
    if isinstance(tstats, list):
        for t in tstats:
            total_s += t.get('success', 0)
            total_f += t.get('failure', t.get('fail', 0))
    elif isinstance(tstats, dict):
        for stats in tstats.values():
            total_s += stats.get('success', 0)
            total_f += stats.get('failure', stats.get('fail', 0))
    if total_s or total_f:
        print(f'{total_s}/{total_f}')
    else:
        print('')
except Exception:
    print('')
" 2>/dev/null)
    [ -z "$result" ] && return
    local success="${result%/*}" fail="${result#*/}"
    if [ "$fail" -gt 0 ]; then
        echo -e "${_CC_AMBER}󰠗 ${success}✓/${fail}✗${_CC_RESET}"
    else
        echo -e "${_CC_EMERALD_DIM}󰠗 ${success}✓${_CC_RESET}"
    fi
}

# ── Headroom compression % + tokens saved ──
get_headroom_savings() {
    local stats
    stats=$(_cached_fetch "$HEADROOM_URL/stats" hr_stats) || {
        stats=$(_cached_fetch "$HEADROOM_URL/metrics" hr_stats) || return
    }
    [ -z "$stats" ] && return
    local result
    result=$(echo "$stats" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    s = d.get('summary', d)
    comp = s.get('compression', {}) if isinstance(s.get('compression'), dict) else {}
    avg_pct = comp.get('avg_compression_pct', 0) or 0
    saved = comp.get('total_tokens_removed', 0) or 0
    if saved >= 1_000_000:
        s_str = f'{saved/1_000_000:.1f}M'
    elif saved >= 1_000:
        s_str = f'{saved/1_000:.1f}K'
    else:
        s_str = str(saved) if saved else '0'
    print(f'{avg_pct:.0f}%|{s_str}')
except Exception:
    print('')
" 2>/dev/null)
    [ -z "$result" ] || [ "$result" = "|" ] && return
    local pct="${result%|*}" saved="${result#*|}"
    echo -e "${_CC_EMERALD}󱐋 HR:${pct:-0%} (${saved:-0})${_CC_RESET}"
}

# ── RTK tokens saved this session ──
get_rtk_savings() {
    command -v rtk &>/dev/null || return
    local gain
    gain=$(rtk gain --format json 2>/dev/null) || return
    local result
    result=$(echo "$gain" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    s = d.get('summary', d)
    saved = s.get('total_saved', 0) or 0
    pct = s.get('avg_savings_pct', 0) or 0
    if saved >= 1_000_000:
        s_str = f'{saved/1_000_000:.1f}M'
    elif saved >= 1_000:
        s_str = f'{saved/1_000:.1f}K'
    else:
        s_str = str(saved) if saved else '0'
    print(f'{pct:.0f}%|{s_str}')
except Exception:
    print('')
" 2>/dev/null)
    [ -z "$result" ] || [ "$result" = "|" ] && return
    local pct="${result%|*}" saved="${result#*|}"
    echo -e "${_CC_EMERALD_DIM}󰚩 RTK:${pct:-0%} (${saved:-0})${_CC_RESET}"
}

# ── Last proxy error code/model ──
get_last_proxy_error() {
    local stats
    stats=$(_cached_fetch "$PROXY_URL/api/stats" stats) || return
    local err
    err=$(echo "$stats" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for r in d.get('recent_requests', []):
        if r.get('status') != 'success':
            model = r.get('model', '?')[:18]
            print(f'{model}')
            break
except Exception:
    pass
" 2>/dev/null)
    [ -z "$err" ] && return
    echo -e "${_CC_ROSE}⚠ ${err}${_CC_RESET}"
}

# ── Fixed-width model name (prevents status bar jumping) ──
# Usage: pass model name string, outputs padded to 12 chars visible width
get_fixed_width_model() {
    local model="${1:-?}"
    # Normalize to short form
    case "$model" in
        *opus*)       model="Opus" ;;
        *sonnet*)     model="Sonnet" ;;
        *haiku*)      model="Haiku" ;;
        *minimax*)    model="Minimax" ;;
        *nemotron*)   model="Nemotron" ;;
        *qwen*)       model="Qwen" ;;
        *gpt-oss*)    model="GPT-OSS" ;;
        *chimera*)    model="Chimera" ;;
        */*)          model="${model##*/}"; model="${model:0:10}" ;;
    esac
    # Pad to 10 chars
    printf "%-10s" "$model"
}

# ── Active routing mode ──
get_routing_mode() {
    local chain_file="/home/cheta/code/claude-code-proxy/config/proxy_chain.json"
    [ -f "$chain_file" ] || return
    local mode
    mode=$(python3 -c "
import json, sys
try:
    with open('$chain_file') as f:
        d = json.load(f)
    r = d.get('router', {})
    if r.get('_passthrough'):
        print('passthrough')
    elif r.get('_disabled'):
        print('tier-only')
    else:
        print('routing')
except Exception:
    pass
" 2>/dev/null)
    [ -z "$mode" ] && return
    case "$mode" in
        passthrough) echo -e "${_CC_AMBER}⇒ passthru${_CC_RESET}" ;;
        tier-only)   echo -e "${_CC_GRAY}⇒ tier${_CC_RESET}" ;;
        routing)     echo -e "${_CC_VIOLET}⇒ routed${_CC_RESET}" ;;
    esac
}

# ── Standalone dispatch (when sourced, this block is skipped) ──
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    case "${1:-all}" in
        health)        get_proxy_health ;;
        headroom)      get_headroom_health ;;
        tps)           get_tokens_per_sec ;;
        tokens)        get_session_tokens ;;
        tools)         get_tool_stats ;;
        hr-savings)    get_headroom_savings ;;
        rtk)           get_rtk_savings ;;
        error)         get_last_proxy_error ;;
        mode)          get_routing_mode ;;
        all)
            out=()
            h=$(get_proxy_health);       [ -n "$h" ] && out+=("$h")
            hr=$(get_headroom_health);   [ -n "$hr" ] && out+=("$hr")
            m=$(get_routing_mode);       [ -n "$m" ] && out+=("$m")
            t=$(get_session_tokens);     [ -n "$t" ] && out+=("$t")
            tool=$(get_tool_stats);      [ -n "$tool" ] && out+=("$tool")
            hrs=$(get_headroom_savings); [ -n "$hrs" ] && out+=("$hrs")
            rs=$(get_rtk_savings);       [ -n "$rs" ] && out+=("$rs")
            err=$(get_last_proxy_error); [ -n "$err" ] && out+=("$err")

            # Join with ' │ '
            SEP="  ${_CC_GRAY}│${_CC_RESET} "
            for i in "${!out[@]}"; do
                if [ "$i" -eq 0 ]; then
                    printf "%b" "${out[$i]}"
                else
                    printf "%b%b" "$SEP" "${out[$i]}"
                fi
            done
            echo
            ;;
        *)
            echo "Usage: $0 {health|headroom|tps|tokens|tools|hr-savings|rtk|error|mode|all}"
            exit 1
            ;;
    esac
    # Cleanup cache on exit
    trap "rm -rf '$_CACHE_DIR' 2>/dev/null" EXIT
fi
