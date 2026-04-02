#!/usr/bin/env bash
# Test the full proxy chain with a real API request
# Usage: ./test-request.sh

set -euo pipefail

PROXY_URL="http://127.0.0.1:8082"
HEADROOM_URL="http://127.0.0.1:8787"

echo "========================================"
echo "  TESTING FULL PROXY CHAIN"
echo "========================================"
echo ""

# Check services are running
echo "Checking services..."

if curl -s "$PROXY_URL/health" | grep -q "healthy"; then
    echo "✓ Proxy (8082): Running"
else
    echo "✗ Proxy (8082): NOT RUNNING"
    echo "  Run: ./debug-full-stack.sh"
    exit 1
fi

if curl -s "$HEADROOM_URL/health" | grep -q "optimize.*true"; then
    echo "✓ Headroom (8787): Running (compression ENABLED)"
else
    echo "✗ Headroom (8787): NOT RUNNING or compression disabled"
    echo "  Run: ./debug-full-stack.sh"
    exit 1
fi

echo ""
echo "Sending test request..."
echo ""

# Get OpenRouter API key
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    echo "ERROR: OPENROUTER_API_KEY not set"
    exit 1
fi

# Send a test request through the proxy
RESPONSE=$(curl -s -X POST "$PROXY_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -d '{
        "model": "qwen/qwen3.5-9b",
        "messages": [
            {"role": "user", "content": "Say hello in exactly 3 words"}
        ],
        "max_tokens": 20,
        "stream": false
    }' 2>&1)

echo "Response:"
echo "----------------------------------------"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo "----------------------------------------"
echo ""

# Check if we got a valid response
if echo "$RESPONSE" | grep -q "choices"; then
    echo "✓ Request SUCCESSFUL"
    CONTENT=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','NO CONTENT'))" 2>/dev/null || echo "PARSE ERROR")
    echo "  Model response: $CONTENT"
else
    echo "✗ Request FAILED"
    if echo "$RESPONSE" | grep -q "error"; then
        echo "  Error: $(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','Unknown'))" 2>/dev/null || echo "Unknown")"
    fi
fi

echo ""
echo "========================================"
echo "  CHECKING LOGS"
echo "========================================"
echo ""

echo "Last 5 proxy log entries:"
tail -5 ~/code/claude-code-proxy/debug-proxy.log 2>/dev/null || echo "  (no logs found)"

echo ""
echo "Last 5 headroom log entries:"
tail -5 ~/.local/share/headroom/proxy-default.jsonl 2>/dev/null || echo "  (no logs found)"
