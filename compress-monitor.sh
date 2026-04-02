#!/usr/bin/env bash
# Full Compression Stack Monitor - Headroom + RTK
# CLI and Web UI status for compression layers
# Usage: ./compress-monitor.sh [--web]

set -euo pipefail

WEB_MODE=false
if [[ "${1:-}" == "--web" ]]; then
    WEB_MODE=true
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================

# Get Headroom health
get_headroom_health() {
    local port="$1"
    local response=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:$port/health" 2>/dev/null || echo -e "\n000")
    local code=$(echo "$response" | tail -n 1)
    
    if [[ "$code" == "200" ]]; then
        local body=$(echo "$response" | head -n -1)
        local optimize=$(echo "$body" | python3 -c "import sys,json; print('true' if json.load(sys.stdin).get('config',{}).get('optimize',False) else 'false')" 2>/dev/null || echo "false")
        local cache=$(echo "$body" | python3 -c "import sys,json; print('true' if json.load(sys.stdin).get('config',{}).get('cache',False) else 'false')" 2>/dev/null || echo "false")
        echo "{\"running\":true,\"optimize\":$optimize,\"cache\":$cache}"
    else
        echo "{\"running\":false,\"optimize\":false,\"cache\":false}"
    fi
}

# Get RTK status
get_rtk_status() {
    if command -v rtk >/dev/null 2>&1; then
        local version=$(rtk --version 2>/dev/null || echo "unknown")
        local history=$(rtk gain --history 2>/dev/null | head -20 || echo "")
        echo "{\"installed\":true,\"version\":\"$version\"}"
    else
        echo "{\"installed\":false,\"version\":null}"
    fi
}

