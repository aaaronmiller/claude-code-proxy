# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Step 2: Configure Your Provider

Choose your LLM provider and configure accordingly:

#### VibeProxy / Antigravity (Recommended - Free!)
The easiest way to use Claude Code with premium models. No API keys needed.

1. Install VibeProxy: https://github.com/automazeio/vibeproxy/releases
2. Launch and authenticate with Google (Antigravity)
3. Run the setup wizard:
```bash
python start_proxy.py --setup
# Select "VibeProxy/Antigravity (DETECTED)" when it appears
```

Or configure manually:
```bash
cp .env.example .env
# Edit .env:
# PROVIDER_API_KEY="dummy"
# PROVIDER_BASE_URL="http://127.0.0.1:8317/v1"
# BIG_MODEL="gemini-claude-opus-4-5-thinking"
# MIDDLE_MODEL="gemini-3-pro-preview"
# SMALL_MODEL="gemini-3-flash"
# REASONING_MAX_TOKENS="128000"
```

**Available Antigravity models:**
- `gemini-claude-opus-4-5-thinking` - Claude Opus with 128k thinking
- `gemini-claude-sonnet-4-5-thinking` - Claude Sonnet with thinking
- `gemini-3-pro-preview` - Gemini 3 Pro
- `gemini-3-flash` - Fast Gemini 3

#### OpenAI
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="sk-your-openai-key"
# BIG_MODEL="gpt-4o"
# SMALL_MODEL="gpt-4o-mini"
```

#### Azure OpenAI
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="your-azure-key"
# OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
# BIG_MODEL="gpt-4"
# SMALL_MODEL="gpt-35-turbo"
```

#### Local Models (Ollama)
```bash
cp .env.example .env
# Edit .env:
# OPENAI_API_KEY="dummy-key"
# OPENAI_BASE_URL="http://localhost:11434/v1"
# BIG_MODEL="llama3.1:70b"
# SMALL_MODEL="llama3.1:8b"
```

### Step 3: Start and Use

```bash
# Start the proxy server
python start_proxy.py

# In another terminal, use with Claude Code
ANTHROPIC_BASE_URL=http://localhost:8082 claude
```

### Web Configuration UI

Once the proxy is running, access the web dashboard at `http://localhost:8082`:

- Configure providers with one-click presets
- Set model routing (BIG/MIDDLE/SMALL)
- Manage profiles and settings
- Monitor live request logs

## 🎯 How It Works

| Your Input | Proxy Action | Result |
|-----------|--------------|--------|
| Claude Code sends `claude-3-5-sonnet-20241022` | Maps to your `BIG_MODEL` | Uses `gpt-4o` (or whatever you configured) |
| Claude Code sends `claude-3-5-haiku-20241022` | Maps to your `SMALL_MODEL` | Uses `gpt-4o-mini` (or whatever you configured) |

## 📋 What You Need

- Python 3.9+
- API key for your chosen provider
- Claude Code CLI installed
- 2 minutes to configure

## 🔧 Default Settings
- Server runs on `http://localhost:8082`
- Maps haiku → SMALL_MODEL, sonnet/opus → BIG_MODEL
- Supports streaming, function calling, images

## 🧪 Test Your Setup
```bash
# Quick test
python src/test_claude_to_openai.py
```

That's it! Now Claude Code can use any OpenAI-compatible provider! 🎉