# Troubleshooting Guide

## 401 Unauthorized Error: "No auth credentials found"

**Symptom:** You see errors like:
```
Error code: 401 - {'error': {'message': 'No auth credentials found', 'code': 401}}
```

**Cause:** Your `OPENAI_API_KEY` in `.env` is not set to a valid API key.

**Solution:**

1. **For OpenRouter users:**
   - Go to https://openrouter.ai/keys
   - Create or copy your API key
   - Update `.env` file:
     ```bash
     OPENAI_API_KEY="sk-or-v1-YOUR-ACTUAL-KEY-HERE"
     ```

2. **For OpenAI users:**
   - Go to https://platform.openai.com/api-keys
   - Create or copy your API key
   - Update `.env` file:
     ```bash
     OPENAI_API_KEY="sk-YOUR-ACTUAL-KEY-HERE"
     OPENAI_BASE_URL="https://api.openai.com/v1"
     ```

3. **Restart the proxy** after updating the `.env` file

## 400 Bad Request: Unsupported verbosity value

**Symptom:** You see errors like:
```
Error code: 400 - "Unsupported value: 'high' is not supported with the 'gpt-5.1-codex' model"
```

**Cause:** The `VERBOSITY` parameter is not supported by all models.

**Solution:**

1. Open your `.env` file
2. Set `VERBOSITY` to empty:
   ```bash
   VERBOSITY=""
   ```
3. Restart the proxy

**Note:** Verbosity support varies by model and provider. It's recommended to leave it empty unless you know your specific model supports it.

## Reasoning Configuration Issues

### Model doesn't support reasoning parameters

**Symptom:** Reasoning parameters are ignored or cause errors.

**Solution:** Only these models support reasoning:

- **OpenAI o-series:** o1, o3, o4-mini, gpt-5 (use effort: low/medium/high)
- **Anthropic Claude:** claude-opus-4, claude-sonnet-4, claude-3-7-sonnet (use thinking tokens: 1024-16000)
- **Google Gemini:** gemini-2.5-flash-preview-04-17 (use thinking budget: 0-24576)

### Using model suffix notation

You can specify reasoning parameters directly in model names:

```bash
# OpenAI o-series
"o4-mini:high"           # High reasoning effort
"o4-mini:medium"         # Medium reasoning effort

# Anthropic Claude
"claude-opus-4-20250514:4k"    # 4096 thinking tokens
"claude-opus-4-20250514:8000"  # 8000 thinking tokens

# Google Gemini
"gemini-2.5-flash-preview-04-17:16k"  # 16384 thinking budget
```

## General Debugging Steps

1. **Check your `.env` file:**
   ```bash
   cat .env
   ```
   Verify all required variables are set correctly.

2. **Check the proxy logs:**
   Look for ERROR or WARNING messages that indicate what's wrong.

3. **Test with a simple model first:**
   Try using a basic model like `gpt-4o-mini` without reasoning parameters to verify your API key works.

4. **Verify your API key has credits:**
   - OpenRouter: Check https://openrouter.ai/credits
   - OpenAI: Check https://platform.openai.com/usage

5. **Check provider status:**
   - OpenRouter: https://status.openrouter.ai/
   - OpenAI: https://status.openai.com/
