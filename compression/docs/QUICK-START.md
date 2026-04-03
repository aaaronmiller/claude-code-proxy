# Compression Stack - Quick Start

**Version:** 2.3.0  
**Date:** April 2, 2026

---

## The Simple Version

### Step 1: Install Aliases

```bash
# One-time setup
cat ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh >> ~/.zshrc
source ~/.zshrc
```

### Step 2: Start Compression (Once Per Day)

```bash
# At the start of your work session:
cs-start
```

### Step 3: Use Any CLI in Any Terminal

```bash
# Terminal 1
csi          # Claude with compression

# Terminal 2 (open new tab, same compression)
qsi          # Qwen with compression

# Terminal 3 (another tab, still same compression)
csi-codex    # Codex with compression

# All terminals share ONE compression proxy
```

---

## That's It!

**Three commands:**
1. `cs-start` - Start compression (once per day)
2. `csi` - Use Claude with compression
3. `csr` - Resume Claude session

---

## All Aliases

### Claude Code
```bash
csi          # Start Claude
csr          # Resume Claude
csi-yolo     # Claude (no permission prompts)
```

### Qwen Code
```bash
qsi          # Start Qwen
qsr          # Resume Qwen
qsi-yolo     # Qwen (no permission prompts)
```

### Codex
```bash
csi-codex    # Start Codex
csr-codex    # Resume Codex
```

### OpenCode
```bash
osi          # Start OpenCode
osr          # Resume OpenCode
# YOLO mode: set in settings.json
```

### OpenClaw
```bash
ocl          # Start OpenClaw
ocr          # Resume OpenClaw
ocl-yolo     # OpenClaw (no permission prompts)
```

### Hermes
```bash
hsi          # Start Hermes
hsr          # Resume Hermes
hsi-yolo     # Hermes (no permission prompts)
```

### Global
```bash
cs-start     # Start compression
cs-stop      # Stop compression
cs-status    # Check status
```

---

## Typical Day

```bash
# Morning: Open first terminal
cs-start     # Takes 2 seconds

# Use any CLI in any terminal
csi          # Terminal 1
qsi          # Terminal 2
csi-codex    # Terminal 3
# All work simultaneously with same compression

# Evening: Optional cleanup
cs-stop      # Or just leave it running
```

---

## Auto-Start (Optional)

Want compression to start automatically on boot?

```bash
# One-time setup
~/code/claude-code-proxy/compression/scripts/install-autostart.sh

# After this, no manual cs-start needed!
# Compression starts with your computer
csi  # Works immediately
```

---

## Troubleshooting

### "Compression not running"

```bash
# Just start it:
cs-start

# Now use your CLI:
csi
```

### "Which port?"

```
Headroom runs on :8787
All CLIs connect there automatically
```

### "Multiple terminals?"

```
YES! That's the point.
One Headroom instance serves ALL terminals.
Just run cs-start once, then use any terminal.
```

---

## Next Steps

- **Full docs:** `compression/docs/`
- **Alias reference:** `ALIAS-QUICK-REFERENCE.md`
- **Single instance:** `SINGLE-INSTANCE-GUIDE.md`
- **Auto-start:** `AUTO-START-GUIDE.md`

---

*Quick Start v2.3.0 - April 2, 2026*
