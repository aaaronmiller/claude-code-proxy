#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# DEV LAUNCH - Start server and open Chrome for testing
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PORT="${PORT:-8082}"
HOST="${HOST:-127.0.0.1}"
FRONTEND_URL="http://${HOST}:${PORT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           Claude Code Proxy - Dev Launch Tool                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for existing server
check_existing_server() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
        read -p "Kill existing process? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Killing process on port $PORT...${NC}"
            lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            echo -e "${RED}Aborting. Stop the existing server first.${NC}"
            exit 1
        fi
    fi
}

# Start the backend server
start_backend() {
    echo -e "${CYAN}🚀 Starting backend server...${NC}"
    cd "$PROJECT_ROOT"
    
    # Start server in background
    .venv/bin/python start_proxy.py --host $HOST --port $PORT &
    SERVER_PID=$!
    
    echo -e "${GREEN}   Server PID: $SERVER_PID${NC}"
    
    # Wait for server to be ready
    echo -e "${CYAN}   Waiting for server to be ready...${NC}"
    for i in {1..30}; do
        if curl -s "http://${HOST}:${PORT}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}   ✓ Server is ready!${NC}"
            return 0
        fi
        sleep 0.5
    done
    
    echo -e "${RED}   ✗ Server failed to start in 15 seconds${NC}"
    return 1
}

# Open Chrome
open_chrome() {
    echo -e "${CYAN}🌐 Opening Chrome...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open -a "Google Chrome" "$FRONTEND_URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        google-chrome "$FRONTEND_URL" 2>/dev/null || chromium-browser "$FRONTEND_URL" 2>/dev/null
    else
        echo -e "${YELLOW}   Cannot auto-open browser. Visit: $FRONTEND_URL${NC}"
    fi
    
    echo -e "${GREEN}   ✓ Browser opened at $FRONTEND_URL${NC}"
}

# Cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down...${NC}"
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}   ✓ Server stopped${NC}"
}

trap cleanup EXIT INT TERM

# Main
main() {
    check_existing_server
    start_backend
    open_chrome
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Dev environment is running!${NC}"
    echo -e "${GREEN}  Frontend: $FRONTEND_URL${NC}"
    echo -e "${GREEN}  API Docs: $FRONTEND_URL/docs${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Press Ctrl+C to stop the server${NC}"
    echo ""
    
    # Keep script running (server in background will keep running)
    wait $SERVER_PID
}

main "$@"
