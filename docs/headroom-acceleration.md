# Headroom Acceleration

Headroom is the context-compression layer. It runs on `:8787` and forwards optimized requests to the gateway on `:8082`.

## Modes

| Mode | How to select | Result |
|------|---------------|--------|
| Auto | default | detects NVIDIA, Intel, then CPU |
| Intel | `HEADROOM_ACCELERATOR=intel` | OpenVINO Kompress on `HEADROOM_KOMPRESS_DEVICE`, default `GPU.0` |
| NVIDIA | `HEADROOM_ACCELERATOR=nvidia` | disables OpenVINO and ONNX so PyTorch can use CUDA |
| CPU | `HEADROOM_ACCELERATOR=cpu` | disables OpenVINO and uses ONNX/CPU |
| Remote | `HEADROOM_REMOTE_URL=http://host:8787` | local relay forwards to a LAN Headroom instance |

## Local GPU

```bash
./proxies restart headroom
curl -sf http://127.0.0.1:8787/health
```

For Intel Arc / Intel iGPU:

```bash
HEADROOM_ACCELERATOR=intel \
HEADROOM_KOMPRESS_DEVICE=GPU.0 \
./proxies restart headroom
```

Verified local evidence on this machine:

```text
preload: backend=openvino model=_OpenVINOModel
HEADROOM_KOMPRESS_DEVICE=GPU.0
ONEAPI_DEVICE_SELECTOR=level_zero:0
LIBVA_DRIVER_NAME=iHD
```

## CPU Fallback

If no GPU is detected, `scripts/headroom-start.sh` sets:

```bash
HEADROOM_DISABLE_OPENVINO=1
HEADROOM_KOMPRESS_DEVICE=cpu
```

The local compatibility patch also restores the missing ONNX wrapper found in some Headroom `0.20.27` installs. Verified CPU preload:

```text
onnx _OnnxModel
```

## Remote Headroom

Use this when another machine has the better GPU.

On the GPU host, start Headroom so other machines can reach it:

```bash
HEADROOM_HOST=0.0.0.0 \
HEADROOM_ACCELERATOR=intel \
HEADROOM_UPSTREAM_URL=http://127.0.0.1:8082 \
scripts/headroom-start.sh
```

On a client machine:

```bash
HEADROOM_REMOTE_URL=http://gpu-box.local:8787 ./proxies restart headroom
```

The client keeps a local `http://127.0.0.1:8787` endpoint. `scripts/headroom-relay.py` forwards all methods, headers, streaming responses, and health checks to the remote Headroom URL.

Network rule: the remote Headroom server sends upstream requests from the GPU host. Configure `HEADROOM_UPSTREAM_URL` on that host to a gateway endpoint it can reach.

## Multiple Sessions

Multiple agent sessions can share one Headroom process. The Kompress model is loaded once per Headroom worker process and reused by concurrent requests.

Current defaults from `/health`:

```text
anthropic_pre_upstream.resolved_concurrency=8
compression_executor.max_workers=32
```

Keep `HEADROOM_WORKERS=1` on low-VRAM machines. Extra workers can load extra model copies.

## Size and Memory

Verified local artifacts:

```text
/tmp/kompress-base-ov.bin  286M
/tmp/kompress-base-ov.xml  1008K
largest HF source blob     600,014,148 bytes
process RSS after preload  about 603 MiB
```

Exact VRAM is unavailable under this WSL setup because native i915 DRM memory counters are not exposed and `intel_gpu_top` cannot see a native i915 device.
