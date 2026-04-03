#!/usr/bin/env bash
# Start the full proxy chain
# Usage: ./start-chain.sh

PROXY_DIR="/home/cheta/code/claude-code-proxy"
CLIPROXY_BIN="/home/cheta/code/cliproxyapi/cli-proxy-api-plus"
CLIPROXY_CFG="/home/cheta/code/cliproxyapi/config.yaml"

wait_for() {
    local port=$1 timeout=${2:-20}
    for i in $(seq 1 $timeout); do
        curl -sf --max-time 1 "http://127.0.0.1:$port/" > /dev/null 2>&1 && return 0
        sleep 1
    done
    return 1
}

echo "Starting CLIProxyAPI..."
nohup $CLIPROXY_BIN --config $CLIPROXY_CFG > /tmp/cliproxy.log 2>&1 &
if wait_for 8317; then echo "  ✓ CLIProxyAPI :8317"; else echo "  ✗ CLIProxyAPI failed"; exit 1; fi

echo "Starting Claude Code Proxy..."
nohup bash -c "cd $PROXY_DIR && source .venv/bin/activate && \
PROVIDER_API_KEY='proxy-secret-key' \
PROVIDER_BASE_URL='http://127.0.0.1:8317/v1' \
BIG_MODEL='gemini-3-pro-high' \
MIDDLE_MODEL='gemini-2.5-flash' \
SMALL_MODEL='gemini-2.5-flash-lite' \
python start_proxy.py --skip-validation" > /tmp/proxy.log 2>&1 &
if wait_for 8082; then echo "  ✓ ClaudeProxy :8082"; else echo "  ✗ ClaudeProxy failed"; exit 1; fi

echo "Starting Headroom..."
nohup headroom proxy --port 8787 --mode token_headroom > /tmp/headroom.log 2>&1 &
if wait_for 8787; then echo "  ✓ Headroom :8787"; else echo "  ✗ Headroom failed"; exit 1; fi

echo ""
echo "Chain: tools → :8787 → :8082 → :8317"
echo ""
echo "PIDs: CLIProxyAPI=$(pgrep -f cli-proxy-api-plus | head -1) Proxy=$(pgrep -f start_proxy.py | head -1) Headroom=$(pgrep -f 'headroom proxy' | head -1)"
