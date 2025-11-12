<div align="center">

# Claude Code Proxy

**Use Claude Code with any OpenAI-compatible provider**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)

</div>

---

## 🎯 What is this?

Claude Code Proxy is a **drop-in replacement** that enables the official Claude Code CLI to work with **any OpenAI-compatible API provider** (OpenAI, OpenRouter, Azure OpenAI, local models via Ollama/LMStudio, and more).

### Why use it?

- ✅ **Use Claude Code with any provider** - Not just Anthropic's API
- ✅ **Save money** - Use local models (Ollama/LMStudio) or cheaper providers
- ✅ **GPT-5 & Advanced Reasoning** - Support for high-reasoning mode
- ✅ **352+ models** - Browse and configure from our model database
- ✅ **Smart templates** - One-click setups for common use cases
- ✅ **Free alternatives** - Find cost-saving model suggestions
- ✅ **Local models** - Run everything on your machine

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/claude-code-proxy.git
cd claude-code-proxy

# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

**Example: OpenRouter with GPT-5 (High Reasoning)**
```bash
OPENAI_API_KEY="your-openrouter-key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="openai/gpt-5"
REASONING_EFFORT="high"
VERBOSITY="high"
```

**Example: Free Local Models (No API costs!)**
```bash
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/llama3.1:70b"
SMALL_MODEL="ollama/llama3.1:8b"
REASONING_EFFORT="medium"
```

### 3. Start Server

```bash
python start_proxy.py
```

### 4. Use with Claude Code

```bash
# Set the base URL
export ANTHROPIC_BASE_URL=http://localhost:8082

# Use Claude Code normally
claude "Write a Python function to calculate fibonacci numbers"
```

---

## ✨ Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Full Claude API Compatibility** | Complete `/v1/messages` endpoint support with all Claude features |
| **Multi-Provider Support** | OpenAI, Azure, OpenRouter, local (Ollama/LMStudio), any OpenAI-compatible API |
| **Smart Model Mapping** | Configure BIG, MIDDLE, SMALL models via environment variables |
| **Function Calling** | Full tool/function calling support with proper conversion |
| **Streaming Responses** | Real-time Server-Sent Events (SSE) streaming |
| **Image Support** | Handle base64 encoded image inputs |
| **Error Handling** | Comprehensive error handling with detailed logging |

### Advanced Features

#### 🤖 GPT-5 & Advanced Reasoning

Full support for reasoning-capable models across all providers via OpenRouter's unified API:

```bash
REASONING_EFFORT="high"        # low, medium, high
REASONING_MAX_TOKENS="8000"    # Optional: fine-grained token control
VERBOSITY="high"               # Response detail level
REASONING_EXCLUDE="false"      # Show/hide reasoning tokens
```

**Comprehensive reasoning support:**

**OpenAI Models:**
- GPT-5 family (openai/gpt-5)
- o1 series (openai/o1, openai/o1-mini)
- o3 series (openai/o3, openai/o3-mini)

**Anthropic Models:**
- Claude 3.7 Sonnet/Opus/Haiku
- Claude 4.x series
- Claude 4.1 series

**OpenRouter & Other Providers:**
- Qwen3 and Qwen-2.5 thinking models
- DeepSeek V3, V3.1, and R1 variants
- xAI Grok with reasoning
- MiniMax M2 thinking models
- Kimi K2 thinking models
- Local models (Ollama Qwen 2.5, DeepSeek V2.5)

**Unified Reasoning Control:**
- Uses OpenRouter's `reasoning` object for cross-provider compatibility
- Supports both `effort` (OpenAI-style) and `max_tokens` (Anthropic-style)
- Auto-detects reasoning-capable models from model metadata
- Preserves reasoning blocks in responses for tool-calling workflows

#### 📦 Mode Templates (10 Pre-Built Configurations)

One-click setups for common use cases:

