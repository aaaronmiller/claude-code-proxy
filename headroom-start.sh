#!/usr/bin/env bash
# Start headroom proxy with OpenVINO dGPU Kompress compression
# Routes: Claude → headroom(:8787) → proxy(:8082) → upstream

set -e

HEADROOM_PORT="${HEADROOM_PORT:-8787}"
PROXY_URL="${PROXY_URL:-http://127.0.0.1:8082/v1}"
HEADROOM_MODE="${HEADROOM_MODE:-token_headroom}"

echo "🚀 Starting Headroom proxy on :${HEADROOM_PORT}"
echo "   Mode: ${HEADROOM_MODE}"
echo "   Upstream: ${PROXY_URL}"
echo "   GPU: Intel Arc A370M (OpenVINO GPU.1)"
echo ""

# Pre-load the OpenVINO model so first request isn't slow
echo "⏳ Pre-loading Kompress model on dGPU..."
python3 -c "
from headroom.transforms.kompress_compressor import _load_kompress, _kompress_backend
model, tokenizer = _load_kompress('GPU.1')
print(f'   ✅ Backend: {_kompress_backend}')
print(f'   ✅ Tokenizer: {type(tokenizer).__name__}')
print('   ✅ Ready for compression')
" 2>/dev/null || echo "   ⚠️  Model pre-load failed (will load on first request)"

echo ""
echo "📡 Starting headroom proxy..."
exec headroom proxy \
    --port "${HEADROOM_PORT}" \
    --mode "${HEADROOM_MODE}" \
    --anthropic-api-url "${PROXY_URL}" \
    --log-file ~/.headroom/logs/proxy.jsonl \
    "$@"
