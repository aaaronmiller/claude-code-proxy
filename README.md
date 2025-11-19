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
- ✅ **Advanced Reasoning** - Arbitrary thinking token budgets (50k, 350k, etc.)
- ✅ **Rich Terminal Output** - Color-coded logs with progress bars
- ✅ **Token Visualization** - See context window and output usage in real-time
- ✅ **352+ models** - Browse and configure from our model database
- ✅ **Smart templates** - One-click setups for common use cases
- ✅ **Performance Metrics** - Tokens/sec, latency, thinking token tracking
- ✅ **Local models** - Run everything on your machine

- **Full Claude API Compatibility**: Complete `/v1/messages` endpoint support
- **Multiple Provider Support**: OpenAI, Azure OpenAI, local models (Ollama), and any OpenAI-compatible API
- **Smart Model Mapping**: Configure BIG and SMALL models via environment variables
- **Function Calling**: Complete tool use support with proper conversion
- **Streaming Responses**: Real-time SSE streaming support
- **Image Support**: Base64 encoded image input
- **Custom Headers**: Automatic injection of custom HTTP headers for API requests
- **Error Handling**: Comprehensive error handling and logging

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
REASONING_MAX_TOKENS="8000"
VERBOSITY="high"
REASONING_EXCLUDE="false"
```

**Example: Anthropic Claude with Reasoning**
```bash
OPENAI_API_KEY="your-openrouter-key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
BIG_MODEL="anthropic/claude-4.1-sonnet"
REASONING_EFFORT="high"
REASONING_MAX_TOKENS="16000"
REASONING_EXCLUDE="false"
```

**Example: Free Local Models (No API costs!)**
```bash
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/llama3.1:70b"
SMALL_MODEL="ollama/llama3.1:8b"
REASONING_EFFORT="medium"
ENABLE_OPENROUTER_SELECTION="false"  # Hide marketplace, show only local
```

**Example: Local-Only Deployment**
```bash
# Hide all OpenRouter models from selector
ENABLE_OPENROUTER_SELECTION="false"

# Use only local models
BIG_MODEL="ollama/qwen2.5:72b"
MIDDLE_MODEL="ollama/llama3.1:70b"
SMALL_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
REASONING_EFFORT="medium"
```

### 3. Start Server

**Option A: Direct Python**
```bash
python start_proxy.py
```

**Option B: Docker (Recommended for Production)**
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t claude-code-proxy .
docker run -p 8082:8082 --env-file .env claude-code-proxy
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
- **Browse by capability** - Filter by reasoning, vision, free, local
- **Search functionality** - Find specific models
- **Local models filter** - Show only LMStudio/Ollama models (Option 6)
- **OpenRouter toggle** - Hide/show marketplace models via config
- **Template system** - One-click apply 10 pre-built configurations (Option 7)
- **Smart recommendations** - Find free alternatives (Option 8)
- **Visual feedback** - Clear status messages

**Interactive selector features:**

- **Option 1-3**: Select BIG/MIDDLE/SMALL models
- **Option 4**: Configure reasoning settings (effort, max_tokens, exclude)
- **Option 5**: View current selections
- **Option 6**: Browse LOCAL models only (LMStudio, Ollama)
- **Option 7**: Use Template (pre-built configurations)
- **Option 8**: Get Recommendations (find free alternatives)
- **Option 9**: Save and apply configuration
- **Option 10**: Load saved mode
- **Option 11**: Save current as mode
- **Option 12**: List all modes

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

#### Selector Configuration
```bash
ENABLE_OPENROUTER_SELECTION="true"  # Show/hide OpenRouter models in selector
```

**Selector Configuration Options:**

- **ENABLE_OPENROUTER_SELECTION**: Control which models appear in interactive selector
  - `true`: Show all models (OpenRouter + local) (default)
  - `false`: Show local models only (LMStudio, Ollama)
  - Useful for local-only deployments or when you want to hide marketplace models
**Custom Headers:**

- `CUSTOM_HEADER_*` - Custom headers for API requests (e.g., `CUSTOM_HEADER_ACCEPT`, `CUSTOM_HEADER_AUTHORIZATION`)
  - Uncomment in `.env` file to enable custom headers

### Custom Headers Configuration

Add custom headers to your API requests by setting environment variables with the `CUSTOM_HEADER_` prefix:

```bash
# Uncomment to enable custom headers
# CUSTOM_HEADER_ACCEPT="application/jsonstream"
# CUSTOM_HEADER_CONTENT_TYPE="application/json"
# CUSTOM_HEADER_USER_AGENT="your-app/1.0.0"
# CUSTOM_HEADER_AUTHORIZATION="Bearer your-token"
# CUSTOM_HEADER_X_API_KEY="your-api-key"
# CUSTOM_HEADER_X_CLIENT_ID="your-client-id"
# CUSTOM_HEADER_X_CLIENT_VERSION="1.0.0"
# CUSTOM_HEADER_X_REQUEST_ID="unique-request-id"
# CUSTOM_HEADER_X_TRACE_ID="trace-123"
# CUSTOM_HEADER_X_SESSION_ID="session-456"
```

### Header Conversion Rules

Environment variables with the `CUSTOM_HEADER_` prefix are automatically converted to HTTP headers:

- Environment variable: `CUSTOM_HEADER_ACCEPT`
- HTTP Header: `ACCEPT`

- Environment variable: `CUSTOM_HEADER_X_API_KEY`
- HTTP Header: `X-API-KEY`

- Environment variable: `CUSTOM_HEADER_AUTHORIZATION`
- HTTP Header: `AUTHORIZATION`

### Supported Header Types

- **Content Type**: `ACCEPT`, `CONTENT-TYPE`
- **Authentication**: `AUTHORIZATION`, `X-API-KEY`
- **Client Identification**: `USER-AGENT`, `X-CLIENT-ID`, `X-CLIENT-VERSION`
- **Tracking**: `X-REQUEST-ID`, `X-TRACE-ID`, `X-SESSION-ID`

### Usage Example

```bash
# Basic configuration
OPENAI_API_KEY="sk-your-openai-api-key-here"
OPENAI_BASE_URL="https://api.openai.com/v1"

