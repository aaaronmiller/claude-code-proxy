# Install Compression Layer - Existing Installation Guide

**Version:** 1.0.0  
**Date:** April 2, 2026

---

## Quick Answer

**YES!** The install command plays nicely with existing installations.

It will:
- ✅ Detect your existing claude-code-proxy
- ✅ Skip re-installing what's already there
- ✅ Only add the compression layer
- ✅ Preserve all your existing config
- ✅ Not break anything

---

## For Existing Installations

### Option 1: Run Install Script (Recommended)

```bash
# From your existing claude-code-proxy directory
cd ~/code/claude-code-proxy

# Run the compression installer
./compression/scripts/install-all.sh
```

**What it does:**
1. Checks if claude-code-proxy exists → ✅ Yes, skips clone
2. Checks if Headroom installed → Installs if missing
3. Checks if RTK installed → Installs if missing
4. Adds `compression/` directory → ✅ Adds it
5. Installs aliases → ✅ Adds to ~/.zshrc
6. Configures env vars → ✅ Updates .envrc

**What it preserves:**
- ✅ Your `.envrc` settings
- ✅ Your database
- ✅ Your logs
- ✅ Your custom config
- ✅ Your git history

---

### Option 2: Manual Install (If You Prefer Control)

```bash
# 1. Go to your existing installation
cd ~/code/claude-code-proxy

# 2. Pull latest changes (includes compression/)
git pull origin main

# 3. Install dependencies (if any new ones)
source .venv/bin/activate
pip install -r requirements.txt

# 4. Install Headroom (compression layer)
pip install --user "headroom-ai[ml]"

# 5. Install RTK (optional, for command compression)
cargo install rtk  # OR: pip install --user rtk

# 6. Add aliases
cat compression/scripts/compression-aliases.zsh >> ~/.zshrc
source ~/.zshrc

# 7. Start compression
cs-start

# Done!
csi  # Test it works
```

---

### Option 3: Just Add Compression (Minimal)

If you already have claude-code-proxy and just want compression:

```bash
# Install Headroom
pip install --user "headroom-ai[ml]"

# Add aliases
cat ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh >> ~/.zshrc
source ~/.zshrc

# Start compression
cs-start

# Use
csi
```

That's it! Your existing proxy keeps working, compression is added on top.

---

## What Gets Added

### New Files/Directories

```
claude-code-proxy/
├── compression/              # NEW - All compression code
│   ├── bin/
│   ├── scripts/
│   ├── docs/
│   └── lib/
├── .envrc                    # UPDATED - Compression env vars
└── ... (your existing files preserved)
```

### New Aliases

```bash
# Added to ~/.zshrc
csi          # Claude with compression
csr          # Resume Claude
qsi          # Qwen with compression
cs-start     # Start compression
# ... and 30+ more
```

### New Dependencies

```bash
# Python packages
headroom-ai[ml]  # Compression layer

# Optional
rtk              # Command compression
```

---

## Verification

### After Installation

```bash
# Check compression is working
cs-status
# Should show: ✅ Compression: Running

# Test with Claude
csi
# Should start Claude with compression

# Check Headroom directly
curl http://127.0.0.1:8787/health
# Should return: {"status":"healthy",...}
```

### Check Nothing Broke

```bash
# Your existing proxy should still work
cd ~/code/claude-code-proxy
python start_proxy.py --skip-validation

# In another terminal
export ANTHROPIC_BASE_URL="http://127.0.0.1:8082"
claude
# Should work exactly as before
```

---

## Rollback (If Needed)

If something goes wrong:

```bash
# Remove compression aliases
sed -i '/compression-aliases/d' ~/.zshrc
source ~/.zshrc

# Stop compression
cs-stop

# Uninstall Headroom (optional)
pip uninstall headroom-ai

# Your existing proxy is untouched
cd ~/code/claude-code-proxy
python start_proxy.py
# Works exactly as before
```

---

## Common Scenarios

### Scenario 1: Fresh Install

```bash
# Run full installer
./compression/scripts/install-all.sh

# Installs everything from scratch
```

### Scenario 2: Existing Proxy, No Compression

```bash
# Just add compression
cd ~/code/claude-code-proxy
./compression/scripts/install-all.sh

# Detects existing proxy, adds compression only
```

### Scenario 3: Existing Proxy, Old Compression

```bash
# Update compression
cd ~/code/claude-code-proxy
git pull origin main

# Updates compression/ to latest
```

### Scenario 4: Multiple Machines

```bash
# Machine 1: Full install
./compression/scripts/install-all.sh

# Machine 2: Just compression (proxy already installed)
pip install --user "headroom-ai[ml]"
cat compression/scripts/compression-aliases.zsh >> ~/.zshrc
source ~/.zshrc
cs-start
```

---

## Troubleshooting

### "Port 8787 Already in Use"

```bash
# Means Headroom is already running (good!)
lsof -i :8787

# If it's your old Headroom instance, kill it:
pkill -f "headroom proxy"

# Start fresh:
cs-start
```

### "Aliases Not Found"

```bash
# Reload shell
source ~/.zshrc

# Check if added
grep compression-aliases ~/.zshrc

# If missing, add manually:
cat ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh >> ~/.zshrc
source ~/.zshrc
```

### "Headroom Not Found"

```bash
# Install it
pip install --user "headroom-ai[ml]"

# Verify
which headroom
```

---

## Summary

| Scenario | Command | Result |
|----------|---------|--------|
| Fresh install | `./install-all.sh` | Installs everything |
| Existing proxy | `./install-all.sh` | Adds compression only |
| Just compression | `pip install headroom-ai[ml]` | Minimal install |
| Update | `git pull` | Updates compression |

**All scenarios preserve your existing config and data.**

---

*Existing Installation Guide v1.0.0 - April 2, 2026*
