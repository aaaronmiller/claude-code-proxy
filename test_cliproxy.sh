#!/bin/bash
echo "Testing gemini-claude-opus-4-6-thinking..."
curl -s -X POST http://127.0.0.1:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-claude-opus-4-6-thinking",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1
  }' | head -c 200
echo ""
echo "----------------------------------------"

echo "Testing gemini-claude-opus-4-5-thinking..."
curl -s -X POST http://127.0.0.1:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-claude-opus-4-5-thinking",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1
  }' | head -c 200
echo ""
echo "----------------------------------------"
