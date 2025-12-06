#!/bin/bash

# Wrapper script for Claude Code Client
# Automatically handles proxy authentication and error recovery

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. Check Mode (Proxy vs Direct)
IS_PROXY_MODE=false
if [[ "$ANTHROPIC_BASE_URL" == *"localhost"* || "$ANTHROPIC_BASE_URL" == *"127.0.0.1"* ]]; then
    IS_PROXY_MODE=true
fi

# 2. Prepare Command
CMD="$@"
if [ $# -eq 0 ]; then
    echo "Usage: $0 <command>"
    exit 1
fi

# If Proxy Mode, force 'pass' as the API key for the client
if [ "$IS_PROXY_MODE" = true ]; then
    export ANTHROPIC_API_KEY="pass"
    # echo -e "${CYAN}[Wrapper] Proxy Mode detected. Forcing ANTHROPIC_API_KEY=pass${NC}"
fi

# 3. Run Command and Capture Output/Exit Code
# We use a temporary file to capture output because piping hides exit codes and TTY behavior
TEMP_OUT=$(mktemp)

# Run the command
# We need to preserve TTY for interactive CLI tools like claude
# So we can't easily capture output AND keep interactivity perfect without 'script' or similar tools.
# However, Claude Code CLI usually exits on auth error immediately.
# Let's try running it directly. If it fails, we check the exit code.
# Capturing stderr might be enough for the error message.

"$@" 2> >(tee "$TEMP_OUT" >&2)
EXIT_CODE=$?

# 4. Check for Errors
if [ $EXIT_CODE -ne 0 ]; then
    # Check if output contains auth errors
    ERROR_OUTPUT=$(cat "$TEMP_OUT")
    
    if [[ "$ERROR_OUTPUT" == *"401"* || "$ERROR_OUTPUT" == *"Unauthorized"* || "$ERROR_OUTPUT" == *"Invalid API key"* ]]; then
        echo ""
        echo -e "${RED}🛑 Authentication Error Detected!${NC}"
        echo "It seems your API key is invalid or missing."
        echo ""
        
        echo -e "${YELLOW}🚀 Launching Auto-Healing Wizard...${NC}"
        echo ""
        
        # Run the Wizard
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
        "$SCRIPT_DIR/api_key_wizard.sh"
        WIZARD_EXIT=$?
        
        if [ $WIZARD_EXIT -ne 0 ]; then
            echo -e "${RED}Wizard cancelled or failed. Exiting.${NC}"
            rm "$TEMP_OUT"
            exit $WIZARD_EXIT
        fi
        
        # Post-Wizard Actions
        echo ""
        if [ "$IS_PROXY_MODE" = true ]; then
            echo -e "${RED}⚠️  ACTION REQUIRED ⚠️${NC}"
            echo -e "${YELLOW}You are running in PROXY MODE.${NC}"
            echo "You MUST restart your Proxy Server (ccproxy) terminal now so it picks up the new key."
            echo ""
            read -p "Press Enter once you have restarted the proxy..."
        else
            echo -e "${YELLOW}You are running in DIRECT MODE.${NC}"
            echo "You need to source your profile to pick up the new key in this terminal."
            echo "Run: source ~/.zshrc (or your profile)"
            echo ""
        fi
        
        echo -e "${CYAN}🔄 Restarting your command...${NC}"
        echo ""
        
        # We can't easily "restart" with the new env vars in the SAME script process 
        # because the wizard updated the FILE, not our current process env.
        # We'll try to re-source if we can find the profile, or just tell user to restart.
        
        # Attempt to re-source (best effort)
        if [ -f "$HOME/.zshrc" ]; then source "$HOME/.zshrc"; fi
        if [ -f "$HOME/.bash_profile" ]; then source "$HOME/.bash_profile"; fi
        
        # Retry command
        "$@"
    fi
fi

rm "$TEMP_OUT"
exit $EXIT_CODE
