# API Key Configuration Explained

## The Confusion

The environment variable is named `OPENAI_API_KEY`, but you're using **OpenRouter**, not OpenAI. This is confusing!

## Why It's Named This Way

The proxy was originally designed for OpenAI, then extended to support any OpenAI-compatible API (including OpenRouter). The variable name wasn't changed to maintain backward compatibility.

**Think of it as:** `OPENAI_COMPATIBLE_API_KEY` (but it's still called `OPENAI_API_KEY`)

## What You Need

Since you're using OpenRouter (as shown by `OPENAI_BASE_URL="https://openrouter.ai/api/v1"`), you need to put your **OpenRouter API key** in the `OPENAI_API_KEY` variable.

### Your Current .env:

```bash
# This is the OpenRouter endpoint
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# Put your OpenRouter API key here (despite the misleading name)
OPENAI_API_KEY="sk-or-v1-YOUR_OPENROUTER_KEY_HERE"
```

## How to Get Your OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign in or create an account
3. Go to "Keys" section
4. Create a new API key
5. Copy the key (starts with `sk-or-v1-...`)
6. Paste it in your `.env` file

## Example Configuration

```bash
# ===== For OpenRouter =====
OPENAI_API_KEY="sk-or-v1-abc123def456..."  # Your OpenRouter key
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# ===== For OpenAI (if you were using OpenAI instead) =====
# OPENAI_API_KEY="sk-proj-abc123..."  # Your OpenAI key
# OPENAI_BASE_URL="https://api.openai.com/v1"

# ===== For Azure OpenAI =====
# OPENAI_API_KEY="your-azure-key"
# OPENAI_BASE_URL="https://your-resource.openai.azure.com/..."

# ===== For Local Ollama (no real key needed) =====
# OPENAI_API_KEY="dummy"  # Any value works
# OPENAI_BASE_URL="http://localhost:11434/v1"
```

## The Two API Keys in This Proxy

### 1. `OPENAI_API_KEY` (Required)
- **Purpose:** Authenticate with your AI provider (OpenRouter, OpenAI, etc.)
- **Used for:** Making API calls to get AI responses
- **Your case:** Put your OpenRouter API key here

### 2. `ANTHROPIC_API_KEY` (Optional)
- **Purpose:** Validate that Claude Code clients have the correct key
- **Used for:** Security - only allow authorized clients to use your proxy
- **Your case:** Set to `"pass"` (or any value) if you want to require clients to send this exact key

## What Happens If You Don't Set OPENAI_API_KEY

The proxy will fail to start with this error:
```
ValueError: OPENAI_API_KEY not found in environment variables
```

## Current Status

Your `.env` currently has:
```bash
OPENAI_API_KEY="sk-or-v1-YOUR_OPENROUTER_KEY_HERE"
```

**You need to replace `YOUR_OPENROUTER_KEY_HERE` with your actual OpenRouter API key.**

## Quick Fix

1. Get your OpenRouter API key from https://openrouter.ai/keys
2. Edit `.env` and replace the placeholder:
   ```bash
   OPENAI_API_KEY="sk-or-v1-PASTE_YOUR_REAL_KEY_HERE"
   ```
3. Save the file
4. Restart the proxy:
   ```bash
   python start_proxy.py
   ```

## Verification

When you start the proxy with a valid key, you'll see:
```
✅ Configuration loaded successfully
   OpenAI Base URL: https://openrouter.ai/api/v1
```

If the key is invalid, you'll see errors when making requests:
```
❌ Error code: 401 - Invalid API key
```

## Summary

- ✅ `OPENAI_API_KEY` = Your OpenRouter API key (despite the confusing name)
- ✅ `OPENAI_BASE_URL` = `https://openrouter.ai/api/v1` (already correct)
- ✅ `ANTHROPIC_API_KEY` = Optional security key for client validation

**Action needed:** Replace the placeholder with your real OpenRouter API key.
