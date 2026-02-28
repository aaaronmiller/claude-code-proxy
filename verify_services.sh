#!/bin/bash
# Test CLIProxyAPI first
echo "Testing CLIProxyAPI (port 8317)..."
curl -s -X POST http://127.0.0.1:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-claude-opus-4-5-thinking",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1
  }' > /tmp/test_cliproxy.json

if [ -s /tmp/test_cliproxy.json ]; then
    echo "CLIProxyAPI returned data:"
    cat /tmp/test_cliproxy.json | head -c 100
    echo "..."
else
    echo "CLIProxyAPI failed (empty response)"
    exit 1
fi

echo ""
echo "----------------------------------------"

# Test Claude Code Proxy
echo "Testing Claude Code Proxy (port 8082)..."
# Using the model configured in .env (gemini-claude-opus-4-5-thinking)
# but passing it as 'claude-opus-4-5' maybe? Or just letting it default?
# Better to be explicit to test routing.
# Actually, let's test a simple "haiku" request which should go to SMALL_MODEL
# just to verify the proxy is alive.
# BUT we really want to verify the BIG_MODEL path.

curl -s -X POST http://127.0.0.1:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "claude-3-opus-20240229",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1
  }' > /tmp/test_proxy.json

if [ -s /tmp/test_proxy.json ]; then
    echo "Claude Code Proxy returned data:"
    cat /tmp/test_proxy.json | head -c 100
    echo "..."
else
    echo "Claude Code Proxy failed (empty response)"
    # Check log
    echo "Proxy Log Tail:"
    tail -n 10 /tmp/proxy.log
    exit 1
fi
