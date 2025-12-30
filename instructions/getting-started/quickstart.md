# Claude Code Proxy - Quick Start

Get up and running in **5 minutes**.

---

## 1. Install (30 seconds)

```bash
# Clone
git clone https://github.com/yourusername/claude-code-proxy.git
cd claude-code-proxy

# Install dependencies
uv sync  # or: pip install -r requirements.txt
```

## 2. Configure (30 seconds)

```bash
# Copy example config
cp .env.example .env

# Edit with your API key
nano .env
```

**Minimum config:**
```bash
OPENAI_API_KEY="your-api-key-here"
```

## 3. Start (10 seconds)

```bash
python start_proxy.py
```

## 4. Use with Claude Code (30 seconds)

```bash
# In new terminal
export ANTHROPIC_BASE_URL=http://localhost:8082

# Test it
claude "Write a Python hello world"
```

---

## That's It! 🎉

**You're now using Claude Code with your chosen provider.**

---

## Next Steps (Optional)

### Use Interactive Model Selector

```bash
python scripts/select_model.py
```

Browse 352+ models and apply pre-built templates.

### Enable Usage Tracking

```bash
# In .env
TRACK_USAGE="true"

# View analytics
python scripts/view_usage_analytics.py
```

### Use Different Providers

**OpenRouter (GPT-5, Claude, etc.):**
```bash
OPENAI_API_KEY="sk-or-..."
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="openai/gpt-5"
```

**Local Models (Ollama):**
```bash
OPENAI_API_KEY="dummy"
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="ollama/qwen2.5:72b"
```

**LMStudio:**
```bash
OPENAI_API_KEY="dummy"
OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
BIG_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
```

---

## Docker (Alternative)

```bash
cp .env.example .env
# Edit .env
docker-compose up --build
```

---

## Need Help?

- Full guide: [SETUP.md](SETUP.md)
- Features: [README.md](README.md)
- Issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Made with ❤️ for the developer community**
