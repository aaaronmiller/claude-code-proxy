# Compression Stack - Complete Integration Guide

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPRESSION STACK                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CLI TOOLS           SHIMS/WRAPPERS        COMPRESSION LAYERS       │
│  ─────────           ──────────────        ──────────────────       │
│                                                                     │
│  claude      ──→     claude (shim)   ──→   ┌──────────────┐        │
│  qwen        ──→     qwen (shim)     ──→   │  Headroom    │        │
│  codex       ──→     codex (shim)    ──→   │  :8787       │ ──→ OpenRouter │
│  opencode    ──→     opencode (shim) ──→   │  GPU: 787MB  │        │
│  openclaw    ──→     openclaw (shim) ──→   │  Kompress    │        │
│  hermes      ──→     hermes (shim)   ──→   └──────────────┘        │
│                                                                     │
│                    ┌──────────────┐                                 │
│                    │  RTK         │                                 │
│                    │  (shell out) │                                 │
│                    └──────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Enable compression for all tools
compressctl on

# Disable compression
compressctl off

# Check status
compressctl status
```

## Installed Components

### 1. Shims (Auto-detected tools)
Located: `~/.config/input-compression/shims/`

- `claude` - Claude Code shim
- `qwen` - Qwen Code shim  
- `codex` - Codex CLI shim
- `opencode` - OpenCode shim
- `openclaw` - OpenClaw shim
- `hermes` - Hermes Bot shim

### 2. Compressed Wrappers (Forced compression)
Located: `~/.local/bin/`

- `claude-compressed` - Claude with forced compression
- `qwen-compressed` - Qwen with forced compression
- `codex-compressed` - Codex with forced compression
- `opencode-compressed` - OpenCode with forced compression
- `openclaw-compressed` - OpenClaw with forced compression
- `hermes-compressed` - Hermes with forced compression

### 3. Monitoring Tools

```bash
# Real-time GPU + compression monitoring
compression-watch

# Full status report
compress-monitor

# Web dashboard
compress-web  # http://localhost:8899
```

## Compression Performance

| Metric | Value |
|--------|-------|
| **Model** | `chopratejas/kompress-base` |
| **GPU** | RTX 4050 6GB @ 787 MiB |
| **Compression Ratio** | 97% (900→26 tokens) |
| **Device** | `cuda:0` |

## Usage Examples

### Standard Mode (respects compressctl state)
```bash
# After: compressctl on
claude          # Uses compression
qwen            # Uses compression
codex           # Uses compression

# After: compressctl off
claude          # Direct connection
qwen            # Direct connection
```

### Forced Compression Mode
```bash
# Always uses compression, ignores compressctl state
claude-compressed
qwen-compressed
codex-compressed
```

### Per-Tool Configuration

#### Claude Code
```bash
# Settings updated automatically
# OPENAI_BASE_URL set to headroom proxy
cat ~/.claude/settings.json
```

#### Qwen Code
```bash
# Env configured in settings.json
cat ~/.qwen/settings.json
```

#### Codex CLI
```bash
# Env file created
cat ~/.codex/env
```

#### OpenCode
```bash
# .env in project root
cat ~/.opencode/.env
```

## Troubleshooting

### Headroom Not Running
```bash
# Start headroom proxy
headroom proxy --port 8787 --mode token_headroom \
  --openai-api-url https://openrouter.ai/api/v1 \
  --backend openrouter --no-telemetry
```

### GPU Not Being Used
```bash
# Verify patch is in place
grep "KompressConfig(device" ~/.local/lib/python3.14/site-packages/headroom/transforms/content_router.py

# Should show: KompressConfig(device="cuda")

# Clear caches and restart
find ~/.local/lib/python3.14/site-packages/headroom -name "__pycache__" -exec rm -rf {} +
pkill -f "headroom"
headroom proxy --port 8787 --mode token_headroom --no-telemetry &
```

### Check Compression Stats
```bash
# View compression events
tail -f ~/.local/share/headroom/headroom-default.out | grep -E "saved|compress"

# Monitor GPU
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```

## Systemd Service

Auto-start headroom on login:
```bash
systemctl --user enable headroom-proxy.service
systemctl --user start headroom-proxy.service
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPRESSION_ENABLED` | `0` | Enable/disable compression (1/0) |
| `HEADROOM_PORT` | `8787` | Headroom proxy port |
| `OPENAI_BASE_URL` | Auto | Provider base URL |
| `PROVIDER_BASE_URL` | Auto | Provider base URL |

## File Locations

```
~/.config/input-compression/
├── bin/
│   ├── compressctl          # Main control
│   └── compress-monitor     # CLI monitor
├── shims/
│   ├── claude              # Tool shims
│   ├── qwen
│   └── ...
├── state.env               # Current state
└── manifests/              # Tool manifests

~/.local/share/headroom/
├── headroom-default.out    # Default tier logs
└── headroom-small.out      # Small tier logs

~/.local/bin/
├── claude-compressed       # Forced compression wrappers
├── qwen-compressed
└── ...
```

## Reverting Changes

All tools are backed up before modification:
```bash
# Restore Claude settings
cp ~/.claude/settings.json.backup.* ~/.claude/settings.json

# Restore Qwen settings
cp ~/.qwen/settings.json.backup.* ~/.qwen/settings.json

# Remove shims
rm -rf ~/.config/input-compression/shims/*

# Remove wrappers
rm ~/.local/bin/*-compressed
```

## Performance Tuning

### Adjust Compression Aggressiveness
Edit `~/.headroom/config.json`:
```json
{
  "kompress": {
    "device": "cuda",
    "min_tokens_to_compress": 100
  }
}
```

### Monitor Compression Ratio
```bash
# Watch compression in real-time
compression-watch

# Check token savings
tail -100 ~/.local/share/headroom/headroom-default.out | grep "saved"
```

## Support Matrix

| Tool | Shim | Wrapper | Config | Status |
|------|------|---------|--------|--------|
| Claude Code | ✓ | ✓ | ✓ | Full |
| Qwen Code | ✓ | ✓ | ✓ | Full |
| Codex CLI | ✓ | ✓ | ✓ | Full |
| OpenCode | ✓ | ✓ | ✓ | Full |
| OpenClaw | ✓ | ✓ | ✓ | Full |
| Hermes | ✓ | ✓ | ✓ | Full |
