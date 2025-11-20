# Claude Code Proxy - Complete Setup Guide

This guide will walk you through setting up the Claude Code Proxy from scratch to production deployment.

---

## Prerequisites

- Python 3.9 or higher
- pip or uv package manager
- Git (for cloning)
- Docker (optional, for containerized deployment)

---

## Quick Start (5 Minutes)

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-code-proxy.git
cd claude-code-proxy

# Install dependencies using UV (recommended)
uv sync

# OR using pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API key
nano .env  # or use your preferred editor
```

**Minimum required configuration:**
```bash
OPENAI_API_KEY="your-api-key-here"
```

### 3. Start the Proxy

```bash
# Start with default settings
python start_proxy.py

# The server will start on http://localhost:8082
```

### 4. Test with Claude Code CLI

```bash
# In a new terminal, set the base URL
export ANTHROPIC_BASE_URL=http://localhost:8082

# Test with Claude Code
claude "Write a Python function to calculate fibonacci numbers"
```

**That's it!** You now have a working Claude Code Proxy.

---

## Detailed Setup

### Environment Configuration

The `.env` file supports many configuration options. Here are the most important ones:

#### Required Settings

```bash
# Your API key (required)
OPENAI_API_KEY="sk-your-api-key-here"

# Base URL for your provider (optional, defaults to OpenAI)
OPENAI_BASE_URL="https://api.openai.com/v1"
```

#### Model Mapping

```bash
# Map Claude models to your preferred models
BIG_MODEL="gpt-4o"           # For Claude Opus requests
MIDDLE_MODEL="gpt-4o"        # For Claude Sonnet requests
SMALL_MODEL="gpt-4o-mini"    # For Claude Haiku requests
```

#### Reasoning Support

```bash
# Enable reasoning for supported models
REASONING_EFFORT="high"           # low, medium, high
REASONING_MAX_TOKENS="8000"       # Max tokens for reasoning
REASONING_EXCLUDE="false"         # Show/hide reasoning tokens
```

#### Usage Tracking (Optional)

```bash
# Enable persistent usage tracking
TRACK_USAGE="true"

# Use compact single-line logger
USE_COMPACT_LOGGER="true"
```

---

## Interactive Model Selection

Instead of manually editing `.env`, you can use the interactive model selector:

```bash
# Launch the interactive selector
python scripts/select_model.py
```

Features:
- Browse 352+ models with filtering
- Apply pre-built templates (Free, Production, etc.)
- Get recommendations for cost optimization
- Configure BIG/MIDDLE/SMALL models
- Set reasoning parameters
- Save configurations for later use

---

## Provider-Specific Setup

### OpenAI

```bash
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o-mini"
```

### OpenRouter

```bash
OPENAI_API_KEY="sk-or-..."
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="openai/gpt-5"
REASONING_EFFORT="high"
```

### Azure OpenAI

```bash
OPENAI_API_KEY="your-azure-key"
OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
BIG_MODEL="gpt-4"
```

### Local Models (Ollama)

```bash
OPENAI_API_KEY="dummy"  # Required but can be any value
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/llama3.1:70b"
SMALL_MODEL="ollama/llama3.1:8b"
REASONING_EFFORT="medium"
```

### LMStudio

```bash
OPENAI_API_KEY="dummy"
OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
BIG_MODEL="lmstudio/Meta-Llama-3.1-405B-Instruct"
```

### Hybrid Setup (Mix Local & Remote)

```bash
# Main config
OPENAI_API_KEY="your-openrouter-key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# BIG model - Local Ollama
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="ollama/qwen2.5:72b"

# MIDDLE model - OpenRouter (uses main config)
ENABLE_MIDDLE_ENDPOINT="false"
MIDDLE_MODEL="openai/gpt-5"

# SMALL model - LMStudio
ENABLE_SMALL_ENDPOINT="true"
SMALL_ENDPOINT="http://127.0.0.1:1234/v1"
SMALL_API_KEY="dummy"
SMALL_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Build and start
docker-compose up --build

# 3. Use with Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "Hello world"
```

### Manual Docker Build

```bash
# Build image
docker build -t claude-code-proxy .

# Run container
docker run -p 8082:8082 --env-file .env claude-code-proxy

# Or with environment variables
docker run -p 8082:8082 \
  -e OPENAI_API_KEY="your-key" \
  -e OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
  -e BIG_MODEL="openai/gpt-5" \
  claude-code-proxy