# Enable custom headers (uncomment as needed)
CUSTOM_HEADER_ACCEPT="application/jsonstream"
CUSTOM_HEADER_CONTENT_TYPE="application/json"
CUSTOM_HEADER_USER_AGENT="my-app/1.0.0"
CUSTOM_HEADER_AUTHORIZATION="Bearer my-token"
```

The proxy will automatically include these headers in all API requests to the target LLM provider.

### Model Mapping

#### Hybrid Mode Configuration (Per-Model Routing)
```bash
# Enable per-model endpoints (set to "true" to enable)
ENABLE_BIG_ENDPOINT="true"
ENABLE_MIDDLE_ENDPOINT="true"
ENABLE_SMALL_ENDPOINT="true"

# Per-model endpoints (if enabled above)
BIG_ENDPOINT="http://localhost:11434/v1"
MIDDLE_ENDPOINT="https://openrouter.ai/api/v1"
SMALL_ENDPOINT="http://127.0.0.1:1234/v1"

# Per-model API keys (defaults to OPENAI_API_KEY if not set)
BIG_API_KEY="sk-or-..."
MIDDLE_API_KEY=""
SMALL_API_KEY="dummy"
```

**Hybrid Mode Options:**

- **ENABLE_BIG_ENDPOINT**: Enable custom endpoint for BIG model (Claude Opus)
  - `true`: Use `BIG_ENDPOINT` and `BIG_API_KEY`
  - `false`: Use default `OPENAI_BASE_URL` and `OPENAI_API_KEY`

- **ENABLE_MIDDLE_ENDPOINT**: Enable custom endpoint for MIDDLE model (Claude Sonnet)
  - `true`: Use `MIDDLE_ENDPOINT` and `MIDDLE_API_KEY`
  - `false`: Use default `OPENAI_BASE_URL` and `OPENAI_API_KEY`

- **ENABLE_SMALL_ENDPOINT**: Enable custom endpoint for SMALL model (Claude Haiku)
  - `true`: Use `SMALL_ENDPOINT` and `SMALL_API_KEY`
  - `false`: Use default `OPENAI_BASE_URL` and `OPENAI_API_KEY`

- **Per-Model Endpoints**: Custom base URLs for different providers
  - Ollama: `http://localhost:11434/v1`
  - LMStudio: `http://127.0.0.1:1234/v1`
  - OpenRouter: `https://openrouter.ai/api/v1`
  - OpenAI: `https://api.openai.com/v1`
  - Azure OpenAI: `https://your-resource.openai.azure.com/openai/deployments/your-deployment`

