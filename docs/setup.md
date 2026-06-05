# Setup

This project is now a local AI gateway for coding agents. The common path is:

```text
agent CLI -> Headroom :8787 -> gateway :8082 -> provider
```

Use `:8787` when you want compression. Use `:8082` only when you want routing without Headroom.

## Install

```bash
git clone https://github.com/aaaronmiller/claude-code-proxy.git
cd claude-code-proxy
uv sync
cp .env.example .env
```

Edit `.env` with provider keys and model assignments, then start:

```bash
./proxies up
```

## Use with Claude Code

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
export ANTHROPIC_API_KEY=pass
claude
```

`ANTHROPIC_API_KEY=pass` is a local SDK compatibility value. Real provider credentials stay in `.env` or your shell.

## Headroom Acceleration

Default behavior is automatic:

```bash
./proxies restart headroom
```

The launcher detects GPU support in this order:

1. NVIDIA via `nvidia-smi`
2. Intel Arc/iGPU via `clinfo`, `lspci`, or WSL `/dev/dxg`
3. CPU fallback

Force a mode:

```bash
HEADROOM_ACCELERATOR=intel ./proxies restart headroom
HEADROOM_ACCELERATOR=nvidia ./proxies restart headroom
HEADROOM_ACCELERATOR=cpu ./proxies restart headroom
```

Intel Arc default:

```bash
HEADROOM_KOMPRESS_DEVICE=GPU.0
ONEAPI_DEVICE_SELECTOR=level_zero:0
LIBVA_DRIVER_NAME=iHD
```

Full details: [Headroom Acceleration](headroom-acceleration.md).

## Remote Headroom on a LAN GPU Host

Use a shared GPU machine when your laptop has no useful GPU.

On the GPU host:

```bash
HEADROOM_HOST=0.0.0.0 \
HEADROOM_ACCELERATOR=intel \
HEADROOM_UPSTREAM_URL=http://127.0.0.1:8082 \
scripts/headroom-start.sh
```

On each client machine:

```bash
HEADROOM_REMOTE_URL=http://gpu-box.local:8787 ./proxies restart headroom
```

Clients keep using:

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
```

The local `:8787` service becomes a relay to the remote Headroom instance.

## Health Checks

```bash
curl -sf http://127.0.0.1:8787/health
curl -sf http://127.0.0.1:8082/health
./proxies status
```

## Common Failures

### Headroom starts on CPU when a GPU exists

Force the accelerator:

```bash
HEADROOM_ACCELERATOR=intel HEADROOM_KOMPRESS_DEVICE=GPU.0 ./proxies restart headroom
```

### Remote Headroom relay is healthy but requests fail

The remote GPU host sends upstream requests from its own network namespace. Make sure its `HEADROOM_UPSTREAM_URL` points to a gateway reachable from that host.

### Port already in use

```bash
./proxies down
./proxies up
```

### Provider 401

Do not replace `ANTHROPIC_API_KEY=pass`. Check the real provider key in `.env`, then see [401 troubleshooting](troubleshooting/401-errors.md).