```

---

## Advanced Features

### Usage Tracking & Analytics

Enable usage tracking to see which models you actually use, track costs, and optimize performance:

```bash
# Enable tracking
TRACK_USAGE="true"
```

After making some requests, view analytics:

```bash
python scripts/view_usage_analytics.py
```

Features:
- Top models by actual request count
- Cost summary (7/30/90 days)
- JSON/TOON conversion analysis
- Export to CSV for custom analysis

### Compact Logger

Enable single-line logging with emojis and sophisticated color coding:

```bash
USE_COMPACT_LOGGER="true"
```

Benefits:
- 80% less terminal clutter
- Session-based color consistency
- Type identification at a glance
- All info on one line per event

### Dashboard System

Interactive configuration with live previews:

```bash
python scripts/configure_dashboard.py
```

Select from 5 dashboard modules:
- Performance Monitor
- Activity Feed
- Routing Visualizer
- Analytics Panel
- Request Waterfall

---

## Testing Your Setup

### 1. Test Proxy Startup

```bash
python start_proxy.py
```

You should see:
- Colorful startup display
- Provider information
- Model mappings
- Reasoning settings
- Server listening on port 8082

### 2. Test Basic Request

```bash
curl -X POST http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: test" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

### 3. Test with Claude Code CLI

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
claude "Write a haiku about programming"
```

### 4. Verify Usage Tracking (if enabled)

```bash
# Check database was created
ls -la usage_tracking.db

# View analytics
python scripts/view_usage_analytics.py
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError

```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

#### 2. API Key Invalid

```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY

# Verify the key is correct (no quotes in value)
OPENAI_API_KEY=sk-your-key-here  # Correct
```

#### 3. Port Already in Use

```bash
# Use a different port
python start_proxy.py --port 8083

# Or check what's using port 8082
lsof -i :8082
```

#### 4. Model Not Found

```bash
# Update model database
python scripts/fetch_openrouter_models.py

# Check if model exists
python scripts/select_model.py
```

#### 5. Docker Build Fails

```bash
# Clear Docker cache
docker-compose down
docker system prune -a

# Rebuild
docker-compose up --build
```

### Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions
- Review [README.md](README.md) for feature documentation
- Check logs for error messages
- Verify `.env` configuration

---

## Production Deployment

### Security Checklist

- [ ] Use environment variables (never hardcode keys)
- [ ] Set `ANTHROPIC_API_KEY` to require client authentication
- [ ] Use HTTPS in production (reverse proxy)
- [ ] Limit network access (firewall rules)
- [ ] Enable rate limiting (if needed)
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### Performance Optimization

```bash
# Server settings
HOST="0.0.0.0"
PORT="8082"
LOG_LEVEL="info"  # Use "warning" or "error" in production

# Disable verbose features in production
USE_COMPACT_LOGGER="true"  # Less logging overhead
```

### Monitoring

```bash
# Enable usage tracking for analytics
TRACK_USAGE="true"

# View regular reports
python scripts/view_usage_analytics.py
```

### Backup & Persistence

```bash
# Backup usage database
cp usage_tracking.db usage_tracking_backup.db

# Backup configuration
cp .env .env.backup
```

---

## Next Steps

- Read [README.md](README.md) for complete feature list
- Explore [docs/](docs/) for advanced topics
- Try different model providers
- Enable usage tracking and analytics
- Join the community and contribute

---

## Quick Reference

### Start Commands

```bash
# Basic start
python start_proxy.py

# With custom models
python start_proxy.py --big-model gpt-5 --reasoning-effort high

# Load saved mode
python start_proxy.py --load-mode production

# List available modes
python start_proxy.py --list-modes
```

### Common Scripts

```bash
# Model selection
python scripts/select_model.py

# Usage analytics
python scripts/view_usage_analytics.py

# Update model database
python scripts/fetch_openrouter_models.py

# Dashboard configuration
python scripts/configure_dashboard.py
```

### Environment Variables (Key Ones)

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | API key for provider | Required |
| `OPENAI_BASE_URL` | Provider base URL | OpenAI |
| `BIG_MODEL` | Model for Opus | gpt-4o |
| `MIDDLE_MODEL` | Model for Sonnet | gpt-4o |
| `SMALL_MODEL` | Model for Haiku | gpt-4o-mini |
| `REASONING_EFFORT` | Reasoning level | None |
| `TRACK_USAGE` | Enable tracking | false |
| `USE_COMPACT_LOGGER` | Compact logs | false |

---

**Made with ❤️ for the developer community**

For more help, see [README.md](README.md) or [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
