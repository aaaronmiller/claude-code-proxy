#!/usr/bin/env bash
# Unified Status Monitor for Proxy + Headroom Stack
# Usage: ./status-monitor.sh

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
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  CLAUDE CODE PROXY - STATUS MONITOR${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

check_service() {
    local name="$1"
    local url="$2"
    local response
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    local body=$(echo "$response" | head -n -1)
    local code=$(echo "$response" | tail -n 1)
    
    if [[ "$code" == "200" ]]; then
        echo -e "${GREEN}✓${NC} $name: Running (HTTP $code)"
        return 0
    else
        echo -e "${RED}✗${NC} $name: NOT RUNNING (HTTP $code)"
        return 1
    fi
}

# Get Claude Code sessions
get_claude_sessions() {
    local claude_dir="$HOME/.claude/sessions"
    if [[ -d "$claude_dir" ]]; then
        find "$claude_dir" -name "*.json" -type f 2>/dev/null | while read -r file; do
            local filename=$(basename "$file" .json)
            local modified=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
            local messages=$(python3 -c "import json; d=json.load(open('$file')); print(len(d.get('messages',[])))" 2>/dev/null || echo "0")
            local cwd=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('cwd','N/A'))" 2>/dev/null || echo "N/A")
            local duration=$(python3 -c "
import json, datetime
d=json.load(open('$file'))
msgs = d.get('messages',[])
if len(msgs) >= 2:
    first = msgs[0].get('timestamp',0)
    last = msgs[-1].get('timestamp',0)
    diff = last - first
    mins = int(diff // 60)
    secs = int(diff % 60)
    print(f'{mins}m {secs}s')
else:
    print('N/A')
" 2>/dev/null || echo "N/A")
            echo "$modified|Claude Code|$filename|$messages|$duration|$cwd"
        done
    fi
}

# Get Qwen Code sessions
get_qwen_sessions() {
    local qwen_dir="$HOME/.qwen/sessions"
    if [[ -d "$qwen_dir" ]]; then
        find "$qwen_dir" -name "*.json" -type f 2>/dev/null | while read -r file; do
            local filename=$(basename "$file" .json)
            local modified=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
            local messages=$(python3 -c "import json; d=json.load(open('$file')); print(len(d.get('messages',[])))" 2>/dev/null || echo "0")
            local cwd=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('cwd','N/A'))" 2>/dev/null || echo "N/A")
            local duration=$(python3 -c "
import json
d=json.load(open('$file'))
msgs = d.get('messages',[])
if len(msgs) >= 2:
    first = msgs[0].get('timestamp',0)
    last = msgs[-1].get('timestamp',0)
    diff = last - first
    mins = int(diff // 60)
    secs = int(diff % 60)
    print(f'{mins}m {secs}s')
else:
    print('N/A')
" 2>/dev/null || echo "N/A")
            echo "$modified|Qwen Code|$filename|$messages|$duration|$cwd"
        done
    fi
}

# Get Codex CLI sessions
get_codex_sessions() {
    local codex_dir="$HOME/.codex/sessions"
    if [[ -d "$codex_dir" ]]; then
        find "$codex_dir" -name "*.json" -type f 2>/dev/null | while read -r file; do
            local filename=$(basename "$file" .json)
            local modified=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
            local messages=$(python3 -c "import json; d=json.load(open('$file')); print(len(d.get('messages',[])))" 2>/dev/null || echo "0")
            local cwd=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('cwd','N/A'))" 2>/dev/null || echo "N/A")
            local duration=$(python3 -c "
import json
d=json.load(open('$file'))
msgs = d.get('messages',[])
if len(msgs) >= 2:
    first = msgs[0].get('timestamp',0)
    last = msgs[-1].get('timestamp',0)
    diff = last - first
    mins = int(diff // 60)
    secs = int(diff % 60)
    print(f'{mins}m {secs}s')
else:
    print('N/A')
" 2>/dev/null || echo "N/A")
            echo "$modified|Codex CLI|$filename|$messages|$duration|$cwd"
        done
    fi
}

# Get OpenCode sessions
get_opencode_sessions() {
    local opencode_dir="$HOME/.opencode/sessions"
    if [[ -d "$opencode_dir" ]]; then
        find "$opencode_dir" -name "*.json" -type f 2>/dev/null | while read -r file; do
            local filename=$(basename "$file" .json)
            local modified=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo "0")
            local messages=$(python3 -c "import json; d=json.load(open('$file')); print(len(d.get('messages',[])))" 2>/dev/null || echo "0")
            local cwd=$(python3 -c "import json; d=json.load(open('$file')); print(d.get('cwd','N/A'))" 2>/dev/null || echo "N/A")
            local duration=$(python3 -c "
import json
d=json.load(open('$file'))
msgs = d.get('messages',[])
if len(msgs) >= 2:
    first = msgs[0].get('timestamp',0)
    last = msgs[-1].get('timestamp',0)
    diff = last - first
    mins = int(diff // 60)
    secs = int(diff % 60)
    print(f'{mins}m {secs}s')
else:
    print('N/A')
" 2>/dev/null || echo "N/A")
            echo "$modified|OpenCode|$filename|$messages|$duration|$cwd"
        done
    fi
}

# Get all sessions sorted by timestamp (newest first)
get_all_sessions() {
    {
        get_claude_sessions
        get_qwen_sessions
        get_codex_sessions
        get_opencode_sessions
    } | sort -t'|' -k1 -rn | head -15
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

print_header

echo -e "${BLUE}=== SERVICE HEALTH ===${NC}"
echo ""

# Check services
PROXY_OK=false
HEADROOM_OK=false
HEADROOM_SMALL_OK=false

if check_service "Proxy (8082)" "http://127.0.0.1:8082/health"; then
    PROXY_OK=true
fi

if check_service "Headroom Default (8787)" "http://127.0.0.1:8787/health"; then
    HEADROOM_OK=true
fi

if check_service "Headroom Small (8790)" "http://127.0.0.1:8790/health"; then
    HEADROOM_SMALL_OK=true
fi

echo ""
echo -e "${BLUE}=== CONFIGURATION ===${NC}"
echo ""

# Load config
cd /home/misscheta/code/claude-code-proxy
source .venv/bin/activate 2>/dev/null || true
source .envrc 2>/dev/null || true

echo "BIG_MODEL:    ${YELLOW}${BIG_MODEL:-NOT SET}${NC}"
echo "MIDDLE_MODEL: ${YELLOW}${MIDDLE_MODEL:-NOT SET}${NC}"
echo "SMALL_MODEL:  ${YELLOW}${SMALL_MODEL:-NOT SET}${NC}"
echo ""

echo -e "${BLUE}=== COMPRESSION STATUS ===${NC}"
echo ""

if $HEADROOM_OK; then
    HEALTH=$(curl -s http://127.0.0.1:8787/health 2>/dev/null)
    OPTIMIZE=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('config',{}).get('optimize',False))" 2>/dev/null || echo "unknown")
    
    if [[ "$OPTIMIZE" == "True" ]]; then
        echo -e "Default Tier: ${GREEN}Compression ENABLED${NC}"
    else
        echo -e "Default Tier: ${YELLOW}Compression DISABLED (passthrough)${NC}"
    fi
else
    echo -e "Default Tier: ${RED}Service not running${NC}"
fi

if $HEADROOM_SMALL_OK; then
    HEALTH=$(curl -s http://127.0.0.1:8790/health 2>/dev/null)
    OPTIMIZE=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('config',{}).get('optimize',False))" 2>/dev/null || echo "unknown")
    
    if [[ "$OPTIMIZE" == "True" ]]; then
        echo -e "Small Tier:   ${GREEN}Compression ENABLED${NC}"
    else
        echo -e "Small Tier:   ${YELLOW}Compression DISABLED (passthrough)${NC}"
    fi
else
    echo -e "Small Tier:   ${RED}Service not running${NC}"
fi

echo ""
echo -e "${MAGENTA}=== RECENT SESSIONS (All CLI Tools) ===${NC}"
echo ""

# Table header
printf "${WHITE}%-12s %-14s %-10s %-8s %-10s %s${NC}\n" "TOOL" "SESSION" "MESSAGES" "DURATION" "AGE" "WORKSPACE"
echo "--------------------------------------------------------------------------------"

# Get and display sessions
get_all_sessions | while IFS='|' read -r timestamp tool session messages duration cwd; do
    if [[ -n "$timestamp" && "$timestamp" != "0" ]]; then
        age=$(format_time "$timestamp")
        
        # Truncate session ID if too long
        session_short="${session:0:12}"
        if [[ ${#session} -gt 12 ]]; then
            session_short="${session_short}..."
        fi
        
        # Truncate cwd if too long
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
        if [[ "$messages" -gt 100 ]]; then
            msg_col="${RED}$messages${NC}"
        elif [[ "$messages" -gt 50 ]]; then
            msg_col="${YELLOW}$messages${NC}"
        else
            msg_col="${GREEN}$messages${NC}"
        fi
        
        printf "%-12b %-14s %-10b %-8s %-10s %s\n" "$tool_col" "$session_short" "$msg_col" "$duration" "$age" "$cwd_short"
    fi
done

echo ""
echo -e "${BLUE}=== RECENT ACTIVITY ===${NC}"
echo ""

# Proxy logs
if [[ -f /home/misscheta/code/claude-code-proxy/proxy.log ]]; then
    echo "Last 5 proxy requests:"
    tail -20 /home/misscheta/code/claude-code-proxy/proxy.log 2>/dev/null | grep -E "POST.*messages|200 OK|ERROR" | tail -5 | while read -r line; do
        if [[ "$line" == *"ERROR"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ "$line" == *"200 OK"* ]]; then
            echo -e "${GREEN}$line${NC}"
        else
            echo "$line"
        fi
    done
else
    echo "  (no proxy logs found)"
fi

echo ""

# Headroom logs
if [[ -f ~/.local/share/headroom/proxy-default.jsonl ]] && [[ -s ~/.local/share/headroom/proxy-default.jsonl ]]; then
    echo "Last 5 headroom events:"
    tail -5 ~/.local/share/headroom/proxy-default.jsonl 2>/dev/null | head -5 || echo "  (no events)"
else
    echo "Headroom logs: (empty or not found)"
fi

echo ""
echo -e "${BLUE}=== QUICK COMMANDS ===${NC}"
echo ""
echo "Proxy Dashboard:  ${CYAN}open http://localhost:8082${NC}"
echo "Proxy Logs:       ${CYAN}tail -f ~/code/claude-code-proxy/proxy.log${NC}"
echo "Headroom Logs:    ${CYAN}tail -f ~/.local/share/headroom/proxy-default.jsonl${NC}"
echo "Test Request:     ${CYAN}cd ~/code/claude-code-proxy && ./test-request.sh${NC}"
echo "Restart Stack:    ${CYAN}./debug-full-stack.sh${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
