#!/usr/bin/env bash
# Start Headroom with auto GPU detection, CPU fallback, or remote relay mode.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEADROOM_BIN="${HEADROOM_BIN:-headroom}"
HEADROOM_RESOLVED_BIN="$(command -v "$HEADROOM_BIN")"
HEADROOM_PYTHON="${HEADROOM_PYTHON:-}"
HEADROOM_PORT="${HEADROOM_PORT:-8787}"
HEADROOM_HOST="${HEADROOM_HOST:-127.0.0.1}"
HEADROOM_MODE="${HEADROOM_MODE:-token_headroom}"
HEADROOM_UPSTREAM_URL="${HEADROOM_UPSTREAM_URL:-http://127.0.0.1:8082}"
HEADROOM_LOG_FILE="${HEADROOM_LOG_FILE:-$HOME/.headroom/logs/proxy.jsonl}"
HEADROOM_ACCELERATOR="${HEADROOM_ACCELERATOR:-auto}"
HEADROOM_KOMPRESS_DEVICE="${HEADROOM_KOMPRESS_DEVICE:-}"
# Kompress compression model + backbone. Upstream headroom hardcodes these; the
# patch below (patch-headroom-kompress.py) makes them honor these env vars so a
# model swap is one line on any machine. Defaults match upstream — changing
# nothing until overridden. NOTE (2026-06): chopratejas publishes only
# kompress-small / -base / -v2-base; no larger checkpoint exists, so a "bigger
# model for more savings" is not currently possible without training one. The
# backbone MUST match the checkpoint's training backbone.
HEADROOM_KOMPRESS_MODEL="${HEADROOM_KOMPRESS_MODEL:-chopratejas/kompress-base}"
HEADROOM_KOMPRESS_BACKBONE="${HEADROOM_KOMPRESS_BACKBONE:-answerdotai/ModernBERT-base}"
export HEADROOM_KOMPRESS_MODEL HEADROOM_KOMPRESS_BACKBONE
HEADROOM_PRELOAD_TIMEOUT="${HEADROOM_PRELOAD_TIMEOUT:-90s}"
HEADROOM_ALLOW_CPU_FALLBACK="${HEADROOM_ALLOW_CPU_FALLBACK:-1}"
HEADROOM_REMOTE_URL="${HEADROOM_REMOTE_URL:-}"
HEADROOM_RELAY_TIMEOUT="${HEADROOM_RELAY_TIMEOUT:-600}"

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

# Make the installed headroom package honor HEADROOM_KOMPRESS_MODEL/BACKBONE.
# Idempotent + best-effort: re-applied every startup so it survives
# `pip install --upgrade headroom`. A failure here never blocks the proxy.
"$HEADROOM_PYTHON" "${ROOT_DIR}/compression/scripts/patch-headroom-kompress.py" 2>/dev/null \
    || echo "  (kompress model-knob patch skipped — headroom layout may have changed)" >&2

detect_accelerator() {
    case "$HEADROOM_ACCELERATOR" in
        auto) ;;
        cpu|intel|nvidia)
            printf '%s\n' "$HEADROOM_ACCELERATOR"
            return
            ;;
        *)
            echo "Unsupported HEADROOM_ACCELERATOR=$HEADROOM_ACCELERATOR" >&2
            exit 2
            ;;
    esac

    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
        printf 'nvidia\n'
        return
    fi

    if command -v clinfo >/dev/null 2>&1 && clinfo --list 2>/dev/null | grep -qi intel; then
        printf 'intel\n'
        return
    fi

    if command -v lspci >/dev/null 2>&1 && lspci 2>/dev/null | grep -Eiq 'vga|display|3d' && lspci 2>/dev/null | grep -qi intel; then
        printf 'intel\n'
        return
    fi

    if [[ -e /dev/dxg ]] && [[ -d /dev/dri ]]; then
        printf 'intel\n'
        return
    fi

    printf 'cpu\n'
}

if [ -n "$HEADROOM_REMOTE_URL" ]; then
    relay_python="${HEADROOM_RELAY_PYTHON:-${ROOT_DIR}/.venv/bin/python}"
    [ -x "$relay_python" ] || relay_python="$HEADROOM_PYTHON"
    echo "Starting local Headroom relay on ${HEADROOM_HOST}:${HEADROOM_PORT}"
    echo "  remote: ${HEADROOM_REMOTE_URL}"
    echo "  python: ${relay_python}"
    exec "$relay_python" "${ROOT_DIR}/scripts/headroom-relay.py" \
        --listen-host "$HEADROOM_HOST" \
        --listen-port "$HEADROOM_PORT" \
        --remote-url "$HEADROOM_REMOTE_URL" \
        --timeout "$HEADROOM_RELAY_TIMEOUT"
fi

accelerator="$(detect_accelerator)"
expected_backend=""

