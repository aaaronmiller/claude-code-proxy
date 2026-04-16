#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# statusline_render.sh — Universal Claude Code statusline renderer
#
# Reads stdin JSON (CC-supplied session info) + config JSON, renders
# the status line with left/right-anchored segments per line.
#
# Wire up in ~/.claude/settings.json:
#   "statusLine": {
#     "type": "command",
#     "command": "bash /home/cheta/code/claude-code-proxy/scripts/statusline_render.sh"
#   }
#
# Config at ~/.claude/statusline-config.json:
#   {
#     "separator": "│",
#     "sep_padding": 2,
#     "lines": [
#       {
#         "left":  [{"id": "model"}, {"id": "cwd"}, {"id": "git_branch"}],
#         "right": [{"id": "clock"}, {"id": "session_cost"}]
#       },
#       {
#         "left":  [{"id": "proxy_health"}, {"id": "headroom_savings"}],
#         "right": [{"id": "session_tokens"}, {"id": "tool_stats"}]
#       }
#     ]
#   }
# ═══════════════════════════════════════════════════════════════════

set -u  # No -e: segment failures should not kill the whole line

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${STATUSLINE_CONFIG:-$HOME/.claude/statusline-config.json}"

# Read stdin JSON once (used by CC-aware segments)
export CC_JSON=""
if [ ! -t 0 ]; then
    CC_JSON=$(command cat)
fi
export CC_JSON

# Source segment library
# shellcheck disable=SC1091
source "$_SCRIPT_DIR/statusline_segments.sh"

# Default config if none exists
_DEFAULT_CONFIG='{
  "separator": "│",
  "sep_padding": 2,
  "lines": [
    {
      "left":  [{"id": "model"}, {"id": "cwd"}, {"id": "git_branch"}],
      "right": [{"id": "clock"}]
    },
    {
      "left":  [{"id": "proxy_health"}, {"id": "headroom_health"}, {"id": "routing_mode"}],
      "right": [{"id": "session_tokens"}, {"id": "tool_stats"}, {"id": "headroom_savings"}]
    }
  ]
}'

if [ -f "$CONFIG_FILE" ]; then
    CONFIG=$(command cat "$CONFIG_FILE")
else
    CONFIG="$_DEFAULT_CONFIG"
fi

# Strip ANSI escape codes for visible-width measurement
_strip_ansi() {
    # POSIX-ish: use sed with ESC literal
    printf "%b" "$1" | sed -E $'s/\x1b\\[[0-9;]*[a-zA-Z]//g'
}

# Visible width counting wide Nerd Font glyphs as width=2 (approximation)
_vis_width() {
    local s; s=$(_strip_ansi "$1")
    python3 -c "
import sys, unicodedata
s = sys.argv[1]
w = 0
for c in s:
    # Nerd Font private use + CJK wide -> 2, else 1
    cp = ord(c)
    if unicodedata.east_asian_width(c) in ('W', 'F'):
        w += 2
    elif 0xE000 <= cp <= 0xF8FF or 0xF0000 <= cp <= 0xFFFFD:
        w += 2  # PUA (Nerd Font icons)
    else:
        w += 1
print(w)
" "$s" 2>/dev/null || echo ${#s}
}

# Extract config fields via python (jq may not be installed everywhere)
_cfg_fields() {
    echo "$CONFIG" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    sep = d.get('separator', '│')
    pad = d.get('sep_padding', 2)
    print(sep)
    print(pad)
    for i, line in enumerate(d.get('lines', [])):
        for side in ('left', 'right'):
            for seg in line.get(side, []):
                print(f'L{i}|{side}|{seg.get(\"id\", \"\")}')
except Exception as e:
    pass
" 2>/dev/null
}

_SEP="│"
_PAD=2
declare -A _LINE_LEFT  _LINE_RIGHT
declare -A _LINE_SEEN

# Parse config into associative arrays
_first=1
while IFS= read -r row; do
    if [ $_first -eq 1 ]; then _SEP="$row"; _first=2; continue; fi
    if [ $_first -eq 2 ]; then _PAD="$row"; _first=3; continue; fi
    IFS='|' read -r lineno side segid <<< "$row"
    _LINE_SEEN[$lineno]=1
    [ -z "$segid" ] && continue
    if [ "$side" = "left" ]; then
        _LINE_LEFT[$lineno]="${_LINE_LEFT[$lineno]:-} $segid"
    else
        _LINE_RIGHT[$lineno]="${_LINE_RIGHT[$lineno]:-} $segid"
    fi
done < <(_cfg_fields)

_TERM_W="${COLUMNS:-$(tput cols 2>/dev/null || echo 120)}"
_SEP_VIS="  ${_CC_GRAY}${_SEP}${_CC_RESET}  "
_JOIN_SPACE=$(command printf '%*s' "$_PAD" '')

# Join an array of rendered segments with separator
_join_segments() {
    local arr=("$@") out="" first=1
    for seg in "${arr[@]}"; do
        [ -z "$seg" ] && continue
        if [ $first -eq 1 ]; then
            out="$seg"; first=0
        else
            out="${out}${_JOIN_SPACE}${_CC_GRAY}${_SEP}${_CC_RESET}${_JOIN_SPACE}${seg}"
        fi
    done
    printf "%s" "$out"
}

# Render each configured line
for lineno in $(echo "${!_LINE_SEEN[@]}" | tr ' ' '\n' | command sort -n); do
    # Render left segments
    left_rendered=()
    for sid in ${_LINE_LEFT[$lineno]:-}; do
        out=$(seg_render "$sid")
        [ -n "$out" ] && left_rendered+=("$out")
    done
    left_str=$(_join_segments "${left_rendered[@]}")

    # Render right segments
    right_rendered=()
    for sid in ${_LINE_RIGHT[$lineno]:-}; do
        out=$(seg_render "$sid")
        [ -n "$out" ] && right_rendered+=("$out")
    done
    right_str=$(_join_segments "${right_rendered[@]}")

    if [ -n "$right_str" ]; then
        # Anchor right side at (terminal_width - visible_width)
        right_vis=$(_vis_width "$right_str")
        right_col=$(( _TERM_W - right_vis + 1 ))
        [ $right_col -lt 1 ] && right_col=1
        # Emit left, then cursor-move to right_col, then right
        command printf "%b" "$left_str"
        command printf '\033[%dG' "$right_col"
        command printf "%b" "$right_str"
        echo
    else
        command printf "%b\n" "$left_str"
    fi
done
