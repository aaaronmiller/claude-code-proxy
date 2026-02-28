#!/bin/bash
# Kill any existing processes (simple commands, no pipes in arguments if possible)
pkill -f cli-proxy-api-plus
pkill -f "python start_proxy.py"

# Wait a moment
sleep 2

# Start CLIProxyAPI
echo "Starting CLIProxyAPI..."
cd /home/cheta/code/cliproxyapi
# Launch in background, redirect output
/home/cheta/code/cliproxyapi/cli-proxy-api-plus --config /home/cheta/code/cliproxyapi/config.yaml > /tmp/cliproxy.log 2>&1 &

# Wait for it to initialize
sleep 2

# Check if running
if pgrep -f cli-proxy-api-plus > /dev/null; then
    echo "CLIProxyAPI started successfully (PID: $(pgrep -f cli-proxy-api-plus))"
else
    echo "CLIProxyAPI failed to start. Check /tmp/cliproxy.log"
    exit 1
fi

# Start Claude Code Proxy
echo "Starting Claude Code Proxy..."
cd /home/cheta/code/claude-code-proxy
source .venv/bin/activate
# Export dummy key to bypass .envrc override if OPENROUTER_API_KEY is unset
export PROVIDER_API_KEY="dummy"
# Launch in background, redirect output
python start_proxy.py --skip-validation > /tmp/proxy.log 2>&1 &

# Wait for it to initialize
sleep 5

# Check if running
if pgrep -f "python start_proxy.py" > /dev/null; then
    echo "Claude Code Proxy started successfully (PID: $(pgrep -f "python start_proxy.py"))"
else
    echo "Claude Code Proxy failed to start. Check /tmp/proxy.log"
    # Show tail of log if failed
    tail -n 20 /tmp/proxy.log
    exit 1
fi

echo "All services started."
