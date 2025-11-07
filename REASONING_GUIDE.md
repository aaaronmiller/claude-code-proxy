# GPT-5 and Advanced Reasoning Models - Complete Guide

## Overview

This guide explains how to use GPT-5 and other advanced reasoning models through the Claude Code Proxy with full support for reasoning parameters, verbosity settings, and automatic model detection.

## What Was Added

### 1. **Configuration Support** (`src/core/config.py`)

New environment variables:

- **`REASONING_EFFORT`**: Controls reasoning depth
  - `"low"` - Faster, less compute
  - `"medium"` - Balanced (default)
  - `"high"` - Best quality, most compute
  - Empty/Not set - Disabled

- **`VERBOSITY`**: Controls response detail level
  - `"high"` - More detailed responses
  - Empty/Not set - Default verbosity

- **`REASONING_EXCLUDE`**: Controls reasoning token visibility
  - `"true"` - Hide reasoning tokens from response
  - `"false"` - Show reasoning tokens (default)

### 2. **Request Converter** (`src/conversion/request_converter.py`)

Automatically detects models that support reasoning and adds the proper API parameters:

```python
# Added to requests for supported models
{
    "reasoning": {
        "effort": "high",
        "enabled": True,
        "exclude": False
    },
    "verbosity": "high"
}
```

**Models Automatically Detected**:
- OpenAI GPT-5 (`gpt-5`, `openai/gpt-5`)
- OpenAI o3 series (`o3`, `o3-mini`, `openai/o3`)
- Qwen thinking models (`qwen3`, `qwen-2.5-thinking`)
- DeepSeek V3 thinking (`deepseek-v3.1`, `deepseek-v3.2-exp`)
- Anthropic Claude Haiku 4.5
- Any model with "thinking" in the name

### 3. **Interactive Model Selector** (`scripts/select_model.py`)

A powerful TUI that allows you to:
- Browse 340+ OpenRouter models
- Filter by capabilities (reasoning, vision, free)
- Search for specific models
- Configure BIG, MIDDLE, and SMALL models
- Set reasoning parameters
- Automatically update `.env` file

### 4. **Model Fetcher** (`scripts/fetch_openrouter_models.py`)

Fetches the latest model list from OpenRouter and categorizes them:
- Identifies models with reasoning support
- Identifies models with verbosity support
- Saves to JSON and CSV for easy browsing
- Shows top models in each category

## How to Use

### Step 1: Fetch Latest Models (Optional but Recommended)

```bash
# Downloads current model list from OpenRouter
python scripts/fetch_openrouter_models.py
```

This creates:
- `models/openrouter_models.json` - Structured data for the selector
- `models/openrouter_models.csv` - Spreadsheet format for manual browsing

**Output from recent fetch**:
- 340 total models
- 209 with reasoning support
- 129 standard models
- 2 with verbosity support

### Step 2: Configure Your Models

#### Option A: Use the Interactive Selector (Recommended)

```bash
# Launch the interactive model selector
python scripts/select_model.py
```

Then follow the menu to:
1. Select your BIG model (Claude Opus equivalent)
2. Select your MIDDLE model (Claude Sonnet equivalent)
3. Select your SMALL model (Claude Haiku equivalent)
4. Configure reasoning settings
5. Save to `.env`

#### Option B: Manual Configuration

Edit your `.env` file:

```bash
# OpenRouter with GPT-5 high-reasoning
OPENAI_API_KEY="your-openrouter-key"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# Model configuration
BIG_MODEL="openai/gpt-5"
MIDDLE_MODEL="openai/gpt-5"
SMALL_MODEL="gpt-4o-mini"

# Reasoning configuration
REASONING_EFFORT="high"
VERBOSITY="high"
REASONING_EXCLUDE="false"
```

### Step 3: Start the Proxy

```bash
# Start the proxy server
python start_proxy.py
```

### Step 4: Use with Claude Code

```bash
# Use Claude Code with the proxy
ANTHROPIC_BASE_URL=http://localhost:8082 claude
```

## Example Configurations

### High-Quality Reasoning (GPT-5)

```bash
# Best for complex analysis and reasoning tasks
REASONING_EFFORT="high"
VERBOSITY="high"
BIG_MODEL="openai/gpt-5"
```

