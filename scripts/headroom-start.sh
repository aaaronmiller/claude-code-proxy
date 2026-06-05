#!/usr/bin/env bash
# Start Headroom with Intel Arc/OpenVINO Kompress pinned to the dGPU.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEADROOM_BIN="${HEADROOM_BIN:-headroom}"
HEADROOM_RESOLVED_BIN="$(command -v "$HEADROOM_BIN")"
HEADROOM_PYTHON="${HEADROOM_PYTHON:-}"
HEADROOM_PORT="${HEADROOM_PORT:-8787}"
HEADROOM_MODE="${HEADROOM_MODE:-token_headroom}"
HEADROOM_UPSTREAM_URL="${HEADROOM_UPSTREAM_URL:-http://127.0.0.1:8082}"
HEADROOM_LOG_FILE="${HEADROOM_LOG_FILE:-$HOME/.headroom/logs/proxy.jsonl}"
HEADROOM_KOMPRESS_DEVICE="${HEADROOM_KOMPRESS_DEVICE:-GPU.0}"
HEADROOM_PRELOAD_TIMEOUT="${HEADROOM_PRELOAD_TIMEOUT:-90s}"
HEADROOM_ALLOW_CPU_FALLBACK="${HEADROOM_ALLOW_CPU_FALLBACK:-0}"

export ONEAPI_DEVICE_SELECTOR="${ONEAPI_DEVICE_SELECTOR:-level_zero:0}"
export LIBVA_DRIVER_NAME="${LIBVA_DRIVER_NAME:-iHD}"
export HEADROOM_KOMPRESS_DEVICE
export PYTHONPATH="${ROOT_DIR}/scripts/headroom-openvino-site${PYTHONPATH:+:${PYTHONPATH}}"

mkdir -p "$(dirname "$HEADROOM_LOG_FILE")"

if [ -z "$HEADROOM_PYTHON" ]; then
    bin_dir="$(cd "$(dirname "$HEADROOM_RESOLVED_BIN")" && pwd)"
    if [ -x "${bin_dir}/python" ]; then
        HEADROOM_PYTHON="${bin_dir}/python"
    elif [ -x "${bin_dir}/python3" ]; then
        HEADROOM_PYTHON="${bin_dir}/python3"
    else
        HEADROOM_PYTHON="python"
    fi
fi

echo "Starting Headroom on :${HEADROOM_PORT}"
echo "  mode: ${HEADROOM_MODE}"
echo "  upstream: ${HEADROOM_UPSTREAM_URL}"
echo "  kompress: OpenVINO ${HEADROOM_KOMPRESS_DEVICE}"
echo "  selector: ${ONEAPI_DEVICE_SELECTOR}"
echo "  python: ${HEADROOM_PYTHON}"

preload_status=0
timeout "$HEADROOM_PRELOAD_TIMEOUT" "$HEADROOM_PYTHON" - <<'PY' || preload_status=$?
import os
from headroom.transforms.kompress_compressor import _load_kompress
import headroom.transforms.kompress_compressor as kompress

device = os.environ.get("HEADROOM_KOMPRESS_DEVICE", "GPU.0")
model, _ = _load_kompress(device)
backend = getattr(kompress, "_kompress_backend", None)
print(f"  preload: backend={backend} model={type(model).__name__}")
if backend != "openvino":
    raise SystemExit(f"Kompress did not load on OpenVINO: backend={backend}")
PY

if [ "$preload_status" -ne 0 ]; then
    echo "Headroom Kompress GPU preload failed (status ${preload_status})." >&2
    if [ "$HEADROOM_ALLOW_CPU_FALLBACK" != "1" ]; then
        echo "Refusing CPU fallback. Set HEADROOM_ALLOW_CPU_FALLBACK=1 to override." >&2
        exit "$preload_status"
    fi
    echo "Continuing because HEADROOM_ALLOW_CPU_FALLBACK=1." >&2
fi

exec "$HEADROOM_BIN" proxy \
    --port "$HEADROOM_PORT" \
    --mode "$HEADROOM_MODE" \
    --anthropic-api-url "$HEADROOM_UPSTREAM_URL" \
    --log-file "$HEADROOM_LOG_FILE" \
    "$@"