- **Per-Model API Keys**: Optional per-model authentication
  - If not set, falls back to main `OPENAI_API_KEY`
  - Useful for different API keys per provider
  - Local models can use dummy values

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

### Hybrid Mode - Mix Local & Remote Models

**The project NOW supports TRUE hybrid deployments!** Route each model (BIG/MIDDLE/SMALL) to different providers simultaneously:

#### Hybrid Mode Examples

**Example 1: BIG=Local Ollama, MIDDLE=OpenRouter, SMALL=LMStudio**

```bash
# Main API config
OPENAI_API_KEY="your-openrouter-key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# BIG model - Local Ollama
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="http://localhost:11434/v1"
BIG_API_KEY="dummy"
BIG_MODEL="ollama/qwen2.5:72b"

# MIDDLE model - OpenRouter
ENABLE_MIDDLE_ENDPOINT="false"  # Uses default OPENAI_BASE_URL
MIDDLE_MODEL="openai/gpt-5"

# SMALL model - LMStudio
ENABLE_SMALL_ENDPOINT="true"
SMALL_ENDPOINT="http://127.0.0.1:1234/v1"
SMALL_API_KEY="dummy"
SMALL_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
```

**Example 2: All Different Providers**

```bash
# BIG - GPT-5 on OpenRouter
ENABLE_BIG_ENDPOINT="true"
BIG_ENDPOINT="https://openrouter.ai/api/v1"
BIG_API_KEY="sk-or-..."
BIG_MODEL="openai/gpt-5"

# MIDDLE - Azure OpenAI
ENABLE_MIDDLE_ENDPOINT="true"
MIDDLE_ENDPOINT="https://your-resource.openai.azure.com/openai/deployments/your-deployment"
MIDDLE_API_KEY="your-azure-key"
MIDDLE_MODEL="gpt-4"
MIDDLE_AZURE_API_VERSION="2024-03-01-preview"

# SMALL - Local LMStudio
ENABLE_SMALL_ENDPOINT="true"
SMALL_ENDPOINT="http://127.0.0.1:1234/v1"
SMALL_API_KEY="dummy"
SMALL_MODEL="lmstudio/Meta-Llama-3.1-8B-Instruct"
```

**How It Works:**

1. **Enable per-model routing**: Set `ENABLE_BIG_ENDPOINT="true"`, etc.
2. **Configure endpoint**: Set `BIG_ENDPOINT`, `MIDDLE_ENDPOINT`, `SMALL_ENDPOINT`
3. **Optional API key**: Set per-model API keys or use main `OPENAI_API_KEY`
4. **Automatic routing**: Proxy automatically routes each request to the correct provider

**Benefits:**

- ✅ **Cost optimization**: Use free local models for simple tasks
- ✅ **Best-of-breed**: Pick the best model for each tier
- ✅ **Failover**: If one provider is down, others still work
- ✅ **Privacy**: Route sensitive requests to local models
- ✅ **Performance**: Use local models for speed, cloud for complexity

### OpenRouter Reasoning Tokens

OpenRouter provides unified reasoning support across all providers. Claude Code Proxy implements full compatibility with OpenRouter's reasoning tokens specification.

**Reasoning Token Features:**

1. **Preserving Reasoning Blocks**: Automatically preserves reasoning tokens when `REASONING_EXCLUDE="false"`
   - Reasoning appears in `choices[].message.reasoning` field
   - Enables tool-calling workflows with continued reasoning
   - Maintains conversation integrity across multiple API calls

2. **Unified Control**: Single configuration works across all reasoning-capable models:
   - OpenAI (GPT-5, o1, o3)
   - Anthropic (Claude 3.7, 4.x)
   - Qwen, DeepSeek, xAI Grok, MiniMax, Kimi

3. **Dual Control Modes**:
   - **Effort-based**: `REASONING_EFFORT="high/medium/low"`
     - OpenAI-style proportional reasoning
     - ~20%/50%/80% of max_tokens for reasoning

   - **Token-based**: `REASONING_MAX_TOKENS="8000"`
     - Anthropic/OpenRouter-style direct control
     - Exact token budget for reasoning
     - Capped at 32,000 tokens max, 1,024 tokens min

**Example: Tool Calling with Reasoning**