### Balanced Performance (o3-mini)

```bash
# Good balance of speed and quality
REASONING_EFFORT="medium"
VERBOSITY="high"
BIG_MODEL="openai/o3-mini"
```

### Cost-Effective (Qwen Thinking)

```bash
# Lower cost with reasoning support
REASONING_EFFORT="medium"
VERBOSITY="high"
BIG_MODEL="qwen/qwen-2.5-thinking-32b"
```

### Free Tier (NVIDIA Nemotron)

```bash
# Free models with reasoning
REASONING_EFFORT="low"
VERBOSITY="default"
BIG_MODEL="nvidia/nemotron-nano-12b-v2-vl:free"
```

## Understanding Reasoning Modes

### Effort Levels

1. **Low**: Minimal reasoning budget
   - Faster responses
   - Lower cost
   - Good for simple tasks

2. **Medium**: Balanced reasoning (default)
   - Moderate compute usage
   - Balanced cost/quality
   - Good for most tasks

3. **High**: Maximum reasoning budget
   - Best quality
   - Highest cost
   - Best for complex analysis

### Verbosity

- **Default**: Standard response length
- **High**: More detailed, explanatory responses

### Reasoning Exclusion

- **exclude=false**: Show reasoning tokens in response
  - Useful for transparency
  - See the model's thought process

- **exclude=true**: Hide reasoning tokens
  - Cleaner final answer
  - Reasoning still happens internally

## How It Works

### Request Flow

1. **Client** sends Claude API request to proxy
2. **Proxy** converts request to OpenAI format
3. **Converter** checks if model supports reasoning
4. If yes, adds `reasoning` object with configured parameters
5. **OpenAI Client** sends request to provider
6. **Provider** processes with reasoning budget
7. **Response** is converted back to Claude format
8. **Client** receives response with reasoning (if not excluded)

### Automatic Model Detection

The proxy uses keyword matching to detect reasoning-capable models:

```python
# From request_converter.py
def _model_supports_reasoning(model_id: str) -> bool:
    keywords = [
        "gpt-5",
        "openai/o3",
        "qwen3",
        "qwen-2.5-thinking",
        "deepseek-v3",
        "deepseek-v3.1",
        "claude-haiku",
        "thinking"
    ]
    return any(keyword in model_id.lower() for keyword in keywords)
```

## Troubleshooting

### Models Not Using Reasoning?

1. Check that `REASONING_EFFORT` is set
2. Verify the model name contains reasoning keywords
3. Check logs for: "Added reasoning configuration"
4. Ensure provider supports reasoning parameters

### Getting Errors?

1. Check `.env` syntax (no spaces around `=`)
2. Verify API key is valid
3. Check model is available on your provider
4. Review error messages in logs

### Want to See What's Happening?

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python start_proxy.py
```

This will show the converted request including reasoning parameters.

## Files Modified

1. **`src/core/config.py`** - Added reasoning config
2. **`src/conversion/request_converter.py`** - Added reasoning support
3. **`.env.example`** - Added new config options
4. **`README.md`** - Updated with reasoning documentation

## Files Created

1. **`scripts/fetch_openrouter_models.py`** - Model fetcher
2. **`scripts/select_model.py`** - Interactive model selector
3. **`models/openrouter_models.json`** - Model database
4. **`models/openrouter_models.csv`** - Model spreadsheet
5. **`REASONING_GUIDE.md`** - This guide

## Key Benefits

✅ **Automatic Detection** - No manual parameter handling
✅ **Provider Agnostic** - Works with any OpenAI-compatible API
✅ **Multiple Models** - Support for GPT-5, o3, Qwen, DeepSeek, etc.
✅ **Easy Configuration** - Simple environment variables
✅ **Interactive Setup** - Visual model selector
✅ **Cost Control** - Set reasoning level based on needs
✅ **Backward Compatible** - Existing configs work unchanged

## Summary

You now have a complete system for using GPT-5 and other advanced reasoning models with Claude Code. The proxy automatically:
- Detects reasoning-capable models
- Adds proper API parameters
- Supports multiple providers
- Provides easy configuration tools

**Start here**:
```bash
python scripts/fetch_openrouter_models.py
python scripts/select_model.py
```

Enjoy your enhanced reasoning capabilities! 🚀
