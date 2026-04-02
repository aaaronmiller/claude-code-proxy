#!/usr/bin/env bash
# Headroom Compression Stack Monitor
# Shows compression stats, token savings, and CLI session activity
# Usage: ./compression-status.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   HEADROOM COMPRESSION - STATUS MONITOR   ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if headroom is running
check_headroom() {
    local port="$1"
    local name="$2"
    
    local response=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:$port/health" 2>/dev/null || echo -e "\n000")
    local code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | head -n -1)
    
    if [[ "$code" == "200" ]]; then
        local optimize=$(echo "$body" | python3 -c "import sys,json; print('✓ ON' if json.load(sys.stdin).get('config',{}).get('optimize',False) else '✗ OFF')" 2>/dev/null || echo "?")
        local cache=$(echo "$body" | python3 -c "import sys,json; print('✓' if json.load(sys.stdin).get('config',{}).get('cache',False) else '✗')" 2>/dev/null || echo "?")
        echo -e "${GREEN}✓${NC} $name (:$port): Compression $optimize | Cache: $cache"
        return 0
    else
        echo -e "${RED}✗${NC} $name (:$port): NOT RUNNING"
        return 1
    fi
}

# Get compression stats from headroom logs
get_compression_stats() {
    local log_file="$1"
    
    if [[ ! -f "$log_file" || ! -s "$log_file" ]]; then
        echo "0|0|0|0"
        return
    fi
    
    # Count total requests, compressed requests, tokens saved
    python3 << EOF
import json
import sys

total = 0
compressed = 0
tokens_in = 0
tokens_out = 0

try:
    with open('$log_file', 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                total += 1
                
                # Check for compression events
                if 'compression' in event or 'compressed' in event or 'optimize' in event:
                    compressed += 1
                
                # Count tokens if available
                if 'tokens_in' in event:
                    tokens_in += event.get('tokens_in', 0)
                if 'tokens_out' in event:
                    tokens_out += event.get('tokens_out', 0)
                if 'input_tokens' in event:
                    tokens_in += event.get('input_tokens', 0)
                if 'output_tokens' in event:
                    tokens_out += event.get('output_tokens', 0)
            except json.JSONDecodeError:
                continue
except Exception as e:
    pass

print(f"{total}|{compressed}|{tokens_in}|{tokens_out}")
EOF
}

# Get CLI sessions with message counts
get_cli_sessions() {
    # Claude Code sessions
    if [[ -d "$HOME/.claude/sessions" ]]; then
        find "$HOME/.claude/sessions" -name "*.json" -type f -exec stat -c "%Y|%n|Claude Code" {} \; 2>/dev/null
    fi
    
    # Qwen Code sessions
    if [[ -d "$HOME/.qwen/sessions" ]]; then
        find "$HOME/.qwen/sessions" -name "*.json" -type f -exec stat -c "%Y|%n|Qwen Code" {} \; 2>/dev/null
    fi
    
    # Codex CLI sessions
    if [[ -d "$HOME/.codex/sessions" ]]; then
        find "$HOME/.codex/sessions" -name "*.json" -type f -exec stat -c "%Y|%n|Codex CLI" {} \; 2>/dev/null
    fi
    
    # OpenCode sessions
    if [[ -d "$HOME/.opencode/sessions" ]]; then
        find "$HOME/.opencode/sessions" -name "*.json" -type f -exec stat -c "%Y|%n|OpenCode" {} \; 2>/dev/null
    fi
}

# Format file size
format_size() {
    local bytes="$1"
    if [[ $bytes -gt 1073741824 ]]; then
        echo "$(echo "scale=1; $bytes/1073741824" | bc)GB"
    elif [[ $bytes -gt 1048576 ]]; then
        echo "$(echo "scale=1; $bytes/1048576" | bc)MB"
    elif [[ $bytes -gt 1024 ]]; then
        echo "$(echo "scale=1; $bytes/1024" | bc)KB"
    else
        echo "${bytes}B"
    fi
}

# Format timestamp to human readable
format_time() {
    local ts="$1"
    local now=$(date +%s)
    local diff=$((now - ts))
    
    if [[ $diff -lt 60 ]]; then
        echo "${diff}s ago"
    elif [[ $diff -lt 3600 ]]; then
        echo "$((diff / 60))m ago"
    elif [[ $diff -lt 86400 ]]; then
        echo "$((diff / 3600))h ago"
    else
        echo "$((diff / 86400))d ago"
    fi
}

# Get session details
get_session_details() {
    local file="$1"
    local tool="$2"
    
    # Get file info
    local modified=$(stat -c %Y "$file" 2>/dev/null || echo "0")
    local size=$(stat -c %s "$file" 2>/dev/null || echo "0")
    local cwd="N/A"
    local messages="0"
    
    # Try to extract info from session file
    if [[ -f "$file" ]]; then
        cwd=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('cwd', d.get('workspace', 'N/A')))" 2>/dev/null || echo "N/A")
        
        # Count messages based on tool
        case "$tool" in
            "Claude Code")
                messages=$(python3 -c "
import json
try:
    d=json.load(open('$file'))
    # Claude Code stores messages differently
    msgs = d.get('messages', [])
    print(len(msgs))
except:
    print('0')
" 2>/dev/null || echo "0")
                ;;
            "Qwen Code")
                messages=$(python3 -c "
import json
try:
    d=json.load(open('$file'))
    msgs = d.get('messages', [])
    print(len(msgs))
except:
    print('0')
" 2>/dev/null || echo "0")
                ;;
            *)
                messages="?"
                ;;
        esac
    fi
    
    echo "$modified|$messages|$size|$cwd"
}