# Get compression stats from headroom logs
get_headroom_stats() {
    local log_file="$1"
    
    if [[ ! -f "$log_file" || ! -s "$log_file" ]]; then
        echo '{"requests":0,"compressed":0,"tokens_in":0,"tokens_out":0}'
        return
    fi
    
    python3 << EOF
import json
stats = {"requests": 0, "compressed": 0, "tokens_in": 0, "tokens_out": 0}
try:
    with open('$log_file', 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                stats["requests"] += 1
                if any(k in str(event).lower() for k in ["compress", "optimize", "save"]):
                    stats["compressed"] += 1
                stats["tokens_in"] += event.get("tokens_in", event.get("input_tokens", 0))
                stats["tokens_out"] += event.get("tokens_out", event.get("output_tokens", 0))
            except:
                continue
except:
    pass
print(json.dumps(stats))
EOF
}

# Get CLI sessions
get_cli_sessions() {
    python3 << 'EOF'
import os
import json
from pathlib import Path
from datetime import datetime

sessions = []

# Session directories to check
session_dirs = [
    (Path.home() / ".claude" / "sessions", "Claude Code"),
    (Path.home() / ".qwen" / "sessions", "Qwen Code"),
    (Path.home() / ".codex" / "sessions", "Codex CLI"),
    (Path.home() / ".opencode" / "sessions", "OpenCode"),
]

for session_dir, tool_name in session_dirs:
    if not session_dir.exists():
        continue
    
    for session_file in session_dir.glob("*.json"):
        try:
            stat = session_file.stat()
            with open(session_file) as f:
                data = json.load(f)
            
            sessions.append({
                "tool": tool_name,
                "session": session_file.stem,
                "modified": int(stat.st_mtime),
                "size": stat.st_size,
                "messages": len(data.get("messages", [])),
                "cwd": data.get("cwd", data.get("workspace", "N/A")),
                "file": str(session_file)
            })
        except:
            continue

# Sort by modification time (newest first)
sessions.sort(key=lambda x: x["modified"], reverse=True)
print(json.dumps(sessions[:20]))
EOF
}

# Get RTK compression stats
get_rtk_stats() {
    python3 << 'EOF'
import subprocess
import json

stats = {"total_compressions": 0, "tokens_saved": 0, "last_compression": None}

try:
    # Try to get RTK history
    result = subprocess.run(["rtk", "gain", "--history"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        stats["total_compressions"] = len([l for l in lines if l.strip()])
        
        # Parse token savings if available
        for line in lines:
            if "tokens" in line.lower():
                try:
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            stats["tokens_saved"] += int(part)
                except:
                    pass
        
        if lines and lines[0].strip():
            stats["last_compression"] = lines[0].strip()[:100]
except:
    pass

print(json.dumps(stats))
EOF
}

# ============================================================================
# CLI OUTPUT
# ============================================================================

print_cli_status() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     COMPRESSION STACK MONITOR - HEADROOM + RTK        ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Headroom Health
    echo -e "${BLUE}=== HEADROOM STATUS ===${NC}"
    echo ""
    
    local default_health=$(get_headroom_health 8787)
    local small_health=$(get_headroom_health 8790)
    
    local default_running=$(echo "$default_health" | python3 -c "import sys,json; print('✓ RUNNING' if json.load(sys.stdin).get('running') else '✗ OFFLINE')")
    local default_opt=$(echo "$default_health" | python3 -c "import sys,json; print('ON' if json.load(sys.stdin).get('optimize') else 'OFF')")
    
    local small_running=$(echo "$small_health" | python3 -c "import sys,json; print('✓ RUNNING' if json.load(sys.stdin).get('running') else '✗ OFFLINE')")
    local small_opt=$(echo "$small_health" | python3 -c "import sys,json; print('ON' if json.load(sys.stdin).get('optimize') else 'OFF')")
    
    echo "Default Tier (:8787): $default_running | Compression: ${YELLOW}$default_opt${NC}"
    echo "Small Tier  (:8790): $small_running | Compression: ${YELLOW}$small_opt${NC}"
    echo ""
    
    # RTK Status
    echo -e "${BLUE}=== RTK STATUS ===${NC}"
    echo ""
    
    local rtk_status=$(get_rtk_status)
    local rtk_installed=$(echo "$rtk_status" | python3 -c "import sys,json; print('✓ INSTALLED' if json.load(sys.stdin).get('installed') else '✗ NOT FOUND')")
    local rtk_version=$(echo "$rtk_status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version', 'unknown'))")
    
    echo "RTK: $rtk_installed (v$rtk_version)"
    echo ""
    
    # Compression Metrics
    echo -e "${BLUE}=== COMPRESSION METRICS ===${NC}"
    echo ""
    
    local default_stats=$(get_headroom_stats "$HOME/.local/share/headroom/proxy-default.jsonl")
    local small_stats=$(get_headroom_stats "$HOME/.local/share/headroom/proxy-small.jsonl")
    local rtk_stats=$(get_rtk_stats)
    
    echo -e "${CYAN}Headroom Default:${NC}"
    echo "$default_stats" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Requests: {d[\"requests\"]}'); print(f'  Compressed: {d[\"compressed\"]}'); print(f'  Tokens In: {d[\"tokens_in\"]:,}'); print(f'  Tokens Out: {d[\"tokens_out\"]:,}')"
    echo ""
    
    echo -e "${CYAN}Headroom Small:${NC}"
    echo "$small_stats" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Requests: {d[\"requests\"]}'); print(f'  Compressed: {d[\"compressed\"]}'); print(f'  Tokens In: {d[\"tokens_in\"]:,}'); print(f'  Tokens Out: {d[\"tokens_out\"]:,}')"
    echo ""
    
    echo -e "${CYAN}RTK:${NC}"
    echo "$rtk_stats" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Total Compressions: {d[\"total_compressions\"]}'); print(f'  Tokens Saved: {d[\"tokens_saved\"]:,}')"
    echo ""
    
    # CLI Sessions
    echo -e "${MAGENTA}=== CLI SESSIONS (Recent 15) ===${NC}"
    echo ""
    
    printf "${WHITE}%-14s %-12s %-6s %-8s %-10s %s${NC}\n" "TOOL" "SESSION" "MSG" "SIZE" "AGE" "WORKSPACE"
    echo "----------------------------------------------------------------------------------"
    
    python3 << 'EOF'
import json
import sys
from datetime import datetime
from pathlib import Path

sessions = []
session_dirs = [
    (Path.home() / ".claude" / "sessions", "Claude Code"),
    (Path.home() / ".qwen" / "sessions", "Qwen Code"),
    (Path.home() / ".codex" / "sessions", "Codex CLI"),
    (Path.home() / ".opencode" / "sessions", "OpenCode"),
]

for session_dir, tool_name in session_dirs:
    if not session_dir.exists():
        continue
    for session_file in session_dir.glob("*.json"):
        try:
            stat = session_file.stat()
            with open(session_file) as f:
                data = json.load(f)
            sessions.append({
                "tool": tool_name,
                "session": session_file.stem,
                "modified": int(stat.st_mtime),
                "size": stat.st_size,
                "messages": len(data.get("messages", [])),
                "cwd": data.get("cwd", data.get("workspace", "N/A")),
            })
        except:
            continue

sessions.sort(key=lambda x: x["modified"], reverse=True)
now = datetime.now().timestamp()

for s in sessions[:15]:
    age_secs = now - s["modified"]
    if age_secs < 60:
        age = f"{int(age_secs)}s ago"
    elif age_secs < 3600:
        age = f"{int(age_secs/60)}m ago"
    elif age_secs < 86400:
        age = f"{int(age_secs/3600)}h ago"
    else:
        age = f"{int(age_secs/86400)}d ago"
    
    tool_colors = {
        "Claude Code": "\033[0;32m",
        "Qwen Code": "\033[0;36m",
        "Codex CLI": "\033[1;33m",
        "OpenCode": "\033[0;35m"
    }
    nc = "\033[0m"
    
    tool_colored = f"{tool_colors.get(s['tool'], '')}{s['tool']}{nc}"
    session_short = s["session"][:12] + ("..." if len(s["session"]) > 12 else "")
    cwd_short = s["cwd"][-35:] if len(s["cwd"]) > 35 else s["cwd"]
    size_fmt = f"{s['size']/1024:.1f}KB" if s["size"] < 1048576 else f"{s["size"]/1048576:.1f}MB"
    
    msg_color = "\033[0;32m" if s["messages"] <= 50 else "\033[1;33m" if s["messages"] <= 100 else "\033[0;31m"
    
    print(f"{tool_colored:<14} {session_short:<12} {msg_color}{s['messages']}{nc:<6} {size_fmt:<8} {age:<10} {cwd_short}")
EOF
    
    echo ""
    echo -e "${BLUE}=== QUICK COMMANDS ===${NC}"
    echo ""
    echo "Web Dashboard:     ${CYAN}compress-monitor --web${NC} (or open http://localhost:8899)"
    echo "Headroom Logs:     ${CYAN}tail -f ~/.local/share/headroom/proxy-default.jsonl${NC}"
    echo "RTK History:       ${CYAN}rtk gain --history${NC}"
    echo "Restart Headroom:  ${CYAN}headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1${NC}"
    echo ""
    echo -e "${CYAN}================================================${NC}"
}

# ============================================================================
# WEB UI OUTPUT
# ============================================================================

print_web_json() {
    # Generate JSON for web UI
    local default_health=$(get_headroom_health 8787)
    local small_health=$(get_headroom_health 8790)
    local rtk_status=$(get_rtk_status)
    local default_stats=$(get_headroom_stats "$HOME/.local/share/headroom/proxy-default.jsonl")
    local small_stats=$(get_headroom_stats "$HOME/.local/share/headroom/proxy-small.jsonl")
    local rtk_stats=$(get_rtk_stats)
    local sessions=$(get_cli_sessions)
    
    cat << EOF
{
    "timestamp": "$(date -Iseconds)",
    "headroom": {
        "default": $default_health,
        "small": $small_health,
        "default_stats": $default_stats,
        "small_stats": $small_stats
    },
    "rtk": $rtk_status,
    "rtk_stats": $rtk_stats,
    "sessions": $sessions
}
EOF
}

# ============================================================================
# MAIN
# ============================================================================

if $WEB_MODE; then
    print_web_json
else
    print_cli_status
fi
