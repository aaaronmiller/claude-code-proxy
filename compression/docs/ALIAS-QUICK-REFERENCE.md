# Compression Stack - Alias Quick Reference v2.2

**Key Changes:**
- ✅ Aliases **DON'T start** services anymore (instant!)
- ✅ Services should auto-start with computer (systemd)
- ✅ Manual start commands still available (`cs-start`, `cproxy-start`)
- ✅ OpenCode YOLO is in settings.json, not CLI flag

---

## Complete Alias Table

| CLI | Start (Direct) | Start (Proxy) | Resume (Direct) | Resume (Proxy) | YOLO (Direct) | YOLO (Proxy) |
|-----|----------------|---------------|-----------------|----------------|---------------|--------------|
| **Claude Code** | `csi` | `csi-proxy` | `csr` | `csr-proxy` | `csi-yolo` | `csi-proxy-yolo` |
| **Qwen Code** | `qsi` | `qsi-proxy` | `qsr` | `qsr-proxy` | `qsi-yolo` | `qsi-proxy-yolo` |
| **Codex** | `csi-codex` | `csi-codex-proxy` | `csr-codex` | `csr-codex-proxy` | `csi-codex-yolo` | `csi-codex-proxy-yolo` |
| **OpenCode**¹ | `osi` | `osi-proxy` | `osr` | `osr-proxy` | N/A | N/A |
| **OpenClaw** | `ocl` | `ocl-proxy` | `ocr` | `ocr-proxy` | `ocl-yolo` | `ocl-proxy-yolo` |
| **Hermes** | `hsi` | `hsi-proxy` | `hsr` | `hsr-proxy` | `hsi-yolo` | `hsi-proxy-yolo` |

**Note ¹:** OpenCode YOLO mode is set in `~/.opencode/settings.json`:
```json
{
  "dangerouslySkipPermissions": true
}
```

---

## Manual Start Commands

**Aliases check if services are running, but don't start them.** Use these to manually start:

| Command | Starts | Use Case |
|---------|--------|----------|
| `cs-start` | Compression only | Start Headroom manually |
| `cs-stop` | Compression only | Stop Headroom |
| `cs-restart` | Compression only | Restart Headroom |
| `cs-status` | N/A | Check compression status |
| `cproxy-start` | Proxy + Compression | Start both manually |
| `cproxy-stop` | Proxy + Compression | Stop both |
| `cproxy-status` | N/A | Check both status |

---

## Auto-Start Setup (Recommended)

### For Compression (Headroom)

Create systemd service:
```bash
cat > ~/.config/systemd/user/headroom.service << 'EOF'
[Unit]
Description=Headroom Compression Proxy
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable headroom
systemctl --user start headroom
```

### For Proxy (Optional)

```bash
cat > ~/.config/systemd/user/claude-proxy.service << 'EOF'
[Unit]
Description=Claude Code Proxy
After=network.target headroom.service

[Service]
Type=simple
WorkingDirectory=%h/code/claude-code-proxy
Environment="OPENAI_BASE_URL=http://127.0.0.1:8787/v1"
ExecStart=%h/code/claude-code-proxy/.venv/bin/python start_proxy.py --skip-validation
Restart=on-failure

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable claude-proxy
systemctl --user start claude-proxy
```

---

## Usage Flow

### Normal Workflow (Services Auto-Start)

```bash
# Boot computer → services start automatically

# Just use aliases (instant!)
csi          # Claude with compression
csr          # Resume Claude
qsi          # Qwen with compression

# If services aren't running, you'll see a warning:
# ⚠️  Compression not running. Run 'cs-start' first.

# Then manually start:
cs-start     # Start compression
csi          # Now works
```

### Manual Workflow (No Auto-Start)

```bash
# Start what you need
cs-start         # Start compression
# OR
cproxy-start     # Start both

# Use aliases
csi
csr-proxy
qsi-yolo

# Check status
cs-status
cproxy-status
```

---

## Troubleshooting

### Alias Says "Not Running"

```bash
# Check what's running
cs-status
cproxy-status

# Start what's needed
cs-start         # Just compression
cproxy-start     # Both layers

# Verify
cs-health
cproxy-health
```

### Want Instant Aliases (No Checks)

Remove the `_check_compression` / `_check_proxy` calls from aliases:

```bash
# Instead of:
csi() { _check_compression || return 1; OPENAI_BASE_URL="..." claude "$@"; }

# Use:
csi() { OPENAI_BASE_URL="http://127.0.0.1:8787/v1" claude "$@"; }
```

---

## Performance

| Version | Alias Latency |
|---------|---------------|
| v2.1 (auto-start) | ~3 seconds (waits for startup) |
| v2.2 (check only) | ~0ms (instant!) |

**Improvement:** Aliases are now **instant** because they don't start services, they just use them.

---

*Quick Reference v2.2 - April 2, 2026*