print_header

echo -e "${BLUE}=== HEADROOM COMPRESSION STATUS ===${NC}"
echo ""

DEFAULT_OK=false
SMALL_OK=false

check_headroom 8787 "Default" && DEFAULT_OK=true
check_headroom 8790 "Small" && SMALL_OK=true

echo ""
echo -e "${BLUE}=== COMPRESSION METRICS ===${NC}"
echo ""

# Default tier stats
if [[ -f "$HOME/.local/share/headroom/proxy-default.jsonl" ]]; then
    stats=$(get_compression_stats "$HOME/.local/share/headroom/proxy-default.jsonl")
    IFS='|' read -r total compressed tokens_in tokens_out <<< "$stats"
    
    echo -e "${CYAN}Default Tier (8787):${NC}"
    echo "  Total Requests:    $total"
    echo "  Compression Events: $compressed"
    echo "  Tokens In:         $tokens_in"
    echo "  Tokens Out:        $tokens_out"
    
    if [[ $tokens_in -gt 0 && $tokens_out -gt 0 ]]; then
        local ratio=$(echo "scale=1; $tokens_out * 100 / $tokens_in" | bc 2>/dev/null || echo "N/A")
        echo "  Compression Ratio: ${ratio}%"
    fi
else
    echo -e "${YELLOW}Default Tier: No compression logs yet${NC}"
fi

echo ""

# Small tier stats
if [[ -f "$HOME/.local/share/headroom/proxy-small.jsonl" ]]; then
    stats=$(get_compression_stats "$HOME/.local/share/headroom/proxy-small.jsonl")
    IFS='|' read -r total compressed tokens_in tokens_out <<< "$stats"
    
    echo -e "${CYAN}Small Tier (8790):${NC}"
    echo "  Total Requests:    $total"
    echo "  Compression Events: $compressed"
    echo "  Tokens In:         $tokens_in"
    echo "  Tokens Out:        $tokens_out"
else
    echo -e "${YELLOW}Small Tier: No compression logs yet${NC}"
fi

echo ""
echo -e "${BLUE}=== LOG FILE SIZES ===${NC}"
echo ""

for log_file in \
    "$HOME/.local/share/headroom/proxy-default.jsonl" \
    "$HOME/.local/share/headroom/proxy-small.jsonl" \
    "$HOME/.local/share/headroom/headroom-default.out" \
    "$HOME/.local/share/headroom/headroom-small.out"
do
    if [[ -f "$log_file" ]]; then
        size=$(stat -c %s "$log_file" 2>/dev/null || echo "0")
        lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
        echo "  $(basename "$log_file"): $(format_size $size) ($lines lines)"
    else
        echo "  $(basename "$log_file"): (empty)"
    fi
done

echo ""
echo -e "${MAGENTA}=== CLI SESSIONS (By Activity) ===${NC}"
echo ""

# Table header
printf "${WHITE}%-12s %-14s %-8s %-10s %-10s %s${NC}\n" "TOOL" "SESSION" "MSG" "SIZE" "AGE" "WORKSPACE"
echo "--------------------------------------------------------------------------------"

# Get sessions sorted by modification time (newest first)
get_cli_sessions | sort -t'|' -k1 -rn | head -15 | while IFS='|' read -r timestamp file tool; do
    if [[ -n "$timestamp" && "$timestamp" != "0" ]]; then
        details=$(get_session_details "$file" "$tool")
        IFS='|' read -r mod_time messages size cwd <<< "$details"
        
        age=$(format_time "$timestamp")
        session_name=$(basename "$file" .json)
        session_short="${session_name:0:12}"
        
        # Truncate cwd
        cwd_short="$cwd"
        if [[ ${#cwd} -gt 35 ]]; then
            cwd_short="...${cwd: -32}"
        fi
        
        # Color tool name
        case "$tool" in
            "Claude Code") tool_col="${GREEN}$tool${NC}" ;;
            "Qwen Code")   tool_col="${CYAN}$tool${NC}" ;;
            "Codex CLI")   tool_col="${YELLOW}$tool${NC}" ;;
            "OpenCode")    tool_col="${MAGENTA}$tool${NC}" ;;
            *)             tool_col="$tool" ;;
        esac
        
        # Color message count
        if [[ "$messages" != "?" && "$messages" -gt 100 ]]; then
            msg_col="${RED}$messages${NC}"
        elif [[ "$messages" != "?" && "$messages" -gt 50 ]]; then
            msg_col="${YELLOW}$messages${NC}"
        else
            msg_col="${GREEN}$messages${NC}"
        fi
        
        size_fmt=$(format_size "$size")
        
        printf "%-12b %-14s %-8b %-10s %-10s %s\n" "$tool_col" "$session_short" "$msg_col" "$size_fmt" "$age" "$cwd_short"
    fi
done

echo ""
echo -e "${BLUE}=== QUICK COMMANDS ===${NC}"
echo ""
echo "Headroom Default Logs: ${CYAN}tail -f ~/.local/share/headroom/proxy-default.jsonl${NC}"
echo "Headroom Small Logs:   ${CYAN}tail -f ~/.local/share/headroom/proxy-small.jsonl${NC}"
echo "Health Check:          ${CYAN}curl http://127.0.0.1:8787/health${NC}"
echo "Restart Headroom:      ${CYAN}headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