```python
# First request with reasoning
response = client.chat.completions.create(
    model="openai/gpt-5",
    messages=[{"role": "user", "content": "What's 9.9 vs 9.11?"}],
    extra_body={
        "reasoning": {
            "effort": "high",
            "exclude": False
        }
    }
)

# Reasoning is preserved in response
reasoning = response.choices[0].message.reasoning
content = response.choices[0].message.content

# Pass reasoning back for continued reasoning
response2 = client.chat.completions.create(
    model="openai/gpt-5",
    messages=[
        {"role": "user", "content": f"Context: {reasoning}"},
        {"role": "user", "content": "Explain this comparison"}
    ],
    extra_body={
        "reasoning": {
            "effort": "high",
            "exclude": False
        }
    }
)
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
Test proxy functionality:

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

## 📊 Monitoring & Analytics

### Real-Time Dashboards

**Terminal Dashboard** (Live TUI with Rich):
```bash
# Enable terminal dashboard
python src/main.py --dashboard
# or
export ENABLE_DASHBOARD="true"
python src/main.py
```

**WebSocket Dashboard** (Browser-based):
```bash
# Start proxy normally
python src/main.py

# Access dashboard in browser
open http://localhost:8082/dashboard
```

Features:
- ⚡ Real-time request waterfall
- 📈 Performance metrics (latency, tokens/sec)
- 💰 Cost tracking and estimation
- 🔄 Live routing visualization
- ⚠️ Error monitoring with recent errors
- 🤖 Top model usage statistics

### Prompt Injection (Claude Code Context)

**Inject proxy stats into Claude Code prompts** - Give Claude visibility into proxy performance!

**Interactive Configuration**:
```bash
# Run the configurator
python configure_prompt_injection.py

# Select modules, size, and injection mode
# Generates commands for .zshrc and p10k
```

**Manual Configuration**:
```bash
# Enable prompt injection
export PROMPT_INJECTION_ENABLED="true"
export PROMPT_INJECTION_MODULES="status,performance,errors"
export PROMPT_INJECTION_SIZE="medium"  # large, medium, small
export PROMPT_INJECTION_MODE="auto"    # auto, always, manual, header
```

**Size Variants**:

- **Large** (~200-300 tokens): Multi-line boxes with full details
  ```
  ┌─ 🔧 Proxy Status ─────────────┐
  │ Provider: OpenRouter | Proxy  │
  │ BIG: openai/gpt-5             │
  │ Reasoning: high | 8000 tokens │
  └────────────────────────────────┘
  ```

- **Medium** (~50-100 tokens): Single-line compact [RECOMMENDED]
  ```
  🔧 OpenRouter | 🤖 gpt-5 | 🧠 high | 🔒
  ⚡ 847req | 1234ms | 78t/s | $12.45
  ```

- **Small** (~20-40 tokens): Ultra-compact icons
  ```
  🌐🧠 ⚡847r·78t/s ✓99%
  ```

**Available Modules**:
- `status` - Provider, models, reasoning config
- `performance` - Requests, latency, speed, cost
- `errors` - Success rate, error types
- `models` - Top models and usage stats

**Injection Modes**:
- `auto` - Smart injection (tool calls, streaming) [RECOMMENDED]
- `always` - Inject on every request
- `header` - Compact header only
- `manual` - Programmatic control

**Powerlevel10k Integration**:
```zsh
# Add to ~/.p10k.zsh (see examples/p10k_integration.zsh)
function prompt_custom_proxy_status() {
  # Shows: 🔧⚡✓🤖 in your prompt
  ...
}
```

**Examples**: See `examples/PROMPT_INJECTION_EXAMPLES.md` for detailed scenarios.

### Analytics API

**Get Usage Summary**:
```bash
curl http://localhost:8082/api/analytics/summary?days=7
```

**Time-Series Data** (for charting):
```bash
curl http://localhost:8082/api/analytics/timeseries?days=7&interval=hour
```

**Cost Breakdown**:
```bash
curl http://localhost:8082/api/analytics/cost-breakdown?days=7
```

**Error Analytics**:
```bash
curl http://localhost:8082/api/analytics/errors?days=7
```

**Export Data**:
```bash
curl http://localhost:8082/api/analytics/export?days=30&format=csv -o analytics.csv
curl http://localhost:8082/api/analytics/export?days=30&format=json -o analytics.json
```

### Billing Integration

**Check Account Balances**:
```bash
curl http://localhost:8082/api/billing/balance
```

**Get Usage from Providers**:
```bash
curl http://localhost:8082/api/billing/usage?days=7
```

**Provider-Specific Data**:
```bash
curl http://localhost:8082/api/billing/provider/openrouter?days=7
```

### Model Benchmarking

**Run Benchmark**:
```bash
curl -X POST "http://localhost:8082/api/benchmarks/run?model_name=gpt-4o&iterations=3"
```

**Compare Models**:
```bash
curl -X POST "http://localhost:8082/api/benchmarks/compare?models=gpt-4o&models=gpt-4o-mini"
```

**Get Benchmark Results**:
```bash
curl http://localhost:8082/api/benchmarks/results
```

**View Specific Result**:
```bash
curl http://localhost:8082/api/benchmarks/results/benchmark_gpt-4o_20250119_123456.json
```

### Multi-User Management

**Create User**:
```bash
curl -X POST http://localhost:8082/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "quota_requests": 1000,
    "quota_tokens": 1000000,
    "quota_cost": 10.0
  }'