case "$accelerator" in
    intel)
        export LIBVA_DRIVER_NAME="${LIBVA_DRIVER_NAME:-iHD}"
        # Select the GPU for Kompress. Prefer the DISCRETE GPU (e.g. Arc): on a
        # dual-GPU laptop the iGPU often carries a far older host driver, and in
        # WSL2 a guest/host driver-version gap faults the /dev/dxg bridge hard
        # enough to crash the whole VM (dmesg: dxgkio_reserve_gpu_va: -75).
        # Picking by device TYPE (not a hardcoded index) survives enumeration
        # reordering. Honors an explicit HEADROOM_KOMPRESS_DEVICE if set.
        if [ -z "${HEADROOM_KOMPRESS_DEVICE:-}" ]; then
            HEADROOM_KOMPRESS_DEVICE="$("$HEADROOM_PYTHON" - <<'PYDEV' 2>/dev/null
from openvino import Core
c = Core()
gpus = [d for d in c.available_devices if d.startswith("GPU")]
disc = [d for d in gpus if str(c.get_property(d, "DEVICE_TYPE")).endswith("DISCRETE")]
print(disc[0] if disc else (gpus[0] if gpus else ""))
PYDEV
)"
        fi
        export HEADROOM_KOMPRESS_DEVICE="${HEADROOM_KOMPRESS_DEVICE:-GPU.0}"
        # Expose ALL level_zero GPUs so the discrete pick is never hidden.
        export ONEAPI_DEVICE_SELECTOR="${ONEAPI_DEVICE_SELECTOR:-level_zero:*}"
        expected_backend="openvino"
        echo "  intel gpu: kompress device = ${HEADROOM_KOMPRESS_DEVICE} (discrete-preferred)"
        ;;
    nvidia)
        export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
        export HEADROOM_DISABLE_OPENVINO="${HEADROOM_DISABLE_OPENVINO:-1}"
        export HEADROOM_DISABLE_ONNX="${HEADROOM_DISABLE_ONNX:-1}"
        ;;
    cpu)
        export HEADROOM_DISABLE_OPENVINO="${HEADROOM_DISABLE_OPENVINO:-1}"
        export HEADROOM_KOMPRESS_DEVICE="${HEADROOM_KOMPRESS_DEVICE:-cpu}"
        ;;
esac

echo "Starting Headroom on ${HEADROOM_HOST}:${HEADROOM_PORT}"
echo "  mode: ${HEADROOM_MODE}"
echo "  upstream: ${HEADROOM_UPSTREAM_URL}"
echo "  accelerator: ${accelerator}"
echo "  kompress_device: ${HEADROOM_KOMPRESS_DEVICE:-auto}"
echo "  python: ${HEADROOM_PYTHON}"

export HEADROOM_EXPECT_BACKEND="$expected_backend"
preload_status=0
timeout "$HEADROOM_PRELOAD_TIMEOUT" "$HEADROOM_PYTHON" - <<'PY' || preload_status=$?
import os
from headroom.transforms.kompress_compressor import _load_kompress
import headroom.transforms.kompress_compressor as kompress

device = os.environ.get("HEADROOM_KOMPRESS_DEVICE", "auto")
model, _ = _load_kompress(device)
backend = getattr(kompress, "_kompress_backend", None)
print(f"  preload: backend={backend} model={type(model).__name__}")
expected = os.environ.get("HEADROOM_EXPECT_BACKEND", "").strip()
if expected and backend != expected:
    raise SystemExit(f"Kompress did not load on {expected}: backend={backend}")
PY

if [ "$preload_status" -ne 0 ]; then
    echo "Headroom Kompress preload failed (status ${preload_status})." >&2
    if [ "$HEADROOM_ALLOW_CPU_FALLBACK" != "1" ]; then
        echo "Refusing CPU fallback. Set HEADROOM_ALLOW_CPU_FALLBACK=1 to override." >&2
        exit "$preload_status"
    fi
    echo "Retrying with CPU fallback." >&2
    export HEADROOM_DISABLE_OPENVINO=1
    export HEADROOM_KOMPRESS_DEVICE=cpu
    timeout "$HEADROOM_PRELOAD_TIMEOUT" "$HEADROOM_PYTHON" - <<'PY'
from headroom.transforms.kompress_compressor import _load_kompress
import headroom.transforms.kompress_compressor as kompress
model, _ = _load_kompress("cpu")
print(f"  preload: backend={getattr(kompress, '_kompress_backend', None)} model={type(model).__name__}")
PY
fi

# Anthropic upstream redirect. headroom 0.5.7's `proxy` CLI dropped --anthropic-api-url
# (anthropic upstream was hardcoded to api.anthropic.com). We patched the installed
# package's server.py to honor ANTHROPIC_TARGET_API_URL (mirroring its OPENAI_TARGET_API_URL).
# Default: chain anthropic traffic through the upstream, restoring prior behaviour.
# To send anthropic straight to api.anthropic.com, run with HEADROOM_ANTHROPIC_UPSTREAM="".
export ANTHROPIC_TARGET_API_URL="${HEADROOM_ANTHROPIC_UPSTREAM-$HEADROOM_UPSTREAM_URL}"

exec "$HEADROOM_BIN" proxy \
    --host "$HEADROOM_HOST" \
    --port "$HEADROOM_PORT" \
    --mode "$HEADROOM_MODE" \
    --openai-api-url "$HEADROOM_UPSTREAM_URL" \
    --log-file "$HEADROOM_LOG_FILE" \
    "$@"
