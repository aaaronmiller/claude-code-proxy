# Auto-Start Compression Stack with Systemd

**Version:** 1.0.0  
**Date:** April 2, 2026

---

## Why Auto-Start?

**Problem:** Aliases that start services are slow (~3 seconds per command).

**Solution:** Auto-start services with systemd → aliases become instant.

---

## Quick Install

```bash
# Run the auto-start installer
~/code/claude-code-proxy/compression/scripts/install-autostart.sh

# Or manually (see below)
```

---

## Manual Installation

### 1. Headroom Auto-Start

```bash
# Create service directory
mkdir -p ~/.config/systemd/user

# Create service file
cat > ~/.config/systemd/user/headroom.service << 'EOF'
[Unit]
Description=Headroom Compression Proxy
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/headroom proxy --port 8787 --mode token_headroom --openai-api-url https://openrouter.ai/api/v1 --backend openrouter --no-telemetry
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable headroom
systemctl --user start headroom

# Verify
systemctl --user status headroom
```

### 2. Claude Proxy Auto-Start (Optional)

```bash
# Create service file
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
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable claude-proxy
systemctl --user start claude-proxy

# Verify
systemctl --user status claude-proxy
```

### 3. Compression Dashboard Auto-Start (Optional)

```bash
cat > ~/.config/systemd/user/compression-dashboard.service << 'EOF'
[Unit]
Description=Compression Dashboard
After=network.target headroom.service

[Service]
Type=simple
ExecStart=%h/code/claude-code-proxy/compression/scripts/compression-dashboard.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable compression-dashboard
systemctl --user start compression-dashboard
```

---

## Verify Auto-Start

```bash
# Check all services
systemctl --user status headroom claude-proxy compression-dashboard

# Check if running
pgrep -f "headroom proxy" && echo "✅ Headroom running"
pgrep -f "start_proxy.py" && echo "✅ Proxy running"

# Reboot and verify
reboot
# After reboot:
cs-status  # Should show running
```

---

## Usage After Auto-Start

### Aliases Are Now Instant!

```bash
# Before (v2.1): ~3 seconds to start compression
csi  # Waits for headroom to start

# After (v2.2): Instant!
csi  # Uses already-running headroom
```

### Manual Control Still Available

```bash
# Stop compression
cs-stop

# Start compression
cs-start

# Restart
cs-restart

# Check status
cs-status
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
systemctl --user status headroom
journalctl --user -u headroom

# Common issues:
# 1. headroom not installed
pip install --user "headroom-ai[ml]"

# 2. Port already in use
lsof -i :8787
# Kill conflicting process or change port

# 3. Permission issues
chmod +x ~/.local/bin/headroom
```

### Service Starts Then Stops

```bash
# Check logs
journalctl --user -u headroom -f

# Increase restart delay
systemctl --user edit headroom
# Add:
# [Service]
# RestartSec=10
```

### Services Don't Start on Boot

```bash
# Enable linger (start services even when user not logged in)
sudo loginctl enable-linger $USER

# Verify
loginctl show-user $USER | grep Linger
# Should show: Linger=yes
```

---

## Service Management Commands

```bash
# Status
systemctl --user status headroom
systemctl --user status claude-proxy

# Start/Stop/Restart
systemctl --user start headroom
systemctl --user stop headroom
systemctl --user restart headroom

# Enable/Disable auto-start
systemctl --user enable headroom
systemctl --user disable headroom

# View logs
journalctl --user -u headroom -f
journalctl --user -u claude-proxy -f

# Reload config
systemctl --user daemon-reload
```

---

## Uninstall Auto-Start

```bash
# Stop and disable services
systemctl --user stop headroom claude-proxy compression-dashboard
systemctl --user disable headroom claude-proxy compression-dashboard

# Remove service files
rm ~/.config/systemd/user/headroom.service
rm ~/.config/systemd/user/claude-proxy.service
rm ~/.config/systemd/user/compression-dashboard.service

# Reload
systemctl --user daemon-reload

# Aliases will now warn but still work (manual start required)
```

---

## Performance Comparison

| Configuration | Alias Latency | Boot Time |
|---------------|---------------|-----------|
| No auto-start (v2.1) | ~3s | N/A |
| Auto-start (v2.2) | ~0ms | +2s |
| **Net Gain** | **3s per command** | **-2s boot** |

**Break-even:** After 1 command, auto-start wins.

---

*Auto-Start Guide v1.0.0 - April 2, 2026*