```

**Get Current User**:
```bash
curl http://localhost:8082/api/users/me \
  -H "x-api-key: sk-..."
```

**Check Quota**:
```bash
curl http://localhost:8082/api/users/me/quota \
  -H "x-api-key: sk-..."
```

**View Usage History**:
```bash
curl http://localhost:8082/api/users/me/usage?days=7 \
  -H "x-api-key: sk-..."
```

### Configuration

**Enable Usage Tracking**:
```bash
# .env
TRACK_USAGE="true"
```

**Enable Terminal Dashboard**:
```bash
# .env
ENABLE_DASHBOARD="true"
DASHBOARD_LAYOUT="default"  # default, compact, detailed
DASHBOARD_REFRESH="0.5"     # seconds between updates
DASHBOARD_WATERFALL_SIZE="20"  # number of requests to show
```

**Compact Logger Mode**:
```bash
# Reduce console noise when dashboard is active
COMPACT_LOGGER="true"
```

---

## 🐳 Docker Deployment

### Quick Start with Docker

**Using Docker Compose (Recommended):**
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

**Manual Docker Build:**
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

### Docker Configuration

**Environment Variables:**
- Mount `.env` file: `-v $(pwd)/.env:/app/.env`
- Or pass directly: `-e OPENAI_API_KEY="..." -e BIG_MODEL="..."`

**Persistent Configuration:**
```bash
# Mount modes.json for persistent configuration
docker run -p 8082:8082 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/modes.json:/app/modes.json \
  claude-code-proxy
```

**Dashboard with Docker:**
```bash
# Run with dashboard modules
docker run -p 8082:8082 \
  -e DASHBOARD_MODULES="performance:dense,activity:sparse" \
  --env-file .env \
  claude-code-proxy
```

### Production Docker Setup

**docker-compose.prod.yml:**
```yaml
services:
  proxy:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8082:8082"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
      - BIG_MODEL=${BIG_MODEL}
      - REASONING_EFFORT=high
    volumes:
      - ./modes.json:/app/modes.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

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

## 🎛️ Dashboard System

### ✅ **FULLY IMPLEMENTED** - Modular Dashboard System

**Interactive Configuration Tool:**
- ✅ `configure_dashboard.py` - Interactive module selection with previews
- ✅ Dense vs Sparse display modes for all modules
- ✅ 1-4 module selection with live previews
- ✅ Command generation for Claude Code and .zshrc integration
- ✅ Startup script generation with executable permissions

**Dashboard Manager:**
- ✅ `src/dashboard/dashboard_manager.py` - Orchestrates multiple modules
- ✅ Environment variable configuration (`DASHBOARD_MODULES`)
- ✅ Rich layout system (1-4 modules in grid/split layouts)
- ✅ Live updating dashboard with configurable refresh rates
- ✅ Plain text fallback when Rich library unavailable

**Live Dashboard Interface:**
- ✅ `src/dashboard/live_dashboard.py` - Replaces terminal output
- ✅ Real-time API monitoring with Rich interface
- ✅ Integration with existing request logger
- ✅ Signal handling (Ctrl+C graceful shutdown)
- ✅ Full-screen dashboard mode

**5 Complete Dashboard Modules:**

1. **✅ Performance Monitor** (`src/dashboard/modules/performance_monitor.py`)
   - Dense: Full performance panel with progress bars, context usage, thinking tokens
   - Sparse: Single line with key metrics (duration, tokens, cost, speed)
   - Real-time session tracking with color coding
   - Cost estimation and efficiency calculations