1. **Free Tier** - Completely free local models
2. **Development** - Cost-effective setup
3. **Production** - Premium GPT-5 setup
4. **Reasoning Intensive** - For complex analysis
5. **Vision & Multimodal** - Image processing
6. **Fast Inference** - Speed optimized
7. **Local Reasoning** - Free local with reasoning
8. **Budget Conscious** - Ultra-low cost
9. **LMStudio** - GUI-based local models
10. **Research** - High context models

#### 🎯 Smart Model Recommender

Intelligent suggestions based on your usage:

- **Find free alternatives** to expensive models
- **Usage pattern analysis** - see what works for you
- **Correlation tracking** - find models used together
- **Cost optimization** - discover cheaper alternatives

#### 📊 Model Database

**352 models** from multiple sources:

- **OpenRouter** - 340+ models
- **LMStudio** - 5 local models (port 1234)
- **Ollama** - 7 local models (port 11434)
- **140 free models** - All listed and easy to find

**Detailed metadata for each model:**
- Pricing per 1M tokens
- Context window size
- Reasoning support
- Vision support
- Provider information
- Endpoint URLs

#### 💾 Configuration Modes

Save and load different configurations:

- **99 mode slots** (ID 1-99)
- **Load by name or ID**
- **Case-insensitive lookup**
- **JSON persistence**
- **Export/import ready**

#### 🎨 Interactive Selector

Beautiful terminal UI with:

- **Color-coded interface** - 16-color palette
- **ASCII art headers** - Professional appearance
- **Browse by capability** - Filter by reasoning, vision, free
- **Search functionality** - Find specific models
- **Visual feedback** - Clear status messages

---

## 🛠️ Configuration

### Environment Variables

#### Required
```bash
OPENAI_API_KEY="your-api-key"    # Your provider's API key
```

#### Security
```bash
ANTHROPIC_API_KEY="exact-key"    # (Optional) Client must match this
```

#### Model Configuration
```bash
BIG_MODEL="openai/gpt-5"         # Claude Opus requests
MIDDLE_MODEL="openai/gpt-5"      # Claude Sonnet requests  
SMALL_MODEL="gpt-4o-mini"        # Claude Haiku requests
```

#### Reasoning Configuration
```bash
REASONING_EFFORT="high"          # low, medium, high
REASONING_MAX_TOKENS="8000"      # Optional: max tokens for reasoning
VERBOSITY="high"                 # Response detail
REASONING_EXCLUDE="false"        # Show/hide reasoning
```

**Reasoning Configuration Options:**

- **REASONING_EFFORT**: Controls reasoning intensity
  - `low`: ~20% of tokens for reasoning (faster)
  - `medium`: ~50% of tokens (balanced)
  - `high`: ~80% of tokens (best quality)
  - Empty/None: Disable reasoning

- **REASONING_MAX_TOKENS**: Fine-grained control (Anthropic/OpenRouter style)
  - Integer value (e.g., `2000`, `8000`, `16000`)
  - Directly specifies maximum tokens for reasoning
  - Works with Anthropic and OpenRouter models
  - Leave empty to use provider default

- **REASONING_EXCLUDE**: Control reasoning token visibility
  - `false`: Include reasoning tokens in response (default)
  - `true`: Use reasoning internally but exclude from response

- **VERBOSITY**: Response detail level
  - `high`: More detailed responses
  - `default` or empty: Standard detail

#### API Configuration
```bash
OPENAI_BASE_URL="https://openrouter.ai/api/v1"  # Your provider's base URL
```

#### Server Settings
```bash
HOST="0.0.0.0"                   # Server host
PORT="8082"                      # Server port
LOG_LEVEL="info"                 # debug, info, warning, error
```

### Provider Examples

#### OpenAI
```bash
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1"
BIG_MODEL="gpt-4o"
MIDDLE_MODEL="gpt-4o"
SMALL_MODEL="gpt-4o-mini"
```

#### OpenRouter
```bash
OPENAI_API_KEY="sk-or-..."
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="openai/gpt-5"
REASONING_EFFORT="high"
```

#### Azure OpenAI
```bash
OPENAI_API_KEY="your-azure-key"
OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
BIG_MODEL="gpt-4"
MIDDLE_MODEL="gpt-4"
SMALL_MODEL="gpt-35-turbo"
```

