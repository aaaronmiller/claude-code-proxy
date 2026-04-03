# Compression Stack - Single Instance Architecture

**Version:** 2.3.0  
**Date:** April 2, 2026

---

## Key Principle: ONE Proxy, ALL Terminals

```
Terminal 1 ─┐
Terminal 2 ─┤
Terminal 3 ─┼──→ Headroom (:8787) ──→ OpenRouter
Terminal 4 ─┤
Terminal 5 ─┘
```

**One Headroom instance serves ALL terminals and ALL CLI tools.**

---

## What You Need

### 1. Start Compression ONCE (Per Session)

```bash
# At the start of your work session:
cs-start

# That's it! All terminals can now use compression.
```

### 2. Use Any CLI in Any Terminal

```bash
# Terminal 1
csi          # Claude with compression

# Terminal 2 (simultaneously)
qsi          # Qwen with compression

# Terminal 3 (simultaneously)
csi-codex    # Codex with compression

# Terminal 4 (simultaneously)
osi          # OpenCode with compression

# All share the SAME Headroom instance on :8787
```

---

## Why This Works

### Headroom is Multi-Threaded

```
Headroom (:8787)
├── Request from Terminal 1 (Claude)
├── Request from Terminal 2 (Qwen)
├── Request from Terminal 3 (Codex)
├── Request from Terminal 4 (OpenCode)
└── Request from Terminal 5 (Hermes)

All handled concurrently by the same process.
```

### No Per-CLI Proxy Needed

- ❌ **DON'T** start `headroom` for Claude, then another for Qwen, etc.
- ✅ **DO** start `headroom` ONCE, all CLIs use it

---

## Typical Workflow

### Morning: Start Session

```bash
# Open first terminal
cs-start  # Start compression (takes ~2s)

# That's it for the whole day!
```

### Throughout the Day

```bash
# Terminal 1: Claude session
csi
# ... work ...

# Terminal 2: Quick Qwen question
qsi
# ... work ...

# Terminal 3: Codex for something else
csi-codex
# ... work ...

# All share the same compression instance
```

### End of Day

```bash
# Optional: Stop compression
cs-stop

# Or just leave it running (minimal idle resource usage)
```

---

## Resource Usage

| State | CPU | Memory | VRAM |
|-------|-----|--------|------|
| **Idle** | <1% | 200 MB | 0 MB |
| **Active** | 10-30% | 200 MB | 5.3 GB |

**Idle usage is negligible** - safe to leave running all day.

---

## Multi-User Scenario

Even with multiple users on the same machine:

```bash
# User 1 Terminal 1
csi  # Uses Headroom :8787

# User 2 Terminal 1 (same machine)
csi  # Also uses Headroom :8787

# Both share the same instance
```

**Note:** For production multi-user, you'd want separate instances. For single dev machine, one instance is perfect.

---

## What NOT to Do

### ❌ Don't Start Multiple Instances

```bash
# WRONG - Don't do this:
cs-start  # Terminal 1
cs-start  # Terminal 2 (unnecessary!)
cs-start  # Terminal 3 (crazy!)

# One is enough!
```

### ❌ Don't Start Per-CLI

```bash
# WRONG - Don't do this:
headroom --port 8787  # For Claude
headroom --port 8788  # For Qwen (unnecessary!)
headroom --port 8789  # For Codex (crazy!)

# One port serves all!
```

---

## Troubleshooting

### "Address Already in Use" Error

```bash
# Means Headroom is already running (good!)
cs-start
# Output: ✅ Compression already running

# Just use your aliases:
csi  # Works!
```

### "Connection Refused" Error

```bash
# Means Headroom isn't running
csi
# Output: ⚠️ Compression not running. Run 'cs-start' first.

# Start it:
cs-start

# Now works:
csi
```

### Check What's Running

```bash
# See all Headroom processes
pgrep -fa "headroom"

# Should show ONE process like:
# 12345 headroom proxy --port 8787 ...

# If you see multiple, kill extras:
pkill -f "headroom proxy"
cs-start  # Start fresh single instance
```

---

## Advanced: Systemd Auto-Start

For automatic start on boot (single instance):

```bash
# One-time setup
~/code/claude-code-proxy/compression/scripts/install-autostart.sh

# After this, Headroom starts automatically on boot
# No manual cs-start needed!
csi  # Works immediately after boot
```

---

## Performance

### Single Instance (Recommended)

| Metric | Value |
|--------|-------|
| Memory | 200 MB (shared) |
| VRAM | 5.3 GB (shared) |
| CPU per request | 10-30% |
| Concurrent requests | Unlimited (queued) |

### Multiple Instances (DON'T DO THIS)

| Metric | Value |
|--------|-------|
| Memory | 200 MB × N (wasteful) |
| VRAM | 5.3 GB × N (impossible!) |
| CPU per request | Same |
| Concurrent requests | Same |

**Single instance is strictly better.**

---

## Summary

| Do This | Not This |
|---------|----------|
| `cs-start` once per day | `cs-start` in every terminal |
| One Headroom :8787 | Multiple ports |
| Share across all CLIs | Per-CLI instances |
| Leave running all day | Start/stop constantly |

---

*Single Instance Guide v2.3.0 - April 2, 2026*
