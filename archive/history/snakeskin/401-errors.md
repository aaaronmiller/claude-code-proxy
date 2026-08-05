# Troubleshooting 401 "User Not Found" Errors

If you're experiencing 401 authentication errors after updating the Claude Code Proxy, this guide will help you diagnose and resolve the issue.

## Understanding the Error

The error `401 Unauthorized - user not found` comes from your API provider (OpenRouter, OpenAI, Azure, etc.), not from the proxy itself. This typically means:

1. **Invalid API Key**: The API key is not recognized by the provider
2. **Expired API Key**: The API key has expired or been revoked
3. **Account Issue**: The account associated with the API key is inactive or suspended
4. **Wrong API Key**: The wrong API key is being sent (e.g., Anthropic key instead of provider key)
5. **Configuration Issue**: The API key is not being loaded correctly from environment variables

## Important Note About `OPENAI_API_KEY`

**The `OPENAI_API_KEY` environment variable is used for ANY provider you connect to**, not just OpenAI:
- **OpenRouter**: Use your OpenRouter API key (starts with `sk-or-v1-`)
- **OpenAI**: Use your OpenAI API key (starts with `sk-`)
- **Azure**: Use your Azure API key
- **Other providers**: Use whatever API key that provider gives you

The variable is named `OPENAI_API_KEY` for compatibility reasons, but it works with any OpenAI-compatible endpoint.

## Quick Fixes

### 1. Verify Your API Key is Loaded

Check that your API key is correctly set in your environment:

```bash
# Check if the API key is set
echo $OPENAI_API_KEY

# If empty, make sure your .env file is correctly configured
cat .env | grep OPENAI_API_KEY
```

### 2. Reinstall Dependencies

After pulling new changes, reinstall dependencies to ensure all packages are up to date:

```bash
pip install -r requirements.txt
```

### 3. Restart the Proxy

Make sure to fully restart the proxy after pulling new changes:

```bash
# Stop the proxy (Ctrl+C)
# Then start it again
python start_proxy.py
```

### 4. Check Your Provider Account

Verify your API provider account is active:

**For OpenRouter:**
1. Go to https://openrouter.ai/
2. Log in to your account
3. Check your API key is active
4. Verify you have sufficient credits
5. Try regenerating your API key if needed

**For OpenAI:**
1. Go to https://platform.openai.com/
2. Check your API key is active
3. Verify your billing is set up and has credits

**For Azure OpenAI:**
1. Check your Azure portal
2. Verify your deployment is active
3. Confirm your API key and endpoint are correct

## Detailed Diagnostics

### Check Your Configuration

Run this script to verify your configuration:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

print(f"API Key set: {bool(api_key)}")
print(f"API Key prefix: {api_key[:7] if api_key else 'None'}...")
print(f"Base URL: {base_url}")

# Check for passthrough mode triggers
if api_key == "pass" or api_key == "your-api-key-here":
    print("WARNING: Passthrough mode enabled - you need to provide API key via headers")
elif not api_key:
    print("WARNING: No API key configured")
else:
    print("API Key appears to be configured correctly")
```

### Test Your API Key Directly

Test if your API key works directly with your provider:

**For OpenRouter:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**For OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**For custom endpoints:**
```bash
# Replace with your OPENAI_BASE_URL
curl $OPENAI_BASE_URL/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If this returns a 401 error, the problem is with your API key or provider account, not the proxy.

### Check for Environment Variable Conflicts

Make sure no other environment variables are overriding your API key:

```bash
# List all environment variables containing "KEY"
env | grep -i key
```

Look for any variables that might conflict with `OPENAI_API_KEY`.

## Common Issues and Solutions

### Issue 1: "Passthrough Mode" Enabled

**Symptoms**: Proxy says "enabling passthrough mode" on startup

**Cause**: `OPENAI_API_KEY` is not set, or is set to "pass" or "your-api-key-here"

**Solution**: Set a valid API key in your `.env` file:

```bash
# For OpenRouter
OPENAI_API_KEY="sk-or-v1-YOUR-ACTUAL-KEY-HERE"

# For OpenAI
OPENAI_API_KEY="sk-YOUR-ACTUAL-KEY-HERE"

# For Azure or other providers
OPENAI_API_KEY="your-provider-api-key-here"
```

### Issue 2: API Key in Wrong Format

**Symptoms**: 401 error even though key appears to be set

**Cause**: API key is in wrong format for the provider

**Solution**: Verify your key format:
- OpenRouter keys start with: `sk-or-v1-`
- OpenAI keys start with: `sk-`
- Make sure there are no spaces or newlines in the key

### Issue 3: Wrong Base URL

**Symptoms**: API works with `curl` but not with proxy

**Cause**: `OPENAI_BASE_URL` is pointing to wrong endpoint