2. **✅ Activity Feed** (`src/dashboard/modules/activity_feed.py`)
   - Dense: Multi-session request history with status icons
   - Sparse: Compact status summary with request counts
   - Request pairing (start/complete/error tracking)
   - Model routing display and performance metrics

3. **✅ Routing Visualizer** (`src/dashboard/modules/routing_visualizer.py`)
   - Dense: Visual model routing flow with ASCII art
   - Sparse: Compact routing info with token flow
   - Context and output token visualization
   - Performance and cost analysis per routing decision

4. **✅ Analytics Panel** (`src/dashboard/modules/analytics_panel.py`)
   - Dense: Comprehensive analytics (requests, cost, performance, model usage)
   - Sparse: Key metrics summary line
   - Success rate calculation and performance extremes
   - Hot model tracking and usage patterns

5. **✅ Request Waterfall** (`src/dashboard/modules/request_waterfall.py`)
   - Dense: Detailed request lifecycle with timing breakdown
   - Sparse: Compact lifecycle summary
   - Phase-by-phase timing (Parse→Route→Think→Send→Wait→Recv→Done)
   - Real-time progress for active requests

**Base Module System:**
- ✅ `src/dashboard/modules/base_module.py` - Common functionality
- ✅ Request history management with configurable limits
- ✅ Token formatting, cost estimation, progress bars
- ✅ Rich and plain text rendering support
- ✅ Active/completed request tracking

### 🎯 **DASHBOARD USAGE**

**Quick Setup:**
```bash
# 1. Configure your dashboard interactively
python configure_dashboard.py

# 2. Select modules (e.g., performance:dense,activity:sparse)
# 3. Copy generated commands to .zshrc or run directly:
export DASHBOARD_MODULES="performance:dense,activity:sparse"

# 4. Start live dashboard
python -m src.dashboard.live_dashboard
```

**Example Configurations:**
```bash
# Performance monitoring only
DASHBOARD_MODULES="performance:dense"

# Multi-module setup
DASHBOARD_MODULES="performance:sparse,activity:sparse,analytics:dense"

# Full dashboard (4 modules)
DASHBOARD_MODULES="performance:dense,activity:dense,routing:sparse,waterfall:sparse"
```

**Generated Commands:**
- ✅ Environment variable export
- ✅ Claude Code integration instructions
- ✅ .zshrc aliases for easy access
- ✅ Executable startup script (`start_dashboard.sh`)

### 📊 **DASHBOARD PREVIEW EXAMPLES**

**Dense Mode Example (Performance Monitor):**
```
┌─ API Performance Monitor ─────────────────────────────────────┐
│ 🔵 Session abc123 | anthropic/claude-3.5-sonnet→openai/gpt-4o │
│ ⚡ 15.8s | 📊 CTX: ████████░░ 43.7k/200k (22%) | 82 tok/s    │
│ 🧠 THINK: ███░░░░░░░ 920 tokens | 💰 $0.0234 estimated       │
│ 📤 OUT: ██░░░░░░░░ 1.3k/16k | 🌊 STREAMING | 3msg + SYS     │
└───────────────────────────────────────────────────────────────┘
```

**Sparse Mode Example (Activity Feed):**
```
🔵abc123→OK 🟢def456→OK 🔴ghi789→ERR 🔵jkl012→OK | 4req 3.2s avg
```

### 🔧 **DASHBOARD INTEGRATION STATUS**

**✅ PHASE 1 COMPLETE - Standalone Dashboard:**
- Interactive configuration tool with previews
- All 5 dashboard modules (dense + sparse modes)
- Dashboard manager with layout system
- Live dashboard with real-time updates
- Request logger integration
- Command generation for setup
- Environment variable configuration
- Rich formatting with fallback to plain text
- Signal handling and graceful shutdown

**✅ TESTED:**
- Module rendering in both modes
- Configuration parsing and validation
- Layout generation for 1-4 modules
- Request data flow from logger to modules
- Cost estimation and token formatting
- Progress bar generation
- Model name formatting and provider detection

**🔄 PHASE 2 IN DEVELOPMENT - Integrated Proxy Dashboard:**
- **Terminal output replacement** - Dashboard becomes the proxy interface
- **Edge-based module positioning** - Modules on top/bottom/left/right edges
- **Central waterfall display** - Live request flow in center area
- **Moveable modules** - Drag modules between edges and corners
- **Layout persistence** - Save/load dashboard arrangements
- **Resize panels** - Dynamic module sizing
- **Auto-hide inactive modules** - Clean interface when not needed
- **Focus mode** - Expand waterfall to full screen

