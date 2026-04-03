# Install Compression Stack Aliases

**Quick Start:** One command to add all aliases to your shell.

---

## Option 1: Automatic Install (Recommended)

```bash
# Single command install
curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/compression/scripts/install-aliases.sh | bash
```

This will:
- ✅ Backup your existing `~/.zshrc`
- ✅ Add compression aliases
- ✅ Reload your shell
- ✅ Verify installation

---

## Option 2: Manual Install

### Step 1: Copy aliases file

```bash
# Clone repository (if not already done)
git clone https://github.com/aaaronmiller/claude-code-proxy.git ~/code/claude-code-proxy

# Or download just the aliases file
curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/compression/scripts/compression-aliases.zsh \
  -o ~/.compression-aliases.zsh
```

### Step 2: Add to ~/.zshrc

```bash
# Add source line to ~/.zshrc
echo '' >> ~/.zshrc
echo '# Compression Stack Aliases' >> ~/.zshrc
echo 'source ~/.compression-aliases.zsh' >> ~/.zshrc

# Or if you kept the file in the repo:
echo '' >> ~/.zshrc
echo '# Compression Stack Aliases' >> ~/.zshrc
echo 'source ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh' >> ~/.zshrc
```

### Step 3: Reload shell

```bash
source ~/.zshrc
```

---

## Option 3: Copy-Paste Install

Copy this entire block and paste into your terminal:

```bash
# Create aliases file
cat > ~/.compression-aliases.zsh << 'ALIASES'
# Compression Stack Aliases
export COMPRESSION_DIR="$HOME/code/claude-code-proxy/compression"
export PATH="$COMPRESSION_DIR/scripts:$PATH"

_compression_auto_start() {
    if ! pgrep -f "headroom proxy" > /dev/null 2>&1; then
        echo -n "🔧 Starting compression... "
        headroom proxy --port 8787 --mode token_headroom \
            --openai-api-url https://openrouter.ai/api/v1 \
            --backend openrouter --no-telemetry > /dev/null 2>&1 &
        sleep 3
        pgrep -f "headroom proxy" > /dev/null 2>&1 && echo "✅" || echo "⚠️ Failed"
    fi
}

alias cs-start='_compression_auto_start'
alias cs-stop='pkill -f "headroom proxy" 2>/dev/null; echo "⏹️ Stopped"'
alias cs-status='pgrep -f "headroom proxy" > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"'

alias csi='_compression_auto_start && claude'
alias csr='_compression_auto_start && claude --resume'
alias csi-yolo='_compression_auto_start && claude --dangerously-skip-permissions'

alias qsi='_compression_auto_start && qwen'
alias qsr='_compression_auto_start && qwen --resume'
alias qsi-yolo='_compression_auto_start && qwen --dangerously-skip-permissions'

alias csi-codex='_compression_auto_start && codex'
alias csr-codex='_compression_auto_start && codex resume'

alias osi='_compression_auto_start && opencode'
alias osr='_compression_auto_start && opencode --resume'

alias ocl='_compression_auto_start && openclaw'
alias ocr='_compression_auto_start && openclaw --resume'

alias hsi='_compression_auto_start && hermes'
alias hsr='_compression_auto_start && hermes --resume'
ALIASES

# Add to ~/.zshrc
echo '' >> ~/.zshrc
echo '# Compression Stack Aliases' >> ~/.zshrc
echo 'source ~/.compression-aliases.zsh' >> ~/.zshrc

# Reload
source ~/.zshrc

echo "✅ Aliases installed!"
```

---

## Verify Installation

```bash
# Check if aliases are loaded
alias csi
alias csr
alias cs-start

# Should show:
# alias csi='_compression_auto_start && claude'
# alias csr='_compression_auto_start && claude --resume'
# alias cs-start='_compression_auto_start'
```

---

## Test It Works

```bash
# Start compression
cs-start

# Check status
cs-status

# Start Claude with compression
csi

# Should auto-start compression if not running, then launch Claude
```

---

## Uninstall

```bash
# Remove from ~/.zshrc
sed -i '/# Compression Stack Aliases/d' ~/.zshrc
sed -i '/compression-aliases.zsh/d' ~/.zshrc
sed -i '/COMPRESSION_DIR/d' ~/.zshrc

# Remove aliases file
rm -f ~/.compression-aliases.zsh

# Reload
source ~/.zshrc

echo "✅ Aliases uninstalled!"
```

---

## Available Aliases

| Command | Description |
|---------|-------------|
| `csi` | Start Claude with compression |
| `csr` | Resume Claude session |
| `csi-yolo` | Claude with no permission prompts |
| `qsi` | Start Qwen with compression |
| `qsr` | Resume Qwen session |
| `csi-codex` | Start Codex with compression |
| `csr-codex` | Resume Codex session |
| `osi` | Start OpenCode with compression |
| `osr` | Resume OpenCode session |
| `ocl` | Start OpenClaw with compression |
| `ocr` | Resume OpenClaw session |
| `hsi` | Start Hermes with compression |
| `hsr` | Resume Hermes session |
| `cs-start` | Start compression stack |
| `cs-stop` | Stop compression stack |
| `cs-status` | Check compression status |

---

## Requirements

- **Shell:** zsh (bash also works with minor modifications)
- **Dependencies:**
  - `headroom` (installed via `install-all.sh`)
  - `pgrep` (usually pre-installed)
  - `curl` (for auto-install)

---

## Troubleshooting

### Aliases not working

```bash
# Check if file is sourced
grep compression-aliases ~/.zshrc

# Should show: source ~/.compression-aliases.zsh

# If not, add it:
echo 'source ~/.compression-aliases.zsh' >> ~/.zshrc
source ~/.zshrc
```

### Compression not auto-starting

```bash
# Check if headroom is installed
which headroom

# If not found, install it:
pip install --user "headroom-ai[ml]"

# Or run full install:
curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/install-all.sh | bash
```

### Permission denied errors

```bash
# Make sure aliases file is readable
chmod 644 ~/.compression-aliases.zsh

# Or if using repo version:
chmod 644 ~/code/claude-code-proxy/compression/scripts/compression-aliases.zsh
```

---

*Installation Guide v1.0.0 - April 2, 2026*