**Solution**: Set the correct base URL for your provider:

```bash
# For OpenRouter
OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# For OpenAI
OPENAI_BASE_URL="https://api.openai.com/v1"

# For Azure OpenAI
OPENAI_BASE_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment-name"

# For local models (Ollama, LM Studio, etc.)
OPENAI_BASE_URL="http://localhost:11434/v1"
```

### Issue 4: Credits Exhausted

**Symptoms**: API worked before but stopped working

**Cause**: API provider account has run out of credits or exceeded quota

**Solution**:

**For OpenRouter:**
1. Go to https://openrouter.ai/account
2. Check your credit balance
3. Add more credits if needed

**For OpenAI:**
1. Go to https://platform.openai.com/account/billing
2. Check your usage and billing status
3. Add a payment method or increase limits if needed

**For Azure:**
1. Check your Azure portal
2. Verify your subscription is active
3. Check quota limits for your deployment

### Issue 5: API Key Cached

**Symptoms**: Changed API key but still getting 401

**Cause**: Old API key cached in environment

**Solution**: Fully restart your terminal/shell:

```bash
# Exit and reopen your terminal
# OR source your .env file again
source .env

# Then restart the proxy
python start_proxy.py
```

## Specific Fix for Recent Update

If the error started **immediately after pulling commit d8bc31c** (terminal output enhancements):

### Step 1: Update and Restart

```bash
# Pull the latest fix
git pull origin main

# Reinstall dependencies
pip install -r requirements.txt

# Restart the proxy
python start_proxy.py
```

The latest version includes defensive error handling that prevents workspace extraction from interfering with API calls.

### Step 2: Verify Rich Library

The terminal enhancements require the `rich` library. Verify it's installed:

```bash
python -c "from rich.console import Console; print('Rich OK')"
```

If this fails:

```bash
pip install rich>=14.2.0
```

### Step 3: Check Logs

Look for any error messages during startup that might indicate configuration issues:

```bash
python start_proxy.py 2>&1 | grep -i error
```

## Still Having Issues?

If none of these solutions work:

1. **Enable Debug Logging**:
   ```bash
   export LOG_LEVEL="DEBUG"
   python start_proxy.py
   ```

2. **Test with Minimal Configuration**:
   Create a minimal `.env` file with just:
   ```bash
   OPENAI_API_KEY="your-key-here"
   OPENAI_BASE_URL="https://openrouter.ai/api/v1"
   BIG_MODEL="openai/gpt-4o"
   SMALL_MODEL="openai/gpt-4o-mini"
   ```

3. **Check for Proxy/VPN Interference**:
   Some corporate proxies or VPNs can interfere with API calls. Try:
   ```bash
   unset http_proxy
   unset https_proxy
   python start_proxy.py
   ```

4. **Verify Python Version**:
   ```bash
   python --version  # Should be 3.10 or higher
   ```

5. **Report the Issue**:
   If the problem persists, create an issue at:
   https://github.com/anthropics/claude-code-proxy/issues

   Include:
   - Error message
   - Output from the diagnostic script above
   - Python version
   - Operating system
   - Contents of `.env` (with API keys redacted)

## Prevention

To avoid similar issues in the future:

1. **Keep dependencies updated**: Run `pip install -r requirements.txt` after each pull
2. **Use environment files**: Keep API keys in `.env` rather than exporting manually
3. **Test after updates**: Run a test request after pulling changes:
   ```bash
   curl -X POST http://localhost:8000/v1/messages \
     -H "x-api-key: your-anthropic-key" \
     -H "Content-Type: application/json" \
     -d '{"model": "claude-3-5-sonnet-20241022", "messages": [{"role": "user", "content": "test"}], "max_tokens": 10}'
   ```

4. **Monitor API usage**: Regularly check your OpenRouter dashboard to ensure you have credits

## FAQ: Why is it called `OPENAI_API_KEY`?

The environment variable is named `OPENAI_API_KEY` for compatibility with OpenAI's API format, but **it works with ANY OpenAI-compatible provider**:

- **OpenRouter**: Most common use case - proxy OpenAI models through OpenRouter
- **OpenAI**: Direct OpenAI API access
- **Azure OpenAI**: Microsoft's Azure-hosted OpenAI models
- **Local models**: Ollama, LM Studio, vLLM, etc.
- **Other providers**: Any service with OpenAI-compatible endpoints

The proxy translates Claude API requests to OpenAI-compatible format, then forwards them to whatever endpoint you specify in `OPENAI_BASE_URL`. The naming convention is kept for compatibility, but the key itself is for whatever provider you're using.

## Related Documentation

- [Configuration Guide](../README.md#configuration)
- [Terminal Output Configuration](TERMINAL_OUTPUT.md)
- [API Key Setup](../README.md#api-key-setup)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