**🔄 PHASE 3 PLANNED:**
- WebSocket dashboard for browser access
- Historical data persistence
- Advanced analytics with trend analysis
- Custom module creation API
- Dashboard themes and color schemes

---

## 🎉 Complete Features Summary

### ✅ **CORE PROXY FEATURES (FULLY WORKING)**
- **352 models** from multiple sources (OpenRouter, Ollama, LMStudio)
- **Comprehensive reasoning support** (OpenAI, Anthropic, all providers)
- **Dual reasoning control** (effort + max_tokens)
- **OpenRouter reasoning tokens** with block preservation
- **Multi-provider support** (OpenAI, Azure, OpenRouter, local)
- **Function calling** & streaming support
- **Claude API compatibility** with full `/v1/messages` endpoint
- **Smart model mapping** (BIG/MIDDLE/SMALL configuration)
- **Hybrid mode** - Mix local and remote models simultaneously
- **Per-model routing** - Each model to different provider

### ✅ **CONFIGURATION SYSTEM (FULLY WORKING)**
- **10 pre-built templates** for quick setup
- **Smart recommendations** with cost optimization
- **99 configuration modes** for flexibility
- **Interactive selector** with beautiful UI + filtering
- **Local-only mode** (hide/show OpenRouter models)
- **CLI configuration** for automation
- **Environment variable management**
- **Mode saving/loading system**

### ✅ **DASHBOARD SYSTEM (FULLY WORKING)**
- **5 complete dashboard modules** with dense/sparse modes
- **Interactive configuration tool** with live previews
- **Modular architecture** (1-4 modules, user selectable)
- **Real-time monitoring** with Rich terminal interface
- **Request lifecycle tracking** with detailed analytics
- **Cost and performance monitoring**
- **Session-based color coding**
- **Command generation** for integration

### ✅ **MODEL DATABASE (FULLY WORKING)**
- **352 total models** with complete metadata
- **140 free models** (local + OpenRouter free tier)
- **Reasoning support detection** (210+ models)
- **Vision support tracking** (45+ models)
- **Pricing information** per 1M tokens
- **Context window limits** for all models
- **Provider endpoint mapping**

### ✅ **LOGGING SYSTEM (FULLY WORKING)**
- **Rich colored terminal output** with session colors
- **Comprehensive request logging** (start/complete/error)
- **Token usage visualization** with progress bars
- **Performance metrics** (tokens/sec, latency)
- **Cost estimation** with real-time tracking
- **Context window monitoring** with percentage usage
- **Thinking token tracking** for reasoning models

### 🔄 **NEXT PHASE: INTEGRATED PROXY DASHBOARD**

**🎯 Terminal Output Replacement (In Development)**

The next major phase will replace the standard proxy terminal output with a **live dashboard interface** that integrates directly with the running proxy server:

**Core Concept:**
- **Static modules on edges** (top, bottom, left, right) showing persistent info
- **Central waterfall area** displaying real-time request flow
- **Moveable module positioning** - drag modules to any edge or corner
- **Live proxy integration** - dashboard updates as requests flow through proxy

**Planned Layout System:**
```
┌─────────────────────────────────────────────────────────────┐
│ [Performance Monitor]     [Analytics Panel]                │ ← Top Edge
├─────────────────────────────────────────────────────────────┤
│[Activity] │                                     │ [Routing] │ ← Left/Right
│  Feed     │        LIVE REQUEST WATERFALL       │Visualizer │   Edges
│           │                                     │           │
│           │ 🔵 req_123 Parse→Route→Send→Wait... │           │
│           │ 🟢 req_122 ──────────────── Done   │           │
│           │ 🔵 req_124 Parse→Route...           │           │
│           │ 🔴 req_121 ──── Error: Rate Limit  │           │
├─────────────────────────────────────────────────────────────┤
│              [Model Usage Stats]                            │ ← Bottom Edge
└─────────────────────────────────────────────────────────────┘
```

**Module Positioning Options:**
- **Top Edge:** Performance, Analytics, Summary stats
- **Bottom Edge:** Model usage, Cost tracking, System info  
- **Left Edge:** Activity feed, Request history, Alerts
- **Right Edge:** Routing info, Token usage, Performance metrics
- **Corners:** Compact modules (4 corner positions available)

