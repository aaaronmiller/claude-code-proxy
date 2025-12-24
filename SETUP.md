# Setup Guide: Auto-Healing Wizard & Aliases

This guide explains how to set up the Claude Code Proxy with the new Auto-Healing Wizard.

## 1. Overview

Use these commands to start the respective software:

-   **Proxy Server (`ccproxy`)**: Runs the proxy. Needs your **REAL** API keys (e.g., `sk-ant-...`).
-   **Client (`cproxy-init`)**: Runs Claude Code. Sends a **DUMMY** key (`pass`) to the proxy.
-   **Wizard (`api_key_wizard.sh`)**: Interactive tool to fix your API keys in `~/.zshrc` when errors occur.
-   **Wrapper (`run_router.sh`)**: Automatically runs the Wizard if the client gets a 401 error.

## 2. Add Aliases to Profile

Add the following aliases to your `~/.zshrc` (or `~/.bash_profile`):

```bash
# -----------------------------------------------------------------------------
# CLAUDE CODE PROXY ALIASES
# -----------------------------------------------------------------------------

# PROXY SERVER (Terminal A)
# Sources profile to ensure REAL keys are loaded.
# Sets PROXY_AUTH_KEY=pass so the proxy expects 'pass' from the client.
alias ccproxy='cd $HOME/git/claude-code-proxy && uv run python start_proxy.py' # switch claude code proxy between anthropic account and proxy

# CLIENT (Terminal B)
# Uses the Python wrapper to auto-heal on 401 errors.
# Forces ANTHROPIC_API_KEY=pass to authenticate with the proxy.
alias cproxy-continue='ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY=pass CLAUDE_CODE_MAX_OUTPUT_TOKENS=128768 claude --continue --dangerously-skip-permissions --verbose --model=opus' # Continue Claude session with verbose output, via proxy
alias cproxy-init='ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY=pass CLAUDE_CODE_MAX_OUTPUT_TOKENS=128768 claude --dangerously-skip-permissions --verbose' # Initialize new Claude session with verbose output, via proxy

# DIRECT CLIENT (No Proxy)
# Standard command, uses your real keys directly.
alias claude-continue='claude --continue --dangerously-skip-permissions --verbose' # Continue Claude session with verbose output, anthropic account
alias claude-init='claude --dangerously-skip-permissions --verbose' # Initialize new Claude session with verbose output, anthropic account
```

> **Note**: Adjust the path `$HOME/git/claude-code-proxy` if your repository is located elsewhere.

## 3. Usage

### Step 1: Start the Proxy
Open **Terminal A** and run:
```bash
ccproxy
```
*The proxy will start and listen on port 8082.*

### Step 2: Start the Client
Open **Terminal B** and run:
```bash
cproxy-init
```
*This runs Claude Code through the proxy.*

### Step 3: Auto-Healing
If your API key is invalid or missing, Claude Code Proxy will:
1.  Detect the 401 error.
2.  Launch the **API Key Wizard**.
3.  Ask you to select a provider and enter your **REAL** key.
4.  Update your `~/.zshrc`.
5.  **Prompt you to restart the Proxy (Terminal A)**.
6.  Once you restart the proxy, the client will retry automatically.