#### Local Models (Ollama)
```bash
OPENAI_API_KEY="dummy"  # Required but can be dummy
OPENAI_BASE_URL="http://localhost:11434/v1"
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/llama3.1:70b"
SMALL_MODEL="ollama/llama3.1:8b"
REASONING_EFFORT="medium"
```

#### LMStudio
```bash
OPENAI_API_KEY="dummy"  # Required but can be dummy
OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
BIG_MODEL="lmstudio/Meta-Llama-3.1-405B-Instruct"
MIDDLE_MODEL="lmstudio/Meta-Llama-3.1-70B-Instruct"
SMALL_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
```

---

## 💡 Usage Examples

### Interactive Model Selection

**Browse and configure models visually:**

```bash
# Step 1: Fetch latest models (optional, updates monthly)
python scripts/fetch_openrouter_models.py

# Step 2: Launch interactive selector
python scripts/select_model.py
```

**Features:**
- Browse 352 models with filtering
- Apply templates (one-click setup)
- Get recommendations (find free alternatives)
- Configure BIG/MIDDLE/SMALL models
- Set reasoning parameters
- Save as mode for later

### CLI Configuration

**Start with specific models:**

```bash
# Use GPT-5 with high reasoning
python start_proxy.py \
  --big-model openai/gpt-5 \
  --reasoning-effort high \
  --verbosity high

# Use local models
python start_proxy.py \
  --big-model ollama/qwen2.5:72b \
  --reasoning-effort medium
```

**Manage modes:**

```bash
# Save current config as mode
python start_proxy.py --save-mode production

# List all saved modes
python start_proxy.py --list-modes

# Load a mode
python start_proxy.py --load-mode production

# Delete a mode
python start_proxy.py --delete-mode production

# Save with parameters (shorthand)
python start_proxy.py \
  --big-model gpt-5 \
  --reasoning-effort high \
  --mode premium
```

### Programmatic Usage

**Apply a template:**

```python
from src.utils.templates import ModeTemplates

config = ModeTemplates.get_config("free-tier")
# Returns: {'BIG_MODEL': 'ollama/qwen2.5:72b', ...}
```

**Find free alternatives:**

```python
from src.utils.recommender import ModelRecommender

recommender = ModelRecommender()
alternatives = recommender.find_model_alternatives("openai/gpt-5", "free")

for alt in alternatives[:3]:
    print(f"{alt['model']['id']}: score={alt['score']}")
    for reason in alt['reasons'][:2]:
        print(f"  - {reason}")
```

---

## 🔌 API Reference

### Endpoints

#### POST /v1/messages

Main Claude API endpoint. Converts Claude requests to OpenAI format.

**Request:**
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 100,
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

**Response:**
```json
{
  "id": "msg_...",
  "object": "message",
  "content": [...],
  "model": "openai/gpt-5"
}
```

### Model Mapping

| Claude Model | Maps To | Config Variable |
|--------------|---------|-----------------|
| `claude-3-opus-*` | BIG_MODEL | `BIG_MODEL` |
| `claude-3-sonnet-*` | MIDDLE_MODEL | `MIDDLE_MODEL` |
| `claude-3-5-sonnet-*` | MIDDLE_MODEL | `MIDDLE_MODEL` |
| `claude-3-haiku-*` | SMALL_MODEL | `SMALL_MODEL` |

---

## 📊 Model Database

### Statistics

```
Total Models: 352
├─ Local Models: 12 (at TOP)
│  ├─ LMStudio: 5 models
│  └─ Ollama: 7 models
│
├─ OpenRouter Models: 340
│  ├─ Reasoning Support: 210 (62%)
│  ├─ Vision Support: 45 (13%)
│  └─ Standard: 85 (25%)
│
Pricing:
├─ Free Models: 140 (40%)
│  └─ All 12 local + 128 OpenRouter
│
└─ Paid Models: 212 (60%)
```

### Top Free Models (No API costs!)