**Interactive Features (Planned):**
- ✅ **Module dragging** - Move modules between edges with mouse/keyboard
- ✅ **Resize panels** - Adjust module sizes dynamically
- ✅ **Module cycling** - Rotate through different modules in same position
- ✅ **Layout presets** - Save/load different dashboard arrangements
- ✅ **Auto-hide** - Modules collapse when inactive
- ✅ **Focus mode** - Expand waterfall to full screen

**Integration Method:**
```bash
# Instead of standard proxy output:
python start_proxy.py

# New integrated dashboard mode:
python start_proxy.py --dashboard-mode
# or
export PROXY_DASHBOARD_MODE="true"
python start_proxy.py
```

**Configuration:**
```bash
# Dashboard layout configuration
DASHBOARD_LAYOUT="performance:top,activity:left,routing:right,analytics:bottom"
DASHBOARD_WATERFALL_SIZE="60%"  # Central area size
DASHBOARD_AUTO_HIDE="true"      # Hide inactive modules
DASHBOARD_REFRESH_RATE="2.0"    # Updates per second
```

### 🔄 **OTHER FEATURES IN DEVELOPMENT**
- **WebSocket dashboard** for browser access
- **Historical data persistence** beyond current session
- **Advanced trend analysis** with usage patterns
- **Custom dashboard themes** and color schemes
- **Dashboard module API** for third-party extensions
- **Automated model benchmarking**
- **Cost optimization alerts**
- **Usage analytics export**

### ❌ **KNOWN LIMITATIONS**
- Dashboard data is **session-only** (no persistence between restarts)
- **No web interface** (terminal-only dashboard currently)
- **Limited to 4 modules** maximum in dashboard
- **No custom module creation** without code changes
- **Cost estimates are approximate** (not real-time billing)

### 🔒 **SECURITY NOTES**
- **No hardcoded secrets** - All API keys via environment variables
- **Gitignore protection** - Sensitive files excluded from version control
- **Clean repository** - No development artifacts or temporary files

### 🧪 **TESTING STATUS**
- ✅ **Core proxy functionality** - Fully tested with multiple providers
- ✅ **Model selection and configuration** - Tested with all templates
- ✅ **Dashboard modules** - All 5 modules tested in both modes
- ✅ **Request logging integration** - Tested with live API calls
- ✅ **Configuration management** - Mode saving/loading tested
- ✅ **Interactive tools** - Selector and configurator tested
- 🔄 **Load testing** - In progress for high-volume scenarios
- 🔄 **Edge case handling** - Ongoing testing for error conditions

---

## 📋 **AUDIT CHECKLIST**

### ✅ **IMPLEMENTED AND WORKING**
- [x] Claude API proxy with full compatibility
- [x] Multi-provider support (OpenAI, Azure, OpenRouter, local)
- [x] Reasoning token support across all providers
- [x] 352 model database with metadata
- [x] Interactive model selector with filtering
- [x] 10 pre-built configuration templates
- [x] 99 configuration mode slots
- [x] Smart model recommendations
- [x] Hybrid deployment support
- [x] Rich terminal logging with colors
- [x] Complete dashboard system (5 modules)
- [x] Dashboard configuration tool
- [x] Live dashboard interface
- [x] Request lifecycle tracking
- [x] Cost and performance monitoring
- [x] Session-based analytics

### ✅ **NEWLY IMPLEMENTED** (Latest Update)
- [x] **WebSocket dashboard** for browser - Real-time dashboard at `/dashboard`
- [x] **Historical data persistence** - Analytics API with time-series data
- [x] **Advanced analytics** - Cost breakdown, error analysis, trend tracking
- [x] **Real-time billing integration** - Provider API integration (OpenRouter, OpenAI, Anthropic)
- [x] **Automated model benchmarking** - Standardized tests, performance comparison
- [x] **Multi-user authentication** - User management with API keys and quotas
- [x] **Database backend** - Enhanced SQLite with export capabilities

### 🔄 **IN DEVELOPMENT**
- [ ] Custom dashboard themes
- [ ] Module creation API
- [ ] Web-based configuration interface (currently API-only)

---

<div align="center">

**Made with ❤️ for the developer community**

[⭐ Star on GitHub](https://github.com/yourusername/claude-code-proxy)

</div>
