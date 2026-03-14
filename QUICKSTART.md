# ⚡ Quick Start Guide

Get The Ultimate Proxy up and running in minutes!

---

## 🎯 What You'll Get

After following this guide, you'll have:
- ✅ A fully configured proxy server
- ✅ Web dashboard at `http://localhost:8082`
- ✅ Claude Code CLI routing through the proxy
- ✅ Usage tracking and analytics
- ✅ Support for multiple providers (OpenRouter, Gemini, OpenAI, etc.)

---

## 📋 Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- **One of the following**:
  - `uv` package manager (recommended) - [Install](https://docs.astral.sh/uv/)
  - `pip` package manager (comes with Python)

---

## 🚀 Automated Setup (Recommended)

The easiest way to get started is with our automated setup script.

### Step 1: Clone the Repository

```bash
git clone https://github.com/holegots/claude-code-proxy.git
cd claude-code-proxy
```

### Step 2: Run the Quick Start Script

```bash
python quickstart.py
```

This script will:
1. ✅ Check Python version (3.9+ required)
2. ✅ Create a virtual environment
3. ✅ Install all dependencies
4. ✅ Launch an interactive configuration wizard
5. ✅ Set up your `.env` file
6. ✅ Initialize the database
7. ✅ Start the proxy server

### Step 3: Configure Your API Provider

The setup wizard will ask you to choose a provider:

| Option | Description | Best For |
|--------|-------------|----------|
| **1. OpenRouter** | Access to 100+ models | Multi-model access |
| **2. OpenAI** | Direct OpenAI API | OpenAI models only |
| **3. Google Gemini** | Google's models | Gemini/Flash models |
| **4. VibeProxy** | Free premium models | Free tier users |
| **5. Skip** | Configure manually later | Advanced users |

> 💡 **Don't have an API key yet?**
> - OpenRouter: [Get key here](https://openrouter.ai/keys)
> - OpenAI: [Get key here](https://platform.openai.com/api-keys)
> - Google: [Get key here](https://aistudio.google.com/apikey)
> - VibeProxy: [Download](https://github.com/automazeio/vibeproxy/releases)

### Step 4: Start Using!

Once the proxy is running, you'll see:

```
🌐 Serving Svelte Web UI from: /path/to/web-ui/build
✅ Live metrics system started
✅ Notification service initialized
✅ User management initialized
✅ Alert engine started
✅ Advanced scheduler started

═══════════════════════════════════════════════════════════
  The Ultimate Proxy is running at: http://localhost:8082
═══════════════════════════════════════════════════════════
```

---

## 🔧 Manual Setup (Alternative)

If you prefer manual control:

### Step 1: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# OR using pip
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

Add your configuration:

```bash
# Provider (choose one)
OPENROUTER_API_KEY="sk-or-v1-your-key-here"
# OPENAI_API_KEY="sk-your-key-here"
# GOOGLE_API_KEY="your-key-here"

# Model routing
BIG_MODEL="anthropic/claude-sonnet-4-20250514"
MIDDLE_MODEL="google/gemini-2.0-flash-001"
SMALL_MODEL="google/gemini-2.0-flash-001"

# Server settings
HOST="0.0.0.0"
PORT="8082"

# Features
ENABLE_DASHBOARD="true"
TRACK_USAGE="true"
```

### Step 3: Run the Setup Wizard

```bash
python start_proxy.py --setup
```

### Step 4: Start the Proxy

```bash
python start_proxy.py
```

---

## 🎮 Using with Claude Code

### Basic Usage

Open a **new terminal** and run:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY=pass
claude
```

### Recommended: Add Aliases

Add these to your `~/.zshrc` or `~/.bash_profile`:

```bash
# Toggle between proxy and direct Anthropic
cproxy() {
  if [[ -n "$ANTHROPIC_BASE_URL" ]]; then
    unset ANTHROPIC_BASE_URL ANTHROPIC_CUSTOM_HEADERS
    export PROXY_AUTH_KEY="${CLAUDE_REAL_KEY:-$PROXY_AUTH_KEY}"
    echo "🎯 Direct to Anthropic"
  else
    export CLAUDE_REAL_KEY="${PROXY_AUTH_KEY}"
    export ANTHROPIC_BASE_URL="${CLAUDE_PROXY_URL:-http://localhost:8082}"
    echo "🔀 Proxy: $ANTHROPIC_BASE_URL"
  fi
}

# Start the proxy server
alias ccproxy='cd $HOME/code/claude-code-proxy && python quickstart.py --no-launch'

# Claude Code via proxy
alias cproxy-init='ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY=pass CLAUDE_CODE_MAX_OUTPUT_TOKENS=128768 claude --dangerously-skip-permissions --verbose'

# Continue session via proxy
alias cproxy-continue='ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY=pass CLAUDE_CODE_MAX_OUTPUT_TOKENS=128768 claude --continue --dangerously-skip-permissions --verbose'

# Direct to Anthropic (no proxy)
alias claude-init='claude --dangerously-skip-permissions --verbose'
alias claude-continue='claude --continue --dangerously-skip-permissions --verbose'
```

Then reload your shell:

```bash
source ~/.zshrc  # or source ~/.bash_profile
```

Now you can:
```bash
cproxy        # Toggle proxy on/off
ccproxy       # Start the proxy server
cproxy-init   # Start Claude via proxy
claude-init   # Start Claude direct
```

---

## 🧪 Verify Installation

### 1. Check Proxy Status

```bash
curl http://localhost:8082/config
```

Should return configuration JSON.

### 2. Test with a Simple Request

```bash
curl -X POST http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pass" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 3. Check Web Dashboard

Open your browser to: `http://localhost:8082`

You should see the dashboard with:
- Real-time request monitoring
- Provider configuration
- Model selection
- Usage analytics

---

## 🐛 Troubleshooting

### "Python 3.9+ required" Error

**Solution**: Install Python 3.9 or higher
```bash
# Check current version
python --version

# Install on Ubuntu/Debian
sudo apt update && sudo apt install python3.11

# Install on macOS
brew install python@3.11

# Install on Windows
# Download from https://www.python.org/downloads/
```

### "uv: command not found" Error

**Solution**: Install uv or use pip instead
```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# OR use pip
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Reinstall dependencies
```bash
# Activate venv first
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Then reinstall
pip install -r requirements.txt
```

### "Port 8082 already in use"

**Solution**: Change the port in `.env`
```bash
PORT=8083  # or any available port
```

### "401 Unauthorized" Error

**Solution**: Check your API key
```bash
# Run the doctor command
python start_proxy.py --doctor

# Or reconfigure
python start_proxy.py --setup
```

### Database Errors (muted_until, missing columns)

**Solution**: The database schema will be auto-created on startup. If you have an old database:
```bash
# Option 1: Delete and recreate
rm usage_tracking.db
python start_proxy.py

# Option 2: Add missing column manually
sqlite3 usage_tracking.db "ALTER TABLE alert_rules ADD COLUMN muted_until TEXT"
```

---

## 📚 Next Steps

Now that you're set up, explore these features:

| Feature | Command | Description |
|---------|---------|-------------|
| **Settings** | `python start_proxy.py --settings` | Unified settings TUI |
| **Model Selection** | `python start_proxy.py --select-models` | Interactive model picker |
| **Health Check** | `python start_proxy.py --doctor` | Auto-fix common issues |
| **Analytics** | `python start_proxy.py --analytics` | View usage statistics |
| **Crosstalk** | `python start_proxy.py --crosstalk-studio` | Multi-model conversations |
| **Configuration** | `python start_proxy.py --config` | Show current config |

---

## 🆘 Getting Help

- **Documentation**: [Full Docs](docs/index.md)
- **Setup Guide**: [Detailed Setup](docs/setup.md)
- **Crosstalk**: [Multi-Model Chat](docs/crosstalk.md)
- **Issues**: [GitHub Issues](https://github.com/holegots/claude-code-proxy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/holegots/claude-code-proxy/discussions)

---

## 🎉 Success!

You're now ready to use The Ultimate Proxy with Claude Code!

**Quick Reference:**
```bash
# Terminal 1: Start proxy
python start_proxy.py

# Terminal 2: Use Claude
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY=pass
claude
```

Happy coding! 🚀