1. **ollama/qwen2.5:72b** - 131K context, Reasoning ✓
2. **ollama/deepseek-v2.5:236b** - 131K context, Reasoning ✓
3. **ollama/llama3.1:70b** - 131K context
4. **ollama/mistral-nemo:12b** - 131K context
5. **lmstudio/Meta-Llama-3.1-405B-Instruct** - 131K context

### Top Reasoning Models

1. **openai/gpt-5** - Premium reasoning
2. **openai/o3-mini** - Fast reasoning
3. **qwen/qwen-2.5-thinking-32b** - Open source
4. **ollama/qwen2.5:72b** - Free local
5. **amazon/nova-premier-v1** - 1M context

---

## 🛠️ Development

### Project Structure

```
claude-code-proxy/
├── src/
│   ├── main.py                 # FastAPI server
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── model_manager.py    # Model mapping
│   ├── conversion/
│   │   └── request_converter.py # Claude → OpenAI conversion
│   ├── api/
│   │   └── endpoints.py        # API routes
│   ├── utils/
│   │   ├── modes.py            # Configuration modes
│   │   ├── templates.py        # 10 pre-built templates
│   │   └── recommender.py      # Smart recommendations
│   └── client.py               # OpenAI client
├── scripts/
│   ├── fetch_openrouter_models.py  # Model database fetcher
│   └── select_model.py             # Interactive selector
├── models/                     # Model databases
│   ├── openrouter_models.json  # 352 models
│   └── openrouter_models.csv   # Spreadsheet format
├── .env.example                # Config template
├── .gitignore                  # Git ignore rules
├── start_proxy.py              # Startup script
└── README.md                   # This file
```

### Development Setup

```bash
# Install dependencies
uv sync

# Run server in development
uv run python start_proxy.py

# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Adding New Features

**Add a new model source:**

1. Add models to `scripts/fetch_openrouter_models.py`
2. Add endpoint in `get_local_providers()`
3. Update model selector in `scripts/select_model.py`

**Add a new template:**

1. Edit `src/utils/templates.py`
2. Add template to `TEMPLATES` dict
3. Include config, description, requirements

**Extend recommender:**

1. Edit `src/utils/recommender.py`
2. Add new recommendation algorithm
3. Update scoring logic

---

## 📈 Performance

- **Async/await** for high concurrency
- **Connection pooling** for efficiency
- **Streaming support** for real-time responses
- **Configurable timeouts** and retries
- **Smart error handling** with detailed logging
- **Automatic model detection** for reasoning parameters

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Ways to contribute:

- 🐛 Report bugs
- 💡 Suggest features
- 📚 Improve documentation
- 🔧 Submit pull requests
- ⭐ Star the repository

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for Claude Code
- [OpenAI](https://openai.com) for the API
- [OpenRouter](https://openrouter.ai) for model aggregation
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [Ollama](https://ollama.com) for local model serving
- [LMStudio](https://lmstudio.ai) for the GUI

---

## 📞 Support

- 📖 [Documentation](https://github.com/yourusername/claude-code-proxy/wiki)
- 🐛 [Issues](https://github.com/yourusername/claude-code-proxy/issues)
- 💬 [Discussions](https://github.com/yourusername/claude-code-proxy/discussions)

---

## 🎉 Features Summary

✅ **352 models** from multiple sources  
✅ **GPT-5 & Advanced Reasoning** support  
✅ **10 pre-built templates** for quick setup  
✅ **Smart recommendations** with cost optimization  
✅ **99 configuration modes** for flexibility  
✅ **Interactive selector** with beautiful UI  
✅ **Free local models** (Ollama, LMStudio)  
✅ **Multi-provider support** (OpenAI, Azure, OpenRouter, local)  
✅ **Function calling** & streaming support  
✅ **CLI configuration** for automation  
✅ **Comprehensive documentation** & examples  

---

<div align="center">

**Made with ❤️ for the developer community**

[⭐ Star on GitHub](https://github.com/yourusername/claude-code-proxy)

</div>
